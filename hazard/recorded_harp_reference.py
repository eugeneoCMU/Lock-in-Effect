"""Training-only reference fits for recorded mapped-HARP events, not all refinance.

Time is calendar months since pilot opening; it does not separately identify
seasoning or a causal rate effect. Unknown observations are excluded only from
likelihood. Other observed exits must retain their distinct source labels upstream.
"""
from dataclasses import dataclass
from datetime import date
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit


def _month(m):
    if not isinstance(m,str) or len(m)!=7:raise ValueError('month')
    d=date.fromisoformat(m+'-01');return d.year*12+d.month-1


def _arrays(rows,end=None):
    times=[];labels=[];unknown=0
    for row in rows:
        t=_month(row['month'])
        if end is not None and t>end:continue
        y=row['recorded_link_event']
        if y is None:unknown+=1;continue
        if isinstance(y,(float,np.floating)) or not isinstance(y,(bool,int,np.integer)) or y not in (0,1):raise ValueError('recorded_link_event must be0/1or unknown')
        times.append(t-_month('2009-04'));labels.append(y)
    return np.asarray(times,dtype=float),np.asarray(labels,dtype=float),unknown


@dataclass(frozen=True)
class RecordedHARPReferences:
    training_end: str
    training_rows: int
    training_events: int
    excluded_unknown_rows: int
    time_mean: float
    time_scale: float
    frequency_logit: float
    coefficients: np.ndarray
    optimization_gradient_max: float

    def logits(self,months,*,model):
        times=np.array([_month(m)-_month('2009-04') for m in months],dtype=float)
        if model=='frequency':return np.full(times.shape,self.frequency_logit)
        if model=='linear_time':return self.coefficients[0]+self.coefficients[1]*(times-self.time_mean)/self.time_scale
        raise ValueError('Unknown reference model')


def fit_references(rows,*,training_end):
    end=_month(training_end);times,y,unknown=_arrays(rows,end=end)
    if not len(y) or not 0<y.sum()<len(y):raise ValueError('Training needs observed events and nonevents')
    mean=float(times.mean());scale=float(times.std())
    if not scale>0:raise ValueError('Time reference needs multiple training months')
    base=float(np.log(y.mean())-np.log1p(-y.mean()));scaled_time=(times-mean)/scale
    def loss(beta):
        z=beta[0]+beta[1]*scaled_time;return float(np.mean(np.logaddexp(0,z)-y*z))
    def grad(beta):
        residual=expit(beta[0]+beta[1]*scaled_time)-y
        return np.array([np.mean(residual),np.mean(scaled_time*residual)])
    fit=minimize(loss,np.array([base,0.]),jac=grad,method='BFGS',options={'gtol':1e-10,'maxiter':500})
    gradient=float(np.max(np.abs(grad(fit.x))))
    if not np.isfinite(fit.x).all() or gradient>1e-8:raise ValueError('Reference fit failed convergence')
    beta=np.array(fit.x,copy=True);beta.setflags(write=False)
    return RecordedHARPReferences(training_end,len(y),int(y.sum()),unknown,mean,scale,base,beta,gradient)


def score_reference(fit,rows,*,model):
    rows=list(rows);_,y,unknown=_arrays(rows)
    if not len(y):raise ValueError('No observed outcomes to score')
    months=[r['month'] for r in rows if r['recorded_link_event'] is not None];z=fit.logits(months,model=model);p=expit(z)
    return dict(rows=len(y),excluded_unknown_rows=unknown,recorded_events=int(y.sum()),predicted_events=float(p.sum()),log_loss=float(np.mean(np.logaddexp(0,z)-y*z)),brier=float(np.mean((p-y)**2)))
