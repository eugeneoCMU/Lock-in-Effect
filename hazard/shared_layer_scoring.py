#!/usr/bin/env python3
"""
Shared-accounting-layer scoring of every estimator (July 2026 referee round).

The paper's §VII.F showed Path B at 97.9% under the ABM's shared
macro-accounting layer versus 107.0% under its standalone scorer, but never
re-scored Path A or the β₁=0 null on that layer, and never composed the two
quantified corrections (shared accounting; full-book SOMA coupon reweighting)
into one number. This script puts benchmark, Path A, Path B, the no-lock-in
null, and the full-book variants of both paths through the SAME layer —
fed_mbs_extension_risk.compute_metrics(use_hazard_microsim=True), exactly as
abm/hybrid_pipeline.py does — so every recovery figure sits on one accounting
basis, and reports the composed (shared accounting + full-book) figures.

Reads production caches directly (no load_or_build; raw Freddie files are
not required). Never overwrites a production cache: variant microsim runs
write to _sharedlayer_*.parquet temporaries and delete them.

Run:  cd hazard && python3 shared_layer_scoring.py
      → data/shared_layer_scoring_results.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

_REPO = Path(__file__).resolve().parents[1]
for p in (_REPO, _REPO / "abm", _REPO / "hazard"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import fed_mbs_extension_risk as fed  # noqa: E402

from config import LOAN_SAMPLE_PATH, MICROSIM_RESULTS_PATH, SIM_RESULTS_PATH  # noqa: E402
from extension_risk import score_extension_risk  # noqa: E402
from macro import (  # noqa: E402
    build_empirical_metrics,
    calculate_dynamic_friction,
    fetch_data as fetch_data_hazard,
    fetch_soma_mbs_monthly,
)
from microsim_engine import run_qt_microsim  # noqa: E402
from simulate import simulate_qt_window  # noqa: E402

DATA_DIR = Path(__file__).parent / "data"
NULL_CACHE = DATA_DIR / "microsim_results_pq0.0.parquet"
OUT = DATA_DIR / "shared_layer_scoring_results.json"

# §17.1 / §20 published value for the Path B hybrid U.S. leg — parity gate.
PUBLISHED_PATH_B_SHARED_PCT = 97.9


def _paths_from_combined_cache(cache: Path) -> dict[str, pd.DataFrame]:
    """Rebuild per-regime frames from a combined microsim results parquet."""
    combined = pd.read_parquet(cache)
    us = combined[["hazard_cpr_pct", "simulated_rolloff_b"]].copy()
    dk = pd.DataFrame(
        {
            "hazard_cpr_pct": combined["CPR_Danish"],
            "simulated_rolloff_b": combined["Danish_simulated_rolloff_b"],
        },
        index=combined.index,
    )
    return {"US": us, "Danish": dk}


def score_on_shared_layer(
    macro_abm: pd.DataFrame,
    soma: pd.Series,
    micro_paths: dict[str, pd.DataFrame],
) -> dict:
    """Run the ABM shared accounting layer over pre-computed CPR paths."""
    original = fed._load_hazard_microsim_paths
    fed._load_hazard_microsim_paths = lambda df: micro_paths
    try:
        m = fed.compute_metrics(
            macro_abm.copy(),
            soma_rolloff=soma,
            use_hazard_microsim=True,
            apply_settlement_lag_kernel=True,  # auto-disabled in microsim mode
        )
    finally:
        fed._load_hazard_microsim_paths = original
    hm = fed.export_headline_metrics(m)
    d = hm["dollars_b"]
    out = {
        "us_trapped_b": d["us_trapped"],
        "share_pct": d["share_explained_pct"],
        "empirical_trapped_b": d["empirical_trapped"],
        "danish_trapped_b": d["danish_trapped"],
        "institutional_gap_b": d["institutional_gap"],
    }
    if "curtailment_b" in hm:
        out["curtailment_netted_b"] = hm["curtailment_b"]["total"]
    if "scheduled_amort_b" in hm:
        out["sched_amort_layer_b"] = hm["scheduled_amort_b"]["total"]
    return out


def main() -> None:
    print("Fetching ABM macro + SOMA …")
    macro_abm = fed.fetch_data()
    soma = fed.fetch_soma_mbs_monthly()

    print("Fetching hazard macro + empirical benchmark (standalone scorer) …")
    macro_h = calculate_dynamic_friction(fetch_data_hazard())
    empirical = build_empirical_metrics(macro_h, soma_rolloff=fetch_soma_mbs_monthly())

    print("Fetching SOMA coupon cohorts (full-book weights) …")
    cohorts = fed.fetch_soma_mbs_cohorts()

    loans = pl.read_parquet(LOAN_SAMPLE_PATH)

    # --- Assemble per-estimator CPR paths ---------------------------------
    print("\nLoading cached production paths …")
    paths_b = _paths_from_combined_cache(MICROSIM_RESULTS_PATH)
    paths_null = _paths_from_combined_cache(NULL_CACHE)

    path_a_sim = pd.read_parquet(SIM_RESULTS_PATH)
    # Path A has no Danish counterfactual; the Danish leg below is borrowed
    # from Path B purely to satisfy the layer's two-regime interface — only
    # Path A's U.S.-side numbers are reported.
    paths_a = {"US": path_a_sim, "Danish": paths_b["Danish"]}

    print("Running Path B full-book microsim (both regimes) …")
    tmp_b = DATA_DIR / "_sharedlayer_pathb_fullbook.parquet"
    fb_results = run_qt_microsim(
        loan_sample=loans, macro=macro_h, output=tmp_b, soma_cohorts=cohorts
    )
    paths_b_fb = {"US": fb_results["US"], "Danish": fb_results["Danish"]}
    if tmp_b.exists():
        tmp_b.unlink()

    print("Running Path A full-book simulation …")
    tmp_a = DATA_DIR / "_sharedlayer_patha_fullbook.parquet"
    path_a_fb_sim = simulate_qt_window(soma_cohorts=cohorts, output=tmp_a)
    if tmp_a.exists():
        tmp_a.unlink()
    paths_a_fb = {"US": path_a_fb_sim, "Danish": paths_b_fb["Danish"]}

    estimators = {
        "path_b_central": paths_b,
        "no_lockin_null": paths_null,
        "path_a": paths_a,
        "path_b_fullbook_composed": paths_b_fb,
        "path_a_fullbook_composed": paths_a_fb,
    }

    # --- Standalone-scorer reference numbers ------------------------------
    standalone = {
        "path_b_central": score_extension_risk(pd.read_parquet(MICROSIM_RESULTS_PATH), empirical),
        "no_lockin_null": score_extension_risk(pd.read_parquet(NULL_CACHE), empirical),
        "path_a": score_extension_risk(path_a_sim, empirical),
        "path_b_fullbook_composed": score_extension_risk(fb_results["US"], empirical),
        "path_a_fullbook_composed": score_extension_risk(path_a_fb_sim, empirical),
    }

    # --- Shared-layer scoring ---------------------------------------------
    results = {}
    for name, micro_paths in estimators.items():
        print(f"\nShared layer: {name} …")
        results[name] = score_on_shared_layer(macro_abm, soma, micro_paths)
        results[name]["standalone_trapped_b"] = standalone[name]["hazard_trapped_b"]
        results[name]["standalone_share_pct"] = standalone[name]["share_explained_pct"]

    # Parity gate: Path B central must reproduce the published hybrid 97.9%.
    got = results["path_b_central"]["share_pct"]
    assert abs(got - PUBLISHED_PATH_B_SHARED_PCT) < 0.25, (
        f"Path B shared-layer share {got:.2f}% != published "
        f"{PUBLISHED_PATH_B_SHARED_PCT}% — layer drift, do not use."
    )

    payload = {
        "mode": "shared_layer_scoring",
        "layer": "fed_mbs_extension_risk.compute_metrics(use_hazard_microsim=True)",
        "published_parity": {"path_b_central_expected_pct": PUBLISHED_PATH_B_SHARED_PCT,
                             "path_b_central_got_pct": got},
        "results": results,
    }
    OUT.write_text(json.dumps(
        payload, indent=2,
        default=lambda x: float(x) if isinstance(x, (np.floating, np.integer)) else x,
    ) + "\n")

    print("\n" + "=" * 78)
    print(" SHARED ACCOUNTING LAYER — all estimators, one basis")
    print("=" * 78)
    print(f"  {'estimator':<28}{'standalone':>16}{'shared layer':>16}{'delta pp':>10}")
    for name, r in results.items():
        print(f"  {name:<28}"
              f"{r['standalone_trapped_b']:>8.1f}B {r['standalone_share_pct']:>5.1f}%"
              f"{r['us_trapped_b']:>9.1f}B {r['share_pct']:>5.1f}%"
              f"{r['share_pct'] - r['standalone_share_pct']:>+9.1f}")
    print(f"\n  Saved: {OUT}")


if __name__ == "__main__":
    main()
