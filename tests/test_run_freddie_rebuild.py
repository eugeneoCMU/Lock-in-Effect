"""Cloud cleanup and resume must be evidenced, never inferred from filenames."""
import sys,json
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'hazard'))
from run_freddie_rebuild import provider_flags,verify_cleanup_receipt,validate_completed,digest


def good_file():
    return dict(exists=True,allocated_bytes=0,isDownloaded=0,isTrashed=0,isUploaded=1)


def test_provider_flags_require_all_unambiguous_states():
    assert provider_flags('isDownloaded = 0\nisTrashed = 0\nisUploaded = 1') == {
        'isDownloaded':0,'isTrashed':0,'isUploaded':1}
    with pytest.raises(ValueError):provider_flags('isDownloaded = 0\nisTrashed = 0')
    with pytest.raises(ValueError):provider_flags('isDownloaded = 0\nisDownloaded = 1\nisTrashed = 0\nisUploaded = 1')


@pytest.mark.parametrize('field,bad',[('exists',False),('allocated_bytes',4096),('isDownloaded',1),('isTrashed',1),('isUploaded',0)])
def test_cleanup_needs_cloud_only_uploaded_untrashed_originals(field,bad):
    files=[good_file(),good_file()];files[1][field]=bad
    with pytest.raises(ValueError):verify_cleanup_receipt({'files':files})


from types import SimpleNamespace
import subprocess
import run_freddie_rebuild as driver


class StubbornWorker:
    pid = 123
    returncode = None
    killed = False
    terminated = False

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.killed = True
        self.returncode = -9

    def wait(self, timeout=None):
        if self.returncode is None:
            raise subprocess.TimeoutExpired('synthetic worker', timeout)
        return self.returncode


