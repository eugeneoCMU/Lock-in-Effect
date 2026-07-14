"""
Temporal moving-block bootstrap for Path A macro-coefficient uncertainty.

The stratum-cluster bootstrap (bootstrap_se.py) resamples strata and therefore
reproduces the identical friction series phi_t in every replication: phi_t is a
purely time-varying aggregate regressor (macro.calculate_dynamic_friction is
built from national inventory and sentiment series only), so cluster resampling
never perturbs the only dimension in which it varies. The binding dependence
for beta_f — and partly for burnout — is across strata within a month, i.e.
the ~36 serially correlated training months. This script resamples MONTHS in
moving blocks (default length 6, matching the paper's moving-block CPR
bootstrap), keeping each sampled month's full cross-section intact, and refits
the production spec per replication via bootstrap_se.fit_betas (same warm
start, same failure accounting, same rescale to production standardized
units), so the two schemes differ only in the resampled dimension.

Run:
    python3 hazard/temporal_block_bootstrap.py --reps 200 --block 6
"""

from __future__ import annotations

import argparse
import json
import time

import numpy as np
import pandas as pd
import polars as pl

from config import DATA_DIR, HAZARD_COEF_PATH, HOLDOUT_DATE, PANEL_PATH
from bootstrap_se import (
    BETA_NAMES,
    fit_betas,
    production_start_head,
    rescale_to_production_units,
)
from hazard_fit import enrich_panel_with_macro

RESULTS_PATH = DATA_DIR / "temporal_block_bootstrap.json"
DRAWS_CSV = DATA_DIR / "temporal_block_bootstrap_draws.csv"


def load_train() -> pd.DataFrame:
    panel = pl.read_parquet(PANEL_PATH)
    pdf = enrich_panel_with_macro(panel)
    pdf = pdf.dropna(subset=["rate_gap_bps", "exposure", "loan_age", "stratum_id"])
    pdf = pdf[pdf["exposure"] > 0]
    return pdf[pdf["period"] < HOLDOUT_DATE].copy()


def resample_months(train: pd.DataFrame, months: np.ndarray, block: int,
                    rng: np.random.Generator) -> pd.DataFrame:
    """Moving-block bootstrap over the ordered month index (no wrap)."""
    T = len(months)
    n_starts = T - block + 1
    picked: list = []
    while len(picked) < T:
        s = int(rng.integers(0, n_starts))
        picked.extend(months[s: s + block])
    picked = picked[:T]
    groups = dict(tuple(train.groupby("period")))
    chunks = [groups[m] for m in picked]
    return pd.concat(chunks, ignore_index=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--block", type=int, default=6)
    ap.add_argument("--alpha", type=float, default=1e-4)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    train = load_train()
    months = np.array(
        pd.to_datetime(pd.Series(train["period"].unique())).sort_values().tolist(),
        dtype=object,
    )
    print(f"Training cells: {len(train):,} | months: {len(months)} | "
          f"block: {args.block} | reps: {args.reps}")

    prod = json.load(open(HAZARD_COEF_PATH))
    seasonal = "month_effects" in prod  # spec v4 production artifact
    print(f"Design: seasonal={seasonal} "
          f"(production spec_version {prod.get('spec_version')})")
    point = fit_betas(train, args.alpha, seasonal=seasonal,
                      start_head=production_start_head(prod) if seasonal
                      else None)
    prod_scales = {k: point[k] for k in ["gap_std", "burn_std", "fric_std"]}
    print("Point refit (production standardized units): "
          + "  ".join(f"{n}={point[n]:+.4f}" for n in BETA_NAMES))

    rng = np.random.default_rng(args.seed)
    draws: dict[str, list[float]] = {n: [] for n in BETA_NAMES}
    n_failed = 0
    t0 = time.perf_counter()
    for i in range(args.reps):
        boot = resample_months(train, months, args.block, rng)
        try:
            b = fit_betas(boot, args.alpha, start_head=point["params_head"],
                          seasonal=seasonal)
        except Exception as exc:
            n_failed += 1
            print(f"  rep {i + 1}/{args.reps}: FAILED ({exc})")
            continue
        r = rescale_to_production_units(b, prod_scales)
        for n in BETA_NAMES:
            draws[n].append(r[n])
        pd.DataFrame(draws).to_csv(DRAWS_CSV, index=False)
        if (i + 1) % 10 == 0:
            el = time.perf_counter() - t0
            print(f"  rep {i + 1}/{args.reps} ({el:.0f}s elapsed)")

    out = {
        "scheme": "temporal_moving_block",
        "block_length_months": args.block,
        "n_months": int(len(months)),
        "n_reps": args.reps,
        "n_failed": n_failed,
        "ridge_alpha": args.alpha,
        "seed": args.seed,
        "spec_version": int(prod.get("spec_version", -1)),
        "seasonal_design": bool(seasonal),
        "production_scales": prod_scales,
        "point_production_units": {n: point[n] for n in BETA_NAMES},
        "note": ("Months resampled in moving blocks (cross-sections kept "
                 "intact); stratum-cluster scheme in hazard_bootstrap_se.json "
                 "cannot perturb the time-only friction regressor."),
    }
    stats = {}
    for n in BETA_NAMES:
        d = np.asarray(draws[n])
        stats[n] = {
            "se": float(d.std(ddof=1)),
            "mean": float(d.mean()),
            "median": float(np.median(d)),
            "ci_95_percentile": [float(np.percentile(d, 2.5)),
                                 float(np.percentile(d, 97.5))],
            "frac_le_0": float((d <= 0).mean()),
        }
    out["stats"] = stats
    RESULTS_PATH.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(stats, indent=2))
    print(f"Saved: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
