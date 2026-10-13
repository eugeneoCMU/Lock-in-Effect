"""Bounded quarterly rebuild after the external original-source schema gate.

Only origination identities, compact cohort cells, the exact May 2022 snapshot,
and one contiguous loan history are held in memory. Sources are read-only. No
download, cloud eviction, cache replacement, or population pooling occurs here.
Individual identifiers appear only in private parquet artifacts, never reports.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re

import polars as pl

# This source-only command never fetches macro data. config's legacy import
# requires a key even to read constants; do not require live credentials here.
os.environ.setdefault('FRED_API_KEY', 'offline-source-rebuild-no-network')
from config import COUPON_STEP, MARKOV_STATES
from freddie_raw_quarter_audit import IdentityExceptions, check_resources, finite
from schema import SOURCE_SEMANTICS_VERSION, validate_performance_semantics

SNAPSHOT_MONTH = "202205"
COHORT_KEYS = ["vintage", "coupon", "fico_bucket", "ltv_bucket"]
HISTORY_KEYS = ["vintage", "cohort_coupon", "fico_bucket", "ltv_bucket"]
TERMINAL = {"Prepaid", "Defaulted", "Liquidated"}
MONTH_RE = re.compile(rb"20\d{2}(0[1-9]|1[0-2])")
SNAPSHOT_SCHEMA = {
    "loan_id": pl.String, "stratum_id": pl.String, "fico": pl.Int64,
    "property_state": pl.String, "orig_ltv": pl.Float64, "coupon": pl.Float64,
    "orig_upb": pl.Float64, "balance": pl.Float64, "loan_age": pl.Float64,
    "state": pl.String, "vintage": pl.Int64, "fico_bucket": pl.String,
    "ltv_bucket": pl.String, "cohort_coupon": pl.Float64,
    "original_loan_term": pl.Float64, "reporting_period": pl.String,
    "current_note_rate": pl.Float64, "remaining_months": pl.Float64,
    "modification_flag": pl.String, "current_non_ib_upb": pl.Float64,
    "interest_bearing_upb": pl.Float64, "payment_deferral_flag": pl.String,
}
HISTORY_SCHEMA = dict(zip(HISTORY_KEYS, [pl.Int64, pl.Float64, pl.String, pl.String]),
    cohort_original_upb=pl.Float64, historical_prepaid_upb=pl.Float64,
    survivor_original_upb=pl.Float64, history_first_observed_payoff_count=pl.Int64,
    history_gap_payoff_count=pl.Int64)


def _month(value):
    if not MONTH_RE.fullmatch(value):
        raise ValueError("Invalid required YYYYMM identity/date field")
    return int(value[:4]) * 12 + int(value[4:]) - 1


def _state(delinquency, assistance, zero_balance):
    if zero_balance == b"01":
        return "Prepaid"
    if zero_balance in {b"02", b"03", b"09", b"15"}:
        return "Defaulted"
    if zero_balance in {b"16", b"96"}:
        return "Liquidated"
    # REO acquisition is not reversed by a concurrent assistance-plan flag.
    if delinquency == b"RA":
        return "Defaulted"
    if assistance == b"F":
        return "Forbearance"
    if delinquency in {b"RA", b"RP"}:
        return "Defaulted"
    if delinquency.isdigit() and int(delinquency) >= 3:
        return "D90+"
    return {b"1": "D30", b"2": "D60"}.get(delinquency, "Current")


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_quarter(orig, perf, output, quarter, cutoff="202509", transition_end="202205", *, exclude_zero_note_rate=False,
                  allow_partial_cohort_overrun=False, identity_exceptions=None):
    """Write corrected compact artifacts only after every source check succeeds.

    Coupon buckets and outcome mapping match ingest.py. First-observed voluntary
    payoffs use original UPB; payoffs after gaps use the last observed valid UPB.
    Those assumptions are counted and reported, not silently presented as known
    previous-month balances. Opening-UPB transition weights require adjacent
    calendar months and an active positive opening state through transition_end.
    """
    orig, perf, output = Path(orig), Path(perf), Path(output)
    if not re.fullmatch(r"20\d{2}Q[1-4]", quarter):
        raise ValueError("quarter must be YYYYQn")
    cutoff_b, transition_b = str(cutoff).encode(), str(transition_end).encode()
    cutoff_ord, transition_ord = _month(cutoff_b), _month(transition_b)
    snapshot_ord = _month(SNAPSHOT_MONTH.encode())
    if transition_ord > cutoff_ord or snapshot_ord > cutoff_ord:
        raise ValueError("The panel cutoff must cover snapshot and transition cutoffs")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise FileExistsError("Choose a new or empty quarterly output directory")
    id_re = re.compile(("F" + quarter[2:] + r"\d+").encode())
    identity = IdentityExceptions(quarter, identity_exceptions)
    vintage = int(quarter[:4])
    counts = Counter({k: 0 for k in [
        "origination_rows", "eligible_original_ids", "excluded_original_ids",
        "performance_rows", "eligible_pre_cutoff_rows", "post_cutoff_date_rows",
        "excluded_pre_cutoff_rows", "valid_balance_rows", "invalid_balance_rows",
        "negative_balance_rows", "missing_or_nonfinite_age_rows",
        "within_loan_backward_rows", "missing_calendar_months",
        "valid_balance_missing_calendar_months", "voluntary_payoff_rows",
        "first_observed_payoff_rows", "payoff_with_nonadjacent_prior_rows",
        "loans_with_pre_cutoff_history", "loans_with_pre_snapshot_history",
        "history_eligible_original_ids", "source_group_reentries",
        "duplicate_loan_month_rows", "maximum_single_loan_rows",
    ]})
    counts.update(first_observed_payoff_fallback_upb=0.0,
                  payoff_with_nonadjacent_prior_upb=0.0, total_prepaid_upb=0.0)
    zero_rates=dict(enabled=exclude_zero_note_rate,otherwise_eligible_frm_count=0,
        otherwise_eligible_frm_upb=0.,known360_count=0,known360_upb=0.)
    all_ids, loans = set(), {}
    fixed, source_history = defaultdict(float), defaultdict(lambda: [0., 0., 0., 0, 0])
    orig_hash, perf_hash = hashlib.sha256(), hashlib.sha256()
    with orig.open("rb") as source:
        for raw in source:
            orig_hash.update(raw)
            counts["origination_rows"] += 1
            if counts["origination_rows"] % 200000 == 0:
                check_resources(orig.parent)
            row = raw.rstrip(b"\r\n").split(b"|")
            if len(row) != 32:
                raise ValueError("Origination source requires exactly 32 fields")
            loan_id = row[19]
            exceptional = not id_re.fullmatch(loan_id) and identity.accept(loan_id, 'origination')
            if not id_re.fullmatch(loan_id) and not exceptional:
                raise ValueError("Origination identity does not match the declared quarter")
            if loan_id in all_ids:
                raise ValueError("Duplicate origination identity")
            all_ids.add(loan_id)
            fico, upb, ltv, rate, term = (finite(row[i]) for i in (0, 10, 11, 12, 21))
            base_eligible = (row[15] == b"FRM" and upb is not None and upb > 0
                        and ltv is not None and 1 <= ltv <= 200
                        and fico is not None and 300 <= fico <= 850)
            if base_eligible and rate == 0 and exclude_zero_note_rate:
                zero_rates['otherwise_eligible_frm_count']+=1
                zero_rates['otherwise_eligible_frm_upb']+=upb
                if term == 360:
                    zero_rates['known360_count']+=1
                    zero_rates['known360_upb']+=upb
                counts['excluded_original_ids']+=1
                continue
            eligible = base_eligible and term == 360
            if not eligible:
                counts["excluded_original_ids"] += 1
                continue
            if rate is None or not 0 < rate < 30:
                raise ValueError("Eligible origination lacks a valid note rate")
            if exceptional:
                identity.eligible(upb)
            first_month = _month(row[1])
            bucket = round((rate / 100.) / COUPON_STEP) * COUPON_STEP
            key = (vintage, bucket, "<680" if fico < 680 else "680-740" if fico < 740 else "740+",
                   "≤80" if ltv <= 80 else ">80")
            # Tuple retains original term by the explicit eligibility constant.
            loans[loan_id] = (key, upb, rate / 100., int(fico), ltv,
                              row[16].decode("utf-8") if row[16] else None, first_month)
            fixed[key] += upb
            counts["eligible_original_ids"] += 1
            if first_month <= snapshot_ord:
                source_history[key][0] += upb
                counts["history_eligible_original_ids"] += 1
    if not loans:
        raise ValueError("No eligible 360-month fixed-rate source loans")
    if any(not math.isfinite(upb) for upb in fixed.values()):
        raise ValueError("Original cohort balances exceed finite numeric support")

    # Values: financial/risk sums, finite age count, record count and state counts.
    cells = defaultdict(lambda: {"exposure_upb": 0., "orig_upb_sum": 0., "prepaid_upb": 0.,
        "finite_age_sum": 0., "finite_age_count": 0, "loan_count": 0,
        "opening_upb": 0., "adjacent_opening_upb": 0., "first_observed_opening_upb": 0.,
        "gap_opening_upb": 0., "first_observed_payoff_upb": 0., "gap_payoff_upb": 0.,
        "first_observed_payoff_count": 0, "gap_payoff_count": 0, "states": Counter()})
    snapshot, covered, history_covered = [], set(), set()
    weighted_transitions, count_transitions = Counter(), Counter()
    cohort_cash = defaultdict(lambda: dict(loans=0,loans_with_payoff_above_original=0,
        above_original_payoff_upb=0.,multiple_positive_payoff_loans=0,terminal_revival_loans=0))
    td = Counter({k: 0 for k in ["eligible_rows", "contiguous_pairs", "used_pairs",
        "gap_pairs_excluded", "zero_opening_balance_pairs", "terminal_absorption_violations"]})

    def finish(loan_id, rows):
        if not rows:
            return
        months = [r[0] for r in rows]
        counts["within_loan_backward_rows"] += sum(b < a for a, b in zip(months, months[1:]))
        if len(months) != len(set(months)):
            raise ValueError("Duplicate loan-month in quarterly source")
        counts["missing_calendar_months"] += max(months) - min(months) + 1 - len(months)
        valid = sorted((r for r in rows if r[1] is not None and r[1] >= 0), key=lambda r: r[0])
        if not valid:
            return
        covered.add(loan_id)
        counts["loans_with_pre_cutoff_history"] += 1
        vm = [r[0] for r in valid]
        counts["valid_balance_missing_calendar_months"] += max(vm) - min(vm) + 1 - len(vm)
        key, upb, rate, fico, ltv, property_state, first_month = loans[loan_id]
        is_history_source = first_month <= snapshot_ord
        previous = None
        loan_paid=0.;positive_payoffs=0;revivals=0
        for month, balance, age, state, contract in valid:
            yr, zero_month = divmod(month, 12)
            ym = f"{yr:04d}{zero_month+1:02d}"
            first = previous is None
            adjacent = not first and month == previous[0] + 1
            opening = upb if first else previous[1]
            paid = opening if state == "Prepaid" else 0.
            loan_paid+=paid
            positive_payoffs+=int(paid>0)
            revivals+=int(previous is not None and previous[3] in TERMINAL and state not in TERMINAL)
            c = cells[key + (ym,)]
            c["exposure_upb"] += balance
            c["orig_upb_sum"] += upb
            c["prepaid_upb"] += paid
            c["opening_upb"] += opening
            c["first_observed_opening_upb" if first else "adjacent_opening_upb" if adjacent else "gap_opening_upb"] += opening
            c["loan_count"] += 1
            c["states"][state] += 1
            if age is not None:
                c["finite_age_sum"] += age
                c["finite_age_count"] += 1
            if state == "Prepaid":
                counts["voluntary_payoff_rows"] += 1
                counts["total_prepaid_upb"] += paid
                if first:
                    counts["first_observed_payoff_rows"] += 1
                    counts["first_observed_payoff_fallback_upb"] += paid
                    c["first_observed_payoff_upb"] += paid
                    c["first_observed_payoff_count"] += 1
                elif not adjacent:
                    counts["payoff_with_nonadjacent_prior_rows"] += 1
                    counts["payoff_with_nonadjacent_prior_upb"] += paid
                    c["gap_payoff_upb"] += paid
                    c["gap_payoff_count"] += 1
            if is_history_source and month <= snapshot_ord:
                history_covered.add(loan_id)
                h = source_history[key]
                h[1] += paid
                h[3] += int(state == "Prepaid" and first)
                h[4] += int(state == "Prepaid" and not first and not adjacent)
                if month == snapshot_ord and balance > 0 and state not in TERMINAL:
                    if age is None or age < 0 or age != int(age):
                        raise ValueError("Active snapshot requires a finite nonnegative integer loan age")
                    h[2] += upb
                    snapshot.append(dict(zip(SNAPSHOT_SCHEMA, [
                        loan_id.decode(), f"{key[0]}_{round(key[1]*10000)}_{key[2]}_{key[3]}",
                        fico, property_state, ltv, rate, upb, balance, age, state, vintage,
                        key[2], key[3], key[1], 360., ym, *contract])))
            if month <= transition_ord:
                td["eligible_rows"] += 1
                if previous is not None:
                    td["contiguous_pairs"] += int(adjacent)
                    td["gap_pairs_excluded"] += int(not adjacent)
                    td["zero_opening_balance_pairs"] += int(adjacent and opening == 0)
                    if previous[3] in TERMINAL and state not in TERMINAL:
                        td["terminal_absorption_violations"] += 1
                    if adjacent and opening > 0 and previous[3] not in TERMINAL:
                        pair = previous[3], state
                        weighted_transitions[pair] += opening
                        count_transitions[pair] += 1
                        td["used_pairs"] += 1
            previous = (month, balance, age, state)
        cash=cohort_cash[key]
        cash['loans']+=1
        cash['loans_with_payoff_above_original']+=int(loan_paid>upb)
        cash['above_original_payoff_upb']+=max(loan_paid-upb,0.)
        cash['multiple_positive_payoff_loans']+=int(positive_payoffs>1)
        cash['terminal_revival_loans']+=int(revivals>0)

    seen_groups, current, group, group_dates = set(), None, [], set()
    max_decoded_month = None
    with perf.open("rb") as source:
        for raw in source:
            perf_hash.update(raw)
            counts["performance_rows"] += 1
            row = raw.rstrip(b"\r\n").split(b"|")
            if len(row) != 32:
                raise ValueError("Performance source requires exactly 32 fields")
            loan_id = row[0]
            if ((not id_re.fullmatch(loan_id) and not identity.accept(loan_id, 'performance'))
                    or loan_id not in all_ids):
                raise ValueError("Performance identity has no matching quarterly origination")
            month = _month(row[1])
            if current != loan_id:
                finish(current, group)
                if loan_id in seen_groups:
                    raise ValueError("Noncontiguous loan group reentry in quarterly source")
                seen_groups.add(loan_id)
                current, group, group_dates = loan_id, [], set()
            # Identity/date checks cover excluded loans and dates too. Outcomes
            # still remain untouched until the boundary immediately below.
            if month in group_dates:
                raise ValueError("Duplicate loan-month in quarterly source")
            group_dates.add(month)
            counts["maximum_single_loan_rows"] = max(counts["maximum_single_loan_rows"],len(group_dates))
            if len(group_dates) > 10000:
                raise ValueError("Single-loan history exceeds the 10000-row memory bound")
            # No outcome field is decoded before this date/identity boundary.
            if month > cutoff_ord:
                counts["post_cutoff_date_rows"] += 1
            elif loan_id not in loans:
                counts["excluded_pre_cutoff_rows"] += 1
            else:
                counts["eligible_pre_cutoff_rows"] += 1
                validate_performance_semantics(row)
                counts["semantic_rows_validated"] += 1
                counts["forbearance_assistance_rows"] += int(row[29] == b'F')
                counts["reo_with_forbearance_flag_rows"] += int(row[3] == b'RA' and row[29] == b'F')
                counts["extended_delinquency_rows"] += int(row[3].isdigit() and int(row[3]) >= 10)
                counts["other_terminal_rows"] += int(row[8] in {b'16', b'96'})
                balance, age = finite(row[2]), finite(row[4])
                max_decoded_month = max(month, max_decoded_month or month)
                if balance is None or balance < 0:
                    counts["invalid_balance_rows"] += 1
                    counts["negative_balance_rows"] += int(balance is not None and balance < 0)
                else:
                    counts["valid_balance_rows"] += 1
                counts["missing_or_nonfinite_age_rows"] += int(age is None)
                # Additional May-only evidence is retained without replacing
                # the recorded original-rate/original-term model inputs.
                contract = None
                if month == snapshot_ord:
                    current_rate = finite(row[10])
                    contract = (None if current_rate is None else current_rate/100., finite(row[5]), row[7].decode() or None,
                                finite(row[11]), finite(row[31]), row[24].decode() or None)
                group.append((month, balance, age, _state(row[3], row[29], row[8]), contract))
            if counts["performance_rows"] % 2000000 == 0:
                check_resources(perf.parent)
                print(f"Quarterly rebuild rows scanned: {counts['performance_rows']:,}", flush=True)
    finish(current, group)
    identity_report = identity.finish({'origination': orig_hash.hexdigest(), 'performance': perf_hash.hexdigest()})
    if len(covered) != len(loans):
        raise ValueError("Eligible original sources lack valid pre-cutoff performance coverage")
    if len(history_covered) != counts["history_eligible_original_ids"]:
        raise ValueError("Eligible original sources lack valid pre-snapshot performance coverage")
    counts["loans_with_pre_snapshot_history"] = len(history_covered)
    if td["terminal_absorption_violations"]:
        raise ValueError(f"Terminal absorption violations in the frozen transition history: {td['terminal_absorption_violations']}")

    panel_rows, cumulative, overruns = [], defaultdict(float), {}
    for key, c in sorted(cells.items()):
        states = c.pop("states")
        if any(not math.isfinite(v) for v in c.values()):
            raise ValueError("Cohort cell totals exceed finite numeric support")
        mode = max(MARKOV_STATES, key=lambda s: (states[s], -MARKOV_STATES.index(s)))
        denominator = fixed[key[:4]]
        cumulative[key[:4]] += c["prepaid_upb"]
        burnout = cumulative[key[:4]] / denominator
        if burnout<0 or not math.isfinite(burnout):
            raise ValueError('Invalid finite nonnegative source cash ratio')
        if burnout > 1 + 1e-10:
            cash=cohort_cash[key[:4]]
            if not allow_partial_cohort_overrun:
                raise ValueError("Cumulative prepayments exceed the fixed source original balance")
            if cash['multiple_positive_payoff_loans'] or cash['terminal_revival_loans']:
                raise ValueError('Unresolved payoff identity cannot use a partial-cohort exception')
            if key[:4] not in overruns:
                overruns[key[:4]]=dict(cohort=list(key[:4]),first_crossing_month=key[4],
                    original_upb=denominator,**cash)
            overruns[key[:4]].update(peak_ratio=burnout,cumulative_prepaid_upb=cumulative[key[:4]])
        panel_rows.append(dict(zip(COHORT_KEYS + ["reporting_period"], key), **c,
            cohort_original_upb=denominator,
            mean_loan_age=c["finite_age_sum"]/c["finite_age_count"] if c["finite_age_count"] else float("nan"),
            mode_state=mode, monthly_prepay_rate=c["prepaid_upb"]/max(c["exposure_upb"],1.),
            burnout=burnout, period=datetime.strptime(key[4],"%Y%m")))
    history_rows = []
    for key, (original, paid, surviving, first, gaps) in sorted(source_history.items()):
        if not all(math.isfinite(v) for v in (original, paid, surviving)) or not 0 <= paid <= original or not 0 <= surviving <= original:
            raise ValueError("Invalid fixed source cohort pre-snapshot history")
        history_rows.append(dict(zip(HISTORY_SCHEMA, [*key, original, paid, surviving, first, gaps])))
    frames = {
        "panel.parquet": pl.DataFrame(panel_rows),
        "cohort_history.parquet": pl.DataFrame(history_rows, schema=HISTORY_SCHEMA),
        "snapshot.parquet": pl.DataFrame(snapshot, schema=SNAPSHOT_SCHEMA),
        "eligible_source_ids.parquet": pl.DataFrame({"loan_sequence_number": sorted(x.decode() for x in loans)}),
        "transition_counts.parquet": pl.DataFrame([
            {"from_state": a,"to_state": b,"opening_upb": float(weighted_transitions[a,b]),
             "count": count_transitions[a,b]} for a in MARKOV_STATES for b in MARKOV_STATES]),
    }
    total_paid, total_events = counts["total_prepaid_upb"], counts["voluntary_payoff_rows"]
    td = dict(td, estimation_end=str(transition_end), weighting="opening_upb_and_count",
              unsupported_states=[s for s in MARKOV_STATES if not sum(weighted_transitions[s,t] for t in MARKOV_STATES)])
    risk_sets = {name:sum(r[name] for r in panel_rows) for name in
                ["opening_upb","adjacent_opening_upb","first_observed_opening_upb","gap_opening_upb","exposure_upb"]}
    if not all(math.isfinite(v) for v in [*risk_sets.values(), *counts.values(), *weighted_transitions.values()]):
        raise ValueError("Quarter totals exceed finite numeric support")
    report = dict(quarter=quarter, population="known 360-month fixed-rate originations; valid FICO/LTV/positive original UPB and note rate",
        source_semantics_version=SOURCE_SEMANTICS_VERSION,
        current_contract_fields='Contemporaneous May evidence only; rates decimal, maturity months, balances USD, flags as reported; original model conventions unchanged; missing or nonfinite numeric fields retained as null',
        identity_exceptions=identity_report,
        zero_note_rate_exclusions=zero_rates,
        quarter_cash_ratio_audit=dict(partial_cohort_overrun_enabled=allow_partial_cohort_overrun,
            overrun_cohort_count=len(overruns),overruns=list(overruns.values()),
            complete_cohort_gate='Final model panel remains bounded after all source partitions combine'),
        cutoff=str(cutoff), snapshot_month=SNAPSHOT_MONTH, transition_end=str(transition_end),
        source_sha256={"origination":orig_hash.hexdigest(),"performance":perf_hash.hexdigest()},
        schema={"origination_width_counts":{"32":counts["origination_rows"]},
                "performance_width_counts":{"32":counts["performance_rows"]},
                "declared_quarter_ids_validated":True,"duplicate_origination_ids":0,
                "unknown_performance_ids":0,"duplicate_loan_months":0,"group_reentries":0},
        counts=dict(counts), transition_diagnostics=td,
        cutoff_proof={"post_cutoff_outcomes_decoded":0,"outcome_filter_precedes_decode":True,
                      "latest_decoded_month": None if max_decoded_month is None else f"{max_decoded_month//12:04d}{max_decoded_month%12+1:02d}"},
        payoff_assumptions={"first_observed":"original UPB fallback", "calendar_gap":"last observed valid UPB",
            "first_observed_payoff_upb_fraction": counts["first_observed_payoff_fallback_upb"]/total_paid if total_paid else 0.,
            "gap_payoff_upb_fraction":counts["payoff_with_nonadjacent_prior_upb"]/total_paid if total_paid else 0.,
            "first_observed_payoff_row_fraction":counts["first_observed_payoff_rows"]/total_events if total_events else 0.,
            "gap_payoff_row_fraction":counts["payoff_with_nonadjacent_prior_rows"]/total_events if total_events else 0.},
        risk_sets=risk_sets,
        mode_state_tie_order=list(MARKOV_STATES),
        artifacts={name:{"rows":df.height} for name,df in frames.items()})
    # All checks precede publication. IDs remain in owner-readable local files.
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    for name, frame in frames.items():
        path = output/name
        frame.write_parquet(path)
        path.chmod(0o600)
        report["artifacts"][name]["sha256"] = _sha256(path)
    (output/"report.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--orig", type=Path, required=True)
    parser.add_argument("--perf", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--quarter", required=True)
    parser.add_argument("--cutoff", default="202509")
    parser.add_argument("--transition-end", default="202205")
    args = parser.parse_args()
    result = build_quarter(args.orig,args.perf,args.output,args.quarter,args.cutoff,args.transition_end)
    print(json.dumps({"quarter":result["quarter"],"artifacts":result["artifacts"]},indent=2))
