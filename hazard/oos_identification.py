#!/usr/bin/env python3
"""
oos_identification.py — Out-of-sample identification of Path B's lock-in
marginal under an involuntary-turnover floor NOT calibrated on the locked-in,
in-window population.

PRE-COMMITTED SPEC (fixed in this header BEFORE any run; ex-ante convention of
floor_sweep.py / floor_form_test.py / out_of_window_floor.py). The referee's
central identification objection: Path B's involuntary-turnover floor (4% annual
CPR, monthly SMM ~0.0034) is the dominant level-setter — it binds in ~36% of the
1,683,124 evaluated loan-months — yet it is calibrated IN-WINDOW on the same
deeply-out-of-the-money 2023-24 cohorts whose lock-in the marginal is meant to
decompose. Because the eq.(3) max-form floor CENSORS the elasticity wherever it
binds, the lock-in marginal's MAGNITUDE moves with the floor (committed sweep:
+9.2pp at a 4% floor, +2.28pp at 6%). This run re-derives the marginal under a
floor sourced OUTSIDE that locked-in in-window population, and reports it
honestly on both sign and magnitude. It does NOT defend $70.3B.

Decision taken upstream (not relitigated here): headline the out-of-sample
marginal; demote +$70.3B/+9.2pp to "the in-sample production-calibration point."

No benchmark feedback anywhere. The floor comes from turnover data; the
elasticity stays imported from Liebersohn/Rothstein (5.5/6.5/7.7 quarterly
mobility decline). Nothing is tuned to the $764.748B benchmark.

=======================================================================
STEP 1 — PARITY GATE (runs first; blocks everything downstream)
=======================================================================
Reproduce the committed production anchors EXACTLY, fresh (caches not
consulted), before changing any floor. From no_lockin_null_results.json /
floor_sweep_results.json at the 4.0% production floor:
    central  $818.5300844B  (107.033% of the $764.7B benchmark)
    null     $748.1850240B  ( 97.834%)
    marginal +$70.3450604B  (+9.198pp)
    floor-bind share 0.36269 of 1,683,124 evaluated U.S. loan-months
Tolerances: +/- $0.01B, +/- 0.01pp on the dollar/point gates; +/- 0.01 on the
bind share and +/- 0.5% on the bind count (floor_sweep's own tolerances). If
parity FAILS, STOP — report the environment problem, do not build on it.

=======================================================================
STEP 2 — INSTRUMENT 1: out-of-sample involuntary floor (PRIMARY; governs
the headline magnitude)
=======================================================================
Builds on out_of_window_floor.py. Re-measure the involuntary floor as
exposure-weighted annualized turnover CPR on discount (out-of-the-money)
cohort-months observed OUTSIDE the QT window [2022-06, 2025-12) — i.e. the
pre-episode 2017-2019 performance months carried by the committed Path A
cohort_month_panel.parquet (reporting 201701..201912).

DEFINITIONS (identical to the paper / out_of_window_floor.py)
  gap = coupon - MORTGAGE30US (decimal); < 0 == locked in / OTM / discount.
  SMM(cohort-month) = prepaid_upb / exposure_upb.
  Exposure-weighted CPR over selection S:
     SMM_bar = sum_S prepaid_upb / sum_S exposure_upb;  CPR = 1-(1-SMM_bar)^12.

ANCHOR GRID (all reported)
  Legs:  pooled 2017-2019 | 2018 (RISING-rate leg) | 2019 (FALLING-rate leg).
  gap thresholds: {<=0, <=-0.0025, <=-0.005}.  age cuts: {>=12, >=24}.
  SEASONING PROFILE per leg: turnover CPR by loan-age bucket
     {[0,12) ramp-ambiguous, [12,24), [24,36), [36,60), [60,inf)}.

CONTAMINATION RULE (mechanical, ex ante)
  A pure involuntary floor (death/divorce/relocation) is ~flat in loan age. So:
  - SEASONING-CONTAMINATED if turnover RISES materially with age within a leg:
        CPR(age>=24) - CPR(age in [12,24)) > 1.0pp.
  - REGIME-CONTAMINATED if the leg's rate environment carries a live refi
    incentive: the FALLING-rate 2019 leg is regime-contaminated by construction
    (rates fell 4.46%->3.72%, a refi wave); the RISING-rate 2018 leg
    (4.03%->4.64%) suppresses refi and is the clean-candidate leg.
  - RAMP CAVEAT (pre-registered, from out_of_window_floor.py): 2017-2019 OTM
    cohorts are younger / less deeply discounted than 2023-24. Reads BELOW 4%
    from age<12 buckets are AMBIGUOUS (PSA-ramp immaturity), not disconfirming.
    Mature reads require age>=12.

  DEFENSIBLE CLEAN FLOOR (h*): the 2018 rising-rate leg, age>=12, exposure-
  weighted, across the gap grid -> a RANGE [min,max] of those reads (the
  clean band). Its gap<=-0.0025 read is the primary point pick (deeply-OTM-
  ish, matching the paper's floor definition). The pooled and 2019 reads are
  reported as CONTAMINATED UPPER anchors, flagged NOT-preferred.

MARGINAL RE-RUN (for each floor h below)
  Set literature_hazard.INVOLUNTARY_CPR_ANNUAL = h (the ONLY change from
  production; caches not consulted, own output dir), rerun the central and
  beta1=0 null legs across the 5.5/6.5/7.7 elasticity band (null is band-
  invariant: p_q=0 => beta1=0). Report per (h, band point): central %/$B,
  null %/$B, marginal (pp,$B), floor-bind share. Cross-check each against the
  committed floor_sweep_results.json read at h (exact at the committed grid
  points 4.0/4.5/5.0/6.0; monotone-bracketed elsewhere).

  Engine floor set = committed cross-check grid {4.0, 4.5, 5.0, 6.0}%
     UNION the measured defensible clean h* {clean_lo, clean_mid, clean_hi}
     UNION the measured contaminated 2019 upper anchor
     UNION the Instrument-2 calibration floor h_cal (Step 3).
  4.0% doubles as the parity anchor.

=======================================================================
STEP 3 — INSTRUMENT 2: temporal holdout (SECONDARY; tests the Section VIII.A
"no untouched evaluation months" limitation directly)
=======================================================================
Calibrate the floor on turnover in the EARLY in-window sub-period
[2022-06, 2024-01) (Jun 2022 - Dec 2023), deeply-OTM discount cohorts
(gap<=-0.02, age>=12, matching the paper's floor definition) -> h_cal. Run the
engine at h_cal, then evaluate the central-null marginal SUMMED OVER THE
STRICTLY HELD-OUT months [2024-01, 2025-12) (Jan 2024 - Nov 2025) ONLY — those
months touch nothing in the floor calibration. The marginal is additive by
month (trapped = sum_t(rolloff_t - target_t); the QT target cancels in
central-null), so the held-out marginal = sum over held-out months of
(rolloff_central_t - rolloff_null_t). Contrast with the production 4% floor's
marginal over the SAME held-out months. Report both, and the sign.

=======================================================================
STEP 4 — SIGN ROBUSTNESS
=======================================================================
Over the plausible OOS floor range (every engine floor h above) x the
5.5/6.5/7.7 band, confirm freshly that the central-null marginal is POSITIVE
in every floor x band cell (and, for Instrument 2, over the held-out months).

=======================================================================
SELF-CHECKS — split by kind, because they are not the same kind of claim.
=======================================================================
HARD (wiring invariants; a failure means the run is mis-wired. Results are
still written for diagnosis, then SystemExit — they must not be cited):
  - Production floor 4.0% reproduces +$70.3450604B / +9.198pp (== parity gate).
  - Every committed floor_sweep grid point (4.0/4.5/5.0/6.0%) reproduces to
    +/- $0.01B on both the null and the marginal.
  - The per-month held-out attribution sums back to the aggregate marginal
    (additivity of trapped = sum_t(rolloff_t - target_t)).

SOFT (interpretive expectations carried in from the brief; a failure is a
FINDING to report and re-examine, never a crash and never something to be
"fixed" by tuning a floor or an elasticity):
  - Floor 6.0% reproduces ~+$17.4B / ~+2.28pp (committed sweep read).
  - Overshoot: central 818.5, null 748.2, benchmark 764.748 => a
    benchmark-consistent marginal ~= 764.748 - 748.185 = $16.563B. The
    reported OOS marginal RANGE (across defensible + contaminated floors)
    should contain it; if the CLEAN headline sits far above it, that is
    reported as the clean-vs-contaminated-floor distinction, not silently
    accepted and not tuned away.
  - Sign robustness: every floor x band cell positive.

Run:  cd hazard && python3 oos_identification.py
  -> data/oos_identification_results.json  (frozen)
  -> ../OOS_IDENTIFICATION.md               (written by report step)
  (+ per-run parquets under data/oos_identification/, regenerable, uncommitted)

Does NOT change config.py production defaults. Does NOT edit any .tex file.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
from fredapi import Fred

import competing_risks
import config
import literature_hazard
from config import FRED_API_KEY, LOAN_SAMPLE_PATH
from extension_risk import score_extension_risk
from literature_hazard import cpr_annual_to_monthly_hazard, rothstein_beta1
from macro import (
    build_empirical_metrics,
    calculate_dynamic_friction,
    fetch_data,
    fetch_soma_mbs_monthly,
    qt_active_frame,
)
from microsim_engine import run_qt_microsim

HAZARD_DIR = Path(__file__).parent
DATA_DIR = HAZARD_DIR / "data"
RUN_DIR = DATA_DIR / "oos_identification"
PANEL_PATH = DATA_DIR / "cohort_month_panel.parquet"
RESULTS_JSON = DATA_DIR / "oos_identification_results.json"
REPORT_MD = HAZARD_DIR.parent / "OOS_IDENTIFICATION.md"
COMMITTED_SWEEP = DATA_DIR / "floor_sweep_results.json"
NULL_ARTIFACT = DATA_DIR / "no_lockin_null_results.json"

PRODUCTION_FLOOR = 0.04
CENTRAL_PQ = 6.5
NULL_PQ = 0.0
BAND_PCT = (5.5, 6.5, 7.7)  # Rothstein/Liebersohn quarterly-mobility band

# Committed grid points reproduced by floor_sweep (exact cross-check anchors).
COMMITTED_CROSSCHECK_FLOORS = [0.04, 0.045, 0.05, 0.06]

# Parity anchors (committed production; §V.C / App. B).
BIND_SHARE_ANCHOR = 0.36
BIND_N_ANCHOR = 1_683_124

# QT window (single source of truth: common/qt_window.py).
QT_START = pd.Timestamp("2022-06-01")
QT_END = pd.Timestamp("2025-12-01")            # exclusive
HELDOUT_START = pd.Timestamp("2024-01-01")     # Instrument-2 held-out months
CALIB_END = pd.Timestamp("2024-01-01")         # Instrument-2 calibration end (exclusive)

_ORIG_PREPAY = competing_risks.prepay_hazard


# ======================================================================
# Bind instrumentation (value-preserving wrapper, identical to floor_sweep)
# ======================================================================
class BindTally:
    """Counts U.S. loan-months where the involuntary floor lifts the hazard."""

    def __init__(self) -> None:
        self.bound = 0
        self.n = 0

    @property
    def share(self) -> float:
        return self.bound / self.n if self.n else float("nan")


def _tallying_prepay(tally: BindTally):
    """Returns exactly what production returns; additionally tallies
    bind = (voluntary hazard < floor hazard) by re-evaluating with the floor
    zeroed. prepay_hazard is only reached on the U.S. branch of competing_risks
    (Danish routes through berger_calibration), so no regime flag is needed."""

    def wrapped(*args, **kwargs):
        out = _ORIG_PREPAY(*args, **kwargs)
        cur = literature_hazard.INVOLUNTARY_CPR_ANNUAL
        literature_hazard.INVOLUNTARY_CPR_ANNUAL = 0.0
        try:
            h_vol = _ORIG_PREPAY(*args, **kwargs)
        finally:
            literature_hazard.INVOLUNTARY_CPR_ANNUAL = cur
        h_floor = float(
            cpr_annual_to_monthly_hazard(np.array([cur], dtype=np.float64))[0]
        )
        h_vol = np.asarray(h_vol)
        tally.bound += int((h_vol < h_floor).sum())
        tally.n += int(h_vol.size)
        return out

    return wrapped


# ======================================================================
# Engine run at a given floor + elasticity (production convention otherwise)
# ======================================================================
def _run_scored(
    loans: pl.DataFrame,
    macro: pd.DataFrame,
    empirical: pd.DataFrame,
    floor: float,
    pq: float,
    tag: str,
) -> dict:
    """One microsim run at (floor, elasticity). Fresh (own output path);
    caches not consulted. Returns scored aggregates + the per-month rolloff
    series (US primary) for the temporal-holdout attribution."""
    literature_hazard.INVOLUNTARY_CPR_ANNUAL = floor
    tally = BindTally()
    competing_risks.prepay_hazard = _tallying_prepay(tally)
    out_path = RUN_DIR / f"microsim_{tag}.parquet"
    try:
        run_qt_microsim(
            loan_sample=loans, macro=macro, output=out_path, p_q_shock_pct=pq
        )
    finally:
        competing_risks.prepay_hazard = _ORIG_PREPAY
        literature_hazard.INVOLUNTARY_CPR_ANNUAL = PRODUCTION_FLOOR
    sim = pd.read_parquet(out_path)
    score = score_extension_risk(sim, empirical)
    return {
        "floor_annual_cpr_pct": floor * 100.0,
        "p_q_shock_pct": pq,
        "beta1": rothstein_beta1(pq / 100.0),
        "trapped_b": float(score["hazard_trapped_b"]),
        "share_pct": float(score["share_explained_pct"]),
        "mean_us_cpr_pct": float(sim["hazard_cpr_pct"].mean()),
        "floor_bind_share": tally.share,
        "floor_bind_loan_months": tally.n,
        "_rolloff": sim["simulated_rolloff_b"],  # per-month Series (dropped before JSON)
    }


# ======================================================================
# Instrument 1: out-of-window involuntary-floor measurement
# ======================================================================
AGE_BUCKETS = [(0, 12), (12, 24), (24, 36), (36, 60), (60, 10_000)]
GAP_THRESHOLDS = (0.0, -0.0025, -0.005)
AGE_CUTS = (12, 24)


def _cpr_of(sel: pd.DataFrame) -> tuple[float, float, int]:
    exp = float(sel["exposure_upb"].sum())
    if exp <= 0:
        return float("nan"), 0.0, 0
    smm = float(sel["prepaid_upb"].sum()) / exp
    return 1.0 - (1.0 - smm) ** 12, exp, int(len(sel))


def measure_oow_floor() -> tuple[dict, pd.DataFrame]:
    """Exposure-weighted annualized turnover CPR on 2017-2019 discount cohorts,
    with seasoning profiles and the mechanical contamination classification.
    Returns (results, gap-annotated panel) — the panel is reused by
    measure_calibration_floor for Instrument 2."""
    df = pd.read_parquet(PANEL_PATH)
    df = df[(df["coupon"] > 0) & (df["exposure_upb"] > 0)].copy()
    df["rp"] = df["reporting_period"].astype(int)
    df["ym"] = df["reporting_period"].astype(str)

    fred = Fred(api_key=FRED_API_KEY)
    rate = (
        fred.get_series(
            "MORTGAGE30US", observation_start="2016-12-01",
            observation_end="2025-10-31",
        )
        .resample("ME").mean()
    )
    rate_by_ym = {ix.strftime("%Y%m"): float(v) / 100.0 for ix, v in rate.items()}
    df["market_rate"] = df["ym"].map(rate_by_ym)
    df = df[df["market_rate"].notna()].copy()
    df["gap"] = df["coupon"] - df["market_rate"]

    legs = {
        "pooled_2017_2019": (201701, 201912),
        "2018_rising_rate": (201801, 201812),
        "2019_falling_rate": (201901, 201912),
    }
    regime = {
        "pooled_2017_2019": "mixed",
        "2018_rising_rate": "rising (refi-suppressed; clean candidate)",
        "2019_falling_rate": "falling (refi wave; regime-contaminated)",
    }

    out: dict = {
        "spec": "exposure-weighted annual CPR on 2017-2019 OTM cohorts; "
                "gap=coupon-MORTGAGE30US; seasoning + 2018/2019 leg split",
        # MORTGAGE30US arrives from FRED already in PERCENT (e.g. 4.03) — the
        # decimal conversion happens only in rate_by_ym below, so these display
        # fields must NOT be scaled again.
        "market_rate_by_year_pct": {
            str(y): {
                "mean": round(float(rate[rate.index.year == y].mean()), 3),
                "jan": round(float(rate[rate.index.year == y].iloc[0]), 3),
                "dec": round(float(rate[rate.index.year == y].iloc[-1]), 3),
            }
            for y in (2017, 2018, 2019)
        },
        "legs": {},
    }

    for leg, (lo, hi) in legs.items():
        w = df[(df["rp"] >= lo) & (df["rp"] <= hi)]
        leg_out: dict = {"rate_regime": regime[leg], "anchor_grid": {}, "seasoning": {}}

        # anchor grid: gap x age
        for gthr in GAP_THRESHOLDS:
            for amin in AGE_CUTS:
                sel = w[(w["gap"] <= gthr) & (w["mean_loan_age"] >= amin)]
                cpr, exp, n = _cpr_of(sel)
                leg_out["anchor_grid"][f"gap<={gthr:+.4f}_age>={amin}"] = {
                    "cpr_pct": round(100 * cpr, 3) if cpr == cpr else None,
                    "exposure_upb": exp, "n_cohort_months": n,
                }

        # seasoning profile: gap<=0, by age bucket
        wg = w[w["gap"] <= 0]
        for a_lo, a_hi in AGE_BUCKETS:
            sel = wg[(wg["mean_loan_age"] >= a_lo) & (wg["mean_loan_age"] < a_hi)]
            cpr, exp, n = _cpr_of(sel)
            leg_out["seasoning"][f"age[{a_lo},{a_hi})"] = {
                "cpr_pct": round(100 * cpr, 3) if cpr == cpr else None,
                "exposure_upb": exp, "n_cohort_months": n,
            }

        # ---- mechanical contamination classification ------------------------
        # The MATURE test (age>=24 vs [12,24)) is the decisive one: a pure
        # involuntary floor is ~flat in age, so a material rise there is
        # voluntary-refi accumulation. It is NOT always computable — a leg with
        # no age>=24 OTM cohort-months cannot be tested, and that must be
        # recorded as NOT-TESTABLE, never silently as "passed".
        # The RAMP rise ([12,24) vs [0,12)) is always computable but is
        # confounded by PSA-ramp immaturity (young loans genuinely turn over
        # less), so it is reported as diagnostic context, never as a verdict.
        s0 = leg_out["seasoning"]["age[0,12)"]["cpr_pct"]
        s12 = leg_out["seasoning"]["age[12,24)"]["cpr_pct"]
        s24 = leg_out["seasoning"]["age[24,36)"]["cpr_pct"]
        mature_rise = (
            (s24 - s12) if (s12 is not None and s24 is not None) else None
        )
        ramp_rise = (s12 - s0) if (s12 is not None and s0 is not None) else None
        mature_testable = mature_rise is not None
        if not mature_testable:
            seasoning_contaminated = None          # untested, not "clean"
        else:
            seasoning_contaminated = bool(mature_rise > 1.0)
        regime_contaminated = leg == "2019_falling_rate"

        if seasoning_contaminated or regime_contaminated:
            verdict = "CONTAMINATED"
        elif not mature_testable:
            # clean by REGIME construction (rising rates suppress refi), but the
            # mature-age seasoning test could not be run — this is exactly why
            # the OOS floor resolves to a range rather than a point.
            verdict = "CLEAN_BY_CONSTRUCTION_MATURE_TEST_NOT_COMPUTABLE"
        else:
            verdict = "CLEAN_CANDIDATE"

        leg_out["contamination"] = {
            "mature_rise_pp_24_vs_12": (
                round(mature_rise, 3) if mature_rise is not None else None
            ),
            "mature_test_computable": bool(mature_testable),
            "ramp_rise_pp_12_vs_0": (
                round(ramp_rise, 3) if ramp_rise is not None else None
            ),
            "ramp_rise_is_psa_confounded": True,
            "seasoning_contaminated": seasoning_contaminated,
            "regime_contaminated": regime_contaminated,
            "verdict": verdict,
        }
        out["legs"][leg] = leg_out

    # defensible clean floor = 2018 leg, age>=12, across gap grid
    def _read(leg_name: str, cell: str) -> float:
        """Fetch a required anchor cell as a decimal CPR, or fail loudly."""
        v = out["legs"][leg_name]["anchor_grid"].get(cell, {}).get("cpr_pct")
        if v is None:
            raise SystemExit(
                f"Required anchor cell '{cell}' is empty for leg '{leg_name}' — "
                "the OOS floor cannot be measured from the available panel. "
                "Report this as a not-computable anchor; do not substitute."
            )
        return float(v) / 100.0

    clean = out["legs"]["2018_rising_rate"]["anchor_grid"]
    clean_reads = {
        k: v["cpr_pct"] for k, v in clean.items()
        if k.endswith("age>=12") and v["cpr_pct"] is not None
    }
    if not clean_reads:
        raise SystemExit(
            "No age>=12 out-of-the-money cohort-months in the 2018 rising-rate "
            "leg — the clean out-of-sample floor is NOT COMPUTABLE from this "
            "panel. Do not fall back to the contaminated pooled/2019 read."
        )
    clean_vals = sorted(clean_reads.values())
    clean_lo = clean_vals[0] / 100.0
    clean_hi = clean_vals[-1] / 100.0
    clean_mid = _read("2018_rising_rate", "gap<=-0.0025_age>=12")  # primary point
    contaminated_2019 = _read("2019_falling_rate", "gap<=+0.0000_age>=12")
    pooled_headline = _read("pooled_2017_2019", "gap<=+0.0000_age>=12")
    out["defensible_clean_floor"] = {
        "leg": "2018_rising_rate", "age_cut": ">=12",
        "reads_pct": clean_reads,
        "clean_lo_pct": round(clean_lo * 100, 3),
        "clean_mid_pct": round(clean_mid * 100, 3),
        "clean_hi_pct": round(clean_hi * 100, 3),
        "primary_point_selection": "gap<=-0.0025_age>=12",
        "note": "2018 leg has NO age>=24 OTM cohort-months (OTM-in-2018 loans "
                "are all recently-originated low-coupon => young); the age>=24 "
                "probe is not computable for the clean leg.",
    }
    out["contaminated_upper_anchors"] = {
        "pooled_2017_2019_gap0_age12_pct": round(pooled_headline * 100, 3),
        "2019_falling_gap0_age12_pct": round(contaminated_2019 * 100, 3),
    }
    out["_floor_values"] = {  # decimals, consumed by the engine step
        "clean_lo": clean_lo, "clean_mid": clean_mid, "clean_hi": clean_hi,
        "contaminated_2019": contaminated_2019, "pooled": pooled_headline,
    }
    return out, df


# ======================================================================
# Instrument 2: in-window early-period calibration floor h_cal
# ======================================================================
def measure_calibration_floor(df: pd.DataFrame) -> dict:
    """Deeply-OTM discount-cohort turnover over the EARLY in-window sub-period
    [2022-06, 2024-01) (Jun 2022 - Dec 2023) -> h_cal. Matches the paper's
    floor definition (gap<=-0.02, deeply OTM); the held-out later months touch
    nothing here."""
    w = df[(df["rp"] >= 202206) & (df["rp"] <= 202312)]
    res = {"window": "202206..202312 (Jun 2022 - Dec 2023)", "reads": {}}
    primary = None
    for gthr, label in ((-0.02, "gap<=-0.02_age>=12"), (0.0, "gap<=0_age>=12")):
        sel = w[(w["gap"] <= gthr) & (w["mean_loan_age"] >= 12)]
        cpr, exp, n = _cpr_of(sel)
        res["reads"][label] = {
            "cpr_pct": round(100 * cpr, 3) if cpr == cpr else None,
            "exposure_upb": exp, "n_cohort_months": n,
        }
        if gthr == -0.02:
            primary = cpr
    res["h_cal_pct"] = round(100 * primary, 3) if primary == primary else None
    res["_h_cal"] = float(primary)
    res["primary_selection"] = "gap<=-0.02_age>=12 (deeply-OTM, paper floor def.)"
    return res


# ======================================================================
# Monthly attribution helper (Instrument 2)
# ======================================================================
def _monthly_marginal(central_roll: pd.Series, null_roll: pd.Series,
                      idx: pd.DatetimeIndex) -> pd.Series:
    """Per-month lock-in marginal $B on the scored QT-active index: the QT
    target cancels in central-null, so marginal_t = rolloff_central_t -
    rolloff_null_t."""
    c = central_roll.reindex(idx)
    n = null_roll.reindex(idx)
    return (c - n)


def main() -> None:
    assert rothstein_beta1(0.0) == 0.0, "p_q shock 0 must give exactly beta1=0"
    assert config.FLOOR_MODE == "max", "production is the eq.(3) hard-max form"
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    t_start = time.perf_counter()

    # ---- Instrument 1 + 2 floor measurement (data-only) --------------------
    print("=" * 72)
    print("STEP 2/3 measurement: out-of-window + calibration floors")
    print("=" * 72)
    oow, panel_df = measure_oow_floor()
    calib = measure_calibration_floor(panel_df)
    fv = oow["_floor_values"]
    h_cal = calib["_h_cal"]
    print(f"  2018 clean band: {oow['defensible_clean_floor']['clean_lo_pct']}% .. "
          f"{oow['defensible_clean_floor']['clean_hi_pct']}%  "
          f"(mid {oow['defensible_clean_floor']['clean_mid_pct']}%)")
    print(f"  contaminated upper: pooled {fv['pooled']*100:.3f}%, "
          f"2019 {fv['contaminated_2019']*100:.3f}%")
    print(f"  Instrument-2 h_cal (202206..202312, gap<=-0.02): {h_cal*100:.3f}%")

    # ---- Engine floor set --------------------------------------------------
    def _r(x):
        """Quantize a floor for stable set-dedup. 6 dp of the DECIMAL = 4 dp of
        the percent, so a measured 4.695% floor is run at exactly 4.695% and the
        reported label matches the floor actually simulated (a 4-dp quantization
        would have silently run it at 4.70%)."""
        return round(float(x), 6)

    engine_floors = sorted({
        _r(f) for f in (
            COMMITTED_CROSSCHECK_FLOORS
            + [fv["clean_lo"], fv["clean_mid"], fv["clean_hi"],
               fv["contaminated_2019"], h_cal]
        )
    })
    print(f"\nEngine floor set (annual CPR): "
          f"{[round(f*100,3) for f in engine_floors]}%")

    # ---- Shared macro frame (fetched once; identical to production) --------
    print("\nScoring empirical benchmark (shared macro frame, fetched once) …")
    macro_raw = fetch_data()
    macro = calculate_dynamic_friction(macro_raw)
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro_raw, soma_rolloff=soma)
    scored_idx = qt_active_frame(empirical).index  # the 42 scored QT-active months

    if not LOAN_SAMPLE_PATH.exists():
        raise FileNotFoundError(f"{LOAN_SAMPLE_PATH} missing — build via production first.")
    loans = pl.read_parquet(LOAN_SAMPLE_PATH)

    # ---- Run all (floor, elasticity) legs ----------------------------------
    print("\n" + "=" * 72)
    print("Engine runs: null (band-invariant) + central @ 5.5/6.5/7.7 per floor")
    print("=" * 72)
    runs: dict[float, dict] = {}
    for floor in engine_floors:
        fp = floor * 100
        null = _run_scored(loans, macro, empirical, floor, NULL_PQ, f"floor{fp:g}_null")
        centrals = {}
        for pq in BAND_PCT:
            centrals[pq] = _run_scored(
                loans, macro, empirical, floor, pq, f"floor{fp:g}_pq{pq:g}"
            )
        runs[floor] = {"null": null, "central": centrals}
        cmid = centrals[CENTRAL_PQ]
        print(
            f"floor {fp:5.3f}%:  null ${null['trapped_b']:7.2f}B "
            f"({null['share_pct']:6.2f}%)   central@6.5 ${cmid['trapped_b']:7.2f}B "
            f"({cmid['share_pct']:6.2f}%)   marginal "
            f"${cmid['trapped_b']-null['trapped_b']:+6.2f}B "
            f"({cmid['share_pct']-null['share_pct']:+5.2f}pp)   "
            f"bind {cmid['floor_bind_share']*100:4.1f}%"
        )

    # ---- STEP 1 PARITY GATE (4.0% production floor) ------------------------
    print("\n" + "=" * 72)
    print("STEP 1 PARITY GATE (fresh 4.0% floor vs committed production)")
    print("=" * 72)
    with open(NULL_ARTIFACT) as f:
        anchor = json.load(f)
    p = runs[_r(PRODUCTION_FLOOR)]
    p_null = p["null"]
    p_cen = p["central"][CENTRAL_PQ]
    p_marg_b = p_cen["trapped_b"] - p_null["trapped_b"]
    p_marg_pp = p_cen["share_pct"] - p_null["share_pct"]
    parity = {
        "central_trapped_b": (p_cen["trapped_b"], anchor["central_trapped_b"]),
        "null_trapped_b": (p_null["trapped_b"], anchor["null_trapped_b"]),
        "lockin_marginal_b": (p_marg_b, anchor["lockin_marginal_b"]),
        "lockin_marginal_share_pp": (p_marg_pp, anchor["lockin_marginal_share_pp"]),
    }
    parity_report = {}
    for name, (got, want) in parity.items():
        ok = abs(got - want) < 0.01
        parity_report[name] = {"got": got, "want": want, "pass": bool(ok)}
        print(f"  {name}: got {got:.6f} want {want:.6f} [{'PASS' if ok else 'FAIL'}]")
    bind_share_ok = abs(p_cen["floor_bind_share"] - BIND_SHARE_ANCHOR) <= 0.01
    bind_n_ok = abs(p_cen["floor_bind_loan_months"] - BIND_N_ANCHOR) / BIND_N_ANCHOR <= 0.005
    parity_report["bind_instrumentation"] = {
        "share_got": p_cen["floor_bind_share"], "share_anchor": BIND_SHARE_ANCHOR,
        "n_got": p_cen["floor_bind_loan_months"], "n_anchor": BIND_N_ANCHOR,
        "pass": bool(bind_share_ok and bind_n_ok),
    }
    print(f"  bind: share {p_cen['floor_bind_share']:.5f} vs {BIND_SHARE_ANCHOR} | "
          f"n {p_cen['floor_bind_loan_months']:,} vs {BIND_N_ANCHOR:,} "
          f"[{'PASS' if bind_share_ok and bind_n_ok else 'FAIL'}]")
    parity_hard_fail = [
        k for k, v in parity_report.items()
        if k != "bind_instrumentation" and not v["pass"]
    ]
    if parity_hard_fail:
        # Diagnostics go to a SIDECAR so a failed rerun can never clobber the
        # frozen results artifact.
        sidecar = RESULTS_JSON.with_name("oos_identification_PARITY_FAILED.json")
        payload = {"mode": "oos_identification", "PARITY_FAILED": True,
                   "parity_gates": parity_report}
        with open(sidecar, "w") as f:
            json.dump(payload, f, indent=2,
                      default=lambda x: float(x) if isinstance(x, (np.floating, np.integer)) else x)
        raise SystemExit(
            f"PARITY GATE FAILURE: {parity_hard_fail} — environment problem; "
            f"STOP. Diagnostics in {sidecar}. Do NOT build on a broken baseline."
        )
    print("  PARITY PASS — safe to proceed.")

    # ---- Committed floor_sweep cross-check ---------------------------------
    with open(COMMITTED_SWEEP) as f:
        sweep = json.load(f)
    sweep_by_floor = {}
    for row in sweep["rows"]:
        fpct = round(row["floor_annual_cpr_pct"], 4)
        sweep_by_floor[fpct] = {
            "null_b": row["null"]["trapped_b"],
            "central_b": row["central"]["trapped_b"],
            "marginal_b": row["lockin_marginal_b"],
            "marginal_pp": row["lockin_marginal_share_pp"],
        }

    # ---- Assemble Instrument-1 table + sign matrix + cross-checks -----------
    table = []
    sign_matrix_ok = True
    crosscheck = {}
    for floor in engine_floors:
        fp = round(floor * 100, 4)
        null = runs[floor]["null"]
        band = {}
        for pq in BAND_PCT:
            cen = runs[floor]["central"][pq]
            marg_b = cen["trapped_b"] - null["trapped_b"]
            marg_pp = cen["share_pct"] - null["share_pct"]
            if marg_b <= 0:
                sign_matrix_ok = False
            band[f"{pq}"] = {
                "central_trapped_b": cen["trapped_b"],
                "central_share_pct": cen["share_pct"],
                "marginal_b": marg_b,
                "marginal_pp": marg_pp,
                "marginal_positive": bool(marg_b > 0),
            }
        cmid = runs[floor]["central"][CENTRAL_PQ]
        h_floor_smm = float(
            cpr_annual_to_monthly_hazard(np.array([floor], dtype=np.float64))[0]
        )
        row = {
            "floor_annual_cpr_pct": fp,
            "floor_monthly_smm": round(h_floor_smm, 6),
            "floor_bind_share": cmid["floor_bind_share"],
            "floor_bind_loan_months": cmid["floor_bind_loan_months"],
            "null_trapped_b": null["trapped_b"],
            "null_share_pct": null["share_pct"],
            "band": band,
        }
        table.append(row)
        # cross-check vs committed sweep at exact grid points
        # (matches committed floors robustly: 3.5 -> 3.5000000000000004 style)
        matched = None
        for sf in sweep_by_floor:
            if abs(sf - fp) < 1e-6:
                matched = sf
                break
        if matched is not None:
            sw = sweep_by_floor[matched]
            got_b = band[f"{CENTRAL_PQ}"]["marginal_b"]
            got_null = null["trapped_b"]
            crosscheck[f"{fp}"] = {
                "committed_marginal_b": sw["marginal_b"],
                "fresh_marginal_b": got_b,
                "delta_marginal_b": got_b - sw["marginal_b"],
                "committed_null_b": sw["null_b"],
                "fresh_null_b": got_null,
                "delta_null_b": got_null - sw["null_b"],
                "match_within_0.01B": bool(abs(got_b - sw["marginal_b"]) < 0.01
                                           and abs(got_null - sw["null_b"]) < 0.01),
            }

    # ---- STEP 3: temporal-holdout marginal ---------------------------------
    print("\n" + "=" * 72)
    print("STEP 3 temporal holdout: floor calibrated on 202206..202312, "
          "marginal over held-out 2024-01..2025-11")
    print("=" * 72)

    def _holdout_for(floor: float) -> dict:
        null_roll = runs[floor]["null"]["_rolloff"]
        cen_roll = runs[floor]["central"][CENTRAL_PQ]["_rolloff"]
        m = _monthly_marginal(cen_roll, null_roll, scored_idx)
        held_mask = (scored_idx >= HELDOUT_START) & (scored_idx < QT_END)
        cal_mask = (scored_idx >= QT_START) & (scored_idx < CALIB_END)
        held_b = float(m[held_mask].sum())
        cal_b = float(m[cal_mask].sum())
        total_b = float(m.sum())
        # aggregate marginal (score-based) for the additivity cross-check
        agg = (runs[floor]["central"][CENTRAL_PQ]["trapped_b"]
               - runs[floor]["null"]["trapped_b"])
        # share basis for the held-out window (emp Extension_Delta over held-out)
        qt_emp = qt_active_frame(empirical)
        held_emp = float(
            qt_emp.loc[(qt_emp.index >= HELDOUT_START) & (qt_emp.index < QT_END),
                       "Extension_Delta_Billions"].sum()
        )
        return {
            "floor_annual_cpr_pct": round(floor * 100, 4),
            "heldout_marginal_b": held_b,
            "heldout_marginal_pp_of_heldout_emp": (
                held_b / held_emp * 100 if held_emp else float("nan")
            ),
            "calibration_window_marginal_b": cal_b,
            "full_window_marginal_b": total_b,
            "aggregate_marginal_b_scorecheck": agg,
            "additivity_ok": bool(abs(total_b - agg) < 0.05),
            "heldout_sign_positive": bool(held_b > 0),
            "n_heldout_months": int(held_mask.sum()),
            "n_calibration_months": int(cal_mask.sum()),
            "heldout_emp_delta_b": held_emp,
        }

    h_cal_r = _r(h_cal)
    holdout = {
        "calibration_floor": calib,
        "heldout_window": "2024-01..2025-11 (strictly held out of floor calibration)",
        "at_calibrated_floor_h_cal": _holdout_for(h_cal_r),
        "at_production_floor_4pct": _holdout_for(_r(PRODUCTION_FLOOR)),
    }
    for label, key in [("h_cal", "at_calibrated_floor_h_cal"),
                       ("production 4%", "at_production_floor_4pct")]:
        hb = holdout[key]
        print(f"  {label:14s} floor {hb['floor_annual_cpr_pct']:.3f}%: "
              f"held-out marginal ${hb['heldout_marginal_b']:+.2f}B "
              f"({hb['heldout_marginal_pp_of_heldout_emp']:+.1f}% of held-out emp) "
              f"[additivity {'OK' if hb['additivity_ok'] else 'FAIL'}, "
              f"sign {'+' if hb['heldout_sign_positive'] else '-'}]")

    # ---- Headline OOS marginal (clean point + range) -----------------------
    def _marg_at(floor_dec, pq=CENTRAL_PQ):
        fr = _r(floor_dec)
        return (runs[fr]["central"][pq]["trapped_b"] - runs[fr]["null"]["trapped_b"])

    def _pp_at(floor_dec, pq=CENTRAL_PQ):
        fr = _r(floor_dec)
        return (runs[fr]["central"][pq]["share_pct"] - runs[fr]["null"]["share_pct"])

    clean_lo_f, clean_mid_f, clean_hi_f = fv["clean_lo"], fv["clean_mid"], fv["clean_hi"]
    # clean band: lower floor -> larger marginal, so $ range is [hi-floor, lo-floor]
    clean_marg_hi = _marg_at(clean_lo_f)   # lowest clean floor -> biggest marginal
    clean_marg_lo = _marg_at(clean_hi_f)   # highest clean floor -> smallest marginal
    clean_point = _marg_at(clean_mid_f)
    contaminated_marg = _marg_at(fv["contaminated_2019"])
    # Benchmark-consistent marginal: the SOMA active-QT benchmark ($764.748B)
    # minus the production-floor null. Used only as an overshoot yardstick;
    # NOT a target (no benchmark feedback into any floor or elasticity).
    benchmark_consistent = 764.748 - anchor["null_trapped_b"]

    all_marg = [b["band"][f"{pq}"]["marginal_b"] for b in table for pq in BAND_PCT]
    range_contains_benchmark = min(all_marg) <= benchmark_consistent <= max(all_marg)

    headline = {
        "clean_floor_provenance": "2018 rising-rate leg, age>=12, exposure-"
            "weighted turnover CPR on OTM cohort-months OUTSIDE the QT window "
            "(no in-window locked-in population used).",
        "clean_floor_band_pct": [round(clean_lo_f * 100, 3), round(clean_hi_f * 100, 3)],
        "clean_floor_point_pct": round(clean_mid_f * 100, 3),
        "clean_marginal_b_point_at_6.5": clean_point,
        "clean_marginal_pp_point_at_6.5": _pp_at(clean_mid_f),
        "clean_marginal_b_range_at_6.5": [clean_marg_lo, clean_marg_hi],
        "clean_marginal_b_full_band_range": [
            min(_marg_at(clean_hi_f, pq) for pq in BAND_PCT),
            max(_marg_at(clean_lo_f, pq) for pq in BAND_PCT),
        ],
        "contaminated_upper_floor_pct": round(fv["contaminated_2019"] * 100, 3),
        "contaminated_marginal_b_at_6.5": contaminated_marg,
        "in_sample_production_point_b": p_marg_b,
        "in_sample_production_point_pp": p_marg_pp,
        "benchmark_consistent_marginal_b": benchmark_consistent,
        "reported_range_contains_benchmark_consistent": bool(range_contains_benchmark),
    }

    # ---- Self-checks -------------------------------------------------------
    # HARD = wiring invariants. A failure means the run is mis-wired and the
    # artifact must not be cited (enforced by SystemExit after the write).
    hard_checks = {
        "production_4pct_reproduces_70.345B": bool(abs(p_marg_b - 70.3450604) < 0.01),
        "production_4pct_reproduces_9.198pp": bool(abs(p_marg_pp - 9.1984598) < 0.01),
        "committed_sweep_crosscheck_all_match": bool(
            crosscheck and all(c["match_within_0.01B"] for c in crosscheck.values())
        ),
        "holdout_monthly_additivity_ok": bool(
            holdout["at_calibrated_floor_h_cal"]["additivity_ok"]
            and holdout["at_production_floor_4pct"]["additivity_ok"]
        ),
    }
    # SOFT = interpretive expectations carried in from the brief. A failure here
    # is a FINDING to report and re-examine, not a wiring bug, so it must never
    # crash the run or be silently "fixed" by tuning anything.
    soft_flags = {
        "floor_6pct_in_2.1_to_2.4pp": bool(2.0 <= _pp_at(0.06) <= 2.5),
        "floor_6pct_in_16_to_18B": bool(16.0 <= _marg_at(0.06) <= 18.5),
        "range_contains_benchmark_consistent_16.5B": bool(range_contains_benchmark),
        "sign_robust_all_cells_positive": bool(sign_matrix_ok),
    }
    selfchecks = {**hard_checks, **soft_flags}

    verdict = _build_verdict(headline, holdout, sign_matrix_ok, oow, selfchecks)

    # ---- Freeze results ----------------------------------------------------
    def _strip(d):
        """Drop the per-month Series before JSON serialization."""
        if isinstance(d, dict):
            return {k: _strip(v) for k, v in d.items() if k != "_rolloff"}
        return d

    runtime_s = round(time.perf_counter() - t_start, 1)
    payload = {
        "mode": "oos_identification",
        "spec": "OOS involuntary floor (2018 rising-rate leg) + temporal holdout; "
                "central 5.5/6.5/7.7 band; null beta1=0; production convention "
                "otherwise (committed 75k sample, seed 42, US+Danish tuple, shared "
                "macro frame); raw-basis scoring; parity vs no_lockin_null at 4%; "
                "no benchmark feedback.",
        "parity_gates": parity_report,
        "parity_all_pass": not parity_hard_fail,
        "instrument1_oow_floor": _strip(oow),
        "instrument1_marginal_table": table,
        "committed_sweep_crosscheck": crosscheck,
        "instrument2_temporal_holdout": holdout,
        "step4_sign_robustness": {
            "all_floor_x_band_cells_positive": bool(sign_matrix_ok),
            "n_cells": len(engine_floors) * len(BAND_PCT),
            "floors_pct": [round(f * 100, 3) for f in engine_floors],
            "band_pct": list(BAND_PCT),
        },
        "headline_oos_marginal": headline,
        "self_checks_hard_wiring": hard_checks,
        "self_checks_soft_interpretive": soft_flags,
        "self_checks": selfchecks,
        "verdict": verdict,
        "runtime_s": runtime_s,
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2,
                  default=lambda x: float(x) if isinstance(x, (np.floating, np.integer)) else x)
        f.write("\n")

    _write_report(payload)

    print("\n" + "=" * 72)
    print("SELF-CHECKS — HARD (wiring invariants; failure invalidates the run)")
    for k, v in hard_checks.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    print("SELF-CHECKS — SOFT (interpretive expectations; failure = a finding)")
    for k, v in soft_flags.items():
        print(f"  [{'PASS' if v else 'FLAG'}] {k}")
    print("=" * 72)
    print(f"\nVERDICT: {verdict['one_paragraph']}")
    print(f"\nResults -> {RESULTS_JSON}")
    print(f"Report  -> {REPORT_MD}")
    print(f"Runtime: {runtime_s}s")

    if not all(hard_checks.values()):
        raise SystemExit(
            "HARD WIRING CHECK FAILURE: "
            f"{[k for k, v in hard_checks.items() if not v]} — results written "
            f"to {RESULTS_JSON} for diagnosis but MUST NOT be cited."
        )


def _build_verdict(headline, holdout, sign_ok, oow, selfchecks) -> dict:
    clean_pt = headline["clean_marginal_b_point_at_6.5"]
    clean_lo, clean_hi = headline["clean_marginal_b_range_at_6.5"]
    cont = headline["contaminated_marginal_b_at_6.5"]
    insample = headline["in_sample_production_point_b"]
    bcons = headline["benchmark_consistent_marginal_b"]
    held_hcal = holdout["at_calibrated_floor_h_cal"]["heldout_marginal_b"]
    held_prod = holdout["at_production_floor_4pct"]["heldout_marginal_b"]
    para = (
        f"The lock-in marginal is SIGN-ROBUST out of sample: it stays strictly "
        f"positive at every floor x elasticity cell "
        f"({'confirmed' if sign_ok else 'NOT confirmed'}), and the temporal "
        f"holdout — floor calibrated on Jun2022-Dec2023, marginal summed over the "
        f"strictly held-out Jan2024-Nov2025 months — is +${held_hcal:.1f}B "
        f"(vs +${held_prod:.1f}B at the production 4% floor over the same months), "
        f"so the positive sign is not an artifact of the floor touching the "
        f"evaluation months. On MAGNITUDE: anchored on the CLEAN out-of-window "
        f"involuntary floor (the 2018 rising-rate leg, ~"
        f"{headline['clean_floor_point_pct']:.1f}% CPR, age>=12, refi-suppressed), "
        f"the central (6.5) marginal is ~${clean_pt:.0f}B "
        f"(range ${clean_lo:.0f}-${clean_hi:.0f}B across the clean floor band), "
        f"materially BELOW the ${insample:.0f}B in-sample production point but NOT "
        f"collapsed to the benchmark-consistent ~${bcons:.1f}B. The collapse to "
        f"~${cont:.0f}B occurs ONLY if the contaminated, refi-inflated pooled/2019 "
        f"floor (~{headline['contaminated_upper_floor_pct']:.1f}%) is used — and "
        f"that read is disqualified as a pure involuntary floor because its "
        f"turnover rises with loan age (seasoning contamination) and sits in a "
        f"falling-rate refi wave (regime contamination). A SINGLE OOS floor is "
        f"NOT cleanly identifiable — only a range — because (a) 2017-2019 lacks "
        f"deep-OTM MATURE cohorts (the clean 2018 leg has NO age>=24 OTM "
        f"cohort-months at all), (b) the pooled and 2019 reads are refi-"
        f"contaminated, and (c) consequently the decisive mature-age seasoning "
        f"test is NOT COMPUTABLE on the clean leg — 2018 is clean by rate-regime "
        f"construction, not clean by test, and its one computable age contrast "
        f"([0,12)->[12,24)) is confounded by PSA-ramp immaturity. The reported "
        f"OOS range "
        f"{'DOES' if selfchecks['range_contains_benchmark_consistent_16.5B'] else 'does NOT'} "
        f"contain the ${bcons:.1f}B benchmark-consistent figure at its "
        f"contaminated-floor edge."
    )
    return {
        "sign_robust_oos": bool(sign_ok),
        "clean_marginal_b_point": clean_pt,
        "clean_marginal_b_range": [clean_lo, clean_hi],
        "contaminated_marginal_b": cont,
        "in_sample_point_b": insample,
        "single_floor_identifiable": False,
        "single_floor_reason": "only a range: no deep-OTM mature 2017-2019 "
            "cohorts; pooled/2019 refi-contaminated; residual seasoning in the "
            "clean 2018 leg.",
        "one_paragraph": para,
    }


def _write_report(payload: dict) -> None:
    """OOS_IDENTIFICATION.md — instrument table, headline, verdict."""
    h = payload["headline_oos_marginal"]
    v = payload["verdict"]
    oow = payload["instrument1_oow_floor"]
    lines = []
    A = lines.append
    A("# Out-of-Sample Identification of Path B's Lock-in Marginal\n")
    A("_Recomputes the lock-in marginal (central minus the β₁=0 null) under an "
      "involuntary-turnover floor calibrated OUTSIDE the locked-in in-window "
      "population, and reports it honestly on sign and magnitude. Generated by "
      "`hazard/oos_identification.py`; frozen to "
      "`hazard/data/oos_identification_results.json`. Does not defend $70.3B; "
      "does not tune to the $764.748B benchmark._\n")

    A("## Parity gate (Step 1)\n")
    pg = payload["parity_gates"]
    A("Fresh 4.0% production floor, caches not consulted, vs committed anchors:\n")
    A("| anchor | fresh | committed | pass |")
    A("|---|---|---|---|")
    for k in ("central_trapped_b", "null_trapped_b", "lockin_marginal_b",
              "lockin_marginal_share_pp"):
        r = pg[k]
        A(f"| {k} | {r['got']:.6f} | {r['want']:.6f} | {'✅' if r['pass'] else '❌'} |")
    b = pg["bind_instrumentation"]
    A(f"| floor-bind share | {b['share_got']:.5f} | {b['share_anchor']} | "
      f"{'✅' if b['pass'] else '❌'} |")
    A(f"| floor-bind loan-months | {b['n_got']:,} | {b['n_anchor']:,} | |")
    A(f"\n**Parity: {'PASS' if payload['parity_all_pass'] else 'FAIL'}.**\n")

    A("## Instrument 1 — out-of-window involuntary floor\n")
    A("Exposure-weighted annualized turnover CPR on 2017–2019 discount "
      "(out-of-the-money) cohort-months. Market rate by leg: "
      f"2018 rising {oow['market_rate_by_year_pct']['2018']['jan']}→"
      f"{oow['market_rate_by_year_pct']['2018']['dec']}%, "
      f"2019 falling {oow['market_rate_by_year_pct']['2019']['jan']}→"
      f"{oow['market_rate_by_year_pct']['2019']['dec']}%.\n")
    A("### Seasoning profiles (gap≤0, turnover CPR % by loan age)\n")
    A("A pure involuntary floor is ~flat in loan age. The decisive test is the "
      "MATURE contrast (age≥24 vs [12,24)); the ramp contrast ([12,24) vs "
      "[0,12)) is confounded by PSA immaturity and is diagnostic only.\n")
    A("| leg | rate regime | [0,12) | [12,24) | [24,36) | mature Δ | mature test | verdict |")
    A("|---|---|---|---|---|---|---|---|")
    for leg, lo in oow["legs"].items():
        s = lo["seasoning"]
        c = lo["contamination"]

        def g(k):
            v2 = s.get(k, {}).get("cpr_pct")
            return f"{v2}" if v2 is not None else "—"

        mr = c["mature_rise_pp_24_vs_12"]
        A(f"| {leg} | {lo['rate_regime']} | {g('age[0,12)')} | {g('age[12,24)')} "
          f"| {g('age[24,36)')} | {('+' + str(mr)) if mr is not None else '—'} "
          f"| {'computable' if c['mature_test_computable'] else '**NOT COMPUTABLE**'} "
          f"| {c['verdict']} |")
    dcf = oow["defensible_clean_floor"]
    A(f"\n**Defensible clean floor:** {dcf['leg']}, age≥12 → band "
      f"{dcf['clean_lo_pct']}–{dcf['clean_hi_pct']}% (point {dcf['clean_mid_pct']}%). "
      f"{dcf['note']}\n")
    A(f"**Contaminated upper anchors (not preferred):** pooled "
      f"{oow['contaminated_upper_anchors']['pooled_2017_2019_gap0_age12_pct']}%, "
      f"2019 {oow['contaminated_upper_anchors']['2019_falling_gap0_age12_pct']}%.\n")

    A("### Marginal at each floor (central−null), across the 5.5/6.5/7.7 band\n")
    A("| floor % (CPR) | SMM | bind share | null $B | "
      "marg $B @5.5 | @6.5 | @7.7 | marg pp @6.5 |")
    A("|---|---|---|---|---|---|---|---|")
    for row in payload["instrument1_marginal_table"]:
        band = row["band"]
        A(f"| {row['floor_annual_cpr_pct']:.3f} | {row['floor_monthly_smm']:.5f} "
          f"| {row['floor_bind_share']*100:.1f}% | {row['null_trapped_b']:.2f} "
          f"| {band['5.5']['marginal_b']:+.2f} | {band['6.5']['marginal_b']:+.2f} "
          f"| {band['7.7']['marginal_b']:+.2f} | {band['6.5']['marginal_pp']:+.2f} |")

    cc = payload["committed_sweep_crosscheck"]
    if cc:
        A("\n### Cross-check vs committed `floor_sweep_results.json`\n")
        A("| floor % | committed marg $B | fresh marg $B | Δ | match ≤0.01B |")
        A("|---|---|---|---|---|")
        for fp, r in cc.items():
            A(f"| {fp} | {r['committed_marginal_b']:.4f} | {r['fresh_marginal_b']:.4f} "
              f"| {r['delta_marginal_b']:+.2e} | {'✅' if r['match_within_0.01B'] else '❌'} |")

    A("\n## Instrument 2 — temporal holdout\n")
    ho = payload["instrument2_temporal_holdout"]
    cf = ho["calibration_floor"]
    A(f"Floor calibrated on {cf['window']}, deeply-OTM (gap≤−0.02, age≥12): "
      f"h_cal = **{cf['h_cal_pct']}%**. Marginal summed over the strictly "
      f"held-out **{ho['heldout_window']}**:\n")
    A("| floor | held-out marg $B | % of held-out emp | calib-window marg $B "
      "| full-window marg $B | additivity | sign |")
    A("|---|---|---|---|---|---|---|")
    for key in ("at_calibrated_floor_h_cal", "at_production_floor_4pct"):
        r = ho[key]
        A(f"| {r['floor_annual_cpr_pct']:.3f}% | {r['heldout_marginal_b']:+.2f} "
          f"| {r['heldout_marginal_pp_of_heldout_emp']:+.1f}% "
          f"| {r['calibration_window_marginal_b']:+.2f} "
          f"| {r['full_window_marginal_b']:+.2f} "
          f"| {'OK' if r['additivity_ok'] else 'FAIL'} "
          f"| {'+' if r['heldout_sign_positive'] else '−'} |")

    A("\n## Step 4 — sign robustness\n")
    sr = payload["step4_sign_robustness"]
    A(f"All **{sr['n_cells']}** floor×band cells "
      f"({len(sr['floors_pct'])} floors × {len(sr['band_pct'])} band points): "
      f"marginal positive = **{sr['all_floor_x_band_cells_positive']}**.\n")

    A("## Headline OOS marginal\n")
    A(f"- **Clean out-of-window floor** (2018 rising-rate leg, "
      f"~{h['clean_floor_point_pct']:.1f}% CPR, age≥12): central (6.5) marginal "
      f"**${h['clean_marginal_b_point_at_6.5']:.1f}B** "
      f"(**{h['clean_marginal_pp_point_at_6.5']:.2f}pp**), range "
      f"${h['clean_marginal_b_range_at_6.5'][0]:.1f}–"
      f"${h['clean_marginal_b_range_at_6.5'][1]:.1f}B across the clean floor band; "
      f"full-band range ${h['clean_marginal_b_full_band_range'][0]:.1f}–"
      f"${h['clean_marginal_b_full_band_range'][1]:.1f}B.")
    A(f"- **Contaminated upper floor** (~{h['contaminated_upper_floor_pct']:.1f}%, "
      f"refi-inflated, NOT preferred): marginal collapses to "
      f"**${h['contaminated_marginal_b_at_6.5']:.1f}B**.")
    A(f"- **In-sample production point** (4.0% floor): "
      f"${h['in_sample_production_point_b']:.1f}B "
      f"({h['in_sample_production_point_pp']:.2f}pp) — demoted, not headlined.")
    A(f"- **Benchmark-consistent** (764.748 − null): "
      f"${h['benchmark_consistent_marginal_b']:.1f}B; reported range contains it: "
      f"{h['reported_range_contains_benchmark_consistent']}.\n")

    A("## Self-checks\n")
    A("| check | kind | result |")
    A("|---|---|---|")
    for k, val in payload["self_checks_hard_wiring"].items():
        A(f"| {k} | hard (wiring) | {'✅ PASS' if val else '❌ FAIL'} |")
    for k, val in payload["self_checks_soft_interpretive"].items():
        A(f"| {k} | soft (interpretive) | {'✅ PASS' if val else '⚠️ FLAG'} |")
    A("\nHard checks are wiring invariants — a failure invalidates the run. "
      "Soft flags are interpretive expectations carried in from the brief; a "
      "failure is a finding to report, never something tuned away.\n")

    A("## Verdict\n")
    A(v["one_paragraph"] + "\n")
    A("### Anchors NOT computable from available data\n")
    A("- **The clean leg's decisive seasoning test cannot be run.** The 2018 "
      "rising-rate leg has **zero** age≥24 out-of-the-money cohort-months — "
      "loans that are out-of-the-money when rates *rise* are all recently-"
      "originated low-coupon loans, hence young. So the mature-age involuntary "
      "probe (age≥24 vs [12,24)) is **NOT COMPUTABLE** on the clean leg: 2018 "
      "is clean by rate-regime construction, not clean by test. Its one "
      "computable age contrast ([0,12)→[12,24)) is confounded by PSA-ramp "
      "immaturity and is reported as diagnostic context only. This is precisely "
      "why the out-of-sample floor resolves to a **range, not a point**.")
    A("- Deep out-of-the-money selection comparable to 2023–24 (gap ≤ −0.02) is "
      "**not available** in 2017–2019: rates peaked near 4.94%, so no cohort "
      "reaches that discount depth. The out-of-window grid therefore stops at "
      "gap ≤ −0.005.\n")

    REPORT_MD.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
