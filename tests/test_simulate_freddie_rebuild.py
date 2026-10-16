"""Offline pair tests use a synthetic book and the real monthly engine."""
import importlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
import pytest

from test_calibrate_freddie_rebuild import inputs as floor_inputs, source, dump


def module():
    try:
        return importlib.import_module('hazard.simulate_freddie_rebuild')
    except ModuleNotFoundError as exc:
        pytest.fail(f'The gated offline paired simulation wrapper is missing: {exc}')


@pytest.fixture
def pair_inputs(floor_inputs, tmp_path):
    root = floor_inputs['root']
    combined = root / 'combined'
    n = 20
    loans = pl.DataFrame({
        'loan_id': [f'F{q[2:]}000001' for q in source.QUARTERS],
        'stratum_id': ['one'] * n, 'fico': [720.] * n, 'orig_ltv': [80.] * n,
        'property_state': ['PA'] * n, 'coupon': [.03] * n, 'orig_upb': [120000.] * n,
        'balance': [100000.] * n, 'loan_age': [359., 36.] + [60.] * (n - 2),
        'vintage': [int(q[:4]) for q in source.QUARTERS],
        'original_loan_term': [360.] * n, 'initial_burnout': [.2] * n,
        'burnout_denominator_multiplier': [1.25] * n, 'reporting_period': ['202205'] * n,
        'state': ['Current', 'D30'] + ['Current'] * (n - 2), 'weight': [1.] * n})
    loans.write_parquet(combined / 'loan_sample.parquet')
    from config import MARKOV_STATES
    matrix = pd.DataFrame(np.eye(len(MARKOV_STATES)), index=MARKOV_STATES, columns=MARKOV_STATES)
    matrix.loc['D30'] = 0.
    matrix.loc['D30', 'Defaulted'] = 1.
    matrix.attrs = dict(estimator='identified_monthly_loan_transitions', estimation_end='202205', weighting='balance')
    matrix.to_parquet(combined / 'markov_transition_matrix.parquet')
    report = json.loads((combined / 'report.json').read_text())
    for name in report['output_sha256']:
        report['output_sha256'][name] = source.digest(combined / name)
    dump(combined / 'report.json', report)
    dates = pd.date_range('2021-01-31', '2026-10-31', freq='ME')
    macro = pd.DataFrame({'WSHOMCB': 2700000., 'MORTGAGE30US': 6.,
                         'ACTLISCOUUS': 100., 'UMCSENT': 90.}, index=dates)
    macro.loc['2022-05-31', 'WSHOMCB'] = 2707446.
    macro_path = tmp_path / 'macro_frozen.parquet'
    macro.to_parquet(macro_path)
    freeze_path = tmp_path / 'parameter_freeze.json'
    dump(freeze_path, {'annual_floor_grid': [0., .02, .035, .04991], 'psa_grid': [50., 75., 100.],
        'selected': {'floor_only': {'annual_floor': .035, 'psa': 100.},
                     'floor_psa': {'annual_floor': .035, 'psa': 100.}},
        'selection_start': '2023-01-01', 'selection_end': '2023-12-01',
        'input_sha256': {str(macro_path): source.digest(macro_path)}})
    qt = pd.date_range('2022-06-30', '2025-11-30', freq='ME')
    actual = (764.7482532227002 - 1417.5) / 42
    archive = pd.DataFrame({'MORTGAGE30US': 6., 'QT_Target_Billions': [-17.5] * 3 + [-35.] * 39,
                            'Actual_Monthly_Rolloff_Billions': actual,
                            'Empirical_CPR_Pct': 999.}, index=qt)
    archive['Extension_Delta_Billions'] = actual - archive.QT_Target_Billions
    archive_path = tmp_path / 'metrics_monthly.csv'
    archive.to_csv(archive_path)
    benchmark = tmp_path / 'monthly_benchmark.json'
    dump(benchmark, {'status': 'OK', 'committed_method_monthly_diff_b':
                     {ts.strftime('%Y-%m'): actual for ts in qt}})
    inventory = tmp_path / 'downstream_inventory.json'
    def item(path): return {'path': str(path), 'sha256': source.digest(path)}
    dump(inventory, {'frozen_macro': item(macro_path), 'recorded_selection': item(freeze_path),
        'archived_empirical_comparator': dict(item(archive_path), monthly_rebuild_reference=item(benchmark))})
    return dict(root=root, macro_path=macro_path, parameter_freeze=freeze_path,
                empirical_csv=archive_path, input_inventory=inventory,
                benchmark_reference=benchmark, output=tmp_path / 'new-pair')


