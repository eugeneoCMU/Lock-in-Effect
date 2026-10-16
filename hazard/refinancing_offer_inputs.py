"""Retrospective, date-lagged PMMS benchmark scenarios, never verified loan offers."""
from datetime import date
import math


def _finite_nonnegative(value,name):
    if isinstance(value,bool):raise ValueError(name)
    try:x=float(value)
    except (TypeError,ValueError):raise ValueError(name)
    if not math.isfinite(x) or x<0:raise ValueError(name)
    return x


def dated_benchmark(observations,*,decision_month,term_months,spread_pp=0.,max_staleness_days=14):
    """Latest valid weekly date before month-start; rates supplied in percent.

    Observations are (ISO date, percent) pairs. Current/future observations do not
    supply values. No interpolation/extrapolation beyond the explicit age limit.
    Latest-vintage historical dates are not asserted to be real-time releases.
    """
    if not isinstance(decision_month,str) or len(decision_month)!=7:raise ValueError('decision_month')
    try:decision=date.fromisoformat(decision_month+'-01')
    except ValueError:raise ValueError('decision_month')
    if isinstance(term_months,bool) or term_months not in (180,360):raise ValueError('Only180/360month benchmarks supported')
    if isinstance(max_staleness_days,bool) or not isinstance(max_staleness_days,int) or max_staleness_days<0:raise ValueError('max_staleness_days')
    spread=_finite_nonnegative(spread_pp,'spread_pp');past={}
    for iso,value in observations:
        observed=date.fromisoformat(iso)
        if observed>=decision:continue
        if observed in past:raise ValueError('Duplicate prior observation date')
        past[observed]=_finite_nonnegative(value,'benchmark_percent')
    if not past:raise ValueError('No prior benchmark')
    observed=max(past);age=(decision-observed).days
    if age>max_staleness_days:raise ValueError('Stale benchmark')
    benchmark=past[observed]
    return dict(decision_month=decision_month,decision_date=decision.isoformat(),observation_date=observed.isoformat(),age_days=age,term_months=term_months,series='MORTGAGE15US' if term_months==180 else 'MORTGAGE30US',benchmark_percent=benchmark,assumed_spread_pp=spread,annual_nominal_rate=(benchmark+spread)/100.,eligibility=None,borrower_offer_verified=False,source_methodology='post2022-11-17' if observed>=date(2022,11,17) else 'pre2022-11-17',information_set='latest-vintage retrospective date-lagged benchmark; release vintage not verified')
