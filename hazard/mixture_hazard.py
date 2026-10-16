"""Assumed sensitive/insensitive decomposition on the intensity scale.

The reference schedule is the existing zero-gap PSA/covariate probability;
or its hard-max response-OFF counterpart; neither is newly estimated.
No fixed turnover floor is applied after the mixture response.
"""
from contextlib import contextmanager
import numpy as np


def mixture_probability(p_reference, rate_gap, sensitive_share, gamma_per_pp,
                        *, lock_in=True, gap_mode='positive_only'):
    p, gap, s, gamma = np.broadcast_arrays(*[np.asarray(x, dtype=float) for x in
        (p_reference, rate_gap, sensitive_share, gamma_per_pp)])
    if (not all(np.isfinite(x).all() for x in (p, gap, s, gamma))
            or np.any((p < 0) | (p >= 1)) or np.any((s < 0) | (s > 1))
            or np.any(gamma < 0)):
        raise ValueError('Finite inputs require 0 <= p < 1, 0 <= share <= 1, gamma >= 0')
    if gap_mode not in ('positive_only', 'preserve_refinancing'):
        raise ValueError('Unknown gap mode')
    positive_gap = np.maximum(-100. * gap, 0.)
    intensity = -np.log1p(-p)
    if lock_in:
        intensity = intensity * ((1. - s) + s * np.exp(-gamma * positive_gap))
        # Separate structural sensitivity: boost the whole reference intensity
        # for favorable refinancing gaps, using the same response coefficient.
        if gap_mode == 'preserve_refinancing':
            with np.errstate(over='ignore', invalid='ignore'):
                boost = np.exp(gamma * np.maximum(100. * gap, 0.))
                intensity = np.where(intensity == 0, 0., intensity * boost)
    return -np.expm1(-intensity)


def reference_probability(loan_age, burnout, fico_z, ltv_z, *, psa=100., coefs=None,
                          reference_mode='inherited_psa', annual_floor=.04991):
    if reference_mode not in ('inherited_psa', 'matched_max_off'):
        raise ValueError('Unknown reference mode')
    if not np.isfinite(annual_floor) or not 0 <= annual_floor < 1:
        raise ValueError('Reference annual floor must lie in [0,1)')
    from hazard import simulate_freddie_rebuild as pair
    lh = pair.lh
    c = lh.LITERATURE_COEFS if coefs is None else coefs
    baseline = lh.h0_psa(np.asarray(loan_age), psa_speed=psa)
    log_adjustment = (c['beta_fico'] * np.asarray(fico_z)
        + c['beta_ltv'] * np.asarray(ltv_z) + c['beta_burnout'] * np.asarray(burnout))
    with np.errstate(over='ignore'):
        p = baseline * np.exp(log_adjustment)
    if not np.isfinite(p).all() or np.any((p < 0) | (p >= 1)):
        raise ValueError('Reference schedule outside probability support; recalibration required')
    if reference_mode == 'matched_max_off':
        p = np.maximum(p, -np.expm1(np.log1p(-annual_floor)/12.))
    return p


def response_gamma(beta, calibration):
    if calibration == 'legacy_conversion':
        return -np.asarray(beta, dtype=float)
    if calibration == 'illustrative':
        return np.where(np.asarray(beta) == 0, 0., -np.log(.935))
    raise ValueError('Unknown response calibration')


@contextmanager
def mixture_context(sensitive_share, calibration='legacy_conversion', gap_mode='positive_only',
                    reference_mode='inherited_psa'):
    """Adapt the existing engine in one process, restoring all hooks on exit.

    Not thread-safe. Frozen source files and global config files are untouched.
    """
    from hazard import simulate_freddie_rebuild as pair
    mixture_probability(.02, 0., sensitive_share, response_gamma(0., calibration), gap_mode=gap_mode)
    reference_probability(0.,0.,0.,0.,reference_mode=reference_mode)
    original_lh, original_cr = pair.lh.prepay_hazard, pair.cr.prepay_hazard
    def prepay(loan_age, rate_gap, burnout, fico_z, ltv_z,
               beta1=pair.lh.BETA1_PREPAY_MID, coefs=None):
        p0 = reference_probability(loan_age, burnout, fico_z, ltv_z, coefs=coefs, reference_mode=reference_mode)
        return mixture_probability(p0, rate_gap, sensitive_share,
            response_gamma(beta1, calibration), gap_mode=gap_mode)
    pair.lh.prepay_hazard = pair.cr.prepay_hazard = prepay
    try:
        yield
    finally:
        pair.lh.prepay_hazard, pair.cr.prepay_hazard = original_lh, original_cr
