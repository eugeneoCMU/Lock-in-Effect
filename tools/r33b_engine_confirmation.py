"""R33-B part 2: ask the engine directly whether the book-sched wedge is right.

Implements `specs/SPEC_R33B_engine_confirmation.md`, committed before this ran.
Two legs through `fed.compute_metrics`, identical except the scheduled series:
the population one the cross-design uses today (PARITY), and the book's own
cohort-weighted, term-aware series rebuilt from the pinned 2026-07-01 cohort
book (BOOK).

Writes abm/data/r33b_engine_confirmation_results.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "abm"))

import fed_mbs_extension_risk as fed  # noqa: E402
import abm_lockin_simulation as abm  # noqa: E402
from cross_design_test import (  # noqa: E402
    _population_sched_series,
    _surface_csv,
    load_freddie_structural_sample,
)

COMMITTED = {
    "trapped_b": 453.5186133616682,
    "share_pct": 59.30299434493775,
    "empirical_trapped_b": 764.7482532227002,
    "mobility_scale": 36085.9375,
}
DELTA_DECOMP = 63.8803470149806
G0_TOL = 1e-6


def book_sched_series(index) -> pd.Series:
    cohorts = fed.load_pinned_cohorts("2026-07-01")
    s = pd.Series(0.0, index=index)
    for c in cohorts:
        s = s + c["weight"] * fed.scheduled_amortization_series(
            index, coupon=c["coupon"], origin=c["origin_date"],
            term=c["term_months"])
    return s


def score(df0, surface, soma_rolloff, sched) -> dict:
    df = fed.compute_metrics(
        df0.copy(), surface=surface, soma_rolloff=soma_rolloff,
        use_burnout=False, apply_settlement_lag_kernel=True,
        sched_smm_override=sched)
    m = fed.export_headline_metrics(df)
    d = m["dollars_b"]
    return {
        "trapped_b": d["us_trapped"],
        "share_pct": d["share_explained_pct"],
        "empirical_trapped_b": d["empirical_trapped"],
        "us_cpr_mean_pct": m["cpr_pct"]["us_abm"]["mean"],
        "empirical_cpr_mean_pct": m["cpr_pct"]["empirical"]["mean"],
        "sched_annualized_pct": m["scheduled_amort_b"]["annualized_pct"],
        "sched_total_b": m["scheduled_amort_b"]["total"],
    }


def main() -> int:
    out = {"mode": "r33b_engine_confirmation",
           "spec": "specs/SPEC_R33B_engine_confirmation.md"}

    loans = load_freddie_structural_sample(abm.N_HOUSEHOLDS)
    df0 = fed.fetch_data()
    soma_rolloff = fed.fetch_soma_mbs_monthly()
    surface = fed.load_cpr_surface(_surface_csv("recalibrated"))

    sched_pop = _population_sched_series(df0.index, loans)
    sched_book = book_sched_series(df0.index)

    parity = score(df0, surface, soma_rolloff, sched_pop)
    book = score(df0, surface, soma_rolloff, sched_book)
    out["legs"] = {"parity_population_sched": parity, "book_sched": book}

    g0 = {
        "trapped_b": {"want": COMMITTED["trapped_b"], "got": parity["trapped_b"],
                      "diff": parity["trapped_b"] - COMMITTED["trapped_b"]},
        "share_pct": {"want": COMMITTED["share_pct"], "got": parity["share_pct"],
                      "diff": parity["share_pct"] - COMMITTED["share_pct"]},
        "empirical_trapped_b": {
            "want": COMMITTED["empirical_trapped_b"],
            "got": parity["empirical_trapped_b"],
            "diff": parity["empirical_trapped_b"]
            - COMMITTED["empirical_trapped_b"]},
    }
    for v in g0.values():
        v["pass"] = abs(v["diff"]) <= G0_TOL
    g0_pass = all(v["pass"] for v in g0.values())
    out["G0_parity"] = {"tolerance": G0_TOL, "checks": g0, "pass": g0_pass}

    delta_engine = parity["trapped_b"] - book["trapped_b"]
    gap = abs(delta_engine - DELTA_DECOMP)
    B = COMMITTED["empirical_trapped_b"]
    out["wedge"] = {
        "delta_engine_b": delta_engine,
        "delta_decomposition_b": DELTA_DECOMP,
        "abs_gap_b": gap,
        "delta_engine_pp": delta_engine / B * 100.0,
        "book_share_pct_committed_draw": book["share_pct"],
        "direction_prediction_held": bool(delta_engine > 0),
    }

    # T2 branch as the decomposition defined it, recomputed on the engine wedge
    seeds = json.loads((ROOT / "abm" / "data"
                        / "cross_design_seeds_results.json").read_text())
    dist = seeds["distributions"]["A_joint.recalibrated"]
    mean_book = (dist["mean_trapped_b"] - delta_engine) / B * 100.0
    min_book = (dist["min_pct"] / 100.0 * B - delta_engine) / B * 100.0
    cells = [c for c in seeds["per_cell"]
             if c.get("leg") == "A_joint" and c.get("variant") == "recalibrated"]
    n_below = sum(1 for c in cells
                  if (c["trapped_b"] - delta_engine) / B * 100.0 < 50.0)
    branch_same = (mean_book >= 50.0 > min_book)
    out["t2_on_engine_wedge"] = {
        "book_mean_pct": mean_book, "book_min_pct": min_book,
        "seeds_below": n_below, "seeds_scored": len(cells),
        "branch_unchanged": bool(branch_same)}

    if not g0_pass:
        branch, text = "E4", ("INCONCLUSIVE: G0 parity failed; live FRED does "
                              "not reproduce the frozen macro frame.")
    elif gap <= 3.0:
        branch, text = "E1", ("Decomposition confirmed by the engine within "
                              "$3bn; landed numbers stand.")
    elif gap <= 10.0 and branch_same:
        branch, text = "E2", ("Direction and branch confirmed, magnitude "
                              "imprecise; restate on the engine figure.")
    else:
        branch, text = "E3", ("Decomposition materially wrong; retract and "
                              "re-land on the engine result.")
    out["verdict"] = {"branch": branch, "text": text}

    path = ROOT / "abm" / "data" / "r33b_engine_confirmation_results.json"
    path.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in
                      ("G0_parity", "wedge", "t2_on_engine_wedge", "verdict")},
                     indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
