"""Fail-closed, local-artifact acceptance gate for the prespecified comparison.

This gate verifies saved artifacts and structural identities, not empirical
identification. It never opens paths from input manifests or original sources.
Shares and response conversions remain assumptions; matching OFF paths does
not establish the reference as an estimated neutral-rate counterfactual.
"""
from datetime import datetime, timezone
import hashlib
from itertools import product
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

REFERENCES = ('inherited_psa', 'matched_max_off')
CALIBRATIONS = ('legacy_conversion', 'illustrative')
GAPS = ('positive_only', 'preserve_refinancing')
SHARES = (0., .25, .5, .75, 1.)
ATOL_B = 1e-8
RTOL = 1e-12
PREDICTION_ATOL = 1e-12
ACCOUNT_COLUMNS = {
    'opening_active_b', 'closing_active_b', 'opening_total_b', 'closing_total_b',
    'voluntary_b', 'scheduled_b', 'default_transfer_b', 'other_terminal_transfer_b',
    'cash_principal_b', 'default_cash_b', 'curtailment_b', 'additions_b',
    'active_residual_b', 'total_residual_b', 'reporting_scale',
    'production_principal_b', 'production_voluntary_b', 'production_scheduled_b',
}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _finite_json(value):
    if isinstance(value, dict):
        return all(_finite_json(v) for v in value.values())
    if isinstance(value, list):
        return all(_finite_json(v) for v in value)
    return not isinstance(value, (int, float)) or math.isfinite(value)


def _read_json(path):
    _require(path.is_file() and not path.is_symlink(), f'Missing local evidence: {path}')
    try:
        value = json.loads(path.read_text())
    except (ValueError, OSError) as exc:
        raise ValueError(f'Invalid JSON evidence: {path}') from exc
    _require(isinstance(value, dict) and _finite_json(value), f'Nonfinite or invalid receipt: {path}')
    return value


def _receipt(directory, required, evidence):
    _require(directory.is_dir() and not directory.is_symlink(), f'Missing output directory: {directory}')
    _require(not (directory / 'failed.json').exists(), f'Failed output cannot pass: {directory}')
    result = _read_json(directory / 'results.json')
    hashes = result.get('output_sha256')
    _require(isinstance(hashes, dict) and required.issubset(hashes), f'Missing output hash evidence: {directory}')
    actual = {p.name for p in directory.iterdir() if p.is_file() and p.name != 'results.json'}
    _require(set(hashes) == actual, f'Incomplete output hash coverage: {directory}')
    for name, expected in hashes.items():
        _require(isinstance(name, str) and Path(name).name == name and name not in ('.', '..'),
                 f'Unsafe output hash path: {directory}')
        path = directory / name
        _require(path.is_file() and not path.is_symlink(), f'Missing local hashed output: {path}')
        _require(isinstance(expected, str) and _digest(path) == expected, f'Output hash mismatch: {path}')
    manifest = _read_json(directory / 'input_manifest.json')
    _require(manifest.get('parameters') == result.get('parameters') and 'parameters' in manifest,
             f'Result/manifest parameters differ: {directory}')
    _require(isinstance(manifest.get('input_sha256'), dict) and manifest['input_sha256'],
             f'Missing input identity evidence: {directory}')
    if 'input_manifest_sha256' in result:
        _require(result['input_manifest_sha256'] == hashes['input_manifest.json'],
                 f'Input manifest binding differs: {directory}')
    _require(result.get('source_inputs_unchanged') is True
             and result.get('parameter_selection_performed') is False,
             f'Missing fixed-input/no-selection evidence: {directory}')
    _require('pre_snapshot_coverage' in result and isinstance(result['pre_snapshot_coverage'], dict),
             f'Missing coverage evidence: {directory}')
    _require(all(k in result for k in ('population', 'source_semantics_version')),
             f'Missing population identity: {directory}')
    evidence[directory.name] = {'results_sha256': _digest(directory / 'results.json'),
                               'input_manifest_sha256': hashes['input_manifest.json']}
    return result, manifest


def _close(left, right, message, *, atol=ATOL_B):
    try:
        a, b = np.asarray(left, dtype=float), np.asarray(right, dtype=float)
    except (ValueError, TypeError) as exc:
        raise ValueError(message) from exc
    _require(a.shape == b.shape and np.isfinite(a).all() and np.isfinite(b).all()
             and np.allclose(a, b, rtol=RTOL, atol=atol), message)