@pytest.mark.parametrize('failure', ['limit', 'monitor', 'interrupt'])
def test_worker_is_reaped_before_cleanup_on_every_failure(tmp_path, monkeypatch, failure):
    source = tmp_path/'source'; source.mkdir()
    for name in ['orig_2017Q2.txt','perf_2017Q2.txt']:
        (source/name).write_text('synthetic')
    output = tmp_path/'output'; output.mkdir()
    spec = tmp_path/'spec.md'; spec.write_text('frozen synthetic scope')
    (output/'spec_frozen.md').write_bytes(spec.read_bytes())
    (output/'eligibility_clarification_frozen.md').write_bytes(driver.ELIGIBILITY_CLARIFICATION.read_bytes())
    (output/'cash_ratio_clarification_frozen.md').write_bytes(driver.CASH_RATIO_CLARIFICATION.read_bytes())
    monkeypatch.setattr(driver, 'SPEC', spec)
    monkeypatch.setattr(driver.shutil, 'disk_usage', lambda _: SimpleNamespace(free=30*driver.GIB))
    worker = StubbornWorker()
    monkeypatch.setattr(driver.subprocess, 'Popen', lambda *a, **kw: worker)
    def monitor(*a, **kw):
        if failure == 'monitor': raise OSError('monitor unavailable')
        if failure == 'interrupt': raise KeyboardInterrupt('interrupted')
        return SimpleNamespace(stdout=str(9*driver.GIB//1024))
    monkeypatch.setattr(driver.subprocess, 'run', monitor)
    cleaned = []
    def cleanup(*a):
        assert worker.poll() is not None, 'cleanup began with a live worker'
        cleaned.append(True)
        return {'files':[good_file(),good_file()]}
    monkeypatch.setattr(driver, 'cleanup', cleanup)
    expected = {'limit':RuntimeError,'monitor':OSError,'interrupt':KeyboardInterrupt}[failure]
    with pytest.raises(expected): driver.run_quarter('2017Q2',source,output)
    assert worker.terminated and worker.killed
    assert cleaned == [True]


def test_failed_kill_never_evicts_a_live_source(tmp_path, monkeypatch):
    worker = StubbornWorker()
    monkeypatch.setattr(worker, 'kill', lambda: None)
    with pytest.raises(RuntimeError, match='reap'):
        driver.stop_worker(worker)
    assert worker.poll() is None


def audit_fixture(root, quarter='2017Q2'):
    p=root/'quarters'/quarter; p.mkdir(parents=True)
    (root/'spec_frozen.md').write_text('frozen synthetic specification')
    driver.write_json(p/'schema.json', {'passed':True, 'origination':{'sha256':'a'*64,'rows':1,'eligible_360_month_ids':1},'performance':{'sha256':'b'*64,'rows':2}})
    hashes={'origination':'a'*64,'performance':'b'*64}
    driver.write_json(p/'source_hashes_after.json', hashes)
    code=p/'executed_code'; code.mkdir()
    for name in driver.CORE_CODE_FILES: (code/name).write_text('synthetic code '+name)
    driver.write_json(p/'execution_freeze.json', {'quarter':quarter,'cutoff':'202509','transition_end':'202205','spec_sha256':digest(root/'spec_frozen.md'),'code_sha256':{n:digest(code/n) for n in driver.CORE_CODE_FILES}})
    (p/'spec_frozen.md').write_bytes((root/'spec_frozen.md').read_bytes())
    files=[dict(good_file(),path=str(root/f'{kind}_{quarter}.txt'),size=20,mtime_ns=100) for kind in ['orig','perf']]
    driver.write_json(p/'cleanup.json', {'files':files})
    driver.write_json(p/'source_metadata_at_worker_start.json', files)
    driver.write_json(p/'resources.json',{'peak_rss_bytes':10,'worker_reaped':True,'free_disk_bytes_after':20*driver.GIB})
    rebuilt=p/'rebuilt';rebuilt.mkdir()
    for name in driver.REBUILT_ARTIFACTS: (rebuilt/name).write_bytes(b'synthetic compact output')
    report={'quarter':quarter,'cutoff':'202509','snapshot_month':'202205','transition_end':'202205','source_sha256':hashes,
            'counts':{'origination_rows':1,'performance_rows':2,'eligible_original_ids':1},
            'cutoff_proof':{'post_cutoff_outcomes_decoded':0,'outcome_filter_precedes_decode':True,'latest_decoded_month':'202205'},
            'artifacts':{n:{'sha256':digest(rebuilt/n),'rows':1} for n in driver.REBUILT_ARTIFACTS}}
    driver.write_json(rebuilt/'report.json',report)
    driver.write_json(p/'worker_passed.json',{'source_hashes':hashes,'report':report})
    return p


def test_sealed_completion_requires_complete_evidence_and_detects_tampering(tmp_path):
    p=audit_fixture(tmp_path)
    driver.seal_completion(p)
    record=validate_completed(p)
    assert record['status']=='completed'
    (p/'source_hashes_after.json').write_text('{}')
    with pytest.raises(ValueError,match='changed'):validate_completed(p)


def test_one_output_cannot_masquerade_as_completed_quarter(tmp_path):
    (tmp_path/'data').write_bytes(b'checked')
    driver.write_json(tmp_path/'completed.json',{'cleanup':{'files':[good_file(),good_file()]},'output_sha256':{'data':digest(tmp_path/'data')}})
    with pytest.raises(ValueError):validate_completed(tmp_path)


@pytest.mark.parametrize('mutation',['missing_schema','mismatched_source','wrong_quarter','wrong_spec','missing_code','wrong_cutoff','wrong_cleanup_source'])
def test_sealing_rejects_inconsistent_required_evidence(tmp_path,mutation):
    p=audit_fixture(tmp_path)
    if mutation=='missing_schema':(p/'schema.json').unlink()
    elif mutation=='missing_code':(p/'executed_code'/driver.CORE_CODE_FILES[0]).unlink()
    elif mutation=='mismatched_source':driver.write_json(p/'source_hashes_after.json',{'origination':'c'*64,'performance':'b'*64})
    elif mutation in ['wrong_quarter','wrong_spec','wrong_cutoff']:
        data=json.loads((p/'execution_freeze.json').read_text())
        field,value={'wrong_quarter':('quarter','2018Q1'),'wrong_spec':('spec_sha256','c'*64),'wrong_cutoff':('cutoff','202601')}[mutation]
        data[field]=value;driver.write_json(p/'execution_freeze.json',data)
    else:
        data=json.loads((p/'cleanup.json').read_text()); data['files'][0]['path']='wrong_source.txt';driver.write_json(p/'cleanup.json',data)
    with pytest.raises((ValueError,FileNotFoundError)):driver.seal_completion(p)
    assert not (p/'completed.json').exists()


def add_zero_rate_evidence(p, *, authorized):
    z={'enabled':True,'otherwise_eligible_frm_count':1,'otherwise_eligible_frm_upb':237000.,'known360_count':1,'known360_upb':237000.}
    schema=json.loads((p/'schema.json').read_text());schema['origination']['zero_note_rate_exclusions']=z;driver.write_json(p/'schema.json',schema)
    report=json.loads((p/'rebuilt/report.json').read_text());report['zero_note_rate_exclusions']=z;driver.write_json(p/'rebuilt/report.json',report)
    worker=json.loads((p/'worker_passed.json').read_text());worker['report']=report;driver.write_json(p/'worker_passed.json',worker)
    if authorized:
        (p/'eligibility_clarification.md').write_text('synthetic explicit positive-rate scope')
        (p.parent.parent/'eligibility_clarification_frozen.md').write_bytes((p/'eligibility_clarification.md').read_bytes())
        freeze=json.loads((p/'execution_freeze.json').read_text());freeze['eligibility_clarification_sha256']=digest(p/'eligibility_clarification.md');driver.write_json(p/'execution_freeze.json',freeze)


def test_zero_rate_exclusion_needs_hashed_scope_and_matching_accounting(tmp_path):
    p=audit_fixture(tmp_path)
    add_zero_rate_evidence(p,authorized=False)
    with pytest.raises(ValueError,match='clarification'):driver.seal_completion(p)
    add_zero_rate_evidence(p,authorized=True)
    driver.seal_completion(p)
    assert 'eligibility_clarification.md' in validate_completed(p)['output_sha256']


def test_zero_rate_schema_stream_disagreement_blocks_completion(tmp_path):
    p=audit_fixture(tmp_path);add_zero_rate_evidence(p,authorized=True)
    schema=json.loads((p/'schema.json').read_text());schema['origination']['zero_note_rate_exclusions']['known360_upb']=238000.;driver.write_json(p/'schema.json',schema)
    with pytest.raises(ValueError,match='exclusion'):driver.seal_completion(p)


@pytest.mark.parametrize('problem',['none','unfrozen','multiple_events','changed_ratio','changed_spec'])
def test_partial_cohort_exception_requires_frozen_accounting_evidence(tmp_path,problem):
    p=audit_fixture(tmp_path)
    audit=dict(partial_cohort_overrun_enabled=True,overrun_cohort_count=1,overruns=[dict(original_upb=100.,cumulative_prepaid_upb=120.,peak_ratio=1.2,multiple_positive_payoff_loans=0,terminal_revival_loans=0)])
    if problem=='multiple_events':audit['overruns'][0]['multiple_positive_payoff_loans']=1
    if problem=='changed_ratio':audit['overruns'][0]['peak_ratio']=2.
    report=json.loads((p/'rebuilt/report.json').read_text());report['quarter_cash_ratio_audit']=audit;driver.write_json(p/'rebuilt/report.json',report)
    worker=json.loads((p/'worker_passed.json').read_text());worker['report']=report;driver.write_json(p/'worker_passed.json',worker)
    if problem!='unfrozen':
        (p/'cash_ratio_clarification.md').write_text('synthetic partial-cohort rule; final bound unchanged')
        (p.parent.parent/'cash_ratio_clarification_frozen.md').write_bytes((p/'cash_ratio_clarification.md').read_bytes())
        freeze=json.loads((p/'execution_freeze.json').read_text());freeze['cash_ratio_clarification_sha256']=digest(p/'cash_ratio_clarification.md');driver.write_json(p/'execution_freeze.json',freeze)
    if problem=='changed_spec':(p/'cash_ratio_clarification.md').write_text('changed')
    if problem=='none':
        driver.seal_completion(p)
        assert 'cash_ratio_clarification.md' in validate_completed(p)['output_sha256']
    else:
        with pytest.raises(ValueError):driver.seal_completion(p)
        assert not (p/'completed.json').exists()
