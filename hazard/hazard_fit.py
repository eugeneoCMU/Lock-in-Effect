"""
Discrete-time proportional hazards: grouped binomial logistic GLM.

logit(h) = spline(loan_age) + β1·RateGap + β2·Burnout + β3·Friction
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
)
from macro import fetch_data, calculate_dynamic_friction


def _age_spline_basis(age: np.ndarray, knots: list[int]) -> np.ndarray:
    """Truncated power basis for loan age seasoning spline."""
    cols = [age.astype(float)]
    for k in knots:
        cols.append(np.maximum(age - k, 0.0) ** 2)
    return np.column_stack(cols)


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
    pdf["rate_gap"] = pdf["coupon"] - pdf["market_rate"]
    pdf["friction"] = pdf["Dynamic_Friction"].fillna(BASE_FRICTION)
    pdf["burnout"] = pdf["burnout"].fillna(0).clip(0, 1)
    pdf["loan_age"] = pdf["mean_loan_age"].fillna(12)
    pdf["events"] = pdf["prepaid_upb"].fillna(0)
    pdf["exposure"] = pdf["exposure_upb"].clip(lower=1)
    pdf["hazard_obs"] = (pdf["events"] / pdf["exposure"]).clip(0, 1)
    return pdf


def fit_hazard_glm(
    panel: Optional[pl.DataFrame] = None,
    holdout_date: pd.Timestamp = HOLDOUT_DATE,
    output: Path = HAZARD_COEF_PATH,
) -> dict:
    """
    Fit discrete-time logistic hazard on cohort-month cells.
    Uses WLS on logit(prepay_rate) with exposure weights (grouped data).
    """
    if panel is None:
        panel = pl.read_parquet(PANEL_PATH)

    pdf = enrich_panel_with_macro(panel)
    pdf = pdf.dropna(subset=["rate_gap", "exposure", "loan_age"])
    pdf = pdf[pdf["exposure"] > 0]
    pdf["prepay_rate"] = (pdf["events"] / pdf["exposure"]).clip(1e-6, 1 - 1e-6)

    train = pdf[pdf["period"] < holdout_date].copy()
    holdout = pdf[pdf["period"] >= holdout_date].copy()
    print(f"Training cells: {len(train):,}  |  Holdout: {len(holdout):,}")

    age_basis = _age_spline_basis(train["loan_age"].to_numpy(), AGE_SPLINE_KNOTS)
    X = np.column_stack([
        age_basis,
        train["rate_gap"].to_numpy(),
        train["burnout"].to_numpy(),
        train["friction"].to_numpy(),
    ])
    col_names = (
        ["age_linear"]
        + [f"age_spline_{k}" for k in AGE_SPLINE_KNOTS]
        + ["rate_gap", "burnout", "friction"]
    )
    X = sm.add_constant(X, has_constant="add")
    col_names = ["const"] + col_names

    y_logit = np.log(train["prepay_rate"] / (1 - train["prepay_rate"]))
    weights = train["exposure"].to_numpy()

    model = sm.WLS(y_logit, X, weights=weights)
    result = model.fit()
    print(result.summary())

    coefs = {col_names[i]: float(result.params[i]) for i in range(len(col_names))}
    diag = {
        "coefficients": coefs,
        "r2": float(result.rsquared),
        "n_train": len(train),
        "n_holdout": len(holdout),
    }

    if len(holdout) > 0:
        age_h = _age_spline_basis(holdout["loan_age"].to_numpy(), AGE_SPLINE_KNOTS)
        X_h = np.column_stack([
            age_h,
            holdout["rate_gap"].to_numpy(),
            holdout["burnout"].to_numpy(),
            holdout["friction"].to_numpy(),
        ])
        X_h = sm.add_constant(X_h, has_constant="add")
        pred_logit = X_h @ result.params
        holdout = holdout.copy()
        holdout["pred_hazard"] = 1 / (1 + np.exp(-pred_logit))
        holdout["pred_cpr_pct"] = holdout["pred_hazard"] * 12 * 100
        holdout["obs_cpr_pct"] = holdout["prepay_rate"] * 12 * 100
        ss_res = ((holdout["obs_cpr_pct"] - holdout["pred_cpr_pct"]) ** 2).sum()
        ss_tot = ((holdout["obs_cpr_pct"] - holdout["obs_cpr_pct"].mean()) ** 2).sum()
        diag["holdout_r2"] = float(1 - ss_res / ss_tot) if ss_tot > 0 else np.nan
        diag["holdout_rmse"] = float(np.sqrt(
            ((holdout["obs_cpr_pct"] - holdout["pred_cpr_pct"]) ** 2).mean()
        ))

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
) -> float:
    """Predict monthly hazard from fitted coefficients."""
    age_basis = _age_spline_basis(np.array([loan_age]), AGE_SPLINE_KNOTS)[0]
    x = [1.0] + list(age_basis) + [rate_gap, burnout, friction]
    names = (
        ["const", "age_linear"]
        + [f"age_spline_{k}" for k in AGE_SPLINE_KNOTS]
        + ["rate_gap", "burnout", "friction"]
    )
    logit = sum(coefs.get(n, 0) * v for n, v in zip(names, x))
    return float(1 / (1 + np.exp(-logit)))


def load_coefficients(path: Path = HAZARD_COEF_PATH) -> dict:
    with open(path) as f:
        data = json.load(f)
    return data["coefficients"]


if __name__ == "__main__":
    from ingest import load_or_build_panel
    panel = load_or_build_panel()
    fit_hazard_glm(panel)