def _account(directory, result, leg):
    path = directory / (leg + '_accounting.parquet')
    try:
        frame = pd.read_parquet(path)
    except Exception as exc:
        raise ValueError(f'Unreadable accounting evidence: {path}') from exc
    expected_dates = pd.date_range('2022-06-30', '2025-11-30', freq='ME')
    _require(frame.index.equals(expected_dates) and ACCOUNT_COLUMNS.issubset(frame.columns)
             and frame.columns.is_unique, f'Incomplete QT accounting calendar/columns: {path}')
    _require(all(pd.api.types.is_numeric_dtype(t) for t in frame.dtypes)
             and np.isfinite(frame.to_numpy(dtype=float)).all(), f'Nonfinite accounting: {path}')
    for residual in ('active_residual_b', 'total_residual_b'):
        _require(float(frame[residual].abs().max()) <= ATOL_B, f'Accounting residual exceeds tolerance: {path}')
    _close(frame.opening_active_b - frame.closing_active_b - frame.voluntary_b - frame.scheduled_b
           - frame.default_transfer_b - frame.other_terminal_transfer_b,
           frame.active_residual_b, f'Active principal identity differs: {path}')
    _close(frame.opening_total_b - frame.closing_total_b - frame.voluntary_b - frame.scheduled_b,
           frame.total_residual_b, f'Total principal identity differs: {path}')
    _close(frame.cash_principal_b, frame.voluntary_b + frame.scheduled_b, f'Cash principal identity differs: {path}')
    for output, source in [('production_principal_b', 'cash_principal_b'),
                           ('production_voluntary_b', 'voluntary_b'),
                           ('production_scheduled_b', 'scheduled_b')]:
        _close(frame[output], frame[source] * frame.reporting_scale, f'Reporting scale identity differs: {path}')
    summary = result.get('legs', {}).get(leg, {})
    for key, column in [('production_principal_b', 'production_principal_b'),
                        ('closed_pool_cash_principal_b', 'cash_principal_b'),
                        ('voluntary_b', 'voluntary_b'), ('scheduled_b', 'scheduled_b'),
                        ('default_transfer_b', 'default_transfer_b'),
                        ('other_terminal_transfer_b', 'other_terminal_transfer_b'),
                        ('default_cash_b', 'default_cash_b')]:
        _require(key in summary, f'Missing accounting summary: {path}/{key}')
        _close(summary[key], float(frame[column].sum()), f'Accounting summary differs: {path}/{key}')
    for key, column in [('max_active_identity_error_b', 'active_residual_b'),
                        ('max_total_identity_error_b', 'total_residual_b')]:
        _require(key in summary, f'Missing residual summary: {path}/{key}')
        _close(summary[key], float(frame[column].abs().max()), f'Residual summary differs: {path}/{key}')
        _require(0 <= summary[key] <= ATOL_B, f'Invalid residual summary: {path}/{key}')
    return frame


def _pair(directory, evidence):
    result, manifest = _receipt(directory,
        {'input_manifest.json', 'off_accounting.parquet', 'on_accounting.parquet'}, evidence)
    off, on = (_account(directory, result, leg) for leg in ('off', 'on'))
    for key, column in [('reported_marginal_b', 'production_principal_b'),
                        ('closed_pool_cash_marginal_b', 'cash_principal_b')]:
        _require(key in result, f'Missing paired marginal: {directory}/{key}')
        _close(result[key], float(off[column].sum() - on[column].sum()),
               f'Paired marginal differs: {directory}/{key}')
    return result, manifest, off, on


