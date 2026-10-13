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
    result=stage.run(pipeline=p,output=output)
    assert len(result['scenarios'])==20
    assert len({r['scenario'] for r in result['scenarios']})==20
    assert json.loads((output/'progress.json').read_text())['status']=='complete'
    assert result['sensitive_share_estimated'] is False
