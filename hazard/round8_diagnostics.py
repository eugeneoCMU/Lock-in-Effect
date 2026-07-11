#!/usr/bin/env python3
"""
Round-8 referee diagnostics (no refits, no production-cache writes):

1. Moving-block bootstrap block-length sensitivity for the four 95%
   intervals printed in Table 4's note (ABM lag-0, Path A lag-0, Path B
   lag-0 and peak lag −3), at block lengths 4/6/8. Design identified by
   parity reconstruction: CIRCULAR moving-block resampling of the joint
   (empirical, simulated) monthly series, correlations recomputed on the
   resampled series at fixed lags via macro.cpr_cross_correlation, 4,000
   replications. Block 6 must reproduce every printed interval to within
   seed noise (±0.02) — asserted below.
2. Per-lag overlap counts and i.i.d. zero bands 1.96/sqrt(n−|k|) for lagged
   cross-correlation statements (a lag-3 coefficient has 39 overlapping
   observations, not 42).
3. Panel accounting recount: tab:panel printed holdout 6,076;
   hazard_coefficients.json says 6,077 — adjudicated from the panel itself.

Run:  cd hazard && python3 round8_diagnostics.py
      → data/round8_diagnostics.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

from config import HOLDOUT_DATE, MICROSIM_RESULTS_PATH, PANEL_PATH, QT_END, QT_START, SIM_RESULTS_PATH
from hazard_fit import enrich_panel_with_macro
from macro import (
    build_empirical_metrics,
    calculate_dynamic_friction,
    cpr_cross_correlation,
    fetch_data,
    fetch_soma_mbs_monthly,
)

DATA_DIR = Path(__file__).parent / "data"
OUT = DATA_DIR / "round8_diagnostics.json"
ABM_METRICS = (Path(__file__).parent.parent / "abm" / "data" / "runs"
               / "run-2026-07-04-15yr-foldin" / "metrics_monthly.csv")

# Printed in Table 4's note (v15r2), block length 6.
PRINTED = {
    "abm_lag0": (-0.60, 0.04),
    "path_a_lag0": (-0.68, -0.02),
    "path_b_lag0": (-0.13, 0.44),
    "path_b_peak_m3": (-0.21, 0.49),
}


def series_mbb(e: np.ndarray, p: np.ndarray, block: int, lag: int,
               reps: int = 4000, seed: int = 42) -> tuple[float, float]:
    """Circular MBB of the joint series; r at fixed `lag` per replication."""
    rng = np.random.default_rng(seed)
    n = len(e)
    nb = int(np.ceil(n / block))
    draws = []
    for _ in range(reps):
        pos = []
        for s in rng.integers(0, n, size=nb):
            pos.extend(((s + np.arange(block)) % n).tolist())
        pos = np.array(pos[:n])
        x = cpr_cross_correlation(pd.Series(e[pos]), pd.Series(p[pos]), max_lag=3)
        if lag in x:
            draws.append(x[lag])
    d = np.asarray(draws)
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def main() -> None:
    out: dict = {}

    print("Loading series …")
    macro = calculate_dynamic_friction(fetch_data())
    empirical = build_empirical_metrics(macro, soma_rolloff=fetch_soma_mbs_monthly())
    qt = empirical[(empirical.index >= QT_START) & (empirical.index < QT_END)]
    e_hz = qt["Empirical_CPR_Pct"].to_numpy(dtype=float)

    p_b = pd.read_parquet(MICROSIM_RESULTS_PATH)["hazard_cpr_pct"].reindex(qt.index).to_numpy(float)
    p_a = pd.read_parquet(SIM_RESULTS_PATH)["hazard_cpr_pct"].to_numpy(float)

    abm = pd.read_csv(ABM_METRICS, index_col=0, parse_dates=True)
    e_abm = abm["Empirical_CPR_Pct"].to_numpy(float)
    p_abm = abm["US_CPR_Pct"].to_numpy(float)

    cases = {
        "abm_lag0": (e_abm, p_abm, 0),
        "path_a_lag0": (e_hz, p_a, 0),
        "path_b_lag0": (e_hz, p_b, 0),
        "path_b_peak_m3": (e_hz, p_b, -3),
    }

    sens = {}
    for name, (e, p, lag) in cases.items():
        x = cpr_cross_correlation(pd.Series(e), pd.Series(p), max_lag=3)
        row = {"r_point": round(x[lag], 4), "lag": lag, "n": int(len(e))}
        for block in (4, 6, 8):
            lo, hi = series_mbb(e, p, block, lag)
            row[f"block{block}"] = [round(lo, 3), round(hi, 3)]
        sens[name] = row
        print(name, row)

    parity = {}
    for name, (plo, phi) in PRINTED.items():
        got = sens[name]["block6"]
        ok = abs(got[0] - plo) <= 0.02 and abs(got[1] - phi) <= 0.02
        parity[name] = {"printed": [plo, phi], "recomputed_block6": got,
                        "within_0.02": bool(ok)}
        print(f"parity {name}: printed {plo, phi} got {got} ok={ok}")
        assert ok, f"block-6 parity failed for {name}"

    zero_crossing = {
        name: {f"block{b}": bool(row[f"block{b}"][0] < 0 < row[f"block{b}"][1])
               for b in (4, 6, 8)}
        for name, row in sens.items()
    }
    out["moving_block_sensitivity"] = sens
    out["parity_block6"] = parity
    out["interval_contains_zero"] = zero_crossing
    out["design_note"] = (
        "Circular moving-block bootstrap of the joint monthly series, 4,000 "
        "replications, correlation recomputed at the FIXED printed lag per "
        "replication; identified by exact reconstruction of all four printed "
        "block-6 intervals. Seed noise on endpoints is about ±0.015.")

    bands = {}
    n = int(len(e_hz))
    for k in range(-3, 4):
        n_eff = n - abs(k)
        bands[str(k)] = {"n_overlap": n_eff,
                         "iid_band": round(1.96 / np.sqrt(n_eff), 4)}
    out["per_lag_zero_bands"] = bands
    out["per_lag_note"] = (
        "n=42 QT months; a lag-k levels cross-correlation uses n-|k| "
        "overlapping pairs, so its i.i.d. reference band is 1.96/sqrt(n-|k|): "
        "0.3024 at lag 0, 0.3061 at |k|=1, 0.3099 at |k|=2, 0.3139 at |k|=3. "
        "First-difference statistics lose one further observation (n=41 at "
        "lag 0). Detrended-levels statistics keep n=42 at lag 0.")

    panel = pl.read_parquet(PANEL_PATH)
    pdf = enrich_panel_with_macro(panel)
    pdf = pdf.dropna(subset=["rate_gap_bps", "exposure", "loan_age", "stratum_id"])
    pdf = pdf[pdf["exposure"] > 0]
    out["panel_recount"] = {
        "train_cells": int((pdf["period"] < HOLDOUT_DATE).sum()),
        "holdout_cells": int((pdf["period"] >= HOLDOUT_DATE).sum()),
        "printed_tab_panel": {"train": 10176, "holdout": 6076},
        "artifact_hazard_coefficients": {"train": 10176, "holdout": 6077},
    }
    print("panel recount:", out["panel_recount"])

    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