def _scoring(directory, evidence, family):
    result, manifest = _receipt(directory, {'input_manifest.json', 'predictions.parquet'}, evidence)
    _require(all(isinstance(result.get(k), dict) and result[k] for k in ('support', 'aggregate'))
             and isinstance(result.get('exclusions'), dict), f'Missing scoring support evidence: {directory}')
    try:
        frame = pd.read_parquet(directory / 'predictions.parquet')
    except Exception as exc:
        raise ValueError(f'Unreadable prediction evidence: {directory}') from exc
    required = {'cell', 'period', 'coupon'} | {family + '_' + leg + suffix
        for leg in ('off', 'on') for suffix in ('', '_predicted_burnout')}
    _require(required.issubset(frame.columns) and frame.columns.is_unique and not frame.empty
             and not frame[['cell', 'period', 'coupon']].isna().any().any()
             and not frame.duplicated(['cell', 'period']).any(), f'Invalid prediction keys/columns: {directory}')
    _require(pd.api.types.is_datetime64_any_dtype(frame.period), f'Invalid prediction dates: {directory}')
    months = pd.date_range('2024-01-01', '2025-09-01', freq='MS')
    _require(set(frame.period) == set(months)
             and len(frame) == frame.cell.nunique() * len(months), f'Incomplete prediction calendar: {directory}')
    numeric = frame.select_dtypes(include=['number', 'bool'])
    _require(np.isfinite(numeric.to_numpy(dtype=float)).all(), f'Nonfinite prediction: {directory}')
    for leg in ('off', 'on'):
        name = family + '_' + leg
        _require(pd.api.types.is_numeric_dtype(frame[name]) and frame[name].between(0, 1).all()
                 and pd.api.types.is_numeric_dtype(frame[name + '_predicted_burnout'])
                 and frame[name + '_predicted_burnout'].between(0, 1).all(),
                 f'Prediction outside support: {directory}/{name}')
        _require(name in result['aggregate'], f'Missing aggregate candidate: {directory}/{name}')
    return result, manifest, frame.sort_values(['cell', 'period']).reset_index(drop=True)


def _same_account(left, right, label):
    _require(left.index.equals(right.index) and set(left.columns) == set(right.columns),
             f'Accounting path support differs: {label}')
    _close(left.to_numpy(dtype=float), right[left.columns].to_numpy(dtype=float),
           f'Accounting paths differ: {label}')


def _same_prediction(left, left_name, right, right_name, label):
    _require(left[['cell', 'period']].equals(right[['cell', 'period']]), f'Prediction support differs: {label}')
    _close(left.coupon, right.coupon, f'Prediction coupons differ: {label}', atol=PREDICTION_ATOL)
    for suffix in ('', '_predicted_burnout'):
        _close(left[left_name + suffix], right[right_name + suffix],
               f'Prediction paths differ: {label}/{suffix}', atol=PREDICTION_ATOL)


def _identity(scenario):
    try:
        label = scenario['scenario']
        identity = (scenario['reference_mode'], scenario['calibration'], scenario['gap_mode'],
                    scenario['sensitive_share'])
    except (KeyError, TypeError) as exc:
        raise ValueError('Missing scenario identity') from exc
    _require(isinstance(label, str) and label not in ('', '.', '..') and Path(label).name == label,
             'Invalid scenario label')
    _require(not isinstance(identity[-1], bool), 'Invalid sensitive share')
    return label, identity