def refresh_inventory(paths):
    path = paths['input_inventory']
    data = json.loads(path.read_text())
    for key, field in [('macro_path', 'frozen_macro'), ('parameter_freeze', 'recorded_selection'),
                       ('empirical_csv', 'archived_empirical_comparator')]:
        data[field]['sha256'] = source.digest(paths[key])
    data['archived_empirical_comparator']['monthly_rebuild_reference']['sha256'] = source.digest(paths['benchmark_reference'])
    dump(path, data)


def test_real_engine_pair_keeps_initial_holdings_and_reconciles_both_legs(pair_inputs, monkeypatch):
    stage = module()
    previous_floor, previous_step = stage.lh.INVOLUNTARY_CPR_ANNUAL, stage.engine.monthly_step
    original_run = stage.engine.run_qt_microsim
    calls = []
    def explicit_engine_call(**kwargs):
        assert (pair_inputs['output'] / 'input_manifest.json').exists()
        assert kwargs['allow_legacy_inputs'] is False
        assert kwargs['regimes'] == ('US',) and kwargs['seed'] == 42
        assert kwargs['macro'].index[0] == pd.Timestamp('2021-01-31')
        assert len(kwargs['macro']) == 70
        assert stage.lh.INVOLUNTARY_CPR_ANNUAL == .04991
        calls.append(kwargs['p_q_shock_pct'])
        return original_run(**kwargs)
    monkeypatch.setattr(stage.engine, 'run_qt_microsim', explicit_engine_call)
    result = stage.run(**pair_inputs)
    assert calls == [0., 6.5]
    assert result['initialization'] == {'date': '2022-05-31', 'holdings_b': 2707.446}
    assert result['empirical_benchmark']['denominator_b'] == pytest.approx(764.7482532227002, abs=1e-8)
    for name in ['off', 'on']:
        accounting = pd.read_parquet(pair_inputs['output'] / f'{name}_accounting.parquet')
        simulation = pd.read_parquet(pair_inputs['output'] / f'{name}_simulation.parquet')
        assert len(accounting) == len(simulation) == 42
        assert accounting.opening_active_b.iloc[0] == pytest.approx(2707.446)
        np.testing.assert_allclose(accounting.opening_active_b - accounting.closing_active_b,
            accounting.voluntary_b + accounting.scheduled_b + accounting.default_transfer_b + accounting.other_terminal_transfer_b,
            rtol=1e-12, atol=1e-8)
        np.testing.assert_allclose(accounting.opening_total_b - accounting.closing_total_b,
                                   accounting.voluntary_b + accounting.scheduled_b, rtol=1e-12, atol=1e-8)
        np.testing.assert_allclose(-simulation.simulated_rolloff_b, accounting.production_principal_b)
        assert accounting.default_transfer_b.sum() > 0
        assert accounting.default_cash_b.sum() == 0
        assert accounting.scheduled_b.iloc[1] > accounting.scheduled_b.iloc[2]
    empirical = pd.read_parquet(pair_inputs['output'] / 'empirical_replay.parquet')
    assert (empirical.Empirical_CPR_Pct < 999).all()
    assert result['parameter_selection_performed'] is False
    assert result['source_inputs_unchanged'] is True
    assert stage.lh.INVOLUNTARY_CPR_ANNUAL == previous_floor
    assert stage.engine.monthly_step is previous_step


def test_missing_source_quarter_prevents_any_simulation_output(pair_inputs):
    (pair_inputs['root'] / 'quarters/2021Q4/completed.json').unlink()
    with pytest.raises(FileNotFoundError, match='2021Q4'): module().run(**pair_inputs)
    assert not pair_inputs['output'].exists()


@pytest.mark.parametrize('mutation', ['inventory_hash', 'freeze_macro_hash', 'wrong_initialization',
                                     'missing_month', 'different_selected_candidate'])
