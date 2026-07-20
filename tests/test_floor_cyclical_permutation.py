"""
Gates for the floor-cyclicality attribution probe
(hazard/floor_cyclical_permutation.py).

The probe's whole claim is that the floor_cyclical kappa grid moves the
marginal mostly through DISPERSION under eq. (3)'s hard maximum rather than
through CO-MOVEMENT with the rate cycle. That claim rests on three
constructions whose arithmetic is testable without touching the microsim:

(1) a permutation of the floor path must preserve the path's multiset, and
    therefore its mean, sd, min and max, EXACTLY — otherwise the permuted leg
    differs from the true leg in level as well as in order, and the
    decomposition attributes level movement to order;
(2) the convexity-matched flat floor must be the flat rate whose MONTHLY
    hazard equals the path's mean monthly hazard, which is NOT the arithmetic
    mean of the annual rates — the annual/monthly transform is convex, so a
    naive mean would smuggle a level difference into the "level" control;
(3) the three-way split must be exhaustive: level + residual dispersion +
    time-order must sum to the departure identically, so no part of a cell's
    movement can go unattributed.

Run with: python3 -m pytest tests/test_floor_cyclical_permutation.py
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "hazard"))

os.environ.setdefault("FRED_API_KEY", "test-dummy-key")

ARTIFACT = (
    _REPO_ROOT / "hazard" / "data" / "floor_cyclical_permutation_results.json"
)


def _macro_stub() -> pd.DataFrame:
    """Minimal frame with the two columns the floor law reads, spanning the
    real QT window so config's QT_START/QT_END select it."""
    from config import QT_END, QT_START

    idx = pd.date_range(QT_START, QT_END, freq="MS", inclusive="left")
    rng = np.random.default_rng(0)
    return pd.DataFrame(
        {"MORTGAGE30US": 3.0 + 4.0 * rng.random(len(idx))}, index=idx
    )


def test_permutation_preserves_the_multiset_exactly():
    import floor_cyclical_permutation as m

    path, _ = m.cyclical_floor_path(_macro_stub(), 0.5)
    rng = np.random.default_rng(m.SEED)
    for _ in range(8):
        perm = rng.permutation(path)
        assert np.array_equal(np.sort(perm), np.sort(path))
        assert perm.mean() == pytest.approx(path.mean(), abs=0.0, rel=1e-15)
        assert perm.std(ddof=1) == pytest.approx(path.std(ddof=1), rel=1e-15)


def test_kappa_zero_path_is_constant_and_permutation_is_a_no_op():
    import floor_cyclical_permutation as m

    path, clip = m.cyclical_floor_path(_macro_stub(), 0.0)
    assert not clip
    assert path.std(ddof=1) == 0.0
    assert np.all(path == m.PRODUCTION_FLOOR)
    perm = np.random.default_rng(1).permutation(path)
    assert np.array_equal(perm, path)


def test_convexity_matched_flat_is_not_the_arithmetic_mean():
    """If these coincided the level control would be free; they do not, and
    the gap is the whole reason flat_equiv is run rather than assumed."""
    import floor_cyclical_permutation as m
    from literature_hazard import cpr_annual_to_monthly_hazard

    path, _ = m.cyclical_floor_path(_macro_stub(), 0.5)
    flat = m.convexity_matched_flat(path)

    hbar = float(np.mean(cpr_annual_to_monthly_hazard(path)))
    assert flat == pytest.approx(1.0 - (1.0 - hbar) ** 12, rel=1e-15)
    # a dispersed path's convexity-matched flat sits strictly above its mean
    assert flat > float(path.mean())
    # and a constant path's is its own level
    const = np.full(len(path), m.PRODUCTION_FLOOR)
    assert m.convexity_matched_flat(const) == pytest.approx(
        m.PRODUCTION_FLOOR, rel=1e-12
    )


