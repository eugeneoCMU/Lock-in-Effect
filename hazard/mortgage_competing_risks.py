"""Independent scenario accounting for constant cause-specific intensities.

Inputs are intensities per month, never monthly probabilities. Cause labels are
provided by the caller; this module neither identifies payoff causes nor fits
hazards. Credit/admin exits are principal removals, not assumed cash receipts.
Nothing here changes or reproduces the production simulator's event timing.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real
from typing import Mapping


@dataclass(frozen=True)
class CompetingProbabilities:
    cause_probabilities: Mapping[str, float]
    survival_probability: float


@dataclass(frozen=True)
class PrincipalStep:
    beginning_balance: float
    scheduled_principal: float
    cause_principal: Mapping[str, float]
    ending_balance: float


@dataclass(frozen=True)
class PairedPrincipalContributions:
    first: PrincipalStep
    second: PrincipalStep
    cause_differences: Mapping[str, float]
    total_exit_difference: float
    ending_balance_difference: float


def _finite_real(value: float, name: str, *, nonnegative: bool = True) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number, excluding bool")
    value = float(value)
    if not math.isfinite(value) or (nonnegative and value < 0):
        raise ValueError(f"{name} must be finite" + (" and nonnegative" if nonnegative else ""))
    return value


def _duration(dt_months: float) -> float:
    value = _finite_real(dt_months, "dt_months")
    if value == 0:
        raise ValueError("dt_months must be strictly positive")
    return value


def competing_probabilities(
    intensities: Mapping[str, float], *, dt_months: float = 1.0,
    intensity_unit: str = "per_month", time_unit: str = "months",
) -> CompetingProbabilities:
    """Return mutually exclusive cause probabilities and survival over dt.

    For constant intensities: p_k = lambda_k / sum(lambda) *
    (1 - exp(-sum(lambda) * dt)). Empty causes are rejected; explicit zeros
    represent no exits. Arbitrary labels remain unchanged, including unresolved
    causes. Nonmonthly units must be converted explicitly by the caller.
    """
    if intensity_unit != "per_month" or time_unit != "months":
        raise ValueError("Use intensity_unit='per_month' and time_unit='months'")
    duration = _duration(dt_months)
    if not isinstance(intensities, Mapping) or not intensities:
        raise ValueError("Provide a nonempty mapping of explicit cause intensities")
    checked = {}
    for cause, value in intensities.items():
        if not isinstance(cause, str) or not cause.strip():
            raise ValueError("Cause labels must be nonempty strings")
        checked[cause] = _finite_real(value, f"intensity[{cause}]")
    scale = max(checked.values())
    if scale == 0:
        return CompetingProbabilities(dict.fromkeys(checked, 0.0), 1.0)
    # Scaling keeps cause shares valid even if the finite inputs' sum overflows.
    scaled_sum = math.fsum(value / scale for value in checked.values())
    exposure = (scale * duration) * scaled_sum
    if exposure == 0:
        # Recover a representable exposure if the first product underflows.
        exposure = scale * (duration * scaled_sum)
    event_probability = -math.expm1(-exposure)
    return CompetingProbabilities(
        {cause: (value / scale) / scaled_sum * event_probability
         for cause, value in checked.items()},
        math.exp(-exposure),
    )


def probability_to_monthly_intensity(probability: float, *, dt_months: float = 1.0) -> float:
    """Convert an interval probability p to -log(1-p)/dt per month.

    p=1 has no finite intensity and is rejected. The probability describes the
    supplied interval, so an annual probability requires dt_months=12.
    """
    probability = _finite_real(probability, "probability")
    duration = _duration(dt_months)
    if probability >= 1:
        raise ValueError("probability must be below 1 for finite intensity")
    result = -math.log1p(-probability) / duration
    if not math.isfinite(result):
        raise ValueError("Converted intensity exceeds finite float range")
    return result


def sale_mixture_intensity(
    baseline_intensity_per_month: float, sensitive_share: float,
    gamma_per_pp: float, rate_gap: float, *, gap_unit: str = "pp",
    gamma_unit: str = "per_pp",
) -> float:
    """h0 * [(1-s) + s exp(-gamma * max(gap_pp, 0))], per month.

    h0 is a baseline intensity, s an intensity mixture share, and gamma is per
    percentage point. gap=2 in 'pp' or .02 in 'decimal' both mean two pp.
    This is an imposed scenario restriction, not an estimated sale hazard.
    """
    baseline = _finite_real(baseline_intensity_per_month, "baseline_intensity_per_month")
    share = _finite_real(sensitive_share, "sensitive_share")
    gamma = _finite_real(gamma_per_pp, "gamma_per_pp")
    gap = _finite_real(rate_gap, "rate_gap", nonnegative=False)
    if share > 1:
        raise ValueError("sensitive_share must be between 0 and 1")
    if gap_unit not in ("pp", "decimal") or gamma_unit != "per_pp":
        raise ValueError("Use gap_unit='pp' or 'decimal' and gamma_unit='per_pp'")
    if gamma == 0 or share == 0 or gap <= 0:
        return baseline
    gap_pp = gap * (100 if gap_unit == "decimal" else 1)
    return baseline * ((1 - share) + share * math.exp(-gamma * gap_pp))


def monthly_principal_step(
    beginning_balance: float, scheduled_principal: float,
    intensities: Mapping[str, float],
) -> PrincipalStep:
    """Deterministic one-month expected principal accounting, schedule first.

    The caller supplies scheduled principal; this function does not calculate
    payments. All causes remove post-schedule principal. A credit/default/admin
    amount is tracked under its original label without settlement/recovery or
    cash-runoff assumptions. The production default transition pipeline has a
    different meaning and is deliberately not called here.
    """
    beginning = _finite_real(beginning_balance, "beginning_balance")
    scheduled = _finite_real(scheduled_principal, "scheduled_principal")
    if scheduled > beginning:
        raise ValueError("scheduled_principal cannot exceed beginning_balance")
    probabilities = competing_probabilities(intensities)
    residual = beginning - scheduled
    return PrincipalStep(
        beginning, scheduled,
        {cause: residual * probability for cause, probability in probabilities.cause_probabilities.items()},
        residual * probabilities.survival_probability,
    )


def paired_principal_contributions(
    beginning_balance: float, scheduled_principal: float,
    first_intensities: Mapping[str, float], second_intensities: Mapping[str, float],
) -> PairedPrincipalContributions:
    """First-minus-second cause amounts on the same balance and schedule.

    These are accounting contributions, not causal channel effects: changing
    one intensity changes other causes' probabilities through survival. Missing
    labels in either leg mean zero for that leg; no cause is relabelled.
    """
    first = monthly_principal_step(beginning_balance, scheduled_principal, first_intensities)
    second = monthly_principal_step(beginning_balance, scheduled_principal, second_intensities)
    causes = dict.fromkeys((*first.cause_principal, *second.cause_principal))
    differences = {cause: first.cause_principal.get(cause, 0.0) - second.cause_principal.get(cause, 0.0)
                   for cause in causes}
    return PairedPrincipalContributions(
        first, second, differences, math.fsum(differences.values()),
        first.ending_balance - second.ending_balance,
    )
