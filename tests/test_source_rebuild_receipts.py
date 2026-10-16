"""Receipt dispatch must preserve each transport's sealed evidence contract."""
import importlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'hazard'))


@pytest.mark.parametrize('policy,module_name,function', [
    (None, 'run_freddie_rebuild', 'validate_completed'),
    ('local_archive_retained', 'release47_local_rebuild', 'validate_local_completed'),
    ('annual_archive_retained', 'freddie_archive_rebuild', 'validate_archive_completed'),
])
def test_dispatch_resolves_symlink_to_original_quarter(tmp_path, monkeypatch, policy, module_name, function):
    source = tmp_path / 'source' / '2021Q1'
    source.mkdir(parents=True)
    receipt = {} if policy is None else {'storage_policy': policy}
    (source / 'completed.json').write_text(json.dumps(receipt))
    link = tmp_path / '2021Q1'
    link.symlink_to(source, target_is_directory=True)
    def sealed_validator(path):
        assert path == source.resolve()
        return dict(receipt, sealed=True)
    monkeypatch.setitem(sys.modules, module_name, SimpleNamespace(**{function: sealed_validator}))
    api = importlib.import_module('source_rebuild_receipts')
    assert api.validate_source_completed(link) == dict(receipt, sealed=True)


def test_unknown_storage_policy_fails_closed(tmp_path):
    (tmp_path / 'completed.json').write_text(json.dumps({'storage_policy': 'skip_validation'}))
    api = importlib.import_module('source_rebuild_receipts')
    with pytest.raises(ValueError, match='storage policy'):
        api.validate_source_completed(tmp_path)


def test_scoped_session_verifies_inputs_once_and_rechecks_before_acceptance(tmp_path, monkeypatch):
    stage = importlib.import_module('source_rebuild_receipts')
    raw = tmp_path / 'raw'; raw.write_bytes(b'fixed-source')
    import hashlib
    expected = hashlib.sha256(raw.read_bytes()).hexdigest()
    q = tmp_path / 'quarter'; q.mkdir()
    (q / 'completed.json').write_text(json.dumps({'storage_policy':'annual_archive_retained'}))
    (q / 'input_manifest.json').write_text(json.dumps({'input_sha256':{str(raw):expected}}))
    calls=[]
    class Validator:
        @staticmethod
        def validate_archive_completed(path, *, verify_inputs=True):
            calls.append(verify_inputs)
            return {'compact_evidence_verified':True}
    monkeypatch.setattr(stage.importlib, 'import_module', lambda name: Validator)
    with stage.receipt_validation_session() as session:
        assert stage.validate_source_completed(q)['compact_evidence_verified']
        assert stage.validate_source_completed(q)['compact_evidence_verified']
        assert calls == [False, False]
        assert session.inputs == {str(raw):expected}
        session.verify_unchanged()
        raw.write_bytes(b'changed-source')
        with pytest.raises(ValueError, match='changed'):session.verify_unchanged()
    stage.validate_source_completed(q)
    assert calls[-1] is True
    raw.write_bytes(b'fixed-source')
    with stage.receipt_validation_session():
        stage.validate_source_completed(q)
        (q / 'completed.json').write_text(json.dumps({'storage_policy':'annual_archive_retained','changed':True}))
        with pytest.raises(ValueError, match='receipt changed'):stage.validate_source_completed(q)
