#!/usr/bin/env python3
"""
cross_design_seeds.py — the seed distribution of the cross-design pair: every
cross-design number in the manuscript is a SINGLE seed-42 draw, and the
pre-committed 50%/35% thresholds are being crossed by an N=1 estimator.

PRE-COMMITTED SPEC (fixed in this header BEFORE any run; ex-ante convention of
hazard/concave_marginal.py, hazard/floor_form_offwindow.py and
abm/cross_design_reweight.py).

Referee objection (round 21, seed-noise leg). Six cross-design quantities are
quoted in the manuscript — 59.3% and 20.9% (cross_design_test.py), 76.3%,
12.6%, 70.6% and 36.0% (cross_design_reweight.py), plus the 150.6%
external-gate variant (abm_external_gates.py) — and every one of them is a
single draw at seed 42. Two randomization layers are pinned at 42 and neither
has ever been varied on this design:
  (i)  the behavioral draw — abm_lockin_simulation.RNG_SEED = 42 feeding
       HousingMarketEngine.__init__(seed=...) -> np.random.default_rng(seed)
       for income, home value, mobility desire, transaction cost, patience;
  (ii) the balance-weighted 10,000-of-75,000 covariate subsample —
       freddie_population.load_freddie_structural_sample(..., seed=42).
The sibling 50-seed run that DOES exist (abm/monte_carlo_simulation.py, seeds
0-49, committed abm/monte_carlo_results.csv) has SD $24.834907519213886B on a
$764.7482532227002B benchmark (3.247 points), but it varies only layer (i), on
the SYNTHETIC population, and it never varies the calibration. So the sentence
this run exists to test — paper/v18/revised_paper_v18.tex line 72
(tab:headline): "the operative uncertainty is calibration, not seed noise
(single-choice swings span 20.9--59.3%)" — compares a seed band measured on
one population against a calibration swing measured on another. The seed band
of the cross-design pair itself has never been measured. This script measures
it, and varies BOTH layers.

SCOPE (fixed ex ante; what this run does NOT do)
- Only the un-reweighted cross-design pair (cross_design_test.py variants
  (a) recalibrated and (b) frozen) is re-seeded. The composition-reweighted
  quartet (76.3 / 12.6 / 70.6 / 36.0, cross_design_reweight.py) and the
  external-gate variant (150.6, abm_external_gates.py) are NOT re-seeded here:
  the reweight design's importance weights and re-draw allocation are functions
  of the covariate draw, so re-seeding them is a separate run. The seed
  dispersion measured here is the DISCLOSED PROXY for those four numbers, and
  that is a limitation of this run, not a result of it.
- No decision rule, hazard, floor, benchmark or scoring path is touched. The
  Danish leg is population-independent under the production 'dk_level' anchor
  and is not exercised. Nothing in hazard/ runs.
- Grids are NOT restricted. monte_carlo_simulation.restrict_grids_to_observed
  mutates abm.RATE_GRID / FRICTION_GRID / RATE_VELOCITY_GRID; its claim of
  interpolation-identity is not asserted here, because a bit-exact parity gate
  cannot be run against the committed 3,380-node surface on a trimmed grid.
  Every surface in this run is the full 13 x 26 x 10 = 3,380-node sweep.
- The share basis is fed.export_headline_metrics dollars_b
  share_explained_pct against the $764.7482532227002B benchmark — the basis on
  which the manuscript quotes 59.3 / 20.9 / 76.3 / 12.6. It is NOT the shared
  accounting basis on which the production-ABM row quotes 13.6% seed mean and
  the 10-17% seed band, and no cross-basis comparison is made anywhere below.

LEGS (all at the pinned frozen-manifest calibration inputs; SEEDS = 0..49)
  SEEDS = tuple(range(50)) — chosen to match abm/monte_carlo_simulation.py
  (N_RUNS = 50, default seed range [0, 50)), so this seed band and the
  manuscript's existing 50-seed band are drawn on the same seed set; 42 is
  inside the range, so the committed configuration is one cell of leg A and
  supplies the parity gate. 50 seeds put SE(mean) at SD/sqrt(50) = 0.141 x SD,
  which resolves the mean against the 50/35 thresholds at any SD this design
  can plausibly produce, and the runtime evidence below puts 3 legs x 50 seeds
  x 2 variants = 300 scored cells at roughly ten minutes.
  Leg A (JOINT, PRIMARY): behavioral seed = covariate seed = s. Total seed
     noise of the design. The verdict is read off leg A.
  Leg B (behavioral only): behavioral seed = s, covariate seed = 42.
  Leg C (covariate only): behavioral seed = 42, covariate seed = s.
     B and C attribute A; the attribution is reported, and NO threshold rides
     on it (variance additivity is a diagnostic, not a claim).
  Each leg runs BOTH variants at every seed:
     recalibrated — the III.C floor search (calibrate_mobility_scale_freddie
        semantics: binary-search the mobility scale so the population hits the
        4-5% involuntary floor at 8% market rate, zero velocity, static 7%
        friction; lo/hi 1,000/500,000, 30 iterations, mid rule) re-run on THAT
        seed's population. This is the paper's own rule whenever the
        population changes, so it must be re-run per seed.
     frozen — the committed production scale 43,882.8125 held FIXED at every
        seed. Holding it is what "frozen" means (cross_design_test variant
        (b): "the production synthetic calibration applied unchanged"); a
        per-seed re-derivation would no longer be frozen.
  Leg D (calibration-anchor seed sweep, unscored): the frozen anchor 43,882.8125
     is itself a seed-42 draw, so calibrate_mobility_scale's own search is
     re-run at each behavioral seed on the synthetic cohort population
     (manifest reference cohort 2.0%, 60mo). Scales only, no surfaces, no
     scoring; reported as the seed dispersion of the calibration anchor.

PARITY GATES (blocking; HALT with a GATE_FAILURE artifact before any new
quantity is interpreted; the abm/cross_design_reweight.py convention)
  G0a committed-state quotes (1e-9): cross_design_results.json variants
     reproduce mobility_scale 36,085.9375 / 43,882.8125, trapped_b
     453.5186133616682 / 159.49813800542833, share_pct 59.30299434493775 /
     20.856293209339483, empirical_trapped_b 764.7482532227002, and its
     preregistration bands == {>50 undercut, [10,35] corroborate}.
  G0b the gate this run must not disturb (1e-9): cross_design_reweight_results
     .json variants.v1_recalibrated.share_pct == 59.30299434493775 and
     variants.v2_reweighted_frozen.share_pct == 12.561542534955805 — the two
     values tools/liveness_gates.py pins at 1e-9 / 1e-6 in the round-21
     cross-design-reweight gate. This run never writes that file; G0b asserts
     the state it depends on is intact before starting.
  G0c production constants: abm.RNG_SEED 42, N_HOUSEHOLDS 10,000, DTI_MAX
     0.43, WAIT_AND_SEE 0.20/0.015, load_freddie_structural_sample's default
     seed 42, latest_run_manifest run_tag == run-2026-07-05-berger, that
     manifest's pipeline.mobility_scale == 43,882.8125 and its medians
     83,730 / 403,200 (pinned as the calibration inputs; live FRED medians are
     fetched, reported and never used — the dti_threshold_sweep convention).
  G0d no-overwrite: sha256 of abm/abm_cpr_surface_freddie_recalibrated.csv,
     abm/abm_cpr_surface_freddie_frozen.csv, abm/data/cross_design_results
     .json, abm/data/cross_design_reweight_results.json and
     abm/data/abm_external_gates_results.json recorded at start and asserted
     UNCHANGED at the end. Provenance echo of the two surface CSVs at spec
     time (recorded, not gated, because a legitimate --rebuild elsewhere may
     move them): c2a69e85... / 28fca7cd....
  G1 builder equivalence (bit-exact): the seeded engine builder in this file,
     at behavioral seed 42, reproduces cross_design_test._build_engine on
     every precomputed population array (_monthly_income, _home_values,
     _desires, _txn_offsets, _patience, _current_payment, _outstanding_us,
     _n_rem) via np.array_equal. The builder exists only because
     _build_engine hard-pins seed 42; it must be its exact restriction at 42.
  G2 search equivalence (bit-exact / 1e-9): the seeded Freddie floor search at
     seed 42 returns EXACTLY cross_design_test.calibrate_mobility_scale_freddie
     on the same population, and both equal 36,085.9375; the seeded synthetic
     search at seed 42 returns EXACTLY abm.calibrate_mobility_scale at the
     manifest reference cohort, and both equal 43,882.8125.
  G3 SCORE PARITY, the gate that licenses everything else (leg A, seed 42,
     run first, on the fresh-surface path this whole script uses):
       G3a |delta| <= 1e-9 on share_pct AND trapped_b for both variants vs
           59.30299434493775 / 453.5186133616682 and 20.856293209339483 /
           159.49813800542833;
       G3b |delta| <= 0.05B on empirical_trapped_b vs 764.7482532227002 (the
           reweight spec's EMPIRICAL_TOL_B; it absorbs only upstream
           FRED/SOMA revision noise).
     Declared ex ante: if G3b passes and G3a fails, the code path drifted —
     HALT. If G3b fails, the upstream frame was revised — HALT and report the
     deltas. There is no branch that loosens a tolerance and continues.
  G4 leg identity (exact 0.0): legs B and C at seed 42 are the committed
     configuration by construction and are recomputed independently in the
     sweep; their scale, trapped_b and share_pct must equal leg A's parity
     cell exactly.
  G5 determinism (exact 0.0): the leg-A seed-7 recalibrated cell is executed
     twice end-to-end (search included) and must return bit-identical scale,
     floor CPR, trapped_b and share_pct. No global RNG state is set anywhere
     in this run: the engine's rng is self-contained
     (np.random.default_rng(seed)), and setting np.random.seed would depart
     from the committed cross_design_test path.
  G6 floor retention (pre-committed handling, NOT a silent drop; applies to
     the RECALIBRATED cells only): every recalibrated cell records its floor
     CPR at 8%, and seeds whose search leaves [4%, 5%] are FLAGGED and
     reported. The primary distribution INCLUDES them, because the paper's
     rule returns whatever scale its search returns; the distribution
     excluding them is reported beside it. HALT only if more than 20% of the
     recalibrated seeds in any leg are flagged — that would mean the III.C
     recalibration rule is not seed-portable and no distribution on it is
     interpretable. The FROZEN cells are deliberately NOT floor-gated: the
     frozen scale is calibrated on the synthetic cohort population and applied
     unchanged to the real one, so a floor miss on the real population is the
     definition of variant (b), not a failure. Their floor CPR at 8% is
     recorded and summarized as a diagnostic (this is the first measurement of
     how far the frozen anchor misses the floor it was built to hit, per seed).

EX-ANTE VERDICT PARTITION (fixed here BEFORE any result is seen; keyed to the
committed VII.D bands of cross_design_test.PREREGISTRATION: >50% undercuts the
paradigm reading, 10-35% corroborates it, 35-50% ambiguous. Applied to the
LEG-A RECALIBRATED 50-seed MEAN. T1's boundary is inclusive (>= 50) as
instructed; cross_design_test.classify uses strict > at 50, a measure-zero
difference recorded here so the two cannot be conflated.)
  T1: mean >= 50 -> the undercut verdict SURVIVES seed averaging. The
      manuscript keeps VII.D's reading but must quote the 50-seed mean and
      band beside 59.3% wherever 59.3% appears, because the quoted number is
      then a draw from a distribution, not an estimate.
  T2: 35 <= mean < 50 -> the undercut verdict becomes AMBIGUOUS on the
      paper's own pre-committed partition. VII.D must say so explicitly, the
      abstract's 59.3% must carry the mean and band, and the "undercuts"
      language must be withdrawn to the ambiguous band.
  T3: mean < 35 -> the undercut was a seed artifact; VII.D reverts to
      corroborating the paradigm reading and every site quoting 59.3%
      requalifies.
  S1 (THE POINT OF THIS RUN — falsifier of tex line 72). The committed
      calibration swing at fixed seed 42 is 59.30299434493775 -
      20.856293209339483 = 38.44670113559827 points. The sentence "the
      operative uncertainty is calibration, not seed noise" is FALSE as
      written if the leg-A RECALIBRATED 95% seed band (p97.5 - p2.5) is at
      least HALF that swing, i.e. >= 19.223350567799134 points — at half the
      calibration swing seed noise is the same order as calibration and cannot
      be called non-operative. Normal-theory equivalent, the SD threshold the
      spec is required to name: SD >= 38.44670113559827 x 0.5 / (2 x 1.959964)
      = 4.904006073435653 points. The empirical band width is the primary
      statistic; the SD is reported against its threshold as the named
      equivalent. For calibration, the tex's own contrast implies a ratio of
      7.0/38.4 = 0.18 (production ABM 10-17% band vs the 20.9-59.3% swing, on
      a different basis), and the sibling monte_carlo SD is 3.247 points on
      this benchmark — i.e. S1 is set well ABOVE the dispersion the existing
      evidence would predict, deliberately, so that firing it means something.
  S1b (weaker, disclosure-forcing): if the leg-A recalibrated band width is
      >= 20% of the swing (>= 7.689340227119654 points, itself wider than the
      7.0-point band the sentence's own evidence rests on; SD equivalent
      1.9616024293742613), then the sentence must at minimum carry the
      cross-design seed band explicitly, and "single-choice swings span
      20.9--59.3%" must be replaced by the seed-aware swing emitted below as
      seed_aware_calibration_swing_pp = [p2.5(frozen), p97.5(recalibrated)].
      On the existing evidence S1b is EXPECTED to fire; that expectation is
      recorded here so it cannot be read as a post-hoc threshold.
  S2 (verdict fragility): per-seed labels come from the committed
      cross_design_test.classify. If fewer than 90% of leg-A recalibrated
      seeds carry the same label as the leg-A mean, the pre-committed verdict
      is seed-fragile and the manuscript must report the band-crossing shares
      (the fraction of seeds landing in each committed band).
  S3 (atypical draw): if the committed seed-42 value (59.30299434493775) lies
      outside the interquartile range [p25, p75] of the leg-A recalibrated
      distribution, the manuscript must disclose that 59.3% is an atypical
      draw and lead with the mean and band.
  No further discretion is exercised after the run. The frozen leg is reported
  symmetrically for every statistic, but no verdict is keyed to it: the
  committed thresholds are keyed to the recalibrated primary.

OUTPUT (no committed artifact is written; G0d proves it)
  abm/data/cross_design_seeds_results.json                — the artifact
  abm/data/cross_design_seeds/per_seed_progress.csv       — per-cell checkpoint,
      rewritten after every cell so a halt or crash preserves the rows
  abm/data/cross_design_seeds/surface_<leg>_<variant>.csv — scratch surface,
      REUSED (overwritten) at every seed: 6 such files, not 300, so the sweep
      costs ~2MB of disk instead of ~60MB. Per-cell surfaces are therefore
      NOT retained; the cell's scored quantities in the artifact are.
  abm/data/cross_design_seeds/surface_parity_<variant>_seed42.csv and
      surface_determinism_{1,2}.csv — the two parity surfaces and the G5
      repeat pair, preserved under distinct names for audit.
  All of abm/data/cross_design_seeds/ is regenerable and not committed. The
  committed cached surfaces cross_design_test.py writes
  (abm/abm_cpr_surface_freddie_{recalibrated,frozen}.csv) are never opened for
  writing here and are never consulted for reading either: every cell builds
  its own surface.

RUNTIME (estimated ex ante, printed at start). Evidence: the committed
cross_design_reweight_results.json records runtime_s 15.553569583 for a run
containing 6 fresh 3,380-node single-cohort surface builds plus their scoring,
about 5 binary floor searches of <= 30 single-point engine evaluations, three
75k-parquet reads and the live FRED/SOMA fetches — so a surface build plus its
compute_metrics scoring is order 1.5s and a floor search order 0.5s on this
machine. Counting units precisely: 3 legs x 50 seeds = 150 (leg, seed) pairs,
each = 2 scored cells (recalibrated + frozen) = 2 surface builds + 1 floor
search ~ 3.5s, so 300 scored cells ~ 9 minutes, plus 50 unscored leg-D searches
(~30s), the two parity cells and the seed-7 determinism repeat pair (the sweep
recomputes leg-A seed 7 once more, by design: the parity cell is reused but the
determinism pair is not). Expect 8-20 minutes end-to-end; the
single-cohort 3,380-node surface is an order of magnitude smaller than the
11-cohort 37,180-node production surface, which is why this is minutes rather
than hours. Deliberately NOT accelerated by grid restriction (see SCOPE).

NETWORK DEPENDENCY (explicit): fed.fetch_data() pulls five FRED series
(WSHOMCB, MORTGAGE30US, ACTLISCOUUS, UMCSENT, DSPIC96) with no local cache,
fed.fetch_soma_mbs_monthly() pulls the NY Fed SOMA summary endpoint, and
abm.fetch_macro_from_fred() pulls MEHOINUSA672N / MSPUS (reported only, never
used — the calibration inputs are pinned to the frozen manifest). All are
fetched ONCE and shared across all 300 scored cells. A FRED revision, a new
observation inside the QT-active window, or a SOMA endpoint change moves the
$764.7B benchmark and trips G3b, which HALTS the run by design; an unreachable
SOMA endpoint (fetch returns None) also HALTS, because the benchmark cannot be
reproduced from the WSHOMCB fallback.

Run:  cd abm && python3 cross_design_seeds.py
"""
from __future__ import annotations

