import numpy as np
import pytest
from hazard.positive_gap_mixture import PositiveGapMixture


def test_reference_is_exact_when_disabled_or_share_zero():
    p=np.array([.02,.1,0.,.8]);g=np.array([4.,2.,0.,-1.])
    for model in [PositiveGapMixture(0,.1),PositiveGapMixture(.75,.1,False),PositiveGapMixture(.75,0)]:
        np.testing.assert_array_equal(model.probability(p,g),p)


def test_intensity_components_and_positive_only_response():
    p=np.array([.02]*3);g=np.array([-2.,0.,4.])
    model=PositiveGapMixture(.75,-np.log(.935))
    result=model.probability(p,g)
    assert result[0]==result[1]==.02
    expected=-np.expm1(np.log1p(-.02)*(.25+.75*.935**4))
    assert result[2]==pytest.approx(expected)
    assert .016 < result[2] < .017


def test_share_order_and_asymptotic_insensitive_component():
    values=[PositiveGapMixture(s,.1).probability([.02],[4.])[0] for s in [0,.25,.5,.75,1]]
    assert all(a>b for a,b in zip(values,values[1:]))
    expected=-np.expm1(np.log1p(-.02)*.25)
    assert PositiveGapMixture(.75,10).probability([.02],[1e6])[0]==pytest.approx(expected)


@pytest.mark.parametrize('args',[(True,.1),(-.1,.1),(1.1,.1),(.5,-.1),(.5,float('nan')),(.5,.1,'yes')])
def test_invalid_configuration(args):
    with pytest.raises((ValueError,TypeError)):PositiveGapMixture(*args)


@pytest.mark.parametrize('p,g',[([1.],[1.]),([-.1],[1.]),([.1],[float('nan')]),([.1,.2],[1.])])
def test_invalid_or_misaligned_arrays(p,g):
    with pytest.raises(ValueError):PositiveGapMixture(.75,.1).probability(p,g)


def test_full_path_zero_share_and_disabled_response_match_reference():
    import sys
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'hazard'))
    import pandas as pd
    import polars as pl
    from hazard.microsim_ledger_audit import audit_microsim_regime
    df=pl.DataFrame({'loan_id':['synthetic'],'stratum_id':['s'],'fico':[720.],
        'property_state':['PA'],'orig_ltv':[80.],'coupon':[.03],'orig_upb':[100.],
        'balance':[100.],'loan_age':[36],'state':['Current']})
    macro=pd.DataFrame({'MORTGAGE30US':[7.,2.,7.],'WSHOMCB':[.0001]*3},
        index=pd.date_range('2022-06-01',periods=3,freq='MS'))
    args=dict(loan_df=df,macro=macro,regime='US',holdings_scale_b=1e-7,
        trans=pd.DataFrame([[1.]],index=['Current'],columns=['Current']),seed=42,beta1=0.)
    reference=audit_microsim_regime(**args)
    for model in [PositiveGapMixture(0,.1),PositiveGapMixture(.75,.1,False)]:
        result=audit_microsim_regime(**args,prepayment_model=model)
        pd.testing.assert_frame_equal(result.legacy_outputs,reference.legacy_outputs,check_exact=True)
        assert result.total_cash_principal_usd==reference.total_cash_principal_usd
    with pytest.raises(ValueError):
        audit_microsim_regime(**dict(args,regime='Danish'),prepayment_model=PositiveGapMixture(.75,.1))
