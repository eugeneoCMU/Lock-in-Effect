"""
Coverage for common/berger_calibration.py — the Danish-counterfactual
calibration (audit: 1/2 mutants killed).

This module is a transcription layer plus four pieces of load-bearing
arithmetic, and the arithmetic is where the damage lives: a units slip in
danish_moving_cpr_annual (decimal gap -> per-100bp slope) or a sign slip in
_buyback_discount_frac moves the Danish counterfactual — and therefore the
institutional-gap comparison the paper reports — without raising anything.

Every expectation below is either a literal transcribed from the paper (with
the section named) or recomputed inside the test from first principles with
plain arithmetic. Nothing is read back out of the module and compared to
itself.

Run with: python3 -m pytest tests/test_berger_calibration.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from common import berger_calibration as bc


# ---------------------------------------------------------------------------
# Transcribed literals — Berger, Jeong, Marx, Olesen & Tourre (berger2026,
# "A Danish fix for U.S. mortgage lock-in?"). Not Berger, Milbradt, Tourre &
# Vavra (2021 AER), which is a different, non-Danish paper.
# ---------------------------------------------------------------------------
def test_table3_structural_parameters_are_the_transcribed_values():
    """Table 3: moving opportunity hazard, refi opportunity hazard, cost draws."""
    assert bc.PSI == {"DK": 0.055, "US": 0.13}
    assert bc.SIGMA_PSI == {"DK": 0.10, "US": 0.15}
    assert bc.LAMBDA == {"DK": 0.33, "US": 0.30}
    assert bc.KAPPA_LAMBDA == {"DK": 0.008, "US": 0.02}
    assert bc.SIGMA_LAMBDA == {"DK": 0.005, "US": 0.02}


def test_moving_slope_confidence_intervals_are_transcribed():
    """§3.3.1 Danish moving-hazard slope CI spans zero; Fonseca & Liu 2024 U.S."""
    assert (bc.DK_MOVE_SLOPE_LO_PP, bc.DK_MOVE_SLOPE_HI_PP) == (-0.198, 0.12)
    assert (bc.US_MOVE_SLOPE_LO_PP, bc.US_MOVE_SLOPE_HI_PP) == (0.57, 1.20)
    assert bc.DK_UNCOND_MOVE_ANNUAL == 0.032  # 3.2%/yr unconditional moving


def test_danish_moving_ci_actually_spans_zero():
    """The paper's claim is statistical flatness. If the CI stopped spanning
    zero the 'no lock-in on the moving margin' reading would not follow."""
    assert bc.DK_MOVE_SLOPE_LO_PP < 0.0 < bc.DK_MOVE_SLOPE_HI_PP
    # ... whereas the U.S. slope is bounded strictly away from zero.
    assert bc.US_MOVE_SLOPE_LO_PP > 0.0


def test_tax_parameters_are_transcribed():
    """§4.9.1 footnote 24. Denmark's capital-gains exemption is the whole
    mechanism: THETA_G_DK must be exactly zero."""
    assert bc.THETA_I_US == 0.22
    assert bc.THETA_G_US == 0.15
    assert bc.THETA_DK == 0.33
    assert bc.THETA_G_DK == 0.0
    assert bc.US_BUYBACK_EQUIL_RATE_SHIFT_BP == 1.0


# ---------------------------------------------------------------------------
# Derived constants — recomputed from the transcribed endpoints
# ---------------------------------------------------------------------------
def test_midpoints_are_midpoints_of_the_stated_intervals():
    assert bc.DK_MOVE_SLOPE_MID_PP == pytest.approx(-0.039, abs=1e-12)
    assert bc.US_MOVE_SLOPE_MID_PP == pytest.approx(0.885, abs=1e-12)


def test_move_attenuation_is_absolute_dk_over_us():
    """|-0.039| / 0.885 = 0.044068. Two failure modes this pins: dropping the
    abs() (attenuation goes negative, and 'essentially flat' inverts), and
    inverting the ratio (22.7x amplification instead of 4.4% attenuation)."""
    assert bc.MOVE_ATTENUATION == pytest.approx(0.039 / 0.885, rel=1e-12)
    assert bc.MOVE_ATTENUATION == pytest.approx(0.044068, abs=1e-6)
    assert 0.0 < bc.MOVE_ATTENUATION < 0.1  # attenuation, not amplification


# ---------------------------------------------------------------------------
# danish_moving_cpr_annual — the per-100bp unit conversion
# ---------------------------------------------------------------------------
def test_moving_cpr_at_zero_gap_is_the_unconditional_rate():
    got = bc.danish_moving_cpr_annual(np.array([0.0]))[0]
    assert got == pytest.approx(0.032, abs=1e-15)


@pytest.mark.parametrize(
    "gap_decimal,expected",
    [
        # slope is -0.039 %/yr per 100bp = -0.00039 fraction/yr per 100bp.
        # gap is a DECIMAL, so 0.01 decimal == 1 unit of 100bp.
        (-0.01, 0.032 + 0.00039 * 1),    # 100bp below market
        (-0.02, 0.032 + 0.00039 * 2),
        (+0.01, 0.032 - 0.00039 * 1),
        (+0.03, 0.032 - 0.00039 * 3),
    ],
)
def test_moving_cpr_slope_is_per_100bp_of_a_decimal_gap(gap_decimal, expected):
    """A x100 / /100 slip here rescales the Danish moving channel by 10,000.
    Hand-computed on the right, nothing read from the module."""
    got = bc.danish_moving_cpr_annual(np.array([gap_decimal]))[0]
    assert got == pytest.approx(expected, abs=1e-12)


def test_moving_cpr_is_decreasing_in_the_coupon_gap():
    """Danish slope is NEGATIVE: a larger coupon-minus-market gap means lower
    moving. Small in magnitude, but the sign is the identified fact."""
    gaps = np.array([-0.03, -0.01, 0.0, 0.01, 0.03])
    out = bc.danish_moving_cpr_annual(gaps)
    assert np.all(np.diff(out) < 0.0)


def test_moving_cpr_is_clipped_into_the_unit_interval():
    """An absurd gap must not produce a negative or >1 annual CPR."""
    assert bc.danish_moving_cpr_annual(np.array([1e6]))[0] == 0.0
    assert bc.danish_moving_cpr_annual(np.array([-1e6]))[0] == 1.0


def test_moving_cpr_is_near_flat_over_the_realistic_gap_range():
    """The economic claim: over a +/-300bp swing the Danish moving channel
    barely moves — total variation under a quarter of a percentage point."""
    out = bc.danish_moving_cpr_annual(np.array([-0.03, 0.03]))
    assert abs(out[0] - out[1]) < 0.0025


# ---------------------------------------------------------------------------
# _buyback_discount_frac — sign, magnitude, monotonicity
# ---------------------------------------------------------------------------
def _pv_discount(coupon, market, age, term=360):
    """Independent recomputation with plain math: 1 - PV(coupon annuity at market)."""
    n = max(term - age, 1)
    rc, rm = coupon / 12.0, market / 12.0
    pmt = rc / (1.0 - (1.0 + rc) ** (-n))
    pv = pmt * (1.0 - (1.0 + rm) ** (-n)) / rm
    return max(1.0 - pv, 0.0)


@pytest.mark.parametrize("market", [0.045, 0.06, 0.08])
def test_buyback_discount_matches_an_independent_annuity_calculation(market):
    got = bc._buyback_discount_frac(np.array([0.025]), market, np.array([36]))[0]
    assert got == pytest.approx(_pv_discount(0.025, market, 36), rel=1e-12)


def test_buyback_discount_is_zero_when_rates_have_not_risen():
    """The debt trades at or above par: no discount to realize. A flipped
    comparison would manufacture a discount exactly where none exists."""
    for market in (0.010, 0.020, 0.025):
        got = bc._buyback_discount_frac(np.array([0.025]), market, np.array([36]))[0]
        assert got == 0.0, market


def test_buyback_discount_is_strictly_positive_when_rates_have_risen():
    got = bc._buyback_discount_frac(np.array([0.025]), 0.07, np.array([36]))[0]
    assert 0.0 < got < 1.0


def test_buyback_discount_increases_with_the_market_rate():
    markets = [0.03, 0.04, 0.05, 0.06, 0.07, 0.08]
    vals = [bc._buyback_discount_frac(np.array([0.025]), m, np.array([36]))[0]
            for m in markets]
    assert all(b > a for a, b in zip(vals, vals[1:]))


def test_buyback_discount_shrinks_as_the_loan_seasons():
    """Shorter remaining term -> less duration -> smaller discount at the same
    rate gap. Pins the term_months - loan_age direction."""
    ages = np.array([0, 60, 120, 240, 340])
    vals = bc._buyback_discount_frac(np.full(5, 0.025), 0.07, ages)
    assert all(b < a for a, b in zip(vals, vals[1:]))


def test_buyback_discount_handles_a_fully_seasoned_loan_without_dividing_by_zero():
    """n_rem is floored at 1, so age >= term must not blow up."""
    got = bc._buyback_discount_frac(np.array([0.025]), 0.07, np.array([360]))[0]
    assert math.isfinite(got) and 0.0 <= got < 1.0


# ---------------------------------------------------------------------------
# _annual_to_monthly_cpr — the convex transform
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("cpr", [0.0, 0.01, 0.032, 0.10, 0.33, 0.9])
def test_annual_to_monthly_is_the_constant_hazard_transform(cpr):
    got = bc._annual_to_monthly_cpr(np.array([cpr]))[0]
    assert got == pytest.approx(1.0 - (1.0 - cpr) ** (1.0 / 12.0), rel=1e-14)


def test_annual_to_monthly_is_strictly_convex_so_12x_overstates():
    """12 * monthly > annual for any positive CPR — this is exactly the
    convexity the floor_cyclical permutation probe relies on. A linear /12
    would satisfy 12*monthly == annual and is killed here."""
    for cpr in (0.01, 0.05, 0.10, 0.32, 0.6):
        m = bc._annual_to_monthly_cpr(np.array([cpr]))[0]
        assert 12.0 * m > cpr
        assert m < cpr


def test_annual_to_monthly_clips_its_input_at_99_percent():
    """CPR = 1.0 would send the monthly hazard to exactly 1 and the survival
    scale to zero; the clip must bind at 0.99."""
    at_one = bc._annual_to_monthly_cpr(np.array([1.0]))[0]
    at_clip = bc._annual_to_monthly_cpr(np.array([0.99]))[0]
    assert at_one == pytest.approx(at_clip, rel=1e-15)
    assert at_one < 1.0
    assert bc._annual_to_monthly_cpr(np.array([-5.0]))[0] == 0.0


# ---------------------------------------------------------------------------
# danish_refi_in_place_cpr_annual — regime routing and the sweepable global
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("regime", ["DK", "dk", "Danish", "DANISH", "dk_home"])
def test_danish_regime_labels_all_route_to_the_tax_shield_branch(regime):
    got = bc.danish_refi_in_place_cpr_annual(
        np.array([0.025]), 0.07, np.array([36]), regime=regime
    )[0]
    assert got > 0.0


@pytest.mark.parametrize("regime", ["US", "us", "United States", ""])
def test_non_danish_regime_labels_route_to_the_transplant_anchor(regime):
    got = bc.danish_refi_in_place_cpr_annual(
        np.array([0.025]), 0.07, np.array([36]), regime=regime
    )[0]
    assert got == bc.get_us_transplant_refi()


def test_us_transplant_refi_default_is_the_berger_ge_zero_anchor():
    """Berger §4.9.1: ~1bp equilibrium shift -> essentially no incremental refi."""
    assert bc.US_TRANSPLANT_REFI_BEST_ESTIMATE == 0.0
    assert bc.get_us_transplant_refi() == 0.0


def test_us_transplant_refi_is_sweepable_and_flows_through(monkeypatch):
    """refi_sweep.py depends on this global actually reaching the output."""
    monkeypatch.setattr(bc, "_US_TRANSPLANT_REFI_ANNUAL", 0.0)
    bc.set_us_transplant_refi(0.07)
    try:
        assert bc.get_us_transplant_refi() == 0.07
        out = bc.danish_refi_in_place_cpr_annual(
            np.array([0.025, 0.04]), 0.07, np.array([36, 36]), regime="US"
        )
        assert np.allclose(out, 0.07)
        # It is a flat anchor: independent of the discount, by construction.
        no_disc = bc.danish_refi_in_place_cpr_annual(
            np.array([0.09]), 0.02, np.array([36]), regime="US"
        )[0]
        assert no_disc == 0.07
    finally:
        bc.set_us_transplant_refi(bc.US_TRANSPLANT_REFI_BEST_ESTIMATE)
    assert bc.get_us_transplant_refi() == 0.0


def test_danish_refi_is_zero_without_a_discount_to_realize():
    """No discount -> no tax shield -> no incremental refi, even in Denmark."""
    got = bc.danish_refi_in_place_cpr_annual(
        np.array([0.025]), 0.02, np.array([36]), regime="DK"
    )[0]
    assert got == 0.0


def test_danish_refi_is_capped_by_the_opportunity_hazard():
    """Take-up is a probability; the channel cannot exceed LAMBDA['DK'] = 0.33
    no matter how large the discount."""
    got = bc.danish_refi_in_place_cpr_annual(
        np.array([0.001]), 0.20, np.array([1]), regime="DK"
    )[0]
    assert 0.0 < got <= bc.LAMBDA["DK"]


def test_danish_refi_increases_with_the_discount():
    markets = [0.03, 0.045, 0.06, 0.08]
    vals = [bc.danish_refi_in_place_cpr_annual(
        np.array([0.025]), m, np.array([36]), regime="DK")[0] for m in markets]
    assert all(b >= a for a, b in zip(vals, vals[1:]))
    assert vals[-1] > vals[0]


# Berger literals for the DK take-up draw, restated here rather than read from
# the module, so this recomputation is independent of the values under test:
#   tax advantage  theta_dk - theta_g_dk = 0.33 - 0.0   (§4.9.1)
#   cost draw      N(kappa_lambda, sigma_lambda) = N(0.008, 0.005)  (Table 3)
#   opportunity    lambda_dk = 0.33                                 (Table 3)
_DK_TAX_ADV = 0.33
_DK_KAPPA_LAMBDA = 0.008
_DK_SIGMA_LAMBDA = 0.005
_DK_LAMBDA = 0.33


def _dk_refi_from_first_principles(coupon, market, age, term=360):
    """lambda_dk * P(cost draw < after-tax benefit), written out in full."""
    disc = _pv_discount(coupon, market, age, term)
    if disc <= 0.0:
        return 0.0
    z = (disc * _DK_TAX_ADV - _DK_KAPPA_LAMBDA) / _DK_SIGMA_LAMBDA
    take = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
    return min(_DK_LAMBDA * take, 1.0)


@pytest.mark.parametrize("market", [0.026, 0.027, 0.028, 0.0285, 0.029])
def test_danish_refi_take_up_level_in_the_transition_region(market):
    """Pin the LEVEL of the take-up curve where it is strictly interior.

    HOLE (adversarial mutation pass). Every other DK assertion in this file
    probes the channel only where it is SATURATED (markets 0.03-0.08 all give
    take-up > 0.98, i.e. the flat top at lambda_dk) or exactly ZERO (no
    discount). Monotonicity, `last > first` and the `0 < x <= lambda` cap all
    hold on the flat top no matter what the structural parameters are, so the
    region where kappa_lambda, sigma_lambda and the tax advantage actually do
    work was pinned by nothing.

    Measured: substituting the U.S. thetas (0.22 - 0.15 = 0.07) for the Danish
    tax advantage (0.33 - 0.0) leaves the channel at 0.0705 where production
    gives 0.32542 — a 4.6x error in the Danish refi-in-place rate — and the
    whole file still passed. Flipping the sign on the refinancing cost draw
    likewise survived. These markets sit at take-up 0.21-0.93, where both are
    immediately visible.
    """
    coupon, age = np.array([0.025]), np.array([36])
    got = bc.danish_refi_in_place_cpr_annual(coupon, market, age, regime="DK")[0]
    want = _dk_refi_from_first_principles(0.025, market, 36)

    # Genuinely interior: this is not another probe of the saturated top.
    assert 0.05 < want < 0.99 * _DK_LAMBDA
    assert got == pytest.approx(want, rel=1e-12)


# ---------------------------------------------------------------------------
# danish_cpr_annual — the competing-risks combination
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("regime,market", [("DK", 0.07), ("US", 0.07), ("DK", 0.02)])
def test_total_is_the_survival_scale_combination_not_a_sum(regime, market):
    """1 - (1-move)(1-refi), recomputed here from the two channels. A plain
    move + refi would agree to first order and diverge in the second — which
    is precisely where the Danish channel lives."""
    coupon, age = np.array([0.025]), np.array([36])
    move = bc.danish_moving_cpr_annual(coupon - market)[0]
    refi = bc.danish_refi_in_place_cpr_annual(coupon, market, age, regime=regime)[0]
    total = bc.danish_cpr_annual(coupon, market, age, regime=regime)[0]
    assert total == pytest.approx(1.0 - (1.0 - move) * (1.0 - refi), rel=1e-14)


def test_total_never_exceeds_the_sum_of_its_channels():
    """Competing risks: the combination must be sub-additive, strictly so when
    both channels are live."""
    coupon, age = np.array([0.025]), np.array([36])
    move = bc.danish_moving_cpr_annual(coupon - 0.07)[0]
    refi = bc.danish_refi_in_place_cpr_annual(coupon, 0.07, age, regime="DK")[0]
    total = bc.danish_cpr_annual(coupon, 0.07, age, regime="DK")[0]
    assert refi > 0.0
    assert total < move + refi
    assert total > max(move, refi)


def test_total_reduces_to_the_moving_channel_under_the_us_transplant():
    """With the transplant refi anchored at 0, the U.S. Danish-rule
    counterfactual IS the moving channel — the paper's whole point."""
    coupon, age = np.array([0.025]), np.array([36])
    assert bc.get_us_transplant_refi() == 0.0
    total = bc.danish_cpr_annual(coupon, 0.07, age, regime="US")[0]
    move = bc.danish_moving_cpr_annual(coupon - 0.07)[0]
    assert total == pytest.approx(move, rel=1e-14)


