#!/usr/bin/env python3
"""
Path A spec v4 adoption: the calendar-month specification becomes production
(pre-submission freeze item (i); spec committed before any run).

This is a PROMOTION, not a search: the seasonal variant was estimated as
robustness by seasonality_concave_gap.py and its numbers are committed in
data/seasonality_concave_gap_results.json (seasonal block: recovery 121.5%,
r(lag0) -0.378, peak lag -2).

AMENDMENT (second pre-registration; the first attempt's Gate B FAILED and
was reported, commit 7c3c673's runner): re-assembling the seasonal design
inside fit_hazard_glm (pandas ddof-1 standardization) flipped the Poisson
IRLS into its cold-start ridge fallback and landed a different, incompletely
converged penalized optimum (near-uniform ~-0.30 "month effects"; an
intercept split, not seasonality) — while the committed construction,
seasonality_concave_gap.fit_with_month_dummies, still reproduces its
artifact to zero drift on today's inputs. The committed seasonal numbers
are pinned to that construction, so production spec v4 is DEFINED as that
construction: this runner now imports and calls fit_with_month_dummies
directly (single source of truth, no re-assembly), and the v4 artifact is
assembled as the committed v3 artifact's prediction metadata (scales,
burnout-age adjustment, stratum means, FE layout — exactly what the
committed seasonal simulation consumed) plus the seasonal fit's
coefficients and month effects. The parity gates below are UNCHANGED from
the first pre-registration: same targets, same tolerances.

PARITY GATES, fixed ex ante; if either fails this run hard-exits
"must not be cited" and promotes nothing:

- Gate A (control): refitting with spec v3 settings (seasonal=False, the
  committed artifact's ridge alpha, same panel and holdout split) must
  reproduce the committed data/hazard_coefficients.json macro coefficients
  (rate_gap_bps +0.6734 standardized, burnout_orth -0.1301, friction
  -0.0371) to 1e-4.
- Gate B (target): the v4 fit + forward simulation (simulate_qt_window
  with the in-loop seasonal multiplier, per-month WSHOMCB rescale) must
  reproduce the committed seasonal artifact's recovery to $0.1B, its lag-0
  correlation to 0.001, and its peak lag exactly (-2).

PROMOTION (only after both gates pass):
- data/hazard_coefficients.json (spec v3) is preserved as
  data/hazard_coefficients_specv3.json — permutation_test_pathA.py remains
  a spec-v3 exhibit and future Gate A controls reference it.
- The v4 artifact becomes data/hazard_coefficients.json (production).
  Its holdout fields are removed rather than inherited (they described the
  v3 fit; the committed seasonal robustness run reported none).
- The v4 forward simulation is written to the production sim path.
- data/pathA_seasonal_adoption_results.json records gates, month effects,
  scores, and the v4 mean simulated CPR (consumed by the WAL table).

Run:  cd hazard && python3 pathA_seasonal_adoption.py
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import polars as pl

from config import HAZARD_COEF_PATH, HOLDOUT_DATE, PANEL_PATH
from extension_risk import score_extension_risk
from hazard_fit import enrich_panel_with_macro, fit_hazard_glm
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly
from seasonality_concave_gap import fit_with_month_dummies
from simulate import SIM_RESULTS_PATH, simulate_qt_window

DATA_DIR = Path(__file__).parent / "data"
SEASONAL_ARTIFACT = DATA_DIR / "seasonality_concave_gap_results.json"
V3_PRESERVED = DATA_DIR / "hazard_coefficients_specv3.json"
TMP_V3 = DATA_DIR / "_gateA_v3_refit.json"
CANDIDATE_V4 = DATA_DIR / "_candidate_v4_coefficients.json"
TMP_SIM = DATA_DIR / "_gateB_v4_sim.parquet"
RESULTS_JSON = DATA_DIR / "pathA_seasonal_adoption_results.json"

MACRO_BETAS = ["rate_gap_bps", "burnout_orth", "friction"]
GATE_A_TOL = 1e-4
GATE_B_TOL_B = 0.1
GATE_B_TOL_R = 0.001


def hard_fail(msg: str) -> None:
    print(f"\nPARITY GATE FAILURE: {msg}")
    print("Results must not be cited; nothing was promoted.")
    sys.exit(1)


def main() -> None:
    committed = json.load(open(HAZARD_COEF_PATH))
    if "month_effects" in committed:
        hard_fail("production artifact is already spec v4 — refusing to re-run "
                  "adoption on top of itself")
    ridge_alpha = float(committed["ridge_alpha"])
    seasonal_target = json.load(open(SEASONAL_ARTIFACT))["path_a_seasonality"]["seasonal"]

    panel = pl.read_parquet(PANEL_PATH)

    # ---- Gate A: v3 control refit --------------------------------------------
    print(f"Gate A: spec v3 control refit (alpha={ridge_alpha:g}) …")
    v3 = fit_hazard_glm(panel, output=TMP_V3, ridge_alpha=ridge_alpha,
                        seasonal=False)
    gate_a = {}
    for name in MACRO_BETAS:
        got = float(v3["coefficients"][name])
        want = float(committed["coefficients"][name])
        ok = abs(got - want) < GATE_A_TOL
        gate_a[name] = {"got": got, "want": want, "pass": bool(ok)}
        print(f"  gate A {name}: got {got:+.6f} want {want:+.6f} "
              f"[{'PASS' if ok else 'FAIL'}]")
    if not all(g["pass"] for g in gate_a.values()):
        hard_fail("Gate A (v3 control) did not reproduce the committed "
                  "macro coefficients — fitting path or live inputs drifted")

    # ---- v4 fit: the committed construction, verbatim -------------------------
    print(f"\nSpec v4 fit via seasonality_concave_gap.fit_with_month_dummies "
          f"(alpha={ridge_alpha:g}) …")
    pdf = enrich_panel_with_macro(panel)
    pdf = pdf.dropna(subset=["rate_gap_bps", "exposure", "loan_age", "stratum_id"])
    pdf = pdf[pdf["exposure"] > 0]
    train = pdf[pdf["period"] < HOLDOUT_DATE].copy()
    coefs_s, month_effects, fit_method = fit_with_month_dummies(train, ridge_alpha)
    print(f"  fit method: {fit_method}")
    print("  month log-effects (Jan = 0): "
          + ", ".join(f"{m}:{v:+.3f}" for m, v in sorted(month_effects.items())))

    # v4 artifact: committed v3 prediction metadata + seasonal coefficients —
    # exactly the pairing the committed seasonal simulation consumed.
    v4_artifact = dict(committed)
    v4_artifact["spec_version"] = 4
    v4_artifact["coefficients"] = coefs_s
    v4_artifact["month_effects"] = {
        str(m): float(v) for m, v in sorted(month_effects.items())
    }
    v4_artifact["fit_method"] = fit_method
    v4_artifact.pop("holdout_r2", None)
    v4_artifact.pop("holdout_rmse", None)
    v4_artifact["provenance"] = (
        "Spec v4 (freeze item i): coefficients and month effects from "
        "seasonality_concave_gap.fit_with_month_dummies (the committed "
        "seasonal robustness construction, reproduced to zero drift at "
        "adoption); prediction scales, burnout-age adjustment, stratum "
        "burnout means, and FE layout inherited from the spec v3 artifact, "
        "exactly as the committed seasonal simulation consumed them. "
        "Holdout metrics not recomputed at adoption; see "
        "hazard_coefficients_specv3.json for the v3 fit's."
    )
    with open(CANDIDATE_V4, "w") as f:
        json.dump(v4_artifact, f, indent=2)

    # ---- Gate B: forward simulation must reproduce the committed artifact -----
    print("  forward simulation under v4 …")
    sim = simulate_qt_window(panel=panel, coef_path=CANDIDATE_V4,
                             output=TMP_SIM)
    empirical = build_empirical_metrics(
        fetch_data(), soma_rolloff=fetch_soma_mbs_monthly()
    )
    score = score_extension_risk(sim, empirical)

    checks = {
        "trapped_b": (float(score["hazard_trapped_b"]),
                      float(seasonal_target["trapped_b"]), GATE_B_TOL_B),
        "r_lag0": (float(score["cross_correlation"].get(0)),
                   float(seasonal_target["r_lag0"]), GATE_B_TOL_R),
    }
    gate_b = {}
    for name, (got, want, tol) in checks.items():
        ok = abs(got - want) <= tol
        gate_b[name] = {"got": got, "want": want, "tol": tol, "pass": bool(ok)}
        print(f"  gate B {name}: got {got:.4f} want {want:.4f} (tol {tol}) "
              f"[{'PASS' if ok else 'FAIL'}]")
    got_lag = int(score["best_lag"])
    want_lag = int(seasonal_target["peak_lag"])
    ok = got_lag == want_lag
    gate_b["peak_lag"] = {"got": got_lag, "want": want_lag, "pass": bool(ok)}
    print(f"  gate B peak_lag: got {got_lag} want {want_lag} "
          f"[{'PASS' if ok else 'FAIL'}]")
    if not all(g["pass"] for g in gate_b.values()):
        hard_fail("Gate B (v4 target) did not reproduce the committed "
                  "seasonal artifact")

    # ---- Promotion ------------------------------------------------------------
    print("\nBoth gates PASS — promoting spec v4 to production.")
    shutil.copy2(HAZARD_COEF_PATH, V3_PRESERVED)
    shutil.move(str(CANDIDATE_V4), HAZARD_COEF_PATH)
    sim.to_parquet(SIM_RESULTS_PATH)
    TMP_V3.unlink(missing_ok=True)
    TMP_SIM.unlink(missing_ok=True)

    payload = {
        "mode": "pathA_seasonal_adoption",
        "spec_version": 4,
        "ridge_alpha": ridge_alpha,
        "fit_method": fit_method,
        "construction": "seasonality_concave_gap.fit_with_month_dummies",
        "gate_a_v3_control": gate_a,
        "gate_b_v4_target": gate_b,
        "v4_trapped_b": float(score["hazard_trapped_b"]),
        "v4_share_pct": float(score["share_explained_pct"]),
        "v4_r_lag0": float(score["cross_correlation"].get(0)),
        "v4_best_lag": int(score["best_lag"]),
        "v4_peak_lag_r": float(score["peak_lag_r"]),
        "v4_mean_sim_cpr_pct": float(sim["hazard_cpr_pct"].mean()),
        "v4_macro_betas": {n: float(coefs_s[n]) for n in MACRO_BETAS},
        "month_effects": v4_artifact["month_effects"],
        "v3_preserved_as": V3_PRESERVED.name,
        "first_attempt_note": (
            "The first pre-registered attempt (commit 7c3c673) failed Gate B: "
            "re-assembling the design inside fit_hazard_glm flipped IRLS into "
            "its cold-start ridge fallback and a different penalized optimum. "
            "Production v4 is therefore pinned to the committed construction."
        ),
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")

    print(f"v4 production: ${score['hazard_trapped_b']:.1f}B "
          f"({score['share_explained_pct']:.1f}%)  "
          f"r(lag0)={score['cross_correlation'].get(0):+.3f}  "
          f"peak lag {score['best_lag']}  "
          f"mean sim CPR {payload['v4_mean_sim_cpr_pct']:.2f}%")
    print(f"Results saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
