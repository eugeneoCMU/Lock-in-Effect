"""Accounting, temporal separation, and source-order regression evidence."""
import numpy as np
import pandas as pd
import polars as pl
import pytest

from hazard.pathb_prediction_diagnostics import (
    ORIGINAL_FLOOR, annual_floor_monthly, diagnose_groups, ordered_previous_upb,
    predict_path, select_parameters, strict_score,
)


def fixture():
    rows = pd.DataFrame({
        'cell': ['a', 'a'], 'period': pd.to_datetime(['2023-01-01', '2023-02-01']),
        'coupon': [.03, .03], 'opening_exposure': [100., 90.],
        'prepaid_upb': [2., 3.],
    })
    pre = pd.DataFrame({'cell': ['a'], 'period': pd.to_datetime(['2022-12-01']),
                        'mean_loan_age': [40.], 'burnout': [.2],
                        'exposure_upb': [100.], 'orig_upb_sum': [120.]}).set_index('cell')
    cov = pd.DataFrame({'fico_z': [0.], 'ltv_z': [0.]}, index=['a'])
    rates = pd.Series([.07, .07], index=pd.period_range('2023-01', periods=2, freq='M'))
    return rows, pre, cov, rates


def test_annual_probability_is_compounded_not_divided_or_used_monthly():
    floor = annual_floor_monthly(ORIGINAL_FLOOR)
    assert 1 - (1 - floor)**12 == pytest.approx(ORIGINAL_FLOOR)
    assert floor < .005
    assert floor != pytest.approx(ORIGINAL_FLOOR / 12)


def test_accounting_and_floor_group_totals_are_additive():
    d = pd.DataFrame({'opening_exposure': [100., 300.], 'prepaid_upb': [10., 30.],
                      'prediction': [.2, .1], 'group': ['bound', 'free']})
    s = strict_score(d.opening_exposure, d.prepaid_upb, d.prediction)
    assert s['predicted_b'] == pytest.approx(50 / 1e9)
    assert s['signed_error_b'] == pytest.approx(10 / 1e9)
    assert s['weighted_rmse_monthly_pp'] == pytest.approx(5.)
    g = diagnose_groups(d, 'group', 'prediction')
    assert sum(v['signed_error_b'] for v in g.values()) == pytest.approx(s['signed_error_b'])
    assert sum(v['predicted_b'] for v in g.values()) == pytest.approx(s['predicted_b'])


@pytest.mark.parametrize('exposure,event,hazard', [
    ([np.inf], [1], [.1]), ([0], [0], [.1]), ([100], [101], [.1]),
    ([100], [-1], [.1]), ([100], [1], [np.nan]), ([100], [1], [1.1]),
])
def test_invalid_accounting_inputs_fail(exposure, event, hazard):
    with pytest.raises(ValueError):
        strict_score(exposure, event, hazard)


def test_predictions_do_not_read_future_outcomes_or_realized_burnout():
    rows, pre, cov, rates = fixture()
    expected = predict_path(rows, pre, cov, rates, .02, 75, -.07)
    poisoned = rows.copy()
    poisoned['prepaid_upb'] = [99., 89.]
    poisoned['burnout'] = [np.nan, 10000.]
    poisoned['mean_loan_age'] = [-1000., 10000.]
    actual = predict_path(poisoned, pre, cov, rates, .02, 75, -.07)
    pd.testing.assert_frame_equal(expected, actual)


def test_response_off_removes_only_rate_gap_coefficient():
    rows, pre, cov, rates = fixture()
    off = predict_path(rows, pre, cov, rates, 0., 100, 0.)
    on = predict_path(rows, pre, cov, rates, 0., 100, -.07)
    assert on.hazard.iloc[0] / off.hazard.iloc[0] == pytest.approx(np.exp(-.07 * 4))
    zero_gap = rates * 0 + .03
    pd.testing.assert_frame_equal(
        predict_path(rows, pre, cov, zero_gap, .02, 75, 0.),
        predict_path(rows, pre, cov, zero_gap, .02, 75, -.07),
    )


def test_development_selector_rejects_evaluation_rows():
    rows, pre, cov, rates = fixture()
    rows.loc[0, 'period'] = pd.Timestamp('2024-01-01')
    with pytest.raises(ValueError, match='2023'):
        select_parameters(rows, pre, cov, rates)


def test_selection_uses_training_error_and_prespecified_grid():
    rows, pre, cov, rates = fixture()
    # Use the same imported coefficient as the implementation, never evaluation data.
    from hazard.pathb_prediction_diagnostics import RESPONSE_BETA
    truth = predict_path(rows, pre, cov, rates, .02, 75, RESPONSE_BETA)
    rows['prepaid_upb'] = rows.opening_exposure * truth.hazard
    selected, grid = select_parameters(rows, pre, cov, rates)
    assert len(grid) == 12
    assert selected['floor_psa']['psa'] == 75
    assert selected['floor_psa']['annual_floor'] == .02
    assert selected['floor_psa']['development_rmse_monthly_pp'] < 1e-12


def test_ingest_unsorted_rows_reproduce_wrong_payoff_and_ordered_fix(monkeypatch, tmp_path):
    """Real ingest function: input order can turn a $90 payoff into $100.

    This proves a latent implementation bug, not corruption of the saved panel.
    No source files are modified and real loan histories are never opened.
    """
    from hazard import ingest
    perf = pl.DataFrame({
        'loan_sequence_number': ['a', 'a', 'a'],
        'reporting_period': ['202301', '202303', '202302'],
        'current_upb': [100., 0., 90.], 'is_prepay': [False, True, False],
        'loan_age': [1., 3., 2.], 'servicer_state': ['Current', 'Prepaid', 'Current'],
    })
    orig = pl.DataFrame({'loan_sequence_number': ['a'], 'vintage': [2020],
                         'coupon': [.03], 'fico_bucket': ['740+'], 'ltv_bucket': ['≤80'],
                         'original_upb': [100.]})
    monkeypatch.setattr(ingest, '_scan_orig', lambda _: orig.lazy())
    monkeypatch.setattr(ingest, '_scan_perf', lambda _: perf.lazy())
    actual = ingest.build_panel_from_files([(tmp_path/'orig', tmp_path/'perf')], tmp_path/'panel.parquet')
    actual_payoff = actual.filter(pl.col('reporting_period') == '202303')['prepaid_upb'].item()
    legacy = perf.with_columns(pl.col('current_upb').shift(1).over('loan_sequence_number').alias('prev_upb'))
    legacy_payoff = legacy.filter(pl.col('reporting_period') == '202303')['prev_upb'].item()
    corrected = ordered_previous_upb(perf)
    ordered_payoff = corrected.filter(pl.col('reporting_period') == '202303')['prev_upb'].item()
    assert legacy_payoff == 100.
    assert ordered_payoff == 90.
    assert legacy_payoff != ordered_payoff
    assert actual_payoff == 90.
