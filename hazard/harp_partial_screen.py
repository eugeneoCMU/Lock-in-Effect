"""As-of monthly payment proxy, not actual HARP underwriting or qualification.

FHFA's retrospective Fannie HARP analytical payment-history measure is applied
as a descriptive proxy. Manual SEL-2011-12 reference is dated separately; unknown
application date and underwriting route prevent actual eligibility/exclusion claims.
"""
from datetime import date


def prior_month(month):
    y,m=map(int,month.split('-'))
    return f'{y-(m==1):04}-{12 if m==1 else m-1:02}'


def _status(value):
    if not isinstance(value,str) or not value.isascii() or not value.isdigit():return None
    n=int(value)
    return n if 0<=n<=99 else None


def payment_history_screen(history,*,decision_month):
    if not isinstance(decision_month,str) or len(decision_month)!=7:raise ValueError('decision_month')
    decision=date.fromisoformat(decision_month+'-01');month=decision_month;months=[];statuses=[]
    for _ in range(12):
        month=prior_month(month);months.append(month);statuses.append(_status(history.get(month)))
    recent=statuses[:6];older=statuses[6:];reasons=[]
    if any(v is not None and v>0 for v in recent):reasons.append('recent_six_month_delinquency')
    if any(v is not None and v>=2 for v in older):reasons.append('older_six_month_60plus_status')
    if sum(v==1 for v in older)>1:reasons.append('multiple_older_30day_statuses')
    known=sum(v is not None for v in statuses)
    outcome='fail' if reasons else 'unknown' if known<12 else 'pass'
    return dict(decision_month=decision_month,lookback_months=months,known_months=known,recent_six_known=sum(v is not None for v in recent),payment_proxy=outcome,failure_reasons=reasons,latest_disclosed_status=statuses[0],manual_2011_reference_available=decision>=date(2011,12,1),actual_harp_eligible=None,actual_underwriting_exclusion=None,underwriting_route='unknown',application_date=None,current_ltv_verified=False,actual_offer_verified=False,interpretation='Strictly prior monthly-status proxy; application/closing status and full qualification unverified')
