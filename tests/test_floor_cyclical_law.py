"""
Arithmetic gates on the W2 cyclical-floor law (hazard/floor_cyclical.py).

Audit: 1/4 mutants killed. tests/test_floor_cyclical.py checks two aggregate
PROPERTIES of the floor path (the window mean pins at 4% off the clip; it does
not pin on the clip) and one tautology (`floor_at(r) == PRODUCTION_FLOOR` at
kappa = 0, where floor_at literally returns PRODUCTION_FLOOR). Those properties
are invariant to the things most likely to be wrong: the SIGN of z, the ddof of
the standardization, the percent-to-decimal conversion on the rate series, and
the orientation of the level-sweep envelope. The window mean pins at 4%
whichever way z points, because z sums to zero either way.

This file goes at the per-month values and at the surrounding plumbing.
Expectations are hand-computed from a closed-form series or stated as
directional facts fixed by the module's own pre-registered spec.

Run with: python3 -m pytest tests/test_floor_cyclical_law.py
"""

from __future__ import annotations

import json
import os
import statistics
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "hazard"))

os.environ.setdefault("FRED_API_KEY", "test-dummy-key")

# A rate series chosen so that ddof=0 and ddof=1 differ by a visible margin
# (n = 5) and the mean is exact in binary floating point.
RATES = pd.Series([0.02, 0.04, 0.06, 0.08, 0.10])
RATES_MEAN = 0.06
RATES_SD1 = statistics.stdev([0.02, 0.04, 0.06, 0.08, 0.10])       # ddof=1
RATES_SD0 = statistics.pstdev([0.02, 0.04, 0.06, 0.08, 0.10])      # ddof=0


# ---------------------------------------------------------------------------
# Pre-registered spec constants — literals from the module docstring
# ---------------------------------------------------------------------------
def test_spec_constants_are_the_pre_registered_values():
    """These are quoted in TECHNICAL §24.1 and fix the whole W2 run. They are
    asserted as literals; nothing here re-derives them from the module."""
    import floor_cyclical as fc

    assert fc.PRODUCTION_FLOOR == 0.04           # 4% annual involuntary CPR
    assert fc.KAPPA_GRID == [-0.5, -0.25, -0.1, 0.0, 0.1, 0.25, 0.5]
    assert fc.CENTRAL_PQ == 6.5                  # central elasticity leg
    assert fc.NULL_PQ == 0.0                     # no-lock-in null leg
    assert fc.PARITY_TOL == 0.01                 # $0.01B / 0.01pp


def test_kappa_grid_is_symmetric_and_nests_production_at_zero():
    """kappa = 0 must be ON the grid — it is the parity anchor that licenses
    every other cell — and the stress envelope must be two-sided."""
    import floor_cyclical as fc

    assert 0.0 in fc.KAPPA_GRID
    assert sorted(fc.KAPPA_GRID) == fc.KAPPA_GRID  # ascending
    assert [-k for k in fc.KAPPA_GRID] == sorted(
        [-k for k in fc.KAPPA_GRID]
    )[::-1]
    assert set(-k for k in fc.KAPPA_GRID) == set(fc.KAPPA_GRID)


# ---------------------------------------------------------------------------
# CyclicalFloor — standardization
# ---------------------------------------------------------------------------
def test_standardization_uses_the_sample_sd_not_the_population_sd():
    """The spec says ddof=1 explicitly. On this series the two differ by ~12%,
    so a ddof slip rescales every off-centre month's floor."""
    import floor_cyclical as fc

    cf = fc.CyclicalFloor(RATES, kappa=0.25)
    assert cf.mean == pytest.approx(RATES_MEAN, abs=1e-15)
    assert cf.std == pytest.approx(RATES_SD1, rel=1e-12)
    assert cf.std != pytest.approx(RATES_SD0, rel=1e-6)


# A deliberately SKEWED series: RATES above is symmetric, so its mean and its
# median coincide exactly and a np.mean -> np.median slip is invisible on it.
SKEWED = pd.Series([0.02, 0.03, 0.04, 0.05, 0.26])
SKEWED_MEAN = 0.08
SKEWED_MEDIAN = 0.04


def test_standardization_centers_on_the_mean_not_the_median():
    """z_t = (r - MEAN)/sd. Every other test in this file uses a symmetric
    rate series on which mean == median, so a `np.mean -> np.median` slip
    survives all of them while shifting the centering of the whole floor path
    on the real (right-skewed) QT rate series. Centered on the wrong
    statistic, the window mean of the floor is no longer 4% and the parity
    anchor at kappa = 0 silently stops meaning what the spec says."""
    import floor_cyclical as fc

    assert SKEWED_MEAN != SKEWED_MEDIAN  # the fixture must actually separate them
    cf = fc.CyclicalFloor(SKEWED, kappa=0.25)
    assert cf.mean == pytest.approx(SKEWED_MEAN, abs=1e-15)
    assert cf.mean != pytest.approx(SKEWED_MEDIAN, rel=1e-6)
    # and the law inherits it: the floor equals base exactly AT the mean,
    # and is strictly below base at the median (which lies below the mean).
    assert cf.floor_at(SKEWED_MEAN) == pytest.approx(0.04, abs=1e-15)
    assert cf.floor_at(SKEWED_MEDIAN) < 0.04


