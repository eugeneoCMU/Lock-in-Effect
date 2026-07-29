#!/usr/bin/env python3
"""
episode_confrontation_within.py — composition-standardized confrontation of the
committed episode gradient (round-28 WP-I1; three referees ask for the
"within-stratum" version of the tex-292 exhibit).

PRE-COMMITTED SPEC (fixed in this header BEFORE any run; full drafting spec at
specs/SPEC_round28_D_F1_I1_I3_J2_S8.md SPEC I1 — its parameterization,
feasibility gate, thresholds, gates, tolerances, branch map and artifact schema
are adopted unchanged). Ex-ante convention of episode_confrontation.py /
floor_uncertainty.py / matched_depth_reconciliation.py.

=======================================================================
THE STRUCTURAL FINDING THAT DEFINES THIS RUN (absorb before reading further)
=======================================================================
episode_confrontation.py assigns gap buckets PER STRATUM from the stratum's
exposure-weighted window-mean gap (episode_confrontation.py:668-678), and the
stratum id CONTAINS coupon (stratum.build_stratum_id: vintage_couponbps_fico_
ltv), while gap = coupon - market_rate. Every stratum therefore lives in
exactly ONE bucket by construction. A "within-stratum gradient" in the literal
sense is NOT COMPUTABLE, EVER — not for want of data, but because the
conditioning set and the treatment are the same variable. Any run that
"re-runs within the vintage x coupon x FICO x LTV cells" is an empty run.

What the referees are actually asking for is COMPOSITION CONTROL: remove the
credit/vintage differences between the shallow and deep buckets that tex 292
names as the confound ("credit composition, within-window refinancing on the
high-coupon shallow buckets, residual seasoning past the age cut"). That is
computable, on the axes of the stratum id OTHER than coupon. Hence:

    COMPOSITION CELL  c = (vintage, fico_bucket, ltv_bucket)
                        = the stratum id with the coupon dimension removed.

=======================================================================
THREE LIMBS (all on the existing panel; NO engine run anywhere)
=======================================================================
LIMB A (PRIMARY) — composition-standardized gradient. Direct standardization
  in the template already used and disclosed in this paper: floor_uncertainty
  .py:478-521 (part_b_age_standardization, the run behind tab:assembly's "84%
  imputed weight" row). Reweight the DEEP endpoint bucket's composition cells
  to the SHALLOW endpoint bucket's cell-weight vector; where a cell carries
  shallow weight but no deep support, IMPUTE by ratio-scaling from the nearest
  populated common cell — the analogue of floor_uncertainty.py:489's
      used = r18_oldest * (rin / rin_oldest)
  here
      used(c) = CPR_deep(ref) * ( CPR_shallow(c) / CPR_shallow(ref) )
  with floor_uncertainty.py:494-499's FLAT FALLBACK (used = CPR_deep(ref))
  when the reference's shallow read is not computable or zero — and REPORT THE
  IMPUTED WEIGHT SHARE, exactly as floor_uncertainty.py:493,499,514 does.
  "Nearest" (the analogue of that template's "oldest populated bucket") is
  fixed ex ante and mechanically: L1 distance in the ordinal encoding
  (vintage year; fico <680<680-740<740+; ltv <=80 < >80), each axis step
  counting 1, ties broken by larger deep exposure then by cell id.
  STATISTIC   G_std = CPR_shallow_standardized - CPR_deep_standardized,
  both sides aggregated with the SAME shallow weight vector w_c (so the
  statistic is zero when the two buckets share composition and cell CPRs; the
  pooled-shallow variant is reported alongside, never primary).
  UNCERTAINTY joint stratum-cluster bootstrap, 1000 reps, seed 42 — the
  imported joint_gradient_bootstrap's resampling convention (ONE
  default_rng(42) stream, shallow cluster indices drawn first, then deep, per
  replicate block). joint_gradient_bootstrap IS imported and used verbatim for
  the raw gradient, and this run's standardized bootstrap reproduces its index
  stream exactly: the raw gradient recomputed from THIS run's indices is
  asserted bit-equal (1e-12) to the imported function's draws. Weights are
  resampled with the data (they are estimated), and the imputation rule is
  re-applied inside every replicate; the mean imputed weight share across
  replicates and the count of degenerate replicates are reported.

LIMB B — exact within/between decomposition of the committed +4.198pp.
  Always computable (it is an identity), so it never degenerates; this is the
  number that adjudicates the defence. Pooled dollar SMM is EXACTLY the
  exposure-weighted mean of composition-cell SMMs (numerator and denominator
  are both sums), so with
      SMM_deep* = sum_c w_shallow(c) * SMM_deep(c)      (deep under shallow mix)
      CPR(s)    = 100 * (1 - (1-s)^12)
  the split
      between = CPR(SMM_deep*) - CPR(SMM_deep)
      within  = CPR(SMM_shallow) - CPR(SMM_deep*)
  TELESCOPES to the committed total exactly — identity_residual is zero by
  construction and is computed and asserted (<1e-12), not assumed. Cells
  carrying support in only one endpoint bucket take the other bucket's cell
  SMM as the placeholder, so their within contribution is zero and the whole
  difference there loads on BETWEEN (the honest reading: a cell one bucket
  does not occupy is composition, not behaviour). The unmatched exposure
  shares are reported. The symmetric (average-weight, Oaxaca two-fold) split
  is reported alongside as a robustness read, with its own residual. The
  between component is ALSO reported axis by axis (vintage only; fico x ltv
  only; full cell) — under FG-2 the vintage axis is handled by reporting
  Limb B's vintage component separately.

LIMB C (SECONDARY, identified by construction; REPORTED, NEVER PRIMARY) —
  stratum-fixed-effects within estimator. Monthly dollar SMM on the monthly
  decimal gap with stratum FE over the 40-month window, exposure-weighted
  (the paper's pooled-dollar convention; the unweighted read is reported as a
  variant), stratum-clustered CRVE with the usual G/(G-1) x (N-1)/(N-K)
  correction. CONFOUND NAMED EX ANTE AND EXACTLY: within a stratum the coupon
  is constant, so gap_it = coupon_i - r_t is a deterministic function of
  calendar time; the within regressor is identified ONLY off the unbalanced
  panel (which months each stratum is observed in, and with what exposure
  weight). Seasoning and seasonality therefore load onto it in full, and a
  two-way (stratum + month) FE version is EXACTLY unidentified — it is not run.
  The share of within-transformed regressor variance explained by month dummies
  is reported as the size of that confound.

=======================================================================
FEASIBILITY GATE FG (evaluated BEFORE any outcome is read; disposition fixed
here, not after the run)
=======================================================================
From exposure_upb and cell counts ONLY — prepaid_upb is NOT touched until FG
resolves (the episode_confrontation.py:102-110 ex-ante-inspection convention).
Reported: the number of composition cells carrying BOTH endpoint buckets,
their share of the shallow bucket's exposure (and of the deep bucket's), and
their stratum counts.
    coverage_shallow = (exposure of shallow-bucket rows in common cells)
                       / (exposure of all shallow-bucket rows)
    coverage_deep    = the same with the deep bucket
    common cell      = a cell carrying >=1 stratum in BOTH endpoint buckets,
                       inside the PRIMARY (age-matched, bucketed) selection.
The risk is concrete and sized ex ante: the primary selection's shallow
endpoint B1 [-1,0) has 35 strata, 1.08% exposure, mean coupon 6.02%; the deep
endpoint B4 <=-3 has 52 strata, 16.38% exposure, mean coupon 3.37% (committed
artifact). A 6.02% and a 3.37% coupon in a 2017-2021 Freddie sample are
2018-19 and 2020-21 originations — B1 and B4 may occupy nearly disjoint
vintages, and vintage-blocked overlap may be thin or empty.
  FG-1  coverage_shallow >= 30% AND >= 10 common cells
        -> Limb A on (vintage, fico_bucket, ltv_bucket);
           standardization_axis "vintage_fico_ltv".
  FG-2  coverage_shallow < 30% -> Limb A FALLS BACK to (fico_bucket,
        ltv_bucket) only (vintage dropped), and the vintage axis is handled by
        reporting Limb B's vintage component separately;
        standardization_axis "fico_ltv_only".
  FG-3  even FG-2 fails -> Limb A is NOT_COMPUTABLE. This is a LANDING, not a
        failure (branch (c)); Limbs B and C still run and are reported.
  DOCUMENTED THRESHOLD ADAPTATION (the one place the spec's arithmetic does
  not close, resolved here ex ante and disclosed in the artifact): the panel
  carries 5 vintages x 3 FICO x 2 LTV = 30 possible cells on FG-1's axis, so
  ">= 10 cells" is attainable there; on FG-2's fallback axis there are at most
  3 x 2 = 6 cells, so a literal ">= 10" would make FG-2 unreachable and FG-3
  automatic — i.e. it would delete the branch the spec builds. The 30%
  coverage bar is therefore carried across UNCHANGED, and the cell-count bar
  on the fallback axis is 2 (the least at which standardization can move
  anything). Both bars, and what a literal 10 would have returned, are written
  into the artifact.

=======================================================================
PARITY GATES (BLOCKING; G0-G4 are episode_confrontation.py's OWN gates, run
UNCHANGED and FIRST; on any failure the JSON is written with status
GATE_FAILURE and the run stops)
=======================================================================
  G0-G4  replicated line-for-line from episode_confrontation.py:512-655
         (production constants; E3 pooled Freddie velocity
         -0.07438857974396679, n=39, <1e-9; six E3 per-cohort lag-0
         velocities <1e-9; vintage_residual_bound pooled-SMM anchor
         4.302657826519651% <=1e-6pp from cohort_month_panel_fannie.parquet;
         floor_uncertainty R2 read 4.990624060575566%, n=137, clusters=31
         <=0.001pp). Their constants and tolerances are READ FROM the
         committed module (ec.E3_POOLED_FREDDIE, ec.TOL_*, ...) so there is
         one source of truth; episode_confrontation.py is imported, never
         modified, and its main() is never called (calling it would rewrite
         its frozen artifact, which MUST NOT CHANGE).
  G5     frozen-artifact reproduction (NEW): the committed raw gradient
         +4.198179219676357, CI [3.5852591750975797, 4.656477952145319],
         implied(mid) +0.9371125522400376, B2-vs-B4 +2.414104180240706 to
         1e-9, and injected power at beta_1=0.069 0.675 to 1e-3 — recomputed
         here from the imported bucket_block / joint_gradient_bootstrap /
         permutation machinery on the same panel, and checked against BOTH
         the frozen artifact and the literals quoted in this header (which
         are first asserted equal to the artifact at 1e-12). Power is a mean
         over 200 permutations at a fixed seed, so exact reproduction is
         expected; a miss is an ENVIRONMENT ALARM, not a finding.
  ORDER  G0-G4 -> selection + FG (exposure and counts only) -> G5 (the first
         read of prepaid_upb on this run's selection) -> Limbs A/B/C. G5 is
         blocking and sits after FG precisely so that FG cannot be tuned on an
         outcome; G0-G4 already establish environment integrity before it.
  STOP-E any of G0-G4 fails, OR cohort_month_panel_fannie.parquet is absent
         (G3 consumes it). Checked before anything else runs. _fail_out halts.

=======================================================================
HELD AT PRODUCTION (identical to the committed run)
=======================================================================
Window 202206..202509 (40 months, asserted); coupon>0 & exposure_upb>0; gap on
the calendar-month FRED ME-mean (ONE fetch, via the imported build_panel);
buckets [-1,0)/[-2,-1)/[-3,-2)/<=-3 with gap>=0 excluded; primary seasoning cut
age0 >= 24; endpoint support rule >=1% exposure AND >=10 strata; pooled dollar
SMM -> CPR = 1-(1-SMM)^12, cumulative 1-(1-SMM)^40; analytic model counterpart
with covariate multiplier 1; RNG_SEED = 42 everywhere; caches not consulted;
config.py never edited; no .tex edit.

=======================================================================
PRE-COMMITTED EXPECTATION
=======================================================================
NONE on the outcome — this is the test the paper lacks, and the review says so
explicitly. The only pre-committed quantities are FG's thresholds, the parity
targets, and the branch map below.

=======================================================================
LANDING RULE PER BRANCH (fixed ex ante; every tex landing queues for Eugene)
=======================================================================
Let G_std be Limb A's standardized gradient with 95% CI and G_model = +0.937.
Evaluation order (total and deterministic): (c) if FG-3; else (d) if the CI is
wholly negative; else (b); else (a); else (d) as the residual STOP.
  (a) GAP PERSISTS — G_std's CI excludes G_model from above (lo > G_model).
      The composition-confounding defence at tex 292 falls as stated; tex 292's
      closing sentence is replaced by the tested version; the finding enters
      tab:assembly (tex 313-334) as an UPWARD entry, labelled in the Status
      column "directional; not a marginal re-estimate" (the gradient is a
      cross-sectional LEVEL object, the marginal is a DOLLAR object).
      [posture] posture-adjacent: it is the first upward entry sourced from
      realized data and the assembly is what the retired-posture decision
      rests on. Direction drafted; Eugene signs.
  (b) GAP CLOSES MATERIALLY — the CI contains G_model, OR G_std falls below
      half the raw +4.198. The defence is VINDICATED and stated as tested:
      "...and the confound is measured: standardizing to common [vintage x]
      FICO x LTV cells moves the gradient from $+4.20$ to $+X.XX$ points."
      No assembly row. liveness_gates.py:4396-4406 is EXTENDED, not replaced —
      "$+4.20$ CPR points" stays as the raw number.
  (c) NOT_COMPUTABLE (FG-3) — land the negative result, which is itself the
      answer three referees asked for: the within-stratum control this exhibit
      needs is not identified in this panel, because the gradient axis
      (coupon) and the vintage axis are nearly collinear in a 2017-2021
      sample. Reported at tex 292 with the coverage number. No assembly row,
      no gate change beyond the artifact reference.
  (d) WRONG SIGN / Limb A negative CI, or any outcome the map above does not
      classify — STOP. Report, diagnose, land nothing; the same disposition as
      the committed script's T4. status STOP, SystemExit after the artifact is
      written.

MUST NOT CHANGE: episode_confrontation.py and its committed artifact (this is
a NEW script with a NEW artifact; the committed machinery is IMPORTED);
matched_depth_reconciliation.build_panel; floor_uncertainty.cluster_bootstrap_
cpr; the bucket rule, the age cut and the support rule; +4.20, [+3.59,+4.66],
+0.94, 0.68, p = 0.005 at tex 292 and at liveness_gates.py:4396-4406;
config.py; any .tex file.

Run:  cd hazard && python3 episode_confrontation_within.py
      -> data/episode_confrontation_within_results.json (frozen)
No engine runs; one FRED MORTGAGE30US fetch (inside the imported build_panel).
Deterministic, seed 42 throughout. Runtime target < 10 minutes.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
HAZARD_DIR = ROOT / "hazard"
DATA_DIR = HAZARD_DIR / "data"
if str(HAZARD_DIR) not in sys.path:
    sys.path.insert(0, str(HAZARD_DIR))

# House machinery — imported, not reimplemented (floor_uncertainty.py posture).
import matched_depth_reconciliation as mdr  # build_panel / cpr_of  # noqa: E402
import floor_uncertainty as fu              # cluster_bootstrap_cpr / _select  # noqa: E402
import literature_hazard as lh              # baseline / floor / rothstein_beta1  # noqa: E402
import episode_confrontation as ec          # the committed run: gates + machinery  # noqa: E402
from episode_confrontation import (         # noqa: E402  used VERBATIM
    bucket_block,
    cluster_sums,
    gap_bucket,
    joint_gradient_bootstrap,
)
from config import (                        # noqa: E402
    BASELINE_MODE,
    FLOOR_MODE,
    INVOLUNTARY_CPR_ANNUAL,
    P_Q_BASELINE,
    PSA_SPEED,
    QT_END,
    QT_START,
    ROTHSTEIN_Q_DECLINE_HIGH,
    ROTHSTEIN_Q_DECLINE_LOW,
    ROTHSTEIN_Q_DECLINE_MID,
)
from stratum import build_stratum_id        # noqa: E402

# episode_confrontation already appended ROOT/"abm"; repeated for explicitness.
if str(ROOT / "abm") not in sys.path:
    sys.path.append(str(ROOT / "abm"))
import cohort_timing_diagnostic as e3       # noqa: E402

RESULTS_JSON = DATA_DIR / "episode_confrontation_within_results.json"
COMMITTED_ARTIFACT = ec.RESULTS_JSON        # READ ONLY — never written by this run

# ---- G5 targets: the five frozen values quoted ex ante (SPEC I1) ------------
REF_GRADIENT_PP = 4.198179219676357
REF_CI95_PP = (3.5852591750975797, 4.656477952145319)
REF_IMPLIED_MID_PP = 0.9371125522400376
REF_POWER_069 = 0.675
REF_B2_B4_PP = 2.414104180240706
REF_VERDICT = "T5"
TOL_G5 = 1e-9
TOL_G5_POWER = 1e-3
TOL_QUOTE = 1e-12

# ---- pre-committed run constants (production values re-read from ec) --------
SEED = ec.SEED                      # 42
N_BOOT = ec.N_BOOT                  # 1000
N_PERM = ec.N_PERM                  # 200
BUCKET_ORDER = ec.BUCKET_ORDER
AGE0_MIN = ec.AGE0_MIN              # 24
SUPPORT_MIN_SHARE = ec.SUPPORT_MIN_SHARE      # 0.01
SUPPORT_MIN_STRATA = ec.SUPPORT_MIN_STRATA    # 10
WINDOW = ec.WINDOW                  # (202206, 202509)
T_MONTHS = ec.T_MONTHS              # 40
Z_ONE_SIDED_95 = ec.Z_ONE_SIDED_95

# ---- FG thresholds (pre-committed) -----------------------------------------
FG_MIN_COVERAGE = 0.30
FG_MIN_CELLS_FULL = 10
FG_MIN_CELLS_FALLBACK = 2           # see the header's documented adaptation
AXIS_FULL = ("vintage", "fico_bucket", "ltv_bucket")
AXIS_FALLBACK = ("fico_bucket", "ltv_bucket")
AXIS_NAME = {AXIS_FULL: "vintage_fico_ltv", AXIS_FALLBACK: "fico_ltv_only"}

# ---- ordinal encodings for the nearest-populated-cell rule (ex ante) -------
FICO_ORDER = {"<680": 0, "680-740": 1, "740+": 2}
LTV_ORDER = {"≤80": 0, ">80": 1}

# ---- branch (b)'s "materially closed" bar -----------------------------------
HALF_RAW_PP = 0.5 * REF_GRADIENT_PP

BRANCH_SENTENCES = {
    "a": ("(a) GAP PERSISTS: standardizing the deep bucket to the shallow "
          "bucket's {AX} composition leaves the gradient at {G:+.3f} points "
          "(95% CI [{LO:+.3f}, {HI:+.3f}], imputed weight share {IW:.1f}%), "
          "against the production hazard's implied {M:+.3f}: the excess is "
          "NOT composition in the dimensions the panel can hold fixed. The "
          "tex-292 composition-confounding defence falls as stated; the "
          "finding enters tab:assembly as an UPWARD entry labelled "
          "'directional; not a marginal re-estimate'. What remains "
          "unresolved is within-window refinancing on the high-coupon "
          "shallow buckets, which no field in this design separates from "
          "moving. [posture] Eugene signs."),
    "b": ("(b) GAP CLOSES MATERIALLY: standardizing to common {AX} cells "
          "moves the gradient from {RAW:+.3f} to {G:+.3f} points (95% CI "
          "[{LO:+.3f}, {HI:+.3f}], imputed weight share {IW:.1f}%) against "
          "the implied {M:+.3f}. The tex-292 defence is VINDICATED and now "
          "stated as tested rather than asserted; +4.20 stays as the raw "
          "number and liveness_gates.py:4396-4406 is extended, not replaced. "
          "No assembly row."),
    "c": ("(c) NOT_COMPUTABLE (FG-3): the within-stratum control this exhibit "
          "needs is not identified in this panel. The gradient axis (coupon) "
          "and the vintage axis are nearly collinear in a 2017-2021 sample, "
          "so the shallow and deep buckets share {COV:.1f}% of "
          "composition-cell exposure ({NC} common cells) — too little to "
          "standardize. The confound is named, not measured, and the exhibit "
          "stays declined on that basis. Limb B still reports the exact "
          "within/between split ({WITHIN:+.3f} within, {BETWEEN:+.3f} "
          "between, of {TOTAL:+.3f})."),
    "d": ("(d) STOP ({SUB}): standardized gradient {G:+.3f} points, 95% CI "
          "[{LO:+.3f}, {HI:+.3f}], against the implied {M:+.3f} and the raw "
          "{RAW:+.3f}. Report every number, diagnose, land NOTHING — the same "
          "disposition as the committed script's T4."),
}


def _json_default(x):
    if isinstance(x, (np.floating, np.integer)):
        return float(x)
    if isinstance(x, np.bool_):
        return bool(x)
    if isinstance(x, np.ndarray):
        return [float(v) for v in x]
    return x


def _write(payload: dict) -> None:
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2, default=_json_default)
        f.write("\n")


def _fail_out(gate_report: dict, msg: str) -> None:
    """episode_confrontation._fail_out's contract, writing THIS run's artifact
    (ec._fail_out would overwrite the committed one, which MUST NOT CHANGE)."""
    _write({"mode": "episode_confrontation_within", "status": "GATE_FAILURE",
            "parity_gates": gate_report, "detail": msg})
    raise SystemExit(
        f"PARITY GATE FAILURE — {msg}. Environment problem; STOP. "
        f"Diagnostics in {RESULTS_JSON}. Do NOT build on a broken baseline."
    )


# ==========================================================================
# G0-G4 — episode_confrontation.py's own gates, replicated line-for-line
# SOURCE: episode_confrontation.py:512-655 (main()); constants and tolerances
# are read from the committed module so there is exactly one source of truth.
# The committed main() is deliberately NOT called: it would rewrite
# data/episode_confrontation_results.json, which MUST NOT CHANGE.
# ==========================================================================
def run_committed_gates_g0_g4() -> tuple[dict, pd.DataFrame, dict, float]:
    gates: dict = {}

    # ---- STOP-E precondition: the input G3 consumes ------------------------
    if not ec.FANNIE_PANEL.exists():
        _fail_out(gates, f"STOP-E: {ec.FANNIE_PANEL.name} absent from "
                         f"{DATA_DIR} (gitignored; G3 consumes it). Run in the "
                         f"main checkout or copy the file in first")

    # ---- committed artifacts, asserted vs the quoted constants (pre-gate) --
    with open(ec.E3_ARTIFACT) as f:
        e3_art = json.load(f)
    pooled_c = e3_art["realized_cohorts"]["pooled_velocity"]["freddie"]
    assert abs(pooled_c["delta_velocity_lag0"] - ec.E3_POOLED_FREDDIE[0]) < 1e-9
    assert pooled_c["n"] == ec.E3_POOLED_FREDDIE[1]
    assert abs(pooled_c["zero_band"] - ec.E3_POOLED_FREDDIE[2]) < 1e-9
    for k, v in ec.E3_COHORT_LAG0_FREDDIE.items():
        assert abs(e3_art["realized_cohorts"]["freddie"]["cohorts"][k]
                   ["delta_velocity_lag0"] - v) < 1e-9, k
    with open(ec.VRB_ARTIFACT) as f:
        vrb = json.load(f)
    assert abs(vrb["results"]["segments"]["sampled_2017_2021"]["cpr_pct"]
               - ec.VRB_SAMPLED_CPR_PCT) < 1e-9
    with open(ec.FU_ARTIFACT) as f:
        fu_art = json.load(f)
    r2 = fu_art["part_a_sampling_uncertainty"]["reads"]["R2_2018_gap<=-0.0025_age>=12"]
    assert abs(r2["point_cpr_pct"] - ec.FU_R2_READ[0]) < 1e-9
    assert r2["n_cohort_months"] == ec.FU_R2_READ[1]
    assert r2["n_clusters"] == ec.FU_R2_READ[2]

    print("=" * 72)
    print("PARITY GATES G0-G4 (episode_confrontation.py's own, unchanged, first)")
    print("=" * 72)

    # ---- G0 — production-constants integrity -------------------------------
    b_low = lh.rothstein_beta1(ROTHSTEIN_Q_DECLINE_LOW)
    b_mid = lh.rothstein_beta1(ROTHSTEIN_Q_DECLINE_MID)
    b_high = lh.rothstein_beta1(ROTHSTEIN_Q_DECLINE_HIGH)
    g0_checks = {
        "floor_mode_max": FLOOR_MODE == "max",
        "involuntary_cpr_4pct": INVOLUNTARY_CPR_ANNUAL == 0.04,
        "baseline_psa": BASELINE_MODE == "psa",
        "psa_speed_100": PSA_SPEED == 100.0,
        "p_q_baseline_0.06": P_Q_BASELINE == 0.06,
        "declines_5.5_6.5_7.7": (ROTHSTEIN_Q_DECLINE_LOW, ROTHSTEIN_Q_DECLINE_MID,
                                 ROTHSTEIN_Q_DECLINE_HIGH) == (0.055, 0.065, 0.077),
        "beta1_low_0.0577": abs(abs(b_low) - 0.0577) < 5e-4,
        "beta1_mid_rounds_to_0.069": round(abs(b_mid), 3) == 0.069,
        "beta1_high_0.0817": abs(abs(b_high) - 0.0817) < 5e-4,
    }
    gates["G0_production_constants"] = {
        **g0_checks,
        "beta1_signed": {"low": b_low, "mid": b_mid, "high": b_high},
        "pass": all(g0_checks.values()),
    }
    print(f"  G0 constants: |beta1| low/mid/high = {abs(b_low):.4f}/"
          f"{abs(b_mid):.4f}/{abs(b_high):.4f}, floor {INVOLUNTARY_CPR_ANNUAL}, "
          f"mode {FLOOR_MODE}  "
          f"[{'PASS' if gates['G0_production_constants']['pass'] else 'FAIL'}]")
    if not gates["G0_production_constants"]["pass"]:
        _fail_out(gates, "G0 production-constants integrity failed")

    # ---- G1/G2 — E3 realized-velocity parity -------------------------------
    raw = pd.read_parquet(mdr.PANEL_PATH)
    csv = pd.read_csv(e3.FOLDIN_CSV, index_col=0, parse_dates=True)
    rate_level = csv["MORTGAGE30US"].copy()
    rate_level.index = rate_level.index.to_period("M")
    drate_p = rate_level.diff()

    # Source: abm/cohort_timing_diagnostic.py main()::pooled_velocity —
    # nested (not importable), replicated verbatim (as ec does).
    q = raw[(raw["period"] >= e3.QT0) & (raw["period"] <= e3.QT1)]
    sub = q.groupby("period").agg(prep=("prepaid_upb", "sum"),
                                  exp=("exposure_upb", "sum"))
    cpr_pool = (sub["prep"] / sub["exp"]).clip(lower=0.0) * 12 * 100.0
    cpr_pool.index = sub.index.to_period("M")
    dvel, n = e3._delta_corr(cpr_pool, drate_p)
    band = 2.0 / np.sqrt(n)
    g1_ok = (abs(dvel - ec.E3_POOLED_FREDDIE[0]) < ec.TOL_E3
             and n == ec.E3_POOLED_FREDDIE[1]
             and abs(band - ec.E3_POOLED_FREDDIE[2]) < ec.TOL_E3)
    gates["G1_e3_pooled_velocity"] = {
        "got": dvel, "want": ec.E3_POOLED_FREDDIE[0], "n": n,
        "zero_band": band, "tol": ec.TOL_E3, "pass": bool(g1_ok),
    }
    print(f"  G1 E3 pooled Freddie velocity: {dvel:+.12f} vs "
          f"{ec.E3_POOLED_FREDDIE[0]:+.12f} (n={n})  "
          f"[{'PASS' if g1_ok else 'FAIL'}]")
    if not g1_ok:
        _fail_out(gates, "G1 E3 pooled realized velocity parity failed")

    g2_cells, g2_ok = {}, True
    for c in e3.COHORT_COUPONS:
        cpr_c = e3._realized_coupon_cpr(raw, c)
        dv, nc = e3._delta_corr(cpr_c, drate_p)
        want = ec.E3_COHORT_LAG0_FREDDIE[f"{c * 100:.1f}"]
        ok = abs(dv - want) < ec.TOL_E3
        g2_cells[f"{c * 100:.1f}"] = {"got": dv, "want": want, "n": nc,
                                      "pass": bool(ok)}
        g2_ok &= ok
    gates["G2_e3_cohort_lag0"] = {"cells": g2_cells, "tol": ec.TOL_E3,
                                  "pass": bool(g2_ok)}
    print(f"  G2 E3 per-cohort lag-0 velocities (6 cells)  "
          f"[{'PASS' if g2_ok else 'FAIL'}]")
    if not g2_ok:
        _fail_out(gates, "G2 E3 per-cohort lag-0 parity failed")

    # ---- G3 — vintage_residual_bound anchor from the Fannie panel ----------
    fan = pd.read_parquet(ec.FANNIE_PANEL)
    fqt = fan[(fan["period"] >= QT_START.to_pydatetime())
              & (fan["period"] < QT_END.to_pydatetime())]
    smm_f = float(fqt["prepaid_upb"].sum()) / float(fqt["exposure_upb"].sum())
    cpr_f = (1.0 - (1.0 - smm_f) ** 12) * 100.0
    g3_ok = abs(cpr_f - ec.VRB_SAMPLED_CPR_PCT) <= ec.TOL_VRB_PP
    gates["G3_vrb_pooled_smm_anchor"] = {
        "got_cpr_pct": cpr_f, "want_cpr_pct": ec.VRB_SAMPLED_CPR_PCT,
        "tol_pp": ec.TOL_VRB_PP, "pass": bool(g3_ok),
    }
    print(f"  G3 vintage_residual_bound sampled CPR: {cpr_f:.12f}% vs "
          f"{ec.VRB_SAMPLED_CPR_PCT:.12f}%  [{'PASS' if g3_ok else 'FAIL'}]")
    if not g3_ok:
        _fail_out(gates, "G3 pooled-SMM anchor parity failed")

    # ---- G4 — floor_uncertainty R2 read (THE ONE FRED FETCH lives here) ----
    df = mdr.build_panel()
    df["stratum"] = [
        build_stratum_id(v, c, fb, lb)
        for v, c, fb, lb in zip(df["vintage"], df["coupon"],
                                df["fico_bucket"], df["ltv_bucket"])
    ]
    sel_r2 = fu._select(df, 201801, 201812, -0.0025, 12)
    cpr_r2, _, n_r2 = mdr.cpr_of(sel_r2)
    cl_r2 = int(sel_r2["stratum"].nunique())
    g4_ok = (abs(cpr_r2 - ec.FU_R2_READ[0]) <= ec.TOL_FU_PP
             and n_r2 == ec.FU_R2_READ[1] and cl_r2 == ec.FU_R2_READ[2])
    gates["G4_floor_uncertainty_R2"] = {
        "got_cpr_pct": cpr_r2, "want_cpr_pct": ec.FU_R2_READ[0],
        "got_n": n_r2, "want_n": ec.FU_R2_READ[1],
        "got_clusters": cl_r2, "want_clusters": ec.FU_R2_READ[2],
        "tol_pp": ec.TOL_FU_PP, "pass": bool(g4_ok),
    }
    print(f"  G4 floor_uncertainty R2: {cpr_r2:.4f}% (n={n_r2}, "
          f"clusters={cl_r2}) vs {ec.FU_R2_READ[0]:.4f}%  "
          f"[{'PASS' if g4_ok else 'FAIL'}]")
    if not g4_ok:
        _fail_out(gates, "G4 floor_uncertainty R2 parity failed")
    print("  G0-G4 ALL PASS — safe to proceed.")

    h_floor = float(lh.cpr_annual_to_monthly_hazard(
        np.array([INVOLUNTARY_CPR_ANNUAL]))[0])
    return gates, df, {"mid": b_mid, "low": b_low, "high": b_high}, h_floor


# ==========================================================================
# Selection — episode_confrontation.py:664-686 replicated verbatim
# (exposure_upb / gap / mean_loan_age / rp only; prepaid_upb is NOT read here)
# ==========================================================================
def build_selection(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame,
                                               pd.DataFrame, pd.DataFrame]:
    win = df[(df["rp"] >= WINDOW[0]) & (df["rp"] <= WINDOW[1])].copy()
    n_months = int(win["rp"].nunique())
    assert n_months == T_MONTHS, (
        f"window carries {n_months} months, expected {T_MONTHS}")

    win["_gx"] = win["gap"] * win["exposure_upb"]
    agg = win.groupby("stratum").agg(gx=("_gx", "sum"),
                                     ex=("exposure_upb", "sum"))
    wmg_pp = (agg["gx"] / agg["ex"]) * 100.0
    first = win.sort_values("rp").groupby("stratum").first()
    age0 = first["mean_loan_age"] - ec._months_since_window_start(first["rp"])
    info = pd.DataFrame({"wmg_pp": wmg_pp, "age0": age0})
    info["bucket"] = info["wmg_pp"].map(gap_bucket)
    win = win.drop(columns=["_gx"]).merge(
        info, left_on="stratum", right_index=True, how="left")

    bucketed = win[win["bucket"].notna()].copy()
    primary = bucketed[bucketed["age0"] >= AGE0_MIN].copy()
    print(f"  strata: {len(info)} total, {int(info['bucket'].isna().sum())} "
          f"excluded (window-mean gap >= 0), "
          f"{int(info['bucket'].notna().sum())} bucketed, "
          f"{int((info['bucket'].notna() & (info['age0'] >= AGE0_MIN)).sum())} "
          f"age-matched (age0 >= {AGE0_MIN})")
    return win, info, bucketed, primary


def endpoints_exposure_only(sel: pd.DataFrame) -> tuple[list, str | None, str | None]:
    """The committed endpoint/support rule (episode_confrontation.py:470-477)
    evaluated on EXPOSURE and STRATUM COUNTS ONLY — prepaid_upb untouched, so
    FG can be resolved before any outcome is read. Cross-checked against
    bucket_block's own endpoints once G5 has run."""
    total_exp = float(sel["exposure_upb"].sum())
    qualified = []
    for b in BUCKET_ORDER:
        rows = sel[sel["bucket"] == b]
        exp = float(rows["exposure_upb"].sum())
        if exp <= 0:
            continue
        if (exp / total_exp) >= SUPPORT_MIN_SHARE and \
                int(rows["stratum"].nunique()) >= SUPPORT_MIN_STRATA:
            qualified.append(b)
    if len(qualified) < 2:
        return qualified, None, None
    return qualified, qualified[0], qualified[-1]


