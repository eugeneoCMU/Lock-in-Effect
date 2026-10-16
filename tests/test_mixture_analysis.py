import json
import pytest
from hazard.mixture_analysis import planned_inputs


def test_pipeline_inputs_are_explicit_and_do_not_execute_commands(tmp_path):
    p=tmp_path/'pipeline.json'
    p.write_text(json.dumps({'stages':[
        {'name':'paired-simulation','command':['python','-u','script','--root','/data','--output','/old']},
        {'name':'scoring','command':['python','-u','script','--root','/data','--output','/old-scores']}]}))
    result=planned_inputs(p)
    assert result['paired-simulation']=={'root':__import__('pathlib').Path('/data')}
    assert 'output' not in result['scoring']


def test_pipeline_rejects_missing_required_stage(tmp_path):
    p=tmp_path/'pipeline.json';p.write_text('{"stages": []}')
    with pytest.raises(ValueError): planned_inputs(p)


def test_incomplete_corrected_data_stops_before_output(tmp_path):
    from hazard.mixture_analysis import run
    p=tmp_path/'pipeline.json'
    root=tmp_path/'incomplete'
    p.write_text(json.dumps({'frozen_sha256':{},'stages':[
        {'name':name,'command':['python','-u','script','--root',str(root),'--output','/unused']}
        for name in ('paired-simulation','scoring')]}))
    output=tmp_path/'analysis'
    with pytest.raises((ValueError,FileNotFoundError)): run(pipeline=p,output=output)
    assert not output.exists()


def test_matrix_keeps_benchmarks_and_records_terminal_status(tmp_path,monkeypatch):
    import hazard.mixture_analysis as stage
    root=tmp_path/'corrected';output=tmp_path/'analysis';p=tmp_path/'pipeline.json'
    p.write_text(json.dumps({'frozen_sha256':{},'stages':[
        {'name':name,'command':['python','-u','script','--root',str(root),'--output','/unused']}
        for name in ('paired-simulation','scoring')]}))
    calls=[]
    monkeypatch.setattr(stage.pair,'validated_combined',lambda root: ({},{}))
    def old_pair(**kwargs):
        calls.append('benchmark-pair');return {'reported_marginal_b':1.}
    def old_score(**kwargs):
        calls.append('benchmark-score');return {'aggregate':{}}
    def mixture_pair(**kwargs):
        assert calls[:2]==['benchmark-pair','benchmark-score']
        return {'reported_marginal_b':kwargs['sensitive_share'], 'closed_pool_cash_marginal_b':0.}
    monkeypatch.setattr(stage.pair,'run',old_pair)
    monkeypatch.setattr(stage.scoring,'run',old_score)
    monkeypatch.setattr(stage,'run_pair',mixture_pair)
    monkeypatch.setattr(stage,'score_mixture',lambda **kwargs: {'aggregate':{},'support':{}})
    monkeypatch.setattr(stage,'run_additive_pair',lambda **kwargs: {'reported_marginal_b':2.})
    monkeypatch.setattr(stage,'score_additive',lambda **kwargs: {'aggregate':{}})
    def validate(output,scenarios):
        assert len(scenarios)==40
        assert not (output/'results.json').exists()
        return {'status':'passed'}
    monkeypatch.setattr(stage,'validate_analysis',validate)
    result=stage.run(pipeline=p,output=output)
    assert result['acceptance']['status']=='passed'
    assert len(result['scenarios'])==40
    assert len({r['scenario'] for r in result['scenarios']})==40
    assert json.loads((output/'progress.json').read_text())['status']=='complete'
    assert result['sensitive_share_estimated'] is False


