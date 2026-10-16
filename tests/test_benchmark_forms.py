"""Additive benchmark uses the same gates, accounting and fixed reference."""
import importlib
import json
import numpy as np
import pandas as pd
import pytest
from test_calibrate_freddie_rebuild import inputs as source_inputs
from test_simulate_freddie_rebuild import pair_inputs
from test_calibrate_freddie_rebuild import inputs as floor_inputs
from test_score_freddie_rebuild import inputs


def forms():
    try:
        return importlib.import_module('hazard.benchmark_forms')
    except ModuleNotFoundError:
        pytest.fail('Additive benchmark adapter is missing')


def test_real_additive_pair_preserves_accounting_and_restores(pair_inputs):
    from hazard import simulate_freddie_rebuild as pair
    previous = pair.PARAMETERS, pair.SPEC, pair.CODE_FILES, pair.lh.FLOOR_MODE
    result = forms().run_additive_pair(**pair_inputs)
    assert result['parameters']['floor_form'] == 'additive'
    assert result['parameters']['annual_floor'] == .04991
    assert result['closed_pool_cash_marginal_b'] > 0
    assert result['legs']['on']['max_total_identity_error_b'] < 1e-8
    assert (pair.PARAMETERS, pair.SPEC, pair.CODE_FILES, pair.lh.FLOOR_MODE) == previous
    saved = json.loads((pair_inputs['output']/'results.json').read_text())
    assert saved == result
    assert 'additive' in result['scope'].lower()


def test_pair_context_restores_after_failure():
    from hazard import simulate_freddie_rebuild as pair
    previous = pair.PARAMETERS, pair.SPEC, pair.CODE_FILES, pair.lh.FLOOR_MODE
    with pytest.raises(RuntimeError):
        with forms().additive_pair_context():
            pair.validate_conventions()
            assert pair.lh.FLOOR_MODE == 'additive'
            raise RuntimeError('probe')
    assert (pair.PARAMETERS, pair.SPEC, pair.CODE_FILES, pair.lh.FLOOR_MODE) == previous


def test_additive_scoring_and_hand_calculated_first_month(inputs):
    from hazard import score_freddie_rebuild as scoring
    from hazard.pathb_prediction_diagnostics import annual_floor_monthly, lh
    previous = scoring.predict_path, scoring.recorded_choices, scoring.SPEC, scoring.CODE_FILES
    result = forms().score_additive(**inputs)
    assert set(result['parameters']) == {'additive'}
    assert result['parameters']['additive']['annual_floor'] == .04991
    prediction = pd.read_parquet(inputs['output']/'predictions.parquet')
    row = prediction.iloc[0]
    vol = float(lh.h0_psa(np.array([51.]), psa_speed=100.)[0]*np.exp(-.5*.8))
    expected = 1-(1-annual_floor_monthly(.04991))*(1-vol)
    assert row.additive_off == pytest.approx(expected)
    assert not prediction.additive_on_floor_bound.any()
    assert (scoring.predict_path, scoring.recorded_choices, scoring.SPEC, scoring.CODE_FILES) == previous


def test_additive_retains_recorded_choice_gate_and_restores(inputs):
    from hazard import score_freddie_rebuild as scoring
    inputs['parameter_freeze'].write_text('{}')
    previous = scoring.predict_path, scoring.recorded_choices, scoring.SPEC, scoring.CODE_FILES
    with pytest.raises(ValueError):
        forms().score_additive(**inputs)
    assert not inputs['output'].exists()
    assert (scoring.predict_path, scoring.recorded_choices, scoring.SPEC, scoring.CODE_FILES) == previous


def test_unrequested_additive_mode_rejected():
    from hazard import simulate_freddie_rebuild as pair
    old = pair.lh.FLOOR_MODE
    try:
        pair.lh.FLOOR_MODE = 'additive'
        with pytest.raises(ValueError):
            pair.validate_conventions()
    finally:
        pair.lh.FLOOR_MODE = old


def test_predictor_additive_saturates_without_floor_censoring():
    from hazard.pathb_prediction_diagnostics import predict_path
    rows = pd.DataFrame({'cell':['one'], 'period':pd.to_datetime(['2024-01-01']), 'coupon':[.03]})
    pre = pd.DataFrame({'cell':['one'], 'period':pd.to_datetime(['2023-12-01']),
        'mean_loan_age':[60.], 'burnout':[.8], 'exposure_upb':[100.],
        'cohort_original_upb':[1000.]}).set_index('cell')
    cov = pd.DataFrame({'cell':['one'], 'fico_z':[-1000.], 'ltv_z':[0.]}).set_index('cell')
    rates = pd.Series([.07], index=pd.period_range('2024-01','2024-01',freq='M'))
    result = predict_path(rows,pre,cov,rates,.04991,100.,0.,floor_form='additive')
    # Both saturated voluntary and default probabilities normalize to one half.
    assert result.hazard.iloc[0] == pytest.approx(.5)
    assert result.normalized.iloc[0]
    assert not result.floor_bound.iloc[0]
    with pytest.raises(ValueError,match='floor form'):
        predict_path(rows,pre,cov,rates,.04991,100.,0.,floor_form='unknown')
