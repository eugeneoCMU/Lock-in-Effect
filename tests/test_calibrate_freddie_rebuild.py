"""The floor rerun must fail closed before touching corrected results."""
from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'hazard'))
import run_freddie_rebuild as source


def module():
    try:
        return importlib.import_module('hazard.calibrate_freddie_rebuild')
    except ModuleNotFoundError as exc:
        pytest.fail(f'The gated offline Freddie calibration wrapper is missing: {exc}')


def dump(path, value):
    source.write_json(path, value)


def synthetic_quarter(root, quarter):
    """Real completion validator, with only local synthetic compact evidence."""
    path = root / 'quarters' / quarter
    path.mkdir(parents=True)
    (path / 'spec_frozen.md').write_bytes((root / 'spec_frozen.md').read_bytes())
    (path / 'executed_code').mkdir()
    for name in source.CORE_CODE_FILES:
        (path / 'executed_code' / name).write_text('synthetic executed code')
    dump(path / 'execution_freeze.json', {
        'quarter': quarter, 'cutoff': '202509', 'transition_end': '202205',
        'spec_sha256': source.digest(root / 'spec_frozen.md'),
        'code_sha256': {n: source.digest(path / 'executed_code' / n) for n in source.CORE_CODE_FILES}})
    hashes = {'origination': 'a' * 64, 'performance': 'b' * 64}
    zero = {'enabled': False, 'known360_count': 0, 'known360_upb': 0.}
    dump(path / 'schema.json', {'passed': True, 'source_semantics_version':'freddie-native32-ddlpi-states-v1',
        'origination': {'sha256': hashes['origination'], 'rows': 1,
                        'eligible_360_month_ids': 1, 'zero_note_rate_exclusions': zero},
        'performance': {'sha256': hashes['performance'], 'rows': 2}})
    dump(path / 'source_hashes_after.json', hashes)
    files = [dict(exists=True, path=str(root / f'{kind}_{quarter}.txt'), size=1,
                  mtime_ns=1, allocated_bytes=0, isDownloaded=0, isTrashed=0, isUploaded=1)
             for kind in ('orig', 'perf')]
    dump(path / 'cleanup.json', {'files': files})
    dump(path / 'source_metadata_at_worker_start.json', files)
    dump(path / 'resources.json', {'worker_reaped': True, 'peak_rss_bytes': 100,
                                   'free_disk_bytes_after': 20 * source.GIB})
    (path / 'rebuilt').mkdir()
    for name in source.REBUILT_ARTIFACTS:
        (path / 'rebuilt' / name).write_bytes(b'synthetic compact source evidence')
    report = dict(quarter=quarter, cutoff='202509', snapshot_month='202205', transition_end='202205',
        source_semantics_version='freddie-native32-ddlpi-states-v1',
        source_sha256=hashes, counts={'origination_rows': 1, 'performance_rows': 2, 'eligible_original_ids': 1,
                                    'semantic_rows_validated':2,'eligible_pre_cutoff_rows':2},
        cutoff_proof={'post_cutoff_outcomes_decoded': 0, 'outcome_filter_precedes_decode': True,
                      'latest_decoded_month': '202205'}, zero_note_rate_exclusions=zero,
        payoff_assumptions={'first_observed': 'original UPB fallback', 'calendar_gap': 'last observed valid UPB'},
        artifacts={n: {'sha256': source.digest(path / 'rebuilt' / n), 'rows': 1}
                   for n in source.REBUILT_ARTIFACTS})
    dump(path / 'rebuilt/report.json', report)
    dump(path / 'worker_passed.json', {'source_hashes': hashes, 'report': report})
    if quarter == '2017Q1':
        dump(path / 'production_comparison.json', {'passed': True, 'rows': 1,
            'checks': {n: {'passed': True} for n in source.COMPARISON_COLUMNS}})
        (path / 'production_cells_360.parquet').write_bytes(b'synthetic independent panel')
    source.seal_completion(path)
    return report


