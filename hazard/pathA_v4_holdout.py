#!/usr/bin/env python3
"""
Freeze follow-up: out-of-sample evaluation of the FROZEN spec v4 Path A fit.

The pre-submission freeze adopted the calendar-month specification (spec v4,
run-2026-07-14-pathA-seasonal) under parity gates that reproduce the committed
robustness numbers, but did not re-evaluate the seasonal fit on the
>= 2024-01-01 holdout used for spec v3 (manuscript Section V.B flags this).
This script fills that gap: PREDICTION ONLY, no refitting — the frozen
coefficient artifact is loaded and scored on the identical holdout split, so
the documented bootstrap branch-instability (TECHNICAL.md; the resample-refit
path) does not apply.

Pre-registered, ex ante (this spec is committed before the run):

  - Holdout: cohort-month cells with period >= HOLDOUT_DATE (2024-01-01),
    the same split as spec v3; n must equal the 6,077 recorded in both
    coefficient artifacts, else abort.
  - Report unweighted and exposure-weighted RMSE of annualized stratum-month
    CPR in percentage points — exactly the two weightings of
    ridge_reference_weighting.py (committed spec v3 values at the production
    alpha: 37.8295 unweighted / 2.5338 exposure-weighted).
  - Parity gate: re-scoring the frozen spec v3 artifact
    (hazard_coefficients_specv3.json) through this same prediction path must
    reproduce its committed holdout RMSEs to 1e-6 pp (unweighted against the
    artifact's own holdout_rmse; both weightings against
    ridge_reference_weighting.json at alpha_0.0001). On failure STOP and
    report; do not edit the manuscript.
  - STOP gate: if the spec v4 exposure-weighted RMSE exceeds 5.0 pp (double
    the spec v3 2.5 pp), STOP and report rather than print in the manuscript.

Run:  cd hazard && python3 pathA_v4_holdout.py
      → data/pathA_v4_holdout_results.json (written with gate verdicts even
        on gate failure; exit code 1 signals a failed gate)
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

from config import AGE_SPLINE_KNOTS, HOLDOUT_DATE, PANEL_PATH
from hazard_fit import (
    MONTH_COLS,
    _age_spline_basis,
    _burnout_orthogonalized,
    _month_dummy_matrix,
    _stratum_dummy_matrix,
    enrich_panel_with_macro,
)

DATA_DIR = Path(__file__).parent / "data"
V4_COEFS = DATA_DIR / "runs" / "run-2026-07-14-pathA-seasonal" / "hazard_coefficients.json"
V3_COEFS = DATA_DIR / "hazard_coefficients_specv3.json"
RIDGE_REF = DATA_DIR / "ridge_reference_weighting.json"
OUT = DATA_DIR / "pathA_v4_holdout_results.json"

STOP_GATE_WEIGHTED_PP = 5.0
PARITY_TOL_PP = 1e-6


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_holdout() -> pd.DataFrame:
    """The production panel pipeline, cut at the committed holdout date."""
    panel = pl.read_parquet(PANEL_PATH)
    pdf = enrich_panel_with_macro(panel)
    pdf = pdf.dropna(subset=["rate_gap_bps", "exposure", "loan_age", "stratum_id"])
    pdf = pdf[pdf["exposure"] > 0]
    pdf["prepay_rate"] = (pdf["events"] / pdf["exposure"]).clip(0, 1)
    return pdf[pdf["period"] >= HOLDOUT_DATE].copy()


def score_frozen(holdout: pd.DataFrame, artifact: Path) -> dict:
    """Score a frozen coefficient artifact on the holdout.

    Prediction only: every preprocessing constant (standardization moments,
    burnout orthogonalization, stratum means, reference stratum, FE columns)
    comes from the artifact; nothing is recomputed from training data."""
    art = json.loads(artifact.read_text())
    spec_version = int(art.get("spec_version", 3))
    seasonal = spec_version >= 4
    coefs = art["coefficients"]

    n_expected = int(art["n_holdout"])
    if len(holdout) != n_expected:
        raise SystemExit(
            f"ABORT: holdout has {len(holdout):,} cells; artifact "
            f"{artifact.name} recorded n_holdout={n_expected:,} — split drift."
        )

    age_h = _age_spline_basis(holdout["loan_age"].to_numpy(), AGE_SPLINE_KNOTS)
    burn_demean_h = holdout["burnout"].to_numpy() - holdout["stratum_id"].map(
        art["stratum_burnout_mean"]).fillna(0).to_numpy()
    burn_h = _burnout_orthogonalized(burn_demean_h, age_h, art["burnout_age_adjust"])
    stratum_h = _stratum_dummy_matrix(
        holdout["stratum_id"], art["reference_stratum"], art["fe_columns"])
    blocks = [
        age_h,
        (holdout["rate_gap_bps"].to_numpy() - art["rate_gap_bps_mean"])
        / art["rate_gap_bps_std"],
        burn_h / art["burnout_demean_std"],
        (holdout["friction"].to_numpy() - art["friction_mean"])
        / art["friction_std"],
    ]
    names = (
        ["age_linear"]
        + [f"age_spline_{k}" for k in AGE_SPLINE_KNOTS]
        + ["rate_gap_bps", "burnout_orth", "friction"]
    )
    if seasonal:
        blocks.append(_month_dummy_matrix(holdout["period"]))
        names += MONTH_COLS
    blocks.append(stratum_h)
    names += art["fe_columns"]
    X_h = np.column_stack(blocks)
    X_h = np.asarray(sm.add_constant(X_h, has_constant="add"), dtype=np.float64)
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

    pred_cpr = np.exp(np.clip(X_h.dot(params), -20, 0)) * 12 * 100
    obs_cpr = holdout["prepay_rate"].to_numpy() * 12 * 100
    w = holdout["exposure"].to_numpy(dtype=float)
    sq = (obs_cpr - pred_cpr) ** 2
    ss_tot = float(((obs_cpr - obs_cpr.mean()) ** 2).sum())
    return {
        "artifact": str(artifact.relative_to(DATA_DIR.parent.parent)),
        "artifact_sha256": _sha256(artifact),
        "spec_version": spec_version,
        "n_holdout": int(len(holdout)),
        "rmse_unweighted_pp": float(np.sqrt(sq.mean())),
        "rmse_exposure_weighted_pp": float(np.sqrt((w * sq).sum() / w.sum())),
        "holdout_r2_unweighted": float(1 - sq.sum() / ss_tot),
        "holdout_obs_cpr_mean_unweighted_pp": float(obs_cpr.mean()),
        "holdout_obs_cpr_mean_exposure_weighted_pp": float(
            (w * obs_cpr).sum() / w.sum()
        ),
    }


def main() -> None:
    holdout = load_holdout()
    print(f"Holdout cells (period >= {HOLDOUT_DATE.date()}): {len(holdout):,}")

    v3 = score_frozen(holdout, V3_COEFS)
    v4 = score_frozen(holdout, V4_COEFS)

    # --- parity gate: the v3 re-scoring must reproduce committed values ----
    v3_art = json.loads(V3_COEFS.read_text())
    ridge = json.loads(RIDGE_REF.read_text())
    ridge_prod = ridge["holdout_rmse_grid"]["alpha_0.0001"]
    parity_checks = {
        "unweighted_vs_specv3_artifact": {
            "got": v3["rmse_unweighted_pp"],
            "want": float(v3_art["holdout_rmse"]),
        },
        "unweighted_vs_ridge_reference": {
            "got": v3["rmse_unweighted_pp"],
            "want": float(ridge_prod["rmse_unweighted_pp"]),
        },
        "exposure_weighted_vs_ridge_reference": {
            "got": v3["rmse_exposure_weighted_pp"],
            "want": float(ridge_prod["rmse_exposure_weighted_pp"]),
        },
    }
    parity_pass = True
    for name, chk in parity_checks.items():
        ok = abs(chk["got"] - chk["want"]) <= PARITY_TOL_PP
        chk["tol_pp"] = PARITY_TOL_PP
        chk["pass"] = bool(ok)
        parity_pass &= ok
        print(f"  parity {name}: got {chk['got']:.10f} "
              f"want {chk['want']:.10f} {'PASS' if ok else 'FAIL'}")

    # --- pre-registered STOP gate on the v4 exposure-weighted RMSE ---------
    stop_gate = {
        "rule": "STOP if spec v4 exposure-weighted holdout RMSE > 5.0 pp "
                "(double the spec v3 2.5 pp); do not print in the manuscript",
        "threshold_pp": STOP_GATE_WEIGHTED_PP,
        "got_pp": v4["rmse_exposure_weighted_pp"],
        "pass": bool(v4["rmse_exposure_weighted_pp"] <= STOP_GATE_WEIGHTED_PP),
    }

    out = {
        "mode": "pathA_v4_holdout",
        "holdout_definition": (
            f"cohort-month cells with period >= {HOLDOUT_DATE.date()} from the "
            "production panel pipeline (hazard_fit split; prediction only, "
            "no refitting)"
        ),
        "panel_sha256": _sha256(Path(PANEL_PATH)),
        "spec_v4": v4,
        "spec_v3_reference": v3,
        "parity_gate": {"pass": bool(parity_pass), "checks": parity_checks},
        "stop_gate": stop_gate,
    }
    OUT.write_text(json.dumps(out, indent=2))
    print(f"\nspec v4 holdout: unweighted {v4['rmse_unweighted_pp']:.2f}pp  "
          f"exposure-weighted {v4['rmse_exposure_weighted_pp']:.2f}pp  "
          f"R^2 {v4['holdout_r2_unweighted']:.4f}")
    print(f"spec v3 holdout: unweighted {v3['rmse_unweighted_pp']:.2f}pp  "
          f"exposure-weighted {v3['rmse_exposure_weighted_pp']:.2f}pp")
    print(f"Written to {OUT}")

    if not parity_pass:
        print("PARITY GATE FAILED — stop and report; no manuscript edit.")
        sys.exit(1)
    if not stop_gate["pass"]:
        print("STOP GATE FAILED (exposure-weighted RMSE > 5.0 pp) — "
              "stop and report; no manuscript edit.")
        sys.exit(1)
    print("All gates passed.")


if __name__ == "__main__":
    main()
