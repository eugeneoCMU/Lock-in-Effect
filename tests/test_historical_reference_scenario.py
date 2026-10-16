import pandas as pd
from historical_reference_scenario import historical_reference_scenario


def frame():
    rows=[]
    for i in range(12):
        for month in ['201801','201802','201803']:
            rows.append(dict(loan_id=f't{i}',reporting_period=month,at_risk_adjacent=True,
                current_note_gap_pp=.1,lag_loan_age=8.,fico_bucket='740+',ltv_bucket='≤80',property_state='PA',
                adjacent_opening_upb=100.,adjacent_payoff_upb=100. if i==0 and month=='201803' else 0.,benchmark_rate=.04))
    for loan,month,state,w,p in [('dev','202204','PA',100.,0.),('e','202206','PA',100.,100.),('u','202206','OH',900.,0.)]:
        rows.append(dict(loan_id=loan,reporting_period=month,at_risk_adjacent=True,current_note_gap_pp=2.,
            lag_loan_age=8.,fico_bucket='740+',ltv_bucket='≤80',property_state=state,
            adjacent_opening_upb=w,adjacent_payoff_upb=p,benchmark_rate=.07))
    return pd.DataFrame(rows)


def test_training_fraction_is_amount_weighted_and_evaluation_never_changes_predictions():
    a=frame();b=a.copy();b.loc[b.reporting_period>'202112','adjacent_payoff_upb']=0.
    ra=historical_reference_scenario(a);rb=historical_reference_scenario(b)
    assert ra['cells']==rb['cells'] and ra['predictions']==rb['predictions']
    assert ra['cells'][0]['historical_fraction']==1/36
    assert ra['causal_reference_estimated'] is False


def test_unmatched_exposure_never_disappears_from_full_target_envelope():
    r=historical_reference_scenario(frame())
    x=next(x for x in r['evaluation'] if x['half_width_pp']==.25 and x['screen']=='10loans_3months' and x['view']=='evaluation')
    assert x['matched_exposure_fraction']==.1
    assert x['conditional_full_fraction_lower']==(100/36)/1000
    assert x['conditional_full_fraction_upper']==(100/36+900)/1000
    assert x['matched_rate_environment_extrapolation_exposure_fraction']==1.


def test_zero_payoff_cell_is_retained_without_hidden_floor_or_event_selection():
    d=frame();d.adjacent_payoff_upb=0.
    r=historical_reference_scenario(d)
    assert r['cells'][0]['historical_fraction']==0.
    assert next(x for x in r['evaluation'] if x['screen']=='10loans_3months')['matched_rows']==1


def test_distinct_loan_count_not_month_count_controls_match():
    d=frame();d=d[~d.loan_id.str.startswith('t')|(d.loan_id=='t0')]
    r=historical_reference_scenario(d)
    assert all(x['matched_rows']==0 for x in r['evaluation'])


def test_target_age_outside_training_range_is_not_extrapolated_silently():
    d=frame();d.loc[d.loan_id=='e','lag_loan_age']=9.
    r=historical_reference_scenario(d)
    assert all(x['matched_rows']==0 for x in r['evaluation'] if x['view']=='evaluation')
