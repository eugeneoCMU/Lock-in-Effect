#!/usr/bin/env python3
"""
Rate-input timing diagnosis for the Path B three-month offset (§V.C).

The corrected timing direction (v15) left the empirical-leads-simulation
offset at peak lag −3 as an "unexplained regularity". This script runs the
two diagnostics a five-month decision-lag reading calls for:

1. Input-timing cross-correlation: at which monthly lag does the empirical
   factor-month CPR respond to the PMMS rate input, versus the lag at which
   the simulated CPR responds? The difference is the model's effective
   decision-lag offset, measured directly against the input.

2. Shift scan: rerun Path B (U.S. regime, production sample, seed, and β₁)
   with the MORTGAGE30US input shifted by k ∈ {−3 … +3} months and rescore.
   k > 0 feeds the rate from k months LATER at each simulation month (a
   rate-input lead); k < 0 feeds the rate from k months EARLIER (a lag,
   the direction a borrower lock delay would imply). Reports which shift,
   if any, moves the peak cross-correlation lag to 0.

Never touches production caches; variant runs write to a temporary parquet.

Run:  cd hazard && python3 rate_timing_scan.py
      → data/rate_timing_scan_results.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

from config import LOAN_SAMPLE_PATH, MICROSIM_RESULTS_PATH, QT_END, QT_START
from extension_risk import score_extension_risk
from macro import (
    build_empirical_metrics,
    calculate_dynamic_friction,
    cpr_cross_correlation,
    fetch_data,
    fetch_soma_mbs_monthly,
)
from microsim_engine import run_qt_microsim

DATA_DIR = Path(__file__).parent / "data"
OUT = DATA_DIR / "rate_timing_scan_results.json"
TMP = DATA_DIR / "_rate_timing_tmp.parquet"

SHIFTS = [-3, -2, -1, 1, 2, 3]


def series_vs_rate_lags(series: pd.Series, rate: pd.Series, max_lag: int = 6) -> dict:
    """corr(series(t), rate(t−j)) for j in [−max_lag, max_lag] on the QT window."""
    out = {}
    for j in range(-max_lag, max_lag + 1):
        r = rate.shift(j)  # j > 0: rate from j months earlier
        mask = series.notna() & r.notna()
        if mask.sum() < 8:
            continue
        out[j] = float(np.corrcoef(series[mask], r[mask])[0, 1])
    return out


def main() -> None:
    print("Fetching macro + empirical benchmark …")
    macro = calculate_dynamic_friction(fetch_data())
    empirical = build_empirical_metrics(macro, soma_rolloff=fetch_soma_mbs_monthly())
    loans = pl.read_parquet(LOAN_SAMPLE_PATH)

    qt = empirical[(empirical.index >= QT_START) & (empirical.index < QT_END)]
    rate_qt = macro["MORTGAGE30US"].reindex(qt.index)
    prod_sim = pd.read_parquet(MICROSIM_RESULTS_PATH)["hazard_cpr_pct"].reindex(qt.index)

    print("Part 1: input-timing cross-correlations …")
    emp_vs_rate = series_vs_rate_lags(qt["Empirical_CPR_Pct"], rate_qt)
    sim_vs_rate = series_vs_rate_lags(prod_sim, rate_qt)
    fric_vs_emp = series_vs_rate_lags(
        qt["Empirical_CPR_Pct"], macro["Dynamic_Friction"].reindex(qt.index)
    )
    emp_peak = max(emp_vs_rate, key=lambda k: abs(emp_vs_rate[k]))
    sim_peak = max(sim_vs_rate, key=lambda k: abs(sim_vs_rate[k]))

    print(f"  empirical CPR responds to rate at lag {emp_peak:+d} "
          f"(r={emp_vs_rate[emp_peak]:+.3f})")
    print(f"  simulated CPR responds to rate at lag {sim_peak:+d} "
          f"(r={sim_vs_rate[sim_peak]:+.3f})")

    print("\nPart 2: shift scan (production sample, seed, β₁; U.S. regime) …")
    baseline = score_extension_risk(
        pd.read_parquet(MICROSIM_RESULTS_PATH), empirical
    )
    scan = {
        "0": {
            "peak_lag": baseline["best_lag"],
            "peak_r": baseline["peak_lag_r"],
            "r_lag0": baseline["cross_correlation"].get(0),
            "trapped_b": baseline["hazard_trapped_b"],
            "share_pct": baseline["share_explained_pct"],
        }
    }
    for k in SHIFTS:
        macro_k = macro.copy()
        macro_k["MORTGAGE30US"] = (
            macro["MORTGAGE30US"].shift(-k).ffill().bfill()
        )
        paths = run_qt_microsim(
            loan_sample=loans, macro=macro_k, regimes=("US",), output=TMP
        )
        r = score_extension_risk(paths["US"], empirical)
        scan[str(k)] = {
            "peak_lag": r["best_lag"],
            "peak_r": r["peak_lag_r"],
            "r_lag0": r["cross_correlation"].get(0),
            "trapped_b": r["hazard_trapped_b"],
            "share_pct": r["share_explained_pct"],
        }
        print(f"  shift {k:+d}: peak lag {r['best_lag']:+d} "
              f"(r={r['peak_lag_r']:+.3f})  r(lag0)={r['cross_correlation'].get(0):+.3f}  "
              f"trapped ${r['hazard_trapped_b']:.1f}B ({r['share_explained_pct']:.1f}%)")
    if TMP.exists():
        TMP.unlink()

    kills = [k for k, v in scan.items() if v["peak_lag"] == 0]
    payload = {
        "mode": "rate_timing_scan",
        "convention": {
            "part1": "corr(series(t), rate(t-j)); j>0 = series responds to older rates",
            "part2": "shift k>0 feeds rate(t+k) at month t (input lead); "
                     "k<0 feeds rate(t-|k|) (input lag)",
            "xcorr": "peak lag -3 = empirical leads simulation by 3 months",
        },
        "empirical_cpr_vs_rate": emp_vs_rate,
        "empirical_peak_rate_lag": emp_peak,
        "simulated_cpr_vs_rate": sim_vs_rate,
        "simulated_peak_rate_lag": sim_peak,
        "empirical_cpr_vs_friction": fric_vs_emp,
        "shift_scan": scan,
        "shifts_with_peak_lag_0": kills,
    }
    OUT.write_text(json.dumps(
        payload, indent=2,
        default=lambda x: float(x) if isinstance(x, (np.floating, np.integer)) else x,
    ) + "\n")
    print(f"\nShifts that move the peak to lag 0: {kills or 'none'}")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
