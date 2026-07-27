"""
BOUNDARY gates on every pre-registered PASS/FAIL predicate (audit MISSING #5).

Pre-registered verdicts are quoted in the manuscript as binding. An
inclusive/exclusive slip flips a verdict WITHOUT changing any reported number,
so it is invisible to every artifact-vs-prose consistency check the liveness
gates run. The existing test_envelope_gate_logic in tests/test_fannie_replication.py
probes 5.0, 1.0, -3.0 and 14.0 against a [2.11, 13.17] box — all far from the
edges, so `<=` vs `<` on either side survives it, and so does `>=` vs `>` on the
positivity leg.

Each predicate below is exercised AT the boundary, JUST INSIDE, and JUST
OUTSIDE, with the boundary case asserted in the direction the pre-registration
actually states:

  evaluate_envelope_gate  positive    : marginal_pp >  0      STRICT
                          in_envelope : box_min <= x <= box_max  INCLUSIVE both
  freddie_parity_gate                 : |got - want| <= tol      INCLUSIVE
  load_freddie_envelope               : (min, max) of the box, in that order

Run with: python3 -m pytest tests/test_gate_boundaries.py
"""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "hazard"))

os.environ.setdefault("FRED_API_KEY", "test-dummy-key")

# The committed Freddie box actually quoted in the manuscript.
BOX_MIN = 2.11
BOX_MAX = 13.17
# One ULP-ish step, small enough that "just inside/outside" is unambiguously a
# boundary probe and not a coarse re-run of the existing far-from-edge test.
EPS = 1e-12


# ---------------------------------------------------------------------------
# evaluate_envelope_gate — lower edge
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "marginal,in_envelope",
    [
        (BOX_MIN - EPS, False),  # just outside
        (BOX_MIN, True),         # AT the boundary: pre-registration is inclusive
        (BOX_MIN + EPS, True),   # just inside
    ],
)
def test_envelope_lower_edge_is_inclusive(marginal, in_envelope):
    from fannie_replication import evaluate_envelope_gate

    g = evaluate_envelope_gate(marginal, box_min=BOX_MIN, box_max=BOX_MAX)
    assert g["in_envelope"] is in_envelope
    assert g["pass"] is in_envelope  # positivity holds throughout this row set


# ---------------------------------------------------------------------------
# evaluate_envelope_gate — upper edge
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "marginal,in_envelope",
    [
        (BOX_MAX - EPS, True),   # just inside
        (BOX_MAX, True),         # AT the boundary: inclusive
        (BOX_MAX + EPS, False),  # just outside
    ],
)
def test_envelope_upper_edge_is_inclusive(marginal, in_envelope):
    from fannie_replication import evaluate_envelope_gate

    g = evaluate_envelope_gate(marginal, box_min=BOX_MIN, box_max=BOX_MAX)
    assert g["in_envelope"] is in_envelope
    assert g["pass"] is in_envelope


# ---------------------------------------------------------------------------
# evaluate_envelope_gate — positivity is STRICT at zero
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "marginal,positive",
    [
        (-EPS, False),  # just outside
        (0.0, False),   # AT the boundary: `> 0` is strict, zero does NOT pass
        (EPS, True),    # just inside
    ],
)
def test_positivity_edge_is_strict_at_zero(marginal, positive):
    """Box straddles zero so in_envelope is True on every row and the only
    thing separating them is the strictness of `marginal_pp > 0`. A `>=` slip
    would license a replication that found EXACTLY no lock-in marginal as a
    pre-registered PASS."""
    from fannie_replication import evaluate_envelope_gate

    g = evaluate_envelope_gate(marginal, box_min=-1.0, box_max=1.0)
    assert g["in_envelope"] is True
    assert g["positive"] is positive
    assert g["pass"] is positive