import contextlib
import hashlib
import inspect
import io
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import abm_lockin_simulation as abm
import cross_design_test as cdt
import fed_mbs_extension_risk as fed
from freddie_population import (
    attach_freddie_covariates,
    load_freddie_structural_sample,
)
from paths import ABM_DIR, LATEST_RUN_MANIFEST, RUNS_DIR

DATA_DIR = ABM_DIR / "data"
OUT_DIR = DATA_DIR / "cross_design_seeds"
RESULTS_JSON = DATA_DIR / "cross_design_seeds_results.json"
PROGRESS_CSV = OUT_DIR / "per_seed_progress.csv"

CROSS_DESIGN_JSON = DATA_DIR / "cross_design_results.json"
REWEIGHT_JSON = DATA_DIR / "cross_design_reweight_results.json"
EXTERNAL_GATES_JSON = DATA_DIR / "abm_external_gates_results.json"
SURFACE_RECAL_CSV = ABM_DIR / "abm_cpr_surface_freddie_recalibrated.csv"
SURFACE_FROZEN_CSV = ABM_DIR / "abm_cpr_surface_freddie_frozen.csv"

# Files this run must leave byte-identical (G0d: sha256 at start == at end).
WATCHED_PATHS = (SURFACE_RECAL_CSV, SURFACE_FROZEN_CSV, CROSS_DESIGN_JSON,
                 REWEIGHT_JSON, EXTERNAL_GATES_JSON)