@pytest.fixture
def inputs(tmp_path):
    root = tmp_path / 'source-rebuild'
    root.mkdir()
    (root / 'spec_frozen.md').write_bytes(source.SPEC.read_bytes())
    reports = {q: synthetic_quarter(root, q) for q in source.QUARTERS}
    combined = root / 'combined'
    combined.mkdir()
    panel = pd.DataFrame({'vintage': [2017, 2021, 2021], 'coupon': [.03] * 3,
        'fico_bucket': ['700-739'] * 3, 'ltv_bucket': ['70-80'] * 3,
        'reporting_period': ['201801', '202301', '202302'],
        'mean_loan_age': [24., 24., 12.], 'exposure_upb': [1000., 2000., 1000.],
        'prepaid_upb': [10., 20., 10.]})
    legacy = tmp_path / 'exact-legacy-panel.parquet'
    panel.to_parquet(legacy)
    panel['prepaid_upb'] *= 2
    panel.to_parquet(combined / 'cohort_month_panel.parquet')
    for name in ('loan_sample.parquet', 'markov_transition_matrix.parquet'):
        (combined / name).write_bytes(b'synthetic unused input')
    dump(combined / 'transition_diagnostics.json', {'estimation_end': '202205'})
    report = dict(quarters=source.QUARTERS, complete_freddie_manifest=True,
        source_semantics_version='freddie-native32-ddlpi-states-v1',
        population='known360FRM; original vintage2017–2021', cutoff='202509', transition_end='202205',
        sample_month='202205', panel_rows=3, original_loans=20, sample_n=20, sample_unique_ids=20,
        observed_source_survivors=20, zero_note_rate_excluded_loans=0,
        zero_note_rate_excluded_original_upb=0.,
        quarter_cash_ratio_audits_by_quarter={q:None for q in source.QUARTERS},
        partial_cohort_overrun_count=0,complete_cohort_burnout_bounds_verified=True,
        zero_note_rate_exclusions_by_quarter={q: r['zero_note_rate_exclusions'] for q, r in reports.items()},
        original_payoff_assumptions=[dict(quarter=q, **r['payoff_assumptions']) for q, r in reports.items()],
        source_report_sha256={q: source.digest(root / 'quarters' / q / 'rebuilt/report.json') for q in source.QUARTERS},
        output_sha256={p.name: source.digest(p) for p in combined.iterdir()})
    dump(combined / 'report.json', report)
    rates = tmp_path / 'frozen_rates.csv'
    dates = [f'{year}-{month:02}-01' for year in [2017, 2018, 2019, 2023, 2024] for month in range(1, 13)]
    # The two January observations average to 6%, checking the saved mean convention.
    rows = pd.DataFrame({'observation_date': dates, 'MORTGAGE30US': [6.] * len(dates)})
    rows.loc[rows.observation_date == '2018-01-01', 'MORTGAGE30US'] = 5.
    rows.loc[len(rows)] = ['2018-01-08', 7.]
    rows.to_csv(rates, index=False)
    rate_meta = tmp_path / 'rate_source.json'
    dump(rate_meta, {'url': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US&cosd=2016-12-01&coed=2025-10-31',
                     'sha256': source.digest(rates), 'retrieved_utc': '2026-10-09T00:00:00+00:00'})
    # Hand-derived legacy SMM is 1% in every selected cell: CPR rounds to 11.362%.
    saved = {'grids': {}}
    for window, exposure12, exposure24, count12 in [
            ('out_of_window_2017_2019', 1000., 1000., 1),
            ('in_window_2023_2024', 3000., 2000., 2)]:
        saved['grids'][window] = {
            f'gap<={gap}_age>={age}': dict(cpr_pct=11.362, exposure_upb=exp, n_cohort_months=count)
            for gap in ('+0.0000', '-0.0025', '-0.0050')
            for age, exp, count in [(12, exposure12, count12), (24, exposure24, 1)]}
    saved['in_window_deep_OTM_validation'] = {
        f'gap<=-0.02_age>={age}': dict(cpr_pct=11.362, exposure_upb=exp, n_cohort_months=count)
        for age, exp, count in [(12, 3000., 2), (24, 2000., 1)]}
    saved_path = tmp_path / 'saved_grid.json'
    dump(saved_path, saved)
    return dict(root=root, legacy_panel=legacy, saved_grid=saved_path, rate_csv=rates,
                rate_source=rate_meta, output=tmp_path / 'new-calibration')


