"""Exact hashed source identity exceptions never relax the default prefix gate."""
from copy import deepcopy
import hashlib
import json

import polars as pl
import pytest

from test_freddie_rebuild_stream import orig, perf, sources, build_quarter
from test_run_freddie_rebuild import audit_fixture
from test_calibrate_freddie_rebuild import inputs as calibration_inputs
import freddie_raw_quarter_audit as raw_audit
import run_freddie_rebuild as driver


def id_hash(loan_id):
    return hashlib.sha256(loan_id.encode()).hexdigest()


def record_for(o, p, loan_id='F20Q2000001', quarter='2020Q1'):
    return dict(quarter=quarter, allowed_id_sha256=[id_hash(loan_id)],
        source_sha256={'origination': driver.digest(o), 'performance': driver.digest(p)},
        expected=dict(original_records=1, performance_rows=2, eligible_original_loans=1,
                      eligible_original_upb=100.),
        clarification_sha256='c' * 64,
        evidence_sha256={'diagnostic/report.json': 'd' * 64})


def exception_sources(tmp_path, loan_id='F20Q2000001'):
    return sources(tmp_path,
        [orig(1).replace('F20Q1000001', loan_id)],
        [perf(1, '202204', 100).replace('F20Q1000001', loan_id),
         perf(1, '202205', 90).replace('F20Q1000001', loan_id)])


def test_default_prefix_gate_remains_strict(tmp_path):
    o, p = exception_sources(tmp_path)
    assert raw_audit.schema_audit(o, p, quarter='2020Q1')[0]['passed'] is False
    with pytest.raises(ValueError, match='identity'):
        build_quarter(o, p, tmp_path / 'strict', '2020Q1')


def test_exact_same_year_exception_preserves_source_principal_and_identity(tmp_path):
    o, p = exception_sources(tmp_path)
    record = record_for(o, p)
    schema, _ = raw_audit.schema_audit(o, p, quarter='2020Q1', identity_exceptions=record)
    report = build_quarter(o, p, tmp_path / 'accepted', '2020Q1', identity_exceptions=record)
    assert schema['passed'] is True
    assert schema['identity_exceptions'] == report['identity_exceptions']
    audit = report['identity_exceptions']
    for k, v in record['expected'].items():
        assert audit[k] == v
    sample = pl.read_parquet(tmp_path / 'accepted/snapshot.parquet')
    assert sample['loan_id'].to_list() == ['F20Q2000001']
    assert sample['vintage'].to_list() == [2020]
    assert sample['balance'].sum() == 90.
    assert pl.read_parquet(tmp_path / 'accepted/cohort_history.parquet')['cohort_original_upb'].sum() == 100.


@pytest.mark.parametrize('loan_id', ['F19Q2000001', 'F20Q9000001', 'F20Q2bad', 'F20Q2000002'])
def test_malformed_cross_year_and_unlisted_ids_remain_rejected(tmp_path, loan_id):
    o, p = exception_sources(tmp_path, loan_id)
    record = record_for(o, p, loan_id if loan_id != 'F20Q2000002' else 'F20Q2000001')
    with pytest.raises(ValueError):
        raw_audit.schema_audit(o, p, quarter='2020Q1', identity_exceptions=record)
    with pytest.raises(ValueError):
        build_quarter(o, p, tmp_path / 'rejected', '2020Q1', identity_exceptions=record)
    assert not (tmp_path / 'rejected').exists()


@pytest.mark.parametrize('mutation', ['unused', 'performance_count', 'eligible_count', 'upb',
                                     'orig_hash', 'perf_hash', 'same_prefix'])
def test_record_requires_exhausted_allowlist_exact_counts_and_source_hashes(tmp_path, mutation):
    o, p = exception_sources(tmp_path)
    record = record_for(o, p)
    if mutation == 'unused':
        record['allowed_id_sha256'].append(id_hash('F20Q2000002'))
        record['expected']['original_records'] = 2
    elif mutation == 'same_prefix':
        o.write_text(o.read_text().replace('F20Q2', 'F20Q1'))
        p.write_text(p.read_text().replace('F20Q2', 'F20Q1'))
        record = record_for(o, p, 'F20Q1000001')
    elif mutation.endswith('hash'):
        record['source_sha256']['origination' if mutation == 'orig_hash' else 'performance'] = 'f' * 64
    else:
        key = {'performance_count': 'performance_rows', 'eligible_count': 'eligible_original_loans', 'upb': 'eligible_original_upb'}[mutation]
        record['expected'][key] += 1
    with pytest.raises(ValueError):
        raw_audit.schema_audit(o, p, quarter='2020Q1', identity_exceptions=record)
    with pytest.raises(ValueError):
        build_quarter(o, p, tmp_path / 'rejected', '2020Q1', identity_exceptions=record)


def test_allowlisted_unknown_performance_id_still_requires_original_membership(tmp_path):
    o, p = exception_sources(tmp_path)
    p.write_text(p.read_text() + perf(9, '202205', 100) + '\n')
    record = record_for(o, p)
    schema, _ = raw_audit.schema_audit(o, p, quarter='2020Q1', identity_exceptions=record)
    assert not schema['passed'] and schema['performance']['unknown_origination_ids'] == 1
    with pytest.raises(ValueError, match='matching'):
        build_quarter(o, p, tmp_path / 'rejected', '2020Q1', identity_exceptions=record)


