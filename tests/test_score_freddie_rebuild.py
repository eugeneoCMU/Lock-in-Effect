"""Offline retrospective scoring must retain frozen choices and evidence gates."""
import importlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from test_calibrate_freddie_rebuild import inputs as source_inputs, dump, source


def module():
    try:
        return importlib.import_module('hazard.score_freddie_rebuild')
    except ModuleNotFoundError as exc:
        pytest.fail(f'The offline corrected retrospective scorer is missing: {exc}')


def rebind(root):
    combined = root / 'combined'
    report = json.loads((combined / 'report.json').read_text())
    report['panel_rows'] = len(pd.read_parquet(combined / 'cohort_month_panel.parquet'))
    sample = pd.read_parquet(combined / 'loan_sample.parquet')
    report.update(sample_n=len(sample), sample_unique_ids=sample.loan_id.nunique())
    report['output_sha256'] = {name: source.digest(combined / name)
                              for name in report['output_sha256']}
    dump(combined / 'report.json', report)


@pytest.fixture
def inputs(source_inputs, tmp_path):
    root = source_inputs['root']
    months = pd.date_range('2022-12-01', '2025-09-01', freq='MS')
    panel = pd.DataFrame(dict(period=months, reporting_period=months.strftime('%Y%m'),
        vintage=2017, coupon=.03, fico_bucket='740+', ltv_bucket='<=80',
        mean_loan_age=50., exposure_upb=100., orig_upb_sum=200.,
        cohort_original_upb=1000., burnout=.8,
        prepaid_upb=np.where(months.year == 2023, 1., .5)))
    panel.to_parquet(root / 'combined/cohort_month_panel.parquet')
    sample = pd.DataFrame(dict(loan_id=['a', 'b'], vintage=2017, coupon=.03,
        fico_bucket='740+', ltv_bucket='<=80', fico=780., orig_ltv=70.,
        original_loan_term=360, reporting_period='202205',
        initial_burnout=.1, burnout_denominator_multiplier=2., balance=100.))
    sample.to_parquet(root / 'combined/loan_sample.parquet')
    rebind(root)
    macro = tmp_path / 'macro_frozen.parquet'
    pd.DataFrame({'MORTGAGE30US': 7.},
                 index=pd.date_range('2023-12-31', '2025-09-30', freq='ME')).to_parquet(macro)
    freeze = tmp_path / 'parameter_freeze.json'
    params = {name: dict(annual_floor=.035, psa=100., development_rmse_monthly_pp=.124)
              for name in ('floor_only', 'floor_psa')}
    dump(freeze, dict(selection_start='2023-01-01', selection_end='2023-12-01',
        annual_floor_grid=[0., .02, .035, .04991], psa_grid=[50., 75., 100.],
        selected=params, input_sha256={
            'output/review-revision/2026-10-07-checks/macro_frozen.parquet': source.digest(macro)}))
    recorded = tmp_path / 'recorded_results.json'
    dump(recorded, dict(evaluation_start='2024-01-01', evaluation_end='2025-09-01',
        parameter_freeze_sha256=source.digest(freeze), selected_parameters=params,
        input_sha256=json.loads(freeze.read_text())['input_sha256']))
    return dict(root=root, macro=macro, parameter_freeze=freeze, recorded_result=recorded,
                output=tmp_path / 'corrected-scores')


def test_offline_scores_preserve_choices_and_hand_calculated_comparator(inputs):
    before = {p: source.digest(p) for p in inputs['root'].rglob('*') if p.is_file()}
    result = module().run(**inputs)
    assert result['parameter_selection_performed'] is False
    assert result['baseline_training'] == ['2023-01-01', '2023-12-01']
    assert result['evaluation_start'] == '2024-01-01'
    assert result['evaluation_end'] == '2025-09-01'
    assert result['aggregate']['base']['predicted_b'] == pytest.approx(21. / 1e9)
    assert result['aggregate']['base']['observed_b'] == pytest.approx(10.5 / 1e9)
    assert result['aggregate']['original_off']['predicted_b'] == pytest.approx(
        2100. * (1. - (1. - .04991) ** (1. / 12.)) / 1e9)
    assert result['aggregate']['floor_only_on'] == result['aggregate']['floor_psa_on']
    assert result['support']['retained_rows'] == 21
    assert result['support']['exposure_retained_fraction'] == 1.
    assert result['prediction_calendar_rows'] == 21
    for name, metrics in result['aggregate'].items():
        assert sum(v['predicted_b'] for v in result['groups']['halfyear'][name].values()) == pytest.approx(metrics['predicted_b'])
    assert before == {p: source.digest(p) for p in before}
    assert json.loads((inputs['output'] / 'results.json').read_text()) == result


def test_missing_quarter_halts_before_output_or_outcome_read(inputs, monkeypatch):
    (inputs['root'] / 'quarters/2021Q4/completed.json').unlink()
    stage = module()
    def forbid(*args, **kwargs):
        raise AssertionError('Outcomes must not be read before the all-quarter gate')
    monkeypatch.setattr(stage, 'load_panel', forbid)
    with pytest.raises(FileNotFoundError, match='2021Q4'):
        stage.run(**inputs)
    assert not inputs['output'].exists()


@pytest.mark.parametrize('mutation', ['macro_hash', 'freeze_binding', 'selected_value',
                                    'result_selection', 'selection_window'])
