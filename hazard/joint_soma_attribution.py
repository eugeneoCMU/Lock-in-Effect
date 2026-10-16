"""Cell attribution for the saved-sample joint SOMA weighting sensitivity.

Uses value-preserving hooks around the production monthly step. Cell principal
changes are computed from before/after balances and reconciled to the engine's
aggregate scheduled-plus-prepaid principal each month. This is a model
allocation, not a causal subgroup estimate.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "abm", ROOT / "hazard"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import agents  # noqa: E402
import book_composition_marginal as prior  # noqa: E402
import competing_risks  # noqa: E402
import literature_hazard  # noqa: E402
import microsim_engine  # noqa: E402
from joint_soma_pair import BOOK, joint_reweight, targets  # noqa: E402
from literature_hazard import cpr_annual_to_monthly_hazard  # noqa: E402
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly  # noqa: E402

OUTPUT = ROOT / "hazard/data/joint_soma_attribution_results.json"


def score_leg(loans, empirical, macro, target, pq):
    cell_rolloff = defaultdict(float)
    bind_n = defaultdict(int)
    evaluated_n = defaultdict(int)
    max_reconcile_b = 0.0
    current = {"pool": None}
    original_step = microsim_engine.monthly_step
    original_prepay = competing_risks.prepay_hazard
    previous_reweight = agents.MicrosimPool.reweight_to_soma_coupons
    previous_fetch = microsim_engine.fetch_data
    index = macro.index[(macro.index >= prior.microsim_engine.QT_START) &
                        (macro.index < prior.microsim_engine.QT_END)]
    month = 0

    def cell_ids(pool):
        coupon = np.round(np.round((pool.coupon - 0.008) / 0.005) * 0.005, 4)
        vintage = np.where(pool.vintage <= 2019, "2017-19", pool.vintage.astype(str))
        return np.array([f"{c:.4f}|{v}" for c, v in zip(coupon, vintage)], dtype=object)

    def prepay(*args, **kwargs):
        out = original_prepay(*args, **kwargs)
        pool = current["pool"]
        if pool is not None and pool.regime == "US":
            active = pool.active_mask
            labels = cell_ids(pool)[active]
            current_floor = literature_hazard.INVOLUNTARY_CPR_ANNUAL
            literature_hazard.INVOLUNTARY_CPR_ANNUAL = 0.0
            try:
                voluntary = np.asarray(original_prepay(*args, **kwargs))
            finally:
                literature_hazard.INVOLUNTARY_CPR_ANNUAL = current_floor
            threshold = float(cpr_annual_to_monthly_hazard(
                np.array([current_floor], dtype=np.float64))[0])
            bound = voluntary < threshold
            for label in np.unique(labels):
                mask = labels == label
                evaluated_n[label] += int(mask.sum())
                bind_n[label] += int(bound[mask].sum())
        return out

    def step(pool, market_rate, trans, beta1):
        nonlocal month, max_reconcile_b
        current["pool"] = pool
        before = pool.balance.copy() if pool.regime == "US" else None
        result = original_step(pool, market_rate, trans=trans, beta1=beta1)
        if before is not None:
            ts = index[month]
            month += 1
            delta = before - pool.balance
            accounted = result["settled_b"] + result["sched_amt"]
            max_reconcile_b = max(max_reconcile_b, abs(delta.sum() - accounted) / 1e9)
            total_after_b = pool.total_exposure() / 1e9
            holdings_b = float(macro.loc[ts, "WSHOMCB"]) / 1000
            scale = holdings_b / max(total_after_b, 1e-6) if total_after_b > 0 else 1.0
            labels = cell_ids(pool)
            for label in np.unique(labels):
                cell_rolloff[label] += float(delta[labels == label].sum() * scale / 1e9)
        current["pool"] = None
        return result

    agents.MicrosimPool.reweight_to_soma_coupons = joint_reweight(target, {})
    microsim_engine.fetch_data = lambda *args, **kwargs: macro
    microsim_engine.monthly_step = step
    competing_risks.prepay_hazard = prepay
    literature_hazard.INVOLUNTARY_CPR_ANNUAL = prior.FLOOR
    try:
        out = prior.fs.SWEEP_DIR / f"joint_attribution_pq{pq:g}.parquet"
        microsim_engine.run_qt_microsim(loan_sample=loans, output=out,
                                        p_q_shock_pct=pq, soma_cohorts=[])
        from extension_risk import score_extension_risk
        import pandas as pd
        scored = score_extension_risk(pd.read_parquet(out), empirical)
    finally:
        agents.MicrosimPool.reweight_to_soma_coupons = previous_reweight
        microsim_engine.fetch_data = previous_fetch
        microsim_engine.monthly_step = original_step
        competing_risks.prepay_hazard = original_prepay
        literature_hazard.INVOLUNTARY_CPR_ANNUAL = prior.fs.PRODUCTION_FLOOR
    return {"trapped_b": float(scored["hazard_trapped_b"]),
            "rolloff_b_by_cell": dict(cell_rolloff),
            "bind_n_by_cell": dict(bind_n), "evaluated_n_by_cell": dict(evaluated_n),
            "max_monthly_principal_reconciliation_b": max_reconcile_b}


def main():
    book = json.loads(BOOK.read_text())
    target, mass = targets(book)
    prior_result = json.loads((ROOT / "hazard/data/joint_soma_pair_results.json").read_text())
    loans = pl.read_parquet(prior.fs.LOAN_SAMPLE_PATH)
    macro = fetch_data()
    empirical = build_empirical_metrics(macro, soma_rolloff=fetch_soma_mbs_monthly())
    off = score_leg(loans, empirical, macro, target, 0.0)
    on = score_leg(loans, empirical, macro, target, 6.5)
    if abs(off["trapped_b"] - prior_result["joint_pair"]["null_trapped_b"]) > 1e-8:
        raise RuntimeError("Response-off parity failed")
    if abs(on["trapped_b"] - prior_result["joint_pair"]["central_trapped_b"]) > 1e-8:
        raise RuntimeError("Response-on parity failed")
    keys = sorted(f"{coupon:.4f}|{vintage}" for coupon, vintage in target)
    cells = []
    for key in keys:
        off_roll = off["rolloff_b_by_cell"].get(key, 0.0)
        on_roll = on["rolloff_b_by_cell"].get(key, 0.0)
        n = on["evaluated_n_by_cell"].get(key, 0)
        cells.append({"cell": key, "marginal_trapped_b": off_roll - on_roll,
                      "response_on_floor_bind_share": on["bind_n_by_cell"].get(key, 0) / n if n else None,
                      "response_on_evaluated_loan_months": n})
    marginal = on["trapped_b"] - off["trapped_b"]
    if abs(sum(c["marginal_trapped_b"] for c in cells) - marginal) > 1e-7:
        raise RuntimeError("Cell marginals fail to sum to aggregate")
    if max(on["max_monthly_principal_reconciliation_b"],
           off["max_monthly_principal_reconciliation_b"]) > 1e-8:
        raise RuntimeError("Principal accounting failed")
    result = {"mode": "saved_sample_joint_cell_attribution",
              "book_as_of": book["soma_book"]["asof_june_2022"]["as_of"],
              "covered_total_soma_face_share": mass,
              "aggregate_marginal_b": marginal,
              "max_monthly_principal_reconciliation_b": max(
                  on["max_monthly_principal_reconciliation_b"],
                  off["max_monthly_principal_reconciliation_b"]),
              "cells": cells,
              "scope": "Model allocation within the saved Freddie sample reweighted to supported UMBS 30-year cells and rescaled to total holdings; not a contribution of the 47.6% book slice."}
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Wrote {len(cells)} cells; sum marginal ${marginal:.4f}B")


if __name__ == "__main__":
    main()
