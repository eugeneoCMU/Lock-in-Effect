"""Preserve payoff information and dated borrower/loan disclosures.

No ordinary payoff cause, current qualification, offer access, or behavior is
imputed. Latest-vintage lagged reports are not real-time release vintages.
"""
from datetime import date
from numbers import Real,Integral
import math,re

ORIGINAL_NUMERIC={'original_ltv':'original_ltv','original_cltv':'original_cltv',
    'original_dti':'original_dti','original_borrower_fico':'legacy_original_borrower_fico',
    'original_term_months':'original_term_months'}
ORIGINAL_CATEGORICAL={'original_loan_purpose':'origination_loan_purpose',
    'original_occupancy':'origination_occupancy','original_property_state':'property_state',
    'original_property_type':'property_type','original_units':'units'}

def _month(m):
    if not isinstance(m,str) or re.fullmatch(r'[0-9]{4}-[0-9]{2}',m) is None:raise ValueError('Month must be YYYY-MM')
    d=date.fromisoformat(m+'-01');return d.year*12+d.month-1

def _number(x,name,positive=False):
    if x is None:return None
    if isinstance(x,bool) or not isinstance(x,Real) or not math.isfinite(x) or x<0 or (positive and x<=0):raise ValueError(name)
    return float(x)

def classify_payoff_record(*,event_label,source_code):
    if source_code is not None and not isinstance(source_code,str):raise ValueError('Source removal code must be a string or None')
    raw_code=source_code
    source_code=source_code or ''
    allowed={'linked_harp_payoff','linked_date_conflict','unmapped_payoff_or_maturity','other_source_removal','observed_nonterminal'}
    if event_label not in allowed:raise ValueError('Unknown accepted audit label')
    if event_label in ('linked_harp_payoff','linked_date_conflict','unmapped_payoff_or_maturity') and source_code!='01':raise ValueError('Audit label/code mismatch')
    if event_label=='observed_nonterminal' and source_code:raise ValueError('Nonterminal source code mismatch')
    if event_label=='other_source_removal' and source_code in ('','01'):raise ValueError('Removal source code mismatch')
    categories={'02':'source_third_party_sale','03':'source_short_sale','06':'source_repurchase',
        '09':'source_deed_in_lieu_or_REO_disposition','15':'source_nonperforming_note_sale',
        '16':'source_reperforming_note_sale','96':'source_noncredit_removal'}
    category={'linked_harp_payoff':'accepted_selected_HARP_refinance',
        'linked_date_conflict':'unresolved_link_date_conflict',
        'unmapped_payoff_or_maturity':'unresolved_payoff_or_maturity',
        'observed_nonterminal':'no_observed_terminal_event'}.get(event_label,
            categories.get(source_code,'unrecognized_source_removal'))
    return dict(source_event_label=event_label,source_removal_code=raw_code,
        payoff_information=category,refinancing_known=True if event_label=='linked_harp_payoff' else None,
        ordinary_sale_known=None,
        interpretation='Source origination purpose, unmapped payoff and credit/note-sale codes do not establish ordinary owner sale versus refinancing.')

