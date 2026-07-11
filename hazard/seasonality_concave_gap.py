#!/usr/bin/env python3
"""
Seasonality (Path A) and concave-gap (Path B) robustness runs (§V.B / §V.C).

Part 1 — Seasonality. The paper names calendar-month effects as the first
suspect for Path A's negative monthly path correlation but deferred them.
This refits the production Poisson PML with 11 calendar-month dummies
(January reference) on the same training window, reports the seasonal
pattern and holdout RMSE, then forward-simulates the QT window with the
seasonal multipliers applied in-loop and rescores. A zero-seasonality run
through the same loop must reproduce the production $915.1B (parity gate).

Part 2 — Concave gap. Path B extrapolates the Liebersohn–Rothstein
elasticity log-linearly to QT-era gaps (~−380bp), flagged as an untested
functional form. This reruns Path B (U.S. regime, production sample, seed,
β₁) with a piecewise-concave transform: full marginal effect for the first
200bp of lock-in, half marginal beyond — the transform the limitations
section promised.

Run:  cd hazard && python3 seasonality_concave_gap.py
      → data/seasonality_concave_gap_results.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
import statsmodels.api as sm

import competing_risks
import literature_hazard
from config import (
    AGE_SPLINE_KNOTS,
    HAZARD_COEF_PATH,
    HOLDOUT_DATE,
    LOAN_SAMPLE_PATH,
    MICROSIM_RESULTS_PATH,
    PANEL_PATH,
    QT_END,
    QT_START,
    TERM_MONTHS,
)
from extension_risk import score_extension_risk
from hazard_fit import (
    _age_spline_basis,
    _fit_poisson_glm,
    _orthogonalize_burnout,
    enrich_panel_with_macro,
    load_burnout_age_adjust,
    load_predict_scales,
    predict_hazard,
)
from macro import (
    build_empirical_metrics,
    calculate_dynamic_friction,
    coupon_to_decimal,
    fetch_data,
    fetch_soma_mbs_monthly,
    scheduled_amortization_smm,
)
from microsim_engine import run_qt_microsim
from simulate import build_cohort_inventory
from stratum import build_stratum_id

DATA_DIR = Path(__file__).parent / "data"
OUT = DATA_DIR / "seasonality_concave_gap_results.json"
TMP = DATA_DIR / "_seasonality_tmp.parquet"

CONCAVE_KINK_PP = 2.0    # full marginal effect for the first 200bp of lock-in
CONCAVE_SLOPE2 = 0.5     # half marginal beyond the kink


def fit_with_month_dummies(train: pd.DataFrame, ridge_alpha: float):
    """Production design + 11 calendar-month dummies (January reference)."""
    age_basis = _age_spline_basis(train["loan_age"].to_numpy(), AGE_SPLINE_KNOTS)
    burn_demean = (
        train.groupby("stratum_id")["burnout"].transform(lambda s: s - s.mean()).to_numpy()
    )
    burnout_orth, _ = _orthogonalize_burnout(age_basis, burn_demean)
    z = lambda v: (v - v.mean()) / (v.std() or 1.0)
    months = pd.get_dummies(train["period"].dt.month, prefix="m", drop_first=True)
    month_cols = list(months.columns)  # m_2 … m_12
    fe = pd.get_dummies(train["stratum_id"], prefix="fe_stratum", drop_first=True)
    fe_cols = list(fe.columns)
    X = np.column_stack([
        age_basis,
        z(train["rate_gap_bps"].to_numpy()),
        burnout_orth / (burnout_orth.std() or 1.0),
        z(train["friction"].to_numpy()),
        months.to_numpy(dtype=np.float64),
        fe.to_numpy(dtype=np.float64),
    ])
    X = sm.add_constant(X, has_constant="add")
    names = (
        ["const", "age_linear"] + [f"age_spline_{k}" for k in AGE_SPLINE_KNOTS]
        + ["rate_gap_bps", "burnout_orth", "friction"] + month_cols + fe_cols
    )
    y = train["events"].to_numpy()
    offset = np.log(train["exposure"].to_numpy())
    result, method = _fit_poisson_glm(X, y, offset, ridge_alpha)
    params = np.asarray(result.params, dtype=np.float64).ravel()
    coefs = {names[i]: float(params[i]) for i in range(len(names))}
    month_effects = {1: 0.0}
    for c in month_cols:
        month_effects[int(c.split("_")[1])] = coefs[c]
    return coefs, month_effects, method


def simulate_with_seasonality(
    panel: pl.DataFrame,
    coefs: dict,
    month_effects: dict[int, float],
    macro: pd.DataFrame,
) -> pd.DataFrame:
    """simulate.simulate_qt_window's loop with an in-loop seasonal multiplier."""
    burnout_adj = load_burnout_age_adjust(HAZARD_COEF_PATH)
    scales = load_predict_scales(HAZARD_COEF_PATH)
    qt_index = macro.index[(macro.index >= QT_START) & (macro.index < QT_END)]
    cohorts = build_cohort_inventory(panel)

    meta = {}
    for _, row in cohorts.iterrows():
        key = (row["vintage"], row["coupon"], row["fico_bucket"], row["ltv_bucket"])
        meta[key] = dict(
            balance=row["balance"], burnout=row["burnout"], age=row["loan_age"],
            coupon=row["coupon"],
            sid=build_stratum_id(row["vintage"], row["coupon"],
                                 row["fico_bucket"], row["ltv_bucket"]),
        )
    balances = {k: v["balance"] for k, v in meta.items()}
    burn = {k: v["burnout"] for k, v in meta.items()}
    ages = {k: v["age"] for k, v in meta.items()}

    records = []
    for ts in qt_index:
        mkt = float(macro.loc[ts, "MORTGAGE30US"]) / 100.0
        fric = float(macro.loc[ts, "Dynamic_Friction"])
        season = float(np.exp(month_effects.get(ts.month, 0.0)))
        m_prepay = m_sched = 0.0
        bal_start = sum(balances.values())
        for key, bal in list(balances.items()):
            if bal <= 0:
                continue
            coupon = float(coupon_to_decimal(meta[key]["coupon"]))
            hazard = predict_hazard(
                ages[key], coupon - mkt, burn[key], fric, coefs,
                burnout_age_adjust=burnout_adj,
                stratum_id=meta[key]["sid"],
                reference_stratum=scales["reference_stratum"],
                fe_columns=scales["fe_columns"],
                friction_mean=scales["friction_mean"],
                friction_std=scales["friction_std"],
                rate_gap_bps_mean=scales["rate_gap_bps_mean"],
                rate_gap_bps_std=scales["rate_gap_bps_std"],
                burnout_demean_std=scales["burnout_demean_std"],
                stratum_burnout_mean=scales["stratum_burnout_mean"],
                fe_index=scales["fe_index"],
            ) * season
            sched = scheduled_amortization_smm(coupon, TERM_MONTHS, int(ages[key]))
            prepay_amt, sched_amt = bal * hazard, bal * sched
            balances[key] = max(bal - prepay_amt - sched_amt, 0)
            burn[key] = min(1.0, burn[key] + prepay_amt / max(bal, 1))
            ages[key] += 1
            m_prepay += prepay_amt
            m_sched += sched_amt
        holdings_b = float(macro.loc[ts, "WSHOMCB"]) / 1_000
        scale = holdings_b / max(bal_start / 1e9, 1e-6)
        records.append({
            "period": ts,
            "simulated_rolloff_b": -(m_prepay + m_sched) * scale / 1e9,
            "hazard_cpr_pct": (m_prepay / max(bal_start, 1)) * 12 * 100,
        })
    return pd.DataFrame(records).set_index("period")


