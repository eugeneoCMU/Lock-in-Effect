"""
INDEPENDENT-LITERAL gates on the QT window (common/qt_window.py).

Why this file exists (audit MISSING #4). Every test in tests/test_qt_window.py
derives its expectation from the very constants it is checking: the synthetic
index is built from QT_START/QT_END, the month count is compared against
expected_qt_active_months(), and the framework-sharing test asserts identity
(`is`) rather than value. Change QT_END to any other date and all seven still
pass. That suite tests the SHAPE of the window (half-open, masked before
aggregation) but pins none of its VALUES.

Everything below is a hardcoded literal traceable to an external source, never
re-derived from the module. Sources:

  * QT start, 1 June 2022, and the three-month ramp to full pace in September
    2022 — FOMC, "Plans for Reducing the Size of the Federal Reserve's Balance
    Sheet" (issued with the 4 May 2022 statement): runoff begins 1 June 2022;
    agency-MBS cap $17.5B/month for the first three months, $35B/month
    thereafter.
  * QT end, 1 December 2025 (exclusive) — the balance-sheet runoff end date
    this project's window adopts; the last ACTIVE month is November 2025.
  * 42 active months — counted by hand below from those two dates, month by
    month, without calling anything in the module under test.

Run with: python3 -m pytest tests/test_qt_window_literals.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from common import qt_window as qw

# --------------------------------------------------------------------------
# Hand-counted active months: June 2022 through November 2025 inclusive.
#   2022: Jun..Dec  =  7
#   2023: Jan..Dec  = 12
#   2024: Jan..Dec  = 12
#   2025: Jan..Nov  = 11
#                     --
#                     42
# Written out as an explicit literal list so the count is auditable and owes
# nothing to qt_active_mask().
# --------------------------------------------------------------------------
_ACTIVE_MONTHS_LITERAL = (
    [(2022, m) for m in range(6, 13)]
    + [(2023, m) for m in range(1, 13)]
    + [(2024, m) for m in range(1, 13)]
    + [(2025, m) for m in range(1, 12)]
)
EXPECTED_ACTIVE_MONTHS = 42


def test_hand_count_is_internally_consistent_and_brackets_the_module_bounds():
    """Guard the literal itself: 7 + 12 + 12 + 11 = 42, no duplicates.

    The first four assertions are a check on this file's own fixture and can
    fail only if someone edits the literal — they say nothing about
    common/qt_window.py. The last two connect the fixture to the module
    ARITHMETICALLY rather than by re-deriving it: QT_START must BE the first
    hand-counted month, and QT_END must be the month immediately after the
    last one (that is what 'exclusive' means). Stated this way the guard
    also fires on a shifted bound, instead of being pure self-consistency.
    """
    assert len(_ACTIVE_MONTHS_LITERAL) == EXPECTED_ACTIVE_MONTHS
    assert len(set(_ACTIVE_MONTHS_LITERAL)) == EXPECTED_ACTIVE_MONTHS
    assert _ACTIVE_MONTHS_LITERAL[0] == (2022, 6)
    assert _ACTIVE_MONTHS_LITERAL[-1] == (2025, 11)

    first, last = _ACTIVE_MONTHS_LITERAL[0], _ACTIVE_MONTHS_LITERAL[-1]
    assert (qw.QT_START.year, qw.QT_START.month) == first
    after_last = pd.Timestamp(year=last[0], month=last[1], day=1) + \
        pd.DateOffset(months=1)
    assert qw.QT_END == after_last


def test_qt_start_is_the_announced_runoff_start():
    """FOMC 4 May 2022 balance-sheet plan: runoff begins 1 June 2022."""
    assert qw.QT_START == pd.Timestamp("2022-06-01")


def test_qt_ramp_end_is_the_announced_full_pace_month():
    """Caps step to full pace in September 2022 (after three ramp months)."""
    assert qw.QT_RAMP_END == pd.Timestamp("2022-09-01")


def test_qt_end_is_december_2025_exclusive():
    """QT_END is EXCLUSIVE: the last active month is November 2025."""
    assert qw.QT_END == pd.Timestamp("2025-12-01")


def test_expected_qt_active_months_is_42():
    """Literal, not `len(qt_active_frame(...))`. A shifted QT_END fails here."""
    assert qw.expected_qt_active_months() == EXPECTED_ACTIVE_MONTHS


def test_expected_qt_active_months_is_derived_from_the_bounds_not_hardcoded():
    """The count must be COMPUTED from the window, not asserted to be 42.

    HOLE (adversarial mutation pass). Replacing the whole body with
    `return 42` fired no test: the literal above is satisfied by the constant,
    and the docstring's own promise ("must match qt_active_frame()") was
    checked nowhere. That decouples the count from the bounds, so the function
    keeps answering 42 after the window moves — exactly the drift the module
    exists to prevent. Assert the contract instead: the number this returns is
    the number of months qt_active_mask() actually accepts, whatever they are.
    """
    probe = pd.date_range("2018-01-01", "2030-01-01", freq="ME")
    assert qw.expected_qt_active_months() == int(qw.qt_active_mask(probe).sum())

    # And it tracks a moved window rather than answering from memory.
    import unittest.mock as mock

    with mock.patch.object(qw, "QT_END", pd.Timestamp("2025-06-01")):
        moved = qw.expected_qt_active_months()
    assert moved == EXPECTED_ACTIVE_MONTHS - 6  # Jun-Nov 2025 dropped
    assert qw.expected_qt_active_months() == EXPECTED_ACTIVE_MONTHS  # restored


def test_mask_selects_exactly_the_hand_counted_month_list():
    """The strongest form: every month from 2021-01 to 2027-12 is classified,
    and the ACTIVE set must equal the hand-written literal set exactly."""
    probe = pd.date_range("2021-01-01", "2027-12-01", freq="MS")
    mask = qw.qt_active_mask(probe)
    got = {(ts.year, ts.month) for ts in probe[mask]}
    assert got == set(_ACTIVE_MONTHS_LITERAL)


def test_ramp_months_are_exactly_june_july_august_2022():
    """Three ramp months at the $17.5B cap; September 2022 is already full pace."""
    probe = pd.date_range("2021-01-01", "2027-12-01", freq="MS")
    target = qw.compute_qt_target_series(probe)
    ramp_months = {(ts.year, ts.month) for ts in probe[target == -17.5]}
    assert ramp_months == {(2022, 6), (2022, 7), (2022, 8)}


def test_cap_levels_are_the_announced_dollar_figures():
    """$17.5B/month ramp, $35B/month full pace — signed negative (roll-off)."""
    assert qw.QT_TARGET_RAMP_B == -17.5
    assert qw.QT_TARGET_FULL_B == -35.0
    assert qw.POST_QT_TARGET_B == 0.0


@pytest.mark.parametrize(
    "date,expected",
    [
        # Independently stated boundary facts, one row per external claim.
        ("2022-05-01", None),    # month before runoff begins: no target regime
        ("2022-06-01", -17.5),   # first runoff month, ramp cap
        ("2022-08-01", -17.5),   # last ramp month
        ("2022-09-01", -35.0),   # full pace begins
        ("2025-11-01", -35.0),   # last active month, still full pace
        ("2025-12-01", 0.0),     # QT over
        ("2026-06-01", 0.0),
    ],
)
def test_target_series_at_named_calendar_dates(date, expected):
    idx = pd.DatetimeIndex([pd.Timestamp(date)])
    got = qw.compute_qt_target_series(idx).iloc[0]
    if expected is None:
        assert pd.isna(got)
    else:
        assert got == expected


@pytest.mark.parametrize(
    "date,active",
    [
        ("2022-05-31", False),  # day before the window opens
        ("2022-06-01", True),   # inclusive lower bound
        ("2025-11-30", True),   # last instant inside
        ("2025-12-01", False),  # exclusive upper bound
    ],
)
def test_window_is_half_open_at_named_calendar_dates(date, active):
    """Same half-open property test_qt_window.py has, but anchored to literal
    dates, so it fails on a wrong bound as well as on a wrong inequality."""
    idx = pd.DatetimeIndex([pd.Timestamp(date)])
    assert bool(qw.qt_active_mask(idx)[0]) is active


def test_hazard_config_reexports_the_literal_dates_not_just_the_object():
    """test_qt_window.py asserts `hazard_config.QT_START is QT_START`, which
    holds for any value. Assert the VALUES too, so a hazard-side override to a
    different date is caught even if it re-exports by reference."""
    import importlib

    sys.path.insert(0, str(_REPO_ROOT / "hazard"))
    cfg = importlib.import_module("config")
    assert cfg.QT_START == pd.Timestamp("2022-06-01")
    assert cfg.QT_END == pd.Timestamp("2025-12-01")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
