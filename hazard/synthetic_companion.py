#!/usr/bin/env python3
"""
2.1-2.3 — Symmetric companion test: fully synthetic population → hazard framework.

Runs both hazard paths on the independently-calibrated synthetic population
(synthetic_population.py) and assembles the {ABM, hazard} x {synthetic, real}
2x2 table (2.2), plus a calibration-source sensitivity sweep (2.3).

Interpretation note. Path B uses *literature* calibration (Rothstein/PSA — no
Freddie loan-level data), so "synthetic population + Path B" is the cleanest
fully-divorced test. Path A *learns* its coefficients from Freddie, so
"synthetic Path A" applies the real fitted survival structure (coefficients) to
synthetic covariates via forward simulation — the coefficients remain
Freddie-derived; only the population is synthetic. Novel synthetic strata fall
back to the reference-stratum fixed effect.
"""

from __future__ import annotations

import json

import pandas as pd
import polars as pl

from config import COUPON_STEP, QT_START, SIM_RESULTS_PATH
from extension_risk import score_extension_risk
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly
from microsim_engine import run_qt_microsim
from simulate import simulate_qt_window
from synthetic_population import CALIBRATIONS, build_synthetic_population, summary

DATA_DIR = SIM_RESULTS_PATH.parent
OUT = DATA_DIR / "synthetic_companion_results.json"

# Known cells of the 2x2 (from prior sections).
ABM_SYNTHETIC = {"trapped_b": 91.0, "share_pct": 11.9}          # production (§12)
ABM_REAL = {"trapped_b": 453.5, "share_pct": 59.3}              # cross-design (§15 Fix1, recalibrated)
HAZARD_REAL_B = {"trapped_b": 818.5, "share_pct": 107.0}        # Path B production (§16)


def _score_pathB(pop, macro, empirical, tag):
    out = DATA_DIR / f"_synth_{tag}.parquet"
    paths = run_qt_microsim(loan_sample=pop, macro=macro, regimes=("US",),
                            output=out)
    res = score_extension_risk(paths["US"], empirical)
    if out.exists():
        out.unlink()
    return {"trapped_b": res["hazard_trapped_b"],
            "share_pct": res["share_explained_pct"],
            "cpr_r_lag0": res["cross_correlation"].get(0)}


def _synth_panel(pop: pl.DataFrame) -> pl.DataFrame:
    """Aggregate synthetic loans into a minimal pre-QT cohort panel for Path A."""
    p = pop.to_pandas()
    p["coupon"] = (p["coupon"] / COUPON_STEP).round() * COUPON_STEP
    g = (p.groupby(["vintage", "coupon", "fico_bucket", "ltv_bucket"])
         .agg(exposure_upb=("balance", "sum"),
              orig_upb_sum=("orig_upb", "sum"),
              mean_loan_age=("loan_age", "mean"),
              loan_count=("loan_id", "count"))
         .reset_index())
    g["burnout"] = 0.0
    g["period"] = QT_START - pd.DateOffset(months=1)
    g["reporting_period"] = g["period"].dt.strftime("%Y%m")
    g["prepaid_upb"] = 0.0
    g["monthly_prepay_rate"] = 0.0
    g["mode_state"] = "Current"
    return pl.from_pandas(g)


def _score_pathA(pop, empirical, tag):
    """Forward-sim with REAL fitted coefficients on synthetic-cohort balances."""
    panel = _synth_panel(pop)
    out = DATA_DIR / f"_synthA_{tag}.parquet"
    sim = simulate_qt_window(panel=panel, output=out)
    res = score_extension_risk(sim, empirical)
    if out.exists():
        out.unlink()
    return {"trapped_b": res["hazard_trapped_b"],
            "share_pct": res["share_explained_pct"],
            "cpr_r_lag0": res["cross_correlation"].get(0)}


def main() -> None:
    macro = fetch_data()
    empirical = build_empirical_metrics(fetch_data(),
                                        soma_rolloff=fetch_soma_mbs_monthly())

    results = {}
    for cal in CALIBRATIONS:
        pop = build_synthetic_population(calibration=cal)
        print(f"\n[{cal}] {summary(pop)}")
        b = _score_pathB(pop, macro, empirical, cal)
        a = _score_pathA(pop, empirical, cal)
        results[cal] = {"path_b": b, "path_a": a}
        print(f"  Path B: ${b['trapped_b']:.1f}B ({b['share_pct']:.1f}%) "
              f"r={b['cpr_r_lag0']:+.3f}")
        print(f"  Path A: ${a['trapped_b']:.1f}B ({a['share_pct']:.1f}%) "
              f"r={a['cpr_r_lag0']:+.3f}  (real coefficients, synthetic pop)")

    base_b = results["baseline"]["path_b"]
    base_a = results["baseline"]["path_a"]
    payload = {
        "two_by_two": {
            "abm_synthetic": ABM_SYNTHETIC, "abm_real": ABM_REAL,
            "hazard_synthetic_pathB": base_b, "hazard_synthetic_pathA": base_a,
            "hazard_real_pathB": HAZARD_REAL_B,
        },
        "calibration_sensitivity": results,
    }
    OUT.write_text(json.dumps(payload, indent=2))

    print("\n" + "=" * 66)
    print(" 2x2 — {ABM, hazard} x {synthetic, real}   (share of benchmark)")
    print("=" * 66)
    print(f"  {'':16}{'synthetic pop':>18}{'real Freddie pop':>18}")
    print(f"  {'ABM':16}{ABM_SYNTHETIC['share_pct']:>17.1f}%{ABM_REAL['share_pct']:>17.1f}%")
    print(f"  {'hazard Path B':16}{base_b['share_pct']:>17.1f}%{HAZARD_REAL_B['share_pct']:>17.1f}%")
    print("-" * 66)
    print(" Calibration sensitivity (Path B share %):")
    for cal, r in results.items():
        print(f"   {cal:18}{r['path_b']['share_pct']:>8.1f}%   "
              f"(Path A {r['path_a']['share_pct']:.1f}%)")
    print(f"\n Saved: {OUT}")


if __name__ == "__main__":
    main()
