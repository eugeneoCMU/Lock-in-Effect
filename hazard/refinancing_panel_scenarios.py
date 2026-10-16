"""Rolling-memory multi-contract evaluation of supplied refinancing scenarios.

Equivalent to dynamic_refinancing_terms for each queried contract. No inferred
eligibility, fitted offers, historical future rates or event probabilities.
"""
import numpy as np
from .dynamic_refinancing_terms import _number,_integer,_payment


def evaluate_contracts(*,current_coupons,remaining_months,offer_rates,offer_terms,
                       transition_matrix,horizon_months,discount_rate,cost_fraction,
                       financing='cash',tie_tolerance=1e-12):
    originals=np.array(current_coupons,dtype=float,copy=True)
    if originals.ndim!=1 or not originals.size or not np.isfinite(originals).all() or np.any(originals<0):raise ValueError('current_coupons')
    remaining=np.array([_integer(n,'remaining_months',1) for n in remaining_months],dtype=int)
    if remaining.shape!=originals.shape:raise ValueError('Contract lengths differ')
    terms=tuple(_integer(n,'offer_terms') for n in offer_terms)
    horizon=_integer(horizon_months,'horizon_months',1);discount=_number(discount_rate,'discount_rate');fee=_number(cost_fraction,'cost_fraction');tol=_number(tie_tolerance,'tie_tolerance')
    if financing not in ('cash','financed'):raise ValueError('financing')
    rates=np.array(offer_rates,dtype=float,copy=True);matrix=np.array(transition_matrix,dtype=float,copy=True)
    if rates.ndim!=2 or not rates.size or not terms or rates.shape[1]!=len(terms) or not np.isfinite(rates).all() or np.any(rates<0):raise ValueError('offer_rates')
    states=len(rates)
    if matrix.shape!=(states,states) or not np.isfinite(matrix).all() or np.any(matrix<0) or np.any(matrix>1) or not np.allclose(matrix.sum(axis=1),1,rtol=0,atol=1e-12):raise ValueError('transition_matrix')
    matrix/=matrix.sum(axis=1)[:,None]
    coupons=np.unique(np.concatenate([originals,rates.ravel()]));maximum=max(int(remaining.max()),*terms)
    if (maximum+1)*len(coupons)*states>2_000_000 or horizon>1200:raise ValueError('State grid exceeds supported budget')
    values=np.ones((maximum+1,len(coupons),states));values[0]=0
    payments=np.array([[_payment(c,n) for c in coupons] for n in range(1,maximum+1)])
    residual=np.maximum(1.+coupons[None,:]/12.-payments,0);residual[0]=0
    quote_indices=np.searchsorted(coupons,rates);sidx=np.arange(states);df=1/(1+discount/12.)
    for t in range(horizon-1,-1,-1):
        expected=np.einsum('ncs,js->ncj',values[:maximum],matrix,optimize=False)
        waits=df*(payments[:,:,None]+residual[:,:,None]*expected)
        best=waits.copy();refinance=np.full_like(best,np.inf);action=np.full(best.shape,-1,dtype=np.int32)
        for a,term in enumerate(terms):
            quoted=waits[:,quote_indices[:,a],sidx] if term==0 else waits[term-1,quote_indices[:,a],sidx][None,:]
            candidate=quoted[:,None,:]*(1+fee if financing=='financed' else 1)+(fee if financing=='cash' else 0)
            candidate=np.broadcast_to(candidate,waits.shape);refinance=np.minimum(refinance,candidate)
            choose=candidate<best-tol;best=np.where(choose,candidate,best);action=np.where(choose,a,action)
        values[1:]=best
    ci=np.searchsorted(coupons,originals);ni=remaining-1
    result=dict(normalized_value=best[ni,ci].copy(),advantage_fraction=(waits-refinance)[ni,ci].copy(),offer_index=action[ni,ci].copy())
    if not all(np.isfinite(v).all() for v in result.values()):raise ValueError('Computed costs overflowed')
    for v in result.values():v.setflags(write=False)
    return result
