"""Shared output paths for the ABM pipeline (anchor to this package directory)."""
from pathlib import Path

ABM_DIR = Path(__file__).resolve().parent

ABM_LOCKIN_RESULTS_CSV = ABM_DIR / "abm_lockin_results.csv"
ABM_CPR_SURFACE_CSV = ABM_DIR / "abm_cpr_surface.csv"
ABM_LOCKIN_SCURVE_PNG = ABM_DIR / "abm_lockin_scurve.png"
ABM_LOCKIN_RESULTS_VIZ_PNG = ABM_DIR / "abm_lockin_results_viz.png"
ABM_CPR_SURFACE_VIZ_PNG = ABM_DIR / "abm_cpr_surface_viz.png"
MBS_DASHBOARD_PNG = ABM_DIR / "mbs_extension_risk_dashboard.png"
CPR_DIAGNOSTIC_PNG = ABM_DIR / "cpr_diagnostic.png"
SENSITIVITY_RESULTS_CSV = ABM_DIR / "sensitivity_results.csv"
ROBUSTNESS_RESULTS_CSV = ABM_DIR / "robustness_results.csv"
MONTE_CARLO_RESULTS_CSV = ABM_DIR / "monte_carlo_results.csv"
MONTE_CARLO_HISTOGRAM_PNG = ABM_DIR / "monte_carlo_trapped_liquidity.png"
RUNS_DIR = ABM_DIR / "data" / "runs"
LATEST_RUN_MANIFEST = ABM_DIR / "data" / "latest_run_manifest.json"

# Monthly columns written by freeze_run.py for the active QT slice
QT_MONTHLY_EXPORT_COLS = [
    "MORTGAGE30US",
    "Dynamic_Friction",
    "Empirical_CPR_Pct",
    "US_CPR_Pct",
    "Danish_CPR_Pct",
    "Extension_Delta_Billions",
    "US_Missed_Rolloff_Billions",
    "Danish_Missed_Rolloff_Billions",
    "Actual_Monthly_Rolloff_Billions",
    "QT_Target_Billions",
]
