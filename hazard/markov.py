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
    *, allow_cohort_proxy: bool = False,
) -> pd.DataFrame:
    """
    Estimate monthly transition counts from consecutive servicer states per cohort.
    Falls back to literature-based priors when synthetic data lacks transitions.
    """
    if not allow_cohort_proxy:
        raise ValueError("Use identified loan histories; cohort-mode estimation requires explicit legacy opt-in")
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


def estimate_transitions_from_loans(histories, *, estimation_end, output=None,
                                   weighting="balance"):
    """Opening-to-closing monthly transitions; never infer a loan path from a mode.

    Only observations through the explicit cutoff are converted/validated as
    outcomes. Unsupported rows remain self-loops. Diagnostics expose skipped
    calendar gaps and zero-balance opening rows; no literature prior is injected.
    """
    if weighting not in {"balance", "count"}:
        raise ValueError("weighting must be balance or count")
    d = histories.to_pandas() if isinstance(histories, pl.DataFrame) else histories.copy()
    # DataFrame labels are not loan identities and may repeat after concatenation.
    d = d.reset_index(drop=True)
    required = {"loan_sequence_number", "reporting_period", "current_upb", "servicer_state"}
    if not required.issubset(d.columns):
        raise ValueError("Identified loan histories with dates, balances and states are required")
    end = str(estimation_end)
    if not pd.Series([end]).str.fullmatch(r"20\d{2}(0[1-9]|1[0-2])").all():
        raise ValueError("estimation_end must be YYYYMM")
    dates = d.reporting_period.astype(str)
    if not dates.str.fullmatch(r"20\d{2}(0[1-9]|1[0-2])").all():
        raise ValueError("Invalid reporting month")
    d = d.loc[dates <= end].copy()
    d["reporting_period"] = dates.loc[d.index]
    if d.loan_sequence_number.isna().any() or d.duplicated(["loan_sequence_number", "reporting_period"]).any():
        raise ValueError("Missing loan ID or duplicate loan-month")
    if not d.servicer_state.isin(MARKOV_STATES).all():
        raise ValueError("Unknown servicer state")
    d["current_upb"] = pd.to_numeric(d.current_upb, errors="raise")
    if not np.all(np.isfinite(d.current_upb) & (d.current_upb >= 0)):
        raise ValueError("Balances must be finite and nonnegative")
    d["month"] = pd.to_datetime(d.reporting_period, format="%Y%m").dt.to_period("M").astype("int64")
    d = d.sort_values(["loan_sequence_number", "month"])
    prev = d.groupby("loan_sequence_number")[["month", "current_upb", "servicer_state"]].shift(1)
    consecutive = (d.month - prev.month) == 1
    terminal = {"Prepaid", "Defaulted", "Liquidated"}
    if (prev.servicer_state.isin(terminal) & ~d.servicer_state.isin(terminal)).any():
        raise ValueError("Absorbing loan state resurrects into an active state")
    counts = pd.DataFrame(0., index=MARKOV_STATES, columns=MARKOV_STATES)
    supported = consecutive & (prev.current_upb > 0) & ~prev.servicer_state.isin(terminal)
    for ix in d.index[supported]:
        weight = float(prev.at[ix, "current_upb"]) if weighting == "balance" else 1.
        counts.at[prev.at[ix, "servicer_state"], d.at[ix, "servicer_state"]] += weight
    trans = counts.copy()
    totals = counts.sum(axis=1)
    for state in MARKOV_STATES:
        if totals[state] > 0:
            trans.loc[state] /= totals[state]
        else:
            trans.at[state, state] = 1.
    trans.index.name = "from_state"
    diagnostics = dict(estimation_end=end, weighting=weighting, eligible_rows=len(d),
        contiguous_pairs=int(consecutive.sum()), used_pairs=int(supported.sum()),
        gap_pairs_excluded=int((prev.month.notna() & ~consecutive).sum()),
        zero_opening_balance_pairs=int((consecutive & (prev.current_upb == 0)).sum()),
        unsupported_states=totals[totals == 0].index.tolist(),
        opening_weight_by_state=totals.to_dict(), counts=counts.to_dict(orient="index"))
    trans.attrs.update(estimator='identified_monthly_loan_transitions', estimation_end=end,
                       weighting=weighting)
    if output is not None:
        output = Path(output)
        if output.exists():
            raise FileExistsError("Preserve the prior matrix; choose a new output path")
        output.parent.mkdir(parents=True, exist_ok=True)
        trans.to_parquet(output)
    return trans, diagnostics


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
    import argparse
    import json
    parser = argparse.ArgumentParser(description="Estimate identified monthly loan transitions")
    parser.add_argument("--histories", type=Path, required=True)
    parser.add_argument("--end", required=True, help="Frozen YYYYMM estimation cutoff")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    # The source must already be an authorized, prepared local history extract.
    histories = pd.read_parquet(args.histories, filters=[("reporting_period", "<=", args.end)])
    _, diagnostics = estimate_transitions_from_loans(histories, estimation_end=args.end, output=args.output)
    args.output.with_suffix(".diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
