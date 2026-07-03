"""4-way cohort stratum identifiers for panel FE and simulation."""

from __future__ import annotations


def build_stratum_id(
    vintage,
    coupon,
    fico_bucket,
    ltv_bucket,
) -> str:
    """e.g. 2020_250_740+_low (coupon in bps)."""
    coupon_bps = int(round(float(coupon) * 10_000))
    return f"{int(vintage)}_{coupon_bps}_{fico_bucket}_{ltv_bucket}"
