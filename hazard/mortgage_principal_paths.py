"""Paired expected-principal paths under supplied exogenous monthly intensities.

A homogeneous starting cohort shares a contractual principal schedule per
original surviving loan. Explicit schedule-first or exit-first monthly ordering.
The active fraction scales scheduled principal; the schedule is not recalculated
from a shrinking aggregate balance. This is a scenario accounting extension,
not a fit, a general production-model reproduction, or an observed runoff estimate.
"""
from dataclasses import dataclass
from types import MappingProxyType
import math
from collections.abc import Mapping
from hazard.mortgage_competing_risks import competing_probabilities, _finite_real


@dataclass(frozen=True)
class PrincipalPathMonth:
    month: int
    beginning_balance: float
    beginning_active_fraction: float
    scheduled_principal: float
    cause_principal: Mapping[str, float]
    ending_balance: float
    ending_active_fraction: float
    designated_cash_principal: float
    unclassified_removal_principal: float
    accounting_residual: float


@dataclass(frozen=True)
class PrincipalPath:
    beginning_balance: float
    months: tuple[PrincipalPathMonth, ...]
    scheduled_principal: float
    cause_principal: Mapping[str, float]
    ending_balance: float
    designated_cash_principal: float
    unclassified_removal_principal: float
    cash_causes: tuple[str, ...]
    accounting_residual: float
    event_order: str


@dataclass(frozen=True)
class PairedPrincipalPaths:
    first: PrincipalPath
    second: PrincipalPath
    scheduled_difference: float
    cause_differences: Mapping[str, float]
    ending_balance_difference: float
    designated_cash_difference: float
    unclassified_removal_difference: float
    accounting_residual: float


def _inputs(beginning_balance, contractual_principal, intensity_path, cash_causes):
    balance=_finite_real(beginning_balance,'beginning_balance')
    if isinstance(contractual_principal,(str,bytes)) or isinstance(intensity_path,(str,bytes)):
        raise TypeError('Schedule and intensity path must be sequences, not text')
    schedule=tuple(_finite_real(v,'contractual_principal') for v in contractual_principal)
    intensities=tuple(intensity_path)
    if not schedule or len(schedule)!=len(intensities):
        raise ValueError('A nonempty schedule and matching monthly intensity horizon are required')
    try:total=math.fsum(schedule)
    except OverflowError:raise ValueError('Contractual principal exceeds starting balance') from None
    if total>balance:raise ValueError('Contractual principal exceeds starting balance')
    # Validate every supplied month, including months after all principal exits.
    probabilities=tuple(competing_probabilities(m) for m in intensities)
    causes=tuple(dict.fromkeys(k for m in probabilities for k in m.cause_probabilities))
    if isinstance(cash_causes,(str,bytes,Mapping)):
        raise TypeError('cash_causes must be an explicit collection of cause labels')
    cash=tuple(dict.fromkeys(cash_causes))
    if any(not isinstance(k,str) or k not in causes for k in cash):
        raise ValueError('Every designated cash cause must occur in the supplied intensity path')
    return balance,schedule,probabilities,causes,cash


