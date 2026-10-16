"""Regression cases for the October 10 scientific implementation repairs."""
import os
import sys
from pathlib import Path
os.environ.setdefault('FRED_API_KEY', 'test-no-network')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'hazard'))
import numpy as np
import pandas as pd
import polars as pl
import pytest
from agents import MicrosimPool, STATE_TO_CODE
import competing_risks as cr
from config import MARKOV_STATES


def pool(age=36, term=360, state='Current', history=False):
    d={'loan_id':['a'], 'stratum_id':['s'], 'fico':[720.], 'property_state':['PA'],
       'orig_ltv':[80.], 'coupon':[.03], 'orig_upb':[100000.], 'balance':[80000.],
       'loan_age':[age], 'state':[state], 'original_loan_term':[term]}
    if history:
        d.update(initial_burnout=[.25], burnout_denominator_multiplier=[2.])
    return MicrosimPool(pl.DataFrame(d), rng=np.random.default_rng(0))


def matrix():
    return pd.DataFrame(np.eye(len(MARKOV_STATES)), index=MARKOV_STATES, columns=MARKOV_STATES)


def hazards_off(monkeypatch):
    monkeypatch.setattr(cr, 'prepay_hazard', lambda ages,*a,**k:np.zeros(len(ages)))
    monkeypatch.setattr(cr, 'default_hazard', lambda stress,*a,**k:np.zeros(len(stress)))


def test_markov_payoff_closes_cash_and_history_once(monkeypatch):
    hazards_off(monkeypatch); p=pool(state='D30'); t=matrix();t.loc['D30',:]=0;t.loc['D30','Prepaid']=1
    r=cr.monthly_step(p,.07,trans=t)
    assert r['prepay_upb']==r['settled_b']==80000.
    assert p.balance[0]==0 and not p.active_mask[0]
    assert p.cohort_burnout[0]==pytest.approx(.8)
    assert cr.monthly_step(p,.07,trans=t)['settled_b']==0


def test_transition_columns_can_be_reordered(monkeypatch):
    hazards_off(monkeypatch); p=pool(state='D30');t=matrix();t.loc['D30',:]=0;t.loc['D30','Prepaid']=1
    r=cr.monthly_step(p,.07,trans=t.loc[:,list(reversed(t.columns))])
    assert r['settled_b']==80000.


def test_new_delinquency_waits_until_next_month(monkeypatch):
    hazards_off(monkeypatch);monkeypatch.setattr(cr,'default_hazard',lambda x,*a,**k:np.ones(len(x)))
    p=pool();t=matrix();t.loc['D30',:]=0;t.loc['D30','Prepaid']=1
    r=cr.monthly_step(p,.07,trans=t)
    assert p.state_code[0]==STATE_TO_CODE['D30'] and r['settled_b']==0


@pytest.mark.parametrize('age',[179,180,181])
def test_maturity_settles_principal_without_voluntary_burnout(monkeypatch,age):
    hazards_off(monkeypatch);p=pool(age=age,term=180)
    r=cr.monthly_step(p,.07,trans=matrix())
    assert r['sched_amt']==pytest.approx(80000.)
    assert r['prepay_upb']==0 and p.balance[0]==pytest.approx(0.)
    assert p.cohort_burnout[0]==0


@pytest.mark.parametrize('term',[0,-1,180.5,float('nan')])
def test_invalid_known_term_rejected(term):
    with pytest.raises(ValueError,match='term'): pool(term=term)


def test_pool_initializes_historical_share_and_fixed_denominator():
    p=pool(history=True)
    assert p.cohort_burnout[0]==.25
    assert p.stratum_orig_upb[0]==200000.
    p.scale_to_holdings(.001)
    assert p.cohort_burnout[0]==.25
    assert p.stratum_orig_upb[0]==pytest.approx(2500000.)


def test_fixed_burnout_retains_original_cohort_after_payoff(monkeypatch,tmp_path):
    from hazard import ingest
    o=pl.DataFrame({'loan_sequence_number':['a','b'],'vintage':[2020]*2,'coupon':[.03]*2,
       'fico_bucket':['high']*2,'ltv_bucket':['low']*2,'original_upb':[100.,100.]})
    p=pl.DataFrame({'loan_sequence_number':['a','a','b','b','b'],
       'reporting_period':['202301','202302','202301','202302','202303'],
       'current_upb':[100.,0.,100.,90.,80.], 'is_prepay':[False,True,False,False,False],
       'loan_age':[1.,2.,1.,2.,3.], 'servicer_state':['Current','Prepaid','Current','Current','Current']})
    monkeypatch.setattr(ingest,'_scan_orig',lambda _:o.lazy());monkeypatch.setattr(ingest,'_scan_perf',lambda _:p.lazy())
    out=ingest.build_panel_from_files([(tmp_path/'o',tmp_path/'p')],tmp_path/'out.parquet')
    assert out.filter(pl.col('reporting_period')=='202303')['burnout'].item()==.5
    assert out['cohort_original_upb'].unique().to_list()==[200.]


def test_prediction_rejects_legacy_history_in_corrected_mode():
    from hazard.cohort_history import prediction_initial_state
    pre=pd.DataFrame({'exposure_upb':[80.],'orig_upb_sum':[100.],'burnout':[2.]},index=['a'])
    with pytest.raises(ValueError,match='fixed|cohort_original'): prediction_initial_state(pre)


def test_loan_transition_counts_ignore_gap_and_future_outcomes():
    from hazard.markov import estimate_transitions_from_loans
    d=pd.DataFrame({'loan_sequence_number':['a']*4,'reporting_period':['202301','202302','202304','202510'],
       'current_upb':[100.,90.,80.,'DO NOT PARSE'], 'servicer_state':['Current','D30','D60','DO NOT PARSE']})
    t,diag=estimate_transitions_from_loans(d,estimation_end='202509')
    assert t.loc['Current','D30']==1 and t.loc['D30','D30']==1
    assert diag['contiguous_pairs']==1 and diag['gap_pairs_excluded']==1


def test_cohort_proxy_requires_explicit_legacy_opt_in():
    from hazard.markov import estimate_transitions_from_panel
    with pytest.raises(ValueError,match='loan|legacy'): estimate_transitions_from_panel(pl.DataFrame())
