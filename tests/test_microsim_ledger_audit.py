"""Full-path ledger audit agrees with the unchanged legacy loop on supplied inputs."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import polars as pl
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'hazard'))
from config import QT_START,MARKOV_STATES
from microsim_engine import _simulate_regime
from hazard.microsim_ledger_audit import audit_microsim_regime


@pytest.fixture
def inputs():
    loans=pl.DataFrame({'loan_id':['synthetic-a','synthetic-b','synthetic-c','synthetic-d'],
        'stratum_id':['s0']*4,'fico':[720.,730.,700.,710.],'property_state':['PA']*4,
        'orig_ltv':[80.]*4,'coupon':[3.]*4,'orig_upb':[100000.]*4,
        'balance':[100000.,80000.,60000.,0.],'loan_age':[36]*4,
        'state':['Current','D30','Defaulted','Prepaid']})
    macro=pd.DataFrame({'MORTGAGE30US':[7.]*6,'WSHOMCB':[.24]*6},index=pd.date_range(QT_START,periods=6,freq=pd.offsets.MonthEnd()))
    trans=pd.DataFrame(np.eye(len(MARKOV_STATES)),index=MARKOV_STATES,columns=MARKOV_STATES)
    return dict(loan_df=loans,macro=macro,regime='US',holdings_scale_b=.00024,trans=trans,seed=7,beta1=0.)


def test_full_path_reproduces_legacy_outputs_and_retains_inactive_debt(inputs):
    expected=_simulate_regime(**inputs)
    actual=audit_microsim_regime(**inputs)
    pd.testing.assert_frame_equal(actual.legacy_outputs,expected,check_exact=True)
    assert len(actual.ledger)==6
    assert actual.ledger[0].before.inactive_unsettled_principal==60000
    assert all(m.after.full_book_principal>=m.after.active_principal for m in actual.ledger)
    assert all(abs(m.accounting_residual)<=m.tolerance for m in actual.ledger)
    assert actual.security_receipts_usd.isna().all()
    assert actual.security_receipt_evidence=='not_supplied'


def test_security_receipts_are_explicit_and_never_inferred_from_model_cash(inputs):
    supplied=pd.Series([1.,2.,3.,4.,5.,6.],index=inputs['macro'].index)
    actual=audit_microsim_regime(**inputs,security_receipts_usd=supplied,
        security_receipt_provenance='synthetic external series, not observed')
    pd.testing.assert_series_equal(actual.security_receipts_usd,supplied.rename('security_principal_receipts_usd'))
    assert actual.security_receipt_evidence=='caller_supplied_unverified'
    assert actual.security_receipt_provenance=='synthetic external series, not observed'
    assert actual.security_source_verified is False


@pytest.mark.parametrize('case',['missing_provenance','wrong_periods','negative','nan','provenance_without_series'])
def test_incomplete_security_mapping_fails_before_simulation(inputs,case):
    s=pd.Series([1.]*6,index=inputs['macro'].index);p='synthetic source'
    if case=='missing_provenance':p=''
    elif case=='wrong_periods':s.index=s.index+pd.offsets.MonthEnd(1)
    elif case=='negative':s.iloc[0]=-1
    elif case=='nan':s.iloc[0]=np.nan
    elif case=='provenance_without_series':s=None
    with pytest.raises((ValueError,TypeError)):
        audit_microsim_regime(**inputs,security_receipts_usd=s,security_receipt_provenance=p)


@pytest.mark.parametrize('case',['duplicate_month','gap','unordered','bad_matrix','unknown_state'])
def test_inconsistent_source_inputs_fail_closed(inputs,case):
    if case=='duplicate_month':inputs['macro']=pd.concat([inputs['macro'],inputs['macro'].iloc[:1]])
    elif case=='gap':inputs['macro']=inputs['macro'].drop(inputs['macro'].index[2])
    elif case=='unordered':inputs['macro']=inputs['macro'].iloc[::-1]
    elif case=='bad_matrix':inputs['trans']=inputs['trans'].iloc[:,::-1]
    elif case=='unknown_state':inputs['loan_df']=inputs['loan_df'].with_columns(pl.lit('unknown').alias('state'))
    with pytest.raises((ValueError,TypeError)):
        audit_microsim_regime(**inputs)