def test_pass_is_the_conjunction_not_either_leg():
    """Positive-but-outside and inside-but-nonpositive must BOTH fail; an
    `or` slip in the conjunction passes each of them."""
    from fannie_replication import evaluate_envelope_gate

    positive_outside = evaluate_envelope_gate(20.0, box_min=BOX_MIN, box_max=BOX_MAX)
    assert positive_outside["positive"] and not positive_outside["in_envelope"]
    assert positive_outside["pass"] is False

    inside_nonpositive = evaluate_envelope_gate(-0.5, box_min=-1.0, box_max=1.0)
    assert inside_nonpositive["in_envelope"] and not inside_nonpositive["positive"]
    assert inside_nonpositive["pass"] is False


def test_degenerate_box_admits_only_its_single_point():
    """box_min == box_max: the only admissible marginal is that exact value.
    Kills a `<`/`>` slip on either side, which would empty the box entirely."""
    from fannie_replication import evaluate_envelope_gate

    assert evaluate_envelope_gate(5.0, box_min=5.0, box_max=5.0)["pass"] is True
    assert evaluate_envelope_gate(5.0 - EPS, box_min=5.0, box_max=5.0)["pass"] is False
    assert evaluate_envelope_gate(5.0 + EPS, box_min=5.0, box_max=5.0)["pass"] is False


def test_envelope_gate_echoes_its_own_inputs():
    """The artifact's audit trail: a gate that reports a box it did not apply
    is unfalsifiable downstream."""
    from fannie_replication import evaluate_envelope_gate

    g = evaluate_envelope_gate(5.0, box_min=BOX_MIN, box_max=BOX_MAX)
    assert g["marginal_pp"] == 5.0
    assert g["box_min"] == BOX_MIN
    assert g["box_max"] == BOX_MAX

    # HOLE (adversarial mutation pass). 5.0, BOX_MIN and BOX_MAX all survive a
    # round(x, 2) on the echoed marginal, so the box was pinned exactly while
    # the marginal itself was not — the one number of the three the manuscript
    # actually quotes. Echo a value with digits past the second decimal.
    precise = 8.123456789
    g2 = evaluate_envelope_gate(precise, box_min=BOX_MIN, box_max=BOX_MAX)
    assert g2["marginal_pp"] == precise
    assert repr(g2["marginal_pp"]) == repr(precise)


def test_nan_marginal_cannot_pass():
    """A NaN marginal (a failed scoring run) must not be reported as a PASS.

    Each leg is asserted SEPARATELY, not just the conjunction. Asserting only
    `pass` is False is too weak: a De-Morgan rewrite of either leg alone
    (`positive = not (marginal_pp <= 0)`, or
    `in_envelope = not (x < box_min or x > box_max)`) turns that leg True on
    NaN, and the other leg still drags the conjunction to False — so the
    conjunction-only assertion survives both single-point rewrites and only
    fires if BOTH are broken at once. Pinning the legs individually kills each
    rewrite on its own.
    """
    from fannie_replication import evaluate_envelope_gate

    g = evaluate_envelope_gate(float("nan"), box_min=BOX_MIN, box_max=BOX_MAX)
    assert g["positive"] is False
    assert g["in_envelope"] is False
    assert g["pass"] is False

    # ... and with a box that would otherwise admit anything, so neither leg
    # can be False for an incidental reason.
    wide = evaluate_envelope_gate(
        float("nan"), box_min=float("-inf"), box_max=float("inf")
    )
    assert wide["in_envelope"] is False
    assert wide["positive"] is False
    assert wide["pass"] is False


# ---------------------------------------------------------------------------
# load_freddie_envelope — orientation of (min, max)
# ---------------------------------------------------------------------------
def test_load_freddie_envelope_returns_min_then_max(tmp_path, monkeypatch):
    """A min<->max inversion here silently inverts the box for every downstream
    envelope verdict while changing no printed number. Asymmetric, non-sorted
    input so an inversion cannot coincidentally agree."""
    import fannie_replication as fr

    path = tmp_path / "floor_band_cross_results.json"
    path.write_text(json.dumps({"box_marginals_pp": [
        {"marginal_pp": 7.40}, {"marginal_pp": 2.11},
        {"marginal_pp": 13.17}, {"marginal_pp": 9.02},
    ]}))
    monkeypatch.setattr(fr, "FLOOR_BAND_PATH", path)

    lo, hi = fr.load_freddie_envelope()
    assert (lo, hi) == (2.11, 13.17)
    assert lo < hi
    # And the box it yields must actually admit every observed cell.
    for cell in (2.11, 7.40, 9.02, 13.17):
        assert fr.evaluate_envelope_gate(cell, box_min=lo, box_max=hi)["in_envelope"]


