"""Boundary checks for audited accounting and identified transition estimates."""
import os
import sys
from pathlib import Path

os.environ.setdefault("FRED_API_KEY", "test-no-network")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hazard"))

import numpy as np
import pandas as pd
import polars as pl
import pytest

from agents import MicrosimPool
from config import MARKOV_STATES
import competing_risks as cr
from markov import estimate_transitions_from_loans


def _pool(state="Current", regime="US"):
    return MicrosimPool(pl.DataFrame({
        "loan_id": ["a", "b"], "stratum_id": ["s", "s"],
        "fico": [720., 720.], "property_state": ["PA", "PA"],
        "orig_ltv": [80., 80.], "coupon": [.03, .03],
        "orig_upb": [100000., 100000.], "balance": [80000., 80000.],
        "loan_age": [36, 36], "state": [state, state],
        "original_loan_term": [180, 360],
    }), regime=regime, rng=np.random.default_rng(0))


def _matrix():
    return pd.DataFrame(np.eye(len(MARKOV_STATES)),
                        index=MARKOV_STATES, columns=MARKOV_STATES)


def _histories():
    return pd.DataFrame({
        "loan_sequence_number": ["a", "a", "b", "b"],
        "reporting_period": ["202301", "202302", "202301", "202302"],
        "current_upb": [100., 90., 300., 280.],
        "servicer_state": ["Current", "D30", "Current", "Current"],
    })


def test_fractional_and_markov_payoff_counts_each_borrower_once(monkeypatch):
    monkeypatch.setattr(cr, "PREPAY_MODE", "fractional")
    monkeypatch.setattr(cr, "prepay_hazard", lambda x, *a, **k: np.full(len(x), .01))
    monkeypatch.setattr(cr, "default_hazard", lambda x, *a, **k: np.zeros(len(x)))
    trans = _matrix()
    trans.loc["D30", :] = 0.
    trans.loc["D30", "Prepaid"] = 1.
    p = _pool(state="D30")
    result = cr.monthly_step(p, .07, trans=trans)
    assert result["prepay_count"] == 2
    assert result["prepay_upb"] == result["settled_b"] == 160000.
    assert not p.active_mask.any()
    assert p.cohort_burnout[0] == pytest.approx(.8)


def test_binary_payoff_records_principal_before_zeroing_balance(monkeypatch):
    monkeypatch.setattr(cr, "PREPAY_MODE", "binary")
    monkeypatch.setattr(cr, "prepay_hazard", lambda x, *a, **k: np.ones(len(x)))
    monkeypatch.setattr(cr, "default_hazard", lambda x, *a, **k: np.zeros(len(x)))
    p = _pool()
    result = cr.monthly_step(p, .07, trans=_matrix())
    assert result["prepay_count"] == 2
    assert result["prepay_upb"] == result["settled_b"] == 160000.
    assert not p.active_mask.any()
    assert p.cohort_burnout[0] == pytest.approx(.8)


@pytest.mark.parametrize("anchor", ["us_intercept", "dk_level"])
def test_danish_helpers_receive_each_loans_known_term(monkeypatch, anchor):
    from common import berger_calibration as calibration
    captured = []

    def capture(coupon, market, age, *, regime, term_months):
        captured.append(np.asarray(term_months))
        return np.zeros(len(coupon))

    monkeypatch.setattr(calibration, "get_danish_moving_anchor", lambda: anchor)
    monkeypatch.setattr(calibration, "danish_refi_in_place_cpr_annual", capture)
    monkeypatch.setattr(calibration, "danish_cpr_annual", capture)
    monkeypatch.setattr(cr, "prepay_hazard", lambda x, *a, **k: np.zeros(len(x)))
    monkeypatch.setattr(cr, "default_hazard", lambda x, *a, **k: np.zeros(len(x)))
    cr.monthly_step(_pool(regime="Danish"), .07, trans=_matrix())
    assert len(captured) == 1
    np.testing.assert_array_equal(captured[0], [180, 360])


def test_danish_calibration_accepts_term_vectors():
    from common.berger_calibration import _buyback_discount_frac, danish_cpr_annual
    coupon, age = np.array([.03, .03]), np.array([36, 36])
    terms = np.array([180, 360])
    discounts = _buyback_discount_frac(coupon, .07, age, terms)
    assert discounts[0] < discounts[1]
    vector = danish_cpr_annual(coupon, .07, age, regime="Danish", term_months=terms)
    scalar = [danish_cpr_annual(coupon[i:i+1], .07, age[i:i+1],
                              regime="Danish", term_months=int(terms[i]))[0]
              for i in range(2)]
    np.testing.assert_allclose(vector, scalar)


def test_nonunique_dataframe_index_does_not_change_transition_estimate():
    d = _histories()
    expected, _ = estimate_transitions_from_loans(d, estimation_end="202302")
    d.index = [0, 1, 0, 1]
    actual, _ = estimate_transitions_from_loans(d, estimation_end="202302")
    pd.testing.assert_frame_equal(actual, expected)


def test_opening_balance_weighting_differs_from_loan_counts():
    d = _histories()
    weighted, diag = estimate_transitions_from_loans(d, estimation_end="202302")
    counted, _ = estimate_transitions_from_loans(d, estimation_end="202302", weighting="count")
    assert weighted.loc["Current", "D30"] == .25
    assert counted.loc["Current", "D30"] == .5
    assert diag["opening_weight_by_state"]["Current"] == 400.
    assert diag["used_pairs"] == 2


def test_empty_histories_report_no_empirical_support():
    trans, diag = estimate_transitions_from_loans(_histories().iloc[:0], estimation_end="202302")
    np.testing.assert_array_equal(trans.to_numpy(), np.eye(len(MARKOV_STATES)))
    assert diag["eligible_rows"] == diag["used_pairs"] == 0
    assert set(diag["unsupported_states"]) == set(MARKOV_STATES)


def test_duplicate_loan_month_rejected():
    d = _histories()
    with pytest.raises(ValueError, match="duplicate loan-month"):
        estimate_transitions_from_loans(pd.concat([d, d.iloc[:1]]), estimation_end="202302")


@pytest.mark.parametrize("return_month", ["202302", "202304"])
def test_terminal_state_cannot_resurrect_even_across_reporting_gap(return_month):
    d = pd.DataFrame({"loan_sequence_number": ["a", "a"],
                      "reporting_period": ["202301", return_month],
                      "current_upb": [0., 100.],
                      "servicer_state": ["Prepaid", "Current"]})
    with pytest.raises(ValueError, match="resurrect"):
        estimate_transitions_from_loans(d, estimation_end="202304")


def test_after_cutoff_outcomes_and_duplicates_are_not_inspected():
    d = _histories()
    expected, expected_diag = estimate_transitions_from_loans(d, estimation_end="202302")
    poison = pd.DataFrame({"loan_sequence_number": ["a", "a"],
                           "reporting_period": ["202303", "202303"],
                           "current_upb": ["unread", "unread"],
                           "servicer_state": ["unread", "unread"]})
    actual, diag = estimate_transitions_from_loans(pd.concat([d, poison], ignore_index=True),
                                                 estimation_end="202302")
    pd.testing.assert_frame_equal(actual, expected)
    assert diag == expected_diag
