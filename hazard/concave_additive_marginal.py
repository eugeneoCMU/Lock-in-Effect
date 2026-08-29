#!/usr/bin/env python3
"""
concave_additive_marginal.py — the unmeasured {concave gap transform} x
{additive floor form} cell, and with it the first test of whether the
manuscript's designated form-conditional hull is COMPLETE over the
{form x transform} product it is quoted as spanning.

PRE-COMMITTED SPEC (fixed in this header BEFORE any run; ex-ante convention of
floor_form_test.py / oos_identification.py / floor_form_offwindow.py /
concave_marginal.py).

AUDIT OBJECTION (round 22, hull completeness). The manuscript designates a
form-conditional identified hull of "$+3.9$ to $+13.1$" points and quotes that
literal at five .tex sites (abstract; Table 1 tab:headline; V.E; Table 8
tab:uncertainty; VII.I), pinned by liveness gate #69 against
floor_form_offwindow_results.json designated_interval_pp =
[3.891507360127463, 13.09774126267503]. That hull is a hull over the
{max, additive} floor forms at the LOG-LINEAR gap transform ONLY:
floor_form_offwindow.py never varied the transform, and concave_marginal.py
tested the concave transform under FLOOR_MODE='max' exclusively — its own SPEC
disclaims the other dimension ("Floor form: production 'max' throughout (the
form dimension is floor_form_offwindow.py's remit, not this script's)"). The
concave x additive cell has therefore never been run, and the hull's
completeness over the {form x transform} product is ASSERTED, not established.
tab:uncertainty (line 509) makes the assertion visible: in one cell it lists
"additive form $+11.2$ (form-conditional hull $+3.9$ to $+13.1$)" and "concave
transform $+5.1$" as parallel, un-interacted entries, which silently claims a
separability that nothing has measured. Both mechanisms are individually
material by the manuscript's own +/-1.0pp convention (the form moves the
production-floor marginal +9.20 -> +11.25; the transform moves it +9.20 ->
+7.87), so their interaction is exactly the term the parallel listing assumes
away. This script measures it.

MECHANISM COMPOSITION (verified against the code before this header was
written, so that the design rests on no assumption about plumbing):
- The transform is applied by monkeypatching competing_risks.prepay_hazard
  with the concave wrapper of concave_marginal.py:102-113 (constants
  CONCAVE_KINK_PP = 2.0, CONCAVE_SLOPE2 = 0.5, identical to
  seasonality_concave_gap.py:73-74), restored in a finally block.
- The floor form is literature_hazard.FLOOR_MODE, which
  literature_hazard.prepay_hazard reads from its own module globals at CALL
  time (literature_hazard.py:110), not at import time.
- competing_risks imports prepay_hazard by value (competing_risks.py:16-20),
  so the wrapper's delegate IS literature_hazard.prepay_hazard and reads the
  mutated FLOOR_MODE. The two mechanisms therefore compose with NO new
  plumbing: set both, restore both.
- Regime tuple and macro frame: US-only regime (concave_marginal.py's
  committed convention) with macro=fetch_data() passed in. Both are
  bit-invariances rather than choices: microsim_engine._simulate_regime reads
  only MORTGAGE30US and WSHOMCB from the macro frame (the Dynamic_Friction /
  Search_Penalty / Sentiment_Penalty columns that macro.calculate_dynamic_
  friction adds are consumed nowhere in the simulation path), US is
  regimes[0] and so carries seed offset 0 whether or not the Danish leg runs,
  and extension_risk.score_extension_risk reads only simulated_rolloff_b and
  hazard_cpr_pct — never the CPR_Danish / Danish_simulated_rolloff_b columns
  that run_qt_microsim appends to the combined parquet. G0/G1 below convert
  those three invariances from claims into gates by replaying two-regime
  committed anchors from US-only runs.

SPEC (fixed ex ante)
- Full 2x2x2 factorial, {central, null} at each cell: transform
  {loglinear (production), concave} x form {max, additive} x floor
  {4.0% (production), 4.991% (committed off-window headline point)} = 16
  US-regime microsim legs. No cell is inferred from another; the four legs
  the parity targets need and the two new cells are all run fresh, and the
  eight nulls are run under BOTH transforms so the beta1=0 transform
  invariance is gated rather than assumed.
- Elasticity: central p_q 6.5 (the committed Liebersohn-Rothstein midpoint)
  and null p_q 0. The {5.5, 7.7} band ends of the NEW concave-additive cell
  are deliberately OUT of scope — see the T1 honesty scope below, which
  states ex ante what a central-only cell can and cannot settle about a hull
  whose endpoints are band ends.
- Off-window floor: the literal 0.04991, asserted at runtime against
  oos_identification_results.json headline_oos_marginal.clean_floor_point_pct
  to 1e-9. DISCLOSED ex ante: the two committed runs this script replays used
  floor literals that differ by one ULP — concave_marginal.py used 0.04991
  while floor_form_offwindow.py used clean_floor_point_pct/100.0 =
  0.049909999999999996 — and the committed artifacts show that difference is
  bit-immaterial (both record null_trapped_b = 724.9180585654117 at 4.991%
  under the max form, identical to 17 significant figures). The mechanism is
  that PREPAY_MODE = 'fractional', so prepayment is a deterministic
  balance x hazard flow rather than a Bernoulli draw; the only RNG-threshold
  comparison in monthly_step is the default draw u < h_def_n, whose flip
  probability under a relative 1e-16 hazard perturbation is ~1e-16 per
  comparison. A 1e-9 parity tolerance is five orders of magnitude above the
  ~1e-14pp effect this can have. This script uses 0.04991 uniformly.
- Production convention otherwise: committed 75k loan sample, RNG_SEED 42,
  one shared macro frame fetched once, raw-basis scoring via
  extension_risk.score_extension_risk, caches not consulted (fresh microsim
  runs into data/concave_additive_marginal/).

PARITY GATES (run first, block all interpretation; tolerance abs diff < 1e-9
on both dollars and points — tighter than the house +/-$0.01B/+/-0.01pp
because every target here is a same-seed replay of a committed leg and the
committed gates recorded got == want exactly; each gate also records whether
the diff was exactly 0.0, so a successor can see bit-identity separately from
tolerance satisfaction):
  G0 (loglinear x max, both floors — the base anchors; also the regime-tuple
     and macro-frame equivalence check that licenses comparing US-only runs to
     two-regime committed artifacts):
       @4.0%:   central $818.5300844066606, null $748.1850239867648,
                marginal +9.198459770709789pp
                [no_lockin_null_results.json central_trapped_b /
                 null_trapped_b / lockin_marginal_share_pp]
       @4.991%: central $767.5264524465003, null $724.9180585654117,
                marginal +5.571558182909726pp
                [floor_form_offwindow_results.json rows[2] (max, 4.991) ->
                 band["6.5"].central_trapped_b / null_trapped_b /
                 band["6.5"].marginal_pp]
  G1 (concave x max @4.0%) — PRIMARY TARGET 1: marginal
     +7.8741354244354085pp [concave_marginal_results.json
     concave_marginal_pp_at_4], with levels $808.4023371015244 /
     $748.1850239867648 [legs.concave_central_4.trapped_b /
     legs.concave_null_4.trapped_b].
  G2 (concave x max @4.991%) — PRIMARY TARGET 2: marginal
     +5.056147332383432pp [concave_marginal_results.json
     concave_marginal_pp_at_offwindow_point], with levels
     $763.5848569701802 / $724.9180585654117
     [legs.concave_central_4991 / legs.concave_null_4991 trapped_b].
  G3 (loglinear x additive @4.0%) — PRIMARY TARGET 3: marginal
     +11.248471889121141pp [floor_form_results.json rows -> the
     form=='additive', floor==4.0 row, lockin_marginal_share_pp], with levels
     $513.7265922748531 / $427.7040999885527 [same row central.trapped_b /
     null.trapped_b].
  G4 (loglinear x additive @4.991%) — PRIMARY TARGET 4: marginal
     +11.207021073656186pp [floor_form_offwindow_results.json rows[3]
     (additive, 4.991) band["6.5"].marginal_pp], with levels
     $427.54488764725437 / $341.83938974816874, plus the two RECOVERY LEVELS:
     central 55.90661839965657% [rows[3].band["6.5"].central_share_pct] and
     null 44.69959732600039% [rows[3].null_share_pct]. Gating the levels and
     not just the marginal is deliberate: a marginal is a difference and can
     replay correctly off two compensating level errors, so the levels are
     replayed independently.
  G5 (beta1 = 0 transform invariance — ex-ante integrity assertion, not a
     sensitivity): at each of the four (form, floor) combinations the concave
     null must equal the loglinear null to < 1e-9, because beta1 = 0 makes the
     gap transform inert in log_h. Failure means the patch leaks into a
     non-elasticity channel and BLOCKS interpretation of every new cell.
  Any G0-G5 failure raises SystemExit and fixes the verdict at T3.

EX-ANTE INTERPRETIVE PARTITION (fixed here before any result is seen; the
+/-1.0pp materiality convention is the project's, imported from
floor_form_test.py and reused unchanged):
  T1 (HULL STANDS): the concave-additive marginal at central elasticity lies
     INSIDE the closed committed hull [3.891507360127463, 13.09774126267503]
     at BOTH floors. Then the hull survives its first {form x transform}
     interaction test, the five .tex literals and gate #69 stand unchanged,
     and the new cell is reported as a COMPLETENESS CHECK.
     HONEST SCOPE, stated ex ante so it cannot be quietly widened after the
     fact: this is a NECESSARY condition, not a proof of completeness. The
     committed hull's endpoints are band ends of the additive off-window
     cell — the max 13.09774126267503 is (additive, 4.695%, p_q 7.7) and the
     min 3.891507360127463 is a max-form band end — and this script runs the
     concave-additive cell at p_q 6.5 only, at 4.991% only. A T1 finding
     therefore licenses the sentence "verified at the central elasticity at
     the headline off-window anchor" and NOT the sentence "the hull is
     complete over {form x transform}". Whichever branch fires, the .tex must
     say which of the two it is.
  T2 (HULL MUST BE RE-DERIVED): the concave-additive marginal falls outside
     that closed interval at EITHER floor. Then the designated hull is
     incomplete: the literal "$+3.9$ to $+13.1$" must move at all five .tex
     sites and gate #69's designated_interval_pp must be re-pinned. The
     artifact emits implied_hull_pp = the hull of the committed
     off-window max-form and additive-form joint ranges extended by the NEW
     off-window (4.991%) concave-additive value only — matching
     floor_form_offwindow.py's construction rule, which built the committed
     hull from off-window anchors and used the 4.0% legs for parity alone.
     implied_hull_pp is pre-committed to be read as a LOWER BOUND on the
     widening, never as the replacement literal, because the unrun
     {4.695%, 5.334%} x {5.5, 7.7} concave-additive cells can only widen it
     further; a successor run must close those before any new endpoint is
     quotable.
  T3 (DEGENERATE / PARITY FAILURE): any of G0-G5 fails, or any new
     concave-additive leg returns a non-finite trapped_b or share_pct, or a
     concave-additive marginal is inert (|marginal_pp| < 1e-6, i.e. the two
     mechanisms have annihilated the elasticity channel). Nothing
     interpretive is reported; the run is a wiring failure and the .tex and
     gates are left alone.
  S (SEPARABILITY, orthogonal to T1/T2 and the partition that actually
     settles tab:uncertainty line 509): at each floor the interaction term is
     the difference-in-differences
       interaction_pp(f) = [concave_additive(f) - loglinear_additive(f)]
                         - [concave_max(f)      - loglinear_max(f)]
     computed entirely from the 16 legs run here, with no committed value
     substituted for a leg.
     S1: |interaction_pp| <= 1.0pp at both floors -> the two mechanisms are
         separable within the project's materiality convention and the
         parallel un-interacted listing at tab:uncertainty line 509 is
         defensible as written, with a footnote recording that separability
         was measured rather than assumed.
     S2: |interaction_pp| > 1.0pp at either floor -> the parallel listing is
         not defensible: line 509 must replace the two independent entries
         with the measured joint cell, and the interaction term must be
         disclosed with its sign.
  No discretion is exercised after the runs. T1/T2/T3 and S1/S2 are decided
  by the arithmetic below.

ALSO EMITTED, NOT RECOMPUTED: committed_additive_offwindow_levels_pct echoes
the three additive off-window recovery LEVELS (central 55.90661839965657% and
null 44.69959732600039% at the 4.991% anchor; central 61.16497790030112% at
the hull maximum, i.e. the (additive, 4.695%, p_q 7.7) cell) straight out of
floor_form_offwindow_results.json, with their field paths recorded beside
them. They are ALREADY COMMITTED and are not this script's to recompute; two
of the three are additionally replayed as G4 level gates.
  CORRECTION TO THE AUDIT BRIEF THAT COMMISSIONED THIS RUN: the brief holds
  that these levels are undisclosed in the .tex. They are not. All three are
  already stated at paper/final/paper_final_v1.tex line 784
  (Section~\ref{sec:robustness-floor}): "at the 4.991\% headline anchor the
  additive central leg recovers 55.9\% of the benchmark against a 44.7\%
  null, and at the 4.695\% and 5.334\% anchors 59.3\% and 52.0\%", and
  "$+13.10$ points comes from the additive form at the 4.695\% floor and the
  band's 7.7\% high edge, whose central leg recovers 61.2\% of the benchmark
  it is scored against." No .tex edit is owed for them; the echo below exists
  so a successor can verify the .tex against the artifact in one place
  instead of two.

Run:  cd hazard && python3 concave_additive_marginal.py
      -> data/concave_additive_marginal_results.json (+ per-run parquets under
         data/concave_additive_marginal/, regenerable, not committed)

Expected runtime: ~180-200s in the timed block for 16 US-regime legs, from
concave_marginal_results.json runtime_s = 66.311s for 6 US-only legs
(11.05s/leg -> 177s) cross-checked against floor_form_offwindow_results.json
runtime_s = 535.876s for 22 two-regime legs (12.18s/single-regime-leg ->
195s), plus the one-time FRED/SOMA fetch and 75k parquet read outside the
timed block.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

import competing_risks
import literature_hazard
from config import LOAN_SAMPLE_PATH
from extension_risk import score_extension_risk
from literature_hazard import rothstein_beta1
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly
from microsim_engine import run_qt_microsim

DATA_DIR = Path(__file__).parent / "data"
OUT_DIR = DATA_DIR / "concave_additive_marginal"
RESULTS_JSON = DATA_DIR / "concave_additive_marginal_results.json"
NULL_ARTIFACT = DATA_DIR / "no_lockin_null_results.json"
CONCAVE_MARGINAL_ARTIFACT = DATA_DIR / "concave_marginal_results.json"
FLOOR_FORM_ARTIFACT = DATA_DIR / "floor_form_results.json"
FLOOR_FORM_OFFWINDOW_ARTIFACT = DATA_DIR / "floor_form_offwindow_results.json"
OOS_ARTIFACT = DATA_DIR / "oos_identification_results.json"

# Concave gap transform — identical constants to seasonality_concave_gap.py:73-74
CONCAVE_KINK_PP = 2.0
CONCAVE_SLOPE2 = 0.5

PRODUCTION_FLOOR = 0.04
OFFWINDOW_POINT_FLOOR = 0.04991  # asserted vs committed oos artifact at runtime
PRODUCTION_FORM = "max"
CENTRAL_PQ = 6.5
NULL_PQ = 0.0

TOL_PARITY = 1e-9          # bit-exact replay tolerance (dollars and points)
MATERIALITY_PP = 1.0       # project convention, floor_form_test.py
INERT_PP = 1e-6            # below this a marginal counts as degenerate (T3)

# Committed hull under audit (floor_form_offwindow_results.json
# designated_interval_pp); asserted against the artifact at runtime.
COMMITTED_HULL_PP = [3.891507360127463, 13.09774126267503]


def _concave_wrapper(original_prepay):
    """concave_marginal.py:102-113, verbatim: transform the gap, delegate."""
    def concave_prepay(loan_age, rate_gap, burnout, fico_z, ltv_z, beta1,
                       coefs=None):
        g_pp = np.abs(rate_gap) * 100.0
        g_concave = np.minimum(g_pp, CONCAVE_KINK_PP) + CONCAVE_SLOPE2 * (
            np.maximum(g_pp - CONCAVE_KINK_PP, 0.0)
        )
        gap_t = np.sign(rate_gap) * g_concave / 100.0
        return original_prepay(loan_age, gap_t, burnout, fico_z, ltv_z,
                               beta1=beta1, coefs=coefs)
    return concave_prepay


def _run_scored(loans, macro, empirical, transform: str, form: str,
                floor: float, pq: float) -> dict:
    """One US-regime microsim run at (transform, form, floor, elasticity).

    Extends concave_marginal.py:117-140 with the form dimension. Both
    mechanisms are mutated here and BOTH are restored in the finally block:
    the transform via competing_risks.prepay_hazard, the form via
    literature_hazard.FLOOR_MODE (read at call time inside
    literature_hazard.prepay_hazard, so it reaches the wrapper's delegate).
    """
    original_prepay = competing_risks.prepay_hazard
    literature_hazard.INVOLUNTARY_CPR_ANNUAL = floor
    literature_hazard.FLOOR_MODE = form
    out_path = OUT_DIR / (
        f"microsim_{transform}_{form}_floor{floor * 100:g}pct_pq{pq:g}.parquet"
    )
    try:
        if transform == "concave":
            competing_risks.prepay_hazard = _concave_wrapper(original_prepay)
        paths = run_qt_microsim(loan_sample=loans, macro=macro,
                                regimes=("US",), output=out_path,
                                p_q_shock_pct=pq)
        sim = paths["US"] if isinstance(paths, dict) else pd.read_parquet(out_path)
    finally:
        competing_risks.prepay_hazard = original_prepay
        literature_hazard.FLOOR_MODE = PRODUCTION_FORM
        literature_hazard.INVOLUNTARY_CPR_ANNUAL = PRODUCTION_FLOOR
    score = score_extension_risk(sim, empirical)
    return {
        "transform": transform,
        "form": form,
        "floor_annual_cpr_pct": floor * 100.0,
        "p_q_shock_pct": pq,
        "beta1": rothstein_beta1(pq / 100.0),
        "trapped_b": float(score["hazard_trapped_b"]),
        "share_pct": float(score["share_explained_pct"]),
        "r_lag0": (None if score["cross_correlation"].get(0) is None
                   else float(score["cross_correlation"].get(0))),
        "peak_lag": (None if score.get("best_lag") is None
                     else int(score["best_lag"])),
    }


def _gate(name, got, want, tol, report):
    diff = abs(got - want)
    ok = diff < tol
    report[name] = {"got": got, "want": want, "diff": diff, "tol": tol,
                    "bit_exact": diff == 0.0, "pass": bool(ok)}
    print(f"parity gate {name}: got {got:.10f} want {want:.10f} "
          f"diff {diff:.3e} [{'PASS' if ok else 'FAIL'}"
          f"{', bit-exact' if diff == 0.0 else ''}]")


def main() -> None:
    assert rothstein_beta1(0.0) == 0.0
    assert literature_hazard.FLOOR_MODE == PRODUCTION_FORM
    assert literature_hazard.INVOLUNTARY_CPR_ANNUAL == PRODUCTION_FLOOR
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---- committed anchors, consumed at runtime (never hard-coded alone) ----
    with open(NULL_ARTIFACT) as f:
        anchor = json.load(f)
    with open(CONCAVE_MARGINAL_ARTIFACT) as f:
        cm = json.load(f)
    with open(FLOOR_FORM_ARTIFACT) as f:
        ff = json.load(f)
    with open(FLOOR_FORM_OFFWINDOW_ARTIFACT) as f:
        ffo = json.load(f)
    with open(OOS_ARTIFACT) as f:
        oos = json.load(f)

    off_point_pct = oos["headline_oos_marginal"]["clean_floor_point_pct"]
    assert abs(off_point_pct - OFFWINDOW_POINT_FLOOR * 100.0) < 1e-9, off_point_pct
    for i, want in enumerate(COMMITTED_HULL_PP):
        assert abs(ffo["designated_interval_pp"][i] - want) < 1e-12, (i, want)

    ff_add4 = next(r for r in ff["rows"] if r["form"] == "additive"
                   and r["floor_annual_cpr_pct"] == 4.0)
    ffo_max_off = next(r for r in ffo["rows"] if r["form"] == "max"
                       and abs(r["floor_annual_cpr_pct"] - off_point_pct) < 1e-9)
    ffo_add_off = next(r for r in ffo["rows"] if r["form"] == "additive"
                       and abs(r["floor_annual_cpr_pct"] - off_point_pct) < 1e-9)
    ffo_add_hullmax = next(r for r in ffo["rows"] if r["form"] == "additive"
                           and abs(r["floor_annual_cpr_pct"] - 4.695) < 1e-9)

    print("Scoring empirical benchmark (shared macro frame, fetched once) …")
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)
    if not LOAN_SAMPLE_PATH.exists():
        raise FileNotFoundError(f"{LOAN_SAMPLE_PATH} missing")
    loans = pl.read_parquet(LOAN_SAMPLE_PATH)

    t0 = time.perf_counter()
    report: dict = {}
    legs: dict = {}
    floors = {"4": PRODUCTION_FLOOR, "4991": OFFWINDOW_POINT_FLOOR}

    # ---- the full 2x2x2 factorial, {central, null} at each cell ------------
    for transform in ("loglinear", "concave"):
        for form in ("max", "additive"):
            for ftag, floor in floors.items():
                for pqtag, pq in (("central", CENTRAL_PQ), ("null", NULL_PQ)):
                    key = f"{transform}_{form}_{ftag}_{pqtag}"
                    legs[key] = _run_scored(loans, macro, empirical,
                                            transform, form, floor, pq)
                    leg = legs[key]
                    print(f"  {key:38s} trapped ${leg['trapped_b']:8.3f}B  "
                          f"share {leg['share_pct']:7.3f}%")
    runtime_s = time.perf_counter() - t0

    def marginal_pp(transform, form, ftag):
        return (legs[f"{transform}_{form}_{ftag}_central"]["share_pct"]
                - legs[f"{transform}_{form}_{ftag}_null"]["share_pct"])

    def marginal_b(transform, form, ftag):
        return (legs[f"{transform}_{form}_{ftag}_central"]["trapped_b"]
                - legs[f"{transform}_{form}_{ftag}_null"]["trapped_b"])

    # ---- G0: base anchors, loglinear x max at both floors -------------------
    _gate("G0_loglin_max_4_central_b", legs["loglinear_max_4_central"]["trapped_b"],
          anchor["central_trapped_b"], TOL_PARITY, report)
    _gate("G0_loglin_max_4_null_b", legs["loglinear_max_4_null"]["trapped_b"],
          anchor["null_trapped_b"], TOL_PARITY, report)
    _gate("G0_loglin_max_4_marginal_pp", marginal_pp("loglinear", "max", "4"),
          anchor["lockin_marginal_share_pp"], TOL_PARITY, report)
    _gate("G0_loglin_max_4991_central_b",
          legs["loglinear_max_4991_central"]["trapped_b"],
          ffo_max_off["band"]["6.5"]["central_trapped_b"], TOL_PARITY, report)
    _gate("G0_loglin_max_4991_null_b",
          legs["loglinear_max_4991_null"]["trapped_b"],
          ffo_max_off["null_trapped_b"], TOL_PARITY, report)
    _gate("G0_loglin_max_4991_marginal_pp", marginal_pp("loglinear", "max", "4991"),
          ffo_max_off["band"]["6.5"]["marginal_pp"], TOL_PARITY, report)

    # ---- G1 (primary 1): concave x max @4.0% --------------------------------
    _gate("G1_concave_max_4_central_b", legs["concave_max_4_central"]["trapped_b"],
          cm["legs"]["concave_central_4"]["trapped_b"], TOL_PARITY, report)
    _gate("G1_concave_max_4_null_b", legs["concave_max_4_null"]["trapped_b"],
          cm["legs"]["concave_null_4"]["trapped_b"], TOL_PARITY, report)
    _gate("G1_concave_max_4_marginal_pp", marginal_pp("concave", "max", "4"),
          cm["concave_marginal_pp_at_4"], TOL_PARITY, report)

    # ---- G2 (primary 2): concave x max @4.991% ------------------------------
    _gate("G2_concave_max_4991_central_b",
          legs["concave_max_4991_central"]["trapped_b"],
          cm["legs"]["concave_central_4991"]["trapped_b"], TOL_PARITY, report)
    _gate("G2_concave_max_4991_null_b",
          legs["concave_max_4991_null"]["trapped_b"],
          cm["legs"]["concave_null_4991"]["trapped_b"], TOL_PARITY, report)
    _gate("G2_concave_max_4991_marginal_pp", marginal_pp("concave", "max", "4991"),
          cm["concave_marginal_pp_at_offwindow_point"], TOL_PARITY, report)

    # ---- G3 (primary 3): loglinear x additive @4.0% -------------------------
    _gate("G3_loglin_add_4_central_b",
          legs["loglinear_additive_4_central"]["trapped_b"],
          ff_add4["central"]["trapped_b"], TOL_PARITY, report)
    _gate("G3_loglin_add_4_null_b", legs["loglinear_additive_4_null"]["trapped_b"],
          ff_add4["null"]["trapped_b"], TOL_PARITY, report)
    _gate("G3_loglin_add_4_marginal_pp", marginal_pp("loglinear", "additive", "4"),
          ff_add4["lockin_marginal_share_pp"], TOL_PARITY, report)

    # ---- G4 (primary 4): loglinear x additive @4.991%, levels included ------
    _gate("G4_loglin_add_4991_central_b",
          legs["loglinear_additive_4991_central"]["trapped_b"],
          ffo_add_off["band"]["6.5"]["central_trapped_b"], TOL_PARITY, report)
    _gate("G4_loglin_add_4991_null_b",
          legs["loglinear_additive_4991_null"]["trapped_b"],
          ffo_add_off["null_trapped_b"], TOL_PARITY, report)
    _gate("G4_loglin_add_4991_marginal_pp",
          marginal_pp("loglinear", "additive", "4991"),
          ffo_add_off["band"]["6.5"]["marginal_pp"], TOL_PARITY, report)
    # the two off-window additive recovery LEVELS, replayed for parity. These
    # ARE stated in the manuscript (round-22 B2 added them at the additive-form
    # paragraph); the gate exists so they cannot drift away from the artifact.
    _gate("G4_loglin_add_4991_central_share_pct",
          legs["loglinear_additive_4991_central"]["share_pct"],
          ffo_add_off["band"]["6.5"]["central_share_pct"], TOL_PARITY, report)
    _gate("G4_loglin_add_4991_null_share_pct",
          legs["loglinear_additive_4991_null"]["share_pct"],
          ffo_add_off["null_share_pct"], TOL_PARITY, report)

    # ---- G5: beta1 = 0 transform invariance at every (form, floor) ----------
    for form in ("max", "additive"):
        for ftag in floors:
            _gate(f"G5_null_transform_invariance_{form}_{ftag}",
                  legs[f"concave_{form}_{ftag}_null"]["trapped_b"],
                  legs[f"loglinear_{form}_{ftag}_null"]["trapped_b"],
                  TOL_PARITY, report)

    hard_fail = [k for k, v in report.items() if not v["pass"]]

    # ---- the new cells ------------------------------------------------------
    new_cells = {}
    for ftag in floors:
        new_cells[ftag] = {
            "floor_annual_cpr_pct": floors[ftag] * 100.0,
            "null_trapped_b": legs[f"concave_additive_{ftag}_null"]["trapped_b"],
            "null_share_pct": legs[f"concave_additive_{ftag}_null"]["share_pct"],
            "central_trapped_b":
                legs[f"concave_additive_{ftag}_central"]["trapped_b"],
            "central_share_pct":
                legs[f"concave_additive_{ftag}_central"]["share_pct"],
            "marginal_b": marginal_b("concave", "additive", ftag),
            "marginal_pp": marginal_pp("concave", "additive", ftag),
        }

    ca4 = new_cells["4"]["marginal_pp"]
    ca_off = new_cells["4991"]["marginal_pp"]

    # ---- T3 degeneracy screen ----------------------------------------------
    nonfinite = [k for k, v in legs.items()
                 if not (math.isfinite(v["trapped_b"])
                         and math.isfinite(v["share_pct"]))]
    inert = [ftag for ftag, c in new_cells.items()
             if abs(c["marginal_pp"]) < INERT_PP]
    t3 = bool(hard_fail or nonfinite or inert)

    # ---- T1/T2 hull membership (closed interval) ----------------------------
    lo, hi = COMMITTED_HULL_PP
    membership = {}
    for ftag, m in (("4", ca4), ("4991", ca_off)):
        membership[ftag] = {
            "marginal_pp": m,
            "inside_committed_hull": bool(lo <= m <= hi),
            "distance_below_lo_pp": (lo - m) if m < lo else 0.0,
            "distance_above_hi_pp": (m - hi) if m > hi else 0.0,
            "distance_to_nearer_edge_pp": min(abs(m - lo), abs(m - hi)),
        }
    # ROUND-22 REVIEW FIX: the committed hull [3.891507, 13.097741] is an
    # OFF-WINDOW object -- floor_form_offwindow.py builds it from the three
    # off-window anchors only, and no production-floor cell is a member by
    # construction. Testing hull membership at the 4.0% production floor
    # therefore asks a question the hull cannot answer, and would have let a
    # production-floor cell outside the range fire T2 spuriously. Membership is
    # still REPORTED at both floors for the reader; only the off-window cell
    # decides the verdict.
    t1 = (not t3) and membership["4991"]["inside_committed_hull"]

    # implied hull: committed off-window ranges extended by the NEW off-window
    # cell only, matching floor_form_offwindow.py's construction rule. Emitted
    # as a LOWER BOUND on the widening (see the T2 spec above), never as a
    # replacement literal.
    implied_hull = [min(lo, ca_off), max(hi, ca_off)]

    # ---- S: separability difference-in-differences --------------------------
    interaction = {}
    for ftag in floors:
        form_effect_concave = (marginal_pp("concave", "additive", ftag)
                               - marginal_pp("concave", "max", ftag))
        form_effect_loglin = (marginal_pp("loglinear", "additive", ftag)
                              - marginal_pp("loglinear", "max", ftag))
        transform_effect_add = (marginal_pp("concave", "additive", ftag)
                                - marginal_pp("loglinear", "additive", ftag))
        transform_effect_max = (marginal_pp("concave", "max", ftag)
                                - marginal_pp("loglinear", "max", ftag))
        interaction[ftag] = {
            "floor_annual_cpr_pct": floors[ftag] * 100.0,
            "form_effect_under_loglinear_pp": form_effect_loglin,
            "form_effect_under_concave_pp": form_effect_concave,
            "transform_effect_under_max_pp": transform_effect_max,
            "transform_effect_under_additive_pp": transform_effect_add,
            "interaction_pp": transform_effect_add - transform_effect_max,
            "material": bool(abs(transform_effect_add - transform_effect_max)
                             > MATERIALITY_PP),
        }
    # ROUND-22 REVIEW FIX: s1 was `(not t3) and not any(material)`, so a T3
    # wiring failure emitted s1_separable=False -- indistinguishable in the
    # artifact from a genuine finding of non-separability. Separability is now
    # tri-state: None under T3 (not evaluated), True/False otherwise.
    s1 = (None if t3
          else (not any(v["material"] for v in interaction.values())))

    if t3:
        verdict = (
            "T3: DEGENERATE / PARITY FAILURE — "
            f"failed gates {hard_fail or 'none'}, non-finite legs "
            f"{nonfinite or 'none'}, inert concave-additive cells "
            f"{inert or 'none'}. Nothing interpretive is reported; the .tex "
            "literals and gate #69 are left alone until this is fixed."
        )
    elif t1:
        verdict = (
            "T1: HULL STANDS — the concave x additive marginal at central "
            f"elasticity lies inside the committed hull [{lo:.4f}, {hi:.4f}]pp "
            f"at both floors ({ca4:+.4f}pp @4.0%, {ca_off:+.4f}pp @4.991%). "
            "The five '$+3.9$ to $+13.1$' tex literals and gate #69 stand "
            "unchanged; report the cell as a completeness check scoped, "
            "explicitly, to the CENTRAL elasticity at the headline off-window "
            "anchor — the {5.5, 7.7} band ends of this cell are unrun, so the "
            "hull is not shown complete over {form x transform}."
        )
    else:
        verdict = (
            "T2: HULL MUST BE RE-DERIVED — the concave x additive marginal "
            f"falls outside the committed hull [{lo:.4f}, {hi:.4f}]pp "
            f"({ca4:+.4f}pp @4.0%, {ca_off:+.4f}pp @4.991%). The literal "
            "'$+3.9$ to $+13.1$' must move at all five tex sites and gate "
            "#69's designated_interval_pp must be re-pinned. implied_hull_pp "
            "is a LOWER BOUND on the widening, not the replacement literal: "
            "the unrun {4.695, 5.334}% x {5.5, 7.7} concave-additive cells can "
            "only widen it further and must be run first."
        )

    sep_verdict = (
        "S0: NOT EVALUATED — T3 fired, so separability was never measured. "
        "This is not a finding of non-separability."
        if s1 is None else
        "S1: |interaction| <= 1.0pp at both floors — the form and transform "
        "effects on the marginal are separable within the project's "
        "materiality convention, so tab:uncertainty line 509's parallel "
        "un-interacted listing is defensible as written; add a footnote "
        "recording that separability was measured, not assumed"
        if s1 else
        "S2: |interaction| > 1.0pp at a floor — the form and transform effects "
        "are NOT separable; tab:uncertainty line 509 must replace its two "
        "independent entries ('additive form $+11.2$' and 'concave transform "
        "$+5.1$') with the measured joint cell, and disclose the interaction "
        "term with its sign"
    ) if not t3 else "S: not evaluated (T3)"

    payload = {
        "mode": "concave_additive_marginal",
        "spec": (
            "full 2x2x2 factorial transform {loglinear, concave} x form "
            "{max, additive} x floor {4.0, 4.991}% annual CPR, central "
            "(p_q 6.5) + null (p_q 0) at every cell = 16 US-regime legs; "
            "concave transform = seasonality_concave_gap kink 2.0pp / slope2 "
            "0.5 patched onto competing_risks.prepay_hazard; form = "
            "literature_hazard.FLOOR_MODE, read at call time so the two "
            "mechanisms compose without new plumbing; production convention "
            "otherwise (75k sample, seed 42, shared macro frame, raw-basis "
            "scoring); parity gates G0-G5 at abs diff < 1e-9; ex-ante "
            "partition T1/T2/T3 on membership in the committed hull "
            "[3.891507360127463, 13.09774126267503] plus an orthogonal "
            "separability partition S1/S2 on the difference-in-differences "
            "interaction at the +/-1.0pp materiality convention"
        ),
        "legs": legs,
        "parity_gates": report,
        "parity_gates_all_pass": not hard_fail,
        "parity_gates_all_bit_exact": all(v["bit_exact"] for v in report.values()),
        "committed_hull_pp": COMMITTED_HULL_PP,
        "concave_additive_cells": new_cells,
        "concave_additive_marginal_pp_at_4": ca4,
        "concave_additive_marginal_b_at_4": new_cells["4"]["marginal_b"],
        "concave_additive_marginal_pp_at_offwindow_point": ca_off,
        "concave_additive_marginal_b_at_offwindow_point":
            new_cells["4991"]["marginal_b"],
        "concave_additive_central_share_pct_at_offwindow_point":
            new_cells["4991"]["central_share_pct"],
        "concave_additive_null_share_pct_at_offwindow_point":
            new_cells["4991"]["null_share_pct"],
        "hull_membership": membership,
        "implied_hull_pp": implied_hull,
        "implied_hull_is_lower_bound_only": True,
        "interaction": interaction,
        "max_abs_interaction_pp": max(abs(v["interaction_pp"])
                                     for v in interaction.values()),
        "t1_hull_stands": bool(t1),
        "t2_hull_must_be_rederived": bool((not t3) and not t1),
        "t3_degenerate": bool(t3),
        # tri-state: None means NOT EVALUATED (T3 fired), not "not separable"
        "s1_separable": (None if s1 is None else bool(s1)),
        "interpretive_verdict": verdict,
        "separability_verdict": sep_verdict,
        "degeneracy_detail": {
            "failed_gates": hard_fail,
            "nonfinite_legs": nonfinite,
            "inert_cells": inert,
        },
        # Echoed from the committed artifact, NOT recomputed here.
        "committed_additive_offwindow_levels_pct": {
            "note": ("the additive off-window recovery levels; already "
                     "committed in floor_form_offwindow_results.json AND "
                     "already disclosed in the .tex at line 784 (contrary to "
                     "the audit brief that commissioned this run), read here "
                     "for one-place verification and not recomputed"),
            "central_at_4991_pct": ffo_add_off["band"]["6.5"]["central_share_pct"],
            "central_at_4991_field":
                "rows[3].band['6.5'].central_share_pct (form=additive, floor=4.991)",
            "null_at_4991_pct": ffo_add_off["null_share_pct"],
            "null_at_4991_field":
                "rows[3].null_share_pct (form=additive, floor=4.991)",
            "central_at_hull_max_pct":
                ffo_add_hullmax["band"]["7.7"]["central_share_pct"],
            "central_at_hull_max_field":
                "rows[1].band['7.7'].central_share_pct (form=additive, "
                "floor=4.695, p_q 7.7 — the cell carrying the hull maximum "
                "marginal_pp 13.09774126267503)",
        },
        "runtime_s": runtime_s,
    }
    # ROUND-22 REVIEW FIX: under the non-finite branch of T3 the artifact used
    # to be written before the SystemExit below, producing a results JSON
    # carrying bare `NaN` literals -- invalid strict JSON, and a file a
    # downstream gate could read as if it meant something. Nothing is written
    # when a leg is non-finite; the run must be re-executed, not salvaged.
    if nonfinite:
        print(f"\nNOT WRITING {RESULTS_JSON.name}: non-finite legs "
              f"{nonfinite}. Artifact suppressed so no gate can read NaNs.")
    else:
        with open(RESULTS_JSON, "w") as f:
            json.dump(payload, f, indent=1)

    print(f"\nconcave x additive marginal: {ca4:+.4f}pp @4.0%   "
          f"{ca_off:+.4f}pp @4.991%")
    print(f"committed hull [{lo:+.4f}, {hi:+.4f}]pp   inside: "
          f"@4.0%={membership['4']['inside_committed_hull']} "
          f"@4.991%={membership['4991']['inside_committed_hull']}")
    for ftag, v in interaction.items():
        print(f"interaction @{v['floor_annual_cpr_pct']:.3f}%: "
              f"{v['interaction_pp']:+.4f}pp "
              f"(material={v['material']})")
    print(f"verdict: {verdict}")
    print(f"separability: {sep_verdict}")
    print(f"gates all pass: {not hard_fail}   runtime {runtime_s:,.0f}s")
    # T3 fails loudly in ALL of its forms, not only parity: a non-finite or
    # inert leg is a wiring failure, and exiting 0 on one would let a
    # downstream gate read an artifact whose numbers mean nothing (and, for
    # the non-finite case, an artifact carrying NaN literals).
    if t3:
        raise SystemExit(
            "T3 — do not build on this: failed gates "
            f"{hard_fail or 'none'}, non-finite legs {nonfinite or 'none'}, "
            f"inert concave-additive cells {inert or 'none'}"
        )


if __name__ == "__main__":
    main()
