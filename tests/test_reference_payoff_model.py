import pandas as pd
import pytest

from reference_payoff_model import fit_reference


def test_reference_does_not_fit_unsupported_target():
    out = fit_reference(pd.DataFrame(), design={'evaluation_kind': 'retrospective'},
                        support={'target_status': 'insufficient_support'})
    assert out['status'] == 'reference_not_estimated'
    assert out['predictions'] == []


def data(evaluation_fraction=.8):
    return pd.DataFrame(dict(reporting_period=['202112', '202204', '202206'],
        adjacent_payoff_fraction=[.01,.2,evaluation_fraction], adjacent_opening_upb=[100.,100.,100.],
        measurement_valid=[True,True,True], gap_pp=[0.,0.,0.], mean_loan_age=[24.,24.,24.],
        vintage=[2020,2020,2020]))


def design():
    return dict(evaluation_kind='retrospective', fit_end='202112', evaluation_start='202206',
        evaluation_end='202509', near_zero_bands_pp=[.25,.5],
        reference_condition='original_coupon_market_gap_within_declared_band',
        decision_time_covariates_verified=False)


def test_evaluation_and_development_outcomes_never_enter_training_summary():
    a = fit_reference(data(), design=design(), support={'target_status':'supported'})
    b = fit_reference(data(.99), design=design(), support={'target_status':'supported'})
    assert a['training_diagnostics'] == b['training_diagnostics']
    assert a['training_diagnostics']['rows'] == 1
    assert a['training_diagnostics']['weighted_recorded_fraction'] == pytest.approx(.01)
    assert a['evaluation_kind'] == 'retrospective'
    assert a['predictions'] == []
    assert 'decision_time_covariates' in a['unidentified_components']


def test_unsupported_predictions_flagged_and_no_transform_of_mean_covariates():
    d = data(); d.loc[2,'gap_pp'] = 3.
    r = fit_reference(d, design=design(), support={'target_status':'supported'})
    assert r['unsupported_evaluation_rows'] == 1
    assert r['borrower_heterogeneity_estimated'] is False
    assert r['causal_no_lock_in_reference_identified'] is False


def test_invalid_time_split_rejected():
    spec = design(); spec['fit_end'] = '202207'
    with pytest.raises(ValueError, match='overlap'):
        fit_reference(data(), design=spec, support={'target_status':'supported'})
