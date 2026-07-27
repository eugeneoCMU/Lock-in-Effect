#!/usr/bin/env python3
"""
B2 seasonal involuntary-turnover floor — wiring harness and parity controls
(pre-committed; spec fixed in this header before any run executed).

Referee residual (B2): eq. (2)/(3)'s involuntary-turnover floor is a single
constant (4% annual CPR), so involuntary turnover is treated as ASEASONAL.
floor_cyclical.py bracketed the floor's co-movement with the RATE cycle;
floor_sweep.py bracketed its LEVEL. Neither touches its CALENDAR-MONTH
profile, which is the only floor variation that can move the SIMULATED
MONTHLY TIMING (Theil U2 / lag-0 detrended correlation) without moving the
window level at all.

WHAT THIS MODULE IS. Part 1 of B2: the harness plus its FLAT-FLOOR PARITY
CONTROLS. A time-varying floor driver is wired at the microsim_engine
qt_index loop and then set FLAT. If a flat 12-vector does not reproduce the
committed constant-floor anchors bit-for-bit, the wiring is wrong and every
seasonal number downstream is meaningless.

PART 2 (this revision) runs the two SEASONAL legs, captures the full
simulated monthly CPR path over the 42-month QT window for every leg, and
scores each against the FROZEN B3 timing criterion. The flat controls are
RE-RUN IN THE SAME SESSION as the seasonal legs, so the parity gates are
evidence about the very process that produced the seasonal numbers, not
about a previous one.

FROZEN B3 TIMING CRITERION (pre-committed; not editable, not searchable):
  PASS requires BOTH  Theil U2(first diffs) < 1  AND  a POSITIVE lag-0
  correlation between the linearly detrended simulated and empirical CPR
  paths. Formulas are the committed ones: figures/make_theil_data.py:231
  theil_u1, :237 theil_u2_diffs, :261 detrend. The scored object is the
  CENTRAL (p_q = 6.5) run, which is the production Path B object those
  committed baselines were computed on (path_b: u1_levels 0.2653,
  u2_diffs 1.0029, u1_detrended 0.9797, n = 42, n_diffs = 41).
  If the seasonal legs fail it => CONCEDE: monthly timing is not
  identifiable from the floor's calendar profile; every claim is restricted
  to LEVELS and the abstract says so. An adverse result is a reportable
  outcome and is NOT to be tuned away. No lag-kernel hunting.

LEVEL/SHAPE DECOMPOSITION (the reason four legs exist). Against the
production flat-4.0 control:
  LEVEL  = flat_4.5      - flat_4.0     (floor level alone, no seasonality)
  SHAPE  = shape_only    - flat_4.0     (calendar profile alone, mean pinned
                                         at the production 4.0%)
  TOTAL  = prereg_4.5    - flat_4.0     (the pre-registered leg, level+shape)
  INTERACTION = TOTAL - LEVEL - SHAPE   (non-additivity, reported not hidden)
Reported in $B and in pp of the empirical trapped benchmark.

WIRING (the reason this module exists).
- competing_risks.monthly_step(pool, market_rate, trans=None, beta1=None)
  receives NO timestamp, so the calendar month is not in its scope. The
  driver is therefore taken one frame up: microsim_engine._simulate_regime
  walks `for ts in qt_index` (microsim_engine.py:47-50) calling
  monthly_step exactly once per ts per regime.
- We wrap microsim_engine.monthly_step (imported into that module's
  namespace, so patching the name is sufficient — same idiom already proven
  and parity-gated in floor_cyclical.py:120-125, floor_sweep.py:124,
  floor_form_test.py:80, oos_identification.py:258) with a wrapper that
  advances a positional cursor over qt_index and sets
  literature_hazard.INVOLUNTARY_CPR_ANNUAL = H_MONTH[ts.month - 1],
  restoring PRODUCTION_FLOOR in a finally.
- microsim_engine._simulate_regime is ALSO wrapped, purely to reset the
  cursor to 0 at the start of each regime pool. It changes no arguments and
  no return value.
- SELF-CHECK, every call: the market_rate the engine passes must equal
  macro.loc[qt_index[cursor], "MORTGAGE30US"] / 100 exactly, else the cursor
  has desynchronised from the calendar and the run aborts. This makes the
  month attribution verifiable rather than assumed.
- NOTHING ELSE IS TOUCHED. beta1, the Rothstein elasticity, the hazard
  coefficients, FLOOR_MODE, the loan sample, the RNG seeds, the regime
  tuple, and the scorer are production. No existing repo file is modified.

PARITY CONTROLS (this run; both are pure wiring invariants):
  (a) H_MONTH = 4.0% in all twelve months. Must reproduce the committed
      no_lockin_null_results.json anchors — central $818.530084B, null
      $748.185024B, marginal +$70.345060B / +9.198460pp. Because setting the
      same constant on every month is arithmetically the production code
      path, this leg is expected BIT-EXACT, not merely within tolerance;
      both gates are recorded (BITWISE at 1e-9, COMMITTED at floor_cyclical's
      +/- 0.01).
  (b) H_MONTH = 4.5% in all twelve months. Must reproduce the committed
      floor_sweep_results.json 4.5% marginal, +$57.641550B.
  On failure: STOP. Report the discrepancy. Do not adjust anything to make
  it match — withdraw-not-reinterpret.

THE FOUR H_MONTH NORMALIZATIONS (constructed and recorded here; only the two
flat ones are RUN in part 1):
  flat_4.0    — control (a); production floor.
  flat_4.5    — control (b); the committed level-sweep 4.5% point.
  shape_only  — the B1 deep-OOM seasonal shape rescaled so its
                EXPOSURE-WEIGHTED MEAN annual CPR equals the production 4.0%.
                Multiplicative rescaling on the ANNUAL-CPR scale (the scale
                INVOLUNTARY_CPR_ANNUAL is expressed in), weights = each
                calendar month's share of deep-OOM exposure in the B1 set.
                This is the leg that isolates the B2 mechanism: the window
                floor level is held at production, so any movement in the
                marginal or in the timing scores is attributable to SHAPE.
  prereg_4.5  — the same shape rescaled to an exposure-weighted mean of
                FLOOR_TARGET_ANNUAL_CPR = 4.5%, as the brief froze it.
                CONFOUNDED BY CONSTRUCTION and retained anyway (see below).

WHY prereg_4.5 IS CONFOUNDED, AND WHY IT IS STILL REPORTED. The committed
constant-floor sweep already establishes that the LEVEL move 4.0% -> 4.5%
alone, with no seasonality whatsoever, drops the lock-in marginal from
+$70.3451B to +$57.6416B (-$12.70B, 9.198pp -> 7.537pp). Any seasonal leg
normalized to a 4.5% mean therefore carries that entire level effect inside
it, and a naive read of "seasonal floor moves the marginal by ~$13B" would
be reporting the level sweep a second time under a new name. shape_only
removes exactly that confound by pinning the exposure-weighted mean at the
production 4.0%, leaving the calendar profile as the only difference from
production. BOTH legs are reported. prereg_4.5 is NOT discarded — it was
pre-registered, it is the honest pre-committed object, and its correct
interpretation is simply level-plus-shape, decomposable against the
committed 4.5% flat control run here as leg (b).

B1 PROFILE PROVENANCE (recomputed in this module, not taken on trust):
hazard/data/cohort_month_panel.parquet, filter gap <= -150bp (cohort coupon
minus MORTGAGE30US for that month), coupon > 0, mean_loan_age >= 12;
exposure-weighted SMM by calendar month = sum(prepaid_upb)/sum(exposure_upb)
within month. The market-rate series is read from the B0 artifact rather
than re-fetched from FRED.

  BASIS — CORRECTED. The committed 12-vector (B1_SMM_ANCHOR) is the
  FULL-PANEL estimate: the deep-OOM filter is applied to EVERY month of
  cohort_month_panel.parquet, not to the QT window.  An earlier draft of
  this docstring described it as "in-window"; that was WRONG.  The two
  bases are materially different and BOTH are now computed and recorded
  in the artifact under b1_profile.bases:
      full_panel : 7,756 cohort-months, $74.21T exposure, POOLED annual CPR
                   4.187%  <-- the basis the committed anchor and every
                   H_MONTH normalization use
      qt_window  : 7,452 cohort-months, $72.49T exposure, POOLED annual CPR
                   4.1132%, with DIFFERENT Mar/Apr/May/Dec cells
  "Pooled" means sum(prepaid_upb)/sum(exposure_upb) over the basis, then
  annualized.  It is NOT the same as the exposure-weighted mean of the
  twelve already-annualized calendar-month CPRs (4.1832% on the full
  panel) — the two differ by Jensen and both are recorded.
  Every number downstream of h_month_from_shape uses the FULL-PANEL basis.
  The QT-restricted basis is computed for disclosure only and is not used
  to drive any run.  Which basis a quoted figure rests on must be stated
  wherever the seasonal floor is quoted.

CARRIED CAVEATS (disclosure obligations, not defects to be fixed here):
 1. B1 is CIRCULAR in-window: gap <= -150bp captures ~98% of QT exposure, so
    the "deeply out-of-the-money" filter is near the identity map and the
    estimated profile is essentially the aggregate CPR seasonal, itself
    lock-in-suppressed. The floor is not identified off a lock-in-free
    population.
 2. The clean out-of-window (2017-2019) leg cannot rescue it: too few
    deep-OOM cohort-months, with literally zero prepaid_upb in some calendar
    cells, so no 12-cell profile is estimable there.
 3. The seasonal SHARE inverts between windows (full-panel seasonal R2 ~0.01
    vs QT-window 0.755). B1 inherits that instability.
 4. Tension with the committed Path A VOLUNTARY seasonality
    (seasonality_concave_gap.py), whose calendar-month log effects peak in
    MAR/OCT/SEP; this INVOLUNTARY profile peaks in JUN. Different objects
    (voluntary refi/move vs involuntary turnover), but the tension must be
    stated wherever the seasonal floor is quoted.

PLACEBO / NULL LEGS (added in the hardening revision; RUN, not asserted)
  The four substantive legs above cannot by themselves establish that any
  movement they produce is a CALENDAR effect.  Three placebo families are
  therefore run in the same session, on the same harness, and written to
  the artifact as first-class fields:

  PERMUTATION (placebo_permutation, N = 14).  The SAME twelve shape_only
    floor values, assigned to SCRAMBLED calendar months by a seeded RNG
    (PLACEBO_SEED, orders recorded verbatim).  If the marginal survives
    scrambling, the effect is DISPERSION under FLOOR_MODE='max'
    (hazard/config.py:52), not calendar timing: max(h_floor, h_vol)
    truncates the floor away in low months and lets it bind in high ones,
    so any dispersion in the floor raises the effective hazard one-sidedly.
    Both p_q legs are run so a marginal $B is available per permutation.

  ROTATION (placebo_rotation, all 12 shifts, shape_only AND prereg_4.5).
    h_rot_k[m] = h[(m - k) mod 12] — the true profile moved to the WRONG
    months, amplitude and dispersion held exactly.  Rotation k=0 is the
    identity and doubles as an internal reproduction check.  Central runs
    only; the rotation family tests the TIMING rule, not the level.

  JENSEN-EQUIVALENT FLAT (placebo_jensen_flat).  The single FLAT annual CPR
    whose monthly hazard equals the QT-calendar-frequency-weighted mean of
    the twelve seasonal monthly hazards, i.e. the level that reproduces the
    convexity of cpr_annual_to_monthly_hazard with NO dispersion at all.
    Its marginal separates pure level leakage from dispersion.

  These legs are placebos: they are EXPECTED to move nothing if the
  mechanism is calendar timing.  Whatever they show is reported as-is.

Run:  cd hazard && python3 seasonal_floor_timing.py
      -> data/seasonal_floor_timing_results.json (+ per-run parquets under
         data/seasonal_floor_timing/, regenerable, not committed)
"""
from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

