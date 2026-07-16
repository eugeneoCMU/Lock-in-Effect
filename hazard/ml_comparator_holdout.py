#!/usr/bin/env python3
"""
Round-16 W6: flexible-learner ceiling test on the committed cell panel.

SPEC (committed before execution; interpretation thresholds ex ante)
--------------------------------------------------------------------

PURPOSE
  Reviewer note (round 16): "no head-to-head predictive comparisons" with
  modern survival ML.  The faithful comparator — a sadhwani2021-class deep
  model on loan-month records — is DECLINED on data grounds (raw loan-month
  data are not in the repo; the 826M-row Fannie ingest was external and
  headline-stats-only by ratified license posture); that decline is handled
  in prose, not by this run.  What IS deliverable inside the repo is a
  flexible-learner ceiling test at the paper's own unit of analysis: can a
  gradient-boosted Poisson learner or a penalized Poisson GLM, given the
  SAME covariate information, beat the frozen Path A spec v4 on the
  IDENTICAL pre-committed temporal holdout, under the identical target,
  weighting, and RMSE definitions?  Path A's disclosed-weak holdout numbers
  (37.90 pp unweighted / 3.04 pp exposure-weighted / R2 -0.011) are the
  anchor.  Path A is already excluded from headline figures by
  pre-committed spec (paper tex line 328), so no headline can move; the run
  disambiguates WHY Path A fails out-of-sample — functional form vs 2024+
  regime drift.

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
     train side: pl.read_parquet(PANEL_PATH) -> enrich_panel_with_macro ->
     dropna(rate_gap_bps, exposure, loan_age, stratum_id) -> exposure > 0
     -> prepay_rate = (events/exposure).clip(0, 1).  Split at
     config.HOLDOUT_DATE (2024-01-01): train = period <, holdout =
     period >=.  Expected sizes: train 10,176 (the macro frame starts
     2021-01, so pre-2021 cells drop in the rate_gap_bps dropna — the same
     filter that produced the frozen artifacts' n_train), holdout 6,077.
  2. Parity BEFORE any learner runs: pathA_v4_holdout.score_frozen —
     imported, not reimplemented — scores both frozen coefficient
     artifacts through this panel and must reproduce the committed holdout
     numbers (gates G1-G4), proving identical split + metric.
  3. Target / units / metrics, identical for every model scored here:
     y = per-cell monthly prepayment intensity prepay_rate;
     sample_weight = exposure (UPB dollars, clip lower=1 from enrich);
     predicted hazard clipped to [0, 1] (Path A caps hazard at exp(0)=1 by
     clipping the linear predictor to <= 0; learner predictions are
     nonnegative by construction under Poisson/log-link, so only the upper
     clip can bind); annualized CPR pp = hazard * 12 * 100;
     obs_cpr = prepay_rate * 12 * 100;
     rmse_unweighted_pp  = sqrt(mean(sq));
     rmse_weighted_pp    = sqrt(sum(w*sq)/sum(w)), w = exposure;
     r2_unweighted       = 1 - SS_res/SS_tot —
     bit-for-bit the score_frozen formulas.
  4. Learner (a) hgb_poisson: sklearn.ensemble.HistGradientBoostingRegressor
     (loss='poisson', random_state=42, early_stopping=False,
     categorical_features='from_dtype'; all else sklearn 1.6.1 defaults).
     Features (same information set as the v4 design): rate_gap_bps,
     loan_age, burnout, friction, coupon as numerics; calendar month,
     vintage, fico_bucket, ltv_bucket as pandas categoricals.  Encoding
     differences, disclosed ex ante: (i) no spline / standardization /
     orthogonalization — trees are invariant to monotone rescaling and the
     burnout orthogonalization is a GLM identification device, not
     information; (ii) stratum_id enters as its four components because
     HGB native categoricals are capped at max_bins=255 < 296 strata — the
     components carry the identical information and trees can learn the
     interaction; (iii) coupon enters as the raw decimal, a refinement of
     the 0.5%-bucket component of stratum_id.  Category sets fixed ex
     ante: month = 1..12; vintage / fico_bucket / ltv_bucket = sorted
     uniques of the full filtered panel (an ID labeling; no target
     leakage).
  5. Learner (b) poisson_glm: sklearn.linear_model.PoissonRegressor
     (solver='newton-cholesky', fit_intercept=True, max_iter=5000,
     tol=1e-8) on the EXACT v4 design matrix built by the hazard_fit
     helpers: age spline (config.AGE_SPLINE_KNOTS), standardized
     rate_gap_bps, stratum-demeaned + age-orthogonalized + standardized
     burnout, standardized friction, 11 calendar-month dummies (January
     reference), stratum FE dummies (pd.get_dummies drop_first on the
     fitting set; unseen apply-side strata map to the reference row).
     Every preprocessing constant is computed on the fitting set only
     (inner_train during selection, full train for the final fit); the
     apply side is transformed with those constants.  Solver choice fixed
     ex ante with reason: the default lbfgs stalls at the intercept-only
     start on this design (raw-scale quadratic age-spline columns, up to
     ~7e3, defeat its line search — verified in the scratchpad prototype);
     newton-cholesky is IRLS-like, deterministic, converges in a handful
     of iterations, and is the sklearn analogue of the statsmodels IRLS
     that produced Path A itself.  Age-spline hinge columns beyond the
     fitting set's maximum loan age are identically zero (also true of the
     frozen v3/v4 fits); the L2 penalty keeps the Newton system
     nonsingular.  A numerically failing grid fit is an uncaught
     exception, i.e. a nonzero-exit run failure, not a silent skip.
  6. Hyperparameter selection — train-only, temporal, deterministic, fixed
     ex ante (the holdout is touched exactly once per learner, after
     selection): inner_train = train with period < 2023-01-01; inner_val =
     train with period >= 2023-01-01 (calendar-2023 cells).  Selection
     metric: exposure-weighted RMSE (pp) on inner_val, identical formula.
     Grids, enumerated in itertools.product order with strict-< so the
     earlier config wins ties:
       hgb_poisson : learning_rate {0.05, 0.1} x max_leaf_nodes
                     {15, 31, 63} x max_iter {100, 300}   (12 configs)
       poisson_glm : alpha {1e-8, 1e-6, 1e-4, 1e-2, 1.0}  (5 configs)
     The winning config is refit on the full train set and scored on the
     holdout.  The full inner-validation table is recorded in the
     artifact.
  7. Determinism: no wall-clock enters the artifact; the only stochastic
     component is HGB's binning subsample, seeded by random_state=42;
     newton-cholesky is deterministic.  /usr/bin/python3 3.9,
     pandas 2.3.3, numpy 2.0.2, polars parquet read (repo convention),
     sklearn 1.6.1.  lightgbm is broken in this environment and is not
     imported; no torch.

GATES (all must PASS before the artifact is written; nonzero exit and NO
artifact otherwise.  G1-G5 run before any learner is fit.)
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
  G6  learner sanity: every holdout prediction finite and >= 0 before the
      upper clip, for both learners.
  Input-integrity assert (before G1): the reference artifact on disk must
  still carry the exact values quoted in G1-G4 (|diff| <= 1e-12);
  reference drift aborts with a clear message.

PRE-COMMITTED INTERPRETATION (both outcomes fixed ex ante; the run is
reported either way; no post-hoc reframing)
  Primary metric: exposure-weighted holdout RMSE (pp).  A learner
  "materially beats" Path A iff rmse_weighted_pp <
  0.80 * 3.037942336998421 = 2.430354 pp (>= 20% improvement; the 0.80
  factor is fixed here, ex ante).  Secondary, recorded but non-decisive:
  the same 0.80 rule on unweighted RMSE vs 37.903228802264934 pp.
  Outcome A — NO learner materially beats on the primary metric
    ("regime_drift_vindicated"): the 2024+ regime-drift diagnosis is
    vindicated empirically — flexible function classes with the same
    covariate information fail on the same holdout, so Path A's
    out-of-sample failure is attributable to the environment (post-2024
    regime relative to the 2021-2023 training window), not to its
    functional form.  Reported as supporting evidence for the
    manuscript's disclosed-weak treatment of Path A.
  Outcome B — at least one learner materially beats on the primary metric
    ("flexible_fit_helps_no_headline_change"): flexible fit helps
    prediction OOS at this unit of analysis; NO headline moves — Path A
    is excluded from headline figures by pre-committed spec (tex line
    328), and the paper's calibrated-counterfactual (Path B) claims do
    not rest on Path A OOS accuracy.  Reported as-is with the learner's
    numbers.

OUTPUT
  hazard/data/ml_comparator_holdout_results.json, keys:
    mode, spec, holdout_definition, panel_sha256, input_sha256,
    n_train, n_holdout,
    pathA_reference {rmse_unweighted_pp, rmse_weighted_pp, r2_unweighted,
                     source},
    parity {spec_v4, spec_v3},
    gates {G1..G6 with got/want/tol/pass},
    learners {hgb_poisson, poisson_glm} each
      {rmse_unweighted_pp, rmse_weighted_pp, r2_unweighted, features,
       hyperparameters, inner_validation},
    interpretation {primary_metric, material_improvement_frac,
                    threshold_weighted_pp, verdicts, overall_verdict,
                    reading}.

LICENSE / PROVENANCE
  Cell-panel-derived headline statistics only; no loan-level data touched
  or shipped.  The panel is the committed in-repo Freddie cohort-month
  panel; sklearn learners add no data provenance.  The declined
  sadhwani2021-class loan-level comparator is a prose matter (data
  grounds), not part of this run.

Run:  cd hazard && python3 ml_comparator_holdout.py
Runtime estimate: seconds on the 22,709-cell panel (12 + 5 small inner
fits plus 2 refits on <= 10,176 cells) after the live FRED fetch.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import PoissonRegressor

from config import AGE_SPLINE_KNOTS, HOLDOUT_DATE, PANEL_PATH
from hazard_fit import (
    _age_spline_basis,
    _burnout_orthogonalized,
    _month_dummy_matrix,
    _orthogonalize_burnout,
    _stratum_dummy_matrix,
    enrich_panel_with_macro,
)
from pathA_v4_holdout import V3_COEFS, V4_COEFS, score_frozen

DATA_DIR = Path(__file__).parent / "data"
REFERENCE_JSON = DATA_DIR / "pathA_v4_holdout_results.json"
OUT = DATA_DIR / "ml_comparator_holdout_results.json"

# ---- spec constants (fixed ex ante; sources quoted in the header) ----------
V4_UNWEIGHTED_PP = 37.903228802264934
V4_WEIGHTED_PP = 3.037942336998421
V4_R2_UNWEIGHTED = -0.011428527641577979
V3_UNWEIGHTED_PP = 37.8295321331
V3_WEIGHTED_PP = 2.5338262679523766
PARITY_TOL_PP = 0.01
REFERENCE_DRIFT_TOL = 1e-12
N_TRAIN_EXPECTED = 10_176
N_HOLDOUT_EXPECTED = 6_077

INNER_SPLIT_DATE = pd.Timestamp("2023-01-01")
MATERIAL_IMPROVEMENT_FRAC = 0.80

HGB_FIXED = dict(loss="poisson", random_state=42, early_stopping=False,
                 categorical_features="from_dtype")
HGB_GRID = dict(learning_rate=[0.05, 0.1], max_leaf_nodes=[15, 31, 63],
                max_iter=[100, 300])
GLM_FIXED = dict(solver="newton-cholesky", max_iter=5000, tol=1e-8,
                 fit_intercept=True)
GLM_ALPHA_GRID = [1e-8, 1e-6, 1e-4, 1e-2, 1.0]

HGB_NUM_FEATURES = ["rate_gap_bps", "loan_age", "burnout", "friction", "coupon"]
HGB_CAT_FEATURES = ["month", "vintage", "fico_bucket", "ltv_bucket"]


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
    """score_frozen's metric formulas, applied to a learner's hazard vector."""
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


# ---- learner (a): gradient-boosted Poisson ---------------------------------

def hgb_frame(cells: pd.DataFrame, cats: dict) -> pd.DataFrame:
    df = pd.DataFrame(index=cells.index)
    for c in HGB_NUM_FEATURES:
        df[c] = cells[c].astype(float)
    df["month"] = pd.Categorical(
        pd.to_datetime(cells["period"]).dt.month, categories=cats["month"])
    df["vintage"] = pd.Categorical(cells["vintage"], categories=cats["vintage"])
    df["fico_bucket"] = pd.Categorical(
        cells["fico_bucket"], categories=cats["fico_bucket"])
    df["ltv_bucket"] = pd.Categorical(
        cells["ltv_bucket"], categories=cats["ltv_bucket"])
    return df[HGB_NUM_FEATURES + HGB_CAT_FEATURES]


def fit_hgb(cells: pd.DataFrame, cats: dict, config: dict):
    model = HistGradientBoostingRegressor(**HGB_FIXED, **config)
    model.fit(hgb_frame(cells, cats), cells["prepay_rate"].to_numpy(),
              sample_weight=cells["exposure"].to_numpy(dtype=float))
    return model


def select_and_fit_hgb(train: pd.DataFrame, cats: dict) -> tuple[object, dict, list]:
    inner_train = train[train["period"] < INNER_SPLIT_DATE]
    inner_val = train[train["period"] >= INNER_SPLIT_DATE]
    table, best = [], None
    for lr, leaves, iters in itertools.product(*HGB_GRID.values()):
        config = {"learning_rate": lr, "max_leaf_nodes": leaves, "max_iter": iters}
        model = fit_hgb(inner_train, cats, config)
        rmse_w = cell_metrics(model.predict(hgb_frame(inner_val, cats)),
                              inner_val)["rmse_weighted_pp"]
        table.append({**config, "inner_val_rmse_weighted_pp": rmse_w})
        if best is None or rmse_w < best[1]:  # strict <: earlier config wins ties
            best = (config, rmse_w)
        print(f"  hgb inner  lr={lr:<5} leaves={leaves:<3} iters={iters:<4} "
              f"val wRMSE={rmse_w:.4f}pp")
    print(f"  hgb selected: {best[0]}  (inner wRMSE {best[1]:.4f}pp)")
    return fit_hgb(train, cats, best[0]), best[0], table


# ---- learner (b): penalized Poisson GLM on the exact v4 design -------------

def glm_design(fit_df: pd.DataFrame, apply_df: pd.DataFrame
               ) -> tuple[np.ndarray, np.ndarray, dict]:
    """The fit_hazard_glm(seasonal=True) design, constants from fit_df only."""
    age_f = _age_spline_basis(fit_df["loan_age"].to_numpy(), AGE_SPLINE_KNOTS)
    burn_demean_f = fit_df.groupby("stratum_id")["burnout"].transform(
        lambda s: s - s.mean()).to_numpy()
    stratum_burnout_mean = fit_df.groupby("stratum_id")["burnout"].mean().to_dict()
    burn_orth_f, burn_age_adj = _orthogonalize_burnout(age_f, burn_demean_f)
    fric_mean = float(fit_df["friction"].mean())
    fric_std = float(fit_df["friction"].std()) or 1.0
    gap_mean = float(fit_df["rate_gap_bps"].mean())
    gap_std = float(fit_df["rate_gap_bps"].std()) or 1.0
    burn_std = float(burn_orth_f.std()) or 1.0
    reference_stratum = sorted(fit_df["stratum_id"].unique())[0]
    dummies_f = pd.get_dummies(fit_df["stratum_id"], prefix="fe_stratum",
                               drop_first=True)
    fe_columns = list(dummies_f.columns)

    X_fit = np.asarray(np.column_stack([
        age_f,
        (fit_df["rate_gap_bps"].to_numpy() - gap_mean) / gap_std,
        burn_orth_f / burn_std,
        (fit_df["friction"].to_numpy() - fric_mean) / fric_std,
        _month_dummy_matrix(fit_df["period"]),
        dummies_f.to_numpy(),
    ]), dtype=np.float64)

    age_a = _age_spline_basis(apply_df["loan_age"].to_numpy(), AGE_SPLINE_KNOTS)
    burn_demean_a = apply_df["burnout"].to_numpy() - apply_df["stratum_id"].map(
        stratum_burnout_mean).fillna(0).to_numpy()
    burn_a = _burnout_orthogonalized(burn_demean_a, age_a, burn_age_adj)
    X_apply = np.asarray(np.column_stack([
        age_a,
        (apply_df["rate_gap_bps"].to_numpy() - gap_mean) / gap_std,
        burn_a / burn_std,
        (apply_df["friction"].to_numpy() - fric_mean) / fric_std,
        _month_dummy_matrix(apply_df["period"]),
        _stratum_dummy_matrix(apply_df["stratum_id"], reference_stratum, fe_columns),
    ]), dtype=np.float64)
    return X_fit, X_apply, {"n_stratum_fe": len(fe_columns)}


def fit_glm(X: np.ndarray, cells: pd.DataFrame, alpha: float) -> PoissonRegressor:
    model = PoissonRegressor(alpha=alpha, **GLM_FIXED)
    model.fit(X, cells["prepay_rate"].to_numpy(),
              sample_weight=cells["exposure"].to_numpy(dtype=float))
    return model


def select_and_fit_glm(train: pd.DataFrame, holdout: pd.DataFrame
                       ) -> tuple[np.ndarray, dict, list, dict]:
    inner_train = train[train["period"] < INNER_SPLIT_DATE]
    inner_val = train[train["period"] >= INNER_SPLIT_DATE]
    X_it, X_iv, _ = glm_design(inner_train, inner_val)
    table, best = [], None
    for alpha in GLM_ALPHA_GRID:
        model = fit_glm(X_it, inner_train, alpha)
        rmse_w = cell_metrics(model.predict(X_iv), inner_val)["rmse_weighted_pp"]
        table.append({"alpha": alpha, "inner_val_rmse_weighted_pp": rmse_w})
        if best is None or rmse_w < best[1]:  # strict <: earlier config wins ties
            best = (alpha, rmse_w)
        print(f"  glm inner  alpha={alpha:<6g} val wRMSE={rmse_w:.4f}pp")
    print(f"  glm selected: alpha={best[0]:g}  (inner wRMSE {best[1]:.4f}pp)")
    X_tr, X_ho, meta = glm_design(train, holdout)
    model = fit_glm(X_tr, train, best[0])
    return model.predict(X_ho), {"alpha": best[0], **GLM_FIXED}, table, meta


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
        sys.exit("G5 split-integrity failure — no learner run, no artifact.")

    # ---- G1-G4 parity: frozen artifacts through this panel, before learners
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
                 "no learner run, no artifact.")

    # ---- learners (holdout touched once each, after train-only selection) --
    cats = {
        "month": list(range(1, 13)),
        "vintage": sorted(pd.concat([train, holdout])["vintage"].unique().tolist()),
        "fico_bucket": sorted(pd.concat([train, holdout])["fico_bucket"].unique().tolist()),
        "ltv_bucket": sorted(pd.concat([train, holdout])["ltv_bucket"].unique().tolist()),
    }
    print("Learner (a) hgb_poisson — train-only temporal selection:")
    hgb_model, hgb_config, hgb_table = select_and_fit_hgb(train, cats)
    hgb_pred = hgb_model.predict(hgb_frame(holdout, cats))

    print("Learner (b) poisson_glm — train-only temporal selection:")
    glm_pred, glm_config, glm_table, glm_meta = select_and_fit_glm(train, holdout)

    g6_ok = bool(
        np.isfinite(hgb_pred).all() and (hgb_pred >= 0).all()
        and np.isfinite(glm_pred).all() and (glm_pred >= 0).all()
    )
    gates["G6_learner_sanity"] = {
        "hgb_pred_min": float(hgb_pred.min()), "hgb_pred_max": float(hgb_pred.max()),
        "glm_pred_min": float(glm_pred.min()), "glm_pred_max": float(glm_pred.max()),
        "pass": g6_ok,
    }
    print(f"[GATE] G6 learner sanity: hgb [{hgb_pred.min():.3e}, {hgb_pred.max():.3e}] "
          f"glm [{glm_pred.min():.3e}, {glm_pred.max():.3e}] "
          f"{'PASS' if g6_ok else 'FAIL'}")
    if not g6_ok:
        sys.exit("G6 learner-sanity failure — no artifact.")

    hgb_metrics = cell_metrics(hgb_pred, holdout)
    glm_metrics = cell_metrics(glm_pred, holdout)

    # ---- pre-committed interpretation ---------------------------------------
    threshold_w = MATERIAL_IMPROVEMENT_FRAC * V4_WEIGHTED_PP
    threshold_u = MATERIAL_IMPROVEMENT_FRAC * V4_UNWEIGHTED_PP
    verdicts = {}
    for name, m in (("hgb_poisson", hgb_metrics), ("poisson_glm", glm_metrics)):
        verdicts[name] = {
            "primary_weighted": ("material_improvement"
                                 if m["rmse_weighted_pp"] < threshold_w
                                 else "comparable_or_worse"),
            "secondary_unweighted": ("material_improvement"
                                     if m["rmse_unweighted_pp"] < threshold_u
                                     else "comparable_or_worse"),
        }
    any_material = any(v["primary_weighted"] == "material_improvement"
                       for v in verdicts.values())
    overall = ("flexible_fit_helps_no_headline_change" if any_material
               else "regime_drift_vindicated")
    reading = (
        "At least one flexible learner materially beats Path A spec v4 on the "
        "exposure-weighted holdout RMSE. Flexible fit helps prediction "
        "out-of-sample at the cell-panel unit; NO headline moves — Path A is "
        "excluded from headline figures by pre-committed spec (tex line 328) "
        "and the calibrated-counterfactual claims do not rest on Path A OOS "
        "accuracy." if any_material else
        "No flexible learner materially beats Path A spec v4 on the "
        "exposure-weighted holdout RMSE (threshold: >=20% improvement). The "
        "2024+ regime-drift diagnosis is vindicated empirically: flexible "
        "function classes with the same covariate information fail on the "
        "same pre-committed holdout, so the failure is the environment, not "
        "the functional form."
    )

    for name, m in (("pathA v4 (frozen)", {**{
            "rmse_unweighted_pp": v4["rmse_unweighted_pp"],
            "rmse_weighted_pp": v4["rmse_exposure_weighted_pp"],
            "r2_unweighted": v4["holdout_r2_unweighted"]}}),
            ("hgb_poisson", hgb_metrics), ("poisson_glm", glm_metrics)):
        print(f"{name:>18}: unweighted {m['rmse_unweighted_pp']:7.2f}pp  "
              f"weighted {m['rmse_weighted_pp']:6.3f}pp  "
              f"R2 {m['r2_unweighted']:+.4f}")
    print(f"Overall verdict: {overall}")

    payload = {
        "mode": "ml_comparator_holdout",
        "spec": ("round-16 W6 flexible-learner ceiling test; identical Path A "
                 "temporal holdout, target, weighting, and RMSE definitions; "
                 "train-only temporal hyperparameter selection; thresholds ex ante"),
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
        "pathA_reference": {
            "rmse_unweighted_pp": V4_UNWEIGHTED_PP,
            "rmse_weighted_pp": V4_WEIGHTED_PP,
            "r2_unweighted": V4_R2_UNWEIGHTED,
            "source": "hazard/data/pathA_v4_holdout_results.json (spec_v4)",
        },
        "parity": {"spec_v4": v4, "spec_v3": v3},
        "gates": gates,
        "learners": {
            "hgb_poisson": {
                **hgb_metrics,
                "features": HGB_NUM_FEATURES + HGB_CAT_FEATURES,
                "encoding_notes": (
                    "raw covariates, no spline/standardization/"
                    "orthogonalization (tree-invariant); stratum_id enters as "
                    "vintage/fico_bucket/ltv_bucket categoricals + raw coupon "
                    "(native categorical cap 255 < 296 strata); month "
                    "categorical 1-12"),
                "hyperparameters": {
                    **{k: v for k, v in HGB_FIXED.items()}, **hgb_config},
                "inner_validation": hgb_table,
            },
            "poisson_glm": {
                **glm_metrics,
                "features": (
                    ["age_linear"] + [f"age_spline_{k}" for k in AGE_SPLINE_KNOTS]
                    + ["rate_gap_bps(std)", "burnout_orth(std)", "friction(std)"]
                    + ["m_2..m_12"]
                    + [f"fe_stratum_* (n={glm_meta['n_stratum_fe']})"]),
                "encoding_notes": (
                    "exact fit_hazard_glm(seasonal=True) design via hazard_fit "
                    "helpers; constants train-only; fit_intercept replaces the "
                    "explicit const column"),
                "hyperparameters": glm_config,
                "inner_validation": glm_table,
            },
        },
        "hyperparameter_selection": {
            "inner_train": f"period < {INNER_SPLIT_DATE.date()}",
            "inner_val": f"{INNER_SPLIT_DATE.date()} <= period < {HOLDOUT_DATE.date()}",
            "metric": "exposure-weighted RMSE (pp), identical formula",
            "tie_break": "first config in enumeration order (strict <)",
        },
        "interpretation": {
            "primary_metric": "rmse_weighted_pp",
            "material_improvement_frac": MATERIAL_IMPROVEMENT_FRAC,
            "threshold_weighted_pp": threshold_w,
            "threshold_unweighted_pp_secondary": threshold_u,
            "verdicts": verdicts,
            "overall_verdict": overall,
            "reading": reading,
        },
        "declined_scope": (
            "sadhwani2021-class loan-level deep comparator declined on data "
            "grounds (no loan-month records in repo; 826M-row ingest external, "
            "headline-stats-only license posture); handled in prose"),
    }
    OUT.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"All gates PASS — results saved to {OUT}")


if __name__ == "__main__":
    main()