def test_full_offline_replay_freezes_inputs_before_corrected_grid(inputs, monkeypatch):
    stage = module()
    original_prep = stage.prep
    def checked_prep(path, monthly):
        manifest = json.loads((inputs['output'] / 'input_manifest.json').read_text())
        assert manifest['input_sha256'][str(inputs['legacy_panel'])] == source.digest(inputs['legacy_panel'])
        assert monthly['201801'] == pytest.approx(.06)
        if Path(path) != inputs['legacy_panel']:
            assert json.loads((inputs['output'] / 'legacy_replay.json').read_text())['parity']['passed'] is True
        return original_prep(path, monthly)
    monkeypatch.setattr(stage, 'prep', checked_prep)
    before = {p: source.digest(p) for p in inputs['root'].rglob('*') if p.is_file()}
    result = stage.run(**inputs)
    assert result['legacy_replay']['parity']['cells'] == 14
    cell = result['corrected_grid']['in_window_2023_2024']['gap<=-0.0025_age>=12']
    assert cell == dict(cpr_pct=21.528, exposure_upb=3000., n_cohort_months=2)
    assert result['parameter_selection_performed'] is False
    assert result['source_inputs_unchanged'] is True
    assert result['population_comparison']['corrected'] == 'known360FRM; original vintage2017–2021'
    assert before == {p: source.digest(p) for p in before}
    assert json.loads((inputs['output'] / 'results.json').read_text()) == result
    assert not (inputs['output'] / 'failed.json').exists()


def test_an_incomplete_quarter_stops_before_a_manifest_or_new_values(inputs):
    (inputs['root'] / 'quarters/2021Q4/completed.json').unlink()
    with pytest.raises(FileNotFoundError, match='2021Q4'):
        module().run(**inputs)
    assert not inputs['output'].exists()


@pytest.mark.parametrize('mutation', ['partial_combined', 'wrong_cutoff', 'changed_output',
                                     'missing_output_hash', 'wrong_source_hash', 'wrong_exclusions', 'old_semantics'])
def test_combined_evidence_must_bind_all_quarters_and_every_output(inputs, mutation):
    path = inputs['root'] / 'combined/report.json'
    report = json.loads(path.read_text())
    if mutation == 'partial_combined': report['complete_freddie_manifest'] = False
    elif mutation == 'wrong_cutoff': report['cutoff'] = '202601'
    elif mutation == 'changed_output': (path.parent / 'loan_sample.parquet').write_bytes(b'changed')
    elif mutation == 'missing_output_hash': del report['output_sha256']['loan_sample.parquet']
    elif mutation == 'wrong_source_hash': report['source_report_sha256']['2017Q1'] = 'c' * 64
    elif mutation == 'old_semantics': report.pop('source_semantics_version')
    else: report['zero_note_rate_excluded_loans'] = 1
    dump(path, report)
    with pytest.raises(ValueError): module().run(**inputs)
    assert not inputs['output'].exists()


@pytest.mark.parametrize('mutation', ['hash', 'source', 'missing_month', 'duplicate_date'])
def test_rate_provenance_and_saved_monthly_support_are_required(inputs, mutation):
    path = inputs['rate_source']
    meta = json.loads(path.read_text())
    if mutation == 'hash': meta['sha256'] = 'c' * 64
    elif mutation == 'source': meta['url'] = 'https://example.com/rates'
    else:
        data = pd.read_csv(inputs['rate_csv'])
        if mutation == 'missing_month': data = data[data.observation_date != '2024-12-01']
        else: data = pd.concat([data, data.iloc[:1]])
        data.to_csv(inputs['rate_csv'], index=False)
        meta['sha256'] = source.digest(inputs['rate_csv'])
    dump(path, meta)
    with pytest.raises(ValueError): module().run(**inputs)
    assert not inputs['output'].exists()


