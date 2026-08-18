"""Tests for the round-31 render gate (tools/render_gate.py).

The gate exists because ~919 text items across 9 pages once rendered OUTSIDE the
physical sheet while all 108 source gates passed: the literals were present and
correctly derived in the .tex, they just never reached the page.

These tests are deliberately split so the suite can never go vacuous:

  * the detector tests exercise the load-bearing math on synthetic matrices and
    therefore run even when no PDF has been built;
  * the integration test runs against the built PDFs when they exist.

The failure this gate is named for -- an early probe that read the text matrix
alone and reported every page as broken -- is pinned as its own test, because
tm[5] is NOT a device coordinate.
"""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "render_gate", ROOT / "tools" / "render_gate.py")
rg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rg)

LETTER = (0.0, 0.0, 612.0, 792.0)
IDENT = [1, 0, 0, 1, 0, 0]


def tm_at(x, y):
    """A text matrix placing the text object's origin at (x, y)."""
    return [1, 0, 0, 1, x, y]


# --- the detector's math -------------------------------------------------
def test_device_xy_is_the_composition_not_the_text_matrix():
    """The bug this gate was born from: tm alone is not a page position.

    Under a translating CTM the same text matrix lands somewhere else; a
    detector reading tm[5] would have called an on-page glyph off-page.
    """
    cm = [1, 0, 0, 1, 0, 740]          # content translated near the page top
    tm = tm_at(72, -700)               # text object walking back down
    dx, dy = rg.device_xy(cm, tm)
    assert (dx, dy) == (72.0, 40.0)
    assert not rg.is_offpage(dx, dy, LETTER)
    # the naive reading (tm[5] = -700) would have flagged this on-page glyph
    assert rg.is_offpage(dx, tm[5], LETTER)


def test_scaled_ctm_is_honoured():
    dx, dy = rg.device_xy([0.5, 0, 0, 0.5, 10, 20], tm_at(100, 200))
    assert (dx, dy) == (60.0, 120.0)


@pytest.mark.parametrize("x,y,expected", [
    (306, 400, False),   # mid-page
    (72, 72, False),     # bottom-left text corner
    (540, 720, False),   # top-right text corner
    (306, -1.0, False),  # within the descender tolerance
    (306, -50, True),    # below the sheet: the round-31 defect
    (306, -1026, True),  # the worst measured item (Appendix O ledger)
    (306, 800, True),    # above the sheet
    (620, 400, True),    # past the right edge (the tab:assembly defect)
    (-5, 400, True),     # past the left edge
])
def test_offpage_predicate(x, y, expected):
    assert rg.is_offpage(x, y, LETTER) is expected


def test_tolerance_cannot_hide_a_clipped_line():
    """A whole clipped line is >= one 12pt line height below the box; the
    2pt tolerance must never absorb one."""
    assert rg.EPS < 12.0
    assert rg.is_offpage(306, -12.0, LETTER)


# --- integration against the real build ----------------------------------
def _built():
    return [p for p in rg.DEFAULTS if p.exists()]


@pytest.mark.skipif(not _built(), reason="no built PDF present")
@pytest.mark.parametrize("pdf", _built(), ids=lambda p: p.name)
def test_built_pdf_has_no_offpage_content(pdf):
    result = rg.scan(pdf)
    assert result["offpage"] == [], (
        f"{pdf.name}: {len(result['offpage'])} text items render off the sheet; "
        f"first few: {result['offpage'][:3]}")
    assert result["unresolved"] == 0, f"{pdf.name}: unresolved cross-references"
    assert result["pages"] > 1
