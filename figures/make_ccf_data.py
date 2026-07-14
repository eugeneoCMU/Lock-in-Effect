#!/usr/bin/env python3
"""
Regenerate figures/ccf_data.json (±6-lag CPR cross-correlations) from the
three estimators' committed series. Replaces the README snippet with a
committed, gated generator (post-freeze consistency pass).

Sources (all committed):
  - ABM (production): abm/data/runs/run-2026-07-04-15yr-foldin/
    metrics_monthly.csv (Empirical_CPR_Pct vs US_CPR_Pct). The prior
    ccf_data.json used the run-2026-07-05-berger variant series; the
    manuscript's Table 2 and the cross-design figure both quote the
    production fold-in run (r at lag 0 = -0.318), so the CCF figure now
    plots the same series the paper describes.
  - Path A (spec v4): hazard/data/simulation_results.parquet
    (hash-identical to the frozen run-2026-07-14-pathA-seasonal artifact),
    scored against the hazard scorer's own empirical series
    (macro.build_empirical_metrics) over the 42-month QT window, exactly
    as extension_risk.score_extension_risk does, at max_lag=6.
  - Path B: hazard/data/microsim_results.parquet, same construction.

Ex-ante gates (all against committed values; on failure: no output, exit 1):
  - ABM ±3 values equal the fold-in manifest's cross_correlation block to
    1e-9 (same committed CSV, deterministic).
  - Path A r at lag 0 equals the frozen v4 manifest headline r_lag0
    (-0.37817) within 0.001, and the ±3 peak (max |r|, the
    extension_risk.best_lag convention) sits at lag -2.
  - Path B ±3 values equal extension_risk_results_literature_microsim.json's
    cross_correlation block to 1e-6 (unchanged estimator: peak -3 at +0.404).

Sign convention (verified on synthetic data; extension_risk.py / manuscript
Section V.C): a peak at NEGATIVE lag means the EMPIRICAL series leads and
the simulated path trails.

Run:  python3 figures/make_ccf_data.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hazard"))

from config import MICROSIM_RESULTS_PATH, SIM_RESULTS_PATH  # noqa: E402
from macro import (  # noqa: E402
    assert_qt_window_only,
    build_empirical_metrics,
    calculate_dynamic_friction,
    cpr_cross_correlation,
    fetch_data,
    fetch_soma_mbs_monthly,
    qt_active_frame,
)

OUT = ROOT / "figures" / "ccf_data.json"
FOLDIN_DIR = ROOT / "abm" / "data" / "runs" / "run-2026-07-04-15yr-foldin"
PATHA_MANIFEST = (
    ROOT / "hazard" / "data" / "runs" / "run-2026-07-14-pathA-seasonal"
    / "manifest.json"
)
EXT_LIT = ROOT / "hazard" / "data" / "extension_risk_results_literature_microsim.json"

MAX_LAG = 6


def _fail(msg: str) -> None:
    print(f"GATE FAILED: {msg}")
    sys.exit(1)


def main() -> None:
    # --- ABM production series (self-contained committed CSV) --------------
    csv = pd.read_csv(FOLDIN_DIR / "metrics_monthly.csv")
    sub = csv.dropna(subset=["Empirical_CPR_Pct", "US_CPR_Pct"])
    abm = cpr_cross_correlation(
        sub["Empirical_CPR_Pct"].reset_index(drop=True),
        sub["US_CPR_Pct"].reset_index(drop=True),
        max_lag=MAX_LAG,
    )

    foldin_manifest = json.loads((FOLDIN_DIR / "manifest.json").read_text())
    want_abm = {int(k): v
                for k, v in foldin_manifest["metrics"]["cross_correlation"].items()}
    for lag, want in want_abm.items():
        if abs(abm[lag] - want) > 1e-9:
            _fail(f"ABM lag {lag}: got {abm[lag]:.10f}, manifest {want:.10f}")
    print(f"ABM gate: ±3 values match fold-in manifest exactly "
          f"(lag 0 = {abm[0]:+.4f})")

    # --- Hazard empirical series (42-month QT window) -----------------------
    print("Fetching hazard macro + SOMA for the empirical series …")
    macro = calculate_dynamic_friction(fetch_data())
    empirical = build_empirical_metrics(macro, soma_rolloff=fetch_soma_mbs_monthly())
    qt_emp = qt_active_frame(empirical)
    assert_qt_window_only(qt_emp.index)

    def hazard_ccf(parquet: Path) -> dict[int, float]:
        sim = pd.read_parquet(parquet)
        qt_sim = sim.reindex(qt_emp.index).dropna(subset=["simulated_rolloff_b"])
        assert_qt_window_only(qt_sim.index)
        return cpr_cross_correlation(
            qt_emp["Empirical_CPR_Pct"], qt_sim["hazard_cpr_pct"], max_lag=MAX_LAG
        )

    path_a = hazard_ccf(Path(SIM_RESULTS_PATH))
    path_b = hazard_ccf(Path(MICROSIM_RESULTS_PATH))

    # --- Path A gates: frozen v4 manifest headline --------------------------
    headline = json.loads(PATHA_MANIFEST.read_text())["headline"]
    if abs(path_a[0] - headline["r_lag0"]) > 1e-3:
        _fail(f"Path A lag 0: got {path_a[0]:.5f}, "
              f"frozen manifest {headline['r_lag0']:.5f}")
    peak = max(range(-3, 4), key=lambda k: abs(path_a[k]))
    if peak != int(headline["best_lag"]):
        _fail(f"Path A ±3 peak: got {peak}, frozen manifest {headline['best_lag']}")
    print(f"Path A gate: lag 0 = {path_a[0]:+.4f} (manifest "
          f"{headline['r_lag0']:+.4f}), ±3 peak at {peak}")

    # --- Path B gate: unchanged vs committed standalone artifact ------------
    want_pb = {int(k): v
               for k, v in json.loads(EXT_LIT.read_text())["cross_correlation"].items()}
    for lag, want in want_pb.items():
        if abs(path_b[lag] - want) > 1e-6:
            _fail(f"Path B lag {lag}: got {path_b[lag]:.8f}, committed {want:.8f}")
    pb_peak = max(range(-3, 4), key=lambda k: abs(path_b[k]))
    print(f"Path B gate: ±3 values match committed artifact "
          f"(peak {pb_peak} at {path_b[pb_peak]:+.3f})")

    payload = {
        "abm": {str(k): abm[k] for k in sorted(abm)},
        "path_a": {str(k): path_a[k] for k in sorted(path_a)},
        "path_b": {str(k): path_b[k] for k in sorted(path_b)},
        "note": (
            "±6-lag CPR cross-correlations, 42-month QT window. Sign "
            "convention (verified on synthetic data; §V.C): a peak at "
            "negative lag means the empirical series leads and the "
            "simulated path trails."
        ),
        "sources": {
            "abm": "abm/data/runs/run-2026-07-04-15yr-foldin/metrics_monthly.csv "
                   "(production fold-in run)",
            "path_a": "hazard/data/simulation_results.parquet (spec v4, "
                      "hash-identical to run-2026-07-14-pathA-seasonal) vs "
                      "macro.build_empirical_metrics",
            "path_b": "hazard/data/microsim_results.parquet vs "
                      "macro.build_empirical_metrics",
        },
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"All gates passed. Written to {OUT}")


if __name__ == "__main__":
    main()
