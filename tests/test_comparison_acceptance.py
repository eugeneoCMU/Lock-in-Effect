"""Final gate rejects incomplete matrices and internally inconsistent receipts."""
from itertools import product
import hashlib
import json

import numpy as np
import pandas as pd
import pytest


def dump(path, value):
    path.write_text(json.dumps(value))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seal(directory, result):
    result['output_sha256'] = {p.name: digest(p) for p in directory.iterdir()
                               if p.is_file() and p.name != 'results.json'}
    dump(directory / 'results.json', result)


def reseal(directory):
    seal(directory, json.loads((directory / 'results.json').read_text()))


def account(level):
    dates = pd.date_range('2022-06-30', '2025-11-30', freq='ME')
    frame = pd.DataFrame(index=dates)
    frame['opening_active_b'] = frame['opening_total_b'] = 10.
    frame['closing_active_b'] = frame['closing_total_b'] = 10. - level - 1.
    frame['voluntary_b'] = level
    frame['scheduled_b'] = 1.
    for key in ('default_transfer_b', 'other_terminal_transfer_b', 'default_cash_b',
                'curtailment_b', 'additions_b', 'active_residual_b', 'total_residual_b'):
        frame[key] = 0.
    frame['cash_principal_b'] = level + 1.
    frame['reporting_scale'] = 1.
    frame['production_principal_b'] = level + 1.
    frame['production_voluntary_b'] = level
    frame['production_scheduled_b'] = 1.
    return frame


def make_outputs(root, label, parameters, family, off=1., on=.9):
    common = dict(pre_snapshot_coverage={'policy': 'known_pre_snapshot_history_v1',
                      'missing_loans': 4, 'unknown_original_upb': 1487000.},
                  source_semantics_version='test-corrected', population='known360FRM',
                  parameter_selection_performed=False, source_inputs_unchanged=True)
    pair_dir = root / (label + '-pair'); pair_dir.mkdir()
    manifest = {'parameters': parameters, 'input_sha256': {'corrected-input': 'a' * 64},
                'spec_sha256': 'b' * 64}
    dump(pair_dir / 'input_manifest.json', manifest)
    legs = {}
    for leg, level in [('off', off), ('on', on)]:
        frame = account(level)
        frame.to_parquet(pair_dir / (leg + '_accounting.parquet'))
        legs[leg] = dict(production_principal_b=float(frame.production_principal_b.sum()),
            closed_pool_cash_principal_b=float(frame.cash_principal_b.sum()),
            voluntary_b=float(frame.voluntary_b.sum()), scheduled_b=float(frame.scheduled_b.sum()),
            default_transfer_b=0., other_terminal_transfer_b=0., default_cash_b=0.,
            max_active_identity_error_b=0., max_total_identity_error_b=0.)
    seal(pair_dir, dict(common, parameters=parameters, legs=legs,
        reported_marginal_b=legs['off']['production_principal_b']-legs['on']['production_principal_b'],
        closed_pool_cash_marginal_b=legs['off']['closed_pool_cash_principal_b']-legs['on']['closed_pool_cash_principal_b']))
    score_dir = root / (label + '-scoring'); score_dir.mkdir()
    score_params = ({'mixture': dict(reference_mode=parameters['reference_mode'],
        sensitive_share=parameters['sensitive_share'], calibration=parameters['response_calibration'],
        gap_mode=parameters['gap_mode'])} if family == 'mixture' else {family: {'annual_floor': .04991, 'psa': 100.}})
    dump(score_dir / 'input_manifest.json', dict(manifest, parameters=score_params))
    pred = pd.DataFrame({'cell': ['cell'] * 21,
        'period': pd.date_range('2024-01-01', '2025-09-01', freq='MS'), 'coupon': [.03] * 21})
    for leg, level in [('off', off), ('on', on)]:
        pred[family + '_' + leg] = level / 100.
        pred[family + '_' + leg + '_predicted_burnout'] = .1
        pred[family + '_' + leg + '_floor_bound'] = False
    pred.to_parquet(score_dir / 'predictions.parquet', index=False)
    seal(score_dir, dict(common, parameters=score_params, support={'retained_rows': 21, 'retained_cells': 1},
        exclusions={'invalid': 0}, aggregate={family + '_off': {'predicted_b': off, 'observed_b': .5},
        family + '_on': {'predicted_b': on, 'observed_b': .5}}, input_manifest_sha256=digest(score_dir / 'input_manifest.json')))


@pytest.fixture
def matrix(tmp_path):
    make_outputs(tmp_path, 'benchmark', {'floor_form': 'max'}, 'original')
    make_outputs(tmp_path, 'additive-benchmark', {'floor_form': 'additive'}, 'additive', off=1.1)
    scenarios = []
    for ref, cal, gap, share in product(('inherited_psa', 'matched_max_off'),
            ('legacy_conversion', 'illustrative'), ('positive_only', 'preserve_refinancing'),
            (0., .25, .5, .75, 1.)):
        label = f'{ref}-{cal}-{gap}-{share}'
        scenarios.append(dict(scenario=label, reference_mode=ref, calibration=cal,
                              gap_mode=gap, sensitive_share=share))
        p = dict(reference_mode=ref, response_calibration=cal, gap_mode=gap, sensitive_share=share)
        off = 1. if ref == 'matched_max_off' else .8
        on = off if share == 0 and gap == 'positive_only' else off - .1
        make_outputs(tmp_path, label, p, 'mixture', off=off, on=on)
    return tmp_path, scenarios


