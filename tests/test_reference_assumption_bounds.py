import numpy as np
import pandas as pd
import pytest
from reference_assumption_bounds import payoff_bounds


def data():
    return pd.DataFrame(dict(loan_id=['a','b','c'],reporting_period=['202206']*3,
        at_risk_adjacent=[True]*3,current_note_gap_pp=[2.,2.,-1.],
        adjacent_opening_upb=[100.,100.,100.],adjacent_payoff_upb=[100.,0.,0.]))


def test_unrestricted_and_monotone_bounds_are_different_assumptions():
    r=payoff_bounds(data(),caps=[.1])
    u=next(x for x in r['monthly'] if x['scenario']=='unrestricted')
    m=next(x for x in r['monthly'] if x['scenario']=='monotone_recorded_payoff')
    assert (u['reference_fraction_lower'],u['reference_fraction_upper'])==(0.,1.)
    assert u['extra_payoff_lower']==-100 and u['extra_payoff_upper']==200
    assert m['extra_payoff_lower']==0 and m['extra_payoff_upper']==200
    assert r['causal_effect_estimated'] is False


def test_cap_is_group_average_and_only_positive_gap_exposure_can_change():
    r=payoff_bounds(data(),caps=[.1])
    c=next(x for x in r['monthly'] if x['scenario']=='positive_gap_cap_0.1')
    assert c['extra_payoff_upper']==20
    assert c['reference_fraction_upper']==120/300
    assert c['known_nonpositive_opening_upb']==100


def test_missing_gap_is_not_dropped_or_silently_capped():
    d=data();d.loc[2,'current_note_gap_pp']=np.nan
    r=payoff_bounds(d,caps=[.1])
    c=next(x for x in r['monthly'] if x['scenario']=='positive_gap_cap_0.1')
    assert c['unknown_gap_opening_upb']==100 and c['extra_payoff_upper']==120
    assert c['opening_upb']==300


def test_caps_apply_month_by_month_and_never_exceed_remaining_exposure():
    a=data();b=data().assign(reporting_period='202207',loan_id=lambda x:x.loan_id+'2')
    r=payoff_bounds(pd.concat([a,b],ignore_index=True),caps=[.9])
    c=[x for x in r['monthly'] if x['scenario']=='positive_gap_cap_0.9']
    assert len(c)==2 and all(x['extra_payoff_upper']==100 for x in c)


def test_invalid_denominators_and_caps_fail():
    d=data();d.loc[0,'adjacent_payoff_upb']=101
    with pytest.raises(ValueError):payoff_bounds(d,caps=[.1])
    with pytest.raises(ValueError):payoff_bounds(data(),caps=[-1])
