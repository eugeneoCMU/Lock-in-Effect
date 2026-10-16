import pandas as pd

from borrower_origination_reference import select_origination_ids, describe_landmark_selection, reference_support


def test_origination_sample_is_order_invariant_and_does_not_require_may_survival():
    ids=['F21Q1'+str(i) for i in range(100)]
    a=select_origination_ids(ids,n=10,seed='fixed')
    b=select_origination_ids(list(reversed(ids)),n=10,seed='fixed')
    assert a==b and len(set(a))==10


def test_pre_may_exits_remain_in_origination_denominator():
    d=pd.DataFrame(dict(loan_id=['a','b','b'],reporting_period=['202112','202205','202509'],
        state=['Prepaid','Current','Current'],balance=[0.,100.,90.],
        recorded_payoff_event=[1,0,0],recorded_credit_exit=[0,0,0]))
    r=describe_landmark_selection(d,selected_loans=2)
    assert r['selected_origination_loans']==2
    assert r['pre_may_payoff_loans']==1
    assert r['may_active_loans']==1
    assert r['population_conditioned_on_may_survival'] is False


def test_reference_views_never_pool_evaluation_outcomes_into_training():
    d=pd.DataFrame(dict(reporting_period=['202112','202204','202206'],
        at_risk_adjacent=[True]*3,current_note_gap_pp=[.1,.1,.1],lag_loan_age=[6.,10.,12.],
        adjacent_opening_upb=[100.]*3,adjacent_payoff_upb=[0.,0.,100.],
        recorded_payoff_event=[0,0,1],loan_id=['a','b','c']))
    r=reference_support(d)
    train=next(c for c in r['cells'] if c['view']=='training' and c['half_width_pp']==.25)
    assert train['recorded_payoff_events']==0
    assert train['rows']==1
    assert r['causal_reference_estimated'] is False
    assert r['reference_predictions_generated'] is False
    assert r['prior_designated_support_verdict']=='insufficient_support'
