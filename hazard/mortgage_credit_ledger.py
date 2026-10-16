"""Pool-level principal reconciliation across complete loan-state snapshots.

A departure from active exposure is not a cash receipt or principal write-off.
Cash, additions and write-downs must be supplied explicitly in common principal
units. This module does not estimate recoveries, payment lags, probabilities or
loan-level cash allocations, and never changes a production pool.
"""
from dataclasses import dataclass
from collections.abc import Mapping
from types import MappingProxyType
import math
from hazard.mortgage_competing_risks import _finite_real

ACTIVE_STATES=('Current','D30','D60','D90+','Forbearance')
INACTIVE_STATES=('Defaulted','Liquidated')
STATES=(*ACTIVE_STATES,'Prepaid',*INACTIVE_STATES)


def _sum(values):
    try:value=math.fsum(values)
    except OverflowError:raise ValueError('Principal total exceeds finite arithmetic range') from None
    if not math.isfinite(value):raise ValueError('Principal total must be finite')
    return value


@dataclass(frozen=True)
class PrincipalFlows:
    scheduled: float
    voluntary: float
    settlement: float
    write_down: float
    addition: float

    def __post_init__(self):
        for name in ('scheduled','voluntary','settlement','write_down','addition'):
            object.__setattr__(self,name,_finite_real(getattr(self,name),name))


@dataclass(frozen=True)
class DebtStock:
    loan_count: int
    principal_by_state: Mapping[str,float]
    full_book_principal: float
    active_principal: float
    inactive_unsettled_principal: float


@dataclass(frozen=True)
class CreditLedgerStep:
    before: DebtStock
    after: DebtStock
    flows: PrincipalFlows
    cash_principal: float
    added_principal: float
    active_to_inactive_principal: float
    accounting_residual: float
    tolerance: float
    reconciliation_scope: str='pool_total_only'
    per_loan_cash_allocation_verified: bool=False


@dataclass(frozen=True)
class CreditLedgerPath:
    months: tuple[CreditLedgerStep,...]
    beginning_full_book_principal: float
    ending_full_book_principal: float
    cash_principal: float
    credit_settlement_principal: float
    write_down_principal: float
    added_principal: float
    accounting_residual: float
    tolerance: float


def _snapshot(records):
    if not isinstance(records,Mapping):raise TypeError('Snapshot must map loan keys to state/balance pairs')
    checked={};amounts={state:[] for state in STATES}
    for key,row in records.items():
        if not isinstance(key,str) or not key.strip():raise ValueError('Loan keys must be nonempty strings')
        if not isinstance(row,(tuple,list)) or len(row)!=2:
            raise ValueError('Each snapshot row must contain state and principal')
        state,principal=row
        if not isinstance(state,str) or state not in STATES:raise ValueError('Unknown source state')
        principal=_finite_real(principal,'source principal')
        if state=='Prepaid' and principal!=0:raise ValueError('Prepaid snapshot must retain an explicit zero balance')
        checked[key]=(state,principal);amounts[state].append(principal)
    state_totals={state:_sum(values) for state,values in amounts.items()}
    stock=DebtStock(len(checked),MappingProxyType(state_totals),_sum(state_totals.values()),
        _sum(state_totals[state] for state in ACTIVE_STATES),
        _sum(state_totals[state] for state in INACTIVE_STATES))
    return checked,stock


def _residual(beginning,ending,cash,write_down,addition):
    # Absolute floor plus a few ulps, with no percentage-of-UPB gap tolerance.
    tolerance=max(1e-8,8*math.ulp(max(beginning,ending,cash,write_down,addition)))
    value=_sum([beginning,addition,-cash,-write_down,-ending])
    if abs(value)>tolerance:
        raise ValueError('Principal does not reconcile with explicit cash, write-downs and additions')
    return value,tolerance


def credit_ledger_step(before,after,flows):
    """Reconcile full-book debt; classify source-state transfers separately.

    Both snapshots contain every same loan key, including closed zero-balance
    rows. Delinquent/forbearance balances remain active under the current source
    convention. Positive Defaulted/Liquidated balances are retained in the
    inactive bucket; its 'unsettled' label does not establish actual recovery,
    legal claim or settlement status from the state name alone.

    flows must explicitly provide all five components. Principal settlement
    excludes interest, fees or other recoveries. A supplied zero is a statement
    about this interval, never an estimate of zero ultimate recovery. The
    identity is at pool level; offsetting per-loan changes cannot be verified
    without independently allocated per-loan flows. No population entry/exit,
    state policy or borrower transaction cause is inferred.
    """
    if not isinstance(flows,PrincipalFlows):raise TypeError('Supply explicit PrincipalFlows')
    old,stock_before=_snapshot(before);new,stock_after=_snapshot(after)
    if old.keys()!=new.keys():raise ValueError('Complete same-loan snapshots required; no implicit population changes')
    cash=_sum([flows.scheduled,flows.voluntary,flows.settlement])
    residual,tolerance=_residual(stock_before.full_book_principal,
        stock_after.full_book_principal,cash,flows.write_down,flows.addition)
    transfer=_sum(balance for key,(state,balance) in new.items()
        if old[key][0] in ACTIVE_STATES and state in INACTIVE_STATES)
    return CreditLedgerStep(stock_before,stock_after,flows,cash,flows.addition,
        transfer,residual,tolerance)


