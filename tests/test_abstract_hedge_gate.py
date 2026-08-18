"""Perturbation battery for liveness gate #68 (abstract-scoped hedge spans).

A gate that cannot be made to fail is not a gate. The suite passing tells you
nothing about whether any individual gate bites, so this test mutates the
abstract and asserts the gate flips to FAIL for every mutation, and stays PASS
for benign rewrites.

Two rules this file obeys, both learned the hard way:

1. It imports ABSTRACT_HEDGES and abstract_hedge_check from liveness_gates and
   never redefines them. The first cut of gate #68 was "validated" by a
   prototype carrying its own copy of the span dict; the prototype reported
   every variant caught while the shipped design still had the seam hole
   below. A test that mirrors the implementation only confirms the
   implementation's own assumptions.

2. The two attacks that actually found bugs (SEAM and COMMENT) are first-class
   cases here, not afterthoughts. The original battery had 14 mutations, all
   passing, and neither of these was among them.

Runs against the gate's pure rule rather than main(), so it does not need any
run artifact and stays fast.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import (  # noqa: E402
    ABSTRACT_BOUNDS,
    ABSTRACT_HEDGES,
    RELOCATED_TO_BODY,
    TEX,
    abstract_hedge_check,
)

# ROUND-23: the abstract was cut 574 -> 263 words and five claims left it. Their
# hedges left with them and are now pinned against the BODY. A hedge only has to
# travel with the claim it scopes -- but it does have to travel, so this file
# checks BOTH halves and the coverage test below unions the two dicts. If a
# future round moves a span back into the abstract, the union keeps passing and
# the per-dict mutation tests are what notice.
ALL_SPANS = {**ABSTRACT_HEDGES, **RELOCATED_TO_BODY}

# Every hedge the round's handoff named. Each must be covered by some span, or
# the gate silently stopped protecting one of them.
HANDOFF_PHRASES = [
    "genuine surprise",
    "large majority",
    "fifty-seed mean",
    "recalibrated on real loan covariates",
    "institutional cash-flow",
    "turnover floor",
    "uniform-spread",
    "input-stability check",
    "modeling paradigm",
]


@pytest.fixture(scope="module")
def tex() -> str:
    return TEX.read_text()


@pytest.fixture(scope="module")
def abstract(tex: str) -> str:
    i = tex.find(ABSTRACT_BOUNDS[0])
    j = tex.find(ABSTRACT_BOUNDS[1], i + 1)
    assert i != -1 and j != -1, "abstract environment not found in the manuscript"
    return tex[i + len(ABSTRACT_BOUNDS[0]):j]


def _swap(tex: str, abstract: str, mutated: str) -> str:
    """Rebuild the manuscript with a mutated abstract."""
    assert mutated != abstract, "mutation was a no-op -- the test would be vacuous"
    return tex.replace(abstract, mutated)


def test_control_passes(tex: str) -> None:
    """The real manuscript must pass, or every failure below is meaningless."""
    ok, info = abstract_hedge_check(tex)
    assert ok, f"gate #68 fails the real manuscript: {info}"
    assert info["missing"] == []
    assert info["words"] > 100


@pytest.mark.parametrize("phrase", HANDOFF_PHRASES)
def test_every_handoff_phrase_is_covered_by_a_span(phrase: str) -> None:
    """Each named hedge must appear inside at least one gated span."""
    covering = [k for k, v in ALL_SPANS.items() if phrase in v]
    assert covering, (
        f"{phrase!r} is named in the handoff but no span covers it, in either "
        f"the abstract-scoped or the body-scoped dict")


def _mutations(abstract: str) -> dict[str, str]:
    """Each entry must flip the gate to FAIL."""
    return {
        # --- ROUND-27 option-2 cut: the SEAM attack's abstract target (the
        # fed-projection sentence) left the abstract with the expectations
        # pair. The seam lesson survives structurally: the pair's body pins
        # (fed_projection_body, surprise_denominator_body) each join
        # attribution/switch to hedge in ONE span, so opening a boundary
        # between them deletes the span and the body-mutation battery below
        # catches it. The two seam cases, the two projection-misattribution
        # cases, drops_large_majority, and drops_denominator_switch are
        # retired with the sentences they mutated.
        # COMMENT: the hedge survives in the source but not in the PDF. This
        # passed while the gate read raw tex instead of comment-stripped text.
        "comment_smuggled_hedge": abstract.replace(
            "The institutional cash-flow cost is small",
            "The cash-flow cost is large\n% The institutional cash-flow cost is small"),
        "whole_abstract_commented_out": "\n".join(
            "% " + line for line in abstract.splitlines()),
        # --- dropped hedges ----------------------------------------------
        "drops_institutional_scope": abstract.replace(
            "The institutional cash-flow cost is small", "The cost is small"),
        "drops_baseline_turnover": abstract.replace(
            "scheduled amortization plus a turnover floor read from "
            "realized, partly behavioral turnover, accounts",
            "scheduled amortization accounts"),
        # --- scoping ------------------------------------------------------
        # the body keeps every phrase; only the abstract is gutted. A
        # whole-file count gate would pass this.
        "abstract_emptied_body_intact": " ",
        "abstract_reduced_to_stub": " Lock-in raised the Federal Reserve's QT "
                                    "shortfall. ",
        # --- ROUND-27: the ABM and cross-design readings LEFT the abstract
        # again (author-directed cut), taking their four hedges with them
        # under the round-23 hedges-travel-with-claims rule. The four
        # ROUND-24 abstract mutation cases that lived here are retired with
        # the claims; the same hedges are now body-pinned
        # (RELOCATED_TO_BODY: abm_seed_averaged_body,
        # crossdesign_recalibrated_body, crossdesign_seed_body,
        # crossdesign_reweight_body, paradigm_attribution_hedged_body) and
        # exercised by the body-mutation battery below.
    }


MUTATION_NAMES = [
    "comment_smuggled_hedge",
    "whole_abstract_commented_out",
    "drops_institutional_scope",
    "drops_baseline_turnover",
    "abstract_emptied_body_intact",
    "abstract_reduced_to_stub",
]


def test_mutation_list_matches_definitions(abstract: str) -> None:
    """Guard against a mutation being defined but never parametrized (or vice
    versa) -- an unrun mutation is a hole that looks like coverage."""
    assert sorted(_mutations(abstract)) == sorted(MUTATION_NAMES)


@pytest.mark.parametrize("name", MUTATION_NAMES)
def test_mutation_flips_gate_to_fail(name: str, tex: str, abstract: str) -> None:
    mutated = _mutations(abstract)[name]
    ok, info = abstract_hedge_check(_swap(tex, abstract, mutated))
    assert not ok, (
        f"gate #68 PASSED the {name!r} mutation -- it does not bite here. "
        f"info={info}"
    )


# ROUND-23: the five relocated spans need their own mutation set. Deleting the
# abstract mutations when the claims moved would have left them protected on
# paper and untested in practice -- coverage that exists only in a dict is the
# hole this whole file was written to close.
def _body_mutations(tex: str) -> dict[str, str]:
    """Each entry mutates the BODY and must flip the gate to FAIL."""
    return {
        "body_drops_seed_averaging": tex.replace(
            "13.6\\% on the fifty-seed mean", "13.6\\%", 1),
        "body_drops_recalibrated": tex.replace(
            "A cross-design variant of the ABM recalibrated on real loan "
            "covariates", "A cross-design variant of the ABM", 1),
        "body_drops_holdout_relabel": tex.replace(
            "the nineteen-month floor variant reported later is an "
            "input-stability check rather than an outcome holdout",
            "the nineteen-month floor variant reported later is a holdout", 1),
        # ROUND-24c: this span now occurs TWICE in the body. Section IV's lead
        # was rewritten to open with the cross-design result and repeats the
        # paradigm hedge verbatim, which is the right thing for the manuscript
        # to do -- a hedge should travel with the claim it scopes, and the claim
        # is now made in two places. The consequence for this gate is real and
        # is recorded rather than hidden: RELOCATED_TO_BODY is a whole-body
        # PRESENCE rule, so deleting either occurrence alone no longer trips it,
        # and the mutation below must therefore remove every occurrence to test
        # what the rule actually promises ("pinned somewhere a reader meets it").
        # If a future round needs per-site protection, that is a new gate, not a
        # tighter mutation here.
        "body_drops_paradigm_hedge": tex.replace(
            "be cleanly attributed to modeling paradigm rather than to "
            "calibration and data source",
            "be attributed to modeling paradigm"),
        "body_drops_allocation_naming": tex.replace(
            "they require the uniform-spread allocation, because the "
            "settlement-aware allocation puts the anticipated share at 75.6\\%",
            "they require one of the two disclosed allocations", 1),
    }


BODY_MUTATION_NAMES = [
    "body_drops_seed_averaging",
    "body_drops_recalibrated",
    "body_drops_holdout_relabel",
    "body_drops_paradigm_hedge",
    "body_drops_allocation_naming",
]


def test_body_mutation_list_matches_definitions(tex: str) -> None:
    assert sorted(_body_mutations(tex)) == sorted(BODY_MUTATION_NAMES)


@pytest.mark.parametrize("name", BODY_MUTATION_NAMES)
def test_body_mutation_flips_gate_to_fail(name: str, tex: str) -> None:
    """A relocated hedge deleted from the body must still fail the gate."""
    mutated = _body_mutations(tex)[name]
    assert mutated != tex, f"body mutation {name!r} was a no-op -- test vacuous"
    ok, info = abstract_hedge_check(mutated)
    assert not ok, (
        f"gate #68 PASSED the {name!r} body mutation -- the relocated span is "
        f"not actually protected. info={info}")


BENIGN = {
    "reword_unrelated_sentence": (
        "The cost to households who could not move is real.",
        "The cost to households who could not move is real and large."),
    "reword_unrelated_lead": (
        "lock households into old, cheap loans",
        "lock households into old and cheap loans"),
}


@pytest.mark.parametrize("name", sorted(BENIGN))
def test_benign_rewrite_still_passes(name: str, tex: str, abstract: str) -> None:
    """A gate that fires on everything is as useless as one that never fires."""
    old, new = BENIGN[name]
    assert old in abstract, f"benign fixture {old!r} no longer in the abstract"
    ok, info = abstract_hedge_check(_swap(tex, abstract, abstract.replace(old, new)))
    assert ok, f"gate #68 false-alarmed on benign rewrite {name!r}: {info}"


# ROUND-27: the ROUND-24 known seam (recalibration hedge vs the 60.2/76.3
# numbers, unjoinable across the archived variant) is RETIRED, per the old
# test's own instruction: the cross-design sentences left the abstract in
# the author-directed cut, so the seam no longer exists to measure. The
# claims are body-pinned (RELOCATED_TO_BODY) and exercised above.
