import numpy as np
import pytest
from hazard.structural_sale_extension import scheduled_loan_value, effective_penalty, sale_intensity, competing_probabilities


def test_par_value_and_below_market_cost():
    assert scheduled_loan_value(200000,.03,.03,240)==pytest.approx(200000)
    assert scheduled_loan_value(200000,0,0,240)==pytest.approx(200000)
    assert scheduled_loan_value(200000,.03,.07,240)<200000


def test_concessions_require_explicit_permission_and_assumed_cap():
    assert effective_penalty(50000)==50000
    assert effective_penalty(50000,concessions_permitted=True,assumed_cap=20000)==20000
    with pytest.raises(ValueError):effective_penalty(50000,concessions_permitted=True)
    with pytest.raises(ValueError):effective_penalty(50000,assumed_cap=20000)


def test_arrival_and_gain_distribution_are_separate():
    cdf=lambda x:1-np.exp(-np.asarray(x)/10000.)
    assert sale_intensity(10000,.02,cdf)==pytest.approx(.02/np.e)
    assert sale_intensity(0,0,cdf)==0
    with pytest.raises(ValueError):sale_intensity(1,.02,lambda x:np.asarray(x)*2)


def test_competing_causes_conserve_exit_probability():
    result=competing_probabilities(sale=.01,refinancing=.02,other=0,default=.005)
    assert sum(result.values())==pytest.approx(1-np.exp(-.035))
    assert result['refinancing']==pytest.approx(2*result['sale'])
    assert sum(competing_probabilities(sale=0,refinancing=0,other=0,default=0).values())==0
    with pytest.raises(ValueError):competing_probabilities(sale=-1,refinancing=0,other=0,default=0)


def test_home_sale_need_not_terminate_the_mortgage():
    from hazard.structural_sale_extension import sale_termination_intensity
    assert sale_termination_intensity(.02,0)==0
    assert sale_termination_intensity(.02,1)==.02
    with pytest.raises(ValueError):sale_termination_intensity(.02,1.1)


# These tests catch applying mobility to every cause, averaging intensities,
# silently supplying an unestimated refinance rate, and treating a static saving
# as a dynamic refinancing optimum.
def test_sale_mobility_changes_only_sale_intensity_before_competing_conversion():
    from hazard.structural_sale_extension import supplied_cause_probabilities
    baseline = supplied_cause_probabilities(
        sale=np.log(2), refinancing=np.log(2), other=0, default=0,
        sale_mobility_factor=1,
    )
    blocked_sale = supplied_cause_probabilities(
        sale=np.log(2), refinancing=np.log(2), other=0, default=0,
        sale_mobility_factor=0,
    )
    assert baseline['sale'] == pytest.approx(.375)
    assert baseline['refinancing'] == pytest.approx(.375)
    assert blocked_sale['sale'] == 0
    # Its intensity is unchanged; its first-exit probability rises because
    # the competing sale exit is absent.
    assert blocked_sale['refinancing'] == pytest.approx(.5)


def test_supplied_causes_broadcast_and_preserve_non_sale_relative_intensities():
    from hazard.structural_sale_extension import supplied_cause_probabilities
    result = supplied_cause_probabilities(
        sale=[.1, .1], refinancing=.03, other=.02, default=.01,
        sale_mobility_factor=[0, 2],
    )
    assert result['sale'][0] == 0
    np.testing.assert_allclose(result['refinancing']/result['other'], 1.5)
    np.testing.assert_allclose(result['other']/result['default'], 2)
    np.testing.assert_allclose(sum(result.values()), -np.expm1(-np.array([.06, .26])))
    assert sum(supplied_cause_probabilities(
        sale=0, refinancing=0, other=0, default=0, sale_mobility_factor=3,
    ).values()) == 0


@pytest.mark.parametrize('bad', [-1, np.nan, np.inf])
def test_supplied_causes_reject_invalid_mobility_and_refinance_inputs(bad):
    from hazard.structural_sale_extension import supplied_cause_probabilities
    with pytest.raises(ValueError):
        supplied_cause_probabilities(sale=.1, refinancing=.1, other=0, default=0,
                                     sale_mobility_factor=bad)
    with pytest.raises(ValueError):
        supplied_cause_probabilities(sale=.1, refinancing=bad, other=0, default=0,
                                     sale_mobility_factor=1)


def test_supplied_causes_reject_overflow_and_missing_unestimated_inputs():
    from hazard.structural_sale_extension import supplied_cause_probabilities
    with pytest.raises(ValueError):
        supplied_cause_probabilities(sale=1e308, refinancing=0, other=0, default=0,
                                     sale_mobility_factor=2)
    with pytest.raises(TypeError):
        supplied_cause_probabilities(sale=.1, sale_mobility_factor=1)


