import pandas as pd
import pytest

from empirical_payoff_measurement import measure_payoffs, audit_gap_support


def source_row(**kw):
    row = dict(reporting_period='202205', prepaid_upb=30., first_observed_payoff_upb=5.,
               gap_payoff_upb=10., adjacent_opening_upb=100., coupon=.03,
               mean_loan_age=24., vintage=2020, fico_bucket='high', ltv_bucket='low')
    row.update(kw)
    return row


def test_gap_payoffs_are_not_one_month_events():
    out = measure_payoffs(pd.DataFrame([source_row()]), cutoff='202509')
    assert out.iloc[0].adjacent_payoff_upb == 15.
    assert out.iloc[0].adjacent_payoff_fraction == .15
    assert out.iloc[0].unallocated_timing_payoff_upb == 15.


@pytest.mark.parametrize('change,reason', [
    ({'adjacent_opening_upb': 0.}, 'zero_adjacent_denominator'),
    ({'prepaid_upb': 5.}, 'negative_adjusted_numerator'),
    ({'adjacent_opening_upb': 10.}, 'ratio_above_one'),
    ({'reporting_period': '202510'}, 'post_cutoff'),
    ({'prepaid_upb': float('nan')}, 'nonfinite_or_negative_source'),
])
def test_invalid_rows_recorded_not_clipped(change, reason):
    out = measure_payoffs(pd.DataFrame([source_row(**change)]), cutoff='202509')
    assert not out.iloc[0].measurement_valid
    assert reason in out.iloc[0].measurement_issue
    assert pd.isna(out.iloc[0].adjacent_payoff_fraction)


def test_duplicate_cohort_month_rejected():
    with pytest.raises(ValueError, match='Duplicate'):
        measure_payoffs(pd.DataFrame([source_row(), source_row()]), cutoff='202509')


def test_support_join_lags_benchmark_and_preserves_missing():
    d = measure_payoffs(pd.DataFrame([source_row(), source_row(reporting_period='202206')]), cutoff='202509')
    r = audit_gap_support(d, pd.Series({'202204': .04}), gap_basis='original_coupon', lag_months=1)
    assert r['missing_benchmark_months'] == ['202206']
    assert r['positive_gap_pp_range'] == pytest.approx([1., 1.])
    assert r['benchmark_lag_months'] == 1
    assert r['gap_sign'] == 'market_minus_original_coupon'


def test_no_contemporaneous_or_future_lag_and_no_current_rate_imputation():
    d = measure_payoffs(pd.DataFrame([source_row()]), cutoff='202509')
    with pytest.raises(ValueError):
        audit_gap_support(d, pd.Series({'202205': .04}), gap_basis='original_coupon', lag_months=-1)
    with pytest.raises(ValueError):
        audit_gap_support(d, pd.Series({'202205': .04}), gap_basis='current_note_rate', lag_months=1)