def test_clip_breaks_the_window_mean_pin_on_the_real_floor_law():
    """The correction the probe exists to make permanent: the pin is
    conditional on the clip, not unconditional."""
    import floor_cyclical_permutation as m

    macro = _macro_stub()
    for kappa in (-0.1, 0.0, 0.1):
        path, clip = m.cyclical_floor_path(macro, kappa)
        assert not clip
        assert float(path.mean()) == pytest.approx(m.PRODUCTION_FLOOR, abs=1e-15)
    for kappa in (-3.0, 3.0):
        path, clip = m.cyclical_floor_path(macro, kappa)
        assert clip
        assert float(path.mean()) > m.PRODUCTION_FLOOR
        assert float(path.min()) == 0.0


def test_job_plan_shape_and_rng_independence_of_skipped_cells():
    """kappa = 0 burns its 12 draws rather than skipping them, so the draws
    used at every other kappa do not depend on which cells are run."""
    import floor_cyclical_permutation as m

    jobs, meta = m.build_jobs(_macro_stub())
    kinds = {}
    for k, *_ in jobs:
        kinds[k] = kinds.get(k, 0) + 1
    assert kinds == {"true": 7, "additive": 7, "flat_equiv": 7, "perm": 72}
    assert set(meta) == {f"{k:+g}" for k in m.KAPPA_GRID}

    rng = np.random.default_rng(m.SEED)
    path0, _ = m.cyclical_floor_path(_macro_stub(), m.KAPPA_GRID[0])
    for _ in range(m.N_PERM):
        rng.permutation(path0)
    first_second_cell = rng.permutation(
        m.cyclical_floor_path(_macro_stub(), m.KAPPA_GRID[1])[0]
    )
    got = next(j[3] for j in jobs
               if j[0] == "perm" and j[1] == f"{m.KAPPA_GRID[1]:+g}"
               and j[2] == 0)
    assert np.array_equal(got, first_second_cell)


# --------------------------------------------------------------------------
# Artifact gates (skipped if the run has not been executed in this tree)
# --------------------------------------------------------------------------
requires_artifact = pytest.mark.skipif(
    not ARTIFACT.exists(), reason="floor_cyclical_permutation has not been run"
)


@requires_artifact
def test_artifact_parity_is_bit_exact_on_all_seven_cells():
    import json

    a = json.loads(ARTIFACT.read_text())
    cells = a["parity_gate_bitexact_cells"]
    assert len(cells) == 7
    for key, g in cells.items():
        assert g["pass_bitwise"], key
        assert g["abs_diff_b"] == 0.0 and g["abs_diff_pp"] == 0.0, key
    assert a["parity_gate_bitexact_all_pass"]
    cross = a["parity_gate_additive_cross_check"]
    assert cross["pass"]
    assert cross["want_source"].startswith("floor_form_results.json")


@requires_artifact
def test_artifact_three_way_split_is_exhaustive():
    import json

    a = json.loads(ARTIFACT.read_text())
    for key, row in a["per_kappa"].items():
        if "three_way_split_b" not in row:
            continue
        s = row["three_way_split_b"]
        total = (s["level_equivalence"] + s["residual_dispersion"]
                 + s["time_order"])
        assert total == pytest.approx(
            row["departure_from_kappa0_b"], abs=1e-9
        ), key
        pct = row["three_way_split_pct_of_magnitude"]
        assert sum(pct.values()) == pytest.approx(100.0, abs=1e-9), key
        assert row["order_free_share_pct_of_magnitude"] == pytest.approx(
            pct["level_equivalence"] + pct["residual_dispersion"], abs=1e-9
        ), key


@requires_artifact
def test_artifact_records_the_clip_in_exactly_the_two_stress_cells():
    import json

    a = json.loads(ARTIFACT.read_text())
    pk = a["per_kappa"]
    assert a["headline"]["n_clip_bound_cells"] == 2
    assert pk["-0.5"]["clip_bound"] and pk["+0.5"]["clip_bound"]
    assert not any(pk[k]["clip_bound"]
                   for k in ("-0.25", "-0.1", "+0", "+0.1", "+0.25"))
    # pinning broken upward in both, as clipping can only raise a value
    assert pk["-0.5"]["floor_path_mean_pct"] > 4.0
    assert pk["+0.5"]["floor_path_mean_pct"] > 4.0
