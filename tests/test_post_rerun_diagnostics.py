import numpy as np
import pandas as pd
import pytest
from hazard.post_rerun_diagnostics import infer_floor, check_common_groups, bridge_samples


def test_zero_variance_floor_does_not_manufacture_interval():
    d=pd.DataFrame({'stratum':['a','b','c'],'prepaid_upb':[1.,2.,3.],'exposure_upb':[100.,200.,300.]})
    r=infer_floor(d, draws=99, n_grid=21)
    assert r['computable'] is False
    assert r['point_cpr_pct']==pytest.approx(100*(1-.99**12))


def test_null_inversion_contains_point_and_is_reproducible():
    d=pd.DataFrame({'stratum':list('abcdef'),'prepaid_upb':[1.,2.,1.,3.,2.,4.],'exposure_upb':[100.]*6})
    a=infer_floor(d,draws=199,n_grid=41)
    assert a==infer_floor(d,draws=199,n_grid=41)
    assert a['computable'] and a['smm_ci95'][0]<=a['point_smm']<=a['smm_ci95'][1]
    assert a['weights_reused_across_grid'] and a['draws']==199


def test_changed_observed_group_is_rejected():
    a={'a':{'n':2,'observed_b':3.,'exposure_b_months':20.}}
    check_common_groups([a,a])
    with pytest.raises(ValueError,match='support'):check_common_groups([a,{'a':dict(a['a'],observed_b=4.)}])


def test_history_ablation_keeps_known_term_and_does_not_mutate_sources():
    import polars as pl
    old=pl.DataFrame({'loan_id':['x'],'balance':[10.]})
    new=pl.DataFrame({'loan_id':['y'],'balance':[9.],'original_loan_term':[360.], 'initial_burnout':[.3],'burnout_denominator_multiplier':[2.]})
    stages=bridge_samples(old,new)
    assert 'original_loan_term' not in stages[0].columns
    assert stages[1]['original_loan_term'].to_list()==[360.]
    assert 'initial_burnout' not in stages[1].columns
    assert stages[2]['initial_burnout'].to_list()==[.3]
    assert new['initial_burnout'].to_list()==[.3]


def test_primary_floor_selects_inherited_depth_age_year_and_strata():
    from hazard.post_rerun_diagnostics import select_floor
    d=pd.DataFrame({'vintage':[2017]*3,'coupon':[.03]*3,'fico_bucket':['740+']*3,'ltv_bucket':['low']*3,
        'reporting_period':['201801','201802','201901'],'mean_loan_age':[12,11,24],'exposure_upb':[100]*3,'prepaid_upb':[1]*3})
    r=select_floor(d,{'201801':.04,'201802':.04,'201901':.04})
    assert r.reporting_period.to_list()==['201801']
    assert r.stratum.to_list()==['2017_300_740+_low']


def test_zero_transition_rows_allowed_only_in_archived_replay():
    from hazard.post_rerun_diagnostics import validate_bridge_matrix
    m=pd.DataFrame([[1.,0.],[0.,0.]],index=['a','b'],columns=['a','b'])
    validate_bridge_matrix(m,legacy=True)
    with pytest.raises(ValueError,match='transition'):validate_bridge_matrix(m,legacy=False)
    with pytest.raises(ValueError,match='transition'):validate_bridge_matrix(m*2,legacy=True)


def test_sample_audit_uses_actual_polars_numeric_arrays():
    import polars as pl
    from hazard.post_rerun_diagnostics import sample_summary
    d=pl.DataFrame({'loan_id':['a','b'],'balance':[100.,300.],'weight':[1.,1.],'coupon':[.02,.06],'loan_age':[10.,30.]})
    r=sample_summary(d)
    assert r['balance_weighted_coupon']==pytest.approx(.05)
    assert r['balance_weighted_age']==pytest.approx(25.)
    assert r['original_term_observed'] is False

from test_simulate_freddie_rebuild import pair_inputs, floor_inputs


def test_actual_engine_floor_changes_both_legs_and_restores_benchmark(pair_inputs,tmp_path):
    import polars as pl
    from hazard.post_rerun_diagnostics import run_pair_data,pair
    loans=pl.read_parquet(pair_inputs['root']/'combined/loan_sample.parquet')
    matrix=pd.read_parquet(pair_inputs['root']/'combined/markov_transition_matrix.parquet')
    macro=pd.read_parquet(pair_inputs['macro_path']);before=pair.PARAMETERS['annual_floor']
    low=run_pair_data(loans,matrix,macro,tmp_path/'low',floor=.02)
    high=run_pair_data(loans,matrix,macro,tmp_path/'high',floor=.10)
    assert low['legs']['off']['cash_principal_b']!=pytest.approx(high['legs']['off']['cash_principal_b'])
    assert low['reported_marginal_b']>high['reported_marginal_b']+1e-6
    assert pair.PARAMETERS['annual_floor']==before
