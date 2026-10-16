"""Recorded payoff principal on matched adjacent exposure, never event counts."""
import numpy as np
import pandas as pd

from empirical_readiness import month_ordinal, month_string

COHORT_KEYS = ['vintage', 'coupon', 'fico_bucket', 'ltv_bucket']
AMOUNTS = ['prepaid_upb', 'first_observed_payoff_upb', 'gap_payoff_upb', 'adjacent_opening_upb']


def measure_payoffs(panel: pd.DataFrame, *, cutoff: str) -> pd.DataFrame:
    boundary = month_ordinal(cutoff)
    d = panel.copy()
    keys = [k for k in COHORT_KEYS if k in d] + ['reporting_period']
    if d.duplicated(keys).any():
        raise ValueError('Duplicate cohort-months')
    missing = set(AMOUNTS + ['reporting_period']) - set(d)
    if missing:
        raise ValueError(f'Missing source fields: {sorted(missing)}')
    d['reporting_period'] = d.reporting_period.astype(str)
    ordinals = d.reporting_period.map(month_ordinal)
    d['unallocated_timing_payoff_upb'] = d.first_observed_payoff_upb + d.gap_payoff_upb
    d['adjacent_payoff_upb'] = d.prepaid_upb - d.unallocated_timing_payoff_upb
    issues = [[] for _ in range(len(d))]
    def flag(mask, label):
        for i in np.flatnonzero(np.asarray(mask)):
            issues[i].append(label)
    flag(~np.isfinite(d[AMOUNTS].to_numpy(float)).all(axis=1) | (d[AMOUNTS] < 0).any(axis=1),
         'nonfinite_or_negative_source')
    flag(d.adjacent_payoff_upb < 0, 'negative_adjusted_numerator')
    flag(d.adjacent_opening_upb <= 0, 'zero_adjacent_denominator')
    flag(d.adjacent_payoff_upb > d.adjacent_opening_upb, 'ratio_above_one')
    flag(ordinals > boundary, 'post_cutoff')
    d['measurement_issue'] = [';'.join(x) for x in issues]
    d['measurement_valid'] = d.measurement_issue.eq('')
    d['adjacent_payoff_fraction'] = np.nan
    valid = d.measurement_valid
    d.loc[valid, 'adjacent_payoff_fraction'] = d.loc[valid, 'adjacent_payoff_upb'] / d.loc[valid, 'adjacent_opening_upb']
    # Other views are cash ratios. No transformation to CPR or probabilities.
    for source, name in [('opening_upb', 'opening_cash_ratio'), ('exposure_upb', 'end_balance_cash_ratio')]:
        if source in d:
            d[name] = d.prepaid_upb.div(d[source].where(d[source] > 0))
    d['outcome_label'] = 'amount_weighted_recorded_payoff_principal'
    return d


def audit_gap_support(measurements: pd.DataFrame, benchmark: pd.Series, *, gap_basis: str, lag_months: int) -> dict:
    if gap_basis != 'original_coupon':
        raise ValueError('This source supplies original cohort coupons, not current note rates')
    if isinstance(lag_months, bool) or not isinstance(lag_months, int) or lag_months < 0:
        raise ValueError('Benchmark lag must be a nonnegative integer')
    if benchmark.index.duplicated().any():
        raise ValueError('Duplicate benchmark month')
    b = {str(k): float(v) for k, v in benchmark.items()}
    for key, value in b.items():
        month_ordinal(key)
        if not np.isfinite(value) or not 0 < value < 1:
            raise ValueError('Benchmark must be a finite positive decimal rate')
    d = measurements.copy()
    d['benchmark_month'] = d.reporting_period.map(lambda m: month_string(month_ordinal(str(m)) - lag_months))
    d['benchmark_rate'] = d.benchmark_month.map(b)
    d['gap_pp'] = (d.benchmark_rate - d.coupon) * 100
    valid = d[d.measurement_valid & d.gap_pp.notna() & np.isfinite(d.coupon)]
    positive = valid.loc[valid.gap_pp > 0, 'gap_pp']
    strata = [k for k in COHORT_KEYS if k in d]
    def describe(group):
        return dict(rows=len(group), months=group.reporting_period.nunique(),
            strata=len(group[strata].drop_duplicates()) if strata else 0,
            adjacent_opening_upb=float(group.adjacent_opening_upb.sum()),
            adjacent_payoff_upb=float(group.adjacent_payoff_upb.sum()),
            unknown_timing_payoff_upb=float(group.unallocated_timing_payoff_upb.sum()),
            observed_gap_pp_range=[float(group.gap_pp.min()), float(group.gap_pp.max())] if len(group) else None,
            mean_age_range=[float(group.mean_loan_age.min()), float(group.mean_loan_age.max())]
                if 'mean_loan_age' in group and group.mean_loan_age.notna().any() else None)
    return dict(gap_basis=gap_basis, gap_sign='market_minus_original_coupon', benchmark_lag_months=lag_months,
        benchmark_units='decimal', gap_units='percentage_points',
        missing_benchmark_months=sorted(d.loc[d.benchmark_rate.isna(), 'reporting_period'].unique().tolist()),
        positive_gap_pp_range=[float(positive.min()), float(positive.max())] if len(positive) else None,
        valid_measurement_rows=len(valid), invalid_measurement_rows=int((~d.measurement_valid).sum()),
        by_calendar_year={str(k): describe(g) for k, g in valid.groupby(valid.reporting_period.str[:4])},
        by_vintage={str(k): describe(g) for k, g in valid.groupby('vintage')} if 'vintage' in valid else {},
        by_coupon={str(k): describe(g) for k, g in valid.groupby('coupon')},
        seasoning_views={str(age): describe(valid[valid.mean_loan_age >= age]) for age in [12,24,36,60]}
            if 'mean_loan_age' in valid else {},
        qualification='Coupon bins and concurrent count-weighted cohort mean age; no individual hazards or decision-time borrower covariates',
        overall=describe(valid))