def test_recorded_inputs_and_initialization_cannot_drift(pair_inputs, mutation):
    if mutation in ('wrong_initialization', 'missing_month'):
        macro = pd.read_parquet(pair_inputs['macro_path'])
        if mutation == 'wrong_initialization': macro = macro.loc[macro.index >= '2022-06-01']
        else: macro = macro.drop(pd.Timestamp('2023-08-31'))
        macro.to_parquet(pair_inputs['macro_path'])
        freeze = json.loads(pair_inputs['parameter_freeze'].read_text())
        freeze['input_sha256'][str(pair_inputs['macro_path'])] = source.digest(pair_inputs['macro_path'])
        dump(pair_inputs['parameter_freeze'], freeze)
        refresh_inventory(pair_inputs)
    elif mutation == 'inventory_hash': pair_inputs['empirical_csv'].write_text('changed archived data')
    else:
        freeze = json.loads(pair_inputs['parameter_freeze'].read_text())
        if mutation == 'freeze_macro_hash': freeze['input_sha256'][str(pair_inputs['macro_path'])] = 'b' * 64
        else: freeze['selected']['floor_only']['annual_floor'] = .02
        dump(pair_inputs['parameter_freeze'], freeze)
        refresh_inventory(pair_inputs)
    with pytest.raises(ValueError): module().run(**pair_inputs)
    assert not (pair_inputs['output'] / 'off_simulation.parquet').exists()
    assert not (pair_inputs['output'] / 'results.json').exists()


@pytest.mark.parametrize('mutation', ['same_total_changed_months', 'different_denominator', 'monthly_reference'])
def test_benchmark_gate_uses_each_month_and_the_frozen_total(pair_inputs, mutation):
    path = pair_inputs['empirical_csv']
    archive = pd.read_csv(path, index_col=0)
    if mutation == 'monthly_reference':
        ref = json.loads(pair_inputs['benchmark_reference'].read_text())
        ref['committed_method_monthly_diff_b']['2022-06'] += 1.
        dump(pair_inputs['benchmark_reference'], ref)
    else:
        archive.iloc[0, archive.columns.get_loc('Actual_Monthly_Rolloff_Billions')] += 1.
        if mutation == 'same_total_changed_months':
            archive.iloc[1, archive.columns.get_loc('Actual_Monthly_Rolloff_Billions')] -= 1.
        archive['Extension_Delta_Billions'] = archive.Actual_Monthly_Rolloff_Billions - archive.QT_Target_Billions
        if mutation == 'different_denominator':
            ref = json.loads(pair_inputs['benchmark_reference'].read_text())
            ref['committed_method_monthly_diff_b']['2022-06'] += 1.
            dump(pair_inputs['benchmark_reference'], ref)
        archive.to_csv(path)
    refresh_inventory(pair_inputs)
    with pytest.raises(ValueError): module().run(**pair_inputs)
    assert (pair_inputs['output'] / 'input_manifest.json').exists()
    assert not (pair_inputs['output'] / 'off_simulation.parquet').exists()


def test_failed_second_leg_restores_floor_and_step_and_preserves_first_leg(pair_inputs, monkeypatch):
    stage = module()
    old_floor, old_step = stage.lh.INVOLUNTARY_CPR_ANNUAL, stage.engine.monthly_step
    original = stage.engine.run_qt_microsim
    def failing_on(**kwargs):
        if kwargs['p_q_shock_pct'] == 6.5:
            raise RuntimeError('synthetic second-leg failure')
        return original(**kwargs)
    monkeypatch.setattr(stage.engine, 'run_qt_microsim', failing_on)
    with pytest.raises(RuntimeError, match='second-leg'): stage.run(**pair_inputs)
    assert stage.lh.INVOLUNTARY_CPR_ANNUAL == old_floor
    assert stage.engine.monthly_step is old_step
    assert (pair_inputs['output'] / 'off_simulation.parquet').exists()
    assert (pair_inputs['output'] / 'failed.json').exists()
    assert not (pair_inputs['output'] / 'results.json').exists()


def test_changed_source_after_simulation_cannot_write_success(pair_inputs, monkeypatch):
    stage = module()
    original = stage.engine.run_qt_microsim
    def changing_input(**kwargs):
        result = original(**kwargs)
        if kwargs['p_q_shock_pct'] == 6.5:
            pair_inputs['empirical_csv'].write_text(pair_inputs['empirical_csv'].read_text() + '\n')
        return result
    monkeypatch.setattr(stage.engine, 'run_qt_microsim', changing_input)
    with pytest.raises(ValueError, match='changed'): stage.run(**pair_inputs)
    assert (pair_inputs['output'] / 'failed.json').exists()
    assert not (pair_inputs['output'] / 'results.json').exists()


