"""Offline full-path accounting audit on explicitly supplied microsim inputs.

The legacy loop is preserved as a comparison object. Its monthly active-balance
normalization is reproduced and labelled, never promoted to an observed SOMA
receipt mapping. Missing security-principal receipts remain unknown.
Legacy modules require the repository's hazard directory on PYTHONPATH.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np
import pandas as pd
from hazard.mortgage_competing_risks import _finite_real
from hazard.mortgage_credit_ledger import (
    STATES,observe_pool_month,current_microsim_principal_flows,_residual,
)


@dataclass(frozen=True)
class MicrosimLedgerAudit:
    legacy_outputs: pd.DataFrame
    ledger: tuple
    beginning_full_book_principal_usd: float
    ending_full_book_principal_usd: float
    total_cash_principal_usd: float
    cumulative_accounting_residual: float
    cumulative_tolerance: float
    security_receipts_usd: pd.Series
    security_receipt_provenance: str | None
    security_receipt_evidence: str
    security_source_verified: bool=False
    payment_component_history: tuple=()


def audit_microsim_regime(loan_df,macro,regime,holdings_scale_b,trans,seed,beta1,
        soma_cohorts=None,coupon_convert=None,*,security_receipts_usd=None,
        security_receipt_provenance=None,payment_rule=None,prepayment_model=None):
    """Replay the legacy regime loop with a credit ledger on every month.

    All loans, rates, holdings normalization, matrix and model parameters must
    be supplied. No network fetch, fallback dataset, fitted parameter, file write
    or production-function replacement is performed. Source identity and target
    representativeness require separate verification outside this function.
    An explicit payment_rule adds component scheduling and monthly aggregate
    component history. The direct comparison must use that same rule.

    Security receipts, if supplied, are an independently labelled principal
    series in USD on exactly the selected dates, with required provenance. The
    caller's statement is not authenticated; it never becomes a verified source
    or an assumed pass-through of loan cash. Legacy weighted results are an
    unchanged comparison under the legacy normalization, not revised estimates.
    """
    from agents import MicrosimPool,CODE_TO_STATE
    from competing_risks import monthly_step
    from config import QT_START,QT_END

    if not isinstance(macro,pd.DataFrame) or not isinstance(macro.index,pd.DatetimeIndex):
        raise TypeError('Macro inputs need a DatetimeIndex')
    if macro.index.tz is not None or not macro.index.is_unique or not macro.index.is_monotonic_increasing:
        raise ValueError('Macro dates must be unique, ordered and timezone-naive')
    qt_index=macro.index[(macro.index>=QT_START)&(macro.index<QT_END)]
    if len(qt_index)==0:raise ValueError('No supplied QT-window months')
    periods=qt_index.to_period('M')
    if not periods.equals(pd.period_range(periods[0],periods[-1],freq='M')):
        raise ValueError('Require one observation per consecutive selected month')
    if not {'MORTGAGE30US','WSHOMCB'}.issubset(macro.columns):
        raise ValueError('Missing supplied mortgage-rate or holdings-normalization column')
    for column in ('MORTGAGE30US','WSHOMCB'):
        for value in macro.loc[qt_index,column]:_finite_real(value,column)
    holdings_scale_b=_finite_real(holdings_scale_b,'initial holdings normalization in billions')
    _finite_real(beta1,'beta1',nonnegative=False)
    if not isinstance(trans,pd.DataFrame) or not trans.index.is_unique or not trans.columns.is_unique or list(trans.index)!=list(trans.columns):
        raise ValueError('Transition matrix must be square with identically ordered state labels')
    if not set(trans.index).issubset(STATES) or len(trans)==0:
        raise ValueError('Unknown or empty source transition-state labels')
    for value in trans.to_numpy().flat:_finite_real(value,'transition weight')
    # Zero rows are permitted: the existing step leaves those states unchanged.
    if 'state' not in loan_df.columns or any(state not in STATES for state in loan_df['state'].to_list()):
        raise ValueError('Unknown or missing original loan states may not silently become Current')

    if security_receipts_usd is None:
        if security_receipt_provenance is not None:raise ValueError('Provenance without supplied security receipts')
        receipts=pd.Series([None]*len(qt_index),index=qt_index,name='security_principal_receipts_usd',dtype=object)
        evidence='not_supplied'
    else:
        if not isinstance(security_receipts_usd,pd.Series) or not security_receipts_usd.index.equals(qt_index):
            raise ValueError('Security receipt dates must match the entire selected horizon')
        if not isinstance(security_receipt_provenance,str) or not security_receipt_provenance.strip():
            raise ValueError('Explicit security-receipt provenance is required')
        receipts=pd.Series([_finite_real(v,'security principal receipt') for v in security_receipts_usd],
            index=qt_index,name='security_principal_receipts_usd')
        evidence='caller_supplied_unverified'

    pool=MicrosimPool(loan_df,regime=regime,rng=np.random.default_rng(seed))
    if soma_cohorts is not None:pool.reweight_to_soma_coupons(soma_cohorts,coupon_convert=coupon_convert)
    pool.scale_to_holdings(holdings_scale_b)
    payment_state=None
    if payment_rule is not None:
        from hazard.observed_payment_path import ObservedPaymentState
        payment_state=ObservedPaymentState(loan_df,pool,payment_rule=payment_rule)
    records=[];ledgers=[];components=[]
    for ts in qt_index:
        mkt=float(macro.loc[ts,'MORTGAGE30US'])/100.0
        options={} if payment_state is None else {'payment_state':payment_state}
        if prepayment_model is not None:options['prepayment_model']=prepayment_model
        observed=observe_pool_month(pool,monthly_step,mkt,trans=trans,beta1=beta1,
            code_to_state=CODE_TO_STATE,flow_reader=current_microsim_principal_flows,**options)
        if payment_state is not None:components.append(dict(period=ts,**payment_state.summary()))
        result=observed.source_result;ledgers.append(observed.ledger)
        exposure=result['exposure']
        monthly_cpr=result['prepay_upb']/exposure if exposure>0 else 0.0
        total_bal=pool.total_exposure()
        holdings_b=float(macro.loc[ts,'WSHOMCB'])/1000
        scale=holdings_b/max(total_bal/1e9,1e-6) if total_bal>0 else 1.0
        sched_b=result['sched_amt']*scale/1e9
        settled_b=result['settled_b']*scale/1e9
        records.append(dict(period=ts,regime=regime,market_rate_pct=mkt*100,
            hazard_cpr_pct=monthly_cpr*12*100,prepay_upb=result['prepay_upb'],
            exposure=exposure,simulated_rolloff_b=-(settled_b+sched_b),
            weighted_settled_b=settled_b,weighted_sched_b=sched_b,
            default_count=result['default_count'],
            delinquency_stock=int(np.isin(pool.state_code,[1,2,3,4]).sum())))
    cash=math.fsum(m.cash_principal for m in ledgers)
    additions=math.fsum(m.flows.addition for m in ledgers)
    write_downs=math.fsum(m.flows.write_down for m in ledgers)
    beginning=ledgers[0].before.full_book_principal;ending=ledgers[-1].after.full_book_principal
    residual,tolerance=_residual(beginning,ending,cash,write_downs,additions)
    return MicrosimLedgerAudit(pd.DataFrame(records).set_index('period'),tuple(ledgers),
        beginning,ending,cash,residual,tolerance,receipts,
        security_receipt_provenance,evidence,payment_component_history=tuple(components))
