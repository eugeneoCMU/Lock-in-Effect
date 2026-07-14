"""
Stratum-level block bootstrap for Path A hazard coefficient uncertainty.

Ridge + stratum FE invalidate naive GLM standard errors, so we resample the
strata (clusters) with replacement, refit the production Poisson GLM on each
replication, and report percentile CIs for the three macro coefficients
(rate_gap_bps, burnout_orth, friction).

Design choices (report these alongside the CIs):
  * The ridge alpha is FIXED at the production value — it is NOT re-selected
    per replication. Re-selection would bootstrap a different (slower)
    estimator: coefficient-plus-model-selection.
  * Each resampled cluster copy gets a fresh stratum label so duplicated
    strata contribute independent fixed effects.
  * Standardization constants are recomputed per replication (pipeline-
    faithful), then coefficients are rescaled to the production
    standardization so draws are comparable across replications:
        beta_prod = beta_rep * (prod_std / rep_std)

Run:
    python3 hazard/bootstrap_se.py --reps 200
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from config import (
    AGE_SPLINE_KNOTS,
    DATA_DIR,
    HAZARD_COEF_PATH,
    HOLDOUT_DATE,
    PANEL_PATH,
)
from hazard_fit import (
    _age_spline_basis,
    _fit_poisson_glm,
    _month_dummy_matrix,
    _orthogonalize_burnout,
    enrich_panel_with_macro,
)

BOOTSTRAP_RESULTS_PATH = DATA_DIR / "hazard_bootstrap_se.json"
BOOTSTRAP_DRAWS_CSV = DATA_DIR / "hazard_bootstrap_draws.csv"
BETA_NAMES = ["rate_gap_bps", "burnout_orth", "friction"]


def resample_strata(train: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """
    Cluster bootstrap: draw K strata with replacement (K = number of strata),
    relabeling each draw so repeated strata get distinct fixed effects.
    Keeps the source id in `stratum_id_src`.
    """
    ids = np.sort(train["stratum_id"].unique())
    draws = rng.choice(ids, size=len(ids), replace=True)
    groups = dict(tuple(train.groupby("stratum_id")))
    chunks = []
    for k, sid in enumerate(draws):
        g = groups[sid].copy()
        g["stratum_id_src"] = sid
        g["stratum_id"] = f"{sid}__b{k:03d}"
        chunks.append(g)
    return pd.concat(chunks, ignore_index=True)


MAX_ABS_BETA = 20.0  # standardized units; beyond this the IRLS diverged


def fit_betas(train: pd.DataFrame, ridge_alpha: float,
              start_head: np.ndarray | None = None,
              seasonal: bool = False) -> dict:
    """
    Refit the production spec (age spline + standardized macro terms +
    stratum FE, Poisson log link, log-exposure offset) on `train`.
    Returns macro betas in THIS SAMPLE's standardized units plus the
    standardization scales needed to convert them.
    Mirrors hazard_fit.fit_hazard_glm's training path exactly.

    seasonal=True mirrors spec v4: 11 fixed-column calendar-month dummies
    (January reference) between the macro block and the stratum FE. The
    macro betas stay at positions [1+k : 4+k], so extraction and the
    warm-start head are unchanged; month coefficients are nuisance terms
    here and are not returned.

    start_head: optional warm-start for [const | age spline | gap, burn,
    fric] from the point fit; FE coefficients start at zero. Poisson IRLS
    with stratum FE can silently diverge on resampled data — the warm start
    keeps replications on the production solution branch, and any fit that
    still comes back non-finite or absurd raises so the replication is
    counted as failed rather than polluting the draws.
    """
    age_basis = _age_spline_basis(train["loan_age"].to_numpy(), AGE_SPLINE_KNOTS)
    burn_demean = (
        train.groupby("stratum_id")["burnout"]
        .transform(lambda s: s - s.mean())
        .to_numpy()
    )
    burnout_orth, _ = _orthogonalize_burnout(age_basis, burn_demean)

    friction_mean = float(train["friction"].mean())
    friction_std = float(train["friction"].std()) or 1.0
    gap_mean = float(train["rate_gap_bps"].mean())
    gap_std = float(train["rate_gap_bps"].std()) or 1.0
    burn_std = float(burnout_orth.std()) or 1.0

    dummies = pd.get_dummies(
        train["stratum_id"], prefix="fe_stratum", drop_first=True
    ).to_numpy(dtype=np.float64)

    blocks = [
        age_basis,
        (train["rate_gap_bps"].to_numpy() - gap_mean) / gap_std,
        burnout_orth / burn_std,
        (train["friction"].to_numpy() - friction_mean) / friction_std,
    ]
    if seasonal:
        blocks.append(_month_dummy_matrix(train["period"]))
    blocks.append(dummies)
    X = np.column_stack(blocks)
    X = sm.add_constant(X, has_constant="add")

    y_events = train["events"].to_numpy()
    offset = np.log(train["exposure"].to_numpy())
    k = age_basis.shape[1]  # columns: const | age spline (k) | gap, burn, fric | FE

    if start_head is None:
        result, fit_method = _fit_poisson_glm(X, y_events, offset, ridge_alpha)
    else:
        start = np.zeros(X.shape[1])
        start[: len(start_head)] = start_head
        model = sm.GLM(y_events, X, family=sm.families.Poisson(), offset=offset)
        try:
            irls = model.fit(maxiter=100, start_params=start)
            warm = (irls.params if np.isfinite(np.asarray(irls.params)).all()
                    else start)
        except (ValueError, np.linalg.LinAlgError):
            warm = start
        result = model.fit_regularized(
            method="elastic_net", alpha=ridge_alpha, L1_wt=0.0,
            maxiter=100, start_params=warm,
        )
        fit_method = f"ridge(alpha={ridge_alpha}, warm_start)"

    params = np.asarray(result.params, dtype=np.float64).ravel()
    macro = params[1 + k: 4 + k]
    if not np.isfinite(params).all() or np.abs(macro).max() > MAX_ABS_BETA:
        raise RuntimeError(
            f"non-converged fit (max |macro beta| = {np.abs(macro).max():.3g})"
        )
    head_len = 4 + k + (11 if seasonal else 0)  # months ride in the warm start
    return {
        "rate_gap_bps": float(params[1 + k]),
        "burnout_orth": float(params[2 + k]),
        "friction": float(params[3 + k]),
        "gap_std": gap_std,
        "burn_std": burn_std,
        "fric_std": friction_std,
        "fit_method": fit_method,
        "params_head": params[:head_len].copy(),
    }


def production_start_head(prod: dict) -> np.ndarray:
    """Warm-start head [const | age spline | gap, burn, fric | months?] built
    from the production artifact, pinning point fits to the production
    solution branch (the Gate-B lesson: cold IRLS on the seasonal design can
    land a different penalized optimum)."""
    coefs = prod["coefficients"]
    names = (
        ["const", "age_linear"]
        + [f"age_spline_{k}" for k in AGE_SPLINE_KNOTS]
        + ["rate_gap_bps", "burnout_orth", "friction"]
    )
    if "month_effects" in prod:
        names += [f"m_{m}" for m in range(2, 13)]
    return np.array([float(coefs[n]) for n in names], dtype=np.float64)


def rescale_to_production_units(betas: dict, prod_scales: dict) -> dict:
    """
    Convert a replication's standardized betas to production standardized
    units: beta per raw unit = beta_rep / rep_std; times production std.
    """
    return {
        "rate_gap_bps": betas["rate_gap_bps"] / betas["gap_std"] * prod_scales["gap_std"],
        "burnout_orth": betas["burnout_orth"] / betas["burn_std"] * prod_scales["burn_std"],
        "friction": betas["friction"] / betas["fric_std"] * prod_scales["fric_std"],
    }


def run_bootstrap(
    train: pd.DataFrame,
    n_reps: int,
    ridge_alpha: float,
    seed: int,
    prod_scales: dict | None = None,
    draws_csv: Path | None = None,
    seasonal: bool = False,
) -> dict:
    """Full bootstrap: point fit + n_reps cluster replications."""
    point = fit_betas(train, ridge_alpha, seasonal=seasonal)
    if prod_scales is None:
        prod_scales = {k: point[k] for k in ["gap_std", "burn_std", "fric_std"]}

    rng = np.random.default_rng(seed)
    draws: dict[str, list[float]] = {n: [] for n in BETA_NAMES}
    n_failed = 0
    t0 = time.perf_counter()
    start_head = point["params_head"]
    for i in range(n_reps):
        boot = resample_strata(train, rng)
        try:
            b = fit_betas(boot, ridge_alpha, start_head=start_head,
                          seasonal=seasonal)
        except Exception as exc:  # non-converged replication: count, move on
            n_failed += 1
            print(f"  rep {i + 1}/{n_reps}: FAILED ({exc})")
            continue
        r = rescale_to_production_units(b, prod_scales)
        for n in BETA_NAMES:
            draws[n].append(r[n])
        if draws_csv is not None:
            pd.DataFrame(draws).to_csv(draws_csv, index=False)  # checkpoint
        if (i + 1) % 10 == 0 or i == 0:
            el = time.perf_counter() - t0
            print(f"  rep {i + 1}/{n_reps}  "
                  f"({el / (i + 1):.1f}s/rep, {el:.0f}s elapsed)")

    return {
        "n_reps": n_reps,
        "n_failed": n_failed,
        "ridge_alpha": ridge_alpha,
        "seed": seed,
        "cluster": "stratum",
        "alpha_reselected_per_rep": False,
        "production_scales": prod_scales,
        "point_production_units": rescale_to_production_units(point, prod_scales),
        "se": {n: float(np.std(draws[n], ddof=1)) for n in BETA_NAMES},
        "ci_95": {
            n: {
                "lo": float(np.percentile(draws[n], 2.5)),
                "hi": float(np.percentile(draws[n], 97.5)),
            }
            for n in BETA_NAMES
        },
        "frac_le_0": {
            n: float(np.mean(np.asarray(draws[n]) <= 0)) for n in BETA_NAMES
        },
    }


def main() -> None:
    import polars as pl

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reps", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--alpha", type=float, default=None,
                        help="ridge alpha (default: production value)")
    parser.add_argument("--out", default=str(BOOTSTRAP_RESULTS_PATH))
    args = parser.parse_args()

    prod = json.load(open(HAZARD_COEF_PATH))
    ridge_alpha = args.alpha if args.alpha is not None else float(prod["ridge_alpha"])
    prod_scales = {
        "gap_std": float(prod["rate_gap_bps_std"]),
        "burn_std": float(prod["burnout_demean_std"]),
        "fric_std": float(prod["friction_std"]),
    }

    print("Building training frame (production filters) …")
    panel = pl.read_parquet(PANEL_PATH)
    pdf = enrich_panel_with_macro(panel)
    pdf = pdf.dropna(subset=["rate_gap_bps", "exposure", "loan_age", "stratum_id"])
    pdf = pdf[pdf["exposure"] > 0]
    train = pdf[pdf["period"] < HOLDOUT_DATE].copy()
    print(f"Training cells: {len(train):,}  |  strata: {train['stratum_id'].nunique()}")

    seasonal = "month_effects" in prod  # spec v4 production artifact
    print(f"Point refit (alpha={ridge_alpha:g}, seasonal={seasonal}) — "
          f"parity check vs production:")
    point = fit_betas(train, ridge_alpha, seasonal=seasonal,
                      start_head=production_start_head(prod) if seasonal
                      else None)
    for n in BETA_NAMES:
        prod_beta = float(prod["coefficients"][n])
        print(f"  {n}: refit={point[n]:+.4f}  production={prod_beta:+.4f}")

    print(f"\nBlock bootstrap: {args.reps} reps, cluster=stratum, "
          f"fixed alpha={ridge_alpha:g}, seed={args.seed}")
    out = run_bootstrap(train, args.reps, ridge_alpha, args.seed,
                        prod_scales=prod_scales, draws_csv=BOOTSTRAP_DRAWS_CSV,
                        seasonal=seasonal)

    out["spec_version"] = int(prod.get("spec_version", -1))
    out["seasonal_design"] = bool(seasonal)
    out["n_train"] = int(len(train))
    out["point_refit_native_units"] = {n: point[n] for n in BETA_NAMES}
    out["production_coefficients"] = {
        n: float(prod["coefficients"][n]) for n in BETA_NAMES
    }

    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)

    print("\n" + "=" * 60)
    print(" Stratum block bootstrap — production standardized units")
    print("=" * 60)
    for n in BETA_NAMES:
        ci = out["ci_95"][n]
        print(f"  {n:>13}: point={out['production_coefficients'][n]:+.4f}  "
              f"se={out['se'][n]:.4f}  "
              f"95% CI [{ci['lo']:+.4f}, {ci['hi']:+.4f}]  "
              f"frac<=0: {out['frac_le_0'][n]:.3f}")
    print(f"Results saved to {args.out}")


if __name__ == "__main__":
    main()
