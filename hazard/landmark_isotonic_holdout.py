#!/usr/bin/env python3
"""
Round-17 R17-D: LMISO-style isotonic recalibration of the frozen Path A
spec v4 holdout predictions (referee E1 / Q3; the peng2026 landmarking-and-
recalibration strand engaged at Section II).

SPEC (committed before execution; interpretation thresholds ex ante)
--------------------------------------------------------------------

PURPOSE
  Reviewer note (round 17, E1/M1/DC7/Q3): the paper "stops short of testing
  richer survival learners" — asks for a landmarked discrete-time hazard
  with explicit probability recalibration (LMISO, peng2026) and a deep
  multinomial transition model (sadhwani2021).  The deep multinomial half
  remains DECLINED on data grounds of record (no loan-month records in the
  repo; the 826M-row Fannie ingest was external and headline-stats-only by
  ratified license posture; see ml_comparator_holdout_results.json
  declined_scope and TECHNICAL.md §26.3) — that decline is prose, not this
  run.  What IS deliverable at the paper's own unit of analysis is the
  recalibration half: fit a single exposure-weighted isotonic map
  (predicted cell CPR -> observed cell CPR) on the 2023 inner-validation
  year ONLY — the same train-side year the committed hyperparameter
  protocol of ml_comparator_holdout.py used, so no post-2023 information
  enters the map — and apply it to the FROZEN spec v4 predictions on the
  IDENTICAL pre-committed 2024+ holdout (6,077 cells), scored ONCE under
  the identical target, weighting, and RMSE definitions.  Path A is
  already excluded from headline figures by pre-committed spec (paper tex
  line 328), so NO outcome of this run can move a headline; the run
  answers whether a monotone level-recalibration fit in the training
  regime transfers across the 2024 boundary.

DECLINED IN-SPEC: the rolling/expanding-window landmark variant
  A vanhouwelingen2007/putter2022-style landmarking exercise — monthly
  refits (or re-recalibrations) at each of the 21 holdout landmarks — is
  DECLINED here as a DIFFERENT PROTOCOL, not executed: at post-2024
  landmarks the map would be fit on post-2024 information, making it a
  disclosed rolling-origin evaluation that cannot be read against the
  frozen single-split reference numbers (37.90 / 3.04 pp).  It could only
  sit alongside, never replace, the pre-committed split; it is out of
  scope for this run.  This run is the STATIC variant only.

INPUTS
  hazard/data/cohort_month_panel.parquet      committed Freddie cohort-month
    (config.PANEL_PATH)                       cell panel (22,709 raw cells)
  hazard/data/runs/run-2026-07-14-pathA-seasonal/hazard_coefficients.json
                                              frozen Path A spec v4 artifact
  hazard/data/hazard_coefficients_specv3.json frozen spec v3 artifact
  hazard/data/pathA_v4_holdout_results.json   committed holdout reference
                                              (source of the G1-G4 values)
  Live FRED via fredapi (WSHOMCB, MORTGAGE30US, ACTLISCOUUS, UMCSENT),
  FRED_API_KEY resolved by common/fred_key.py (env var or repo .env) —
  the same enrich_panel_with_macro call Path A uses.  If the network fetch
  fails the run ABORTS nonzero with a clear message; there is no cached
  fallback.  The NY Fed SOMA fetch used by the scorer paths elsewhere is
  NOT part of the Path A holdout machinery and is not called here.

CONSTRUCTION (deterministic, step by step)
  1. Panel prep is pathA_v4_holdout's pipeline verbatim, retaining the
     train side (ml_comparator_holdout.load_splits copied unchanged):
     pl.read_parquet(PANEL_PATH) -> enrich_panel_with_macro ->
     dropna(rate_gap_bps, exposure, loan_age, stratum_id) -> exposure > 0
     -> prepay_rate = (events/exposure).clip(0, 1).  Split at
     config.HOLDOUT_DATE (2024-01-01): train = period <, holdout =
     period >=.  Expected sizes: train 10,176, holdout 6,077 (the frozen
     artifacts' recorded counts).
  2. Parity BEFORE the map is fit: pathA_v4_holdout.score_frozen —
     imported, not reimplemented — scores both frozen coefficient
     artifacts through this panel and must reproduce the committed holdout
     numbers (gates G1-G4), proving identical split + metric.
  3. Per-cell predictions: score_frozen returns aggregate metrics only and
     hard-aborts unless the scored frame has exactly the artifact's
     n_holdout, so it CANNOT emit the per-cell 2023 predictions the map
     needs.  predict_frozen_hazard below therefore mirrors score_frozen's
     design/prediction block line for line (same hazard_fit helpers, same
     sm.add_constant, same coefficient ordering and asserts, same
     exp(clip(X@params, -20, 0)) hazard) with the n gate removed.  Gate
     G6 closes the divergence risk: the locally predicted holdout hazards,
     scored through cell_metrics, must reproduce score_frozen's spec v4
     unweighted RMSE, exposure-weighted RMSE, and R2 to <= 1e-9 pp before
     the map is fit.  (cell_metrics' [0,1] hazard clip is a no-op on
     exp(<=0); G6 verifies this numerically.)
  4. Calibration set = the 2023 inner-validation year of the committed
     hyperparameter protocol: train cells with period >= 2023-01-01
     (INNER_SPLIT_DATE, same constant as ml_comparator_holdout).  Expected
     n = 3,473, verified read-only at spec time: the raw panel has exactly
     3,337 / 3,366 / 3,473 cells in 2021/2022/2023 (sum 10,176 = the
     frozen n_train, so the rate_gap_bps dropna keeps all of 2021+; the
     exposure > 0 filter never binds because enrich clips exposure to
     >= 1).  Gate G7: n_calibration == 3,473 exactly, calibration periods
     all in calendar 2023 with 12 distinct months, and
     n_inner_train + n_calibration == n_train.
  5. Target / units / metrics, identical to the template for everything
     scored here: y = per-cell monthly prepayment intensity prepay_rate;
     sample_weight = exposure (UPB dollars, clip lower=1 from enrich);
     predicted hazard clipped to [0, 1]; annualized CPR pp =
     hazard * 12 * 100; obs_cpr = prepay_rate * 12 * 100;
     rmse_unweighted_pp = sqrt(mean(sq)); rmse_weighted_pp =
     sqrt(sum(w*sq)/sum(w)), w = exposure; r2_unweighted =
     1 - SS_res/SS_tot — bit-for-bit the score_frozen formulas
     (cell_metrics copied unchanged from ml_comparator_holdout).
  6. The map: sklearn.isotonic.IsotonicRegression(increasing=True,
     out_of_bounds="clip"), fit with x = frozen spec v4 predicted monthly
     hazard on the 2023 calibration cells, y = observed prepay_rate,
     sample_weight = exposure.  Units note, fixed ex ante: this IS the
     roadmap's "predicted cell CPR -> observed cell CPR" map expressed in
     the scorer's native monthly-hazard units — annualized CPR pp is the
     same fixed positive rescaling (x 1200) of BOTH axes, isotonic
     regression depends on x only through its ordering (which the
     rescaling preserves), and the fitted values rescale exactly; fitting
     in hazard units lets the recalibrated predictions flow through
     cell_metrics unchanged.  No y_min/y_max: PAVA fitted values are
     exposure-weighted means of y in [0, 1], so outputs stay in [0, 1] by
     construction (gate G8 checks anyway).  out_of_bounds="clip": holdout
     predictions outside the 2023 predicted range map to the boundary
     calibration values.
  7. Application, once: recalibrated_hazard =
     iso.predict(frozen v4 holdout hazard from step 3); scored a single
     time through cell_metrics on the 6,077-cell holdout.  The holdout is
     touched exactly once, after the map is frozen; no iteration, no
     selection, no grid.
  8. Recorded diagnostics (non-decisive): the calibration set's in-sample
     exposure-weighted RMSE before and after recalibration; map summary
     stats (n thresholds, x/y ranges in hazard and CPR pp units).
  9. Determinism: PAVA is deterministic; no RNG anywhere; no wall-clock
     enters the artifact.  /usr/bin/python3 3.9, pandas 2.3.3,
     numpy 2.0.2, polars parquet read (repo convention), sklearn 1.6.1.

GATES (all must PASS before the artifact is written; nonzero exit and NO
artifact otherwise.  G1-G7 run before the map is fit.)
  G1  v4 parity, unweighted:        |got - 37.903228802264934| <= 0.01 pp
      (reference: pathA_v4_holdout_results.json spec_v4.rmse_unweighted_pp)
  G2  v4 parity, exposure-weighted: |got - 3.037942336998421|  <= 0.01 pp
      (same source, spec_v4.rmse_exposure_weighted_pp)
  G3  v3 parity, unweighted:        |got - 37.8295321331|      <= 0.01 pp
      (same source spec_v3_reference; equals the specv3 artifact's own
      holdout_rmse and ridge_reference_weighting.json alpha_0.0001)
  G4  v3 parity, exposure-weighted: |got - 2.5338262679523766| <= 0.01 pp
      (same source, spec_v3_reference.rmse_exposure_weighted_pp)
  G5  split integrity: n_holdout == 6,077 and n_train == 10,176, each
      equal to the values recorded in BOTH frozen coefficient artifacts
      (exact equality).
  G6  local-prediction parity: predict_frozen_hazard's holdout scoring
      reproduces score_frozen's spec v4 unweighted RMSE, exposure-weighted
      RMSE, and R2, each to <= 1e-9 (pp / units).
  G7  calibration-set integrity: n_calibration == 3,473 exactly; all
      calibration periods in calendar 2023; 12 distinct periods;
      n_inner_train + n_calibration == n_train.
  G8  recalibrated-prediction sanity: every recalibrated holdout hazard
      finite and inside [0, 1]; map non-degenerate is NOT required (a
      constant map is a legitimate outcome and is reported as-is).
  Input-integrity assert (before G1): the reference artifact on disk must
  still carry the exact values quoted in G1-G4 (|diff| <= 1e-12);
  reference drift aborts with a clear message.

PRE-COMMITTED INTERPRETATION (all three outcomes fixed ex ante; the run is
reported whichever occurs; no post-hoc reframing.  Stated ex ante: NO
outcome moves any headline — Path A is excluded from headline figures by
pre-committed spec (tex line 328), and the paper's calibrated-
counterfactual (Path B) claims do not rest on Path A OOS accuracy.)
  Primary metric: exposure-weighted holdout RMSE (pp).  Thresholds on the
  frozen reference 3.037942336998421 pp, fixed here ex ante:
    material improvement  iff rmse_weighted_pp < 0.80 * ref = 2.430354 pp
      (>= 20% improvement; the same 0.80 factor as ml_comparator_holdout)
    material degradation  iff rmse_weighted_pp > 1.25 * ref = 3.797428 pp
      (1.25 = 1/0.80, the ratio-symmetric counterpart, fixed ex ante)
    no material change    otherwise (the [0.80x, 1.25x] band).
  Secondary, recorded but non-decisive: the same 0.80x / 1.25x rules on
  unweighted RMSE vs 37.903228802264934 pp — this is where recalibration
  vs cross-cell prediction is read, exactly as in the ml-comparator run.
  Outcome A ("recalibration_helps_no_headline_change"): the 2023-fit
    monotone map transfers across the 2024 boundary well enough to
    materially improve the exposure-weighted RMSE.  A level-recalibration
    carries no new covariate information, so, as with the HGB result, any
    gain is recalibration of the high-exposure cells unless the secondary
    unweighted RMSE and R2 also move materially.  No headline moves.
  Outcome B ("no_material_change"): the map neither helps nor hurts
    materially — the 2023 calibration level does not transfer usefully to
    the 2024+ regime, consistent with the regime-drift diagnosis and the
    Theil U2 > 1 result.  No headline moves.
  Outcome C ("recalibration_hurts"): the 2023-fit map materially worsens
    the exposure-weighted RMSE — direct evidence that the level
    relationship itself shifted across the boundary (the map mis-corrects
    in the new regime).  Reported as-is; strengthens the disclosed-weak
    treatment of Path A.  No headline moves.

OUTPUT
  hazard/data/landmark_isotonic_results.json, keys:
    mode, spec, holdout_definition, panel_sha256, input_sha256,
    n_train, n_holdout, n_calibration,
    pathA_reference {rmse_unweighted_pp, rmse_weighted_pp, r2_unweighted,
                     source},
    parity {spec_v4, spec_v3},
    gates {G1..G8 with got/want/tol/pass},
    isotonic_recalibration {rmse_unweighted_pp, rmse_weighted_pp,
      r2_unweighted, protocol, calibration_map {n_thresholds, x/y ranges
      in hazard and CPR pp units}, calibration_fit_diagnostics},
    interpretation {primary_metric, material_improvement_frac,
                    material_degradation_frac, thresholds, verdicts,
                    overall_verdict, reading, no_headline_ex_ante},
    declined_scope.
  Headline stats only; no per-cell vectors, no threshold arrays.

LICENSE / PROVENANCE
  Cell-panel-derived headline statistics only; no loan-level data touched
  or shipped.  The panel is the committed in-repo Freddie cohort-month
  panel; the isotonic map adds no data provenance.  The declined
  sadhwani2021-class loan-level comparator and the declined rolling-
  landmark protocol are prose/spec matters, not part of this run.

Run:  cd hazard && python3 landmark_isotonic_holdout.py
Runtime estimate: seconds after the live FRED fetch (one PAVA fit on
3,473 cells; two frozen-design constructions).  Liveness gate #40 per
paper/v16/revision_roadmap_round17.md is recorded separately in
TECHNICAL.md after execution, not by this script.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
import statsmodels.api as sm
from sklearn.isotonic import IsotonicRegression

from config import AGE_SPLINE_KNOTS, HOLDOUT_DATE, PANEL_PATH
from hazard_fit import (
    MONTH_COLS,
    _age_spline_basis,
    _burnout_orthogonalized,
    _month_dummy_matrix,
    _stratum_dummy_matrix,
    enrich_panel_with_macro,
)
from pathA_v4_holdout import V3_COEFS, V4_COEFS, score_frozen

DATA_DIR = Path(__file__).parent / "data"
REFERENCE_JSON = DATA_DIR / "pathA_v4_holdout_results.json"
OUT = DATA_DIR / "landmark_isotonic_results.json"

# ---- spec constants (fixed ex ante; sources quoted in the header) ----------
V4_UNWEIGHTED_PP = 37.903228802264934
V4_WEIGHTED_PP = 3.037942336998421
V4_R2_UNWEIGHTED = -0.011428527641577979
V3_UNWEIGHTED_PP = 37.8295321331
V3_WEIGHTED_PP = 2.5338262679523766
PARITY_TOL_PP = 0.01
REFERENCE_DRIFT_TOL = 1e-12
LOCAL_PARITY_TOL = 1e-9
N_TRAIN_EXPECTED = 10_176
N_HOLDOUT_EXPECTED = 6_077
N_CALIBRATION_EXPECTED = 3_473

INNER_SPLIT_DATE = pd.Timestamp("2023-01-01")  # same as ml_comparator_holdout
MATERIAL_IMPROVEMENT_FRAC = 0.80
MATERIAL_DEGRADATION_FRAC = 1.25  # = 1/0.80, ratio-symmetric, ex ante

HAZARD_TO_CPR_PP = 12 * 100  # the fixed positive rescaling of both map axes


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_splits() -> tuple[pd.DataFrame, pd.DataFrame]:
    """pathA_v4_holdout.load_holdout's pipeline verbatim, keeping train too."""
    panel = pl.read_parquet(PANEL_PATH)
    try:
        pdf = enrich_panel_with_macro(panel)
    except Exception as exc:  # no silent fallback, per spec
        raise SystemExit(
            f"ABORT: live macro fetch failed ({exc!r}). This run requires "
            "FRED via fredapi (FRED_API_KEY from env or repo .env); there is "
            "no cached fallback by spec."
        )
    pdf = pdf.dropna(subset=["rate_gap_bps", "exposure", "loan_age", "stratum_id"])
    pdf = pdf[pdf["exposure"] > 0]
    pdf["prepay_rate"] = (pdf["events"] / pdf["exposure"]).clip(0, 1)
    train = pdf[pdf["period"] < HOLDOUT_DATE].copy()
    holdout = pdf[pdf["period"] >= HOLDOUT_DATE].copy()
    return train, holdout