# Provenance echo at spec time (recorded, NOT gated — see G0d).
SPEC_TIME_SHA256 = {
    "abm_cpr_surface_freddie_recalibrated.csv":
        "c2a69e85ec6f2f22501fc2a4fc59929e8c3efddf182ee4f8cf8789d2782501ce",
    "abm_cpr_surface_freddie_frozen.csv":
        "28fca7cde1ad3dfe0b5fcde1d9f8f2b1693621aed4ca4bc39dd9fdec49d76937",
}

REFERENCE_RUN_TAG = "run-2026-07-05-berger"

# --- committed cross-design values (quoted ex ante; asserted at runtime) ----
COMMITTED = {
    "recalibrated": {"mobility_scale": 36085.9375,
                     "trapped_b": 453.5186133616682,
                     "share_pct": 59.30299434493775},
    "frozen": {"mobility_scale": 43882.8125,
               "trapped_b": 159.49813800542833,
               "share_pct": 20.856293209339483},
    "empirical_trapped_b": 764.7482532227002,
}
COMMITTED_PREREG = {"undercuts_paradigm_above_pct": 50.0,
                    "corroborates_band_pct": [10.0, 35.0]}
# The two values tools/liveness_gates.py pins in the round-21 reweight gate.
COMMITTED_REWEIGHT_PINS = {"v1_recalibrated": 59.30299434493775,
                           "v2_reweighted_frozen": 12.561542534955805}
# Sibling 50-seed context (abm/monte_carlo_results.csv; synthetic population,
# behavioral layer only, calibration never varied).
MONTE_CARLO_SD_B = 24.834907519213886
MONTE_CARLO_MEAN_B = 96.6791545521707

# --- seed design (ex ante) --------------------------------------------------
SEEDS = tuple(range(50))          # matches monte_carlo_simulation.py [0, 50)
COMMITTED_SEED = 42               # inside SEEDS: leg A's parity cell
DETERMINISM_SEED = 7              # G5 repeat cell
LEGS = ("A_joint", "B_behavioral", "C_covariate")
VARIANTS = ("recalibrated", "frozen")

# --- gate tolerances (ex ante) ---------------------------------------------
QUOTE_TOL = 1e-9                  # G0a/G0b/G2 committed quotes
PARITY_TOL = 1e-9                 # G3a share_pct and trapped_b
EMPIRICAL_TOL_B = 0.05            # G3b benchmark reproduction
MAX_FLAGGED_FRACTION = 0.20       # G6 halt threshold

# --- III.C floor-search convention (production anchor semantics) -----------
FLOOR_RATE = 0.08
FLOOR_BAND = (0.04, 0.05)
FLOOR_SEARCH_LO, FLOOR_SEARCH_HI, FLOOR_SEARCH_ITERS = 1_000.0, 500_000.0, 30

# --- ex-ante interpretive thresholds ---------------------------------------
T1_MIN_PCT = 50.0                 # inclusive, as instructed
T2_MIN_PCT = 35.0
Z95 = 1.959963984540054
CAL_SWING_PP = (COMMITTED["recalibrated"]["share_pct"]
                - COMMITTED["frozen"]["share_pct"])          # 38.44670113559827
S1_BAND_FRACTION = 0.50
S1B_BAND_FRACTION = 0.20
S1_BAND_MIN_PP = S1_BAND_FRACTION * CAL_SWING_PP             # 19.223350567799134
S1B_BAND_MIN_PP = S1B_BAND_FRACTION * CAL_SWING_PP           # 7.689340227119654
S1_SD_MIN_PP = S1_BAND_MIN_PP / (2 * Z95)                    # 4.904006073435653
S1B_SD_MIN_PP = S1B_BAND_MIN_PP / (2 * Z95)                  # 1.9616024293742613 (2*Z95, not the rounded 3.92)
S2_MIN_CONCORDANCE = 0.90
THRESHOLD_TEXT = {
    "T1": ("leg-A recalibrated 50-seed mean >= 50% -> the undercut verdict "
           "survives seed averaging; VII.D's reading stands but the 50-seed "
           "mean and band must be quoted beside 59.3% wherever it appears."),
    "T2": ("35% <= mean < 50% -> the verdict becomes AMBIGUOUS on the paper's "
           "own pre-committed partition; VII.D must say so, the abstract's "
           "59.3% must carry the mean and band, and 'undercuts' is withdrawn."),
    "T3": ("mean < 35% -> the undercut was a seed artifact; VII.D reverts to "
           "corroborating the paradigm reading and every site quoting 59.3% "
           "requalifies."),
    "S1": (f"tex line 72 ('the operative uncertainty is calibration, not seed "
           f"noise') is FALSE if the leg-A recalibrated 95% seed band width "
           f">= {S1_BAND_MIN_PP:.12f}pp (= 50% of the committed "
           f"{CAL_SWING_PP:.12f}pp calibration swing); named SD equivalent "
           f">= {S1_SD_MIN_PP:.12f}pp."),
    "S1b": (f"if the band width >= {S1B_BAND_MIN_PP:.12f}pp (20% of the swing; "
            f"SD equivalent {S1B_SD_MIN_PP:.12f}pp) the sentence must carry "
            f"the cross-design seed band explicitly and '20.9--59.3%' must be "
            f"replaced by seed_aware_calibration_swing_pp."),
    "S2": (f"if fewer than {S2_MIN_CONCORDANCE:.0%} of leg-A recalibrated "
           f"seeds carry the same cross_design_test.classify label as the "
           f"mean, the verdict is seed-fragile and the band-crossing shares "
           f"must be reported."),
    "S3": ("if 59.30299434493775 lies outside [p25, p75] of the leg-A "
           "recalibrated distribution, the manuscript must disclose that "
           "59.3% is an atypical draw and lead with the mean and band."),
}


