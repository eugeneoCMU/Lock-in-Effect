import hashlib

import pytest

from empirical_readiness import build_readiness


def test_readiness_preserves_limits():
    r = build_readiness(observed_cutoff='202509', simulation_end='202511',
        prior_support={'designated_inference_status': 'insufficient_support'}, input_receipts={})
    assert r['unobserved_simulation_months'] == ['202510', '202511']
    assert r['prior_support_status'] == 'insufficient_support'
    assert r['receipt_mapping_verified'] is False


def test_hash_match_does_not_verify_security_receipts(tmp_path):
    p = tmp_path / 'local'; p.write_bytes(b'local derivative')
    r = build_readiness(observed_cutoff='202509', simulation_end='202511', prior_support={},
        input_receipts={'panel': {'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}})
    assert r['source_checks']['panel']['status'] == 'matched_local_receipt'
    assert not r['receipt_mapping_verified']
    assert r['reference_status'] == 'not_estimated'


def test_bad_hash_and_missing_file_are_explicit(tmp_path):
    p = tmp_path / 'local'; p.write_bytes(b'x')
    r = build_readiness(observed_cutoff='202512', simulation_end='202601', prior_support={},
        input_receipts={'bad': {'path': str(p), 'sha256': 'wrong'},
                        'missing': {'path': str(p / 'absent'), 'sha256': 'wrong'}})
    assert r['unobserved_simulation_months'] == ['202601']
    assert r['source_checks']['bad']['status'] == 'hash_mismatch'
    assert r['source_checks']['missing']['status'] == 'unavailable'


@pytest.mark.parametrize('month', ['202513', '20251', '202500', 'no'])
def test_invalid_month_rejected(month):
    with pytest.raises(ValueError):
        build_readiness(observed_cutoff=month, simulation_end='202511', prior_support={}, input_receipts={})