def test_failed_acceptance_prevents_success_receipt(tmp_path,monkeypatch):
    import hazard.mixture_analysis as stage
    root=tmp_path/'root';output=tmp_path/'out';pipeline=tmp_path/'pipeline.json'
    pipeline.write_text(json.dumps({'frozen_sha256':{},'stages':[
        {'name':name,'command':['python','-u','script','--root',str(root),'--output','/unused']}
        for name in ('paired-simulation','scoring')]}))
    monkeypatch.setattr(stage.pair,'validated_combined',lambda root: ({},{}))
    receipt={'reported_marginal_b':0.,'closed_pool_cash_marginal_b':0.}
    score={'aggregate':{},'support':{}}
    monkeypatch.setattr(stage.pair,'run',lambda **kw:receipt)
    monkeypatch.setattr(stage.scoring,'run',lambda **kw:score)
    monkeypatch.setattr(stage,'run_pair',lambda **kw:receipt)
    monkeypatch.setattr(stage,'score_mixture',lambda **kw:score)
    monkeypatch.setattr(stage,'run_additive_pair',lambda **kw:receipt)
    monkeypatch.setattr(stage,'score_additive',lambda **kw:score)
    def reject(*args): raise ValueError('Acceptance failed')
    monkeypatch.setattr(stage,'validate_analysis',reject)
    with pytest.raises(ValueError,match='Acceptance failed'): stage.run(pipeline=pipeline,output=output)
    assert not (output/'results.json').exists()
    assert json.loads((output/'progress.json').read_text())['status']=='failed'


def test_analysis_code_freeze_checked_before_acceptance(tmp_path,monkeypatch):
    import hazard.mixture_analysis as stage
    pipeline=tmp_path/'pipeline.json';output=tmp_path/'out'
    pipeline.write_text(json.dumps({'frozen_sha256':{},'stages':[
        {'name':name,'command':['python','-u','script','--root',str(tmp_path/'root'),'--output','/unused']}
        for name in ('paired-simulation','scoring')]}))
    monkeypatch.setattr(stage.pair,'validated_combined',lambda root: ({},{}))
    receipt={'reported_marginal_b':0.,'closed_pool_cash_marginal_b':0.}
    score={'aggregate':{},'support':{}}
    for name in ('run_pair','run_additive_pair'): monkeypatch.setattr(stage,name,lambda **kw:receipt)
    for name in ('score_mixture','score_additive'): monkeypatch.setattr(stage,name,lambda **kw:score)
    monkeypatch.setattr(stage.pair,'run',lambda **kw:receipt)
    monkeypatch.setattr(stage.scoring,'run',lambda **kw:score)
    checked=[]
    def verify(hashes):
        checked.append(hashes)
        if any('mixture_analysis.py' in path for path in hashes):
            raise ValueError('Changed analysis code')
    monkeypatch.setattr(stage.pair,'verify_hashes',verify)
    monkeypatch.setattr(stage,'validate_analysis',lambda *args: pytest.fail('Gate reached before code check'))
    with pytest.raises(ValueError,match='Changed analysis code'): stage.run(pipeline=pipeline,output=output)
    assert len(checked)==3
    assert not (output/'results.json').exists()


def test_retained_source_drift_prevents_matrix_acceptance(tmp_path, monkeypatch):
    import hazard.mixture_analysis as stage
    import source_rebuild_receipts as receipts
    pipeline=tmp_path/'pipeline.json';output=tmp_path/'out'
    pipeline.write_text(json.dumps({'frozen_sha256':{},'stages':[
        {'name':name,'command':['python','-u','script','--root',str(tmp_path/'root'),'--output','/unused']}
        for name in ('paired-simulation','scoring')]}))
    monkeypatch.setattr(stage.pair,'validated_combined',lambda root: ({},{}))
    receipt={'reported_marginal_b':0.,'closed_pool_cash_marginal_b':0.}
    score={'aggregate':{},'support':{}}
    for name in ('run_pair','run_additive_pair'):monkeypatch.setattr(stage,name,lambda **kw:receipt)
    for name in ('score_mixture','score_additive'):monkeypatch.setattr(stage,name,lambda **kw:score)
    monkeypatch.setattr(stage.pair,'run',lambda **kw:receipt)
    monkeypatch.setattr(stage.scoring,'run',lambda **kw:score)
    def changed(self):raise ValueError('Retained source changed')
    monkeypatch.setattr(receipts.ReceiptValidationSession,'verify_unchanged',changed)
    monkeypatch.setattr(stage,'validate_analysis',lambda *args:pytest.fail('Acceptance before source verification'))
    with pytest.raises(ValueError,match='source changed'):stage.run(pipeline=pipeline,output=output)
    assert not (output/'acceptance.json').exists()
    assert not (output/'results.json').exists()
    assert json.loads((output/'progress.json').read_text())['status']=='failed'
