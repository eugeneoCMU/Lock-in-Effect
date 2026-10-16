import pandas as pd
import pytest

from borrower_panel_diagnostics import followup_status, add_asof_gaps, aggregation_comparison


def test_censoring_credit_and_payoff_denominators_stay_separate():
    d=pd.DataFrame(dict(loan_id=['a','b','c','d'],reporting_period=['202509','202406','202401','202403'],
        state=['Current','Current','Prepaid','Defaulted'],recorded_payoff_event=[0,0,1,0],recorded_credit_exit=[0,0,0,1]))
    r=followup_status(d,cutoff='202509')
    assert r['loans']==4
    assert r['counts']==dict(observed_active_at_cutoff=1,missing_followup_before_cutoff=1,recorded_payoff=1,recorded_credit_exit=1)


def test_gap_uses_prior_rate_and_previous_month_benchmark():
    d=pd.DataFrame(dict(reporting_period=['202206'],at_risk_adjacent=[True],
        lag_current_note_rate=[.03],current_note_rate=[.09],coupon=[.031],cohort_coupon=[.03]))
    out=add_asof_gaps(d,pd.Series({'202205':.05,'202206':.06}))
    assert out.iloc[0].current_note_gap_pp==pytest.approx(2.)
    assert out.iloc[0].original_note_gap_pp==pytest.approx(1.9)
    assert out.iloc[0].benchmark_month=='202205'


def test_unknown_prior_rate_is_not_filled_from_original_rate():
    d=pd.DataFrame(dict(reporting_period=['202206'],at_risk_adjacent=[True],
        lag_current_note_rate=[None],coupon=[.03],cohort_coupon=[.03]))
    out=add_asof_gaps(d,pd.Series({'202205':.05}))
    assert pd.isna(out.iloc[0].current_note_gap_pp)


def test_positive_gap_of_mean_is_not_mean_positive_gap():
    d=pd.DataFrame(dict(reporting_period=['202206']*2,stratum_id=['one']*2,
        at_risk_adjacent=[True]*2,adjacent_opening_upb=[100.,100.],
        lag_current_note_rate=[.0275,.0325],coupon=[.0275,.0325],cohort_coupon=[.03,.03]))
    d=add_asof_gaps(d,pd.Series({'202205':.031}))
    cells=aggregation_comparison(d)
    assert cells.iloc[0].mean_borrower_positive_gap_pp==pytest.approx(.175)
    assert cells.iloc[0].positive_gap_at_mean_current_rate_pp==pytest.approx(.1)
    assert cells.iloc[0].hinge_aggregation_difference_pp==pytest.approx(.075)
