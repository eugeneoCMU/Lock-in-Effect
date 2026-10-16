"""Borrower cash-cost DP with supplied term-specific offers and explicit horizon payoff.

This is a scenario solver, not a lender price, fitted exercise model or reconstruction
of historical offers. Annual nominal rates are decimals; monthly rate = annual/12.
At most one refinancing occurs at each month's start, before its scheduled payment.
Any principal remaining at the calendar horizon is repaid at that horizon.
"""
from dataclasses import dataclass
import math
import numpy as np


def _number(x,name):
    if isinstance(x,(bool,np.bool_)) or not np.isscalar(x):raise ValueError(name)
    try:x=float(x)
    except (ValueError,TypeError):raise ValueError(name)
    if not math.isfinite(x) or x<0:raise ValueError(name)
    return x


def _integer(x,name,minimum=0):
    if isinstance(x,(bool,np.bool_)) or not isinstance(x,(int,np.integer)) or x<minimum:raise ValueError(name)
    return int(x)


def _payment(coupon,n):
    rate=coupon/12.
    return 1./n if rate==0 else rate/(-math.expm1(-n*math.log1p(rate)))


@dataclass(frozen=True)
class TermRefinancingSolution:
    initial_coupon: float
    remaining_months: int
    horizon_months: int
    discount_rate: float
    cost_fraction: float
    financing: str
    offer_rates: np.ndarray
    offer_terms: tuple
    transition_matrix: np.ndarray
    coupons: np.ndarray
    values: np.ndarray
    actions: np.ndarray
    initial_wait: np.ndarray
    initial_refinance: np.ndarray

    def _state(self,state):
        s=_integer(state,'market_state')
        if s>=len(self.offer_rates):raise ValueError('market_state')
        return s

    def value(self,balance,*,market_state):
        b=_number(balance,'balance');s=self._state(market_state)
        ci=int(np.searchsorted(self.coupons,self.initial_coupon))
        result=b*float(self.values[0,self.remaining_months,ci,s])
        if not math.isfinite(result):raise ValueError('Dollar value overflow')
        return result

    def incentive(self,*,market_state):
        """Signed normalized wait minus best refinance cost, under this scenario."""
        s=self._state(market_state)
        return float(self.initial_wait[s]-self.initial_refinance[s])

    def trace(self,balance,*,market_states):
        b=_number(balance,'balance');states=[self._state(s) for s in market_states]
        if len(states)!=self.horizon_months:raise ValueError('One state per horizon month is required')
        if any(self.transition_matrix[a,c]<=0 for a,c in zip(states,states[1:])):raise ValueError('Impossible market path')
        coupon=self.initial_coupon;n=self.remaining_months;df=1./(1.+self.discount_rate/12.)
        total=0.;cash_fees=0.;financed_fees=0.;rows=[]
        for t,s in enumerate(states):
            if n==0 or b==0:break
            ci=int(np.searchsorted(self.coupons,coupon));action=int(self.actions[t,n,ci,s]);opening=b
            old_coupon=coupon;old_n=n;cash=0.;financed=0.;replacement=None
            if action>=0:
                fee=self.cost_fraction*b
                if self.financing=='cash':cash=fee;cash_fees+=fee
                else:financed=fee;financed_fees+=fee;b+=fee
                n=n if self.offer_terms[action]==0 else self.offer_terms[action]
                replacement=n;coupon=float(self.offer_rates[s,action])
            pay=b*_payment(coupon,n);closing=0. if n==1 else max(0.,b*(1.+coupon/12.)-pay)
            total+=df**t*cash+df**(t+1)*pay
            rows.append(dict(month=t,market_state=s,opening_balance=opening,prior_coupon=old_coupon,prior_remaining_months=old_n,refinanced=action>=0,offer_index=action,replacement_term_months=replacement,coupon=coupon,cash_cost=cash,financed_cost=financed,scheduled_payment=pay,closing_balance=closing))
            b=closing;n-=1
        total+=df**self.horizon_months*b
        if not math.isfinite(total):raise ValueError('Trace overflow')
        return dict(months=rows,discounted_cash_cost=total,total_cash_fees=cash_fees,total_financed_fees=financed_fees,terminal_payoff=b,ending_balance_after_settlement=0.)