# ==========================================================================
# Composition cells
# ==========================================================================
def cell_ids(rows: pd.DataFrame, axis: tuple) -> pd.Series:
    parts = [rows[a].astype(str) for a in axis]
    out = parts[0]
    for p in parts[1:]:
        out = out + "|" + p
    return out


def cell_ordinals(cell: str, axis: tuple) -> tuple:
    """Ordinal coordinates for the nearest-populated-cell rule (ex ante)."""
    vals = cell.split("|")
    coords = []
    for a, v in zip(axis, vals):
        if a == "vintage":
            coords.append(float(int(v)))
        elif a == "fico_bucket":
            coords.append(float(FICO_ORDER.get(v, len(FICO_ORDER))))
        elif a == "ltv_bucket":
            coords.append(float(LTV_ORDER.get(v, len(LTV_ORDER))))
        else:  # pragma: no cover — axis is fixed above
            coords.append(0.0)
    return tuple(coords)


def cell_distance_matrix(cells: list, axis: tuple) -> np.ndarray:
    coords = np.array([cell_ordinals(c, axis) for c in cells], dtype=np.float64)
    return np.abs(coords[:, None, :] - coords[None, :, :]).sum(axis=2)


# ==========================================================================
# FEASIBILITY GATE FG — exposure and counts only, BEFORE any outcome is read
# ==========================================================================
def _coverage(sel_sh: pd.DataFrame, sel_dp: pd.DataFrame,
              axis: tuple) -> dict:
    sh = sel_sh.copy()
    dp = sel_dp.copy()
    sh["cell"] = cell_ids(sh, axis)
    dp["cell"] = cell_ids(dp, axis)
    ex_sh = sh.groupby("cell")["exposure_upb"].sum()
    ex_dp = dp.groupby("cell")["exposure_upb"].sum()
    st_sh = sh.groupby("cell")["stratum"].nunique()
    st_dp = dp.groupby("cell")["stratum"].nunique()
    common = sorted(set(ex_sh.index) & set(ex_dp.index))
    tot_sh = float(ex_sh.sum())
    tot_dp = float(ex_dp.sum())
    cov_sh = float(ex_sh.reindex(common).sum() / tot_sh) if tot_sh > 0 else 0.0
    cov_dp = float(ex_dp.reindex(common).sum() / tot_dp) if tot_dp > 0 else 0.0
    table = []
    for c in sorted(set(ex_sh.index) | set(ex_dp.index)):
        table.append({
            "cell": c,
            "in_both": c in set(common),
            "exposure_shallow": float(ex_sh.get(c, 0.0)),
            "exposure_deep": float(ex_dp.get(c, 0.0)),
            "shallow_weight": float(ex_sh.get(c, 0.0) / tot_sh) if tot_sh > 0 else 0.0,
            "n_strata_shallow": int(st_sh.get(c, 0)),
            "n_strata_deep": int(st_dp.get(c, 0)),
        })
    return {"axis": AXIS_NAME[axis], "common_cells_n": len(common),
            "cells_shallow_n": int(len(ex_sh)), "cells_deep_n": int(len(ex_dp)),
            "shallow_exposure_covered_share": cov_sh,
            "deep_exposure_covered_share": cov_dp,
            "common_cells": common, "per_cell_support": table}


