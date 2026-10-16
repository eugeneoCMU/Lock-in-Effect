import importlib.util,sys
from pathlib import Path
import numpy as np
import pytest
from hazard.dynamic_refinancing_terms import solve_term_refinancing

def solve(**kw):
 args=dict(initial_coupon=.06,remaining_months=24,offer_rates=[[.04]],offer_terms=[0],transition_matrix=[[1.]],horizon_months=24,discount_rate=.03,cost_fraction=.01,financing='cash');args.update(kw);return solve_term_refinancing(**args)

def test_sealed_same_term_solver_parity():
 path=Path('/Users/eugene/.codex/worktrees/spatt-contracting-revision/Lock-in-Effect/hazard/dynamic_refinancing.py')
 if not path.exists():pytest.skip('Local sealed historical solver unavailable')
 spec=importlib.util.spec_from_file_location('sealed_dynamic',path);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
 old=module.solve_dynamic_refinancing(initial_coupon=.06,market_rates=[.04,.07],transition_matrix=[[.8,.2],[.3,.7]],remaining_months=24,discount_rate=.03,cost_fraction=.01)
 new=solve(offer_rates=[[.04],[.07]],transition_matrix=[[.8,.2],[.3,.7]])
 for state in range(2):assert new.value(100000,market_state=state)==pytest.approx(old.value(100000,market_state=state),abs=1e-6)

def test_no_benefit_tie_waits_and_trace_matches_value():
 s=solve(offer_rates=[[.06]],cost_fraction=0)
 tr=s.trace(100000,market_states=[0]*24)
 assert not any(r['refinanced'] for r in tr['months'])
 assert tr['discounted_cash_cost']==pytest.approx(s.value(100000,market_state=0))
 assert tr['terminal_payoff']==0

def test_extending_term_retains_horizon_debt():
 s=solve(offer_rates=[[0]],offer_terms=[360],horizon_months=12,discount_rate=.03,cost_fraction=0)
 tr=s.trace(100000,market_states=[0]*12)
 assert tr['months'][0]['replacement_term_months']==360
 assert tr['terminal_payoff']>90000
 assert tr['discounted_cash_cost']==pytest.approx(s.value(100000,market_state=0))

def test_zero_rate_financed_fee_cost_once():
 s=solve(initial_coupon=0,offer_rates=[[0]],offer_terms=[0],discount_rate=0,cost_fraction=.03,financing='financed')
 assert s.value(100000,market_state=0)==pytest.approx(100000)
 assert not s.trace(100000,market_states=[0]*24)['months'][0]['refinanced']

def test_wait_for_lower_future_quote():
 s=solve(offer_rates=[[.059],[0]],transition_matrix=[[0,1],[0,1]],cost_fraction=.01)
 tr=s.trace(100000,market_states=[0]+[1]*23)
 assert not tr['months'][0]['refinanced']
 assert tr['months'][1]['refinanced']
 assert tr['discounted_cash_cost']==pytest.approx(s.value(100000,market_state=0))

def test_added_offer_cannot_raise_optimal_cost():
 a=solve(offer_terms=[180]);b=solve(offer_rates=[[.04,.04]],offer_terms=[180,360])
 assert b.value(100000,market_state=0)<=a.value(100000,market_state=0)+1e-7

def test_stochastic_trace_expected_value():
 s=solve(remaining_months=2,horizon_months=2,offer_rates=[[.04],[.08]],transition_matrix=[[.25,.75],[.5,.5]],cost_fraction=.001)
 a=s.trace(100000,market_states=[0,0])['discounted_cash_cost'];b=s.trace(100000,market_states=[0,1])['discounted_cash_cost']
 assert .25*a+.75*b==pytest.approx(s.value(100000,market_state=0))

def test_reject_invalid_inputs_and_path():
 for kw in [dict(offer_rates=[[float('nan')]]),dict(offer_terms=[-1]),dict(transition_matrix=[[.5]]),dict(financing='x'),dict(horizon_months=0),dict(offer_terms=[1.5])]:
  with pytest.raises(ValueError):solve(**kw)
 with pytest.raises(ValueError):solve().trace(1,market_states=[0])

def test_financed_refinance_scales_principal_once_and_trace_reproduces_value():
 s=solve(offer_rates=[[0]],offer_terms=[360],cost_fraction=.01,financing='financed')
 tr=s.trace(100000,market_states=[0]*24)
 assert tr['months'][0]['refinanced']
 assert tr['months'][0]['financed_cost']==1000
 assert tr['months'][0]['scheduled_payment']*360==pytest.approx(101000)
 assert tr['total_cash_fees']==0
 assert tr['discounted_cash_cost']==pytest.approx(s.value(100000,market_state=0))

def test_fixed_horizon_no_offer_benefit_matches_independent_schedule():
 s=solve(offer_rates=[[.20]],horizon_months=12,cost_fraction=.1)
 b=100000.;r=.06/12;p=b*r/(1-(1+r)**-24);total=0.;d=1+.03/12
 for t in range(1,13):
  total+=p/d**t;b=b*(1+r)-p
 total+=b/d**12
 assert s.value(100000,market_state=0)==pytest.approx(total)
 assert s.trace(100000,market_states=[0]*12)['terminal_payoff']==pytest.approx(b)

def test_grid_budget_and_invalid_states():
 with pytest.raises(ValueError):solve(horizon_months=100000000)
 with pytest.raises(ValueError):solve().value(1,market_state=True)
 with pytest.raises(ValueError):solve().value(1,market_state=99)
 s=solve(offer_rates=[[.20]],discount_rate=0,cost_fraction=.1)
 with pytest.raises(ValueError):s.value(1.79e308,market_state=0)

def test_impossible_transition_path_rejected():
 s=solve(offer_rates=[[.04],[.03]],transition_matrix=[[0,1],[0,1]])
 with pytest.raises(ValueError):s.trace(1,market_states=[0]*24)

@pytest.mark.parametrize('financing',['cash','financed'])
def test_independent_brute_force_action_tree(financing):
 import math
 matrix=[[.7,.3],[.2,.8]];rates=[[.04,.035],[.025,.02]];terms=[0,7];fee=.001;df=1/(1+.03/12)
 def recurse(b,coupon,n,state,t):
  if n==0:return 0.
  if t==3:return b
  alternatives=[]
  for action in [-1,0,1]:
   principal=b;cash=0.;rate=coupon;term=n
   if action>=0:
    rate=rates[state][action];term=n if terms[action]==0 else terms[action]
    if financing=='cash':cash=b*fee
    else:principal+=b*fee
   r=rate/12;pay=principal/term if r==0 else principal*r/(1-(1+r)**(-term))
   closing=0 if term==1 else principal*(1+r)-pay
   continuation=sum(matrix[state][j]*recurse(closing,rate,term-1,j,t+1) for j in range(2))
   alternatives.append(cash+df*(pay+continuation))
  return min(alternatives)
 s=solve(initial_coupon=.06,remaining_months=5,offer_rates=rates,offer_terms=terms,transition_matrix=matrix,horizon_months=3,cost_fraction=fee,financing=financing)
 assert s.value(100000,market_state=0)==pytest.approx(recurse(100000,.06,5,0,0),abs=1e-6)
