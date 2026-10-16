"""Independent payment/PV and exhaustive action-tree checks for the scenario."""
import importlib
import math
import numpy as np
import pytest

pytestmark = pytest.mark.filterwarnings("error")


def model():
    try:
        return importlib.import_module('hazard.dynamic_refinancing')
    except ModuleNotFoundError:
        pytest.fail('The approved dynamic refinancing scenario is not implemented')


def solve(**changes):
    inputs = dict(initial_coupon=.08, market_rates=[.06, .02],
                  transition_matrix=[[0, 1], [0, 1]], remaining_months=120,
                  discount_rate=.04, cost_fraction=.005)
    inputs.update(changes)
    return model().solve_dynamic_refinancing(**inputs)


def test_equal_coupon_has_scheduled_pv_and_wait_ties():
    result = solve(initial_coupon=.06, market_rates=[.06], transition_matrix=[[1]],
                   remaining_months=24, discount_rate=.06, cost_fraction=0)
    assert result.value(200000, market_state=0) == pytest.approx(200000, rel=1e-12)
    assert not result.refinance.any()
    result0 = solve(initial_coupon=0, market_rates=[0], transition_matrix=[[1]],
                    remaining_months=12, discount_rate=0, cost_fraction=0)
    assert result0.value(100, market_state=0) == pytest.approx(100)


def test_zero_horizon_has_no_debt_and_rejects_positive_balance():
    result = solve(remaining_months=0)
    assert result.value(0, market_state=0) == 0
    with pytest.raises(ValueError):
        result.value(100, market_state=0)


def test_prohibitive_cost_reproduces_independent_no_refinance_pv():
    result = solve(cost_fraction=10)
    payment = 200000*(.08/12)/(1-(1+.08/12)**-120)
    expected = math.fsum(payment/(1+.04/12)**j for j in range(1, 121))
    assert result.value(200000, market_state=0) == pytest.approx(expected, rel=1e-12)
    assert not result.refinance.any()


def test_positive_static_savings_can_still_mean_wait():
    result = solve()
    def pv(c):
        payment = 200000*(c/12)/(1-(1+c/12)**-120)
        return math.fsum(payment/(1+.04/12)**j for j in range(1, 121))
    assert pv(.08)-pv(.06)-1000 > 0
    initial_coupon_index = np.flatnonzero(result.coupons == .08)[0]
    assert not result.refinance[120, initial_coupon_index, 0]
    assert result.refinance[119, initial_coupon_index, 1]


def exhaustive_cash_cost(b, c, n, state, rates, matrix, discount, fee):
    # Full small decision tree, dollar balances, no memoization or normalized DP.
    if n == 0:
        return 0.
    outcomes = []
    for do_refinance in (False, True):
        coupon = rates[state] if do_refinance else c
        payment = b/n if coupon == 0 else b*(coupon/12)/(1-(1+coupon/12)**-n)
        next_balance = 0. if n == 1 else b*(1+coupon/12)-payment
        future = sum(matrix[state][j]*exhaustive_cash_cost(
            next_balance, coupon, n-1, j, rates, matrix, discount, fee)
            for j in range(len(rates)) if matrix[state][j])
        outcomes.append((fee*b if do_refinance else 0)+(payment+future)/(1+discount/12))
    return min(outcomes)


@pytest.mark.parametrize('fee', [0, .0001, .005, 10])
def test_bellman_matches_exhaustive_short_horizon_tree(fee):
    rates = [0, .06, .12]
    matrix = [[.6, .3, .1], [.2, .5, .3], [.1, .4, .5]]
    result = solve(initial_coupon=.09, market_rates=rates, transition_matrix=matrix,
                   remaining_months=4, discount_rate=.03, cost_fraction=fee)
    for state in range(3):
        expected = exhaustive_cash_cost(1234, .09, 4, state, rates, matrix, .03, fee)
        assert result.value(1234, market_state=state) == pytest.approx(expected, rel=1e-12)
        assert result.value(2468, market_state=state) == pytest.approx(2*expected, rel=1e-12)


def test_trace_preserves_maturity_and_charges_each_repeated_exercise():
    rates = [.08]*12+[.06]*12+[.02]*36
    matrix = np.zeros((60, 60))
    for i in range(59):
        matrix[i, i+1] = 1
    matrix[-1, -1] = 1
    result = solve(initial_coupon=.10, market_rates=rates, transition_matrix=matrix,
                   remaining_months=60, cost_fraction=.001)
    trace = result.trace(200000, market_states=list(range(60)))
    exercise = [row for row in trace['months'] if row['refinanced']]
    assert len(exercise) >= 2
    assert exercise[0]['month'] == 0
    for row in exercise:
        assert row['cash_refinancing_cost'] == pytest.approx(.001*row['opening_balance'])
    assert trace['ending_balance'] == 0
    assert trace['discounted_cash_cost'] == pytest.approx(result.value(200000, market_state=0), rel=1e-12)
    for row in trace['months']:
        assert row['remaining_months'] == 60-row['month']


@pytest.mark.parametrize('change', [
    dict(market_rates=[]), dict(market_rates=[np.nan, .02]),
    dict(initial_coupon=-.01), dict(cost_fraction=-1), dict(discount_rate=np.inf),
    dict(remaining_months=-1), dict(remaining_months=1.5),
    dict(transition_matrix=[[.5, .4], [0, 1]]),
    dict(transition_matrix=[[1.1, -.1], [0, 1]]),
    dict(transition_matrix=[[1]]), dict(tie_tolerance=-1),
])
def test_invalid_inputs_fail_closed(change):
    with pytest.raises(ValueError):
        solve(**change)


def test_trace_rejects_wrong_length_impossible_transitions_and_negative_balance():
    result = solve(remaining_months=2)
    with pytest.raises(ValueError):
        result.trace(100, market_states=[0])
    with pytest.raises(ValueError):
        result.trace(100, market_states=[1, 0])
    with pytest.raises(ValueError):
        result.value(-1, market_state=0)
    with pytest.raises(ValueError):
        result.value(100, market_state=2)


def test_duplicate_quote_state_splitting_is_representation_invariance():
    """Splitting each observable state into two equivalent labels changes no costs.

    This catches discarding duplicate quote states or using unweighted transitions.
    It is representation invariance of a supplied finite chain, not continuous
    process convergence. Both groups retain the same aggregate transition law.
    """
    original = solve(market_rates=[.06, .02],
                     transition_matrix=[[.6, .4], [.2, .8]], remaining_months=36)
    split = solve(market_rates=[.06, .02, .06, .02],
                  transition_matrix=[[.3, .2, .3, .2], [.1, .4, .1, .4],
                                     [.3, .2, .3, .2], [.1, .4, .1, .4]],
                  remaining_months=36)
    for old_state, copies in [(0, [0, 2]), (1, [1, 3])]:
        for new_state in copies:
            np.testing.assert_allclose(original.normalized_values[:, :, old_state],
                                       split.normalized_values[:, :, new_state],
                                       rtol=1e-13, atol=1e-13)
            np.testing.assert_array_equal(original.refinance[:, :, old_state],
                                          split.refinance[:, :, new_state])
