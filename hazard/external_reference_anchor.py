"""Unit/estimand checks for external evidence; no automatic payoff-cap calibration."""
import math

TARGET=dict(outcome='recorded_payoff_fraction',weighting='opening_principal',frequency='monthly',
            estimand='no_lockin_level_difference',statistic='validated_upper_bound')


def equivalent_monthly_probability(period_probability,months):
    p=period_probability
    if isinstance(p,bool) or not isinstance(p,(float,int)) or not math.isfinite(p) or not 0<=p<=1:
        raise ValueError('Probability must be finite in [0,1]')
    if isinstance(months,bool) or not isinstance(months,int) or months<1:raise ValueError('Months must be a positive integer')
    return 1. if p==1 else -math.expm1(math.log1p(-p)/months)


def monthly_effect_illustration(baseline,reduction,months):
    if isinstance(reduction,bool) or not isinstance(reduction,(float,int)) or not math.isfinite(reduction) or not 0<=reduction<=baseline:
        raise ValueError('Reduction must be in [0,baseline]')
    high=equivalent_monthly_probability(baseline,months)
    low=equivalent_monthly_probability(baseline-reduction,months)
    return dict(illustrative_period_baseline=baseline,period_reduction=reduction,months=months,
        monthly_high=high,monthly_low=low,monthly_difference=high-low,
        conversion_assumption='Equal constant conditional monthly hazard reproduces period survival; no claim of actual monthly timing',
        baseline_status='Illustrative use of source population mean, not estimated counterfactual no-lock-in baseline',
        empirically_anchored_payoff_cap=False)


def assess_anchor(source,*,bridges=None):
    bridges=bridges or {};differences={k:dict(source=source.get(k,'not_supplied'),target=v) for k,v in TARGET.items() if source.get(k)!=v}
    assumed=[k for k in differences if bridges.get(k)=='assumed']
    unresolved=[k for k in differences if k not in assumed]
    return dict(status='related_evidence_only' if unresolved else 'conditional_scenario_only' if assumed else 'dimensionally_aligned_transport_unverified',
        differences=differences,assumed_bridges=assumed,unresolved=unresolved,direct_payoff_cap_authorized=False,
        additional_required_checks=['Target population and rate-regime transport','Cause-to-recorded-exit linkage and amount weights',
                                    'Marginal slope to finite no-lock-in contrast','Valid upper-bound construction and uncertainty'],
        qualification='Correct units or assumed bridges do not establish an empirical upper bound for total recorded payoff')
