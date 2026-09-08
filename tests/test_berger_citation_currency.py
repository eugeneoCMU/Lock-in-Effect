"""Regression battery for the berger2026 citation (R32 fact-check, 2026-07-30).

This is a TEST and not a liveness gate on purpose: the claim is about an external
working paper, so there is no committed artifact to tie it to. What can be pinned
is that the manuscript does not silently drift back to the superseded draft.

Background (specs/RECORD_R32_citation_factcheck_2026-07-30.md): the paper was
citing the January 2026 SSRN draft. In the July 16 2026 version the pinned
section SS4.9.1 NO LONGER EXISTS (numbering moved to SS4.10.x) and the
general-equilibrium result moved from 1 bps to 20 bps -- a 20x change in a
magnitude the manuscript called "economically negligible".
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TEX = (ROOT / "paper" / "final" / "paper_final_v1.tex").read_text()
VARIANT = (ROOT / "paper" / "final"
           / "paper_final_v1_long_abstract.tex").read_text()
BIB = (ROOT / "paper" / "final" / "references.bib").read_text()

BOTH = pytest.mark.parametrize("tex", [TEX, VARIANT], ids=["canonical", "variant"])


@BOTH
def test_no_superseded_section_pins(tex):
    """SS4.9.1 does not exist in the current draft; SS3.2.3 is the wrong section."""
    assert "\\S4.9.1" not in tex, "SS4.9.1 was removed in the July 2026 version"
    assert "\\S3.2.3" not in tex, (
        "SS3.2.3 is 'Aggregate prepayment...' in BOTH drafts and explicitly defers "
        "the behavioural estimate to later sections; the estimate is SS3.3.2")


@BOTH
def test_current_section_pins_present(tex):
    assert "\\citep[\\S4.10.2]{berger2026}" in tex
    assert "\\citep[\\S3.3.2]{berger2026}" in tex
    assert "\\citet[\\S3.3.2]{berger2026}" in tex
    # SS4.6 + table 3 survived the revision and is still correct
    assert "\\citep[\\S4.6, structural parameters in tab.~3]{berger2026}" in tex


@BOTH
def test_ge_magnitude_is_the_current_one(tex):
    assert "about 20 basis points on average" in tex
    assert "16--23 across their robustness variants" in tex
    assert "an equilibrium-rate effect of about 20 basis points" in tex


def test_the_superseded_one_bp_figure_survives_nowhere_as_a_current_claim():
    """Presence checks alone let a stale sibling survive -- and one did.

    Commit 5c9c955 corrected the GE magnitude 1bp -> 20bps "at BOTH sites" and this file
    pinned the two corrected strings. It missed a THIRD site: .tex:661 still read
    "Berger et al.'s roughly one-basis-point equilibrium shift", asserting the superseded
    January-2026 figure as current, two paragraphs after .tex:626 correctly labels one
    basis point as the superseded value. Asserting the new string is present cannot detect
    that; asserting the old one is absent can.

    The hyphenated form is the discriminator. .tex:626's legitimate historical mention
    reads "reported about one basis point" (spaced); only a current-claim usage is
    hyphenated as a compound modifier. So this pins the hyphenated form at zero without
    touching the honest historical reference.
    """
    for name, tex in (("canonical", TEX), ("variant", VARIANT)):
        assert "one-basis-point" not in tex, (
            f"{name}: the superseded 1bp figure is stated as a current claim; "
            f"berger2026's July draft gives ~20 basis points")
        assert "the January 2026 version of the same paper reported about one basis point" in tex, (
            f"{name}: the labelled historical mention of the 1bp figure was removed; it is "
            f"the evidence that the estimate is draft-sensitive and should stay")


@BOTH
def test_only_surviving_one_bp_mention_is_the_declared_draft_history(tex):
    """The 1 bps figure may appear exactly once, and only as version history."""
    hits = [m.start() for m in re.finditer("one basis point", tex)]
    assert len(hits) == 1, f"expected 1 historical mention, found {len(hits)}"
    window = tex[hits[0] - 260: hits[0] + 80]
    assert "January 2026" in window and "draft-sensitive" in window, (
        "the surviving 'one basis point' must be the declared version-history "
        "note, not a live claim")


@BOTH
def test_version_is_stated_as_july(tex):
    assert tex.count("July 2026 SSRN working draft") == 2
    assert "January 2026 SSRN working draft" not in tex


def test_bib_points_at_the_current_draft():
    assert "draft July 2026" in BIB
    assert "draft January 2026" not in BIB
    assert "abstract=6150766" in BIB


@BOTH
def test_flatness_is_quantified_not_merely_asserted(tex):
    """The July draft supplies numbers for the slope this paper imports."""
    assert "$+14$ basis points" in tex
    assert "$-19$" in tex
    assert "not consistently signed" in tex
