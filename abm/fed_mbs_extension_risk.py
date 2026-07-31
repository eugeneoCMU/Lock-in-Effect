"""
Federal Reserve MBS Extension Risk Delta Analysis
===================================================
Quantifies how the high-interest-rate environment has caused "extension risk"
in the Fed's Mortgage-Backed Securities portfolio, trapping liquidity well
beyond the pace targeted by the Quantitative Tightening (QT) programme.

Data sources:
  * FRED (Federal Reserve Economic Data) — balance-sheet & macro series
  * NY Fed Markets API — SOMA MBS holdings (preferred roll-off source)
"""

import datetime
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Union

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from fredapi import Fred

from paths import (
    ABM_CPR_SURFACE_CSV,
    ABM_LOCKIN_RESULTS_CSV,
    CPR_DIAGNOSTIC_PNG,
    MBS_DASHBOARD_PNG,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from common.qt_window import (  # noqa: E402
    POST_QT_TARGET_B,
    QT_END,
    QT_RAMP_END,
    QT_START,
    QT_TARGET_FULL_B,
    QT_TARGET_RAMP_B,
    assert_qt_window_only,
    compute_qt_target_series,
    expected_qt_active_months,
    qt_active_frame,
    qt_active_mask,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
from common.fred_key import get_fred_api_key  # noqa: E402
FRED_API_KEY = get_fred_api_key()
START_DATE = "2021-01-01"
BASELINE_START = "2017-01-01"  # earlier start to compute 2017-2019 baselines
DEFAULT_COHORT_ASOF = pd.Timestamp("2026-06-24")  # pinned SOMA as-of for fallbacks

# ---------------------------------------------------------------------------
# Dynamic Macroeconomic Friction parameters
# ---------------------------------------------------------------------------
BASE_FRICTION = 0.07            # 7% baseline transaction cost
SEARCH_PENALTY_CAP = 0.02       # max +200 bps when inventory is at its lowest
SENTIMENT_BASELINE = 85.0       # healthy consumer-sentiment baseline (UMCSENT)
SENTIMENT_PENALTY_PER_PT = 0.0005   # +5 bps per point below baseline
SENTIMENT_PENALTY_CAP = 0.015   # max +150 bps during peak fear

# ---------------------------------------------------------------------------
# Scheduled amortization — the principal component of each monthly mortgage
# payment that flows through even if nobody prepays.  Must match the ABM's
# origination assumptions so the macro model and the micro model stay aligned.
# ---------------------------------------------------------------------------
PORTFOLIO_COUPON = 0.03         # 3.0% weighted-average coupon (pandemic cohort)
PORTFOLIO_TERM = 360            # 30-year fixed = 360 months
PORTFOLIO_ORIGIN = pd.Timestamp("2020-06-01")  # approximate origination midpoint

# Voluntary partial prepayments (curtailments), scaled by real disposable income.
# Magnitude: ~1.2% CPR annualized from GSE daily-prepayment-report curtailment
# estimates (machinesp.com, Sept-2024 cohort). Driver: disposable income
# availability (SSRN 4949187, "Understanding Excess Repayment").
CURTAILMENT_CPR_HEALTHY = 0.012       # full curtailment at healthy income growth
CURTAILMENT_INCOME_HEALTHY_PCT = 4.0  # real disposable income YoY (%) -> 100%
CURTAILMENT_INCOME_STRESSED_PCT = -2.0  # real disposable income YoY (%) -> 0%

# UMBS/GNMA remittance settlement lag kernel (lags 0/1/2 months; mass-conserving).
# Sourced from standard 55-day / ~50-day agency remittance cycles, not tuned.
SETTLEMENT_LAG_KERNEL = [0.10, 0.60, 0.30]
BURNOUT_LOOKBACK_MONTHS = 36  # max months of pre-QT burn-in per cohort


def scheduled_amortization_smm(annual_rate: float, term_months: int,
                               months_elapsed: int) -> float:
    """
    Monthly scheduled principal as a fraction of the remaining balance.

    For a standard fixed-rate, fully amortizing mortgage:
        scheduled_principal_k = payment - r * balance_k
    where balance_k is the remaining balance after k payments and r is the
    monthly rate.  Dividing by balance_k gives the single-month scheduled
    mortality (SMM-sched).
    """
    r = annual_rate / 12
    n = term_months
    k = months_elapsed
    if r == 0:
        return 1.0 / (n - k) if k < n else 0.0
    growth_k = (1 + r) ** k
    growth_n = (1 + r) ** n
    balance_ratio = (growth_n - growth_k) / (growth_n - 1)
    if balance_ratio <= 0:
        return 0.0
    payment_ratio = r * growth_n / (growth_n - 1)
    sched_principal = payment_ratio - r * balance_ratio
    return sched_principal / balance_ratio


def scheduled_amortization_series(index: pd.DatetimeIndex,
                                  coupon: float = PORTFOLIO_COUPON,
                                  term: int = PORTFOLIO_TERM,
                                  origin: pd.Timestamp = PORTFOLIO_ORIGIN,
                                  ) -> pd.Series:
    """
    Build a per-month scheduled-amortization SMM series for the portfolio,
    increasing over time as the loans season.
    """
    months_since = np.clip(
        (index.year - origin.year) * 12 + (index.month - origin.month),
        a_min=0, a_max=None,
    )
    smm = pd.Series(
        [scheduled_amortization_smm(coupon, term, int(k)) for k in months_since],
        index=index,
    )
    return smm


def curtailment_series(real_income_yoy_pct: pd.Series,
                       healthy_pct: float = CURTAILMENT_INCOME_HEALTHY_PCT,
                       stressed_pct: float = CURTAILMENT_INCOME_STRESSED_PCT,
                       healthy_cpr: float = CURTAILMENT_CPR_HEALTHY) -> pd.Series:
    """
    Monthly curtailment SMM, continuously scaled by real disposable income
    growth.  Source: SSRN 4949187 — curtailment tracks disposable income
    availability, not inflation or mortgage rate directly.  Uses simple /12
    monthly convention to match this module's CPR->monthly-rate treatment.
    """
    span = healthy_pct - stressed_pct
    if span <= 0:
        raise ValueError("healthy_pct must exceed stressed_pct for curtailment scaling")
    frac = ((real_income_yoy_pct - stressed_pct) / span).clip(0.0, 1.0)
    return frac * healthy_cpr / 12


def cpr_goodness_of_fit(empirical: pd.Series, predicted: pd.Series,
                        smooth_window: int = 3) -> dict:
    """
    Compute goodness-of-fit statistics for ABM CPR predictions vs. empirical.
    Returns a dict with raw and smoothed metrics: R², RMSE, MAE, Pearson r.
    """
    mask = empirical.notna() & predicted.notna()
    e, p = empirical[mask].to_numpy(), predicted[mask].to_numpy()

    def _stats(actual, pred):
        ss_res = ((actual - pred) ** 2).sum()
        ss_tot = ((actual - actual.mean()) ** 2).sum()
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
        rmse = np.sqrt(((actual - pred) ** 2).mean())
        mae = np.abs(actual - pred).mean()
        corr = np.corrcoef(actual, pred)[0, 1] if len(actual) > 1 else np.nan
        return {"r2": r2, "rmse": rmse, "mae": mae, "corr": corr, "n": len(actual)}

    raw = _stats(e, p)

    e_s = pd.Series(e).rolling(smooth_window, center=True, min_periods=1).mean()
    p_s = pd.Series(p).rolling(smooth_window, center=True, min_periods=1).mean()
    smoothed = _stats(e_s.to_numpy(), p_s.to_numpy())

    return {"raw": raw, "smoothed": smoothed}


def cpr_cross_correlation(empirical: pd.Series, predicted: pd.Series,
                          max_lag: int = 3) -> dict:
    """
    Pearson r between ABM CPR and empirical CPR at lags −max_lag … +max_lag.
    Positive lag = ABM leads empirical.  Returns {lag: r}.
    """
    mask = empirical.notna() & predicted.notna()
    e = empirical[mask].to_numpy()
    p = predicted[mask].to_numpy()
    out = {}
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            e_s, p_s = e[:lag], p[-lag:]
        elif lag == 0:
            e_s, p_s = e, p
        else:
            e_s, p_s = e[lag:], p[:-lag]
        if len(e_s) < 5:
            continue
        out[lag] = float(np.corrcoef(e_s, p_s)[0, 1])
    return out


def _round_coupon(c: float) -> float:
    return round(float(c), 4)


MONTHS_ELAPSED_DEFAULT = PORTFOLIO_TERM - int(
    (DEFAULT_COHORT_ASOF.normalize() - PORTFOLIO_ORIGIN).days / 30.44
)


def cohorts_from_surface(surface: dict, equal_weight: bool = True) -> List[dict]:
    """Derive cohort metadata from loaded surface keys when API fetch fails."""
    keys = sorted(surface.keys())
    w = 1.0 / len(keys) if equal_weight else 1.0
    return [{
        "coupon": coupon,
        "weight": w,
        "origin_date": PORTFOLIO_ORIGIN,
        "months_elapsed": MONTHS_ELAPSED_DEFAULT,
        "term_months": term_months,
    } for coupon, term_months in keys]


# ---------------------------------------------------------------------------
# ABM-calibrated CPR anchors — loaded dynamically from the ABM output CSV
# so that re-running the simulation automatically updates the dashboard.
# Fallback to hardcoded values if the CSV is not found (first run / offline).
# ---------------------------------------------------------------------------
_FALLBACK_RATES = np.array([3.0, 5.0, 8.0])
_FALLBACK_US    = np.array([39.2, 16.4, 4.56])
_FALLBACK_DK    = np.array([39.2, 35.1, 30.9])


def load_abm_anchors(csv_path=None):
    """
    Read the ABM results CSV and extract anchor CPRs at 3%, 5%, and 8%
    market rates. Returns (rates_pct, us_cpr_pct, danish_cpr_pct).
    """
    if csv_path is None:
        csv_path = ABM_LOCKIN_RESULTS_CSV
    try:
        abm = pd.read_csv(csv_path)
        anchor_decimals = [0.03, 0.05, 0.08]
        rows = [abm.iloc[(abm["Market_Rate"] - r).abs().argsort().iloc[0]]
                for r in anchor_decimals]
        rates  = np.array([r["Market_Rate"] * 100 for r in rows])
        us_cpr = np.array([r["CPR_US"]      * 100 for r in rows])
        dk_cpr = np.array([r["CPR_Danish"]  * 100 for r in rows])
        print(f"ABM anchors loaded from {csv_path}: "
              f"US CPR @ 8% = {us_cpr[-1]:.2f}%, "
              f"Danish CPR @ 8% = {dk_cpr[-1]:.2f}%")
        return rates, us_cpr, dk_cpr
    except FileNotFoundError:
        print(f"{csv_path} not found — using fallback CPR anchors.")
        return _FALLBACK_RATES, _FALLBACK_US, _FALLBACK_DK


def compute_abm_cpr_vectors(mortgage_rate_pct: pd.Series,
                            anchor_rates=None, anchor_us=None,
                            anchor_dk=None) -> pd.DataFrame:
    """
    Map each month's 30-yr mortgage rate to ABM-calibrated annual CPRs via
    linear interpolation between the anchor points. np.interp clamps values
    outside the anchor range to the boundary values automatically.
    """
    if anchor_rates is None:
        anchor_rates = _FALLBACK_RATES
    if anchor_us is None:
        anchor_us = _FALLBACK_US
    if anchor_dk is None:
        anchor_dk = _FALLBACK_DK

    rates = mortgage_rate_pct.to_numpy(dtype=float)
    return pd.DataFrame(
        {
            "US_CPR_Pct": np.interp(rates, anchor_rates, anchor_us),
            "Danish_CPR_Pct": np.interp(rates, anchor_rates, anchor_dk),
        },
        index=mortgage_rate_pct.index,
    )


# ---------------------------------------------------------------------------
# Dynamic Macroeconomic Friction
# ---------------------------------------------------------------------------
def calculate_dynamic_friction(
    df: pd.DataFrame,
    base_friction: float = BASE_FRICTION,
    search_penalty_cap: float = SEARCH_PENALTY_CAP,
    sentiment_penalty_cap: float = SENTIMENT_PENALTY_CAP,
) -> pd.DataFrame:
    """
    Compute a per-month Dynamic_Friction column from two macro drivers:

      * Search friction  -> low housing inventory (ACTLISCOUUS) below its
        2017-2019 baseline adds up to +200 bps (proportional, capped).
      * Psychological friction -> consumer sentiment (UMCSENT) below 85 adds
        +5 bps per point, capped at +150 bps.

    Dynamic_Friction = base_friction + search_penalty + sentiment_penalty.
    With the default parameters this floats between 7.0% and 10.5%. The three
    parameters are exposed as keyword arguments (defaulting to the module
    constants) so the sensitivity analysis can sweep them without monkeypatching.
    """
    df = df.copy()
    baseline = df.attrs.get("inventory_baseline", df["ACTLISCOUUS"].mean())

    # Search penalty: scale so the lowest-inventory month hits the cap
    inventory_min = df["ACTLISCOUUS"].min()
    shortfall = (baseline - df["ACTLISCOUUS"]).clip(lower=0.0)
    denom = baseline - inventory_min
    if denom <= 0:
        search_penalty = pd.Series(0.0, index=df.index)
    else:
        search_penalty = (search_penalty_cap * shortfall / denom).clip(
            upper=search_penalty_cap
        )

    # Sentiment penalty: +5 bps per point below the healthy baseline
    sentiment_drop = (SENTIMENT_BASELINE - df["UMCSENT"]).clip(lower=0.0)
    sentiment_penalty = (sentiment_drop * SENTIMENT_PENALTY_PER_PT).clip(
        upper=sentiment_penalty_cap
    )

    df["Search_Penalty"] = search_penalty
    df["Sentiment_Penalty"] = sentiment_penalty
    df["Dynamic_Friction"] = base_friction + search_penalty + sentiment_penalty
    return df


def _surface_tuple_from_dataframe(surf: pd.DataFrame):
    """Convert one cohort's surface DataFrame into interpolation grids."""
    rates = np.sort(surf["Market_Rate"].unique())
    frictions = np.sort(surf["Friction"].unique())
    has_velocity = "Rate_Velocity" in surf.columns
    if has_velocity:
        velocities = np.sort(surf["Rate_Velocity"].unique())
        nr, nf, nv = len(rates), len(frictions), len(velocities)
        z_us = np.empty((nr, nf, nv))
        z_dk = np.empty((nr, nf, nv))
        for iv, vel in enumerate(velocities):
            slab = surf[np.isclose(surf["Rate_Velocity"], vel)]
            piv_us = slab.pivot(index="Market_Rate", columns="Friction",
                                values="CPR_US").reindex(index=rates,
                                                          columns=frictions)
            piv_dk = slab.pivot(index="Market_Rate", columns="Friction",
                                values="CPR_Danish").reindex(index=rates,
                                                              columns=frictions)
            z_us[:, :, iv] = piv_us.to_numpy() * 100.0
            z_dk[:, :, iv] = piv_dk.to_numpy() * 100.0
        return rates * 100.0, frictions, velocities, z_us, z_dk

    piv_us = surf.pivot(index="Market_Rate", columns="Friction",
                        values="CPR_US").reindex(index=rates,
                                                  columns=frictions)
    piv_dk = surf.pivot(index="Market_Rate", columns="Friction",
                        values="CPR_Danish").reindex(index=rates,
                                                     columns=frictions)
    return rates * 100.0, frictions, piv_us.to_numpy() * 100.0, \
        piv_dk.to_numpy() * 100.0


def load_cpr_surface(csv_path=None):
    """
    Load the ABM CPR surface and reshape into grids for interpolation.

    Returns:
      None if file absent.
      2D tuple -> (rates_pct, frictions, Z_US, Z_DK)
      3D tuple -> (rates_pct, frictions, velocities, Z_US_3d, Z_DK_3d)
      dict[(float, int), tuple] when Cohort_Coupon column is present — one
        tuple per cohort keyed by (decimal coupon, term_months), e.g.
        (0.02, 360) for the 2.0% 30-year bucket. CSVs written before the
        15-year fold-in lack Cohort_Term and load as term 360.
    """
    try:
        if csv_path is None:
            csv_path = ABM_CPR_SURFACE_CSV
        surf = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"{csv_path} not found — falling back to 1D anchor CPRs.")
        return None

    if "Cohort_Coupon" in surf.columns:
        if "Cohort_Term" not in surf.columns:
            surf["Cohort_Term"] = PORTFOLIO_TERM
        surfaces = {}
        for (coupon, term_months), grp in surf.groupby(
                ["Cohort_Coupon", "Cohort_Term"]):
            slab = grp.drop(columns=["Cohort_Coupon", "Cohort_Term"])
            key = (_round_coupon(coupon), int(term_months))
            surfaces[key] = _surface_tuple_from_dataframe(slab)
        n_c = len(surfaces)
        sample = next(iter(surfaces.values()))
        dim = "3D" if len(sample) == 5 else "2D"
        print(f"CPR surface loaded from {csv_path}: {n_c} cohorts ({dim})")
        return surfaces

    tup = _surface_tuple_from_dataframe(surf)
    if len(tup) == 5:
        rates, frictions, velocities, _, _ = tup
        print(f"CPR surface loaded from {csv_path}: "
              f"{len(rates)} rates x {len(frictions)} frictions "
              f"x {len(velocities)} velocities")
    else:
        rates, frictions, _, _ = tup
        print(f"CPR surface loaded from {csv_path}: "
              f"{len(rates)} rates x {len(frictions)} friction levels")
    return tup


def interp_cpr_surface(rate_pct: pd.Series, friction: pd.Series,
                       surface,
                       velocity: Optional[pd.Series] = None) -> pd.DataFrame:
    """
    Interpolation on the CPR surface, evaluated per month.  Uses nested
    np.interp so no SciPy dependency is required; np.interp clamps
    out-of-range inputs.

    Supports both 2D (bilinear on rate x friction) and 3D (trilinear on
    rate x friction x velocity) surfaces, auto-detected from the tuple
    length returned by load_cpr_surface().
    """
    rate_arr = rate_pct.to_numpy(dtype=float)
    fric_arr = friction.to_numpy(dtype=float)

    if len(surface) == 5:
        # 3D surface: (rates_pct, frictions, velocities, z_us, z_dk)
        rates_grid, frictions_grid, vel_grid, z_us, z_dk = surface
        vel_arr = (velocity.to_numpy(dtype=float)
                   if velocity is not None
                   else np.zeros(len(rate_arr)))

        us_out = np.empty(len(rate_arr))
        dk_out = np.empty(len(rate_arr))
        for i in range(len(rate_arr)):
            # Step 1: for each (friction_col, velocity_slab), interp over rate
            # Then interp that 2D slice over friction, then over velocity.
            us_by_vel = np.empty(len(vel_grid))
            dk_by_vel = np.empty(len(vel_grid))
            for iv in range(len(vel_grid)):
                us_by_fric = np.array(
                    [np.interp(rate_arr[i], rates_grid, z_us[:, jf, iv])
                     for jf in range(len(frictions_grid))]
                )
                dk_by_fric = np.array(
                    [np.interp(rate_arr[i], rates_grid, z_dk[:, jf, iv])
                     for jf in range(len(frictions_grid))]
                )
                us_by_vel[iv] = np.interp(fric_arr[i], frictions_grid,
                                          us_by_fric)
                dk_by_vel[iv] = np.interp(fric_arr[i], frictions_grid,
                                          dk_by_fric)
            us_out[i] = np.interp(vel_arr[i], vel_grid, us_by_vel)
            dk_out[i] = np.interp(vel_arr[i], vel_grid, dk_by_vel)
    else:
        # 2D surface: (rates_pct, frictions, z_us, z_dk) — legacy
        rates_grid, frictions_grid, z_us, z_dk = surface
        us_out = np.empty(len(rate_arr))
        dk_out = np.empty(len(rate_arr))
        for i in range(len(rate_arr)):
            us_by_friction = np.array(
                [np.interp(rate_arr[i], rates_grid, z_us[:, j])
                 for j in range(len(frictions_grid))]
            )
            dk_by_friction = np.array(
                [np.interp(rate_arr[i], rates_grid, z_dk[:, j])
                 for j in range(len(frictions_grid))]
            )
            us_out[i] = np.interp(fric_arr[i], frictions_grid, us_by_friction)
            dk_out[i] = np.interp(fric_arr[i], frictions_grid, dk_by_friction)

    return pd.DataFrame(
        {"US_CPR_Pct": us_out, "Danish_CPR_Pct": dk_out},
        index=rate_pct.index,
    )


# ---------------------------------------------------------------------------
# Section 1 – Data Ingestion & Cleaning
# ---------------------------------------------------------------------------
SOMA_SUMMARY_URL = "https://markets.newyorkfed.org/api/soma/summary.json"
SOMA_LATEST_DATE_URL = "https://markets.newyorkfed.org/api/soma/asofdates/latest.json"
SOMA_CUSIP_URL = ("https://markets.newyorkfed.org/api/soma/agency/get/all/"
                  "asof/{date}.json")


def _default_cohort() -> List[dict]:
    """Single-cohort fallback matching legacy PORTFOLIO_* constants."""
    return [{
        "coupon": PORTFOLIO_COUPON,
        "weight": 1.0,
        "origin_date": PORTFOLIO_ORIGIN,
        "months_elapsed": MONTHS_ELAPSED_DEFAULT,
        "term_months": PORTFOLIO_TERM,
    }]


TERM_MONTHS_BY_LABEL = {"30yr": 360, "15yr": 180}


def fetch_soma_mbs_cohorts(min_share: float = 0.02,
                           coupon_step_pct: float = 0.5,
                           terms: tuple = ("30yr", "15yr"),
                           ) -> List[dict]:
    """
    Fetch CUSIP-level SOMA MBS holdings and bucket into per-term coupon
    cohorts: [{coupon, weight, origin_date, months_elapsed, term_months}, ...].

    Coupon and maturity (MM/YY) are parsed from securityDescription
    (e.g. "UMBS MORTPASS 2% 10/51"). origin_date is back-derived per CUSIP
    as maturity_date - term months, weighted-averaged within each rounded
    (term, coupon) bucket. 15-year and 30-year buckets are kept separate —
    their WAC and prepay behavior differ — and weights are normalized over
    the combined included universe. Buckets below min_share fold into the
    nearest surviving bucket of the SAME term. Falls back to a single legacy
    30-year cohort if the API is unreachable.

    terms=("30yr",) reproduces the pre-fold-in behavior exactly (used by the
    Step-3 no-regression check).
    """
    try:
        req = urllib.request.Request(SOMA_LATEST_DATE_URL,
                                     headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            as_of_str = json.loads(resp.read())["soma"]["asOfDates"][0]
        as_of = pd.Timestamp(as_of_str)

        url = SOMA_CUSIP_URL.format(date=as_of_str)
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            holdings = json.loads(resp.read())["soma"]["holdings"]
    except Exception as exc:
        print(f"SOMA CUSIP API unavailable ({exc}); using single-cohort fallback.")
        return _default_cohort()

    step = coupon_step_pct / 100.0
    bucket_value = {}       # (term_months, rounded coupon) -> total face value
    bucket_elapsed_w = {}   # (term_months, rounded coupon) -> sum(value * months_elapsed)
    bucket_origin_w = {}    # (term_months, rounded coupon) -> sum(value * origin ordinal)
    total_mbs_face = 0.0    # all MBS rows, any term (coverage denominator)

    def months_between(d1: pd.Timestamp, d2: pd.Timestamp) -> int:
        return (d1.year - d2.year) * 12 + (d1.month - d2.month)

    for row in holdings:
        if row.get("securityType") != "MBS":
            continue
        value = float(row["currentFaceValue"])
        total_mbs_face += value
        term_label = row.get("term")
        if term_label not in terms or term_label not in TERM_MONTHS_BY_LABEL:
            continue
        term_months = TERM_MONTHS_BY_LABEL[term_label]
        desc = row.get("securityDescription", "")
        mc = re.search(r"(\d+(?:\.\d+)?)%", desc)
        mm = re.search(r"(\d{1,2})/(\d{2})\b", desc)
        if not mc or not mm:
            continue
        coupon = float(mc.group(1)) / 100.0
        mo, yy = int(mm.group(1)), int(mm.group(2))
        mat_year = 2000 + yy
        mat_date = pd.Timestamp(year=mat_year, month=mo, day=1)
        months_remaining = months_between(mat_date, as_of)
        elapsed = max(0, term_months - months_remaining)
        origin = mat_date - pd.DateOffset(months=term_months)
        rounded = round(coupon / step) * step
        key = (term_months, rounded)
        bucket_value[key] = bucket_value.get(key, 0.0) + value
        bucket_elapsed_w[key] = (bucket_elapsed_w.get(key, 0.0)
                                 + value * elapsed)
        bucket_origin_w[key] = (bucket_origin_w.get(key, 0.0)
                                + value * origin.toordinal())

    if not bucket_value:
        print("SOMA CUSIP parse yielded no MBS in requested terms; "
              "using single-cohort fallback.")
        return _default_cohort()

    total = sum(bucket_value.values())
    raw = []
    for term_months, c in sorted(bucket_value):
        key = (term_months, c)
        val = bucket_value[key]
        raw.append({
            "coupon": _round_coupon(c),
            "weight": val / total,
            "origin_date": pd.Timestamp.fromordinal(
                int(round(bucket_origin_w[key] / val))
            ),
            "months_elapsed": int(round(bucket_elapsed_w[key] / val)),
            "term_months": term_months,
        })

    # Fold buckets below min_share into the nearest same-term survivor by
    # coupon distance (never across terms — prepay dynamics differ).
    # min_share is evaluated against the bucket's WITHIN-TERM share so the
    # 30-year cohort structure is invariant to whether 15-year coverage is
    # included; final weights remain combined-universe shares.
    cohorts = []
    for term_months in sorted({r["term_months"] for r in raw}):
        term_raw = [r for r in raw if r["term_months"] == term_months]
        term_mass = sum(r["weight"] for r in term_raw)
        survivors = [r for r in term_raw
                     if r["weight"] / term_mass >= min_share]
        if not survivors:
            survivors = [max(term_raw, key=lambda r: r["weight"])]
        for r in term_raw:
            if r in survivors:
                continue
            nearest = min(survivors, key=lambda s: abs(s["coupon"] - r["coupon"]))
            old_w = nearest["weight"]
            add_w = r["weight"]
            new_w = old_w + add_w
            nearest["origin_date"] = pd.Timestamp.fromordinal(int(round(
                (nearest["origin_date"].toordinal() * old_w
                 + r["origin_date"].toordinal() * add_w) / new_w
            )))
            nearest["months_elapsed"] = int(round(
                (nearest["months_elapsed"] * old_w
                 + r["months_elapsed"] * add_w) / new_w
            ))
            nearest["weight"] = new_w
        cohorts.extend(
            s for s in survivors
            if s["weight"] / term_mass >= min_share * 0.5
        )

    wsum = sum(r["weight"] for r in cohorts)
    for r in cohorts:
        r["weight"] /= wsum
        r["coupon"] = _round_coupon(r["coupon"])

    included_face = total * wsum  # face value surviving the fold filter
    coverage_pct = included_face / total_mbs_face * 100 if total_mbs_face else 0.0
    wac = sum(r["coupon"] * r["weight"] for r in cohorts)
    term_labels = "+".join(sorted(terms))
    print(f"SOMA MBS cohorts loaded ({len(cohorts)} buckets [{term_labels}], "
          f"as-of {as_of_str}, WAC {wac*100:.2f}%, "
          f"coverage {coverage_pct:.1f}% of ${total_mbs_face/1e9:,.0f}B MBS face):")
    for r in cohorts:
        print(f"  {r['term_months']//12}yr coupon {r['coupon']*100:.2f}%  "
              f"weight {r['weight']*100:5.1f}%  "
              f"seasoning {r['months_elapsed']}mo  "
              f"origin {r['origin_date'].strftime('%Y-%m')}")
    return cohorts


def fetch_soma_mbs_monthly(start: str = START_DATE,
                           url: str = SOMA_SUMMARY_URL) -> Optional[pd.Series]:
    """
    Pull weekly SOMA MBS current face value (remaining unpaid principal
    balance, not amortized cost) from the NY Fed Markets API, resample
    to month-end, and return month-over-month changes in $B (negative =
    portfolio decline).  Returns None if the API is unreachable so the
    caller can fall back to WSHOMCB diffs.
    """
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read())["soma"]["summary"]
    except Exception as exc:
        print(f"NY Fed SOMA API unavailable ({exc}); "
              f"will fall back to WSHOMCB diffs.")
        return None

    records = []
    for row in payload:
        mbs_val = row.get("mbs")
        if not mbs_val or mbs_val == "0.00":
            continue
        records.append({
            "date": pd.Timestamp(row["asOfDate"]),
            "mbs_b": float(mbs_val) / 1e9,
        })

    if not records:
        print("SOMA API returned no MBS data; falling back to WSHOMCB diffs.")
        return None

    weekly = (pd.DataFrame(records)
              .set_index("date")
              .sort_index()
              .loc[start:])
    monthly_mbs = weekly["mbs_b"].resample("ME").last()
    rolloff = monthly_mbs.diff()
    rolloff.name = "SOMA_Monthly_Rolloff_Billions"
    print(f"SOMA MBS monthly roll-off loaded from NY Fed API "
          f"({len(rolloff.dropna())} months)")
    return rolloff


def fetch_data(api_key: str = FRED_API_KEY,
               start: str = START_DATE) -> pd.DataFrame:
    """
    Pull the Fed balance-sheet series plus the two macro-friction drivers,
    merge into a clean monthly frame, and stash the 2017-2019 inventory
    baseline in df.attrs for the dynamic-friction calculation.
    """
    fred = Fred(api_key=api_key)

    mbs = fred.get_series("WSHOMCB", observation_start=start)
    rate = fred.get_series("MORTGAGE30US", observation_start=BASELINE_START)

    mbs.name = "WSHOMCB"
    rate.name = "MORTGAGE30US"

    df = pd.merge(mbs, rate, how="outer", left_index=True, right_index=True)
    df.sort_index(inplace=True)
    df.ffill(inplace=True)
    df.dropna(inplace=True)

    # Resample to true calendar-month frequency so each month is counted once
    monthly = pd.DataFrame({
        "WSHOMCB": df["WSHOMCB"].resample("ME").last(),       # stock → end-of-month level
        "MORTGAGE30US": df["MORTGAGE30US"].resample("ME").mean(),  # rate → monthly average
    })
    monthly.dropna(inplace=True)

    # --- Macro-friction drivers (pulled from 2017 for baseline) -----------
    inventory = fred.get_series("ACTLISCOUUS",
                                observation_start=BASELINE_START)  # search friction
    sentiment = fred.get_series("UMCSENT",
                                observation_start=BASELINE_START)  # psych friction
    dspi = fred.get_series("DSPIC96",
                           observation_start=BASELINE_START)  # curtailment driver
    inventory_m = inventory.resample("ME").last()
    sentiment_m = sentiment.resample("ME").mean()
    dspi_m = dspi.resample("ME").last()

    # 2017-2019 inventory baseline (healthy, pre-pandemic supply)
    base_slice = inventory_m.loc["2017-01-01":"2019-12-31"]
    inventory_baseline = float(base_slice.mean())

    # Align friction drivers to the monthly Fed timeline; no NaNs allowed
    monthly["ACTLISCOUUS"] = inventory_m.reindex(monthly.index).ffill().bfill()
    monthly["UMCSENT"] = sentiment_m.reindex(monthly.index).ffill().bfill()
    monthly["DSPIC96"] = dspi_m.reindex(monthly.index).ffill().bfill()

    monthly.attrs["inventory_baseline"] = inventory_baseline
    monthly.attrs["MORTGAGE30US_EXTENDED"] = (
        rate.resample("ME").mean().ffill()
    )
    print(f"FRED friction drivers loaded: 2017-2019 inventory baseline = "
          f"{inventory_baseline:,.0f} listings")

    return monthly


# ---------------------------------------------------------------------------
# Section 2 – Quantitative Calculations
# ---------------------------------------------------------------------------
def apply_settlement_lag(series: pd.Series,
                         kernel: List[float] = None) -> pd.Series:
    """Convolve simulated roll-off with agency remittance settlement lags."""
    if kernel is None:
        kernel = SETTLEMENT_LAG_KERNEL
    out = pd.Series(0.0, index=series.index)
    for lag, weight in enumerate(kernel):
        out = out + weight * series.shift(lag, fill_value=0.0)
    return out


def _load_hazard_microsim_paths(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Run literature hazard microsim; return US and Danish monthly paths."""
    hazard_dir = Path(__file__).resolve().parent.parent / "hazard"
    if str(hazard_dir) not in sys.path:
        sys.path.insert(0, str(hazard_dir))

    from loan_sample import load_or_build_loan_sample
    from microsim_engine import run_qt_microsim

    loans = load_or_build_loan_sample()
    macro = df.copy()
    if "Dynamic_Friction" not in macro.columns:
        macro = calculate_dynamic_friction(macro)
    return run_qt_microsim(loan_sample=loans, macro=macro)


def compute_metrics(
    df: pd.DataFrame,
    base_friction: float = BASE_FRICTION,
    search_penalty_cap: float = SEARCH_PENALTY_CAP,
    sentiment_penalty_cap: float = SENTIMENT_PENALTY_CAP,
    surface=None,
    soma_rolloff: Optional[pd.Series] = None,
    cohorts: Optional[List[dict]] = None,
    use_burnout: bool = False,
    apply_settlement_lag_kernel: bool = False,
    use_hazard_microsim: bool = False,
    abm_params: Optional[dict] = None,
    sched_smm_override: Optional[pd.Series] = None,
    allow_surface_cohort_fallback: bool = False,
) -> pd.DataFrame:
    """
    Derive roll-off, extension delta, and cumulative trapped liquidity.

    The friction parameters default to the module constants (so existing
    callers are unaffected) but can be overridden by the sensitivity sweep.
    An optional pre-loaded `surface` avoids re-reading the CSV on every call.
    When `soma_rolloff` is provided (monthly Series from the NY Fed SOMA
    API), it is used instead of WSHOMCB diffs for the actual roll-off.
    SOMA reports current face value (remaining unpaid principal), so its
    diff avoids the premium/discount amortization drift baked into
    WSHOMCB's amortized-cost accounting. Both series remain settlement-date
    based, so TBA-settlement lag is a limitation shared by either source,
    not something switching to SOMA fixes on its own.
    """
    df = df.copy()

    if soma_rolloff is not None:
        aligned = soma_rolloff.reindex(df.index)
        df["Actual_Monthly_Rolloff_Billions"] = aligned
        df["Rolloff_Source"] = "SOMA"
    else:
        df["Actual_Monthly_Rolloff_Billions"] = (
            df["WSHOMCB"].diff(periods=1) / 1_000
        )
        df["Rolloff_Source"] = "WSHOMCB"

    # Phased QT target: -17.5B ramp-up, -35B full pace, 0B post-QT
    df["QT_Target_Billions"] = compute_qt_target_series(df.index)

    # Masks: QT active window (accumulation only happens here)
    qt_active = (df.index >= QT_START) & (df.index < QT_END)

    # Extension delta vs. the row-wise target (only meaningful after QT began)
    df["Extension_Delta_Billions"] = np.where(
        df.index >= QT_START,
        df["Actual_Monthly_Rolloff_Billions"] - df["QT_Target_Billions"],
        np.nan,
    )

    # Cumulative trapped liquidity: NET accumulation during active QT
    # (months where roll-off exceeded the cap offset months that fell short).
    # After QT ends (Dec 2025) the series flatlines at its terminal value.
    trapped = df["Extension_Delta_Billions"].fillna(0.0)
    trapped = trapped.where(qt_active, 0.0)
    df["Cumulative_Trapped_Liquidity"] = trapped.cumsum()
    df.loc[df.index < QT_START, "Cumulative_Trapped_Liquidity"] = np.nan

    # --- Dynamic macroeconomic friction -----------------------------------
    # Build the per-month friction from inventory + sentiment first, so the
    # CPR surface can be sampled at each month's (rate, friction) coordinate.
    df = calculate_dynamic_friction(
        df,
        base_friction=base_friction,
        search_penalty_cap=search_penalty_cap,
        sentiment_penalty_cap=sentiment_penalty_cap,
    )

    # --- Rate velocity for the 3D CPR surface (6-month rate change) --------
    df["Rate_6M_Change"] = df["MORTGAGE30US"].diff(6).fillna(0.0) / 100.0

    if surface is None and not use_burnout and not use_hazard_microsim:
        surface = load_cpr_surface()

    multi_cohort = isinstance(surface, dict)
    cohort_provenance = "caller-supplied" if cohorts is not None else None
    if (multi_cohort or use_burnout) and cohorts is None and not use_hazard_microsim:
        try:
            cohorts = fetch_soma_mbs_cohorts()
            cohort_provenance = "soma-fetch"
        except Exception as exc:
            # The fallback is EQUAL-WEIGHTED (cohorts_from_surface), so it
            # silently substitutes a different book — and the cohort weights
            # set the scheduled-amortization series that both the simulated
            # roll-off and the empirical CPR back-out are computed from.
            # Failing loud is the default; opting in records the substitution.
            if not allow_surface_cohort_fallback:
                raise RuntimeError(
                    "SOMA cohort fetch failed and the equal-weighted "
                    "surface-derived fallback was not authorized. Pass "
                    "cohorts=... explicitly, or set "
                    "allow_surface_cohort_fallback=True to accept an "
                    "equal-weighted cohort book (which changes scheduled "
                    f"amortization and every figure derived from it). "
                    f"Underlying error: {exc!r}"
                ) from exc
            cohorts = cohorts_from_surface(surface)
            cohort_provenance = "surface-equal-weight-fallback"
            print("WARNING: SOMA cohort fetch failed; using EQUAL-WEIGHTED "
                  "cohort weights derived from loaded surface keys. "
                  "Scheduled amortization and the empirical CPR back-out "
                  "are affected.")
    df.attrs["cohort_provenance"] = cohort_provenance
    df.attrs["n_cohorts"] = len(cohorts) if cohorts is not None else 0

    holdings_b = df["WSHOMCB"] / 1_000
    df["RealDispInc_YoY_Pct"] = df["DSPIC96"].pct_change(12).fillna(0.0) * 100
    df["Curtailment_SMM"] = curtailment_series(df["RealDispInc_YoY_Pct"])
    curtailment_smm = df["Curtailment_SMM"]
    velocity_series = df["Rate_6M_Change"]
    us_cpr = pd.Series(0.0, index=df.index)
    dk_cpr = pd.Series(0.0, index=df.index)
    us_rolloff = pd.Series(0.0, index=df.index)
    sched_smm_weighted = pd.Series(0.0, index=df.index)

    burnout_mode = use_burnout and cohorts
    if use_hazard_microsim:
        print("Using literature hazard microsim CPR paths …")
        micro_paths = _load_hazard_microsim_paths(df)
        us_sim = micro_paths["US"].reindex(df.index)
        dk_sim = micro_paths["Danish"].reindex(df.index)

        df["US_CPR_Pct"] = us_sim["hazard_cpr_pct"].fillna(0.0)
        df["Danish_CPR_Pct"] = dk_sim["hazard_cpr_pct"].fillna(0.0)
        sched_smm = scheduled_amortization_series(df.index)
        df["Scheduled_Amort_SMM"] = sched_smm

        # US rolloff: microsim already routes prepay through Markov pipeline
        us_rolloff = us_sim["simulated_rolloff_b"].reindex(df.index).fillna(0.0)
        us_rolloff = us_rolloff - holdings_b * curtailment_smm
        df["US_Simulated_Monthly_Rolloff_Billions"] = us_rolloff

        # Danish dynamic balance forward loop
        monthly_cpr_dk = df["Danish_CPR_Pct"] / 100 / 12
        dk_rolloff = np.zeros(len(df))
        dk_balance = np.zeros(len(df))
        qt_start_idx = df.index.get_indexer([QT_START], method="nearest")[0]
        bal = float(holdings_b.iloc[qt_start_idx])
        for i in range(len(df)):
            if i < qt_start_idx:
                dk_balance[i] = float(holdings_b.iloc[i])
                continue
            dk_balance[i] = bal
            monthly_drain = (float(monthly_cpr_dk.iloc[i])
                             + float(sched_smm.iloc[i])
                             + float(curtailment_smm.iloc[i]))
            rolloff = bal * monthly_drain
            dk_rolloff[i] = -rolloff
            bal = max(bal - rolloff, 0.0)
        df["Danish_Simulated_Monthly_Rolloff_Billions"] = dk_rolloff
        df["Danish_Balance_Billions"] = dk_balance

    elif burnout_mode:
        import abm_lockin_simulation as abm
        params = abm_params or {}
        engine = abm.HousingMarketEngine(
            seed=params.get("seed", abm.RNG_SEED),
            median_income=params.get("median_income", 80_000.0),
            median_home_value=params.get("median_home_value", 400_000.0),
            mobility_scale=params.get("mobility_scale", abm.MOBILITY_DESIRE_SCALE),
        )
        rates_ext = df.attrs.get("MORTGAGE30US_EXTENDED", df["MORTGAGE30US"])
        cohort_paths = []
        for cohort in cohorts:
            engine.attach_cohort(
                cohort["coupon"], cohort["months_elapsed"],
                term_years=int(cohort.get("term_months", PORTFOLIO_TERM)) // 12,
            )
            origin = pd.Timestamp(cohort["origin_date"])
            end = df.index[-1]
            if origin > end:
                continue
            burn_start = origin
            path_index = pd.date_range(burn_start, end, freq="ME")
            rates_path = rates_ext.reindex(path_index).ffill().bfill()
            fric_path = df["Dynamic_Friction"].reindex(path_index).fillna(base_friction)
            vel_path = df["Rate_6M_Change"].reindex(path_index).fillna(0.0)
            path = engine.simulate_cohort_path(path_index, rates_path,
                                               fric_path, vel_path)
            path = path.reindex(df.index)
            sched_c = scheduled_amortization_series(
                df.index, coupon=cohort["coupon"],
                origin=cohort["origin_date"],
                term=int(cohort.get("term_months", PORTFOLIO_TERM)),
            )
            w = cohort["weight"]
            us_cpr += w * path["US_CPR_Pct"].fillna(0.0)
            dk_cpr += w * path["Danish_CPR_Pct"].fillna(0.0)
            sched_smm_weighted += w * sched_c
            us_rolloff += (
                -holdings_b * w
                * (path["US_CPR_Pct"] / 100 / 12 + sched_c + curtailment_smm)
            )
            cohort_paths.append({
                "key": (_round_coupon(cohort["coupon"]),
                        int(cohort.get("term_months", PORTFOLIO_TERM))),
                "weight": w,
                "dk_monthly_cpr": path["Danish_CPR_Pct"] / 100 / 12,
                "sched": sched_c,
            })
        df["US_CPR_Pct"] = us_cpr
        df["Danish_CPR_Pct"] = dk_cpr
        df["Scheduled_Amort_SMM"] = sched_smm_weighted
        df["US_Simulated_Monthly_Rolloff_Billions"] = us_rolloff

        dk_rolloff = np.zeros(len(df))
        dk_balance = np.zeros(len(df))
        qt_start_idx = df.index.get_indexer([QT_START], method="nearest")[0]
        init_balance = float(holdings_b.iloc[qt_start_idx])
        cohort_balances = {
            cp["key"]: init_balance * cp["weight"]
            for cp in cohort_paths
        }
        for i in range(len(df)):
            if i < qt_start_idx:
                dk_balance[i] = float(holdings_b.iloc[i])
                continue
            total_bal = 0.0
            total_rolloff = 0.0
            for cp in cohort_paths:
                key = cp["key"]
                bal = cohort_balances[key]
                drain = (float(cp["dk_monthly_cpr"].iloc[i])
                         + float(cp["sched"].iloc[i])
                         + float(curtailment_smm.iloc[i]))
                rolloff = bal * drain
                total_rolloff += rolloff
                cohort_balances[key] = max(bal - rolloff, 0.0)
                total_bal += cohort_balances[key]
            dk_balance[i] = total_bal
            dk_rolloff[i] = -total_rolloff
        df["Danish_Simulated_Monthly_Rolloff_Billions"] = dk_rolloff
        df["Danish_Balance_Billions"] = dk_balance

    elif surface is not None and multi_cohort:
        cohort_paths = []
        for cohort in cohorts:
            coupon = _round_coupon(cohort["coupon"])
            term_months = int(cohort.get("term_months", PORTFOLIO_TERM))
            key = (coupon, term_months)
            # Native term-aware 15-year gate (§15 Fix 2 → §19): 15yr cohorts now
            # use their OWN surface, built with the rate-lock penalty that fixes
            # the seasoned-amortization false-gain artifact (5-8% CPR vs the old
            # 32-61%). Falls back to nearest same-term coupon, then any term.
            surf_c = surface.get(key)
            if surf_c is None:
                same_term = [k for k in surface if k[1] == term_months]
                candidates = same_term or list(surface.keys())
                nearest = min(candidates, key=lambda k: abs(k[0] - coupon))
                print(f"WARNING: no surface for {term_months//12}yr coupon "
                      f"{coupon*100:.2f}%; using {nearest[1]//12}yr "
                      f"{nearest[0]*100:.2f}%.")
                surf_c = surface[nearest]
            cpr_c = interp_cpr_surface(
                df["MORTGAGE30US"], df["Dynamic_Friction"], surf_c,
                velocity=velocity_series if len(surf_c) == 5 else None,
            )
            sched_c = scheduled_amortization_series(
                df.index, coupon=cohort["coupon"],
                origin=cohort["origin_date"],
                term=term_months,
            )
            w = cohort["weight"]
            us_cpr += w * cpr_c["US_CPR_Pct"]
            dk_cpr += w * cpr_c["Danish_CPR_Pct"]
            sched_smm_weighted += w * sched_c
            us_rolloff += (
                -holdings_b * w
                * (cpr_c["US_CPR_Pct"] / 100 / 12 + sched_c + curtailment_smm)
            )
            cohort_paths.append({
                "key": key,
                "weight": w,
                "dk_monthly_cpr": cpr_c["Danish_CPR_Pct"] / 100 / 12,
                "sched": sched_c,
            })
        df["US_CPR_Pct"] = us_cpr
        df["Danish_CPR_Pct"] = dk_cpr
        df["Scheduled_Amort_SMM"] = sched_smm_weighted
        df["US_Simulated_Monthly_Rolloff_Billions"] = us_rolloff

        dk_rolloff = np.zeros(len(df))
        dk_balance = np.zeros(len(df))
        qt_start_idx = df.index.get_indexer([QT_START], method="nearest")[0]
        init_balance = float(holdings_b.iloc[qt_start_idx])
        cohort_balances = {
            cp["key"]: init_balance * cp["weight"]
            for cp in cohort_paths
        }
        for i in range(len(df)):
            if i < qt_start_idx:
                dk_balance[i] = float(holdings_b.iloc[i])
                continue
            total_bal = 0.0
            total_rolloff = 0.0
            for cp in cohort_paths:
                key = cp["key"]
                bal = cohort_balances[key]
                drain = (float(cp["dk_monthly_cpr"].iloc[i])
                         + float(cp["sched"].iloc[i])
                         + float(curtailment_smm.iloc[i]))
                rolloff = bal * drain
                total_rolloff += rolloff
                cohort_balances[key] = max(bal - rolloff, 0.0)
                total_bal += cohort_balances[key]
            dk_balance[i] = total_bal
            dk_rolloff[i] = -total_rolloff
        df["Danish_Simulated_Monthly_Rolloff_Billions"] = dk_rolloff
        df["Danish_Balance_Billions"] = dk_balance

    elif surface is not None:
        cpr = interp_cpr_surface(
            df["MORTGAGE30US"], df["Dynamic_Friction"], surface,
            velocity=velocity_series if len(surface) == 5 else None,
        )
        df["US_CPR_Pct"] = cpr["US_CPR_Pct"]
        df["Danish_CPR_Pct"] = cpr["Danish_CPR_Pct"]
        sched_smm = (sched_smm_override if sched_smm_override is not None
                     else scheduled_amortization_series(df.index))
        df["Scheduled_Amort_SMM"] = sched_smm
        monthly_cpr = df["US_CPR_Pct"] / 100 / 12
        df["US_Simulated_Monthly_Rolloff_Billions"] = (
            -holdings_b * (monthly_cpr + sched_smm + curtailment_smm)
        )
        monthly_cpr_dk = df["Danish_CPR_Pct"] / 100 / 12
        dk_rolloff = np.zeros(len(df))
        dk_balance = np.zeros(len(df))
        qt_start_idx = df.index.get_indexer([QT_START], method="nearest")[0]
        init_balance = float(holdings_b.iloc[qt_start_idx])
        bal = init_balance
        for i in range(len(df)):
            if i < qt_start_idx:
                dk_balance[i] = float(holdings_b.iloc[i])
                continue
            dk_balance[i] = bal
            monthly_drain = (float(monthly_cpr_dk.iloc[i])
                             + float(sched_smm.iloc[i])
                             + float(curtailment_smm.iloc[i]))
            rolloff = bal * monthly_drain
            dk_rolloff[i] = -rolloff
            bal = max(bal - rolloff, 0.0)
        df["Danish_Simulated_Monthly_Rolloff_Billions"] = dk_rolloff
        df["Danish_Balance_Billions"] = dk_balance
    else:
        anchor_rates, anchor_us, anchor_dk = load_abm_anchors()
        cpr = compute_abm_cpr_vectors(df["MORTGAGE30US"],
                                      anchor_rates, anchor_us, anchor_dk)
        df["US_CPR_Pct"] = cpr["US_CPR_Pct"]
        df["Danish_CPR_Pct"] = cpr["Danish_CPR_Pct"]
        sched_smm = scheduled_amortization_series(df.index)
        df["Scheduled_Amort_SMM"] = sched_smm
        monthly_cpr = df["US_CPR_Pct"] / 100 / 12
        df["US_Simulated_Monthly_Rolloff_Billions"] = (
            -holdings_b * (monthly_cpr + sched_smm + curtailment_smm)
        )
        monthly_cpr_dk = df["Danish_CPR_Pct"] / 100 / 12
        dk_rolloff = np.zeros(len(df))
        dk_balance = np.zeros(len(df))
        qt_start_idx = df.index.get_indexer([QT_START], method="nearest")[0]
        init_balance = float(holdings_b.iloc[qt_start_idx])
        bal = init_balance
        for i in range(len(df)):
            if i < qt_start_idx:
                dk_balance[i] = float(holdings_b.iloc[i])
                continue
            dk_balance[i] = bal
            monthly_drain = (float(monthly_cpr_dk.iloc[i])
                             + float(sched_smm.iloc[i])
                             + float(curtailment_smm.iloc[i]))
            rolloff = bal * monthly_drain
            dk_rolloff[i] = -rolloff
            bal = max(bal - rolloff, 0.0)
        df["Danish_Simulated_Monthly_Rolloff_Billions"] = dk_rolloff
        df["Danish_Balance_Billions"] = dk_balance

    if apply_settlement_lag_kernel and not use_hazard_microsim:
        df["US_Simulated_Monthly_Rolloff_Billions"] = apply_settlement_lag(
            df["US_Simulated_Monthly_Rolloff_Billions"]
        )
        df["Danish_Simulated_Monthly_Rolloff_Billions"] = apply_settlement_lag(
            df["Danish_Simulated_Monthly_Rolloff_Billions"]
        )

    # --- Empirical CPR: back out from actual roll-off and sched. amort. ---
    actual_abs = df["Actual_Monthly_Rolloff_Billions"].abs()
    empirical_smm = (actual_abs / holdings_b) - df["Scheduled_Amort_SMM"]
    df["Empirical_CPR_Pct"] = (empirical_smm.clip(lower=0) * 12 * 100)

    # --- Extension deltas vs. QT target -----------------------------------
    qt_mask = df.index >= QT_START
    df["US_Extension_Delta_Billions"] = np.where(
        qt_mask,
        df["US_Simulated_Monthly_Rolloff_Billions"] - df["QT_Target_Billions"],
        np.nan,
    )
    df["Danish_Extension_Delta_Billions"] = np.where(
        qt_mask,
        df["Danish_Simulated_Monthly_Rolloff_Billions"]
        - df["QT_Target_Billions"],
        np.nan,
    )

    # Net extension delta per month (positive = shortfall, negative = overshoot)
    df["US_Missed_Rolloff_Billions"] = (
        df["US_Extension_Delta_Billions"].fillna(0.0)
    )
    df["Danish_Missed_Rolloff_Billions"] = (
        df["Danish_Extension_Delta_Billions"].fillna(0.0)
    )

    # NET accumulation during active QT; flatline after Dec 2025
    us_active = df["US_Missed_Rolloff_Billions"].where(qt_active, 0.0)
    dk_active = df["Danish_Missed_Rolloff_Billions"].where(qt_active, 0.0)
    df["US_Cumulative_Trapped_Liquidity_Billions"] = us_active.cumsum()
    df["Danish_Cumulative_Trapped_Liquidity_Billions"] = dk_active.cumsum()
    df.loc[~qt_mask, "US_Cumulative_Trapped_Liquidity_Billions"] = np.nan
    df.loc[~qt_mask, "Danish_Cumulative_Trapped_Liquidity_Billions"] = np.nan

    return df


# ---------------------------------------------------------------------------
# Section 3 – Visualization
# ---------------------------------------------------------------------------
def plot_dashboard(df: pd.DataFrame, save_path=None):
    """Three-panel publication-quality dashboard."""
    if save_path is None:
        save_path = MBS_DASHBOARD_PNG
    qt_mask = df.index >= QT_START
    qt_df = df.loc[qt_mask].dropna(subset=["Actual_Monthly_Rolloff_Billions"])

    fig, (ax1, ax2, ax3) = plt.subplots(
        3, 1, figsize=(14, 14), sharex=True,
        gridspec_kw={"height_ratios": [3, 2, 2]},
    )
    fig.suptitle(
        "Federal Reserve MBS Portfolio — Extension Risk Delta Dashboard",
        fontsize=16, fontweight="bold", y=0.97,
    )

    # ---- Subplot 1: Portfolio & Interest Rates (dual axis) ----------------
    color_mbs = "#1f77b4"
    ax1.plot(
        df.index, df["WSHOMCB"] / 1_000,
        color=color_mbs, linewidth=1.8, label="Fed MBS Holdings ($B)",
    )
    ax1.set_ylabel("Fed MBS Holdings ($B)", color=color_mbs, fontsize=12)
    ax1.tick_params(axis="y", labelcolor=color_mbs)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))

    ax1_r = ax1.twinx()
    color_rate = "#d62728"
    ax1_r.plot(
        df.index, df["MORTGAGE30US"],
        color=color_rate, linewidth=1.5, linestyle="--",
        label="30-Yr Mortgage Rate (%)",
    )
    ax1_r.set_ylabel("30-Yr Mortgage Rate (%)", color=color_rate, fontsize=12)
    ax1_r.tick_params(axis="y", labelcolor=color_rate)

    # QT era shading
    ax1.axvspan(QT_START, df.index[-1], color="grey", alpha=0.12, label="QT Era")

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_r.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=10)
    ax1.set_title("Total Fed MBS Holdings & 30-Year Mortgage Rate", fontsize=13)
    ax1.grid(axis="y", alpha=0.3)

    # ---- Subplot 2: Extension Delta bar chart -----------------------------
    # Bar color compares actual roll-off to the row-wise (time-dependent) target
    bar_colors = np.where(
        qt_df["Actual_Monthly_Rolloff_Billions"]
        <= qt_df["QT_Target_Billions"],
        "#2ca02c",   # green — target met
        "#e8722a",   # orange — target missed (extension risk)
    )
    ax2.bar(
        qt_df.index, qt_df["Actual_Monthly_Rolloff_Billions"],
        width=20, color=bar_colors, edgecolor="none", alpha=0.85,
        label="Actual Monthly Roll-Off ($B)",
    )
    # ABM-calibrated counterfactual roll-off paths
    ax2.plot(
        qt_df.index, qt_df["US_Simulated_Monthly_Rolloff_Billions"],
        color="#1f77b4", linewidth=2.0,
        label="ABM U.S. CPR Simulated Roll-Off ($B)",
    )
    ax2.plot(
        qt_df.index, qt_df["Danish_Simulated_Monthly_Rolloff_Billions"],
        color="#d62728", linewidth=2.0, linestyle="--",
        label="ABM Danish CPR Simulated Roll-Off ($B)",
    )
    ax2.plot(
        qt_df.index, qt_df["QT_Target_Billions"],
        color="#555555", linewidth=1.8, linestyle="--", drawstyle="steps-post",
        label="QT Cap (-17.5B ramp, -35B full, 0B post-QT)",
    )
    # Mark the QT end date
    ax2.axvline(QT_END, color="#222222", linewidth=1.0, linestyle=":",
                alpha=0.6)
    ax2.set_ylabel("Monthly Roll-Off ($B)", fontsize=12)
    ax2.set_title(
        "Monthly MBS Roll-Off vs. QT Target — Actual and ABM-Calibrated "
        "Counterfactuals", fontsize=13,
    )
    ax2.grid(axis="y", alpha=0.3)

    # Dynamic_Friction overlay on a twin axis so the friction regime is visible
    ax2f = ax2.twinx()
    ax2f.plot(
        qt_df.index, qt_df["Dynamic_Friction"] * 100,
        color="#6a3d9a", linewidth=1.4, linestyle=":",
        label="Dynamic Friction (%)",
    )
    ax2f.set_ylabel("Dynamic Friction (%)", fontsize=11, color="#6a3d9a")
    ax2f.tick_params(axis="y", labelcolor="#6a3d9a")
    ax2f.set_ylim(6.5, 11.0)
    # Merge legends from both axes
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2f.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc="lower left", fontsize=9)

    # ---- Subplot 3: Cumulative Trapped Liquidity (US vs Danish) -----------
    cum_us = df.loc[qt_mask, "US_Cumulative_Trapped_Liquidity_Billions"].dropna()
    cum_dk = df.loc[
        qt_mask, "Danish_Cumulative_Trapped_Liquidity_Billions"
    ].dropna()

    ax3.fill_between(cum_us.index, 0, cum_us.values,
                     color="#8B0000", alpha=0.55,
                     label="U.S. System (ABM-calibrated)")
    ax3.plot(cum_us.index, cum_us.values, color="#8B0000", linewidth=1.5)
    ax3.fill_between(cum_dk.index, 0, cum_dk.values,
                     color="#e8722a", alpha=0.45,
                     label="Danish System (ABM-calibrated)")
    ax3.plot(cum_dk.index, cum_dk.values, color="#e8722a", linewidth=1.5,
             linestyle="--")

    # Annotate both terminal endpoints
    ax3.annotate(
        f"U.S.: ${cum_us.iloc[-1]:,.1f}B trapped",
        xy=(cum_us.index[-1], cum_us.iloc[-1]),
        xytext=(-210, -20), textcoords="offset points",
        fontsize=11, fontweight="bold", color="#8B0000",
        arrowprops=dict(arrowstyle="->", color="#8B0000", lw=1.5),
    )
    ax3.annotate(
        f"Danish: ${cum_dk.iloc[-1]:,.1f}B trapped",
        xy=(cum_dk.index[-1], cum_dk.iloc[-1]),
        xytext=(-210, 60), textcoords="offset points",
        fontsize=11, fontweight="bold", color="#e8722a",
        arrowprops=dict(arrowstyle="->", color="#e8722a", lw=1.5),
    )

    # Mark the QT end date — accumulation stops here (permanent trap)
    ax3.axvline(QT_END, color="#222222", linewidth=1.0, linestyle=":",
                alpha=0.6)
    ax3.text(QT_END, 0, " QT ends\n (Dec 2025)", fontsize=9,
             color="#222222", va="bottom", ha="left")

    ax3.set_ylabel("Cumulative Trapped Liquidity ($B)", fontsize=12)
    ax3.set_title(
        "Cumulative Trapped Liquidity — The Permanent Trap "
        "(U.S. vs. Danish Counterfactual)", fontsize=13,
    )
    ax3.legend(loc="upper left", fontsize=10)
    ax3.grid(axis="y", alpha=0.3)

    # Shared x-axis formatting
    ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    fig.autofmt_xdate(rotation=45)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(save_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"\nDashboard saved to {save_path}")


def plot_cpr_diagnostic(df: pd.DataFrame,
                        save_path=None):
    if save_path is None:
        save_path = CPR_DIAGNOSTIC_PNG
    """
    Diagnostic chart comparing the ABM-predicted CPR against the empirical
    CPR backed out from actual SOMA roll-off.  Two panels:

      1. Time-series: both CPRs month-by-month during QT, with the gap shaded.
      2. Scatter: empirical vs. ABM CPR indexed by that month's mortgage rate,
         showing where the ABM over-/under-predicts along the rate curve.
    """
    qt_mask = df.index >= QT_START
    qt = df.loc[qt_mask].dropna(subset=["Empirical_CPR_Pct"]).copy()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle(
        "CPR Diagnostic — ABM Prediction vs. Empirical (SOMA-implied)",
        fontsize=15, fontweight="bold", y=0.98,
    )

    # --- Panel 1: time-series ---
    ax1.plot(qt.index, qt["Empirical_CPR_Pct"],
             color="#2ca02c", linewidth=2.0, label="Empirical CPR (SOMA-implied)")
    ax1.plot(qt.index, qt["US_CPR_Pct"],
             color="#1f77b4", linewidth=2.0, linestyle="--",
             label="ABM U.S. CPR")
    ax1.fill_between(qt.index, qt["Empirical_CPR_Pct"], qt["US_CPR_Pct"],
                     alpha=0.18, color="#d62728", label="Gap")
    ax1.set_ylabel("Annual CPR (%)", fontsize=12)
    ax1.set_xlabel("Date", fontsize=12)
    ax1.set_title("Monthly CPR During QT", fontsize=13)
    ax1.legend(fontsize=10, loc="upper right")
    ax1.grid(alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    fig.autofmt_xdate(rotation=45)

    # --- Panel 2: scatter by mortgage rate ---
    sc = ax2.scatter(qt["MORTGAGE30US"], qt["Empirical_CPR_Pct"],
                     c=qt.index.astype(np.int64) // 10**9,
                     cmap="viridis", s=60, edgecolors="white", linewidth=0.5,
                     label="Empirical CPR", zorder=3)
    ax2.scatter(qt["MORTGAGE30US"], qt["US_CPR_Pct"],
                marker="x", color="#d62728", s=50,
                label="ABM U.S. CPR", zorder=2)

    # Connect each empirical-ABM pair with a thin line to visualise the gap
    for _, row in qt.iterrows():
        ax2.plot([row["MORTGAGE30US"], row["MORTGAGE30US"]],
                 [row["Empirical_CPR_Pct"], row["US_CPR_Pct"]],
                 color="#999999", linewidth=0.6, alpha=0.5)

    ax2.set_xlabel("30-Yr Mortgage Rate (%)", fontsize=12)
    ax2.set_ylabel("Annual CPR (%)", fontsize=12)
    ax2.set_title("CPR vs. Mortgage Rate", fontsize=13)
    ax2.legend(fontsize=10, loc="upper right")
    ax2.grid(alpha=0.3)

    cbar = fig.colorbar(sc, ax=ax2, pad=0.02)
    cbar.set_label("Date", fontsize=10)
    tick_locs = cbar.get_ticks()
    cbar.set_ticklabels([
        pd.Timestamp(int(t), unit="s").strftime("%b '%y")
        for t in tick_locs
    ])

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    plt.savefig(save_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"\nCPR diagnostic saved to {save_path}")


# ---------------------------------------------------------------------------
# Section 4 – Summary Statistics
# ---------------------------------------------------------------------------
def _series_stats(s: pd.Series) -> dict:
    s = s.dropna()
    if s.empty:
        return {"min": None, "mean": None, "max": None, "std": None, "n": 0}
    return {
        "min": float(s.min()),
        "mean": float(s.mean()),
        "max": float(s.max()),
        "std": float(s.std()) if len(s) > 1 else 0.0,
        "n": int(len(s)),
    }


def export_headline_metrics(df: pd.DataFrame) -> dict:
    """
    Single source of truth for headline figures.  Always aggregates over
    qt_active_frame() — the 42-month active QT window [QT_START, QT_END).
    """
    qt_df = qt_active_frame(df)
    assert_qt_window_only(qt_df.index)
    n_months = len(qt_df)
    expected = expected_qt_active_months()

    total_trapped = float(qt_df["Extension_Delta_Billions"].sum())
    total_trapped_us = float(qt_df["US_Missed_Rolloff_Billions"].sum())
    total_trapped_dk = float(qt_df["Danish_Missed_Rolloff_Billions"].sum())
    institutional_gap = total_trapped_us - total_trapped_dk
    share_explained = (total_trapped_us / total_trapped * 100
                       if total_trapped else float("nan"))

    out = {
        "qt_window": {
            "start": QT_START.strftime("%Y-%m-%d"),
            "end_exclusive": QT_END.strftime("%Y-%m-%d"),
            "end_inclusive_label": (
                (QT_END - pd.offsets.MonthBegin(1)).strftime("%B %Y")
            ),
            "n_months": n_months,
            "n_months_expected": expected,
        },
        "dollars_b": {
            "empirical_trapped": total_trapped,
            "us_trapped": total_trapped_us,
            "danish_trapped": total_trapped_dk,
            "institutional_gap": institutional_gap,
            "share_explained_pct": share_explained,
            "avg_actual_rolloff_monthly": float(
                qt_df["Actual_Monthly_Rolloff_Billions"].mean()
            ),
        },
        "rolloff_source": (
            str(df["Rolloff_Source"].iloc[0])
            if "Rolloff_Source" in df.columns else None
        ),
    }

    if "Danish_Balance_Billions" in qt_df.columns:
        out["danish_portfolio_b"] = {
            "start": float(qt_df["Danish_Balance_Billions"].iloc[0]),
            "end": float(qt_df["Danish_Balance_Billions"].iloc[-1]),
        }

    if "Scheduled_Amort_SMM" in qt_df.columns:
        smm = qt_df["Scheduled_Amort_SMM"]
        holdings_b = qt_df["WSHOMCB"] / 1_000
        out["scheduled_amort_b"] = {
            "total": float((holdings_b * smm).sum()),
            "smm_mean_pct": float(smm.mean() * 100),
            "annualized_pct": float(smm.mean() * 12 * 100),
        }

    if "Curtailment_SMM" in qt_df.columns:
        curt = qt_df["Curtailment_SMM"]
        holdings_b = qt_df["WSHOMCB"] / 1_000
        out["curtailment_b"] = {
            "total": float((holdings_b * curt).sum()),
            "smm_mean_pct": float(curt.mean() * 100),
            "annualized_pct": float(curt.mean() * 12 * 100),
        }

    if "Empirical_CPR_Pct" in qt_df.columns:
        ecpr = qt_df["Empirical_CPR_Pct"]
        acpr = qt_df["US_CPR_Pct"]
        dcpr = qt_df["Danish_CPR_Pct"]
        wedge = dcpr - acpr
        abm_gap = acpr - ecpr
        gof = cpr_goodness_of_fit(ecpr, acpr)
        xcorr = cpr_cross_correlation(ecpr, acpr)

        out["cpr_pct"] = {
            "empirical": _series_stats(ecpr),
            "us_abm": _series_stats(acpr),
            "danish": _series_stats(dcpr),
            "wedge_dk_minus_us_pp": _series_stats(wedge),
            "abm_minus_empirical_pp": {
                "mean": float(abm_gap.mean()),
                "max": float(abm_gap.max()),
            },
        }
        out["goodness_of_fit"] = gof
        out["cross_correlation"] = {str(k): v for k, v in xcorr.items()}
        best_lag = max(xcorr, key=xcorr.get) if xcorr else None
        out["cross_correlation_peak"] = (
            {"lag": int(best_lag), "r": float(xcorr[best_lag])}
            if best_lag is not None else None
        )

        holdout_date = pd.Timestamp("2024-01-01")
        in_mask = ecpr.index < holdout_date
        out_mask = ecpr.index >= holdout_date
        if in_mask.sum() >= 6 and out_mask.sum() >= 6:
            gof_in = cpr_goodness_of_fit(ecpr[in_mask], acpr[in_mask])
            gof_out = cpr_goodness_of_fit(ecpr[out_mask], acpr[out_mask])
            in_trapped = float(
                qt_df.loc[in_mask, "US_Missed_Rolloff_Billions"].sum()
            )
            in_emp = float(qt_df.loc[in_mask, "Extension_Delta_Billions"].sum())
            out_trapped = float(
                qt_df.loc[out_mask, "US_Missed_Rolloff_Billions"].sum()
            )
            out_emp = float(
                qt_df.loc[out_mask, "Extension_Delta_Billions"].sum()
            )
            out["holdout"] = {
                "split_date": holdout_date.strftime("%Y-%m-%d"),
                "in_sample": {
                    **gof_in["raw"],
                    "share_explained_pct": (
                        in_trapped / in_emp * 100 if in_emp else float("nan")
                    ),
                },
                "out_of_sample": {
                    **gof_out["raw"],
                    "share_explained_pct": (
                        out_trapped / out_emp * 100 if out_emp else float("nan")
                    ),
                },
            }

    if "Dynamic_Friction" in qt_df.columns:
        fric = qt_df["Dynamic_Friction"] * 100
        out["dynamic_friction_pct"] = _series_stats(fric)

    if n_months != expected:
        out["warning"] = (
            f"qt_active_frame has {n_months} months; expected {expected}. "
            "Do not cite headline CPR means from index >= QT_START without "
            "the QT_END upper bound — that includes post-QT months."
        )

    return out


def build_production_metrics(
    apply_settlement_lag_kernel: bool = True,
) -> tuple:
    """
    Fetch live data and run the production compute_metrics() path used by
    main(), sensitivity_analysis, and freeze_run.
    Returns (metrics_df, calibration_meta).
    """
    import abm_lockin_simulation as abm

    df = fetch_data()
    soma_rolloff = fetch_soma_mbs_monthly()
    cohorts = fetch_soma_mbs_cohorts()
    ref = abm.reference_cohort(cohorts)
    income, home_value = abm.fetch_macro_from_fred()
    mobility_scale = abm.calibrate_mobility_scale(
        income, home_value,
        cohort_rate=ref["coupon"],
        cohort_months=ref["months_elapsed"],
    )
    abm_params = {
        "mobility_scale": mobility_scale,
        "median_income": income,
        "median_home_value": home_value,
    }
    df = compute_metrics(
        df,
        soma_rolloff=soma_rolloff,
        cohorts=cohorts,
        use_burnout=False,
        apply_settlement_lag_kernel=apply_settlement_lag_kernel,
        abm_params=abm_params,
    )
    meta = {
        "apply_settlement_lag_kernel": apply_settlement_lag_kernel,
        "mobility_scale": mobility_scale,
        "median_income": income,
        "median_home_value": home_value,
        "reference_cohort": ref,
        "n_cohorts": len(cohorts),
        "cohort_wac_pct": round(
            sum(c["coupon"] * c["weight"] for c in cohorts) * 100, 2
        ),
    }
    return df, meta


def print_summary(df: pd.DataFrame):
    """Print key aggregate metrics to stdout."""
    metrics = export_headline_metrics(df)
    n_months = metrics["qt_window"]["n_months"]
    expected = metrics["qt_window"]["n_months_expected"]
    if n_months != expected:
        print(
            f"\nWARNING: aggregating {n_months} QT months "
            f"(expected {expected}). Use qt_active_frame(), not "
            f"index >= QT_START alone.\n"
        )

    dollars = metrics["dollars_b"]
    total_trapped = dollars["empirical_trapped"]
    total_trapped_us = dollars["us_trapped"]
    total_trapped_dk = dollars["danish_trapped"]
    institutional_gap = dollars["institutional_gap"]
    share_explained = dollars["share_explained_pct"]

    rolloff_source = metrics.get("rolloff_source", "?")
    qt_end_prev = metrics["qt_window"]["end_inclusive_label"]
    print("\n" + "=" * 65)
    print(" MBS EXTENSION RISK — SUMMARY STATISTICS")
    print("=" * 65)
    print(f"  Roll-off data source:  {rolloff_source}")
    print(f"  Active QT Period:  {QT_START.strftime('%B %Y')} → {qt_end_prev}")
    print(f"  QT Target (ramp-up Jun–Aug 2022):"
          f"  {QT_TARGET_RAMP_B:+.0f} $B / month")
    print(f"  QT Target (full pace Sep 2022+):"
          f"  {QT_TARGET_FULL_B:+.0f} $B / month")
    print(f"  Post-QT Target (from {QT_END.strftime('%B %Y')}):"
          f"  {POST_QT_TARGET_B:+.0f} $B / month")
    print(f"  Avg Actual Roll-Off:      {dollars['avg_actual_rolloff_monthly']:+.2f} $B / month")
    print(f"  Net Trapped Liquidity (sum of monthly deltas):"
          f"  ${total_trapped:,.1f}B")
    print("-" * 65)
    print(" ABM-CALIBRATED COUNTERFACTUALS (CPR + sched. amort. + curtailment)")
    print(f"  U.S. System Trapped Liquidity:    ${total_trapped_us:,.1f}B"
          f"  ({share_explained:.1f}% of empirical)")
    print(f"  Danish System Trapped Liquidity:  ${total_trapped_dk:,.1f}B"
          f"  (dynamic-balance counterfactual)")
    if "danish_portfolio_b" in metrics:
        dk = metrics["danish_portfolio_b"]
        print(f"  Danish Portfolio: ${dk['start']:,.0f}B → ${dk['end']:,.0f}B "
              f"(−${dk['start'] - dk['end']:,.0f}B)")
    print(f"  Institutional Gap (U.S. − Danish): ${institutional_gap:,.1f}B")
    if "scheduled_amort_b" in metrics:
        sa = metrics["scheduled_amort_b"]
        print(f"  Sched. amortization during QT:    ${sa['total']:,.1f}B "
              f"(SMM {sa['smm_mean_pct']:.3f}% avg ≈ "
              f"{sa['annualized_pct']:.2f}% ann.)")
    if "curtailment_b" in metrics:
        cb = metrics["curtailment_b"]
        print(f"  Curtailment during QT:            ${cb['total']:,.1f}B "
              f"(SMM {cb['smm_mean_pct']:.3f}% avg ≈ "
              f"{cb['annualized_pct']:.2f}% ann.)")
    if "cpr_pct" in metrics:
        cpr = metrics["cpr_pct"]
        gof = metrics["goodness_of_fit"]
        print("-" * 65)
        print(" CPR DIAGNOSTIC (ABM vs. SOMA-implied empirical)")
        e, u, d = cpr["empirical"], cpr["us_abm"], cpr["danish"]
        print(f"  Empirical CPR:  min {e['min']:.2f}%  |  "
              f"mean {e['mean']:.2f}%  |  max {e['max']:.2f}%")
        print(f"  ABM U.S. CPR:   min {u['min']:.2f}%  |  "
              f"mean {u['mean']:.2f}%  |  max {u['max']:.2f}%")
        print(f"  Danish CPR:     min {d['min']:.2f}%  |  "
              f"mean {d['mean']:.2f}%  |  max {d['max']:.2f}%")
        w = cpr["wedge_dk_minus_us_pp"]
        print(f"  Institutional wedge (DK−US):  mean {w['mean']:.2f}pp  |  "
              f"range {w['min']:.2f}–{w['max']:.2f}pp")
        ag = cpr["abm_minus_empirical_pp"]
        print(f"  ABM - Empirical gap:  mean {ag['mean']:+.2f}pp  |  "
              f"max {ag['max']:+.2f}pp")
        r = gof["raw"]
        s = gof["smoothed"]
        print(f"  Goodness-of-fit (N={r['n']} months):")
        print(f"    Raw:      R²={r['r2']:.3f}  RMSE={r['rmse']:.2f}pp"
              f"  MAE={r['mae']:.2f}pp  r={r['corr']:.3f}")
        print(f"    Smoothed: R²={s['r2']:.3f}  RMSE={s['rmse']:.2f}pp"
              f"  MAE={s['mae']:.2f}pp  r={s['corr']:.3f}")

        xcorr = {int(k): v for k, v in metrics["cross_correlation"].items()}
        best_lag = max(xcorr, key=xcorr.get)
        print(f"  Cross-correlation (lag −3 … +3 months):")
        lags_str = "    " + "  ".join(
            f"{lag:+d}:{xcorr[lag]:+.3f}" for lag in sorted(xcorr)
        )
        print(lags_str)
        if best_lag != 0 and xcorr[best_lag] > 0:
            print(f"  → Peak at lag {best_lag:+d} (r={xcorr[best_lag]:+.3f}); "
                  f"lag-alignment may improve fit")
        else:
            print(f"  → No lag flips correlation positive; structural sign "
                  f"mismatch, not settlement noise")

        if "holdout" in metrics:
            h = metrics["holdout"]
            ri, ro = h["in_sample"], h["out_of_sample"]
            holdout_date = pd.Timestamp(h["split_date"])
            print(f"  Holdout split at {holdout_date.strftime('%b %Y')}:")
            print(f"    In-sample  (N={ri['n']:>2}): R²={ri['r2']:+.3f}  "
                  f"RMSE={ri['rmse']:.2f}pp  "
                  f"share={ri['share_explained_pct']:.1f}%")
            print(f"    Out-of-sample (N={ro['n']:>2}): R²={ro['r2']:+.3f}  "
                  f"RMSE={ro['rmse']:.2f}pp  "
                  f"share={ro['share_explained_pct']:.1f}%")

    if "dynamic_friction_pct" in metrics:
        fr = metrics["dynamic_friction_pct"]
        print("-" * 65)
        print(" DYNAMIC MACROECONOMIC FRICTION (inventory + sentiment)")
        print(f"  Friction range:  min {fr['min']:.2f}%  |  "
              f"mean {fr['mean']:.2f}%  |  max {fr['max']:.2f}%")
    print("=" * 65 + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("Building production metrics (FRED + SOMA + settlement lag) …")
    df, _meta = build_production_metrics(apply_settlement_lag_kernel=True)

    print("Generating dashboard …")
    plot_dashboard(df)

    print("Generating CPR diagnostic …")
    plot_cpr_diagnostic(df)

    print_summary(df)


if __name__ == "__main__":
    main()
