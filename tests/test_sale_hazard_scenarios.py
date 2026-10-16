import math

import pytest
import numpy as np

from hazard.sale_hazard_scenarios import (
    quarterly_probability_to_monthly_intensity,
    quarterly_probability_to_monthly_probability,
    sale_scenario,
)


FORMS = ["lpm_absolute", "relative_linear_transport", "relative_exponential_transport"]


@pytest.mark.parametrize("p", [0, 1e-12, .00971, .06, .9, 1 - 1e-12])
def test_exact_quarterly_survival_reconstruction(p):
    intensity = quarterly_probability_to_monthly_intensity(p)
    monthly = quarterly_probability_to_monthly_probability(p)
    assert -math.expm1(-3 * intensity) == pytest.approx(p, abs=1e-15)
    assert 1 - (1 - monthly) ** 3 == pytest.approx(p, abs=1e-15)
    if p > 0:
        assert intensity > monthly


def run(p=.02, gap=1, form="lpm_absolute"):
    return sale_scenario(quarterly_reference_probability=p,
                         baseline_provenance="synthetic unit-test baseline, quarterly at risk, zero gap",
                         lock_in_gap_pp=gap, functional_form=form)


def test_published_absolute_slope_is_not_conditional_relative_slope():
    assert run().quarterly_response_probability == pytest.approx(.01824)
    assert run(form="relative_linear_transport").quarterly_response_probability == pytest.approx(.01638)
    # Table 2 relative column normalizes by sample mean, subject to rounding.
    assert .00176 / .00971 == pytest.approx(.181, abs=.0003)


@pytest.mark.parametrize("form", FORMS)
def test_null_and_monotonic_response(form):
    null = run(gap=0, form=form)
    assert null.quarterly_response_probability == null.quarterly_reference_probability
    assert null.monthly_response_intensity == null.monthly_reference_intensity
    responses = [run(gap=g, form=form) for g in [0, 1, 2, 3]]
    assert all(a.monthly_response_intensity > b.monthly_response_intensity
               for a, b in zip(responses, responses[1:]))
    assert all(r.evidence_status == "externally_calibrated_scenario_not_fitted" for r in responses)


def test_functional_forms_agree_at_one_point_but_not_two():
    assert run(form=FORMS[1]).quarterly_response_probability == pytest.approx(run(form=FORMS[2]).quarterly_response_probability)
    assert run(gap=2, form=FORMS[1]).quarterly_response_probability != pytest.approx(run(gap=2, form=FORMS[2]).quarterly_response_probability)


@pytest.mark.parametrize("p", [-.01, 1, 2, float("nan"), float("inf")])
def test_invalid_probabilities_are_rejected_not_clipped(p):
    with pytest.raises(ValueError):
        quarterly_probability_to_monthly_intensity(p)
    with pytest.raises(ValueError):
        run(p=p)


@pytest.mark.parametrize("gap", [-1, float("nan"), float("inf")])
def test_invalid_gap_units_domain(gap):
    with pytest.raises(ValueError):
        run(gap=gap)


def test_extrapolation_and_missing_baseline_requirements():
    with pytest.raises(ValueError):
        run(p=.001, gap=1)
    with pytest.raises(ValueError):
        run(gap=6, form="relative_linear_transport")
    with pytest.raises(ValueError):
        run(form="logit")
    with pytest.raises(TypeError):
        sale_scenario(lock_in_gap_pp=1, functional_form="lpm_absolute")
    with pytest.raises(ValueError):
        sale_scenario(quarterly_reference_probability=.02, baseline_provenance=" ",
                      lock_in_gap_pp=1, functional_form="lpm_absolute")


def test_zero_survival_rate_is_allowed_and_coefficient_is_not_divided_by_three():
    assert run(p=0, gap=0).monthly_response_intensity == 0
    s = run(p=.5, gap=1, form="relative_linear_transport")
    assert s.monthly_response_intensity / s.monthly_reference_intensity != pytest.approx(1 - .181 / 3)
    assert s.monthly_response_intensity / s.monthly_reference_intensity != pytest.approx(.819)


@pytest.mark.parametrize("value", [False, True, "0.02", b"0.02", None, complex(.02, 0), [.02], np.bool_(False)])
def test_nonreal_or_boolean_probability_and_gap_are_rejected(value):
    with pytest.raises(ValueError):
        quarterly_probability_to_monthly_intensity(value)
    with pytest.raises(ValueError):
        run(p=value, gap=0)
    with pytest.raises(ValueError):
        run(gap=value)


@pytest.mark.parametrize("number_type", [float, np.float32, np.float64])
def test_real_numeric_scalars_remain_supported(number_type):
    scenario = run(p=number_type(.02), gap=number_type(1))
    assert scenario.quarterly_response_probability == pytest.approx(.01824)
