import pandas as pd
import pytest
import ast
from pathlib import Path
import subprocess
import sys

from empirical_grounding_pipeline import validate_claim_register, write_json, plan_file_references, verify_panel_receipt


def test_claim_register_requires_evidence_context_for_every_number():
    with pytest.raises(ValueError, match='population'):
        validate_claim_register([{'value': 42.6, 'object': 'historical_result'}])


def test_unknown_evidence_class_rejected():
    claim = dict(value=1, object='payoff', population='synthetic', denominator='dollars',
        period='202205', evidence_class='software_verified_empirical', source_receipt='receipt',
        assumptions=[], unsupported_extensions=[])
    with pytest.raises(ValueError, match='evidence_class'):
        validate_claim_register([claim])


def test_nonfinite_json_is_not_silently_written(tmp_path):
    with pytest.raises(ValueError):
        write_json(tmp_path/'bad.json', {'ratio': float('nan')})


def test_source_inventory_ignores_fenced_code_and_signatures():
    text = '`output/file.json`\n```python\n' + 'x'*300 + '\n```\n`fit_reference(data)`'
    assert plan_file_references(text) == ['output/file.json']


def test_quarter_panel_receipt_mismatch_blocks_reuse(tmp_path):
    path = tmp_path / 'panel.parquet'; path.write_bytes(b'changed local derivative')
    with pytest.raises(ValueError, match='panel receipt'):
        verify_panel_receipt(path, {'output_sha256': {'rebuilt/panel.parquet': 'wrong'}})


def mechanism_builder():
    return Path(__file__).resolve().parents[1] / 'output/empirical-grounding/2026-10-16/attempt-001/mechanisms/build_reports.py'


def test_relocated_mechanism_builder_targets_its_own_attempt(tmp_path):
    tree = ast.parse(mechanism_builder().read_text())
    assignment = next(n for n in tree.body if isinstance(n, ast.Assign)
                      and any(isinstance(t,ast.Name) and t.id == 'BASE' for t in n.targets))
    scope = {'Path':Path, '__file__':str(tmp_path/'attempt-new/mechanisms/build_reports.py')}
    exec(compile(ast.Module(body=[assignment],type_ignores=[]),'builder','exec'),scope)
    assert scope['BASE'] == tmp_path/'attempt-new'


def test_relocated_builder_reproduces_reports_and_refuses_overwrite(tmp_path):
    source = mechanism_builder()
    root = Path(__file__).resolve().parents[1]
    target = tmp_path/'attempt-new/mechanisms/build_reports.py'
    target.parent.mkdir(parents=True)
    target.write_text(source.read_text())
    result = subprocess.run([sys.executable,str(target)],cwd=root,capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
    assert (target.parent/'cause-bounds.json').exists()
    assert (target.parent.parent/'transport/transport-support.json').exists()
    original = (target.parent/'cause-bounds.json').read_bytes()
    repeated = subprocess.run([sys.executable,str(target)],cwd=root,capture_output=True,text=True)
    assert repeated.returncode != 0
    assert 'Stage outputs already exist' in repeated.stderr
    assert (target.parent/'cause-bounds.json').read_bytes() == original
