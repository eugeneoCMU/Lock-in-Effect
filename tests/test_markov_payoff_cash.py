"""A Markov full-payoff transition closes debt and records cash once."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import polars as pl
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'hazard'))
from agents import MicrosimPool, CODE_TO_STATE
import competing_risks as production
from hazard.mortgage_credit_ledger import observe_pool_month, current_microsim_principal_flows


@pytest.mark.parametrize('state', ['D30', 'Forbearance'])
@pytest.mark.parametrize('mode', ['fractional', 'absorbing'])
def test_markov_payoff_closes_remaining_debt_and_records_cash_once(monkeypatch, state, mode):
    df = pl.DataFrame({'loan_id':['synthetic'], 'stratum_id':['s0'],
        'fico':[720.], 'property_state':['PA'], 'orig_ltv':[80.], 'coupon':[3.],
        'orig_upb':[100000.], 'balance':[100000.], 'loan_age':[36], 'state':[state]})
    pool = MicrosimPool(df, rng=np.random.default_rng(7))
    monkeypatch.setattr(production, 'PREPAY_MODE', mode)
    hazard = .1 if mode == 'fractional' else 0.
    monkeypatch.setattr(production, 'prepay_hazard', lambda age,*a,**kw:np.full(len(age),hazard))
    monkeypatch.setattr(production, 'default_hazard', lambda stress,*a:np.zeros(len(stress)))
    trans = pd.DataFrame([[0.,1.],[0.,1.]],index=[state,'Prepaid'],columns=[state,'Prepaid'])
    result = production.monthly_step(pool, .07, trans=trans)
    assert pool.balance[0] == 0
    assert CODE_TO_STATE[int(pool.state_code[0])] == 'Prepaid'
    assert result['prepay_upb'] == pytest.approx(100000.)
    assert result['settled_b'] == result['prepay_upb']
    assert result['sched_amt'] == 0
    assert result['prepay_count'] == 1
    assert pool.cohort_burnout[0] == pytest.approx(1.)
    assert not pool.active_mask[0]
    following = observe_pool_month(pool, production.monthly_step, .07, trans=trans,
        code_to_state=CODE_TO_STATE, flow_reader=current_microsim_principal_flows)
    assert following.ledger.cash_principal == 0
    assert following.ledger.after.full_book_principal == 0
