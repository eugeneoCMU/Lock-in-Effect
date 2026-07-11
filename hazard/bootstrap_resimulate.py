#!/usr/bin/env python3
"""
Refit-and-resimulate uncertainty for Path A's trapped-liquidity estimate.

The stratum block bootstrap (bootstrap_se.py, §21) produced 198 converged
refits of the production Poisson GLM; hazard_bootstrap_draws.csv holds their
macro coefficients (rate_gap_bps, burnout_orth, friction) rescaled to
production standardized units. This script closes the loop the paper priced
but did not run: for each converged replication, resimulate the QT window
with that replication's macro coefficients (age spline, intercept, and
stratum fixed effects held at the production fit — the draws carry only the
macro block, and FE resampling relabels strata so replication FEs do not map
back to production pools) and score trapped liquidity against the $764.7B
benchmark. The result is a percentile interval on the $915.0B / 119.7%
headline that reflects macro-coefficient uncertainty.

Run:  cd hazard && python3 bootstrap_resimulate.py
      → data/bootstrap_resimulate_results.json (+ per-rep CSV)
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

import simulate as sim_mod
from bootstrap_se import BETA_NAMES, BOOTSTRAP_DRAWS_CSV
from config import HAZARD_COEF_PATH, MARKOV_MATRIX_PATH, PANEL_PATH
from extension_risk import score_extension_risk
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly
from markov import load_transition_matrix

DATA_DIR = Path(__file__).parent / "data"
OUT_JSON = DATA_DIR / "bootstrap_resimulate_results.json"
OUT_CSV = DATA_DIR / "bootstrap_resimulate_draws.csv"
TMP_SIM = DATA_DIR / "_bootstrap_resim_tmp.parquet"


def main() -> None:
    print("Fetching macro + empirical benchmark (once) …")
    macro_raw = fetch_data()
    empirical = build_empirical_metrics(macro_raw, soma_rolloff=fetch_soma_mbs_monthly())

    # simulate_qt_window re-fetches FRED on every call; patch its module-level
    # fetch_data so 198 replications reuse the single fetch above.
    sim_mod.fetch_data = lambda: macro_raw

    panel = pl.read_parquet(PANEL_PATH)
    trans = load_transition_matrix(MARKOV_MATRIX_PATH)
    prod = json.load(open(HAZARD_COEF_PATH))
    prod_coefs = dict(prod["coefficients"])

    draws = pd.read_csv(BOOTSTRAP_DRAWS_CSV)
    assert list(draws.columns) == BETA_NAMES, draws.columns
    n = len(draws)
    print(f"Resimulating {n} bootstrap replications "
          f"(macro betas swapped; FE/spline at production) …")

    rows = []
    t0 = time.perf_counter()
    for i, rep in draws.iterrows():
        coefs = dict(prod_coefs)
        for name in BETA_NAMES:
            coefs[name] = float(rep[name])
        sim = sim_mod.simulate_qt_window(
            panel=panel, coefs=coefs, trans=trans, output=TMP_SIM
        )
        r = score_extension_risk(sim, empirical)
        rows.append({
            "rep": i,
            **{name: float(rep[name]) for name in BETA_NAMES},
            "trapped_b": r["hazard_trapped_b"],
            "share_pct": r["share_explained_pct"],
            "cpr_r_lag0": r["cross_correlation"].get(0),
        })
        if (i + 1) % 10 == 0 or i == 0:
            el = time.perf_counter() - t0
            pd.DataFrame(rows).to_csv(OUT_CSV, index=False)  # checkpoint
            print(f"  rep {i + 1}/{n}: trapped ${r['hazard_trapped_b']:.1f}B "
                  f"({el / (i + 1):.1f}s/rep, {el:.0f}s elapsed)")

    if TMP_SIM.exists():
        TMP_SIM.unlink()

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    trapped = df["trapped_b"].to_numpy()
    share = df["share_pct"].to_numpy()
    point_sim = sim_mod.simulate_qt_window(
        panel=panel, coefs=prod_coefs, trans=trans, output=TMP_SIM
    )
    if TMP_SIM.exists():
        TMP_SIM.unlink()
    point = score_extension_risk(point_sim, empirical)

    payload = {
        "mode": "bootstrap_resimulate",
        "n_reps": int(n),
        "held_at_production": ["const", "age_spline", "stratum_fe"],
        "resampled": BETA_NAMES,
        "point_trapped_b": point["hazard_trapped_b"],
        "point_share_pct": point["share_explained_pct"],
        "trapped_b": {
            "mean": float(trapped.mean()),
            "se": float(trapped.std(ddof=1)),
            "ci_95": [float(np.percentile(trapped, 2.5)),
                      float(np.percentile(trapped, 97.5))],
            "median": float(np.percentile(trapped, 50)),
        },
        "share_pct": {
            "mean": float(share.mean()),
            "se": float(share.std(ddof=1)),
            "ci_95": [float(np.percentile(share, 2.5)),
                      float(np.percentile(share, 97.5))],
            "median": float(np.percentile(share, 50)),
        },
        "frac_above_benchmark": float(np.mean(share > 100.0)),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")

    print("\n" + "=" * 66)
    print(" PATH A REFIT-AND-RESIMULATE — trapped-liquidity interval")
    print("=" * 66)
    print(f"  Point:   ${payload['point_trapped_b']:.1f}B "
          f"({payload['point_share_pct']:.1f}%)")
    print(f"  Mean:    ${payload['trapped_b']['mean']:.1f}B  "
          f"SE ${payload['trapped_b']['se']:.1f}B")
    print(f"  95% CI:  [${payload['trapped_b']['ci_95'][0]:.1f}B, "
          f"${payload['trapped_b']['ci_95'][1]:.1f}B]  "
          f"([{payload['share_pct']['ci_95'][0]:.1f}%, "
          f"{payload['share_pct']['ci_95'][1]:.1f}%])")
    print(f"  Share of draws above benchmark: "
          f"{payload['frac_above_benchmark'] * 100:.1f}%")
    print(f"  Saved: {OUT_JSON}")


if __name__ == "__main__":
    main()
