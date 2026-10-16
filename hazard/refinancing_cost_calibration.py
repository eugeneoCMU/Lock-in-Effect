"""Freeze external cost scenarios, then compare held-out cost distributions.

Pennsylvania HMDA 2022/2023 profiles supply separate development cutoffs. Only
2024 cost distributions are compared; this is never behavioral validation or
contemporaneous calibration of a 2009 HARP opportunity. No files are read or
written here. Source/profile file hashes are receipts checked by the acquisition
driver, not hashes independently recoverable from these in-memory mappings.
"""

from collections import Counter
from collections.abc import Mapping
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
import math
from numbers import Real
import re

from .hmda_cost_profiles import REQUIRED, build_profiles, is_narrower, number, quantiles
from .refinancing_cost_bridge import bridge_cost_ratio


YEARS = ("2022", "2023")
PURPOSES = ("31", "32")
QUANTILES = ("p25", "p50", "p75")
VIEW = "conforming_sitebuilt_principal_residence"
COUNTS = (
    "originated_records", "numeric_loan_cost_records",
    "fee_new_rounded_principal_pair_records",
    "missing_or_nonpositive_new_principal_among_known_cost",
    "joint_numeric_rate_and_cost_records", "numeric_points_among_known_cost",
    "numeric_lender_credits_among_known_cost", "reported_zero_cost_records",
    "positive_cost_records", "zero_cost_reporting_lender_count",
)
MISSING_REASONS = {"blank", "not_applicable_or_unavailable", "exempt"}
INTERPRETATION = (
    "External reported-cost evidence and conditional balance/financing scenarios only. "
    "The held-out comparison tests cost-distribution transport, not refinancing behavior. "
    "Modern transaction costs cannot contemporaneously calibrate a 2009 HARP borrower. "
    "No rate, points, or credit quantiles are paired into offers; no causal, s/gamma, "
    "or portfolio estimate is fitted."
)


def _hash(value, name):
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(name + " must be a lowercase SHA256 receipt")
    return value


