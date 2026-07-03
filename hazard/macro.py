"""
FRED / SOMA / QT macro plumbing for the hazard framework.

Standalone port of the empirical side of abm/fed_mbs_extension_risk.py —
no ABM imports, no behavioral CPR surfaces.
"""

from __future__ import annotations

import json
import urllib.request
from typing import List, Optional

import numpy as np
import pandas as pd
from fredapi import Fred

from config import (
    BASE_FRICTION,
    BASELINE_START,
    FRED_API_KEY,
    POST_QT_TARGET_B,
    QT_END,
    QT_RAMP_END,
    QT_START,
    QT_TARGET_FULL_B,
    QT_TARGET_RAMP_B,
    SEARCH_PENALTY_CAP,
    SENTIMENT_BASELINE,
    SENTIMENT_PENALTY_CAP,
    SENTIMENT_PENALTY_PER_PT,
    START_DATE,
    TERM_MONTHS,
)

SOMA_SUMMARY_URL = (
    "https://markets.newyorkfed.org/api/soma/summary.json"
)


def qt_active_mask(index: pd.DatetimeIndex) -> pd.Series:
    return (index >= QT_START) & (index < QT_END)


def qt_active_frame(df: pd.DataFrame) -> pd.DataFrame:
    mask = qt_active_mask(df.index)
    return df.loc[mask].dropna(subset=["Extension_Delta_Billions"])


def compute_qt_target_series(index: pd.DatetimeIndex) -> pd.Series:
    target = pd.Series(np.nan, index=index)
    ramp = (index >= QT_START) & (index < QT_RAMP_END)
    full = (index >= QT_RAMP_END) & (index < QT_END)
    target[ramp] = QT_TARGET_RAMP_B
    target[full] = QT_TARGET_FULL_B
    target[index >= QT_END] = POST_QT_TARGET_B
    return target


def coupon_to_decimal(rate: float | np.ndarray) -> float | np.ndarray:
    """Freddie stores coupon as percent (e.g. 4.5); macro rates use decimal (0.045)."""
    arr = np.asarray(rate, dtype=np.float64)
    out = np.where(arr > 1.0, arr / 100.0, arr)
    if np.ndim(rate) == 0:
        return float(out)
    return out


def scheduled_amortization_smm(annual_rate: float, term_months: int,
                               months_elapsed: int) -> float:
    annual_rate = float(coupon_to_decimal(annual_rate))
    r = annual_rate / 12
    n, k = term_months, months_elapsed
    if r == 0:
        return 1.0 / (n - k) if k < n else 0.0
    growth_k, growth_n = (1 + r) ** k, (1 + r) ** n
    balance_ratio = (growth_n - growth_k) / (growth_n - 1)
    if balance_ratio <= 0:
        return 0.0
    payment_ratio = r * growth_n / (growth_n - 1)
    sched_principal = payment_ratio - r * balance_ratio
    return sched_principal / balance_ratio


def scheduled_amortization_series(
    index: pd.DatetimeIndex,
    coupon: float,
    origin: pd.Timestamp,
    term: int = TERM_MONTHS,
) -> pd.Series:
    months_since = np.clip(
        (index.year - origin.year) * 12 + (index.month - origin.month),
        a_min=0, a_max=None,
    )
    return pd.Series(
        [scheduled_amortization_smm(coupon, term, int(k)) for k in months_since],
        index=index,
    )


def calculate_dynamic_friction(
    df: pd.DataFrame,
    base_friction: float = BASE_FRICTION,
    search_penalty_cap: float = SEARCH_PENALTY_CAP,
    sentiment_penalty_cap: float = SENTIMENT_PENALTY_CAP,
) -> pd.DataFrame:
    df = df.copy()
    baseline = df.attrs.get("inventory_baseline", df["ACTLISCOUUS"].mean())
    inventory_min = df["ACTLISCOUUS"].min()
    shortfall = (baseline - df["ACTLISCOUUS"]).clip(lower=0.0)
    denom = baseline - inventory_min
    if denom <= 0:
        search_penalty = pd.Series(0.0, index=df.index)
    else:
        search_penalty = (search_penalty_cap * shortfall / denom).clip(
            upper=search_penalty_cap
        )
    sentiment_drop = (SENTIMENT_BASELINE - df["UMCSENT"]).clip(lower=0.0)
    sentiment_penalty = (sentiment_drop * SENTIMENT_PENALTY_PER_PT).clip(
        upper=sentiment_penalty_cap
    )
    df["Search_Penalty"] = search_penalty
    df["Sentiment_Penalty"] = sentiment_penalty
    df["Dynamic_Friction"] = base_friction + search_penalty + sentiment_penalty
    return df


def cpr_goodness_of_fit(empirical: pd.Series, predicted: pd.Series,
                        smooth_window: int = 3) -> dict:
    mask = empirical.notna() & predicted.notna()
    e, p = empirical[mask].to_numpy(), predicted[mask].to_numpy()

    def _stats(actual, pred):
        ss_res = ((actual - pred) ** 2).sum()
        ss_tot = ((actual - actual.mean()) ** 2).sum()
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
        rmse = np.sqrt(((actual - pred) ** 2).mean())
        mae = np.abs(actual - pred).mean()
        corr = np.corrcoef(actual, pred)[0, 1] if len(actual) > 1 else np.nan
        return {"r2": r2, "rmse": rmse, "mae": mae, "corr": corr, "n": len(actual)}

    raw = _stats(e, p)
    e_s = pd.Series(e).rolling(smooth_window, center=True, min_periods=1).mean()
    p_s = pd.Series(p).rolling(smooth_window, center=True, min_periods=1).mean()
    smoothed = _stats(e_s.to_numpy(), p_s.to_numpy())
    return {"raw": raw, "smoothed": smoothed}


