import numpy as np
import pytest
from hazard.positive_gap_mixture import PositiveGapMixture
from hazard.floor_clamped_mixture import FloorClampedMixture


def test_matched_model_differs_only_by_final_floor():
    soft=PositiveGapMixture(.75,.1)
    p=np.array([.02,.02,.02,.02]);gap=np.array([-1.,0.,4.,100.])
    result=FloorClampedMixture(soft,.01).probability(p,gap)
    np.testing.assert_array_equal(result,np.maximum(soft.probability(p,gap),.01))
    assert result[0]==result[1]==.02
    assert result[-1]==.01


def test_no_floor_equals_soft_model_exactly():
    soft=PositiveGapMixture(.75,.1)
    np.testing.assert_array_equal(FloorClampedMixture(soft,0).probability([.02],[4.]),soft.probability([.02],[4.]))


@pytest.mark.parametrize('soft',[PositiveGapMixture(0,.1),PositiveGapMixture(.75,.1,False)])
def test_disabled_response_reproduces_reference(soft):
    np.testing.assert_array_equal(FloorClampedMixture(soft,.01).probability([.02],[4.]),[.02])


@pytest.mark.parametrize('floor',[-.1,1.,float('nan'),True])
def test_invalid_floor_rejected(floor):
    with pytest.raises((TypeError,ValueError)):FloorClampedMixture(PositiveGapMixture(.75,.1),floor)


def test_cannot_silently_change_reference_baseline():
    with pytest.raises(ValueError):FloorClampedMixture(PositiveGapMixture(.75,.1),.03).probability([.02],[4.])


def test_wrong_model_rejected():
    with pytest.raises(TypeError):FloorClampedMixture(None,.01)


def test_integration_and_zero_share_reference():
    import sys
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'hazard'))
    import pandas as pd
    import polars as pl
    from hazard.microsim_ledger_audit import audit_microsim_regime
    df=pl.DataFrame({'loan_id':['synthetic'],'stratum_id':['s'],'fico':[720.],
        'property_state':['PA'],'orig_ltv':[80.],'coupon':[.03],'orig_upb':[100.],
        'balance':[100.],'loan_age':[36],'state':['Current']})
    macro=pd.DataFrame({'MORTGAGE30US':[7.]*3,'WSHOMCB':[.0001]*3},index=pd.date_range('2022-06-01',periods=3,freq='MS'))
    args=dict(loan_df=df,macro=macro,regime='US',holdings_scale_b=1e-7,
        trans=pd.DataFrame([[1.]],index=['Current'],columns=['Current']),seed=42,beta1=0.)
    reference=audit_microsim_regime(**args)
    model=FloorClampedMixture(PositiveGapMixture(0,.1),.003)
    actual=audit_microsim_regime(**args,prepayment_model=model)
    pd.testing.assert_frame_equal(actual.legacy_outputs,reference.legacy_outputs,check_exact=True)
