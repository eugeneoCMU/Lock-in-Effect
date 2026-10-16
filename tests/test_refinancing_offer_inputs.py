import pytest
from hazard.refinancing_offer_inputs import dated_benchmark

DATA=[('2009-02-26',5.1),('2009-03-26',4.9),('2009-04-02',4.8),('2009-04-30',4.7)]
def test_strict_prior_date_and_percent_conversion():
 r=dated_benchmark(DATA,decision_month='2009-04',term_months=360)
 assert r['observation_date']=='2009-03-26' and r['annual_nominal_rate']==pytest.approx(.049)
 assert r['eligibility'] is None and r['borrower_offer_verified'] is False

def test_future_poison_cannot_change_input():
 a=dated_benchmark(DATA[:2],decision_month='2009-04',term_months=180)
 assert a==dated_benchmark(DATA+[('2050-01-01',99)],decision_month='2009-04',term_months=180)

def test_missing_stale_and_unsupported_term_fail_closed():
 for rows in [[],[('2009-02-26',5.1)]]:
  with pytest.raises(ValueError):dated_benchmark(rows,decision_month='2009-04',term_months=180)
 with pytest.raises(ValueError):dated_benchmark(DATA,decision_month='2009-04',term_months=240)

def test_duplicate_dates_and_invalid_values_rejected():
 for rows in [[('2009-03-26',4.9)]*2,[('2009-03-26',float('nan'))],[('2009-03-26',-1)]]:
  with pytest.raises(ValueError):dated_benchmark(rows,decision_month='2009-04',term_months=180)

def test_spread_is_explicit_scenario_not_observed_rate():
 r=dated_benchmark(DATA,decision_month='2009-04',term_months=180,spread_pp=1.)
 assert r['annual_nominal_rate']==pytest.approx(.059)
 assert r['benchmark_percent']==4.9 and r['assumed_spread_pp']==1