def validate_analysis(output, scenarios):
    """Return a serializable acceptance receipt, or raise ValueError on any failure.

    Exactly 40 identities and all four saved benchmark directories are required.
    Numeric tolerances concern floating-point equality, not sampling uncertainty.
    All reading is restricted to artifacts under ``output``; input hash maps are
    compared as saved evidence without reopening the referenced inputs.
    """
    output = Path(output)
    _require(not (output / 'failed.json').exists(), 'Analysis has a failure marker')
    scenarios = list(scenarios)
    entries = [_identity(s) for s in scenarios]
    identities = [identity for _, identity in entries]
    expected = set(product(REFERENCES, CALIBRATIONS, GAPS, SHARES))
    try:
        complete = len(entries) == 40 and len(set(identities)) == 40 and set(identities) == expected
    except TypeError as exc:
        raise ValueError('Invalid scenario identity') from exc
    _require(complete and len({label for label, _ in entries}) == 40, 'Incomplete or duplicate 40-scenario matrix')
    required_dirs = {'benchmark-pair', 'benchmark-scoring', 'additive-benchmark-pair', 'additive-benchmark-scoring'}
    required_dirs |= {label + suffix for label, _ in entries for suffix in ('-pair', '-scoring')}
    actual_dirs = {p.name for p in output.iterdir() if p.is_dir() and p.name.endswith(('-pair', '-scoring'))}
    _require(actual_dirs == required_dirs, 'Missing or unexpected comparison output directories')
    evidence = {}
    benchmark = _pair(output / 'benchmark-pair', evidence)
    benchmark_score = _scoring(output / 'benchmark-scoring', evidence, 'original')
    additive = _pair(output / 'additive-benchmark-pair', evidence)
    additive_score = _scoring(output / 'additive-benchmark-scoring', evidence, 'additive')
    _require(benchmark[0]['parameters'].get('floor_form') == 'max'
             and additive[0]['parameters'].get('floor_form') == 'additive', 'Benchmark floor conventions differ')
    baseline = benchmark[0]
    scoring_baseline = benchmark_score[0]

    def common(result, score=False):
        for key in ('pre_snapshot_coverage', 'population', 'source_semantics_version'):
            _require(result[key] == baseline[key], f'Inconsistent comparison {key}')
        if score:
            for key in ('support', 'exclusions'):
                _require(result[key] == scoring_baseline[key], f'Inconsistent scoring {key}')
            observed = scoring_baseline['aggregate']['original_off'].get('observed_b')
            _require(observed is not None, 'Missing observed principal evidence')
            for name, metrics in result['aggregate'].items():
                _require('observed_b' in metrics, f'Missing observed principal: {name}')
                _close(metrics['observed_b'], observed, f'Inconsistent observed principal: {name}', atol=1e-12)

    for result, score in [(baseline, False), (benchmark_score[0], True),
                          (additive[0], False), (additive_score[0], True)]:
        common(result, score)
    pair_inputs = {k:v for k,v in benchmark[1]['input_sha256'].items() if 'specs' not in Path(k).parts}
    score_inputs = {k:v for k,v in benchmark_score[1]['input_sha256'].items() if 'specs' not in Path(k).parts}
    def same_inputs(manifest, expected):
        actual = {k:v for k,v in manifest['input_sha256'].items() if 'specs' not in Path(k).parts}
        _require(actual == expected, 'Comparison input identities differ')
    same_inputs(additive[1], pair_inputs)
    same_inputs(additive_score[1], score_inputs)
    off_accounts, off_predictions = {}, {}
    for label, (reference, calibration, gap, share) in entries:
        pair_result, pair_manifest, off, on = _pair(output / (label + '-pair'), evidence)
        score_result, score_manifest, prediction = _scoring(output / (label + '-scoring'), evidence, 'mixture')
        common(pair_result); common(score_result, True)
        same_inputs(pair_manifest, pair_inputs); same_inputs(score_manifest, score_inputs)
        p = pair_result['parameters']; s = score_result['parameters'].get('mixture', {})
        _require((p.get('reference_mode'), p.get('response_calibration'), p.get('gap_mode'), p.get('sensitive_share'))
                 == (reference, calibration, gap, share), f'Paired scenario identity differs: {label}')
        _require((s.get('reference_mode'), s.get('calibration'), s.get('gap_mode'), s.get('sensitive_share'))
                 == (reference, calibration, gap, share), f'Scoring scenario identity differs: {label}')
        # OFF is a reference-level path: neither the share nor ON-only channels
        # may alter it. Keep only one prediction frame per reference in memory.
        if reference in off_accounts:
            _same_account(off, off_accounts[reference], label + '/OFF')
            _same_prediction(prediction, 'mixture_off', off_predictions[reference], 'mixture_off', label + '/OFF')
        else:
            off_accounts[reference] = off
            off_predictions[reference] = prediction[['cell', 'period', 'coupon', 'mixture_off',
                                                     'mixture_off_predicted_burnout']].copy()
        if reference == 'matched_max_off':
            _same_account(off, benchmark[2], label + '/matched-hardmax-OFF')
            _same_prediction(prediction, 'mixture_off', benchmark_score[2], 'original_off', label + '/matched-hardmax-OFF')
        if share == 0 and gap == 'positive_only':
            _same_account(on, off, label + '/zero-share-ON-OFF')
            _same_prediction(prediction, 'mixture_on', prediction, 'mixture_off', label + '/zero-share-ON-OFF')
    return dict(status='passed', gate_version='comparison_acceptance_v1',
        created_utc=datetime.now(timezone.utc).isoformat(), scenario_count=40,
        benchmark_output_count=4, validated_output_count=len(evidence),
        tolerances=dict(accounting_absolute_b=ATOL_B, relative=RTOL,
                        prediction_absolute=PREDICTION_ATOL), validated_receipts=evidence,
        checks=['exact scenario matrix', 'complete output hashes', 'accounting identities and marginals',
                'common coverage and population', 'common scoring support', 'common input identities',
                'OFF paths invariant within reference', 'matched OFF equals hard-max OFF',
                'zero-share positive-only ON equals OFF'],
        assumptions=['Sensitive shares are assumed, not an identified move/refinance decomposition.',
                     'Response conversions and reference schedules are structural assumptions.',
                     'Retrospective scoring uses previously examined outcomes and realized conditioning inputs.',
                     'Coverage cash-ratio intervals retain their source-audit assumptions.',
                     'Passing verifies saved artifacts and structural identities, not causal or population identification.'])
