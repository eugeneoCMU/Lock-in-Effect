"""Isolated, externally calibrated sale scenarios; never fitted loan-level hazards.

FHFA WP24-03 (August 2024), Table 2, is a linear probability model:
0.176 percentage points of quarterly sale probability per percentage point of
coupon-minus-predicted-market rate delta. Its 18.1% divides that slope by the
sample mean probability, NOT each borrower's conditional probability.

All inputs here use decimal probabilities and market-minus-coupon gap in
percentage points (7%-4% = 3.0). No implicit annual/monthly baseline or /3
coefficient conversion is permitted. Monthly intensity assumes a constant
standalone sale process over the quarter. With competing risks present, this
is not an identified cause-specific intensity or quarterly cumulative incidence.
"""

from dataclasses import dataclass
import math
from numbers import Real
from typing import Literal

FHFA_QUARTERLY_ABSOLUTE_SLOPE = 0.00176
FHFA_RELATIVE_SAMPLE_MEAN_SLOPE = 0.181
SOURCE_URL = "https://www.fhfa.gov/document/wp2403.pdf"
FORM = Literal["lpm_absolute", "relative_linear_transport", "relative_exponential_transport"]


def _finite(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a real numeric scalar, not a boolean")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def _probability(value: float, name: str) -> float:
    value = _finite(value, name)
    if not 0.0 <= value < 1.0:
        raise ValueError(f"{name} must be a decimal probability in [0, 1)")
    return value


def quarterly_probability_to_monthly_intensity(probability: float) -> float:
    """Return lambda/month = -log(1-p_quarter)/3; p=1 has no finite rate."""
    return -math.log1p(-_probability(probability, "quarterly_probability")) / 3.0


def quarterly_probability_to_monthly_probability(probability: float) -> float:
    """Return p_month=1-exp(-lambda/month); distinct from intensity."""
    return -math.expm1(-quarterly_probability_to_monthly_intensity(probability))


@dataclass(frozen=True)
class SaleScenario:
    quarterly_reference_probability: float
    quarterly_response_probability: float
    monthly_reference_probability: float
    monthly_response_probability: float
    monthly_reference_intensity: float
    monthly_response_intensity: float
    lock_in_gap_pp: float
    functional_form: str
    baseline_provenance: str
    evidence_status: str = "externally_calibrated_scenario_not_fitted"
    intensity_interpretation: str = "standalone_constant_sale_only_per_month"
    source_url: str = SOURCE_URL


def sale_scenario(
    *,
    quarterly_reference_probability: float,
    baseline_provenance: str,
    lock_in_gap_pp: float,
    functional_form: FORM,
) -> SaleScenario:
    """Evaluate a zero-gap reference against a nonnegative lock-in gap.

    lpm_absolute transports the published absolute quarterly slope: p1=p0-
    .00176*g. relative_linear_transport instead assumes p1=p0*(1-.181*g),
    which agrees with the reported normalization only at the source sample
    mean (subject to rounding). relative_exponential_transport assumes
    p1=p0*(1-.181)**g; this is an added bounded functional-form sensitivity,
    not the study's regression. Invalid LPM/linear extrapolations raise;
    silently clipping them would add an unapproved floor assumption.

    A supplied baseline must describe a quarterly at-risk home-sale probability
    at zero gap, its population and period. A nonempty provenance label is an
    audit requirement, not empirical verification of that baseline.
    """
    p0 = _probability(quarterly_reference_probability, "quarterly_reference_probability")
    if not isinstance(baseline_provenance, str) or not baseline_provenance.strip():
        raise ValueError("baseline_provenance is required")
    gap = _finite(lock_in_gap_pp, "lock_in_gap_pp")
    if gap < 0:
        raise ValueError("lock_in_gap_pp must be nonnegative (market minus coupon, percentage points)")
    if functional_form == "lpm_absolute":
        p1 = p0 - FHFA_QUARTERLY_ABSOLUTE_SLOPE * gap
    elif functional_form == "relative_linear_transport":
        factor = 1.0 - FHFA_RELATIVE_SAMPLE_MEAN_SLOPE * gap
        if factor < 0:
            raise ValueError("relative-linear factor is negative; extrapolation requires another assumption")
        p1 = p0 * factor
    elif functional_form == "relative_exponential_transport":
        p1 = p0 * math.exp(math.log1p(-FHFA_RELATIVE_SAMPLE_MEAN_SLOPE) * gap)
    else:
        raise ValueError("unknown functional_form")
    p1 = _probability(p1, "quarterly_response_probability")
    return SaleScenario(
        p0, p1,
        quarterly_probability_to_monthly_probability(p0),
        quarterly_probability_to_monthly_probability(p1),
        quarterly_probability_to_monthly_intensity(p0),
        quarterly_probability_to_monthly_intensity(p1),
        gap, functional_form, baseline_provenance.strip(),
    )
