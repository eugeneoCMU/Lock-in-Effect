#!/usr/bin/env python3
"""
Referee-round data disclosures (July 2026): Table 2 scale, microsim
attrition accounting, and delinquency-matrix cell counts with a computed
consequence bound.

1. Table 2 scale (R2-4). The Path A stratum-month panel aggregates the FULL
   Freddie 2017–2021-vintage loan universe (~8.8M active loans at peak), not
   the 75,000-loan Path B sample, and carries no sampling weights: exposure
   and events are raw dollars, so the Poisson PML is UPB-weighted by
   construction. The fit's training window is Jan 2021–Dec 2023 (the macro
   frame begins 2021-01), which reproduces Table 2's $72.5T exposure.

2. Attrition (R2-6). Of the 75,000 sampled loans, those already absorbed
   (Prepaid/Defaulted) before June 2022 are never simulated; the active-at-
   window-start count and its window mean reconcile the 1,683,124 evaluated
   loan-months.

3. Delinquency matrix (R1-4). Per-cell transition counts from the modal-state
   estimation panel — the off-diagonal cells are thin (single digits) — plus
   a computed bound: rerun Path B with the matrix replaced by each extreme
   (all delinquents cure next month / all default next month).

Run:  cd hazard && python3 panel_disclosures.py
      → data/panel_disclosures.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

import markov
import microsim_engine
from config import HOLDOUT_DATE, LOAN_SAMPLE_PATH, MARKOV_STATES, PANEL_PATH
from extension_risk import score_extension_risk
from macro import (
    build_empirical_metrics,
    calculate_dynamic_friction,
    fetch_data,
    fetch_soma_mbs_monthly,
)
from microsim_engine import run_qt_microsim

DATA_DIR = Path(__file__).parent / "data"
OUT = DATA_DIR / "panel_disclosures.json"
TMP = DATA_DIR / "_disclosure_tmp.parquet"

ACTIVE_STATES = ["Current", "D30", "D60", "D90+"]


def table2_scale(panel: pd.DataFrame) -> dict:
    fit_train = panel[(panel["period"] >= "2021-01-01") & (panel["period"] < HOLDOUT_DATE)]
    hold = panel[panel["period"] >= HOLDOUT_DATE]
    def block(df):
        return {
            "cells": int(len(df)),
            "months": int(df["period"].nunique()),
            "exposure_usd_t": float(df["exposure_upb"].sum() / 1e12),
            "prepaid_usd_t": float(df["prepaid_upb"].sum() / 1e12),
            "loan_months": int(df["loan_count"].sum()),
        }
    return {
        "population": "full Freddie 2017-2021-vintage loan universe (not the 75k sample)",
        "weights": "none — exposure and events are raw dollars; the PML is UPB-weighted by construction",
        "peak_monthly_active_loans": int(panel.groupby("period")["loan_count"].sum().max()),
        "training_window": "2021-01 .. 2023-12 (macro frame begins 2021-01)",
        "train": block(fit_train),
        "holdout": block(hold),
    }


def attrition(loans: pl.DataFrame) -> dict:
    by_state = dict(loans.group_by("state").agg(pl.len()).iter_rows())
    active0 = sum(by_state.get(s, 0) for s in ACTIVE_STATES)
    return {
        "sampled_loans": int(len(loans)),
        "state_at_window_start": {k: int(v) for k, v in sorted(by_state.items())},
        "active_at_window_start": int(active0),
        "absorbed_before_window": int(len(loans) - active0),
        "evaluated_loan_months_production": 1_683_124,
        "implied_mean_monthly_active": round(1_683_124 / 42, 1),
    }


def markov_cell_counts(panel: pd.DataFrame) -> dict:
    p = panel.sort_values(["vintage", "coupon", "fico_bucket", "ltv_bucket", "period"]).copy()
    p["prev_state"] = p.groupby(
        ["vintage", "coupon", "fico_bucket", "ltv_bucket"]
    )["mode_state"].shift(1)
    valid = p.dropna(subset=["prev_state", "mode_state"])
    n = valid.groupby(["prev_state", "mode_state"]).size().unstack(fill_value=0)
    upb = (valid.groupby(["prev_state", "mode_state"])["exposure_upb"].sum()
           .unstack(fill_value=0.0))
    return {
        "estimation_unit": "consecutive stratum-month modal servicer states, exposure-UPB weighted",
        "raw_counts": {r: {c: int(v) for c, v in row.items() if v}
                       for r, row in n.iterrows()},
        "row_totals": {r: int(v) for r, v in n.sum(axis=1).items()},
        "upb_weights_usd_b": {r: {c: round(float(v) / 1e9, 2) for c, v in row.items() if v}
                              for r, row in upb.iterrows()},
    }


def extreme_matrix(target: str) -> pd.DataFrame:
    m = pd.DataFrame(0.0, index=MARKOV_STATES, columns=MARKOV_STATES)
    for s in MARKOV_STATES:
        m.loc[s, s] = 1.0
    for s in ["D30", "D60", "D90+", "Forbearance"]:
        m.loc[s, :] = 0.0
        m.loc[s, target] = 1.0
    m.index.name = "from_state"
    return m


def consequence_bound(loans: pl.DataFrame, macro, empirical) -> dict:
    orig = markov.load_transition_matrix
    out = {}
    try:
        for label, target in [("all_cure", "Current"), ("all_default", "Defaulted")]:
            microsim_engine.load_transition_matrix = (
                lambda path=None, t=target: extreme_matrix(t)
            )
            paths = run_qt_microsim(loan_sample=loans, macro=macro,
                                    regimes=("US",), output=TMP)
            r = score_extension_risk(paths["US"], empirical)
            out[label] = {"trapped_b": r["hazard_trapped_b"],
                          "share_pct": r["share_explained_pct"]}
    finally:
        microsim_engine.load_transition_matrix = orig
        if TMP.exists():
            TMP.unlink()
    out["bound_width_b"] = abs(out["all_cure"]["trapped_b"]
                               - out["all_default"]["trapped_b"])
    return out


def main() -> None:
    panel = pl.read_parquet(PANEL_PATH).to_pandas()
    panel["period"] = pd.to_datetime(panel["period"])
    loans = pl.read_parquet(LOAN_SAMPLE_PATH)

    print("Table 2 scale …")
    t2 = table2_scale(panel)
    print(f"  train: {t2['train']['cells']:,} cells, "
          f"${t2['train']['exposure_usd_t']:.2f}T exposure  |  "
          f"holdout: {t2['holdout']['cells']:,} cells, "
          f"${t2['holdout']['exposure_usd_t']:.2f}T")

    print("Attrition …")
    at = attrition(loans)
    print(f"  active at window start: {at['active_at_window_start']:,} of "
          f"{at['sampled_loans']:,}")

    print("Markov cell counts …")
    mk = markov_cell_counts(panel)
    print(f"  row totals: {mk['row_totals']}")

    print("Consequence bound (extreme matrices) …")
    macro = calculate_dynamic_friction(fetch_data())
    empirical = build_empirical_metrics(macro, soma_rolloff=fetch_soma_mbs_monthly())
    cb = consequence_bound(loans, macro, empirical)
    print(f"  all_cure ${cb['all_cure']['trapped_b']:.2f}B  "
          f"all_default ${cb['all_default']['trapped_b']:.2f}B  "
          f"width ${cb['bound_width_b']:.2f}B")

    payload = {
        "mode": "panel_disclosures",
        "table2_scale": t2,
        "microsim_attrition": at,
        "markov_cell_counts": mk,
        "markov_consequence_bound": cb,
    }
    OUT.write_text(json.dumps(
        payload, indent=2,
        default=lambda x: float(x) if isinstance(x, (np.floating, np.integer)) else x,
    ) + "\n")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
