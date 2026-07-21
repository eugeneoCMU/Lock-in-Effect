#!/usr/bin/env python3
"""
episode_confrontation.py — cumulative cross-cohort confrontation of the
imported elasticity against realized QT-era cohort speeds, plus the power
analysis that every prior mechanism-sensitive null lacked (round 21, LG-4).

PRE-COMMITTED SPEC (fixed in this header BEFORE any run; ex-ante convention of
oos_identification.py / floor_form_offwindow.py / floor_uncertainty.py /
matched_depth_reconciliation.py).

WHY THIS RUN EXISTS (LG-4 PARTIAL)
  Every mechanism-sensitive test on realized QT-era data so far has returned a
  null — but all of them (cohort_timing_diagnostic, rate_timing_scan, the
  seasonal-floor timing tests) were run in monthly DIFFERENCES, where calendar
  seasonality dominates the variance. Two things were never done:
    (a) a CUMULATIVE cross-cohort confrontation — the model's implied
        cumulative prepayment divergence across rate-gap depth over the whole
        window, against realized cumulative cohort speeds, with seasoning
        controls (cumulation integrates out monthly seasonality); and
    (b) a POWER analysis — whether beta_1 = 0.069 (the imported elasticity;
        exact |rothstein_beta1(0.065)| = 0.0686) is even detectable against
        the realized series' noise.
  The abstract's verb for the marginal currently reads "Re-anchoring ...
  puts"; the ex-ante branches below decide whether it can strengthen, must
  stay, or must weaken. No discretion after the run.

DATA-PATH DECISION FOR THE MODEL-IMPLIED COUNTERPART (fixed ex ante, after
schema inspection and before any outcome was computed)
  - hazard/data/microsim_results.parquet and every committed
    hazard/data/floor_sweep/microsim_floor*.parquet are 42-row MONTHLY
    AGGREGATES (period x {market_rate_pct, hazard_cpr_pct, prepay_upb,
    exposure, ...}); they carry NO loan or cohort dimension. Verified by
    schema read before this spec was frozen.
  - The committed E3 run (abm/cohort_timing_diagnostic.py) stored NO
    per-cohort simulated CPR series for Path B: its "predicted cohorts" are
    ABM-surface paths (a different design, Path A/ABM), and its artifact
    carries summary statistics only.
  => The model-implied counterpart is therefore derived ANALYTICALLY from the
     production hazard, eq. (2) of the manuscript, with NO engine run:
        h_model = max( h_floor , h0_PSA(age) * exp((-beta_1) * 100 * gap) )
     where h_floor = cpr_annual_to_monthly_hazard(INVOLUNTARY_CPR_ANNUAL=4%),
     h0_PSA is the production PSA-100 baseline, gap is the decimal rate gap
     (coupon - MORTGAGE30US/100, negative when locked in), beta_1 is the
     SIGNED literature value BETA1_PREPAY_MID = rothstein_beta1(0.065) < 0
     (so (-beta_1)*100*gap < 0 in the locked-in region: suppression), and the
     max-form is the production FLOOR_MODE. The covariate multiplier
     exp(beta_fico*z_f + beta_ltv*z_l + beta_burnout*b) is set to 1: its
     production z-scores and burnout states are loan-level engine state not
     reconstructable from the cohort panel without an engine run. This scales
     implied LEVELS, not the exp(beta_1*gap) structure; the level-free
     implied RATIO is reported alongside as the multiplier-invariant check.
     DERIVATION (stated ex ante): above the floor, the implied
     cumulative-CPR ratio between two gap depths g1, g2 (decimal) is
        SMM_1 / SMM_2 = exp( (-beta_1) * 100 * (g1 - g2) )
     applied to the voluntary component; the row-level computation below
     implements exactly this with the production floor applied row-wise and
     the panel's own exposure weights doing the aggregation.

=======================================================================
PART A — CUMULATIVE GAP-GRADIENT CONFRONTATION
=======================================================================
WINDOW: 202206..202509 inclusive — the QT window truncated to the Freddie
  panel's coverage (cohort_month_panel.parquet ends 2025-09); 40 months.
PANEL / CONDITIONING: matched_depth_reconciliation.build_panel() — the exact
  oos_identification.py conditioning (coupon>0 & exposure_upb>0; gap = coupon
  - MORTGAGE30US/100 on the calendar-month FRED ME-mean). Cluster/stratum
  unit: the 4-way stratum (vintage x coupon x fico_bucket x ltv_bucket;
  stratum.build_stratum_id), identical to floor_uncertainty.py.

BUCKETS (ex-ante choice, stated): cohort-months are grouped by each
  STRATUM's window-mean gap (exposure-weighted mean of the monthly decimal
  gap over the stratum's in-window rows), in percentage points:
     B1 [-1,0)   B2 [-2,-1)   B3 [-3,-2)   B4 <=-3
  (disjoint implementation: <=-3 takes gap_pp <= -3 exactly; the [-3,-2)
  label then covers (-3,-2); measure-zero boundary). Strata with window-mean
  gap >= 0 (at/above the money) are EXCLUDED and counted. The gap-depth
  definition is chosen over the committed E3 coupon-cohort definition
  because coupon buckets conflate depth with vintage/seasoning; the E3
  coupons map monotonically into these buckets and each bucket's
  exposure-weighted mean coupon is reported as the cross-walk.

SEASONING CONTROL (ONE chosen ex ante, as required): the simpler age cut,
  NOT an age-spline regression adjustment. PRIMARY sample = strata whose
  loan age at the window start is >= 24 months (age0 = mean_loan_age at the
  stratum's first in-window row minus months elapsed since 2022-06). By
  window end every included cohort-month is past the PSA ramp, so the
  age-composition differential across depth buckets (deep buckets skew
  toward young 2020-21 vintages) is removed the same way the mature-read
  age>=12/24 cuts of oos_identification.py handle it — and the analytic
  counterpart uses the actual mean_loan_age through h0_PSA row-wise anyway.
  The FULL-SAMPLE version (no age cut) is the disclosed sensitivity, never
  primary.

OUTCOME (pooled dollar SMM convention of vintage_residual_bound.py): per
  bucket, SMM_b = sum(prepaid_upb)/sum(exposure_upb) over all the bucket's
  in-window cohort-month rows; window CPR_b = (1-(1-SMM_b)^12)*100; and the
  cumulative prepaid share over the window, (1-(1-SMM_b)^40)*100 (T=40
  window months). Pooled dollar SMM IS the exposure-weighted mean of monthly
  SMMs; cumulation integrates out the monthly seasonality that dominated
  every differenced test.

ENDPOINT / SUPPORT RULE (mechanical, ex ante): the gradient's endpoints are
  the SHALLOWEST and DEEPEST bucket carrying >= 1% of the selection's
  four-bucket exposure AND >= 10 strata (clusters; the bootstrap needs
  them). Fixed from an exposure-composition inspection of the panel made
  before this spec was frozen — exposure_upb sums by candidate bucket ONLY;
  prepaid_upb (the outcome side) was NOT read. Expected endpoints: primary
  (age-matched) B1 vs B4 (B1 carries ~1.1% / 35 strata there); full-sample
  sensitivity B2 vs B4 (B1 carries only ~0.13% unmatched). The primary's
  B2-vs-B4 gradient is also reported for cross-sample comparability.

STATISTIC:
  realized gradient  = CPR(shallowest endpoint) - CPR(deepest endpoint)  [pp]
  model gradient     = same difference on the implied CPRs (same rows, same
                       exposure weights), at beta_1 in {mid, low, high} =
                       rothstein_beta1 on quarterly declines {6.5, 5.5, 7.7}%
                       => |beta_1| = {0.0686 ("0.069"), 0.0577, 0.0817}
  plus their ratio, the cumulative-share gradient, and the level-free
  voluntary ratio exp((-beta_1)*100*(gbar_shallow - gbar_deep)).
  95% CI on the realized gradient: stratum-cluster bootstrap, 1000 reps,
  seed 42, clusters = 4-way strata — floor_uncertainty.py's machinery:
  cluster_bootstrap_cpr is IMPORTED and used verbatim for the per-bucket
  CPR CIs (fresh default_rng(42) per read, its own convention); the joint
  gradient CI uses the same cluster-sum resampling extended to the two
  endpoint buckets from ONE default_rng(42) stream (shallow indices drawn
  first, then deep, per replicate block), because differencing two
  independently re-seeded per-bucket draws would couple identical seeds.
  Percentile CI [2.5, 97.5] and SE reported.

=======================================================================
PART B — POWER ANALYSIS
=======================================================================
H0 (beta_1 = 0): the null distribution of the realized gradient is generated
  by PERMUTING the gap-bucket labels across the selection's strata (the
  4-bucket label multiset preserved; 200 permutations; fresh
  default_rng(42) for Part B) and recomputing the shallow-endpoint-minus-
  deep-endpoint gradient from the permuted labels' pooled stratum sums.
  Under beta_1 = 0 the hazard is floor + seasoning only, and the age-matched
  selection removes the seasoning axis, so depth labels are exchangeable.
  One-sided 95% critical value = 95th percentile of the permuted gradients
  (the ex-ante branches are directional: shallow faster than deep).
POWER (estimator chosen ex ante): INJECTION into the permuted draws —
  power(beta_1) = mean over the 200 permuted gradients g_perm of
  1{ g_perm + G_implied(beta_1) > crit95 }. The normal approximation from
  the bootstrap SE, Phi(G_implied/SE_boot - 1.645), is reported alongside
  as a check, never primary. Power is reported at beta_1 = 0.069 (the
  production mid) and at the band edges 0.0577/0.0817 (rothstein_beta1 on
  5.5/7.7), plus a curve over |beta_1| in {0.01..0.12 step 0.01}.

=======================================================================
PARITY GATES (BLOCKING; run before Parts A/B; on any failure the JSON is
written with status GATE_FAILURE and the run stops — do not build on a
broken baseline)
=======================================================================
  G0  production-constants integrity: FLOOR_MODE == "max",
      INVOLUNTARY_CPR_ANNUAL == 0.04, BASELINE_MODE == "psa",
      PSA_SPEED == 100.0, P_Q_BASELINE == 0.06, Rothstein declines
      (0.055, 0.065, 0.077); |rothstein_beta1| reproduces
      {0.0577, 0.0686->rounds to 0.069, 0.0817} (tol 5e-4).
  G1  E3 pooled realized velocity: the committed
      abm/data/cohort_timing_diagnostic_results.json pooled Freddie
      delta-velocity -0.07438857974396679 (n=39, zero band
      0.32025630761017426) reproduced to < 1e-9 from the raw panel + the
      committed fold-in CSV, using the E3 module's own _delta_corr and its
      QT0/QT1 window (loaders imported; the nested pooled_velocity is
      replicated verbatim with a source comment).
  G2  E3 per-cohort realized lag-0 velocities: all six Freddie coupon
      cohorts (2.0..4.5%) reproduce the committed artifact values to
      < 1e-9, via the imported e3._realized_coupon_cpr / e3._delta_corr.
  G3  vintage_residual_bound pooled-SMM anchor: sampled_2017_2021 cpr_pct
      4.302657826519651 reproduced to <= 1e-6 pp from
      cohort_month_panel_fannie.parquet over QT_START<=period<QT_END (the
      committed G1-parity chain ties the panel to the artifact's cells at
      rel ~5e-16; same pooled-SMM compound-annualized convention).
  G4  floor_uncertainty machinery: the R2 floor read (2018 leg,
      gap<=-0.0025, age>=12) reproduces the committed 4.990624060575566%
      to <= 0.001pp with n == 137 cohort-months and 31 clusters, via the
      imported floor_uncertainty._select + matched_depth_reconciliation
      cpr_of on the same build_panel frame.
All committed values are consumed from the frozen artifacts at runtime and
asserted equal (1e-9) to the constants quoted in this header before gating.

=======================================================================
EX-ANTE INTERPRETIVE THRESHOLDS (verbatim; evaluated on the PRIMARY
age-matched gradient, its cluster-bootstrap 95% CI, the model-implied
gradient at beta_1 = 0.069, and injected power at 0.069; order of
evaluation T4, T1, T3, T2, T5)
=======================================================================
  T1 (episode corroboration): realized gradient positive (shallow faster
     than deep), its 95% CI excludes zero, AND the model-implied gradient
     lies inside the realized CI -> the marginal gains episode-level
     support; the manuscript may strengthen the abstract verb and must
     report the gradient beside the marginal.
  T2 (uninformative): realized CI includes zero AND power at beta_1=0.069
     < 0.5 -> the episode cannot discriminate; the manuscript states the
     power number and keeps its current calibration-projection posture
     (no verb change).
  T3 (episode disconfirmation): realized CI excludes the model-implied
     gradient from below with power >= 0.5 (the data could have seen the
     implied gradient and didn't) -> the manuscript must state that the
     episode's cross-section is inconsistent with the imported
     elasticity's implied magnitude and weaken the marginal's presentation
     accordingly.
  T4 (wrong sign): realized gradient significantly negative -> report as
     anomalous, flag composition/seasoning confound investigation, no
     headline change without diagnosis.
  T5 (residual branch, added ex ante to make the partition TOTAL — T1-T4
     do not cover every outcome): any result matching none of the above —
     e.g. the realized CI excludes zero AND lies wholly ABOVE the
     model-implied gradient (an excess gradient is a composition/credit
     confound signature, or model understatement — it is NOT corroboration
     of beta_1's magnitude), or the CI spans zero with power >= 0.5 ->
     report every number, no abstract verb change, flag for diagnosis.

Runtime target: < 10 minutes (one FRED MORTGAGE30US fetch; no microsim
engine runs anywhere; all arithmetic on committed parquet/CSV + cluster
sums). Deterministic given the frozen inputs: seed 42 throughout.

Run:  cd hazard && python3 episode_confrontation.py
      -> data/episode_confrontation_results.json  (frozen)
Does NOT change config.py production defaults. Does NOT edit any .tex file.
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
import literature_hazard as lh              # h0_psa / cpr_annual_to_monthly_hazard / rothstein_beta1  # noqa: E402
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

# E3 module (abm/cohort_timing_diagnostic.py): loaders/selectors imported
# per the reuse rule; appended (not inserted) so hazard modules keep priority.
sys.path.append(str(ROOT / "abm"))
import cohort_timing_diagnostic as e3       # noqa: E402

RESULTS_JSON = DATA_DIR / "episode_confrontation_results.json"
E3_ARTIFACT = ROOT / "abm" / "data" / "cohort_timing_diagnostic_results.json"
VRB_ARTIFACT = DATA_DIR / "vintage_residual_bound_results.json"
FU_ARTIFACT = DATA_DIR / "floor_uncertainty_results.json"
FANNIE_PANEL = DATA_DIR / "cohort_month_panel_fannie.parquet"

# ---- committed anchors quoted ex ante (asserted vs artifacts at runtime) ----
E3_POOLED_FREDDIE = (-0.07438857974396679, 39, 0.32025630761017426)
E3_COHORT_LAG0_FREDDIE = {
    "2.0": -0.08923910432952191,
    "2.5": -0.05738215063977279,
    "3.0": -0.047200878876133945,
    "3.5": -0.0871594360120068,
    "4.0": -0.12512233533245845,
    "4.5": -0.16419433385089685,
}
VRB_SAMPLED_CPR_PCT = 4.302657826519651     # vintage_residual_bound sampled_2017_2021
FU_R2_READ = (4.990624060575566, 137, 31)   # floor_uncertainty R2 (cpr %, n, clusters)

# ---- pre-committed run constants -------------------------------------------
WINDOW = (202206, 202509)      # QT window truncated to the Freddie panel's coverage
T_MONTHS = 40                  # window length (asserted at runtime)
BUCKET_ORDER = ["[-1,0)", "[-2,-1)", "[-3,-2)", "<=-3"]
AGE0_MIN = 24                  # primary seasoning cut: age >= 24 at window start
SUPPORT_MIN_SHARE = 0.01       # endpoint rule: >= 1% of four-bucket exposure ...
SUPPORT_MIN_STRATA = 10        # ... AND >= 10 strata (bootstrap clusters)
N_BOOT = 1000
N_PERM = 200
SEED = 42
POWER_THRESHOLD = 0.5
Z_ONE_SIDED_95 = 1.6448536269514722
BETA_CURVE_ABS = [round(0.01 * k, 2) for k in range(1, 13)]  # 0.01..0.12

TOL_E3 = 1e-9
TOL_VRB_PP = 1e-6
TOL_FU_PP = 0.001

VERDICT_SENTENCES = {
    "T1": ("T1 EPISODE CORROBORATION: realized gradient {G:+.3f}pp (95% CI "
           "[{LO:+.3f}, {HI:+.3f}]) is positive with the CI excluding zero, "
           "and the model-implied gradient {M:+.3f}pp lies inside the CI. "
           "The marginal gains episode-level support; the manuscript may "
           "strengthen the abstract verb ('Re-anchoring ... puts') and must "
           "report the gradient beside the marginal."),
    "T2": ("T2 UNINFORMATIVE: realized gradient {G:+.3f}pp, 95% CI "
           "[{LO:+.3f}, {HI:+.3f}] includes zero and power {P:.2f} at "
           "beta_1=0.069 is < 0.5. The episode cannot discriminate; the "
           "manuscript states the power number and keeps its current "
           "calibration-projection posture (no verb change)."),
    "T3": ("T3 EPISODE DISCONFIRMATION: realized 95% CI [{LO:+.3f}, "
           "{HI:+.3f}] excludes the model-implied gradient {M:+.3f}pp from "
           "below with power {P:.2f} >= 0.5 — the data could have seen the "
           "implied gradient and didn't. The manuscript must state that the "
           "episode's cross-section is inconsistent with the imported "
           "elasticity's implied magnitude and weaken the marginal's "
           "presentation accordingly."),
    "T4": ("T4 WRONG SIGN: realized gradient {G:+.3f}pp is significantly "
           "negative (95% CI [{LO:+.3f}, {HI:+.3f}]). Anomalous; flag "
           "composition/seasoning confound investigation; no headline change "
           "without diagnosis."),
    "T5": ("T5 OUTSIDE THE EX-ANTE T1-T4 PARTITION ({SUB}): realized "
           "gradient {G:+.3f}pp, 95% CI [{LO:+.3f}, {HI:+.3f}], "
           "model-implied {M:+.3f}pp, power {P:.2f}. Report every number; "
           "an excess gradient is a composition/credit confound signature "
           "or model understatement, NOT corroboration of beta_1's "
           "magnitude; no abstract verb change; flag for diagnosis."),
}


def _fail_out(gate_report: dict, msg: str) -> None:
    payload = {"mode": "episode_confrontation", "status": "GATE_FAILURE",
               "parity_gates": gate_report, "detail": msg}
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2,
                  default=lambda x: float(x)
                  if isinstance(x, (np.floating, np.integer)) else x)
        f.write("\n")
    raise SystemExit(
        f"PARITY GATE FAILURE — {msg}. Environment problem; STOP. "
        f"Diagnostics in {RESULTS_JSON}. Do NOT build on a broken baseline."
    )


def _months_since_window_start(rp: pd.Series) -> pd.Series:
    """Whole months from 2022-06 to the YYYYMM integer reporting period."""
    return (rp // 100) * 12 + (rp % 100) - (2022 * 12 + 6)


def gap_bucket(gpp: float) -> str | None:
    """Disjoint depth buckets on the window-mean gap in pp; None == excluded."""
    if gpp >= 0.0:
        return None
    if gpp <= -3.0:
        return "<=-3"
    if gpp < -2.0:
        return "[-3,-2)"
    if gpp < -1.0:
        return "[-2,-1)"
    return "[-1,0)"


def pooled_stats(rows: pd.DataFrame) -> dict:
    """Pooled dollar SMM convention (vintage_residual_bound.pooled_cpr_pct),
    plus the cumulative prepaid share over the T=40-month window."""
    exp = float(rows["exposure_upb"].sum())
    if exp <= 0:
        return {"computable": False}
    smm = float(rows["prepaid_upb"].sum()) / exp
    return {
        "computable": True,
        "smm": smm,
        "cpr_pct": (1.0 - (1.0 - smm) ** 12) * 100.0,
        "cumulative_share_pct": (1.0 - (1.0 - smm) ** T_MONTHS) * 100.0,
        "exposure_upb": exp,
        "n_rows": int(len(rows)),
        "n_strata": int(rows["stratum"].nunique()),
    }


def implied_hazard(rows: pd.DataFrame, beta1_signed: float,
                   h_floor: float) -> tuple[np.ndarray, np.ndarray]:
    """Production hazard eq.(2), covariate multiplier = 1 — replicates
    literature_hazard.prepay_hazard's floor/voluntary combination exactly
    (max-form under the production FLOOR_MODE; G0 pins FLOOR_MODE=='max')."""
    h0 = lh.baseline_hazard(rows["mean_loan_age"].to_numpy(dtype=np.float64))
    h_vol = h0 * np.exp((-beta1_signed) * (rows["gap"].to_numpy(dtype=np.float64) * 100.0))
    if FLOOR_MODE == "additive":  # pragma: no cover — production is "max" (G0)
        combined = 1.0 - (1.0 - h_floor) * (1.0 - h_vol)
        bind = np.zeros_like(h_vol, dtype=bool)
    else:
        combined = np.maximum(h_floor, h_vol)
        bind = h_floor >= h_vol
    return np.clip(combined, 0.0, 1.0), bind


def implied_bucket_stats(rows: pd.DataFrame, beta1_signed: float,
                         h_floor: float) -> dict:
    """Exposure-weighted implied pooled SMM -> CPR per the same convention."""
    h, bind = implied_hazard(rows, beta1_signed, h_floor)
    w = rows["exposure_upb"].to_numpy(dtype=np.float64)
    smm = float((h * w).sum() / w.sum())
    return {
        "smm": smm,
        "cpr_pct": (1.0 - (1.0 - smm) ** 12) * 100.0,
        "cumulative_share_pct": (1.0 - (1.0 - smm) ** T_MONTHS) * 100.0,
        "floor_bind_exposure_share": float((w * bind).sum() / w.sum()),
    }


def cluster_sums(rows: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Per-stratum (prepaid, exposure) sums — floor_uncertainty's cluster
    unit (cluster_bootstrap_cpr's own groupby, extracted for joint use)."""
    g = rows.groupby("stratum", sort=True)[["prepaid_upb", "exposure_upb"]].sum()
    return (g["prepaid_upb"].to_numpy(dtype=np.float64),
            g["exposure_upb"].to_numpy(dtype=np.float64))


