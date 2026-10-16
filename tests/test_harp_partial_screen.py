from hazard.harp_partial_screen import payment_history_screen

def hist():return {f'2011-{m:02}':'00' for m in range(1,13)}
def test_complete_pass_does_not_claim_eligibility():
 r=payment_history_screen(hist(),decision_month='2012-01')
 assert r['payment_proxy']=='pass' and r['actual_harp_eligible'] is None and r['actual_underwriting_exclusion'] is None
 assert r['manual_2011_reference_available']
def test_recent_late_and_missing_known_failure_precedence():
 h=hist();h['2011-12']='01';del h['2011-02']
 r=payment_history_screen(h,decision_month='2012-01')
 assert r['payment_proxy']=='fail' and 'recent_six_month_delinquency' in r['failure_reasons']
def test_old_one_30_allowed_but_60_or_two_30_fail():
 h=hist();h['2011-01']='01';assert payment_history_screen(h,decision_month='2012-01')['payment_proxy']=='pass'
 h['2011-01']='02';assert payment_history_screen(h,decision_month='2012-01')['payment_proxy']=='fail'
 h['2011-01']='01';h['2011-02']='01';assert payment_history_screen(h,decision_month='2012-01')['payment_proxy']=='fail'
def test_missing_never_passes():
 h=hist();h['2011-01']='XX';r=payment_history_screen(h,decision_month='2012-01')
 assert r['payment_proxy']=='unknown' and r['known_months']==11
def test_no_current_or_future_leakage():
 h=hist();a=payment_history_screen(h,decision_month='2012-01')
 h['2012-01']='99';h['2050-01']='99';assert a==payment_history_screen(h,decision_month='2012-01')
def test_early_manual_rule_not_applied_retroactively():
 h={f'2009-{m:02}':'00' for m in range(1,13)}
 assert not payment_history_screen(h,decision_month='2010-01')['manual_2011_reference_available']
