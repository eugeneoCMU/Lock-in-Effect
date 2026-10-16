"""Cost-denominator conversion and fee-settlement accounting scenarios."""

import importlib
import json
import math

import numpy as np
import pytest

from hazard.dynamic_refinancing_terms import solve_term_refinancing


def bridge(q, **kwargs):
    # Delayed import keeps the missing-feature RED phase an ordinary test failure.
    module = importlib.import_module("hazard.refinancing_cost_bridge")
    return module.bridge_cost_ratio(q, **kwargs)


@pytest.mark.parametrize("financing", ["cash", "financed"])
@pytest.mark.parametrize("purpose_code", [31, 32])
def test_supplied_balance_ratio_converts_new_loan_denominator(financing, purpose_code):
    # $6,000 / $300,000 new loan; $250,000 incumbent balance: k = 0.024.
    result = bridge(
        0.02, balance_rule="supplied_balance_ratio", financing=financing,
        new_to_existing_ratio=1.2, purpose_code=purpose_code,
    )
    assert result["cost_fraction"] == pytest.approx(0.024)
    assert result["new_to_existing_ratio"] == 1.2
    assert result["reported_cost_to_new_loan_ratio"] == 0.02
    assert result["purpose_code"] == purpose_code
    assert result["financing"] == financing


def test_unchanged_balance_cash_scenario_uses_equal_denominators():
    result = bridge(
        0.02, balance_rule="unchanged_balance", financing="cash", purpose_code=31,
    )
    assert result["cost_fraction"] == 0.02
    assert result["new_to_existing_ratio"] == 1.0


def test_financed_no_other_balance_change_solves_fee_identity():
    # Fee 25 on old balance 100 gives new balance 125 and q = 0.2.
    result = bridge(
        0.2, balance_rule="all_fees_financed_no_other_balance_change",
        financing="financed", purpose_code=31,
    )
    assert result["cost_fraction"] == pytest.approx(0.25)
    assert result["new_to_existing_ratio"] == pytest.approx(1.25)


@pytest.mark.parametrize(
    "balance_rule,financing,ratio",
    [
        ("supplied_balance_ratio", "cash", 1.2),
        ("supplied_balance_ratio", "financed", 1.2),
        ("unchanged_balance", "cash", None),
        ("all_fees_financed_no_other_balance_change", "financed", None),
    ],
)
def test_reported_zero_cost_is_valid_without_imputation(balance_rule, financing, ratio):
    result = bridge(
        0.0, balance_rule=balance_rule, financing=financing,
        new_to_existing_ratio=ratio, purpose_code=31,
    )
    assert result["cost_fraction"] == 0.0
    assert result["reported_cost_to_new_loan_ratio"] == 0.0
    assert result["new_to_existing_ratio"] == (1.2 if ratio is not None else 1.0)


@pytest.mark.parametrize(
    "balance_rule,financing,q",
    [
        ("unchanged_balance", "cash", 0.02),
        ("all_fees_financed_no_other_balance_change", "financed", 0.2),
    ],
)
def test_bridge_fee_is_charged_once_by_existing_solver(
    balance_rule, financing, q,
):
    result = bridge(q, balance_rule=balance_rule, financing=financing, purpose_code=31)
    solution = solve_term_refinancing(
        # Deliberately high hypothetical coupon forces refinancing even with a
        # 25% fee and a one-month horizon, so fee settlement is exercised.
        initial_coupon=4.0, remaining_months=12, offer_rates=[[0.0]],
        offer_terms=[12], transition_matrix=[[1.0]], horizon_months=1,
        discount_rate=0.0, cost_fraction=result["cost_fraction"], financing=financing,
    )
    trace = solution.trace(100.0, market_states=[0])
    first = trace["months"][0]
    assert first["refinanced"]
    if financing == "cash":
        assert first["cash_cost"] == pytest.approx(2.0)
        assert first["financed_cost"] == 0.0
        assert first["scheduled_payment"] == pytest.approx(100.0 / 12)
        assert trace["discounted_cash_cost"] == pytest.approx(102.0)
    else:
        assert first["cash_cost"] == 0.0
        assert first["financed_cost"] == pytest.approx(25.0)
        assert first["scheduled_payment"] == pytest.approx(125.0 / 12)
        assert trace["discounted_cash_cost"] == pytest.approx(125.0)
    assert trace["discounted_cash_cost"] == pytest.approx(
        solution.value(100.0, market_state=0), abs=1e-10,
    )