def cpr_cross_correlation(empirical: pd.Series, predicted: pd.Series,
                          max_lag: int = 3) -> dict:
    mask = empirical.notna() & predicted.notna()
    e = empirical[mask].to_numpy()
    p = predicted[mask].to_numpy()
    out = {}
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            e_s, p_s = e[:lag], p[-lag:]
        elif lag == 0:
            e_s, p_s = e, p
        else:
            e_s, p_s = e[lag:], p[:-lag]
        if len(e_s) < 5:
            continue
        out[lag] = float(np.corrcoef(e_s, p_s)[0, 1])
    return out


def fetch_soma_mbs_monthly(start: str = START_DATE,
                           url: str = SOMA_SUMMARY_URL) -> Optional[pd.Series]:
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read())["soma"]["summary"]
    except Exception as exc:
        print(f"NY Fed SOMA API unavailable ({exc}); using WSHOMCB diffs.")
        return None

    records = []
    for row in payload:
        mbs_val = row.get("mbs")
        if not mbs_val or mbs_val == "0.00":
            continue
        records.append({
            "date": pd.Timestamp(row["asOfDate"]),
            "mbs_b": float(mbs_val) / 1e9,
        })
    if not records:
        return None

    weekly = (pd.DataFrame(records).set_index("date").sort_index().loc[start:])
    monthly_mbs = weekly["mbs_b"].resample("ME").last()
    rolloff = monthly_mbs.diff()
    rolloff.name = "SOMA_Monthly_Rolloff_Billions"
    print(f"SOMA MBS monthly roll-off loaded ({len(rolloff.dropna())} months)")
    return rolloff


def fetch_data(api_key: str = FRED_API_KEY, start: str = START_DATE) -> pd.DataFrame:
    fred = Fred(api_key=api_key)
    mbs = fred.get_series("WSHOMCB", observation_start=start)
    rate = fred.get_series("MORTGAGE30US", observation_start=BASELINE_START)
    mbs.name, rate.name = "WSHOMCB", "MORTGAGE30US"

    df = pd.merge(mbs, rate, how="outer", left_index=True, right_index=True)
    df.sort_index(inplace=True)
    df.ffill(inplace=True)
    df.dropna(inplace=True)

    monthly = pd.DataFrame({
        "WSHOMCB": df["WSHOMCB"].resample("ME").last(),
        "MORTGAGE30US": df["MORTGAGE30US"].resample("ME").mean(),
    })
    monthly.dropna(inplace=True)

    inventory = fred.get_series("ACTLISCOUUS", observation_start=BASELINE_START)
    sentiment = fred.get_series("UMCSENT", observation_start=BASELINE_START)
    inventory_m = inventory.resample("ME").last()
    sentiment_m = sentiment.resample("ME").mean()
    base_slice = inventory_m.loc["2017-01-01":"2019-12-31"]
    inventory_baseline = float(base_slice.mean())

    monthly["ACTLISCOUUS"] = inventory_m.reindex(monthly.index).ffill().bfill()
    monthly["UMCSENT"] = sentiment_m.reindex(monthly.index).ffill().bfill()
    monthly.attrs["inventory_baseline"] = inventory_baseline
    monthly.attrs["MORTGAGE30US_EXTENDED"] = rate.resample("ME").mean().ffill()
    print(f"FRED loaded; inventory baseline = {inventory_baseline:,.0f}")
    return monthly


def build_empirical_metrics(
    macro_df: pd.DataFrame,
    soma_rolloff: Optional[pd.Series] = None,
    sched_smm: Optional[pd.Series] = None,
) -> pd.DataFrame:
    """Empirical extension deltas and CPR back-out (no hazard simulation)."""
    df = macro_df.copy()
    if soma_rolloff is not None:
        df["Actual_Monthly_Rolloff_Billions"] = soma_rolloff.reindex(df.index)
        df["Rolloff_Source"] = "SOMA"
    else:
        df["Actual_Monthly_Rolloff_Billions"] = df["WSHOMCB"].diff() / 1_000
        df["Rolloff_Source"] = "WSHOMCB"

    df["QT_Target_Billions"] = compute_qt_target_series(df.index)
    qt_active = qt_active_mask(df.index)

    df["Extension_Delta_Billions"] = np.where(
        df.index >= QT_START,
        df["Actual_Monthly_Rolloff_Billions"] - df["QT_Target_Billions"],
        np.nan,
    )
    trapped = df["Extension_Delta_Billions"].fillna(0.0).where(qt_active, 0.0)
    df["Cumulative_Trapped_Liquidity"] = trapped.cumsum()
    df.loc[df.index < QT_START, "Cumulative_Trapped_Liquidity"] = np.nan

    df = calculate_dynamic_friction(df)
    holdings_b = df["WSHOMCB"] / 1_000
    if sched_smm is None:
        sched_smm = scheduled_amortization_series(
            df.index, coupon=0.025, origin=pd.Timestamp("2020-06-01")
        )
    df["Scheduled_Amort_SMM"] = sched_smm
    actual_abs = df["Actual_Monthly_Rolloff_Billions"].abs()
    empirical_smm = (actual_abs / holdings_b) - sched_smm
    df["Empirical_CPR_Pct"] = (empirical_smm.clip(lower=0) * 12 * 100)
    return df
