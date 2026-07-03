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
