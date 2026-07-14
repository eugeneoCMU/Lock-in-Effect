"""
Fractional-cohort forward simulation over the QT window.

Hazard drains balances continuously; Markov chain routes prepayments
through the servicer pipeline before they reach SOMA roll-off.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import polars as pl

from config import (
    HAZARD_COEF_PATH,
    MARKOV_MATRIX_PATH,
    PANEL_PATH,
    QT_END,
    QT_START,
    SIM_RESULTS_PATH,
    TERM_MONTHS,
)
from hazard_fit import (
    load_burnout_age_adjust,
    load_coefficients,
    load_month_effects,
    load_predict_scales,
    predict_hazard,
)
from stratum import build_stratum_id
from macro import (
    coupon_to_decimal,
    fetch_data,
    calculate_dynamic_friction,
    scheduled_amortization_smm,
)
from markov import load_transition_matrix


def _cohort_key(row) -> tuple:
    return (row["vintage"], row["coupon"], row["fico_bucket"], row["ltv_bucket"])


def build_cohort_inventory(panel: pl.DataFrame) -> pd.DataFrame:
    """Latest pre-QT balance per cohort from the panel."""
    pdf = panel.to_pandas()
    pdf["period"] = pd.to_datetime(pdf["period"])
    pre_qt = pdf[pdf["period"] < QT_START]
    if pre_qt.empty:
        pre_qt = pdf
    latest = (
        pre_qt.sort_values("period")
        .groupby(["vintage", "coupon", "fico_bucket", "ltv_bucket"])
        .last()
        .reset_index()
    )
    latest["balance"] = latest["exposure_upb"]
    latest["burnout"] = latest["burnout"].fillna(0)
    latest["loan_age"] = latest["mean_loan_age"].fillna(36)
    return latest


def _reweight_balances_to_soma(balances: dict, coupons: dict,
                               soma_cohorts: list) -> dict:
    """
    Full-book weighting (roadmap 3.1): rescale per-cohort balances so the
    coupon-bucket composition matches the SOMA book instead of the Freddie
    panel's own mix. Returns a new balances dict (total is renormalized by the
    caller's soma_scale afterward).
    """
    step = 0.005
    soma_share: dict = {}
    for c in soma_cohorts:
        if int(c.get("term_months", 360)) != 360:
            continue
        b = round(round(float(c["coupon"]) / step) * step, 4)
        soma_share[b] = soma_share.get(b, 0.0) + float(c["weight"])
    tot = sum(soma_share.values())
    if tot <= 0:
        return balances
    soma_share = {k: v / tot for k, v in soma_share.items()}

    total_bal = sum(balances.values())
    if total_bal <= 0:
        return balances
    cur_share: dict = {}
    for key, bal in balances.items():
        b = round(round(float(coupons[key]) / step) * step, 4)
        cur_share[b] = cur_share.get(b, 0.0) + bal / total_bal

    out = {}
    for key, bal in balances.items():
        b = round(round(float(coupons[key]) / step) * step, 4)
        w = (soma_share.get(b, 0.0) / cur_share[b]) if cur_share.get(b, 0) > 0 else 0.0
        out[key] = bal * w
    return out


def simulate_qt_window(
    panel: Optional[pl.DataFrame] = None,
    coefs: Optional[dict] = None,
    trans: Optional[pd.DataFrame] = None,
    output: Path = SIM_RESULTS_PATH,
    soma_cohorts: Optional[list] = None,
    coef_path: Path = HAZARD_COEF_PATH,
) -> pd.DataFrame:
    """
    Forward-walk cohort balances through QT window on actual rate path.

    Under a spec-v4 coefficients artifact (freeze item (i)) the artifact's
    month_effects enter as an in-loop seasonal multiplier exp(effect[month]),
    January = 0 — the committed seasonal robustness run's convention. A v3
    artifact has no month_effects, so the multiplier is exp(0) = 1 and the
    pre-adoption behavior is reproduced exactly.
    """
    if panel is None:
        panel = pl.read_parquet(PANEL_PATH)
    if coefs is None:
        coefs = load_coefficients(coef_path)
    burnout_adj = load_burnout_age_adjust(coef_path)
    scales = load_predict_scales(coef_path)
    month_effects = load_month_effects(coef_path)
    if trans is None:
        trans = load_transition_matrix(MARKOV_MATRIX_PATH)

    macro = calculate_dynamic_friction(fetch_data())
    qt_index = macro.index[(macro.index >= QT_START) & (macro.index < QT_END)]
    cohorts = build_cohort_inventory(panel)

    total_balance = cohorts["balance"].sum()
    cohort_meta = {}
    for _, row in cohorts.iterrows():
        key = _cohort_key(row)
        cohort_meta[key] = {
            "balance": row["balance"],
            "burnout": row["burnout"],
            "loan_age": row["loan_age"],
            "coupon": row["coupon"],
            "stratum_id": build_stratum_id(
                row["vintage"], row["coupon"], row["fico_bucket"], row["ltv_bucket"]
            ),
        }

    balances = {k: v["balance"] for k, v in cohort_meta.items()}
    burnout_state = {k: v["burnout"] for k, v in cohort_meta.items()}
    ages = {k: v["loan_age"] for k, v in cohort_meta.items()}
    coupons = {k: v["coupon"] for k, v in cohort_meta.items()}
    stratum_ids = {k: v["stratum_id"] for k, v in cohort_meta.items()}

    if soma_cohorts is not None:
        balances = _reweight_balances_to_soma(balances, coupons, soma_cohorts)
        total_balance = sum(balances.values())

    holdings_at_qt = float(
        macro.loc[qt_index[0], "WSHOMCB"]
    ) / 1_000 if len(qt_index) else 0.0
    soma_scale = holdings_at_qt / max(total_balance / 1e9, 1e-6)
    print(f"Cohort UPB: ${total_balance/1e9:.1f}B  |  SOMA scale: {soma_scale:.3f}x")

    records = []
    for ts in qt_index:
        mkt = float(macro.loc[ts, "MORTGAGE30US"]) / 100.0
        fric = float(macro.loc[ts, "Dynamic_Friction"])
        season = float(np.exp(month_effects.get(ts.month, 0.0)))
        month_prepay = 0.0
        month_sched = 0.0
        month_settled = 0.0
        total_bal_start = sum(balances.values())

        for key in list(balances.keys()):
            bal = balances[key]
            if bal <= 0:
                continue
            coupon = float(coupon_to_decimal(coupons[key]))
            age = ages[key]
            burnout = burnout_state[key]
            gap = coupon - mkt

            hazard = predict_hazard(
                age, gap, burnout, fric, coefs,
                burnout_age_adjust=burnout_adj,
                stratum_id=stratum_ids[key],
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
            sched = scheduled_amortization_smm(coupon, TERM_MONTHS, int(age))

            prepay_amt = bal * hazard
            sched_amt = bal * sched
            drain = prepay_amt + sched_amt

            settled_total = prepay_amt

            balances[key] = max(bal - drain, 0)
            burnout_state[key] = min(1.0, burnout + prepay_amt / max(bal, 1))
            ages[key] = age + 1

            month_prepay += prepay_amt
            month_sched += sched_amt
            month_settled += settled_total

        total_bal = sum(balances.values())
        holdings_b = float(macro.loc[ts, "WSHOMCB"]) / 1_000
        scale = holdings_b / max(total_bal_start / 1e9, 1e-6)

        records.append({
            "period": ts,
            "market_rate_pct": mkt * 100,
            "friction": fric,
            "total_balance": total_bal,
            "weighted_prepay_b": month_prepay * scale / 1e9,
            "weighted_sched_b": month_sched * scale / 1e9,
            "weighted_settled_b": month_settled * scale / 1e9,
            "simulated_rolloff_b": -(month_settled + month_sched) * scale / 1e9,
            "hazard_cpr_pct": (
                (month_prepay / max(total_bal_start, 1)) * 12 * 100
            ),
        })

    sim = pd.DataFrame(records).set_index("period")
    output.parent.mkdir(parents=True, exist_ok=True)
    sim.to_parquet(output)
    print(f"Simulation saved to {output} ({len(sim)} QT months)")
    return sim


if __name__ == "__main__":
    from ingest import load_or_build_panel
    panel = load_or_build_panel()
    simulate_qt_window(panel)
