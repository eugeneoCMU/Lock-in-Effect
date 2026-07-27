"""
Regression tests for the shared QT window filter (common/qt_window.py).

Guards against the original Error-4 bug (TECHNICAL.md §3): summing all
months >= QT_START with no upper bound let post-QT rows drift the
aggregates.  A synthetic series with 8 months of large nonzero values
past QT_END must produce identical aggregates whether or not those rows
are present.

Run:  python3 -m pytest tests/  (or python3 tests/test_qt_window.py)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.qt_window import (
    QT_END,
    QT_START,
    assert_qt_window_only,
    compute_qt_target_series,
    expected_qt_active_months,
    qt_active_frame,
    qt_active_mask,
)


def _synthetic_frame(months_past_qt_end: int = 8) -> pd.DataFrame:
    """QT-era frame plus post-QT months carrying large nonzero deltas."""
    index = pd.date_range(
        QT_START,
        QT_END + pd.DateOffset(months=months_past_qt_end),
        freq="ME",
    )
    rng = np.random.default_rng(0)
    df = pd.DataFrame(
        {
            "Extension_Delta_Billions": rng.uniform(5.0, 25.0, len(index)),
            "Empirical_CPR_Pct": rng.uniform(2.0, 12.0, len(index)),
        },
        index=index,
    )
    # Post-QT rows get huge values: if they ever leak into an aggregate,
    # the totals shift by hundreds of billions and the test fails loudly.
    post_qt = df.index >= QT_END
    assert post_qt.sum() >= months_past_qt_end
    df.loc[post_qt, "Extension_Delta_Billions"] = 500.0
    df.loc[post_qt, "Empirical_CPR_Pct"] = 99.0
    return df


def test_aggregates_ignore_post_qt_rows():
    """Dollar sums and CPR means are unchanged by rows past QT_END."""
    with_tail = _synthetic_frame()
    without_tail = with_tail.loc[with_tail.index < QT_END]

    agg_with = qt_active_frame(with_tail)
    agg_without = qt_active_frame(without_tail)

    assert agg_with["Extension_Delta_Billions"].sum() == pytest.approx(
        agg_without["Extension_Delta_Billions"].sum()
    )
    assert agg_with["Empirical_CPR_Pct"].mean() == pytest.approx(
        agg_without["Empirical_CPR_Pct"].mean()
    )
    assert len(agg_with) == len(agg_without) == expected_qt_active_months()


def test_unbounded_qt_start_filter_would_drift():
    """The pre-fix filter (index >= QT_START, no upper bound) must disagree —
    proving this suite would have caught the original bug.

    HARDENED (suite-hardening pass). The inequality above compares two
    quantities BOTH derived from the module, so it holds for any upper bound
    the module happens to apply, including a wrong one: it fired under none of
    12 single-point mutants of common/qt_window.py. The added assertions pin
    the property that actually matters — the correct frame must contain no
    post-QT row AT ALL, which is checkable against the 500.0 sentinel these
    rows carry, and must have exactly the expected month count.
    """
    df = _synthetic_frame()
    buggy = df.loc[df.index >= QT_START]  # original Error-4 filter
    correct = qt_active_frame(df)
    assert buggy["Extension_Delta_Billions"].sum() > (
        correct["Extension_Delta_Billions"].sum() + 1000.0
    )
    # Not one sentinel row survived the filter.
    assert (correct["Extension_Delta_Billions"] < 500.0).all()
    assert (correct["Empirical_CPR_Pct"] < 99.0).all()
    assert len(correct) == expected_qt_active_months()
    assert correct.index.max() < QT_END
    assert correct.index.min() >= QT_START


def test_assert_qt_window_only_raises_on_unmasked_index():
    df = _synthetic_frame()
    with pytest.raises(ValueError, match="outside the active QT window"):
        assert_qt_window_only(df.index)


def test_assert_qt_window_only_passes_on_masked_index():
    """HARDENED: the original body only round-tripped the module's own mask
    through the module's own assertion, which agrees with itself under any
    bound (it fired under none of 12 mutants). The boundary probes below state
    where the guard must and must not raise, in calendar terms."""
    df = _synthetic_frame()
    assert_qt_window_only(qt_active_frame(df).index)

    # The last instant inside the window is accepted ...
    assert_qt_window_only(pd.DatetimeIndex([QT_END - pd.Timedelta(days=1)]))
    assert_qt_window_only(pd.DatetimeIndex([QT_START]))
    # ... and the exclusive upper bound itself is not.
    with pytest.raises(ValueError, match="outside the active QT window"):
        assert_qt_window_only(pd.DatetimeIndex([QT_END]))
    with pytest.raises(ValueError, match="outside the active QT window"):
        assert_qt_window_only(
            pd.DatetimeIndex([QT_START - pd.Timedelta(days=1)])
        )


def test_qt_mask_bounds_are_half_open():
    index = pd.DatetimeIndex(
        [
            QT_START - pd.DateOffset(months=1),
            QT_START,
            QT_END - pd.DateOffset(months=1),
            QT_END,
        ]
    )
    assert list(qt_active_mask(index)) == [False, True, True, False]


def test_qt_target_series_regimes():
    index = pd.date_range("2022-01-31", "2026-06-30", freq="ME")
    target = compute_qt_target_series(index)
    assert target[index < QT_START].isna().all()
    ramp = target[(index >= QT_START) & (index < pd.Timestamp("2022-09-01"))]
    assert (ramp == -17.5).all() and len(ramp) == 3
    full = target[(index >= pd.Timestamp("2022-09-01")) & (index < QT_END)]
    assert (full == -35.0).all()
    assert (target[index >= QT_END] == 0.0).all()


def test_frameworks_share_single_window_definition():
    """abm and hazard must expose the same objects, not copies.

    HARDENED: `is` identity is true for ANY value the shared object holds, so
    on its own this fired under none of 12 mutants — a re-export of a wrong
    date passes it. Identity is still the point (a copy would drift), but the
    shared object must additionally span the window the module's own mask
    selects, checked without restating the two dates (tests/
    test_qt_window_literals.py owns the literals).
    """
    import importlib

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "abm"))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hazard"))
    hazard_config = importlib.import_module("config")
    assert hazard_config.QT_START is QT_START
    assert hazard_config.QT_END is QT_END

    # The shared bounds and the shared mask must describe the same window:
    # every month the mask accepts lies in [QT_START, QT_END), the first
    # accepted month IS QT_START, and the count matches.
    probe = pd.date_range("2018-01-01", "2030-01-01", freq="MS")
    active = probe[qt_active_mask(probe)]
    assert active.min() == hazard_config.QT_START
    assert active.max() < hazard_config.QT_END
    assert (active.max() + pd.DateOffset(months=1)) == hazard_config.QT_END
    assert len(active) == expected_qt_active_months()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