def _count(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError("Invalid count: " + name)
    return value


def _mapping(value, name):
    if not isinstance(value, Mapping):
        raise ValueError("Missing or invalid mapping: " + name)
    return value


def _cutoffs(value):
    if not isinstance(value, Mapping) or set(value) != set(QUANTILES):
        raise ValueError("All three quantile cutoffs are required")
    result = {}
    for name in QUANTILES:
        x = value[name]
        if isinstance(x, bool) or not isinstance(x, Real) or not math.isfinite(x) or x < 0:
            raise ValueError("Quantiles must be finite nonnegative numbers")
        result[name] = float(x)
    if not result["p25"] <= result["p50"] <= result["p75"]:
        raise ValueError("Quantile cutoffs must be ordered")
    return result


def _denominators(group):
    _mapping(group, "purpose group")
    result = {name: _count(group.get(name), name) for name in COUNTS}
    missing = _mapping(group.get("cost_missing_by_code"), "cost_missing_by_code")
    if not set(missing).issubset(MISSING_REASONS):
        raise ValueError("Unknown cost-missing disclosure code")
    result["cost_missing_by_code"] = {k: _count(v, k) for k, v in missing.items()}
    known, originated = result["numeric_loan_cost_records"], result["originated_records"]
    if known + sum(missing.values()) != originated:
        raise ValueError("Known and missing costs must partition originations")
    if result["fee_new_rounded_principal_pair_records"] + result["missing_or_nonpositive_new_principal_among_known_cost"] != known:
        raise ValueError("Valid and invalid principal must partition known costs")
    if result["reported_zero_cost_records"] + result["positive_cost_records"] != known:
        raise ValueError("Zero and positive costs must partition known costs")
    for name in ("joint_numeric_rate_and_cost_records", "numeric_points_among_known_cost",
                 "numeric_lender_credits_among_known_cost"):
        if result[name] > known:
            raise ValueError("Joint disclosure count exceeds known costs")
    lenders = group.get("zero_cost_counts_by_lender_descending")
    purposes = _mapping(group.get("zero_cost_purpose_counts"), "zero_cost_purpose_counts")
    if not isinstance(lenders, list) or not set(purposes).issubset(PURPOSES):
        raise ValueError("Missing zero-cost concentration counts")
    lender_counts = [_count(n, "lender zero count", 1) for n in lenders]
    purpose_counts = {k: _count(v, "purpose zero count") for k, v in purposes.items()}
    zeros = result["reported_zero_cost_records"]
    if sum(lender_counts) != zeros or len(lenders) != result["zero_cost_reporting_lender_count"] or sum(purpose_counts.values()) != zeros:
        raise ValueError("Zero-cost concentration counts are inconsistent")
    result["zero_cost_counts_by_lender_descending"] = list(lender_counts)
    result["zero_cost_purpose_counts"] = purpose_counts
    return result


def _source_validation(profile):
    source = _mapping(profile.get("source_validation"), "source_validation")
    _hash(source.get("source_sha256"), "source_sha256")
    _count(source.get("source_bytes"), "source_bytes", 1)
    _count(source.get("csv_columns"), "csv_columns", len(REQUIRED))
    if source.get("frozen_source_schema_matched") is not True or source.get("all_query_cells_match") is not True:
        raise ValueError("Source schema and official aggregation acceptance are required")
    cells = source.get("cells")
    if not isinstance(cells, list) or not cells:
        raise ValueError("Source aggregation cells are required")
    seen = set()
    outcomes = Counter()
    for cell in cells:
        _mapping(cell, "source cell")
        key = cell.get("action_taken"), cell.get("loan_purpose")
        if key in seen or key[0] not in ("1", "2", "3", "4", "5") or key[1] not in PURPOSES:
            raise ValueError("Invalid or duplicate source query cell")
        seen.add(key)
        outcomes[key[0]] += _count(cell.get("count"), "source cell count")
        amount = number(cell.get("loan_amount_sum"))
        if amount is None or amount < 0:
            raise ValueError("Invalid source aggregate principal")
    raw_count = _count(profile.get("raw_application_records"), "raw_application_records", 1)
    raw_outcomes = _mapping(profile.get("raw_application_outcomes"), "raw_application_outcomes")
    if any(k not in ("1", "2", "3", "4", "5") for k in raw_outcomes):
        raise ValueError("Invalid raw application outcome")
    expected = {k: _count(v, "raw outcome") for k, v in raw_outcomes.items()}
    if sum(outcomes.values()) != raw_count or any(outcomes[k] != expected.get(k, 0) for k in set(outcomes) | set(expected)):
        raise ValueError("Source query cells do not match profile denominators")
    return deepcopy(dict(source))


def _profile_groups(profile, year):
    _mapping(profile, "development profile")
    if type(profile.get("year")) is not int or profile["year"] != int(year) or profile.get("state") != "PA":
        raise ValueError("Development profile must match its Pennsylvania year")
    if profile.get("status") != "descriptive_external_cost_profiles" or profile.get("evidence_class") != "observed_reported_loan_cost_component":
        raise ValueError("Expected descriptive observed cost-component profile")
    for name in ("model_parameters_changed", "behavioral_parameters_fitted", "new_portfolio_estimates"):
        if type(profile.get(name)) is not int or profile[name] != 0:
            raise ValueError("Cost profiles cannot contain fitted model or portfolio changes")
    source = _source_validation(profile)
    view = _mapping(profile.get(VIEW), VIEW)
    groups = view.get("by_purpose")
    if not isinstance(groups, list) or len(groups) != 2:
        raise ValueError("Separate purpose 31 and 32 groups are required")
    result = {}
    for group in groups:
        _mapping(group, "purpose group")
        purpose = group.get("purpose_code")
        if purpose not in PURPOSES or purpose in result:
            raise ValueError("Invalid or duplicate purpose group")
        denominators = _denominators(group)
        if denominators["fee_new_rounded_principal_pair_records"] == 0:
            raise ValueError("Each development purpose needs observed cost/principal pairs")
        percent = _cutoffs(group.get("new_principal_cost_ratio_percent_quantiles"))
        result[purpose] = (denominators, {k: float(Decimal(str(v)) / 100) for k, v in percent.items()})
    return result, source


def _digest(payload):
    try:
        raw = json.dumps(
            {k: v for k, v in payload.items() if k != "freeze_integrity_sha256"},
            sort_keys=True, separators=(",", ":"), allow_nan=False,
        ).encode()
    except (ValueError, TypeError) as exc:
        raise ValueError("Frozen metadata must be strict JSON") from exc
    return hashlib.sha256(raw).hexdigest()


def freeze_cost_scenarios(development_profiles, *, protocol_sha256, profile_sha256):
    """Freeze exactly 84 scenarios using separate 2022/2023 PA cost quantiles.

    Both mappings must use exactly the string keys ``2022`` and ``2023``.
    Hash receipts identify files already checked by the acquisition driver.
    This validates their shape and acceptance metadata, not external file bytes.
    """
    profiles = _mapping(development_profiles, "development_profiles")
    hashes = _mapping(profile_sha256, "profile_sha256")
    if set(profiles) != set(YEARS) or set(hashes) != set(YEARS):
        raise ValueError("Exactly the separate 2022 and 2023 development years are required")
    protocol_hash = _hash(protocol_sha256, "protocol_sha256")
    hashes = {year: _hash(hashes[year], "profile_sha256") for year in YEARS}
    result = dict(
        status="frozen_conditional_cost_scenarios", evidence_class="conditional_cost_scenario",
        protocol_sha256=protocol_hash, profile_sha256=hashes,
        development_years=[2022, 2023], held_out_year=2024, geography="PA",
        cost_component="reported_loan_costs", interpretation=INTERPRETATION,
        frozen_cutoffs={}, source_validation={}, scenarios=[],
    )
    for year in YEARS:
        groups, source = _profile_groups(profiles[year], year)
        result["source_validation"][year] = source
        result["frozen_cutoffs"][year] = {}
        for purpose in PURPOSES:
            denominators, cutoffs = groups[purpose]
            result["frozen_cutoffs"][year][purpose] = cutoffs
            for quantile in QUANTILES:
                q = cutoffs[quantile]
                choices = [("supplied_balance_ratio", financing, ratio)
                           for ratio in (.9, 1., 1.1) for financing in ("cash", "financed")]
                if purpose == "31":
                    choices.extend([("unchanged_balance", "cash", None),
                                    ("all_fees_financed_no_other_balance_change", "financed", None)])
                for rule, financing, ratio in choices:
                    scenario = bridge_cost_ratio(
                        q, balance_rule=rule, financing=financing,
                        new_to_existing_ratio=ratio, purpose_code=int(purpose),
                    )
                    scenario.update(
                        development_year=int(year), quantile=quantile,
                        group_denominators=deepcopy(denominators),
                        profile_sha256=hashes[year], protocol_sha256=protocol_hash,
                    )
                    result["scenarios"].append(scenario)
    result["scenario_count"] = len(result["scenarios"])
    result["freeze_integrity_sha256"] = _digest(result)
    return result


def _checked_frozen(frozen):
    _mapping(frozen, "frozen")
    required = {"status", "evidence_class", "protocol_sha256", "profile_sha256",
                "development_years", "held_out_year", "geography", "cost_component",
                "interpretation", "frozen_cutoffs", "source_validation", "scenarios",
                "scenario_count", "freeze_integrity_sha256"}
    if not required.issubset(frozen):
        raise ValueError("Required frozen metadata is missing")
    if _hash(frozen["freeze_integrity_sha256"], "freeze_integrity_sha256") != _digest(frozen):
        raise ValueError("Frozen metadata integrity mismatch")
    if (frozen["status"] != "frozen_conditional_cost_scenarios"
            or frozen["evidence_class"] != "conditional_cost_scenario"
            or frozen["development_years"] != [2022, 2023]
            or frozen["held_out_year"] != 2024 or frozen["geography"] != "PA"
            or frozen["cost_component"] != "reported_loan_costs"
            or frozen["scenario_count"] != 84 or len(frozen["scenarios"]) != 84):
        raise ValueError("Frozen metadata has unsupported scope")
    _hash(frozen["protocol_sha256"], "protocol_sha256")
    for name in ("profile_sha256", "frozen_cutoffs", "source_validation"):
        if not isinstance(frozen[name], Mapping) or set(frozen[name]) != set(YEARS):
            raise ValueError("Frozen development-year metadata is incomplete")
    for year in YEARS:
        _hash(frozen["profile_sha256"][year], "profile_sha256")
        if set(frozen["frozen_cutoffs"][year]) != set(PURPOSES):
            raise ValueError("Frozen purpose cutoffs are incomplete")
        for purpose in PURPOSES:
            _cutoffs(frozen["frozen_cutoffs"][year][purpose])
    return frozen


def compare_held_out_costs(rows, *, frozen):
    """Apply frozen cutoffs to 2024 PA originated records; never fit or refit.

    Wrong year, state, purpose, or application action is rejected. Valid scoped
    originations outside the narrower loan filters are excluded and counted.
    Shares use known costs with positive new principal; empty shares remain None.
    """
    frozen = _checked_frozen(frozen)
    rows = list(rows)
    if any(not isinstance(row, Mapping) or row.get("action_taken") != "1" for row in rows):
        raise ValueError("Held-out comparison requires originated action 1 records only")
    profile = build_profiles(rows, expected_year=2024, expected_state="PA")
    selected = [row for row in rows if is_narrower(row)]
    groups = {g["purpose_code"]: g for g in profile[VIEW]["by_purpose"]}
    result = dict(
        status="held_out_cost_distribution_comparison", test_scope="cost_distribution_transport_only",
        held_out_year=2024, geography="PA", interpretation=INTERPRETATION,
        protocol_sha256=frozen["protocol_sha256"], profile_sha256=deepcopy(frozen["profile_sha256"]),
        freeze_integrity_sha256=frozen["freeze_integrity_sha256"],
        raw_originated_records=len(rows), narrower_originated_records=len(selected),
        excluded_by_loan_filters=len(rows) - len(selected), held_out_by_purpose={}, comparisons=[],
    )
    for purpose in PURPOSES:
        decimals = []
        for row in selected:
            if row["loan_purpose"] != purpose:
                continue
            cost, principal = number(row["total_loan_costs"]), number(row["loan_amount"])
            if cost is not None and principal is not None and principal > 0:
                decimals.append(cost / principal)
        values = [float(q) for q in decimals]
        if any(not math.isfinite(q) for q in values):
            raise ValueError("Held-out cost ratio is not finite")
        denominators = _denominators(groups[purpose])
        result["held_out_by_purpose"][purpose] = dict(
            group_denominators=denominators,
            q_distribution=dict(
                records=len(values), zero_records=values.count(0.),
                positive_records=sum(q > 0 for q in values),
                minimum=min(values) if values else None, maximum=max(values) if values else None,
                quantiles=quantiles(decimals),
            ),
        )
        for year in YEARS:
            cutoffs = frozen["frozen_cutoffs"][year][purpose]
            counts = {"at_or_below_" + name: sum(q <= cutoffs[name] for q in values)
                      for name in QUANTILES}
            counts["central_p25_to_p75_inclusive"] = sum(cutoffs["p25"] <= q <= cutoffs["p75"] for q in values)
            result["comparisons"].append(dict(
                development_year=int(year), purpose_code=int(purpose), held_out_year=2024,
                frozen_q_cutoffs=deepcopy(cutoffs), group_denominators=deepcopy(denominators),
                counts=counts, proportions={k: n / len(values) if values else None for k, n in counts.items()},
            ))
    return result