def test_load_freddie_envelope_is_degenerate_on_a_single_cell(tmp_path, monkeypatch):
    import fannie_replication as fr

    path = tmp_path / "one.json"
    path.write_text(json.dumps({"box_marginals_pp": [{"marginal_pp": 4.25}]}))
    monkeypatch.setattr(fr, "FLOOR_BAND_PATH", path)
    assert fr.load_freddie_envelope() == (4.25, 4.25)


# ---------------------------------------------------------------------------
# freddie_parity_gate — tolerance edge
# ---------------------------------------------------------------------------
_REF_ANCHORS = {
    "null_trapped_b": 748.185, "null_share_pct": 97.834,
    "central_trapped_b": 818.530, "central_share_pct": 107.033,
}


def _parity_harness(monkeypatch, tmp_path, gots, ref=None):
    """Drive freddie_parity_gate with synthetic ABSOLUTE scores, bypassing the
    microsim entirely.

    `gots` gives the value each anchor should score to; anything omitted scores
    to the reference exactly. Absolute rather than offset because the tolerance
    edge has to be probed in EXACT floating point: `want + tol` does not
    generally satisfy `abs((want + tol) - want) == tol`, so an offset-based
    probe silently lands just off the edge and a `<=`-for-`<` slip survives it.
    """
    import extension_risk
    import pandas as pd

    import fannie_replication as fr

    ref = dict(_REF_ANCHORS if ref is None else ref)
    got = {**ref, **gots}
    ref_path = tmp_path / "no_lockin_null_results.json"
    ref_path.write_text(json.dumps(ref))
    monkeypatch.setattr(fr, "FREDDIE_NULL_RESULTS", ref_path)

    null_cache = tmp_path / "null.parquet"
    central_cache = tmp_path / "central.parquet"
    pd.DataFrame({"tag": ["null"]}).to_parquet(null_cache)
    pd.DataFrame({"tag": ["central"]}).to_parquet(central_cache)
    monkeypatch.setattr(fr, "FREDDIE_NULL_CACHE", null_cache)
    monkeypatch.setattr(fr, "MICROSIM_RESULTS_PATH", central_cache)

    def _fake_score(sim, empirical):
        if sim["tag"].iloc[0] == "null":
            return {"hazard_trapped_b": got["null_trapped_b"],
                    "share_explained_pct": got["null_share_pct"]}
        return {"hazard_trapped_b": got["central_trapped_b"],
                "share_explained_pct": got["central_share_pct"]}

    monkeypatch.setattr(extension_risk, "score_extension_risk", _fake_score)
    return fr.freddie_parity_gate(empirical=None)


# want == 0.0 makes `abs(got - want)` bit-exactly `got`, so `got = TOL` sits
# EXACTLY on the tolerance edge and nextafter() steps one ULP either side.
# An offset-based probe (`want + tol`) does NOT land on the edge — floating
# point makes `abs((want + tol) - want) != tol` for realistic anchors — and a
# `<`-for-`<=` slip survives it.
_TOL = 0.01
_EDGE_REF = {k: 0.0 for k in _REF_ANCHORS}


@pytest.mark.parametrize(
    "got,expected_pass",
    [
        (math.nextafter(_TOL, 0.0), True),   # one ULP inside
        (_TOL, True),                        # EXACTLY at tol: `<=` is inclusive
        (math.nextafter(_TOL, 1.0), False),  # one ULP outside
    ],
)
def test_parity_tolerance_edge_is_inclusive(tmp_path, monkeypatch, got, expected_pass):
    from fannie_replication import PARITY_TOL_B

    assert PARITY_TOL_B == _TOL  # literal: the pre-registered tolerance
    gate = _parity_harness(
        monkeypatch, tmp_path, {"central_trapped_b": got}, ref=_EDGE_REF
    )
    assert gate["central_trapped_b"]["pass"] is expected_pass
    assert gate["pass"] is expected_pass