def test_gap_is_coupon_minus_market_not_the_reverse():
    """A flipped gap would make the Danish moving channel rise with rates
    instead of (very slightly) falling. Rates up -> gap negative -> moving
    just ABOVE the 3.2% unconditional level."""
    coupon, age = np.array([0.025]), np.array([36])
    risen = bc.danish_cpr_annual(coupon, 0.07, age, regime="US")[0]
    fallen = bc.danish_cpr_annual(coupon, 0.01, age, regime="US")[0]
    assert risen > bc.DK_UNCOND_MOVE_ANNUAL > fallen


# ---------------------------------------------------------------------------
# Moving-channel anchor selector
# ---------------------------------------------------------------------------
def test_moving_anchor_default_and_round_trip():
    assert bc.get_danish_moving_anchor() == "dk_level"
    try:
        bc.set_danish_moving_anchor("us_intercept")
        assert bc.get_danish_moving_anchor() == "us_intercept"
        bc.set_danish_moving_anchor("dk_level")
        assert bc.get_danish_moving_anchor() == "dk_level"
    finally:
        bc.set_danish_moving_anchor("dk_level")


def test_moving_anchor_rejects_unknown_modes():
    """Silently accepting a typo would run the wrong counterfactual and report
    it as the right one."""
    for bad in ("dk", "DK_LEVEL", "us", "", None):
        with pytest.raises(ValueError):
            bc.set_danish_moving_anchor(bad)
    assert bc.get_danish_moving_anchor() == "dk_level"  # unchanged by failures


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
