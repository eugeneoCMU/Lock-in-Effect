"""Pure scoring of caller-supplied frozen Q1 parameters; no fitting or rescaling.

Gaps are signed percentage points. Elapsed time always starts in April 2009.
Missing outcomes and missing predictors have separate accounting denominators.
"""
from datetime import date
import math
import numbers
import re

_MODELS=('frequency','linear_time','gap_only','gap_and_time')


def _finite(value,name):
    if isinstance(value,bool) or not isinstance(value,numbers.Real):
        raise ValueError(name)
    value=float(value)
    if not math.isfinite(value):raise ValueError(name)
    return value


def _time(month):
    if not isinstance(month,str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}',month):
        raise ValueError('month must be YYYY-MM')
    try:d=date.fromisoformat(month+'-01')
    except ValueError:raise ValueError('month must be YYYY-MM')
    return (d.year-2009)*12+d.month-4


def _vector(value,length,name,positive=False):
    if not isinstance(value,(list,tuple)) or len(value)!=length:raise ValueError(name)
    result=[_finite(x,name) for x in value]
    if positive and any(x<=0 for x in result):raise ValueError(name)
    return result


def frozen_logits(reference,incentive,model,month,gap_pp=None):
    """Return a scalar frozen logit, or None for a gap model's missing gap.

    Only parameters required by the selected model are loaded. Invalid supplied
    parameters or nonmissing features reject rather than trigger a fallback.
    """
    if model not in _MODELS:raise ValueError('Unknown frozen model')
    elapsed=_time(month)
    try:
        if model=='frequency':
            result=_finite(reference['fit_parameters']['frequency_logit'],'frequency_logit')
        elif model=='linear_time':
            p=reference['fit_parameters']
            beta=_vector(p['linear_time_coefficients'],2,'linear_time_coefficients')
            mean=_finite(p['time_mean_training_months_since_april2009'],'time_mean')
            scale=_finite(p['time_scale_training'],'time_scale')
            if scale<=0:raise ValueError('time_scale must be positive')
            result=beta[0]+beta[1]*(elapsed-mean)/scale
        else:
            p=incentive['fit_parameters'][model];n=2 if model=='gap_and_time' else 1
            beta=_vector(p['coefficients_standardized'],n+1,'coefficients_standardized')
            mean=_vector(p['feature_mean'],n,'feature_mean')
            scale=_vector(p['feature_scale'],n,'feature_scale',positive=True)
            if gap_pp is None:return None
            features=[_finite(gap_pp,'gap_pp')]+([elapsed] if n==2 else [])
            result=beta[0]+sum(beta[j+1]*(x-mean[j])/scale[j] for j,x in enumerate(features))
    except (KeyError,TypeError) as exc:
        raise ValueError('Malformed frozen model parameters') from exc
    if not math.isfinite(result):raise ValueError('Nonfinite frozen logit')
    return float(result)


def score_rows(reference,incentive,model,rows):
    """Score known labels with available features; preserve all exposure counts."""
    # Validate model parameters even for an empty cohort.
    frozen_logits(reference,incentive,model,'2009-04',None)
    exposure=unknown=missing=events=0;probabilities=[];losses=[];squares=[]
    for row in rows:
        exposure+=1
        try:month=row['month'];label=row['recorded_link_event']
        except (KeyError,TypeError) as exc:raise ValueError('Malformed scoring row') from exc
        _time(month)
        if label is None:
            unknown+=1;continue
        if not isinstance(label,numbers.Integral) or label not in (0,1):
            raise ValueError('recorded_link_event must be integer0/1 or None')
        z=frozen_logits(reference,incentive,model,month,row.get('gap_pp'))
        if z is None:
            missing+=1;continue
        probability=1/(1+math.exp(-z)) if z>=0 else math.exp(z)/(1+math.exp(z))
        probabilities.append(probability);events+=int(label)
        losses.append(max(z,0)-label*z+math.log1p(math.exp(-abs(z))))
        squares.append((probability-label)**2)
    n=len(probabilities)
    return dict(exposure_rows=exposure,scored_rows=n,excluded_unknown_outcomes=unknown,
                excluded_missing_feature=missing,recorded_events=events,
                predicted_events=math.fsum(probabilities),
                log_loss=math.fsum(losses)/n if n else None,
                brier=math.fsum(squares)/n if n else None)