def decision_information(exposure,*,first_snapshot_month,original_attributes):
    """Enrich an existing exposure; never construct new risk-set membership."""
    decision=_month(exposure['month']);prior=_month(exposure['prior_month'])
    if prior!=decision-1:raise ValueError('Require adjacent prior monthly disclosure')
    upb=_number(exposure['prior_upb'],'prior_upb',positive=True)
    if upb is None:raise ValueError('Positive observed prior balance required')
    coupon=_number(exposure['prior_coupon_percent'],'prior_coupon_percent')
    remaining=exposure['prior_remaining_legal_months']
    if remaining is not None and (isinstance(remaining,bool) or not isinstance(remaining,Integral) or remaining<0):raise ValueError('remaining term')
    label=exposure['recorded_link_event']
    if label is not None and (isinstance(label,bool) or not isinstance(label,Integral) or label not in (0,1)):raise ValueError('Recorded link indicator must be integer0/1/None')
    benchmark=_number(exposure.get('benchmark_percent'),'benchmark_percent')
    observed=exposure.get('benchmark_date')
    if benchmark is not None:
        if not isinstance(observed,str):raise ValueError('Missing benchmark observation date')
        d=date.fromisoformat(observed);cutoff=date.fromisoformat(exposure['month']+'-01')
        age=(cutoff-d).days
        if not 0<age<=14 or age!=exposure.get('benchmark_age_days'):raise ValueError('Benchmark must be dated strictly before decision and nonstale')
    elif observed is not None:raise ValueError('Benchmark date without numeric benchmark')
    supplied=exposure.get('gap_pp')
    signed=coupon-benchmark if coupon is not None and benchmark is not None else None
    if supplied is not None:
        if isinstance(supplied,bool) or not isinstance(supplied,Real) or not math.isfinite(supplied) or signed is None or not math.isclose(signed,supplied,rel_tol=0,abs_tol=1e-10):raise ValueError('Rate gap units or sign mismatch')
    if signed is not None and supplied is None:raise ValueError('Missing supplied gap for available source pair')
    proxy=exposure['payment_proxy']
    if proxy not in ('pass','fail','unknown'):raise ValueError('Unknown payment proxy')
    features=dict(prior_upb=upb,prior_coupon_percent=coupon,
        prior_remaining_legal_months=None if remaining is None else int(remaining),
        prior_delinquency=exposure['prior_delinquency'],payment_history_proxy=proxy,
        benchmark_percent=benchmark,signed_refinance_incentive_gap_pp=signed,
        lockin_positive_gap_pp=max(-signed,0.) if signed is not None else None,
        loan_age_months=None,original_origination_month=None)
    features.update({name:None for name in (*ORIGINAL_NUMERIC,*ORIGINAL_CATEGORICAL)})
    available=first_snapshot_month is not None and _month(first_snapshot_month)<decision
    raw={}
    if available:
        for target,source in ORIGINAL_NUMERIC.items():
            value=original_attributes.get(source);raw[source]=value
            if value in (None,''):continue
            if isinstance(value,bool):raise ValueError('Boolean original attribute')
            try:x=float(value)
            except (ValueError,TypeError):raise ValueError('Nonnumeric original attribute')
            if not math.isfinite(x) or x<0:raise ValueError('Invalid original attribute')
            # Zero or out-of-range credit codes are not current/valid qualification.
            features[target]=None if x==0 or (target=='original_borrower_fico' and not 300<=x<=850) else x
        for target,source in ORIGINAL_CATEGORICAL.items():
            value=original_attributes.get(source);raw[source]=value
            features[target]=None if value in (None,'') else value
        orig=original_attributes.get('origination_month_raw');raw['origination_month_raw']=orig
        if orig not in (None,''):
            if not isinstance(orig,str) or re.fullmatch(r'[0-9]{6}',orig) is None:raise ValueError('Original month format')
            normal=orig[2:]+'-'+orig[:2];origin=_month(normal)
            if origin>decision:raise ValueError('Future origination attribute')
            features['original_origination_month']=normal;features['loan_age_months']=decision-origin
    return dict(month=exposure['month'],prior_observation_month=exposure['prior_month'],
        original_attribute_first_report_month=first_snapshot_month,
        original_attributes_available_before_decision=available,original_attribute_raw=raw,
        benchmark_observation_date=observed,benchmark_age_days=exposure.get('benchmark_age_days'),
        features=features,outcome=dict(kind=exposure['outcome'],recorded_selected_HARP_event=None if label is None else int(label)),
        current_qualification=dict(credit_score=None,ltv=None,dti=None,actual_harp_eligible=None,actual_borrower_offer=None,reason_for_no_refinance=None),
        information_set='Strictly earlier reporting dates in latest-vintage records; historical release availability unverified',
        limits=['Origination attributes are not current qualification.',
            'Payment proxy pass/fail is not actual eligibility or underwriting exclusion.',
            'A no-exit month is not observed refusal or a lifetime non-refinancer label.',
            'Successor terms and final loan outcomes are excluded from features.'])