def principal_path(beginning_balance, contractual_principal, intensity_path, *, cash_causes,
                   event_order="schedule_first"):
    """Expected dollars for one homogeneous cohort over an explicit horizon.

    Schedule entries are principal per initially live mortgage under the common
    contract, in the same units as beginning_balance. An intensity mapping is
    supplied per month; values are per-month constant intensities, not event
    probabilities. For heterogeneous loans, run each homogeneous contract
    separately and aggregate afterward. No schedule extension or extrapolation
    of the horizon is inferred. Time is one month per row.

    cash_causes is explicit. All other removals stay unclassified for settlement;
    they are NOT assumed to be zero ultimate cash recovery. Scheduled principal
    follows the explicit event_order: schedule_first (default) or exit_first.
    In exit_first, only nonterminating loans make the scheduled payment. No
    default-state pipeline is implied by this timing choice. There is no credit
    pipeline, modification, delinquency, recovery or portfolio-weight model.
    """
    if event_order not in ("schedule_first","exit_first"):
        raise ValueError("event_order must be schedule_first or exit_first")
    initial,schedule,probabilities,causes,cash=_inputs(
        beginning_balance,contractual_principal,intensity_path,cash_causes)
    rows=[];active=1.0 if initial else 0.0;remaining=initial
    scheduled_contract=[]
    for month,(principal,prob) in enumerate(zip(schedule,probabilities),1):
        beginning=active*remaining
        scheduled_contract.append(principal)
        # Recompute from the cumulative contract schedule to avoid drift and
        # force exact contractual maturity when the supplied schedule sums to B.
        residual_contract=max(initial-math.fsum(scheduled_contract),0.0)
        scheduled_mass=active if event_order=="schedule_first" else active*prob.survival_probability
        scheduled=scheduled_mass*principal
        event_balance=active*residual_contract if event_order=="schedule_first" else beginning
        removals={k:event_balance*prob.cause_probabilities.get(k,0.0) for k in causes}
        next_active=active*prob.survival_probability if residual_contract else 0.0
        ending=next_active*residual_contract
        cash_amount=math.fsum([scheduled]+[removals[k] for k in cash])
        unclassified=math.fsum(v for k,v in removals.items() if k not in cash)
        residual=math.fsum([beginning,-scheduled,-math.fsum(removals.values()),-ending])
        rows.append(PrincipalPathMonth(month,beginning,active,scheduled,MappingProxyType(removals),
            ending,next_active,cash_amount,unclassified,residual))
        active,remaining=next_active,residual_contract
    totals={k:math.fsum(row.cause_principal[k] for row in rows) for k in causes}
    scheduled=math.fsum(row.scheduled_principal for row in rows)
    ending=rows[-1].ending_balance
    return PrincipalPath(initial,tuple(rows),scheduled,MappingProxyType(totals),ending,
        math.fsum(row.designated_cash_principal for row in rows),
        math.fsum(row.unclassified_removal_principal for row in rows),cash,
        math.fsum([initial,-scheduled,-math.fsum(totals.values()),-ending]),event_order)


def paired_principal_paths(beginning_balance, contractual_principal,
                           first_intensities, second_intensities, *, cash_causes,
                           event_order="schedule_first"):
    """Run two legs from the same contract; report first minus second dollars.

    The scheduled-principal difference is retained. Cause differences are
    accounting allocations, not isolated causal effects: competing survival
    affects every cause and future scheduled payments. Starting debt, contract
    and cash designation are shared. Missing cause labels mean explicit zero
    intensity in that month, not an empirically inferred missing exit type.
    """
    schedule=tuple(contractual_principal)
    first_path=tuple(first_intensities);second_path=tuple(second_intensities)
    if not schedule or len(first_path)!=len(schedule) or len(second_path)!=len(schedule):
        raise ValueError('Both legs must match the common nonempty contractual horizon')
    if isinstance(cash_causes,(str,bytes,Mapping)):
        raise TypeError('cash_causes must be an explicit collection of cause labels')
    cash=tuple(cash_causes)
    for leg in (first_path,second_path):
        for month in leg:
            competing_probabilities(month)
    # Give both legs the union of named causes. A cause can legitimately be
    # absent in one counterfactual and present in the other; do not reject its
    # common cash classification simply because its intensity is zero there.
    causes=tuple(dict.fromkeys(k for leg in (first_path,second_path) for m in leg for k in m))
    def complete(leg):return [{k:m.get(k,0.0) for k in causes} for m in leg]
    first=principal_path(beginning_balance,schedule,complete(first_path),cash_causes=cash,event_order=event_order)
    second=principal_path(beginning_balance,schedule,complete(second_path),cash_causes=cash,event_order=event_order)
    differences={k:first.cause_principal[k]-second.cause_principal[k] for k in causes}
    scheduled=first.scheduled_principal-second.scheduled_principal
    ending=first.ending_balance-second.ending_balance
    return PairedPrincipalPaths(first,second,scheduled,MappingProxyType(differences),ending,
        first.designated_cash_principal-second.designated_cash_principal,
        first.unclassified_removal_principal-second.unclassified_removal_principal,
        math.fsum([scheduled,*differences.values(),ending]))
