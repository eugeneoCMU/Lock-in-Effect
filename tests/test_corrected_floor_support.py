"""Independent denominator, support and sealed-scenario behavior checks."""
import importlib
from itertools import product
import numpy as np
import pandas as pd
import pytest


def module():
    spec = importlib.util.find_spec('hazard.corrected_floor_support')
    assert spec is not None, 'corrected floor support implementation missing'
    return importlib.import_module('hazard.corrected_floor_support')


def panel():
    return pd.DataFrame(dict(vintage=[2017]*3, coupon=[.03]*3,
        fico_bucket=['740+']*3, ltv_bucket=['≤80']*3,
        reporting_period=['201901','201902','201903'], mean_loan_age=[24.,25.,np.nan],
        exposure_upb=[80.,50.,40.], prepaid_upb=[20.,10.,3.], loan_count=[8,5,4],
        finite_age_count=[8,5,0], adjacent_opening_upb=[60.,80.,50.],
        first_observed_opening_upb=[30.,0.,0.],gap_opening_upb=[10.,0.,0.],
        first_observed_payoff_upb=[6.,0.,0.],gap_payoff_upb=[4.,0.,0.],
        first_observed_payoff_count=[1,0,0],gap_payoff_count=[1,0,0]))


def test_adjacent_ratio_uses_matched_source_numerator_and_not_end_or_lag_exposure():
    m=module(); d=m.prepare_support(panel(), {'201901':.04,'201902':.04,'201903':.04})
    r=m.summarize_cell(d,year=2019,min_age=24,max_gap_bp=-25)
    assert r['rows']==2 and r['strata']==1 and r['months']==2
    assert r['loan_count_months']==13
    assert r['end_exposure_upb']==130 and r['end_payoff_upb']==30
    assert r['end_smm']==pytest.approx(30/130)
    assert r['adjacent_opening_upb']==140 and r['adjacent_payoff_upb']==20
    assert r['adjacent_smm']==pytest.approx(20/140)
    assert r['excluded_first_payoff_upb']==6 and r['excluded_gap_payoff_upb']==4
    assert r['missing_mean_age_rows']==1


def test_no_support_is_explicit_and_grid_keeps_empty_cells():
    m=module();d=m.prepare_support(panel(),{'201901':.04,'201902':.04,'201903':.04})
    g=m.support_grid(d)
    assert len(g)==100
    row=next(r for r in g if (r['year'],r['min_age_months'],r['max_gap_bp'])==(2018,60,-200))
    assert row['status']=='no_support' and row['end_smm'] is None and row['adjacent_smm'] is None
    assert row['expected_months']==12
    assert next(r for r in g if r['year']==2025)['expected_months']==9


def test_zero_adjacent_exposure_cannot_borrow_all_payoffs():
    m=module();p=panel().iloc[:1].copy();p['adjacent_opening_upb']=0
    p['first_observed_payoff_upb']=16;p['gap_payoff_upb']=4
    d=m.prepare_support(p,{'201901':.04});r=m.summarize_cell(d,year=2019,min_age=24,max_gap_bp=-25)
    assert r['end_smm']==.25 and r['adjacent_smm'] is None and r['adjacent_rows']==0


def test_invalid_adjacent_numerator_duplicate_rows_and_missing_rates_fail_closed():
    m=module();p=panel();p.loc[0,'first_observed_payoff_upb']=30
    with pytest.raises(ValueError,match='payoff'):m.prepare_support(p,{'201901':.04,'201902':.04,'201903':.04})
    with pytest.raises(ValueError,match='Duplicate'):m.prepare_support(pd.concat([panel(),panel()]),{})
    with pytest.raises(ValueError,match='rate'):m.prepare_support(panel(),{'201901':.04})


def test_mean_age_not_imputed_from_vintage_and_2025_ends_in_september():
    m=module();p=panel();p.loc[2,'mean_loan_age']=60;p.loc[2,'reporting_period']='202510';p.loc[2,'finite_age_count']=4
    d=m.prepare_support(p,{'201901':.04,'201902':.04,'202510':.04})
    assert m.summarize_cell(d,year=2019,min_age=36,max_gap_bp=-25)['rows']==0
    assert m.summarize_cell(d,year=2025,min_age=12,max_gap_bp=0)['rows']==0


def test_sparse_designated_inference_guard():
    m=module();d=m.prepare_support(panel(),{'201901':.04,'201902':.04,'201903':.04})
    r=m.designated_inference(d)
    assert r['status']=='insufficient_support' and r['strata']==1 and r['months']==2
    assert r['stratum'] is None and r['month'] is None