DATA_DIR = Path(__file__).parent / "data"
RUN_DIR = DATA_DIR / "seasonal_floor_timing"
RESULTS_JSON = DATA_DIR / "seasonal_floor_timing_results.json"
SCRATCH_JSON = Path(
    "/private/tmp/claude-501/-Users-eugene-somthing-Lock-In-effect-"
    "Lock-in-Effect/dc42b60e-9f6a-4d3c-9fcb-f964562227af/scratchpad/"
    "b2_seasonal_floor_results.json"
)
NULL_ARTIFACT = DATA_DIR / "no_lockin_null_results.json"
SWEEP_ARTIFACT = DATA_DIR / "floor_sweep_results.json"
PANEL_PATH = DATA_DIR / "cohort_month_panel.parquet"
# Read the COMMITTED copy, not the session scratchpad: the scratchpad is
# session-scoped and gets garbage-collected, so keying off it made this module
# unrunnable from a clean checkout. The scratchpad remains a fallback only.
_B0_REPO = DATA_DIR / "b0_variance_decomposition.json"
B0_ARTIFACT = _B0_REPO if _B0_REPO.is_file() else Path(
    "/private/tmp/claude-501/-Users-eugene-somthing-Lock-In-effect-"
    "Lock-in-Effect/dc42b60e-9f6a-4d3c-9fcb-f964562227af/scratchpad/"
    "b0_variance_decomposition.json"
)

PRODUCTION_FLOOR = 0.04
FLOOR_TARGET_ANNUAL_CPR = 0.045  # pre-registered seasonal-leg mean
CENTRAL_PQ = 6.5
NULL_PQ = 0.0
PARITY_TOL = 0.01      # committed tolerance (floor_cyclical kappa=0 gate)
BITWISE_TOL = 1e-9     # flat legs are arithmetically the production path

# B1 deep-OOM filter (pre-committed)
DEEP_OOM_GAP = -0.015
MIN_MEAN_AGE = 12.0

# B1 anchors to reproduce (from the B0/B1 pre-work handed to this module)
B1_SMM_ANCHOR = np.array([
    0.00221, 0.00243, 0.00333, 0.00376, 0.00441, 0.00471,
    0.00430, 0.00421, 0.00367, 0.00348, 0.00288, 0.00276,
])
B1_P2T_ANCHOR = 2.131

# Frozen B3 timing criterion + committed Path B baseline (figures/theil_data.json)
TIMING_U2_MAX = 1.0
THEIL_N_MONTHS = 42
PATH_B_BASELINE = {
    "u1_levels": 0.2653, "u2_diffs": 1.0029, "u1_detrended": 0.9797,
}
THEIL_BASELINE_TOL = 5e-4

# ---- Placebo / null families (hardening revision) -------------------------
PLACEBO_SEED = 20260719      # fixed before any placebo ran
N_PERMUTATIONS = 14          # >= 14 required by spec
ROTATION_BASE_LEGS = ("shape_only", "prereg_4.5")