def test_heterogeneous_borrowers_aggregate_probabilities_not_mean_intensities():
    from hazard.structural_sale_extension import (
        aggregate_borrower_probabilities, supplied_cause_probabilities,
    )
    borrowers = supplied_cause_probabilities(
        sale=[0, 2*np.log(2)], refinancing=0, other=0, default=0,
        sale_mobility_factor=1,
    )
    result = aggregate_borrower_probabilities(borrowers, weights=[1, 1])
    # Borrower probabilities are 0 and .75; mean-intensity conversion gives .5.
    assert result['sale'] == pytest.approx(.375)
    assert sum(result.values()) == pytest.approx(.375)
    assert aggregate_borrower_probabilities(borrowers, weights=[1, 3])['sale'] == pytest.approx(.5625)
    # Weight magnitudes do not change a weighted mean or overflow its denominator.
    assert aggregate_borrower_probabilities(borrowers, weights=[1e308, 1e308])['sale'] == pytest.approx(.375)


@pytest.mark.parametrize('weights', [[], [0, 0], [-1, 2], [1, np.nan], [1], [[1, 1]]])
def test_probability_aggregation_rejects_invalid_borrower_weights(weights):
    from hazard.structural_sale_extension import aggregate_borrower_probabilities
    probabilities = dict(sale=np.array([0, .75]), refinancing=np.zeros(2),
                         other=np.zeros(2), default=np.zeros(2))
    with pytest.raises(ValueError):
        aggregate_borrower_probabilities(probabilities, weights=weights)


@pytest.mark.parametrize('bad', [np.nan, np.inf, -.01, 1.01])
def test_probability_aggregation_rejects_invalid_probabilities(bad):
    from hazard.structural_sale_extension import aggregate_borrower_probabilities
    with pytest.raises(ValueError):
        aggregate_borrower_probabilities(
            dict(sale=[bad], refinancing=[0], other=[0], default=[0]), weights=[1],
        )


def test_probability_aggregation_rejects_nonexclusive_or_misaligned_causes():
    from hazard.structural_sale_extension import aggregate_borrower_probabilities
    with pytest.raises(ValueError):
        aggregate_borrower_probabilities(
            dict(sale=[.6], refinancing=[.6], other=[0], default=[0]), weights=[1],
        )
    with pytest.raises(ValueError):
        aggregate_borrower_probabilities(
            dict(sale=[.6, .3], refinancing=[.1], other=[0, 0], default=[0, 0]), weights=[1, 1],
        )
    with pytest.raises(ValueError):
        aggregate_borrower_probabilities(dict(sale=[.5]), weights=[1])


def test_static_refinancing_screen_deducts_explicit_upfront_cost():
    from hazard.structural_sale_extension import static_refinancing_savings
    # One month: old payment 101, new payment 100, zero discount, cost .25.
    assert static_refinancing_savings(
        balance=100, contract_rate=.12, refinance_rate=0, discount_rate=0,
        remaining_months=1, refinancing_cost=.25,
    ) == pytest.approx(.75)
    assert static_refinancing_savings(
        balance=100, contract_rate=.12, refinance_rate=.12, discount_rate=.12,
        remaining_months=12, refinancing_cost=2,
    ) == pytest.approx(-2)
    # Same principal and remaining term, signed savings, vector costs.
    np.testing.assert_allclose(static_refinancing_savings(
        balance=100, contract_rate=0, refinance_rate=0, discount_rate=0,
        remaining_months=12, refinancing_cost=[0, 2],
    ), [0, -2])


@pytest.mark.parametrize('change', [
    dict(balance=-1), dict(contract_rate=np.nan), dict(refinance_rate=-.01),
    dict(discount_rate=np.inf), dict(remaining_months=0),
    dict(remaining_months=1.5), dict(refinancing_cost=-1),
])
def test_static_refinancing_screen_rejects_invalid_inputs(change):
    from hazard.structural_sale_extension import static_refinancing_savings
    inputs = dict(balance=100, contract_rate=.12, refinance_rate=0,
                  discount_rate=0, remaining_months=12, refinancing_cost=0)
    inputs.update(change)
    with pytest.raises(ValueError):
        static_refinancing_savings(**inputs)


def test_static_refinancing_screen_has_no_cost_or_rate_defaults():
    from hazard.structural_sale_extension import static_refinancing_savings
    with pytest.raises(TypeError):
        static_refinancing_savings(balance=100, contract_rate=.12,
                                  refinance_rate=0, remaining_months=12)