def validate(root, scenarios):
    from hazard.comparison_acceptance import validate_analysis
    return validate_analysis(root, scenarios)


def test_complete_consistent_matrix_passes_and_receipt_serializes(matrix):
    receipt = validate(*matrix)
    assert receipt['status'] == 'passed'
    assert receipt['scenario_count'] == 40
    json.dumps(receipt, allow_nan=False)


@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'wrong_identity'])
def test_exact_matrix_required(matrix, mutation):
    root, scenarios = matrix
    if mutation == 'missing': scenarios.pop()
    elif mutation == 'duplicate': scenarios[-1] = scenarios[0]
    else: scenarios[0]['sensitive_share'] = .1
    with pytest.raises(ValueError): validate(root, scenarios)


def test_missing_hashed_artifact_fails_closed(matrix):
    root, scenarios = matrix
    (root / 'benchmark-pair' / 'off_accounting.parquet').unlink()
    with pytest.raises(ValueError): validate(root, scenarios)


def test_hash_corruption_rejected(matrix):
    root, scenarios = matrix
    (root / 'benchmark-scoring' / 'predictions.parquet').write_bytes(b'changed')
    with pytest.raises(ValueError, match='hash'): validate(root, scenarios)


@pytest.mark.parametrize('field', ['pre_snapshot_coverage', 'support', 'parameters'])
def test_inconsistent_scoring_evidence_rejected(matrix, field):
    root, scenarios = matrix
    directory = root / (scenarios[-1]['scenario'] + '-scoring')
    result = json.loads((directory / 'results.json').read_text())
    if field == 'pre_snapshot_coverage': result[field]['unknown_original_upb'] += 1
    elif field == 'support': result[field]['retained_rows'] -= 1
    else: result[field]['mixture']['sensitive_share'] = 0.
    seal(directory, result)
    with pytest.raises(ValueError): validate(root, scenarios)


@pytest.mark.parametrize('change', ['off_path', 'residual', 'nan', 'null_pair', 'null_prediction'])
def test_numeric_acceptance_checks_survive_resealed_receipts(matrix, change):
    root, scenarios = matrix
    scenario = scenarios[0] if change.startswith('null') else scenarios[-1]
    suffix = '-scoring' if change == 'null_prediction' else '-pair'
    directory = root / (scenario['scenario'] + suffix)
    name = 'predictions.parquet' if change == 'null_prediction' else ('on_accounting.parquet' if change == 'null_pair' else 'off_accounting.parquet')
    path = directory / name
    frame = pd.read_parquet(path)
    if change == 'null_prediction': frame['mixture_on'] += .01
    elif change == 'null_pair': frame['reporting_scale'] += .01
    elif change == 'off_path': frame['reporting_scale'] += .01
    elif change == 'residual': frame['active_residual_b'] = .001
    else: frame['voluntary_b'] = np.nan
    frame.to_parquet(path, index=change != 'null_prediction')
    reseal(directory)
    with pytest.raises(ValueError): validate(root, scenarios)


def test_matched_reference_must_match_hardmax_off(matrix):
    root, scenarios = matrix
    # Keep all matched-reference OFF paths mutually equal, but make them differ
    # from the independently saved hard-max benchmark.
    directory = root / 'benchmark-pair'
    path = directory / 'off_accounting.parquet'
    frame = pd.read_parquet(path); frame['reporting_scale'] += .01
    frame.to_parquet(path); reseal(directory)
    with pytest.raises(ValueError): validate(root, scenarios)


def test_failure_marker_prevents_acceptance(matrix):
    root, scenarios = matrix
    dump(root / 'benchmark-pair' / 'failed.json', {'error': 'incomplete'})
    reseal(root / 'benchmark-pair')
    with pytest.raises(ValueError): validate(root, scenarios)


def test_saved_input_identity_cannot_change_across_scenarios(matrix):
    root, scenarios = matrix
    directory = root / (scenarios[-1]['scenario'] + '-pair')
    path = directory / 'input_manifest.json'
    manifest = json.loads(path.read_text())
    manifest['input_sha256']['corrected-input'] = 'c' * 64
    dump(path, manifest); reseal(directory)
    with pytest.raises(ValueError, match='input identit'): validate(root, scenarios)


def test_observed_principal_must_match_across_scores(matrix):
    root,scenarios=matrix
    directory=root/(scenarios[-1]['scenario']+'-scoring')
    result=json.loads((directory/'results.json').read_text())
    result['aggregate']['mixture_on']['observed_b'] += 1.
    seal(directory,result)
    with pytest.raises(ValueError,match='observed principal'): validate(root,scenarios)
