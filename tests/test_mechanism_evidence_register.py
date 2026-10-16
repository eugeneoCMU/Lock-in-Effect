import pytest
from hazard.mechanism_evidence_register import summarize_causes


def test_unmatched_payoff_is_not_a_sale_or_nonrefinance():
    r = summarize_causes([{'event':'unmatched_payoff','month':'201501'}], population_id='synthetic',coverage_start='200904',coverage_end='201609')
    assert r['unknown_payoff_cause'] == 1
    assert r['verified_sales'] == r['verified_nonrefinances'] == 0


def test_unverified_claims_conflicts_and_outside_window_stay_separate():
    events = [{'event':'verified_sale','month':'201501'}, {'event':'linked_harp_payoff','month':'201501'}, {'event':'linked_date_conflict','month':'201501'}, {'event':'other_source_removal','month':'201501'}, {'event':'unknown_missing_report','month':'201501'}, {'event':'linked_harp_payoff','month':'201701'}]
    r=summarize_causes(events,population_id='x',coverage_start='200904',coverage_end='201609')
    assert r['verified_sales']==0
    assert r['unknown_payoff_cause']==2
    assert r['verified_selected_refinances']==1
    assert r['credit_or_other_source_removals']==r['missing_follow_up']==r['outside_coverage']==1
    assert r['refinance_classification_count_bounds']==[1,3]


def test_verified_sale_requires_evidence_and_no_double_count():
    r=summarize_causes([{'event':'verified_sale','month':'201501','source_verified':True,'evidence_id':'deed-1'}],population_id='x',coverage_start='201501',coverage_end='201501')
    assert r['verified_sales']==1
    assert r['verified_nonrefinances']==0


def test_bad_month_rejected():
    with pytest.raises(ValueError):
        summarize_causes([{'event':'unmatched_payoff','month':'201513'}],population_id='x',coverage_start='201501',coverage_end='201512')


@pytest.mark.parametrize('month',['20-15-01','2015-0-1'])
def test_malformed_month_format_rejected(month):
    with pytest.raises(ValueError):
        summarize_causes([{'event':'unmatched_payoff','month':month}],population_id='x',coverage_start='201501',coverage_end='201512')