def test_existing_output_is_preserved(pair_inputs):
    pair_inputs['output'].mkdir()
    (pair_inputs['output'] / 'old.txt').write_text('preserved')
    with pytest.raises(FileExistsError): module().run(**pair_inputs)
    assert (pair_inputs['output'] / 'old.txt').read_text() == 'preserved'


def test_monthly_reference_may_include_later_month_without_expanding_qt(pair_inputs):
    reference = json.loads(pair_inputs['benchmark_reference'].read_text())
    reference['committed_method_monthly_diff_b']['2025-12'] = 'DO NOT DECODE'
    dump(pair_inputs['benchmark_reference'], reference)
    refresh_inventory(pair_inputs)
    result = module().run(**pair_inputs)
    assert result['empirical_benchmark']['months'] == 42
    assert result['empirical_benchmark']['excluded_reference_months'] == ['2025-12']


def test_altered_active_hazard_convention_is_rejected(pair_inputs, monkeypatch):
    stage = module()
    monkeypatch.setattr(stage.cr, 'PREPAY_MODE', 'absorbing')
    with pytest.raises(ValueError, match='convention'): stage.run(**pair_inputs)
    assert not (pair_inputs['output'] / 'off_simulation.parquet').exists()


def replacement_draw(paths, *, conflict=False, declared_unique=19):
    combined = paths['root'] / 'combined'
    path = combined / 'loan_sample.parquet'
    original = pl.read_parquet(path)
    copy = original.head(1)
    if conflict:
        copy = copy.with_columns((pl.col('balance') + 1.).alias('balance'))
    pl.concat([original.head(19), copy]).write_parquet(path)
    report = json.loads((combined / 'report.json').read_text())
    report['sample_unique_ids'] = declared_unique
    report['output_sha256']['loan_sample.parquet'] = source.digest(path)
    dump(combined / 'report.json', report)


def test_declared_replacement_draw_preserves_identical_repeated_loan_rows(pair_inputs):
    replacement_draw(pair_inputs)
    result = module().run(**pair_inputs)
    assert result['sampling_multiplicity'] == {
        'sample_rows': 20, 'unique_loan_ids': 19, 'repeated_draw_rows': 1,
        'maximum_id_multiplicity': 2}
    assert result['quarter_cash_ratio_audits_by_quarter'] == {
        quarter: None for quarter in source.QUARTERS}
    for name in ('off', 'on'):
        accounting = pd.read_parquet(pair_inputs['output'] / f'{name}_accounting.parquet')
        assert accounting.opening_active_b.iloc[0] == pytest.approx(2707.446)


@pytest.mark.parametrize('conflict,declared_unique', [(True, 19), (False, 20)])
def test_repeated_ids_require_matching_records_and_declared_unique_count(pair_inputs, conflict, declared_unique):
    replacement_draw(pair_inputs, conflict=conflict, declared_unique=declared_unique)
    with pytest.raises(ValueError, match='sample|repeated|multiplicity'):
        module().run(**pair_inputs)
    assert not (pair_inputs['output'] / 'off_simulation.parquet').exists()

@pytest.mark.parametrize('changed_hash', [False, True])
def test_relative_recorded_macro_survives_worktree_relocation(pair_inputs, changed_hash):
    stage = module()
    freeze = json.loads(pair_inputs['parameter_freeze'].read_text())
    value = freeze['input_sha256'].pop(str(pair_inputs['macro_path']))
    freeze['input_sha256']['output/review-revision/2026-10-07-checks/macro_frozen.parquet'] = ('b' * 64 if changed_hash else value)
    dump(pair_inputs['parameter_freeze'], freeze)
    refresh_inventory(pair_inputs)
    args = {k: pair_inputs[k] for k in ('macro_path', 'parameter_freeze', 'empirical_csv', 'input_inventory', 'benchmark_reference')}
    if changed_hash:
        with pytest.raises(ValueError, match='macro'): stage.validate_recorded_inputs(**args)
    else:
        assert stage.validate_recorded_inputs(**args) == freeze
