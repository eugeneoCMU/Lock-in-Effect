import pandas as pd
from reference_time_environment import audit_time_environment


def frame():
    rows=[]
    for i in range(35):
        for month in ['201801','201802','201803','201804','201805','201806']:
            rows.append(dict(loan_id=f't{i}',reporting_period=month,at_risk_adjacent=True,
                current_note_gap_pp=.1,lag_loan_age=8.,fico_bucket='740+',ltv_bucket='≤80',property_state='PA',
                adjacent_opening_upb=100.,recorded_payoff_event=int(i<5 and month=='201806'),benchmark_rate=.04))
    for name,rate,balance in [('inside',.04,100.),('outside',.07,900.)]:
        rows.append(dict(loan_id=name,reporting_period='202206',at_risk_adjacent=True,
            current_note_gap_pp=2.,lag_loan_age=8.,fico_bucket='740+',ltv_bucket='≤80',property_state='PA',
            adjacent_opening_upb=balance,recorded_payoff_event=1,benchmark_rate=rate))
    return pd.DataFrame(rows)


def test_time_and_rate_coverage_do_not_hide_unsupported_exposure():
    r=audit_time_environment(frame())
    x=next(x for x in r['coverage'] if x['half_width_pp']==.25 and x['screen']=='30loans_6months_5events')
    assert x['base_supported_exposure_fraction']==1.
    assert x['rate_range_supported_exposure_fraction']==.1
    assert x['two_training_years_exposure_fraction']==0.
    assert x['quarter_concentration_le_half_exposure_fraction']==1.
    assert r['cells'][0]['training_years']==1
    assert r['causal_reference_estimated'] is False


def test_evaluation_outcomes_do_not_enter_any_result():
    a=frame();b=a.copy();b.loc[b.reporting_period>'202112','recorded_payoff_event']=0
    assert audit_time_environment(a)==audit_time_environment(b)


def test_one_year_later_training_does_not_inflate_distinct_months():
    d=frame();d.loc[d.loan_id=='t34','reporting_period']=d.loc[d.loan_id=='t34','reporting_period'].str.replace('2018','2019')
    r=audit_time_environment(d)
    c=r['cells'][0]
    assert c['training_years']==2 and c['training_calendar_months']==12


def test_development_rates_and_events_cannot_enlarge_training_range():
    d=frame();dev=d[d.loan_id=='t0'].copy();dev.loan_id='dev';dev.reporting_period=dev.reporting_period.str.replace('2018','2022');dev.benchmark_rate=.07
    r=audit_time_environment(pd.concat([d,dev],ignore_index=True))
    assert all(c['benchmark_max_pct']==4. for c in r['cells'])


def test_missing_target_rate_stays_in_target_denominator():
    d=frame();d.loc[d.loan_id=='outside','benchmark_rate']=float('nan')
    r=audit_time_environment(d)
    assert all(x['evaluation_opening_upb']==1000. for x in r['coverage'])
    assert all(x['rate_range_supported_exposure_fraction']==.1 for x in r['coverage'])