def cell_metrics(pred_hazard: np.ndarray, cells: pd.DataFrame) -> dict:
    """score_frozen's metric formulas, applied to a predicted hazard vector."""
    pred_cpr = np.clip(pred_hazard, 0.0, 1.0) * 12 * 100
    obs_cpr = cells["prepay_rate"].to_numpy() * 12 * 100
    w = cells["exposure"].to_numpy(dtype=float)
    sq = (obs_cpr - pred_cpr) ** 2
    ss_tot = float(((obs_cpr - obs_cpr.mean()) ** 2).sum())
    return {
        "rmse_unweighted_pp": float(np.sqrt(sq.mean())),
        "rmse_weighted_pp": float(np.sqrt((w * sq).sum() / w.sum())),
        "r2_unweighted": float(1 - sq.sum() / ss_tot),
    }


def predict_frozen_hazard(cells: pd.DataFrame, artifact: Path) -> np.ndarray:
    """Per-cell monthly hazard from a frozen coefficient artifact.

    score_frozen's design/prediction block, mirrored line for line (same
    hazard_fit helpers, same coefficient ordering and asserts, same
    exp(clip(X@params, -20, 0))), with score_frozen's n_holdout abort
    removed so the 2023 calibration cells can be scored.  Gate G6 verifies
    this path reproduces score_frozen's holdout metrics to <= 1e-9."""
    art = json.loads(artifact.read_text())
    spec_version = int(art.get("spec_version", 3))
    seasonal = spec_version >= 4
    coefs = art["coefficients"]

    age = _age_spline_basis(cells["loan_age"].to_numpy(), AGE_SPLINE_KNOTS)
    burn_demean = cells["burnout"].to_numpy() - cells["stratum_id"].map(
        art["stratum_burnout_mean"]).fillna(0).to_numpy()
    burn = _burnout_orthogonalized(burn_demean, age, art["burnout_age_adjust"])
    stratum = _stratum_dummy_matrix(
        cells["stratum_id"], art["reference_stratum"], art["fe_columns"])
    blocks = [
        age,
        (cells["rate_gap_bps"].to_numpy() - art["rate_gap_bps_mean"])
        / art["rate_gap_bps_std"],
        burn / art["burnout_demean_std"],
        (cells["friction"].to_numpy() - art["friction_mean"])
        / art["friction_std"],
    ]
    names = (
        ["age_linear"]
        + [f"age_spline_{k}" for k in AGE_SPLINE_KNOTS]
        + ["rate_gap_bps", "burnout_orth", "friction"]
    )
    if seasonal:
        blocks.append(_month_dummy_matrix(cells["period"]))
        names += MONTH_COLS
    blocks.append(stratum)
    names += art["fe_columns"]
    X = np.column_stack(blocks)
    X = np.asarray(sm.add_constant(X, has_constant="add"), dtype=np.float64)
    names = ["const"] + names

    missing = [n for n in names if n not in coefs]
    assert not missing, (
        f"{artifact.name}: design columns missing from stored coefficients: "
        f"{missing[:5]}"
    )
    assert len(names) == len(coefs), (
        f"{artifact.name}: {len(names)} design columns vs "
        f"{len(coefs)} stored coefficients"
    )
    params = np.array([coefs[n] for n in names], dtype=np.float64)
    return np.exp(np.clip(X.dot(params), -20, 0))