# ---------------------------------------------------------------------------
# Gate plumbing (cross_design_reweight convention): HALT with a GATE_FAILURE
# artifact before any downstream quantity is produced or interpreted. The
# per-cell checkpoint CSV survives the halt, so a late gate failure never
# discards the sweep.
# ---------------------------------------------------------------------------
GATES: dict = {}


def gate_fail(gate: str, detail: dict) -> None:
    RESULTS_JSON.write_text(json.dumps(
        {"status": "GATE_FAILURE", "gate": gate, "detail": detail,
         "gates_so_far": GATES,
         "checkpoint_csv": str(PROGRESS_CSV),
         "generated_utc": datetime.now(timezone.utc).isoformat()},
        indent=2, default=str) + "\n")
    raise SystemExit(f"{gate} FAILURE — run halted before interpretation. "
                     f"Detail written to {RESULTS_JSON}; per-cell rows (if "
                     f"any) preserved in {PROGRESS_CSV}")


def check(gate: str, ok: bool, detail: dict, msg: str) -> None:
    GATES[gate] = {"pass": bool(ok), "detail": detail, "msg": msg}
    print(f"{gate}: {msg} [{'PASS' if ok else 'FAIL'}]")
    if not ok:
        gate_fail(gate, detail)


def numeric_gate(gate: str, got: float, want: float, tol: float,
                 msg: str) -> None:
    delta = abs(float(got) - float(want))
    check(gate, delta <= tol,
          {"got": float(got), "want": float(want), "delta": delta, "tol": tol},
          f"{msg}: got {got!r} want {want!r} (|d|={delta:.3e} <= {tol:.0e})")


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() \
        else "MISSING"


# ---------------------------------------------------------------------------
# Seeded restrictions of the committed builders. These exist ONLY because the
# committed helpers hard-pin seed 42 (cross_design_test._build_engine takes no
# seed; calibrate_mobility_scale_freddie and abm.calibrate_mobility_scale build
# default-seeded engines). G1/G2 assert they are exact restrictions at 42.
# ---------------------------------------------------------------------------
def build_engine_seeded(scale: float, income: float, home_value: float,
                        loans: pd.DataFrame,
                        seed: int) -> abm.HousingMarketEngine:
    """cross_design_test._build_engine with the behavioral seed threaded."""
    engine = abm.HousingMarketEngine(
        seed=seed,
        median_income=income,
        median_home_value=home_value,
        mobility_scale=scale,
    )
    attach_freddie_covariates(engine, loans)
    return engine


def calibrate_freddie_seeded(income: float, home_value: float,
                             loans: pd.DataFrame,
                             seed: int) -> tuple[float, float]:
    """calibrate_mobility_scale_freddie with the behavioral seed threaded:
    same band, same lo/hi, same iteration count, same mid rule, same order."""
    target_low, target_high = FLOOR_BAND
    target_mid = (target_low + target_high) / 2
    lo, hi = FLOOR_SEARCH_LO, FLOOR_SEARCH_HI
    scale, cpr = abm.MOBILITY_DESIRE_SCALE, float("nan")
    for _ in range(FLOOR_SEARCH_ITERS):
        scale = (lo + hi) / 2
        engine = build_engine_seeded(scale, income, home_value, loans, seed)
        cpr = engine.cpr_at(FLOOR_RATE, "US")
        if target_low <= cpr <= target_high:
            break
        if cpr < target_mid:
            lo = scale
        else:
            hi = scale
    return scale, cpr


def calibrate_synthetic_seeded(income: float, home_value: float,
                               cohort_rate: float, cohort_months: int,
                               seed: int) -> tuple[float, float]:
    """abm.calibrate_mobility_scale with the behavioral seed threaded."""
    target_low, target_high = FLOOR_BAND
    target_mid = (target_low + target_high) / 2
    lo, hi = FLOOR_SEARCH_LO, FLOOR_SEARCH_HI
    scale, cpr = abm.MOBILITY_DESIRE_SCALE, float("nan")
    for _ in range(FLOOR_SEARCH_ITERS):
        scale = (lo + hi) / 2
        engine = abm.HousingMarketEngine(
            seed=seed,
            median_income=income,
            median_home_value=home_value,
            mobility_scale=scale,
        )
        engine.attach_cohort(cohort_rate, cohort_months)
        cpr = engine.cpr_at(FLOOR_RATE, "US")
        if target_low <= cpr <= target_high:
            break
        if cpr < target_mid:
            lo = scale
        else:
            hi = scale
    return scale, cpr


ENGINE_ARRAYS = ("_monthly_income", "_home_values", "_desires", "_txn_offsets",
                 "_patience", "_current_payment", "_outstanding_us", "_n_rem")


# ---------------------------------------------------------------------------
# Production scoring path (cross_design_test.run_variant's pipeline, with the
# surface written to this run's scratch directory instead of the committed
# per-variant cache, and caches never consulted).
# ---------------------------------------------------------------------------
def build_and_score(engine: abm.HousingMarketEngine, loans: pd.DataFrame,
                    df0: pd.DataFrame, soma_rolloff: pd.Series,
                    csv_path: Path) -> dict:
    surf = engine.build_cpr_surface()
    surf.to_csv(csv_path, index=False)
    surface = fed.load_cpr_surface(csv_path)
    sched = cdt._population_sched_series(df0.index, loans)
    df = fed.compute_metrics(
        df0.copy(),
        surface=surface,
        soma_rolloff=soma_rolloff,
        use_burnout=False,
        apply_settlement_lag_kernel=True,
        sched_smm_override=sched,
    )
    m = fed.export_headline_metrics(df)
    qt = fed.qt_active_frame(df)
    xcorr = fed.cpr_cross_correlation(qt["Empirical_CPR_Pct"],
                                      qt["US_CPR_Pct"])
    best_lag = max(xcorr, key=lambda k: abs(xcorr[k])) if xcorr else 0
    d = m["dollars_b"]
    return {
        "trapped_b": d["us_trapped"],
        "share_pct": d["share_explained_pct"],
        "empirical_trapped_b": d["empirical_trapped"],
        "us_cpr_mean_pct": m["cpr_pct"]["us_abm"]["mean"],
        "empirical_cpr_mean_pct": m["cpr_pct"]["empirical"]["mean"],
        "n_surface_nodes": int(len(surf)),
        "cpr_r_lag0": xcorr.get(0),
        "peak_lag": best_lag,
        "peak_lag_r": xcorr.get(best_lag),
    }


def run_cell(leg: str, variant: str, seed: int, behavioral_seed: int,
             covariate_seed: int, populations: dict, frozen_scale: float,
             income: float, home_value: float, df0: pd.DataFrame,
             soma_rolloff: pd.Series, csv_path: Path,
             quiet: bool = True) -> dict:
    """One (leg, variant, seed) cell: scale -> engine -> surface -> score."""
    t0 = time.perf_counter()
    loans = populations[covariate_seed]
    sink = io.StringIO()
    ctx = contextlib.redirect_stdout(sink) if quiet \
        else contextlib.nullcontext()
    with ctx:
        if variant == "recalibrated":
            # the floor the search converged to, exactly as
            # calibrate_mobility_scale_freddie reports it
            scale, floor_cpr = calibrate_freddie_seeded(
                income, home_value, loans, behavioral_seed)
            engine = build_engine_seeded(scale, income, home_value, loans,
                                         behavioral_seed)
        else:
            scale = frozen_scale
            engine = build_engine_seeded(scale, income, home_value, loans,
                                         behavioral_seed)
            # diagnostic only (G6 does not gate the frozen leg): how far the
            # frozen anchor misses the floor it was built to hit, per seed.
            # _cpr_vec/_movers_mask are pure reads, so querying the scoring
            # engine is bit-identical to querying a fresh one.
            floor_cpr = engine.cpr_at(FLOOR_RATE, "US")
        scored = build_and_score(engine, loans, df0, soma_rolloff, csv_path)
    row = {
        "leg": leg,
        "variant": variant,
        "seed": int(seed),
        "behavioral_seed": int(behavioral_seed),
        "covariate_seed": int(covariate_seed),
        "mobility_scale": float(scale),
        "floor_cpr_at_8pct": float(floor_cpr),
        "floor_in_band": bool(FLOOR_BAND[0] <= floor_cpr <= FLOOR_BAND[1]),
        "floor_gated": variant == "recalibrated",
        "population_wac_pct": float(loans["coupon"].mean() * 100.0),
        "population_mean_age_mo": float(loans["loan_age"].mean()),
        **scored,
        "classification": cdt.classify(scored["share_pct"]),
        "cell_runtime_s": time.perf_counter() - t0,
    }
    print(f"  [{leg:>13} {variant:>13} seed {seed:>2}] scale "
          f"{scale:>12,.4f}  floor {floor_cpr:6.2%}"
          f"{'' if row['floor_in_band'] else ' *OUT*'}  trapped "
          f"${row['trapped_b']:8.2f}B  share {row['share_pct']:7.3f}%  "
          f"({row['cell_runtime_s']:.1f}s)")
    return row


