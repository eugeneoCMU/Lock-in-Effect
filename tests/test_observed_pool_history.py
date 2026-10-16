"""Saved historical shares persist through weighting and monthly amortization."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import polars as pl
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'hazard'))
from agents import MicrosimPool
import competing_risks as production
from macro import scheduled_amortization_smm


def loans():
    return pl.DataFrame({'loan_id':['a','b'],'stratum_id':['s','s'], 'fico':[720.,720.],
        'property_state':['PA','PA'],'orig_ltv':[80.,80.],'coupon':[3.,4.],
        'orig_upb':[100.,200.],'balance':[80.,160.],'loan_age':[36,36],
        'state':['Current','Current'],'original_loan_term':[180.,360.],
        'initial_burnout':[.2,.4],'burnout_denominator_multiplier':[2.,3.]})


def test_observed_history_uses_original_cohort_denominator():
    p=MicrosimPool(loans())
    assert p.stratum_orig_upb[0]==800
    assert p.cohort_burnout[0]==pytest.approx(.35)
    p.broadcast_burnout()
    np.testing.assert_allclose(p.burnout,[.35,.35])
    p.scale_to_holdings(.000001)
    assert p.cohort_burnout[0]==pytest.approx(.35)
    assert p.stratum_orig_upb[0]==pytest.approx(800*1000/240)


def test_coupon_reweight_recomputes_historical_denominator_and_share():
    p=MicrosimPool(loans())
    p.reweight_to_soma_coupons([{'coupon':.03,'weight':1.,'term_months':360}])
    assert p.orig_upb[1]==0
    assert p.stratum_orig_upb[0]==pytest.approx(p.orig_upb[0]*2)
    assert p.cohort_burnout[0]==pytest.approx(.2)


def test_monthly_schedule_reads_each_observed_original_term(monkeypatch):
    p=MicrosimPool(loans())
    monkeypatch.setattr(production,'prepay_hazard',lambda age,*a,**kw:np.zeros(len(age)))
    monkeypatch.setattr(production,'default_hazard',lambda stress,*a:np.zeros(len(stress)))
    expected=[80*scheduled_amortization_smm(.03,180,36),160*scheduled_amortization_smm(.04,360,36)]
    result=production.monthly_step(p,.07,trans=pd.DataFrame([[1.]],index=['Current'],columns=['Current']))
    assert result['sched_amt']==pytest.approx(sum(expected))
    np.testing.assert_allclose(p.balance,np.array([80,160])-expected)


@pytest.mark.parametrize('field,value',[
    ('initial_burnout',float('nan')),('initial_burnout',1.1),
    ('burnout_denominator_multiplier',.5),('original_loan_term',180.5),
    ('original_loan_term',None)])
def test_invalid_observed_fields_are_rejected(field,value):
    f=loans().with_columns(pl.lit(value).alias(field))
    with pytest.raises(ValueError):MicrosimPool(f)


def test_partial_history_is_rejected():
    with pytest.raises(ValueError):MicrosimPool(loans().drop('initial_burnout'))


def test_future_prepayment_adds_to_history_using_adjusted_denominator(monkeypatch):
    p=MicrosimPool(loans())
    monkeypatch.setattr(production,'PREPAY_MODE','fractional')
    monkeypatch.setattr(production,'prepay_hazard',lambda age,*a,**kw:np.full(len(age),.1))
    monkeypatch.setattr(production,'default_hazard',lambda stress,*a:np.zeros(len(stress)))
    result=production.monthly_step(p,.07,trans=pd.DataFrame([[1.]],index=['Current'],columns=['Current']))
    assert result['prepay_upb']==pytest.approx(24)
    assert p.cohort_burnout[0]==pytest.approx(.35+24/800)


def test_legacy_fields_remain_explicit_assumptions():
    p=MicrosimPool(loans().drop('original_loan_term','initial_burnout','burnout_denominator_multiplier'))
    np.testing.assert_array_equal(p.loan_terms,[360,360])
    assert p.history_assumed and p.terms_assumed
    assert p.cohort_burnout[0]==0
    assert p.stratum_orig_upb[0]==300