def test_saved_grid_mismatch_preserves_failed_attempt_and_never_reads_corrected_panel(inputs, monkeypatch):
    stage = module()
    saved = json.loads(inputs['saved_grid'].read_text())
    saved['grids']['out_of_window_2017_2019']['gap<=+0.0000_age>=12']['n_cohort_months'] = 2
    dump(inputs['saved_grid'], saved)
    original_prep = stage.prep
    def legacy_only(path, rates):
        assert Path(path) == inputs['legacy_panel'], 'Corrected values accessed before legacy parity passed'
        return original_prep(path, rates)
    monkeypatch.setattr(stage, 'prep', legacy_only)
    with pytest.raises(ValueError, match='replay'): stage.run(**inputs)
    assert (inputs['output'] / 'input_manifest.json').exists()
    assert (inputs['output'] / 'failed.json').exists()
    assert not (inputs['output'] / 'results.json').exists()


def test_existing_output_is_never_reused_even_if_empty(inputs):
    inputs['output'].mkdir()
    with pytest.raises(FileExistsError): module().run(**inputs)
    assert list(inputs['output'].iterdir()) == []


@pytest.mark.parametrize('field,value', [
    ('cpr_pct', float('nan')), ('cpr_pct', float('inf')), ('cpr_pct', None),
    ('cpr_pct', '11.362'), ('cpr_pct', True), ('cpr_pct', -1.),
    ('exposure_upb', float('nan')), ('exposure_upb', -1.),
    ('n_cohort_months', 1.5), ('n_cohort_months', True),
    ('n_cohort_months', 0)])
def test_malformed_saved_grid_stops_before_any_panel_outcomes(inputs, monkeypatch, field, value):
    stage = module()
    saved = json.loads(inputs['saved_grid'].read_text())
    saved['grids']['out_of_window_2017_2019']['gap<=+0.0000_age>=12'][field] = value
    # Deliberately accept invalid JSON numeric extensions to test the reader.
    inputs['saved_grid'].write_text(json.dumps(saved))
    def forbidden(*args, **kwargs):
        pytest.fail('Panel outcomes were read before saved numeric values were validated')
    monkeypatch.setattr(stage, 'prep', forbidden)
    with pytest.raises(ValueError, match='Saved floor-grid numeric'):
        stage.run(**inputs)
    assert not inputs['output'].exists()


def test_saved_grid_allows_null_cpr_only_for_empty_cells(inputs):
    stage = module()
    saved = json.loads(inputs['saved_grid'].read_text())
    cell = saved['grids']['out_of_window_2017_2019']['gap<=+0.0000_age>=12']
    cell.update(cpr_pct=None, exposure_upb=0., n_cohort_months=0)
    dump(inputs['saved_grid'], saved)
    grid, _ = stage.saved_freddie_grid(inputs['saved_grid'])
    assert grid['out_of_window_2017_2019']['gap<=+0.0000_age>=12'] == cell


def test_input_mutation_during_calculation_cannot_produce_a_success_result(inputs, monkeypatch):
    stage = module()
    original_grids = stage.grids
    calls = 0
    def mutate_after_corrected(frame):
        nonlocal calls
        result = original_grids(frame)
        calls += 1
        if calls == 2:
            inputs['rate_csv'].write_text(inputs['rate_csv'].read_text() + '\n')
        return result
    monkeypatch.setattr(stage, 'grids', mutate_after_corrected)
    with pytest.raises(ValueError, match='changed'): stage.run(**inputs)
    assert (inputs['output'] / 'failed.json').exists()
    assert not (inputs['output'] / 'results.json').exists()
