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
    TEX,
    abstract_hedge_check,
)

# Every hedge the round's handoff named. Each must be covered by some span, or
# the gate silently stopped protecting one of them.
HANDOFF_PHRASES = [
    "genuine surprise",
    "large majority",
    "averaged across seeds",
    "recalibrated",
    "institutional cash-flow",
    "baseline involuntary turnover",
    "central allocation",
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
    covering = [k for k, v in ABSTRACT_HEDGES.items() if phrase in v]
    assert covering, f"{phrase!r} is named in the handoff but no span covers it"


def _mutations(abstract: str) -> dict[str, str]:
    """Each entry must flip the gate to FAIL."""
    return {
        # --- the two that found real holes -------------------------------
        # SEAM: both fragments still present, but a sentence boundary opened
        # between them reattributes the projection to the author. This passed
        # the split-span version of the gate.
        "seam_reattribution_to_author": abstract.replace(
            "The Federal Reserve's own ex-ante projection anticipated the large "
            "majority of the realized shortfall.",
            "The Federal Reserve's own ex-ante projection is described in the "
            "appendix. My model anticipated the large majority of the realized "
            "shortfall."),
        "seam_reattribution_to_consensus": abstract.replace(
            "The Federal Reserve's own ex-ante projection anticipated the large "
            "majority of the realized shortfall.",
            "The Federal Reserve's own ex-ante projection appears below. The "
            "prevailing consensus anticipated the large majority of the "
            "realized shortfall."),
        # COMMENT: the hedge survives in the source but not in the PDF. This
        # passed while the gate read raw tex instead of comment-stripped text.
        "comment_smuggled_hedge": abstract.replace(
            "The institutional cash-flow cost is small",
            "The cash-flow cost is large\n% The institutional cash-flow cost is small"),
        "whole_abstract_commented_out": "\n".join(
            "% " + line for line in abstract.splitlines()),
        # --- misattribution ----------------------------------------------
        "projection_claimed_by_author": abstract.replace(
            "The Federal Reserve's own ex-ante projection anticipated",
            "My own ex-ante projection anticipated"),
        "projection_attributed_to_consensus": abstract.replace(
            "The Federal Reserve's own ex-ante projection",
            "The prevailing ex-ante consensus projection"),
        # --- dropped hedges ----------------------------------------------
        "drops_large_majority": abstract.replace(
            "anticipated the large majority of the realized shortfall",
            "anticipated the realized shortfall"),
        "drops_central_allocation": abstract.replace(
            " under the central allocation", ""),
        "drops_genuine_surprise": abstract.replace(
            "roughly half the genuine surprise under the central allocation",
            "roughly half the shortfall under the central allocation"),
        "drops_denominator_switch": abstract.replace(
            "Measured against that projection rather than the never-binding cap, "
            "the", "The"),
        "drops_seed_averaging": abstract.replace(" averaged across seeds", ""),
        "drops_recalibrated": abstract.replace(
            "recalibrated on real loan covariates", "on real loan covariates"),
        "drops_institutional_scope": abstract.replace(
            "The institutional cash-flow cost is small", "The cost is small"),
        "drops_involuntary_turnover": abstract.replace(
            "scheduled amortization and baseline involuntary turnover undershoot",
            "scheduled amortization undershoots"),
        # --- relocation (what proximity windows cannot catch) -------------
        "relocates_central_allocation": abstract.replace(
            "accounts for roughly half the genuine surprise under the central "
            "allocation.",
            "accounts for roughly half the genuine surprise. The central "
            "allocation is described below."),
        # --- scoping ------------------------------------------------------
        # the body keeps every phrase; only the abstract is gutted. A
        # whole-file count gate would pass this.
        "abstract_emptied_body_intact": " ",
        "abstract_reduced_to_stub": " Lock-in raised the Federal Reserve's QT "
                                    "shortfall. ",
    }


MUTATION_NAMES = [
    "seam_reattribution_to_author",
    "seam_reattribution_to_consensus",
    "comment_smuggled_hedge",
    "whole_abstract_commented_out",
    "projection_claimed_by_author",
    "projection_attributed_to_consensus",
    "drops_large_majority",
    "drops_central_allocation",
    "drops_genuine_surprise",
    "drops_denominator_switch",
    "drops_seed_averaging",
    "drops_recalibrated",
    "drops_institutional_scope",
    "drops_involuntary_turnover",
    "relocates_central_allocation",
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


BENIGN = {
    "reword_unrelated_sentence": (
        "The mobility cost is real.",
        "The mobility cost is real and borne by households."),
    "reword_unrelated_lead": (
        "It cost less than the shortfall suggests.",
        "The cost is smaller than the shortfall suggests."),
}


@pytest.mark.parametrize("name", sorted(BENIGN))
def test_benign_rewrite_still_passes(name: str, tex: str, abstract: str) -> None:
    """A gate that fires on everything is as useless as one that never fires."""
    old, new = BENIGN[name]
    assert old in abstract, f"benign fixture {old!r} no longer in the abstract"
    ok, info = abstract_hedge_check(_swap(tex, abstract, abstract.replace(old, new)))
    assert ok, f"gate #68 false-alarmed on benign rewrite {name!r}: {info}"