# ---------------------------------------------------------------------------
# Statistics (methods fixed ex ante: numpy.percentile linear interpolation,
# SD with ddof=1, 95% CI of the mean at z = 1.959963984540054)
# ---------------------------------------------------------------------------
PCTS = (2.5, 25.0, 50.0, 75.0, 97.5)


def stats_block(rows: list, committed_share: float,
                floor_gated: bool) -> dict:
    shares = np.array([r["share_pct"] for r in rows], dtype=float)
    trapped = np.array([r["trapped_b"] for r in rows], dtype=float)
    scales = np.array([r["mobility_scale"] for r in rows], dtype=float)
    q = {f"p{p}": float(np.percentile(shares, p)) for p in PCTS}
    sd = float(shares.std(ddof=1))
    mean = float(shares.mean())
    sem = sd / np.sqrt(len(shares))
    labels = [r["classification"] for r in rows]
    mean_label = cdt.classify(mean)
    floors = np.array([r["floor_cpr_at_8pct"] for r in rows], dtype=float)
    kept = [r for r in rows if r["floor_in_band"]] if floor_gated else rows
    kept_shares = np.array([r["share_pct"] for r in kept], dtype=float)
    return {
        "n": int(len(shares)),
        "mean_pct": mean,
        "sd_pct": sd,
        "sem_pct": float(sem),
        "ci95_of_mean_pct": [mean - Z95 * sem, mean + Z95 * sem],
        "percentiles_pct": q,
        "min_pct": float(shares.min()),
        "max_pct": float(shares.max()),
        "band_width_p2p5_p97p5_pp": q["p97.5"] - q["p2.5"],
        "iqr_pct": [q["p25.0"], q["p75.0"]],
        "mean_trapped_b": float(trapped.mean()),
        "sd_trapped_b": float(trapped.std(ddof=1)),
        "mobility_scale": {"mean": float(scales.mean()),
                           "sd": float(scales.std(ddof=1)),
                           "min": float(scales.min()),
                           "max": float(scales.max())},
        "committed_seed42_pct": committed_share,
        "committed_seed42_percentile_rank":
            float((shares <= committed_share).mean() * 100.0),
        "committed_seed42_inside_iqr":
            bool(q["p25.0"] <= committed_share <= q["p75.0"]),
        "mean_classification": mean_label,
        "label_counts": {lab: int(labels.count(lab)) for lab in sorted(
            set(labels))},
        "concordance_with_mean_label":
            float(sum(1 for lab in labels if lab == mean_label) / len(labels)),
        "floor_gated": bool(floor_gated),
        "floor_cpr_at_8pct": {"mean": float(floors.mean()),
                              "min": float(floors.min()),
                              "max": float(floors.max())},
        "n_floor_flagged": (int(len(rows) - len(kept)) if floor_gated
                            else None),
        "excluding_flagged": (
            None if not floor_gated or len(kept) == len(rows)
            or len(kept) < 2 else {
                "n": int(len(kept_shares)),
                "mean_pct": float(kept_shares.mean()),
                "sd_pct": float(kept_shares.std(ddof=1)),
                "band_width_pp": float(np.percentile(kept_shares, 97.5)
                                       - np.percentile(kept_shares, 2.5)),
            }),
    }


