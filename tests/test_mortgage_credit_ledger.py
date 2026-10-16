"""Debt stocks and explicitly supplied cash; no inferred recoveries."""
from pathlib import Path
import sys
import pytest
from hazard.mortgage_credit_ledger import (PrincipalFlows, credit_ledger_step, credit_ledger_path,
    observe_pool_month, current_microsim_principal_flows)


def flows(*,scheduled=0,voluntary=0,settlement=0,write_down=0,addition=0):
    return PrincipalFlows(scheduled,voluntary,settlement,write_down,addition)


def test_default_transfer_reduces_active_exposure_without_cash_or_debt_extinction():
    r=credit_ledger_step({'x':('Current',100)},{'x':('Defaulted',100)},flows())
    assert r.before.active_principal==100
    assert r.after.active_principal==0
    assert r.after.inactive_unsettled_principal==100
    assert r.after.full_book_principal==100
    assert r.active_to_inactive_principal==100
    assert r.cash_principal==0
    assert r.accounting_residual==0


def test_delinquent_balances_remain_active_in_source_convention():
    before={str(i):(state,10) for i,state in enumerate(['Current','D30','D60','D90+','Forbearance'])}
    r=credit_ledger_step(before,before,flows())
    assert r.before.active_principal==50
    assert r.after.inactive_unsettled_principal==0


def test_delayed_settlement_and_write_down_are_separate_explicit_flows():
    snapshots=[{'x':('Current',100)},{'x':('Defaulted',100)},{'x':('Defaulted',100)},{'x':('Liquidated',0)}]
    p=credit_ledger_path(snapshots,[flows(),flows(),flows(settlement=80,write_down=20)])
    assert [m.cash_principal for m in p.months]==[0,0,80]
    assert p.credit_settlement_principal==80
    assert p.write_down_principal==20
    assert p.ending_full_book_principal==0
    assert p.cash_principal==80
    assert p.accounting_residual==0


def test_active_to_inactive_transfer_is_measured_after_explicit_cash_reduction():
    r=credit_ledger_step({'x':('D30',100)},{'x':('Defaulted',90)},flows(voluntary=10))
    assert r.active_to_inactive_principal==90
    assert r.cash_principal==10
    assert r.after.full_book_principal==90


def test_explicit_addition_is_separate_from_cash_and_state_changes():
    r=credit_ledger_step({'x':('Forbearance',100)},{'x':('Defaulted',105)},flows(addition=5))
    assert r.added_principal==5 and r.cash_principal==0
    assert r.accounting_residual==0


def test_liquidated_state_does_not_imply_cash_or_zero_balance():
    r=credit_ledger_step({'x':('Defaulted',100)},{'x':('Liquidated',100)},flows())
    assert r.after.inactive_unsettled_principal==100
    assert r.cash_principal==0


def test_full_payoff_cash_is_not_double_counted_as_settlement():
    r=credit_ledger_step({'x':('Current',100)},{'x':('Prepaid',0)},flows(voluntary=100))
    assert r.cash_principal==100
    with pytest.raises(ValueError,match='reconcil'):
        credit_ledger_step({'x':('Current',100)},{'x':('Prepaid',0)},flows(voluntary=100,settlement=100))


@pytest.mark.parametrize('before,after,f',[
    ({'x':('Current',100)},{'x':('Defaulted',0)},flows()),
    ({'x':('Current',100)},{'x':('Current',105)},flows()),
    ({'x':('Current',100)},{},flows()),
    ({'x':('Current',100)},{'y':('Current',100)},flows()),
    ({'x':('unknown',100)},{'x':('unknown',100)},flows()),
    ({'x':('Prepaid',100)},{'x':('Prepaid',100)},flows()),
    ({'x':('Current',True)},{'x':('Current',1)},flows()),
    ({'x':('Current',float('nan'))},{'x':('Current',0)},flows()),
])
def test_invalid_or_unexplained_snapshots_fail_closed(before,after,f):
    with pytest.raises((ValueError,TypeError)):
        credit_ledger_step(before,after,f)


@pytest.mark.parametrize('bad',[True,-1,float('inf'),float('nan'),'10'])
def test_invalid_supplied_cash_is_rejected(bad):
    with pytest.raises((ValueError,TypeError)):
        credit_ledger_step({'x':('Current',100)},{'x':('Current',100)},flows(scheduled=bad))