def test_recorded_inputs_cannot_be_replaced_or_retuned(inputs, mutation):
    freeze = json.loads(inputs['parameter_freeze'].read_text())
    result = json.loads(inputs['recorded_result'].read_text())
    if mutation == 'macro_hash':
        inputs['macro'].write_bytes(b'changed macro bytes')
    elif mutation == 'freeze_binding':
        result['parameter_freeze_sha256'] = 'f' * 64
    elif mutation == 'selected_value':
        freeze['selected']['floor_psa']['annual_floor'] = .02
        result['selected_parameters'] = freeze['selected']
    elif mutation == 'result_selection':
        result['selected_parameters']['floor_only']['psa'] = 75.
    else:
        freeze['selection_end'] = '2024-12-01'
    if mutation not in ('freeze_binding', 'macro_hash', 'result_selection'):
        dump(inputs['parameter_freeze'], freeze)
        result['parameter_freeze_sha256'] = source.digest(inputs['parameter_freeze'])
    dump(inputs['recorded_result'], result)
    with pytest.raises(ValueError):
        module().run(**inputs)
    assert not inputs['output'].exists()


def test_identity_gate_rejects_later_outcomes_before_loading_them(inputs, monkeypatch):
    panel_path = inputs['root'] / 'combined/cohort_month_panel.parquet'
    d = pd.read_parquet(panel_path)
    later = d.iloc[-1:].assign(period=pd.Timestamp('2025-10-01'), reporting_period='202510', prepaid_upb=np.nan)
    pd.concat([d, later], ignore_index=True).to_parquet(panel_path)
    rebind(inputs['root'])
    stage = module()
    def forbid(*args, **kwargs):
        raise AssertionError('A post-cutoff source must be rejected before outcome access')
    monkeypatch.setattr(stage, 'load_panel', forbid)
    with pytest.raises(ValueError, match='cutoff'):
        stage.run(**inputs)
    assert not (inputs['output'] / 'results.json').exists()


def test_manifest_exists_before_outcome_columns_are_read(inputs, monkeypatch):
    stage = module()
    original = stage.load_panel
    def checked(path):
        manifest = json.loads((inputs['output'] / 'input_manifest.json').read_text())
        assert manifest['input_sha256'][str(inputs['macro'])] == source.digest(inputs['macro'])
        assert manifest['spec_sha256'] == source.digest(stage.SPEC)
        return original(path)
    monkeypatch.setattr(stage, 'load_panel', checked)
    stage.run(**inputs)


def test_invalid_observed_month_does_not_skip_predicted_history_update(inputs):
    stage = module()
    stage.run(**inputs)
    first = pd.read_parquet(inputs['output'] / 'predictions.parquet')
    path = inputs['root'] / 'combined/cohort_month_panel.parquet'
    d = pd.read_parquet(path)
    d.loc[d.reporting_period == '202401', 'prepaid_upb'] = 101.
    d.to_parquet(path)
    rebind(inputs['root'])
    inputs['output'] = inputs['output'].with_name('second-scores')
    result = stage.run(**inputs)
    second = pd.read_parquet(inputs['output'] / 'predictions.parquet')
    pd.testing.assert_frame_equal(first, second)
    assert result['exclusions']['evaluation']['invalid_numerator'] == 1
    assert result['support']['retained_rows'] == 20
    assert result['support']['input_rows'] == 21
    assert result['prediction_calendar_rows'] == 21


@pytest.mark.parametrize('field,value', [('burnout', 1.1), ('cohort_original_upb', 0.),
                                        ('mean_loan_age', np.nan)])
def test_invalid_december_state_stops_without_clipping_or_results(inputs, field, value):
    path = inputs['root'] / 'combined/cohort_month_panel.parquet'
    d = pd.read_parquet(path)
    d.loc[d.reporting_period == '202312', field] = value
    d.to_parquet(path)
    rebind(inputs['root'])
    with pytest.raises(ValueError):
        module().run(**inputs)
    assert (inputs['output'] / 'input_manifest.json').exists()
    assert (inputs['output'] / 'failed.json').exists()
    assert not (inputs['output'] / 'results.json').exists()


def test_support_exclusion_has_usable_dollar_denominator(inputs):
    path = inputs['root'] / 'combined/cohort_month_panel.parquet'
    d = pd.read_parquet(path)
    extra = d.assign(vintage=2018, exposure_upb=300., prepaid_upb=1.5)
    pd.concat([d, extra], ignore_index=True).to_parquet(path)
    rebind(inputs['root'])
    result = module().run(**inputs)
    support = result['support']
    assert support['input_rows'] == 42
    assert support['usable_rows'] == 42
    assert support['retained_rows'] == 21
    assert support['usable_exposure_b_months'] == pytest.approx(8400. / 1e9)
    assert support['retained_exposure_b_months'] == pytest.approx(2100. / 1e9)
    assert support['exposure_retained_fraction'] == .25
    assert support['no_covariate_rows'] == 21


def test_existing_attempt_is_preserved(inputs):
    inputs['output'].mkdir()
    (inputs['output'] / 'keep').write_text('preserve')
    with pytest.raises(FileExistsError):
        module().run(**inputs)
    assert (inputs['output'] / 'keep').read_text() == 'preserve'


def test_declared_sampling_with_replacement_keeps_the_combined_draw(inputs):
    path = inputs['root'] / 'combined/loan_sample.parquet'
    sample = pd.read_parquet(path)
    pd.concat([sample, sample.iloc[:1]], ignore_index=True).to_parquet(path)
    rebind(inputs['root'])
    result = module().run(**inputs)
    assert result['sampling']['rows'] == 3
    assert result['sampling']['unique_source_ids'] == 2
    assert result['sampling']['replacement_rows'] == 1
    assert result['support']['retained_rows'] == 21
