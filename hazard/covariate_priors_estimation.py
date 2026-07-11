#!/usr/bin/env python3
"""
Path-A-style estimation of the microsim's FICO/LTV prepayment coefficients.

Path B's Appendix-B priors (beta_fico = −0.15, beta_ltv = +0.10 per 1 SD of
the 75k pool, monthly log-hazard) carry signs opposite the canonical
credit-risk direction for prepayment and cite no source. This script
estimates both coefficients from the same Freddie stratum-month panel that
Path A uses — Poisson PML with log-exposure offset, the production age
spline and standardized rate-gap / burnout / friction terms, but with
(vintage × coupon) fixed effects instead of the 4-way stratum FE (the 4-way
FE absorbs the FICO/LTV buckets, so the credit covariates are identified
from cross-bucket variation within vintage-coupon pools). FICO/LTV enter as
bucket-mean values z-scored by the microsim pool's own mean/std, so the
estimates land in exactly the units of config.LITERATURE_COEFS.

It then reruns Path B (U.S. regime, production sample/seed/β₁) under
(a) beta_fico = beta_ltv = 0 and (b) the estimated coefficients, scoring
each against the $764.7B benchmark — the same exercise §V.C ran for β_b.

Benchmark-independence is unaffected: the estimation touches only the
Freddie panel, never the SOMA benchmark.

Run:  cd hazard && python3 covariate_priors_estimation.py
      → data/covariate_priors_results.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
import statsmodels.api as sm

import literature_hazard
from config import (
    AGE_SPLINE_KNOTS,
    HAZARD_COEF_PATH,
    HOLDOUT_DATE,
    LOAN_SAMPLE_PATH,
    MICROSIM_RESULTS_PATH,
    PANEL_PATH,
)
from extension_risk import score_extension_risk
from hazard_fit import _age_spline_basis, _fit_poisson_glm, _orthogonalize_burnout, enrich_panel_with_macro
from macro import build_empirical_metrics, calculate_dynamic_friction, fetch_data, fetch_soma_mbs_monthly
from microsim_engine import run_qt_microsim

DATA_DIR = Path(__file__).parent / "data"
OUT = DATA_DIR / "covariate_priors_results.json"
TMP = DATA_DIR / "_covariate_priors_tmp.parquet"

N_BOOT = 60
PRIORS = {"beta_fico": -0.15, "beta_ltv": 0.10}


def build_design(train: pd.DataFrame, z_fico: pd.Series, z_ltv: pd.Series):
    age_basis = _age_spline_basis(train["loan_age"].to_numpy(), AGE_SPLINE_KNOTS)
    burn_demean = (
        train.groupby("stratum_id")["burnout"].transform(lambda s: s - s.mean()).to_numpy()
    )
    burnout_orth, _ = _orthogonalize_burnout(age_basis, burn_demean)
    z = lambda v: (v - v.mean()) / (v.std() or 1.0)
    fe = pd.get_dummies(
        train["vintage"].astype(str) + "_" + train["coupon"].astype(str),
        prefix="fe_vc", drop_first=True,
    ).to_numpy(dtype=np.float64)
    X = np.column_stack([
        age_basis,
        z(train["rate_gap_bps"].to_numpy()),
        burnout_orth / (burnout_orth.std() or 1.0),
        z(train["friction"].to_numpy()),
        z_fico.to_numpy(),
        z_ltv.to_numpy(),
        fe,
    ])
    X = sm.add_constant(X, has_constant="add")
    k = age_basis.shape[1]
    idx_fico, idx_ltv = 1 + k + 3, 1 + k + 4
    return X, idx_fico, idx_ltv


def fit_credit_betas(train, z_fico, z_ltv, ridge_alpha) -> tuple[float, float]:
    X, i_f, i_l = build_design(train, z_fico, z_ltv)
    y = train["events"].to_numpy()
    offset = np.log(train["exposure"].to_numpy())
    result, _ = _fit_poisson_glm(X, y, offset, ridge_alpha)
    params = np.asarray(result.params, dtype=np.float64).ravel()
    if not np.isfinite(params).all():
        raise RuntimeError("non-finite fit")
    return float(params[i_f]), float(params[i_l])


def run_variant(loans, macro, empirical, coef_override: dict, tag: str) -> dict:
    saved = dict(literature_hazard.LITERATURE_COEFS)
    try:
        literature_hazard.LITERATURE_COEFS.update(coef_override)
        paths = run_qt_microsim(loan_sample=loans, macro=macro, regimes=("US",), output=TMP)
        r = score_extension_risk(paths["US"], empirical)
    finally:
        literature_hazard.LITERATURE_COEFS.clear()
        literature_hazard.LITERATURE_COEFS.update(saved)
        if TMP.exists():
            TMP.unlink()
    print(f"  {tag}: trapped ${r['hazard_trapped_b']:.1f}B "
          f"({r['share_explained_pct']:.1f}%)  r(lag0)="
          f"{r['cross_correlation'].get(0):+.3f}  peak lag {r['best_lag']}")
    return {
        "trapped_b": r["hazard_trapped_b"],
        "share_pct": r["share_explained_pct"],
        "r_lag0": r["cross_correlation"].get(0),
        "peak_lag": r["best_lag"],
        "coefs": coef_override,
    }


def main() -> None:
    print("Building estimation frame …")
    panel = pl.read_parquet(PANEL_PATH)
    pdf = enrich_panel_with_macro(panel)
    pdf = pdf.dropna(subset=["rate_gap_bps", "exposure", "loan_age", "stratum_id"])
    pdf = pdf[pdf["exposure"] > 0]
    train = pdf[pdf["period"] < HOLDOUT_DATE].copy()

    # Bucket-mean FICO/LTV z-scored by the microsim pool's own moments, so the
    # estimated coefficients are in LITERATURE_COEFS units (per 1 pool SD).
    loans = pl.read_parquet(LOAN_SAMPLE_PATH)
    fico_mu, fico_sd = loans["fico"].mean(), loans["fico"].std()
    ltv_mu, ltv_sd = loans["orig_ltv"].mean(), loans["orig_ltv"].std()
    fico_map = {
        r["fico_bucket"]: (r["fico"] - fico_mu) / fico_sd
        for r in loans.group_by("fico_bucket").agg(pl.col("fico").mean()).iter_rows(named=True)
    }
    ltv_map = {
        r["ltv_bucket"]: (r["orig_ltv"] - ltv_mu) / ltv_sd
        for r in loans.group_by("ltv_bucket").agg(pl.col("orig_ltv").mean()).iter_rows(named=True)
    }
    z_fico = train["fico_bucket"].map(fico_map).astype(float)
    z_ltv = train["ltv_bucket"].map(ltv_map).astype(float)

    ridge_alpha = float(json.load(open(HAZARD_COEF_PATH))["ridge_alpha"])
    print(f"Estimating credit betas (ridge alpha={ridge_alpha:g}, "
          f"{len(train):,} cells, FE = vintage × coupon) …")
    b_f, b_l = fit_credit_betas(train, z_fico, z_ltv, ridge_alpha)
    print(f"  beta_fico = {b_f:+.4f}   beta_ltv = {b_l:+.4f}   "
          f"(priors: {PRIORS['beta_fico']:+.2f} / {PRIORS['beta_ltv']:+.2f})")

    print(f"Cluster bootstrap ({N_BOOT} reps, resampling 4-way strata) …")
    rng = np.random.default_rng(42)
    ids = np.sort(train["stratum_id"].unique())
    groups = dict(tuple(train.groupby("stratum_id")))
    draws_f, draws_l = [], []
    for i in range(N_BOOT):
        picks = rng.choice(ids, size=len(ids), replace=True)
        boot = pd.concat([groups[s] for s in picks], ignore_index=True)
        zf = boot["fico_bucket"].map(fico_map).astype(float)
        zl = boot["ltv_bucket"].map(ltv_map).astype(float)
        try:
            f, l = fit_credit_betas(boot, zf, zl, ridge_alpha)
        except Exception:
            continue
        draws_f.append(f)
        draws_l.append(l)
        if (i + 1) % 10 == 0:
            print(f"  rep {i + 1}/{N_BOOT}")

    est = {
        "beta_fico": {
            "point": b_f,
            "se": float(np.std(draws_f, ddof=1)),
            "ci_95": [float(np.percentile(draws_f, 2.5)), float(np.percentile(draws_f, 97.5))],
            "n_boot": len(draws_f),
        },
        "beta_ltv": {
            "point": b_l,
            "se": float(np.std(draws_l, ddof=1)),
            "ci_95": [float(np.percentile(draws_l, 2.5)), float(np.percentile(draws_l, 97.5))],
            "n_boot": len(draws_l),
        },
    }

    print("\nFetching benchmark; rerunning Path B variants …")
    macro = calculate_dynamic_friction(fetch_data())
    empirical = build_empirical_metrics(macro, soma_rolloff=fetch_soma_mbs_monthly())
    central = score_extension_risk(pd.read_parquet(MICROSIM_RESULTS_PATH), empirical)
    print(f"  production priors: trapped ${central['hazard_trapped_b']:.1f}B "
          f"({central['share_explained_pct']:.1f}%)")

    zero = run_variant(loans, macro, empirical,
                       {"beta_fico": 0.0, "beta_ltv": 0.0}, "beta_F = beta_L = 0")
    estimated = run_variant(loans, macro, empirical,
                            {"beta_fico": b_f, "beta_ltv": b_l}, "estimated betas")

    payload = {
        "mode": "covariate_priors_estimation",
        "priors": PRIORS,
        "estimated": est,
        "bucket_z_values": {"fico": fico_map, "ltv": ltv_map},
        "fe": "vintage x coupon (4-way stratum FE absorbs the credit buckets)",
        "ridge_alpha": ridge_alpha,
        "production": {
            "trapped_b": central["hazard_trapped_b"],
            "share_pct": central["share_explained_pct"],
            "r_lag0": central["cross_correlation"].get(0),
        },
        "zeroed": zero,
        "reestimated": estimated,
    }
    OUT.write_text(json.dumps(
        payload, indent=2,
        default=lambda x: float(x) if isinstance(x, (np.floating, np.integer)) else x,
    ) + "\n")
    print(f"\nSaved: {OUT}")


if __name__ == "__main__":
    main()