def test_individual_unexplained_debt_transfer_is_not_hidden_by_pool_total():
    # Aggregates reconcile, but individual flows are not available. State that
    # limit instead of claiming loan-by-loan verification from pool cash totals.
    r=credit_ledger_step({'x':('Current',100),'y':('Current',100)},
        {'x':('Current',90),'y':('Current',110)},flows())
    assert r.reconciliation_scope=='pool_total_only'
    assert r.per_loan_cash_allocation_verified is False
    assert r.accounting_residual==0


def test_result_state_maps_are_immutable():
    r=credit_ledger_step({'x':('Current',100)},{'x':('Defaulted',100)},flows())
    with pytest.raises(TypeError):r.after.principal_by_state['Defaulted']=0


def test_path_length_and_continuity_require_complete_snapshots():
    with pytest.raises(ValueError):credit_ledger_path([{'x':('Current',100)}],[])
    with pytest.raises(ValueError):credit_ledger_path([{'x':('Current',100)}]*3,[flows()])
    with pytest.raises(ValueError):credit_ledger_path([{'x':('Current',100)},{'y':('Current',100)}],[flows()])


def test_production_default_then_inactive_month_has_no_cash_or_principal_reduction(monkeypatch):
    import numpy as np
    import pandas as pd
    import polars as pl
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'hazard'))
    import competing_risks as production
    from agents import MicrosimPool,CODE_TO_STATE
    df=pl.DataFrame({'loan_id':['synthetic'],'stratum_id':['s0'],'fico':[720.],
        'property_state':['PA'],'orig_ltv':[80.],'coupon':[3.],
        'orig_upb':[100000.],'balance':[100000.],'loan_age':[36],'state':['Current']})
    pool=MicrosimPool(df,regime='US',rng=np.random.default_rng(7))
    monkeypatch.setattr(production,'PREPAY_MODE','fractional')
    monkeypatch.setattr(production,'prepay_hazard',lambda age,*a,**kw:np.zeros_like(age,dtype=float))
    monkeypatch.setattr(production,'default_hazard',lambda stress,*a:np.ones_like(stress,dtype=float))
    trans=pd.DataFrame([[0.,1.],[0.,1.]],index=['D30','Defaulted'],columns=['D30','Defaulted'])
    snapshot=lambda:{str(key):(CODE_TO_STATE[int(state)],float(balance)) for key,state,balance in zip(pool.loan_ids,pool.state_code,pool.balance)}
    snaps=[snapshot()];records=[]
    for i in range(2):
        observed=observe_pool_month(pool,production.monthly_step,.07,trans=trans,
            code_to_state=CODE_TO_STATE,flow_reader=current_microsim_principal_flows)
        actual=observed.source_result
        assert observed.ledger.after.inactive_unsettled_principal==100000
        assert actual['settled_b']==actual['prepay_upb']==actual['sched_amt']==0
        snaps.append(snapshot());records.append(flows(scheduled=actual['sched_amt'],voluntary=actual['settled_b']))
    p=credit_ledger_path(snaps,records)
    assert p.months[0].after.active_principal==0
    assert p.months[0].after.inactive_unsettled_principal==100000
    assert p.months[1].after.inactive_unsettled_principal==100000
    assert p.cash_principal==0
    assert p.ending_full_book_principal==100000
    assert p.accounting_residual==0


def test_current_flow_reader_refuses_to_infer_a_new_credit_settlement():
    result={'sched_amt':10,'prepay_upb':20,'settled_b':25,'default_upb':0}
    with pytest.raises(ValueError):current_microsim_principal_flows(result)
    with pytest.raises(ValueError):current_microsim_principal_flows(dict(result,settled_b=20,default_upb=5))
    with pytest.raises(ValueError):current_microsim_principal_flows({'sched_amt':10})


def test_current_flow_reader_keeps_prepayment_cash_single_counted():
    f=current_microsim_principal_flows({'sched_amt':10,'prepay_upb':20,'settled_b':20,'default_upb':0})
    assert f==flows(scheduled=10,voluntary=20)


