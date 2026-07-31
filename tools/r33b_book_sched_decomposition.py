"""R33-B part 2: price the cross-design scheduled-amortization wedge.

Implements `specs/SPEC_R33B_book_sched_decomposition.md`, which was committed
before this script ran. No estimation and no simulation: the swap of the
scheduled-amortization series is linear in trapped liquidity (the accumulation
is a net, unclipped cumsum), so the effect is an accounting decomposition over
committed artifacts.

Writes abm/data/r33b_book_sched_results.json.
"""
import json
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "abm"))
os.environ.setdefault("FRED_API_KEY", "offline-decomposition-no-fetch")

import fed_mbs_extension_risk as fed  # noqa: E402

FOLDIN = json.loads((ROOT / "abm" / "data" / "runs"
                     / "run-2026-07-04-15yr-foldin" / "manifest.json").read_text())
CROSS = json.loads((ROOT / "abm" / "data"
                    / "cross_design_results.json").read_text())
SEEDS = json.loads((ROOT / "abm" / "data"
                    / "cross_design_seeds_results.json").read_text())
REWEIGHT = json.loads((ROOT / "abm" / "data"
                       / "cross_design_reweight_results.json").read_text())
COMPSHIFT = json.loads((ROOT / "hazard" / "data"
                        / "composition_shift_results.json").read_text())

QT_START = fed.QT_START
N_MONTHS = FOLDIN["metrics"]["qt_window"]["n_months"]
WINDOW = pd.date_range(QT_START, periods=N_MONTHS, freq="ME")


def sched_sum(coupon_pct: float, age_months: float, term: int = 360) -> float:
    """Unweighted sum of the scheduled-amortization SMM over the QT window."""
    origin = QT_START - pd.DateOffset(months=int(round(age_months)))
    s = fed.scheduled_amortization_series(
        WINDOW, coupon=coupon_pct / 100.0, origin=origin, term=term)
    return float(s.sum())


def book_mean_age_months() -> tuple:
    """Share-weighted mean age of the June-2022 SOMA book, mid-year origination."""
    shares = COMPSHIFT["soma_book"]["asof_june_2022"]["vintage_year_shares"]
    tot = sum(shares.values())
    age = 0.0
    for year, w in shares.items():
        # mid-year origination convention, evaluated at 2022-06-30
        months = (2022 - int(year)) * 12 + (6 - 7)
        age += (w / tot) * max(months, 0)
    return age, tot


