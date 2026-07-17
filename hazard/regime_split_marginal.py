#!/usr/bin/env python3
"""
Round-18 R18-G / gate #50: sensitivity of the +9.2pp lock-in marginal to a
STRUCTURAL BREAK in the baseline hazard (referee comment E4 — non-stationary
baselines: pandemic shock, 2022 spread-repricing).

SPEC (committed before execution; interpretation thresholds ex ante)
====================================================================

Referee E4 asks: repeat the central-and-null decomposition under a structural
break in the baseline hazards — is +9.2pp sensitive to non-stationary
baselines?

Why the structural expectation is CANCELLATION
----------------------------------------------
The headline marginal is a Path B object (manuscript eq:pathB): the central
leg (production beta1) minus the beta1=0 null leg, BOTH walked on the SAME
literature-calibrated baseline hazard h0(a) (hazard/literature_hazard.py
prepay_hazard -> baseline_hazard -> h0_psa).  A baseline break that is COMMON
to both legs enters both trapped-liquidity totals and largely cancels from
their difference.  This run makes that argument quantitative rather than
asserted: we impose a break on h0 IDENTICALLY in both legs and measure how
much of it survives into the marginal.

This is a SENSITIVITY, not an estimation: nothing is fitted to the $764.7B
benchmark.  The break factors are a pre-committed grid, applied identically to
both legs, preserving the paper's pre-commitment architecture (same 75k
committed sample, same RNG seed as the production US leg, same macro frame).

Break definition
----------------
A MULTIPLICATIVE LEVEL SHIFT on the baseline hazard h0(a), applied to all
CALENDAR months t >= break_date (a period interaction on h0, per the roadmap's
"period-interacted baseline"):

    h0_break(a, t) = f * h0(a)   for t >= break_date,   1.0 * h0(a) otherwise.

The shift multiplies h0 BEFORE the covariate/rate-gap exponent and BEFORE the
involuntary-floor combination, so it is a pure baseline-level perturbation; the
rate-gap channel (the only thing beta1 touches) and the involuntary floor are
untouched by the h0-level variant.  Because FLOOR_MODE = "max" in production
(config.py:52), wherever the involuntary floor binds (deep-out-of-the-money,
suppressed voluntary hazard — the typical QT-window state) the h0 shift is
absorbed by the floor and has no effect; where the voluntary hazard clears the
floor, the shift moves it.  Both behaviours are identical across the two legs.

Break DATE (pre-committed): 2023-01-01.  Justification: the QT window is
[2022-06, 2025-12) (common/qt_window.py), so the pandemic itself PREDATES the
simulation window and cannot be the in-window break.  The operative in-window
non-stationarity the referee names is the 2022-23 spread-repricing era
(primary-to-10yr spread 170 -> 300bp+, manuscript L47).  2023-01 is a clean
calendar boundary separating the acute 2022 repricing tail (Jun-Dec 2022,
7 window months) from the elevated-but-stabilising 2023+ regime (35 window
months).  A pandemic-dummy interpretation would place the break before the
window and leave every window month post-break (factor applied to all 42
months) — a degenerate case we do NOT run because it is a uniform h0 rescale
that cancels even more trivially.  (The round-17 curtailment demo used a
2024-01 2022-23-vs-2024-25 split; 2023-01 here isolates the acute-repricing
tail, a tougher test of cancellation because pre and post baselines differ.)

Break FACTOR grid (pre-committed): {0.8, 1.0, 1.2}, i.e. a +/-20% baseline
level shift post-break.  1.0 is the parity anchor: with f = 1.0 the patched
hazard is bit-identical to production and MUST reproduce the committed central
and null before any other factor is interpreted.

Two variants
------------
(A) h0-LEVEL break (primary):  f multiplies h0(a) only; involuntary floor
    fixed.  Grid {0.8, 1.0, 1.2}.
(B) FLOOR-LEVEL break (asymmetric, optional):  f multiplies the involuntary
    turnover floor's annual CPR (INVOLUNTARY_CPR_ANNUAL) only; h0 fixed.  Grid
    {0.8, 1.2} (1.0 == the shared anchor already in (A)).  The code structure
    makes this distinction natural — prepay_hazard builds h_vol from h0 and the
    floor from INVOLUNTARY_CPR_ANNUAL separately, then combines by np.maximum —
    so scaling one component while holding the other is a one-line change with
    no design muddle.  This isolates whether the marginal's robustness rests on
    the h0 seasoning ramp or on the turnover floor being common to both legs.

Engine hook (NO existing file is modified; all patches are in-process)
----------------------------------------------------------------------
We reuse the committed microsim_engine._simulate_regime UNCHANGED (the exact
production leg walk).  Two in-process monkey-patches:
  * competing_risks.prepay_hazard  <- patched_prepay_hazard, a faithful copy of
    literature_hazard.prepay_hazard that multiplies h0 by _STATE["h0_factor"]
    and the floor annual CPR by _STATE["floor_factor"].  At (1.0, 1.0) it is
    IEEE-bit-identical to the original (x1.0 is exact), so G1/G2 reproduce the
    committed anchors to 0.0.
  * microsim_engine.monthly_step   <- a wrapper that counts calendar months
    within a leg (monthly_step is called exactly once per QT month, in order,
    by _simulate_regime) and sets the post-break factor for months at index
    >= break_idx, 1.0 otherwise, then delegates to the real
    competing_risks.monthly_step.
The per-leg counter resets before each _simulate_regime call.

Legs (10 total; US regime only — the lock-in marginal is US central minus US
null; the Danish leg is not involved):
  anchor  f=1.0            : central + null   (G1/G2/G3/G4)
  h0      f=0.8, 1.2       : central + null each
  floor   f=0.8, 1.2       : central + null each
Runtime ~= 10 legs x ~12s + setup ~= 3-5 min.

Per-month decomposition (exact)
-------------------------------
score_extension_risk computes trapped = sum_t (simulated_rolloff_b[t] -
QT_target[t]).  Hence the marginal is additive over months and the QT target
CANCELS in central - null:
    marginal_b = sum_t (central_rolloff[t] - null_rolloff[t]).
Splitting that sum at break_date gives the pre-break and post-break marginal
contributions EXACTLY (pre + post = total to float headroom; gate G4).

Gates (hard; failure => STOP, do not loosen)
--------------------------------------------
G1 central parity (f=1.0): reproduce committed central 818.5300844066606 B,
   |diff| <= 1e-6 (0.0 expected).
G2 null parity (f=1.0): reproduce committed null 748.1850239867648 B,
   |diff| <= 1e-6 (0.0 expected).
G3 marginal parity (f=1.0): |marginal_b - 70.34506041989584| <= 1e-6 AND
   |marginal_pp - 9.198459770709789| <= 1e-9.
G4 per-month additivity (every leg pair): |(pre_b + post_b) - marginal_b|
   <= 1e-6 (the pre/post split is exact by construction).

Interpretation envelope (pre-committed, two-sided, ex ante)
-----------------------------------------------------------
Committed marginal m0 = 9.198459770709789 pp.  Justification for the bands is
drawn from the paper's existing tolerance culture:
  E1 near-cancellation band = [m0 - 1.0, m0 + 1.0] pp = [8.198, 10.198].
     1.0pp is (i) smaller than the cyclical-floor variant's own downside
     excursion (m0 -> 7.1pp = -2.1pp; tab:uncertainty), and (ii) far below the
     +/-1.84pp a ~linear (non-cancelling) response to a +/-20% baseline shift
     would produce (0.20 * 9.198).  Staying inside E1 evidences that the common
     baseline break cancels from the difference.
  E2 paper-accepted robustness band = [7.1, 9.4] pp — the full span the
     cyclical-floor baseline variant already moves the marginal across
     kappa in [-0.5, +0.5] (tab:uncertainty).  A perturbation no larger than an
     already-reported, already-accepted single-baseline sensitivity.
  E3 outer calibration box = [2.1, 13.2] pp (manuscript calibration box):
     sign-positive and headline-preserving throughout.

Verdict (reported per design; NOT a stop-gate — a material result is a valid
finding, reported honestly with the committed language):
  cancellation_confirmed        : every swept factor's marginal_pp in E1.
  robust_within_accepted_band   : not all in E1 but all in E2.
  material_sensitivity          : any swept marginal outside E2, or outside E3,
                                  or sign-flipped -> report as material
                                  sensitivity to non-stationary baselines; do
                                  NOT claim cancellation.

Output: data/regime_split_marginal_results.json (spec echo, gates, anchor,
h0-sweep table, floor-sweep table, envelope thresholds, verdict).

Run:  cd hazard && python3 regime_split_marginal.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

import competing_risks
import microsim_engine
from config import (
    FLOOR_MODE,
    INVOLUNTARY_CPR_ANNUAL,
    LITERATURE_COEFS,
    LOAN_SAMPLE_PATH,
    QT_END,
    QT_START,
    RNG_SEED,
    ROTHSTEIN_Q_DECLINE_MID,
)
from extension_risk import score_extension_risk
from literature_hazard import (
    baseline_hazard,
    cpr_annual_to_monthly_hazard,
    rothstein_beta1,
)
from macro import (
    build_empirical_metrics,
    calculate_dynamic_friction,
    fetch_data,
    fetch_soma_mbs_monthly,
    qt_active_frame,
)
from markov import load_transition_matrix

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "regime_split_marginal_results.json"

# ---- Committed anchors (data/no_lockin_null_results.json) — quoted ----------
CENTRAL_TRAPPED_B = 818.5300844066606
NULL_TRAPPED_B = 748.1850239867648
MARGINAL_B = 70.34506041989584
MARGINAL_PP = 9.198459770709789
NETTING_CONTEXT_B = 69.56220187263008  # production shared-layer netting basis

PARITY_TOL_B = 1e-6
ADDITIVITY_TOL_B = 1e-6
PP_TOL = 1e-9

# ---- Pre-committed design ---------------------------------------------------
BREAK_DATE = pd.Timestamp("2023-01-01")
H0_FACTORS = (0.8, 1.0, 1.2)      # variant A: multiply h0(a)
FLOOR_FACTORS = (0.8, 1.2)        # variant B: multiply floor annual CPR (1.0 == anchor)

# Pre-committed interpretation envelope (pp)
E1 = (MARGINAL_PP - 1.0, MARGINAL_PP + 1.0)   # near-cancellation
E2 = (7.1, 9.4)                                # cyclical-floor accepted band
E3 = (2.1, 13.2)                               # outer calibration box

# ---- Mutable per-leg / per-month state read by the patched hazard -----------
_STATE = {
    "leg_month_index": 0,
    "break_idx": 10**9,
    "h0_factor": 1.0,
    "floor_factor": 1.0,
    "post_h0_factor": 1.0,
    "post_floor_factor": 1.0,
}

_REAL_MONTHLY_STEP = competing_risks.monthly_step


def patched_prepay_hazard(loan_age, rate_gap, burnout, fico_z, ltv_z,
                          beta1=None, coefs=None):
    """
    Faithful copy of literature_hazard.prepay_hazard with a baseline-level
    break multiplier on h0 (_STATE["h0_factor"]) and a floor-level break
    multiplier on the involuntary annual CPR (_STATE["floor_factor"]).  At
    (1.0, 1.0) this is IEEE-bit-identical to the production function.
    """
    c = coefs or LITERATURE_COEFS
    h0_raw = baseline_hazard(loan_age)
    h0 = h0_raw * _STATE["h0_factor"]
    log_h = (
        (-beta1) * (rate_gap * 100.0)
        + c["beta_fico"] * fico_z
        + c["beta_ltv"] * ltv_z
        + c["beta_burnout"] * burnout
    )
    h_vol = h0 * np.exp(log_h)
    h_floor = cpr_annual_to_monthly_hazard(
        np.full_like(h0_raw, INVOLUNTARY_CPR_ANNUAL * _STATE["floor_factor"],
                     dtype=np.float64)
    )
    if FLOOR_MODE == "additive":
        combined = 1.0 - (1.0 - h_floor) * (1.0 - h_vol)
    else:
        combined = np.maximum(h_floor, h_vol)
    return np.clip(combined, 0.0, 1.0)


def _monthly_step_wrapped(pool, market_rate, trans=None, beta1=None):
    """Toggle the post-break factor by calendar-month index, then delegate."""
    idx = _STATE["leg_month_index"]
    if idx >= _STATE["break_idx"]:
        _STATE["h0_factor"] = _STATE["post_h0_factor"]
        _STATE["floor_factor"] = _STATE["post_floor_factor"]
    else:
        _STATE["h0_factor"] = 1.0
        _STATE["floor_factor"] = 1.0
    _STATE["leg_month_index"] = idx + 1
    return _REAL_MONTHLY_STEP(pool, market_rate, trans=trans, beta1=beta1)


# Install patches (in-process only; no file on disk is modified).
competing_risks.prepay_hazard = patched_prepay_hazard
microsim_engine.monthly_step = _monthly_step_wrapped


def run_leg(loans, macro, trans, holdings_b, beta1, empirical,
            break_idx, post_h0, post_floor):
    """One US-regime leg under the given post-break factors; returns (score, sim)."""
    _STATE["leg_month_index"] = 0
    _STATE["break_idx"] = break_idx
    _STATE["post_h0_factor"] = post_h0
    _STATE["post_floor_factor"] = post_floor
    _STATE["h0_factor"] = 1.0
    _STATE["floor_factor"] = 1.0
    sim = microsim_engine._simulate_regime(
        loans, macro, "US", holdings_b, trans, seed=RNG_SEED, beta1=beta1
    )
    score = score_extension_risk(sim, empirical)
    return score, sim


def split_marginal(central_sim, null_sim, empirical, break_date):
    """
    Exact per-month marginal (central_rolloff - null_rolloff) on the scorer's
    QT index, split pre/post break.  Returns dollar and pp contributions plus
    the per-leg central/null trapped contributions on each side.
    """
    qt_emp = qt_active_frame(empirical)
    idx = qt_emp.index
    target = qt_emp["QT_Target_Billions"]
    c = central_sim.reindex(idx)["simulated_rolloff_b"]
    n = null_sim.reindex(idx)["simulated_rolloff_b"]
    emp_trapped = float(qt_emp["Extension_Delta_Billions"].sum())

    marg_m = c - n
    pre = idx < break_date
    post = ~pre
    pre_b = float(marg_m[pre].sum())
    post_b = float(marg_m[post].sum())

    c_contrib = c - target
    n_contrib = n - target
    return {
        "n_pre_months": int(pre.sum()),
        "n_post_months": int(post.sum()),
        "pre_marginal_b": pre_b,
        "post_marginal_b": post_b,
        "pre_marginal_pp": pre_b / emp_trapped * 100,
        "post_marginal_pp": post_b / emp_trapped * 100,
        "pre_central_trapped_b": float(c_contrib[pre].sum()),
        "post_central_trapped_b": float(c_contrib[post].sum()),
        "pre_null_trapped_b": float(n_contrib[pre].sum()),
        "post_null_trapped_b": float(n_contrib[post].sum()),
        "emp_trapped_b": emp_trapped,
    }


def classify(marginal_pps: list[float]) -> str:
    lo, hi = min(marginal_pps), max(marginal_pps)
    if all(v > 0 for v in marginal_pps):
        if E1[0] <= lo and hi <= E1[1]:
            return "cancellation_confirmed"
        if E2[0] <= lo and hi <= E2[1]:
            return "robust_within_accepted_band"
    return "material_sensitivity"


def factor_row(loans, macro, trans, holdings_b, empirical, break_idx,
               break_date, post_h0, post_floor, beta1_prod, label):
    """Run central+null for one break factor; assemble the reporting row."""
    t0 = time.perf_counter()
    c_score, c_sim = run_leg(loans, macro, trans, holdings_b, beta1_prod,
                             empirical, break_idx, post_h0, post_floor)
    n_score, n_sim = run_leg(loans, macro, trans, holdings_b, 0.0,
                             empirical, break_idx, post_h0, post_floor)
    central_b = c_score["hazard_trapped_b"]
    null_b = n_score["hazard_trapped_b"]
    marg_b = central_b - null_b
    marg_pp = c_score["share_explained_pct"] - n_score["share_explained_pct"]
    split = split_marginal(c_sim, n_sim, empirical, break_date)
    additivity_diff = (split["pre_marginal_b"] + split["post_marginal_b"]) - marg_b
    row = {
        "variant": label,
        "post_h0_factor": post_h0,
        "post_floor_factor": post_floor,
        "central_trapped_b": central_b,
        "central_share_pct": c_score["share_explained_pct"],
        "null_trapped_b": null_b,
        "null_share_pct": n_score["share_explained_pct"],
        "marginal_b": marg_b,
        "marginal_pp": marg_pp,
        "split": split,
        "g4_additivity_diff_b": additivity_diff,
        "g4_pass": abs(additivity_diff) <= ADDITIVITY_TOL_B,
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    print(f"  [{label:>5} h0={post_h0:.1f} floor={post_floor:.1f}] "
          f"central {central_b:.6f}  null {null_b:.6f}  "
          f"marginal {marg_b:+.6f} B ({marg_pp:+.6f} pp)  "
          f"pre {split['pre_marginal_b']:+.4f} / post {split['post_marginal_b']:+.4f}  "
          f"G4 {'PASS' if row['g4_pass'] else 'FAIL'}")
    return row


def main() -> None:
    t_start = time.perf_counter()
    beta1_prod = rothstein_beta1(ROTHSTEIN_Q_DECLINE_MID)

    print("Building macro/empirical frames …")
    macro_raw = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro_raw, soma_rolloff=soma)
    macro = calculate_dynamic_friction(macro_raw)
    trans = load_transition_matrix()
    qt_start_idx = macro.index.get_indexer([QT_START], method="nearest")[0]
    holdings_b = float(macro.iloc[qt_start_idx]["WSHOMCB"]) / 1_000

    qt_index = macro.index[(macro.index >= QT_START) & (macro.index < QT_END)]
    break_idx = int((qt_index < BREAK_DATE).sum())
    n_window = int(len(qt_index))
    print(f"QT window months: {n_window} | break {BREAK_DATE.date()} at index "
          f"{break_idx} (pre {break_idx}, post {n_window - break_idx})")

    loans = pl.read_parquet(LOAN_SAMPLE_PATH)

    # ---- Anchor (f = 1.0) : G1 / G2 / G3 -----------------------------------
    print("\nAnchor f=1.0 (parity) …")
    anchor = factor_row(loans, macro, trans, holdings_b, empirical, break_idx,
                        BREAK_DATE, 1.0, 1.0, beta1_prod, "anchor")

    g1_diff = anchor["central_trapped_b"] - CENTRAL_TRAPPED_B
    g2_diff = anchor["null_trapped_b"] - NULL_TRAPPED_B
    g3_marg_diff = anchor["marginal_b"] - MARGINAL_B
    g3_pp_diff = anchor["marginal_pp"] - MARGINAL_PP
    g1_pass = abs(g1_diff) <= PARITY_TOL_B
    g2_pass = abs(g2_diff) <= PARITY_TOL_B
    g3_pass = abs(g3_marg_diff) <= PARITY_TOL_B and abs(g3_pp_diff) <= PP_TOL
    g4_anchor_pass = anchor["g4_pass"]
    print(f"  G1 central diff {g1_diff:+.3e}  {'PASS' if g1_pass else 'FAIL'}")
    print(f"  G2 null    diff {g2_diff:+.3e}  {'PASS' if g2_pass else 'FAIL'}")
    print(f"  G3 marginal diff {g3_marg_diff:+.3e} B / {g3_pp_diff:+.3e} pp  "
          f"{'PASS' if g3_pass else 'FAIL'}")
    print(f"  G4 additivity diff {anchor['g4_additivity_diff_b']:+.3e} B  "
          f"{'PASS' if g4_anchor_pass else 'FAIL'}")

    gates = {
        "G1_central_parity": {"trapped_b": anchor["central_trapped_b"],
                              "committed_b": CENTRAL_TRAPPED_B,
                              "diff_b": g1_diff, "tol_b": PARITY_TOL_B,
                              "pass": g1_pass},
        "G2_null_parity": {"trapped_b": anchor["null_trapped_b"],
                           "committed_b": NULL_TRAPPED_B,
                           "diff_b": g2_diff, "tol_b": PARITY_TOL_B,
                           "pass": g2_pass},
        "G3_marginal_parity": {"marginal_b": anchor["marginal_b"],
                               "committed_b": MARGINAL_B,
                               "diff_b": g3_marg_diff,
                               "marginal_pp": anchor["marginal_pp"],
                               "committed_pp": MARGINAL_PP,
                               "diff_pp": g3_pp_diff,
                               "pass": g3_pass},
        "G4_permonth_additivity_anchor": {
            "diff_b": anchor["g4_additivity_diff_b"],
            "tol_b": ADDITIVITY_TOL_B, "pass": g4_anchor_pass},
    }

    if not (g1_pass and g2_pass and g3_pass and g4_anchor_pass):
        payload = {"run": "regime_split_marginal", "status": "GATE_FAILURE",
                   "gates": gates}
        RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=float) + "\n")
        raise SystemExit("Parity/additivity gate failure — variants not interpreted.")

    # ---- Variant A: h0-level break -----------------------------------------
    print("\nVariant A — h0-level break {0.8, 1.0, 1.2} …")
    h0_rows = [anchor if abs(f - 1.0) < 1e-12 else
               factor_row(loans, macro, trans, holdings_b, empirical, break_idx,
                          BREAK_DATE, f, 1.0, beta1_prod, "h0")
               for f in H0_FACTORS]

    # ---- Variant B: floor-level break (asymmetric) -------------------------
    print("\nVariant B — floor-level break {0.8, 1.2} (h0 fixed) …")
    floor_rows = [factor_row(loans, macro, trans, holdings_b, empirical,
                             break_idx, BREAK_DATE, 1.0, f, beta1_prod, "floor")
                  for f in FLOOR_FACTORS]

    # G4 across every varied leg
    g4_all = all(r["g4_pass"] for r in h0_rows + floor_rows)
    gates["G4_permonth_additivity_all_legs"] = {
        "max_abs_diff_b": max(abs(r["g4_additivity_diff_b"])
                              for r in h0_rows + floor_rows),
        "tol_b": ADDITIVITY_TOL_B, "pass": g4_all}

    # ---- Verdicts -----------------------------------------------------------
    h0_pps = [r["marginal_pp"] for r in h0_rows]
    floor_pps = [r["marginal_pp"] for r in floor_rows]
    verdict_h0 = classify(h0_pps)
    verdict_joint = classify(h0_pps + floor_pps)
    max_excursion_h0 = max(abs(v - MARGINAL_PP) for v in h0_pps)
    max_excursion_joint = max(abs(v - MARGINAL_PP) for v in h0_pps + floor_pps)

    print("\n" + "=" * 68)
    print(f"h0-level marginal span: {min(h0_pps):.4f} .. {max(h0_pps):.4f} pp "
          f"(max excursion {max_excursion_h0:.4f} pp) -> {verdict_h0}")
    print(f"joint (incl. floor)   : "
          f"{min(h0_pps + floor_pps):.4f} .. {max(h0_pps + floor_pps):.4f} pp "
          f"(max excursion {max_excursion_joint:.4f} pp) -> {verdict_joint}")
    print("=" * 68)

    payload = {
        "run": "regime_split_marginal",
        "roadmap_item": "R18-G",
        "gate_id": 50,
        "status": "OK",
        "spec": {
            "break_date": str(BREAK_DATE.date()),
            "break_justification": (
                "QT window [2022-06,2025-12): pandemic predates the window; the "
                "in-window non-stationarity is the 2022-23 spread-repricing era. "
                "2023-01 separates the acute 2022 repricing tail (7 months) from "
                "the 2023+ regime (35 months)."),
            "break_idx": break_idx,
            "n_window_months": n_window,
            "n_pre_months": break_idx,
            "n_post_months": n_window - break_idx,
            "h0_factors": list(H0_FACTORS),
            "floor_factors": list(FLOOR_FACTORS),
            "variant_A": "multiplicative level shift on baseline h0(a), post-break",
            "variant_B": "multiplicative level shift on involuntary floor CPR, post-break",
            "applied_identically_to_both_legs": True,
            "floor_mode": FLOOR_MODE,
            "engine": "committed microsim_engine._simulate_regime; US regime; "
                      "seed RNG_SEED; committed 75k sample; in-process monkey-patch only",
            "basis": "standalone scorer (matches marginal_decomposition harness); "
                     "marginal basis-invariant per manuscript Sec V",
            "netting_basis_context_b": NETTING_CONTEXT_B,
        },
        "committed_anchors": {
            "central_trapped_b": CENTRAL_TRAPPED_B,
            "null_trapped_b": NULL_TRAPPED_B,
            "marginal_b": MARGINAL_B,
            "marginal_pp": MARGINAL_PP,
        },
        "gates": gates,
        "envelope": {
            "committed_marginal_pp": MARGINAL_PP,
            "E1_near_cancellation_pp": list(E1),
            "E2_cyclical_floor_band_pp": list(E2),
            "E3_calibration_box_pp": list(E3),
            "linear_noncancellation_reference_pp": 0.20 * MARGINAL_PP,
            "justification": (
                "E1 (+/-1.0pp) is below the cyclical-floor variant's own -2.1pp "
                "downside and below the +/-1.84pp a linear response to a +/-20% "
                "baseline shift would give; E2 is the accepted cyclical-floor "
                "span; E3 the outer calibration box."),
        },
        "h0_sweep": h0_rows,
        "floor_sweep": floor_rows,
        "results": {
            "h0_marginal_pps": h0_pps,
            "floor_marginal_pps": floor_pps,
            "h0_span_pp": [min(h0_pps), max(h0_pps)],
            "joint_span_pp": [min(h0_pps + floor_pps), max(h0_pps + floor_pps)],
            "max_excursion_h0_pp": max_excursion_h0,
            "max_excursion_joint_pp": max_excursion_joint,
            "verdict_h0": verdict_h0,
            "verdict_joint": verdict_joint,
        },
        "runtime_s": round(time.perf_counter() - t_start, 1),
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"\nResults saved to {RESULTS_JSON}")
    print(f"Total runtime {payload['runtime_s']}s")


if __name__ == "__main__":
    main()
