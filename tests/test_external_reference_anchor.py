import math
import pytest
from external_reference_anchor import equivalent_monthly_probability, monthly_effect_illustration, assess_anchor


def test_constant_hazard_frequency_conversion_preserves_survival():
    p=equivalent_monthly_probability(.0752,12)
    assert (1-p)**12==pytest.approx(1-.0752)
    assert equivalent_monthly_probability(1.,3)==1.


def test_effect_conversion_is_difference_of_transformed_probabilities():
    r=monthly_effect_illustration(.0752,.0069,12)
    assert r['monthly_difference']==pytest.approx(equivalent_monthly_probability(.0752,12)-equivalent_monthly_probability(.0752-.0069,12))
    assert r['monthly_difference']!=pytest.approx(.0069/12,rel=1e-5)
    assert r['empirically_anchored_payoff_cap'] is False


def test_frequency_bridge_does_not_cure_outcome_or_weight_mismatch():
    s=dict(outcome='sale_probability',weighting='loan_count',frequency='quarterly',estimand='slope_per_gap_pp',statistic='point_estimate')
    r=assess_anchor(s,bridges={'frequency':'assumed'})
    assert r['direct_payoff_cap_authorized'] is False
    assert 'outcome' in r['unresolved'] and 'weighting' in r['unresolved'] and 'estimand' in r['unresolved']


def test_matching_point_estimate_is_still_not_an_upper_bound():
    s=dict(outcome='recorded_payoff_fraction',weighting='opening_principal',frequency='monthly',estimand='no_lockin_level_difference',statistic='point_estimate')
    assert 'statistic' in assess_anchor(s)['unresolved']


def test_assumed_bridges_are_conditional_not_empirical_authorization():
    s=dict(outcome='moving_probability',weighting='person_count',frequency='annual',estimand='slope_per_gap_pp',statistic='point_estimate')
    r=assess_anchor(s,bridges={x:'assumed' for x in ['outcome','weighting','frequency','estimand','statistic']})
    assert r['status']=='conditional_scenario_only' and r['direct_payoff_cap_authorized'] is False


def test_bad_probability_conversion_rejected():
    for p,n in [(-.1,12),(.1,0),(.1,True)]:
        with pytest.raises(ValueError):equivalent_monthly_probability(p,n)
    with pytest.raises(ValueError):monthly_effect_illustration(.01,.02,3)
