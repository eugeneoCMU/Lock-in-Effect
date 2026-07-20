#!/usr/bin/env python3
"""
B3: re-score monthly TIMING for the four floor legs against the empirical
CPR path, using ONLY the committed scoring implementations, and render the
pre-committed verdict.

SPEC (fixed ex ante; nothing below was chosen after seeing a number)
--------------------------------------------------------------------

PURPOSE
  The B2 run (hazard/seasonal_floor_timing.py) produced four simulated
  monthly CPR paths over the active QT window (2022-06..2025-11, n = 42)
  by driving the involuntary floor with a calendar profile.  B3 does no
  new simulation.  It re-scores the four ALREADY-COMMITTED central
  (p_q = 6.5) paths against the empirical monthly CPR and applies one
  frozen decision rule, once per leg.

SCORERS — REUSED, NOT REWRITTEN
  figures/make_theil_data.py is imported as a module and its functions are
  called directly:
      theil_u1        (:231)  RMSE / (RMS(sim) + RMS(emp))
      theil_u2_diffs  (:237)  RMS(d_sim - d_emp) / RMS(d_emp)
      detrend         (:261)  residual of a degree-1 polyfit on t = 0..n-1
      estimator_block (:267)  the committed {u1_levels, u2_diffs,
                              u1_detrended, decomp} bundle
  hazard/macro.py cpr_cross_correlation (:131) supplies the CCF, called at
  max_lag = 6 with the committed argument order (empirical, predicted).
  No scoring arithmetic is defined in this file except the Pearson
  correlation of the two detrended series, which is numpy's corrcoef
  applied to make_theil_data.detrend output — the same composition B2 used.

EMPIRICAL SERIES — TWO, AND THE DISTINCTION IS LOAD-BEARING
  PRIMARY (parity-gated, comparable to figures/theil_data.json):
      the SOMA back-out Empirical_CPR_Pct, as built by
      macro.build_empirical_metrics + qt_active_frame.  This is the series
      the committed Path B triple was scored on, so it is the ONLY series
      on which the parity gate can bind.  It is carried in the B2 artifact
      (legs_run.<leg>.central.empirical_cpr_pct), identical across legs,
      so no network call is needed and none is made.
  SECONDARY (robustness, NOT adjudicated):
      the panel-derived empirical CPR from the B0 artifact
      (b0_variance_decomposition.json series[].cpr_annual, a decimal
      fraction, x100 to percent), restricted to the same 42 QT months.
      This is a DIFFERENT object — a cohort-panel prepayment back-out, not
      a SOMA rolloff back-out — and the paper's committed timing numbers
      are not defined against it.  It is scored to show whether the verdict
      is an artifact of the benchmark choice.  The pre-committed rule is
      adjudicated on the PRIMARY series only; the secondary is disclosed.

PARITY GATE (must hold or the run is void)
  Scoring the flat-4.0 (production floor) central path on the primary
  empirical must reproduce the committed Path B triple in
  figures/theil_data.json: u1_levels 0.2653, u2_diffs 1.0029,
  u1_detrended 0.9797.  Tolerance 1e-3 (the committed file stores four
  decimals).  Diffs are reported, not just the pass flag.

FROZEN DECISION RULE (one rule, evaluated once per leg, primary series)
      PASS  iff  u2_diffs < 1.0  AND  detrended lag-0 correlation > 0.0
      else  CONCEDE (levels-only)
  No variant of the rule is computed for adjudication.  No spec search.
  An adverse result is reportable as-is and is not to be softened.

B4 TRIGGER (declared before execution)
  B4 — a single pre-registered settlement-lag kernel — is authorized ONLY
  if a seasonal leg NEARLY clears: u2_diffs within 0.02 of 1.0 with a
  positive detrended correlation, or u2_diffs < 1 with a detrended
  correlation just barely negative.  If a seasonal leg CLEARS outright the
  trigger is not met and B4 is not run.  One kernel, one run, no retries.

MARGIN DISCLOSURE (pre-committed, not a post-hoc hedge)
  The rule is a pair of strict inequalities on n = 42 / n_diffs = 41.  A
  pass whose detrended correlation is statistically indistinguishable from
  zero is reported WITH its t-statistic and two-sided p-value against 40
  d.f., and is not to be quoted as a monthly-timing credential.  The
  within-run DIRECTION of movement (flat -> seasonal) is the comparison
  that carries information, because it differences out the benchmark.

FREQUENCY BAND (pre-committed reporting requirement)
  Any surviving timing claim is attributed to a band by decomposing each
  detrended path into (a) the 12-month calendar harmonic (regression on
  sin/cos of 2*pi*m/12, m = calendar month) and (b) the residual.  The
  band that carries the correlation is reported.

OUTPUTS
  hazard/data/b3_timing_scores.json  and the scratchpad copy (identical
  payload).  verdict = TIMING_EARNED | CONCEDE_LEVELS_ONLY.

B1 BASIS — CORRECTED (hardening revision)
  B1's twelve-cell calendar profile is estimated on the FULL cohort-month
  panel (7,756 cohort-months, $74.21T exposure, mean annual CPR 4.187%),
  NOT on the QT window.  An earlier revision of this docstring said
  "in-window"; that was wrong.  The QT-restricted variant is a DIFFERENT
  object (7,452 cohort-months, $72.49T, mean 4.1132%, with different
  Mar/Apr/May/Dec cells).  Both bases are computed by B2 and mirrored into
  this artifact under b1_provenance.bases.  Every run rests on full_panel.
  Which basis a quoted number uses must be stated.

REFUTING DIAGNOSTICS (hardening revision; COMPUTED, not asserted)
  The frozen rule below is MET AS WRITTEN by both seasonal legs, and the
  pass is nevertheless not real.  Every reason is computed here and written
  to the artifact as a first-class field, so no reader has to take the
  concession on trust:
    permutation_null       scrambled calendar orders of the SAME twelve
                           floor values — marginal, U2, r, pass count, and
                           the share of the effect RETAINED under scrambling
    rotation_placebo       all twelve rotations, both seasonal base legs —
                           placebo pass rate, and whether a WRONG-month
                           rotation beats the true profile on U2
    artifact_concentration the benchmark's exact-zero months, their share of
                           RMS(d_emp)^2 and of each leg's U2 numerator, and
                           the rescore on a REPAIRED benchmark
    leave_one_out          all 42 single-month deletions per leg
    null_leg_scores        the p_q = 0 (beta1 = 0) legs — a null that clears
                           the rule is the decisive diagnostic
    level_shape_interaction the additive residual in $B, pp, on r, path-wise
    jensen_equivalent_flat the convexity-matched flat level and its measured
                           marginal — level leakage vs floor dispersion
    frequency_band_summary simulated vs empirical 12-month harmonic share

  HEADLINE CORRECTION carried by these fields: the "shape effect" on the
  marginal is NOT seasonality.  Scrambling the calendar retains most of it,
  so calendar ORDER is nearly irrelevant.  The mechanism is FLOOR_MODE='max'
  (hazard/config.py): max(h_floor, h_vol) truncates the floor away in low
  months and lets it bind in high ones, so ANY dispersion in the floor
  raises the effective hazard one-sidedly.  Report it as a FLOOR-DISPERSION
  / functional-form finding, never as "seasonality moves the marginal".

CARRIED CAVEATS (from B1/B2; still binding on any write-up)
  1. B1 is circular: gap <= -150bp captures 98.2% of QT exposure, so the
     deep-OOM filter is near the identity map and the estimated profile is
     essentially the aggregate CPR seasonal, itself lock-in-suppressed.
     The floor is not identified off a lock-in-free population.
  2. The clean 2017-2019 out-of-window leg cannot rescue it (335 deep-OOM
     cohort-months, literally zero prepaid_upb in some calendar cells).
  3. The seasonal share inverts between windows (full-panel R2 ~ 0.011 vs
     QT 0.755); B1 inherits that instability.
  4. The committed Path A VOLUNTARY seasonality peaks Mar/Oct/Sep while
     this INVOLUNTARY profile peaks Jun.  Different objects, but the
     tension must be stated wherever the seasonal floor is quoted.
  5. The primary empirical benchmark is lumpy: four exact 0.000 months and
     three months above 9% against mean 5.52 / sd 2.83.  Every monthly
     statistic here inherits that.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "figures"))
sys.path.insert(0, str(ROOT / "hazard"))

import make_theil_data as MTD  # noqa: E402  (committed scorers)
from macro import cpr_cross_correlation  # noqa: E402  (committed CCF)

B2_RESULTS = ROOT / "hazard" / "data" / "seasonal_floor_timing_results.json"
COMMITTED_THEIL = ROOT / "figures" / "theil_data.json"
SCRATCH = Path(
    "/private/tmp/claude-501/-Users-eugene-somthing-Lock-In-effect-Lock-in-Effect"
    "/dc42b60e-9f6a-4d3c-9fcb-f964562227af/scratchpad"
)
# Read the COMMITTED copy, not the session scratchpad: the scratchpad is
# session-scoped and gets garbage-collected, so keying off it made this module
# unrunnable from a clean checkout. The scratchpad remains a fallback only.
_B0_REPO = ROOT / "hazard" / "data" / "b0_variance_decomposition.json"
B0_ARTIFACT = _B0_REPO if _B0_REPO.is_file() else SCRATCH / "b0_variance_decomposition.json"
OUT_REPO = ROOT / "hazard" / "data" / "b3_timing_scores.json"
OUT_SCRATCH = SCRATCH / "b3_timing_scores.json"

LEGS = ["flat_4.0", "flat_4.5", "shape_only", "prereg_4.5"]
SEASONAL_LEGS = ["shape_only", "prereg_4.5"]
CONTROL_LEG = "flat_4.0"
MAX_LAG = 6
PARITY_KEYS = ("u1_levels", "u2_diffs", "u1_detrended")
# The committed file stores FULL double precision, not the four decimals an
# earlier revision assumed, so the gate binds at 1e-9 rather than 1e-3.
PARITY_TOL = 1e-9
PARITY_TOL_ROUNDED_4DP = 1e-3   # legacy display tolerance, reported only
NEAR_MISS_U2_BAND = 0.02
N_PERMUTATION_MIN = 14


def load_committed_path_b() -> dict:
    """READ the committed Path B triple from figures/theil_data.json.

    This used to be a hardcoded literal in this file, which meant the parity
    gate compared the scorer against a transcription of the committed file
    rather than against the file itself — a gate that could not detect the
    committed artifact changing underneath it. It now reads the artifact.
    """
    if not COMMITTED_THEIL.exists():
        raise FileNotFoundError(
            f"parity gate cannot run: {COMMITTED_THEIL} is missing")
    doc = json.loads(COMMITTED_THEIL.read_text())
    try:
        blk = doc["estimators"]["path_b"]
    except KeyError as exc:
        raise KeyError(
            f"{COMMITTED_THEIL} has no estimators.path_b block") from exc
    missing = [k for k in PARITY_KEYS if k not in blk]
    if missing:
        raise KeyError(f"{COMMITTED_THEIL} estimators.path_b lacks {missing}")
    return {k: float(blk[k]) for k in PARITY_KEYS}


def _t_and_p(r: float, n: int) -> tuple:
    """t-stat and two-sided p for a Pearson r on n observations."""
    dof = n - 2
    if abs(r) >= 1.0:
        return float("inf"), 0.0
    t = r * np.sqrt(dof / (1.0 - r * r))
    try:
        from scipy import stats
        p = float(2.0 * stats.t.sf(abs(t), dof))
    except Exception:
        # normal approximation; only used if scipy is absent
        from math import erfc, sqrt
        p = float(erfc(abs(t) / sqrt(2.0)))
    return float(t), p


def score_leg(sim: np.ndarray, emp: np.ndarray, periods: list) -> dict:
    """All timing statistics for one (sim, emp) pair, committed scorers."""
    blk = MTD.estimator_block(sim, emp)          # committed bundle
    ds, de = MTD.detrend(sim), MTD.detrend(emp)  # committed detrend
    r_det = float(np.corrcoef(ds, de)[0, 1])
    t, p = _t_and_p(r_det, len(sim))
    idx = pd.PeriodIndex(periods, freq="M").to_timestamp(how="end")
    ccf = cpr_cross_correlation(pd.Series(emp, index=idx),
                                pd.Series(sim, index=idx), max_lag=MAX_LAG)
    ccf = {int(k): float(v) for k, v in ccf.items()}
    peak_lag = max(ccf, key=lambda k: abs(ccf[k]))
    return {
        "n": int(len(sim)),
        "n_diffs": int(len(sim) - 1),
        "u1_levels": float(blk["u1_levels"]),
        "u2_diffs": float(blk["u2_diffs"]),
        "u1_detrended": float(blk["u1_detrended"]),
        "detrended_lag0_r": r_det,
        "detrended_lag0_t": t,
        "detrended_lag0_p_two_sided": p,
        "raw_lag0_r": float(np.corrcoef(sim, emp)[0, 1]),
        "ccf_lags_minus6_to_plus6": {str(k): ccf[k] for k in sorted(ccf)},
        "ccf_peak_lag": int(peak_lag),
        "ccf_peak_r": float(ccf[peak_lag]),
        "u2_lt_1": bool(blk["u2_diffs"] < 1.0),
        "detrended_r_positive": bool(r_det > 0.0),
        "verdict": ("PASS" if (blk["u2_diffs"] < 1.0 and r_det > 0.0)
                    else "CONCEDE"),
        "mse_decomp": blk["decomp"],
    }


def band_attribution(sim: np.ndarray, emp: np.ndarray,
                     periods: list) -> dict:
    """Split each detrended path into the 12-month calendar harmonic and
    the residual; report where the lag-0 correlation lives."""
    months = np.array([int(p.split("-")[1]) for p in periods], dtype=float)
    ang = 2.0 * np.pi * (months - 1.0) / 12.0
    X = np.column_stack([np.ones_like(ang), np.sin(ang), np.cos(ang)])

    def split(x):
        ds = MTD.detrend(x)
        coef, *_ = np.linalg.lstsq(X, ds, rcond=None)
        fit = X @ coef
        return fit, ds - fit

    s_h, s_r = split(sim)
    e_h, e_r = split(emp)
    tot = MTD.detrend(sim), MTD.detrend(emp)
    return {
        "harmonic_12m_r": float(np.corrcoef(s_h, e_h)[0, 1]),
        "residual_r": float(np.corrcoef(s_r, e_r)[0, 1]),
        "detrended_total_r": float(np.corrcoef(*tot)[0, 1]),
        "sim_var_share_in_12m_harmonic": float(
            np.var(s_h) / np.var(MTD.detrend(sim))),
        "emp_var_share_in_12m_harmonic": float(
            np.var(e_h) / np.var(MTD.detrend(emp))),
    }


# ==========================================================================
# REFUTING DIAGNOSTICS.  Each one is COMPUTED here and written to the
# artifact as a first-class field.  They exist because the frozen rule is
# MET AS WRITTEN by both seasonal legs and the pass is nevertheless not
# real; a reader must be able to see every reason for that in the JSON
# without re-deriving anything.
# ==========================================================================

def _rule(u2: float, r: float) -> str:
    return "PASS" if (u2 < 1.0 and r > 0.0) else "CONCEDE"


def _u2_and_r(sim: np.ndarray, emp: np.ndarray) -> tuple:
    u2 = float(MTD.theil_u2_diffs(sim, emp))
    r = float(np.corrcoef(MTD.detrend(sim), MTD.detrend(emp))[0, 1])
    return u2, r


def artifact_concentration(sims: dict, emp: np.ndarray,
                           periods: list) -> dict:
    """The empirical benchmark's exact-zero months, and what they carry.

    The SOMA back-out has months of literally 0.000 CPR, each followed by a
    double-sized spike — a settlement/reporting artifact, not a prepayment
    collapse followed by a boom.  A zero at index i corrupts BOTH adjacent
    first differences, so a handful of months can dominate a U2 statistic
    built entirely out of first differences.  This quantifies that, then
    REPAIRS the benchmark by reallocating each post-zero spike evenly across
    its pair and re-scores every leg on the repaired series.
    """
    n = len(emp)
    zero_idx = [i for i in range(n) if emp[i] == 0.0]
    d_emp = np.diff(emp)
    # a zero at i touches diff i-1 (into it) and diff i (out of it)
    touched = sorted({j for i in zero_idx
                      for j in (i - 1, i) if 0 <= j < n - 1})
    denom = float(np.sum(d_emp ** 2))
    share_demp = float(np.sum(d_emp[touched] ** 2) / denom) if denom else 0.0

    per_leg_num = {}
    for lg, sim in sims.items():
        resid = np.diff(sim) - d_emp
        tot = float(np.sum(resid ** 2))
        per_leg_num[lg] = float(np.sum(resid[touched] ** 2) / tot) if tot else 0.0

    # --- repair: spread each (zero, spike) pair evenly over the two months
    repaired = emp.astype(float).copy()
    pairs = []
    for i in zero_idx:
        j = i + 1
        if j >= n:
            continue
        avg = (repaired[i] + repaired[j]) / 2.0
        pairs.append({"zero_month": periods[i], "spike_month": periods[j],
                      "zero_value": float(emp[i]),
                      "spike_value": float(emp[j]),
                      "each_after_repair": float(avg)})
        repaired[i] = repaired[j] = avg

    rescored = {}
    for lg, sim in sims.items():
        u2, r = _u2_and_r(sim, repaired)
        base_u2, base_r = _u2_and_r(sim, emp)
        rescored[lg] = {
            "u2_diffs_original": base_u2,
            "u2_diffs_repaired": u2,
            "detrended_lag0_r_original": base_r,
            "detrended_lag0_r_repaired": r,
            "verdict_original": _rule(base_u2, base_r),
            "verdict_repaired": _rule(u2, r),
            "flips_to_concede": bool(_rule(base_u2, base_r) == "PASS"
                                     and _rule(u2, r) == "CONCEDE"),
        }
    return {
        "exact_zero_months": [periods[i] for i in zero_idx],
        "n_exact_zero_months": len(zero_idx),
        "first_differences_touched": [f"{periods[j]}->{periods[j + 1]}"
                                      for j in touched],
        "n_first_differences_touched": len(touched),
        "n_first_differences_total": n - 1,
        "share_of_rms_d_emp_squared": share_demp,
        "share_of_u2_numerator_by_leg": per_leg_num,
        "repair_rule": ("each exact-zero month and the month after it are "
                        "both set to their mean, i.e. the post-zero spike is "
                        "reallocated evenly across the pair; total CPR over "
                        "the pair is conserved"),
        "repaired_pairs": pairs,
        "repaired_benchmark_values": list(map(float, repaired)),
        "rescore_on_repaired_benchmark": rescored,
        "n_legs_flipping_to_concede": sum(
            1 for v in rescored.values() if v["flips_to_concede"]),
    }


def leave_one_out(sims: dict, emp: np.ndarray, periods: list) -> dict:
    """Delete each of the 42 months in turn and re-apply the frozen rule."""
    out = {}
    for lg, sim in sims.items():
        flips, rows = [], {}
        base = _rule(*_u2_and_r(sim, emp))
        for j in range(len(emp)):
            keep = np.arange(len(emp)) != j
            u2, r = _u2_and_r(sim[keep], emp[keep])
            v = _rule(u2, r)
            rows[periods[j]] = {"u2_diffs": u2, "detrended_lag0_r": r,
                                "verdict": v}
            if base == "PASS" and v == "CONCEDE":
                flips.append(periods[j])
        out[lg] = {
            "verdict_full_sample": base,
            "n_deletions": len(emp),
            "n_flips_to_concede": len(flips),
            "months_whose_deletion_flips_to_concede": flips,
            "by_deleted_month": rows,
        }
    return out


def level_shape_interaction(sims: dict, emp: np.ndarray, b2: dict) -> dict:
    """Additive LEVEL+SHAPE residual, in $B, in pp, on r, and path-wise."""
    legs = b2["legs_run"]

    def marg(k):
        return legs[k]["lockin_marginal_b"]

    def pp(k):
        return legs[k]["lockin_marginal_share_pp"]

    def rdet(k):
        return float(np.corrcoef(MTD.detrend(sims[k]),
                                 MTD.detrend(emp))[0, 1])

    def triple(f):
        lv = f("flat_4.5") - f("flat_4.0")
        sh = f("shape_only") - f("flat_4.0")
        tt = f("prereg_4.5") - f("flat_4.0")
        return {"level": lv, "shape": sh, "total": tt,
                "interaction": tt - lv - sh}

    # path-wise non-additivity on the simulated monthly CPR paths
    lv_p = sims["flat_4.5"] - sims["flat_4.0"]
    sh_p = sims["shape_only"] - sims["flat_4.0"]
    tt_p = sims["prereg_4.5"] - sims["flat_4.0"]
    res_p = tt_p - lv_p - sh_p
    mean_abs_resid = float(np.mean(np.abs(res_p)))
    mean_abs_total = float(np.mean(np.abs(tt_p)))

    return {
        "basis": "all deltas vs the flat_4.0 production control",
        "marginal_b": triple(marg),
        "marginal_share_pp": triple(pp),
        "detrended_lag0_r": triple(rdet),
        "path_wise_monthly_cpr_pp": {
            "mean_abs_interaction_residual": mean_abs_resid,
            "mean_abs_total_movement": mean_abs_total,
            "interaction_share_of_total_movement": (
                mean_abs_resid / mean_abs_total if mean_abs_total else
                float("nan")),
            "max_abs_interaction_residual": float(np.max(np.abs(res_p))),
        },
        "note": ("LEVEL and SHAPE do not separate. Any additive "
                 "level/shape decomposition of this floor MUST carry its "
                 "interaction residual; quoting LEVEL and SHAPE without it "
                 "misstates both."),
    }


def null_leg_scores(b2: dict, emp: np.ndarray, periods: list) -> dict:
    """Score the p_q = 0 (beta1 = 0) legs. THE DECISIVE DIAGNOSTIC.

    p_q = 0 means rothstein_beta1(0) = 0, i.e. NO lock-in rate elasticity at
    all.  If such a leg clears the frozen timing rule, then clearing the rule
    cannot be evidence of the lock-in mechanism, because a model with the
    mechanism switched off clears it too.
    """
    legs = b2["legs_run"]
    out = {}
    for lg in LEGS:
        sim = np.array(legs[lg]["null"]["path_hazard_cpr_pct"], dtype=float)
        u2, r = _u2_and_r(sim, emp)
        t, p = _t_and_p(r, len(sim))
        out[lg] = {
            "p_q_shock_pct": legs[lg]["null"]["p_q_shock_pct"],
            "beta1": legs[lg]["null"]["beta1"],
            "u2_diffs": u2,
            "detrended_lag0_r": r,
            "detrended_lag0_t": t,
            "detrended_lag0_p_two_sided": p,
            "u1_levels": float(MTD.theil_u1(sim, emp)),
            "verdict": _rule(u2, r),
        }
    clearing = [k for k, v in out.items() if v["verdict"] == "PASS"]
    return {
        "by_leg": out,
        "legs_clearing_frozen_rule": clearing,
        "n_clearing": len(clearing),
        "beta1_is_zero_on_every_null_leg": all(
            abs(v["beta1"]) < 1e-12 for v in out.values()),
        "interpretation": (
            "A beta1 = 0 null clearing the frozen rule is decisive: the rule "
            "cannot evidence the lock-in mechanism, because a specification "
            "with the mechanism removed satisfies it."
            if clearing else
            "No p_q=0 null leg clears the rule."),
    }


def permutation_null(b2: dict, emp: np.ndarray, periods: list) -> dict:
    """Re-score the B2 permutation family with the COMMITTED scorers."""
    perms = b2.get("placebo_permutation", {})
    if not perms:
        raise RuntimeError(
            "B2 artifact carries no placebo_permutation family; re-run "
            "hazard/seasonal_floor_timing.py before B3.")
    if len(perms) < N_PERMUTATION_MIN:
        raise RuntimeError(
            f"permutation family has {len(perms)} members, spec requires "
            f">= {N_PERMUTATION_MIN}")
    legs = b2["legs_run"]
    m_flat40 = legs["flat_4.0"]["lockin_marginal_b"]
    m_shape = legs["shape_only"]["lockin_marginal_b"]
    true_effect = m_shape - m_flat40
    shape_u2, _ = _u2_and_r(
        np.array(legs["shape_only"]["central"]["path_hazard_cpr_pct"],
                 dtype=float), emp)

    rows, retained, u2s = {}, [], []
    for tag, v in sorted(perms.items()):
        sim = np.array(v["central_path_hazard_cpr_pct"], dtype=float)
        u2, r = _u2_and_r(sim, emp)
        eff = v["lockin_marginal_b"] - m_flat40
        rows[tag] = {
            "order_month_to_source_slot": v["order_month_to_source_slot"],
            "values_multiset_preserved": v["values_multiset_preserved"],
            "lockin_marginal_b": v["lockin_marginal_b"],
            "lockin_marginal_share_pp": v["lockin_marginal_share_pp"],
            "effect_vs_flat40_b": eff,
            "share_of_true_shape_effect_retained": (
                eff / true_effect if true_effect else float("nan")),
            "u2_diffs": u2,
            "detrended_lag0_r": r,
            "verdict": _rule(u2, r),
        }
        retained.append(rows[tag]["share_of_true_shape_effect_retained"])
        u2s.append(u2)
    clearing = [k for k, v in rows.items() if v["verdict"] == "PASS"]
    retained = np.array(retained, dtype=float)
    return {
        "seed": b2["placebo_summary"]["permutation"]["seed"],
        "n_permutations": len(rows),
        "design": ("the SAME twelve shape_only floor values assigned to "
                   "SCRAMBLED calendar months; the multiset of values is "
                   "preserved exactly, only the calendar assignment changes"),
        "true_shape_effect_b": float(true_effect),
        "shape_only_u2_diffs": shape_u2,
        "by_permutation": rows,
        "share_of_effect_retained_mean": float(retained.mean()),
        "share_of_effect_retained_min": float(retained.min()),
        "share_of_effect_retained_max": float(retained.max()),
        "n_clearing_frozen_rule": len(clearing),
        "permutations_clearing_frozen_rule": clearing,
        "best_permutation_u2": float(min(u2s)),
        "n_permutations_beating_shape_only_u2": int(
            sum(1 for u in u2s if u < shape_u2)),
        "interpretation": (
            "Calendar ORDER is nearly irrelevant to the marginal: scrambling "
            "the months retains most of the effect. What moves the marginal "
            "is DISPERSION in the floor interacting with FLOOR_MODE='max' "
            "(hazard/config.py) — max(h_floor, h_vol) truncates the floor "
            "away in low months and lets it bind in high ones, a Jensen-type "
            "one-sided effect. The finding is FLOOR DISPERSION / functional "
            "form, NOT seasonality."),
    }


def rotation_placebo(b2: dict, emp: np.ndarray) -> dict:
    """Re-score the B2 rotation family with the COMMITTED scorers."""
    rots = b2.get("placebo_rotation", {})
    if not rots:
        raise RuntimeError(
            "B2 artifact carries no placebo_rotation family; re-run "
            "hazard/seasonal_floor_timing.py before B3.")
    legs = b2["legs_run"]
    out = {}
    for base, family in rots.items():
        true_sim = np.array(legs[base]["central"]["path_hazard_cpr_pct"],
                            dtype=float)
        true_u2, true_r = _u2_and_r(true_sim, emp)
        rows = {}
        for tag, v in sorted(family.items()):
            sim = np.array(v["central_path_hazard_cpr_pct"], dtype=float)
            u2, r = _u2_and_r(sim, emp)
            rows[tag] = {"shift_months": v["shift_months"], "u2_diffs": u2,
                         "detrended_lag0_r": r, "verdict": _rule(u2, r),
                         "beats_true_profile_on_u2": bool(u2 < true_u2)}
        passing = [k for k, v in rows.items() if v["verdict"] == "PASS"]
        # rot00 IS the true profile. Counting it as a placebo would inflate
        # the placebo size by one, so it is excluded from every rate below
        # and retained only as a reproduction check.
        wrong = {k: v for k, v in rows.items() if v["shift_months"] != 0}
        wrong_passing = [k for k, v in wrong.items() if v["verdict"] == "PASS"]
        beating = {k: v["u2_diffs"] for k, v in wrong.items()
                   if v["beats_true_profile_on_u2"]}
        out[base] = {
            "true_profile_u2_diffs": true_u2,
            "true_profile_detrended_lag0_r": true_r,
            "identity_rot00_reproduces_true_leg": bool(
                abs(rows["rot00"]["u2_diffs"] - true_u2) <= 1e-12),
            "n_rotations": len(rows),
            "n_wrong_month_rotations": len(wrong),
            "n_passing_frozen_rule_incl_identity": len(passing),
            "rotations_passing_incl_identity": passing,
            "n_wrong_month_rotations_passing": len(wrong_passing),
            "wrong_month_rotations_passing": wrong_passing,
            "placebo_pass_rate_wrong_month_only": (
                len(wrong_passing) / len(wrong)),
            "wrong_month_rotations_beating_true_u2": beating,
            "any_wrong_rotation_beats_true_u2": bool(beating),
            "count_note": ("rot00 is the identity, i.e. the true profile "
                           "itself; excluded from the placebo pass rate."),
            "by_rotation": rows,
        }
    return {
        "design": ("h_rot_k[m] = h[(m-k) mod 12] — the true calendar profile "
                   "moved to the WRONG months, amplitude and dispersion held "
                   "exactly; k=0 is the identity and is an internal "
                   "reproduction check"),
        "by_base_leg": out,
        "interpretation": (
            "A timing rule that wrong-month rotations clear has no power to "
            "detect timing. The pass rate across rotations is the placebo "
            "size of the frozen rule."),
    }


def jensen_diagnostic(b2: dict, emp: np.ndarray) -> dict:
    """Level leakage vs floor dispersion, from the B2 Jensen-equivalent leg."""
    j = b2.get("placebo_jensen_flat")
    if not j:
        raise RuntimeError(
            "B2 artifact carries no placebo_jensen_flat leg; re-run "
            "hazard/seasonal_floor_timing.py before B3.")
    legs = b2["legs_run"]
    m40 = legs["flat_4.0"]["lockin_marginal_b"]
    true_effect = legs["shape_only"]["lockin_marginal_b"] - m40
    eff = j["lockin_marginal_b"] - m40
    sim = np.array(j["central_path_hazard_cpr_pct"], dtype=float)
    u2, r = _u2_and_r(sim, emp)
    return {
        "definition": ("the flat annual CPR whose monthly hazard equals the "
                       "QT-calendar-frequency-weighted mean of the twelve "
                       "seasonal monthly hazards; reproduces the convexity "
                       "of cpr_annual_to_monthly_hazard with ZERO dispersion"),
        "flat_annual_cpr": j["flat_annual_cpr"],
        "flat_annual_cpr_pct": j["flat_annual_cpr"] * 100.0,
        "alt_exposure_weighted_flat_annual_cpr_pct":
            j["alt_exposure_weighted_flat_annual_cpr"] * 100.0,
        "alt_uniform_weighted_flat_annual_cpr_pct":
            j["alt_uniform_weighted_flat_annual_cpr"] * 100.0,
        "production_flat_annual_cpr_pct": 4.0,
        "measured_marginal_b": j["lockin_marginal_b"],
        "measured_marginal_share_pp": j["lockin_marginal_share_pp"],
        "flat40_marginal_b": m40,
        "true_shape_effect_b": float(true_effect),
        "level_leakage_b": float(eff),
        "level_leakage_share_of_shape_effect": (
            float(eff / true_effect) if true_effect else float("nan")),
        "floor_dispersion_share_of_shape_effect": (
            float(1.0 - eff / true_effect) if true_effect else float("nan")),
        "u2_diffs": u2,
        "detrended_lag0_r": r,
        "interpretation": (
            "The convexity-matched flat level accounts for only a small part "
            "of the shape effect. The remainder is FLOOR DISPERSION under the "
            "max() rule, not calendar timing."),
    }


def frequency_band_summary(bands: dict) -> dict:
    """Where the simulated calendar structure lives vs where the benchmark's
    variance actually is."""
    emp_share = float(np.mean([b["emp_var_share_in_12m_harmonic"]
                               for b in bands.values()]))
    return {
        "empirical_detrended_variance_share_in_12m_harmonic": emp_share,
        "simulated_detrended_variance_share_in_12m_harmonic": {
            lg: b["sim_var_share_in_12m_harmonic"] for lg, b in bands.items()},
        "harmonic_r_by_leg": {lg: b["harmonic_12m_r"]
                              for lg, b in bands.items()},
        "residual_r_by_leg": {lg: b["residual_r"] for lg, b in bands.items()},
        "interpretation": (
            "The seasonal legs push the large majority of SIMULATED detrended "
            "variance into the 12-month calendar harmonic, while the primary "
            "empirical benchmark carries a very small share of its own "
            "detrended variance there. The model manufactures calendar "
            "structure the benchmark does not have and cannot adjudicate."),
    }


def main() -> None:
    b2 = json.loads(B2_RESULTS.read_text())
    legs = b2["legs_run"]

    periods = legs[CONTROL_LEG]["central"]["path_periods"]
    emp_primary = np.array(legs[CONTROL_LEG]["central"]["empirical_cpr_pct"],
                           dtype=float)
    # the empirical benchmark must be identical across legs
    for lg in LEGS:
        other = np.array(legs[lg]["central"]["empirical_cpr_pct"], dtype=float)
        if not np.array_equal(other, emp_primary):
            print(f"ABORT: empirical benchmark differs on leg {lg}")
            sys.exit(1)
        if legs[lg]["central"]["path_periods"] != periods:
            print(f"ABORT: period index differs on leg {lg}")
            sys.exit(1)

    # --- secondary empirical: B0 panel-derived CPR on the same 42 months
    b0 = json.loads(B0_ARTIFACT.read_text())
    b0_map = {r["period"]: float(r["cpr_annual"]) * 100.0
              for r in b0["series"]}
    # B0 ends 2025-09; the QT window runs to 2025-11.  The secondary leg is
    # scored on the OVERLAP only and its shorter n is disclosed.  It is not
    # adjudicated, so the truncation cannot move the verdict.
    sec_pos = [i for i, p in enumerate(periods) if p in b0_map]
    sec_periods = [periods[i] for i in sec_pos]
    sec_missing = [p for p in periods if p not in b0_map]
    emp_secondary = (None if len(sec_pos) < 24 else
                     np.array([b0_map[p] for p in sec_periods], dtype=float))

    sims = {lg: np.array(legs[lg]["central"]["path_hazard_cpr_pct"],
                         dtype=float) for lg in LEGS}

    scores_primary = {lg: score_leg(sims[lg], emp_primary, periods)
                      for lg in LEGS}
    scores_secondary = ({} if emp_secondary is None else
                        {lg: score_leg(sims[lg][sec_pos], emp_secondary,
                                       sec_periods)
                         for lg in LEGS})
    bands = {lg: band_attribution(sims[lg], emp_primary, periods)
             for lg in LEGS}
    bands_secondary = ({} if emp_secondary is None else
                       {lg: band_attribution(sims[lg][sec_pos], emp_secondary,
                                             sec_periods) for lg in LEGS})

    # --- PARITY GATE (values READ from the committed artifact) -------------
    path_b_committed = load_committed_path_b()
    ctrl = scores_primary[CONTROL_LEG]
    parity = {}
    for k, want in path_b_committed.items():
        got = ctrl[k]
        parity[k] = {
            "got": got,
            "want": want,
            "want_source": f"{COMMITTED_THEIL.name}:estimators.path_b.{k}",
            "want_rounded_4dp": round(want, 4),
            "abs_diff": abs(got - want),
            "pass": bool(abs(got - want) <= PARITY_TOL),
            "pass_at_legacy_4dp_tol": bool(
                abs(got - round(want, 4)) <= PARITY_TOL_ROUNDED_4DP),
        }
    parity_pass = all(v["pass"] for v in parity.values())
    print("\n=== PARITY GATE: flat-4.0 central vs committed Path B ===")
    print(f"  values READ from {COMMITTED_THEIL}")
    for k, v in parity.items():
        print(f"  {k:<14} got {v['got']:.12f}  want {v['want']:.12f}  "
              f"|diff| {v['abs_diff']:.2e}  {'PASS' if v['pass'] else 'FAIL'}"
              f"   (4dp literal {v['want_rounded_4dp']:.4f}: "
              f"{'PASS' if v['pass_at_legacy_4dp_tol'] else 'FAIL'})")
    if not parity_pass:
        print("PARITY GATE FAILED — scorer is not the committed one; run void.")
        sys.exit(1)

    # --- verdicts ---------------------------------------------------------
    print("\n=== FROZEN RULE: U2(diffs) < 1 AND detrended lag-0 r > 0 ===")
    for lg in LEGS:
        s = scores_primary[lg]
        print(f"  {lg:<12} U2 {s['u2_diffs']:.6f}  r_det "
              f"{s['detrended_lag0_r']:+.6f} (t {s['detrended_lag0_t']:+.2f}, "
              f"p {s['detrended_lag0_p_two_sided']:.3f})  U1lvl "
              f"{s['u1_levels']:.4f}  U1det {s['u1_detrended']:.4f}  "
              f"peak lag {s['ccf_peak_lag']:+d} (r {s['ccf_peak_r']:+.4f})  "
              f"=> {s['verdict']}")

    seasonal_pass = [lg for lg in SEASONAL_LEGS
                     if scores_primary[lg]["verdict"] == "PASS"]

    # --- REFUTING DIAGNOSTICS --------------------------------------------
    print("\n=== REFUTING DIAGNOSTICS ===")
    diag_perm = permutation_null(b2, emp_primary, periods)
    diag_rot = rotation_placebo(b2, emp_primary)
    diag_art = artifact_concentration(sims, emp_primary, periods)
    diag_loo = leave_one_out(sims, emp_primary, periods)
    diag_null = null_leg_scores(b2, emp_primary, periods)
    diag_lsi = level_shape_interaction(sims, emp_primary, b2)
    diag_jensen = jensen_diagnostic(b2, emp_primary)
    diag_freq = frequency_band_summary(bands)

    print(f"  (a) benchmark artifacts: {diag_art['n_exact_zero_months']} "
          f"exact-zero months touch "
          f"{diag_art['n_first_differences_touched']}/"
          f"{diag_art['n_first_differences_total']} first differences, "
          f"{diag_art['share_of_rms_d_emp_squared']:.4f} of RMS(d_emp)^2; "
          f"repairing flips {diag_art['n_legs_flipping_to_concede']}/"
          f"{len(LEGS)} legs to CONCEDE")
    for base, rs in diag_rot["by_base_leg"].items():
        print(f"  (b) rotation placebo {base:<11} "
              f"{rs['n_wrong_month_rotations_passing']}/"
              f"{rs['n_wrong_month_rotations']} WRONG-month rotations pass "
              f"(identity excluded, reproduces true leg: "
              f"{rs['identity_rot00_reproduces_true_leg']}); "
              f"wrong-month rotation beats true U2: "
              f"{rs['any_wrong_rotation_beats_true_u2']}")
    print(f"  (c) permutation null: {diag_perm['n_clearing_frozen_rule']}/"
          f"{diag_perm['n_permutations']} scrambled calendars clear the rule; "
          f"{diag_perm['n_permutations_beating_shape_only_u2']} beat "
          f"shape_only on U2; "
          f"{diag_perm['share_of_effect_retained_mean'] * 100:.1f}% of the "
          f"shape effect is RETAINED under scrambling")
    print(f"  (d) p_q=0 null legs clearing the rule: "
          f"{diag_null['legs_clearing_frozen_rule']}")
    for lg in SEASONAL_LEGS:
        s = scores_primary[lg]
        print(f"  (e) {lg:<11} r_det {s['detrended_lag0_r']:+.6f} "
              f"t {s['detrended_lag0_t']:+.2f} p "
              f"{s['detrended_lag0_p_two_sided']:.3f} "
              f"(2/sqrt(n) band +/-{2 / np.sqrt(len(periods)):.3f})")
    for lg in LEGS:
        v = diag_loo[lg]
        print(f"  (f) {lg:<11} leave-one-out flips to CONCEDE on "
              f"{v['n_flips_to_concede']}/{v['n_deletions']} deletions "
              f"{v['months_whose_deletion_flips_to_concede']}")
    print(f"  (g) 12m harmonic: empirical carries "
          f"{diag_freq['empirical_detrended_variance_share_in_12m_harmonic'] * 100:.1f}% "
          f"of its detrended variance there; simulated seasonal legs "
          + ", ".join(
              f"{lg} {diag_freq['simulated_detrended_variance_share_in_12m_harmonic'][lg] * 100:.1f}%"
              for lg in SEASONAL_LEGS))
    print(f"  (h) CCF peak lags: "
          + ", ".join(f"{lg} {scores_primary[lg]['ccf_peak_lag']:+d} "
                      f"(r {scores_primary[lg]['ccf_peak_r']:+.4f})"
                      for lg in LEGS))
    print(f"  interaction: level/shape additive residual is "
          f"{diag_lsi['path_wise_monthly_cpr_pp']['interaction_share_of_total_movement'] * 100:.2f}% "
          f"of total path movement")
    print(f"  Jensen-equivalent flat {diag_jensen['flat_annual_cpr_pct']:.4f}% "
          f"-> marginal {diag_jensen['measured_marginal_b']:.6f} B; level "
          f"leakage is "
          f"{diag_jensen['level_leakage_share_of_shape_effect'] * 100:.1f}% of "
          f"the shape effect, floor dispersion "
          f"{diag_jensen['floor_dispersion_share_of_shape_effect'] * 100:.1f}%")

    # --- ADJUDICATION -----------------------------------------------------
    # The frozen rule being MET AS WRITTEN and the pass being REAL are two
    # different questions. The first is scores_primary[...]["verdict"]. The
    # second is decided here, and it is decided by COMPUTED diagnostics, not
    # by judgement: if placebos, scrambles or a beta1=0 null clear the same
    # rule, then clearing it carries no information about timing.
    defeats = []
    if diag_null["n_clearing"] > 0:
        defeats.append(
            "(d) the p_q=0 (beta1=0) null clears the rule: legs "
            f"{diag_null['legs_clearing_frozen_rule']}")
    if any(v["n_wrong_month_rotations_passing"] > 0
           for v in diag_rot["by_base_leg"].values()):
        defeats.append(
            "(b) wrong-month calendar rotations clear the rule: "
            + "; ".join(
                f"{k} {v['n_wrong_month_rotations_passing']}/"
                f"{v['n_wrong_month_rotations']}"
                + (", and a wrong-month rotation BEATS the true profile on "
                   "U2" if v["any_wrong_rotation_beats_true_u2"] else "")
                for k, v in diag_rot["by_base_leg"].items()))
    if diag_perm["n_clearing_frozen_rule"] > 0:
        defeats.append(
            f"(c) {diag_perm['n_clearing_frozen_rule']} of "
            f"{diag_perm['n_permutations']} scrambled calendar orders clear "
            "the rule")
    if diag_art["n_legs_flipping_to_concede"] > 0:
        defeats.append(
            "(a) benchmark artifacts carry the pass: the "
            f"{diag_art['n_exact_zero_months']} exact-zero months carry "
            f"{diag_art['share_of_rms_d_emp_squared']:.4f} of RMS(d_emp)^2 "
            f"and repairing them flips "
            f"{diag_art['n_legs_flipping_to_concede']} leg(s) to CONCEDE")
    if any(diag_loo[lg]["n_flips_to_concede"] > 0 for lg in SEASONAL_LEGS):
        defeats.append(
            "(f) leave-one-out asymmetry: "
            + "; ".join(f"{lg} flips on {diag_loo[lg]['n_flips_to_concede']}/"
                        f"{diag_loo[lg]['n_deletions']}"
                        for lg in SEASONAL_LEGS))
    if all(scores_primary[lg]["detrended_lag0_p_two_sided"] >= 0.05
           for lg in SEASONAL_LEGS):
        defeats.append(
            "(e) the detrended correlations are statistically "
            "indistinguishable from zero on n=42")
    emp_h = diag_freq["empirical_detrended_variance_share_in_12m_harmonic"]
    if any(diag_freq["simulated_detrended_variance_share_in_12m_harmonic"][lg]
           > 4.0 * max(emp_h, 1e-12) for lg in SEASONAL_LEGS):
        defeats.append(
            "(g) frequency-band mismatch: the seasonal legs concentrate "
            "simulated detrended variance in the 12-month harmonic, where "
            f"the benchmark carries only {emp_h * 100:.1f}% of its own")
    if any(scores_primary[lg]["ccf_peak_lag"] >= MAX_LAG
           or scores_primary[lg]["ccf_peak_r"] < 0
           for lg in SEASONAL_LEGS):
        defeats.append(
            "(h) the CCF peak for the seasonal legs sits on the window "
            "boundary and/or is negative, so it is non-interpretable")

    rule_has_power = not defeats
    rule_met_as_written = bool(seasonal_pass)
    verdict = ("TIMING_EARNED" if (rule_met_as_written and rule_has_power)
               else "CONCEDE_LEVELS_ONLY")
    verdict_reason = (
        "The frozen rule (U2<1 AND detrended lag-0 r>0) is MET AS WRITTEN by "
        f"both seasonal legs ({', '.join(seasonal_pass)}), but the pass is "
        "NOT REAL and no monthly-timing claim is earned. Reasons, each "
        "computed and recorded in this artifact: "
        + " | ".join(defeats)
        + ". Every claim is therefore restricted to LEVELS. Separately, and "
        "independently of timing: the marginal movement attributed to the "
        "'shape effect' is NOT seasonality — see permutation_null "
        "(calendar order is nearly irrelevant) and jensen_equivalent_flat "
        "(level leakage vs floor dispersion). It is a FLOOR-DISPERSION / "
        "functional-form result driven by FLOOR_MODE='max', and must be "
        "reported as such."
    ) if not rule_has_power else "Rule met and no diagnostic defeats it."

    # --- B4 trigger evaluation (declared ex ante) --------------------------
    near_miss = []
    for lg in SEASONAL_LEGS:
        s = scores_primary[lg]
        if s["verdict"] == "PASS":
            continue
        if abs(s["u2_diffs"] - 1.0) <= NEAR_MISS_U2_BAND and \
                s["detrended_lag0_r"] > 0:
            near_miss.append(lg)
        elif s["u2_diffs"] < 1.0 and -0.05 < s["detrended_lag0_r"] <= 0:
            near_miss.append(lg)
    b4 = {
        "authorized_condition": (
            "a SEASONAL leg NEARLY clears: |U2-1| <= 0.02 with r_det > 0, or "
            "U2 < 1 with r_det just barely negative"),
        "legs_that_cleared_outright": seasonal_pass,
        "legs_that_near_missed": near_miss,
        "triggered": bool(near_miss) and not seasonal_pass,
        "run": False,
        "note": ("B4 not run. The seasonal legs cleared the rule outright, so "
                 "the near-miss trigger is not met; a kernel run would be a "
                 "spec search, not a pre-registered test. The hardening pass "
                 "strengthens this: the rule has been shown to have no "
                 "discriminating power, so fitting a settlement-lag kernel to "
                 "improve a statistic that placebos already satisfy would be "
                 "meaningless as well as unauthorized."),
    }
    print(f"\nB4 settlement-lag kernel triggered: {b4['triggered']} "
          f"(run: {b4['run']})")

    # --- margin honesty ---------------------------------------------------
    margins = {lg: {
        "u2_margin_below_1": float(1.0 - scores_primary[lg]["u2_diffs"]),
        "detrended_lag0_r": scores_primary[lg]["detrended_lag0_r"],
        "detrended_lag0_p_two_sided":
            scores_primary[lg]["detrended_lag0_p_two_sided"],
        "r_distinguishable_from_zero_at_5pct":
            bool(scores_primary[lg]["detrended_lag0_p_two_sided"] < 0.05),
    } for lg in SEASONAL_LEGS}

    direction = {
        "detrended_lag0_r_flat40": scores_primary["flat_4.0"]["detrended_lag0_r"],
        "detrended_lag0_r_flat45": scores_primary["flat_4.5"]["detrended_lag0_r"],
        "detrended_lag0_r_shape_only":
            scores_primary["shape_only"]["detrended_lag0_r"],
        "detrended_lag0_r_prereg45":
            scores_primary["prereg_4.5"]["detrended_lag0_r"],
        "u1_detrended_flat40": scores_primary["flat_4.0"]["u1_detrended"],
        "u1_detrended_flat45": scores_primary["flat_4.5"]["u1_detrended"],
        "u1_detrended_shape_only": scores_primary["shape_only"]["u1_detrended"],
        "u1_detrended_prereg45": scores_primary["prereg_4.5"]["u1_detrended"],
    }

    secondary_verdicts = {lg: scores_secondary[lg]["verdict"]
                          for lg in LEGS} if scores_secondary else {}
    if scores_secondary:
        print("\n=== SECONDARY benchmark (B0 panel-derived CPR; NOT "
              "adjudicated) ===")
        for lg in LEGS:
            s = scores_secondary[lg]
            print(f"  {lg:<12} U2 {s['u2_diffs']:.6f}  r_det "
                  f"{s['detrended_lag0_r']:+.6f}  peak lag "
                  f"{s['ccf_peak_lag']:+d}  => {s['verdict']}")

    print("\n=== FREQUENCY BAND (primary) ===")
    for lg in LEGS:
        b = bands[lg]
        print(f"  {lg:<12} 12m-harmonic r {b['harmonic_12m_r']:+.4f}  "
              f"residual r {b['residual_r']:+.4f}  "
              f"sim var in harmonic {b['sim_var_share_in_12m_harmonic']:.3f}  "
              f"emp var in harmonic {b['emp_var_share_in_12m_harmonic']:.3f}")

    payload = {
        "mode": "b3_timing_rescore",
        "spec": "hazard/b3_timing_rescore.py module docstring (fixed ex ante)",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "frozen_rule_met_as_written": rule_met_as_written,
        "frozen_rule_has_discriminating_power": rule_has_power,
        "frozen_rule_defeated_by": defeats,
        "adjudication_note": (
            "frozen_rule_met_as_written and verdict answer DIFFERENT "
            "questions. The first is whether the pre-committed inequality "
            "holds; it does. The second is whether holding it is EVIDENCE; it "
            "is not, because placebo rotations, scrambled calendars and a "
            "beta1=0 null satisfy the same inequality. The rule was frozen "
            "ex ante and is reported as met; the diagnostics that strip it of "
            "power were computed afterwards and are reported in full rather "
            "than used to reopen the rule."),
        "b1_provenance": {
            "basis_of_the_12_vector": "full_panel",
            "correction": (
                "An earlier docstring in this file described B1's 12-cell "
                "profile as estimated 'in-window'. That was WRONG. The "
                "committed 12-vector reproduces on the FULL cohort-month "
                "panel, not on the QT window. Both bases are carried in the "
                "B2 artifact under b1_profile.bases and are mirrored here."),
            "bases": b2["b1_profile"].get("bases", {}),
            "calendar_cells_differing_between_bases_at_5dp":
                b2["b1_profile"].get(
                    "calendar_cells_differing_between_bases_at_5dp", []),
            "which_basis_drives_the_runs": (
                "full_panel drives every H_MONTH normalization and every run; "
                "qt_window is disclosure only and drives nothing"),
        },
        "permutation_null": diag_perm,
        "rotation_placebo": diag_rot,
        "artifact_concentration": diag_art,
        "leave_one_out": diag_loo,
        "null_leg_scores": diag_null,
        "level_shape_interaction": diag_lsi,
        "jensen_equivalent_flat": diag_jensen,
        "frequency_band_summary": diag_freq,
        "b2_runtime_s": b2.get("runtime_s"),
        "b2_source_artifact": str(B2_RESULTS),
        "window": {"first": periods[0], "last": periods[-1],
                   "n": len(periods), "n_diffs": len(periods) - 1},
        "scorers_reused": {
            "theil_u1": "figures/make_theil_data.py:231",
            "theil_u2_diffs": "figures/make_theil_data.py:237",
            "detrend": "figures/make_theil_data.py:261",
            "estimator_block": "figures/make_theil_data.py:267",
            "parity_target_read_from": str(COMMITTED_THEIL)
            + ":estimators.path_b (READ, not a hardcoded literal)",
            "cpr_cross_correlation": "hazard/macro.py:131 (max_lag=6)",
            "new_math_written": "none (Pearson r on committed detrend output)",
        },
        "empirical_primary": {
            "definition": "SOMA back-out Empirical_CPR_Pct (qt_active_frame), "
                          "the series figures/theil_data.json is scored on",
            "source": str(B2_RESULTS),
            "values_annual_pct": list(map(float, emp_primary)),
            "mean": float(emp_primary.mean()),
            "sd": float(emp_primary.std(ddof=0)),
        },
        "empirical_secondary": None if emp_secondary is None else {
            "definition": "B0 panel-derived cpr_annual x100; DIFFERENT object "
                          "(cohort-panel prepayment back-out, not SOMA "
                          "rolloff), robustness only, NOT adjudicated",
            "source": str(B0_ARTIFACT),
            "window_first": sec_periods[0],
            "window_last": sec_periods[-1],
            "n": len(sec_periods),
            "months_missing_from_qt_window": sec_missing,
            "values_annual_pct": list(map(float, emp_secondary)),
            "mean": float(emp_secondary.mean()),
            "sd": float(emp_secondary.std(ddof=0)),
        },
        "parity_gate": parity,
        "parity_gate_pass": parity_pass,
        "scores_primary": scores_primary,
        "scores_secondary": scores_secondary,
        "secondary_verdicts": secondary_verdicts,
        "secondary_circularity_warning": (
            "The secondary benchmark is NOT independent corroboration and must "
            "not be quoted as such. B1's 12-cell calendar profile was ESTIMATED "
            "off the same cohort-month panel that produces this CPR series, so "
            "scoring the seasonalized floor against it scores the profile "
            "against its own estimation sample. The large apparent improvement "
            "(U2 0.995 -> 0.762, r_det +0.016 -> +0.863 for shape_only) is the "
            "expected signature of that circularity, not evidence of timing "
            "skill. It is reported only to show that the thin primary pass is "
            "not a sign error."),
        "frequency_band_secondary": bands_secondary,
        "frozen_rule": "U2(first diffs) < 1 AND detrended lag-0 r > 0",
        "seasonal_legs_passing": seasonal_pass,
        "margin_disclosure": margins,
        "direction_of_movement": direction,
        "frequency_band": bands,
        "b4_settlement_lag_kernel": b4,
        "surviving_claim_frequency_band": (
            "NO monthly-timing claim survives; see verdict_reason. The band "
            "diagnostic is retained because it is one of the reasons: the "
            "seasonal legs push the large majority of SIMULATED detrended "
            "variance into the 12-month calendar harmonic while the PRIMARY "
            "empirical benchmark carries only a small share of its own "
            "detrended variance there. The model gained calendar structure the "
            "benchmark can neither confirm nor refute. Exact shares are in "
            "frequency_band_summary, computed, not quoted."),
        "carried_caveats": [
            "B1 is CIRCULAR: gap<=-150bp captures 98.2% of QT exposure, so "
            "the deep-OOM filter is near the identity map and the floor is "
            "NOT identified off a lock-in-free population",
            "the clean 2017-2019 out-of-window leg cannot rescue it: 335 "
            "cohort-months / $86.2B, with ZERO prepaid_upb in Feb and Apr, so "
            "no 12-cell profile is estimable there",
            "the seasonal share INVERTS between windows (full-panel R2 0.0109 "
            "vs QT 0.7554); B1 inherits that instability",
            "the committed Path A VOLUNTARY seasonality "
            "(hazard/seasonality_concave_gap.py) peaks Mar/Oct/Sep while this "
            "INVOLUNTARY profile peaks Jun; different objects, but the "
            "tension must be stated wherever the seasonal floor is quoted",
            "SOMA back-out benchmark is lumpy (four exact-0.000 months, three "
            ">9%); see artifact_concentration for what those months carry",
            "the 12-vector is FULL-PANEL, not in-window; see b1_provenance",
            "the marginal movement is FLOOR DISPERSION under FLOOR_MODE='max', "
            "not seasonality; see permutation_null and jensen_equivalent_flat",
        ],
    }
    OUT_REPO.write_text(json.dumps(payload, indent=2))
    # Mirror to the session scratchpad only if it already exists (see the
    # B0_ARTIFACT note above): absent on a clean checkout.
    _mirrored = OUT_SCRATCH.parent.is_dir()
    if _mirrored:
        OUT_SCRATCH.write_text(json.dumps(payload, indent=2))
    print(f"\nVERDICT: {verdict}")
    print(f"Written: {OUT_REPO}" + (f"\n         {OUT_SCRATCH}" if _mirrored else ""))


if __name__ == "__main__":
    main()