def classify_mean(mean_pct: float) -> tuple[str, str]:
    if mean_pct >= T1_MIN_PCT:
        return "T1", THRESHOLD_TEXT["T1"]
    if mean_pct >= T2_MIN_PCT:
        return "T2", THRESHOLD_TEXT["T2"]
    return "T3", THRESHOLD_TEXT["T3"]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    t0 = time.perf_counter()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print(" CROSS-DESIGN SEEDS — the seed distribution of the 59.3%/20.9% pair")
    print("=" * 72)
    print("Runtime estimate (printed ex ante): 3 legs x 50 seeds x 2 variants "
          "= 300\ncell-scores on the single-cohort 3,380-node surface, plus 50 "
          "unscored\ncalibration-anchor searches. Evidence: the committed "
          "cross_design_reweight\nrun did 6 surface builds + ~5 floor searches "
          "+ live fetches in 15.55s, so a\nsurface+score is order 1.5s and a "
          "search order 0.5s. Expect 8-20 minutes.\nGrids are NOT restricted "
          "(parity-safe). Per-cell rows are checkpointed to\n"
          f"{PROGRESS_CSV} after every cell.\n")

    # =======================================================================
    # G0 — committed state, constants, and no-overwrite baseline
    # =======================================================================
    start_sha = {p.name: sha256_of(p) for p in WATCHED_PATHS}
    print("Watched committed files (sha256 recorded for G0d):")
    for name, sha in start_sha.items():
        echo = SPEC_TIME_SHA256.get(name)
        note = "" if echo is None else (
            " == spec-time" if echo == sha else " != spec-time (recorded only)")
        print(f"  {name}: {sha[:16]}…{note}")

    cd = json.loads(CROSS_DESIGN_JSON.read_text())
    g0a = {}
    for var in ("recalibrated", "frozen"):
        for field in ("mobility_scale", "trapped_b", "share_pct"):
            g0a[f"{var}.{field}"] = abs(cd["variants"][var][field]
                                        - COMMITTED[var][field])
    g0a["empirical_trapped_b"] = abs(
        cd["variants"]["recalibrated"]["empirical_trapped_b"]
        - COMMITTED["empirical_trapped_b"])
    prereg_ok = (
        cd["preregistration"]["undercuts_paradigm_above_pct"]
        == COMMITTED_PREREG["undercuts_paradigm_above_pct"]
        and list(cd["preregistration"]["corroborates_band_pct"])
        == COMMITTED_PREREG["corroborates_band_pct"]
    )
    check("G0a_committed_quotes",
          max(g0a.values()) < QUOTE_TOL and prereg_ok,
          {"deltas": g0a, "prereg_ok": prereg_ok,
           "artifact": str(CROSS_DESIGN_JSON)},
          "cross_design_results.json reproduces the quoted committed values "
          "and the VII.D bands this run's thresholds are keyed to")

    rw = json.loads(REWEIGHT_JSON.read_text())
    # Tolerances mirror the round-21 cross-design-reweight gate (#76) in
    # tools/liveness_gates.py exactly: 1e-9 on cv["v1_recalibrated"], 1e-6 on
    # cv["v2_reweighted_frozen"]. Referenced by gate name, not line number:
    # that file moves under parallel round-22 edits.
    g0b = {k: abs(rw["variants"][k]["share_pct"] - v)
           for k, v in COMMITTED_REWEIGHT_PINS.items()}
    g0b_ok = (g0b["v1_recalibrated"] < 1e-9
              and g0b["v2_reweighted_frozen"] < 1e-6)
    check("G0b_liveness_pins_intact", g0b_ok,
          {"deltas": g0b, "tolerances": {"v1_recalibrated": 1e-9,
                                         "v2_reweighted_frozen": 1e-6},
           "artifact": str(REWEIGHT_JSON)},
          "cross_design_reweight_results.json still carries the values the "
          "round-21 liveness gate pins (59.30299434493775 / "
          "12.561542534955805); this run never writes that file")

    latest = json.loads(LATEST_RUN_MANIFEST.read_text())
    manifest = json.loads(
        (RUNS_DIR / REFERENCE_RUN_TAG / "manifest.json").read_text())
    pipe = manifest["pipeline"]
    lib_seed_default = (inspect.signature(load_freddie_structural_sample)
                        .parameters["seed"].default)
    g0c_ok = (
        latest.get("run_tag") == REFERENCE_RUN_TAG
        and abm.RNG_SEED == 42
        and abm.N_HOUSEHOLDS == 10000
        and lib_seed_default == 42
        and abs(abm.DTI_MAX - 0.43) < 1e-15
        and abs(abm.WAIT_AND_SEE_PROB - 0.20) < 1e-15
        and abs(abm.WAIT_AND_SEE_RATE_THRESHOLD - 0.015) < 1e-15
        and abs(pipe["mobility_scale"]
                - COMMITTED["frozen"]["mobility_scale"]) < QUOTE_TOL
        and abs(float(pipe["median_income"]) - 83730.0) < 1e-9
        and abs(float(pipe["median_home_value"]) - 403200.0) < 1e-9
    )
    check("G0c_production_constants", g0c_ok,
          {"latest_tag": latest.get("run_tag"), "rng_seed": abm.RNG_SEED,
           "n_households": abm.N_HOUSEHOLDS,
           "freddie_sample_default_seed": lib_seed_default,
           "dti_max": abm.DTI_MAX, "manifest_scale": pipe["mobility_scale"],
           "manifest_medians": [pipe["median_income"],
                                pipe["median_home_value"]]},
          f"constants + {REFERENCE_RUN_TAG!r} manifest tag + frozen scale + "
          "pinned medians 83,730/403,200")

    income = float(pipe["median_income"])
    home_value = float(pipe["median_home_value"])
    man_ref = pipe["reference_cohort"]
    try:
        live_income, live_home = abm.fetch_macro_from_fred()
    except Exception:
        live_income = live_home = None
    print(f"Pinned manifest medians: income ${income:,.0f}, home "
          f"${home_value:,.0f} (live FRED: {live_income}, {live_home}; "
          "reported, never used)")

    # =======================================================================
    # G1 / G2 — the seeded builders are exact restrictions at seed 42
    # =======================================================================
    print("\nLoading the committed seed-42 covariate draw (library call) …")
    populations = {COMMITTED_SEED: load_freddie_structural_sample(
        abm.N_HOUSEHOLDS, seed=COMMITTED_SEED)}
    pop42 = populations[COMMITTED_SEED]

    ref_scale = COMMITTED["frozen"]["mobility_scale"]
    sink = io.StringIO()
    with contextlib.redirect_stdout(sink):
        eng_lib = cdt._build_engine(ref_scale, income, home_value, pop42)
        eng_mine = build_engine_seeded(ref_scale, income, home_value, pop42,
                                       COMMITTED_SEED)
    mismatched = [a for a in ENGINE_ARRAYS
                  if not np.array_equal(getattr(eng_lib, a),
                                        getattr(eng_mine, a))]
    check("G1_builder_equivalence", not mismatched,
          {"arrays_checked": list(ENGINE_ARRAYS),
           "mismatched": mismatched, "scale": ref_scale},
          "seeded builder at seed 42 bit-equals cross_design_test._build_engine "
          f"on all {len(ENGINE_ARRAYS)} population arrays")

    print("\nReproducing the committed recalibrated scale (freddie anchor) …")
    with contextlib.redirect_stdout(sink):
        lib_recal = cdt.calibrate_mobility_scale_freddie(income, home_value,
                                                         pop42)
        mine_recal, mine_recal_floor = calibrate_freddie_seeded(
            income, home_value, pop42, COMMITTED_SEED)
    numeric_gate("G2a_freddie_search_vs_library", mine_recal, lib_recal, 0.0,
                 "seeded freddie floor search == library search at seed 42")
    numeric_gate("G2b_freddie_search_vs_committed", mine_recal,
                 COMMITTED["recalibrated"]["mobility_scale"], QUOTE_TOL,
                 "recalibrated scale == committed 36,085.9375")
    print("Reproducing the committed frozen scale (production anchor) …")
    with contextlib.redirect_stdout(sink):
        lib_frozen = abm.calibrate_mobility_scale(
            income, home_value,
            cohort_rate=float(man_ref["coupon"]),
            cohort_months=int(man_ref["months_elapsed"]))
        mine_frozen, mine_frozen_floor = calibrate_synthetic_seeded(
            income, home_value, float(man_ref["coupon"]),
            int(man_ref["months_elapsed"]), COMMITTED_SEED)
    numeric_gate("G2c_synthetic_search_vs_library", mine_frozen, lib_frozen,
                 0.0, "seeded synthetic search == abm.calibrate_mobility_scale "
                      "at seed 42")
    numeric_gate("G2d_synthetic_search_vs_committed", mine_frozen,
                 COMMITTED["frozen"]["mobility_scale"], QUOTE_TOL,
                 "frozen scale == committed 43,882.8125")
    print(f"  seed-42 search floors at 8% market: freddie "
          f"{mine_recal_floor:.4%}, synthetic {mine_frozen_floor:.4%} "
          f"(band {FLOOR_BAND[0]:.0%}-{FLOOR_BAND[1]:.0%})")
    frozen_scale = lib_frozen

    # =======================================================================
    # Macro frames (production fetch path, fetched once, shared by all cells)
    # =======================================================================
    print("\nFetching macro data (production fetch path, once) …")
    df0 = fed.fetch_data()
    soma_rolloff = fed.fetch_soma_mbs_monthly()
    if soma_rolloff is None:
        gate_fail("G3_precondition",
                  {"reason": "SOMA monthly rolloff unavailable; the $764.7B "
                             "benchmark cannot be reproduced from the WSHOMCB "
                             "fallback, so no parity gate can be evaluated"})

    # =======================================================================
    # G3 — SCORE PARITY at leg A / seed 42 (run FIRST; licenses everything)
    # =======================================================================
    print("\n" + "=" * 72)
    print(" G3 — parity cell (leg A, seed 42 = the committed configuration)")
    print("=" * 72)
    rows: list = []
    parity_rows = {}
    for variant in VARIANTS:
        parity_rows[variant] = run_cell(
            "A_joint", variant, COMMITTED_SEED, COMMITTED_SEED,
            COMMITTED_SEED, populations, frozen_scale, income, home_value,
            df0, soma_rolloff,
            OUT_DIR / f"surface_parity_{variant}_seed42.csv", quiet=False)
        rows.append(parity_rows[variant])
        pd.DataFrame(rows).to_csv(PROGRESS_CSV, index=False)

    numeric_gate("G3b_benchmark",
                 parity_rows["recalibrated"]["empirical_trapped_b"],
                 COMMITTED["empirical_trapped_b"], EMPIRICAL_TOL_B,
                 "benchmark reproduction (upstream FRED/SOMA revision guard)")
    for variant in VARIANTS:
        numeric_gate(f"G3a_{variant}_share_pct",
                     parity_rows[variant]["share_pct"],
                     COMMITTED[variant]["share_pct"], PARITY_TOL,
                     f"{variant} share bit-parity")
        numeric_gate(f"G3a_{variant}_trapped_b",
                     parity_rows[variant]["trapped_b"],
                     COMMITTED[variant]["trapped_b"], PARITY_TOL,
                     f"{variant} trapped bit-parity")

    # =======================================================================
    # G5 — determinism repeat (leg A, seed 7, recalibrated, twice)
    # =======================================================================
    print("\nG5 determinism repeat (leg A, seed 7, recalibrated, twice) …")
    populations.setdefault(DETERMINISM_SEED, load_freddie_structural_sample(
        abm.N_HOUSEHOLDS, seed=DETERMINISM_SEED))
    det_a = run_cell("A_joint", "recalibrated", DETERMINISM_SEED,
                     DETERMINISM_SEED, DETERMINISM_SEED, populations,
                     frozen_scale, income, home_value, df0, soma_rolloff,
                     OUT_DIR / "surface_determinism_1.csv")
    det_b = run_cell("A_joint", "recalibrated", DETERMINISM_SEED,
                     DETERMINISM_SEED, DETERMINISM_SEED, populations,
                     frozen_scale, income, home_value, df0, soma_rolloff,
                     OUT_DIR / "surface_determinism_2.csv")
    det_keys = ("mobility_scale", "floor_cpr_at_8pct", "trapped_b",
                "share_pct")
    det_diffs = {k: abs(det_a[k] - det_b[k]) for k in det_keys}
    check("G5_determinism", max(det_diffs.values()) == 0.0,
          {"run1": {k: det_a[k] for k in det_keys},
           "run2": {k: det_b[k] for k in det_keys}, "diffs": det_diffs},
          f"seed-{DETERMINISM_SEED} cell executed twice: bit-identical "
          f"(share {det_a['share_pct']:.9f}%)")

    # =======================================================================
    # THE SWEEP — 3 legs x 50 seeds x 2 variants
    # =======================================================================
    print("\n" + "=" * 72)
    print(f" SWEEP — legs {LEGS} x {len(SEEDS)} seeds x {VARIANTS}")
    print("=" * 72)
    for leg in LEGS:
        for seed in SEEDS:
            behavioral_seed = COMMITTED_SEED if leg == "C_covariate" else seed
            covariate_seed = COMMITTED_SEED if leg == "B_behavioral" else seed
            if covariate_seed not in populations:
                with contextlib.redirect_stdout(io.StringIO()):
                    populations[covariate_seed] = \
                        load_freddie_structural_sample(abm.N_HOUSEHOLDS,
                                                       seed=covariate_seed)
            for variant in VARIANTS:
                if leg == "A_joint" and seed == COMMITTED_SEED:
                    continue  # the parity cell already IS this cell
                rows.append(run_cell(
                    leg, variant, seed, behavioral_seed, covariate_seed,
                    populations, frozen_scale, income, home_value, df0,
                    soma_rolloff,
                    OUT_DIR / f"surface_{leg}_{variant}.csv"))
                pd.DataFrame(rows).to_csv(PROGRESS_CSV, index=False)

    # =======================================================================
    # Leg D — the calibration anchor's own seed dispersion (unscored)
    # =======================================================================
    print("\nLeg D — calibration-anchor seed sweep (unscored, "
          f"{len(SEEDS)} synthetic searches) …")
    anchor_rows = []
    for seed in SEEDS:
        with contextlib.redirect_stdout(io.StringIO()):
            sc, fl = calibrate_synthetic_seeded(
                income, home_value, float(man_ref["coupon"]),
                int(man_ref["months_elapsed"]), seed)
        anchor_rows.append({"seed": int(seed), "frozen_anchor_scale": float(sc),
                            "floor_cpr_at_8pct": float(fl),
                            "floor_in_band": bool(FLOOR_BAND[0] <= fl
                                                  <= FLOOR_BAND[1])})
    anchor_scales = np.array([r["frozen_anchor_scale"] for r in anchor_rows])
    print(f"  frozen anchor across seeds: mean {anchor_scales.mean():,.1f}, "
          f"sd {anchor_scales.std(ddof=1):,.1f}, "
          f"min {anchor_scales.min():,.1f}, max {anchor_scales.max():,.1f} "
          f"(committed {COMMITTED['frozen']['mobility_scale']:,.4f})")

    # =======================================================================
    # G4 — leg identity at seed 42, and G6 — floor retention
    # =======================================================================
    def cell(leg: str, variant: str, seed: int) -> dict:
        return next(r for r in rows if r["leg"] == leg
                    and r["variant"] == variant and r["seed"] == seed)

    g4_detail, g4_ok = {}, True
    for leg in ("B_behavioral", "C_covariate"):
        for variant in VARIANTS:
            got, want = cell(leg, variant, COMMITTED_SEED), parity_rows[variant]
            d = {k: abs(got[k] - want[k])
                 for k in ("mobility_scale", "trapped_b", "share_pct")}
            g4_detail[f"{leg}.{variant}"] = d
            g4_ok = g4_ok and max(d.values()) == 0.0
    check("G4_leg_identity_at_seed42", g4_ok, g4_detail,
          "legs B and C at seed 42 recompute the parity cell exactly "
          "(scale, trapped, share all delta 0.0)")

    flagged = {}
    for leg in LEGS:
        for variant in VARIANTS:
            sub = [r for r in rows if r["leg"] == leg
                   and r["variant"] == variant]
            bad = [r["seed"] for r in sub if not r["floor_in_band"]]
            flagged[f"{leg}.{variant}"] = {
                "gated": variant == "recalibrated",
                "n_flagged": len(bad), "fraction": len(bad) / len(sub),
                "seeds": bad,
                "floor_cpr_mean": float(np.mean(
                    [r["floor_cpr_at_8pct"] for r in sub])),
            }
    worst = max(v["fraction"] for v in flagged.values() if v["gated"])
    check("G6_floor_retention", worst <= MAX_FLAGGED_FRACTION, flagged,
          f"recalibrated floor-band flagged fraction {worst:.1%} <= "
          f"{MAX_FLAGGED_FRACTION:.0%} (flagged seeds reported, retained in "
          "the primary distribution; frozen cells not gated by construction)")

    # =======================================================================
    # Distributions + ex-ante verdicts (no discretion beyond this point)
    # =======================================================================
    dists = {}
    for leg in LEGS:
        for variant in VARIANTS:
            sub = sorted((r for r in rows if r["leg"] == leg
                          and r["variant"] == variant),
                         key=lambda r: r["seed"])
            dists[f"{leg}.{variant}"] = stats_block(
                sub, COMMITTED[variant]["share_pct"],
                floor_gated=(variant == "recalibrated"))

    primary = dists["A_joint.recalibrated"]
    band, verdict = classify_mean(primary["mean_pct"])
    band_width = primary["band_width_p2p5_p97p5_pp"]
    sd_pp = primary["sd_pct"]
    s1_false = band_width >= S1_BAND_MIN_PP
    s1_false_sd_equiv = sd_pp >= S1_SD_MIN_PP
    s1b = band_width >= S1B_BAND_MIN_PP
    s2_fragile = primary["concordance_with_mean_label"] < S2_MIN_CONCORDANCE
    s3_atypical = not primary["committed_seed42_inside_iqr"]
    seed_aware_swing = [
        dists["A_joint.frozen"]["percentiles_pct"]["p2.5"],
        dists["A_joint.recalibrated"]["percentiles_pct"]["p97.5"],
    ]

    var_a = dists["A_joint.recalibrated"]["sd_pct"] ** 2
    var_b = dists["B_behavioral.recalibrated"]["sd_pct"] ** 2
    var_c = dists["C_covariate.recalibrated"]["sd_pct"] ** 2
    decomposition = {
        "note": ("attribution diagnostic only; no threshold or verdict rides "
                 "on it (declared ex ante)"),
        "recalibrated": {
            "var_joint_pp2": var_a,
            "var_behavioral_pp2": var_b,
            "var_covariate_pp2": var_c,
            "var_b_plus_c_pp2": var_b + var_c,
            "additivity_ratio_joint_over_sum":
                (None if (var_b + var_c) == 0 else var_a / (var_b + var_c)),
            "behavioral_share_of_sum":
                (None if (var_b + var_c) == 0 else var_b / (var_b + var_c)),
        },
        "frozen": {
            "var_joint_pp2": dists["A_joint.frozen"]["sd_pct"] ** 2,
            "var_behavioral_pp2": dists["B_behavioral.frozen"]["sd_pct"] ** 2,
            "var_covariate_pp2": dists["C_covariate.frozen"]["sd_pct"] ** 2,
        },
    }

    end_sha = {p.name: sha256_of(p) for p in WATCHED_PATHS}
    changed = [k for k in start_sha if start_sha[k] != end_sha[k]]
    check("G0d_no_overwrite", not changed,
          {"start": start_sha, "end": end_sha, "changed": changed},
          "committed cross-design surfaces and artifacts byte-identical after "
          "the run")

    runtime_s = time.perf_counter() - t0
    cell_times = np.array([r["cell_runtime_s"] for r in rows])
    report = {
        "mode": "cross_design_seeds",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "spec": (
            "Seed distribution of the un-reweighted cross-design pair: both "
            "randomization layers varied (behavioral HousingMarketEngine seed "
            "and the balance-weighted 10k-of-75k covariate subsample seed) "
            "over seeds 0-49, the seed set of monte_carlo_simulation.py; legs "
            "A joint (primary) / B behavioral-only / C covariate-only, each x "
            "{recalibrated (III.C floor search re-run per seed), frozen "
            "(committed 43,882.8125 held fixed)}, plus leg D the calibration "
            "anchor's own seed dispersion (unscored); production scoring path "
            "and $764.7482532227002B benchmark untouched; full 3,380-node "
            "surfaces, grids not restricted; parity gates G0-G6 with leg-A "
            "seed-42 replaying 59.30299434493775 / 20.856293209339483 to "
            "1e-9; ex-ante verdicts T1/T2/T3 on the leg-A recalibrated mean "
            "and S1/S1b/S2/S3 on its dispersion; the composition-reweighted "
            "quartet (76.3/12.6/70.6/36.0) and the 150.6% external-gate "
            "variant are NOT re-seeded and inherit this dispersion only as a "
            "disclosed proxy"
        ),
        "pinned": {
            "committed_cross_design": COMMITTED,
            "committed_prereg_bands": COMMITTED_PREREG,
            "committed_reweight_liveness_pins": COMMITTED_REWEIGHT_PINS,
            "reference_run_tag": REFERENCE_RUN_TAG,
            "manifest_medians": {"income": income, "home_value": home_value},
            "manifest_reference_cohort": man_ref,
            "live_fred_medians_reported_only": [live_income, live_home],
            "watched_sha256_start": start_sha,
            "watched_sha256_end": end_sha,
            "spec_time_sha256_echo": SPEC_TIME_SHA256,
            "monte_carlo_sibling": {
                "artifact": "abm/monte_carlo_results.csv",
                "mean_trapped_b": MONTE_CARLO_MEAN_B,
                "sd_trapped_b": MONTE_CARLO_SD_B,
                "sd_as_pp_of_benchmark":
                    MONTE_CARLO_SD_B / COMMITTED["empirical_trapped_b"] * 100.0,
                "note": ("behavioral layer only, synthetic population, "
                         "calibration never varied; different design, quoted "
                         "for calibration of the S1 threshold only"),
            },
        },
        "design": {
            "seeds": list(SEEDS),
            "legs": {
                "A_joint": "behavioral seed = covariate seed = s (PRIMARY)",
                "B_behavioral": "behavioral seed = s, covariate seed = 42",
                "C_covariate": "behavioral seed = 42, covariate seed = s",
                "D_anchor": ("calibrate_mobility_scale re-searched at each "
                             "behavioral seed; scales only, unscored"),
            },
            "variants": {
                "recalibrated": ("III.C floor search per seed: 4-5% CPR floor "
                                 "at 8% market rate, zero velocity, static 7% "
                                 "friction, lo/hi 1,000/500,000, 30 iters"),
                "frozen": ("committed production scale held fixed at every "
                           "seed (the definition of frozen)"),
            },
            "share_basis": ("fed.export_headline_metrics dollars_b "
                            "share_explained_pct vs $764.7482532227002B — the "
                            "basis of the quoted 59.3/20.9/76.3/12.6, NOT the "
                            "shared accounting basis of the 13.6% ABM row"),
            "statistics": ("numpy.percentile linear interpolation; SD ddof=1; "
                           "95% CI of the mean at z=1.959963984540054"),
        },
        "parity_gates": GATES,
        "parity_gates_all_pass": all(g["pass"] for g in GATES.values()),
        "per_cell": rows,
        "parity_cell": parity_rows,
        "determinism_repeat": [det_a, det_b],
        "distributions": dists,
        "calibration_anchor_seed_sweep": {
            "rows": anchor_rows,
            "committed_anchor": COMMITTED["frozen"]["mobility_scale"],
            "mean": float(anchor_scales.mean()),
            "sd": float(anchor_scales.std(ddof=1)),
            "min": float(anchor_scales.min()),
            "max": float(anchor_scales.max()),
            "n_floor_flagged": int(sum(1 for r in anchor_rows
                                       if not r["floor_in_band"])),
        },
        "variance_decomposition": decomposition,
        "floor_flag_summary": flagged,
        "tex_line72_test": {
            "claim": ("the operative uncertainty is calibration, not seed "
                      "noise (single-choice swings span 20.9--59.3%)"),
            "site": "paper/v18/revised_paper_v18.tex line 72 (tab:headline)",
            "committed_calibration_swing_pp": CAL_SWING_PP,
            "leg_a_recalibrated_band_width_pp": band_width,
            "leg_a_recalibrated_sd_pp": sd_pp,
            "s1_band_threshold_pp": S1_BAND_MIN_PP,
            "s1_sd_threshold_pp": S1_SD_MIN_PP,
            "s1b_band_threshold_pp": S1B_BAND_MIN_PP,
            "s1b_sd_threshold_pp": S1B_SD_MIN_PP,
            "s1_claim_false": bool(s1_false),
            "s1_claim_false_on_sd_equivalent": bool(s1_false_sd_equiv),
            "s1b_must_report_band": bool(s1b),
            "seed_noise_to_calibration_ratio": band_width / CAL_SWING_PP,
            "seed_aware_calibration_swing_pp": seed_aware_swing,
        },
        "verdict": {
            "applied_to": "distributions['A_joint.recalibrated'].mean_pct",
            "mean_pct": primary["mean_pct"],
            "band": band,
            "text": verdict,
            "s2_seed_fragile": bool(s2_fragile),
            "s2_concordance": primary["concordance_with_mean_label"],
            "s3_committed_draw_atypical": bool(s3_atypical),
            "s3_committed_percentile_rank":
                primary["committed_seed42_percentile_rank"],
            "thresholds": THRESHOLD_TEXT,
        },
        "runtime_s": runtime_s,
        "cell_runtime_s": {"n": int(len(cell_times)),
                           "mean": float(cell_times.mean()),
                           "total": float(cell_times.sum())},
    }
    RESULTS_JSON.write_text(json.dumps(
        report, indent=2,
        default=lambda x: float(x) if hasattr(x, "item") else str(x)) + "\n")

    print("\n" + "=" * 72)
    print(" CROSS-DESIGN SEEDS — RESULTS")
    print("=" * 72)
    for key in ("A_joint.recalibrated", "A_joint.frozen",
                "B_behavioral.recalibrated", "C_covariate.recalibrated"):
        s = dists[key]
        print(f" {key:<26} mean {s['mean_pct']:7.3f}%  sd {s['sd_pct']:6.3f}pp"
              f"  [p2.5 {s['percentiles_pct']['p2.5']:7.3f}, p97.5 "
              f"{s['percentiles_pct']['p97.5']:7.3f}]  width "
              f"{s['band_width_p2p5_p97p5_pp']:6.3f}pp")
    print(f"\n committed seed-42 recalibrated draw 59.303% sits at the "
          f"{primary['committed_seed42_percentile_rank']:.1f}th percentile "
          f"of leg A (inside IQR: {primary['committed_seed42_inside_iqr']})")
    print(f" band label counts (leg A recalibrated): {primary['label_counts']}")
    print(f"\n verdict [{band}]: {verdict}")
    print(f" S1  tex-line-72 claim FALSE: {s1_false}  "
          f"(band {band_width:.3f}pp vs threshold {S1_BAND_MIN_PP:.3f}pp; "
          f"sd {sd_pp:.3f}pp vs {S1_SD_MIN_PP:.3f}pp)")
    print(f" S1b must report the seed band: {s1b}  "
          f"(threshold {S1B_BAND_MIN_PP:.3f}pp); seed-aware swing "
          f"[{seed_aware_swing[0]:.2f}, {seed_aware_swing[1]:.2f}]%")
    print(f" S2  verdict seed-fragile: {s2_fragile}  "
          f"(concordance {primary['concordance_with_mean_label']:.2f})")
    print(f" S3  committed draw atypical: {s3_atypical}")
    print(f"\n gates all pass: {report['parity_gates_all_pass']}   "
          f"runtime {runtime_s:,.0f}s   report saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