def feasibility_gate(primary: pd.DataFrame, sh: str, dp: str) -> dict:
    sel_sh = primary[primary["bucket"] == sh]
    sel_dp = primary[primary["bucket"] == dp]
    full = _coverage(sel_sh, sel_dp, AXIS_FULL)
    fg1 = (full["shallow_exposure_covered_share"] >= FG_MIN_COVERAGE
           and full["common_cells_n"] >= FG_MIN_CELLS_FULL)
    if fg1:
        chosen, axis, branch = full, AXIS_FULL, "FG-1"
        fallback = None
    else:
        fallback = _coverage(sel_sh, sel_dp, AXIS_FALLBACK)
        fg2 = (fallback["shallow_exposure_covered_share"] >= FG_MIN_COVERAGE
               and fallback["common_cells_n"] >= FG_MIN_CELLS_FALLBACK)
        if fg2:
            chosen, axis, branch = fallback, AXIS_FALLBACK, "FG-2"
        else:
            chosen, axis, branch = fallback, None, "FG-3"
    out = {
        "branch": branch,
        "standardization_axis": AXIS_NAME[axis] if axis is not None else "none",
        "common_cells_n": chosen["common_cells_n"],
        "shallow_exposure_covered_share": chosen["shallow_exposure_covered_share"],
        "deep_exposure_covered_share": chosen["deep_exposure_covered_share"],
        "endpoints": {"shallow": sh, "deep": dp},
        "thresholds": {
            "min_coverage": FG_MIN_COVERAGE,
            "min_cells_full_axis": FG_MIN_CELLS_FULL,
            "min_cells_fallback_axis": FG_MIN_CELLS_FALLBACK,
            "adaptation_note": (
                "the fallback axis carries at most 3 FICO x 2 LTV = 6 cells, so "
                "a literal >=10 there would make FG-2 unreachable and delete "
                "the branch; the 30% coverage bar is carried across unchanged "
                "and the fallback cell bar is 2. Disclosed, fixed ex ante."),
            "literal_10cell_at_fallback_would_give": (
                "FG-3" if (fallback is not None
                           and fallback["common_cells_n"] < FG_MIN_CELLS_FULL)
                else branch),
        },
        "axis_full": full,
        "axis_fallback": fallback,
        "prepaid_upb_untouched_on_this_selection": True,
        "convention_note": (
            "episode_confrontation.py:102-110 convention: this gate is computed "
            "from exposure_upb sums and cell/stratum counts on the in-window "
            "bucketed selection ONLY. That selection's prepaid_upb is first read "
            "in G5, which runs AFTER this gate, so no threshold here can have "
            "been tuned on an outcome. (G0-G4 do read prepaid_upb — but only on "
            "the committed parity objects: the 2018 off-window leg, the Fannie "
            "panel, and the E3 series — never on this run's endpoint buckets.)"),
    }
    print(f"  FG axis {AXIS_NAME[AXIS_FULL]}: {full['common_cells_n']} common "
          f"cells, shallow coverage {100 * full['shallow_exposure_covered_share']:.2f}%"
          f", deep {100 * full['deep_exposure_covered_share']:.2f}%")
    if fallback is not None:
        print(f"  FG axis {AXIS_NAME[AXIS_FALLBACK]}: "
              f"{fallback['common_cells_n']} common cells, shallow coverage "
              f"{100 * fallback['shallow_exposure_covered_share']:.2f}%")
    print(f"  FG BRANCH {branch}  (standardization axis "
          f"{out['standardization_axis']})  "
          f"[{'Limb A RUNS' if branch != 'FG-3' else 'Limb A NOT_COMPUTABLE'}]")
    return out


