"""Perturbation battery for liveness gate #101 (the response letter tracks the paper).

`response_to_referees_round22.tex` was drafted on 26 July 2026 and not sent. By
the next day it quoted a form-conditional hull the manuscript had already widened
(+3.9 against +3.5) and an abstract word count off by 96. Nothing noticed, because
every other gate in the suite reads the manuscript and no gate read the letter.

That is the highest-stakes rot in this repository. A wrong number in the
manuscript is caught by a hundred checks; a wrong number in the letter goes to a
referee.

The letter is PARTLY HISTORICAL, so "every literal must match the manuscript"
would be the wrong rule -- Sections 1-6 legitimately describe the state at the
time the report was answered. The rule is three narrow ones instead, and this
file checks that each of them bites:

  (a) the retired hull literal may appear only inside the sentence that marks it
      historical -- the exact defect that was found;
  (b) the letter's claim about the abstract's length must equal the measured
      length;
  (c) every present-tense figure in the "Changes since" section must still exist
      in the manuscript.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import liveness_gates as G  # noqa: E402
from liveness_gates import (  # noqa: E402
    LETTER,
    LETTER_CURRENT_LITERALS,
    LETTER_CURRENT_SECTION,
    LETTER_RETIRED_HULL,
    TEX,
    letter_check,
)


@pytest.fixture(scope="module")
def tex() -> str:
    return TEX.read_text()


@pytest.fixture
def letter_file(tmp_path, monkeypatch):
    """Point the gate at a scratch copy so mutations never touch the real letter.

    ROUND-24c: the earlier batteries mutated in-memory strings, which works when
    the rule takes the text as an argument. This rule reads the letter off disk,
    so the copy has to be real -- and it has to be a copy, because a mutation
    left behind in a shipped file is exactly the accident HANDOFF_round22 §4.3
    records.
    """
    scratch = tmp_path / "letter.tex"
    scratch.write_text(LETTER.read_text())
    monkeypatch.setattr(G, "LETTER", scratch)
    return scratch


def test_shipped_letter_passes(tex):
    ok, info = letter_check(tex)
    assert ok, f"gate #101 fails the shipped letter: {info}"


def test_missing_letter_fails(tex, tmp_path, monkeypatch):
    monkeypatch.setattr(G, "LETTER", tmp_path / "does_not_exist.tex")
    ok, info = letter_check(tex)
    assert not ok and info == {"exists": False}


# --- (a) the defect that was actually found -------------------------------
def test_retired_hull_in_a_present_tense_sentence_fails(tex, letter_file):
    """Quoting the superseded hull anywhere but the historical sentence is the
    original defect: the letter told the referee +3.9 while the paper said +3.5."""
    letter_file.write_text(
        letter_file.read_text().replace(
            "The\nform-conditional range is therefore $+3.5$ to $+13.1$ points",
            "The\nform-conditional range is therefore " + LETTER_RETIRED_HULL + " points", 1))
    ok, info = letter_check(tex)
    assert not ok and not info["hull_ok"]


def test_historical_marker_removed_fails(tex, letter_file):
    """If the sentence stops marking the number historical, the number is just
    wrong again -- the marker is what makes the occurrence legitimate."""
    letter_file.write_text(
        letter_file.read_text().replace("That range has since widened", "That range holds", 1))
    ok, info = letter_check(tex)
    assert not ok and not info["hull_ok"]


# --- (b) the count that silently rotted -----------------------------------
@pytest.mark.parametrize("wrong", ["263", "328", "352", "359", "366", "367", "280", "424", "226", "235", "248", "287", "294", "323", "341"])
def test_wrong_abstract_word_count_fails(tex, letter_file, wrong):
    # V20 re-review round: abstract 229 -> 244 words (two hedge additions); the
    # mutation anchor tracks the letter's live claim.
    """Every one of these was the true count at some point, which is
    precisely why a stated count has to be recomputed rather than trusted."""
    letter_file.write_text(
        letter_file.read_text().replace("taken it to 262 words", f"taken it to {wrong} words", 1))
    ok, info = letter_check(tex)
    assert not ok, f"gate #101 accepted a {wrong}-word claim"
    assert info["claimed_words"] == [wrong] and info["actual_words"] != int(wrong)


def test_word_count_claim_deleted_fails(tex, letter_file):
    letter_file.write_text(
        letter_file.read_text().replace("taken it to 262 words", "lengthened it", 1))
    ok, info = letter_check(tex)
    assert not ok and info["claimed_words"] == []


# --- (c) present-tense figures must track ---------------------------------
@pytest.mark.parametrize("lit", LETTER_CURRENT_LITERALS)
def test_deleting_a_current_figure_fails(tex, letter_file, lit):
    body = letter_file.read_text()
    i = body.find(LETTER_CURRENT_SECTION)
    assert i != -1
    letter_file.write_text(body[:i] + body[i:].replace(lit, "", 1))
    ok, info = letter_check(tex)
    assert not ok, f"gate #101 did not notice {lit!r} leaving the current section"
    assert lit in info["absent"]


def test_a_figure_that_drifts_from_the_manuscript_fails(tex, letter_file):
    """The letter keeps a number the manuscript no longer carries. This is the
    general form of the defect, and the reason the check is against the tex
    rather than against a frozen list."""
    body = letter_file.read_text()
    i = body.find(LETTER_CURRENT_SECTION)
    letter_file.write_text(body[:i] + body[i:].replace("68.8\\%", "71.4\\%", 1))
    ok, info = letter_check(tex)
    assert not ok
    # it registers as absent-from-current or drifted-from-tex; either is a fail
    assert info["absent"] or info["drifted"]


def test_missing_current_section_fails(tex, letter_file):
    letter_file.write_text(
        letter_file.read_text().replace(LETTER_CURRENT_SECTION, "\\section{Postscript}", 1))
    ok, info = letter_check(tex)
    assert not ok and not info["has_current_section"]


# --- benign ---------------------------------------------------------------
def test_benign_rewrite_stays_green(tex, letter_file):
    letter_file.write_text(
        letter_file.read_text().replace(
            "Thank you again. The report cost me more runs than any previous one",
            "Thank you again. This report cost me more runs than any before it", 1))
    ok, info = letter_check(tex)
    assert ok, f"gate #101 false-alarmed on a benign rewrite: {info}"


def test_the_real_letter_was_not_mutated():
    """Paranoia with a reason: HANDOFF_round22 §4.3 records a mutation left in a
    shipped file riding into the canonical manuscript."""
    assert LETTER_RETIRED_HULL in LETTER.read_text(), "letter unexpectedly modified"
    ok, _ = letter_check(TEX.read_text())
    assert ok, "the shipped letter no longer passes -- a mutation escaped a fixture"
