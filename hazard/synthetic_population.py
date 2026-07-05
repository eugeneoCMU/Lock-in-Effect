#!/usr/bin/env python3
"""
2.1 — Independently-calibrated synthetic loan population (no Freddie data).

Every covariate is drawn from an external, non-Freddie source so the resulting
75k population contains zero Freddie loan-level information — not even its
marginals. This is the symmetric companion to the ABM cross-design test
(§15 Fix 1): there, real covariates went into the behavioral ABM; here, a fully
synthetic population goes into the hazard framework's survival structure, to
test whether that structure — divorced from real data — still recovers the
$764.7B benchmark.

External calibration sources (all public, none Freddie loan-level):
  - coupon center by vintage: Freddie PMMS *annual-average* 30yr rate (a
    published market index, not loan-level microdata);
  - vintage weights: stylized origination-volume shares (2020-21 refi boom);
  - FICO at origination: stylized national origination buckets;
  - LTV at origination: stylized national distribution (mass near 80).
Alternative calibrations (2.3) are provided via CALIBRATIONS for sensitivity.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import polars as pl

from config import COUPON_STEP, LTV_THRESHOLD, N_LOANS, QT_START, RNG_SEED

# Freddie PMMS annual-average 30yr fixed rate (public index), decimal.
PMMS_ANNUAL = {2017: 0.0399, 2018: 0.0454, 2019: 0.0394, 2020: 0.0311, 2021: 0.0296}
COUPON_SD = 0.0045  # cross-sectional dispersion around the vintage mean

# Stylized origination-volume shares (refi boom concentrates in 2020-21).
VINTAGE_WEIGHTS = {2017: 0.10, 2018: 0.10, 2019: 0.15, 2020: 0.30, 2021: 0.35}

_STATES = ["CA", "TX", "FL", "NY", "PA", "IL", "OH", "GA", "NC", "WA",
           "AZ", "CO", "MI", "NJ", "VA"]

# 2.3 — alternative calibrations per covariate family for sensitivity.
CALIBRATIONS = {
    "baseline": {
        "fico": {"<680": 0.12, "680-740": 0.28, "740+": 0.60},
        "ltv_mean": 73.0, "ltv_sd": 14.0,
    },
    "alt_fico_looser": {  # more sub-740 (e.g. a purchase-heavy book)
        "fico": {"<680": 0.22, "680-740": 0.34, "740+": 0.44},
        "ltv_mean": 73.0, "ltv_sd": 14.0,
    },
    "alt_ltv_higher": {  # higher-LTV book (less equity)
        "fico": {"<680": 0.12, "680-740": 0.28, "740+": 0.60},
        "ltv_mean": 82.0, "ltv_sd": 12.0,
    },
}

_FICO_RANGES = {"<680": (620, 680), "680-740": (680, 740), "740+": (740, 820)}


def _fico_bucket(f):
    return np.where(f < 680, "<680", np.where(f < 740, "680-740", "740+"))


def _ltv_bucket(l):
    return np.where(l <= LTV_THRESHOLD, "≤80", ">80")


def _stratum_id(vintage, coupon, fico_bucket):
    cb = np.round(np.round(coupon / COUPON_STEP) * COUPON_STEP * 10000).astype(int)
    return np.array([f"{int(v)}_{c}_{fb}" for v, c, fb in zip(vintage, cb, fico_bucket)])


def build_synthetic_population(n: int = N_LOANS, seed: int = RNG_SEED,
                               calibration: str = "baseline") -> pl.DataFrame:
    rng = np.random.default_rng(seed)
    cal = CALIBRATIONS[calibration]

    vints = np.array(list(VINTAGE_WEIGHTS.keys()))
    vw = np.array(list(VINTAGE_WEIGHTS.values())); vw = vw / vw.sum()
    vintage = rng.choice(vints, size=n, p=vw)

    coupon = np.array([rng.normal(PMMS_ANNUAL[int(v)], COUPON_SD) for v in vintage])
    coupon = np.clip(coupon, 0.02, 0.07)

    fico_labels = list(cal["fico"].keys())
    fico_p = np.array(list(cal["fico"].values())); fico_p = fico_p / fico_p.sum()
    fico = np.empty(n)
    draws = rng.choice(len(fico_labels), size=n, p=fico_p)
    for i, lab in enumerate(fico_labels):
        lo, hi = _FICO_RANGES[lab]
        m = draws == i
        fico[m] = rng.integers(lo, hi, size=int(m.sum()))

    ltv = np.clip(rng.normal(cal["ltv_mean"], cal["ltv_sd"], n), 20, 97)

    # loan age at QT start (2022-06) from mid-vintage-year origination.
    age = np.array([(QT_START.year - int(v)) * 12 + (QT_START.month - 6)
                    for v in vintage]).clip(1, 240)

    orig_upb = rng.lognormal(np.log(300_000), 0.5, n)
    balance = orig_upb * rng.uniform(0.80, 0.98, n)  # partially amortized

    fb = _fico_bucket(fico)
    df = pd.DataFrame({
        "loan_id": [f"SYN{i:07d}" for i in range(n)],
        "stratum_id": _stratum_id(vintage, coupon, fb),
        "fico": fico.astype(int),
        "property_state": rng.choice(_STATES, size=n),
        "orig_ltv": ltv,
        "coupon": coupon,
        "orig_upb": orig_upb,
        "balance": balance,
        "loan_age": age.astype(int),
        "state": "Current",
        "vintage": vintage,
        "fico_bucket": fb,
        "ltv_bucket": _ltv_bucket(ltv),
        "weight": 1.0,
    })
    return pl.from_pandas(df)


def summary(df: pl.DataFrame) -> str:
    p = df.to_pandas()
    return (f"synthetic n={len(p):,}  WAC {p['coupon'].mean()*100:.2f}%  "
            f"age {p['loan_age'].mean():.0f}mo  LTV {p['orig_ltv'].mean():.0f}  "
            f"FICO {p['fico'].mean():.0f}  strata {p['stratum_id'].nunique()}")


if __name__ == "__main__":
    for c in CALIBRATIONS:
        print(f"[{c:16}] {summary(build_synthetic_population(calibration=c))}")
