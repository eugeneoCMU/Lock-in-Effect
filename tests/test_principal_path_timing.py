"""Event timing and a narrow zero-default production reproduction restriction."""
import math
from pathlib import Path
import sys
import pytest
from hazard.mortgage_principal_paths import principal_path, paired_principal_paths


def test_exit_first_and_schedule_first_change_attribution_but_reconcile():
    inputs=(100,[10,10],[{'sale':math.log(2)}]*2)
    a=principal_path(*inputs,cash_causes={'sale'},event_order='schedule_first')
    b=principal_path(*inputs,cash_causes={'sale'},event_order='exit_first')
    assert a.scheduled_principal==15 and a.cause_principal['sale']==65
    assert b.scheduled_principal==7.5 and b.cause_principal['sale']==72.5
    assert b.ending_balance==a.ending_balance==20
    assert b.designated_cash_principal==a.designated_cash_principal==80
    assert a.event_order=='schedule_first' and b.event_order=='exit_first'
    assert b.accounting_residual==pytest.approx(0,abs=1e-12)


def test_maturity_attribution_depends_on_the_explicit_timing_convention():
    a=principal_path(100,[100],[{'sale':math.log(2)}],cash_causes={'sale'})
    b=principal_path(100,[100],[{'sale':math.log(2)}],cash_causes={'sale'},event_order='exit_first')
    assert a.cause_principal['sale']==0 and a.scheduled_principal==100
    assert b.cause_principal['sale']==50 and b.scheduled_principal==50
    assert a.ending_balance==b.ending_balance==0
    assert a.designated_cash_principal==b.designated_cash_principal==100


@pytest.mark.parametrize('order',[None,True,'unknown','schedule-first'])
def test_unknown_timing_is_rejected(order):
    with pytest.raises(ValueError):
        principal_path(100,[0],[{'sale':0}],cash_causes=set(),event_order=order)


def test_paired_legs_share_the_explicit_timing_convention():
    p=paired_principal_paths(100,[10,10],[{'sale':.1}]*2,[{'sale':.2}]*2,cash_causes={'sale'},event_order='exit_first')
    assert p.first.event_order==p.second.event_order=='exit_first'
    assert p.accounting_residual==pytest.approx(0,abs=1e-12)


def test_timing_changes_cash_classification_when_non_cash_causes_compete():
    kwargs=dict(beginning_balance=100,contractual_principal=[10],intensity_path=[{'credit':math.log(2)}],cash_causes=set())
    a=principal_path(**kwargs,event_order='schedule_first')
    b=principal_path(**kwargs,event_order='exit_first')
    assert a.designated_cash_principal==10
    assert b.designated_cash_principal==5
    assert a.unclassified_removal_principal==45 and b.unclassified_removal_principal==50
    assert a.ending_balance==b.ending_balance==45


def test_exit_first_matches_production_fractional_zero_default_for_full_path(monkeypatch):
    import numpy as np
    import pandas as pd
    import polars as pl
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'hazard'))
    import competing_risks as production
    from agents import MicrosimPool
    from macro import scheduled_amortization_smm
    df=pl.DataFrame({'loan_id':['synthetic'],'stratum_id':['s0'],'fico':[720.0],
        'property_state':['PA'],'orig_ltv':[80.0],'coupon':[3.0],
        'orig_upb':[100000.0],'balance':[100000.0],'loan_age':[36],'state':['Current']})
    pool=MicrosimPool(df,regime='US',rng=np.random.default_rng(7))
    probabilities=([.02,.05,.01,0.0]*6)
    month={'i':0}
    monkeypatch.setattr(production,'PREPAY_MODE','fractional')
    monkeypatch.setattr(production,'prepay_hazard',lambda age,*a,**kw:np.full_like(age,probabilities[month['i']],dtype=float))
    monkeypatch.setattr(production,'default_hazard',lambda stress,*a:np.zeros_like(stress,dtype=float))
    trans=pd.DataFrame([[1.0]],index=['Current'],columns=['Current'])
    contract_balance=100000.0;schedule=[]
    for i in range(len(probabilities)):
        principal=contract_balance*scheduled_amortization_smm(float(pool.coupon[0]),production.TERM_MONTHS,36+i)
        schedule.append(principal);contract_balance-=principal
    path=principal_path(100000,schedule,[{'prepay':-math.log1p(-p)} for p in probabilities],cash_causes={'prepay'},event_order='exit_first')
    total_sched=0.;total_settled=0.
    for i,expected in enumerate(path.months):
        month['i']=i
        actual=production.monthly_step(pool,.07,trans=trans)
        assert actual['default_count']==0
        assert actual['prepay_upb']==pytest.approx(expected.cause_principal['prepay'],rel=1e-12,abs=1e-9)
        assert actual['sched_amt']==pytest.approx(expected.scheduled_principal,rel=1e-12,abs=1e-9)
        assert float(pool.balance.sum())==pytest.approx(expected.ending_balance,rel=1e-12,abs=1e-8)
        total_sched+=actual['sched_amt'];total_settled+=actual['settled_b']
    assert total_sched==pytest.approx(path.scheduled_principal)
    assert total_sched+total_settled==pytest.approx(path.designated_cash_principal)