# ==========================================================================
# G5 — frozen-artifact reproduction (the first outcome read of this run)
# ==========================================================================
def _cpr(smm: np.ndarray | float) -> np.ndarray | float:
    return 100.0 * (1.0 - (1.0 - smm) ** 12)


def run_g5(primary: pd.DataFrame, betas: dict, h_floor: float,
           sh: str, dp: str, gates: dict) -> dict:
    print("\n" + "=" * 72)
    print("PARITY GATE G5 (NEW) — frozen-artifact reproduction")
    print("=" * 72)
    with open(COMMITTED_ARTIFACT) as f:
        art = json.load(f)
    pa = art["part_a"]["primary_age_matched"]
    # the quoted literals must equal the frozen artifact (ec's own convention)
    assert abs(pa["realized_gradient_pp"] - REF_GRADIENT_PP) < TOL_QUOTE
    assert abs(pa["gradient_bootstrap"]["ci95_pp"][0] - REF_CI95_PP[0]) < TOL_QUOTE
    assert abs(pa["gradient_bootstrap"]["ci95_pp"][1] - REF_CI95_PP[1]) < TOL_QUOTE
    assert abs(pa["implied_gradient_pp"]["mid"] - REF_IMPLIED_MID_PP) < TOL_QUOTE
    assert abs(art["part_a"]["primary_b2_vs_b4_gradient_pp"] - REF_B2_B4_PP) < TOL_QUOTE
    assert abs(art["part_b"]["power_at_named_betas"]["mid"]["power_injected"]
               - REF_POWER_069) < TOL_QUOTE
    assert art["verdict"]["branch"] == REF_VERDICT
    assert pa["endpoints"] == {"shallow": sh, "deep": dp}, (
        f"endpoint drift: committed {pa['endpoints']}, this run "
        f"{{'shallow': {sh!r}, 'deep': {dp!r}}}")

    # ---- recompute with the imported machinery, verbatim -------------------
    blk = bucket_block(primary, betas, h_floor, with_bucket_ci=True)
    assert not blk.get("degenerate")
    assert blk["endpoints"] == {"shallow": sh, "deep": dp}, (
        "bucket_block endpoints disagree with the exposure-only support read")
    g_real = blk["realized_gradient_pp"]
    g_model = blk["implied_gradient_pp"]["mid"]
    b2b4 = (blk["buckets"]["[-2,-1)"]["realized"]["cpr_pct"]
            - blk["buckets"]["<=-3"]["realized"]["cpr_pct"])

    rows_sh = primary[primary["bucket"] == sh]
    rows_dp = primary[primary["bucket"] == dp]
    grads = joint_gradient_bootstrap(rows_sh, rows_dp)   # IMPORTED VERBATIM
    ci = [float(np.percentile(grads, 2.5)), float(np.percentile(grads, 97.5))]
    se = float(np.std(grads, ddof=1))

    # permutation null + injected power — episode_confrontation.py:770-810
    g_strata = primary.groupby("stratum").agg(
        pre=("prepaid_upb", "sum"), ex=("exposure_upb", "sum"),
        bucket=("bucket", "first"))
    pre_arr = g_strata["pre"].to_numpy(dtype=np.float64)
    ex_arr = g_strata["ex"].to_numpy(dtype=np.float64)
    labels = g_strata["bucket"].to_numpy()
    rng = np.random.default_rng(SEED)   # fresh rng(42) for Part B
    perm_grads = np.empty(N_PERM)
    for k in range(N_PERM):
        lab_p = labels[rng.permutation(len(labels))]
        ms, md_ = lab_p == sh, lab_p == dp
        smm_s = pre_arr[ms].sum() / ex_arr[ms].sum()
        smm_d = pre_arr[md_].sum() / ex_arr[md_].sum()
        perm_grads[k] = _cpr(smm_s) - _cpr(smm_d)
    crit95 = float(np.percentile(perm_grads, 95.0))
    p_perm = float((1 + (perm_grads >= g_real).sum()) / (N_PERM + 1))
    power_069 = float((perm_grads + g_model > crit95).mean())
    power_normal = float(norm.cdf(g_model / se - Z_ONE_SIDED_95))

    checks = {
        "raw_gradient": abs(g_real - REF_GRADIENT_PP) < TOL_G5,
        "ci_low": abs(ci[0] - REF_CI95_PP[0]) < TOL_G5,
        "ci_high": abs(ci[1] - REF_CI95_PP[1]) < TOL_G5,
        "implied_mid": abs(g_model - REF_IMPLIED_MID_PP) < TOL_G5,
        "b2_vs_b4": abs(b2b4 - REF_B2_B4_PP) < TOL_G5,
        "power_at_0.069": abs(power_069 - REF_POWER_069) < TOL_G5_POWER,
    }
    gates["G5_frozen_artifact_reproduction"] = {
        "got": {"realized_gradient_pp": g_real, "gradient_ci95_pp": ci,
                "gradient_se_pp": se,
                "implied_gradient_pp_at_0.069": g_model,
                "b2_vs_b4_gradient_pp": b2b4,
                "power_injected_at_0.069": power_069,
                "power_normal_approx": power_normal,
                "permutation_crit95_pp": crit95,
                "permutation_p_one_sided": p_perm},
        "want": {"realized_gradient_pp": REF_GRADIENT_PP,
                 "gradient_ci95_pp": list(REF_CI95_PP),
                 "implied_gradient_pp_at_0.069": REF_IMPLIED_MID_PP,
                 "b2_vs_b4_gradient_pp": REF_B2_B4_PP,
                 "power_injected_at_0.069": REF_POWER_069},
        "tol": {"values": TOL_G5, "power": TOL_G5_POWER},
        "checks": checks,
        "pass": all(checks.values()),
    }
    print(f"  G5 raw gradient {g_real:+.15f} vs {REF_GRADIENT_PP:+.15f}  "
          f"[{'PASS' if checks['raw_gradient'] else 'FAIL'}]")
    print(f"  G5 CI [{ci[0]:+.12f}, {ci[1]:+.12f}]  "
          f"[{'PASS' if checks['ci_low'] and checks['ci_high'] else 'FAIL'}]")
    print(f"  G5 implied(mid) {g_model:+.15f}  "
          f"[{'PASS' if checks['implied_mid'] else 'FAIL'}]")
    print(f"  G5 B2-vs-B4 {b2b4:+.15f}  "
          f"[{'PASS' if checks['b2_vs_b4'] else 'FAIL'}]")
    print(f"  G5 power@0.069 {power_069:.4f} vs {REF_POWER_069:.4f}  "
          f"[{'PASS' if checks['power_at_0.069'] else 'FAIL'}]")
    if not gates["G5_frozen_artifact_reproduction"]["pass"]:
        _fail_out(gates, "G5 frozen-artifact reproduction failed — ENVIRONMENT "
                         "ALARM (power is a fixed-seed mean over 200 "
                         "permutations; exact reproduction is expected)")
    print("  G5 PASS — the committed episode numbers reproduce here.")
    return {"block": blk, "gradient_draws": grads, "ci": ci, "se": se,
            "g_real": g_real, "g_model": g_model, "b2b4": b2b4,
            "power_069": power_069, "crit95": crit95, "p_perm": p_perm}


