import numpy as np
import pytest
from hazard.refinancing_payment_constraints import evaluate_payment_constrained
from hazard.refinancing_panel_scenarios import evaluate_contracts

BASE=dict(current_coupons=[.06,.025],remaining_months=[300,360],offer_rates=[[.04,.045]],offer_terms=[180,360],transition_matrix=[[1]],horizon_months=12,discount_rate=.03,cost_fraction=.01,financing='cash')

def test_uncapped_exact_existing_solver_parity():
 a=evaluate_payment_constrained(**BASE,payment_multiplier=None);b=evaluate_contracts(**BASE)
 for key in b:np.testing.assert_allclose(a[key],b[key],rtol=0,atol=0)
 assert a['has_feasible_offer'].all()

def test_no_increase_blocks_shorter_term_and_flags_no_offer():
 r=evaluate_payment_constrained(**BASE,payment_multiplier=1.)
 assert r['offer_index'][0,0]!=0
 assert not r['has_feasible_offer'][1,0]
 assert np.isnan(r['advantage_fraction'][1,0]) and r['offer_index'][1,0]==-1

def test_nested_constraints_cannot_lower_optimal_cost():
 a=evaluate_payment_constrained(**BASE,payment_multiplier=1.)
 b=evaluate_payment_constrained(**BASE,payment_multiplier=1.1)
 c=evaluate_payment_constrained(**BASE,payment_multiplier=None)
 assert np.all(a['normalized_value']>=b['normalized_value']-1e-12)
 assert np.all(b['normalized_value']>=c['normalized_value']-1e-12)

def test_financed_fee_included_in_payment_rule():
 args={**BASE,'current_coupons':[.06],'remaining_months':[360],'offer_rates':[[.06]],'offer_terms':[360],'cost_fraction':.01}
 cash=evaluate_payment_constrained(**args,payment_multiplier=1.)
 financed=evaluate_payment_constrained(**{**args,'financing':'financed'},payment_multiplier=1.)
 assert cash['has_feasible_offer'][0,0] and not financed['has_feasible_offer'][0,0]

def test_invalid_multiplier_rejected():
 for v in [0,-1,True,float('nan')]:
  with pytest.raises(ValueError):evaluate_payment_constrained(**BASE,payment_multiplier=v)

@pytest.mark.parametrize('financing',['cash','financed'])
def test_independent_action_tree_applies_rule_at_every_decision(financing):
 matrix=[[.2,.4,.4],[0,1,0],[0,0,1]];rates=[[.04,.045],[.025,.03],[.055,.06]];terms=[3,7];fee=.001;cap=1.1;df=1/(1+.03/12)
 def pay(b,c,n):return b/n if c==0 else b*(c/12)/(1-(1+c/12)**-n)
 def recurse(b,c,n,state,t):
  if n==0:return 0.
  if t==3:return b
  incumbent=pay(b,c,n);alternatives=[]
  for a in [-1,0,1]:
   principal=b;coupon=c;months=n;cash=0.
   if a>=0:
    coupon=rates[state][a];months=terms[a]
    if financing=='cash':cash=b*fee
    else:principal+=b*fee
    if pay(principal,coupon,months)>cap*incumbent+1e-8:continue
   payment=pay(principal,coupon,months);closing=0 if months==1 else principal*(1+coupon/12)-payment
   continuation=sum(matrix[state][j]*recurse(closing,coupon,months-1,j,t+1) for j in range(3))
   alternatives.append(cash+df*(payment+continuation))
  return min(alternatives)
 out=evaluate_payment_constrained(current_coupons=[.06],remaining_months=[5],offer_rates=rates,offer_terms=terms,transition_matrix=matrix,horizon_months=3,discount_rate=.03,cost_fraction=fee,financing=financing,payment_multiplier=cap)
 assert out['normalized_value'][0,0]*100000==pytest.approx(recurse(100000,.06,5,0,0),abs=1e-6)

def test_uncertain_three_state_unconstrained_parity():
 args={**BASE,'offer_rates':[[.04,.045],[.035,.04],[.045,.05]],'transition_matrix':[[0,.5,.5],[0,1,0],[0,0,1]]}
 a=evaluate_payment_constrained(**args,payment_multiplier=None);b=evaluate_contracts(**args)
 for key in b:np.testing.assert_allclose(a[key],b[key],rtol=0,atol=0)
