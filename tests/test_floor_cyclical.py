"""
Gates for the W2 cyclical-floor variant (hazard/floor_cyclical.py).

The variant replaces the constant 4% involuntary-turnover floor with
floor_t = 0.04 * (1 + kappa * z_t), z_t the standardized QT-window mortgage
rate. Everything hangs on three arithmetic facts, testable without data:
(1) the window MEAN of floor_t is pinned at exactly 4% WHENEVER THE
    NON-NEGATIVITY CLIP DOES NOT BIND (the production spec is nested, not
    re-leveled), and is NOT pinned where it does;
(2) kappa = 0 reproduces the constant production floor at every month;
(3) the floor never goes negative (clip), and the artifact must know when
    the clip binds because pinning is broken there.

CORRECTION (floor_cyclical_permutation.py). An earlier revision of this
docstring asserted (1) unconditionally — "pinned at exactly 4% for every
kappa" — and the manuscript repeated it. That is false on the real QT
window: at |kappa| = 0.5 the clip binds and the realized window means are
4.000519% and 4.082786%, not 4%. The test below never caught it because its
synthetic RATES series is too narrow for the clip to bind at the kappas it
sweeps. It now sweeps a kappa at which the clip DOES bind on that series and
asserts the pin breaks there, so the conditional is exercised in both
directions rather than assumed.

Run with: python3 -m pytest tests/test_floor_cyclical.py
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "hazard"))

os.environ.setdefault("FRED_API_KEY", "test-dummy-key")

RATES = pd.Series([0.050, 0.055, 0.062, 0.070, 0.078, 0.066])


def test_window_mean_pinned_where_the_clip_does_not_bind():
    from floor_cyclical import CyclicalFloor

    for kappa in (-0.5, -0.25, 0.0, 0.25, 0.5):
        cf = CyclicalFloor(RATES, kappa=kappa)
        floors = np.array([cf.floor_at(r) for r in RATES])
        assert not cf.clip_bound, kappa
        assert abs(floors.mean() - 0.04) < 1e-12, kappa


def test_window_mean_is_not_pinned_where_the_clip_binds():
    """The pin is a consequence of z_t summing to zero, and the clip breaks
    it by construction: clipping only ever raises a floor value, so a bound
    clip pushes the realized mean strictly above 4%. On the real QT window
    this happens at |kappa| = 0.5 (realized means 4.000519% and 4.082786%);
    on the synthetic series here it takes a larger kappa to reach."""
    from floor_cyclical import CyclicalFloor

    cf = CyclicalFloor(RATES, kappa=5.0)
    floors = np.array([cf.floor_at(r) for r in RATES])
    assert cf.clip_bound
    assert floors.mean() > 0.04


def test_kappa_zero_is_production_constant():
    """TAUTOLOGY REPAIRED (suite-hardening pass).

    As written, this test compared floor_at(r) against PRODUCTION_FLOOR while
    floor_at at kappa = 0 returns `self.base`, which DEFAULTS to
    PRODUCTION_FLOOR — the same constant on both sides of the ==. Measured
    against 28 single-point mutants of hazard/floor_cyclical.py it killed
    exactly zero: a hardcoded return, a broken standardization, a wrong law,
    a wrong clip all left it green.

    Two independent statements replace it. (1) At kappa = 0 the floor is the
    CONFIGURED base, probed with a base that is deliberately not the
    production constant, so a hardcoded return no longer satisfies it.
    (2) The production default really is 4%, asserted once as a literal.
    """
    from floor_cyclical import CyclicalFloor, PRODUCTION_FLOOR

    assert PRODUCTION_FLOOR == 0.04  # the literal, stated once

    cf = CyclicalFloor(RATES, kappa=0.0, base=0.0731)
    for r in RATES:
        assert cf.floor_at(r) == 0.0731

    prod = CyclicalFloor(RATES, kappa=0.0)
    for r in RATES:
        assert prod.floor_at(r) == 0.04


def test_extreme_kappa_clips_and_flags():
    from floor_cyclical import CyclicalFloor

    cf = CyclicalFloor(RATES, kappa=5.0)
    floors = np.array([cf.floor_at(r) for r in RATES])
    assert (floors >= 0.0).all()
    assert cf.clip_bound  # pinning is broken; the artifact must record it
