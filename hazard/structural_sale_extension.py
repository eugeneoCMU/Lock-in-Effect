"""Exploratory sale/refinancing extension, never selected by the production engine.

All opportunity, gain-distribution, valuation and concession inputs are explicit
assumptions. This module neither estimates them nor solves a lender equilibrium.
"""
import numpy as np


def _nonnegative(*values):
    arrays=np.broadcast_arrays(*[np.asarray(v,dtype=float) for v in values])
    if any(not np.isfinite(a).all() or (a<0).any() for a in arrays):
        raise ValueError('Inputs must be finite and nonnegative')
    return arrays


def _annuity(rate,months):
    monthly=rate/12.
    with np.errstate(invalid='ignore',divide='ignore'):
        value=-np.expm1(-months*np.log1p(monthly))/monthly
    return np.where(monthly==0,months,value)


def scheduled_loan_value(balance,contract_rate,discount_rate,remaining_months):
    """USD PV of deterministic scheduled P&I; not an observed loan market value.

    Annual nominal rates are decimals. No prepayment/default option, servicing,
    credit spread or modification is priced. Remaining term is integer months.
    """
    balance,coupon,discount,n=_nonnegative(balance,contract_rate,discount_rate,remaining_months)
    if np.any((n<1)|(n%1!=0)):
        raise ValueError('Positive integer remaining months required')
    return balance/_annuity(coupon,n)*_annuity(discount,n)


def effective_penalty(contract_penalty,*,concessions_permitted=False,assumed_cap=None):
    """USD effective financing loss; the optional cap is assumed, not estimated."""
    if concessions_permitted:
        if assumed_cap is None:raise ValueError('Explicit assumed cap required when concessions are permitted')
        penalty,cap=_nonnegative(contract_penalty,assumed_cap)
        return np.minimum(penalty,cap)
    if assumed_cap is not None:
        raise ValueError('A concession cap requires explicit institutional permission')
    return _nonnegative(contract_penalty)[0]


def sale_intensity(penalty,opportunity_intensity,gains_cdf):
    """Monthly cause-specific sale intensity from Poisson moving opportunities.

    gains_cdf uses gains and penalties in USD. Its distribution and opportunity
    rate must be supplied. An arrival leads to sale when gain exceeds penalty.
    """
    penalty,arrival=_nonnegative(penalty,opportunity_intensity)
    cdf=np.asarray(gains_cdf(penalty),dtype=float)
    if cdf.shape!=penalty.shape or not np.isfinite(cdf).all() or np.any((cdf<0)|(cdf>1)):
        raise ValueError('Gain CDF must return aligned finite probabilities')
    return arrival*(1-cdf)


def competing_probabilities(*,sale,refinancing,other,default):
    """Exact one-month competing-event probabilities from constant intensities.

    Causes are mutually exclusive first exits. This is a proposed alternative
    interface, not a replacement for the production fractional/Markov engine.
    """
    arrays=_nonnegative(sale,refinancing,other,default)
    with np.errstate(over='ignore'):total=sum(arrays)
    if not np.isfinite(total).all():raise ValueError('Total intensity must be finite')
    exit_probability=-np.expm1(-total)
    scale=np.divide(exit_probability,total,out=np.ones_like(total),where=total>0)
    return {name:value*scale for name,value in zip(('sale','refinancing','other','default'),arrays)}


def sale_termination_intensity(home_sale_intensity,termination_probability):
    """Translate home sales into loan exits only under an explicit payoff rule.

    Assumption/portability can permit sale without payoff. This factor specifies
    termination incidence only; a separate cash/payoff/repurchase rule is still
    required to translate exits into MBS principal. No par-payoff rule is inferred.
    """
    intensity,rho=_nonnegative(home_sale_intensity,termination_probability)
    if np.any(rho>1):raise ValueError('Termination probability must be in [0,1]')
    return intensity*rho



