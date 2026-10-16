"""Scenario kernel accounting tests; no empirical hazard estimation is implied."""
import math
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hazard.mortgage_competing_risks import (
    competing_probabilities,
    monthly_principal_step,
    paired_principal_contributions,
    probability_to_monthly_intensity,
    sale_mixture_intensity,
)


def test_causes_compete_on_survival_scale_and_sum_to_one():
    result = competing_probabilities({"refinance": 0.1, "sale": 0.2, "other": 0.05, "credit": 0.05})
    assert result.survival_probability == pytest.approx(0.6703200460356393)
    assert result.cause_probabilities == pytest.approx({"refinance": 0.08241998849109017, "sale": 0.16483997698218034, "other": 0.041209994245545085, "credit": 0.041209994245545085})
    assert math.fsum(result.cause_probabilities.values()) + result.survival_probability == pytest.approx(1)


def test_single_cause_conversion_reduces_to_original_probability():
    for probability in (0.0, 1e-15, 0.01, 0.75, 0.999999):
        intensity = probability_to_monthly_intensity(probability)
        result = competing_probabilities({"combined": intensity})
        assert result.cause_probabilities["combined"] == pytest.approx(probability, rel=1e-14)


def test_period_conversion_is_explicit_and_all_zero_is_safe():
    assert probability_to_monthly_intensity(0.75, dt_months=2) == pytest.approx(math.log(2))
    result = competing_probabilities({"refinance": 0, "sale": 0}, dt_months=2)
    assert result.cause_probabilities == {"refinance": 0.0, "sale": 0.0}
    assert result.survival_probability == 1
    result = competing_probabilities({"x": math.log(2)}, dt_months=2)
    assert result.cause_probabilities["x"] == pytest.approx(0.75)


def test_large_and_tiny_intensities_keep_probabilities_finite():
    result = competing_probabilities({"x": 1e308, "y": 1e308})
    assert result.cause_probabilities == {"x": 0.5, "y": 0.5}
    assert result.survival_probability == 0
    assert competing_probabilities({"x": 1e-20}).cause_probabilities["x"] == pytest.approx(1e-20, abs=0)


def test_large_intensity_with_short_period_does_not_overflow_prematurely():
    result = competing_probabilities({"x": 1e308, "y": 1e308}, dt_months=1e-308)
    assert result.survival_probability == pytest.approx(0.1353352832366127)
    result = competing_probabilities({"x": 1e-308, "y": 1e-308}, dt_months=1e308)
    assert result.survival_probability == pytest.approx(0.1353352832366127)


def test_adding_credit_intensity_reduces_voluntary_probability():
    alone = competing_probabilities({"sale": .1})
    competing = competing_probabilities({"sale": .1, "unresolved": .2})
    assert competing.cause_probabilities["sale"] < alone.cause_probabilities["sale"]
    assert set(competing.cause_probabilities) == {"sale", "unresolved"}


def test_zero_balance_and_full_amortization_leave_no_event_principal():
    for balance, schedule in [(0, 0), (100, 100)]:
        result = monthly_principal_step(balance, schedule, {"admin": 100})
        assert result.cause_principal == {"admin": 0}
        assert result.ending_balance == 0


def test_mixture_uses_intensity_share_and_gap_in_percentage_points():
    # exp(-log(2) * 2 pp) = 1/4; mixture multiplier = .4 + .6/4.
    assert sale_mixture_intensity(0.02, 0.6, math.log(2), 2) == pytest.approx(0.011)
    assert sale_mixture_intensity(0.02, 0.6, 2, -3) == 0.02
    assert sale_mixture_intensity(0.02, 0, 2, 3) == 0.02
    assert sale_mixture_intensity(0.02, 1, 0, 3) == 0.02
    # Gap decimals are only accepted when labelled, with conversion to pp.
    assert sale_mixture_intensity(0.02, 0.6, math.log(2), 0.02, gap_unit="decimal") == pytest.approx(0.011)


def test_principal_step_keeps_credit_separate_from_cash_runoff():
    # Schedule first: 100 - 10 = 90; total exit probability .5.
    result = monthly_principal_step(100, 10, {"sale": math.log(2)/2, "credit": math.log(2)/2})
    assert result.scheduled_principal == 10
    assert result.cause_principal == pytest.approx({"sale": 22.5, "credit": 22.5})
    assert result.ending_balance == pytest.approx(45)
    assert result.scheduled_principal + math.fsum(result.cause_principal.values()) + result.ending_balance == pytest.approx(100)
    # No 'settled cash' is inferred for a credit event.


def test_paired_contributions_share_balance_and_schedule_and_reconcile():
    result = paired_principal_contributions(100, 10, {"sale": math.log(2)}, {"refinance": math.log(4)})
    assert result.cause_differences == pytest.approx({"sale": 45, "refinance": -67.5})
    assert result.total_exit_difference == pytest.approx(-22.5)
    assert result.ending_balance_difference == pytest.approx(22.5)
    assert result.total_exit_difference + result.ending_balance_difference == pytest.approx(0)
    identical = paired_principal_contributions(100, 10, {"credit": .02}, {"credit": .02})
    assert identical.total_exit_difference == 0


@pytest.mark.parametrize("value", [True, -1, float("nan"), float("inf"), "0.1"])
def test_invalid_intensities_rejected(value):
    with pytest.raises((ValueError, TypeError)):
        competing_probabilities({"sale": value})


@pytest.mark.parametrize("duration", [True, 0, -1, float("inf"), float("nan"), "1"])
def test_invalid_month_durations_rejected(duration):
    with pytest.raises((ValueError, TypeError)):
        competing_probabilities({"sale": 0.1}, dt_months=duration)
    with pytest.raises((ValueError, TypeError)):
        probability_to_monthly_intensity(0.1, dt_months=duration)


@pytest.mark.parametrize("probability", [True, -0.1, 1, 1.1, float("nan"), float("inf")])
def test_probability_one_requires_infinite_intensity_and_is_rejected(probability):
    with pytest.raises((ValueError, TypeError)):
        probability_to_monthly_intensity(probability)


@pytest.mark.parametrize("kwargs", [{"intensity_unit": "annual"}, {"time_unit": "years"}])
def test_unsupported_time_or_intensity_units_are_rejected(kwargs):
    with pytest.raises(ValueError):
        competing_probabilities({"sale": .01}, **kwargs)


@pytest.mark.parametrize("args,kwargs", [((.01, 1.1, 1, 1), {}), ((.01, -.1, 1, 1), {}), ((.01, .5, -1, 1), {}), ((True, .5, 1, 1), {}), ((.01, .5, 1, float("nan")), {}), ((.01, .5, 1, 1), {"gap_unit": "bps"}), ((.01, .5, 1, 1), {"gamma_unit": "per_decimal"})])
def test_mixture_rejects_invalid_parameters_or_ambiguous_units(args, kwargs):
    with pytest.raises((ValueError, TypeError)):
        sale_mixture_intensity(*args, **kwargs)


@pytest.mark.parametrize("balance,schedule", [(True, 0), (100, True), (-1, 0), (100, -1), (100, 101), (float("inf"), 0)])
def test_invalid_principal_rejected(balance, schedule):
    with pytest.raises((ValueError, TypeError)):
        monthly_principal_step(balance, schedule, {"other": 0})


@pytest.mark.parametrize("causes", [{}, {"": .01}, {1: .01}])
def test_causes_must_be_explicit_nonempty_labels(causes):
    with pytest.raises((ValueError, TypeError)):
        competing_probabilities(causes)
