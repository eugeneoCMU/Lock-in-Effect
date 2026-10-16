"""Support-gated reference diagnostics on grouped recorded payoff fractions.

This adapter does not turn a historical mean into structural p0. The existing
grouped-calibration scorer is tied to a different frozen panel/denominator and
cannot be reused as an estimator of this adjacent-dollar outcome.
"""
import numpy as np
import pandas as pd

from empirical_readiness import month_ordinal


def fit_reference(data: pd.DataFrame, *, design: dict, support: dict) -> dict:
    fit_end = design.get('fit_end', '202112')
    eval_start = design.get('evaluation_start', '202206')
    eval_end = design.get('evaluation_end', '202509')
    if month_ordinal(fit_end) >= month_ordinal(eval_start):
        raise ValueError('Training and evaluation overlap')
    if month_ordinal(eval_end) < month_ordinal(eval_start):
        raise ValueError('Evaluation ends before it starts')
    bands = design.get('near_zero_bands_pp', [.25, .5])
    if not bands or any(not np.isfinite(b) or b <= 0 for b in bands):
        raise ValueError('Near-zero bands must be declared positive finite widths')
    result = dict(status='reference_not_estimated', estimand='amount_weighted_monthly_recorded_payoff',
        fit_end=fit_end, evaluation_kind=design.get('evaluation_kind', 'retrospective'),
        reference_condition=design.get('reference_condition', 'not_verified'), supported_cells=[], predictions=[],
        unidentified_components=['causal_no_lock_in_reference', 'favorable_refinancing_selection',
                                 'within_cohort_heterogeneity', 'decision_time_covariates'],
        prior_target_status=support.get('target_status', 'not_supplied'),
        borrower_heterogeneity_estimated=False, causal_no_lock_in_reference_identified=False,
        supported_reference_bounds=[0., 1.], bounds_kind='logical_probability_bounds_not_empirical_interval',
        training_diagnostics=dict(rows=0, weighted_recorded_fraction=None),
        band_diagnostics=[], unsupported_evaluation_rows=0)
    if data.empty:
        result['reason'] = 'No observations or designated target lacks support'
        return result
    required = {'reporting_period', 'measurement_valid', 'adjacent_payoff_fraction',
                'adjacent_opening_upb', 'gap_pp'}
    if not required.issubset(data):
        raise ValueError(f'Missing measurement fields: {sorted(required - set(data))}')
    d = data.copy()
    month = d.reporting_period.astype(str)
    month.map(month_ordinal)
    ok = (d.measurement_valid & np.isfinite(d.adjacent_payoff_fraction)
          & d.adjacent_payoff_fraction.between(0, 1) & np.isfinite(d.adjacent_opening_upb)
          & (d.adjacent_opening_upb > 0) & np.isfinite(d.gap_pp))
    train = d[ok & (month <= fit_end)]
    evaluation = d[ok & month.between(eval_start, eval_end)]
    def describe(frame):
        return dict(rows=len(frame), months=frame.reporting_period.nunique(),
            weighted_recorded_fraction=float(np.average(frame.adjacent_payoff_fraction,
                weights=frame.adjacent_opening_upb)) if len(frame) else None,
            observed_fraction_range=[float(frame.adjacent_payoff_fraction.min()),
                                     float(frame.adjacent_payoff_fraction.max())] if len(frame) else None)
    result['training_diagnostics'] = describe(train)
    for band in bands:
        selected = train[train.gap_pp.abs() <= band]
        result['band_diagnostics'].append(dict(half_width_pp=band, **describe(selected)))
    result['evaluation_diagnostics'] = describe(evaluation)
    near = train[train.gap_pp.abs() <= min(bands)]
    # A coarse coverage flag, not permission to predict or an individual-age test.
    outside = evaluation.gap_pp.abs() > min(bands)
    if len(near) and 'vintage' in d:
        outside |= ~evaluation.vintage.isin(near.vintage)
    else:
        outside[:] = True
    if len(near) and 'mean_loan_age' in d:
        outside |= ~evaluation.mean_loan_age.between(near.mean_loan_age.min(), near.mean_loan_age.max())
    result['unsupported_evaluation_rows'] = int(outside.sum())
    result['reason'] = ('Designated inference support is insufficient; alternative bands are retrospective '
        'descriptive diagnostics only. Grouped coupon bins and concurrent mean ages do not establish '
        'decision-time reference conditions or borrower-level refinancing opportunities.')
    return result