def supplied_cause_probabilities(*, sale, refinancing, other, default,
                                 sale_mobility_factor):
    """Borrower monthly first-exit probabilities under supplied intensities.

    All four baseline cause-specific intensities are explicit nonnegative rates
    per month. ``sale`` denotes mortgage termination on sale, not home-sale
    incidence; use ``sale_termination_intensity`` for an explicit translation.
    Only that sale-exit intensity is multiplied by the supplied dimensionless
    mobility factor. Refinancing, other and default intensities stay unchanged.
    Their first-exit probabilities can nevertheless change through competition.
    Zero suppresses sale exits; one leaves them unchanged; factors above one
    raise the assumed sale-exit intensity. Inputs broadcast across borrowers.

    No rate incentive, static savings screen or empirical data supplies a cause
    automatically. This constant-intensity scenario is not a dynamic refinance
    policy, a fitted hazard, or an integration with the production engine.
    """
    sale, refinancing, other, default, factor = _nonnegative(
        sale, refinancing, other, default, sale_mobility_factor,
    )
    with np.errstate(over='ignore', invalid='ignore'):
        adjusted_sale = sale * factor
    if not np.isfinite(adjusted_sale).all():
        raise ValueError('Adjusted sale intensity must be finite')
    return competing_probabilities(
        sale=adjusted_sale, refinancing=refinancing, other=other, default=default,
    )


def aggregate_borrower_probabilities(probabilities, *, weights):
    """Weighted means of already-converted borrower first-exit probabilities.

    Supply one aligned one-dimensional array per cause (sale, refinancing,
    other, default) and explicit nonnegative borrower weights with positive
    total mass. Weights define the population/denominator and are normalized;
    equal borrower weights and balance weights answer different questions.
    Survival is one minus the sum of the four returned means. Convert each
    borrower's intensities before calling: nonlinear conversion of a mean
    intensity generally produces a different result.
    """
    causes = ('sale', 'refinancing', 'other', 'default')
    if set(probabilities) != set(causes):
        raise ValueError('Exactly four mutually exclusive exit causes required')
    weight = np.asarray(weights, dtype=float)
    if (weight.ndim != 1 or weight.size == 0
            or not np.isfinite(weight).all() or np.any(weight < 0)
            or not np.any(weight > 0)):
        raise ValueError('Finite nonnegative borrower weights with positive mass required')
    arrays = [np.asarray(probabilities[cause], dtype=float) for cause in causes]
    if any(value.shape != weight.shape or not np.isfinite(value).all()
           or np.any((value < 0) | (value > 1)) for value in arrays):
        raise ValueError('Aligned finite borrower probabilities in [0,1] required')
    if np.any(np.sum(arrays, axis=0) > 1 + 1e-12):
        raise ValueError('Borrower cause probabilities must sum to at most one')
    # Rescaling before normalization avoids overflow for large finite weights.
    normalized = weight / np.max(weight)
    normalized /= np.sum(normalized)
    return {cause: float(np.dot(normalized, value))
            for cause, value in zip(causes, arrays)}


def static_refinancing_savings(*, balance, contract_rate, refinance_rate,
                               discount_rate, remaining_months, refinancing_cost):
    """USD PV(old payments) - PV(new payments) - explicit upfront cash cost.

    This is a deterministic static screen, NOT a dynamic refinancing optimum.
    Both fully amortizing schedules use the same supplied principal balance and
    remaining integer months; all annual nominal rates are supplied decimals.
    The cash cost is paid now and is not financed into the replacement balance.
    Discount both schedules at the same explicit rate. Positive signed savings
    identify only a static payment comparison. They do not imply exercise now
    or a refinance intensity: expectations of future rates, the value of
    waiting, borrower heterogeneity and endogenous lender pricing are absent.
    """
    balance, old_rate, new_rate, discount, months, cost = _nonnegative(
        balance, contract_rate, refinance_rate, discount_rate,
        remaining_months, refinancing_cost,
    )
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        old_value = scheduled_loan_value(balance, old_rate, discount, months)
        new_value = scheduled_loan_value(balance, new_rate, discount, months)
        savings = old_value - new_value - cost
    if not np.isfinite(savings).all():
        raise ValueError('Static refinancing savings must be finite')
    return savings
