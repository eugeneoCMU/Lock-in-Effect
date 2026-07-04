"""
Single source of truth for the QT window and cap schedule.

Both frameworks (abm/ and hazard/) must import these bounds instead of
defining their own — duplicated window definitions were how the
post-QT-month drift bug crept into CPR means (see TECHNICAL.md §3,
Error 4).  The window is half-open: QT_START <= t < QT_END.

Aggregations (dollar sums, CPR means) must apply qt_active_mask() /
qt_active_frame() BEFORE aggregating, and should call
assert_qt_window_only() on the frame they are about to aggregate.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

QT_START = pd.Timestamp("2022-06-01")
QT_RAMP_END = pd.Timestamp("2022-09-01")  # full-pace QT begins Sep 2022
QT_END = pd.Timestamp("2025-12-01")       # exclusive — QT ended Dec 2025

QT_TARGET_RAMP_B = -17.5  # $17.5B/month during Jun–Aug 2022 ramp-up
QT_TARGET_FULL_B = -35.0  # $35B/month from Sep 2022 onward
POST_QT_TARGET_B = 0.0    # no balance-sheet shrink target after QT ends


def qt_active_mask(index: pd.DatetimeIndex) -> pd.Series:
    """Boolean mask for months when QT balance-sheet shrink was active."""
    return (index >= QT_START) & (index < QT_END)


def qt_active_frame(
    df: pd.DataFrame,
    delta_col: str = "Extension_Delta_Billions",
) -> pd.DataFrame:
    """Rows during active QT with valid extension deltas (headline aggregations)."""
    mask = qt_active_mask(df.index)
    return df.loc[mask].dropna(subset=[delta_col])


def assert_qt_window_only(index: pd.DatetimeIndex) -> None:
    """
    Raise if any timestamp lies outside [QT_START, QT_END).

    Call at the top of every aggregation over QT-window quantities so that
    an unmasked frame fails loudly instead of silently drifting the totals.
    """
    outside = ~qt_active_mask(index)
    if bool(np.asarray(outside).any()):
        bad = pd.DatetimeIndex(index)[np.asarray(outside)]
        raise ValueError(
            f"{len(bad)} row(s) outside the active QT window "
            f"[{QT_START.date()}, {QT_END.date()}): "
            f"{bad.min().date()} … {bad.max().date()}. "
            "Apply qt_active_mask()/qt_active_frame() before aggregating."
        )


def compute_qt_target_series(index: pd.DatetimeIndex) -> pd.Series:
    """
    Time-dependent QT roll-off target aligned to the index:
      * before QT_START               -> NaN  (no target regime)
      * QT_START <= t < QT_RAMP_END   -> -17.5B/month (ramp-up)
      * QT_RAMP_END <= t < QT_END     -> -35B/month  (full pace)
      * t >= QT_END                   -> 0B/month    (QT ended Dec 2025)
    """
    target = pd.Series(np.nan, index=index)
    ramp = (index >= QT_START) & (index < QT_RAMP_END)
    full = (index >= QT_RAMP_END) & (index < QT_END)
    target[ramp] = QT_TARGET_RAMP_B
    target[full] = QT_TARGET_FULL_B
    target[index >= QT_END] = POST_QT_TARGET_B
    return target


def expected_qt_active_months() -> int:
    """Number of months in [QT_START, QT_END) — must match qt_active_frame()."""
    probe = pd.date_range("2018-01-01", "2030-01-01", freq="ME")
    return int(qt_active_mask(probe).sum())