@pytest.mark.parametrize("rate", [0.02, 0.04, 0.06, 0.08, 0.10])
def test_floor_at_matches_the_closed_form_law(rate):
    """floor_t = 0.04 * (1 + kappa * z_t), z_t = (r - mean)/sd(ddof=1).
    Right-hand side computed here from statistics.stdev, not from the module."""
    import floor_cyclical as fc

    kappa = 0.25
    z = (rate - RATES_MEAN) / RATES_SD1
    expected = 0.04 * (1.0 + kappa * z)
    cf = fc.CyclicalFloor(RATES, kappa=kappa)
    assert cf.floor_at(rate) == pytest.approx(expected, rel=1e-12)


def test_positive_kappa_raises_the_floor_when_rates_are_above_the_window_mean():
    """The spec's sign convention: kappa > 0 means involuntary turnover RISES
    with rates. A z-sign flip inverts the economics of every cell while leaving
    the window mean pinned at 4%, so the existing mean-pin tests cannot see it."""
    import floor_cyclical as fc

    cf = fc.CyclicalFloor(RATES, kappa=0.5)
    assert cf.floor_at(0.10) > fc.PRODUCTION_FLOOR   # above mean -> higher
    assert cf.floor_at(0.02) < fc.PRODUCTION_FLOOR   # below mean -> lower
    assert cf.floor_at(RATES_MEAN) == pytest.approx(fc.PRODUCTION_FLOOR, abs=1e-15)


def test_negative_kappa_is_the_lock_in_adverse_direction():
    """kappa < 0: fewer forced moves exactly when rates are high. Mirror image
    of the positive case, and the mirror must be exact."""
    import floor_cyclical as fc

    up = fc.CyclicalFloor(RATES, kappa=0.3)
    down = fc.CyclicalFloor(RATES, kappa=-0.3)
    for r in RATES:
        assert up.floor_at(r) + down.floor_at(r) == pytest.approx(
            2 * 0.04, abs=1e-15
        )
    assert down.floor_at(0.10) < 0.04 < down.floor_at(0.02)


def test_floor_is_linear_in_kappa_at_fixed_rate():
    """base * (1 + kappa*z) is affine in kappa. An exponent or a `base + kappa*z`
    slip breaks the constant second difference."""
    import floor_cyclical as fc

    r = 0.10
    vals = [fc.CyclicalFloor(RATES, kappa=k).floor_at(r)
            for k in (0.0, 0.1, 0.2, 0.3)]
    d = np.diff(vals)
    assert np.allclose(d, d[0], rtol=1e-12)
    assert d[0] > 0.0  # and increasing, at a rate above the window mean


def test_kappa_scales_the_base_multiplicatively_not_additively():
    """floor - base must be proportional to base. Doubling the base doubles the
    deviation; an additive `base + kappa*z` law leaves it unchanged."""
    import floor_cyclical as fc

    a = fc.CyclicalFloor(RATES, kappa=0.5, base=0.04)
    b = fc.CyclicalFloor(RATES, kappa=0.5, base=0.08)
    dev_a = a.floor_at(0.10) - 0.04
    dev_b = b.floor_at(0.10) - 0.08
    assert dev_b == pytest.approx(2.0 * dev_a, rel=1e-12)


# ---------------------------------------------------------------------------
# kappa = 0 must be the production code path, for ANY base
# ---------------------------------------------------------------------------
def test_kappa_zero_returns_the_configured_base_not_a_hardcoded_constant():
    """Replaces the tautology in tests/test_floor_cyclical.py, which asserted
    `floor_at(r) == PRODUCTION_FLOOR` when floor_at returns PRODUCTION_FLOOR by
    construction. Passing a base that is NOT the production constant makes the
    two sides independent, so a hardcoded return is caught."""
    import floor_cyclical as fc

    cf = fc.CyclicalFloor(RATES, kappa=0.0, base=0.0123)
    for r in list(RATES) + [0.0, 0.5, -0.2]:
        assert cf.floor_at(r) == 0.0123
    assert not cf.clip_bound


