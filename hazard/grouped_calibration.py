#!/usr/bin/env python3
"""
Round-18 R18-J (gate #52): grouped calibration over time — reliability of the
FROZEN Path A spec v4 predictions by prediction-level bin CROSSED with calendar
period, scored on the committed cohort-month panel (referee Q10 grouped half;
T3 CPR-side calibration).  PURE SCORING — no refitting, no recalibration; the
frozen coefficient artifact is loaded and applied through the identical
prediction path the landmark/isotonic scaffold uses.

SPEC (committed BEFORE any number is computed; binning + period scheme +
interpretation thresholds all fixed ex ante)
------------------------------------------------------------------------------

PURPOSE
  Referee Q10 asks for grouped calibration over time — reliability-by-
  prediction-bin per period against realized cohort CPR — beyond the aggregate
  Theil/correlation diagnostics (app:theil) and the coarse two-way
  train-vs-post-training split already at V.B (train-window predicted/empirical
  98%; post-training 137%).  This run refines that coarse split into a
  bin x period reliability table on the SAME object the RMSE parity gates
  cover: the committed Freddie cohort-month cell panel, frozen spec v4
  predictions, identical target / exposure weighting / CPR-pp units as
  pathA_v4_holdout and landmark_isotonic_holdout.  Path A is excluded from the
  paper's headline figures by pre-committed spec (tex line 328), so NO outcome
  of this run can move a headline; it reports WHERE (which prediction level,
  which period) the frozen fit is well- or ill-calibrated.

EVALUATION UNIVERSE (fixed ex ante)
  The committed Path A panel after the production pipeline (load_splits,
  imported verbatim from landmark_isotonic_holdout): pl.read_parquet(PANEL_PATH)
  -> enrich_panel_with_macro (live FRED) -> dropna(rate_gap_bps, exposure,
  loan_age, stratum_id) -> exposure > 0 -> prepay_rate = (events/exposure)
  .clip(0,1).  This retains calendar 2021-01 .. 2025-09 (the rate_gap_bps
  dropna keeps all of 2021+): 10,176 train cells (period < HOLDOUT_DATE
  2024-01-01) + 6,077 holdout cells (period >= 2024-01-01) = 16,253 cells.
  This IS the universe the frozen-prediction RMSE gates are defined on; the run
  is scored on it in full so the parity gates bind.  The QT-window months the
  marginal path is reported over are a DIFFERENT object (the microsim/ABM
  dollar runoff, not the cell panel); this run deliberately stays on the cell
  panel so the frozen-prediction parity is exact.  No cached fallback: a failed
  live FRED fetch ABORTS nonzero (inherited from load_splits).

BINNING SCHEME (fixed ex ante; edges chosen on TRAIN only, never on eval data)
  Prediction axis: 5 bins of frozen spec v4 predicted annualized CPR (pp),
  edges = the exposure-weighted 20/40/60/80th percentiles of the frozen v4
  predicted CPR computed on the TRAINING window ONLY (period < HOLDOUT_DATE).
  Fitting the edges on the training window keeps them off the evaluation data
  and makes each training bin carry ~20% of training exposure.  Weighted-
  quantile convention, fixed ex ante: sort predicted CPR ascending; with
  cumulative exposure cw_i and total W, positions p_i = (cw_i - 0.5 w_i)/W
  (Hazen); edge(q) = numpy.interp(q, p_i, x_i).  The SAME four edges are then
  applied unchanged to every cell (train and holdout) via
  numpy.digitize(pred_cpr, edges, right=False), giving bins 0..4
  (bin 0 = (-inf, e1), bin 4 = [e4, +inf)).  Predicted CPR uses the scorer's
  native clip: pred_cpr = clip(hazard, 0, 1) * 1200 (cell_metrics units).

PERIOD SCHEME (fixed ex ante)
  Primary axis: calendar HALF-YEARS over the evaluation panel — H1 = Jan-Jun,
  H2 = Jul-Dec — yielding 2021H1 .. 2025H2 (10 non-empty periods; 2025H2 is
  Jul-Sep only, the panel's last month is 2025-09).  Half-years align exactly
  with the repo's 2024-01-01 train/holdout cut (train = 2021H1..2023H2,
  holdout = 2024H1..2025H2), so the coarse train-vs-holdout split the
  manuscript already reports (V.B 98% / 137%) is recoverable as a pooling of
  these periods and is reported alongside in CPR-pp units.

PER CELL (bin b x period p) REPORTED
  exposure-weighted mean predicted CPR (pp); exposure-weighted mean realized
  cell CPR (pp); signed gap = pred - obs (pp); exposure share (of total panel
  exposure); cell count.  Plus per-period marginals, per-bin marginals (pooled
  over periods), and the coarse train/holdout aggregate.

CONSTRUCTION (deterministic, step by step)
  1. load_splits() (imported) -> train, holdout; full = concat, index reset.
  2. Parity BEFORE any calibration object is built (gates G1-G6): score_frozen
     (imported) reproduces the committed spec v4 / v3 holdout RMSEs; the local
     predict_frozen_hazard path (imported) reproduces score_frozen to <= 1e-9.
     G5 checks the 10,176 / 6,077 split against both frozen artifacts.
  3. pred_haz_full = predict_frozen_hazard(full, V4_COEFS) (imported, the same
     design/coefficient path score_frozen uses); pred_cpr_full =
     clip(pred_haz_full, 0, 1) * 1200; obs_cpr_full = prepay_rate * 1200;
     w_full = exposure.
  4. Bin edges from the train mask only (weighted-quantile convention above),
     applied to full via digitize.  Period labels from the period column.
  5. Aggregate exposure-weighted pred/obs CPR per (bin, period), per period,
     per bin, and per train/holdout half.
  6. Determinism: no RNG, no wall-clock in the artifact; numpy.interp +
     numpy.digitize + weighted means only.  /usr/bin/python3 3.9,
     numpy 2.0.2, pandas 2.3.3, polars parquet read (repo convention).

GATES (all must PASS before the artifact is written; nonzero exit and NO
artifact otherwise.  Reference-drift assert + G1-G6 run before the calibration
table is built.)
  Input-integrity assert: pathA_v4_holdout_results.json still carries the
    exact G1-G4 values (|diff| <= 1e-12); drift ABORTS.
  G1  v4 parity unweighted:        |got - 37.903228802264934| <= 0.01 pp
  G2  v4 parity exposure-weighted: |got - 3.037942336998421|  <= 0.01 pp
  G3  v3 parity unweighted:        |got - 37.8295321331|       <= 0.01 pp
  G4  v3 parity exposure-weighted: |got - 2.5338262679523766|  <= 0.01 pp
  G5  split integrity: n_train == 10,176 and n_holdout == 6,077, each equal
      to the values recorded in BOTH frozen coefficient artifacts.
  G6  local-prediction parity: predict_frozen_hazard's holdout scoring
      reproduces score_frozen's spec v4 unweighted RMSE, exposure-weighted
      RMSE, and R2 to <= 1e-9.
  G7  holdout realized-CPR tie: the exposure-weighted (unweighted) mean of
      obs_cpr on the 6,077 holdout cells reproduces the committed reference
      4.210290920254706 (7.041628590244825) to <= 1e-6 pp — an independent
      tie of this run's realized-CPR construction to the frozen artifact.
  G8  bin-edge sanity: exactly 4 finite, strictly-increasing edges; every
      cell assigned to a bin in 0..4; all five bins non-empty on the full
      panel.
  G9  partition completeness: summed over the bin x period table, exposure
      equals total panel exposure (rel <= 1e-9) and cell count equals 16,253
      exactly.
  G10 reconstruction: the exposure-weighted aggregate predicted and realized
      CPR over the whole panel, rebuilt from the table cells (each cell's
      exposure-weighted mean re-weighted by its exposure), equals the direct
      exposure-weighted mean over the full panel to <= 1e-9 pp — the table is
      a faithful, loss-free partition of the scored quantities.

PRE-COMMITTED INTERPRETATION (all outcomes reported as-is; NO outcome moves a
headline — Path A is excluded from headline figures by pre-committed spec,
tex line 328, and the calibrated-counterfactual (Path B) claims do not rest on
Path A OOS accuracy.  Read only after the gates pass.)
  Per-cell signed gap g(b,p) = wmean_pred_cpr - wmean_obs_cpr (pp).  Per-period
  aggregate: exposure-weighted signed gap and the predicted/realized ratio
  (the CPR-pp analogue of V.B's 98% / 137% dollar split).
  ADEQUATE grouped calibration (the null this run tests): within each period
    the signed bin gaps are small relative to that bin's realized CPR and do
    NOT increase monotonically with the prediction bin (no reliability-slope
    departure), AND the sign and magnitude of the aggregate per-period gap are
    stable across the 2024-01-01 train/holdout boundary (no systematic
    post-boundary widening).
  DRIFT / MISCALIBRATION: a systematic change in the aggregate signed gap
    across the boundary (holdout periods carry a consistently larger |gap| or
    a sign the training periods do not), and/or a within-period reliability
    slope in which the top prediction bins systematically depart from realized
    in one direction.  This is the pattern the aggregate Theil U2 > 1
    (tab:theil) and the coarse 98% / 137% split already flag; the table
    LOCALIZES it to prediction level x period.  Reported whichever occurs; the
    verdict field records temporal_drift vs adequate_grouped_calibration by the
    rule below, non-decisive for any headline.
  Verdict rule (fixed ex ante): let R_train, R_hold be the pooled
    predicted/realized CPR ratios on the train and holdout halves.  Verdict
    "temporal_drift_post_boundary" iff |R_hold - 1| > 1.25 * |R_train - 1| AND
    R_hold and R_train sit on opposite sides of 1 OR |R_hold - 1| >= 0.20;
    else "no_material_grouped_drift".  (0.20 = the ~20% materiality scale used
    across the round; 1.25 = its ratio-symmetric counterpart.)  The verdict is
    a summary label only; the full table is the deliverable.

OUTPUT
  hazard/data/grouped_calibration_results.json, keys: mode, spec,
  evaluation_universe, panel_sha256, input_sha256, n_train, n_holdout, n_full,
  pathA_reference, parity {spec_v4, spec_v3}, gates {G1..G10}, binning
  {edges_cpr_pp, convention, fit_window}, period_scheme, calibration_table
  (list of {bin, period, n_cells, exposure_share, wmean_pred_cpr_pp,
  wmean_obs_cpr_pp, gap_pp}), period_marginals, bin_marginals,
  train_holdout_split, interpretation.  Headline stats only; no per-cell
  vectors.

LICENSE / PROVENANCE
  Cell-panel-derived headline statistics only; no loan-level data touched or
  shipped.  Committed in-repo Freddie cohort-month panel; frozen spec v4
  coefficient artifact.  No refitting, no recalibration, no new data.

Run:  cd hazard && python3 grouped_calibration.py
Runtime estimate: seconds after the live FRED fetch (two frozen-design
constructions + weighted aggregation).  Liveness gate #52 per
paper/v16/revision_roadmap_round18.md is recorded separately in TECHNICAL.md
after execution, not by this script.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from config import HOLDOUT_DATE, PANEL_PATH
# Reuse the scaffold's data-loading and frozen-prediction machinery (import,
# do not duplicate): load_splits, cell_metrics, predict_frozen_hazard, gate,
# _sha256, the committed parity constants, and the hazard->CPR rescaling.
from landmark_isotonic_holdout import (
    HAZARD_TO_CPR_PP,
    N_HOLDOUT_EXPECTED,
    N_TRAIN_EXPECTED,
    PARITY_TOL_PP,
    REFERENCE_JSON,
    V3_UNWEIGHTED_PP,
    V3_WEIGHTED_PP,
    V4_R2_UNWEIGHTED,
    V4_UNWEIGHTED_PP,
    V4_WEIGHTED_PP,
    _sha256,
    cell_metrics,
    gate,
    load_splits,
    predict_frozen_hazard,
)
from pathA_v4_holdout import V3_COEFS, V4_COEFS, score_frozen

DATA_DIR = Path(__file__).parent / "data"
OUT = DATA_DIR / "grouped_calibration_results.json"

# ---- spec constants (fixed ex ante) ----------------------------------------
REFERENCE_DRIFT_TOL = 1e-12
LOCAL_PARITY_TOL = 1e-9
RECON_TOL_PP = 1e-9
PARTITION_REL_TOL = 1e-9
OBS_TIE_TOL_PP = 1e-6

# Committed holdout realized-CPR means (pathA_v4_holdout_results.json spec_v4;
# also carried in landmark_isotonic_results.json parity block).
HOLDOUT_OBS_CPR_WMEAN_PP = 4.210290920254706
HOLDOUT_OBS_CPR_UMEAN_PP = 7.041628590244825

QUANTILE_LEVELS = (0.20, 0.40, 0.60, 0.80)  # 5 bins
N_FULL_EXPECTED = N_TRAIN_EXPECTED + N_HOLDOUT_EXPECTED  # 16,253

# Verdict-rule constants (fixed ex ante; the round's ~20% materiality scale).
DRIFT_RATIO_MULT = 1.25
DRIFT_ABS_THRESHOLD = 0.20


def _weighted_quantile_edges(x: np.ndarray, w: np.ndarray,
                             levels: tuple) -> np.ndarray:
    """Hazen weighted quantiles: sort by x, p_i = (cw_i - 0.5 w_i)/W,
    edge(q) = interp(q, p, x).  Deterministic; no RNG."""
    order = np.argsort(x, kind="mergesort")  # stable, deterministic
    xs = x[order]
    ws = w[order]
    cw = np.cumsum(ws)
    W = cw[-1]
    p = (cw - 0.5 * ws) / W
    return np.array([float(np.interp(q, p, xs)) for q in levels])


def _wmean(vals: np.ndarray, w: np.ndarray) -> float:
    return float((w * vals).sum() / w.sum())


def _period_label(period: pd.Series) -> np.ndarray:
    dt = pd.to_datetime(period)
    half = np.where(dt.dt.month <= 6, 1, 2)
    return np.array([f"{y}H{h}" for y, h in zip(dt.dt.year.to_numpy(), half)])


def main() -> None:
    # ---- input-integrity: the on-disk reference still matches the spec ------
    ref = json.loads(REFERENCE_JSON.read_text())
    for got, want, label in [
        (ref["spec_v4"]["rmse_unweighted_pp"], V4_UNWEIGHTED_PP, "v4 unweighted"),
        (ref["spec_v4"]["rmse_exposure_weighted_pp"], V4_WEIGHTED_PP, "v4 weighted"),
        (ref["spec_v3_reference"]["rmse_unweighted_pp"], V3_UNWEIGHTED_PP, "v3 unweighted"),
        (ref["spec_v3_reference"]["rmse_exposure_weighted_pp"], V3_WEIGHTED_PP, "v3 weighted"),
        (ref["spec_v4"]["holdout_obs_cpr_mean_exposure_weighted_pp"],
         HOLDOUT_OBS_CPR_WMEAN_PP, "holdout obs cpr weighted mean"),
        (ref["spec_v4"]["holdout_obs_cpr_mean_unweighted_pp"],
         HOLDOUT_OBS_CPR_UMEAN_PP, "holdout obs cpr unweighted mean"),
    ]:
        if abs(got - want) > REFERENCE_DRIFT_TOL:
            raise SystemExit(
                f"ABORT: reference artifact drift on {label}: file has {got!r}, "
                f"spec quotes {want!r}. Re-examine before running."
            )

    train, holdout = load_splits()
    full = pd.concat([train, holdout]).reset_index(drop=True)
    print(f"Train cells (period < {HOLDOUT_DATE.date()}): {len(train):,}  |  "
          f"Holdout cells: {len(holdout):,}  |  Full: {len(full):,}")

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
        sys.exit("G5 split-integrity failure — no calibration table, no artifact.")

    # ---- G1-G4 parity: frozen artifacts through this panel -----------------
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
                 "no calibration table, no artifact.")

    # ---- G6 local-prediction parity (the binning inputs equal the scorer) --
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
        sys.exit("G6 local-prediction parity failure — no calibration table, "
                 "no artifact.")

    # ---- scored quantities on the full panel (cell_metrics units) ----------
    haz_full = predict_frozen_hazard(full, V4_COEFS)
    pred_cpr_full = np.clip(haz_full, 0.0, 1.0) * HAZARD_TO_CPR_PP
    obs_cpr_full = full["prepay_rate"].to_numpy() * HAZARD_TO_CPR_PP
    w_full = full["exposure"].to_numpy(dtype=float)
    is_train = (full["period"] < HOLDOUT_DATE).to_numpy()
    periods = _period_label(full["period"])

    # ---- G7 holdout realized-CPR tie ---------------------------------------
    is_hold = ~is_train
    obs_w_hold = _wmean(obs_cpr_full[is_hold], w_full[is_hold])
    obs_u_hold = float(obs_cpr_full[is_hold].mean())
    g7_checks = {
        "exposure_weighted_pp": gate(
            "G7 holdout obs CPR weighted mean", obs_w_hold,
            HOLDOUT_OBS_CPR_WMEAN_PP, OBS_TIE_TOL_PP),
        "unweighted_pp": gate(
            "G7 holdout obs CPR unweighted mean", obs_u_hold,
            HOLDOUT_OBS_CPR_UMEAN_PP, OBS_TIE_TOL_PP),
    }
    g7_ok = all(c["pass"] for c in g7_checks.values())
    gates["G7_holdout_realized_cpr_tie"] = {"checks": g7_checks, "pass": bool(g7_ok)}
    if not g7_ok:
        sys.exit("G7 holdout realized-CPR tie failure — no artifact.")

    # ---- bin edges from the TRAIN window only ------------------------------
    edges = _weighted_quantile_edges(
        pred_cpr_full[is_train], w_full[is_train], QUANTILE_LEVELS)
    bins_full = np.digitize(pred_cpr_full, edges, right=False)  # 0..4
    n_bins = len(QUANTILE_LEVELS) + 1

    edges_mono = bool(np.all(np.diff(edges) > 0) and np.all(np.isfinite(edges)))
    bins_valid = bool(bins_full.min() >= 0 and bins_full.max() <= n_bins - 1)
    bins_nonempty = bool(all((bins_full == b).sum() > 0 for b in range(n_bins)))
    g8_ok = edges_mono and bins_valid and bins_nonempty
    gates["G8_bin_edge_sanity"] = {
        "n_edges": len(edges), "edges_cpr_pp": [float(e) for e in edges],
        "strictly_increasing_finite": edges_mono,
        "bins_in_range": bins_valid, "all_bins_nonempty": bins_nonempty,
        "pass": bool(g8_ok),
    }
    print(f"[GATE] G8 bin-edge sanity: edges(CPR pp) "
          f"[{', '.join(f'{e:.4f}' for e in edges)}]  "
          f"{'PASS' if g8_ok else 'FAIL'}")
    if not g8_ok:
        sys.exit("G8 bin-edge sanity failure — no artifact.")

    # ---- bin x period calibration table ------------------------------------
    total_exposure = float(w_full.sum())
    period_order = sorted(set(periods))
    table = []
    recon_pred_num = 0.0
    recon_obs_num = 0.0
    recon_w = 0.0
    partition_exp = 0.0
    partition_n = 0
    for b in range(n_bins):
        for p in period_order:
            mask = (bins_full == b) & (periods == p)
            n_cells = int(mask.sum())
            if n_cells == 0:
                continue
            wm = w_full[mask]
            cell_exp = float(wm.sum())
            wmean_pred = _wmean(pred_cpr_full[mask], wm)
            wmean_obs = _wmean(obs_cpr_full[mask], wm)
            table.append({
                "bin": b, "period": p, "n_cells": n_cells,
                "exposure_share": cell_exp / total_exposure,
                "wmean_pred_cpr_pp": wmean_pred,
                "wmean_obs_cpr_pp": wmean_obs,
                "gap_pp": wmean_pred - wmean_obs,
            })
            recon_pred_num += cell_exp * wmean_pred
            recon_obs_num += cell_exp * wmean_obs
            recon_w += cell_exp
            partition_exp += cell_exp
            partition_n += n_cells

    # ---- G9 partition completeness -----------------------------------------
    g9_exp_ok = abs(partition_exp - total_exposure) <= PARTITION_REL_TOL * total_exposure
    g9_n_ok = (partition_n == len(full)) and (len(full) == N_FULL_EXPECTED)
    g9_ok = bool(g9_exp_ok and g9_n_ok)
    gates["G9_partition_completeness"] = {
        "table_exposure": partition_exp, "total_exposure": total_exposure,
        "table_n_cells": partition_n, "n_full": len(full),
        "n_full_expected": N_FULL_EXPECTED,
        "exposure_match": bool(g9_exp_ok), "count_match": bool(g9_n_ok),
        "pass": g9_ok,
    }
    print(f"[GATE] G9 partition completeness: cells {partition_n:,}/{len(full):,} "
          f"exposure match {g9_exp_ok}  {'PASS' if g9_ok else 'FAIL'}")
    if not g9_ok:
        sys.exit("G9 partition-completeness failure — no artifact.")

    # ---- G10 reconstruction of the aggregate exposure-weighted CPR ---------
    direct_pred = _wmean(pred_cpr_full, w_full)
    direct_obs = _wmean(obs_cpr_full, w_full)
    recon_pred = recon_pred_num / recon_w
    recon_obs = recon_obs_num / recon_w
    g10_checks = {
        "pred_cpr_pp": gate("G10 recon pred", recon_pred, direct_pred, RECON_TOL_PP),
        "obs_cpr_pp": gate("G10 recon obs", recon_obs, direct_obs, RECON_TOL_PP),
    }
    g10_ok = all(c["pass"] for c in g10_checks.values())
    gates["G10_reconstruction"] = {"checks": g10_checks, "pass": bool(g10_ok)}
    if not g10_ok:
        sys.exit("G10 reconstruction failure — no artifact.")

    # ---- marginals (period, bin) and train/holdout split -------------------
    def _agg(mask: np.ndarray) -> dict:
        wm = w_full[mask]
        pred = _wmean(pred_cpr_full[mask], wm)
        obs = _wmean(obs_cpr_full[mask], wm)
        return {
            "n_cells": int(mask.sum()),
            "exposure_share": float(wm.sum()) / total_exposure,
            "wmean_pred_cpr_pp": pred,
            "wmean_obs_cpr_pp": obs,
            "gap_pp": pred - obs,
            "pred_over_realized_ratio": pred / obs,
        }

    period_marginals = {p: _agg(periods == p) for p in period_order}
    bin_marginals = {str(b): _agg(bins_full == b) for b in range(n_bins)}
    train_agg = _agg(is_train)
    hold_agg = _agg(is_hold)
    train_holdout_split = {
        "train_2021H1_2023H2": train_agg,
        "holdout_2024H1_2025H2": hold_agg,
        "note": ("CPR-pp analogue of the V.B dollar split (train predicted/"
                 "empirical 98%, post-training 137%); here on the cohort-month "
                 "cell panel, the object the RMSE gates cover"),
    }

    # ---- pre-committed verdict (summary label only; non-decisive) ----------
    r_train = train_agg["pred_over_realized_ratio"]
    r_hold = hold_agg["pred_over_realized_ratio"]
    opposite_sides = (r_hold - 1.0) * (r_train - 1.0) < 0
    drift = bool(
        (abs(r_hold - 1.0) > DRIFT_RATIO_MULT * abs(r_train - 1.0) and opposite_sides)
        or abs(r_hold - 1.0) >= DRIFT_ABS_THRESHOLD
    )
    verdict = "temporal_drift_post_boundary" if drift else "no_material_grouped_drift"

    no_headline = (
        "Ex ante: NO outcome of this run moves any headline — Path A is "
        "excluded from headline figures by pre-committed spec (tex line 328) "
        "and the calibrated-counterfactual (Path B) claims do not rest on "
        "Path A OOS accuracy."
    )
    reading = {
        "temporal_drift_post_boundary": (
            "The pooled predicted/realized CPR ratio shifts materially across "
            "the 2024-01-01 train/holdout boundary (holdout |ratio-1| "
            f">= {DRIFT_ABS_THRESHOLD:.2f} or > {DRIFT_RATIO_MULT:.2f}x the "
            "train departure with a sign flip): the grouped table localizes "
            "the regime drift already visible in the aggregate Theil U2 > 1 "
            "and the coarse 98%/137% split to prediction level x period. "
            + no_headline),
        "no_material_grouped_drift": (
            "The pooled predicted/realized CPR ratio is stable across the "
            "2024-01-01 boundary within the ex-ante materiality band: grouped "
            "calibration is adequate at the panel's own unit. " + no_headline),
    }[verdict]

    print(f"Aggregate exposure-weighted CPR (pp): "
          f"train pred {train_agg['wmean_pred_cpr_pp']:.3f} vs obs "
          f"{train_agg['wmean_obs_cpr_pp']:.3f} (ratio {r_train:.3f}); "
          f"holdout pred {hold_agg['wmean_pred_cpr_pp']:.3f} vs obs "
          f"{hold_agg['wmean_obs_cpr_pp']:.3f} (ratio {r_hold:.3f})")
    print(f"Verdict: {verdict}")

    payload = {
        "mode": "grouped_calibration",
        "spec": ("round-18 R18-J grouped calibration over time — reliability of "
                 "the frozen Path A spec v4 predictions by exposure-weighted "
                 "prediction-CPR quintile bin (edges fit on the training window "
                 "only) crossed with calendar half-years, scored on the "
                 "committed cohort-month panel; pure scoring, no refitting or "
                 "recalibration; identical target/weighting/RMSE definitions as "
                 "pathA_v4_holdout and landmark_isotonic_holdout; binning, "
                 "period scheme, and interpretation thresholds all fixed ex ante"),
        "evaluation_universe": (
            f"committed Path A panel, calendar 2021-01..2025-09 (period rows "
            f"kept after the rate_gap_bps dropna); {N_TRAIN_EXPECTED:,} train "
            f"cells (period < {HOLDOUT_DATE.date()}) + {N_HOLDOUT_EXPECTED:,} "
            f"holdout cells = {N_FULL_EXPECTED:,} cells; the object the "
            "frozen-prediction RMSE gates are defined on"),
        "panel_sha256": _sha256(Path(PANEL_PATH)),
        "input_sha256": {
            "spec_v4_coefficients": _sha256(V4_COEFS),
            "spec_v3_coefficients": _sha256(V3_COEFS),
            "pathA_reference_artifact": _sha256(REFERENCE_JSON),
        },
        "n_train": int(len(train)),
        "n_holdout": int(len(holdout)),
        "n_full": int(len(full)),
        "pathA_reference": {
            "rmse_unweighted_pp": V4_UNWEIGHTED_PP,
            "rmse_weighted_pp": V4_WEIGHTED_PP,
            "r2_unweighted": V4_R2_UNWEIGHTED,
            "holdout_obs_cpr_mean_exposure_weighted_pp": HOLDOUT_OBS_CPR_WMEAN_PP,
            "holdout_obs_cpr_mean_unweighted_pp": HOLDOUT_OBS_CPR_UMEAN_PP,
            "source": "hazard/data/pathA_v4_holdout_results.json (spec_v4)",
        },
        "parity": {"spec_v4": v4, "spec_v3": v3},
        "gates": gates,
        "binning": {
            "n_bins": n_bins,
            "quantile_levels": list(QUANTILE_LEVELS),
            "edges_cpr_pp": [float(e) for e in edges],
            "convention": ("exposure-weighted Hazen quantiles of frozen spec v4 "
                           "predicted annualized CPR (pp); edges fit on the "
                           "training window only, applied unchanged to every "
                           "cell via numpy.digitize(..., right=False)"),
            "fit_window": f"period < {HOLDOUT_DATE.date()} (train, {len(train):,} cells)",
            "predicted_cpr_units": "clip(hazard,0,1) * 1200 (cell_metrics units)",
        },
        "period_scheme": {
            "axis": "calendar half-years (H1=Jan-Jun, H2=Jul-Dec)",
            "periods": period_order,
            "train_periods": [p for p in period_order if p <= "2023H2"],
            "holdout_periods": [p for p in period_order if p >= "2024H1"],
            "note": ("2025H2 is Jul-Sep only (panel ends 2025-09); half-years "
                     "align exactly with the 2024-01-01 train/holdout cut"),
        },
        "calibration_table": table,
        "period_marginals": period_marginals,
        "bin_marginals": bin_marginals,
        "train_holdout_split": train_holdout_split,
        "aggregate": {
            "wmean_pred_cpr_pp": direct_pred,
            "wmean_obs_cpr_pp": direct_obs,
            "pred_over_realized_ratio": direct_pred / direct_obs,
        },
        "interpretation": {
            "verdict": verdict,
            "verdict_rule": (
                f"temporal_drift_post_boundary iff |R_hold-1| > "
                f"{DRIFT_RATIO_MULT} * |R_train-1| with a sign flip across 1, "
                f"OR |R_hold-1| >= {DRIFT_ABS_THRESHOLD}; else "
                "no_material_grouped_drift"),
            "R_train": r_train,
            "R_hold": r_hold,
            "reading": reading,
            "no_headline_ex_ante": no_headline,
        },
    }
    OUT.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"All gates PASS — results saved to {OUT}")


if __name__ == "__main__":
    main()