def credit_ledger_path(snapshots,monthly_flows):
    """Continuous stock/flow ledger from N+1 complete snapshots and N flows.

    Source snapshots and supplied principal components are the evidence inputs.
    These functions do not create a delayed recovery assumption or change the
    simulator's settlement behavior. Defaulted debt may persist over any number
    of snapshots, with explicit later settlement/write-down entries if supplied.
    """
    if isinstance(snapshots,(str,bytes,Mapping)) or isinstance(monthly_flows,(str,bytes,Mapping)):
        raise TypeError('Provide a sequence of snapshots and a sequence of flows')
    snapshots=tuple(snapshots);flows=tuple(monthly_flows)
    if not flows or len(snapshots)!=len(flows)+1:
        raise ValueError('N monthly flows require N+1 complete snapshots, N>=1')
    months=tuple(credit_ledger_step(snapshots[i],snapshots[i+1],flow) for i,flow in enumerate(flows))
    cash=_sum(m.cash_principal for m in months)
    settlement=_sum(m.flows.settlement for m in months)
    write_down=_sum(m.flows.write_down for m in months)
    addition=_sum(m.flows.addition for m in months)
    beginning=months[0].before.full_book_principal;ending=months[-1].after.full_book_principal
    residual,tolerance=_residual(beginning,ending,cash,write_down,addition)
    return CreditLedgerPath(months,beginning,ending,cash,settlement,write_down,
        addition,residual,tolerance)


@dataclass(frozen=True)
class ObservedPoolMonth:
    ledger: CreditLedgerStep
    source_result: Mapping


def current_microsim_principal_flows(result):
    """Explicit flow contract for the current production monthly_step only.

    Its settled_b equals voluntary prepay_upb; default_upb is zero, balances
    are retained on default, and no capitalization/write-down/recovery flow is
    implemented there. Refuse a changed reporting contract rather than infer a
    default settlement from settled_b minus prepay_upb. Any later richer model
    needs an explicit different flow_reader and source validation.
    """
    required={'sched_amt','prepay_upb','settled_b','default_upb'}
    allowed=required|{'exposure','prepay_count','default_count'}
    if not isinstance(result,Mapping) or not required.issubset(result) or set(result)-allowed:
        raise ValueError('Unsupported monthly-step reporting schema; explicit flow mapping required')
    values={k:_finite_real(result[k],k) for k in required}
    if values['settled_b']!=values['prepay_upb'] or values['default_upb']!=0:
        raise ValueError('Changed production principal/settlement contract; no inferred recovery allocation')
    return PrincipalFlows(values['sched_amt'],values['prepay_upb'],0.0,0.0,0.0)


def _pool_snapshot(pool,code_to_state):
    from numbers import Integral
    if not isinstance(code_to_state,Mapping):raise TypeError('Source state-code mapping required')
    if not len(pool.loan_ids)==len(pool.state_code)==len(pool.balance):
        raise ValueError('Pool snapshot arrays must have matching lengths')
    result={}
    for source_key,code,balance in zip(pool.loan_ids,pool.state_code,pool.balance):
        key=str(source_key)
        if key in result:raise ValueError('Duplicate source loan key in pool snapshot')
        if isinstance(code,bool) or not isinstance(code,Integral) or int(code) not in code_to_state:
            raise ValueError('Unrecognized source state code')
        result[key]=(code_to_state[int(code)],balance)
    _snapshot(result)  # Validate the complete pre-step snapshot before mutation.
    return result


def observe_pool_month(pool,step_callable,*args,code_to_state,flow_reader,**kwargs):
    """Execute one supplied step and reconcile complete before/after snapshots.

    This opt-in observer calls the existing function unchanged, without changing
    RNG draws, state logic, portfolio weights or reported cash. The supplied
    reader explicitly maps its return fields to PrincipalFlows. Returned output
    contains aggregate state stocks and flows, never the individual source IDs.

    Reconciliation is checked after the supplied step mutates its pool. A
    failure raises an error; this observer does not roll back that mutation or
    permit the caller to retry it as if no step ran. No data is persisted here.
    """
    if not callable(step_callable) or not callable(flow_reader):
        raise TypeError('Supply a step callable and explicit flow reader')
    before=_pool_snapshot(pool,code_to_state)
    result=step_callable(pool,*args,**kwargs)
    if not isinstance(result,Mapping):raise TypeError('Observed step must return a mapping')
    after=_pool_snapshot(pool,code_to_state)
    flows=flow_reader(result)
    ledger=credit_ledger_step(before,after,flows)
    return ObservedPoolMonth(ledger,MappingProxyType(dict(result)))