def test_kappa_zero_does_not_touch_the_standardization_at_all():
    """The production floor is ACYCLICAL — the referee residual the whole run
    exists to bracket — and kappa = 0 must be the production code path
    *bit-for-bit*, which means it must not consult mean/std at all.

    Rate-invariance alone is too weak to state that: at kappa = 0 the general
    law base*(1 + 0*z) already evaluates to base, so deleting the early-return
    branch is invisible to a rate sweep. It stops being invisible on a
    DEGENERATE window (std = 0), where the general law divides by zero and
    returns NaN while the production path must still return exactly 4%. A
    constant-rate window is not exotic: any single-month or flat-rate slice
    the sweep code hands in produces one."""
    import floor_cyclical as fc

    cf = fc.CyclicalFloor(RATES, kappa=0.0)
    vals = {cf.floor_at(r) for r in np.linspace(-1.0, 1.0, 25)}
    assert vals == {fc.PRODUCTION_FLOOR}
    assert not cf.clip_bound

    degenerate = fc.CyclicalFloor(pd.Series([0.06] * 5), kappa=0.0)
    assert degenerate.std == 0.0  # the fixture really is degenerate
    for r in (0.02, 0.06, 0.10):
        got = degenerate.floor_at(r)
        assert got == fc.PRODUCTION_FLOOR
        assert not np.isnan(got)
    # a single-month window is the same situation (sd is NaN at ddof=1, n=1)
    single = fc.CyclicalFloor(pd.Series([0.06]), kappa=0.0)
    assert single.floor_at(0.10) == fc.PRODUCTION_FLOOR


# ---------------------------------------------------------------------------
# The non-negativity clip
# ---------------------------------------------------------------------------
def test_clip_returns_zero_and_never_a_negative_floor():
    import floor_cyclical as fc

    cf = fc.CyclicalFloor(RATES, kappa=10.0)
    assert cf.floor_at(0.02) == 0.0  # z << 0, raw strongly negative
    assert cf.clip_bound


def test_clip_flag_is_a_latch_not_a_per_call_state():
    """The artifact records ONE clip_bound per cell. If the flag reset on the
    next in-range month the artifact would under-report broken pinning."""
    import floor_cyclical as fc

    cf = fc.CyclicalFloor(RATES, kappa=10.0)
    assert not cf.clip_bound
    cf.floor_at(0.02)          # binds
    assert cf.clip_bound
    cf.floor_at(0.10)          # comfortably positive
    assert cf.clip_bound       # still latched
    cf.floor_at(RATES_MEAN)
    assert cf.clip_bound


def test_clip_does_not_fire_on_a_floor_that_is_merely_small():
    """The clip is `raw < 0`, not `raw <= 0` on a threshold. A floor of 1e-6 is
    legitimate and must be returned intact, unflagged."""
    import floor_cyclical as fc

    # kappa chosen so the lowest month lands just above zero.
    z_min = (0.02 - RATES_MEAN) / RATES_SD1
    kappa = -0.999 / z_min  # raw = 0.04 * (1 - 0.999) > 0
    cf = fc.CyclicalFloor(RATES, kappa=kappa)
    got = cf.floor_at(0.02)
    assert 0.0 < got < 1e-4
    assert not cf.clip_bound


def test_clip_can_only_raise_the_realized_floor():
    """Clipping replaces a negative with zero, so the clipped path's mean is
    strictly ABOVE the unclipped mean — which is why a bound clip breaks the
    4% pin upward and never downward."""
    import floor_cyclical as fc

    kappa = 10.0
    cf = fc.CyclicalFloor(RATES, kappa=kappa)
    clipped = np.array([cf.floor_at(r) for r in RATES])
    z = (np.asarray(RATES) - RATES_MEAN) / RATES_SD1
    unclipped = 0.04 * (1.0 + kappa * z)
    assert cf.clip_bound
    # tolerance only absorbs the ULP-level difference between statistics.stdev
    # here and pandas' std inside the module; the clipped months are lifted by
    # ~0.2-0.5, far above it.
    assert np.all(clipped >= unclipped - 1e-15)
    assert np.all(clipped[unclipped < 0.0] == 0.0)
    assert clipped.mean() > unclipped.mean() + 1e-3
    assert unclipped.mean() == pytest.approx(0.04, abs=1e-15)


# ---------------------------------------------------------------------------
# _qt_window_rates — units and window
# ---------------------------------------------------------------------------
def _macro(start="2022-01-01", end="2026-06-01"):
    idx = pd.date_range(start, end, freq="MS")
    return pd.DataFrame(
        {"MORTGAGE30US": np.linspace(3.0, 7.0, len(idx))}, index=idx
    )


