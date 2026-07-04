#!/usr/bin/env python3
"""
Build the pre-fix baseline manifest consolidating all four headline numbers.

Run from repo root after:
  1. cd abm && python3 freeze_run.py --tag pre-fix-2026-07 --skip-figures
  2. cd hazard && python3 extension_risk.py                  (Path A)
  3. cd hazard && python3 extension_risk.py --mode literature (Path B)

The manifest freezes the "before" state for the four robustness fixes
(QT window consolidation, elasticity band, 15-year MBS, Freddie-covariate
cross-design test) so every later diff is attributable to a specific fix.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RUN_DIR = Path(__file__).resolve().parent

PAPER_NUMBERS = {
    "empirical_benchmark_b": 764.7,
    "abm_trapped_b": 101.2,
    "hazard_path_a_trapped_b": 915.0,
    "hazard_path_b_trapped_b": 747.0,
}

HASH_TARGETS = [
    "abm/abm_cpr_surface.csv",
    "abm/fed_mbs_extension_risk.py",
    "abm/abm_lockin_simulation.py",
    "hazard/config.py",
    "hazard/data/cohort_month_panel.parquet",
    "hazard/data/loan_sample.parquet",
    "hazard/data/microsim_results.parquet",
    "hazard/data/simulation_results.parquet",
    "hazard/data/hazard_coefficients.json",
]


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
        ).strip()
    except Exception:
        return None


def main() -> None:
    abm_manifest = json.loads(
        (REPO / "abm/data/runs/pre-fix-2026-07/manifest.json").read_text()
    )
    path_a = json.loads(
        (REPO / "hazard/data/extension_risk_results_cohort_empirical.json").read_text()
    )
    path_b = json.loads(
        (REPO / "hazard/data/extension_risk_results_literature_microsim.json").read_text()
    )

    abm_dollars = abm_manifest["metrics"]["dollars_b"]
    headline = {
        "empirical_benchmark_b": abm_dollars["empirical_trapped"],
        "abm_trapped_b": abm_dollars["us_trapped"],
        "abm_share_explained_pct": abm_dollars["share_explained_pct"],
        "hazard_path_a_trapped_b": path_a["hazard_trapped_b"],
        "hazard_path_a_share_pct": path_a["share_explained_pct"],
        "hazard_path_b_trapped_b": path_b["hazard_trapped_b"],
        "hazard_path_b_share_pct": path_b["share_explained_pct"],
    }

    checks = {
        "empirical_benchmark_b": (
            headline["empirical_benchmark_b"],
            PAPER_NUMBERS["empirical_benchmark_b"],
        ),
        "abm_trapped_b": (headline["abm_trapped_b"], PAPER_NUMBERS["abm_trapped_b"]),
        "hazard_path_a_trapped_b": (
            headline["hazard_path_a_trapped_b"],
            PAPER_NUMBERS["hazard_path_a_trapped_b"],
        ),
        "hazard_path_b_trapped_b": (
            headline["hazard_path_b_trapped_b"],
            PAPER_NUMBERS["hazard_path_b_trapped_b"],
        ),
    }
    acceptance = {
        name: {"reproduced": actual, "paper": paper, "ok": abs(actual - paper) < 0.5}
        for name, (actual, paper) in checks.items()
    }
    if not all(v["ok"] for v in acceptance.values()):
        raise SystemExit(f"Baseline does NOT reproduce paper numbers: {acceptance}")

    manifest = {
        "baseline_tag": "pre-fix-2026-07",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_head(),
        "purpose": (
            "Known-good pre-fix state for the four robustness fixes: "
            "QT window consolidation, elasticity band, 15-year MBS fold-in, "
            "Freddie-covariate cross-design test."
        ),
        "headline_numbers": headline,
        "acceptance_vs_paper": acceptance,
        "qt_window": abm_manifest["metrics"]["qt_window"],
        "path_a_diagnostics": {
            "cpr_r_lag0": path_a["cross_correlation"]["0"],
            "best_lag": path_a["best_lag"],
        },
        "path_b_diagnostics": {
            "cpr_r_lag0": path_b["cross_correlation"]["0"],
            "best_lag": path_b["best_lag"],
            "peak_lag_r": path_b["peak_lag_r"],
        },
        "config_hashes_sha256": {t: sha256(REPO / t) for t in HASH_TARGETS},
        "sources": {
            "abm_manifest": "abm/data/runs/pre-fix-2026-07/manifest.json",
            "path_a_results": "hazard/data/extension_risk_results_cohort_empirical.json",
            "path_b_results": "hazard/data/extension_risk_results_literature_microsim.json",
        },
        "notes": (
            "hazard/hazard_fit.py had an infinite mutual recursion between "
            "_stratum_fe_row and _stratum_dummy_matrix that made the Path A "
            "refit unrunnable; fixed mechanically (pass fe_index) before this "
            "baseline. Refit reproduces $915.1B / 119.7% exactly, confirming "
            "the fix is numerically neutral."
        ),
    }

    out = RUN_DIR / "manifest.json"
    out.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Baseline manifest written: {out}")
    for name, v in acceptance.items():
        print(f"  {name}: {v['reproduced']:.1f} vs paper {v['paper']:.1f}  OK")


if __name__ == "__main__":
    main()
