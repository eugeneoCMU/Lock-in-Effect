"""Source-scoped borrower checks; do not assert absent lender valuation theorems.

Dunn–Spatt2005 pp603,606,608,611. The implementation's nominal rate differs
from the paper's coupon-payment parameter and its J is not marketed-loan V.
"""
import numpy as np
import pytest
from hazard.dynamic_refinancing import solve_dynamic_refinancing

RATES=np.array([.02,.06,.10])
P=np.array([[.7,.25,.05],[.15,.7,.15],[.05,.25,.7]])

def solve(c=.08,n=24,k=.005):
    return solve_dynamic_refinancing(initial_coupon=c,market_rates=RATES,transition_matrix=P,remaining_months=n,discount_rate=.04,cost_fraction=k)

@pytest.mark.parametrize('k',[0.,.001,.02])
def test_discrete_borrower_branch_ceiling_and_exercise_matching(k):
    s=solve(k=k)
    for n in range(1,25):
        quote=np.searchsorted(s.coupons,RATES)
        replacement=s.normalized_values[n,quote,np.arange(3)]
        ceiling=k+replacement
        assert np.all(s.normalized_values[n]<=ceiling[None,:]+s.tie_tolerance+1e-14)
        exercised=s.refinance[n]
        expected=np.broadcast_to(ceiling,s.normalized_values[n].shape)
        np.testing.assert_allclose(s.normalized_values[n][exercised],expected[exercised],rtol=0,atol=1e-14)

@pytest.mark.parametrize('n',[6,24,120])
def test_same_state_coupon_exercise_nesting_and_common_plateau(n):
    coupons=[0.,.02,.04,.06,.08,.10,.12];solutions=[solve(c=c,n=n) for c in coupons]
    values=np.array([[s.value(200000,market_state=x) for x in range(3)] for s in solutions])
    exercised=np.array([[s.refinance[n,np.searchsorted(s.coupons,c),x] for x in range(3)] for c,s in zip(coupons,solutions)])
    assert (np.diff(values,axis=0)>=-1e-7).all()
    assert (np.diff(exercised.astype(int),axis=0)>=0).all()
    for x in range(3):
        picked=values[exercised[:,x],x]
        if len(picked)>1:assert np.ptp(picked)<1e-7
        for c,s in zip(coupons,solutions):
            if RATES[x]>=c:assert not s.refinance[n,np.searchsorted(s.coupons,c),x]

def test_same_quote_tie_waits_instead_of_double_charging():
    s=solve_dynamic_refinancing(initial_coupon=.06,market_rates=[.06],transition_matrix=[[1]],remaining_months=12,discount_rate=.04,cost_fraction=0.)
    assert not s.refinance.any()

def test_payment_concavity_is_not_nominal_rate_concavity():
    # Independent two-payment algebra, no refinance and zero discount.
    costs=[]
    for annual in [0.,.06,.12]:
        s=solve_dynamic_refinancing(initial_coupon=annual,market_rates=[.20],transition_matrix=[[1]],remaining_months=2,discount_rate=0.,cost_fraction=.005)
        got=s.value(1.,market_state=0);m=annual/12
        assert got==pytest.approx(2*(m+1/(m+2)),abs=1e-13)
        costs.append(got)
    assert costs[1]<(costs[0]+costs[2])/2-1e-7
    # This does not violate source Proposition5: its linear coupon-payment
    # hypothesis is absent when the API instead changes an annuity's rate.
