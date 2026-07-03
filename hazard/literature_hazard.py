"""
Literature-calibrated proportional hazards for prepay and default.

Rothstein beta_1 derived via survival-function conversion (not divide-by-3).
"""

from __future__ import annotations

import math

import numpy as np

from config import (
    BASELINE_MODE,
    LITERATURE_COEFS,
    P_Q_BASELINE,
    PSA_SPEED,
    ROTHSTEIN_Q_DECLINE_HIGH,
    ROTHSTEIN_Q_DECLINE_LOW,
    ROTHSTEIN_Q_DECLINE_MID,
)


def quarterly_to_monthly_hazard(p_q: float) -> float:
    """Constant-hazard compounding: 1 - P_q = (1 - h_m)^3."""
    p_q = float(np.clip(p_q, 0.0, 1.0 - 1e-9))
    return 1.0 - (1.0 - p_q) ** (1.0 / 3.0)


def rothstein_beta1(quarterly_decline: float, p_q_base: float = P_Q_BASELINE) -> float:
    """
    Extract proportional-hazard beta_1 for a 100bp rate gap shock.

    P_q_shocked = P_q_base * (1 - quarterly_decline)
    beta_1 = ln(h_m_shocked / h_m_baseline)
    """
    h_base = quarterly_to_monthly_hazard(p_q_base)
    p_shocked = p_q_base * (1.0 - quarterly_decline)
    h_shocked = quarterly_to_monthly_hazard(p_shocked)
    if h_base <= 0:
        return 0.0
    return math.log(max(h_shocked, 1e-12) / h_base)


BETA1_PREPAY_LOW = rothstein_beta1(ROTHSTEIN_Q_DECLINE_LOW)
BETA1_PREPAY_MID = rothstein_beta1(ROTHSTEIN_Q_DECLINE_MID)
BETA1_PREPAY_HIGH = rothstein_beta1(ROTHSTEIN_Q_DECLINE_HIGH)


def h0_psa(age_months: np.ndarray, psa_speed: float = PSA_SPEED) -> np.ndarray:
    """
    PSA baseline monthly prepayment hazard.

    0.2% CPR/month for age <= 30, ramping to psa_speed% annual CPR at month 30+.
    """
    age = np.asarray(age_months, dtype=np.float64)
    cpr_monthly = np.where(
        age <= 30,
        0.002,
        0.002 + (psa_speed / 100.0) / 12.0 * np.minimum(age - 30, 30) / 30.0,
    )
    # Convert CPR to monthly hazard: h ≈ CPR/12 for small rates
    return np.clip(cpr_monthly, 1e-8, 0.5)


def h0_weibull(age_months: np.ndarray, shape: float = 1.5, scale: float = 60.0) -> np.ndarray:
    age = np.asarray(age_months, dtype=np.float64)
    return np.clip((shape / scale) * (age / scale) ** (shape - 1), 1e-8, 0.5)


def baseline_hazard(age_months: np.ndarray, mode: str = BASELINE_MODE) -> np.ndarray:
    if mode == "weibull":
        return h0_weibull(age_months)
    return h0_psa(age_months)


def prepay_hazard(
    loan_age: np.ndarray,
    rate_gap: np.ndarray,
    burnout: np.ndarray,
    fico_z: np.ndarray,
    ltv_z: np.ndarray,
    beta1: float = BETA1_PREPAY_MID,
    coefs: dict | None = None,
) -> np.ndarray:
    """
    h_prep(t) = h0(t) * exp(beta1 * rate_gap + beta_x' X + beta_b * burnout_stratum)
    """
    c = coefs or LITERATURE_COEFS
    h0 = baseline_hazard(loan_age)
    log_h = (
        beta1 * rate_gap
        + c["beta_fico"] * fico_z
        + c["beta_ltv"] * ltv_z
        + c["beta_burnout"] * burnout
    )
    return np.clip(h0 * np.exp(log_h), 0.0, 1.0)


def default_hazard(
    rate_stress: np.ndarray,
    fico_z: np.ndarray,
    ltv_z: np.ndarray,
    coefs: dict | None = None,
) -> np.ndarray:
    """
    h_def(t) = h0_def * exp(gamma1 * rate_stress + gamma_x' X)
    rate_stress = max(0, market_rate - coupon)
    """
    c = coefs or LITERATURE_COEFS
    h0_def = c["h0_default_monthly"]
    log_h = (
        c["gamma_rate_stress"] * rate_stress
        + c["gamma_fico"] * fico_z
        + c["gamma_ltv"] * ltv_z
    )
    return np.clip(h0_def * np.exp(log_h), 0.0, 1.0)


def normalize_competing_hazards(
    h_prepay: np.ndarray,
    h_default: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Row-wise scale so h_prepay + h_default <= 1."""
    h_sum = h_prepay + h_default
    scale = np.where(h_sum > 1.0, 1.0 / np.maximum(h_sum, 1e-12), 1.0)
    return h_prepay * scale, h_default * scale
