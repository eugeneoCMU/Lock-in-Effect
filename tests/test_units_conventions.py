"""
Regression tests for the two units conventions that produced the §15 Fix 3
bugs (TECHNICAL.md), plus the sweepable Berger refi global (§20.1).

Bug 1 (β₁ units): `prepay_hazard` applied β₁ to the *decimal* rate gap
(`beta1 * rate_gap`), leaving the lock-in channel numerically inert — a
multiplier of ~×1.0026 at a typical QT state instead of the intended ~×0.77.
The fix applies exp(-β₁ · 100 · rate_gap): one β₁ of suppression per −100bp
of refi incentive.

Bug 2 (Danish gap units): `rate_gap_danish` returned the raw price ratio
(PV/balance − 1), price units, not rate units — ~10x mis-scaled under a
per-100bp elasticity. The fix returns 0 when out-of-the-money and
coupon − market when in-the-money (NPV identity, buyback capped at par).

Run:  python3 -m pytest tests/test_units_conventions.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "hazard"))

from common.berger_calibration import (  # noqa: E402
    danish_cpr_annual,
    get_us_transplant_refi,
    set_us_transplant_refi,
)
from literature_hazard import (  # noqa: E402
    BETA1_PREPAY_MID,
    baseline_hazard,
    cpr_annual_to_monthly_hazard,
    prepay_hazard,
    rothstein_beta1,
)
from config import INVOLUNTARY_CPR_ANNUAL, P_Q_BASELINE, ROTHSTEIN_Q_DECLINE_MID  # noqa: E402
from rate_gap import rate_gap_danish, rate_gap_us  # noqa: E402


AGE = np.array([60])  # past the PSA ramp: flat baseline
ZERO = np.zeros(1)


def _h(gap: float, beta1: float = BETA1_PREPAY_MID) -> float:
    return float(
        prepay_hazard(AGE, np.array([gap]), ZERO, ZERO, ZERO, beta1=beta1)[0]
    )


class TestBeta1Units:
    def test_beta1_value_matches_survival_conversion(self):
        """β₁ = ln(h_m_shocked / h_m_base) from the documented conversion."""
        h_base = 1.0 - (1.0 - P_Q_BASELINE) ** (1.0 / 3.0)
        p_shocked = P_Q_BASELINE * (1.0 - ROTHSTEIN_Q_DECLINE_MID)
        h_shocked = 1.0 - (1.0 - p_shocked) ** (1.0 / 3.0)
        assert BETA1_PREPAY_MID == pytest.approx(math.log(h_shocked / h_base))
        assert BETA1_PREPAY_MID < 0  # suppression, by construction

    def test_zero_shock_gives_exactly_zero_beta1(self):
        """p_q_shock_pct=0 is an exact no-lock-in configuration (null run)."""
        assert rothstein_beta1(0.0) == 0.0

    def test_one_beta1_of_suppression_per_100bp(self):
        """At −100bp the multiplier is exactly exp(β₁) (floor not binding)."""
        # Precondition: the suppressed voluntary hazard sits above the
        # turnover floor, so the ratio is the pure elasticity effect.
        h0 = float(baseline_hazard(AGE)[0])
        floor = float(
            cpr_annual_to_monthly_hazard(np.array([INVOLUNTARY_CPR_ANNUAL]))[0]
        )
        assert h0 * math.exp(BETA1_PREPAY_MID) > floor, (
            "test invalid: floor binds at -100bp; pick a different state"
        )
        ratio = _h(-0.01) / _h(0.0)
        assert ratio == pytest.approx(math.exp(BETA1_PREPAY_MID), rel=1e-9)

    def test_typical_qt_state_is_suppressed_not_inert(self):
        """
        Regression for the pre-fix bug: at a −380bp gap (3.0% coupon, 6.8%
        market) the multiplier was ×1.0026 — inert and wrong-signed. Post-fix
        it must be a real suppression (≈×0.77 before the floor, so ≤0.85
        after any plausible floor).
        """
        ratio = _h(-0.038) / _h(0.0)
        assert ratio <= 0.85
        assert ratio < 1.0  # direction: lock-in suppresses, never boosts

    def test_in_the_money_boosts_hazard(self):
        """Positive incentive (coupon above market) raises voluntary prepay."""
        assert _h(+0.01) > _h(0.0)

    def test_monotone_in_lockin_depth_until_floor(self):
        hs = [_h(g) for g in (0.0, -0.01, -0.02, -0.038)]
        assert all(a >= b for a, b in zip(hs, hs[1:]))


class TestDanishGapUnits:
    BAL = np.array([300_000.0])
    AGE = np.array([24])

    def test_out_of_the_money_gap_is_zero(self):
        """Rates above coupon: buyback discount offsets the spread → gap 0."""
        gap = rate_gap_danish(np.array([0.03]), 0.068, self.BAL, self.AGE)
        assert gap[0] == 0.0

    def test_in_the_money_matches_us_gap(self):
        """Rates below coupon: buyback capped at par → U.S.-style incentive."""
        coupon = np.array([0.03])
        gap = rate_gap_danish(coupon, 0.02, self.BAL, self.AGE)
        assert gap[0] == pytest.approx(0.01)
        assert gap[0] == pytest.approx(rate_gap_us(coupon, 0.02)[0])

    def test_rate_units_never_price_units(self):
        """
        Regression for the pre-fix bug: the raw price ratio (PV/balance − 1)
        can reach tens of percent — rate units never exceed |coupon − market|.
        """
        coupon = np.array([0.03])
        for market in np.arange(0.01, 0.095, 0.005):
            gap = rate_gap_danish(coupon, float(market), self.BAL, self.AGE)
            assert abs(gap[0]) <= abs(0.03 - market) + 1e-12


class TestBergerRefiGlobal:
    def test_roundtrip_and_cpr_response(self):
        """
        The sweepable global drives the institutional-gap sign (§20.1); the
        setter must round-trip and propagate into the US-transplant CPR on
        the survival scale.
        """
        coupon, age = np.array([0.025]), np.array([36])
        original = get_us_transplant_refi()
        try:
            set_us_transplant_refi(0.0)
            cpr_zero = danish_cpr_annual(coupon, 0.068, age, regime="US")[0]
            set_us_transplant_refi(0.05)
            assert get_us_transplant_refi() == 0.05
            cpr_five = danish_cpr_annual(coupon, 0.068, age, regime="US")[0]
        finally:
            set_us_transplant_refi(original)
        # survival-scale composition: Δ = 0.05 · (1 − move)
        assert cpr_five - cpr_zero == pytest.approx(0.05 * (1.0 - cpr_zero))
        assert get_us_transplant_refi() == original

    def test_manifest_records_the_global(self):
        """
        Tripwire: freeze_run.py must keep recording the sweepable global in
        the run manifest, or frozen runs under-specify the pipeline (§20.1).
        """
        src = (_ROOT / "abm" / "freeze_run.py").read_text()
        assert "us_transplant_refi_annual" in src
        assert "get_us_transplant_refi" in src


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