# ==========================================================================
# LIMB A — composition-standardized gradient
# floor_uncertainty.py:478-521 template (weights / observed / ratio-imputed /
# flat fallback / imputed-weight reporting), transposed to composition cells.
# ==========================================================================
def _cell_arrays(rows: pd.DataFrame, cells: list) -> tuple[np.ndarray, np.ndarray]:
    idx = {c: i for i, c in enumerate(cells)}
    pre = np.zeros(len(cells))
    ex = np.zeros(len(cells))
    g = rows.groupby("cell")[["prepaid_upb", "exposure_upb"]].sum()
    for c, r in g.iterrows():
        pre[idx[c]] = float(r["prepaid_upb"])
        ex[idx[c]] = float(r["exposure_upb"])
    return pre, ex


def _nearest_common(c: int, common: np.ndarray, dist: np.ndarray,
                    ex_d: np.ndarray) -> int:
    """Nearest populated common cell — floor_uncertainty's 'oldest populated
    bucket' reference, generalized: L1 ordinal distance, ties to larger deep
    exposure, then to the lower cell index. Deterministic, no randomness."""
    order = np.lexsort((common, -ex_d[common], dist[c, common]))
    return int(common[order[0]])


def _standardize(pre_s: np.ndarray, ex_s: np.ndarray,
                 pre_d: np.ndarray, ex_d: np.ndarray,
                 dist: np.ndarray) -> tuple[float, float, float, float, list]:
    """Returns (G_std, shallow_std_cpr, deep_std_cpr, imputed_weight_share,
    per-cell rows). Weights are the SHALLOW bucket's cell exposure shares."""
    tot_s = ex_s.sum()
    if tot_s <= 0:
        return np.nan, np.nan, np.nan, np.nan, []
    w = ex_s / tot_s
    with np.errstate(divide="ignore", invalid="ignore"):
        smm_s = np.where(ex_s > 0, pre_s / np.where(ex_s > 0, ex_s, 1.0), np.nan)
        smm_d = np.where(ex_d > 0, pre_d / np.where(ex_d > 0, ex_d, 1.0), np.nan)
    r_s = _cpr(smm_s)
    r_d = _cpr(smm_d)
    common = np.flatnonzero((ex_s > 0) & (ex_d > 0))
    if common.size == 0:
        return np.nan, np.nan, np.nan, np.nan, []

    deep_std, shal_std, imputed_w = 0.0, 0.0, 0.0
    table = []
    for c in range(len(w)):
        if w[c] == 0.0:
            table.append({"cell_index": c, "weight": 0.0, "used_pct": None,
                          "source": "no_shallow_weight (contributes nothing)"})
            continue
        if ex_d[c] > 0:
            used, source, imp = float(r_d[c]), "observed_deep", False
        else:
            ref = _nearest_common(c, common, dist, ex_d)
            if r_s[ref] is not None and np.isfinite(r_s[ref]) and r_s[ref] > 0:
                used = float(r_d[ref] * (r_s[c] / r_s[ref]))
                source = (f"IMPUTED: deep read in nearest common cell #{ref} "
                          f"({r_d[ref]:.3f}%) x shallow ratio {r_s[c]:.3f}/"
                          f"{r_s[ref]:.3f}")
                imp = True
            else:
                used = float(r_d[ref])
                source = (f"IMPUTED FLAT FALLBACK: shallow CPR of nearest "
                          f"common cell #{ref} not computable/zero — deep read "
                          f"used unscaled")
                imp = True
            imputed_w += float(w[c])
        deep_std += float(w[c]) * used
        shal_std += float(w[c]) * float(r_s[c])
        table.append({"cell_index": c, "weight": float(w[c]),
                      "shallow_cpr_pct": float(r_s[c]),
                      "deep_cpr_pct": float(r_d[c]) if ex_d[c] > 0 else None,
                      "used_pct": used, "source": source, "imputed": imp,
                      "exposure_shallow": float(ex_s[c]),
                      "exposure_deep": float(ex_d[c])})
    return shal_std - deep_std, shal_std, deep_std, imputed_w, table


