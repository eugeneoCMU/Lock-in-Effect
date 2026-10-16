"""Dispatch sealed source receipts and bind corrected per-quarter provenance."""
from __future__ import annotations

import importlib
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json
from pathlib import Path

from schema import (SOURCE_SEMANTICS_VERSION, RELEASE47_SOURCE_SEMANTICS_VERSION,
                    source_layout_metadata)

MIXED_SOURCE_SEMANTICS_VERSION = 'freddie-mixed-layout-reo-priority-v4'


_SESSION = ContextVar('receipt_validation_session', default=None)


def _digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024**2), b''):
            h.update(block)
    return h.hexdigest()


class ReceiptValidationSession:
    """Reuse full retained-input hashes only inside a bounded matrix run.

    Compact evidence is still validated on every call. Receipt seals are pinned,
    and all retained inputs must be fully checked again before acceptance.
    """
    def __init__(self):
        self.inputs, self.seals = {}, {}

    def pin(self, path):
        path = str(Path(path).resolve())
        actual = _digest(path)
        if path in self.seals and self.seals[path] != actual:
            raise ValueError('Pinned source receipt changed: ' + path)
        self.seals[path] = actual

    def check_inputs(self, hashes):
        for name, expected in hashes.items():
            name = str(Path(name).resolve())
            if name in self.inputs:
                if self.inputs[name] != expected:
                    raise ValueError('Conflicting retained input hash: ' + name)
            else:
                if _digest(name) != expected:
                    raise ValueError('Retained input changed: ' + name)
                self.inputs[name] = expected

    def verify_unchanged(self):
        for name, expected in dict(self.seals, **self.inputs).items():
            if _digest(name) != expected:
                raise ValueError('Retained source or receipt changed: ' + name)


@contextmanager
def receipt_validation_session():
    if _SESSION.get() is not None:
        raise ValueError('Nested receipt validation sessions are not supported')
    session = ReceiptValidationSession()
    token = _SESSION.set(session)
    try:
        yield session
    finally:
        _SESSION.reset(token)


def source_receipt_type(receipt):
    policy = receipt.get('storage_policy')
    if policy is None:
        return 'native_cloud'
    if policy in ('local_archive_retained', 'annual_archive_retained'):
        return policy
    raise ValueError('Unknown source receipt storage policy: ' + str(policy))


def validate_source_completed(path):
    """Use the transport's own validator, after resolving combined-root links.

    Archive receipts retain local sources and do not claim cloud eviction.
    Imports stay lazy because archive runners also use this dispatcher.
    """
    path = Path(path).resolve()
    receipt = json.loads((path / 'completed.json').read_text())
    kind = source_receipt_type(receipt)
    module, function = {
        'native_cloud': ('run_freddie_rebuild', 'validate_completed'),
        'local_archive_retained': ('release47_local_rebuild', 'validate_local_completed'),
        'annual_archive_retained': ('freddie_archive_rebuild', 'validate_archive_completed'),
    }[kind]
    validator = getattr(importlib.import_module(module), function)
    session = _SESSION.get()
    if session is None:
        return validator(path)
    session.pin(path / 'completed.json')
    if kind == 'native_cloud':
        return validator(path)
    manifest = json.loads((path / 'input_manifest.json').read_text())
    session.check_inputs(manifest['input_sha256'])
    return validator(path, verify_inputs=False)


def source_provenance(quarters, reports, receipts):
    """Return an exact manifest for accepted corrected V2/V3 source reports."""
    semantics, layouts, types = {}, {}, {}
    for quarter, report, receipt in zip(quarters, reports, receipts):
        version = report.get('source_semantics_version')
        if version not in (SOURCE_SEMANTICS_VERSION, RELEASE47_SOURCE_SEMANTICS_VERSION):
            raise ValueError('Source semantics require a fresh corrected quarterly extraction')
        layout = source_layout_metadata('native32' if version == SOURCE_SEMANTICS_VERSION else 'release47')
        # Earlier native V2 compact reports did not carry layout metadata.
        actual = report.get('source_layout', layout if version == SOURCE_SEMANTICS_VERSION else None)
        if actual != layout:
            raise ValueError('Quarter source layout differs from corrected source semantics')
        if any(report.get(key) != value for key, value in {
                'quarter': quarter, 'cutoff': '202509', 'snapshot_month': '202205',
                'transition_end': '202205'}.items()):
            raise ValueError('Quarter or cutoff mismatch in rebuilt report')
        kind = source_receipt_type(receipt)
        if ((kind == 'native_cloud') != (version == SOURCE_SEMANTICS_VERSION)):
            raise ValueError('Source receipt type disagrees with corrected quarter semantics')
        semantics[quarter], layouts[quarter], types[quarter] = version, actual, kind
    version = (SOURCE_SEMANTICS_VERSION if all(v == SOURCE_SEMANTICS_VERSION for v in semantics.values())
               else MIXED_SOURCE_SEMANTICS_VERSION)
    return dict(source_semantics_version=version, source_semantics_by_quarter=semantics,
                source_layouts_by_quarter=layouts, source_receipt_types_by_quarter=types)


def validate_combined_provenance(report, expected):
    if report.get('source_semantics_version') != expected['source_semantics_version']:
        raise ValueError('Combined source semantics differ from corrected quarters')
    for key in ('source_semantics_by_quarter', 'source_layouts_by_quarter', 'source_receipt_types_by_quarter'):
        # Preserve sealed all-native V2 reports created before these extra fields.
        if key not in report and expected['source_semantics_version'] == SOURCE_SEMANTICS_VERSION:
            continue
        if report.get(key) != expected[key]:
            raise ValueError('Combined source provenance differs from verified quarters: ' + key)
