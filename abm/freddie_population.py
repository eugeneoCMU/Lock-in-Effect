"""
Freddie Mac structural-covariate population for the ABM cross-design test.

Scope (pre-registered, see TECHNICAL.md §15 Fix 1): ONLY structural
covariates transfer from the Freddie sample to ABM households — per-loan
coupon, loan age (from vintage), and original LTV enter the decision rules;
FICO bucket and property state are carried for diagnostics but have no
analogue in the ABM's gates. Behavioral draws (income, home value, mobility
desire, transaction-cost offset, patience) remain synthetic with the same
distributions and seed as the default population, so the only varying input
between --population=synthetic and --population=freddie is the structural
covariate set. This test must NOT be overclaimed as "fully real" agents.

Reuses the same 75k stratified loan sample already ingested for the hazard
framework (hazard/loan_sample.py output).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[1]
LOAN_SAMPLE_PARQUET = _REPO_ROOT / "hazard" / "data" / "loan_sample.parquet"

FREDDIE_TERM_YEARS = 30  # Freddie sample is 30-year fixed originations


def load_freddie_structural_sample(
    n_households: int,
    seed: int = 42,
    parquet_path: Path = LOAN_SAMPLE_PARQUET,
) -> pd.DataFrame:
    """
    Draw n_households loans (balance-weighted, without replacement) from the
    hazard framework's stratified 75k sample and return the structural
    covariate frame: coupon (decimal), loan_age (months), orig_ltv (pct),
    fico, state, stratum_id.

    Balance weighting matches how the loans contribute to pool-level CPR —
    the same convention the microsim uses via UPB-weighted prepay.
    """
    if not parquet_path.exists():
        raise FileNotFoundError(
            f"{parquet_path} not found — run the hazard pipeline first "
            "(hazard/loan_sample.py builds it)."
        )
    loans = pd.read_parquet(parquet_path)

    rng = np.random.default_rng(seed)
    weights = loans["balance"].clip(lower=1.0).to_numpy()
    weights = weights / weights.sum()
    n = min(n_households, len(loans))
    idx = rng.choice(len(loans), size=n, replace=False, p=weights)
    sample = loans.iloc[idx].reset_index(drop=True)

    coupon = sample["coupon"].to_numpy(dtype=float)
    coupon = np.where(coupon > 1.0, coupon / 100.0, coupon)  # pct → decimal

    return pd.DataFrame({
        "coupon": coupon,
        "loan_age": sample["loan_age"].fillna(36).astype(int),
        "orig_ltv": sample["orig_ltv"].fillna(80).astype(float),
        "fico": sample["fico"].fillna(700).astype(float),
        "state": sample.get("property_state", pd.Series(["CA"] * n)),
        "stratum_id": sample["stratum_id"].astype(str),
    })


def attach_freddie_covariates(engine, loans: pd.DataFrame) -> None:
    """
    Rebind each ABM household's mortgage to a real Freddie loan's structural
    covariates. Behavioral draws are untouched. Principal uses the loan's
    real original LTV against the household's synthetic home value (replacing
    the fixed 0.80 LTV assumption); coupon and seasoning come from the loan.

    Loan ages are clipped so at least 12 months of term remain — the ABM's
    payment math is undefined at term end.
    """
    from abm_lockin_simulation import Mortgage  # local import: avoid cycle

    n = len(engine.households)
    if len(loans) < n:
        raise ValueError(
            f"Need {n} loans for {n} households, got {len(loans)}"
        )
    term_months = FREDDIE_TERM_YEARS * 12
    ages = loans["loan_age"].to_numpy()[:n].clip(0, term_months - 12)
    coupons = loans["coupon"].to_numpy()[:n]
    ltvs = (loans["orig_ltv"].to_numpy()[:n] / 100.0).clip(0.20, 1.00)

    for i, h in enumerate(engine.households):
        principal = ltvs[i] * h.current_home_value
        h.mortgage = Mortgage(
            principal,
            float(coupons[i]),
            term_years=FREDDIE_TERM_YEARS,
            months_elapsed=int(ages[i]),
        )

    engine._population_label = "freddie"
    engine._precompute_arrays()


def population_summary(loans: pd.DataFrame) -> str:
    wac = float(np.average(loans["coupon"]))
    return (
        f"Freddie structural population: n={len(loans):,}  "
        f"WAC {wac*100:.2f}%  "
        f"age {loans['loan_age'].mean():.0f}mo  "
        f"LTV {loans['orig_ltv'].mean():.0f}  "
        f"FICO {loans['fico'].mean():.0f}"
    )
