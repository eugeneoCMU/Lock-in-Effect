"""Paths, cohort buckets, and QT constants for the hazard framework."""
from pathlib import Path

import pandas as pd

HAZARD_DIR = Path(__file__).resolve().parent
DATA_DIR = HAZARD_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PANEL_PATH = DATA_DIR / "cohort_month_panel.parquet"
HAZARD_COEF_PATH = DATA_DIR / "hazard_coefficients.json"
MARKOV_MATRIX_PATH = DATA_DIR / "markov_transition_matrix.parquet"
SIM_RESULTS_PATH = DATA_DIR / "simulation_results.parquet"
LOAN_SAMPLE_PATH = DATA_DIR / "loan_sample.parquet"
MICROSIM_RESULTS_PATH = DATA_DIR / "microsim_results.parquet"
EXTENSION_RISK_PNG = DATA_DIR / "extension_risk_dashboard.png"
CPR_DIAGNOSTIC_PNG = DATA_DIR / "cpr_diagnostic.png"

# Literature microsim
N_LOANS = 75_000
RNG_SEED = 42
BASELINE_MODE = "psa"  # "psa" | "weibull"
PSA_SPEED = 100.0
# Fractional SMM prepay (matches cohort simulate.py); "absorbing" = Bernoulli full payoff
PREPAY_MODE = "fractional"

# Rothstein quarterly mobility decline per 100bp rate gap (probability scale)
ROTHSTEIN_Q_DECLINE_LOW = 0.055
ROTHSTEIN_Q_DECLINE_MID = 0.065
ROTHSTEIN_Q_DECLINE_HIGH = 0.077
# Reference baseline quarterly mobility probability (turnover proxy)
P_Q_BASELINE = 0.06

# Involuntary turnover floor (death, divorce, relocation) — annual CPR %
INVOLUNTARY_CPR_ANNUAL = 0.04

LITERATURE_COEFS = {
    "beta_burnout": -0.5,
    "beta_fico": -0.15,
    "beta_ltv": 0.10,
    "h0_default_monthly": 0.0003,
    "gamma_rate_stress": 2.0,
    "gamma_fico": -0.20,
    "gamma_ltv": 0.25,
}

# FRED / QT (aligned with abm/fed_mbs_extension_risk.py empirical benchmark)
FRED_API_KEY = "0da55cec06bcff18594e15cc9da17d2d"
START_DATE = "2021-01-01"
BASELINE_START = "2017-01-01"
QT_START = pd.Timestamp("2022-06-01")
QT_RAMP_END = pd.Timestamp("2022-09-01")
QT_END = pd.Timestamp("2025-12-01")
QT_TARGET_RAMP_B = -17.5
QT_TARGET_FULL_B = -35.0
POST_QT_TARGET_B = 0.0
EMPIRICAL_TRAPPED_B = 764.7  # active QT window SOMA benchmark (July 2026)

# Dynamic friction
BASE_FRICTION = 0.07
SEARCH_PENALTY_CAP = 0.02
SENTIMENT_BASELINE = 85.0
SENTIMENT_PENALTY_PER_PT = 0.0005
SENTIMENT_PENALTY_CAP = 0.015

# Cohort bucket definitions
FICO_BINS = [(0, 680, "<680"), (680, 740, "680-740"), (740, 851, "740+")]
LTV_THRESHOLD = 80
COUPON_STEP = 0.005  # 0.5% buckets
TERM_MONTHS = 360

# Hazard model
HOLDOUT_DATE = pd.Timestamp("2024-01-01")
AGE_SPLINE_KNOTS = [12, 24, 36, 60, 84, 120]
RATE_GAP_UNITS = "bps"
RIDGE_ALPHA = 1e-5  # stratum FE makes IRLS ill-conditioned; mild ridge required
RIDGE_ALPHA_GRID = [1e-5, 1e-4]

# Markov servicer pipeline states
MARKOV_STATES = [
    "Current",
    "D30",
    "D60",
    "D90+",
    "Forbearance",
    "Prepaid",
    "Defaulted",
    "Liquidated",
]

# Freddie file naming (sample: orig_2017.txt / perf_2017.txt; quarterly: orig_2020Q1.txt)
VINTAGE_YEARS = list(range(2017, 2022))
