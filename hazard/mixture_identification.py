"""Conditional mixture loss profiles; numerical optima are not identification."""
import numpy as np
from positive_gap_mixture import PositiveGapMixture


def profile_mixture(reference, gap_pp, observed_fraction, weights, *, shares, gammas, control_design=None):
    arrays=[np.asarray(x,dtype=float) for x in (reference,gap_pp,observed_fraction,weights)]
    if any(x.ndim!=1 for x in arrays) or len({x.shape for x in arrays})!=1:
        raise ValueError('Inputs must be aligned one-dimensional arrays')
    reference,gap,observed,w=arrays
    with np.errstate(over='ignore'):
        total_weight=w.sum()
    if not len(w) or np.any(~np.isfinite(w)) or np.any(w<0) or not np.isfinite(total_weight) or total_weight<=0:
        raise ValueError('Need nonnegative finite weights with positive total')
    if np.any(~np.isfinite(gap)) or np.any(~np.isfinite(observed)) or np.any((observed<0)|(observed>1)):
        raise ValueError('Need finite gaps and observed fractions in [0,1]')
    if not shares or not gammas:raise ValueError('Grid must be nonempty')
    missing=~np.isfinite(reference)
    if np.any((reference[~missing]<0)|(reference[~missing]>=1)):
        raise ValueError('Reference probabilities must be in [0,1)')
    positive=gap[(gap>0)&(w>0)]
    diagnostics=dict(positive_gap_rows=int(len(positive)),missing_reference_rows=int(missing.sum()),
        missing_reference_weight_share=float(w[missing].sum()/w.sum()),
        positive_gap_min=float(positive.min()) if len(positive) else None,
        positive_gap_max=float(positive.max()) if len(positive) else None,
        narrow_gap_warning=bool(len(positive) and np.ptp(positive)<.1),
        control_design_audited=False,control_design_rank=None,
        control_design_limit='Interface has no calendar/coupon control matrix; absorption and rank cannot be certified.',
        extrapolated_predictions_used=False)
    if control_design is not None:
        x=np.asarray(control_design,dtype=float)
        if x.ndim!=2 or x.shape[0]!=len(w) or np.any(~np.isfinite(x)):
            raise ValueError('Control design must have aligned finite rows')
        wx=x*np.sqrt(w[:,None]);wg=np.maximum(gap,0)*np.sqrt(w)
        rank=int(np.linalg.matrix_rank(wx))
        residual=wg-wx@np.linalg.lstsq(wx,wg,rcond=None)[0]
        diagnostics.update(control_design_audited=True,control_design_rank=rank,
            control_design_rank_deficient=rank<x.shape[1],
            gap_absorbed_by_controls=bool(np.linalg.norm(residual)<=1e-10*max(1.,np.linalg.norm(wg))),
            residualized_gap_norm=float(np.linalg.norm(residual)),
            control_design_limit='Diagnostic only; residual gap does not establish causal identification.')
    rows=[]
    for s in shares:
        for gamma in gammas:
            model=PositiveGapMixture(s,gamma)
            score=None
            if not missing.any():
                prediction=model.probability(reference,gap)
                score=float(np.dot(w,(prediction-observed)**2)/w.sum())
            rows.append(dict(sensitive_share=float(s),gamma_per_pp=float(gamma),weighted_mse=score))
    best=min(rows,key=lambda r:r['weighted_mse']) if not missing.any() else None
    if missing.any():status='not_identified_missing_reference_support'
    elif not len(positive):status='not_identified_no_positive_gap'
    elif all(s==0 for s in shares):status='not_identified_zero_share'
    elif all(g==0 for g in gammas):status='not_identified_zero_gamma'
    else:status='conditional_score_profile_only'
    equivalent=list(map(float,gammas)) if (not len(positive) or all(s==0 for s in shares)) else []
    return dict(score_surface=rows,identified_status=status,gamma_identified=False,share_identified=False,
        equivalent_gamma_values=equivalent,support_diagnostics=diagnostics,numerical_best_grid_cell=best,
        supported_parameter_set=None,confidence_region_estimated=False,
        score_definition='Exposure-weighted squared error of amount-weighted recorded payoff fractions',
        reference_status='Caller-supplied fixed conditional reference; not estimated by this function',
        uncertainty_criterion='None justified; loss differences do not define confidence or supported sets',
        borrower_level_share_estimated=False)
