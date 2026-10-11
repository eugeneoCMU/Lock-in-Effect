"""Explicit historical prepayment-state contract for corrected predictions."""
import numpy as np


def prediction_initial_state(pre, *, allow_legacy=False):
    if not pre.index.is_unique:
        raise ValueError('Duplicate cohort identifiers in historical initialization')
    if allow_legacy:
        return (pre.burnout.clip(0, 1).to_dict(), pre.exposure_upb.to_dict(),
                pre.orig_upb_sum.to_dict())
    if "cohort_original_upb" not in pre:
        raise ValueError("Rebuild the fixed cohort_original_upb denominator; legacy cells cannot recover it")
    values = pre[["burnout", "exposure_upb", "cohort_original_upb"]].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values[:, 1] < 0).any() or (values[:, 2] <= 0).any():
        raise ValueError("Historical state requires finite balances and positive fixed denominator")
    if ((values[:, 0] < 0) | (values[:, 0] > 1)).any():
        raise ValueError("Historical burnout must lie between zero and one; do not clip invalid input")
    return (pre.burnout.to_dict(), pre.exposure_upb.to_dict(), pre.cohort_original_upb.to_dict())