def test_result_records_scenario_and_cost_scope_and_is_strict_json():
    result = bridge(
        0.02, balance_rule="supplied_balance_ratio", financing="financed",
        new_to_existing_ratio=1.2, purpose_code=np.int64(32),
    )
    restored = json.loads(json.dumps(result, allow_nan=False))
    assert restored == result
    assert result["evidence_class"] == "conditional_cost_scenario"
    assert result["cost_component"] == "reported_loan_costs"
    assert result["balance_rule"] == "supplied_balance_ratio"
    assert result["input_denominator"] == "public_rounded_new_loan_amount"
    assert result["model_denominator"] == "existing_opening_principal"
    assert result["assumptions"]
    assert result["limitations"]
    assert "production_ready" not in result


@pytest.mark.parametrize(
    "q", [None, True, np.bool_(False), -0.01, math.inf, -math.inf, math.nan, "0.02", []],
)
def test_invalid_or_missing_reported_ratios_are_rejected(q):
    with pytest.raises(ValueError):
        bridge(q, balance_rule="unchanged_balance", financing="cash", purpose_code=31)


@pytest.mark.parametrize(
    "ratio", [None, True, np.bool_(True), 0.0, -1.0, math.inf, math.nan, "1.2", []],
)
def test_supplied_rule_requires_explicit_positive_finite_numeric_ratio(ratio):
    with pytest.raises(ValueError):
        bridge(
            0.02, balance_rule="supplied_balance_ratio", financing="cash",
            new_to_existing_ratio=ratio, purpose_code=31,
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"balance_rule": "unknown", "financing": "cash", "purpose_code": 31},
        {"balance_rule": None, "financing": "cash", "purpose_code": 31},
        {"balance_rule": "unchanged_balance", "financing": "unknown", "purpose_code": 31},
        {"balance_rule": "unchanged_balance", "financing": None, "purpose_code": 31},
        {"balance_rule": "unchanged_balance", "financing": "financed", "purpose_code": 31},
        {"balance_rule": "unchanged_balance", "financing": "cash", "purpose_code": 32},
        {"balance_rule": "all_fees_financed_no_other_balance_change", "financing": "cash", "purpose_code": 31},
        {"balance_rule": "all_fees_financed_no_other_balance_change", "financing": "financed", "purpose_code": 32},
    ],
)
def test_unknown_or_inconsistent_scenario_combinations_fail_closed(kwargs):
    with pytest.raises(ValueError):
        bridge(0.02, **kwargs)


@pytest.mark.parametrize("balance_rule,financing", [
    ("unchanged_balance", "cash"),
    ("all_fees_financed_no_other_balance_change", "financed"),
])
def test_identity_rules_reject_even_plausible_supplied_balance_ratios(balance_rule, financing):
    with pytest.raises(ValueError):
        bridge(
            0.02, balance_rule=balance_rule, financing=financing,
            new_to_existing_ratio=1.0, purpose_code=31,
        )


@pytest.mark.parametrize("q", [1.0, 1.01, 1e308])
def test_financed_identity_requires_fee_ratio_below_one(q):
    with pytest.raises(ValueError):
        bridge(
            q, balance_rule="all_fees_financed_no_other_balance_change",
            financing="financed", purpose_code=31,
        )


@pytest.mark.parametrize("purpose_code", [None, True, np.bool_(True), 1, 2, 31.0, "31", math.nan])
def test_only_explicit_refinancing_integer_purpose_codes_are_accepted(purpose_code):
    with pytest.raises(ValueError):
        bridge(
            0.02, balance_rule="supplied_balance_ratio", financing="cash",
            new_to_existing_ratio=1.0, purpose_code=purpose_code,
        )


@pytest.mark.parametrize("missing", ["balance_rule", "financing", "purpose_code"])
def test_no_default_scenario_selection(missing):
    kwargs = {"balance_rule": "unchanged_balance", "financing": "cash", "purpose_code": 31}
    kwargs.pop(missing)
    with pytest.raises(TypeError):
        bridge(0.02, **kwargs)


def test_finite_inputs_that_overflow_converted_cost_are_rejected():
    with pytest.raises(ValueError):
        bridge(
            1e308, balance_rule="supplied_balance_ratio", financing="cash",
            new_to_existing_ratio=2.0, purpose_code=31,
        )
