"""Numerical precision across paired seeds, separate from observational inference."""
import math
import numpy as np

PILOT_SEEDS=(42,31415,271828)

def summarize_monte_carlo(paired_effects):
    a=np.asarray(paired_effects,dtype=float)
    if a.ndim!=1 or not len(a) or np.any(~np.isfinite(a)):
        raise ValueError('Need a nonempty finite one-dimensional effect sequence')
    mean=float(a.mean());n=len(a)
    sd=float(a.std(ddof=1)) if n>1 else None
    mcse=sd/math.sqrt(n) if sd is not None else None
    goal=max(100000.,.05*abs(mean))
    return dict(mean=mean,simulation_sd=sd,mcse=mcse,n_seeds=n,
        sampling_interval_estimated=False,precision_goal_usd_per_1bn=goal,
        precision_goal_met=bool(mcse is not None and mcse<=goal),
        units='USD loan principal per USD 1bn initial principal',
        uncertainty_kind='Simulation randomness across paired seeds only')
