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
from hazard_fit import load_coefficients, predict_hazard
from macro import (
    fetch_data,
    calculate_dynamic_friction,
    scheduled_amortization_smm,
)
from markov import load_transition_matrix, route_through_pipeline


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


def simulate_qt_window(
    panel: Optional[pl.DataFrame] = None,
    coefs: Optional[dict] = None,
    trans: Optional[pd.DataFrame] = None,
    output: Path = SIM_RESULTS_PATH,
) -> pd.DataFrame:
    """
    Forward-walk cohort balances through QT window on actual rate path.
    """
    if panel is None:
        panel = pl.read_parquet(PANEL_PATH)
    if coefs is None:
        coefs = load_coefficients(HAZARD_COEF_PATH)
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
            "weight": row["balance"] / total_balance if total_balance > 0 else 0,
        }

    balances = {k: v["balance"] for k, v in cohort_meta.items()}
    burnout_state = {k: v["burnout"] for k, v in cohort_meta.items()}
    ages = {k: v["loan_age"] for k, v in cohort_meta.items()}
    coupons = {k: v["coupon"] for k, v in cohort_meta.items()}
    weights = {k: v["weight"] for k, v in cohort_meta.items()}

    records = []
    for ts in qt_index:
        mkt = float(macro.loc[ts, "MORTGAGE30US"]) / 100.0
        fric = float(macro.loc[ts, "Dynamic_Friction"])
        month_prepay = 0.0
        month_sched = 0.0
        month_settled = 0.0

        for key in list(balances.keys()):
            bal = balances[key]
            if bal <= 0:
                continue
            coupon = coupons[key]
            age = ages[key]
            burnout = burnout_state[key]
            gap = coupon - mkt

            hazard = predict_hazard(age, gap, burnout, fric, coefs)
            sched = scheduled_amortization_smm(coupon, TERM_MONTHS, int(age))

            prepay_amt = bal * hazard
            sched_amt = bal * sched
            drain = prepay_amt + sched_amt

            # Route prepayment through Markov servicer pipeline
            settled = route_through_pipeline(prepay_amt, trans, max_steps=3)
            settled_total = sum(settled.values())

            balances[key] = max(bal - drain, 0)
            burnout_state[key] = min(1.0, burnout + prepay_amt / max(bal, 1))
            ages[key] = age + 1

            w = weights[key]

            month_prepay += w * prepay_amt
            month_sched += w * sched_amt
            month_settled += w * settled_total

        total_bal = sum(balances.values())
        # Scale to Fed portfolio ($B): normalize cohort UPB to WSHOMCB at QT start
        holdings_b = float(macro.loc[ts, "WSHOMCB"]) / 1_000
        scale = holdings_b / max(total_bal / 1e9, 1e-6)

        records.append({
            "period": ts,
            "market_rate_pct": mkt * 100,
            "friction": fric,
            "total_balance": total_bal,
            "weighted_prepay_b": month_prepay * scale / 1e9,
            "weighted_sched_b": month_sched * scale / 1e9,
            "weighted_settled_b": month_settled * scale / 1e9,
            "simulated_rolloff_b": -(month_settled + month_sched) * scale / 1e9,
            "hazard_cpr_pct": (month_prepay / max(total_bal, 1)) * 12 * 100,
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