def add_frozen_identity(root, destination):
    quarter = destination.name
    identity = f'F{quarter[2:4]}Q3000001'
    diagnostic = root / 'diagnostic/report.json'
    diagnostic.parent.mkdir(exist_ok=True)
    driver.write_json(diagnostic, {'no_overlap': True})
    clarification = driver.IDENTITY_CLARIFICATION.read_bytes()
    (root / 'identity_clarification_frozen.md').write_bytes(clarification)
    record = dict(quarter=quarter, allowed_id_sha256=[id_hash(identity)],
        source_sha256={'origination': 'a' * 64, 'performance': 'b' * 64},
        expected=dict(original_records=1, performance_rows=2, eligible_original_loans=1,
                      eligible_original_upb=100.),
        clarification_sha256=driver.digest(root / 'identity_clarification_frozen.md'),
        evidence_sha256={'diagnostic/report.json': driver.digest(diagnostic)})
    driver.write_json(root / 'identity_exceptions_frozen.json', {quarter: record})
    record = driver.load_identity_record(root, quarter)
    freeze = json.loads((destination / 'execution_freeze.json').read_text())
    freeze.update(driver.freeze_identity_record(root, destination, quarter, record))
    driver.write_json(destination / 'execution_freeze.json', freeze)
    audit = dict(enabled=True, quarter=quarter, allowed_id_sha256=record['allowed_id_sha256'],
                 source_sha256=record['source_sha256'], **record['expected'])
    for name in ['schema.json', 'rebuilt/report.json']:
        doc = json.loads((destination / name).read_text())
        doc['identity_exceptions'] = audit
        driver.write_json(destination / name, doc)
    worker = json.loads((destination / 'worker_passed.json').read_text())
    worker['report'] = json.loads((destination / 'rebuilt/report.json').read_text())
    driver.write_json(destination / 'worker_passed.json', worker)
    return record


@pytest.mark.parametrize('mutation', ['none', 'root_manifest', 'copied_record', 'evidence',
                                     'clarification', 'schema_count', 'stream_count', 'unfrozen'])
def test_completion_binds_exact_manifest_spec_evidence_and_schema_stream_counts(tmp_path, mutation):
    destination = audit_fixture(tmp_path)
    record = add_frozen_identity(tmp_path, destination)
    if mutation == 'none':
        driver.seal_completion(destination)
        got = driver.validate_completed(destination)
        assert 'identity_exception.json' in got['output_sha256']
        return
    if mutation == 'root_manifest':
        driver.write_json(tmp_path / 'identity_exceptions_frozen.json', {})
    elif mutation == 'copied_record':
        driver.write_json(destination / 'identity_exception.json', {})
    elif mutation == 'clarification':
        (destination / 'identity_clarification.md').write_text('tampered')
    elif mutation == 'evidence':
        next((destination / 'identity_evidence').iterdir()).write_text('tampered')
    elif mutation == 'unfrozen':
        doc = json.loads((destination / 'execution_freeze.json').read_text())
        doc = {k: v for k, v in doc.items() if not k.startswith('identity_')}
        driver.write_json(destination / 'execution_freeze.json', doc)
    else:
        name = 'schema.json' if mutation == 'schema_count' else 'rebuilt/report.json'
        doc = json.loads((destination / name).read_text())
        doc['identity_exceptions']['performance_rows'] += 1
        driver.write_json(destination / name, doc)
        if mutation == 'stream_count':
            worker = json.loads((destination / 'worker_passed.json').read_text())
            worker['report'] = doc
            driver.write_json(destination / 'worker_passed.json', worker)
    with pytest.raises(ValueError):
        driver.seal_completion(destination)
    assert not (destination / 'completed.json').exists()


def test_old_strict_completion_stays_valid_with_an_unrelated_root_manifest(tmp_path):
    destination = audit_fixture(tmp_path)
    driver.seal_completion(destination)
    driver.write_json(tmp_path / 'identity_exceptions_frozen.json', {'2020Q4': {'unused_here': True}})
    assert driver.validate_completed(destination)['status'] == 'completed'


def test_combined_validation_rejects_lost_identity_accounting(calibration_inputs):
    from hazard.calibrate_freddie_rebuild import validated_combined
    root = calibration_inputs['root']
    path = root / 'quarters/2017Q2'
    record = add_frozen_identity(root, path)
    (path / 'completed.json').unlink()
    driver.seal_completion(path)
    report_path = root / 'combined/report.json'
    combined = json.loads(report_path.read_text())
    combined['source_report_sha256']['2017Q2'] = driver.digest(path / 'rebuilt/report.json')
    driver.write_json(report_path, combined)
    with pytest.raises(ValueError, match='identity'):
        validated_combined(root)
    audit = json.loads((path / 'rebuilt/report.json').read_text())['identity_exceptions']
    combined['identity_exceptions_by_quarter'] = {q: audit if q == '2017Q2' else None for q in driver.QUARTERS}
    combined['identity_exception_totals'] = record['expected']
    driver.write_json(report_path, combined)
    assert validated_combined(root)[0]['identity_exception_totals']['eligible_original_upb'] == 100.
