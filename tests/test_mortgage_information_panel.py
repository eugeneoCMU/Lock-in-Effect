"""Unknown payoff causes and strictly prior information must stay distinct."""
from copy import deepcopy
import importlib
import pytest

def api():return importlib.import_module('hazard.mortgage_information_panel')

def exposure(**changes):
    r=dict(month='2014-01',prior_month='2013-12',prior_upb=100000.,
        prior_coupon_percent=6.,prior_remaining_legal_months=294,prior_delinquency='00',
        outcome='observed_no_recorded_exit',recorded_link_event=0,payment_proxy='pass',
        gap_pp=2.,benchmark_date='2013-12-26',benchmark_percent=4.,benchmark_age_days=6,
        actual_harp_eligible=None,actual_offer_verified=False)
    r.update(changes);return r

def attributes(**changes):
    r=dict(original_ltv='80',original_cltv='80',original_dti='40',
        legacy_original_borrower_fico='720',origination_month_raw='062008',
        original_term_months='360',origination_loan_purpose='P',origination_occupancy='P',
        property_state='PA',property_type='SF',units='1',current_borrower_fico='800')
    r.update(changes);return r

def test_unmapped_payoff_never_becomes_a_sale_or_nonrefinance():
    r=api().classify_payoff_record(event_label='unmapped_payoff_or_maturity',source_code='01')
    assert r['refinancing_known'] is None and r['ordinary_sale_known'] is None
    assert r['payoff_information']=='unresolved_payoff_or_maturity'

def test_accepted_link_is_distinct_from_date_conflict():
    good=api().classify_payoff_record(event_label='linked_harp_payoff',source_code='01')
    bad=api().classify_payoff_record(event_label='linked_date_conflict',source_code='01')
    assert good['refinancing_known'] is True
    assert bad['refinancing_known'] is None and bad['payoff_information']=='unresolved_link_date_conflict'

@pytest.mark.parametrize('code',['02','03','09','06','15','16'])
def test_credit_and_administrative_codes_are_not_ordinary_turnover(code):
    r=api().classify_payoff_record(event_label='other_source_removal',source_code=code)
    assert r['ordinary_sale_known'] is None and r['refinancing_known'] is None
    assert r['payoff_information']!='ordinary_home_sale'

def test_nonterminal_is_not_a_lifetime_nonrefinancer_label():
    r=api().classify_payoff_record(event_label='observed_nonterminal',source_code='')
    assert r['payoff_information']=='no_observed_terminal_event'
    assert r['refinancing_known'] is None

def test_original_null_removal_code_is_preserved_for_nonterminal_source():
    r=api().classify_payoff_record(event_label='observed_nonterminal',source_code=None)
    assert r['source_removal_code'] is None
    assert r['payoff_information']=='no_observed_terminal_event'

def test_features_are_prior_and_original_covariates_remain_original():
    r=api().decision_information(exposure(),first_snapshot_month='2008-05',original_attributes=attributes())
    f=r['features']
    assert f['prior_upb']==100000 and f['original_ltv']==80 and f['original_borrower_fico']==720
    assert f['loan_age_months']==67 and f['lockin_positive_gap_pp']==0
    assert f['signed_refinance_incentive_gap_pp']==2
    assert r['current_qualification']==dict(credit_score=None,ltv=None,dti=None,actual_harp_eligible=None,actual_borrower_offer=None,reason_for_no_refinance=None)
    assert r['outcome']['kind']=='observed_no_recorded_exit'
    assert 'recorded_link_event' not in f and 'current_borrower_fico' not in f

def test_positive_lockin_gap_has_correct_sign():
    r=api().decision_information(exposure(prior_coupon_percent=3.,gap_pp=-1.),first_snapshot_month='2008-05',original_attributes=attributes())
    assert r['features']['lockin_positive_gap_pp']==1.

def test_future_snapshot_poison_cannot_supply_features():
    a=api().decision_information(exposure(),first_snapshot_month='2014-01',original_attributes=attributes())
    b=api().decision_information(exposure(),first_snapshot_month='2050-01',original_attributes={'original_ltv':'bad future data'})
    for r in (a,b):
        assert r['original_attributes_available_before_decision'] is False
        assert r['features']['original_ltv'] is None and r['features']['original_borrower_fico'] is None

def test_proxy_failure_and_missing_values_do_not_imply_actual_exclusion():
    r=api().decision_information(exposure(payment_proxy='fail'),first_snapshot_month='2008-05',original_attributes=attributes(original_dti=None,legacy_original_borrower_fico=None))
    assert r['features']['original_dti'] is None and r['features']['original_borrower_fico'] is None
    assert r['current_qualification']['actual_harp_eligible'] is None

@pytest.mark.parametrize('change',[{'prior_month':'2013-11'},{'benchmark_date':'2014-01-01'},{'gap_pp':99},{'prior_upb':0},{'prior_coupon_percent':float('nan')},{'recorded_link_event':True}])
def test_invalid_timing_units_or_denominators_fail_closed(change):
    with pytest.raises(ValueError):api().decision_information(exposure(**change),first_snapshot_month='2008-05',original_attributes=attributes())

def test_inputs_are_not_modified():
    e=exposure();a=attributes();before=(deepcopy(e),deepcopy(a))
    api().decision_information(e,first_snapshot_month='2008-05',original_attributes=a)
    assert (e,a)==before