def limb_a(primary: pd.DataFrame, sh: str, dp: str, axis: tuple,
           ec_draws: np.ndarray) -> dict:
    print("\n" + "=" * 72)
    print(f"LIMB A (PRIMARY) — composition-standardized gradient "
          f"[{AXIS_NAME[axis]}]")
    print("=" * 72)
    shal = primary[primary["bucket"] == sh].copy()
    deep = primary[primary["bucket"] == dp].copy()
    shal["cell"] = cell_ids(shal, axis)
    deep["cell"] = cell_ids(deep, axis)
    cells = sorted(set(shal["cell"]) | set(deep["cell"]))
    dist = cell_distance_matrix(cells, axis)

    pre_s, ex_s = _cell_arrays(shal, cells)
    pre_d, ex_d = _cell_arrays(deep, cells)
    g_std, shal_std, deep_std, imp_w, table = _standardize(
        pre_s, ex_s, pre_d, ex_d, dist)
    for row in table:
        if "cell_index" in row and row["weight"] > 0:
            row["cell"] = cells[row["cell_index"]]
    table = [r for r in table if r.get("weight", 0.0) > 0.0]

    smm_s_pool = float(shal["prepaid_upb"].sum()) / float(shal["exposure_upb"].sum())
    smm_d_pool = float(deep["prepaid_upb"].sum()) / float(deep["exposure_upb"].sum())
    cpr_s_pool, cpr_d_pool = float(_cpr(smm_s_pool)), float(_cpr(smm_d_pool))

    # ---- bootstrap: joint_gradient_bootstrap's index stream, reproduced -----
    gs = shal.groupby("stratum", sort=True).agg(
        pre=("prepaid_upb", "sum"), ex=("exposure_upb", "sum"),
        cell=("cell", "first"))
    gd = deep.groupby("stratum", sort=True).agg(
        pre=("prepaid_upb", "sum"), ex=("exposure_upb", "sum"),
        cell=("cell", "first"))
    code = {c: i for i, c in enumerate(cells)}
    cs = gs["cell"].map(code).to_numpy(dtype=np.int64)
    cd = gd["cell"].map(code).to_numpy(dtype=np.int64)
    ps, es = gs["pre"].to_numpy(np.float64), gs["ex"].to_numpy(np.float64)
    pdp, ed = gd["pre"].to_numpy(np.float64), gd["ex"].to_numpy(np.float64)

    # cluster_sums parity: identical grouping, identical order.
    cps, ces = cluster_sums(shal)
    cpd, ced = cluster_sums(deep)
    assert np.max(np.abs(cps - ps)) < 1e-9 and np.max(np.abs(ces - es)) < 1e-9
    assert np.max(np.abs(cpd - pdp)) < 1e-9 and np.max(np.abs(ced - ed)) < 1e-9

    rng = np.random.default_rng(SEED)
    idx_s = rng.integers(0, len(ps), size=(N_BOOT, len(ps)))
    idx_d = rng.integers(0, len(pdp), size=(N_BOOT, len(pdp)))
    # the imported function's own draws, recomputed from THIS index stream
    raw_draws = (_cpr(ps[idx_s].sum(axis=1) / es[idx_s].sum(axis=1))
                 - _cpr(pdp[idx_d].sum(axis=1) / ed[idx_d].sum(axis=1)))
    stream_err = float(np.max(np.abs(raw_draws - ec_draws)))
    assert stream_err < 1e-12, (
        f"bootstrap stream diverged from joint_gradient_bootstrap "
        f"(max |diff| {stream_err:g}) — the standardized CI would not be "
        f"comparable to the committed one")

    C = len(cells)
    draws = np.full(N_BOOT, np.nan)
    imp_draws = np.full(N_BOOT, np.nan)
    for k in range(N_BOOT):
        a, b = idx_s[k], idx_d[k]
        bp_s = np.bincount(cs[a], weights=ps[a], minlength=C)
        be_s = np.bincount(cs[a], weights=es[a], minlength=C)
        bp_d = np.bincount(cd[b], weights=pdp[b], minlength=C)
        be_d = np.bincount(cd[b], weights=ed[b], minlength=C)
        g_k, _, _, iw_k, _ = _standardize(bp_s, be_s, bp_d, be_d, dist)
        draws[k] = g_k
        imp_draws[k] = iw_k
    ok = np.isfinite(draws)
    n_degen = int((~ok).sum())
    ci = [float(np.percentile(draws[ok], 2.5)),
          float(np.percentile(draws[ok], 97.5))] if ok.any() else [None, None]
    se = float(np.std(draws[ok], ddof=1)) if ok.sum() > 1 else None

    def _f(v: float | None, spec: str = "+.4f") -> str:
        return "n/a" if v is None or not np.isfinite(v) else format(v, spec)

    print(f"  cells: {len(cells)} total, "
          f"{int(((ex_s > 0) & (ex_d > 0)).sum())} common; imputed weight "
          f"share {_f(imp_w, '.4f')} ({_f(100 * imp_w, '.2f')}%)")
    print(f"  shallow standardized CPR {_f(shal_std, '.4f')}% (pooled "
          f"{cpr_s_pool:.4f}%)  |  deep standardized CPR "
          f"{_f(deep_std, '.4f')}% (pooled {cpr_d_pool:.4f}%)")
    print(f"  STANDARDIZED GRADIENT {_f(g_std)}pp, 95% CI "
          f"[{_f(ci[0])}, {_f(ci[1])}], SE {_f(se, '.4f')}pp  "
          f"(raw committed {REF_GRADIENT_PP:+.4f}pp)  "
          f"[{'COMPUTED' if np.isfinite(g_std) else 'DEGENERATE'}]")
    if n_degen:
        print(f"  NOTE: {n_degen} bootstrap replicate(s) had no common cell "
              f"and are excluded from the CI (disclosed).")

    def _n(v):
        """No NaN in the artifact: a non-computable read is null, not NaN."""
        return None if v is None or not np.isfinite(v) else float(v)

    return {
        "status": "OK" if np.isfinite(g_std) else "DEGENERATE",
        "standardization_axis": AXIS_NAME[axis],
        "standardized_gradient_pp": _n(g_std),
        "ci95_pp": ci,
        "se_pp": se,
        "imputed_weight_share": _n(imp_w),
        "per_cell_table": table,
        "shallow_standardized_cpr_pct": _n(shal_std),
        "deep_standardized_cpr_pct": _n(deep_std),
        "shallow_pooled_cpr_pct": cpr_s_pool,
        "deep_pooled_cpr_pct": cpr_d_pool,
        "gradient_vs_pooled_shallow_pp": float(cpr_s_pool - deep_std),
        "raw_gradient_pp": cpr_s_pool - cpr_d_pool,
        "n_cells": len(cells),
        "n_common_cells": int(((ex_s > 0) & (ex_d > 0)).sum()),
        "bootstrap": {
            "n_reps": N_BOOT, "seed": SEED,
            "convention": "joint_gradient_bootstrap's resampling convention — "
                          "ONE default_rng(42) stream, shallow cluster indices "
                          "then deep per replicate block; weights resampled "
                          "with the data; imputation re-applied per replicate",
            "stream_parity_vs_joint_gradient_bootstrap_max_abs": stream_err,
            "mean_imputed_weight_share": _n(np.nanmean(imp_draws))
            if ok.any() else None,
            "n_degenerate_reps": n_degen,
            "draws_min_pp": _n(np.nanmin(draws)) if ok.any() else None,
            "draws_max_pp": _n(np.nanmax(draws)) if ok.any() else None,
        },
    }