def scenarios():
    return [dict(scenario=f's{i}',reference_mode=r,calibration=c,gap_mode=g,sensitive_share=s,
        reported_marginal_b=0 if s==0 and g=='positive_only' else 2*s+1,
        closed_pool_cash_marginal_b=0 if s==0 and g=='positive_only' else 3*s+1)
        for i,(r,c,g,s) in enumerate(product(('inherited_psa','matched_max_off'),
            ('legacy_conversion','illustrative'),('positive_only','preserve_refinancing'),(0.,.25,.5,.75,1.)))]


def test_matrix_completeness_and_zero_share_refinancing_is_distinguished():
    m=module();s=scenarios();r=m.structural_envelope(s)
    assert r['scenario_count']==40
    assert r['reported_marginal_b']['min']==0 and r['reported_marginal_b']['max']==3
    assert r['closed_pool_cash_marginal_b']['max']==4
    assert len(r['zero_share_identity_modes'])==8
    assert all(x['identity_required']==(x['gap_mode']=='positive_only') for x in r['zero_share_identity_modes'])
    with pytest.raises(ValueError,match='40'):m.structural_envelope(s[:-1])
    s[-1]=s[0]
    with pytest.raises(ValueError,match='40'):m.structural_envelope(s)


def test_designated_inference_runs_both_real_cluster_layers_after_support_gate():
    m=module(); rows=[]
    for i in range(10):
        for month in range(1,7):
            row=panel().iloc[0].to_dict()
            row.update(vintage=2000+i,reporting_period=f'2019{month:02}',
                prepaid_upb=1.+i*.1+month*.03,exposure_upb=100.,
                adjacent_opening_upb=100.,first_observed_payoff_upb=0.,gap_payoff_upb=0.)
            rows.append(row)
    d=m.prepare_support(pd.DataFrame(rows),{f'2019{month:02}':.04 for month in range(1,7)})
    r=m.designated_inference(d,draws=101,n_grid=31)
    assert r['status']=='computed' and r['stratum']['n_clusters']==10 and r['month']['n_clusters']==6
    assert r['stratum']['point_smm']==pytest.approx(.01555)
    assert r['month']['point_smm']==pytest.approx(.01555)


def test_denominator_support_statuses_distinguish_zero_end_from_positive_adjacent():
    m=module();p=panel().iloc[:1].copy();p['exposure_upb']=0.
    d=m.prepare_support(p,{'201901':.04})
    r=m.summarize_cell(d,year=2019,min_age=24,max_gap_bp=-25)
    assert r['end_status']=='no_support' and r['adjacent_status']=='supported'
    assert r['end_smm'] is None and r['adjacent_smm']==pytest.approx(10/60)
    assert r['end_missing_months']==[f'2019{n:02}' for n in range(1,13)]
    assert r['adjacent_missing_months']==[f'2019{n:02}' for n in range(2,13)]


@pytest.mark.parametrize('mutation',['unaccepted','changed_output','summary_pair','summary_score'])
def test_sealed_matrix_rejects_bad_acceptance_hashes_and_summary_links(tmp_path,mutation):
    import json
    import runpy
    from pathlib import Path
    helpers=runpy.run_path(str(Path(__file__).with_name('test_comparison_acceptance.py')))
    root,s=helpers['matrix'].__wrapped__(tmp_path)
    for scenario in s:
        label=scenario['scenario']
        p=json.loads((root/(label+'-pair')/'results.json').read_text())
        score=json.loads((root/(label+'-scoring')/'results.json').read_text())
        scenario.update(reported_marginal_b=p['reported_marginal_b'],
            closed_pool_cash_marginal_b=p['closed_pool_cash_marginal_b'],
            retrospective_scores=score['aggregate'],support=score['support'])
    receipt=helpers['validate'](root,s)
    top=dict(status='complete',acceptance=receipt,scenarios=s)
    helpers['dump'](root/'acceptance.json',receipt)
    helpers['dump'](root/'results.json',top)
    if mutation=='unaccepted':
        receipt['status']='failed';helpers['dump'](root/'acceptance.json',receipt)
    elif mutation=='changed_output':
        with (root/(s[0]['scenario']+'-scoring')/'predictions.parquet').open('ab') as stream:stream.write(b'changed')
    elif mutation=='summary_pair':
        top['scenarios'][0]['reported_marginal_b']=123.;helpers['dump'](root/'results.json',top)
    else:
        top['scenarios'][0]['retrospective_scores']['mixture_on']['predicted_b']=456.
        helpers['dump'](root/'results.json',top)
    with pytest.raises(ValueError):module().validate_matrix(root)
