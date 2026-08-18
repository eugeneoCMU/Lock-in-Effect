"""Perturbation battery for liveness gate #98 (the assembled corrections, V.E).

A gate that cannot be made to fail is not a gate, and round 20 found holes in
five of five gates that had been called hardened. So this file mutates the
paragraph and asserts the gate flips to FAIL for every mutation that removes
something the round committed to, and stays PASS for rewrites that do not.

It follows the two rules `test_abstract_hedge_gate.py` records:

1. It imports ASSEMBLY_SPANS and assembly_check from liveness_gates and never
   redefines them. A test carrying its own copy of the span dict can only
   confirm the implementation's own assumptions.

2. The structural attack is a first-class case, not an afterthought. The one
   that matters here is the PARAGRAPH SPLIT: every span survives in the file,
   the assembly does not, and a whole-file count gate passes it happily. That
   attack is the reason the gate is paragraph-scoped at all.

Runs against the pure rule, so it needs no run artifact and stays fast.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import (  # noqa: E402
    ASSEMBLY_OPENER,
    ASSEMBLY_SPANS,
    ASSEMBLY_TABLE_SPANS,
    TEX,
    assembly_check,
)


@pytest.fixture(scope="module")
def tex() -> str:
    return TEX.read_text()


def _para(tex: str) -> str:
    lines = [ln for ln in tex.split("\n") if ln.startswith(ASSEMBLY_OPENER)]
    assert len(lines) == 1, f"expected exactly one assembly paragraph, found {len(lines)}"
    return lines[0]


def _mutate_para(tex: str, old: str, new: str) -> str:
    """Mutate INSIDE the assembly paragraph, not the first match in the file.

    ROUND-24c: the sibling battery for gate #100 reported a hole that did not
    exist, because `tex.replace(span, "", 1)` had deleted an earlier copy of the
    span from the ABSTRACT and left the target paragraph untouched. Every span
    in ASSEMBLY_SPANS happens to occur first in its own paragraph today, so the
    naive form works here by luck. This removes the luck.
    """
    para = _para(tex)
    assert old in para, f"{old!r} is not in the assembly paragraph"
    return tex.replace(para, para.replace(old, new, 1), 1)


def test_shipped_manuscript_passes(tex):
    ok, info = assembly_check(tex)
    assert ok, f"gate #98 fails on the shipped manuscript: {info}"
    assert info["paragraphs"] == 1


# --------------------------------------------------------------------------
# Every span, deleted one at a time. A span that can be deleted without the
# gate noticing is not pinned, whatever the dict says.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("key", sorted(ASSEMBLY_SPANS))
def test_deleting_any_span_fails(tex, key):
    mutated = _mutate_para(tex, ASSEMBLY_SPANS[key], "")
    assert mutated != tex, f"span {key} not found verbatim in the manuscript"
    ok, info = assembly_check(mutated)
    assert not ok, f"deleting span {key} left gate #98 green"
    assert key in info["missing"]


# ROUND-27: tab:assembly's whole-file spans. Each span string is unique in the
# manuscript, so replace(..., 1) cannot silently mutate a different site (the
# round-24c vacuous-mutation class); the table_missing assert would catch a
# no-op replace regardless.
@pytest.mark.parametrize("key", sorted(ASSEMBLY_TABLE_SPANS))
def test_deleting_any_table_span_fails(tex, key):
    span = ASSEMBLY_TABLE_SPANS[key]
    assert tex.count(span) == 1, f"table span {key} is not unique in the manuscript"
    mutated = tex.replace(span, "", 1)
    ok, info = assembly_check(mutated)
    assert not ok, f"deleting table span {key} left gate #98 green"
    assert key in info["table_missing"]


# --------------------------------------------------------------------------
# The structural attacks. Each keeps every literal somewhere in the file.
# --------------------------------------------------------------------------
def test_paragraph_split_fails(tex):
    """Split the paragraph in two and every span survives in the file while the
    assembly does not. This is the attack the gate is paragraph-scoped for."""
    para = _para(tex)
    half = para.index("Three things stop the list")
    mutated = tex.replace(para, para[:half] + "\n\n" + para[half:], 1)
    ok, info = assembly_check(mutated)
    assert not ok
    # the opener line still exists; the spans after the split are what left it
    assert info["paragraphs"] == 1 and info["missing"]


def test_relocating_the_posture_into_a_neighbouring_paragraph_fails(tex):
    """Move the commitment out of the assembly and into its own paragraph. A
    proximity gate would accept this; the claim it concludes would be gone."""
    para = _para(tex)
    posture = ASSEMBLY_SPANS["posture_retired_range_carries"]
    mutated = tex.replace(para, para.replace(posture, "") + "\n\n" + posture + ".", 1)
    ok, _ = assembly_check(mutated)
    assert not ok


def test_duplicate_opener_fails(tex):
    """Two paragraphs opening the same way is ambiguous about which one the
    gate is reading, so the rule refuses rather than picking."""
    para = _para(tex)
    mutated = tex.replace(para, para + "\n\n" + ASSEMBLY_OPENER + " is restated here.", 1)
    ok, info = assembly_check(mutated)
    assert not ok and info["paragraphs"] == 2


def test_commented_out_paragraph_fails(tex):
    """A LaTeX comment removes the paragraph from the compiled PDF. The rule
    strips comments before reading, so commenting it out must not stay green."""
    para = _para(tex)
    mutated = tex.replace(para, "% " + para, 1)
    ok, _ = assembly_check(mutated)
    assert not ok


# --------------------------------------------------------------------------
# Semantic attacks: the number survives, the claim reverses.
# --------------------------------------------------------------------------
def test_posture_softened_to_a_centre_claim_fails(tex):
    """`+5.6 is the center of the interval` is the reading the round rejected;
    it keeps every ladder rung and reverses the conclusion drawn from them."""
    mutated = _mutate_para(
        tex, "no interior member is privileged, and the range rather than any point is what the design delivers",
        "the center of the interval is the best single reading, and the point rather than the range is what the design delivers")
    assert mutated != tex
    ok, _ = assembly_check(mutated)
    assert not ok


def test_censoring_disclaimer_removed_fails(tex):
    """Without the truncation framing the 68.8% reads as `the estimate rests on
    a third of the data`, which HANDOFF_round22 §8.2 records is false on two
    independent counts."""
    for key in ("censor_truncated", "censor_unweighted"):
        mutated = _mutate_para(tex, ASSEMBLY_SPANS[key], "")
        ok, _ = assembly_check(mutated)
        assert not ok, f"{key} is not actually pinned"


def test_one_sided_assembly_fails(tex):
    """Strip all three counterweights at once: the paragraph becomes a clean
    case for a smaller headline, which the evidence does not support."""
    mutated = tex
    for key in ("counter_additive", "counter_fonseca", "counter_three_readings"):
        mutated = _mutate_para(mutated, ASSEMBLY_SPANS[key], "")
    ok, info = assembly_check(mutated)
    assert not ok and len(info["missing"]) == 3


# --------------------------------------------------------------------------
# Benign rewrites must stay green, or the gate is a freeze on the prose rather
# than a pin on the claims.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("old,new", [
    ("because this paper states each correction where it arises",
     "because this paper states each correction in the section that produces it"),
    ("What the assembly settles is where in the interval the mass sits",
     "What the assembly settles is where the mass of the interval sits"),
])
def test_benign_rewrites_stay_green(tex, old, new):
    mutated = _mutate_para(tex, old, new)
    assert mutated != tex, f"benign fixture {old!r} is stale"
    ok, info = assembly_check(mutated)
    assert ok, f"benign rewrite tripped gate #98: {info}"


# --------------------------------------------------------------------------
# Coverage: every commitment HANDOFF_round24 §1 and §4 named must be reachable
# through some span, or the gate quietly stopped protecting one of them.
# --------------------------------------------------------------------------
HANDOFF_COMMITMENTS = [
    "$+9.2$",          # in-sample calibration
    "$+5.6$",          # off-window headline
    "$+4.4$",          # Ginnie overlay
    "$+3.8$",          # age-standardised floor, as the GRID read
    "$+3.7$",          # ...and the value b5_joint_cell actually measured there
    "$+2.9$",          # the composed lower member, measured by b5_joint_cell
                       # (round 27; supersedes the naive $+3.0$ projection,
                       # which survives in prose as the projection history)
    "5.52\\%",         # the independent Fannie read, above the clean band
    "68.8\\%",         # the censoring share (§4)
    "truncated",       # and the framing it must carry
    "$+11.2$",         # the counterweight that is not a floor correction
]


@pytest.mark.parametrize("phrase", HANDOFF_COMMITMENTS)
def test_every_named_commitment_is_covered_by_a_span(phrase, tex):
    covered = any(phrase in span for span in ASSEMBLY_SPANS.values())
    assert covered, f"no span pins {phrase!r}; it can be deleted while gate #98 stays green"
    # and the span it is covered by must actually be in the paragraph
    assert phrase in _para(tex)
