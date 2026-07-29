"""
Forward QT-window microsim: dual US/Danish regime pools on same loan sample.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import polars as pl

from agents import MicrosimPool
from competing_risks import monthly_step
from config import (
    MICROSIM_RESULTS_PATH,
    N_LOANS,
    QT_END,
    QT_START,
    RNG_SEED,
    ROTHSTEIN_Q_DECLINE_MID,
)
from literature_hazard import rothstein_beta1
from loan_sample import load_or_build_loan_sample
from macro import calculate_dynamic_friction, fetch_data
from markov import load_transition_matrix


def _simulate_regime(
    loan_df: pl.DataFrame,
    macro: pd.DataFrame,
    regime: str,
    holdings_scale_b: float,
    trans: pd.DataFrame,
    seed: int,
    beta1: float,
    soma_cohorts: Optional[list] = None,
    coupon_convert=None,
) -> pd.DataFrame:
    """Walk one regime pool through QT window."""
    qt_index = macro.index[(macro.index >= QT_START) & (macro.index < QT_END)]
    pool = MicrosimPool(loan_df, regime=regime, rng=np.random.default_rng(seed))
    if soma_cohorts is not None:
        pool.reweight_to_soma_coupons(  # full-book weighting (3.1)
            soma_cohorts, coupon_convert=coupon_convert)
    pool.scale_to_holdings(holdings_scale_b)

    records = []
    for ts in qt_index:
        mkt = float(macro.loc[ts, "MORTGAGE30US"]) / 100.0
        result = monthly_step(pool, mkt, trans=trans, beta1=beta1)

        exposure = result["exposure"]
        monthly_cpr = (result["prepay_upb"] / exposure) if exposure > 0 else 0.0
        annual_cpr_pct = monthly_cpr * 12 * 100

        total_bal = pool.total_exposure()
        holdings_b = float(macro.loc[ts, "WSHOMCB"]) / 1_000
        scale = holdings_b / max(total_bal / 1e9, 1e-6) if total_bal > 0 else 1.0

        sched_b = result["sched_amt"] * scale / 1e9
        settled_b = result["settled_b"] * scale / 1e9
        sim_rolloff = -(settled_b + sched_b)

        records.append({
            "period": ts,
            "regime": regime,
            "market_rate_pct": mkt * 100,
            "hazard_cpr_pct": annual_cpr_pct,
            "prepay_upb": result["prepay_upb"],
            "exposure": exposure,
            "simulated_rolloff_b": sim_rolloff,
            "weighted_settled_b": settled_b,
            "weighted_sched_b": sched_b,
            "default_count": result["default_count"],
            "delinquency_stock": int(
                np.isin(pool.state_code, [1, 2, 3, 4]).sum()
            ),
        })

    return pd.DataFrame(records).set_index("period")


def run_qt_microsim(
    loan_sample: Optional[pl.DataFrame] = None,
    macro: Optional[pd.DataFrame] = None,
    n_loans: int = N_LOANS,
    regimes: tuple = ("US", "Danish"),
    seed: int = RNG_SEED,
    output: Path = MICROSIM_RESULTS_PATH,
    p_q_shock_pct: float = ROTHSTEIN_Q_DECLINE_MID * 100,
    soma_cohorts: Optional[list] = None,
    coupon_convert=None,
) -> dict[str, pd.DataFrame]:
    """
    Forward-walk loan sample through QT window under US and Danish rate-gap regimes.

    p_q_shock_pct: Rothstein quarterly mobility decline per 100bp rate gap,
    in percent (sensitivity band 5.5–7.7, midpoint 6.5).  β₁ is derived via
    the survival-function conversion — same loan sample and RNG seeds across
    band points, so only the elasticity varies.
    """
    beta1 = rothstein_beta1(p_q_shock_pct / 100.0)
    if loan_sample is None:
        loan_sample = load_or_build_loan_sample(n_loans=n_loans)
    if macro is None:
        macro = calculate_dynamic_friction(fetch_data())

    trans = load_transition_matrix()
    qt_start_idx = macro.index.get_indexer([QT_START], method="nearest")[0]
    holdings_b = float(macro.iloc[qt_start_idx]["WSHOMCB"]) / 1_000

    results = {}
    for i, regime in enumerate(regimes):
        print(f"  Simulating {regime} regime (P_q shock {p_q_shock_pct:.1f}%, β₁={beta1:.4f}) …")
        results[regime] = _simulate_regime(
            loan_sample,
            macro,
            regime,
            holdings_b,
            trans,
            seed=seed + i * 1000,
            beta1=beta1,
            soma_cohorts=soma_cohorts,
            coupon_convert=coupon_convert,
        )

    # Combined output for extension-risk scoring (US primary)
    us = results.get("US", results[regimes[0]])
    dk = results.get("Danish", us)
    combined = us.copy()
    combined["CPR_US"] = us["hazard_cpr_pct"]
    combined["CPR_Danish"] = dk.reindex(us.index)["hazard_cpr_pct"]
    combined["Danish_simulated_rolloff_b"] = dk.reindex(us.index)["simulated_rolloff_b"]

    output.parent.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(output)
    print(f"Microsim results saved to {output} ({len(combined)} QT months)")
    return results


if __name__ == "__main__":
    print("Building loan sample …")
    loans = load_or_build_loan_sample(force_rebuild=False)
    print(f"Running microsim on {len(loans):,} loans …")
    paths = run_qt_microsim(loan_sample=loans)
    for regime, df in paths.items():
        print(f"  {regime}: mean CPR = {df['hazard_cpr_pct'].mean():.2f}%")
