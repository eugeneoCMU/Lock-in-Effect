#!/usr/bin/env python3
"""
Permutation (null-model) test for Path B: does the ~107% benchmark recovery
depend on the REAL joint structure of the loan pool's covariates, or only on
their marginals?

Procedure (per replicate)
-------------------------
Independently permute each of the stratum-defining covariate axes across the
75k loan index, preserving every marginal but destroying cross-column
correlation, then run the Path B microsim otherwise unchanged and record the
same three diagnostics reported for the real-data run.

The four named axes are vintage, coupon, FICO, LTV. Two implementation notes:

1. Path B's `stratum_id` keys on {vintage, coupon-bucket, fico_bucket}; the LTV
   bucket is carried but not part of the stratum key. LTV still enters the
   hazard continuously via `ltv_z`, so we permute it anyway — it is a genuine
   covariate axis even though it does not change stratum membership.

2. `loan_age` and `vintage` are two encodings of one underlying quantity
   (origination time: loan_age ≈ months from origination to the fixed pre-QT
   snapshot). We therefore permute them together as a single origination-time
   block rather than with two independent permutations, which would fabricate
   internally contradictory loans (e.g. vintage 2021 with a 100-month age) and
   inject h0 noise that is not "cross-covariate structure." This still fully
   destroys the correlation between origination-time and {coupon, FICO, LTV},
   which is the target of the test. It is NOT the block shuffle the method
   warns against (reordering intact rows preserves all correlations); the four
   distinct axes each still receive an independent permutation.

Everything else about the microsim is held fixed: same hazard functional form,
same β₁ (Rothstein 6.5% midpoint), same competing-risks logic, same random
draw seed (RNG_SEED). The only thing that varies across replicates is the
permutation, so the spread of outcomes is a pure permutation null distribution.

Outputs
-------
  data/permutation_test_results.csv    one row per replicate (checkpointed)
  data/permutation_test_summary.json   null distribution + real-vs-null stats

Usage
-----
    python3 permutation_test.py --n 100          # full run
    python3 permutation_test.py --n 2 --smoke     # quick smoke test
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

from config import (
    COUPON_STEP,
    DATA_DIR,
    LOAN_SAMPLE_PATH,
    LTV_THRESHOLD,
    RNG_SEED,
    ROTHSTEIN_Q_DECLINE_MID,
)
from extension_risk import score_extension_risk
from loan_sample import load_or_build_loan_sample
from macro import (
    build_empirical_metrics,
    calculate_dynamic_friction,
    fetch_data,
    fetch_soma_mbs_monthly,
)
from microsim_engine import run_qt_microsim

_SCRATCH = DATA_DIR / "_perm_microsim_tmp.parquet"

P_Q_MID_PCT = ROTHSTEIN_Q_DECLINE_MID * 100  # 6.5

# Permutation modes:
#   independent      — main test: each of the 4 axes gets its own permutation,
#                      vintage+loan_age blocked as one origination-time axis.
#   block            — control: shuffle intact rows (one permutation, all
#                      columns move together). Preserves ALL covariate
#                      correlations; only the RNG→loan position alignment
#                      changes, so its spread is the pure draw-noise floor.
#   age-independent  — control: like `independent` but loan_age gets a 5th
#                      independent permutation instead of blocking with vintage,
#                      to confirm the blocking choice does not drive the result.
MODES = ("independent", "block", "age-independent")


def _paths_for_mode(mode: str) -> tuple[Path, Path]:
    tag = "" if mode == "independent" else f"_{mode.replace('-', '')}"
    return (DATA_DIR / f"permutation_test{tag}_results.csv",
            DATA_DIR / f"permutation_test{tag}_summary.json")


# ---------------------------------------------------------------------------
# Covariate bucketing — must match ingest.py / loan_sample.py exactly so the
# recomputed stratum_id reproduces the real pipeline's convention.
# ---------------------------------------------------------------------------
def _fico_bucket(fico: np.ndarray) -> np.ndarray:
    return np.where(fico < 680, "<680", np.where(fico < 740, "680-740", "740+"))


def _ltv_bucket(ltv: np.ndarray) -> np.ndarray:
    return np.where(ltv <= LTV_THRESHOLD, "≤80", ">80")


def _stratum_id(vintage: np.ndarray, coupon: np.ndarray,
                fico_bucket: np.ndarray) -> np.ndarray:
    """vintage_<bucketed coupon bps>_<fico bucket>; matches _stratum_id_expr()."""
    coupon_bp = (np.round(coupon / COUPON_STEP) * COUPON_STEP * 10000)
    coupon_bp = np.round(coupon_bp).astype(np.int64)
    return np.array([f"{int(v)}_{c}_{fb}"
                     for v, c, fb in zip(vintage, coupon_bp, fico_bucket)])


def _verify_stratum_recipe(base: pd.DataFrame) -> None:
    """Fail loudly if our stratum reconstruction diverges from the stored ids."""
    recon = _stratum_id(base["vintage"].to_numpy(),
                        base["coupon"].to_numpy(),
                        base["fico_bucket"].to_numpy())
    n_match = int((recon == base["stratum_id"].to_numpy()).sum())
    if n_match != len(base):
        raise AssertionError(
            f"stratum_id recipe mismatch: {n_match}/{len(base)} — refusing to "
            "run a permutation test on a mis-specified stratum key."
        )


def permute_sample(base: pd.DataFrame, rng: np.random.Generator,
                   mode: str = "independent") -> pl.DataFrame:
    """Per-axis permutation; recompute buckets + stratum_id. See MODES."""
    n = len(base)

    if mode == "block":
        # Shuffle intact rows: all columns move together, so every covariate
        # correlation is preserved. Only RNG→position alignment changes.
        pi = rng.permutation(n)
        return pl.from_pandas(base.iloc[pi].reset_index(drop=True))

    pi_orig = rng.permutation(n)   # origination-time: vintage (+ loan_age if blocked)
    pi_coupon = rng.permutation(n)
    pi_fico = rng.permutation(n)
    pi_ltv = rng.permutation(n)
    pi_age = pi_orig if mode == "independent" else rng.permutation(n)

    out = base.copy()
    out["vintage"] = base["vintage"].to_numpy()[pi_orig]
    out["loan_age"] = base["loan_age"].to_numpy()[pi_age]
    out["coupon"] = base["coupon"].to_numpy()[pi_coupon]
    out["fico"] = base["fico"].to_numpy()[pi_fico]
    out["orig_ltv"] = base["orig_ltv"].to_numpy()[pi_ltv]

    out["fico_bucket"] = _fico_bucket(out["fico"].to_numpy())
    out["ltv_bucket"] = _ltv_bucket(out["orig_ltv"].to_numpy())
    out["stratum_id"] = _stratum_id(out["vintage"].to_numpy(),
                                    out["coupon"].to_numpy(),
                                    out["fico_bucket"].to_numpy())
    return pl.from_pandas(out)


def _run_once(sample: pl.DataFrame, macro: pd.DataFrame,
              empirical: pd.DataFrame) -> dict:
    """One microsim + scoring pass (US regime only; the 3 diagnostics are US-side)."""
    paths = run_qt_microsim(
        loan_sample=sample,
        macro=macro,
        regimes=("US",),
        seed=RNG_SEED,
        output=_SCRATCH,
        p_q_shock_pct=P_Q_MID_PCT,
    )
    res = score_extension_risk(paths["US"], empirical)
    xcorr = res["cross_correlation"]
    return {
        "trapped_b": res["hazard_trapped_b"],
        "share_pct": res["share_explained_pct"],
        "cpr_r_lag0": xcorr.get(0),
        "peak_lag": res["best_lag"],
        "peak_lag_r": res["peak_lag_r"],
        "n_strata": int(sample["stratum_id"].n_unique()),
    }


def _summarize(real: dict, perms: list[dict]) -> dict:
    def col(key):
        return np.array([p[key] for p in perms], dtype=float)

    summary = {"n_permutations": len(perms), "real": real, "null": {}}
    for key in ("trapped_b", "share_pct", "cpr_r_lag0"):
        vals = col(key)
        r = real[key]
        # Two-sided empirical p: fraction of |null − nullmean| >= |real − nullmean|.
        mu, sd = float(vals.mean()), float(vals.std(ddof=1))
        centered_real = abs(r - mu)
        p_two = float((np.abs(vals - mu) >= centered_real).mean())
        # One-sided: fraction of null at least as extreme (high) as real.
        p_ge = float((vals >= r).mean())
        summary["null"][key] = {
            "mean": mu,
            "std": sd,
            "min": float(vals.min()),
            "max": float(vals.max()),
            "p05": float(np.percentile(vals, 5)),
            "p50": float(np.percentile(vals, 50)),
            "p95": float(np.percentile(vals, 95)),
            "real": r,
            "real_z": (r - mu) / sd if sd > 0 else float("nan"),
            "real_percentile": float((vals < r).mean() * 100),
            "p_two_sided": p_two,
            "p_real_ge_null": p_ge,
        }
    # Peak lag is categorical: report the distribution.
    lags = [p["peak_lag"] for p in perms]
    uniq, counts = np.unique(lags, return_counts=True)
    summary["null"]["peak_lag_distribution"] = {
        int(k): int(v) for k, v in zip(uniq, counts)
    }
    summary["real_peak_lag"] = real["peak_lag"]
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=100,
                        help="number of permutation replicates")
    parser.add_argument("--seed", type=int, default=12345,
                        help="master seed for the permutation stream")
    parser.add_argument("--smoke", action="store_true",
                        help="quick smoke run (implies small --n)")
    parser.add_argument("--mode", choices=MODES, default="independent",
                        help="permutation mode (see module docstring)")
    args = parser.parse_args()
    n_perm = 2 if args.smoke else args.n
    results_csv, summary_json = _paths_for_mode(args.mode)

    print("Loading real loan sample …")
    base_pl = load_or_build_loan_sample()
    base = base_pl.to_pandas()
    _verify_stratum_recipe(base)
    print(f"  {len(base):,} loans, {base['stratum_id'].nunique()} strata")

    print("Fetching macro + empirical benchmark (once) …")
    macro = calculate_dynamic_friction(fetch_data())
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(fetch_data(), soma_rolloff=soma)

    print("\nReal-data baseline through the same harness …")
    t0 = time.perf_counter()
    real = _run_once(base_pl, macro, empirical)
    real["replicate"] = "real"
    real["runtime_s"] = round(time.perf_counter() - t0, 1)
    print(f"  real: ${real['trapped_b']:.1f}B ({real['share_pct']:.1f}%)  "
          f"r(lag0)={real['cpr_r_lag0']:+.3f}  peak lag {real['peak_lag']}  "
          f"[{real['runtime_s']}s]")

    real["mode"] = args.mode
    rows = [real]
    pd.DataFrame(rows).to_csv(results_csv, index=False)

    rng = np.random.default_rng(args.seed)
    perms = []
    for i in range(n_perm):
        t0 = time.perf_counter()
        perm_sample = permute_sample(base, rng, mode=args.mode)
        r = _run_once(perm_sample, macro, empirical)
        r["replicate"] = i
        r["mode"] = args.mode
        r["runtime_s"] = round(time.perf_counter() - t0, 1)
        perms.append(r)
        rows.append(r)
        pd.DataFrame(rows).to_csv(results_csv, index=False)  # checkpoint
        print(f"  perm {i + 1:>3}/{n_perm}: ${r['trapped_b']:.1f}B "
              f"({r['share_pct']:.1f}%)  r(lag0)={r['cpr_r_lag0']:+.3f}  "
              f"peak {r['peak_lag']}  [{r['runtime_s']}s]")

    summary = _summarize(real, perms)
    summary["mode"] = args.mode
    with open(summary_json, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 68)
    print(f" PERMUTATION TEST [{args.mode}] — Path B, real vs. null")
    print("=" * 68)
    for key, label in (("trapped_b", "Trapped $B"),
                       ("share_pct", "Share %"),
                       ("cpr_r_lag0", "CPR r(lag0)")):
        s = summary["null"][key]
        print(f" {label:<12}: real {s['real']:.3f}  |  null "
              f"{s['mean']:.3f} ± {s['std']:.3f}  "
              f"[{s['p05']:.3f}, {s['p95']:.3f}]  "
              f"z={s['real_z']:+.2f}  pctile={s['real_percentile']:.0f}  "
              f"p2={s['p_two_sided']:.3f}")
    print(f" Peak lag     : real {summary['real_peak_lag']}  |  null dist "
          f"{summary['null']['peak_lag_distribution']}")
    print(f"\n Results: {results_csv}")
    print(f" Summary: {summary_json}")
    if _SCRATCH.exists():
        _SCRATCH.unlink()


if __name__ == "__main__":
    main()