def main() -> None:
    print("Fetching macro + benchmark …")
    macro = calculate_dynamic_friction(fetch_data())
    empirical = build_empirical_metrics(macro, soma_rolloff=fetch_soma_mbs_monthly())

    panel = pl.read_parquet(PANEL_PATH)
    prod_meta = json.load(open(HAZARD_COEF_PATH))
    ridge_alpha = float(prod_meta["ridge_alpha"])
    prod_coefs = dict(prod_meta["coefficients"])

    # ---------- Part 1: seasonality --------------------------------------
    print("\nPart 1 — Path A calendar-month effects")
    print("Parity gate: production coefficients through this loop …")
    sim0 = simulate_with_seasonality(panel, prod_coefs, {m: 0.0 for m in range(1, 13)}, macro)
    r0 = score_extension_risk(sim0, empirical)
    assert abs(r0["hazard_trapped_b"] - 915.1) < 1.0, r0["hazard_trapped_b"]
    print(f"  parity OK: ${r0['hazard_trapped_b']:.1f}B, "
          f"r(lag0)={r0['cross_correlation'].get(0):+.3f}")

    pdf = enrich_panel_with_macro(panel)
    pdf = pdf.dropna(subset=["rate_gap_bps", "exposure", "loan_age", "stratum_id"])
    pdf = pdf[pdf["exposure"] > 0]
    train = pdf[pdf["period"] < HOLDOUT_DATE].copy()

    print(f"Refitting with month dummies (alpha={ridge_alpha:g}) …")
    coefs_s, month_effects, method = fit_with_month_dummies(train, ridge_alpha)
    print("  seasonal log-effects (Jan = 0): "
          + ", ".join(f"{m}:{v:+.3f}" for m, v in sorted(month_effects.items())))

    sim_s = simulate_with_seasonality(panel, coefs_s, month_effects, macro)
    rs = score_extension_risk(sim_s, empirical)
    print(f"  seasonal run: ${rs['hazard_trapped_b']:.1f}B "
          f"({rs['share_explained_pct']:.1f}%)  "
          f"r(lag0)={rs['cross_correlation'].get(0):+.3f}  peak lag {rs['best_lag']}")

    # ---------- Part 2: concave gap --------------------------------------
    print("\nPart 2 — Path B piecewise-concave gap transform")
    loans = pl.read_parquet(LOAN_SAMPLE_PATH)
    original_prepay = competing_risks.prepay_hazard

    def concave_prepay(loan_age, rate_gap, burnout, fico_z, ltv_z, beta1, coefs=None):
        g_pp = np.abs(rate_gap) * 100.0
        g_concave = np.minimum(g_pp, CONCAVE_KINK_PP) + CONCAVE_SLOPE2 * np.maximum(
            g_pp - CONCAVE_KINK_PP, 0.0
        )
        gap_t = np.sign(rate_gap) * g_concave / 100.0
        return original_prepay(loan_age, gap_t, burnout, fico_z, ltv_z,
                               beta1=beta1, coefs=coefs)

    try:
        competing_risks.prepay_hazard = concave_prepay
        paths = run_qt_microsim(loan_sample=loans, macro=macro, regimes=("US",), output=TMP)
        rc = score_extension_risk(paths["US"], empirical)
    finally:
        competing_risks.prepay_hazard = original_prepay
        if TMP.exists():
            TMP.unlink()
    print(f"  concave run: ${rc['hazard_trapped_b']:.1f}B "
          f"({rc['share_explained_pct']:.1f}%)  "
          f"r(lag0)={rc['cross_correlation'].get(0):+.3f}  peak lag {rc['best_lag']}")

    central = score_extension_risk(pd.read_parquet(MICROSIM_RESULTS_PATH), empirical)

    payload = {
        "mode": "seasonality_concave_gap",
        "path_a_seasonality": {
            "fit_method": method,
            "month_log_effects_jan0": month_effects,
            "production": {
                "trapped_b": r0["hazard_trapped_b"],
                "share_pct": r0["share_explained_pct"],
                "r_lag0": r0["cross_correlation"].get(0),
                "peak_lag": r0["best_lag"],
            },
            "seasonal": {
                "trapped_b": rs["hazard_trapped_b"],
                "share_pct": rs["share_explained_pct"],
                "r_lag0": rs["cross_correlation"].get(0),
                "peak_lag": rs["best_lag"],
            },
        },
        "path_b_concave_gap": {
            "kink_pp": CONCAVE_KINK_PP,
            "slope_beyond": CONCAVE_SLOPE2,
            "production": {
                "trapped_b": central["hazard_trapped_b"],
                "share_pct": central["share_explained_pct"],
                "r_lag0": central["cross_correlation"].get(0),
            },
            "concave": {
                "trapped_b": rc["hazard_trapped_b"],
                "share_pct": rc["share_explained_pct"],
                "r_lag0": rc["cross_correlation"].get(0),
                "peak_lag": rc["best_lag"],
            },
        },
    }
    OUT.write_text(json.dumps(
        payload, indent=2,
        default=lambda x: float(x) if isinstance(x, (np.floating, np.integer)) else x,
    ) + "\n")
    print(f"\nSaved: {OUT}")


if __name__ == "__main__":
    main()