# --------------------------------------------------------------------------
# Frozen timing statistics (formulas copied from figures/make_theil_data.py)
# --------------------------------------------------------------------------
def theil_u1(sim: np.ndarray, emp: np.ndarray) -> float:
    rmse = float(np.sqrt(np.mean((sim - emp) ** 2)))
    return rmse / (float(np.sqrt(np.mean(sim ** 2)))
                   + float(np.sqrt(np.mean(emp ** 2))))


def theil_u2_diffs(sim: np.ndarray, emp: np.ndarray) -> float:
    ds, de = np.diff(sim), np.diff(emp)
    return float(np.sqrt(np.mean((ds - de) ** 2)) / np.sqrt(np.mean(de ** 2)))


def detrend(x: np.ndarray) -> np.ndarray:
    t = np.arange(len(x), dtype=float)
    return x - np.polyval(np.polyfit(t, x, 1), t)


def timing_block(sim: np.ndarray, emp: np.ndarray) -> dict:
    """The frozen B3 criterion, evaluated. No variants, no search."""
    u2 = theil_u2_diffs(sim, emp)
    r_det = float(np.corrcoef(detrend(sim), detrend(emp))[0, 1])
    return {
        "u1_levels": theil_u1(sim, emp),
        "u2_diffs": u2,
        "u1_detrended": theil_u1(detrend(sim), detrend(emp)),
        "detrended_lag0_r": r_det,
        "u2_below_1": bool(u2 < TIMING_U2_MAX),
        "detrended_lag0_r_positive": bool(r_det > 0.0),
        "timing_pass": bool(u2 < TIMING_U2_MAX and r_det > 0.0),
        # HOW MUCH the criterion is cleared by. The frozen rule is a strict
        # inequality on both legs, so a pass can be arbitrarily thin; the
        # margins are recorded so no reader can mistake "PASS" for "large".
        "u2_margin_below_1": float(TIMING_U2_MAX - u2),
        "detrended_lag0_r_t_stat": float(
            r_det * np.sqrt((len(sim) - 2) / (1.0 - r_det ** 2))
        ),
        "detrended_lag0_r_dof": int(len(sim) - 2),
    }


# --------------------------------------------------------------------------
# B1 seasonal profile, recomputed from the panel
# --------------------------------------------------------------------------
def compute_b1_profile(basis: str = "full_panel") -> dict:
    """Exposure-weighted deep-OOM SMM by calendar month, from the panel.

    basis = "full_panel" (DEFAULT, and the basis the committed anchor and
    every H_MONTH normalization rest on): the deep-OOM filter is applied to
    every month present in cohort_month_panel.parquet.

    basis = "qt_window": the same filter, further restricted to
    QT_START <= period < QT_END.  Computed for DISCLOSURE ONLY — it yields a
    different 12-vector (Mar/Apr/May/Dec cells move) and is never used to
    drive a run.
    """
    series = json.load(open(B0_ARTIFACT))["series"]
    rate = {r["period"]: r["mortgage30us_pct"] / 100.0 for r in series}

    p = pl.read_parquet(PANEL_PATH).to_pandas()
    p["ym"] = p["period"].dt.strftime("%Y-%m")
    p["mkt"] = p["ym"].map(rate)
    if p["mkt"].isna().any():
        raise RuntimeError("panel months missing from the B0 rate series")
    p["gap"] = p["coupon"] - p["mkt"]

    f = p[(p["gap"] <= DEEP_OOM_GAP) & (p["coupon"] > 0)
          & (p["mean_loan_age"] >= MIN_MEAN_AGE)]
    if basis == "qt_window":
        from config import QT_END, QT_START
        f = f[(f["period"] >= QT_START) & (f["period"] < QT_END)]
    elif basis != "full_panel":
        raise ValueError(f"unknown basis {basis!r}")
    m = f["period"].dt.month
    prepaid = f.groupby(m)["prepaid_upb"].sum()
    exposure = f.groupby(m)["exposure_upb"].sum()
    if list(prepaid.index) != list(range(1, 13)):
        raise RuntimeError("deep-OOM set does not cover all twelve months")

    smm = (prepaid / exposure).to_numpy()
    w = (exposure / exposure.sum()).to_numpy()
    pooled_smm = float(prepaid.sum() / exposure.sum())
    cpr = 1.0 - (1.0 - smm) ** 12
    return {
        "basis": basis,
        "n_cohort_months": int(len(f)),
        "exposure_usd": float(f["exposure_upb"].sum()),
        "exposure_weighted_mean_annual_cpr": float(np.dot(w, cpr)),
        "smm_by_month": smm,
        "exposure_weight_by_month": w,
        "peak_to_trough": float(smm.max() / smm.min()),
        "peak_month": int(smm.argmax() + 1),
        "trough_month": int(smm.argmin() + 1),
        "pooled_smm": pooled_smm,
        "pooled_annual_cpr": float(1.0 - (1.0 - pooled_smm) ** 12),
    }


def permutation_orders(n: int, seed: int) -> list:
    """n DISTINCT non-identity scrambles of the twelve calendar slots.

    Drawn from a seeded Generator before any of them is run, so the family
    is fixed ex ante and reproducible from the recorded seed alone.
    """
    rng = np.random.default_rng(seed)
    identity = tuple(range(12))
    seen, out = {identity}, []
    while len(out) < n:
        cand = tuple(int(v) for v in rng.permutation(12))
        if cand in seen:
            continue
        seen.add(cand)
        out.append(list(cand))
    return out


def apply_permutation(h: np.ndarray, order: list) -> np.ndarray:
    """Calendar month m gets the floor value that truly belongs to order[m].

    The multiset of twelve values is preserved EXACTLY; only the assignment
    of values to calendar months changes.
    """
    return np.asarray(h, dtype=np.float64)[np.asarray(order, dtype=int)]


def apply_rotation(h: np.ndarray, k: int) -> np.ndarray:
    """Shift the profile k months forward in the calendar (k=0 = identity)."""
    return np.roll(np.asarray(h, dtype=np.float64), k)


def jensen_equivalent_flat(h: np.ndarray, weights: np.ndarray) -> float:
    """The FLAT annual CPR with the same weighted-mean MONTHLY hazard.

    cpr_annual_to_monthly_hazard is convex, so a dispersed floor carries a
    higher mean monthly hazard than its own mean annual CPR implies.  This
    inverts that: it returns the single flat annual CPR reproducing the
    convexity with ZERO dispersion, isolating level leakage from dispersion.
    Uses the committed conversion, not a re-implementation.
    """
    from literature_hazard import cpr_annual_to_monthly_hazard

    h_bar = float(np.dot(np.asarray(weights, dtype=np.float64),
                         cpr_annual_to_monthly_hazard(h)))
    return float(1.0 - (1.0 - h_bar) ** 12)


def h_month_from_shape(prof: dict, target_mean: float) -> np.ndarray:
    """Rescale the B1 shape to an exposure-weighted mean annual CPR.

    Shape is carried on the ANNUAL-CPR scale — the scale
    literature_hazard.INVOLUNTARY_CPR_ANNUAL is expressed in — and rescaled
    multiplicatively, so relative calendar amplitude is preserved exactly.
    """
    cpr = 1.0 - (1.0 - prof["smm_by_month"]) ** 12
    w = prof["exposure_weight_by_month"]
    scale = target_mean / float(np.dot(w, cpr))
    return cpr * scale


