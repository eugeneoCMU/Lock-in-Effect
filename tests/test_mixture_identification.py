import numpy as np
import pytest
from mixture_identification import profile_mixture


def profile(gaps=(1.,3.), shares=(0.,), gammas=(.01,.1)):
    return profile_mixture(np.array([.02,.02]),np.array(gaps),np.array([.02,.02]),np.ones(2),shares=list(shares),gammas=list(gammas))

def test_zero_share_does_not_identify_gamma():
    r=profile()
    assert r['gamma_identified'] is False
    assert r['equivalent_gamma_values']==[.01,.1]

def test_no_positive_gap_is_flat():
    r=profile(gaps=(-1.,0.),shares=(0.,.5,1.))
    assert r['support_diagnostics']['positive_gap_rows']==0
    assert r['identified_status']=='not_identified_no_positive_gap'

def test_zero_gamma_does_not_identify_share():
    r=profile(shares=(0.,.5,1.),gammas=(0.,))
    assert r['share_identified'] is False

def test_narrow_gap_ridge_is_reported():
    r=profile(gaps=(1.,1.),shares=(.5,1.))
    assert r['support_diagnostics']['narrow_gap_warning'] is True
    assert r['confidence_region_estimated'] is False

def test_missing_reference_is_unsupported():
    r=profile_mixture(np.array([np.nan,.02]),np.array([1.,3.]),np.array([.02,.02]),np.ones(2),shares=[.5],gammas=[.1])
    assert r['identified_status']=='not_identified_missing_reference_support'

def test_invalid_weights_rejected():
    with pytest.raises(ValueError):
        profile_mixture(np.array([.02]),np.array([1.]),np.array([.02]),np.array([-1.]),shares=[.5],gammas=[.1])

def test_no_supported_set_without_uncertainty_construction():
    r=profile(shares=(.5,1.))
    assert r['supported_parameter_set'] is None
    assert r['gamma_identified'] is False

def test_rank_deficient_controls_are_not_certified():
    r=profile_mixture(np.array([.02,.02]),np.array([1.,3.]),np.array([.02,.02]),np.ones(2),shares=[.5],gammas=[.1],control_design=np.ones((2,2)))
    assert r['support_diagnostics']['control_design_rank_deficient'] is True
    assert r['gamma_identified'] is False

def test_controls_absorbing_gap_are_reported():
    r=profile_mixture(np.array([.02,.02]),np.array([1.,3.]),np.array([.02,.02]),np.ones(2),shares=[.5],gammas=[.1],control_design=np.eye(2))
    assert r['support_diagnostics']['gap_absorbed_by_controls'] is True

def test_constant_gap_has_exact_share_gamma_ridge():
    gamma1=.1
    gamma2=-np.log(1-.5*(1-np.exp(-gamma1)))
    r=profile(gaps=(1.,1.),shares=(.5,1.),gammas=(gamma1,gamma2))
    rows=r['score_surface']
    a=next(x['weighted_mse'] for x in rows if x['sensitive_share']==.5 and x['gamma_per_pp']==gamma1)
    b=next(x['weighted_mse'] for x in rows if x['sensitive_share']==1. and x['gamma_per_pp']==gamma2)
    assert a==pytest.approx(b,abs=1e-18)

def test_nonfinite_total_weight_rejected():
    with pytest.raises(ValueError):
        profile_mixture(np.array([.02,.02]),np.array([1.,3.]),np.array([.02,.02]),np.array([1e308,1e308]),shares=[.5],gammas=[.1])