# ==========================================================================
# LIMB B — exact within/between decomposition (identity; never degenerates)
# ==========================================================================
def _between_within(shal: pd.DataFrame, deep: pd.DataFrame,
                    axis: tuple) -> dict:
    s = shal.copy()
    d = deep.copy()
    s["cell"] = cell_ids(s, axis)
    d["cell"] = cell_ids(d, axis)
    cells = sorted(set(s["cell"]) | set(d["cell"]))
    pre_s, ex_s = _cell_arrays(s, cells)
    pre_d, ex_d = _cell_arrays(d, cells)
    tot_s, tot_d = ex_s.sum(), ex_d.sum()
    w_s = ex_s / tot_s
    w_d = ex_d / tot_d
    with np.errstate(divide="ignore", invalid="ignore"):
        smm_s = np.where(ex_s > 0, pre_s / np.where(ex_s > 0, ex_s, 1.0), 0.0)
        smm_d = np.where(ex_d > 0, pre_d / np.where(ex_d > 0, ex_d, 1.0), 0.0)
    # placeholder for one-sided cells: the OTHER bucket's cell SMM, so the
    # within contribution there is exactly zero and the whole difference in
    # that cell loads on BETWEEN (a cell a bucket does not occupy is
    # composition, not behaviour).
    smm_d_eff = np.where(ex_d > 0, smm_d, smm_s)
    smm_s_eff = np.where(ex_s > 0, smm_s, smm_d)

    smm_s_pool = float(pre_s.sum() / tot_s)
    smm_d_pool = float(pre_d.sum() / tot_d)
    smm_d_star = float((w_s * smm_d_eff).sum())     # deep under shallow mix

    total = float(_cpr(smm_s_pool) - _cpr(smm_d_pool))
    between = float(_cpr(smm_d_star) - _cpr(smm_d_pool))
    within = float(_cpr(smm_s_pool) - _cpr(smm_d_star))
    residual = total - (between + within)

    # symmetric (average-weight, Oaxaca two-fold) split, in SMM space, then
    # rescaled to pp — reported as a robustness read, never primary.
    w_bar = 0.5 * (w_s + w_d)
    s_bar = 0.5 * (smm_s_eff + smm_d_eff)
    b_smm = float(((w_s - w_d) * s_bar).sum())
    w_smm = float((w_bar * (smm_s_eff - smm_d_eff)).sum())
    tot_smm = smm_s_pool - smm_d_pool
    sym_res = tot_smm - (b_smm + w_smm)
    scale = (total / tot_smm) if tot_smm != 0 else 0.0

    unmatched_s = float(ex_s[ex_d == 0].sum() / tot_s)
    unmatched_d = float(ex_d[ex_s == 0].sum() / tot_d)
    return {
        "axis": AXIS_NAME.get(axis, "|".join(axis)),
        "total_pp": total,
        "between_composition_pp": between,
        "within_composition_pp": within,
        "identity_residual": residual,
        "smm_shallow_pooled": smm_s_pool,
        "smm_deep_pooled": smm_d_pool,
        "smm_deep_standardized_to_shallow_mix": smm_d_star,
        "n_cells": len(cells),
        "unmatched_exposure_share_shallow": unmatched_s,
        "unmatched_exposure_share_deep": unmatched_d,
        "symmetric_split": {
            "between_pp": b_smm * scale, "within_pp": w_smm * scale,
            "identity_residual_smm": sym_res,
            "note": "average-weight (Oaxaca two-fold) split computed in SMM "
                    "space — exact there — and rescaled to pp by the CPR/SMM "
                    "ratio of the total; the telescoping split above is the "
                    "one that is exact in pp",
        },
    }


def limb_b(primary: pd.DataFrame, sh: str, dp: str) -> dict:
    print("\n" + "=" * 72)
    print("LIMB B — exact within/between decomposition of the committed "
          f"{REF_GRADIENT_PP:+.3f}pp")
    print("=" * 72)
    shal = primary[primary["bucket"] == sh]
    deep = primary[primary["bucket"] == dp]
    full = _between_within(shal, deep, AXIS_FULL)
    assert abs(full["total_pp"] - REF_GRADIENT_PP) < TOL_G5, (
        f"Limb B total {full['total_pp']:.15f} is not the committed gradient "
        f"{REF_GRADIENT_PP:.15f} — the decomposition is not of the committed "
        f"object")
    assert abs(full["identity_residual"]) < 1e-12, (
        f"identity residual {full['identity_residual']:g} is not zero — the "
        f"decomposition is not an identity as constructed")

    by_axis = {
        "full_cell": {k: full[k] for k in
                      ("between_composition_pp", "within_composition_pp",
                       "n_cells")},
        "vintage_only": {k: v for k, v in
                         _between_within(shal, deep, ("vintage",)).items()
                         if k in ("between_composition_pp",
                                  "within_composition_pp", "n_cells")},
        "fico_ltv_only": {k: v for k, v in
                          _between_within(shal, deep, AXIS_FALLBACK).items()
                          if k in ("between_composition_pp",
                                   "within_composition_pp", "n_cells")},
    }
    print(f"  total {full['total_pp']:+.6f}pp = between "
          f"{full['between_composition_pp']:+.6f}pp + within "
          f"{full['within_composition_pp']:+.6f}pp   (residual "
          f"{full['identity_residual']:.3e})")
    print(f"  between by axis: vintage-only "
          f"{by_axis['vintage_only']['between_composition_pp']:+.4f}pp, "
          f"FICOxLTV-only "
          f"{by_axis['fico_ltv_only']['between_composition_pp']:+.4f}pp, "
          f"full cell {full['between_composition_pp']:+.4f}pp")
    print(f"  unmatched exposure: shallow "
          f"{100 * full['unmatched_exposure_share_shallow']:.2f}%, deep "
          f"{100 * full['unmatched_exposure_share_deep']:.2f}%")
    out = dict(full)
    out["between_by_axis"] = by_axis
    return out


# ==========================================================================
# LIMB C — stratum-FE within estimator (SECONDARY; reported, never primary)
# ==========================================================================
def _within_wls(rows: pd.DataFrame, weighted: bool) -> dict:
    y = (rows["prepaid_upb"].to_numpy(np.float64)
         / rows["exposure_upb"].to_numpy(np.float64))
    x = rows["gap"].to_numpy(np.float64)
    w = (rows["exposure_upb"].to_numpy(np.float64) if weighted
         else np.ones(len(rows)))
    codes, groups = pd.factorize(rows["stratum"].to_numpy())
    G = len(groups)
    sw = np.bincount(codes, weights=w, minlength=G)
    xm = np.bincount(codes, weights=w * x, minlength=G) / sw
    ym = np.bincount(codes, weights=w * y, minlength=G) / sw
    xt = x - xm[codes]
    yt = y - ym[codes]
    sxx = float((w * xt * xt).sum())
    if sxx <= 0:
        return {"computable": False, "reason": "no within-stratum variation"}
    beta = float((w * xt * yt).sum() / sxx)
    u = yt - beta * xt
    # cluster-robust variance, stratum clusters, usual small-sample correction
    meat = 0.0
    for gsum in np.bincount(codes, weights=w * xt * u, minlength=G):
        meat += float(gsum) ** 2
    n, k = len(rows), 1
    corr = (G / (G - 1.0)) * ((n - 1.0) / (n - k)) if G > 1 else 1.0
    var = corr * meat / (sxx ** 2)
    sst = float((w * yt * yt).sum())
    ssr = float((w * u * u).sum())
    smm_bar = float(rows["prepaid_upb"].sum() / rows["exposure_upb"].sum())
    # dCPR/dSMM at the weighted-mean SMM (the linearization is disclosed)
    dcpr = 12.0 * 100.0 * (1.0 - smm_bar) ** 11
    coef_per_100bp = beta * 0.01     # dSMM per +1pp of gap
    return {
        "computable": True,
        "coef_per_100bp": coef_per_100bp,
        "se": float(np.sqrt(var)) * 0.01,
        "t_stat": beta / float(np.sqrt(var)) if var > 0 else None,
        "n_strata": int(G),
        "n_obs": int(n),
        "r2_within": 1.0 - ssr / sst if sst > 0 else None,
        "implied_cpr_per_point_pp": coef_per_100bp * dcpr,
        "mean_smm": smm_bar,
    }


def limb_c(primary: pd.DataFrame, bucketed: pd.DataFrame,
           dgap_pp: float) -> dict:
    print("\n" + "=" * 72)
    print("LIMB C (SECONDARY — reported, never primary) — stratum-FE within")
    print("=" * 72)
    main_fit = _within_wls(primary, weighted=True)
    variants = {
        "unweighted_primary": _within_wls(primary, weighted=False),
        "exposure_weighted_full_sample": _within_wls(bucketed, weighted=True),
    }
    # how much of the within-transformed regressor is pure calendar time
    codes, groups = pd.factorize(primary["stratum"].to_numpy())
    w = primary["exposure_upb"].to_numpy(np.float64)
    x = primary["gap"].to_numpy(np.float64)
    sw = np.bincount(codes, weights=w, minlength=len(groups))
    xm = np.bincount(codes, weights=w * x, minlength=len(groups)) / sw
    xt = x - xm[codes]
    mcodes, mgroups = pd.factorize(primary["rp"].to_numpy())
    msw = np.bincount(mcodes, weights=w, minlength=len(mgroups))
    mxm = np.bincount(mcodes, weights=w * xt, minlength=len(mgroups)) / msw
    resid = xt - mxm[mcodes]
    denom = float((w * xt * xt).sum())
    month_share = 1.0 - float((w * resid * resid).sum()) / denom if denom > 0 else None

    if main_fit.get("computable"):
        eq = main_fit["implied_cpr_per_point_pp"] * dgap_pp
        main_fit["equivalent_endpoint_gradient_pp"] = eq
        print(f"  coef {main_fit['coef_per_100bp']:+.6e} SMM per +1pp of gap "
              f"(SE {main_fit['se']:.3e}), n={main_fit['n_obs']}, "
              f"strata={main_fit['n_strata']}, R2_within="
              f"{main_fit['r2_within']:.4f}")
        print(f"  implied {main_fit['implied_cpr_per_point_pp']:+.4f} CPR "
              f"points per point of gap -> {eq:+.4f}pp over the endpoints' "
              f"{dgap_pp:+.3f}pp gap difference")
    print(f"  calendar-time share of within-regressor variance: "
          f"{100 * month_share:.2f}%")
    main_fit["month_variance_share_of_within_regressor"] = month_share
    main_fit["variants"] = variants
    main_fit["confounds_note"] = (
        "Within a stratum the coupon is constant, so gap_it = coupon_i - r_t "
        "is a deterministic function of calendar time; the within regressor is "
        "identified ONLY off the unbalanced panel (which months a stratum is "
        "observed in, and with what exposure weight). Seasoning and "
        "seasonality therefore load onto this coefficient in full, and the "
        "two-way (stratum + month) FE version is EXACTLY unidentified and is "
        "not run. Reported for the practitioners who will ask for it; a "
        "near-zero within-stratum response is consistent with — and "
        "strengthens — this paper's own monthly-timing nulls. NEVER PRIMARY."
    )
    return main_fit


