"""
Regime-specific rate gap for U.S. par-payoff vs Danish market-value buyback.

Only rate_gap_* swaps between regimes; all other hazard parameters identical.
"""

from __future__ import annotations

import numpy as np

from config import TERM_MONTHS


def rate_gap_us(coupon: np.ndarray, market_rate: float) -> np.ndarray:
    """Standard gap: coupon minus market rate (decimal)."""
    return coupon - market_rate


def _monthly_payment(balance: np.ndarray, annual_rate: np.ndarray, n_rem: np.ndarray) -> np.ndarray:
    r = annual_rate / 12.0
    n = np.maximum(n_rem, 1).astype(np.float64)
    with np.errstate(divide="ignore", invalid="ignore"):
        pmt = np.where(
            r > 0,
            balance * r / (1.0 - (1.0 + r) ** (-n)),
            balance / n,
        )
    return pmt


def rate_gap_danish(
    coupon: np.ndarray,
    market_rate: float,
    balance: np.ndarray,
    loan_age: np.ndarray,
    term_months: int = TERM_MONTHS,
) -> np.ndarray:
    """
    Market-value gap: (PV of remaining payments at market rate / balance) - 1.

    When rates rise above coupon, PV < par → gap approaches 0 or positive,
    neutralizing lock-in relative to U.S. par-payoff.
    """
    n_rem = np.maximum(term_months - loan_age, 1).astype(np.float64)
    pmt = _monthly_payment(balance, coupon, n_rem)
    r_mkt = market_rate / 12.0
    with np.errstate(divide="ignore", invalid="ignore"):
        pv = np.where(
            r_mkt > 0,
            pmt * (1.0 - (1.0 + r_mkt) ** (-n_rem)) / r_mkt,
            pmt * n_rem,
        )
    market_value = np.minimum(pv, balance)
    safe_bal = np.maximum(balance, 1.0)
    return market_value / safe_bal - 1.0


def rate_stress(coupon: np.ndarray, market_rate: float) -> np.ndarray:
    """Payment stress proxy for default hazard: max(0, market - coupon)."""
    return np.maximum(market_rate - coupon, 0.0)


def compute_rate_gap(
    regime: str,
    coupon: np.ndarray,
    market_rate: float,
    balance: np.ndarray,
    loan_age: np.ndarray,
) -> np.ndarray:
    if regime.upper() == "DANISH":
        return rate_gap_danish(coupon, market_rate, balance, loan_age)
    return rate_gap_us(coupon, market_rate)
