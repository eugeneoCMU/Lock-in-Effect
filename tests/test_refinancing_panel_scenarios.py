import numpy as np
import pytest
from hazard.refinancing_panel_scenarios import evaluate_contracts
from hazard.dynamic_refinancing_terms import solve_term_refinancing

@pytest.mark.parametrize('financing',['cash','financed'])
@pytest.mark.parametrize('matrix',[[[1.]],[[.7,.3],[.2,.8]]])
def test_batch_matches_each_contract(financing,matrix):
 rates=[[.04,.045]] if len(matrix)==1 else [[.04,.045],[.025,.03]]
 old=[.06,.05,.06];terms=[24,5,481]
 args=dict(offer_rates=rates,offer_terms=[180,360],transition_matrix=matrix,horizon_months=12,discount_rate=.03,cost_fraction=.01,financing=financing)
 out=evaluate_contracts(current_coupons=old,remaining_months=terms,**args)
 for i,(c,n) in enumerate(zip(old,terms)):
  single=solve_term_refinancing(initial_coupon=c,remaining_months=n,**args)
  for state in range(len(matrix)):
   assert out['normalized_value'][i,state]==pytest.approx(single.value(1,market_state=state),abs=1e-12)
   assert out['advantage_fraction'][i,state]==pytest.approx(single.incentive(market_state=state),abs=1e-12)
   ci=int(np.searchsorted(single.coupons,c));assert out['offer_index'][i,state]==single.actions[0,n,ci,state]

def test_invalid_contracts_and_shapes():
 base=dict(current_coupons=[.06],remaining_months=[12],offer_rates=[[.04]],offer_terms=[180],transition_matrix=[[1]],horizon_months=12,discount_rate=.03,cost_fraction=.01)
 for update in [dict(remaining_months=[0]),dict(remaining_months=[1.5]),dict(current_coupons=[]),dict(current_coupons=[float('nan')]),dict(transition_matrix=[[.5]]),dict(offer_terms=[-1]),dict(financing='x')]:
  with pytest.raises(ValueError):evaluate_contracts(**{**base,**update})

def test_row_order_invariance_and_larger_menu():
 args=dict(offer_rates=[[.04,.045]],offer_terms=[180,360],transition_matrix=[[1]],horizon_months=12,discount_rate=.03,cost_fraction=.01)
 a=evaluate_contracts(current_coupons=[.06,.05],remaining_months=[24,481],**args)
 b=evaluate_contracts(current_coupons=[.05,.06],remaining_months=[481,24],**args)
 for key in a:np.testing.assert_allclose(a[key],b[key][::-1],rtol=0,atol=0)
 restricted=evaluate_contracts(current_coupons=[.06,.05],remaining_months=[24,481],**{**args,'offer_rates':[[.045]],'offer_terms':[360]})
 assert np.all(a['normalized_value']<=restricted['normalized_value']+1e-12)

def test_higher_fee_cannot_reduce_optimal_cost():
 args=dict(current_coupons=[.06,.05],remaining_months=[24,481],offer_rates=[[.04,.045]],offer_terms=[180,360],transition_matrix=[[1]],horizon_months=12,discount_rate=.03)
 for financing in ['cash','financed']:
  low=evaluate_contracts(**args,financing=financing,cost_fraction=.01)
  high=evaluate_contracts(**args,financing=financing,cost_fraction=.03)
  assert np.all(high['normalized_value']>=low['normalized_value']-1e-12)
