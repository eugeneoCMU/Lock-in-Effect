"""Perturbation battery for liveness gate #100 (Section IV leads with the cross-design).

Section IV used to open with the production 13.6% and treat the cross-design leg
as a qualifier three sections later, so it read as if 13.6% were the result. The
round-24c reframing was entirely PROSE -- not one number moved -- which is the
case `HANDOFF_round22.md` §4.2 names as the gates' structural blind spot. Gate
#100 closes it; this file is what proves the gate bites.

Two attacks are first-class here, because they are the two cheapest edits anyone
would make to that paragraph:

1. ORDERING. Every span survives a paragraph that states the falsification
   verdict first and the cross-design afterwards -- the arrangement the round
   removed. Only the ordering assert catches it.

2. DROPPING A BOUND. The lead quotes 76.3% at book composition; round 23 caught
   that same reweight being quoted one-sidedly, since it moves the FROZEN leg
   down to 12.6%. Keeping 76.3% and dropping either bound is an overclaim that
   leaves every number in place.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import (  # noqa: E402
    ABM_LEAD_OPENER,
    ABM_LEAD_SPANS,
    TEX,
    abm_lead_check,
)


@pytest.fixture(scope="module")
def tex() -> str:
    return TEX.read_text()


def _lead(tex: str) -> str:
    lines = [ln for ln in tex.split("\n") if ln.startswith(ABM_LEAD_OPENER)]
    assert len(lines) == 1, f"expected one Section IV lead paragraph, found {len(lines)}"
    return lines[0]


def _mutate_lead(tex: str, old: str, new: str) -> str:
    """Mutate INSIDE the lead paragraph, not the first match in the file.

    This exists because the naive `tex.replace(span, "", 1)` is vacuous for any
    span that also occurs earlier in the manuscript. `60.2\\% averaged over fifty
    seeds` occurs four times and the first is in the ABSTRACT, so the naive
    mutation deleted the abstract's copy, left the lead untouched, and reported
    a gate hole that did not exist. A test that mutates the wrong text proves
    nothing about the gate, in either direction.
    """
    lead = _lead(tex)
    assert old in lead, f"{old!r} is not in the Section IV lead paragraph"
    return tex.replace(lead, lead.replace(old, new, 1), 1)


def test_shipped_manuscript_passes(tex):
    ok, info = abm_lead_check(tex)
    assert ok, f"gate #100 fails the shipped manuscript: {info}"
    assert info["ordered"] and info["ve_declines"]


@pytest.mark.parametrize("key", sorted(ABM_LEAD_SPANS))
def test_deleting_any_span_fails(tex, key):
    mutated = _mutate_lead(tex, ABM_LEAD_SPANS[key], "")
    assert mutated != tex, f"span {key} is not in the manuscript verbatim"
    ok, info = abm_lead_check(mutated)
    assert not ok, f"deleting span {key} left gate #100 green"
    assert key in info["missing"] or not info["ordered"]


# --------------------------------------------------------------------------
# Attack 1: the reversion. Every literal survives; only the order changes.
# --------------------------------------------------------------------------
def test_verdict_before_crossdesign_fails(tex):
    """Put the falsification verdict back in front. A span-presence check
    accepts this and it undoes the entire round."""
    lead = _lead(tex)
    reverted = (
        "This section is a falsification test of the household-choice hypothesis: "
        "no specification tested here explains the Federal Reserve's trapped liquidity. "
        + lead.split("This section is a falsification test", 1)[1])
    mutated = tex.replace(lead, reverted, 1)
    ok, info = abm_lead_check(mutated)
    assert not ok, "gate #100 accepted a verdict-first lead"
    assert not info["ordered"], f"the ordering assert must be what fires: {info}"


# --------------------------------------------------------------------------
# Attack 2: keep 76.3%, drop a bound. Every number stays put.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("key", [
    "bound_frozen_leg",
    "bound_behavioral_synthetic",
    "bound_verdict_wording",
])
def test_dropping_a_bound_fails(tex, key):
    mutated = _mutate_lead(tex, ABM_LEAD_SPANS[key], "")
    ok, info = abm_lead_check(mutated)
    assert not ok, f"gate #100 accepted a lead with {key} removed"
    assert key in info["missing"]
    # and the favourable number is still sitting there, which is the whole point
    assert ABM_LEAD_SPANS["reweighted"] in mutated


def test_verdict_hardened_from_cannot_attribute_to_is_not_fails(tex):
    """`cannot be cleanly attributed to paradigm` is a limit on what the test
    resolves. `is not a paradigm effect` is a verdict the run does not support --
    the same hardening round 23 caught on the hull's upper end."""
    mutated = _mutate_lead(
        tex, "cannot, on that test alone, be cleanly attributed to modeling paradigm",
        "is not a modeling-paradigm effect")
    assert mutated != tex
    ok, _ = abm_lead_check(mutated)
    assert not ok


# --------------------------------------------------------------------------
# Structural attacks.
# --------------------------------------------------------------------------
def test_paragraph_split_fails(tex):
    lead = _lead(tex)
    half = lead.index("What this section falsifies")
    mutated = tex.replace(lead, lead[:half] + "\n\n" + lead[half:], 1)
    ok, _ = abm_lead_check(mutated)
    assert not ok


def test_commented_out_lead_fails(tex):
    lead = _lead(tex)
    mutated = tex.replace(lead, "% " + lead, 1)
    ok, _ = abm_lead_check(mutated)
    assert not ok


def test_section_ve_dropping_its_declination_fails(tex):
    """The lead's consistency paragraph says V.E DECLINES this same number as
    evidence about the elasticity's size. If V.E stops declining it, the paper
    is using one result two ways with nothing reconciling them."""
    mutated = tex.replace(
        "the third is a recovery level, which this design does not identify",
        "the third is a recovery level", 1)
    assert mutated != tex
    ok, info = abm_lead_check(mutated)
    assert not ok and not info["ve_declines"]


# --------------------------------------------------------------------------
# Benign rewrites stay green.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("old,new", [
    ("because that result governs how everything below should be read",
     "because that result governs how the rest of this section should be read"),
    ("A second qualifier travels with the verdict and is developed where it binds",
     "A second qualifier travels with the verdict, and is developed where it binds"),
])
def test_benign_rewrites_stay_green(tex, old, new):
    mutated = _mutate_lead(tex, old, new)
    assert mutated != tex, f"benign fixture {old!r} is stale"
    ok, info = abm_lead_check(mutated)
    assert ok, f"gate #100 false-alarmed: {info}"


# --------------------------------------------------------------------------
# Coverage against what the round committed to.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("phrase", [
    "60.2\\%",     # the cross-design level that leads
    "50\\%",       # the pre-committed threshold it clears
    "76.3\\%",     # the book-composition reweight
    "12.6\\%",     # and the same reweight's effect on the frozen leg
])
def test_every_committed_number_is_pinned(tex, phrase):
    covered = any(phrase in span for span in ABM_LEAD_SPANS.values())
    assert covered, f"no span pins {phrase!r}; it can be deleted while gate #100 stays green"
    assert phrase in _lead(tex)
