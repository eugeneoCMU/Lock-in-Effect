"""Local evidence checks; simulation validation never upgrades empirical status."""
import hashlib
from pathlib import Path
import re


def month_ordinal(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{6}', value):
        raise ValueError('Month must be YYYYMM')
    year, month = int(value[:4]), int(value[4:])
    if year < 1 or not 1 <= month <= 12:
        raise ValueError('Invalid calendar month')
    return year * 12 + month - 1


def month_string(ordinal):
    year, month = divmod(ordinal, 12)
    return f'{year:04d}{month + 1:02d}'


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def build_readiness(*, observed_cutoff, simulation_end, prior_support, input_receipts):
    start, end = month_ordinal(observed_cutoff), month_ordinal(simulation_end)
    checks = {}
    for name, receipt in input_receipts.items():
        try:
            actual = sha256(receipt['path'])
            checks[name] = dict(receipt, actual_sha256=actual,
                status='matched_local_receipt' if actual == receipt.get('sha256') else 'hash_mismatch')
        except (OSError, KeyError) as exc:
            checks[name] = dict(receipt, status='unavailable', reason=str(exc))
    return dict(observed_cutoff=observed_cutoff,
        unobserved_simulation_months=[month_string(i) for i in range(start + 1, end + 1)],
        prior_support_status=prior_support.get('designated_inference_status', 'not_supplied'),
        source_checks=checks, receipt_mapping_verified=False,
        reference_status='not_estimated', share_status='not_estimated', gamma_status='not_estimated',
        mechanisms_status='selected_labels_and_unknown_causes', transport_status='not_verified',
        receipts_status='not_verified', original_source_audit='not_performed_by_this_adapter')
