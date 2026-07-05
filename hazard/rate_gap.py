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
    Effective rate gap under market-value buyback, in decimal — same units
    as rate_gap_us so one elasticity applies to both regimes.

    NPV identity: when rates rise above coupon, the buyback discount
    (par - PV of remaining payments at market rate) exactly equals the PV of
    the locked-in rate spread, so prepaying is economically neutral —
    effective gap 0, hazard resets toward baseline h0(t).  When rates fall
    below coupon the buyback price is capped at par and the Danish borrower
    refinances exactly like a U.S. one — effective gap = coupon - market.

    Pre-fix this returned the raw price ratio (PV/balance - 1), which is in
    price units, not rate units; under a per-100bp elasticity it would
    mis-scale the Danish regime ~10x.
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
    # PV < par ⇔ locked in ⇒ discount offsets the spread ⇒ gap 0;
    # PV >= par ⇒ buyback capped at par ⇒ U.S.-style refi incentive.
    return np.where(pv < balance, 0.0, coupon - market_rate)


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