# --------------------------------------------------------------------------
# Wiring: calendar-month-driven floor at the qt_index loop
# --------------------------------------------------------------------------
class MonthCursor:
    """Positional cursor over qt_index, reset per regime, self-checked
    against the market rate the engine passes."""

    def __init__(self, qt_index: pd.DatetimeIndex, rates: np.ndarray):
        self.qt_index = qt_index
        self.rates = rates
        self.k = 0
        self.months_seen: list[int] = []

    def reset(self) -> None:
        self.k = 0

    def next_month(self, market_rate: float) -> int:
        if self.k >= len(self.qt_index):
            raise RuntimeError(
                f"cursor overran qt_index ({self.k} >= {len(self.qt_index)}): "
                "monthly_step called more often than once per QT month"
            )
        ts = self.qt_index[self.k]
        want = float(self.rates[self.k])
        if float(market_rate) != want:
            raise RuntimeError(
                f"calendar desync at cursor {self.k} ({ts:%Y-%m}): engine "
                f"passed market_rate {market_rate!r}, qt_index expects {want!r}"
            )
        self.k += 1
        self.months_seen.append(int(ts.month))
        return int(ts.month)


def _qt_index_and_rates(macro: pd.DataFrame):
    from config import QT_END, QT_START

    idx = macro.index[(macro.index >= QT_START) & (macro.index < QT_END)]
    return idx, (macro.loc[idx, "MORTGAGE30US"] / 100.0).to_numpy()


def _run_scored(loans, empirical, macro, h_month: np.ndarray, label: str,
                pq: float) -> dict:
    """One microsim run with a calendar-month-driven floor; production
    convention in every other respect."""
    import literature_hazard
    import microsim_engine
    from extension_risk import score_extension_risk
    from literature_hazard import rothstein_beta1

    qt_index, rates = _qt_index_and_rates(macro)
    cur = MonthCursor(qt_index, rates)
    h = np.asarray(h_month, dtype=np.float64)
    if h.shape != (12,):
        raise ValueError("H_MONTH must be a 12-vector of annual CPRs")
    if not np.all(h >= 0.0):
        raise ValueError("H_MONTH must be non-negative")

    orig_step = microsim_engine.monthly_step
    orig_regime = microsim_engine._simulate_regime

    def _seasonal_step(pool, market_rate, trans=None, beta1=None):
        month = cur.next_month(market_rate)
        literature_hazard.INVOLUNTARY_CPR_ANNUAL = float(h[month - 1])
        try:
            return orig_step(pool, market_rate, trans=trans, beta1=beta1)
        finally:
            literature_hazard.INVOLUNTARY_CPR_ANNUAL = PRODUCTION_FLOOR

    def _cursor_resetting_regime(*args, **kwargs):
        cur.reset()
        return orig_regime(*args, **kwargs)

    out_path = RUN_DIR / f"microsim_{label}_pq{pq:g}.parquet"
    microsim_engine.monthly_step = _seasonal_step
    microsim_engine._simulate_regime = _cursor_resetting_regime
    try:
        microsim_engine.run_qt_microsim(
            loan_sample=loans, macro=macro, output=out_path, p_q_shock_pct=pq
        )
    finally:
        microsim_engine.monthly_step = orig_step
        microsim_engine._simulate_regime = orig_regime
        literature_hazard.INVOLUNTARY_CPR_ANNUAL = PRODUCTION_FLOOR

    sim = pd.read_parquet(out_path)
    score = score_extension_risk(sim, empirical)

    # Full simulated monthly CPR path on the scored QT window, aligned to the
    # empirical frame exactly as score_extension_risk aligns it.
    from macro import qt_active_frame

    qt_emp = qt_active_frame(empirical)
    qt_sim = sim.reindex(qt_emp.index).dropna(subset=["simulated_rolloff_b"])
    path_periods = [f"{t:%Y-%m}" for t in qt_sim.index]
    path_cpr = qt_sim["hazard_cpr_pct"].to_numpy(dtype=float)
    emp_cpr = qt_emp.loc[qt_sim.index, "Empirical_CPR_Pct"].to_numpy(dtype=float)
    if len(path_cpr) != THEIL_N_MONTHS:
        raise RuntimeError(
            f"{label}/pq{pq:g}: scored window has {len(path_cpr)} months, "
            f"expected {THEIL_N_MONTHS}"
        )

    return {
        "path_periods": path_periods,
        "path_hazard_cpr_pct": list(map(float, path_cpr)),
        "path_simulated_rolloff_b": list(
            map(float, qt_sim["simulated_rolloff_b"].to_numpy(dtype=float))
        ),
        "empirical_cpr_pct": list(map(float, emp_cpr)),
        "timing": timing_block(path_cpr, emp_cpr),
        "leg": label,
        "p_q_shock_pct": pq,
        "beta1": rothstein_beta1(pq / 100.0),
        "trapped_b": float(score["hazard_trapped_b"]),
        "share_pct": float(score["share_explained_pct"]),
        "cpr_r_lag0": float(score["cross_correlation"].get(0, float("nan"))),
        "best_lag": score["best_lag"],
        "peak_lag_r": float(score["peak_lag_r"]),
        "mean_us_cpr_pct": float(sim["hazard_cpr_pct"].mean()),
        "months_driven": len(cur.months_seen),
        "month_sequence_ok": (
            cur.months_seen[:len(qt_index)] == [int(t.month) for t in qt_index]
        ),
    }


