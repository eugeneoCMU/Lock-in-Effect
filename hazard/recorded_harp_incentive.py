"""Development-only recorded mapped-HARP prediction from lagged rate benchmarks.

Signed gap is prior coupon minus lagged30year benchmark in percentage points.
No coefficient is a causal elasticity or an estimated offer/exercise parameter.
"""
from dataclasses import dataclass
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from .recorded_harp_reference import _month


def _feature(row,include_time):
    gap=row['gap_pp']
    if isinstance(gap,(bool,np.bool_)):raise ValueError('gap_pp')
    try:gap=float(gap)
    except (TypeError,ValueError):raise ValueError('gap_pp')
    if not np.isfinite(gap):raise ValueError('gap_pp')
    return [gap,_month(row['month'])-_month('2009-04')] if include_time else [gap]


def _collect(rows,include_time,end=None):
    features=[];labels=[];unknown=0
    for row in rows:
        t=_month(row['month'])
        if end is not None and t>end:continue
        y=row['recorded_link_event']
        if y is None:unknown+=1;continue
        if isinstance(y,(float,np.floating)) or not isinstance(y,(bool,int,np.integer)) or y not in (0,1):raise ValueError('recorded_link_event')
        features.append(_feature(row,include_time));labels.append(y)
    return np.asarray(features,dtype=float),np.asarray(labels,dtype=float),unknown


@dataclass(frozen=True)
class RecordedHARPIncentive:
    training_end: str
    include_time: bool
    training_rows: int
    training_events: int
    excluded_unknown_rows: int
    feature_mean: np.ndarray
    feature_scale: np.ndarray
    coefficients: np.ndarray
    gradient_max: float

    def logits(self,rows):
        x=np.array([_feature(r,self.include_time) for r in rows],dtype=float)
        if not len(x):return np.array([],dtype=float)
        return self.coefficients[0]+np.sum(((x-self.feature_mean)/self.feature_scale)*self.coefficients[1:],axis=1)


def fit_incentive(rows,*,training_end,include_time):
    if not isinstance(include_time,bool):raise ValueError('include_time')
    x,y,unknown=_collect(rows,include_time,end=_month(training_end))
    if not len(y) or not 0<y.sum()<len(y):raise ValueError('Training needs events and nonevents')
    mean=x.mean(axis=0);scale=x.std(axis=0)
    if np.any(scale<=0):raise ValueError('Training feature has no variation')
    scaled=(x-mean)/scale;initial=np.zeros(x.shape[1]+1);initial[0]=np.log(y.mean())-np.log1p(-y.mean())
    def logits(b):return b[0]+np.sum(scaled*b[1:],axis=1)
    def loss(b):
        z=logits(b);return float(np.mean(np.logaddexp(0,z)-y*z))
    def grad(b):
        residual=expit(logits(b))-y
        return np.concatenate([[np.mean(residual)],np.mean(scaled*residual[:,None],axis=0)])
    fit=minimize(loss,initial,jac=grad,method='BFGS',options={'gtol':1e-10,'maxiter':500})
    gradient=float(np.max(np.abs(grad(fit.x))))
    if not np.isfinite(fit.x).all() or gradient>1e-8:raise ValueError('Incentive fit did not converge')
    beta=np.array(fit.x,copy=True)
    for a in (mean,scale,beta):a.setflags(write=False)
    return RecordedHARPIncentive(training_end,include_time,len(y),int(y.sum()),unknown,mean,scale,beta,gradient)


def score_incentive(fit,rows):
    rows=list(rows);x,y,unknown=_collect(rows,fit.include_time)
    if not len(y):raise ValueError('No observed outcomes')
    z=fit.coefficients[0]+np.sum(((x-fit.feature_mean)/fit.feature_scale)*fit.coefficients[1:],axis=1);p=expit(z)
    return dict(rows=len(y),excluded_unknown_rows=unknown,recorded_events=int(y.sum()),predicted_events=float(p.sum()),log_loss=float(np.mean(np.logaddexp(0,z)-y*z)),brier=float(np.mean((p-y)**2)))
