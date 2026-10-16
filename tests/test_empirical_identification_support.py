import numpy as np
import pandas as pd
import pytest

from empirical_identification_support import audit_identifying_variation, joint_support


def synthetic():
    # All gaps positive: calendar effects minus coupon are exactly additive.
    return pd.DataFrame([
        dict(reporting_period=month, coupon=coupon, vintage=2020, mean_loan_age=age,
             gap_pp=(rate-coupon)*100, adjacent_opening_upb=100.,
             adjacent_payoff_upb=1., unallocated_timing_payoff_upb=0.,measurement_valid=True)
        for month, rate, age in [('202206', .06, 24.),('202207', .07,25.)]
        for coupon in [.03,.04]])


def test_calendar_coupon_controls_absorb_positive_gap_when_every_gap_positive():
    r = audit_identifying_variation(synthetic(), controls=['reporting_period','coupon'])
    assert r['gap_absorbed_by_controls'] is True
    assert r['residualized_variation_share'] == pytest.approx(0.,abs=1e-20)
    assert r['parameter_identification_established'] is False


def test_zero_hinge_can_leave_variation_but_does_not_establish_identification():
    d = synthetic()
    # Make rates cross the two coupon bins; gplus cannot stay additive.
    d['gap_pp'] = [-.5,-1.5,1.5,.5]
    r = audit_identifying_variation(d,controls=['reporting_period','coupon'])
    assert r['residualized_variation_share'] > 0
    assert r['gap_absorbed_by_controls'] is False
    assert r['parameter_identification_established'] is False


def test_invalid_rows_and_weights_cannot_create_support():
    d = synthetic(); d.loc[0,'measurement_valid']=False
    d.loc[1,'adjacent_opening_upb']=0
    r = audit_identifying_variation(d,controls=['reporting_period','coupon'])
    assert r['rows_used'] == 2
    assert r['excluded_rows'] == 2
    d.loc[2,'gap_pp']=np.inf
    r = audit_identifying_variation(d,controls=['reporting_period','coupon'])
    assert r['rows_used'] == 1


def test_unknown_control_and_missing_age_never_imputed():
    with pytest.raises(ValueError,match='control'):
        audit_identifying_variation(synthetic(),controls=['post_exit_balance'])
    d=synthetic();d.loc[0,'mean_loan_age']=np.nan
    r=joint_support(d)
    assert r['missing_age_rows'] == 1
    assert sum(c['rows'] for c in r['cells']) == 3
    assert r['age_basis'] == 'concurrent_cohort_mean_not_borrower_decision_time_age'


def test_joint_support_retains_unknown_timing_and_missing_months():
    d=synthetic();d.loc[0,'unallocated_timing_payoff_upb']=5.
    r=joint_support(d)
    assert sum(c['unknown_timing_payoff_upb'] for c in r['cells']) == 5.
    assert r['causal_reference_supported'] is False
    assert all('observed_months' in c for c in r['cells'])


def test_large_weighted_design_has_finite_moments_without_floating_errors():
    d=pd.concat([synthetic()]*3000,ignore_index=True)
    with np.errstate(all='raise'):
        r=audit_identifying_variation(d,controls=['reporting_period','coupon'])
    assert np.isfinite(r['residualized_positive_gap_sd_pp'])
    assert r['gap_absorbed_by_controls'] is True
