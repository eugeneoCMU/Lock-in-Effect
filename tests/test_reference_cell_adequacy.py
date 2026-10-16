import pandas as pd
from reference_cell_adequacy import audit_cell_adequacy


def data():
    rows=[]
    for i in range(12):
        for month in ['201801','201802','201803']:
            rows.append(dict(loan_id=f't{i}',reporting_period=month,at_risk_adjacent=True,
                current_note_gap_pp=.1,lag_loan_age=8.,fico_bucket='740+',ltv_bucket='≤80',property_state='PA',
                adjacent_opening_upb=100.,recorded_payoff_event=int(i==0 and month=='201803')))
    rows.append(dict(loan_id='e',reporting_period='202206',at_risk_adjacent=True,
        current_note_gap_pp=3.,lag_loan_age=8.,fico_bucket='740+',ltv_bucket='≤80',property_state='PA',
        adjacent_opening_upb=1000.,recorded_payoff_event=1))
    return pd.DataFrame(rows)


def test_distinct_borrowers_and_calendar_months_determine_diagnostic_screen():
    r=audit_cell_adequacy(data())
    rows=[x for x in r['coverage'] if x['half_width_pp']==.25]
    assert [x['supported_rows'] for x in rows]==[1,1,0]
    cell=r['cells'][0]
    assert cell['training_loans']==12 and cell['training_rows']==36
    assert cell['training_calendar_months']==3 and cell['training_payoff_events']==1
    assert r['causal_reference_estimated'] is False


def test_repeated_months_from_one_loan_cannot_pass_ten_loan_screen():
    d=data();d=d[(d.loan_id=='t0')|(d.loan_id=='e')]
    r=audit_cell_adequacy(d)
    assert next(x for x in r['coverage'] if x['screen']=='10loans_3months_1event')['supported_rows']==0


def test_evaluation_outcomes_are_not_used():
    a=data();b=a.copy();b.loc[b.reporting_period>'202112','recorded_payoff_event']=0
    assert audit_cell_adequacy(a)==audit_cell_adequacy(b)


def test_missing_covariate_and_unsupported_exposure_stay_in_denominator():
    d=data();d.loc[d.loan_id=='e','property_state']=None
    r=audit_cell_adequacy(d)
    assert all(x['evaluation_opening_upb']==1000 and x['unsupported_opening_upb']==1000 for x in r['coverage'])


def test_development_outcomes_cannot_create_training_events():
    d=data();d.loc[d.loan_id.str.startswith('t'),'reporting_period']=d.loc[d.loan_id.str.startswith('t'),'reporting_period'].str.replace('2018','2022')
    r=audit_cell_adequacy(d)
    assert not r['cells']
    assert all(x['supported_rows']==0 for x in r['coverage'])