def solve_term_refinancing(*,initial_coupon,remaining_months,offer_rates,offer_terms,
                           transition_matrix,horizon_months,discount_rate,cost_fraction,
                           financing='cash',tie_tolerance=1e-12):
    """Minimize scenario cash costs; term 0 retains remaining term, others reset it.

    Offers are a (market states, offer choices) annual nominal rate matrix.
    The calendar horizon never resets. Terminal costs equal outstanding principal.
    Ties with waiting select wait; ties across refinance offers use input order.
    Cost is a fraction of opening principal, paid now or added once to new debt.
    """
    initial_coupon=_number(initial_coupon,'initial_coupon');discount_rate=_number(discount_rate,'discount_rate')
    cost_fraction=_number(cost_fraction,'cost_fraction');tol=_number(tie_tolerance,'tie_tolerance')
    old_n=_integer(remaining_months,'remaining_months',1);horizon=_integer(horizon_months,'horizon_months',1)
    if financing not in ('cash','financed'):raise ValueError('financing')
    terms=tuple(_integer(t,'offer_term') for t in offer_terms)
    rates=np.array(offer_rates,dtype=float,copy=True);matrix=np.array(transition_matrix,dtype=float,copy=True)
    if rates.ndim!=2 or not rates.size or not terms or rates.shape[1]!=len(terms) or not np.isfinite(rates).all() or np.any(rates<0):raise ValueError('offer_rates')
    states=len(rates)
    if matrix.shape!=(states,states) or not np.isfinite(matrix).all() or np.any(matrix<0) or np.any(matrix>1) or not np.allclose(matrix.sum(axis=1),1,rtol=0,atol=1e-12):raise ValueError('transition_matrix')
    matrix/=matrix.sum(axis=1)[:,None]
    coupons=np.unique(np.append(rates.ravel(),initial_coupon));maximum=max(old_n,*terms)
    if (horizon+1)*(maximum+1)*len(coupons)*states>20_000_000:raise ValueError('State grid exceeds supported memory budget')
    shape=(horizon+1,maximum+1,len(coupons),states)
    values=np.zeros(shape);actions=np.full((horizon,maximum+1,len(coupons),states),-1,dtype=np.int32)
    values[horizon,1:]=1.
    payments=np.array([[_payment(c,n) for c in coupons] for n in range(1,maximum+1)])
    residual=np.maximum(1.+coupons[None,:]/12.-payments,0.);residual[0]=0.
    df=1./(1.+discount_rate/12.);quote_indices=np.searchsorted(coupons,rates);sidx=np.arange(states)
    ci=int(np.searchsorted(coupons,initial_coupon));wait0=refi0=None
    for t in range(horizon-1,-1,-1):
        expected=np.einsum('ncs,js->ncj',values[t+1,:maximum],matrix,optimize=False)
        waits=df*(payments[:,:,None]+residual[:,:,None]*expected)
        best=waits.copy();best_refi=np.full_like(waits,np.inf)
        for a,term in enumerate(terms):
            quoted=waits[:,quote_indices[:,a],sidx] if term==0 else waits[term-1,quote_indices[:,a],sidx][None,:]
            candidate=quoted[:,None,:]*(1.+cost_fraction if financing=='financed' else 1.)+(cost_fraction if financing=='cash' else 0.)
            candidate=np.broadcast_to(candidate,waits.shape)
            best_refi=np.minimum(best_refi,candidate)
            choose=candidate<best-tol
            best=np.where(choose,candidate,best);actions[t,1:]=np.where(choose,a,actions[t,1:])
        values[t,1:]=best
        if t==0:wait0=waits[old_n-1,ci].copy();refi0=best_refi[old_n-1,ci].copy()
    if not all(np.isfinite(a).all() for a in (values,wait0,refi0)):raise ValueError('Computed costs overflowed')
    for a in (rates,matrix,coupons,values,actions,wait0,refi0):a.setflags(write=False)
    return TermRefinancingSolution(initial_coupon,old_n,horizon,discount_rate,cost_fraction,financing,rates,terms,matrix,coupons,values,actions,wait0,refi0)