def main() -> int:
    out: dict = {
        "mode": "r33b_book_sched_decomposition",
        "spec": "specs/SPEC_R33B_book_sched_decomposition.md",
        "note": ("Accounting decomposition over committed artifacts; no "
                 "simulation, no estimation, no network."),
    }

    sa = FOLDIN["metrics"]["scheduled_amort_b"]
    cu = FOLDIN["metrics"]["curtailment_b"]
    B = float(CROSS["variants"]["recalibrated"]["empirical_trapped_b"])

    # --- effective holdings scale, two independent recoveries -------------
    h_sched = sa["total"] / (N_MONTHS * sa["smm_mean_pct"] / 100.0)
    h_curt = cu["total"] / (N_MONTHS * cu["smm_mean_pct"] / 100.0)
    h_mean = (h_sched + h_curt) / 2.0
    p1_rel = abs(h_sched - h_curt) / h_mean
    out["holdings_scale"] = {
        "h_from_scheduled_b": h_sched,
        "h_from_curtailment_b": h_curt,
        "h_mean_b": h_mean,
        "relative_gap": p1_rel,
    }

    # --- population (cross-design) scheduled leg --------------------------
    pop = REWEIGHT["variants"]["v1_recalibrated"]
    pop_wac = float(pop["sched_wac_pct"])
    pop_age = float(pop["sched_mean_age_mo"])
    sum_pop = sched_sum(pop_wac, pop_age)
    sum_pop_dollars = h_mean * sum_pop

    # --- primary basis: production cohort-weighted, term-aware ------------
    sum_book_dollars_primary = float(sa["total"])
    delta_primary = sum_book_dollars_primary - sum_pop_dollars

    # --- secondary basis: single-pool book annuity ------------------------
    book_wac = float(
        COMPSHIFT["soma_book"]["asof_june_2022"]["wac_face_weighted_pct"])
    book_age, share_sum = book_mean_age_months()
    sum_book_single = sched_sum(book_wac, book_age)
    delta_secondary = h_mean * (sum_book_single - sum_pop)

    out["scheduled_legs"] = {
        "population": {"wac_pct": pop_wac, "mean_age_mo": pop_age,
                       "smm_sum": sum_pop,
                       "annualized_pct": sum_pop / N_MONTHS * 1200,
                       "dollars_b": sum_pop_dollars},
        "book_primary_cohort_weighted": {
            "dollars_b": sum_book_dollars_primary,
            "annualized_pct": sa["annualized_pct"],
            "source": "manifest run-2026-07-04-15yr-foldin scheduled_amort_b"},
        "book_secondary_single_pool": {
            "wac_pct": book_wac, "mean_age_mo": book_age,
            "vintage_share_sum": share_sum,
            "smm_sum": sum_book_single,
            "annualized_pct": sum_book_single / N_MONTHS * 1200,
            "dollars_b": h_mean * sum_book_single},
    }

    # --- parity gates ------------------------------------------------------
    xd = CROSS["variants"]["recalibrated"]
    dist = SEEDS["distributions"]["A_joint.recalibrated"]
    p2 = (abs(xd["trapped_b"] - 453.5186133616682) < 1e-9
          and abs(xd["share_pct"] - 59.30299434493775) < 1e-9
          and abs(B - 764.7482532227002) < 1e-9
          and abs(dist["mean_pct"] - 60.20801984127922) < 1e-9
          and abs(dist["percentiles_pct"]["p2.5"] - 55.09710819371802) < 1e-9
          and abs(dist["min_pct"] - 53.75892234794354) < 1e-9)
    p3 = (abs(pop_wac - 3.3608263) < 1e-9
          and abs(pop_age - 22.2711) < 1e-4)
    p4 = sum_book_dollars_primary > sum_pop_dollars
    out["parity_gates"] = {
        "P1_holdings_scale_agreement": {"rel_gap": p1_rel, "tol": 0.02,
                                        "pass": bool(p1_rel < 0.02)},
        "P2_committed_quotes_replay": {"pass": bool(p2)},
        "P3_population_parameters_replay": {"pass": bool(p3)},
        "P4_direction_prediction": {
            "pass": bool(p4),
            "prediction": "book amortizes faster than the sample population"},
    }
    out["parity_gates_all_pass"] = bool(
        p1_rel < 0.02 and p2 and p3)  # P4 is a prediction, not a precondition

    # --- apply the wedge ---------------------------------------------------
    min_trapped = dist["min_pct"] / 100.0 * B
    legs = {
        "committed_draw": xd["trapped_b"],
        "fifty_seed_mean": dist["mean_trapped_b"],
        "fifty_seed_min": min_trapped,
        "fifty_seed_p2.5": dist["percentiles_pct"]["p2.5"] / 100.0 * B,
        "fifty_seed_p97.5": dist["percentiles_pct"]["p97.5"] / 100.0 * B,
    }
    applied = {}
    for k, trapped in legs.items():
        applied[k] = {
            "sample_basis_trapped_b": trapped,
            "sample_basis_share_pct": trapped / B * 100.0,
            "book_basis_trapped_b": trapped - delta_primary,
            "book_basis_share_pct": (trapped - delta_primary) / B * 100.0,
        }
    out["delta"] = {
        "primary_b": delta_primary,
        "primary_pp_of_benchmark": delta_primary / B * 100.0,
        "secondary_single_pool_b": delta_secondary,
        "secondary_pp_of_benchmark": delta_secondary / B * 100.0,
    }
    out["applied"] = applied

    # --- sensitivities -----------------------------------------------------
    ages = [c["population_mean_age_mo"] for c in SEEDS["per_cell"]]
    seed_span = {}
    for label, a in (("min_age", min(ages)), ("max_age", max(ages))):
        d = sum_book_dollars_primary - h_mean * sched_sum(pop_wac, a)
        seed_span[label] = {"age_mo": a, "delta_b": d}
    out["sensitivities"] = {
        "seed_population_age": seed_span,
        "book_age_pm3mo_secondary": {
            f"{lbl}": h_mean * (sched_sum(book_wac, book_age + off) - sum_pop)
            for lbl, off in (("minus3", -3), ("base", 0), ("plus3", 3))},
        "holdings_scale_bracket_delta_primary_b": {
            "at_h_sched": sum_book_dollars_primary - h_sched * sum_pop,
            "at_h_curt": sum_book_dollars_primary - h_curt * sum_pop,
        },
    }

    # --- pre-committed landing rule ---------------------------------------
    share_mean = applied["fifty_seed_mean"]["book_basis_share_pct"]
    share_min = applied["fifty_seed_min"]["book_basis_share_pct"]
    if not out["parity_gates_all_pass"]:
        branch, text = "T4", "NOT_PRICEABLE: a parity gate failed."
    elif share_min >= 50.0:
        branch, text = "T1", ("book-basis minimum still clears 50%: the undercut "
                              "verdict and the fifty-seed unanimity both survive.")
    elif share_mean >= 50.0:
        branch, text = "T2", ("book-basis mean clears 50% but the minimum does "
                              "not: the verdict survives, the unanimity claim "
                              "does not.")
    else:
        branch, text = "T3", ("book-basis mean falls below 50%: the undercut "
                              "verdict is basis-conditional. Eugene's call.")
    n_below = sum(
        1 for c in SEEDS["per_cell"]
        if c.get("leg") == "A_joint" and c.get("variant") == "recalibrated"
        and (c["trapped_b"] - delta_primary) / B * 100.0 < 50.0)
    n_cells = sum(1 for c in SEEDS["per_cell"]
                  if c.get("leg") == "A_joint" and c.get("variant") == "recalibrated")
    out["verdict"] = {
        "branch": branch,
        "text": text,
        "book_basis_mean_pct": share_mean,
        "book_basis_min_pct": share_min,
        "seeds_below_threshold": n_below,
        "seeds_scored": n_cells,
        "prediction_held": bool(p4),
    }

    path = ROOT / "abm" / "data" / "r33b_book_sched_results.json"
    path.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in
                      ("holdings_scale", "delta", "parity_gates", "verdict")},
                     indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
