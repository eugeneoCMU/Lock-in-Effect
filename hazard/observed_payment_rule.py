"""One-month level-payment scenario; not an observed contractual payment.

Remaining legal maturity is deliberately an explicit amortization assumption.
No prepayments, defaults, future modifications, or security receipts are inferred.
"""
from dataclasses import dataclass
import math
from numbers import Real


@dataclass(frozen=True)
class PaymentScenario:
    scheduled_principal: float
    interest: float
    ending_total: float
    ending_interest_bearing: float
    ending_deferred: float
    component_residual: float
    remaining_legal_months_after: int
    payment_rule: str
    actual_payment_verified: bool = False
    deferred_maturity_cash: object = None


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(name+' must be numeric')
    value=float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(name+' must be finite and nonnegative')
    return value


def payment_scenario(*, total_principal, interest_bearing, deferred,
                     current_rate_decimal, remaining_legal_months, payment_rule):
    """Amortize only interest-bearing debt under an explicitly chosen rule.

    Input component discrepancies of at most one cent are carried as a signed
    residual, not imputed to either component. Larger discrepancies fail closed.
    Deferred principal has no scheduled collection in this scenario; its actual
    maturity collection remains unknown even when the interest-bearing term ends.
    """
    if payment_rule != 'level_payment_to_legal_maturity':
        raise ValueError('An explicit supported payment scenario is required')
    total=_number(total_principal,'total_principal')
    bearing=_number(interest_bearing,'interest_bearing')
    deferred=_number(deferred,'deferred')
    rate=_number(current_rate_decimal,'current_rate_decimal')
    if rate > 1:
        raise ValueError('Rate must be a decimal fraction in [0,1]')
    n=_number(remaining_legal_months,'remaining_legal_months')
    if n < 1 or n != math.floor(n):
        raise ValueError('Remaining legal months must be positive integer months')
    residual=total-bearing-deferred
    if abs(residual) > .01+1e-9:
        raise ValueError('Principal components do not reconcile within one cent')
    monthly=rate/12
    interest=bearing*monthly
    if n==1:
        principal=bearing
    elif monthly==0:
        principal=bearing/n
    else:
        payment=bearing*monthly/(-math.expm1(-n*math.log1p(monthly)))
        principal=max(0.,min(bearing,payment-interest))
    # A signed rounding residual cannot create a negative total at closure.
    principal=min(principal,total)
    return PaymentScenario(principal,interest,total-principal,bearing-principal,
                           deferred,residual,int(n)-1,payment_rule)