def test_source_taxonomy_matches_production_without_importing_it_into_ledger():
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'hazard'))
    from config import MARKOV_STATES
    from agents import ABSORBING_STATES
    from hazard.mortgage_credit_ledger import STATES,ACTIVE_STATES,INACTIVE_STATES
    assert set(STATES)==set(MARKOV_STATES)
    assert set(ACTIVE_STATES)==set(MARKOV_STATES)-set(ABSORBING_STATES)
    assert set(INACTIVE_STATES)==set(ABSORBING_STATES)-{'Prepaid'}


def test_observer_rejects_duplicate_source_ids_before_running_the_step():
    from types import SimpleNamespace
    pool=SimpleNamespace(loan_ids=['same','same'],state_code=[0,0],balance=[100,100])
    called=[]
    with pytest.raises(ValueError):
        observe_pool_month(pool,lambda:called.append(True),code_to_state={0:'Current'},flow_reader=current_microsim_principal_flows)
    assert called==[]


def test_observer_matches_unwrapped_production_with_credit_and_cash_together(monkeypatch):
    import numpy as np
    import pandas as pd
    import polars as pl
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'hazard'))
    import competing_risks as production
    from agents import MicrosimPool,CODE_TO_STATE
    df=pl.DataFrame({'loan_id':['synthetic-a','synthetic-b'],'stratum_id':['s0','s0'],
        'fico':[720.,730.],'property_state':['PA','PA'],'orig_ltv':[80.,80.],
        'coupon':[3.,3.],'orig_upb':[100000.,100000.],'balance':[100000.,100000.],
        'loan_age':[36,36],'state':['Current','Current']})
    pool=MicrosimPool(df,regime='US',rng=np.random.default_rng(7))
    reference=MicrosimPool(df,regime='US',rng=np.random.default_rng(7))
    monkeypatch.setattr(production,'PREPAY_MODE','fractional')
    monkeypatch.setattr(production,'prepay_hazard',lambda age,*a,**kw:np.full_like(age,.1,dtype=float))
    monkeypatch.setattr(production,'default_hazard',lambda stress,*a:np.array([1.,0.]))
    trans=pd.DataFrame([[0.,1.],[0.,1.]],index=['D30','Defaulted'],columns=['D30','Defaulted'])
    expected=production.monthly_step(reference,.07,trans=trans)
    actual=observe_pool_month(pool,production.monthly_step,.07,trans=trans,
        code_to_state=CODE_TO_STATE,flow_reader=current_microsim_principal_flows)
    assert actual.source_result==expected
    np.testing.assert_array_equal(pool.balance,reference.balance)
    np.testing.assert_array_equal(pool.state_code,reference.state_code)
    np.testing.assert_array_equal(pool.loan_age,reference.loan_age)
    np.testing.assert_array_equal(pool.cohort_burnout,reference.cohort_burnout)
    assert pool.rng.bit_generator.state==reference.rng.bit_generator.state
    assert expected['default_count']==1
    assert actual.ledger.after.inactive_unsettled_principal==pytest.approx(100000*(1-.1/1.1))
    assert actual.ledger.after.active_principal>0
    assert actual.ledger.cash_principal==expected['settled_b']+expected['sched_amt']
    assert actual.ledger.after.full_book_principal>actual.ledger.after.active_principal
    assert actual.ledger.accounting_residual==pytest.approx(0,abs=1e-8)


def test_observer_accepts_delayed_settlement_only_from_an_explicit_new_reader():
    from types import SimpleNamespace
    pool=SimpleNamespace(loan_ids=['synthetic'],state_code=[0],balance=[100])
    def settle(p):
        p.state_code=[1];p.balance=[0]
        return {'principal_cash':80,'principal_write_down':20}
    actual=observe_pool_month(pool,settle,code_to_state={0:'Defaulted',1:'Liquidated'},
        flow_reader=lambda r:flows(settlement=r['principal_cash'],write_down=r['principal_write_down']))
    assert actual.ledger.cash_principal==80
    assert actual.ledger.flows.write_down==20
    assert actual.ledger.after.full_book_principal==0


def test_observer_rejects_nonmapping_result_before_calling_the_flow_reader():
    from types import SimpleNamespace
    pool=SimpleNamespace(loan_ids=['synthetic'],state_code=[0],balance=[100])
    called=[]
    def reader(result):
        called.append(True)
        return flows()
    with pytest.raises(TypeError):
        observe_pool_month(pool,lambda p:[],code_to_state={0:'Current'},flow_reader=reader)
    assert called==[]