def _git_head() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
            cwd=Path(__file__).parent, check=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def main() -> None:
    from config import LOAN_SAMPLE_PATH
    from literature_hazard import rothstein_beta1
    from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly

    assert rothstein_beta1(0.0) == 0.0
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    # ---- B1 recomputation, BOTH bases ---------------------------------------
    # The committed anchor is the FULL-PANEL estimate. The QT-restricted
    # variant is computed for disclosure and drives nothing.
    prof = compute_b1_profile("full_panel")
    prof_qt = compute_b1_profile("qt_window")
    smm = prof["smm_by_month"]
    smm_absdiff = np.abs(np.round(smm, 5) - B1_SMM_ANCHOR)
    b1_ok = bool(smm_absdiff.max() <= 5e-6
                 and abs(prof["peak_to_trough"] - B1_P2T_ANCHOR) <= 5e-4)
    print("B1 recomputation (basis = FULL PANEL; this is what the anchor is):")
    print(f"  cohort-months {prof['n_cohort_months']:,}  "
          f"exposure ${prof['exposure_usd'] / 1e12:.2f}T  "
          f"pooled annual CPR {prof['pooled_annual_cpr'] * 100:.4f}%  "
          f"(ew-mean-of-annualized "
          f"{prof['exposure_weighted_mean_annual_cpr'] * 100:.4f}%)")
    print("  SMM Jan..Dec  " + " ".join(f"{v:.5f}" for v in smm))
    print(f"  peak-to-trough {prof['peak_to_trough']:.4f} "
          f"(peak {prof['peak_month']}, trough {prof['trough_month']})  "
          f"[{'REPRODUCED' if b1_ok else 'MISMATCH'}]")
    print("B1 alternative basis (QT window only; DISCLOSURE, drives nothing):")
    print(f"  cohort-months {prof_qt['n_cohort_months']:,}  "
          f"exposure ${prof_qt['exposure_usd'] / 1e12:.2f}T  "
          f"pooled annual CPR {prof_qt['pooled_annual_cpr'] * 100:.4f}%  "
          f"(ew-mean-of-annualized "
          f"{prof_qt['exposure_weighted_mean_annual_cpr'] * 100:.4f}%)")
    print("  SMM Jan..Dec  " + " ".join(f"{v:.5f}" for v in
                                        prof_qt["smm_by_month"]))
    basis_cells_differ = [i + 1 for i in range(12)
                          if abs(round(float(smm[i]), 5)
                                 - round(float(prof_qt["smm_by_month"][i]), 5))
                          >= 1e-5]
    print(f"  calendar cells differing at 5dp vs full panel: "
          f"{basis_cells_differ}")

    # ---- The four H_MONTH normalizations ------------------------------------
    h_shape_only = h_month_from_shape(prof, PRODUCTION_FLOOR)
    h_prereg = h_month_from_shape(prof, FLOOR_TARGET_ANNUAL_CPR)
    h_flat40 = np.full(12, PRODUCTION_FLOOR)
    h_flat45 = np.full(12, FLOOR_TARGET_ANNUAL_CPR)
    w = prof["exposure_weight_by_month"]
    normalizations = {
        "flat_4.0": h_flat40,
        "flat_4.5": h_flat45,
        "shape_only": h_shape_only,
        "prereg_4.5": h_prereg,
    }
    print("\nH_MONTH normalizations (annual CPR %, Jan..Dec):")
    for name, h in normalizations.items():
        print(f"  {name:<11} " + " ".join(f"{v * 100:5.3f}" for v in h)
              + f"   ew-mean {float(np.dot(w, h)) * 100:.4f}%")

    # ---- All four legs, one session -----------------------------------------
    print("\nScoring empirical benchmark (shared macro frame, fetched once) …")
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)
    if not LOAN_SAMPLE_PATH.exists():
        raise FileNotFoundError(f"{LOAN_SAMPLE_PATH} missing.")
    loans = pl.read_parquet(LOAN_SAMPLE_PATH)

    t0 = time.perf_counter()
    legs = {}
    for name in ("flat_4.0", "flat_4.5", "shape_only", "prereg_4.5"):
        h = normalizations[name]
        null = _run_scored(loans, empirical, macro, h, name, NULL_PQ)
        central = _run_scored(loans, empirical, macro, h, name, CENTRAL_PQ)
        legs[name] = {
            "h_month_annual_cpr": list(map(float, h)),
            "null": null,
            "central": central,
            "lockin_marginal_b": central["trapped_b"] - null["trapped_b"],
            "lockin_marginal_share_pp": central["share_pct"] - null["share_pct"],
        }
        c = legs[name]
        print(f"{name}:  null ${null['trapped_b']:.6f}B  "
              f"central ${central['trapped_b']:.6f}B  "
              f"marginal ${c['lockin_marginal_b']:+.6f}B "
              f"({c['lockin_marginal_share_pp']:+.6f}pp)")

    # ---- Gates --------------------------------------------------------------
    anchor = json.load(open(NULL_ARTIFACT))
    sweep = json.load(open(SWEEP_ARTIFACT))
    sweep45 = next(r for r in sweep["rows"]
                   if abs(r["floor_annual_cpr_pct"] - 4.5) < 1e-9)

    checks = [
        ("flat_4.0", "central_trapped_b",
         legs["flat_4.0"]["central"]["trapped_b"], anchor["central_trapped_b"]),
        ("flat_4.0", "null_trapped_b",
         legs["flat_4.0"]["null"]["trapped_b"], anchor["null_trapped_b"]),
        ("flat_4.0", "lockin_marginal_b",
         legs["flat_4.0"]["lockin_marginal_b"], anchor["lockin_marginal_b"]),
        ("flat_4.0", "lockin_marginal_share_pp",
         legs["flat_4.0"]["lockin_marginal_share_pp"],
         anchor["lockin_marginal_share_pp"]),
        ("flat_4.5", "lockin_marginal_b",
         legs["flat_4.5"]["lockin_marginal_b"], sweep45["lockin_marginal_b"]),
        ("flat_4.5", "lockin_marginal_share_pp",
         legs["flat_4.5"]["lockin_marginal_share_pp"],
         sweep45["lockin_marginal_share_pp"]),
    ]
    gate_report = {}
    print()
    for leg, name, got, want in checks:
        diff = abs(got - want)
        gate_report[f"{leg}::{name}"] = {
            "got": got, "want": want, "abs_diff": diff,
            "pass_committed_tol": bool(diff < PARITY_TOL),
            "pass_bitwise": bool(diff <= BITWISE_TOL),
        }
        print(f"parity {leg} {name}: got {got:.6f} want {want:.6f} "
              f"|diff| {diff:.3e} "
              f"[{'PASS' if diff < PARITY_TOL else 'FAIL'}"
              f"{' / BITWISE' if diff <= BITWISE_TOL else ''}]")

    parity_pass = all(v["pass_committed_tol"] for v in gate_report.values())
    bitwise_pass = all(v["pass_bitwise"] for v in gate_report.values())
    wiring_pass = all(
        legs[k][leg]["month_sequence_ok"] for k in legs for leg in ("null", "central")
    )
    print(f"\nmonth-sequence self-check: {'PASS' if wiring_pass else 'FAIL'}")

    # ---- PLACEBO / NULL FAMILIES --------------------------------------------
    # Run only if the harness reproduced the committed anchors: placebo legs
    # off a broken harness would be noise dressed as a diagnostic.
    if not (parity_pass and wiring_pass):
        raise SystemExit(
            "PARITY/WIRING GATE FAILED before the placebo families ran. Every "
            "number in this session is VOID. Do not tune to match."
        )

    qt_index, _ = _qt_index_and_rates(macro)
    qt_month_freq = np.bincount([int(t.month) for t in qt_index],
                                minlength=13)[1:].astype(float)
    qt_month_freq /= qt_month_freq.sum()

    # (1) PERMUTATION: same twelve values, scrambled calendar assignment.
    orders = permutation_orders(N_PERMUTATIONS, PLACEBO_SEED)
    print(f"\nPLACEBO 1/3 — permutation null "
          f"({N_PERMUTATIONS} scrambles of the shape_only 12-vector, "
          f"seed {PLACEBO_SEED}):")
    perm_legs = {}
    for i, order in enumerate(orders):
        h_p = apply_permutation(h_shape_only, order)
        tag = f"perm{i:02d}"
        n_r = _run_scored(loans, empirical, macro, h_p, tag, NULL_PQ)
        c_r = _run_scored(loans, empirical, macro, h_p, tag, CENTRAL_PQ)
        marg = c_r["trapped_b"] - n_r["trapped_b"]
        perm_legs[tag] = {
            "order_month_to_source_slot": order,
            "h_month_annual_cpr": list(map(float, h_p)),
            "values_multiset_preserved": bool(
                np.array_equal(np.sort(h_p), np.sort(h_shape_only))),
            "lockin_marginal_b": marg,
            "lockin_marginal_share_pp":
                c_r["share_pct"] - n_r["share_pct"],
            "central_timing": c_r["timing"],
            "null_timing": n_r["timing"],
            "central_path_hazard_cpr_pct": c_r["path_hazard_cpr_pct"],
        }
        t = c_r["timing"]
        print(f"  {tag}  marginal {marg:+9.6f} B   U2 {t['u2_diffs']:.6f}   "
              f"r_det {t['detrended_lag0_r']:+.6f}   "
              f"[{'PASS' if t['timing_pass'] else 'CONCEDE'}]")

    # (2) ROTATION: true profile moved to the WRONG months, dispersion held.
    print("\nPLACEBO 2/3 — rotation placebo (12 shifts x "
          f"{len(ROTATION_BASE_LEGS)} base legs, central p_q=6.5 only):")
    rot_legs = {}
    for base in ROTATION_BASE_LEGS:
        h_base = normalizations[base]
        rot_legs[base] = {}
        for k in range(12):
            h_k = apply_rotation(h_base, k)
            tag = f"rot{k:02d}"
            c_r = _run_scored(loans, empirical, macro, h_k, f"{base}_{tag}",
                              CENTRAL_PQ)
            rot_legs[base][tag] = {
                "shift_months": k,
                "h_month_annual_cpr": list(map(float, h_k)),
                "central_timing": c_r["timing"],
                "central_trapped_b": c_r["trapped_b"],
                "central_path_hazard_cpr_pct": c_r["path_hazard_cpr_pct"],
            }
            t = c_r["timing"]
            print(f"  {base:<11} {tag}  U2 {t['u2_diffs']:.6f}  r_det "
                  f"{t['detrended_lag0_r']:+.6f}  "
                  f"[{'PASS' if t['timing_pass'] else 'CONCEDE'}]"
                  f"{'   <- identity' if k == 0 else ''}")

    # (3) JENSEN-EQUIVALENT FLAT: convexity without dispersion.
    jensen_cpr = jensen_equivalent_flat(h_shape_only, qt_month_freq)
    h_jensen = np.full(12, jensen_cpr)
    print(f"\nPLACEBO 3/3 — Jensen-equivalent flat floor "
          f"{jensen_cpr * 100:.6f}% (QT calendar-frequency weights):")
    j_null = _run_scored(loans, empirical, macro, h_jensen, "jensen_flat",
                         NULL_PQ)
    j_cent = _run_scored(loans, empirical, macro, h_jensen, "jensen_flat",
                         CENTRAL_PQ)
    jensen_leg = {
        "flat_annual_cpr": jensen_cpr,
        "weights_basis": "QT-window calendar-month frequency (n=42)",
        "weights": list(map(float, qt_month_freq)),
        "alt_exposure_weighted_flat_annual_cpr":
            jensen_equivalent_flat(h_shape_only, w),
        "alt_uniform_weighted_flat_annual_cpr":
            jensen_equivalent_flat(h_shape_only, np.full(12, 1.0 / 12.0)),
        "h_month_annual_cpr": list(map(float, h_jensen)),
        "lockin_marginal_b": j_cent["trapped_b"] - j_null["trapped_b"],
        "lockin_marginal_share_pp": j_cent["share_pct"] - j_null["share_pct"],
        "central_timing": j_cent["timing"],
        "central_path_hazard_cpr_pct": j_cent["path_hazard_cpr_pct"],
    }
    print(f"  marginal {jensen_leg['lockin_marginal_b']:+.6f} B "
          f"({jensen_leg['lockin_marginal_share_pp']:+.6f} pp)")

    # ---- PLACEBO SUMMARY: what the placebos actually establish --------------
    from config import FLOOR_MODE

    m_flat40 = legs["flat_4.0"]["lockin_marginal_b"]
    m_shape = legs["shape_only"]["lockin_marginal_b"]
    true_shape_effect = m_shape - m_flat40          # the "shape effect", $B
    perm_marginals = np.array([v["lockin_marginal_b"]
                               for v in perm_legs.values()], dtype=float)
    perm_effects = perm_marginals - m_flat40
    # Fraction of the shape effect that SURVIVES scrambling the calendar.
    retained = (perm_effects / true_shape_effect
                if true_shape_effect != 0 else np.full_like(perm_effects,
                                                            np.nan))
    jensen_effect = jensen_leg["lockin_marginal_b"] - m_flat40

    perm_pass = [k for k, v in perm_legs.items()
                 if v["central_timing"]["timing_pass"]]
    rot_summary = {}
    for base in ROTATION_BASE_LEGS:
        true_u2 = legs[base]["central"]["timing"]["u2_diffs"]
        rows = rot_legs[base]
        passing = [k for k, v in rows.items()
                   if v["central_timing"]["timing_pass"]]
        # rot00 IS the true profile. It must be excluded from every placebo
        # count, or the identity inflates the placebo size by one.
        wrong = {k: v for k, v in rows.items() if v["shift_months"] != 0}
        wrong_passing = [k for k, v in wrong.items()
                         if v["central_timing"]["timing_pass"]]
        beats = {k: v["central_timing"]["u2_diffs"] for k, v in wrong.items()
                 if v["central_timing"]["u2_diffs"] < true_u2}
        rot_summary[base] = {
            "true_profile_u2_diffs": true_u2,
            "n_rotations": len(rows),
            "n_wrong_month_rotations": len(wrong),
            "n_passing_frozen_rule_incl_identity": len(passing),
            "rotations_passing_incl_identity": passing,
            "n_wrong_month_rotations_passing": len(wrong_passing),
            "wrong_month_rotations_passing": wrong_passing,
            "identity_rot00_reproduces_true_leg": bool(
                abs(rows["rot00"]["central_timing"]["u2_diffs"] - true_u2)
                <= 1e-12),
            "wrong_month_rotations_beating_true_u2": beats,
            "any_wrong_rotation_beats_true_u2": bool(beats),
            "placebo_pass_rate_wrong_month_only": (
                len(wrong_passing) / len(wrong)),
            "count_note": ("rot00 is the identity, i.e. the true profile "
                           "itself; it is reported as a reproduction check "
                           "and EXCLUDED from the placebo pass rate."),
        }

    placebo_summary = {
        "floor_mode": FLOOR_MODE,
        "floor_mode_source": "hazard/config.py FLOOR_MODE",
        "true_shape_effect_b": float(true_shape_effect),
        "permutation": {
            "seed": PLACEBO_SEED,
            "n": int(len(perm_effects)),
            "marginal_b_mean": float(perm_marginals.mean()),
            "marginal_b_min": float(perm_marginals.min()),
            "marginal_b_max": float(perm_marginals.max()),
            "effect_vs_flat40_b_mean": float(perm_effects.mean()),
            "share_of_shape_effect_retained_mean": float(np.mean(retained)),
            "share_of_shape_effect_retained_min": float(np.min(retained)),
            "share_of_shape_effect_retained_max": float(np.max(retained)),
            "n_clearing_frozen_rule": len(perm_pass),
            "permutations_clearing_frozen_rule": perm_pass,
            "best_permutation_u2": float(min(
                v["central_timing"]["u2_diffs"] for v in perm_legs.values())),
            "any_permutation_beats_shape_only_u2": bool(
                min(v["central_timing"]["u2_diffs"]
                    for v in perm_legs.values())
                < legs["shape_only"]["central"]["timing"]["u2_diffs"]),
        },
        "rotation": rot_summary,
        "jensen_flat": {
            "flat_annual_cpr": jensen_cpr,
            "effect_vs_flat40_b": float(jensen_effect),
            "share_of_shape_effect_from_level_leakage": float(
                jensen_effect / true_shape_effect)
            if true_shape_effect else float("nan"),
            "share_of_shape_effect_from_floor_dispersion": float(
                1.0 - jensen_effect / true_shape_effect)
            if true_shape_effect else float("nan"),
        },
        "attribution": (
            "The permutation family scrambles the calendar while holding the "
            "twelve floor values EXACTLY. Whatever share of the shape effect "
            "survives that scramble is NOT a calendar effect. Under "
            f"FLOOR_MODE='{FLOOR_MODE}' the effective hazard is "
            "max(h_floor, h_vol), so the floor is truncated away in months "
            "where the volatility-driven hazard already exceeds it and binds "
            "only in the rest; ANY dispersion in the floor therefore raises "
            "the effective hazard ONE-SIDEDLY, independent of which calendar "
            "month carries which value. The Jensen-equivalent flat leg "
            "separates the remaining piece: it reproduces the convexity of "
            "cpr_annual_to_monthly_hazard with zero dispersion, so its effect "
            "is pure LEVEL LEAKAGE and the residual is FLOOR DISPERSION. Any "
            "write-up must therefore report this as a floor-dispersion / "
            "functional-form finding, NOT as 'seasonality moves the marginal'."
        ),
    }
    print("\nPLACEBO SUMMARY:")
    print(f"  true shape effect (shape_only - flat_4.0)  "
          f"{true_shape_effect:+.6f} B")
    print(f"  permutation mean effect                    "
          f"{perm_effects.mean():+.6f} B  "
          f"({np.mean(retained) * 100:.1f}% of it RETAINED under scrambling)")
    print(f"  Jensen-equivalent flat effect (level only) "
          f"{jensen_effect:+.6f} B  "
          f"({jensen_effect / true_shape_effect * 100:.1f}% of it)")
    print(f"  => residual attributable to FLOOR DISPERSION under "
          f"FLOOR_MODE='{FLOOR_MODE}': "
          f"{(1 - jensen_effect / true_shape_effect) * 100:.1f}%")
    for base, rs in rot_summary.items():
        print(f"  rotation placebo {base:<11} "
              f"{rs['n_wrong_month_rotations_passing']}/"
              f"{rs['n_wrong_month_rotations']} WRONG-month rotations pass "
              f"(identity rot00 excluded, reproduces true leg: "
              f"{rs['identity_rot00_reproduces_true_leg']}); "
              f"wrong-month rotation beating true U2: "
              f"{rs['any_wrong_rotation_beats_true_u2']}")

    # ---- Theil baseline cross-check: flat_4.0 central IS production Path B ---
    base_timing = legs["flat_4.0"]["central"]["timing"]
    theil_baseline_check = {
        k: {"got": base_timing[k], "want": v,
            "abs_diff": abs(base_timing[k] - v),
            "pass": bool(abs(base_timing[k] - v) <= THEIL_BASELINE_TOL)}
        for k, v in PATH_B_BASELINE.items()
    }
    theil_baseline_pass = all(v["pass"] for v in theil_baseline_check.values())
    print("\nTheil baseline cross-check (flat_4.0 central vs committed path_b):")
    for k, v in theil_baseline_check.items():
        print(f"  {k:<13} got {v['got']:.4f}  want {v['want']:.4f}  "
              f"|diff| {v['abs_diff']:.2e} [{'PASS' if v['pass'] else 'FAIL'}]")

    # ---- LEVEL / SHAPE decomposition vs the production flat-4.0 control ------
    def _d(leg: str) -> dict:
        return {
            "delta_marginal_b":
                legs[leg]["lockin_marginal_b"]
                - legs["flat_4.0"]["lockin_marginal_b"],
            "delta_marginal_pp":
                legs[leg]["lockin_marginal_share_pp"]
                - legs["flat_4.0"]["lockin_marginal_share_pp"],
            "delta_central_b":
                legs[leg]["central"]["trapped_b"]
                - legs["flat_4.0"]["central"]["trapped_b"],
            "delta_null_b":
                legs[leg]["null"]["trapped_b"]
                - legs["flat_4.0"]["null"]["trapped_b"],
        }

    level, shape, total = _d("flat_4.5"), _d("shape_only"), _d("prereg_4.5")
    interaction = {
        k: total[k] - level[k] - shape[k] for k in total
    }
    decomposition = {
        "basis": "all deltas are vs the flat_4.0 production control, same session",
        "level_flat45_minus_flat40": level,
        "shape_shapeonly_minus_flat40": shape,
        "total_prereg45_minus_flat40": total,
        "interaction_total_minus_level_minus_shape": interaction,
    }
    print("\nLEVEL/SHAPE decomposition of the lock-in marginal "
          "(vs flat_4.0 production control):")
    for nm, d in (("LEVEL  (flat4.5-flat4.0)", level),
                  ("SHAPE  (shape_only-flat4.0)", shape),
                  ("TOTAL  (prereg4.5-flat4.0)", total),
                  ("INTERACTION", interaction)):
        print(f"  {nm:<28} {d['delta_marginal_b']:+9.4f} B   "
              f"{d['delta_marginal_pp']:+8.4f} pp")

    # ---- FROZEN B3 TIMING VERDICT -------------------------------------------
    print("\nFROZEN B3 timing criterion (U2 < 1 AND detrended lag-0 r > 0), "
          "central p_q=6.5 runs:")
    for name in normalizations:
        t = legs[name]["central"]["timing"]
        print(f"  {name:<11} U2 {t['u2_diffs']:.4f} (margin "
              f"{t['u2_margin_below_1']:+.4f})  "
              f"detrended lag-0 r {t['detrended_lag0_r']:+.4f} "
              f"(t {t['detrended_lag0_r_t_stat']:+.2f})  "
              f"U1 lvl {t['u1_levels']:.4f}  U1 det {t['u1_detrended']:.4f}  "
              f"[{'PASS' if t['timing_pass'] else 'FAIL'}]")
    seasonal_timing_pass = all(
        legs[n]["central"]["timing"]["timing_pass"]
        for n in ("shape_only", "prereg_4.5")
    )

    # The frozen rule can be MET AS WRITTEN and still carry no information.
    # Whether it does is now a COMPUTED question, not a judgement call: if
    # wrong-month rotations clear it, or scrambled calendars clear it, or the
    # beta1 = 0 null clears it, then clearing it is not evidence of timing.
    null_leg_clears = {
        n: bool(legs[n]["null"]["timing"]["timing_pass"]) for n in legs
    }
    rule_defeated_by = []
    if any(rs["n_wrong_month_rotations_passing"] > 0
           for rs in rot_summary.values()):
        rule_defeated_by.append("wrong-month rotations clear it")
    if perm_pass:
        rule_defeated_by.append("scrambled calendars clear it")
    if any(null_leg_clears.values()):
        rule_defeated_by.append("the p_q=0 (beta1=0) null clears it")
    rule_has_power = not rule_defeated_by

    verdict = ("TIMING_PASS" if (seasonal_timing_pass and rule_has_power)
               else "CONCEDE_LEVELS_ONLY")
    print(f"\nB2 frozen rule met as written by both seasonal legs: "
          f"{seasonal_timing_pass}")
    print(f"B2 rule retains discriminating power: {rule_has_power}"
          + ("" if rule_has_power else "  (" + "; ".join(rule_defeated_by) + ")"))
    print(f"B2 TIMING VERDICT: {verdict}")
    if verdict == "CONCEDE_LEVELS_ONLY" and seasonal_timing_pass:
        print("  The rule is MET AS WRITTEN but the pass is NOT REAL: the "
              "placebo families clear the same rule. Restrict every claim to "
              "LEVELS. Do not tune. No lag-kernel hunting.")
    if verdict == "CONCEDE_LEVELS_ONLY" and not seasonal_timing_pass:
        print("  => monthly timing is NOT identifiable from the floor's "
              "calendar profile. Restrict every claim to LEVELS, including "
              "in the abstract. Do not tune. No lag-kernel hunting.")

    payload = {
        "mode": "seasonal_floor_timing_part2_seasonal_legs",
        "spec": "hazard/seasonal_floor_timing.py module docstring (fixed ex ante)",
        "git_commit": _git_head(),
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "b1_profile": {
            "basis_used_for_every_run": "full_panel",
            "basis_note": (
                "The committed 12-vector is the FULL-PANEL deep-OOM estimate, "
                "NOT a QT-window estimate; an earlier docstring said "
                "'in-window' and was wrong. Both bases are recorded below. "
                "Every H_MONTH normalization and every run in this artifact "
                "uses full_panel; qt_window is disclosure only."),
            "bases": {
                b["basis"]: {
                    "n_cohort_months": b["n_cohort_months"],
                    "exposure_usd": b["exposure_usd"],
                    # TWO different means; they differ by Jensen and the
                    # 4.187% / 4.1132% anchors are the POOLED one.
                    "pooled_annual_cpr": b["pooled_annual_cpr"],
                    "pooled_annual_cpr_definition":
                        "annualization of sum(prepaid_upb)/sum(exposure_upb) "
                        "over the whole basis; THIS is the 4.187% "
                        "(full_panel) / 4.1132% (qt_window) anchor",
                    "exposure_weighted_mean_annual_cpr":
                        b["exposure_weighted_mean_annual_cpr"],
                    "exposure_weighted_mean_annual_cpr_definition":
                        "exposure-weighted mean of the twelve ALREADY "
                        "annualized calendar-month CPRs; differs from the "
                        "pooled figure by Jensen and is NOT the anchor",
                    "smm_by_month_jan_dec": list(map(float,
                                                     b["smm_by_month"])),
                    "peak_to_trough": b["peak_to_trough"],
                    "peak_month": b["peak_month"],
                    "trough_month": b["trough_month"],
                } for b in (prof, prof_qt)
            },
            "calendar_cells_differing_between_bases_at_5dp":
                basis_cells_differ,
            "n_cohort_months": prof["n_cohort_months"],
            "exposure_usd": prof["exposure_usd"],
            "exposure_weighted_mean_annual_cpr":
                prof["exposure_weighted_mean_annual_cpr"],
            "smm_by_month_jan_dec": list(map(float, smm)),
            "smm_anchor_jan_dec": list(map(float, B1_SMM_ANCHOR)),
            "max_abs_diff_vs_anchor_5dp": float(smm_absdiff.max()),
            "peak_to_trough": prof["peak_to_trough"],
            "peak_month": prof["peak_month"],
            "trough_month": prof["trough_month"],
            "exposure_weight_by_month": list(map(float, w)),
            "reproduced": b1_ok,
        },
        "h_month_normalizations_annual_cpr": {
            k: list(map(float, v)) for k, v in normalizations.items()
        },
        "h_month_exposure_weighted_mean": {
            k: float(np.dot(w, v)) for k, v in normalizations.items()
        },
        "legs_run": legs,
        "placebo_permutation": perm_legs,
        "placebo_rotation": rot_legs,
        "placebo_jensen_flat": jensen_leg,
        "placebo_summary": placebo_summary,
        "decomposition": decomposition,
        "timing_criterion": {
            "frozen_rule": "U2(first diffs) < 1 AND detrended lag-0 r > 0",
            "scored_object": "central p_q=6.5 run (production Path B object)",
            "n_months": THEIL_N_MONTHS,
            "by_leg": {n: legs[n]["central"]["timing"] for n in normalizations},
            "by_leg_null_pq0": {n: legs[n]["null"]["timing"]
                                for n in normalizations},
            "seasonal_legs_pass": seasonal_timing_pass,
            "null_leg_clears_frozen_rule": null_leg_clears,
            "rule_has_discriminating_power": rule_has_power,
            "rule_defeated_by": rule_defeated_by,
            "verdict": verdict,
            "verdict_note": (
                "seasonal_legs_pass records whether the frozen rule is MET AS "
                "WRITTEN; verdict records whether that pass is EVIDENCE. They "
                "differ here, and the difference is the finding: the rule is "
                "cleared by wrong-month rotations, by scrambled calendars, and "
                "by the p_q=0 (beta1=0) null, so clearing it cannot evidence "
                "the lock-in mechanism."),
            "margin_caveat": (
                "The frozen rule is a strict inequality and both seasonal legs "
                "clear it by very little: U2 falls below 1 by 0.005 "
                "(shape_only) and 0.010 (prereg_4.5), and the detrended lag-0 "
                "correlations are +0.016 and +0.070 on n=42, i.e. |t| of 0.10 "
                "and 0.44 against zero. The criterion is met as written and is "
                "reported as met; it is NOT evidence of a substantively "
                "identified monthly timing channel, and must not be quoted as "
                "one. What the seasonal floor demonstrably does is flip the "
                "SIGN of the detrended lag-0 correlation (flat_4.0 -0.203 -> "
                "shape_only +0.016) and cut U1(detrended) 0.980 -> 0.878; the "
                "level move alone does neither (flat_4.5 -0.255, 0.986). "
                "SUPERSEDING NOTE (hardening revision): even that residual "
                "claim does not survive. See placebo_summary — wrong-month "
                "rotations and scrambled calendars clear the same rule, and "
                "the p_q=0 null clears it too, so the sign flip is not "
                "attributable to calendar timing either."
            ),
            "empirical_series_caveat": (
                "The empirical CPR benchmark is the SOMA back-out and is very "
                "coarse over this window: four of the 42 months are exactly "
                "0.000 (2022-06, 2023-02, 2024-04, 2025-09) and three exceed "
                "9% (2023-03 9.34, 2024-05 12.59, 2025-10 14.01), against a "
                "mean of 5.52 and sd 2.83. Any monthly-timing statistic scored "
                "against it inherits that lumpiness, which is a further reason "
                "not to over-read a thin U2/correlation margin."
            ),
        },
        "theil_baseline_cross_check": theil_baseline_check,
        "theil_baseline_pass": theil_baseline_pass,
        "parity_gates": gate_report,
        "parity_gates_all_pass": parity_pass,
        "parity_gates_bitwise": bitwise_pass,
        "month_sequence_self_check_pass": wiring_pass,
        "unchanged_parameters_attestation": (
            "Only literature_hazard.INVOLUNTARY_CPR_ANNUAL is set, per calendar "
            "month, and restored to 0.04 in a finally. beta1 (rothstein_beta1 of "
            "p_q), the Rothstein elasticity, hazard_coefficients, FLOOR_MODE, the "
            "loan sample, N_LOANS, RNG_SEED, the ('US','Danish') regime tuple, "
            "QT_START/QT_END and the raw-basis scorer are production and are not "
            "touched by any leg. Demonstrated, not asserted: the flat_4.0 control "
            "re-run in THIS session reproduces the committed production anchors."
        ),
        "level_confound_note": (
            "committed constant-floor sweep: 4.0%% -> 4.5%% moves the marginal "
            f"{anchor['lockin_marginal_b']:.4f}B -> "
            f"{sweep45['lockin_marginal_b']:.4f}B with no seasonality at all; "
            "the pre-registered 4.5%%-mean seasonal leg therefore confounds "
            "level with shape, and shape_only (mean pinned at 4.0%%) is the "
            "leg that isolates the B2 mechanism. Both are reported."
        ),
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    # Mirror to the session scratchpad only if it already exists: on a clean
    # checkout that path is absent, and mkdir(parents=True) would silently
    # create stray directories under /private/tmp on an unrelated machine.
    _targets = [RESULTS_JSON]
    if SCRATCH_JSON.parent.is_dir():
        _targets.append(SCRATCH_JSON)
    for target in _targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w") as f:
            json.dump(payload, f, indent=2, default=float)
            f.write("\n")

    if not (parity_pass and wiring_pass):
        raise SystemExit(
            "PARITY/WIRING GATE FAILED — the time-varying floor driver does "
            "not reproduce the constant-floor path in this session. Every "
            "seasonal number in this artifact is VOID. Do not tune to match."
        )
    print(f"\nPARITY_PASS ({'BITWISE' if bitwise_pass else 'tolerance'}). "
          f"Verdict {verdict}. Results saved to {RESULTS_JSON} and {SCRATCH_JSON}")


if __name__ == "__main__":
    main()
