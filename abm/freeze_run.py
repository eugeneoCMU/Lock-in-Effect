#!/usr/bin/env python3
"""
Freeze a tagged production ABM run: manifest JSON, monthly QT CSV, figures.

All headline numbers in docs and the paper should match the manifest for the
cited run tag.  Aggregation always uses qt_active_frame() (42 months:
June 2022 – November 2025); never index >= QT_START alone (that includes
post-QT months and drifts CPR means).

Usage:
    python3 freeze_run.py
    python3 freeze_run.py --tag run-2026-07-04 --skip-figures
"""
from typing import List, Optional
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import fed_mbs_extension_risk as fed
from common.berger_calibration import get_us_transplant_refi
from paths import (
    ABM_CPR_SURFACE_CSV,
    ABM_DIR,
    CPR_DIAGNOSTIC_PNG,
    LATEST_RUN_MANIFEST,
    MBS_DASHBOARD_PNG,
    QT_MONTHLY_EXPORT_COLS,
    RUNS_DIR,
)


def _git_head() -> Optional[str]:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ABM_DIR.parent,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _sha256(path: Path) -> Optional[str]:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _json_default(obj):
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if hasattr(obj, "item"):
        return obj.item()
    raise TypeError(f"Not JSON-serializable: {type(obj)}")


def _sanitize_for_json(obj):
    """Recursively convert Timestamps and numpy scalars for JSON."""
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(v) for v in obj]
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if hasattr(obj, "item"):
        return obj.item()
    return obj


def freeze_run(
    tag: str,
    *,
    skip_figures: bool = False,
    apply_settlement_lag_kernel: bool = True,
) -> Path:
    run_dir = RUNS_DIR / tag
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"Running production pipeline for tag {tag!r} …")
    df, calib = fed.build_production_metrics(
        apply_settlement_lag_kernel=apply_settlement_lag_kernel,
    )

    if not skip_figures:
        print("Writing figures …")
        fed.plot_dashboard(df)
        fed.plot_cpr_diagnostic(df)
        for src in (MBS_DASHBOARD_PNG, CPR_DIAGNOSTIC_PNG):
            if src.is_file():
                shutil.copy2(src, run_dir / src.name)

    metrics = fed.export_headline_metrics(df)
    qt_df = fed.qt_active_frame(df)
    cols = [c for c in QT_MONTHLY_EXPORT_COLS if c in qt_df.columns]
    monthly_path = run_dir / "metrics_monthly.csv"
    qt_df[cols].to_csv(monthly_path, date_format="%Y-%m-%d")

    manifest = {
        "run_tag": tag,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_head(),
        "pipeline": _sanitize_for_json({
            "script": "freeze_run.py",
            "module": "fed_mbs_extension_risk.build_production_metrics",
            "apply_settlement_lag_kernel": apply_settlement_lag_kernel,
            # Sweepable module global (common/berger_calibration.py) that
            # drives the sign of the institutional gap (§20.1); record it or
            # the manifest under-specifies the run.
            "us_transplant_refi_annual": get_us_transplant_refi(),
            **calib,
        }),
        "inputs": {
            "abm_cpr_surface_csv": str(ABM_CPR_SURFACE_CSV.name),
            "abm_cpr_surface_sha256": _sha256(ABM_CPR_SURFACE_CSV),
        },
        "metrics": metrics,
        "artifacts": {
            "metrics_monthly_csv": monthly_path.name,
            "dashboard_png": MBS_DASHBOARD_PNG.name if not skip_figures else None,
            "cpr_diagnostic_png": (
                CPR_DIAGNOSTIC_PNG.name if not skip_figures else None
            ),
        },
    }

    manifest_path = run_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=_json_default)
        f.write("\n")

    LATEST_RUN_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(manifest_path, LATEST_RUN_MANIFEST)

    fed.print_summary(df)

    m = metrics["dollars_b"]
    c = metrics["cpr_pct"]
    w = c["wedge_dk_minus_us_pp"]
    print(f"Frozen → {manifest_path}")
    print(f"Latest symlink copy → {LATEST_RUN_MANIFEST}")
    print(
        f"Headlines: US trapped ${m['us_trapped']:.1f}B | "
        f"Danish ${m['danish_trapped']:.1f}B | gap ${m['institutional_gap']:.1f}B | "
        f"CPR {c['us_abm']['mean']:.2f}% / {c['empirical']['mean']:.2f}% / "
        f"DK {c['danish']['mean']:.2f}% | wedge {w['mean']:.2f}pp"
    )
    return manifest_path


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tag",
        default=datetime.now(timezone.utc).strftime("run-%Y-%m-%d"),
        help="Run directory name under abm/data/runs/ (default: run-YYYY-MM-DD)",
    )
    parser.add_argument(
        "--skip-figures",
        action="store_true",
        help="Skip dashboard / CPR diagnostic PNG generation",
    )
    parser.add_argument(
        "--no-settlement-lag",
        action="store_true",
        help="Disable settlement-lag kernel (sensitivity comparison only)",
    )
    args = parser.parse_args(argv)

    try:
        freeze_run(
            args.tag,
            skip_figures=args.skip_figures,
            apply_settlement_lag_kernel=not args.no_settlement_lag,
        )
    except Exception as exc:
        print(f"freeze_run failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
