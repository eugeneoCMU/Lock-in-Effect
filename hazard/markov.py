"""
Markov servicer-pipeline transition matrix from observed loan-level states.

States: Current → D30 → D60 → D90+ → Forbearance → Defaulted → Liquidated
        (+ absorbing Prepaid from any active state)
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import polars as pl

from config import MARKOV_MATRIX_PATH, MARKOV_STATES, PANEL_PATH


def _state_index() -> dict[str, int]:
    return {s: i for i, s in enumerate(MARKOV_STATES)}


def estimate_transitions_from_panel(
    panel: Optional[pl.DataFrame] = None,
    output: Path = MARKOV_MATRIX_PATH,
) -> pd.DataFrame:
    """
    Estimate monthly transition counts from consecutive servicer states per cohort.
    Falls back to literature-based priors when synthetic data lacks transitions.
    """
    if panel is None:
        panel = pl.read_parquet(PANEL_PATH)

    pdf = panel.to_pandas()
    pdf["period"] = pd.to_datetime(pdf["period"])
    pdf = pdf.sort_values(["vintage", "coupon", "fico_bucket", "ltv_bucket", "period"])
    pdf["prev_state"] = pdf.groupby(
        ["vintage", "coupon", "fico_bucket", "ltv_bucket"]
    )["mode_state"].shift(1)

    idx = _state_index()
    counts = np.zeros((len(MARKOV_STATES), len(MARKOV_STATES)))

    valid = pdf.dropna(subset=["prev_state", "mode_state"])
    for _, row in valid.iterrows():
        s_from = row["prev_state"] if row["prev_state"] in idx else "Current"
        s_to = row["mode_state"] if row["mode_state"] in idx else "Current"
        w = row.get("exposure_upb", 1) or 1
        counts[idx[s_from], idx[s_to]] += w

    row_sums = counts.sum(axis=1, keepdims=True)
    off_diag = counts.sum() - np.trace(counts)
    if row_sums.sum() == 0 or off_diag < 1e-6:
        # Literature-based servicer pipeline priors (monthly)
        trans = pd.DataFrame(0.0, index=MARKOV_STATES, columns=MARKOV_STATES)
        trans.loc["Current", "Current"] = 0.97
        trans.loc["Current", "D30"] = 0.01
        trans.loc["Current", "Prepaid"] = 0.02
        trans.loc["D30", "Current"] = 0.30
        trans.loc["D30", "D60"] = 0.40
        trans.loc["D30", "Prepaid"] = 0.05
        trans.loc["D60", "D30"] = 0.20
        trans.loc["D60", "D90+"] = 0.50
        trans.loc["D60", "Forbearance"] = 0.10
        trans.loc["D90+", "Defaulted"] = 0.15
        trans.loc["D90+", "D90+"] = 0.80
        trans.loc["Forbearance", "Current"] = 0.40
        trans.loc["Forbearance", "D90+"] = 0.20
        trans.loc["Forbearance", "Forbearance"] = 0.35
        trans.loc["Defaulted", "Liquidated"] = 0.10
        trans.loc["Defaulted", "Defaulted"] = 0.90
        trans.loc["Prepaid", "Prepaid"] = 1.0
        trans.loc["Liquidated", "Liquidated"] = 1.0
        print("Using literature-based Markov priors (insufficient transitions in panel).")
    else:
        row_sums[row_sums == 0] = 1
        trans = pd.DataFrame(counts / row_sums, index=MARKOV_STATES, columns=MARKOV_STATES)

    trans.index.name = "from_state"
    output.parent.mkdir(parents=True, exist_ok=True)
    trans.to_parquet(output)
    print(f"Markov transition matrix saved to {output}")
    print(trans.round(3).to_string())
    return trans


def route_through_pipeline(
    amount: float,
    trans: pd.DataFrame,
    start_state: str = "Current",
    max_steps: int = 6,
) -> dict[str, float]:
    """
    Distribute `amount` through the Markov pipeline over max_steps months.
    Returns cash settled by month (from Prepaid + Liquidated absorbers).
    """
    idx = _state_index()
    dist = np.zeros(len(MARKOV_STATES))
    dist[idx.get(start_state, 0)] = amount
    T = trans.to_numpy()
    settled_by_month = {}

    for step in range(max_steps):
        dist = dist @ T
        prepaid = dist[idx["Prepaid"]]
        liquidated = dist[idx["Liquidated"]]
        settled = prepaid + liquidated
        settled_by_month[step] = settled
        # Remove mass from absorbers for next step (stay absorbed)
        dist[idx["Prepaid"]] = 0
        dist[idx["Liquidated"]] = 0

    return settled_by_month


def load_transition_matrix(path: Path = MARKOV_MATRIX_PATH) -> pd.DataFrame:
    return pd.read_parquet(path)


if __name__ == "__main__":
    estimate_transitions_from_panel()
