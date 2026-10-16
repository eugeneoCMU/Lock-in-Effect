"""Component balances follow the real competing-risks loop under an explicit rule."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import polars as pl
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'hazard'))
from agents import MicrosimPool,CODE_TO_STATE
import competing_risks as production
from hazard.observed_payment_path import ObservedPaymentState,PAYMENT_RULE
from hazard.mortgage_credit_ledger import observe_pool_month,current_microsim_principal_flows
from hazard.microsim_ledger_audit import audit_microsim_regime
from microsim_engine import _simulate_regime


def loans(state='Current',months=2):
    return pl.DataFrame({'loan_id':['a'],'stratum_id':['s'],'fico':[720.],
        'property_state':['PA'],'orig_ltv':[80.],'coupon':[.03],'orig_upb':[120.],
        'balance':[120.],'loan_age':[36],'state':[state],
        'interest_bearing_upb':[100.],'current_non_ib_upb':[20.],
        'current_note_rate':[0.],'remaining_months':[float(months)]})


def no_hazards(monkeypatch,h=.0):
    monkeypatch.setattr(production,'PREPAY_MODE','fractional')
    monkeypatch.setattr(production,'prepay_hazard',lambda age,*a,**kw:np.full(len(age),h))
    monkeypatch.setattr(production,'default_hazard',lambda stress,*a:np.zeros(len(stress)))


def step(p,s,t):
    return observe_pool_month(p,production.monthly_step,.07,trans=t,beta1=0.,payment_state=s,
        code_to_state=CODE_TO_STATE,flow_reader=current_microsim_principal_flows)


def test_fractional_prepayment_and_schedule_then_maturity_preserve_deferred(monkeypatch):
    no_hazards(monkeypatch,.1)
    p=MicrosimPool(loans());s=ObservedPaymentState(loans(),p,payment_rule=PAYMENT_RULE)
    t=pd.DataFrame([[1.]],index=['Current'],columns=['Current'])
    first=step(p,s,t)
    assert first.source_result['prepay_upb']==pytest.approx(12)
    assert first.source_result['sched_amt']==pytest.approx(45)
    assert s.interest_bearing[0]==pytest.approx(45)
    assert s.deferred[0]==pytest.approx(18)
    second=step(p,s,t)
    assert second.source_result['sched_amt']==pytest.approx(40.5)
    assert s.deferred[0]==pytest.approx(16.2)
    assert s.interest_bearing[0]==pytest.approx(0)
    third=step(p,s,t)
    assert third.source_result['sched_amt']==0
    assert s.deferred[0]==pytest.approx(14.58)
    assert s.summary()['deferred_maturity_cash'] is None
    assert all(abs(x.ledger.accounting_residual)<1e-8 for x in [first,second,third])


@pytest.mark.parametrize('target',['Prepaid','Defaulted'])
def test_markov_exit_clears_full_payoff_but_retains_default_components(monkeypatch,target):
    no_hazards(monkeypatch)
    f=loans('D30');p=MicrosimPool(f);s=ObservedPaymentState(f,p,payment_rule=PAYMENT_RULE)
    t=pd.DataFrame([[0.,1.],[0.,1.]],index=['D30',target],columns=['D30',target])
    first=step(p,s,t);following=step(p,s,t)
    if target=='Prepaid':
        assert first.source_result['prepay_upb']==120
        assert s.interest_bearing[0]==s.deferred[0]==0
    else:
        assert first.ledger.cash_principal==0
        assert s.interest_bearing[0]==100 and s.deferred[0]==20
    assert following.ledger.cash_principal==0


def test_components_follow_initial_holdings_scale(monkeypatch):
    no_hazards(monkeypatch)
    f=loans();p=MicrosimPool(f);p.scale_to_holdings(.0000012)
    s=ObservedPaymentState(f,p,payment_rule=PAYMENT_RULE)
    assert s.interest_bearing[0]==pytest.approx(1000)
    assert s.deferred[0]==pytest.approx(200)


@pytest.mark.parametrize('case',['missing_field','mismatch','wrong_rule','foreign_pool'])
def test_incomplete_or_misaligned_components_fail_closed(monkeypatch,case):
    no_hazards(monkeypatch);f=loans();p=MicrosimPool(f)
    if case=='missing_field':f=f.drop('current_note_rate')
    if case=='mismatch':f=f.with_columns(pl.lit(21.).alias('current_non_ib_upb'))
    with pytest.raises((ValueError,TypeError)):
        s=ObservedPaymentState(f,p,payment_rule='wrong' if case=='wrong_rule' else PAYMENT_RULE)
        if case=='foreign_pool':s.before_month(MicrosimPool(f))


def test_direct_and_observed_scenario_loops_agree(monkeypatch):
    no_hazards(monkeypatch,.1)
    macro=pd.DataFrame({'MORTGAGE30US':[7.]*4,'WSHOMCB':[.00012]*4},
        index=pd.date_range('2022-06-01',periods=4,freq='MS'))
    kwargs=dict(loan_df=loans(),macro=macro,regime='US',holdings_scale_b=.00000012,
        trans=pd.DataFrame([[1.]],index=['Current'],columns=['Current']),seed=42,beta1=0.,payment_rule=PAYMENT_RULE)
    actual=audit_microsim_regime(**kwargs)
    pd.testing.assert_frame_equal(actual.legacy_outputs,_simulate_regime(**kwargs),check_exact=True)
    assert len(actual.payment_component_history)==4
    assert actual.security_receipts_usd.isna().all()
