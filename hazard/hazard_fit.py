"""
Discrete-time proportional hazards: Poisson GLM on cohort-month cells.

log(h) = spline(loan_age) + β1·RateGap_bps + β2·Burnout_orth + β3·Friction + FE(stratum)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import polars as pl
import statsmodels.api as sm

from config import (
    AGE_SPLINE_KNOTS,
    BASE_FRICTION,
    HAZARD_COEF_PATH,
    HOLDOUT_DATE,
    PANEL_PATH,
    RIDGE_ALPHA,
    RIDGE_ALPHA_GRID,
    RATE_GAP_UNITS,
)
from macro import fetch_data, calculate_dynamic_friction, coupon_to_decimal
from stratum import build_stratum_id

SPEC_VERSION = 3


def _orthogonalize_burnout(
    age_basis: np.ndarray,
    burnout: np.ndarray,
) -> tuple[np.ndarray, dict[str, float]]:
    """Residualize burnout on age spline so β_burnout is not a seasoning proxy."""
    X = sm.add_constant(age_basis, has_constant="add")
    ols = sm.OLS(burnout, X).fit()
    names = ["burnout_age_const"] + [f"burnout_age_{i}" for i in range(age_basis.shape[1])]
    adj = {names[i]: float(ols.params[i]) for i in range(len(names))}
    return ols.resid, adj


def _age_spline_basis(age: np.ndarray, knots: list[int]) -> np.ndarray:
    """Truncated power basis for loan age seasoning spline."""
    cols = [age.astype(float)]
    for k in knots:
        cols.append(np.maximum(age - k, 0.0) ** 2)
    return np.column_stack(cols)


def _burnout_orthogonalized(
    burnout: np.ndarray,
    age_basis: np.ndarray,
    burnout_age_adj: dict[str, float],
) -> np.ndarray:
    adj_names = ["burnout_age_const"] + [
        f"burnout_age_{i}" for i in range(age_basis.shape[1])
    ]
    X_adj = sm.add_constant(age_basis, has_constant="add")
    burnout_fitted = sum(
        burnout_age_adj.get(adj_names[i], 0) * X_adj[:, i]
        for i in range(X_adj.shape[1])
    )
    return burnout - burnout_fitted


def _stratum_fe_row(
    stratum_id: str,
    reference_stratum: str,
    fe_columns: list[str],
    fe_index: dict[str, int] | None = None,
) -> list[float]:
    """O(1) stratum dummy row when fe_index maps 'fe_stratum_{id}' → column index."""
    if fe_index is not None:
        row = [0.0] * len(fe_columns)
        if stratum_id != reference_stratum:
            col = f"fe_stratum_{stratum_id}"
            idx = fe_index.get(col)
            if idx is not None:
                row[idx] = 1.0
        return row
    return _stratum_dummy_matrix(
        pd.Series([stratum_id]), reference_stratum, fe_columns
    )[0].tolist()


def build_fe_index(fe_columns: list[str]) -> dict[str, int]:
    return {col: i for i, col in enumerate(fe_columns)}


def _stratum_dummy_matrix(
    stratum_ids: pd.Series,
    reference_stratum: str,
    fe_columns: list[str],
) -> np.ndarray:
    """Vectorized stratum dummies for holdout panels."""
    rows = [
        _stratum_fe_row(sid, reference_stratum, fe_columns)
        for sid in stratum_ids.astype(str)
    ]
    return np.asarray(rows, dtype=np.float64)


def enrich_panel_with_macro(panel: pl.DataFrame) -> pd.DataFrame:
    """Join cohort-month panel with FRED market rates and dynamic friction."""
    macro = fetch_data()
    macro = calculate_dynamic_friction(macro)
    macro_df = macro.reset_index()
    first_col = macro_df.columns[0]
    if first_col != "period":
        macro_df = macro_df.rename(columns={first_col: "period"})

    pdf = panel.to_pandas()
    pdf["period"] = pd.to_datetime(pdf["period"])
    pdf["period_ym"] = pdf["period"].dt.strftime("%Y%m")

    macro_df["period"] = pd.to_datetime(macro_df["period"])
    macro_df["period_ym"] = macro_df["period"].dt.strftime("%Y%m")
    mcols = macro_df[["period_ym", "MORTGAGE30US", "Dynamic_Friction"]].drop_duplicates("period_ym")

    pdf = pdf.merge(mcols, on="period_ym", how="left")
    pdf["market_rate"] = pdf["MORTGAGE30US"] / 100.0
    pdf["coupon_dec"] = coupon_to_decimal(pdf["coupon"].to_numpy())
    pdf["rate_gap"] = pdf["coupon_dec"] - pdf["market_rate"]
    pdf["rate_gap_bps"] = pdf["rate_gap"] * 10_000.0
    pdf["friction"] = pdf["Dynamic_Friction"].fillna(BASE_FRICTION)
    pdf["burnout"] = pdf["burnout"].fillna(0).clip(0, 1)
    pdf["loan_age"] = pdf["mean_loan_age"].fillna(12)
    pdf["events"] = pdf["prepaid_upb"].fillna(0)
    pdf["exposure"] = pdf["exposure_upb"].clip(lower=1)
    pdf["hazard_obs"] = (pdf["events"] / pdf["exposure"]).clip(0, 1)
    pdf["stratum_id"] = [
        build_stratum_id(v, c, f, l)
        for v, c, f, l in zip(
            pdf["vintage"], pdf["coupon"], pdf["fico_bucket"], pdf["ltv_bucket"]
        )
    ]
    return pdf


def _fit_poisson_glm(
    X: np.ndarray,
    y_events: np.ndarray,
    offset: np.ndarray,
    ridge_alpha: float,
) -> tuple[object, str]:
    """IRLS with Ridge fallback (stratum FE is ill-conditioned for plain IRLS)."""
    model = sm.GLM(
        y_events,
        X,
        family=sm.families.Poisson(),
        offset=offset,
    )
    try:
        irls = model.fit(maxiter=100)
        if ridge_alpha > 0:
            result = model.fit_regularized(
                method="elastic_net",
                alpha=ridge_alpha,
                L1_wt=0.0,
                maxiter=100,
                start_params=irls.params,
            )
            return result, f"ridge(alpha={ridge_alpha})"
        return irls, "irls"
    except (ValueError, np.linalg.LinAlgError):
        alpha = ridge_alpha if ridge_alpha > 0 else 1e-5
        result = model.fit_regularized(
            method="elastic_net",
            alpha=alpha,
            L1_wt=0.0,
            maxiter=100,
        )
        return result, f"ridge(alpha={alpha}, irls_fallback)"


def _holdout_metrics(
    holdout: pd.DataFrame,
    result,
    burnout_age_adj: dict,
    friction_mean: float,
    friction_std: float,
    gap_mean: float,
    gap_std: float,
    burn_std: float,
    stratum_burnout_mean: dict,
    reference_stratum: str,
    fe_columns: list[str],
) -> tuple[float, float]:
    age_h = _age_spline_basis(holdout["loan_age"].to_numpy(), AGE_SPLINE_KNOTS)
    burn_demean_h = holdout["burnout"].to_numpy() - holdout["stratum_id"].map(
        stratum_burnout_mean
    ).fillna(0).to_numpy()
    burnout_h_orth = _burnout_orthogonalized(
        burn_demean_h, age_h, burnout_age_adj
    )
    stratum_h = _stratum_dummy_matrix(
        holdout["stratum_id"], reference_stratum, fe_columns
    )
    X_h = np.column_stack([
        age_h,
        (holdout["rate_gap_bps"].to_numpy() - gap_mean) / gap_std,
        burnout_h_orth / burn_std,
        (holdout["friction"].to_numpy() - friction_mean) / friction_std,
        stratum_h,
    ])
    X_h = sm.add_constant(X_h, has_constant="add")
    X_h = np.asarray(X_h, dtype=np.float64)
    params = np.asarray(result.params, dtype=np.float64).ravel()
    linpred = X_h.dot(params)
    pred_hazard = np.exp(np.clip(linpred.astype(np.float64), -20, 0))
    pred_cpr = pred_hazard * 12 * 100
    obs_cpr = holdout["prepay_rate"].to_numpy() * 12 * 100
    ss_res = ((obs_cpr - pred_cpr) ** 2).sum()
    ss_tot = ((obs_cpr - obs_cpr.mean()) ** 2).sum()
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else np.nan
    rmse = float(np.sqrt(((obs_cpr - pred_cpr) ** 2).mean()))
    return r2, rmse


def fit_hazard_glm(
    panel: Optional[pl.DataFrame] = None,
    holdout_date: pd.Timestamp = HOLDOUT_DATE,
    output: Path = HAZARD_COEF_PATH,
    ridge_alpha: float | None = None,
    ridge_grid: bool = True,
) -> dict:
    """
    Grouped Poisson GLM with log(exposure) offset, rate gap in bps,
    optional Ridge penalty, and stratum fixed effects.
    """
    if panel is None:
        panel = pl.read_parquet(PANEL_PATH)

    pdf = enrich_panel_with_macro(panel)
    pdf = pdf.dropna(subset=["rate_gap_bps", "exposure", "loan_age", "stratum_id"])
    pdf = pdf[pdf["exposure"] > 0]
    pdf["prepay_rate"] = (pdf["events"] / pdf["exposure"]).clip(0, 1)

    train = pdf[pdf["period"] < holdout_date].copy()
    holdout = pdf[pdf["period"] >= holdout_date].copy()
    print(f"Training cells: {len(train):,}  |  Holdout: {len(holdout):,}")

    reference_stratum = sorted(train["stratum_id"].unique())[0]
    stratum_dummies_train = pd.get_dummies(
        train["stratum_id"],
        prefix="fe_stratum",
        drop_first=True,
    )
    fe_columns = list(stratum_dummies_train.columns)
    stratum_extra = stratum_dummies_train.to_numpy()
    print(f"Stratum FE: {len(fe_columns)} dummies  |  reference: {reference_stratum}")

    age_basis = _age_spline_basis(train["loan_age"].to_numpy(), AGE_SPLINE_KNOTS)
    train["burnout_demean"] = train.groupby("stratum_id")["burnout"].transform(
        lambda s: s - s.mean()
    )
    stratum_burnout_mean = (
        train.groupby("stratum_id")["burnout"].mean().to_dict()
    )
    burnout_orth, burnout_age_adj = _orthogonalize_burnout(
        age_basis, train["burnout_demean"].to_numpy()
    )
    friction_mean = float(train["friction"].mean())
    friction_std = float(train["friction"].std()) or 1.0
    gap_mean = float(train["rate_gap_bps"].mean())
    gap_std = float(train["rate_gap_bps"].std()) or 1.0
    burn_std = float(burnout_orth.std()) or 1.0
    train_fric = (train["friction"].to_numpy() - friction_mean) / friction_std
    train_gap = (train["rate_gap_bps"].to_numpy() - gap_mean) / gap_std
    train_burn = burnout_orth / burn_std
    X = np.column_stack([
        age_basis,
        train_gap,
        train_burn,
        train_fric,
        stratum_extra,
    ])
    col_names = (
        ["age_linear"]
        + [f"age_spline_{k}" for k in AGE_SPLINE_KNOTS]
        + ["rate_gap_bps", "burnout_orth", "friction"]
        + fe_columns
    )
    X = sm.add_constant(X, has_constant="add")
    col_names = ["const"] + col_names

    y_events = train["events"].to_numpy()
    offset = np.log(train["exposure"].to_numpy())

    alphas = [ridge_alpha] if ridge_alpha is not None else list(RIDGE_ALPHA_GRID)
    best_alpha = alphas[0]
    best_result = None
    best_method = "irls"
    best_rmse = np.inf

    for alpha in alphas:
        result, fit_method = _fit_poisson_glm(X, y_events, offset, alpha)
        if len(holdout) > 0:
            _, rmse = _holdout_metrics(
                holdout, result, burnout_age_adj,
                friction_mean, friction_std, gap_mean, gap_std, burn_std,
                stratum_burnout_mean, reference_stratum, fe_columns,
            )
            print(f"  alpha={alpha:g}  holdout RMSE={rmse:.2f}pp")
            if rmse < best_rmse:
                best_rmse = rmse
                best_alpha = alpha
                best_result = result
                best_method = fit_method
        else:
            best_alpha = alpha
            best_result = result
            best_method = fit_method

    result = best_result
    ridge_alpha = best_alpha
    coefs = {col_names[i]: float(result.params[i]) for i in range(len(col_names))}
    print(f"Poisson GLM coefficients ({best_method}):")
    for name in ["const", "rate_gap_bps", "burnout_orth", "friction"]:
        print(f"  {name}: {coefs.get(name, 0):+.6f}")
    print(f"  ... + {len(fe_columns)} stratum FE coefficients")

    diag = {
        "spec_version": SPEC_VERSION,
        "link": "poisson_log",
        "rate_gap_units": RATE_GAP_UNITS,
        "ridge_alpha": ridge_alpha,
        "fe_type": "stratum",
        "reference_stratum": reference_stratum,
        "fe_columns": fe_columns,
        "friction_mean": friction_mean,
        "friction_std": friction_std,
        "rate_gap_bps_mean": gap_mean,
        "rate_gap_bps_std": gap_std,
        "burnout_demean_std": burn_std,
        "stratum_burnout_mean": stratum_burnout_mean,
        "coefficients": coefs,
        "burnout_age_adjust": burnout_age_adj,
        "n_train": len(train),
        "n_holdout": len(holdout),
        "n_strata": len(fe_columns) + 1,
    }

    if len(holdout) > 0:
        r2, rmse = _holdout_metrics(
            holdout, result, burnout_age_adj,
            friction_mean, friction_std, gap_mean, gap_std, burn_std,
            stratum_burnout_mean, reference_stratum, fe_columns,
        )
        diag["holdout_r2"] = r2
        diag["holdout_rmse"] = rmse
        print(f"Holdout RMSE: {rmse:.2f}pp  R²: {r2:.3f}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(diag, f, indent=2)
    print(f"Coefficients saved to {output}")
    return diag


def predict_hazard(
    loan_age: float,
    rate_gap: float,
    burnout: float,
    friction: float,
    coefs: dict,
    burnout_age_adjust: dict | None = None,
    stratum_id: str | None = None,
    reference_stratum: str | None = None,
    fe_columns: list[str] | None = None,
    friction_mean: float = 0.0,
    friction_std: float = 1.0,
    rate_gap_bps_mean: float = 0.0,
    rate_gap_bps_std: float = 1.0,
    burnout_demean_std: float = 1.0,
    stratum_burnout_mean: dict | None = None,
    fe_index: dict[str, int] | None = None,
) -> float:
    """Predict monthly hazard: Poisson GLM with log link → h = exp(Xβ)."""
    age_basis = _age_spline_basis(np.array([loan_age]), AGE_SPLINE_KNOTS)[0]
    burn_demean = burnout
    if stratum_burnout_mean and stratum_id is not None:
        burn_demean = burnout - stratum_burnout_mean.get(stratum_id, 0.0)
    burnout_val = burn_demean
    if burnout_age_adjust:
        adj_names = ["burnout_age_const"] + [
            f"burnout_age_{i}" for i in range(len(age_basis))
        ]
        x_adj = [1.0] + list(age_basis)
        burnout_fitted = sum(
            burnout_age_adjust.get(adj_names[i], 0) * x_adj[i]
            for i in range(len(x_adj))
        )
        burnout_val = burn_demean - burnout_fitted

    gap_bps = rate_gap * 10_000.0
    x = [1.0] + list(age_basis) + [
        (gap_bps - rate_gap_bps_mean) / rate_gap_bps_std,
        burnout_val / burnout_demean_std,
        (friction - friction_mean) / friction_std,
    ]
    names = (
        ["const", "age_linear"]
        + [f"age_spline_{k}" for k in AGE_SPLINE_KNOTS]
        + ["rate_gap_bps", "burnout_orth", "friction"]
    )

    if fe_columns and stratum_id is not None and reference_stratum is not None:
        fe_row = _stratum_fe_row(
            stratum_id, reference_stratum, fe_columns, fe_index=fe_index
        )
        x.extend(fe_row)
        names.extend(fe_columns)

    log_mu = sum(coefs.get(n, 0) * v for n, v in zip(names, x))
    return float(np.exp(np.clip(log_mu, -20, 0)))


def load_coefficients(path: Path = HAZARD_COEF_PATH) -> dict:
    with open(path) as f:
        data = json.load(f)
    return data["coefficients"]


def load_burnout_age_adjust(path: Path = HAZARD_COEF_PATH) -> dict:
    with open(path) as f:
        data = json.load(f)
    return data.get("burnout_age_adjust", {})


def load_fe_meta(path: Path = HAZARD_COEF_PATH) -> dict:
    with open(path) as f:
        return json.load(f)


def load_predict_scales(path: Path = HAZARD_COEF_PATH) -> dict:
    data = load_fe_meta(path)
    fe_columns = list(data.get("fe_columns", []))
    return {
        "reference_stratum": str(data.get("reference_stratum", "")),
        "fe_columns": fe_columns,
        "fe_index": build_fe_index(fe_columns),
        "friction_mean": float(data.get("friction_mean", 0.0)),
        "friction_std": float(data.get("friction_std", 1.0)),
        "rate_gap_bps_mean": float(data.get("rate_gap_bps_mean", 0.0)),
        "rate_gap_bps_std": float(data.get("rate_gap_bps_std", 1.0)),
        "burnout_demean_std": float(data.get("burnout_demean_std", 1.0)),
        "stratum_burnout_mean": dict(data.get("stratum_burnout_mean", {})),
    }


if __name__ == "__main__":
    from ingest import load_or_build_panel
    panel = load_or_build_panel()
    fit_hazard_glm(panel)
