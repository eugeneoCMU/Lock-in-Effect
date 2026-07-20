"""
Regression tests for `extension_risk.score_extension_risk` — the function that
produces `hazard_trapped_b` and `share_explained_pct`, i.e. the $B and pp
quantities the manuscript reports.

Before this file the function had no test at all: a mutation audit introduced
three mutants against it and the whole suite (plus every liveness gate) stayed
green.  The three mutants, and the tests that kill them:

  (a) numerator/denominator swap in `share_explained_pct`
      -> TestShareExplained
  (b) sign flip on the `qt_target` subtraction
      -> TestQtTargetSubtraction
  (c) off-by-one / wrong-window aggregation in `hazard_trapped_b`
      -> TestTrappedAggregation

Every expected value below is derived arithmetically inside the test from the
test's own synthetic inputs, never read back from an artifact.

Run:  python3 -m pytest tests/test_extension_risk_scoring.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "hazard"))

from common.qt_window import (  # noqa: E402
    QT_END,
    QT_START,
    QT_TARGET_FULL_B,
    QT_TARGET_RAMP_B,
)
from extension_risk import score_extension_risk  # noqa: E402


# Twelve months fully inside the active QT window: 2022-06 .. 2023-05.
# The first three are ramp months (-17.5B/mo target), the rest full pace
# (-35B/mo), so any mutant that treats the target as a constant also dies.
QT_MONTHS = pd.date_range("2022-06-01", periods=12, freq="MS")
RAMP_N = 3
FULL_N = 9
TARGETS = np.array([QT_TARGET_RAMP_B] * RAMP_N + [QT_TARGET_FULL_B] * FULL_N)

# Deterministic, non-constant CPR series so the goodness-of-fit and
# cross-correlation legs are exercised but never drive an assertion here.
EMP_CPR = np.array([6.0, 5.5, 5.0, 4.6, 4.3, 4.1, 4.0, 4.2, 4.5, 4.9, 5.4, 6.1])
SIM_CPR = EMP_CPR * 0.8 + 0.3


def _empirical(
    deltas: np.ndarray,
    months: pd.DatetimeIndex = QT_MONTHS,
    targets: np.ndarray | None = None,
    pad_outside: bool = True,
) -> pd.DataFrame:
    """
    Empirical frame in the shape `score_extension_risk` consumes.

    When `pad_outside` is set, rows are added before QT_START and after QT_END
    carrying deliberately huge deltas and targets.  A correctly masked
    aggregation ignores them entirely; an unmasked one is off by thousands.
    """
    df = pd.DataFrame(
        {
            "Extension_Delta_Billions": np.asarray(deltas, dtype=float),
            "QT_Target_Billions": (
                TARGETS if targets is None else np.asarray(targets, dtype=float)
            ),
            "Empirical_CPR_Pct": EMP_CPR[: len(months)],
        },
        index=months,
    )
    if not pad_outside:
        return df
    outside = pd.DatetimeIndex(
        [QT_START - pd.DateOffset(months=k) for k in (3, 2, 1)]
        + [QT_END, QT_END + pd.DateOffset(months=1)]
    )
    pad = pd.DataFrame(
        {
            "Extension_Delta_Billions": np.full(len(outside), -1_000.0),
            "QT_Target_Billions": np.full(len(outside), -1_000.0),
            "Empirical_CPR_Pct": np.full(len(outside), 99.0),
        },
        index=outside,
    )
    return pd.concat([df, pad]).sort_index()


def _sim(
    rolloff: np.ndarray,
    months: pd.DatetimeIndex = QT_MONTHS,
    pad_outside: bool = True,
) -> pd.DataFrame:
    """Simulated frame; padded outside the window with large decoy roll-off."""
    df = pd.DataFrame(
        {
            "simulated_rolloff_b": np.asarray(rolloff, dtype=float),
            "hazard_cpr_pct": SIM_CPR[: len(months)],
        },
        index=months,
    )
    if not pad_outside:
        return df
    outside = pd.DatetimeIndex(
        [QT_START - pd.DateOffset(months=k) for k in (3, 2, 1)]
        + [QT_END, QT_END + pd.DateOffset(months=1)]
    )
    pad = pd.DataFrame(
        {
            "simulated_rolloff_b": np.full(len(outside), -1_000.0),
            "hazard_cpr_pct": np.full(len(outside), 99.0),
        },
        index=outside,
    )
    return pd.concat([df, pad]).sort_index()


class TestShareExplained:
    """Mutant (a): share_explained_pct numerator/denominator swap."""

    def test_share_is_simulated_over_empirical(self):
        """
        share = hazard / empirical * 100, not its reciprocal.

        Inputs are chosen so the two readings are far apart and neither is
        near 100: empirical -120B, hazard -30B -> 25%, swapped -> 400%.
        """
        emp = _empirical(np.full(12, -10.0))
        # roll-off = target - 2.5 each month => trapped = -2.5 * 12 = -30
        sim = _sim(TARGETS - 2.5)

        r = score_extension_risk(sim, emp)

        assert r["empirical_trapped_b"] == pytest.approx(-120.0)
        assert r["hazard_trapped_b"] == pytest.approx(-30.0)
        assert r["share_explained_pct"] == pytest.approx(25.0)
        # The swapped reading, stated explicitly so the intent is unambiguous.
        assert r["share_explained_pct"] != pytest.approx(400.0)

    def test_share_is_consistent_with_the_reported_components(self):
        """
        The published share must be reconstructible from the two published
        dollar figures.  This is the general form of the swap check: it holds
        for any inputs and fails for any mutant that reorders the ratio.
        """
        emp = _empirical(np.linspace(-4.0, -18.0, 12))
        sim = _sim(TARGETS - np.linspace(1.0, 6.0, 12))

        r = score_extension_risk(sim, emp)

        assert r["share_explained_pct"] == pytest.approx(
            r["hazard_trapped_b"] / r["empirical_trapped_b"] * 100.0
        )

    def test_partial_recovery_is_under_one_hundred_percent(self):
        """A model trapping less than the benchmark explains under 100%."""
        emp = _empirical(np.full(12, -10.0))
        sim = _sim(TARGETS - 1.0)  # trapped -12B against -120B empirical

        r = score_extension_risk(sim, emp)

        assert abs(r["hazard_trapped_b"]) < abs(r["empirical_trapped_b"])
        assert r["share_explained_pct"] < 100.0
        assert r["share_explained_pct"] == pytest.approx(10.0)

    def test_over_recovery_exceeds_one_hundred_percent(self):
        """Mirror case: trapping more than the benchmark must exceed 100%."""
        emp = _empirical(np.full(12, -10.0))
        sim = _sim(TARGETS - 15.0)  # trapped -180B against -120B empirical

        r = score_extension_risk(sim, emp)

        assert abs(r["hazard_trapped_b"]) > abs(r["empirical_trapped_b"])
        assert r["share_explained_pct"] > 100.0
        assert r["share_explained_pct"] == pytest.approx(150.0)

    def test_zero_empirical_benchmark_gives_nan_not_a_division_error(self):
        emp = _empirical(np.zeros(12))
        sim = _sim(TARGETS - 1.0)

        r = score_extension_risk(sim, emp)

        assert r["empirical_trapped_b"] == 0.0
        assert np.isnan(r["share_explained_pct"])


class TestQtTargetSubtraction:
    """Mutant (b): sign flip on the qt_target subtraction."""

    def test_trapped_is_rolloff_minus_target(self):
        """
        hazard_trapped_b = sum(simulated_rolloff - QT_target).

        Roll-off is a flat -40B/month against a -17.5/-35 target schedule:
          correct : 3*(-40 + 17.5) + 9*(-40 + 35) = -67.5 + -45 = -112.5
          flipped : 3*(-40 - 17.5) + 9*(-40 - 35) = -172.5 + -675 = -847.5
          ignored : 12*(-40)                                     = -480.0
        All three readings are far apart, and the ramp/full mix means a
        constant-target mutant lands on none of them.
        """
        emp = _empirical(np.full(12, -10.0))
        sim = _sim(np.full(12, -40.0))

        r = score_extension_risk(sim, emp)

        assert r["hazard_trapped_b"] == pytest.approx(-112.5)
        assert r["hazard_trapped_b"] != pytest.approx(-847.5)  # sign flip
        assert r["hazard_trapped_b"] != pytest.approx(-480.0)  # target dropped

    def test_meeting_the_target_exactly_traps_nothing(self):
        """
        The zero of the scale is the QT target, not zero roll-off.  A model
        that hits the schedule every month traps exactly $0B.
        """
        emp = _empirical(np.full(12, -10.0))
        sim = _sim(TARGETS.copy())

        r = score_extension_risk(sim, emp)

        assert r["hazard_trapped_b"] == pytest.approx(0.0, abs=1e-12)
        assert r["share_explained_pct"] == pytest.approx(0.0, abs=1e-12)

    def test_undershooting_the_target_traps_negatively_like_the_empirical(self):
        """
        Sign convention: roll-off smaller in magnitude than the target means
        balance sheet failed to shrink -> trapped, and the empirical
        extension deltas carry that same sign.  A sign flip on the target
        breaks this agreement for undershoot and overshoot simultaneously.
        """
        emp = _empirical(np.full(12, -10.0))

        under = score_extension_risk(_sim(TARGETS + 5.0), emp)
        over = score_extension_risk(_sim(TARGETS - 5.0), emp)

        assert under["hazard_trapped_b"] > 0.0   # rolled off less than target
        assert over["hazard_trapped_b"] < 0.0    # rolled off more than target
        assert np.sign(over["hazard_trapped_b"]) == np.sign(
            over["empirical_trapped_b"]
        )
        assert under["hazard_trapped_b"] == pytest.approx(+60.0)
        assert over["hazard_trapped_b"] == pytest.approx(-60.0)

    def test_target_is_taken_month_by_month_not_as_a_window_average(self):
        """
        The ramp months carry a different target (-17.5B) from the full-pace
        months (-35B).  Over a complete window an averaged target is an
        equivalent mutation — the sums coincide — so the discriminating case
        is a window where the simulated leg is missing a month: then the
        per-month schedule and its average diverge.

        Simulated leg missing the first ramp month, roll-off -40B/month:
          correct  : 2*(-40 + 17.5) + 9*(-40 + 35)      = -45 + -45 = -90.0
          averaged : 11*(-40 + 30.625)                  = -103.125
        """
        emp = _empirical(np.full(12, -10.0), pad_outside=False)
        sim = _sim(np.full(12, -40.0), pad_outside=False)
        sim.loc[QT_MONTHS[0], "simulated_rolloff_b"] = np.nan  # a ramp month

        r = score_extension_risk(sim, emp)

        assert r["hazard_trapped_b"] == pytest.approx(-90.0)
        assert r["hazard_trapped_b"] != pytest.approx(-103.125)


class TestTrappedAggregation:
    """Mutant (c): off-by-one / wrong-window aggregation in hazard_trapped_b."""

    def test_one_month_shift_changes_the_answer(self):
        """
        Guards against an off-by-one alignment between the simulated path and
        the empirical/target index.  The roll-off path is strictly monotone
        and defined on a wider index than the QT window, so a +/-1 month shift
        stays fully populated and lands on a different sum.
        """
        wide = pd.date_range("2022-03-01", periods=18, freq="MS")
        path = -np.arange(30.0, 30.0 + len(wide))  # -30, -31, ... strictly decreasing
        sim_wide = pd.DataFrame(
            {
                "simulated_rolloff_b": path,
                "hazard_cpr_pct": np.linspace(5.0, 3.0, len(wide)),
            },
            index=wide,
        )
        emp = _empirical(np.full(12, -10.0))

        aligned = score_extension_risk(sim_wide, emp)
        shifted_early = score_extension_risk(
            sim_wide.shift(1, freq="MS"), emp
        )
        shifted_late = score_extension_risk(
            sim_wide.shift(-1, freq="MS"), emp
        )

        # The aligned window is 2022-06..2023-05, i.e. path entries 3..14
        # (-33 .. -44), against the -17.5/-35 target schedule.
        expected = float(
            sum(path[3:15]) - (RAMP_N * QT_TARGET_RAMP_B + FULL_N * QT_TARGET_FULL_B)
        )
        assert aligned["hazard_trapped_b"] == pytest.approx(expected)
        assert shifted_early["hazard_trapped_b"] != pytest.approx(expected)
        assert shifted_late["hazard_trapped_b"] != pytest.approx(expected)
        # A one-month shift of a -1B/month ramp moves the sum by exactly 12B.
        assert shifted_early["hazard_trapped_b"] - expected == pytest.approx(12.0)
        assert expected - shifted_late["hazard_trapped_b"] == pytest.approx(12.0)

    def test_months_outside_the_qt_window_never_enter_either_total(self):
        """
        Both frames are padded outside [QT_START, QT_END) with -1000B decoys.
        A masking failure on either leg moves the totals by thousands.
        """
        emp = _empirical(np.full(12, -10.0), pad_outside=True)
        sim = _sim(np.full(12, -40.0), pad_outside=True)

        r = score_extension_risk(sim, emp)

        assert r["empirical_trapped_b"] == pytest.approx(-120.0)
        assert r["hazard_trapped_b"] == pytest.approx(-112.5)

    def test_totals_are_sums_over_months_not_means_or_counts(self):
        """
        Doubling the window doubles both dollar totals exactly.  A mean-instead
        -of-sum aggregation leaves them unchanged; a wrong-axis reduction
        (e.g. collapsing to a scalar count) breaks the proportionality.
        """
        six = QT_MONTHS[:6]
        emp_6 = _empirical(
            np.full(6, -10.0), months=six, targets=TARGETS[:6], pad_outside=False
        )
        sim_6 = _sim(TARGETS[:6] - 5.0, months=six, pad_outside=False)
        r6 = score_extension_risk(sim_6, emp_6)

        twelve = QT_MONTHS
        emp_12 = _empirical(np.full(12, -10.0), pad_outside=False)
        sim_12 = _sim(TARGETS - 5.0, pad_outside=False)
        r12 = score_extension_risk(sim_12, emp_12)

        assert r6["hazard_trapped_b"] == pytest.approx(-30.0)
        assert r12["hazard_trapped_b"] == pytest.approx(-60.0)
        assert r6["empirical_trapped_b"] == pytest.approx(-60.0)
        assert r12["empirical_trapped_b"] == pytest.approx(-120.0)
        # Share is scale-free under a proportional extension of the window.
        assert r6["share_explained_pct"] == pytest.approx(
            r12["share_explained_pct"]
        )

    def test_missing_simulated_months_are_dropped_not_zero_filled(self):
        """
        A month with no simulated roll-off must leave the simulated total
        alone.  Zero-filling it would silently charge the model the full
        target for that month (+35B of phantom trapping).
        """
        emp = _empirical(np.full(12, -10.0), pad_outside=False)
        rolloff = TARGETS - 5.0
        sim = _sim(rolloff, pad_outside=False)
        sim.loc[QT_MONTHS[7], "simulated_rolloff_b"] = np.nan

        r = score_extension_risk(sim, emp)

        assert r["hazard_trapped_b"] == pytest.approx(-55.0)  # 11 months x -5
        assert r["hazard_trapped_b"] != pytest.approx(-20.0)  # zero-filled

    def test_empirical_months_with_missing_deltas_are_excluded(self):
        """
        qt_active_frame drops NaN extension deltas; the simulated leg must be
        reindexed onto that reduced index, so both totals lose the same month.
        """
        deltas = np.full(12, -10.0)
        deltas[4] = np.nan
        emp = _empirical(deltas, pad_outside=False)
        sim = _sim(TARGETS - 5.0, pad_outside=False)

        r = score_extension_risk(sim, emp)

        assert r["empirical_trapped_b"] == pytest.approx(-110.0)
        assert r["hazard_trapped_b"] == pytest.approx(-55.0)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
