"""Exercise all 40 scenarios and final acceptance with one small synthetic book."""
import json
import pandas as pd
from test_simulate_freddie_rebuild import pair_inputs, floor_inputs
from test_calibrate_freddie_rebuild import source, dump


def test_real_matrix_passes_acceptance(pair_inputs,tmp_path):
    from hazard import mixture_analysis as stage
    from hazard import score_freddie_rebuild as scoring
    from hazard.coverage_exception import combined_audit
    root=pair_inputs['root'];combined=root/'combined'
    sample=pd.read_parquet(combined/'loan_sample.parquet')
    sample['fico_bucket']='660-739';sample['ltv_bucket']='<=80'
    sample.to_parquet(combined/'loan_sample.parquet',index=False)
    months=pd.date_range('2022-12-01','2025-09-01',freq='MS')
    panel=pd.DataFrame(dict(period=months,reporting_period=months.strftime('%Y%m'),
        vintage=2017,coupon=.03,fico_bucket='660-739',ltv_bucket='<=80',
        mean_loan_age=50.,exposure_upb=100.,orig_upb_sum=200.,cohort_original_upb=1000.,
        burnout=.8,prepaid_upb=1.))
    panel.to_parquet(combined/'cohort_month_panel.parquet',index=False)
    report=json.loads((combined/'report.json').read_text())
    reports=[json.loads((root/'quarters'/q/'rebuilt/report.json').read_text()) for q in source.QUARTERS]
    report['pre_snapshot_coverage']=combined_audit(reports,[])
    report.update(sample_n=len(sample),sample_unique_ids=sample.loan_id.nunique(),panel_rows=len(panel))
    report['output_sha256']={name:source.digest(combined/name) for name in report['output_sha256']}
    dump(combined/'report.json',report)
    freeze=pair_inputs['parameter_freeze'];f=json.loads(freeze.read_text())
    f['input_sha256'][scoring.MACRO_REFERENCE]=source.digest(pair_inputs['macro_path'])
    dump(freeze,f)
    inventory=pair_inputs['input_inventory'];inv=json.loads(inventory.read_text())
    inv['recorded_selection']['sha256']=source.digest(freeze);dump(inventory,inv)
    recorded=tmp_path/'recorded.json'
    dump(recorded,dict(evaluation_start='2024-01-01',evaluation_end='2025-09-01',
        parameter_freeze_sha256=source.digest(freeze),selected_parameters=f['selected'],input_sha256=f['input_sha256']))
    pair_args={k:v for k,v in pair_inputs.items() if k!='output'}
    score_args=dict(root=root,macro=pair_inputs['macro_path'],parameter_freeze=freeze,recorded_result=recorded)
    pipeline=tmp_path/'pipeline.json'
    def command(args):
        return ['python','-u','unused.py']+[item for key,value in args.items() for item in ('--'+key.replace('_','-'),str(value))]
    dump(pipeline,dict(frozen_sha256={},stages=[
        dict(name='paired-simulation',command=command(pair_args)),dict(name='scoring',command=command(score_args))]))
    result=stage.run(pipeline=pipeline,output=tmp_path/'matrix')
    assert result['status']=='complete'
    assert result['acceptance']['scenario_count']==40
    assert result['acceptance']['validated_output_count']==84
    assert len(result['scenarios'])==40
