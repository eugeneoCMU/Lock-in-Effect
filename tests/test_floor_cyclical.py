"""
Gates for the W2 cyclical-floor variant (hazard/floor_cyclical.py).

The variant replaces the constant 4% involuntary-turnover floor with
floor_t = 0.04 * (1 + kappa * z_t), z_t the standardized QT-window mortgage
rate. Everything hangs on three arithmetic facts, testable without data:
(1) the window MEAN of floor_t is pinned at exactly 4% for every kappa
    (the production spec is nested, not re-leveled);
(2) kappa = 0 reproduces the constant production floor at every month;
(3) the floor never goes negative (clip), and the artifact must know when
    the clip binds because pinning is broken there.

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


def test_window_mean_pinned_for_every_kappa():
    from floor_cyclical import CyclicalFloor

    for kappa in (-0.5, -0.25, 0.0, 0.25, 0.5):
        cf = CyclicalFloor(RATES, kappa=kappa)
        floors = np.array([cf.floor_at(r) for r in RATES])
        assert abs(floors.mean() - 0.04) < 1e-12, kappa
        assert not cf.clip_bound


def test_kappa_zero_is_production_constant():
    from floor_cyclical import CyclicalFloor, PRODUCTION_FLOOR

    cf = CyclicalFloor(RATES, kappa=0.0)
    for r in RATES:
        assert cf.floor_at(r) == PRODUCTION_FLOOR


def test_extreme_kappa_clips_and_flags():
    from floor_cyclical import CyclicalFloor

    cf = CyclicalFloor(RATES, kappa=5.0)
    floors = np.array([cf.floor_at(r) for r in RATES])
    assert (floors >= 0.0).all()
    assert cf.clip_bound  # pinning is broken; the artifact must record it