def test_parity_tolerance_edge_is_inclusive_from_below(tmp_path, monkeypatch):
    """The same edge approached from the negative side: -tol is a PASS, one ULP
    beyond it is not."""
    at = _parity_harness(
        monkeypatch, tmp_path, {"null_trapped_b": -_TOL}, ref=_EDGE_REF
    )
    assert at["null_trapped_b"]["pass"] is True
    out = _parity_harness(
        monkeypatch, tmp_path,
        {"null_trapped_b": -math.nextafter(_TOL, 1.0)}, ref=_EDGE_REF,
    )
    assert out["null_trapped_b"]["pass"] is False


def test_parity_tolerance_is_two_sided(tmp_path, monkeypatch):
    """|got - want| — a dropped abs() would let an arbitrarily NEGATIVE drift
    pass while catching only positive drift."""
    over = _parity_harness(
        monkeypatch, tmp_path,
        {"null_trapped_b": _REF_ANCHORS["null_trapped_b"] - 0.5},
    )
    assert over["null_trapped_b"]["pass"] is False
    assert over["pass"] is False


def test_parity_gate_pass_requires_all_four_checks(tmp_path, monkeypatch):
    """Each of the four anchors must be able to sink the gate on its own; an
    `any`-for-`all` slip would let three failures through."""
    for key in _REF_ANCHORS:
        gate = _parity_harness(
            monkeypatch, tmp_path, {key: _REF_ANCHORS[key] + 1.0}
        )
        assert gate[key]["pass"] is False, key
        assert gate["pass"] is False, key

    clean = _parity_harness(monkeypatch, tmp_path, {})
    assert clean["pass"] is True


def test_parity_gate_reports_the_tolerance_it_applied(tmp_path, monkeypatch):
    from fannie_replication import PARITY_TOL_B, PARITY_TOL_PP

    assert PARITY_TOL_PP == 0.01
    gate = _parity_harness(monkeypatch, tmp_path, {})
    assert gate["central_trapped_b"]["tol"] == PARITY_TOL_B
    assert gate["central_share_pct"]["tol"] == PARITY_TOL_PP
    assert math.isclose(gate["null_trapped_b"]["want"], 748.185)


def test_parity_gate_does_not_transpose_got_and_want(tmp_path, monkeypatch):
    """The audit trail must say which side is the fresh score and which is the
    committed reference.

    The tolerance tests above cannot see a got/want transposition, because
    |got - want| is symmetric AND every anchor they leave alone scores exactly
    to its reference — got == want, so the swap is invisible. Drive a KNOWN
    offset on one anchor, in a known direction, so the two sides are
    distinguishable, and a transposed report is caught even though the verdict
    it produces is unchanged.
    """
    want = _REF_ANCHORS["null_trapped_b"]
    got = want + 5.0
    gate = _parity_harness(monkeypatch, tmp_path, {"null_trapped_b": got})

    assert gate["null_trapped_b"]["got"] == pytest.approx(got)
    assert gate["null_trapped_b"]["want"] == pytest.approx(want)
    assert gate["null_trapped_b"]["got"] > gate["null_trapped_b"]["want"]
    # the untouched anchors still report their reference on the `want` side
    assert gate["central_trapped_b"]["want"] == pytest.approx(
        _REF_ANCHORS["central_trapped_b"]
    )
    # and the drift is genuinely out of tolerance, so this is not a no-op setup
    assert gate["null_trapped_b"]["pass"] is False


def test_parity_gate_scores_the_null_cache_as_the_null_leg(tmp_path,
                                                           monkeypatch):
    """A swap of the two microsim caches would compare the central run against
    the null reference and vice versa. Give the two legs distinguishable
    scores and check each lands against its own anchor."""
    gate = _parity_harness(
        monkeypatch, tmp_path,
        {"null_trapped_b": _REF_ANCHORS["null_trapped_b"] + 3.0},
    )
    assert gate["null_trapped_b"]["pass"] is False
    assert gate["central_trapped_b"]["pass"] is True


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