# ---- gates ------------------------------------------------------------------

def gate(name: str, got: float, want: float, tol: float) -> dict:
    ok = abs(got - want) <= tol
    print(f"[GATE] {name}: got {got:.10f}  want {want:.10f}  "
          f"tol {tol}  {'PASS' if ok else 'FAIL'}")
    return {"got": got, "want": want, "tol": tol, "pass": bool(ok)}


def main() -> None:
    # Input-integrity assert: the on-disk reference must match the spec quotes.
    ref = json.loads(REFERENCE_JSON.read_text())
    for got, want, label in [
        (ref["spec_v4"]["rmse_unweighted_pp"], V4_UNWEIGHTED_PP, "v4 unweighted"),
        (ref["spec_v4"]["rmse_exposure_weighted_pp"], V4_WEIGHTED_PP, "v4 weighted"),
        (ref["spec_v3_reference"]["rmse_unweighted_pp"], V3_UNWEIGHTED_PP, "v3 unweighted"),
        (ref["spec_v3_reference"]["rmse_exposure_weighted_pp"], V3_WEIGHTED_PP, "v3 weighted"),
    ]:
        if abs(got - want) > REFERENCE_DRIFT_TOL:
            raise SystemExit(
                f"ABORT: reference artifact drift on {label}: file has {got!r}, "
                f"spec quotes {want!r}. Re-examine before running."
            )

    train, holdout = load_splits()
    print(f"Train cells (period < {HOLDOUT_DATE.date()}): {len(train):,}  |  "
          f"Holdout cells: {len(holdout):,}")

    # ---- G5 split integrity (before anything is scored) --------------------
    v3_art = json.loads(V3_COEFS.read_text())
    v4_art = json.loads(V4_COEFS.read_text())
    g5_ok = (
        len(holdout) == N_HOLDOUT_EXPECTED
        and len(train) == N_TRAIN_EXPECTED
        and all(int(a["n_holdout"]) == N_HOLDOUT_EXPECTED for a in (v3_art, v4_art))
        and all(int(a["n_train"]) == N_TRAIN_EXPECTED for a in (v3_art, v4_art))
    )
    g5 = {
        "n_train_got": len(train), "n_train_want": N_TRAIN_EXPECTED,
        "n_holdout_got": len(holdout), "n_holdout_want": N_HOLDOUT_EXPECTED,
        "frozen_artifacts_agree": bool(g5_ok), "pass": bool(g5_ok),
    }
    print(f"[GATE] G5 split integrity: train {len(train):,}/{N_TRAIN_EXPECTED:,} "
          f"holdout {len(holdout):,}/{N_HOLDOUT_EXPECTED:,} "
          f"{'PASS' if g5_ok else 'FAIL'}")
    if not g5_ok:
        sys.exit("G5 split-integrity failure — no map fit, no artifact.")

    # ---- G1-G4 parity: frozen artifacts through this panel, before the map -
    v4 = score_frozen(holdout, V4_COEFS)
    v3 = score_frozen(holdout, V3_COEFS)
    gates = {
        "G5_split_integrity": g5,
        "G1_v4_parity_unweighted": gate(
            "G1 v4 unweighted", v4["rmse_unweighted_pp"], V4_UNWEIGHTED_PP, PARITY_TOL_PP),
        "G2_v4_parity_weighted": gate(
            "G2 v4 weighted", v4["rmse_exposure_weighted_pp"], V4_WEIGHTED_PP, PARITY_TOL_PP),
        "G3_v3_parity_unweighted": gate(
            "G3 v3 unweighted", v3["rmse_unweighted_pp"], V3_UNWEIGHTED_PP, PARITY_TOL_PP),
        "G4_v3_parity_weighted": gate(
            "G4 v3 weighted", v3["rmse_exposure_weighted_pp"], V3_WEIGHTED_PP, PARITY_TOL_PP),
    }
    if not all(g["pass"] for g in gates.values()):
        sys.exit("Parity gate failure — split/metric not reproduced; "
                 "no map fit, no artifact.")

    # ---- G6 local-prediction parity (the map's inputs must equal the scorer)
    haz_v4_holdout = predict_frozen_hazard(holdout, V4_COEFS)
    local_m = cell_metrics(haz_v4_holdout, holdout)
    g6_checks = {
        "rmse_unweighted_pp": gate(
            "G6 local v4 unweighted", local_m["rmse_unweighted_pp"],
            v4["rmse_unweighted_pp"], LOCAL_PARITY_TOL),
        "rmse_weighted_pp": gate(
            "G6 local v4 weighted", local_m["rmse_weighted_pp"],
            v4["rmse_exposure_weighted_pp"], LOCAL_PARITY_TOL),
        "r2_unweighted": gate(
            "G6 local v4 r2", local_m["r2_unweighted"],
            v4["holdout_r2_unweighted"], LOCAL_PARITY_TOL),
    }
    g6_ok = all(c["pass"] for c in g6_checks.values())
    gates["G6_local_prediction_parity"] = {"checks": g6_checks, "pass": bool(g6_ok)}
    if not g6_ok:
        sys.exit("G6 local-prediction parity failure — the local prediction "
                 "path does not reproduce score_frozen; no map fit, no artifact.")

    # ---- G7 calibration-set integrity (the 2023 inner-validation year) -----
    inner_train = train[train["period"] < INNER_SPLIT_DATE]
    calib = train[train["period"] >= INNER_SPLIT_DATE]
    calib_periods = pd.to_datetime(calib["period"])
    g7_ok = (
        len(calib) == N_CALIBRATION_EXPECTED
        and len(inner_train) + len(calib) == len(train)
        and set(calib_periods.dt.year.unique()) == {2023}
        and calib_periods.nunique() == 12
    )
    g7 = {
        "n_calibration_got": len(calib),
        "n_calibration_want": N_CALIBRATION_EXPECTED,
        "n_inner_train": len(inner_train),
        "calibration_years": sorted(int(y) for y in calib_periods.dt.year.unique()),
        "n_distinct_periods_got": int(calib_periods.nunique()),
        "n_distinct_periods_want": 12,
        "pass": bool(g7_ok),
    }
    print(f"[GATE] G7 calibration-set integrity: n {len(calib):,}/"
          f"{N_CALIBRATION_EXPECTED:,}  periods {int(calib_periods.nunique())}/12 "
          f"in {g7['calibration_years']}  {'PASS' if g7_ok else 'FAIL'}")
    gates["G7_calibration_set_integrity"] = g7
    if not g7_ok:
        sys.exit("G7 calibration-set integrity failure — no map fit, no artifact.")

    # ---- the map: fit on 2023 only, apply once to the frozen holdout preds -
    print("Isotonic recalibration — exposure-weighted, 2023 calibration year "
          "only (train-side; no post-2023 information enters the map):")
    haz_v4_calib = predict_frozen_hazard(calib, V4_COEFS)
    iso = IsotonicRegression(increasing=True, out_of_bounds="clip")
    iso.fit(haz_v4_calib, calib["prepay_rate"].to_numpy(),
            sample_weight=calib["exposure"].to_numpy(dtype=float))

    calib_raw_m = cell_metrics(haz_v4_calib, calib)
    calib_recal_m = cell_metrics(iso.predict(haz_v4_calib), calib)
    n_thresholds = int(len(iso.X_thresholds_))
    print(f"  n_calib {len(calib):,}  thresholds {n_thresholds}  "
          f"x range [{float(iso.X_min_) * HAZARD_TO_CPR_PP:.4f}, "
          f"{float(iso.X_max_) * HAZARD_TO_CPR_PP:.4f}] CPR pp")
    print(f"  calib in-sample wRMSE (diagnostic, non-decisive): "
          f"raw {calib_raw_m['rmse_weighted_pp']:.4f}pp -> "
          f"recalibrated {calib_recal_m['rmse_weighted_pp']:.4f}pp")

    recal_haz = iso.predict(haz_v4_holdout)  # the holdout is touched ONCE
    g8_ok = bool(
        np.isfinite(recal_haz).all()
        and (recal_haz >= 0.0).all()
        and (recal_haz <= 1.0).all()
    )
    gates["G8_recalibrated_prediction_sanity"] = {
        "pred_min": float(recal_haz.min()), "pred_max": float(recal_haz.max()),
        "all_finite": bool(np.isfinite(recal_haz).all()), "pass": g8_ok,
    }
    print(f"[GATE] G8 recalibrated-prediction sanity: "
          f"[{recal_haz.min():.3e}, {recal_haz.max():.3e}] hazard "
          f"{'PASS' if g8_ok else 'FAIL'}")
    if not g8_ok:
        sys.exit("G8 recalibrated-prediction sanity failure — no artifact.")

    iso_metrics = cell_metrics(recal_haz, holdout)

    # ---- pre-committed interpretation ---------------------------------------
    threshold_w = MATERIAL_IMPROVEMENT_FRAC * V4_WEIGHTED_PP
    threshold_w_hurt = MATERIAL_DEGRADATION_FRAC * V4_WEIGHTED_PP
    threshold_u = MATERIAL_IMPROVEMENT_FRAC * V4_UNWEIGHTED_PP
    threshold_u_hurt = MATERIAL_DEGRADATION_FRAC * V4_UNWEIGHTED_PP

    def _band_verdict(got: float, lo: float, hi: float) -> str:
        if got < lo:
            return "material_improvement"
        if got > hi:
            return "material_degradation"
        return "no_material_change"

    verdicts = {
        "isotonic_recalibration": {
            "primary_weighted": _band_verdict(
                iso_metrics["rmse_weighted_pp"], threshold_w, threshold_w_hurt),
            "secondary_unweighted": _band_verdict(
                iso_metrics["rmse_unweighted_pp"], threshold_u, threshold_u_hurt),
        }
    }
    primary = verdicts["isotonic_recalibration"]["primary_weighted"]
    overall = {
        "material_improvement": "recalibration_helps_no_headline_change",
        "no_material_change": "no_material_change",
        "material_degradation": "recalibration_hurts",
    }[primary]
    no_headline = (
        "Ex ante: NO outcome of this run moves any headline — Path A is "
        "excluded from headline figures by pre-committed spec (tex line 328) "
        "and the calibrated-counterfactual (Path B) claims do not rest on "
        "Path A OOS accuracy."
    )
    reading = {
        "recalibration_helps_no_headline_change": (
            "The 2023-fit exposure-weighted isotonic map materially improves "
            "the frozen spec v4 exposure-weighted holdout RMSE (>= 20% by the "
            "ex-ante 0.80x threshold). A monotone level-recalibration carries "
            "no new covariate information, so the gain is recalibration of "
            "the high-exposure cells unless the secondary unweighted RMSE "
            "and R2 (recorded, non-decisive) also move materially. "
            + no_headline),
        "no_material_change": (
            "The 2023-fit exposure-weighted isotonic map leaves the frozen "
            "spec v4 exposure-weighted holdout RMSE inside the ex-ante "
            "[0.80x, 1.25x] no-material-change band: the training-regime "
            "calibration level does not transfer usefully across the 2024 "
            "boundary, consistent with the regime-drift diagnosis and the "
            "Theil U2 > 1 result. " + no_headline),
        "recalibration_hurts": (
            "The 2023-fit exposure-weighted isotonic map materially worsens "
            "the frozen spec v4 exposure-weighted holdout RMSE (> 1.25x, the "
            "ex-ante degradation threshold): the level relationship itself "
            "shifted across the 2024 boundary, so the map mis-corrects in "
            "the new regime — direct evidence for the disclosed-weak "
            "treatment of Path A. " + no_headline),
    }[overall]

    for name, m in (
        ("pathA v4 (frozen)", {
            "rmse_unweighted_pp": v4["rmse_unweighted_pp"],
            "rmse_weighted_pp": v4["rmse_exposure_weighted_pp"],
            "r2_unweighted": v4["holdout_r2_unweighted"]}),
        ("isotonic recalib", iso_metrics),
    ):
        print(f"{name:>18}: unweighted {m['rmse_unweighted_pp']:7.2f}pp  "
              f"weighted {m['rmse_weighted_pp']:6.3f}pp  "
              f"R2 {m['r2_unweighted']:+.4f}")
    print(f"Overall verdict: {overall}")

    payload = {
        "mode": "landmark_isotonic_holdout",
        "spec": ("round-17 R17-D LMISO-style isotonic recalibration of the "
                 "frozen Path A spec v4 holdout predictions; identical "
                 "temporal holdout, target, weighting, and RMSE definitions; "
                 "map fit on the 2023 inner-validation year only (train-side); "
                 "thresholds ex ante; static variant — the rolling/expanding-"
                 "window landmark protocol is declined in-spec"),
        "holdout_definition": (
            f"cohort-month cells with period >= {HOLDOUT_DATE.date()} from the "
            "production panel pipeline (hazard_fit split; identical to "
            "pathA_v4_holdout)"),
        "panel_sha256": _sha256(Path(PANEL_PATH)),
        "input_sha256": {
            "spec_v4_coefficients": _sha256(V4_COEFS),
            "spec_v3_coefficients": _sha256(V3_COEFS),
            "pathA_reference_artifact": _sha256(REFERENCE_JSON),
        },
        "n_train": int(len(train)),
        "n_holdout": int(len(holdout)),
        "n_calibration": int(len(calib)),
        "pathA_reference": {
            "rmse_unweighted_pp": V4_UNWEIGHTED_PP,
            "rmse_weighted_pp": V4_WEIGHTED_PP,
            "r2_unweighted": V4_R2_UNWEIGHTED,
            "source": "hazard/data/pathA_v4_holdout_results.json (spec_v4)",
        },
        "parity": {"spec_v4": v4, "spec_v3": v3},
        "gates": gates,
        "isotonic_recalibration": {
            **iso_metrics,
            "protocol": {
                "estimator": ("sklearn.isotonic.IsotonicRegression("
                              "increasing=True, out_of_bounds='clip'), "
                              "sklearn 1.6.1"),
                "fit_set": (f"train cells with period >= "
                            f"{INNER_SPLIT_DATE.date()} (the 2023 "
                            "inner-validation year of the committed "
                            "ml_comparator_holdout hyperparameter protocol; "
                            "no post-2023 information enters the map)"),
                "x": "frozen spec v4 predicted monthly hazard (predict-only)",
                "y": "observed prepay_rate",
                "sample_weight": "exposure (UPB dollars)",
                "units_note": (
                    "fit on the monthly-hazard scale; annualized CPR pp is "
                    "the same fixed positive rescaling (x 1200) of both "
                    "axes, so this is the predicted-cell-CPR -> "
                    "observed-cell-CPR map of the roadmap spec in the "
                    "scorer's native units — isotonic regression depends on "
                    "x only through its ordering and the fitted values "
                    "rescale exactly"),
                "application": (
                    "applied once to the frozen spec v4 predictions on the "
                    "identical pre-committed 2024+ holdout; scored once via "
                    "the template cell_metrics formulas; out-of-range "
                    "holdout predictions clip to boundary calibration "
                    "values"),
            },
            "calibration_map": {
                "n_thresholds": n_thresholds,
                "x_min_hazard": float(iso.X_min_),
                "x_max_hazard": float(iso.X_max_),
                "x_min_cpr_pp": float(iso.X_min_) * HAZARD_TO_CPR_PP,
                "x_max_cpr_pp": float(iso.X_max_) * HAZARD_TO_CPR_PP,
                "y_min_hazard": float(np.min(iso.y_thresholds_)),
                "y_max_hazard": float(np.max(iso.y_thresholds_)),
                "y_min_cpr_pp": float(np.min(iso.y_thresholds_)) * HAZARD_TO_CPR_PP,
                "y_max_cpr_pp": float(np.max(iso.y_thresholds_)) * HAZARD_TO_CPR_PP,
            },
            "calibration_fit_diagnostics": {
                "n_cells": int(len(calib)),
                "in_sample_rmse_weighted_pp_raw": calib_raw_m["rmse_weighted_pp"],
                "in_sample_rmse_weighted_pp_recalibrated":
                    calib_recal_m["rmse_weighted_pp"],
                "note": "in-sample for the map; diagnostic, non-decisive",
            },
        },
        "interpretation": {
            "primary_metric": "rmse_weighted_pp",
            "material_improvement_frac": MATERIAL_IMPROVEMENT_FRAC,
            "material_degradation_frac": MATERIAL_DEGRADATION_FRAC,
            "threshold_weighted_pp": threshold_w,
            "threshold_weighted_hurt_pp": threshold_w_hurt,
            "threshold_unweighted_pp_secondary": threshold_u,
            "threshold_unweighted_hurt_pp_secondary": threshold_u_hurt,
            "verdicts": verdicts,
            "overall_verdict": overall,
            "reading": reading,
            "no_headline_ex_ante": no_headline,
        },
        "declined_scope": (
            "rolling/expanding-window landmark variant (monthly refits or "
            "re-recalibrations at the 21 holdout landmarks) declined in-spec "
            "as a different protocol: post-2024 landmarks would fit on "
            "post-2024 information, a rolling-origin design not comparable "
            "to the frozen single split. sadhwani2021-class loan-level deep "
            "comparator remains declined on data grounds (no loan-month "
            "records in repo; 826M-row ingest external, headline-stats-only "
            "license posture); handled in prose."),
    }
    OUT.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"All gates PASS — results saved to {OUT}")


if __name__ == "__main__":
    main()