def joint_gradient_bootstrap(shallow: pd.DataFrame, deep: pd.DataFrame,
                             n_reps: int = N_BOOT, seed: int = SEED) -> np.ndarray:
    """Joint stratum-cluster bootstrap of the CPR gradient: the
    cluster_bootstrap_cpr resampling convention (draw C clusters with
    replacement, recompute CPR from resampled cluster sums), applied to both
    endpoint buckets from ONE default_rng(seed) stream — shallow indices
    drawn first, then deep, per replicate block."""
    ps, es = cluster_sums(shallow)
    pdp, ed = cluster_sums(deep)
    rng = np.random.default_rng(seed)
    idx_s = rng.integers(0, len(ps), size=(n_reps, len(ps)))
    idx_d = rng.integers(0, len(pdp), size=(n_reps, len(pdp)))
    smm_s = ps[idx_s].sum(axis=1) / es[idx_s].sum(axis=1)
    smm_d = pdp[idx_d].sum(axis=1) / ed[idx_d].sum(axis=1)
    cpr_s = 100.0 * (1.0 - (1.0 - smm_s) ** 12)
    cpr_d = 100.0 * (1.0 - (1.0 - smm_d) ** 12)
    return cpr_s - cpr_d


def bucket_block(sel: pd.DataFrame, betas: dict[str, float],
                 h_floor: float, with_bucket_ci: bool) -> dict:
    """Realized + implied per-bucket stats, endpoints, gradients for one
    selection (primary or full-sample sensitivity)."""
    total_exp = float(sel["exposure_upb"].sum())
    buckets: dict[str, dict] = {}
    for b in BUCKET_ORDER:
        rows = sel[sel["bucket"] == b]
        st = pooled_stats(rows)
        if not st.get("computable"):
            buckets[b] = {"computable": False}
            continue
        entry = {
            "realized": st,
            "exposure_share": st["exposure_upb"] / total_exp,
            "mean_gap_pp": float(np.average(rows["gap"] * 100.0,
                                            weights=rows["exposure_upb"])),
            "mean_coupon_pct": float(np.average(rows["coupon"] * 100.0,
                                                weights=rows["exposure_upb"])),
            "implied": {lab: implied_bucket_stats(rows, bv, h_floor)
                        for lab, bv in betas.items()},
        }
        if with_bucket_ci:
            # floor_uncertainty's machinery verbatim (fresh rng(42) per read).
            draws, n_clusters = fu.cluster_bootstrap_cpr(rows)
            entry["realized"]["bootstrap_ci95_pct"] = [
                float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))]
            entry["realized"]["bootstrap_se_pp"] = float(np.std(draws, ddof=1))
            entry["realized"]["n_clusters"] = int(n_clusters)
        buckets[b] = entry

    qualified = [b for b in BUCKET_ORDER
                 if buckets[b].get("realized")
                 and buckets[b]["exposure_share"] >= SUPPORT_MIN_SHARE
                 and buckets[b]["realized"]["n_strata"] >= SUPPORT_MIN_STRATA]
    if len(qualified) < 2:
        return {"buckets": buckets, "degenerate": True,
                "qualified_buckets": qualified}
    shallow_end, deep_end = qualified[0], qualified[-1]

    g_real = (buckets[shallow_end]["realized"]["cpr_pct"]
              - buckets[deep_end]["realized"]["cpr_pct"])
    g_cum = (buckets[shallow_end]["realized"]["cumulative_share_pct"]
             - buckets[deep_end]["realized"]["cumulative_share_pct"])
    g_impl = {lab: (buckets[shallow_end]["implied"][lab]["cpr_pct"]
                    - buckets[deep_end]["implied"][lab]["cpr_pct"])
              for lab in betas}
    dgap = (buckets[shallow_end]["mean_gap_pp"]
            - buckets[deep_end]["mean_gap_pp"])
    vol_ratio = {lab: float(np.exp((-bv) * dgap))
                 for lab, bv in betas.items()}
    return {
        "buckets": buckets,
        "degenerate": False,
        "qualified_buckets": qualified,
        "endpoints": {"shallow": shallow_end, "deep": deep_end},
        "realized_gradient_pp": g_real,
        "realized_cumulative_gradient_pp": g_cum,
        "implied_gradient_pp": g_impl,
        "endpoint_mean_gap_delta_pp": dgap,
        "implied_voluntary_ratio_endpoints": vol_ratio,
        "realized_over_implied_mid": (g_real / g_impl["mid"]
                                      if g_impl["mid"] != 0 else None),
    }


