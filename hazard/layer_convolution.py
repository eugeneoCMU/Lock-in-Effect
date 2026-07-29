#!/usr/bin/env python3
"""
layer_convolution.py — the floor-read layer and the loan-sample layer summed as
independent draws on the marginal (pp) scale, reported as a LABELED SECOND LINE
beside the two committed intervals, never as a replacement for either
(round-28 WP-C2; PLAN Decision record item 4; REVIEW2: the paper reports two
sampling layers side by side and never says what one number a reader who wants
one number should use).

PRE-COMMITTED SPEC (fixed in this header BEFORE any run; committed before first
execution; full drafting spec at specs/SPEC_round28_C1_C2_C3_C6.md SPEC C2,
INCLUDING the trailing "C2 AMENDMENTS (labeled, PRE-RUN, 2026-07-29)" block
A1-A6, which OVERRIDE the base spec's numbers where they conflict — C1 was
executed after C2 was drafted, so every quantity C2.3 predicted against the
pre-C1 interval is re-anchored here to C1's REALIZED Webb interval).

EVERYTHING THIS SCRIPT READS IS FROZEN AND IS READ, NEVER WRITTEN. The one file
this script creates is data/layer_convolution_results.json. No committed
artifact, no .tex file and no .py file is modified.

DESIGN. PURE POST-PROCESSING. NO microsim engine anywhere: microsim_engine,
simulate, competing_risks and run_qt_microsim are neither imported nor called;
no refit, no resimulation, no config write. The floor->marginal map is the
COMMITTED PCHIP (mdr.FloorMapping), imported, not reimplemented; the SMM->CPR
conversion, the selection and the cluster bootstrap are the committed
floor_uncertainty / floor_inference_correction_v2 code paths, imported or
copied verbatim. The ONE non-arithmetic step is step 0 below (amendment A5),
which rebuilds the panel through mdr.build_panel — C1's own data-loading path,
and therefore ONE FRED MORTGAGE30US fetch, the same single fetch every floor
read in this repo already makes. That fetch is inherited from the committed
panel construction; it is not a macro-model call and it touches no simulation.

=======================================================================
STEP 0 (amendment A5) — the percentile replicate set, regenerated
=======================================================================
C1's v2 run persisted only the two R2 t* CSVs, NOT the 1,000 percentile floor
draws (floor_uncertainty.cluster_bootstrap_cpr builds them and returns only
summaries; floor_uncertainty.py:201-214). C2.0's standalone fallback is
therefore executed here: panel via mdr.build_panel with stratum.build_stratum_id
labels, R2 selection via fu._select(df, 201801, 201812, -0.0025, 12) — the
literal READ_SELECTIONS[R2] of floor_inference_correction_v2.py:238 — then
fu.cluster_bootstrap_cpr(sel) under its committed defaults (n_reps=1000,
fresh default_rng(42)), which is floor_inference_correction_v2.py:594 verbatim,
with the RETURNED DRAWS RETAINED instead of discarded. Gated bit-exactly (P0)
on se_pp = 0.3933971547430653 and ci95_pct = [4.368576777908708,
6.003552252675821]; on a miss the run STOPS and lands nothing.

THE ONLY RNG IN THIS SCRIPT is that one committed default_rng(42) inside
fu.cluster_bootstrap_cpr. Everything else is deterministic arithmetic on
committed files.

=======================================================================
THE CONVOLUTION (C2.2, as amended by A1/A2)
=======================================================================
FLOOR LAYER — a confidence distribution on the marginal, not a resample. For
each of the 9,999 Webb t* draws in data/floor_inference_v2_tstar_R2_webb.csv:

    R_b   = R_smm - t*_b * se_cr1_smm          (SMM scale, C1's studentization)
    CPR_b = 100 * (1 - (1 - R_b)^12)           (cpr_pct_of_smm, v1 verbatim)
    M_b   = PCHIP(CPR_b) at band delta = 6.5   (edge-truncation convention)

with R_smm = 0.004257129719866917 and se_cr1_smm = 0.0003053670536820312 read
from and asserted against C1's frozen artifact (A1). EDGE-TRUNCATION, C1's
convention (floor_inference_correction_v2.py:281-287): a floor outside the
committed grid [2.0, 6.0]% CPR is mapped AT the nearest edge, flagged and
counted — never extrapolated, and never dropped (dropping is _map_draws's
exclusion convention, deliberately not used for the wild-t line).

LOAN LAYER — deviations from the committed point, NOT from the replicate mean
or median. d_j = m_j - 5.5715581829 over the 200 marginal_pp draws of
bootstrap_pathb_cluster_draws.csv. The centering constant is the committed
point marginal at this floor (bootstrap_pathb_cluster_results.json
.comparison.committed_point_marginal_pp), FIXED EX ANTE. Centering on the
replicate median (5.6407) or mean (5.6830) instead would smuggle a +0.07 /
+0.11pp recentering into the headline layer.

CONVOLVED — the full outer sum {M_b + d_j}, 9,999 x 200 = 1,999,800 pairs, by
exact enumeration (np.add.outer), not a Monte-Carlo sub-sample. Reported: the
2.5/97.5 percentiles in pp and $B, the median, the sd, the width, and the width
ratio against C1's realized floor-read width 5.822976726802727.

SECONDARY LINE — the same construction with the 1,000 regenerated PERCENTILE
floor draws in place of the t*-implied set: the convolved companion to the
[+3.0, +8.0] percentile layer. Its floor draws are mapped under BOTH
conventions and BOTH counts are reported; the convolution itself uses
edge-truncation. The committed percentile map EXCLUDED 26 of 1,000 draws as
out-of-grid (floor_uncertainty_results.json .part_a_sampling_uncertainty.reads.
R2...mapped_marginal_at_6.5.n_draws_outside_grid = 26), all above the 6.0%
floor edge, i.e. all on the LOW-marginal side — the side the lower edge is read
from. That is why edge-truncation is preferred, and it is disclosed either way.

INDEPENDENCE IS AN ASSUMPTION, NOT A MEASUREMENT. The two layers sit on
disjoint data and disjoint time (a 2018 cohort-month cluster ratio on the
Freddie disclosure panel vs a 130-stratum resample of the 75,000-loan
simulation sample over 2022-06..2025-11); nothing in any committed artifact
links a 2018 stratum-ratio replicate to a window-period composition replicate.
The independent sum is therefore the LOWER bound of the dependence bracket and
the comonotone sum is the upper bound; both are reported and the bracket is
recomputed from the realized widths, never hard-coded.

ONE INPUT IS ITSELF A LOWER BOUND. tab:uncertainty's tablenote already says the
loan/stratum interval "is still better read as a lower bound on sampling
uncertainty than as calibrated 95% coverage" (no wild-cluster correction is run
for that scheme). A sum with a lower-bound summand is a lower bound. The
convolved line inherits that and must say so (C2.4 item 3).

=======================================================================
PARITY GATES (BLOCKING unless stated; on failure the JSON is written with
status GATE_FAILURE, the process exits NONZERO, and nothing lands)
=======================================================================
  P0 (A5) percentile regeneration bit-exact at R2 via fu.cluster_bootstrap_cpr
     (rng 42): se_pp 0.3933971547430653 and ci95_pct [4.368576777908708,
     6.003552252675821] to 1e-9. Also asserts n_reps 1000 / 31 clusters /
     137 cohort-months / point 4.990624060575566%.
  P1 bootstrap_pathb_cluster_draws.csv has exactly 200 rows;
     percentile(marginal_pp, [2.5, 97.5]) reproduces [4.630919609903703,
     6.924433300615744] to 1e-9 and the committed sd 0.6044572173024999 to
     1e-9. The committed sd's ddof is NOT documented anywhere, so BOTH are
     computed, the matching one is adopted for every sd this script reports,
     and WHICH ONE MATCHED is recorded in the artifact
     (.parity_gates.P1_loan_draws.sd_ddof_matched).
  P2 (A1) the t*-implied floor layer reproduces C1's realized Webb interval
     [2.8549950653913494, 8.677971792194077]. TWO LEGS, both blocking:
       P2a QUANTILE ROUTE, tol 1e-12 — percentile(t*, [2.5, 97.5]) mapped
           through R_smm/se_cr1_smm -> CPR% -> PCHIP is C1's OWN arithmetic
           (floor_inference_correction_v2.py:336-337, 721-722) and must
           reproduce it to machine precision. This is the load-bearing leg: it
           is what licenses reading the t* CSV as C1's own object.
       P2b PER-DRAW ROUTE, tol 1e-6 pp — percentile({M_b}, [2.5, 97.5]).
           SPEC C2.2 asserts this is exact "by construction"; IT IS NOT, and
           the reason is arithmetic, not a defect. np.percentile interpolates
           LINEARLY between order statistics: at B = 9,999 the 2.5th percentile
           sits at index 0.025*9998 = 249.95, i.e. 95% of the way from order
           statistic 250 to 251. Interpolating in t and then mapping (C1) is
           not the same as mapping and then interpolating (this line): they
           differ by the linear-interpolation error of a curved map,
           ~ (1/2)|g''| w(1-w) h^2, with h the realized order-statistic gap.
           At the realized tail gap that is O(1e-7)pp — six orders below the
           artifact's own reporting precision and eleven below anything
           printed. A 1e-9 gate here would fail on an interpolation artifact
           and land nothing, so the pre-committed tolerance for THIS LEG ONLY
           is 1e-6 pp, and it is backed by a TOLERANCE-FREE co-assertion:
           both the per-draw percentile AND C1's value must lie inside the SAME
           adjacent-order-statistic bracket [M_(k), M_(k+1)], k = floor(0.025*
           (B-1)) and floor(0.975*(B-1)). Same bracket = same sample quantile
           to the resolution the sample has. Recorded as a labeled spec
           deviation; the realized residual and the bracket width are both
           reported so the loosened tolerance is auditable rather than
           asserted.
  P3 the percentile secondary line, with the loan deviations set to zero,
     reproduces the committed percentile interval [2.974329560125351,
     8.01850965353176] to 1e-9 UNDER THE EXCLUSION CONVENTION — that is the
     convention the committed number was computed under (fu._map_draws), so
     P3 is stated under it and NOT under the edge-truncation convention the
     secondary convolution uses. Cross-checked to 1e-12 against a direct call
     to fu._map_draws on the same draws. "Loan deviations set to zero" is read
     as the DEGENERATE one-point loan layer {0}: the outer sum is then the
     974-value retained set itself. Replicating each retained value 200 times
     and taking percentiles of the 194,800-value array is a DIFFERENT number
     (the interpolation index lands inside a repeated block), so that variant
     is reported as a labeled diagnostic and is not the gate.
  P4 (A6) THE INTERACTION PROBE — the substitute for a 3-hour joint
     re-simulation, and the only thing that prices the interaction the additive
     convolution assumes away. bootstrap_pathb_cluster.py --floor 4.695 --reps
     60 and --floor 5.334 --reps 60 (A3 pinned their band-6.5 anchors into
     ANCHORS_BY_FLOOR, bootstrap_pathb_cluster.py:146-152). Pre-committed
     tolerance: each band end's 5-95 percentile width of marginal_pp within
     +/-25% of the 4.991% run's 5-95 width. NOT BLOCKING IN EITHER DIRECTION —
     it ROUTES THE LANDING, per C2.5: inside tolerance the additive
     convolution stands as specified; outside, the convolved line is reported
     ONLY at 4.991% with the floor dependence disclosed and the RSS is not
     claimed to hold across the floor range. The probe runs may still be in
     flight when this script is run: if either results JSON is absent the probe
     is marked PENDING, P4 is excluded from parity_gates_all_pass, and the
     verdict carries C2.5's mandatory caveat ("the loan-layer width is assumed
     floor-invariant; not tested") until the coordinator re-runs. A results
     JSON present but disagreeing with its own draws CSV row count is a data
     integrity failure and IS blocking.

=======================================================================
PRE-COMMITTED EXPECTATION (C2.3 as restated by A2 — realized widths)
=======================================================================
Floor-read Webb width w1 = 5.822976726802727pp (C1 realized); loan/stratum
width w2 = 2.2935136907120413pp; w2/w1 = 0.3939. Independent half-widths add in
quadrature, so w_conv/w1 = sqrt(1 + 0.3939^2) = 1.0748 -> +7.5% wider. Applied
asymmetrically about the point +5.5716: lower half-width
sqrt(2.7166^2 + 1.0098^2) = 2.898, upper sqrt(3.1064^2 + 1.2837^2) = 3.361.

  PRE-COMMITTED POINT PREDICTION: convolved ~ [+2.67, +8.93]pp, width ~6.26pp,
  ~+0.43pp (+7.5%) wider than C1's [+2.85, +8.68].

  DEPENDENCE BRACKET, also pre-committed: independence is the LOWER bound on
  the convolved width; perfect positive dependence is the upper bound,
  5.8230 + 2.2935 = 8.117pp (+39.4%). Both endpoints of the bracket are
  RECOMPUTED IN-SCRIPT from the realized widths — the sum above is stated here
  as the expectation and is never hard-coded into the arithmetic.

VERDICT RULE (ex ante, NO DISCRETION, unchanged by A2): the convolved primary
width MUST EXCEED the realized floor-read width 5.822976726802727pp. A sum of
independent variates cannot narrow, so if it does not, the construction is
wrong: status GATE_FAILURE, exit nonzero, STOP and debug rather than report.

=======================================================================
LANDING (C2.4, re-anchored by A4; single branch — the decision record fixed
the presentation form and the only free content is the numbers)
=======================================================================
 1. tab:uncertainty (tex 357), headline row, "Sampling 95% CI" cell: a LABELED
    SECOND LINE appended after the existing loan/stratum clause, naming the run,
    stating that independence is assumed and not measured, and quoting the
    comonotone width as the bound under maximal dependence.
    ZERO-SLACK COLLISION: that cell also carries the bracket-form binding-layer
    literal and the gate-pinned $[+4.63, +6.92]$ (liveness_gates.py:4175) and
    25.8 (:4177); NEITHER MAY BE DISTURBED, and the :4167 assertion
    width_ratio_vs_floor_read < 0.5 is against the PERCENTILE width and must be
    confirmed unaffected before committing.
 2. tex 301: one appended sentence after the interval-discussion clause and
    before "The hull's lower edge is thus narrower...", saying the two layers
    are reported side by side rather than maximized over, giving the convolved
    span as the one number a reader who wants one number should use, and
    stating why it does not replace the floor read.
 3. tex 364 tablenote: one clause recording that one input to the sum is itself
    a lower bound, so the convolved line is a lower bound too.
 NOT LANDING ANYWHERE: the abstract (tex 30), tab:headline (tex 76),
 tab:crosswalk (tex 677), the conclusion (tex 605/611). Body-and-table object
 only, per "labeled second line, not a replacement".
 [posture-adjacent] The tex 301 sentence changes how the paper RANKS its
 uncertainty layers. Eugene sees the drafted sentence before it lands. Per A4
 the manuscript now prints $+2.9$ to $+8.7$; every C2.4/C2.7 reference to the
 pre-C1 printed pair maps to the current pair, and the census is re-derived
 with count-asserted replacements at apply time.

MUST NOT CHANGE: the binding-layer literal at any of its occurrences;
$[+4.63, +6.92]$, 25.8 and "factor of $37$" (gate-pinned,
liveness_gates.py:4175-4177); the percentile layer [+3.0, +8.0] x4; the point
+5.6pp / +$42.6B; the label "the binding layer" (C3 may move it, C2 may not);
any committed artifact, any .py file, any .tex file.

Run:  cd hazard && python3 layer_convolution.py
      -> data/layer_convolution_results.json     (the ONLY file written)
Runtime: seconds of arithmetic plus one FRED MORTGAGE30US fetch and the 1,000
committed-seed percentile replicates of step 0.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import floor_uncertainty as fu
import matched_depth_reconciliation as mdr
from stratum import build_stratum_id

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "layer_convolution_results.json"   # the ONLY write

# ---- frozen inputs (read, never written) ------------------------------------
C1_ARTIFACT = DATA_DIR / "floor_inference_correction_v2_results.json"
TSTAR_WEBB_CSV = DATA_DIR / "floor_inference_v2_tstar_R2_webb.csv"
FU_ARTIFACT = DATA_DIR / "floor_uncertainty_results.json"
LOAN_DRAWS_CSV = DATA_DIR / "bootstrap_pathb_cluster_draws.csv"
LOAN_RESULTS_JSON = DATA_DIR / "bootstrap_pathb_cluster_results.json"

R2 = "R2_2018_gap<=-0.0025_age>=12"
CENTRAL_PQ = "6.5"
GRID_LO, GRID_HI = 2.0, 6.0

# ---- A1: C1's realized R2 Webb inputs and target (asserted vs the artifact) --
R_SMM = 0.004257129719866917
SE_CR1_SMM = 0.0003053670536820312
C1_WEBB_CI95_PP = (2.8549950653913494, 8.677971792194077)
FLOOR_READ_WIDTH_PP = 5.822976726802727          # C1 realized; the verdict bar
B_WILD = 9999

# ---- P0 (A5): the committed percentile-bootstrap targets --------------------
COMMITTED_R2_SE_PP = 0.3933971547430653
COMMITTED_R2_CI95_PCT = (4.368576777908708, 6.003552252675821)
COMMITTED_PERCENTILE_PP = (2.974329560125351, 8.01850965353176)
COMMITTED_N_OUTSIDE_GRID = 26
COMMITTED_R2_POINT_PCT = 4.990624060575566
COMMITTED_R2_N_CLUSTERS = 31
COMMITTED_R2_N_COHORT_MONTHS = 137
# floor_inference_correction_v2.py:238 READ_SELECTIONS[R2], verbatim
R2_SELECTION = (*fu.LEG_2018, -0.0025, 12)

# ---- P1: the committed loan/stratum layer -----------------------------------
N_LOAN_REPS = 200
COMMITTED_LOAN_CI95_PP = (4.630919609903703, 6.924433300615744)
COMMITTED_LOAN_SD_PP = 0.6044572173024999
COMMITTED_LOAN_WIDTH_PP = 2.2935136907120413
LOAN_EFFECTIVE_CLUSTERS = 25.77710660741266

# ---- centering, FIXED EX ANTE (C2.2): the committed point, not mean/median ---
CENTER_PP = 5.5715581829                  # .comparison.committed_point_marginal_pp
CENTER_B = 42.60839388108866              # 767.5264524465003 - 724.9180585654117
CENTER_PP_UNROUNDED = 5.571558182909726   # floor_uncertainty POINT_MARGINAL pp
LOAN_MEDIAN_PP = 5.640716853146607        # NOT used as the centre; recorded
LOAN_MEAN_PP = 5.682988123686434          # NOT used as the centre; recorded

# ---- P4 (A6): the interaction probe -----------------------------------------
P4_FLOORS = (4.695, 5.334)
P4_REF_FLOOR = 4.991
P4_REPS = 60
P4_TOL_REL = 0.25
P4_PCTL = (5.0, 95.0)

# ---- tolerances -------------------------------------------------------------
TOL_1E9 = 1e-9
TOL_PARITY = 1e-12
TOL_P2B_PP = 1e-6          # see P2b in the header: interpolation-artifact floor

# ---- A2 pre-committed expectation -------------------------------------------
PREDICTED_CI95_PP = (2.67, 8.93)
PREDICTED_WIDTH_PP = 6.26
PREDICTED_RSS_RATIO = 1.0748


# =========================================================================
# VERBATIM COPY FROM floor_inference_correction_v2.py (v1's, unchanged)
# =========================================================================
def cpr_pct_of_smm(smm):
    """SMM -> annual CPR %, the committed conversion. Vectorized over ndarray;
    on a scalar it is floor_inference_correction_v2.py:255-256 verbatim."""
    return 100.0 * (1.0 - (1.0 - smm) ** 12)


# =========================================================================
# MAPPING CONVENTIONS
# =========================================================================
def map_edge_truncated(mapping: mdr.FloorMapping, floors_pct: np.ndarray) -> dict:
    """C1's convention (floor_inference_correction_v2.py:281-287) applied
    draw-wise: a floor outside the committed grid is mapped AT the nearest edge,
    flagged and counted; never extrapolated, never dropped. The per-element
    scalar call is deliberate — it is the same call fu._map_draws makes, so the
    two conventions differ ONLY in the handling of out-of-grid draws."""
    f = np.asarray(floors_pct, dtype=np.float64)
    n_below = int((f < GRID_LO).sum())
    n_above = int((f > GRID_HI).sum())
    x = np.clip(f, GRID_LO, GRID_HI)
    pairs = [mapping(float(v)) for v in x]
    return {
        "b": np.array([p[0] for p in pairs], dtype=np.float64),
        "pp": np.array([p[1] for p in pairs], dtype=np.float64),
        "n_truncated_at_edge": n_below + n_above,
        "n_truncated_below_grid_lo": n_below,
        "n_truncated_above_grid_hi": n_above,
        "convention": ("edge truncation: min(max(floor, 2.0), 6.0), flagged and "
                       "counted (C1/v1 convention; extrapolation refused)"),
    }


def map_excluded(mapping: mdr.FloorMapping, floors_pct: np.ndarray) -> dict:
    """The committed percentile convention (fu._map_draws): out-of-grid draws
    are EXCLUDED and counted. Reproduced here so the retained arrays are
    available; cross-checked against fu._map_draws itself in P3."""
    f = np.asarray(floors_pct, dtype=np.float64)
    in_grid = np.array([mapping.in_grid(float(d)) for d in f])
    pairs = [mapping(float(d)) for d in f[in_grid]]
    return {
        "b": np.array([p[0] for p in pairs], dtype=np.float64),
        "pp": np.array([p[1] for p in pairs], dtype=np.float64),
        "n_draws_outside_grid": int((~in_grid).sum()),
        "n_retained": int(in_grid.sum()),
        "convention": ("exclusion: out-of-grid draws dropped and counted "
                       "(fu._map_draws; the convention the committed "
                       "percentile interval was computed under)"),
    }


def pct(a: np.ndarray, q=(2.5, 97.5)) -> list:
    return [float(v) for v in np.percentile(np.asarray(a), list(q))]


def orderstat_bracket(sorted_vals: np.ndarray, p: float) -> tuple:
    """[v_(k), v_(k+1)] with k = floor(p/100 * (n-1)) — the two order statistics
    np.percentile interpolates between at probability p. Used by P2b to state
    the floor-layer agreement WITHOUT a tolerance."""
    n = sorted_vals.size
    k = int(np.floor(p / 100.0 * (n - 1)))
    k = min(max(k, 0), n - 2)
    return float(sorted_vals[k]), float(sorted_vals[k + 1]), k


# =========================================================================
# FAILURE PATH
# =========================================================================
def _fail_out(status: str, gate_report: dict, t0: float,
              extra: dict | None = None) -> None:
    payload = {
        "mode": "layer_convolution",
        "status": status,
        "spec_source": ("specs/SPEC_round28_C1_C2_C3_C6.md SPEC C2 + "
                        "C2 AMENDMENTS A1-A6 (PRE-RUN, 2026-07-29)"),
        "parity_gates": gate_report,
        "parity_gates_all_pass": False,
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    if extra:
        payload.update(extra)
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2, default=lambda o: o.item())
        f.write("\n")
    failed = [k for k, v in gate_report.items()
              if isinstance(v, dict) and not v.get("pass", True)]
    raise SystemExit(
        f"{status} {failed} — STOP. Nothing lands in the manuscript. "
        f"Diagnostics in {RESULTS_JSON}."
    )


# =========================================================================
def main() -> None:
    t0 = time.perf_counter()
    gate_report: dict = {}

    # ---- frozen artifacts, asserted against the constants quoted above ------
    with open(C1_ARTIFACT) as f:
        c1 = json.load(f)
    assert c1.get("status") == "OK" and c1.get("parity_gates_all_pass"), C1_ARTIFACT
    assert c1["mode"] == "floor_inference_correction_v2"
    c1r2 = c1["reads"][R2]
    assert abs(c1r2["R_smm"] - R_SMM) < 1e-18, "R_smm drifted from A1"
    assert abs(c1r2["se_cr1_smm"] - SE_CR1_SMM) < 1e-18, "se_cr1 drifted from A1"
    assert abs(c1r2["point_cpr_pct"] - COMMITTED_R2_POINT_PCT) < 1e-12
    webb = c1r2["wild_t_webb"]
    assert webb["weights"] == "webb" and webb["B"] == B_WILD and webb["seed"] == 42
    for i in (0, 1):
        assert abs(webb["marginal_ci95_pp"][i] - C1_WEBB_CI95_PP[i]) < 1e-15, i
    assert abs((C1_WEBB_CI95_PP[1] - C1_WEBB_CI95_PP[0])
               - FLOOR_READ_WIDTH_PP) < 1e-12

    with open(FU_ARTIFACT) as f:
        fua = json.load(f)
    assert fua.get("status") == "OK" and fua.get("parity_gates_all_pass")
    fu_r2 = fua["part_a_sampling_uncertainty"]["reads"][R2]
    fu_map = fu_r2["mapped_marginal_at_6.5"]
    for i in (0, 1):
        assert abs(fu_map["ci95_pp"][i] - COMMITTED_PERCENTILE_PP[i]) < 1e-15, i
    assert fu_map["n_draws_outside_grid"] == COMMITTED_N_OUTSIDE_GRID

    with open(LOAN_RESULTS_JSON) as f:
        loan_art = json.load(f)
    assert loan_art.get("parity_gates_all_pass")
    assert abs(loan_art["floor_annual_cpr_pct"] - P4_REF_FLOOR) < 1e-12
    lcmp = loan_art["comparison"]
    assert abs(lcmp["committed_point_marginal_pp"] - CENTER_PP) < 1e-12, \
        "the ex-ante centering constant is not the committed point marginal"
    g1c = loan_art["parity_gates"]["G1_central_b"]["got"]
    g1n = loan_art["parity_gates"]["G1_null_b"]["got"]
    assert abs((g1c - g1n) - CENTER_B) < 1e-9, "the $B centre is not the anchor delta"

    print("=" * 72)
    print("layer_convolution — floor-read layer (x) loan-sample layer, "
          "independent sum on the pp scale")
    print("SPEC C2 + amendments A1-A6.  NO ENGINE.  Pure post-processing.")
    print("=" * 72)

    # =====================================================================
    # STEP 0 (A5) — regenerate the 1,000 percentile floor draws, RETAINED
    # =====================================================================
    print("\nSTEP 0 (A5) — percentile replicate regeneration "
          "(fu.cluster_bootstrap_cpr, rng 42, draws RETAINED)")
    print("  PANEL — matched_depth_reconciliation.build_panel "
          "(one FRED MORTGAGE30US fetch; C1's own path)")
    df = mdr.build_panel()
    df["stratum"] = [
        build_stratum_id(v, c, fb, lb)
        for v, c, fb, lb in zip(df["vintage"], df["coupon"],
                                df["fico_bucket"], df["ltv_bucket"])
    ]
    sel_r2 = fu._select(df, *R2_SELECTION)
    point_cpr, _exp, n_cm = mdr.cpr_of(sel_r2)
    mapping = mdr.FloorMapping()
    assert abs(float(mapping.x.min()) - GRID_LO) < 1e-12
    assert abs(float(mapping.x.max()) - GRID_HI) < 1e-12

    pct_draws, n_cl = fu.cluster_bootstrap_cpr(sel_r2)     # rng 42, 1000 reps
    p0_se_pp = float(np.std(pct_draws, ddof=1))
    p0_ci = pct(pct_draws)
    p0_mapped_committed = fu._map_draws(mapping, pct_draws)   # committed path
    p0_ok = bool(
        pct_draws.size == fu.N_REPS
        and n_cl == COMMITTED_R2_N_CLUSTERS
        and n_cm == COMMITTED_R2_N_COHORT_MONTHS
        and abs(point_cpr - COMMITTED_R2_POINT_PCT) < TOL_1E9
        and abs(p0_se_pp - COMMITTED_R2_SE_PP) < TOL_1E9
        and abs(p0_ci[0] - COMMITTED_R2_CI95_PCT[0]) < TOL_1E9
        and abs(p0_ci[1] - COMMITTED_R2_CI95_PCT[1]) < TOL_1E9
    )
    gate_report["P0_percentile_regeneration"] = {
        "source": "fu.cluster_bootstrap_cpr(fu._select(panel, 201801, 201812, "
                  "-0.0025, 12)) with committed defaults n_reps=1000, "
                  "fresh np.random.default_rng(42)",
        "n_reps": int(pct_draws.size), "want_n_reps": int(fu.N_REPS),
        "seed": int(fu.SEED),
        "n_clusters": int(n_cl), "want_n_clusters": COMMITTED_R2_N_CLUSTERS,
        "n_cohort_months": int(n_cm),
        "want_n_cohort_months": COMMITTED_R2_N_COHORT_MONTHS,
        "point_cpr_pct": float(point_cpr),
        "want_point_cpr_pct": COMMITTED_R2_POINT_PCT,
        "got_se_pp": p0_se_pp, "want_se_pp": COMMITTED_R2_SE_PP,
        "got_ci95_pct": p0_ci, "want_ci95_pct": list(COMMITTED_R2_CI95_PCT),
        "tol": TOL_1E9, "pass": p0_ok,
    }
    print(f"  P0 percentile regeneration bit-exact: se {p0_se_pp:.16f} "
          f"ci {p0_ci} [{'PASS' if p0_ok else 'FAIL'}]")
    if not p0_ok:
        _fail_out("GATE_FAILURE", gate_report, t0)

    # =====================================================================
    # P1 — the loan/stratum replicate set
    # =====================================================================
    print("\nP1 — loan/stratum cluster draws")
    loan = pd.read_csv(LOAN_DRAWS_CSV)
    m = loan["marginal_pp"].to_numpy(dtype=np.float64)
    m_b = loan["marginal_b"].to_numpy(dtype=np.float64)
    loan_ci = pct(m)
    sd0 = float(np.std(m, ddof=0))
    sd1 = float(np.std(m, ddof=1))
    ddof_matched = (1 if abs(sd1 - COMMITTED_LOAN_SD_PP) < TOL_1E9
                    else (0 if abs(sd0 - COMMITTED_LOAN_SD_PP) < TOL_1E9
                          else None))
    p1_ok = bool(
        m.size == N_LOAN_REPS
        and abs(loan_ci[0] - COMMITTED_LOAN_CI95_PP[0]) < TOL_1E9
        and abs(loan_ci[1] - COMMITTED_LOAN_CI95_PP[1]) < TOL_1E9
        and ddof_matched is not None
    )
    loan_width = loan_ci[1] - loan_ci[0]
    gate_report["P1_loan_draws"] = {
        "csv": str(LOAN_DRAWS_CSV), "field": "marginal_pp",
        "n_rows": int(m.size), "want_n_rows": N_LOAN_REPS,
        "got_ci95_pp": loan_ci, "want_ci95_pp": list(COMMITTED_LOAN_CI95_PP),
        "want_sd_pp": COMMITTED_LOAN_SD_PP,
        "sd_ddof0": sd0, "sd_ddof1": sd1,
        "sd_ddof_matched": ddof_matched,
        "sd_ddof_note": ("the committed sd's ddof is undocumented; BOTH were "
                         "computed and the matching one is adopted for every "
                         "sd this script reports"),
        "got_width_pp": loan_width,
        "want_width_pp": COMMITTED_LOAN_WIDTH_PP,
        "tol": TOL_1E9, "pass": p1_ok,
    }
    print(f"  P1 loan draws n={m.size} ci={loan_ci} sd_ddof={ddof_matched} "
          f"[{'PASS' if p1_ok else 'FAIL'}]")
    if not p1_ok:
        _fail_out("GATE_FAILURE", gate_report, t0)
    SD_DDOF = int(ddof_matched)

    # =====================================================================
    # FLOOR LAYER — the t*-implied confidence distribution on the marginal
    # =====================================================================
    print("\nFLOOR LAYER — 9,999 Webb t* draws -> SMM -> CPR% -> PCHIP "
          "(edge truncation)")
    tstar = np.loadtxt(TSTAR_WEBB_CSV, skiprows=1, dtype=np.float64)
    assert tstar.ndim == 1 and tstar.size == B_WILD, \
        f"expected {B_WILD} t* draws, got {tstar.shape}"
    floor_smm = R_SMM - tstar * SE_CR1_SMM
    floor_cpr = cpr_pct_of_smm(floor_smm)
    fl = map_edge_truncated(mapping, floor_cpr)
    M_pp, M_b = fl["pp"], fl["b"]
    floor_ci_pp = pct(M_pp)
    floor_ci_b = pct(M_b)
    floor_width = floor_ci_pp[1] - floor_ci_pp[0]
    print(f"  floors {floor_cpr.min():.4f}%..{floor_cpr.max():.4f}%; "
          f"{fl['n_truncated_at_edge']} mapped at a grid edge "
          f"({fl['n_truncated_above_grid_hi']} above 6.0%, "
          f"{fl['n_truncated_below_grid_lo']} below 2.0%)")
    print(f"  per-draw ci95 [{floor_ci_pp[0]:+.10f}, {floor_ci_pp[1]:+.10f}]pp "
          f"width {floor_width:.10f}")

    # ---- P2a QUANTILE ROUTE (C1's own arithmetic; tol 1e-12) ---------------
    q_lo, q_hi = np.percentile(tstar, [2.5, 97.5])
    # the CSV IS C1's draw set: its own quantiles must reproduce .t_star_q
    tsq_diff = [abs(float(q_lo) - webb["t_star_q"][0]),
                abs(float(q_hi) - webb["t_star_q"][1])]
    q_route_hi_pp = mapping(float(np.clip(
        cpr_pct_of_smm(R_SMM - q_hi * SE_CR1_SMM), GRID_LO, GRID_HI)))[1]
    q_route_lo_pp = mapping(float(np.clip(
        cpr_pct_of_smm(R_SMM - q_lo * SE_CR1_SMM), GRID_LO, GRID_HI)))[1]
    q_route = [q_route_lo_pp, q_route_hi_pp]     # low marginal <- high floor
    p2a_diff = [abs(q_route[i] - C1_WEBB_CI95_PP[i]) for i in (0, 1)]
    p2a_ok = bool(max(p2a_diff) <= TOL_PARITY and max(tsq_diff) <= TOL_PARITY)

    # ---- P2b PER-DRAW ROUTE (tol 1e-6 pp + tolerance-free bracket) ---------
    M_sorted = np.sort(M_pp)
    p2b_diff = [abs(floor_ci_pp[i] - C1_WEBB_CI95_PP[i]) for i in (0, 1)]
    brackets, in_bracket = {}, True
    for i, p in ((0, 2.5), (1, 97.5)):
        lo_k, hi_k, k = orderstat_bracket(M_sorted, p)
        ok_i = (lo_k <= floor_ci_pp[i] <= hi_k) and (lo_k <= C1_WEBB_CI95_PP[i] <= hi_k)
        in_bracket = in_bracket and ok_i
        brackets[f"p{p}"] = {
            "k": k, "M_k_pp": lo_k, "M_k_plus_1_pp": hi_k,
            "bracket_width_pp": hi_k - lo_k,
            "per_draw_percentile_pp": floor_ci_pp[i],
            "c1_value_pp": C1_WEBB_CI95_PP[i],
            "both_inside_same_bracket": bool(ok_i),
        }
    p2b_ok = bool(max(p2b_diff) <= TOL_P2B_PP and in_bracket)
    gate_report["P2_floor_layer_vs_C1_webb"] = {
        "target_pp": list(C1_WEBB_CI95_PP), "target_source": "A1 / C1 artifact "
        f"reads.{R2}.wild_t_webb.marginal_ci95_pp",
        "P2a_quantile_route": {
            "got_pp": q_route, "abs_diff_pp": p2a_diff,
            "tol": TOL_PARITY, "pass": p2a_ok,
            "t_star_q_from_csv": [float(q_lo), float(q_hi)],
            "t_star_q_committed": list(webb["t_star_q"]),
            "t_star_q_abs_diff": tsq_diff,
            "note": "percentile(t*,[2.5,97.5]) -> SMM -> CPR% -> PCHIP; this is "
                    "C1's own arithmetic and must agree to machine precision. "
                    "The CSV's own t* quantiles are asserted against the "
                    "committed .wild_t_webb.t_star_q, which is what proves the "
                    "CSV is C1's draw set and not a re-draw.",
        },
        "P2b_per_draw_route": {
            "got_pp": floor_ci_pp, "abs_diff_pp": p2b_diff,
            "tol_pp": TOL_P2B_PP, "order_stat_brackets": brackets,
            "both_values_in_same_order_stat_bracket": bool(in_bracket),
            "pass": p2b_ok,
            "note": "np.percentile interpolates linearly between order "
                    "statistics, so mapping-then-interpolating differs from "
                    "C1's interpolating-then-mapping by ~(1/2)|g''|w(1-w)h^2, "
                    "O(1e-7)pp at the realized tail gap. SPEC C2.2's 'exactly' "
                    "is unattainable; the tolerance-free statement is the "
                    "shared order-statistic bracket, which is asserted.",
        },
        "pass": bool(p2a_ok and p2b_ok),
    }
    print(f"  P2a quantile route  {q_route} max|d|={max(p2a_diff):.3e} "
          f"[{'PASS' if p2a_ok else 'FAIL'}]")
    print(f"  P2b per-draw route  max|d|={max(p2b_diff):.3e}pp, shared "
          f"order-stat bracket={in_bracket} [{'PASS' if p2b_ok else 'FAIL'}]")
    if not (p2a_ok and p2b_ok):
        _fail_out("GATE_FAILURE", gate_report, t0)

    # =====================================================================
    # SECONDARY FLOOR LAYER — the percentile replicates, both conventions
    # =====================================================================
    print("\nSECONDARY FLOOR LAYER — 1,000 percentile draws, both conventions")
    sec_excl = map_excluded(mapping, pct_draws)
    sec_edge = map_edge_truncated(mapping, pct_draws)
    sec_excl_ci = pct(sec_excl["pp"])
    sec_edge_ci = pct(sec_edge["pp"])
    print(f"  exclusion: {sec_excl['n_draws_outside_grid']} of "
          f"{pct_draws.size} dropped, ci95 {sec_excl_ci}")
    print(f"  edge trunc: {sec_edge['n_truncated_at_edge']} clipped "
          f"({sec_edge['n_truncated_above_grid_hi']} above 6.0%), "
          f"ci95 {sec_edge_ci}")

    # ---- P3 (exclusion convention, loan deviations set to zero) ------------
    p3_zero_dev = pct(sec_excl["pp"] + 0.0)
    p3_diff = [abs(p3_zero_dev[i] - COMMITTED_PERCENTILE_PP[i]) for i in (0, 1)]
    p3_vs_fu = [abs(p3_zero_dev[i] - p0_mapped_committed["ci95_pp"][i])
                for i in (0, 1)]
    rep_variant = pct(np.repeat(sec_excl["pp"], N_LOAN_REPS))
    p3_ok = bool(max(p3_diff) <= TOL_1E9
                 and max(p3_vs_fu) <= TOL_PARITY
                 and sec_excl["n_draws_outside_grid"] == COMMITTED_N_OUTSIDE_GRID)
    gate_report["P3_percentile_secondary_zero_deviation"] = {
        "convention": "EXCLUSION (the convention the committed number was "
                      "computed under); the secondary CONVOLUTION uses edge "
                      "truncation, this gate does not",
        "zero_deviation_reading": "degenerate one-point loan layer {0}: the "
                                  "outer sum is the retained set itself",
        "got_pp": p3_zero_dev, "want_pp": list(COMMITTED_PERCENTILE_PP),
        "abs_diff_pp": p3_diff, "tol": TOL_1E9,
        "cross_check_vs_fu_map_draws_pp": p0_mapped_committed["ci95_pp"],
        "cross_check_abs_diff": p3_vs_fu, "cross_check_tol": TOL_PARITY,
        "n_draws_outside_grid": sec_excl["n_draws_outside_grid"],
        "want_n_draws_outside_grid": COMMITTED_N_OUTSIDE_GRID,
        "replicated_outer_variant_pp": rep_variant,
        "replicated_outer_variant_note": ("replicating each retained value 200x "
                                          "and taking percentiles of the "
                                          "194,800-value array lands the "
                                          "interpolation index inside a "
                                          "repeated block and is a DIFFERENT "
                                          "number; diagnostic only"),
        "pass": p3_ok,
    }
    print(f"  P3 zero-deviation vs committed percentile interval "
          f"max|d|={max(p3_diff):.3e} [{'PASS' if p3_ok else 'FAIL'}]")
    if not p3_ok:
        _fail_out("GATE_FAILURE", gate_report, t0)

    # =====================================================================
    # THE CONVOLUTION
    # =====================================================================
    print("\nCONVOLUTION — full outer sum, exact enumeration")
    d_pp = m - CENTER_PP
    d_b = m_b - CENTER_B
    conv_pp = np.add.outer(M_pp, d_pp).ravel()
    conv_b = np.add.outer(M_b, d_b).ravel()
    conv_ci_pp = pct(conv_pp)
    conv_ci_b = pct(conv_b)
    conv_width = conv_ci_pp[1] - conv_ci_pp[0]

    sec_conv_pp = np.add.outer(sec_edge["pp"], d_pp).ravel()
    sec_conv_b = np.add.outer(sec_edge["b"], d_b).ravel()
    sec_conv_ci_pp = pct(sec_conv_pp)
    sec_conv_width = sec_conv_ci_pp[1] - sec_conv_ci_pp[0]
    sec_conv_excl_ci_pp = pct(np.add.outer(sec_excl["pp"], d_pp).ravel())

    print(f"  primary   [{conv_ci_pp[0]:+.4f}, {conv_ci_pp[1]:+.4f}]pp "
          f"width {conv_width:.4f} (n_pairs {conv_pp.size:,})")
    print(f"  secondary [{sec_conv_ci_pp[0]:+.4f}, {sec_conv_ci_pp[1]:+.4f}]pp "
          f"width {sec_conv_width:.4f} (n_pairs {sec_conv_pp.size:,})")

    # ---- P4 (A6) the interaction probe — routes the landing, not blocking --
    print("\nP4 (A6) — floor-invariance interaction probe")
    ref5_95 = float(np.percentile(m, P4_PCTL[1]) - np.percentile(m, P4_PCTL[0]))
    probe_cells, probe_missing, probe_inconsistent = {}, [], []
    for fl_pct in P4_FLOORS:
        tag = f"_floor{fl_pct:g}"
        rj = DATA_DIR / f"bootstrap_pathb_cluster_results{tag}.json"
        dc = DATA_DIR / f"bootstrap_pathb_cluster_draws{tag}.csv"
        if not rj.exists():
            probe_missing.append(str(rj))
            probe_cells[f"{fl_pct:g}"] = {"status": "PENDING",
                                          "results_json": str(rj),
                                          "draws_csv": str(dc),
                                          "draws_csv_exists": bool(dc.exists())}
            continue
        with open(rj) as f:
            pr = json.load(f)
        pm = pd.read_csv(dc)["marginal_pp"].to_numpy(dtype=np.float64)
        n_declared = int(pr.get("n_reps", -1))
        consistent = bool(pm.size == n_declared)
        if not consistent:
            probe_inconsistent.append(str(dc))
        w = float(np.percentile(pm, P4_PCTL[1]) - np.percentile(pm, P4_PCTL[0]))
        ratio = w / ref5_95
        probe_cells[f"{fl_pct:g}"] = {
            "status": "RUN", "results_json": str(rj), "draws_csv": str(dc),
            "n_reps_declared": n_declared, "n_draws_csv_rows": int(pm.size),
            "draws_consistent_with_results": consistent,
            "want_n_reps": P4_REPS,
            "parity_gates_all_pass": bool(pr.get("parity_gates_all_pass")),
            "width_5_95_pp": w, "ratio_vs_ref": ratio,
            "abs_rel_dev": abs(ratio - 1.0),
            "within_tolerance": bool(abs(ratio - 1.0) <= P4_TOL_REL),
        }
        print(f"  floor {fl_pct:g}%: 5-95 width {w:.4f}pp vs ref "
              f"{ref5_95:.4f}pp  ratio {ratio:.4f}")

    if probe_inconsistent:
        gate_report["P4_floor_invariance_probe"] = {
            "cells": probe_cells, "status": "INCONSISTENT",
            "inconsistent_draw_files": probe_inconsistent,
            "reason": "a probe results JSON disagrees with its own draws CSV "
                      "row count — the CSV is truncated or a run is mid-flight "
                      "while its JSON is stale; data integrity failure",
            "pass": False}
        _fail_out("GATE_FAILURE", gate_report, t0)

    p4_pending = bool(probe_missing)
    if p4_pending:
        p4_within = None
        p4_block = {
            "status": "PENDING", "reps": P4_REPS, "floors": list(P4_FLOORS),
            "ref_floor_pct": P4_REF_FLOOR, "ref_width_5_95_pp": ref5_95,
            "percentiles": list(P4_PCTL), "tol_rel": P4_TOL_REL,
            "cells": probe_cells, "widths_pp": None, "within_tolerance": None,
            "missing_artifacts": probe_missing,
            "excluded_from_parity_gates_all_pass": True,
            "note": ("the A6 probe runs had not landed when this script ran. "
                     "P4 is NOT RUN, is excluded from parity_gates_all_pass, "
                     "and until it lands the convolved line must carry C2.5's "
                     "mandatory caveat: 'the loan-layer width is assumed "
                     "floor-invariant; not tested'. The coordinator re-runs "
                     "layer_convolution once both probe artifacts exist."),
            "pass": None,
        }
        print(f"  P4 PENDING — missing {len(probe_missing)} probe artifact(s); "
              "excluded from parity_gates_all_pass")
    else:
        p4_within = all(c["within_tolerance"] for c in probe_cells.values())
        p4_block = {
            "status": "RUN", "reps": P4_REPS, "floors": list(P4_FLOORS),
            "ref_floor_pct": P4_REF_FLOOR, "ref_width_5_95_pp": ref5_95,
            "percentiles": list(P4_PCTL), "tol_rel": P4_TOL_REL,
            "cells": probe_cells,
            "widths_pp": {k: v["width_5_95_pp"] for k, v in probe_cells.items()},
            "within_tolerance": bool(p4_within),
            "excluded_from_parity_gates_all_pass": False,
            "note": ("NOT blocking in either direction — it ROUTES the landing "
                     "(C2.5): inside tolerance the additive convolution stands "
                     "as specified; outside, the convolved line is reported "
                     "ONLY at 4.991% with the floor dependence disclosed and "
                     "the RSS is not claimed across the floor range."),
            "pass": True,
        }
        print(f"  P4 within_tolerance = {p4_within}")
    gate_report["P4_floor_invariance_probe"] = p4_block

    # =====================================================================
    # THE VERDICT RULE (ex ante, no discretion)
    # =====================================================================
    wider = bool(conv_width > FLOOR_READ_WIDTH_PP)
    comonotone_width = float(floor_width + loan_width)

    blocking_pass = all(v.get("pass") is True for k, v in gate_report.items()
                        if k != "P4_floor_invariance_probe")
    all_pass = bool(blocking_pass and (p4_pending or p4_block["pass"] is True))

    if not wider:
        gate_report["VERDICT_RULE_wider_than_floor_read"] = {
            "convolved_width_pp": conv_width,
            "floor_read_width_pp": FLOOR_READ_WIDTH_PP,
            "rule": "a sum of independent variates cannot narrow; if the "
                    "convolved width does not exceed the floor-read width the "
                    "construction is wrong",
            "pass": False}
        _fail_out("GATE_FAILURE", gate_report, t0, {
            "convolved_primary": {"ci95_pp": conv_ci_pp, "width_pp": conv_width},
            "layers": {"floor_wild_t": {"ci95_pp": floor_ci_pp,
                                        "width_pp": floor_width},
                       "loan_cluster": {"ci95_pp": loan_ci,
                                        "width_pp": loan_width}}})

    # ---- RSS prediction recomputed from the realized half-widths (A2) ------
    rss_lo = float(np.hypot(CENTER_PP - floor_ci_pp[0], CENTER_PP - loan_ci[0]))
    rss_hi = float(np.hypot(floor_ci_pp[1] - CENTER_PP, loan_ci[1] - CENTER_PP))
    rss_pred = [CENTER_PP - rss_lo, CENTER_PP + rss_hi]

    caveat = ("" if not p4_pending else
              " P4 IS PENDING: until the two band-end probes land, the "
              "convolved line must carry 'the loan-layer width is assumed "
              "floor-invariant; not tested'.")
    if p4_pending:
        action_p4 = ("P4 not run at write time — do not land the convolved line "
                     "without either the probe result or C2.5's untested "
                     "caveat.")
    elif p4_within:
        action_p4 = ("P4 inside tolerance: the additive convolution stands as "
                     "specified across the band ends.")
    else:
        action_p4 = ("P4 OUTSIDE tolerance: report the convolved line ONLY at "
                     "the 4.991% floor, disclose the floor dependence of the "
                     "loan-layer width in the tablenote, and do NOT claim the "
                     "RSS relation across the floor range.")

    verdict = {
        "wider_than_committed": wider,
        "convolved_width_pp": conv_width,
        "floor_read_width_pp": FLOOR_READ_WIDTH_PP,
        "width_excess_pp": float(conv_width - FLOOR_READ_WIDTH_PP),
        "p4_probe_pending": p4_pending,
        "p4_within_tolerance": p4_within,
        "manuscript_action": (
            "LABELED SECOND LINE, NOT A REPLACEMENT (PLAN Decision record item "
            "4). (1) tab:uncertainty tex 357, headline row 'Sampling 95% CI': "
            f"append the convolved pair [{conv_ci_pp[0]:+.2f}, "
            f"{conv_ci_pp[1]:+.2f}]pp naming run layer_convolution, stating "
            "that independence is ASSUMED and not measured, and quoting the "
            f"comonotone width {comonotone_width:.2f}pp as the bound under "
            "maximal positive dependence. DO NOT disturb the bracket-form "
            "binding-layer literal, $[+4.63, +6.92]$ (liveness_gates.py:4175) "
            "or 25.8 (:4177), and confirm :4167's width_ratio_vs_floor_read "
            "< 0.5 is unaffected (it is against the PERCENTILE width). "
            "(2) tex 301: append the side-by-side sentence giving "
            f"$+{conv_ci_pp[0]:.1f}$ to $+{conv_ci_pp[1]:.1f}$ points as the "
            "one number a reader who wants one number should use, with the "
            "reason it does not replace the floor read. (3) tex 364 tablenote: "
            "one clause recording that the loan/stratum input is itself a "
            "lower bound, so the convolved line is a lower bound too. NOT "
            "LANDING: abstract tex 30, tab:headline tex 76, tab:crosswalk tex "
            "677, conclusion tex 605/611. [posture-adjacent: the tex 301 "
            "sentence re-ranks the uncertainty layers — Eugene sees the draft "
            "before it lands.] Per A4 re-anchor every literal to the current "
            "printed pair and re-derive the census with count-asserted "
            "replacements." + caveat + " " + action_p4),
    }

    payload = {
        "mode": "layer_convolution",
        "status": "OK",
        "spec": (
            "The floor-read layer and the loan-sample layer summed as "
            "INDEPENDENT draws on the marginal (pp) scale and reported as a "
            "labeled second line, never as a replacement. Floor layer: a "
            "confidence distribution built from C1's 9,999 Webb wild-t draws, "
            "R_b = R_smm - t*_b*se_cr1_smm on the SMM scale, converted by "
            "CPR = 100(1-(1-SMM)^12) and mapped through the committed "
            "floor_sweep PCHIP at band 6.5 under C1's grid-edge truncation "
            "convention (flagged and counted, never extrapolated). Loan layer: "
            "deviations of the 200 committed stratum-cluster marginal_pp "
            "replicates from the COMMITTED POINT +5.5715581829pp, a centering "
            "fixed ex ante (the replicate median 5.6407 / mean 5.6830 would "
            "smuggle a +0.07/+0.11pp recentering into the headline layer). "
            "Convolved by exact enumeration of the full 9,999 x 200 outer sum. "
            "Secondary line: the same construction on the 1,000 percentile "
            "floor replicates regenerated under the committed rng-42 cluster "
            "bootstrap, with BOTH truncation conventions' counts disclosed. "
            "Independence is an ASSUMPTION, not a measurement, and is the "
            "lower bound of a dependence bracket whose upper bound is the "
            "comonotone sum; one summand (the loan/stratum interval) is itself "
            "a lower bound, so the convolved line is a lower bound too. Gates "
            "P0-P4 as in the header; verdict rule: the convolved width must "
            "exceed the floor-read width. NO ENGINE RUNS, NO REFIT, NO "
            "RESIMULATION; pure post-processing plus the single committed FRED "
            "MORTGAGE30US fetch inherited from mdr.build_panel."),
        "spec_source": ("specs/SPEC_round28_C1_C2_C3_C6.md SPEC C2, with the "
                        "trailing C2 AMENDMENTS block A1-A6 (PRE-RUN, "
                        "2026-07-29) APPLIED and overriding the base spec "
                        "wherever they conflict"),
        "amendments_applied": {
            "A1": "P2 re-anchored to C1's REALIZED Webb interval "
                  "[2.8549950653913494, 8.677971792194077] (width "
                  "5.822976726802727), not C2.3's pre-C1 predicted "
                  "[2.796, 8.723] (width 5.9268); R_smm, se_cr1_smm and the "
                  "t* CSV pinned and asserted against the C1 artifact.",
            "A2": "expectation restated at realized widths: w2/w1 = 0.3939, "
                  "RSS +7.5%, predicted [+2.67, +8.93]pp width 6.26pp, "
                  "comonotone bound 8.117pp; VERDICT RULE unchanged (the "
                  "convolved width must exceed 5.822976726802727pp).",
            "A3": "the P4 band-end anchors are the committed band-6.5 cells of "
                  "oos_identification_results.json .instrument1_marginal_table, "
                  "already pinned into bootstrap_pathb_cluster.ANCHORS_BY_FLOOR.",
            "A4": "landing literals re-anchored to the post-C1 printed pair; "
                  "the C2.4 draft sentences are re-anchored to current text at "
                  "apply time with count-asserted replacements.",
            "A5": "the 1,000 percentile floor draws were NOT persisted by C1, "
                  "so C2.0's standalone fallback is executed as STEP 0 here "
                  "and gated bit-exactly (P0).",
            "A6": "the interaction probe RUNS (not declined); this script "
                  "consumes its floor-tagged artifacts and marks P4 PENDING "
                  "if they have not landed yet.",
        },
        "spec_deviations": [
            "P2 is split into P2a (quantile route, tol 1e-12) and P2b "
            "(per-draw route, tol 1e-6 pp plus a tolerance-free shared "
            "order-statistic bracket assertion). SPEC C2.2 claims the per-draw "
            "percentiles reproduce C1 'exactly'; they cannot, because "
            "np.percentile interpolates linearly between order statistics and "
            "the floor->marginal map is curved, so interpolate-then-map (C1) "
            "and map-then-interpolate (this line) differ by "
            "~(1/2)|g''|w(1-w)h^2 = O(1e-7)pp at B=9,999. A 1e-9 gate would "
            "fail on an interpolation artifact and land nothing. The realized "
            "residual and the bracket width are both reported so the loosened "
            "tolerance is auditable.",
            "P3's 'loan deviations set to zero' is read as the degenerate "
            "one-point loan layer {0} (the outer sum is the retained set "
            "itself). Replicating each retained value 200x changes the "
            "percentile interpolation index and is a different number; that "
            "variant is reported as a diagnostic, not as the gate.",
            "P4 is NOT blocking in either direction — it routes the landing, "
            "per C2.5's own text. A probe results JSON that disagrees with its "
            "own draws CSV row count IS blocking (data integrity, distinct "
            "from the tolerance question). A missing probe artifact marks P4 "
            "PENDING and excludes it from parity_gates_all_pass.",
            "P0 is added to the C2.6 schema (the schema names P1..P4 only) "
            "because amendment A5 makes the percentile regeneration a gated "
            "step of THIS run rather than an inherited C1 by-product.",
            "The committed loan sd's ddof is undocumented, so both are "
            "computed and the matching one is adopted and recorded "
            "(sd_ddof_matched); it is the ddof used for every sd reported "
            "here.",
            "dependence_bracket.comonotone_width_pp is RECOMPUTED from the "
            "realized layer widths rather than taking A2's 8.117 arithmetic as "
            "an input.",
            "$B companions to every pp quantity are computed on the same "
            "construction (floor layer through the PCHIP's marginal_b; loan "
            "deviations centred on the committed $42.60839388108866B anchor "
            "delta) because C2.6's schema asks for convolved_primary.ci95_b.",
        ],
        "parity_gates": gate_report,
        "parity_gates_all_pass": all_pass,
        "inputs": {
            "floor_tstar_csv": str(TSTAR_WEBB_CSV),
            "floor_tstar_source": (f"{C1_ARTIFACT.name} reads.{R2}."
                                   "wild_t_webb (Webb six-point, B=9999, "
                                   "default_rng(42))"),
            "floor_percentile_source": (
                "REGENERATED in this run (amendment A5): "
                "fu.cluster_bootstrap_cpr on the R2 selection, n_reps=1000, "
                "fresh np.random.default_rng(42); gated on P0. C1 persisted "
                "only the t* CSVs."),
            "loan_draws_csv": str(LOAN_DRAWS_CSV),
            "loan_draws_field": "marginal_pp (and marginal_b for the $B line)",
            "n_floor_reps": int(B_WILD),
            "n_floor_reps_percentile": int(pct_draws.size),
            "n_loan_reps": int(m.size),
            "centering_convention": (
                "the COMMITTED POINT marginal at this floor, fixed ex ante — "
                "NOT the replicate median or mean"),
            "center_pp": CENTER_PP,
            "center_b": CENTER_B,
            "center_pp_unrounded_reference": CENTER_PP_UNROUNDED,
            "loan_replicate_median_pp_not_used": LOAN_MEDIAN_PP,
            "loan_replicate_mean_pp_not_used": LOAN_MEAN_PP,
            "R_smm": R_SMM, "se_cr1_smm": SE_CR1_SMM,
            "pchip_grid_pct": [float(v) for v in mapping.x],
            "sd_ddof": SD_DDOF,
        },
        "layers": {
            "floor_wild_t": {
                "ci95_pp": floor_ci_pp, "ci95_b": floor_ci_b,
                "width_pp": float(floor_width),
                "c1_ci95_pp": list(C1_WEBB_CI95_PP),
                "c1_width_pp": FLOOR_READ_WIDTH_PP,
                "median_pp": float(np.median(M_pp)),
                "sd_pp": float(np.std(M_pp, ddof=SD_DDOF)),
                "n_reps": int(M_pp.size),
                "n_truncated_at_edge": fl["n_truncated_at_edge"],
                "n_truncated_above_grid_hi": fl["n_truncated_above_grid_hi"],
                "n_truncated_below_grid_lo": fl["n_truncated_below_grid_lo"],
                "truncation_convention": fl["convention"],
                "floor_pct_min": float(floor_cpr.min()),
                "floor_pct_max": float(floor_cpr.max()),
            },
            "floor_percentile": {
                "ci95_pp_edge_truncation": sec_edge_ci,
                "ci95_pp_exclusion": sec_excl_ci,
                "width_pp_edge_truncation": float(sec_edge_ci[1] - sec_edge_ci[0]),
                "width_pp_exclusion": float(sec_excl_ci[1] - sec_excl_ci[0]),
                "n_reps": int(pct_draws.size),
                "n_truncated_at_edge": sec_edge["n_truncated_at_edge"],
                "n_truncated_above_grid_hi": sec_edge["n_truncated_above_grid_hi"],
                "n_truncated_below_grid_lo": sec_edge["n_truncated_below_grid_lo"],
                "n_draws_outside_grid_excluded": sec_excl["n_draws_outside_grid"],
                "n_retained_under_exclusion": sec_excl["n_retained"],
                "committed_exclusion_ci95_pp": list(COMMITTED_PERCENTILE_PP),
                "disclosure": (
                    f"{sec_excl['n_draws_outside_grid']} of {pct_draws.size} "
                    "percentile draws fall outside the committed grid, all "
                    "ABOVE the 6.0% floor edge, i.e. all on the LOW-marginal "
                    "side — the side the lower edge is read from. The "
                    "committed interval dropped them; this line clips them to "
                    "the edge instead. Both counts are reported."),
            },
            "loan_cluster": {
                "ci95_pp": loan_ci, "width_pp": float(loan_width),
                "sd_pp": float(np.std(m, ddof=SD_DDOF)),
                "median_pp": float(np.median(m)),
                "n_reps": int(m.size),
                "effective_clusters": LOAN_EFFECTIVE_CLUSTERS,
                "deviation_min_pp": float(d_pp.min()),
                "deviation_max_pp": float(d_pp.max()),
                "is_itself_a_lower_bound": True,
                "lower_bound_note": (
                    "no wild-cluster correction is run for the loan/stratum "
                    "scheme; tab:uncertainty's tablenote already calls its "
                    "interval better read as a lower bound on sampling "
                    "uncertainty than as calibrated 95% coverage. A sum with a "
                    "lower-bound summand is a lower bound."),
            },
        },
        "convolved_primary": {
            "ci95_pp": conv_ci_pp, "ci95_b": conv_ci_b,
            "width_pp": float(conv_width),
            "width_b": float(conv_ci_b[1] - conv_ci_b[0]),
            "median_pp": float(np.median(conv_pp)),
            "sd_pp": float(np.std(conv_pp, ddof=SD_DDOF)),
            "width_ratio_vs_floor_read": float(conv_width / FLOOR_READ_WIDTH_PP),
            "width_ratio_vs_realized_floor_layer": float(conv_width / floor_width),
            "n_pairs": int(conv_pp.size),
            "construction": ("exact enumeration of the full outer sum "
                             "{M_b + d_j}, not a Monte-Carlo sub-sample"),
        },
        "convolved_percentile_secondary": {
            "ci95_pp": sec_conv_ci_pp,
            "ci95_b": pct(sec_conv_b),
            "width_pp": float(sec_conv_width),
            "median_pp": float(np.median(sec_conv_pp)),
            "sd_pp": float(np.std(sec_conv_pp, ddof=SD_DDOF)),
            "n_pairs": int(sec_conv_pp.size),
            "floor_convention_used": "edge truncation",
            "ci95_pp_exclusion_variant": sec_conv_excl_ci_pp,
            "companion_to": "the committed percentile layer [+3.0, +8.0]",
        },
        "dependence_bracket": {
            "independent_width_pp": float(conv_width),
            "comonotone_width_pp": comonotone_width,
            "comonotone_components_pp": {"floor_layer": float(floor_width),
                                         "loan_layer": float(loan_width)},
            "recomputed_in_script": True,
            "independence_is_assumed_not_measured": True,
            "note": ("the two layers sit on disjoint data and disjoint time "
                     "and nothing in any committed artifact links a 2018 "
                     "cohort-month cluster ratio to a window-period "
                     "composition resample; independence is the LOWER bound of "
                     "the bracket and the comonotone sum is the upper bound"),
        },
        "expectation_check": {
            "predicted_ci95_pp": list(PREDICTED_CI95_PP),
            "predicted_width_pp": PREDICTED_WIDTH_PP,
            "predicted_rss_width_ratio": PREDICTED_RSS_RATIO,
            "realized_ci95_pp": conv_ci_pp,
            "realized_width_pp": float(conv_width),
            "abs_err_pp": float(abs(conv_width - PREDICTED_WIDTH_PP)),
            "abs_err_endpoints_pp": [
                float(abs(conv_ci_pp[0] - PREDICTED_CI95_PP[0])),
                float(abs(conv_ci_pp[1] - PREDICTED_CI95_PP[1]))],
            "rss_prediction_recomputed_pp": rss_pred,
            "rss_prediction_recomputed_width_pp": float(rss_hi + rss_lo),
            "rss_half_widths_pp": {"lower": rss_lo, "upper": rss_hi},
            "realized_width_ratio": float(conv_width / floor_width),
            "source": "amendment A2",
        },
        "floor_invariance_probe": p4_block,
        "verdict": verdict,
        "runtime_s": round(time.perf_counter() - t0, 1),
    }

    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2, default=lambda o: o.item())
        f.write("\n")

    print("\n" + "=" * 72)
    print(f"ALL BLOCKING GATES PASS = {blocking_pass}; "
          f"parity_gates_all_pass = {all_pass}")
    print(json.dumps(verdict, indent=2, default=lambda o: o.item()))
    print(f"\nfrozen -> {RESULTS_JSON}")


if __name__ == "__main__":
    main()
