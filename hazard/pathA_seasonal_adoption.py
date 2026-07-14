#!/usr/bin/env python3
"""
Path A spec v4 adoption: the calendar-month specification becomes production
(pre-submission freeze item (i); spec committed before any run).

This is a PROMOTION, not a search: the seasonal variant was estimated as
robustness by seasonality_concave_gap.py and its numbers are committed in
data/seasonality_concave_gap_results.json (seasonal block: recovery 121.5%,
r(lag0) -0.378, peak lag -2). Adoption refits the same design through
hazard_fit.fit_hazard_glm(seasonal=True) — 11 calendar-month dummies,
January reference, inserted between the macro block and the stratum FE —
and promotes the artifact to production spec v4.

PARITY GATES, fixed ex ante; if either fails this run hard-exits
"must not be cited" and promotes nothing:

- Gate A (control): refitting with spec v3 settings (seasonal=False, the
  committed artifact's ridge alpha, same panel and holdout split) must
  reproduce the committed data/hazard_coefficients.json macro coefficients
  (rate_gap_bps +0.6734 standardized, burnout_orth -0.1301, friction
  -0.0371) to 1e-4. This proves the fitting path and the live FRED inputs
  still reproduce the frozen fit before any spec change is layered on.
- Gate B (target): the v4 refit + forward simulation (simulate_qt_window
  with the in-loop seasonal multiplier, per-month WSHOMCB rescale) must
  reproduce the committed seasonal artifact's recovery to $0.1B, its lag-0
  correlation to 0.001, and its peak lag exactly (-2).

PROMOTION (only after both gates pass):
- data/hazard_coefficients.json (spec v3) is preserved as
  data/hazard_coefficients_specv3.json — permutation_test_pathA.py remains
  a spec-v3 exhibit and future Gate A controls reference it.
- The v4 artifact becomes data/hazard_coefficients.json (production).
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

from config import HAZARD_COEF_PATH, PANEL_PATH
from extension_risk import score_extension_risk
from hazard_fit import fit_hazard_glm
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly
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

    # ---- Gate B: v4 refit + forward simulation -------------------------------
    print(f"\nGate B: spec v4 refit (seasonal=True, alpha={ridge_alpha:g}) …")
    v4 = fit_hazard_glm(panel, output=CANDIDATE_V4, ridge_alpha=ridge_alpha,
                        seasonal=True)
    print("  month log-effects (Jan = 0): "
          + ", ".join(f"{m}:{v:+.3f}"
                      for m, v in sorted(v4["month_effects"].items(),
                                         key=lambda kv: int(kv[0]))))

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
        "gate_a_v3_control": gate_a,
        "gate_b_v4_target": gate_b,
        "v4_trapped_b": float(score["hazard_trapped_b"]),
        "v4_share_pct": float(score["share_explained_pct"]),
        "v4_r_lag0": float(score["cross_correlation"].get(0)),
        "v4_best_lag": int(score["best_lag"]),
        "v4_peak_lag_r": float(score["peak_lag_r"]),
        "v4_mean_sim_cpr_pct": float(sim["hazard_cpr_pct"].mean()),
        "month_effects": v4["month_effects"],
        "holdout_rmse": v4.get("holdout_rmse"),
        "holdout_r2": v4.get("holdout_r2"),
        "v3_preserved_as": V3_PRESERVED.name,
        "notes": (
            "Promotion of the committed seasonal robustness variant "
            "(seasonality_concave_gap_results.json) to production spec v4; "
            "gates reproduce the committed v3 macro coefficients and the "
            "committed seasonal recovery/r/peak-lag before promotion. "
            "permutation_test_pathA.py remains a spec-v3 exhibit against "
            "hazard_coefficients_specv3.json."
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