# ==========================================================================
def main() -> None:
    t0 = time.perf_counter()

    gates, df, betas, h_floor = run_committed_gates_g0_g4()

    print("\n" + "=" * 72)
    print(f"SELECTION + FEASIBILITY GATE (exposure and counts only; "
          f"{WINDOW[0]}..{WINDOW[1]}, {T_MONTHS} months)")
    print("=" * 72)
    _win, info, bucketed, primary = build_selection(df)
    qualified, sh, dp = endpoints_exposure_only(primary)
    if sh is None:
        _fail_out(gates, "fewer than two qualified buckets in the primary "
                         "age-matched selection under the committed support "
                         "rule — the committed run's own DEGENERATE branch")
    print(f"  endpoints (support rule, exposure/counts only): {sh} vs {dp} "
          f"(qualified {qualified})")
    fg = feasibility_gate(primary, sh, dp)

    g5 = run_g5(primary, betas, h_floor, sh, dp, gates)

    blk = g5["block"]
    dgap_pp = blk["endpoint_mean_gap_delta_pp"]

    # ---- limbs -------------------------------------------------------------
    if fg["branch"] == "FG-3":
        la = {"status": "NOT_COMPUTABLE",
              "standardization_axis": "none",
              "standardized_gradient_pp": None, "ci95_pp": [None, None],
              "se_pp": None, "imputed_weight_share": None,
              "per_cell_table": [],
              "reason": (f"FG-3: {fg['common_cells_n']} common composition "
                         f"cells covering "
                         f"{100 * fg['shallow_exposure_covered_share']:.2f}% of "
                         f"shallow-bucket exposure — below the pre-committed "
                         f"{100 * FG_MIN_COVERAGE:.0f}% bar on both axes")}
        print("\n" + "=" * 72)
        print("LIMB A — NOT_COMPUTABLE (FG-3). This is a LANDING, not a "
              "failure; Limbs B and C still run.")
        print("=" * 72)
    else:
        axis = AXIS_FULL if fg["branch"] == "FG-1" else AXIS_FALLBACK
        la = limb_a(primary, sh, dp, axis, g5["gradient_draws"])

    lb = limb_b(primary, sh, dp)
    lc = limb_c(primary, bucketed, dgap_pp)

    # ---- verdict -----------------------------------------------------------
    g_model = g5["g_model"]
    lo, hi = (la["ci95_pp"] if la["status"] == "OK" else (None, None))
    g_std = la["standardized_gradient_pp"]
    sub = None
    computed = (la["status"] == "OK" and g_std is not None
                and lo is not None and hi is not None)
    if fg["branch"] == "FG-3":
        branch = "c"
    elif not computed:
        branch, sub = "d", "limb_a_degenerate_despite_passing_FG"
    elif hi < 0.0:
        branch, sub = "d", "limb_a_ci_wholly_negative"
    elif lo <= g_model <= hi or g_std < HALF_RAW_PP:
        branch = "b"
    elif lo > g_model:
        branch = "a"
    else:
        branch, sub = "d", "unclassified_by_the_ex_ante_branch_map"

    sentence = BRANCH_SENTENCES[branch].format(
        AX=("vintage x FICO x LTV" if la.get("standardization_axis")
            == "vintage_fico_ltv" else "FICO x LTV"),
        G=g_std if g_std is not None else float("nan"),
        LO=lo if lo is not None else float("nan"),
        HI=hi if hi is not None else float("nan"),
        IW=100 * la["imputed_weight_share"] if la.get("imputed_weight_share")
        is not None else float("nan"),
        M=g_model, RAW=REF_GRADIENT_PP,
        COV=100 * fg["shallow_exposure_covered_share"],
        NC=fg["common_cells_n"],
        WITHIN=lb["within_composition_pp"],
        BETWEEN=lb["between_composition_pp"],
        TOTAL=lb["total_pp"],
        SUB=sub or "",
    )
    print("\n" + "=" * 72)
    print(f"VERDICT: {sentence}")

    # ---- freeze ------------------------------------------------------------
    runtime_s = round(time.perf_counter() - t0, 1)
    payload = {
        "mode": "episode_confrontation_within",
        "status": "STOP" if branch == "d" else "OK",
        "spec": {
            "purpose": "round-28 WP-I1: the composition-controlled version of "
                       "the tex-292 episode gradient three referees ask for; "
                       "design frozen in the module docstring before the run "
                       "(specs/SPEC_round28_D_F1_I1_I3_J2_S8.md SPEC I1)",
            "structural_finding": "the stratum id CONTAINS coupon and the "
                                  "bucket is a function of the stratum's "
                                  "window-mean gap, so every stratum lives in "
                                  "exactly one bucket: a literal "
                                  "within-stratum gradient is NOT COMPUTABLE, "
                                  "EVER. What is computable is composition "
                                  "control on the non-coupon axes.",
            "composition_cell": "(vintage, fico_bucket, ltv_bucket) — the "
                                "stratum id with the coupon dimension removed",
            "limb_a": "direct standardization, floor_uncertainty.py:478-521 "
                      "template (shallow-bucket weights, observed / "
                      "ratio-imputed / flat-fallback reads, imputed weight "
                      "share reported); joint stratum-cluster bootstrap, "
                      f"{N_BOOT} reps, seed {SEED}",
            "limb_b": "exact within/between decomposition of the committed "
                      "gradient; telescoping counterfactual CPR(SMM_deep under "
                      "shallow mix); identity_residual zero by construction "
                      "and asserted",
            "limb_c": "stratum-FE within estimator on monthly SMM vs monthly "
                      "gap, exposure-weighted, stratum-clustered SE; SECONDARY "
                      "— reported, never primary",
            "feasibility_gate": f"FG-1 coverage >= {FG_MIN_COVERAGE:.0%} and "
                                f">= {FG_MIN_CELLS_FULL} common cells on "
                                f"(vintage, fico, ltv); FG-2 falls back to "
                                f"(fico, ltv); FG-3 NOT_COMPUTABLE (a landing, "
                                f"not a failure). Evaluated from exposure_upb "
                                f"and cell counts ONLY, before any outcome is "
                                f"read.",
            "held_at_production": f"window {WINDOW[0]}..{WINDOW[1]} "
                                  f"({T_MONTHS} months, asserted); coupon>0 & "
                                  f"exposure_upb>0; gap on the calendar-month "
                                  f"FRED ME-mean; buckets "
                                  f"{'/'.join(BUCKET_ORDER)} with gap>=0 "
                                  f"excluded; age0 >= {AGE0_MIN}; endpoint "
                                  f"support >= {SUPPORT_MIN_SHARE:.0%} "
                                  f"exposure AND >= {SUPPORT_MIN_STRATA} "
                                  f"strata; pooled dollar SMM -> CPR = "
                                  f"1-(1-SMM)^12; analytic model counterpart, "
                                  f"covariate multiplier 1; seed {SEED}",
            "gates": "G0-G4 are episode_confrontation.py's own gates, "
                     "replicated line-for-line from its main() (the committed "
                     "main() is never called: it would rewrite the frozen "
                     "artifact); G5 is this run's new frozen-artifact "
                     "reproduction gate",
            "must_not_change": "episode_confrontation.py and its committed "
                               "artifact; matched_depth_reconciliation."
                               "build_panel; floor_uncertainty."
                               "cluster_bootstrap_cpr; the bucket rule, age "
                               "cut and support rule; +4.20, [+3.59,+4.66], "
                               "+0.94, 0.68, p = 0.005 at tex 292 and "
                               "liveness_gates.py:4396-4406; config.py; any "
                               ".tex file",
        },
        "parity_gates": gates,
        "parity_gates_all_pass": all(
            g.get("pass", True) for g in gates.values() if isinstance(g, dict)),
        "selection": {
            "n_strata_total": int(len(info)),
            "n_strata_excluded_gap_ge0": int(info["bucket"].isna().sum()),
            "n_strata_bucketed": int(info["bucket"].notna().sum()),
            "n_strata_primary": int(primary["stratum"].nunique()),
            "n_rows_primary": int(len(primary)),
            "n_rows_full": int(len(bucketed)),
            "endpoints": {"shallow": sh, "deep": dp},
            "qualified_buckets": qualified,
            "endpoint_mean_gap_delta_pp": dgap_pp,
        },
        "feasibility_gate": fg,
        "limb_a": la,
        "limb_b": lb,
        "limb_c": lc,
        "committed_reference": {
            "realized_gradient_pp": REF_GRADIENT_PP,
            "gradient_ci95_pp": list(REF_CI95_PP),
            "implied_gradient_pp_at_0.069": REF_IMPLIED_MID_PP,
            "power_injected_at_0.069": REF_POWER_069,
            "b2_vs_b4_gradient_pp": REF_B2_B4_PP,
            "verdict_branch": REF_VERDICT,
            "source": str(COMMITTED_ARTIFACT.name),
            "reproduced_here": gates["G5_frozen_artifact_reproduction"]["got"],
        },
        "verdict": {
            "branch": branch,
            "subcase": sub,
            "sentence": sentence,
            "inputs": {
                "standardized_gradient_pp": g_std,
                "standardized_ci95_pp": [lo, hi],
                "model_implied_gradient_pp_at_0.069": g_model,
                "raw_committed_gradient_pp": REF_GRADIENT_PP,
                "half_raw_bar_pp": HALF_RAW_PP,
                "fg_branch": fg["branch"],
            },
            "landing": {
                "a": "tex 292 rewritten to the tested version; UPWARD entry in "
                     "tab:assembly (tex 313-334) with Status 'directional; not "
                     "a marginal re-estimate'. [posture] Eugene signs.",
                "b": "tex 292's 'composition-confounded' upgraded from "
                     "assertion to result; +4.20 stays as the raw number; "
                     "liveness_gates.py:4396-4406 EXTENDED, not replaced; no "
                     "assembly row.",
                "c": "tex 292 gains the negative result with the coverage "
                     "number; no assembly row; no gate change beyond the "
                     "artifact reference.",
                "d": "STOP — report, diagnose, land nothing.",
            }[branch],
        },
        "runtime_s": runtime_s,
    }
    _write(payload)
    print(f"\nResults -> {RESULTS_JSON}")
    print(f"Runtime: {runtime_s}s")
    if branch == "d":
        raise SystemExit(
            "BRANCH (d) — STOP. The ex-ante map lands NOTHING here: report the "
            f"numbers and diagnose. Diagnostics in {RESULTS_JSON}.")


if __name__ == "__main__":
    main()
