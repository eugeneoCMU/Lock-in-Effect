import pandas as pd
from borrower_reference_transport import audit_reference_transport


def fixture():
    return pd.DataFrame(dict(loan_id=['train','eval1','eval2','eval3'],
        reporting_period=['202112','202206','202206','202206'],at_risk_adjacent=[True]*4,
        current_note_gap_pp=[.1,2.,2.,2.],lag_loan_age=[8.,8.,8.,24.],
        fico_bucket=['740+','740+','<680','740+'],ltv_bucket=['≤80']*4,
        property_state=['PA']*4,adjacent_opening_upb=[100.,100.,200.,700.],
        recorded_payoff_event=[0,1,1,1]))


def test_joint_support_uses_exposure_and_keeps_unsupported_bucket():
    r=audit_reference_transport(fixture())
    row=next(x for x in r['coverage'] if x['half_width_pp']==.25 and x['controls']=='age_fico_ltv')
    assert row['evaluation_rows']==3 and row['supported_rows']==1
    assert row['evaluation_opening_upb']==1000.
    assert row['supported_opening_upb']==100.
    assert row['unsupported_opening_upb']==900.
    assert row['supported_exposure_fraction']==.1
    assert r['causal_reference_estimated'] is False


def test_evaluation_outcomes_do_not_change_coverage():
    a=fixture();b=a.copy();b.loc[b.reporting_period>'202112','recorded_payoff_event']=0
    assert audit_reference_transport(a)==audit_reference_transport(b)


def test_empty_training_does_not_manufacture_support():
    a=fixture();a.loc[0,'current_note_gap_pp']=1.
    r=audit_reference_transport(a)
    assert all(x['supported_rows']==0 for x in r['coverage'])
    assert all(x['supported_exposure_fraction']==0 for x in r['coverage'])


def test_missing_covariate_never_matches_missing_training_covariate():
    a=fixture();a.loc[0,'fico_bucket']=None;a.loc[1,'fico_bucket']=None
    r=audit_reference_transport(a)
    x=next(x for x in r['coverage'] if x['half_width_pp']==.25 and x['controls']=='age_fico_ltv')
    assert x['supported_rows']==0


def test_earlier_training_is_explicit_and_target_denominator_does_not_change():
    a=fixture();a.loc[0,'reporting_period']='201812'
    baseline=audit_reference_transport(a)
    extended=audit_reference_transport(a,training_start='201801')
    assert baseline['coverage'][0]['supported_rows']==0
    assert extended['coverage'][0]['supported_rows']==2
    assert extended['coverage'][0]['evaluation_rows']==3
    assert extended['design']['training']==['201801','202112']