def test_qt_window_rates_converts_percent_to_decimal():
    """MORTGAGE30US is quoted in PERCENT; the floor law standardizes decimals.
    Dropping the /100 leaves z unchanged (scale-invariant) but corrupts mean
    and std, which the artifact reports — and the existing suite never looks."""
    import floor_cyclical as fc

    macro = _macro()
    out = fc._qt_window_rates(macro)
    assert out.max() < 0.15  # decimals, not 3.0-7.0 percent
    aligned = macro.loc[out.index, "MORTGAGE30US"]
    assert np.allclose(out.to_numpy(), aligned.to_numpy() / 100.0, rtol=1e-15)


def test_qt_window_rates_uses_the_half_open_qt_window():
    """Same half-open convention as common/qt_window: 2022-06 in, 2025-12 out."""
    import floor_cyclical as fc
    from config import QT_END, QT_START

    out = fc._qt_window_rates(_macro())
    assert out.index.min() == QT_START
    assert out.index.max() < QT_END
    assert QT_END not in out.index
    assert out.index.max() == pd.Timestamp("2025-11-01")
    assert len(out) == 42  # Jun 2022 .. Nov 2025 inclusive


def test_qt_window_rates_drops_months_outside_the_window():
    import floor_cyclical as fc

    wide = _macro("2018-01-01", "2029-12-01")
    narrow = _macro()
    assert len(fc._qt_window_rates(wide)) == len(fc._qt_window_rates(narrow))


# ---------------------------------------------------------------------------
# _level_sweep_envelope — orientation and inclusive band
# ---------------------------------------------------------------------------
def _write_sweep(tmp_path, rows):
    p = tmp_path / "floor_sweep_results.json"
    p.write_text(json.dumps({"rows": rows}))
    return p


def test_level_sweep_envelope_returns_min_then_max(tmp_path, monkeypatch):
    """A min<->max inversion silently inverts the ex-ante interpretive
    threshold — every cell would be read as OUTSIDE the envelope and the
    manuscript's acyclical-floor concession would be withdrawn for no reason.
    Rows deliberately unsorted so an inversion cannot coincidentally agree."""
    import floor_cyclical as fc

    rows = [
        {"floor_annual_cpr_pct": 4.0, "lockin_marginal_share_pp": 9.2},
        {"floor_annual_cpr_pct": 3.0, "lockin_marginal_share_pp": 10.8},
        {"floor_annual_cpr_pct": 5.0, "lockin_marginal_share_pp": 5.5},
    ]
    monkeypatch.setattr(fc, "SWEEP_ARTIFACT", _write_sweep(tmp_path, rows))
    lo, hi = fc._level_sweep_envelope()[:2]
    assert (lo, hi) == (5.5, 10.8)
    assert lo < hi


@pytest.mark.parametrize("floor_pct,included", [
    (2.999, False),  # just outside the 3-5% band
    (3.0, True),     # AT the lower edge: the spec says floors 3-5% INCLUSIVE
    (3.001, True),
    (4.999, True),
    (5.0, True),     # AT the upper edge
    (5.001, False),  # just outside
])
def test_level_sweep_band_edges_are_inclusive(tmp_path, monkeypatch,
                                              floor_pct, included):
    """The pre-registered band is 'floors 3-5%'. An exclusive slip at either
    edge drops the 3% or 5% cell and NARROWS the envelope, making cells look
    like they exited it. Probe row carries an extreme marginal so its
    inclusion is unmistakable in the min/max."""
    import floor_cyclical as fc

    rows = [
        {"floor_annual_cpr_pct": 4.0, "lockin_marginal_share_pp": 9.2},
        {"floor_annual_cpr_pct": floor_pct, "lockin_marginal_share_pp": 99.0},
    ]
    monkeypatch.setattr(fc, "SWEEP_ARTIFACT", _write_sweep(tmp_path, rows))
    lo, hi = fc._level_sweep_envelope()[:2]
    assert (hi == 99.0) is included
    assert (lo, hi) == ((9.2, 99.0) if included else (9.2, 9.2))


def test_level_sweep_envelope_returns_the_rows_it_used(tmp_path, monkeypatch):
    """The third return value is the audit trail for the envelope; it must
    contain exactly the in-band rows."""
    import floor_cyclical as fc

    rows = [
        {"floor_annual_cpr_pct": 2.0, "lockin_marginal_share_pp": 14.0},
        {"floor_annual_cpr_pct": 3.0, "lockin_marginal_share_pp": 10.8},
        {"floor_annual_cpr_pct": 5.0, "lockin_marginal_share_pp": 5.5},
        {"floor_annual_cpr_pct": 6.0, "lockin_marginal_share_pp": 1.0},
    ]
    monkeypatch.setattr(fc, "SWEEP_ARTIFACT", _write_sweep(tmp_path, rows))
    lo, hi, used = fc._level_sweep_envelope()
    assert [r["floor_annual_cpr_pct"] for r in used] == [3.0, 5.0]
    assert (lo, hi) == (5.5, 10.8)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