def main() -> None:
    t0 = time.perf_counter()
    gates: dict = {}

    # =====================================================================
    # Committed artifacts, asserted vs the quoted constants (pre-gate)
    # =====================================================================
    with open(E3_ARTIFACT) as f:
        e3_art = json.load(f)
    pooled_c = e3_art["realized_cohorts"]["pooled_velocity"]["freddie"]
    assert abs(pooled_c["delta_velocity_lag0"] - E3_POOLED_FREDDIE[0]) < 1e-9
    assert pooled_c["n"] == E3_POOLED_FREDDIE[1]
    assert abs(pooled_c["zero_band"] - E3_POOLED_FREDDIE[2]) < 1e-9
    for k, v in E3_COHORT_LAG0_FREDDIE.items():
        assert abs(e3_art["realized_cohorts"]["freddie"]["cohorts"][k]
                   ["delta_velocity_lag0"] - v) < 1e-9, k
    with open(VRB_ARTIFACT) as f:
        vrb = json.load(f)
    assert abs(vrb["results"]["segments"]["sampled_2017_2021"]["cpr_pct"]
               - VRB_SAMPLED_CPR_PCT) < 1e-9
    with open(FU_ARTIFACT) as f:
        fu_art = json.load(f)
    r2 = fu_art["part_a_sampling_uncertainty"]["reads"]["R2_2018_gap<=-0.0025_age>=12"]
    assert abs(r2["point_cpr_pct"] - FU_R2_READ[0]) < 1e-9
    assert r2["n_cohort_months"] == FU_R2_READ[1]
    assert r2["n_clusters"] == FU_R2_READ[2]

    # =====================================================================
    # G0 — production-constants integrity
    # =====================================================================
    print("=" * 72)
    print("PARITY GATES (blocking)")
    print("=" * 72)
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

    # =====================================================================
    # G1/G2 — E3 realized-velocity parity (raw panel + committed fold-in CSV)
    # =====================================================================
    raw = pd.read_parquet(mdr.PANEL_PATH)
    csv = pd.read_csv(e3.FOLDIN_CSV, index_col=0, parse_dates=True)
    rate_level = csv["MORTGAGE30US"].copy()
    rate_level.index = rate_level.index.to_period("M")
    drate_p = rate_level.diff()

    # Source: abm/cohort_timing_diagnostic.py main()::pooled_velocity —
    # nested (not importable), replicated verbatim.
    q = raw[(raw["period"] >= e3.QT0) & (raw["period"] <= e3.QT1)]
    sub = q.groupby("period").agg(prep=("prepaid_upb", "sum"),
                                  exp=("exposure_upb", "sum"))
    cpr_pool = (sub["prep"] / sub["exp"]).clip(lower=0.0) * 12 * 100.0
    cpr_pool.index = sub.index.to_period("M")
    dvel, n = e3._delta_corr(cpr_pool, drate_p)
    band = 2.0 / np.sqrt(n)
    g1_ok = (abs(dvel - E3_POOLED_FREDDIE[0]) < TOL_E3
             and n == E3_POOLED_FREDDIE[1]
             and abs(band - E3_POOLED_FREDDIE[2]) < TOL_E3)
    gates["G1_e3_pooled_velocity"] = {
        "got": dvel, "want": E3_POOLED_FREDDIE[0], "n": n,
        "zero_band": band, "tol": TOL_E3, "pass": bool(g1_ok),
    }
    print(f"  G1 E3 pooled Freddie velocity: {dvel:+.12f} vs "
          f"{E3_POOLED_FREDDIE[0]:+.12f} (n={n})  "
          f"[{'PASS' if g1_ok else 'FAIL'}]")
    if not g1_ok:
        _fail_out(gates, "G1 E3 pooled realized velocity parity failed")

    g2_cells, g2_ok = {}, True
    for c in e3.COHORT_COUPONS:
        cpr_c = e3._realized_coupon_cpr(raw, c)
        dv, nc = e3._delta_corr(cpr_c, drate_p)
        want = E3_COHORT_LAG0_FREDDIE[f"{c * 100:.1f}"]
        ok = abs(dv - want) < TOL_E3
        g2_cells[f"{c * 100:.1f}"] = {"got": dv, "want": want, "n": nc,
                                      "pass": bool(ok)}
        g2_ok &= ok
    gates["G2_e3_cohort_lag0"] = {"cells": g2_cells, "tol": TOL_E3,
                                  "pass": bool(g2_ok)}
    print(f"  G2 E3 per-cohort lag-0 velocities (6 cells)  "
          f"[{'PASS' if g2_ok else 'FAIL'}]")
    if not g2_ok:
        _fail_out(gates, "G2 E3 per-cohort lag-0 parity failed")

    # =====================================================================
    # G3 — vintage_residual_bound pooled-SMM anchor from the Fannie panel
    # =====================================================================
    fan = pd.read_parquet(FANNIE_PANEL)
    fqt = fan[(fan["period"] >= QT_START.to_pydatetime())
              & (fan["period"] < QT_END.to_pydatetime())]
    smm_f = float(fqt["prepaid_upb"].sum()) / float(fqt["exposure_upb"].sum())
    cpr_f = (1.0 - (1.0 - smm_f) ** 12) * 100.0
    g3_ok = abs(cpr_f - VRB_SAMPLED_CPR_PCT) <= TOL_VRB_PP
    gates["G3_vrb_pooled_smm_anchor"] = {
        "got_cpr_pct": cpr_f, "want_cpr_pct": VRB_SAMPLED_CPR_PCT,
        "tol_pp": TOL_VRB_PP, "pass": bool(g3_ok),
    }
    print(f"  G3 vintage_residual_bound sampled CPR: {cpr_f:.12f}% vs "
          f"{VRB_SAMPLED_CPR_PCT:.12f}%  [{'PASS' if g3_ok else 'FAIL'}]")
    if not g3_ok:
        _fail_out(gates, "G3 pooled-SMM anchor parity failed")

    # =====================================================================
    # G4 — floor_uncertainty R2 read on the shared panel (FRED fetch here)
    # =====================================================================
    df = mdr.build_panel()
    df["stratum"] = [
        build_stratum_id(v, c, fb, lb)
        for v, c, fb, lb in zip(df["vintage"], df["coupon"],
                                df["fico_bucket"], df["ltv_bucket"])
    ]
    sel_r2 = fu._select(df, 201801, 201812, -0.0025, 12)
    cpr_r2, _, n_r2 = mdr.cpr_of(sel_r2)
    cl_r2 = int(sel_r2["stratum"].nunique())
    g4_ok = (abs(cpr_r2 - FU_R2_READ[0]) <= TOL_FU_PP
             and n_r2 == FU_R2_READ[1] and cl_r2 == FU_R2_READ[2])
    gates["G4_floor_uncertainty_R2"] = {
        "got_cpr_pct": cpr_r2, "want_cpr_pct": FU_R2_READ[0],
        "got_n": n_r2, "want_n": FU_R2_READ[1],
        "got_clusters": cl_r2, "want_clusters": FU_R2_READ[2],
        "tol_pp": TOL_FU_PP, "pass": bool(g4_ok),
    }
    print(f"  G4 floor_uncertainty R2: {cpr_r2:.4f}% (n={n_r2}, "
          f"clusters={cl_r2}) vs {FU_R2_READ[0]:.4f}%  "
          f"[{'PASS' if g4_ok else 'FAIL'}]")
    if not g4_ok:
        _fail_out(gates, "G4 floor_uncertainty R2 parity failed")
    print("  ALL GATES PASS — safe to proceed.")

    # =====================================================================
    # PART A — selection, buckets, gradients
    # =====================================================================
    print("\n" + "=" * 72)
    print(f"PART A — cumulative gap-gradient confrontation "
          f"({WINDOW[0]}..{WINDOW[1]}, {T_MONTHS} months)")
    print("=" * 72)
    win = df[(df["rp"] >= WINDOW[0]) & (df["rp"] <= WINDOW[1])].copy()
    n_months = int(win["rp"].nunique())
    assert n_months == T_MONTHS, f"window carries {n_months} months, expected {T_MONTHS}"

    # stratum window-mean gap (exposure-weighted) and age at window start
    win["_gx"] = win["gap"] * win["exposure_upb"]
    agg = win.groupby("stratum").agg(gx=("_gx", "sum"),
                                     ex=("exposure_upb", "sum"))
    wmg_pp = (agg["gx"] / agg["ex"]) * 100.0
    first = win.sort_values("rp").groupby("stratum").first()
    age0 = first["mean_loan_age"] - _months_since_window_start(first["rp"])
    info = pd.DataFrame({"wmg_pp": wmg_pp, "age0": age0})
    info["bucket"] = info["wmg_pp"].map(gap_bucket)
    win = win.drop(columns=["_gx"]).merge(
        info, left_on="stratum", right_index=True, how="left")

    excluded = info[info["bucket"].isna()]
    bucketed = win[win["bucket"].notna()].copy()
    primary = bucketed[bucketed["age0"] >= AGE0_MIN].copy()
    print(f"  strata: {len(info)} total, {len(excluded)} excluded (window-mean "
          f"gap >= 0), {info['bucket'].notna().sum()} bucketed, "
          f"{int((info['bucket'].notna() & (info['age0'] >= AGE0_MIN)).sum())} "
          f"age-matched (age0 >= {AGE0_MIN})")

    h_floor = float(lh.cpr_annual_to_monthly_hazard(
        np.array([INVOLUNTARY_CPR_ANNUAL]))[0])
    betas = {"mid": b_mid, "low": b_low, "high": b_high}

    blk_primary = bucket_block(primary, betas, h_floor, with_bucket_ci=True)
    blk_full = bucket_block(bucketed, betas, h_floor, with_bucket_ci=False)
    if blk_primary.get("degenerate"):
        payload = {"mode": "episode_confrontation", "status": "DEGENERATE",
                   "parity_gates": gates,
                   "detail": "fewer than two qualified buckets in the primary "
                             "age-matched selection — gradient not computable",
                   "primary": blk_primary}
        with open(RESULTS_JSON, "w") as f:
            json.dump(payload, f, indent=2, default=float)
            f.write("\n")
        raise SystemExit("DEGENERATE selection — see results JSON.")

    for label, blk in (("PRIMARY (age-matched)", blk_primary),
                       ("SENSITIVITY (full sample)", blk_full)):
        if blk.get("degenerate"):
            print(f"\n  {label}: DEGENERATE — fewer than two qualified "
                  f"buckets ({blk['qualified_buckets']}); reported, not used")
            continue
        print(f"\n  {label}: endpoints "
              f"{blk['endpoints']['shallow']} vs {blk['endpoints']['deep']}")
        for b in BUCKET_ORDER:
            e = blk["buckets"][b]
            if not e.get("realized"):
                print(f"    {b:>8s}: not computable")
                continue
            r = e["realized"]
            print(f"    {b:>8s}: CPR {r['cpr_pct']:6.3f}%  cum "
                  f"{r['cumulative_share_pct']:6.2f}%  share "
                  f"{100 * e['exposure_share']:6.2f}%  strata "
                  f"{r['n_strata']:3d}  gap {e['mean_gap_pp']:+.2f}pp  "
                  f"coupon {e['mean_coupon_pct']:.2f}%  implied(mid) "
                  f"{e['implied']['mid']['cpr_pct']:6.3f}%")
        print(f"    realized gradient {blk['realized_gradient_pp']:+.4f}pp | "
              f"implied (mid/low/high) "
              f"{blk['implied_gradient_pp']['mid']:+.4f}/"
              f"{blk['implied_gradient_pp']['low']:+.4f}/"
              f"{blk['implied_gradient_pp']['high']:+.4f}pp")

    # secondary comparability line: B2-vs-B4 gradient inside the primary
    b2b4 = None
    if (blk_primary["buckets"]["[-2,-1)"].get("realized")
            and blk_primary["buckets"]["<=-3"].get("realized")):
        b2b4 = (blk_primary["buckets"]["[-2,-1)"]["realized"]["cpr_pct"]
                - blk_primary["buckets"]["<=-3"]["realized"]["cpr_pct"])

    # ---- joint cluster bootstrap on the primary gradient --------------------
    sh, dp = blk_primary["endpoints"]["shallow"], blk_primary["endpoints"]["deep"]
    grads = joint_gradient_bootstrap(primary[primary["bucket"] == sh],
                                     primary[primary["bucket"] == dp])
    ci = [float(np.percentile(grads, 2.5)), float(np.percentile(grads, 97.5))]
    se = float(np.std(grads, ddof=1))
    blk_primary["gradient_bootstrap"] = {
        "n_reps": N_BOOT, "seed": SEED,
        "convention": "joint stratum-cluster resampling, one default_rng(42) "
                      "stream, shallow indices then deep per replicate block",
        "ci95_pp": ci, "se_pp": se,
        "draws_min_pp": float(grads.min()), "draws_max_pp": float(grads.max()),
    }
    if not blk_full.get("degenerate"):
        grads_full = joint_gradient_bootstrap(
            bucketed[bucketed["bucket"] == blk_full["endpoints"]["shallow"]],
            bucketed[bucketed["bucket"] == blk_full["endpoints"]["deep"]])
        blk_full["gradient_bootstrap"] = {
            "n_reps": N_BOOT, "seed": SEED,
            "ci95_pp": [float(np.percentile(grads_full, 2.5)),
                        float(np.percentile(grads_full, 97.5))],
            "se_pp": float(np.std(grads_full, ddof=1)),
        }
    print(f"\n  PRIMARY gradient {blk_primary['realized_gradient_pp']:+.4f}pp, "
          f"95% CI [{ci[0]:+.4f}, {ci[1]:+.4f}], SE {se:.4f}pp")

    # =====================================================================
    # PART B — permutation null + power
    # =====================================================================
    print("\n" + "=" * 72)
    print(f"PART B — permutation null ({N_PERM} perms, seed {SEED}) + power")
    print("=" * 72)
    g_strata = primary.groupby("stratum").agg(
        pre=("prepaid_upb", "sum"), ex=("exposure_upb", "sum"),
        bucket=("bucket", "first"))
    pre_arr = g_strata["pre"].to_numpy(dtype=np.float64)
    ex_arr = g_strata["ex"].to_numpy(dtype=np.float64)
    labels = g_strata["bucket"].to_numpy()
    rng = np.random.default_rng(SEED)  # fresh rng(42) for Part B
    perm_grads = np.empty(N_PERM)
    for k in range(N_PERM):
        lab_p = labels[rng.permutation(len(labels))]
        ms, md_ = lab_p == sh, lab_p == dp
        smm_s = pre_arr[ms].sum() / ex_arr[ms].sum()
        smm_d = pre_arr[md_].sum() / ex_arr[md_].sum()
        perm_grads[k] = (100.0 * (1.0 - (1.0 - smm_s) ** 12)
                         - 100.0 * (1.0 - (1.0 - smm_d) ** 12))
    crit95 = float(np.percentile(perm_grads, 95.0))
    g_real = blk_primary["realized_gradient_pp"]
    p_perm = float((1 + (perm_grads >= g_real).sum()) / (N_PERM + 1))

    def power_pair(g_impl: float) -> tuple[float, float]:
        injected = float((perm_grads + g_impl > crit95).mean())
        normal = float(norm.cdf(g_impl / se - Z_ONE_SIDED_95))
        return injected, normal

    named_powers = {}
    for lab, bv in betas.items():
        g_i = blk_primary["implied_gradient_pp"][lab]
        inj, nrm = power_pair(g_i)
        named_powers[lab] = {"beta1_abs": abs(bv), "implied_gradient_pp": g_i,
                             "power_injected": inj, "power_normal_approx": nrm}
    curve = []
    rows_sh = primary[primary["bucket"] == sh]
    rows_dp = primary[primary["bucket"] == dp]
    for babs in sorted(set(BETA_CURVE_ABS
                           + [round(abs(b), 6) for b in betas.values()])):
        g_i = (implied_bucket_stats(rows_sh, -babs, h_floor)["cpr_pct"]
               - implied_bucket_stats(rows_dp, -babs, h_floor)["cpr_pct"])
        inj, nrm = power_pair(g_i)
        curve.append({"beta1_abs": babs, "implied_gradient_pp": g_i,
                      "power_injected": inj, "power_normal_approx": nrm})
    power_069 = named_powers["mid"]["power_injected"]
    print(f"  crit95 (one-sided) {crit95:+.4f}pp, permutation p(one-sided) "
          f"{p_perm:.4f}")
    print(f"  power (injected/normal): mid {named_powers['mid']['power_injected']:.3f}/"
          f"{named_powers['mid']['power_normal_approx']:.3f}  low "
          f"{named_powers['low']['power_injected']:.3f}  high "
          f"{named_powers['high']['power_injected']:.3f}")

    # =====================================================================
    # VERDICT — ex-ante branches (order T4, T1, T3, T2, T5)
    # =====================================================================
    lo, hi = ci
    g_model = blk_primary["implied_gradient_pp"]["mid"]
    checks = {
        "gradient_positive": g_real > 0,
        "ci_excludes_zero_above": lo > 0,
        "ci_includes_zero": lo <= 0 <= hi,
        "ci_significantly_negative": hi < 0,
        "model_inside_ci": lo <= g_model <= hi,
        "ci_below_model": hi < g_model,
        "ci_above_model": lo > g_model,
        "power_at_0.069": power_069,
        "power_ge_threshold": power_069 >= POWER_THRESHOLD,
    }
    sub = None
    if checks["ci_significantly_negative"]:
        branch = "T4"
    elif (checks["gradient_positive"] and checks["ci_excludes_zero_above"]
          and checks["model_inside_ci"]):
        branch = "T1"
    elif checks["ci_below_model"] and checks["power_ge_threshold"]:
        branch = "T3"
    elif checks["ci_includes_zero"] and not checks["power_ge_threshold"]:
        branch = "T2"
    else:
        branch = "T5"
        sub = ("excess_gradient_ci_above_model" if checks["ci_above_model"]
               else "zero_spanning_with_power" if checks["ci_includes_zero"]
               else "other")
    sentence = VERDICT_SENTENCES[branch].format(
        G=g_real, LO=lo, HI=hi, M=g_model, P=power_069, SUB=sub or "")
    print("\n" + "=" * 72)
    print(f"VERDICT: {sentence}")

    # =====================================================================
    # Freeze
    # =====================================================================
    runtime_s = round(time.perf_counter() - t0, 1)
    payload = {
        "mode": "episode_confrontation",
        "status": "OK",
        "spec": {
            "purpose": "round-21 LG-4: cumulative cross-cohort confrontation "
                       "of the imported elasticity + power analysis; design "
                       "frozen in the module docstring before the run",
            "window": f"{WINDOW[0]}..{WINDOW[1]} ({T_MONTHS} months; QT window "
                      "truncated to the Freddie panel's coverage)",
            "bucket_rule": "stratum window-mean gap (exposure-weighted), pp "
                           "buckets [-1,0)/[-2,-1)/[-3,-2)/<=-3; gap>=0 "
                           "excluded; chosen over E3 coupon cohorts (depth "
                           "axis directly, coupon crosswalk reported)",
            "seasoning_control": f"age0 >= {AGE0_MIN} at window start "
                                 "(PRIMARY); full sample disclosed sensitivity",
            "outcome_convention": "pooled dollar SMM over the window "
                                  "(vintage_residual_bound.py), CPR = "
                                  "1-(1-SMM)^12, cumulative share "
                                  f"1-(1-SMM)^{T_MONTHS}",
            "endpoint_support_rule": f">= {100 * SUPPORT_MIN_SHARE:.0f}% of "
                                     f"four-bucket exposure AND >= "
                                     f"{SUPPORT_MIN_STRATA} strata",
            "model_implied_path": "ANALYTIC from hazard eq.(2): "
                                  "max(h_floor, h0_PSA(age)*exp((-beta1)*100*"
                                  "gap)), production floor 4% / FLOOR_MODE "
                                  "max / PSA-100; covariate multiplier = 1 "
                                  "(disclosed); NO engine run — committed "
                                  "microsim/floor_sweep parquets are monthly "
                                  "aggregates with no cohort dimension",
            "power_estimator": "primary = implied-gradient injection into "
                               "permuted draws vs one-sided 95% critical "
                               "value; normal approximation reported as check",
        },
        "parity_gates": gates,
        "parity_gates_all_pass": True,
        "selection": {
            "n_strata_total": int(len(info)),
            "n_strata_excluded_gap_ge0": int(len(excluded)),
            "excluded_exposure_share": float(
                win[win["bucket"].isna()]["exposure_upb"].sum()
                / win["exposure_upb"].sum()) if win["bucket"].isna().any() else 0.0,
            "n_strata_bucketed": int(info["bucket"].notna().sum()),
            "n_strata_primary": int(primary["stratum"].nunique()),
            "n_rows_primary": int(len(primary)),
            "n_rows_full": int(len(bucketed)),
        },
        "part_a": {
            "primary_age_matched": blk_primary,
            "sensitivity_full_sample": blk_full,
            "primary_b2_vs_b4_gradient_pp": b2b4,
        },
        "part_b": {
            "permutation": {
                "n_permutations": N_PERM, "seed": SEED,
                "crit95_one_sided_pp": crit95,
                "p_value_one_sided": p_perm,
                "mean_pp": float(perm_grads.mean()),
                "sd_pp": float(perm_grads.std(ddof=1)),
                "percentiles_pp": {p: float(np.percentile(perm_grads, p))
                                   for p in (2.5, 5, 25, 50, 75, 95, 97.5)},
                "draws_pp": [float(x) for x in perm_grads],
            },
            "power_at_named_betas": named_powers,
            "power_curve": curve,
            "power_threshold": POWER_THRESHOLD,
        },
        "verdict": {
            "branch": branch,
            "t5_subcase": sub,
            "checks": checks,
            "inputs": {
                "realized_gradient_pp": g_real,
                "gradient_ci95_pp": ci,
                "gradient_se_pp": se,
                "model_implied_gradient_pp_at_0.069": g_model,
                "power_injected_at_0.069": power_069,
            },
            "sentence": sentence,
            "abstract_verb_context": "current abstract verb: 'Re-anchoring "
                                     "... puts'; T1 may strengthen, T2 keeps, "
                                     "T3 weakens, T4/T5 no change without "
                                     "diagnosis",
        },
        "runtime_s": runtime_s,
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2,
                  default=lambda x: float(x)
                  if isinstance(x, (np.floating, np.integer)) else x)
        f.write("\n")
    print(f"\nResults -> {RESULTS_JSON}")
    print(f"Runtime: {runtime_s}s")


if __name__ == "__main__":
    main()
