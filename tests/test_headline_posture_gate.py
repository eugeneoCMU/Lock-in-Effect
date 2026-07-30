"""Perturbation battery for liveness gate #99 (the abstract leads with the range).

Section V.E argues that the identified content is the range and that $+5.6$ is
an upper-middle member of it. Before this round the abstract, the introduction,
Table 1 and the conclusion all led with the point, so the front of the paper
argued against its own Section V.E. Gate #99 keeps that fixed.

The case this file exists for is the ORDERING one. Every span in ABSTRACT_POSTURE
survives an abstract that states the point first and the range second -- the
exact arrangement this round removed -- so a span-presence check alone would not
catch a reversion. `test_point_before_range_fails` is therefore the load-bearing
test here, not a nice-to-have.

Follows the two rules `test_abstract_hedge_gate.py` records: it imports the
shipped rule rather than redefining it, and it treats the structural attack as a
first-class case.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import (  # noqa: E402
    ABSTRACT_BOUNDS,
    ABSTRACT_POSTURE,
    TEX,
    abstract_posture_check,
)


@pytest.fixture(scope="module")
def tex() -> str:
    return TEX.read_text()


@pytest.fixture(scope="module")
def abstract(tex: str) -> str:
    i = tex.find(ABSTRACT_BOUNDS[0])
    j = tex.find(ABSTRACT_BOUNDS[1], i + 1)
    assert i != -1 and j != -1, "abstract environment not found"
    return tex[i + len(ABSTRACT_BOUNDS[0]):j]


def _swap(tex: str, abstract: str, mutated: str) -> str:
    assert mutated != abstract, "mutation was a no-op -- the test would be vacuous"
    return tex.replace(abstract, mutated, 1)


def test_shipped_manuscript_passes(tex):
    ok, info = abstract_posture_check(tex)
    assert ok, f"gate #99 fails the shipped manuscript: {info}"
    assert info["ordered"]


@pytest.mark.parametrize("key", sorted(ABSTRACT_POSTURE))
def test_deleting_any_span_fails(tex, key):
    mutated = tex.replace(ABSTRACT_POSTURE[key], "", 1)
    assert mutated != tex, f"span {key} is not in the manuscript verbatim"
    ok, info = abstract_posture_check(mutated)
    assert not ok, f"deleting span {key} left gate #99 green"


# --------------------------------------------------------------------------
# THE reversion. Both halves survive; only the order changes.
# --------------------------------------------------------------------------
def test_point_before_range_fails(tex, abstract):
    """Put the point back in front, keeping every literal. This is the exact
    arrangement round 24b removed, and a span-presence check accepts it."""
    mutated = (
        " \\noindent Baseline turnover (itself read from realized, "
        "partly behavioral turnover) sets the floor. "
        "Lock-in itself adds $+5.6$ points, or \\$42.6 billion. "
        "What lock-in itself adds is a range rather than a number. "
        "The design bounds it between $+2.9$ and $+8.7$ points under its "
        "production floor form (the floor read's sampling error at my "
        "central elasticity; a wild-cluster interval on 31 clusters; the "
        "percentile read under-covers), with a "
        "form-conditional hull of $+3.5$ to $+13.1$ points, and it identifies "
        "levels only. Inside that range, $+5.6$ points, or \\$42.6 billion, is "
        "the value at the calibration I headline, and the corrections I can "
        "measure to the baseline turnover floor or to the accounting basis "
        "no longer all run one way. ")
    ok, info = abstract_posture_check(_swap(tex, abstract, mutated))
    assert not ok, "gate #99 accepted a point-first abstract"
    assert info["missing"] == [] and not info["ordered"], (
        "the ordering assert must be what fires here, not a missing span -- "
        f"info={info}")


def test_frame_dropped_from_the_corrections_claim_fails(tex):
    """Without `to the baseline turnover floor or to the accounting basis`
    the claim is FALSE: the additive form (+11.2) and the Fonseca anchor (+11.5)
    move the marginal up. An unframed 'every correction moves it down' is the
    overclaim HANDOFF_round25 §4.2 records."""
    mutated = tex.replace(
        ABSTRACT_POSTURE["corrections_framed"],
        "the corrections I can measure no longer all run one way", 1)
    assert mutated != tex
    ok, _ = abstract_posture_check(mutated)
    assert not ok


def test_range_softened_to_an_afterthought_fails(tex):
    """`a range around that` restores the old subordinate reading -- the point
    is the claim and the range is a caveat on it."""
    mutated = tex.replace(
        "What lock-in itself adds is a range rather than a number",
        "What the design pins down is a range around that", 1)
    assert mutated != tex
    ok, _ = abstract_posture_check(mutated)
    assert not ok


def test_commented_out_posture_fails(tex, abstract):
    """A commented posture is absent from the PDF. The rule strips comments."""
    mutated = abstract.replace(
        ABSTRACT_POSTURE["range_not_number"],
        "% " + ABSTRACT_POSTURE["range_not_number"])
    ok, _ = abstract_posture_check(_swap(tex, abstract, mutated))
    assert not ok


# --------------------------------------------------------------------------
# Benign rewrites stay green, or the gate freezes prose instead of pinning a
# claim.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("old,new", [
    ("however the rate-responsive margin behaves",
     "however the rate-responsive margin moves"),
    ("The cost to households who could not move is real.",
     "The cost to households who could not move is real and unevenly borne."),
])
def test_benign_rewrites_stay_green(tex, old, new):
    mutated = tex.replace(old, new, 1)
    assert mutated != tex, f"benign fixture {old!r} is stale"
    ok, info = abstract_posture_check(mutated)
    assert ok, f"gate #99 false-alarmed: {info}"


# --------------------------------------------------------------------------
# The posture must agree with Section V.E. Two places stating it means two
# places it can drift, so check they still say the same thing.
# --------------------------------------------------------------------------
def test_abstract_posture_agrees_with_section_ve(tex):
    ve = [ln for ln in tex.split("\n") if ln.startswith("A seventh qualification")]
    assert len(ve) == 1, "Section V.E's assembly paragraph is missing or duplicated"
    assert "$+2.9$ to $+8.7$ points" in ve[0], "V.E no longer quotes the binding interval"
    assert "no interior member is privileged, and the range rather than any point is what the design delivers" in ve[0], (
        "V.E no longer states the range-carries reading of Section V.E")
