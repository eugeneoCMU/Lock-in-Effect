#!/usr/bin/env python3
"""
No-lock-in null run (TECHNICAL.md §12).

Runs Path B with the Rothstein lock-in elasticity disabled — p_q_shock_pct=0,
so rothstein_beta1(0) == 0 exactly and the rate-gap channel contributes
nothing. What remains is the PSA seasoning baseline, involuntary floor,
FICO/LTV covariates, cohort burnout, competing-risk default, and scheduled
amortization: the mechanical model. Scoring this against the $764.7B
benchmark quantifies how much of the "recovery" any amortization-respecting
model achieves with no lock-in mechanism at all, so lock-in claims can be
stated as the marginal contribution above this null.

Same loan sample and RNG seed as the production run; only β₁ differs.

Run:  cd hazard && python3 no_lockin_null.py
      → data/no_lockin_null_results.json  (+ cache microsim_results_pq0.0.parquet)
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import polars as pl

from config import LOAN_SAMPLE_PATH, MICROSIM_RESULTS_PATH
from extension_risk import score_extension_risk
from literature_hazard import rothstein_beta1
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly
from microsim_engine import run_qt_microsim

DATA_DIR = Path(__file__).parent / "data"
NULL_CACHE = DATA_DIR / "microsim_results_pq0.0.parquet"
RESULTS_JSON = DATA_DIR / "no_lockin_null_results.json"


def main() -> None:
    assert rothstein_beta1(0.0) == 0.0, "p_q shock 0 must give exactly beta1=0"

    print("Scoring empirical benchmark …")
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)

    # Use the committed production loan sample directly — the null must run
    # on the identical 75k sample, and load_or_build_loan_sample() re-verifies
    # raw Freddie files even when the parquet cache exists.
    if not LOAN_SAMPLE_PATH.exists():
        raise FileNotFoundError(
            f"{LOAN_SAMPLE_PATH} missing — build it via the production "
            "pipeline first (extension_risk.py --mode literature)."
        )
    loans = pl.read_parquet(LOAN_SAMPLE_PATH)

    t0 = time.perf_counter()
    if NULL_CACHE.exists():
        print(f"No-lock-in null: cached ({NULL_CACHE.name})")
        sim = pd.read_parquet(NULL_CACHE)
    else:
        print("No-lock-in null: running microsim with beta1 = 0 …")
        run_qt_microsim(loan_sample=loans, output=NULL_CACHE, p_q_shock_pct=0.0)
        sim = pd.read_parquet(NULL_CACHE)
    runtime_s = time.perf_counter() - t0

    null = score_extension_risk(sim, empirical)

    central = None
    if MICROSIM_RESULTS_PATH.exists():
        central = score_extension_risk(
            pd.read_parquet(MICROSIM_RESULTS_PATH), empirical
        )

    payload = {
        "mode": "no_lockin_null",
        "p_q_shock_pct": 0.0,
        "beta1": 0.0,
        "null_trapped_b": null["hazard_trapped_b"],
        "null_share_pct": null["share_explained_pct"],
        "null_cpr_r_lag0": null["cross_correlation"].get(0),
        "null_best_lag": null["best_lag"],
        "null_peak_lag_r": null["peak_lag_r"],
        "runtime_s": round(runtime_s, 1),
    }
    if central is not None:
        payload.update({
            "central_trapped_b": central["hazard_trapped_b"],
            "central_share_pct": central["share_explained_pct"],
            "lockin_marginal_b": (
                central["hazard_trapped_b"] - null["hazard_trapped_b"]
            ),
            "lockin_marginal_share_pp": (
                central["share_explained_pct"] - null["share_explained_pct"]
            ),
        })

    with open(RESULTS_JSON, "w") as f:
        json.dump(
            payload, f, indent=2,
            default=lambda x: float(x)
            if isinstance(x, (np.floating, np.integer)) else x,
        )
        f.write("\n")

    print(
        f"\nNo-lock-in null: trapped ${null['hazard_trapped_b']:.1f}B "
        f"({null['share_explained_pct']:.1f}% of benchmark)  "
        f"r(lag0)={null['cross_correlation'].get(0, float('nan')):+.3f}  "
        f"peak lag {null['best_lag']} r={null['peak_lag_r']:+.3f}"
    )
    if central is not None:
        print(
            f"Central (P_q 6.5%): ${central['hazard_trapped_b']:.1f}B "
            f"({central['share_explained_pct']:.1f}%)  →  lock-in marginal "
            f"${payload['lockin_marginal_b']:.1f}B "
            f"({payload['lockin_marginal_share_pp']:.1f}pp of benchmark)"
        )
    print(f"Results saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
