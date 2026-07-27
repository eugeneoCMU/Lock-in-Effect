#!/usr/bin/env python3
"""
burnout_ablation.py — the beta_B = 0 ablation of Path B that the manuscript
quotes at four sites but never ran.

PRE-COMMITTED SPEC (fixed in this header BEFORE any run; ex-ante convention of
floor_form_test.py / oos_identification.py / floor_form_offwindow.py /
concave_marginal.py).

=======================================================================
THE DEFECT (round-22 provenance audit, CONFIRMED before this run)
=======================================================================
The manuscript asserts a burnout ablation at four sites:

  V.B / sec:pathb (tex line 324, the primary literal):
      "I test whether the channel is load-bearing with a beta_B = 0 rerun on
       the production seed: trapped liquidity moves by $6.6 billion (-0.9pp
       of benchmark, to 106.2%; endpoint rounding makes this -0.8pp if
       computed from the rounded shares), with the peak lag unchanged at -3."
  VI / sec:hazard-interp (line 584):   "burnout 0.9 points"
  VII / sec:discussion (line 588):     "switching burnout off moves Path B by
                                        $6.6 billion (0.9 points)"
  Conclusion / sec:conclusion (l. 899): "burnout 0.9 points"

(Line numbers are v18 as of this writing and a concurrent concision pass is
editing the same file: locate the four sites by their literals — "$6.6
billion", "burnout 0.9 points", "to 106.2\\%", "peak lag unchanged at $-3$" —
not by line number.)

There is NO committed artifact, NO script, NO TECHNICAL.md run record and NO
liveness gate behind any of it. config.py:55 sets beta_burnout = -0.5 and no
script in the repo ever overrides it to 0 — covariate_priors_estimation.py
zeroes beta_fico/beta_ltv only (its "zeroed" leg is the separate 1.3-point
FICO/LTV ablation the same sentences quote).

The only place in the repo carrying the implied values is ONE replicate row of
hazard/data/permutation_test_ablate_orig_results.csv (replicate 21) and, as
the extreme order statistic, permutation_test_ablate_orig_summary.json
null.trapped_b.min / null.share_pct.min:

      811.911646619444 B   and   106.16717896353396 %

which are the MINIMUM over 100 replicates of a completely unrelated
experiment — one that PERMUTES ORIGINATION TIME across the loan sample.
818.5300844066606 - 811.911646619444 = 6.6184  ->  "$6.6 billion";
107.0326190295068 - 106.16717896353396 = 0.8654  ->  "0.9 points";
811.911646619444/764.7482532227002 -> 106.167%   ->  "to 106.2%";
that experiment's peak_lag_distribution is {-3: 100} -> "peak lag unchanged
at -3". Every element of the manuscript's sentence is reproduced by the wrong
object, so the number was read off the origination-permutation minimum (not
even its mean, 812.8957 / 106.2959) rather than produced by a beta_B = 0 run.
Gate G0e below asserts that identification bit-exactly, so the artifact
carries the diagnosis and not just the replacement.

This script produces the real number.

=======================================================================
STANDALONE vs A FOURTH SCENARIO IN covariate_priors_estimation.py
=======================================================================
covariate_priors_estimation.py already has the mechanical scaffold (a PRIORS
dict, a coef_override plumbed into run_variant, and a "zeroed" scenario). A
fourth scenario there would be the WRONG design, independently of the
no-edit constraint under which this file was authored:

  (a) NO PARITY. covariate_priors_estimation reads its production comparator
      (818.5300844066606) out of the cached microsim_results.parquet and
      never replays it. A burnout leg bolted there would inherit zero parity
      discipline — which is the exact defect class this run exists to repair.
  (b) IRRELEVANT DEPENDENCIES. That script's remit is ESTIMATION: a Poisson
      PML on the Freddie stratum-month panel plus a 60-rep cluster bootstrap,
      requiring PANEL_PATH, HAZARD_COEF_PATH and statsmodels before it ever
      touches the microsim. The burnout ablation needs none of that and must
      not become unrunnable when the panel is absent.
  (c) WRONG LEG SET. It runs one floor (production) and no beta_1 = 0 null,
      so it cannot state the ablation at the off-window floor the paper
      headlines, and cannot state it as a marginal — the identified object.
  (d) ARTIFACT UNIT. The audit found a missing artifact/gate/TECHNICAL record;
      those attach to a run, and the run is this one.

Followup (someone else lands it): covariate_priors_estimation.py's
"production" comparator should either be replaced by a fresh replay gated
against no_lockin_null_results.json, or cross-gated against this script's
G1, so the FICO/LTV 1.3-point literal acquires the parity the burnout literal
was missing. That file is NOT edited here.

=======================================================================
SPEC (fixed ex ante)
=======================================================================
- Ablation: literature_hazard.LITERATURE_COEFS["beta_burnout"] 0.0 vs the
  production -0.5, mutated IN PLACE (the dict is the same object as
  config.LITERATURE_COEFS, and prepay_hazard resolves it from the module
  global at call time) and restored by clear+update in a finally block with a
  post-restore assertion. The in-place mutation is the ONLY available route:
  prepay_hazard takes a `coefs` argument, but competing_risks.monthly_step
  never forwards it, so the parameter is unreachable from the engine.
  Nothing else changes: burnout STATE accumulation (cohort prepaid UPB share)
  is untouched; only its coefficient is switched off.
- Basis: the STANDALONE raw scorer, extension_risk.score_extension_risk —
  the basis the "to 106.2%" literal is on (production central is 107.033%
  standalone, 97.937% shared; 107.033 - 0.865 = 106.167 -> "106.2%"). The
  shared-basis image is emitted alongside via the committed flat offset
  (calibration_reconciliation_results.json basis_map offset_pp =
  9.096091632702699 = $69.56220187263008B over $764.7482532227002B), read at
  runtime and gated. Percentage-POINT deltas are basis-invariant here because
  the netting is a constant dollar flow over a constant denominator, so the
  "0.9 points" quoted at lines 584/588/899 inside shared-basis paragraphs is
  legitimately basis-free; the LEVEL "106.2%" is standalone-only and is
  labelled as such in the artifact.
- Floors: {4.0% (production, the floor the 106.2% literal is on),
  4.991% (the committed off-window point floor the paper headlines, consumed
  from oos_identification_results.json and asserted equal at runtime)}.
  Rationale for the second floor: under the production hard-max floor form
  the burnout multiplier exp(beta_B * B) is inert wherever the floor binds,
  so raising the floor censors the channel. The three interpretive sites at
  lines 584/588/899 quote the ablation inside paragraphs whose other figures
  (91.3%, 85.7%) are at the off-window calibration; without this leg the
  ablation cannot be stated on the calibration the paper headlines.
- Legs per floor: production central (p_q 6.5) + production null (p_q 0) +
  burnout-off central (p_q 6.5) + burnout-off null (p_q 0). Eight US-regime
  microsim runs total. The null legs are required because the burnout state
  is endogenous to realized prepayment, so the ablation moves the
  beta_1 = 0 null too and the identified marginal must be re-differenced
  rather than assumed invariant.
- Production convention otherwise: committed 75k loan sample, RNG_SEED = 42
  passed explicitly, US regime only (the concave_marginal convention; the US
  leg is regime-tuple invariant and G1/G2/G6/G7 verify this against the
  committed two-regime anchors), one shared macro frame fetched once, hard-max
  floor form throughout (the form dimension is floor_form_offwindow.py's
  remit), caches not consulted for the fresh legs (own parquets under
  data/burnout_ablation/).
- Bind instrumentation: the value-preserving tally wrapper of
  oos_identification.py / floor_sweep.py (returns exactly what production
  returns; re-evaluates with the floor zeroed to count bound loan-months).
  It supplies the committed bind anchor for G7 and quantifies how much of the
  burnout channel the floor censors at each floor.

=======================================================================
PARITY GATES — all run BEFORE anything new is reported; any FAIL raises
SystemExit and the artifact is marked parity_gates_all_pass = false.
Tolerance is BIT-EXACT (< 1e-9) on every dollar and share anchor, not the
house +/-$0.01B: oos_identification_results.json records got == want to all
16 digits for the fresh 4.0% legs, and concave_marginal_results.json records
the same under this script's exact US-only convention, so the committed
anchors are reproducible bit-exactly and a looser tolerance would hide drift.
=======================================================================
  FREE GATES (no microsim; run first so input drift is caught in seconds)
  G0a benchmark frame: score_extension_risk empirical_trapped_b must equal
      the committed cap benchmark $764.7482532227002B. A FAIL here means FRED
      or SOMA revised and NOTHING downstream is comparable to the committed
      artifacts — distinguishes input drift from engine drift.
  G0b committed production cache (microsim_results.parquet) rescored must
      equal $818.5300844066606B.
  G0c committed null cache (microsim_results_pq0.0.parquet) rescored must
      equal $748.1850239867648B.
  G0d WIRING, analytic: with burnout = 1.0 and a 1000bp in-the-money gap
      (floor asserted non-binding in both legs), the ratio
      h_prepay(beta_B = 0) / h_prepay(beta_B = -0.5) must equal exp(0.5) to
      1e-12. A FAIL means the coefficient override does not reach the hazard
      and every ablation number below is meaningless.
  G0d2 LEAK, analytic: with burnout = 0.0 the two coefficient settings must
      give identical hazards to 1e-12 (expected diff exactly 0.0), because
      beta_B multiplies burnout. A FAIL means the override leaks into a
      non-burnout
      channel and BLOCKS interpretation (the analogue of concave_marginal's
      G3 transform-invariance gate).
  G0e PROVENANCE, forensic: permutation_test_ablate_orig_summary.json
      null.trapped_b.min == 811.911646619444 and null.share_pct.min ==
      106.16717896353396, and the production central minus those two equals
      the manuscript's $6.6B / 0.9pp at the manuscript's own printed
      precision. Pins the misattribution in the artifact.
  G0f/G0g BASIS: the committed basis_map is internally consistent
      (offset_pp == curtailment/cap * 100) and reproduces the committed
      shared central 97.9365273968041 from the standalone 107.0326190295068.
  ENGINE GATES (fresh runs, production coefficients)
  G1 fresh production central @4.0%  == $818.5300844066606B
     (no_lockin_null_results.json central_trapped_b)
  G2 fresh production null    @4.0%  == $748.1850239867648B
     (no_lockin_null_results.json null_trapped_b)
  G3 fresh marginal @4.0% == $70.34506041989584B and +9.198459770709789pp
     (no_lockin_null_results.json lockin_marginal_b /
      lockin_marginal_share_pp)
  G4 fresh production central share @4.0% == 107.0326190295068 and null share
     == 97.83415925879702 (the two shares the 106.2% literal is derived from)
  G5 fresh production central peak lag @4.0% == -3 (the baseline of the
     "peak lag unchanged at -3" clause)
  G6 fresh production central @4.991% == $767.5264524465003B and null @4.991%
     == $724.9180585654117B (oos_identification_results.json
      instrument1_marginal_table, floor 4.991, band 6.5)
  G7 floor-bind anchor: fresh production central @4.0% bind share ==
     0.36269282595934704 over 1683124 US loan-months
     (oos_identification_results.json parity_gates.bind_instrumentation)
  G8 restoration: after every leg, LITERATURE_COEFS["beta_burnout"] == -0.5
     and INVOLUNTARY_CPR_ANNUAL == 0.04 (asserted inside _run_scored).

=======================================================================
EX-ANTE INTERPRETIVE THRESHOLDS — fixed here BEFORE the run. The primary
verdict is a partition of the signed standalone-basis share delta at the
PRODUCTION floor, d_pp = share(beta_B = 0) - share(beta_B = -0.5) @ 4.0%,
because that is the object the manuscript's "-0.9pp / to 106.2%" literal
names. Precedence T3 -> T1 -> T2; no further discretion after the run.
=======================================================================
  T3 (DEGENERATE) if |d_$| < $0.01B at BOTH floors while G0d PASSES: the
     burnout channel is numerically inert under the production floor form.
     NOTE (round-22 review): the run CANNOT discriminate floor censoring
     from a burnout state that never accumulates (agents.py initialises
     cohort_burnout to zeros), so the T3 wording must say 'inert under the
     production floor form', report the bind share as context, and NOT
     assert censoring as the cause. All four sites lose
     the number rather than restating it: the sentence becomes "the burnout
     coefficient is inert under the production hard-max floor, because the
     involuntary floor binds in <bind share> of U.S. loan-months", the
     "$6.6 billion / 0.9 points / 106.2% / peak lag unchanged" literals are
     DELETED, and burnout is removed from the list of ablated mechanisms in
     lines 584/588/899. (If G0d FAILS the run is VOID, not T3 — the override
     never reached the hazard; SystemExit fires and no verdict is emitted.)
  T1 (LITERAL STANDS) if |d_pp - (-0.9)| <= 0.2pp: the manuscript's magnitude
     survives. The four sites keep their wording; the run tag
     \\texttt{burnout\\_ablation} is added at line 324, TECHNICAL.md gets the
     run record, and the liveness gate pins the artifact. The provenance
     defect is still disclosed: the number was previously unbacked and is now
     replaced by the committed value, and any digit that the artifact
     contradicts is restated under R1/R2/P1 below even inside T1.
  T2 (LITERAL FALSIFIED) if d_pp is outside [-1.1, -0.7] and |d_$| >= $0.01B
     at either floor: the manuscript's ablation magnitude and/or sign is
     wrong. ALL FOUR sites must be restated from this artifact — line 324's
     full clause (dollars, points, level, peak lag), and the "burnout 0.9
     points" / "moves Path B by $6.6 billion (0.9 points)" phrases at lines
     584, 588 and 899 — and if d_pp > 0 the sentences must additionally flip
     direction (switching burnout off RAISES recovery), which changes the
     rhetorical role of the ablation from "mechanism is small" to "mechanism
     pushes the other way".

  ROUNDING/CLAUSE CHECKS, applied in EVERY branch (each independently
  pre-committed; each failure obliges restating only its own literal):
  R1 LEVEL: |share(beta_B = 0) @4.0% standalone - 106.2| <= 0.05pp, the
     half-width of the manuscript's own printed precision. Else line 324's
     "to 106.2%" is restated from the artifact.
  R2 DOLLARS: |d_$ - (-6.6)| <= $0.05B. Else the "$6.6 billion" at lines 324,
     588 is restated from the artifact.
  P1 PEAK LAG: peak lag of the beta_B = 0 central @4.0% == -3. Else line
     324's "with the peak lag unchanged at -3" is restated.

  M1 MARGINAL MATERIALITY (the house +/-1.0pp convention of
     floor_form_test.py / concave_marginal.py, applied to this ablation): if
     |marginal_pp(beta_B = 0) - marginal_pp(beta_B = -0.5)| > 1.0pp at either
     floor, the burnout coefficient is LOAD-BEARING for the identified
     marginal (not merely for the level) and must be carried as a dimension
     in the uncertainty consolidation (Table 8) and quoted in
     sec:identification; otherwise the ablation is a level statement only and
     the marginal is reported as burnout-invariant. This is reported in both
     T-branches: the manuscript currently makes NO claim about burnout and
     the marginal, so M1 can only add a claim, never rescue one.

  OFF-WINDOW REPORTING (unconditional): the ablation at the 4.991% headline
  floor is reported beside the 4.0% figure wherever the ablation is quoted at
  headline level, on the same standalone/shared pair as Table 10
  (tab:bases), so the mechanism bound sits on the calibration the paper
  headlines rather than on the demoted in-sample one.

Run:  cd hazard && python3 burnout_ablation.py
      -> data/burnout_ablation_results.json (+ per-run parquets under
         data/burnout_ablation/, regenerable, not committed)

Runtime budget: 8 US-regime microsim legs. Evidence: concave_marginal ran 6
US-only legs in 66.3s (11.1s/leg, artifact runtime_s); oos_identification ran
36 two-regime legs WITH the same bind instrumentation in 774.8s (10.8s per
regime-leg, artifact runtime_s); permutation_test_ablate_orig_results.csv
records runtime_s over its 101 rows with min 6.0, median 9.2, mean 10.8 and
max 30.4 (14.0 is the single `real` row). Expect ~90s of engine time plus one
FRED + SOMA fetch; budget 3 minutes, hard ceiling 10.
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
from config import LITERATURE_COEFS, LOAN_SAMPLE_PATH, MICROSIM_RESULTS_PATH, RNG_SEED
from extension_risk import score_extension_risk
from literature_hazard import (
    BETA1_PREPAY_MID,
    cpr_annual_to_monthly_hazard,
    rothstein_beta1,
)
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly
from microsim_engine import run_qt_microsim

DATA_DIR = Path(__file__).parent / "data"
OUT_DIR = DATA_DIR / "burnout_ablation"
RESULTS_JSON = DATA_DIR / "burnout_ablation_results.json"
NULL_ARTIFACT = DATA_DIR / "no_lockin_null_results.json"
NULL_CACHE = DATA_DIR / "microsim_results_pq0.0.parquet"
OOS_ARTIFACT = DATA_DIR / "oos_identification_results.json"
CALIB_ARTIFACT = DATA_DIR / "calibration_reconciliation_results.json"
PERM_SUMMARY = DATA_DIR / "permutation_test_ablate_orig_summary.json"

# ---- production convention -------------------------------------------------
PRODUCTION_FLOOR = 0.04
# The engine floor must be the DECIMAL literal, not the committed percent
# divided by 100: oos_identification quantizes with round(x, 6) on the decimal,
# so it simulated exactly the double 0.04991, whereas 4.991/100.0 is a
# different double (0.049909999999999996). Deriving it from the artifact's
# percent would break the bit-exact G6 replay. The percent is asserted equal
# to the committed clean_floor_point_pct at runtime instead.
OFFWINDOW_POINT_FLOOR = 0.04991
CENTRAL_PQ = 6.5
NULL_PQ = 0.0
PRODUCTION_BETA_BURNOUT = -0.5
ABLATED_BETA_BURNOUT = 0.0

# ---- tolerances ------------------------------------------------------------
TOL_EXACT = 1e-9      # parity: bit-exact replay of committed artifacts
TOL_WIRING = 1e-12    # analytic wiring/leak gates
TOL_B_HOUSE = 0.01    # house dollar tolerance, reported for comparability only

# ---- the manuscript literals under test (tex lines 324/584/588/899) --------
CLAIMED_DELTA_B = -6.6
CLAIMED_DELTA_PP = -0.9
CLAIMED_LEVEL_PCT = 106.2
CLAIMED_PEAK_LAG = -3
T1_TOL_PP = 0.2
# ROUND-22 REVIEW FIX: makes the pre-registered "<=" windows genuinely inclusive
# at their stated endpoints instead of inclusive-or-not by accident of binary
# representation. Far below any reporting precision (the tightest window here is
# 0.05), so it cannot change a verdict that was not already exactly on a
# boundary -- it only makes the code implement the docstring.
BOUNDARY_EPS = 1e-9
R1_HALF_WIDTH_PP = 0.05
R2_HALF_WIDTH_B = 0.05
DEGENERACY_TOL_B = 0.01
MARGINAL_MATERIALITY_PP = 1.0

# ---- committed anchors (all re-read from artifacts at runtime; these are the
# ---- ex-ante values the assertions below pin them to) ----------------------
COMMITTED_CENTRAL_B = 818.5300844066606
COMMITTED_NULL_B = 748.1850239867648
COMMITTED_CENTRAL_SHARE = 107.0326190295068
COMMITTED_NULL_SHARE = 97.83415925879702
COMMITTED_CAP_BENCHMARK_B = 764.7482532227002
COMMITTED_OFFSET_PP = 9.096091632702699
COMMITTED_SHARED_CENTRAL_SHARE = 97.9365273968041
COMMITTED_OFFWINDOW_CENTRAL_B = 767.5264524465003
COMMITTED_OFFWINDOW_NULL_B = 724.9180585654117
COMMITTED_BIND_SHARE = 0.36269282595934704
COMMITTED_BIND_N = 1683124
PERM_MIN_TRAPPED_B = 811.911646619444        # the misattributed source values
PERM_MIN_SHARE_PCT = 106.16717896353396

_ORIG_PREPAY = competing_risks.prepay_hazard


# ======================================================================
# Bind instrumentation (value-preserving; identical to oos_identification /
# floor_sweep). Returns exactly what production returns.
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
# Gate helper
# ======================================================================
def _gate(name: str, got, want, tol: float, report: dict) -> None:
    ok = abs(float(got) - float(want)) < tol
    report[name] = {
        "got": float(got), "want": float(want), "tol": tol, "pass": bool(ok),
    }
    print(f"parity gate {name}: got {float(got):.10f} want {float(want):.10f} "
          f"[{'PASS' if ok else 'FAIL'}]")


# ======================================================================
# One scored engine leg
# ======================================================================
def _run_scored(
    loans: pl.DataFrame,
    macro: pd.DataFrame,
    empirical: pd.DataFrame,
    floor: float,
    pq: float,
    beta_burnout: float,
    tag: str,
) -> dict:
    """One US-regime microsim at (floor, elasticity, beta_burnout).

    The coefficient override mutates literature_hazard.LITERATURE_COEFS in
    place — the only route into the engine, because monthly_step never
    forwards prepay_hazard's `coefs` argument — and is restored by
    clear+update in the finally block, with the restoration asserted (G8).
    """
    saved = dict(literature_hazard.LITERATURE_COEFS)
    tally = BindTally()
    out_path = OUT_DIR / f"microsim_{tag}.parquet"
    literature_hazard.INVOLUNTARY_CPR_ANNUAL = floor
    literature_hazard.LITERATURE_COEFS["beta_burnout"] = beta_burnout
    competing_risks.prepay_hazard = _tallying_prepay(tally)
    try:
        run_qt_microsim(
            loan_sample=loans,
            macro=macro,
            regimes=("US",),
            seed=RNG_SEED,
            output=out_path,
            p_q_shock_pct=pq,
        )
    finally:
        competing_risks.prepay_hazard = _ORIG_PREPAY
        literature_hazard.INVOLUNTARY_CPR_ANNUAL = PRODUCTION_FLOOR
        literature_hazard.LITERATURE_COEFS.clear()
        literature_hazard.LITERATURE_COEFS.update(saved)
    # G8 restoration (hard, in-line: a leaked override would silently
    # contaminate every later leg)
    assert literature_hazard.LITERATURE_COEFS["beta_burnout"] == (
        PRODUCTION_BETA_BURNOUT
    ), "beta_burnout not restored — later legs are contaminated"
    assert literature_hazard.INVOLUNTARY_CPR_ANNUAL == PRODUCTION_FLOOR, (
        "involuntary floor not restored — later legs are contaminated"
    )
    sim = pd.read_parquet(out_path)
    score = score_extension_risk(sim, empirical)
    return {
        "tag": tag,
        "beta_burnout": float(beta_burnout),
        "floor_annual_cpr_pct": floor * 100.0,
        "p_q_shock_pct": pq,
        "beta1": rothstein_beta1(pq / 100.0),
        "trapped_b": float(score["hazard_trapped_b"]),
        "share_pct": float(score["share_explained_pct"]),
        "empirical_trapped_b": float(score["empirical_trapped_b"]),
        "r_lag0": (None if score["cross_correlation"].get(0) is None
                   else float(score["cross_correlation"].get(0))),
        "peak_lag": (None if score.get("best_lag") is None
                     else int(score["best_lag"])),
        "mean_us_cpr_pct": float(sim["hazard_cpr_pct"].mean()),
        "floor_bind_share": float(tally.share),
        "floor_bind_loan_months": int(tally.n),
    }


# ======================================================================
# Free analytic gates: does the override reach the hazard, and only there?
# ======================================================================
def _wiring_gates(report: dict) -> None:
    """G0d (response) and G0d2 (no leak), both analytic and exact."""
    age = np.array([60.0])
    zeros = np.zeros(1)
    gap_itm = np.array([0.10])   # 1000bp in the money -> floor cannot bind
    burn_one = np.array([1.0])

    saved = dict(literature_hazard.LITERATURE_COEFS)
    try:
        literature_hazard.LITERATURE_COEFS["beta_burnout"] = (
            PRODUCTION_BETA_BURNOUT
        )
        h_prod = float(literature_hazard.prepay_hazard(
            age, gap_itm, burn_one, zeros, zeros, beta1=BETA1_PREPAY_MID)[0])
        h_prod_b0 = float(literature_hazard.prepay_hazard(
            age, gap_itm, zeros, zeros, zeros, beta1=BETA1_PREPAY_MID)[0])
        literature_hazard.LITERATURE_COEFS["beta_burnout"] = (
            ABLATED_BETA_BURNOUT
        )
        h_off = float(literature_hazard.prepay_hazard(
            age, gap_itm, burn_one, zeros, zeros, beta1=BETA1_PREPAY_MID)[0])
        h_off_b0 = float(literature_hazard.prepay_hazard(
            age, gap_itm, zeros, zeros, zeros, beta1=BETA1_PREPAY_MID)[0])
    finally:
        literature_hazard.LITERATURE_COEFS.clear()
        literature_hazard.LITERATURE_COEFS.update(saved)

    h_floor = float(cpr_annual_to_monthly_hazard(
        np.array([PRODUCTION_FLOOR], dtype=np.float64))[0])
    non_binding = (h_prod > h_floor) and (h_off > h_floor)
    report["G0d_probe_floor_non_binding"] = {
        "h_prod": h_prod, "h_off": h_off, "h_floor": h_floor,
        "pass": bool(non_binding),
    }
    print(f"parity gate G0d_probe_floor_non_binding: h_prod {h_prod:.10f} "
          f"h_off {h_off:.10f} h_floor {h_floor:.10f} "
          f"[{'PASS' if non_binding else 'FAIL'}]")
    # burnout = 1.0, so h ratio = exp(beta_off * 1) / exp(beta_prod * 1)
    _gate("G0d_beta_burnout_response", h_off / h_prod,
          math.exp(ABLATED_BETA_BURNOUT - PRODUCTION_BETA_BURNOUT),
          TOL_WIRING, report)
    _gate("G0d2_no_leak_at_zero_burnout", h_off_b0 - h_prod_b0, 0.0,
          TOL_WIRING, report)


# ======================================================================
# The pre-committed interpretive rule, as pure functions so tests exercise
# THE RULE and not a copy of it (the abstract_hedge_check convention in
# tools/liveness_gates.py). Boundary semantics, fixed ex ante:
#   T3 degeneracy uses STRICT  < DEGENERACY_TOL_B on BOTH floors
#   T1 window     uses INCLUSIVE <= T1_TOL_PP around CLAIMED_DELTA_PP
#   R1/R2         use INCLUSIVE <= their half-widths
#   M1            uses STRICT  > MARGINAL_MATERIALITY_PP on EITHER floor
# ======================================================================
def classify_verdict(d_pp: float, d_b_production: float,
                     d_b_offwindow: float) -> str:
    """T3 -> T1 -> T2, in that precedence. Assumes G0d (wiring) PASSED; if it
    did not, main() raises before any verdict is emitted and T3 is unreachable
    (a dead override must never be read as a censored channel)."""
    if (abs(d_b_production) < DEGENERACY_TOL_B
            and abs(d_b_offwindow) < DEGENERACY_TOL_B):
        return "T3"
    # ROUND-22 REVIEW FIX: the docstring pre-registers this window as
    # INCLUSIVE ("|d_pp - (-0.9)| <= 0.2pp"), but in IEEE-754 the raw
    # comparison is EXCLUSIVE at both endpoints -- abs(-1.1 - -0.9) is
    # 0.20000000000000007 and abs(-0.7 - -0.9) is 0.19999999999999996 only
    # by luck of representation. A pre-registration whose code does not
    # implement its stated rule is exactly the defect class this paper
    # audits, so the boundary is made inclusive to a representation
    # epsilon rather than left to the float.
    if abs(d_pp - CLAIMED_DELTA_PP) <= T1_TOL_PP + BOUNDARY_EPS:
        return "T1"
    return "T2"


def claim_literal_checks(burnout_off_share_pct: float, d_b: float,
                         burnout_off_peak_lag) -> tuple[bool, bool, bool]:
    """R1 (the 106.2% level), R2 (the $6.6B delta), P1 (the -3 peak lag)."""
    # same inclusive-boundary treatment as classify_verdict (round-22 review)
    r1 = abs(burnout_off_share_pct - CLAIMED_LEVEL_PCT) <= R1_HALF_WIDTH_PP + BOUNDARY_EPS
    r2 = abs(d_b - CLAIMED_DELTA_B) <= R2_HALF_WIDTH_B + BOUNDARY_EPS
    p1 = burnout_off_peak_lag == CLAIMED_PEAK_LAG
    return bool(r1), bool(r2), bool(p1)


def marginal_materiality(marginal_delta_pp_production: float,
                         marginal_delta_pp_offwindow: float) -> bool:
    """M1: is the burnout coefficient load-bearing for the MARGINAL?"""
    return bool(abs(marginal_delta_pp_production) > MARGINAL_MATERIALITY_PP
                or abs(marginal_delta_pp_offwindow) > MARGINAL_MATERIALITY_PP)


def verdict_text(band: str, d_pp: float, bind_share_4: float,
                 bind_share_off: float) -> str:
    """The prescriptive sentence attached to each band, fixed ex ante."""
    if band == "T3":
        return (
            "T3: the burnout coefficient is numerically INERT under the "
            "production hard-max floor at both the production and off-window "
            "floors (|delta| < $0.01B), while the analytic wiring gate G0d "
            "passes — the channel is censored by the involuntary floor, not "
            "merely small. DELETE the '$6.6 billion / 0.9 points / to 106.2% "
            "/ peak lag unchanged' literals at all four manuscript sites "
            "(V.B Path B, VI Interpretation, VII Discussion, Conclusion) and "
            "replace them with the censoring statement plus the floor-bind "
            f"share ({bind_share_4 * 100:.1f}% of U.S. loan-months at the "
            f"4.0% floor, {bind_share_off * 100:.1f}% at 4.991%); remove "
            "burnout from the ablated-mechanism list."
        )
    if band == "T1":
        return (
            "T1: the recomputed beta_B = 0 ablation lands within +/-0.2pp of "
            "the manuscript's claimed -0.9pp — the literal magnitude stands, "
            "but it now rests on a committed artifact instead of on the "
            "origination-permutation minimum it was read off. Keep the "
            "wording at all four sites, add the burnout_ablation run tag at "
            "the V.B site, and restate any single digit that R1/R2/P1 "
            "contradict."
        )
    return (
        "T2: the recomputed beta_B = 0 ablation differs from the "
        "manuscript's claimed -0.9pp by more than 0.2pp — the literal is "
        "FALSIFIED. Restate all four sites (V.B Path B, VI Interpretation, "
        "VII Discussion, Conclusion) from this artifact: the dollar delta, "
        "the point delta, the 106.2% level and the peak-lag clause"
        + (", and flip the direction of the sentences: switching burnout off "
           "RAISES recovery." if d_pp > 0 else ".")
    )


def main() -> None:
    assert rothstein_beta1(0.0) == 0.0, "p_q shock 0 must give exactly beta1=0"
    assert RNG_SEED == 42, f"RNG_SEED must be 42, got {RNG_SEED}"
    assert LITERATURE_COEFS["beta_burnout"] == PRODUCTION_BETA_BURNOUT, (
        f"production beta_burnout drifted from {PRODUCTION_BETA_BURNOUT}"
    )
    assert literature_hazard.FLOOR_MODE == "max", "production floor form is max"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---- committed anchors, read at runtime and pinned ---------------------
    with open(NULL_ARTIFACT) as f:
        anchor = json.load(f)
    with open(OOS_ARTIFACT) as f:
        oos = json.load(f)
    with open(CALIB_ARTIFACT) as f:
        calib = json.load(f)
    with open(PERM_SUMMARY) as f:
        perm = json.load(f)

    for got, want in (
        (anchor["central_trapped_b"], COMMITTED_CENTRAL_B),
        (anchor["null_trapped_b"], COMMITTED_NULL_B),
        (anchor["central_share_pct"], COMMITTED_CENTRAL_SHARE),
        (anchor["null_share_pct"], COMMITTED_NULL_SHARE),
        # the permutation summary's "real" row IS the production central; this
        # pins it before its peak lag is used as G5's anchor
        (perm["real"]["trapped_b"], COMMITTED_CENTRAL_B),
        (perm["real"]["share_pct"], COMMITTED_CENTRAL_SHARE),
    ):
        assert abs(got - want) < TOL_EXACT, (got, want)

    off_point = oos["headline_oos_marginal"]["clean_floor_point_pct"]
    assert abs(off_point - OFFWINDOW_POINT_FLOOR * 100) < TOL_EXACT
    off_row = next(r for r in oos["instrument1_marginal_table"]
                   if abs(r["floor_annual_cpr_pct"] - off_point) < TOL_EXACT)
    off_central_committed = off_row["band"]["6.5"]["central_trapped_b"]
    off_null_committed = off_row["null_trapped_b"]
    off_marginal_pp_committed = off_row["band"]["6.5"]["marginal_pp"]
    assert abs(off_central_committed - COMMITTED_OFFWINDOW_CENTRAL_B) < TOL_EXACT
    assert abs(off_null_committed - COMMITTED_OFFWINDOW_NULL_B) < TOL_EXACT
    # The committed bind anchor is a U.S.-loan-month count even though oos ran
    # the ("US","Danish") tuple: competing_risks routes the Danish leg through
    # berger_calibration unless the moving anchor is 'us_intercept', and the
    # module default is 'dk_level'. So the US-only convention here reproduces
    # both the share and the raw count. G7 is the check on that claim.
    bind_anchor = oos["parity_gates"]["bind_instrumentation"]
    assert abs(bind_anchor["share_got"] - COMMITTED_BIND_SHARE) < TOL_EXACT
    assert int(bind_anchor["n_got"]) == COMMITTED_BIND_N

    basis = calib["basis_map"]
    offset_pp = float(basis["offset_pp"])
    cap_b = float(basis["cap_benchmark_b"])
    curtail_b = float(basis["curtailment_netted_b"])
    assert abs(cap_b - COMMITTED_CAP_BENCHMARK_B) < TOL_EXACT
    assert abs(offset_pp - COMMITTED_OFFSET_PP) < TOL_EXACT

    t0 = time.perf_counter()
    report: dict = {}

    # ------------------------------------------------------------------
    # FREE GATES (no engine): basis arithmetic, provenance, wiring
    # ------------------------------------------------------------------
    print("\n--- free gates (no microsim) ---")
    _gate("G0f_offset_pp_internal", offset_pp, curtail_b / cap_b * 100.0,
          TOL_EXACT, report)
    # ROUND-22 REVIEW FIX: was asserted against a bare module constant, so a
    # change in the committed shared central would have left G0g passing.
    # Read the want side from the artifact and cross-check the constant.
    _shared_want = float(calib["gates"]["A_committed_4pct_parity"]
                              ["central"]["shared_share_want_pct"])
    assert abs(_shared_want - COMMITTED_SHARED_CENTRAL_SHARE) < 1e-12, (
        f"committed shared central moved: artifact {_shared_want} vs "
        f"module constant {COMMITTED_SHARED_CENTRAL_SHARE}")
    _gate("G0g_shared_central_from_standalone",
          COMMITTED_CENTRAL_SHARE - offset_pp,
          _shared_want, TOL_EXACT, report)
    perm_min_b = float(perm["null"]["trapped_b"]["min"])
    perm_min_share = float(perm["null"]["share_pct"]["min"])
    perm_mean_b = float(perm["null"]["trapped_b"]["mean"])
    perm_mean_share = float(perm["null"]["share_pct"]["mean"])
    _gate("G0e_perm_min_trapped_b", perm_min_b, PERM_MIN_TRAPPED_B,
          TOL_EXACT, report)
    _gate("G0e_perm_min_share_pct", perm_min_share, PERM_MIN_SHARE_PCT,
          TOL_EXACT, report)
    _gate("G0e_perm_min_reproduces_claimed_b",
          round(COMMITTED_CENTRAL_B - perm_min_b, 1), abs(CLAIMED_DELTA_B),
          TOL_EXACT, report)
    _gate("G0e_perm_min_reproduces_claimed_pp",
          round(COMMITTED_CENTRAL_SHARE - perm_min_share, 1),
          abs(CLAIMED_DELTA_PP), TOL_EXACT, report)
    _gate("G0e_perm_min_reproduces_claimed_level",
          round(perm_min_share, 1), CLAIMED_LEVEL_PCT, TOL_EXACT, report)
    _wiring_gates(report)

    # ---- benchmark frame + committed caches (free) ------------------------
    print("\nScoring empirical benchmark (shared macro frame, fetched once) …")
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)

    for p in (MICROSIM_RESULTS_PATH, NULL_CACHE, LOAN_SAMPLE_PATH):
        if not p.exists():
            raise FileNotFoundError(f"{p} missing — build via production first")
    cache_central = score_extension_risk(
        pd.read_parquet(MICROSIM_RESULTS_PATH), empirical)
    cache_null = score_extension_risk(pd.read_parquet(NULL_CACHE), empirical)
    _gate("G0a_benchmark_frame_b",
          cache_central["empirical_trapped_b"], cap_b, TOL_EXACT, report)
    _gate("G0b_committed_central_cache_b",
          cache_central["hazard_trapped_b"], COMMITTED_CENTRAL_B, TOL_EXACT,
          report)
    _gate("G0c_committed_null_cache_b",
          cache_null["hazard_trapped_b"], COMMITTED_NULL_B, TOL_EXACT, report)

    # FAIL FAST. Every G0* gate is a PRECONDITION: a dead coefficient override
    # (G0d), a leaking one (G0d2), a revised benchmark frame (G0a) or a drifted
    # engine cache (G0b/G0c) makes all eight engine legs uninterpretable, and a
    # failed G0d in particular must never be readable as a T3 "censored
    # channel". Raise here rather than after ~90s of microsim, and emit NO
    # artifact — the run is VOID, not a result.
    free_fail = [k for k, v in report.items() if not v["pass"]]
    if free_fail:
        raise SystemExit(
            "PRECONDITION FAILURE (free gates) — run is VOID, no artifact "
            f"written: {free_fail}"
        )

    loans = pl.read_parquet(LOAN_SAMPLE_PATH)

    # ------------------------------------------------------------------
    # ENGINE LEGS — production floor
    # ------------------------------------------------------------------
    print("\n--- engine legs @ 4.0% production floor ---")
    prod_central_4 = _run_scored(loans, macro, empirical, PRODUCTION_FLOOR,
                                 CENTRAL_PQ, PRODUCTION_BETA_BURNOUT,
                                 "prod_central_floor4")
    prod_null_4 = _run_scored(loans, macro, empirical, PRODUCTION_FLOOR,
                              NULL_PQ, PRODUCTION_BETA_BURNOUT,
                              "prod_null_floor4")
    _gate("G1_central_b_at4", prod_central_4["trapped_b"],
          anchor["central_trapped_b"], TOL_EXACT, report)
    _gate("G2_null_b_at4", prod_null_4["trapped_b"],
          anchor["null_trapped_b"], TOL_EXACT, report)
    _gate("G3_marginal_b_at4",
          prod_central_4["trapped_b"] - prod_null_4["trapped_b"],
          anchor["lockin_marginal_b"], TOL_EXACT, report)
    _gate("G3_marginal_pp_at4",
          prod_central_4["share_pct"] - prod_null_4["share_pct"],
          anchor["lockin_marginal_share_pp"], TOL_EXACT, report)
    _gate("G4_central_share_at4", prod_central_4["share_pct"],
          anchor["central_share_pct"], TOL_EXACT, report)
    _gate("G4_null_share_at4", prod_null_4["share_pct"],
          anchor["null_share_pct"], TOL_EXACT, report)
    # G5's anchor is the COMMITTED production central peak lag (the "real" row
    # of the permutation summary, whose trapped_b is asserted equal to the
    # production central above) — NOT the manuscript's claim about the ablated
    # leg, which is P1's job.
    _gate("G5_central_peak_lag_at4", prod_central_4["peak_lag"],
          perm["real"]["peak_lag"], TOL_EXACT, report)
    _gate("G7_bind_share_at4", prod_central_4["floor_bind_share"],
          bind_anchor["share_got"], TOL_EXACT, report)
    _gate("G7_bind_n_at4", prod_central_4["floor_bind_loan_months"],
          bind_anchor["n_got"], TOL_EXACT, report)

    off_central_4 = _run_scored(loans, macro, empirical, PRODUCTION_FLOOR,
                                CENTRAL_PQ, ABLATED_BETA_BURNOUT,
                                "burnoutoff_central_floor4")
    off_null_4 = _run_scored(loans, macro, empirical, PRODUCTION_FLOOR,
                             NULL_PQ, ABLATED_BETA_BURNOUT,
                             "burnoutoff_null_floor4")

    # ------------------------------------------------------------------
    # ENGINE LEGS — off-window headline floor
    # ------------------------------------------------------------------
    print("\n--- engine legs @ 4.991% off-window headline floor ---")
    prod_central_off = _run_scored(loans, macro, empirical,
                                   OFFWINDOW_POINT_FLOOR, CENTRAL_PQ,
                                   PRODUCTION_BETA_BURNOUT,
                                   "prod_central_floor4991")
    prod_null_off = _run_scored(loans, macro, empirical, OFFWINDOW_POINT_FLOOR,
                                NULL_PQ, PRODUCTION_BETA_BURNOUT,
                                "prod_null_floor4991")
    _gate("G6_central_b_at4991", prod_central_off["trapped_b"],
          off_central_committed, TOL_EXACT, report)
    _gate("G6_null_b_at4991", prod_null_off["trapped_b"],
          off_null_committed, TOL_EXACT, report)

    off_central_off = _run_scored(loans, macro, empirical,
                                  OFFWINDOW_POINT_FLOOR, CENTRAL_PQ,
                                  ABLATED_BETA_BURNOUT,
                                  "burnoutoff_central_floor4991")
    off_null_off = _run_scored(loans, macro, empirical, OFFWINDOW_POINT_FLOOR,
                               NULL_PQ, ABLATED_BETA_BURNOUT,
                               "burnoutoff_null_floor4991")
    runtime_s = time.perf_counter() - t0

    hard_fail = [k for k, v in report.items() if not v["pass"]]

    # ------------------------------------------------------------------
    # The ablation, on the basis the manuscript quotes
    # ------------------------------------------------------------------
    def _ablation(prod_c, off_c, prod_n, off_n) -> dict:
        return {
            "floor_annual_cpr_pct": prod_c["floor_annual_cpr_pct"],
            "production_trapped_b": prod_c["trapped_b"],
            "burnout_off_trapped_b": off_c["trapped_b"],
            "delta_b": off_c["trapped_b"] - prod_c["trapped_b"],
            "production_share_pct_standalone": prod_c["share_pct"],
            "burnout_off_share_pct_standalone": off_c["share_pct"],
            "delta_pp": off_c["share_pct"] - prod_c["share_pct"],
            "production_share_pct_shared": prod_c["share_pct"] - offset_pp,
            "burnout_off_share_pct_shared": off_c["share_pct"] - offset_pp,
            "production_peak_lag": prod_c["peak_lag"],
            "burnout_off_peak_lag": off_c["peak_lag"],
            "production_r_lag0": prod_c["r_lag0"],
            "burnout_off_r_lag0": off_c["r_lag0"],
            "production_floor_bind_share": prod_c["floor_bind_share"],
            "burnout_off_floor_bind_share": off_c["floor_bind_share"],
            "production_marginal_b": prod_c["trapped_b"] - prod_n["trapped_b"],
            "production_marginal_pp": prod_c["share_pct"] - prod_n["share_pct"],
            "burnout_off_marginal_b": off_c["trapped_b"] - off_n["trapped_b"],
            "burnout_off_marginal_pp": off_c["share_pct"] - off_n["share_pct"],
            "marginal_delta_pp": (
                (off_c["share_pct"] - off_n["share_pct"])
                - (prod_c["share_pct"] - prod_n["share_pct"])
            ),
            "marginal_delta_b": (
                (off_c["trapped_b"] - off_n["trapped_b"])
                - (prod_c["trapped_b"] - prod_n["trapped_b"])
            ),
        }

    abl_4 = _ablation(prod_central_4, off_central_4, prod_null_4, off_null_4)
    abl_off = _ablation(prod_central_off, off_central_off, prod_null_off,
                        off_null_off)

    d_b = abl_4["delta_b"]
    d_pp = abl_4["delta_pp"]

    # ---- ex-ante verdict partition (T3 -> T1 -> T2) -----------------------
    band = classify_verdict(d_pp, d_b, abl_off["delta_b"])
    verdict = verdict_text(
        band, d_pp,
        abl_4["production_floor_bind_share"],
        abl_off["production_floor_bind_share"],
    )
    r1_ok, r2_ok, p1_ok = claim_literal_checks(
        abl_4["burnout_off_share_pct_standalone"], d_b,
        abl_4["burnout_off_peak_lag"],
    )
    m1 = marginal_materiality(abl_4["marginal_delta_pp"],
                              abl_off["marginal_delta_pp"])

    payload = {
        "mode": "burnout_ablation",
        "spec": (
            "beta_burnout 0.0 vs production -0.5 (in-place LITERATURE_COEFS "
            "override; monthly_step never forwards prepay_hazard's coefs "
            "argument), central p_q 6.5 + beta_1=0 null at floors {4.0 "
            "production, 4.991 off-window headline}; US regime, seed 42, "
            "committed 75k sample, hard-max floor form, one shared macro "
            "frame, standalone raw-basis scoring with the committed flat "
            "shared-basis offset emitted alongside; bit-exact parity gates "
            "G0a-G0g/G1-G8; ex-ante partition T3->T1->T2 on the signed "
            "standalone share delta at the production floor, plus R1/R2/P1 "
            "rounding-and-clause checks and the +/-1.0pp M1 marginal "
            "materiality rule"
        ),
        "provenance_audit": {
            "manuscript_sites_tex_v18": [324, 584, 588, 899],
            "claimed_delta_b": CLAIMED_DELTA_B,
            "claimed_delta_pp": CLAIMED_DELTA_PP,
            "claimed_level_pct_standalone": CLAIMED_LEVEL_PCT,
            "claimed_peak_lag": CLAIMED_PEAK_LAG,
            "misattributed_source": (
                "permutation_test_ablate_orig_summary.json "
                "null.trapped_b.min / null.share_pct.min — the MINIMUM over "
                "100 replicates of the origination-time permutation "
                "experiment, not a beta_B = 0 run"
            ),
            "perm_min_trapped_b": perm_min_b,
            "perm_min_share_pct": perm_min_share,
            "perm_mean_trapped_b": perm_mean_b,
            "perm_mean_share_pct": perm_mean_share,
            "perm_min_implied_delta_b": perm_min_b - COMMITTED_CENTRAL_B,
            "perm_min_implied_delta_pp": (
                perm_min_share - COMMITTED_CENTRAL_SHARE),
            "prior_artifact": None,
            "prior_gate": None,
            "prior_technical_record": None,
        },
        "legs": {
            "production_central_4": prod_central_4,
            "production_null_4": prod_null_4,
            "burnout_off_central_4": off_central_4,
            "burnout_off_null_4": off_null_4,
            "production_central_4991": prod_central_off,
            "production_null_4991": prod_null_off,
            "burnout_off_central_4991": off_central_off,
            "burnout_off_null_4991": off_null_off,
        },
        "parity_gates": report,
        "parity_gates_all_pass": not hard_fail,
        "parity_tolerance": TOL_EXACT,
        "house_tolerance_b_for_comparison": TOL_B_HOUSE,
        "basis_map": {
            "curtailment_netted_b": curtail_b,
            "cap_benchmark_b": cap_b,
            "offset_pp": offset_pp,
            "note": ("shared = standalone - offset_pp; pp DELTAS are "
                     "basis-invariant (constant dollar netting over a "
                     "constant denominator), the 106.2% LEVEL is "
                     "standalone-only"),
        },
        "ablation_at_production_floor": abl_4,
        "ablation_at_offwindow_floor": abl_off,
        "offwindow_committed_marginal_pp": off_marginal_pp_committed,
        "claim_checks": {
            "d_b": d_b,
            "d_pp": d_pp,
            "t1_window_pp": [CLAIMED_DELTA_PP - T1_TOL_PP,
                             CLAIMED_DELTA_PP + T1_TOL_PP],
            "R1_level_ok": bool(r1_ok),
            "R1_level_got_pct": abl_4["burnout_off_share_pct_standalone"],
            "R2_dollar_ok": bool(r2_ok),
            "P1_peak_lag_ok": bool(p1_ok),
            "P1_peak_lag_got": abl_4["burnout_off_peak_lag"],
        },
        "verdict_band": band,
        "t1_manuscript_literal_stands": bool(band == "T1"),
        "t3_channel_degenerate": bool(band == "T3"),
        "m1_burnout_material_for_marginal": bool(m1),
        "interpretive_verdict": verdict,
        "runtime_s": runtime_s,
        "runtime_includes_benchmark_fetch": True,
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(
            payload, f, indent=1,
            default=lambda x: float(x)
            if isinstance(x, (np.floating, np.integer)) else x,
        )

    # ------------------------------------------------------------------
    # The comparison the audit asked for, printed explicitly
    # ------------------------------------------------------------------
    print("\n" + "=" * 78)
    print(" BURNOUT ABLATION — recomputed vs the manuscript's claim")
    print("=" * 78)
    print(f"  {'':<34}{'dollars':>14}{'standalone %':>15}{'peak lag':>11}")
    print(f"  {'production central @4.0%':<34}"
          f"{prod_central_4['trapped_b']:>13.4f}B"
          f"{prod_central_4['share_pct']:>14.4f}%"
          f"{str(prod_central_4['peak_lag']):>11}")
    print(f"  {'beta_B = 0 central @4.0%':<34}"
          f"{off_central_4['trapped_b']:>13.4f}B"
          f"{off_central_4['share_pct']:>14.4f}%"
          f"{str(off_central_4['peak_lag']):>11}")
    print(f"  {'RECOMPUTED ablation':<34}{d_b:>+13.4f}B{d_pp:>+14.4f}pp")
    print(f"  {'MANUSCRIPT claim (lines 324+)':<34}"
          f"{CLAIMED_DELTA_B:>+13.4f}B{CLAIMED_DELTA_PP:>+14.4f}pp"
          f"{CLAIMED_PEAK_LAG:>11}")
    print(f"  {'claim minus recomputed':<34}"
          f"{CLAIMED_DELTA_B - d_b:>+13.4f}B"
          f"{CLAIMED_DELTA_PP - d_pp:>+14.4f}pp")
    print(f"  {'(the claim reproduces instead)':<34}"
          f"{perm_min_b - COMMITTED_CENTRAL_B:>+13.4f}B"
          f"{perm_min_share - COMMITTED_CENTRAL_SHARE:>+14.4f}pp"
          "   <- origination-permutation MIN")
    print("-" * 78)
    print(f"  level:  beta_B = 0 @4.0% = "
          f"{abl_4['burnout_off_share_pct_standalone']:.4f}% standalone "
          f"({abl_4['burnout_off_share_pct_shared']:.4f}% shared)  vs claimed "
          f"{CLAIMED_LEVEL_PCT}%  [R1 {'PASS' if r1_ok else 'FAIL'}]")
    print(f"  dollars: R2 {'PASS' if r2_ok else 'FAIL'}   "
          f"peak lag: P1 {'PASS' if p1_ok else 'FAIL'} "
          f"(got {abl_4['burnout_off_peak_lag']})")
    print(f"  off-window @4.991%: {abl_off['delta_b']:+.4f}B "
          f"({abl_off['delta_pp']:+.4f}pp), level "
          f"{abl_off['burnout_off_share_pct_standalone']:.4f}% standalone "
          f"({abl_off['burnout_off_share_pct_shared']:.4f}% shared)")
    print(f"  floor bind share: {abl_4['production_floor_bind_share']:.4f} "
          f"@4.0%  ->  {abl_off['production_floor_bind_share']:.4f} @4.991% "
          "(burnout is inert wherever the floor binds)")
    print(f"  marginal: {abl_4['production_marginal_pp']:+.4f}pp -> "
          f"{abl_4['burnout_off_marginal_pp']:+.4f}pp @4.0% "
          f"(delta {abl_4['marginal_delta_pp']:+.4f}pp); "
          f"{abl_off['production_marginal_pp']:+.4f}pp -> "
          f"{abl_off['burnout_off_marginal_pp']:+.4f}pp @4.991% "
          f"(delta {abl_off['marginal_delta_pp']:+.4f}pp)   "
          f"M1 material={m1}")
    print("=" * 78)
    print(f"verdict: {verdict}")
    print(f"gates all pass: {not hard_fail}   runtime {runtime_s:,.0f}s")
    print(f"Saved: {RESULTS_JSON}")
    if hard_fail:
        raise SystemExit(f"PARITY FAILURE — do not build on this: {hard_fail}")


if __name__ == "__main__":
    main()
