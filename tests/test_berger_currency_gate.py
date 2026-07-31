"""Battery for gate #128 (berger2026 GE magnitude currency).

The manuscript quoted the January 2026 draft's 1 bp equilibrium-rate effect
long after the March 2026 draft replaced it with 18 bps and moved the section
from 4.9.1 to 4.10.2. Evidence, with both drafts quoted:
specs/RECORD_R33_berger_currency_2026-07-31.md.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import berger_currency_check  # noqa: E402

TEX = (ROOT / "paper" / "v18" / "revised_paper_v18.tex").read_text()
VARIANT = (ROOT / "paper" / "v18"
           / "revised_paper_v18_long_abstract.tex").read_text()
BIB = (ROOT / "paper" / "v18" / "references.bib").read_text()


def test_gate_passes_on_both_editions():
    for tex, label in ((TEX, "main"), (VARIANT, "variant")):
        ok, info = berger_currency_check(tex)
        assert ok, f"gate #128 fails on {label}: {info}"


@pytest.mark.parametrize("stale", [
    "by only about one basis point, economically negligible",
    "an equilibrium-rate effect of about one basis point",
    "\\citep[\\S4.9.1]{berger2026}",
])
def test_stale_forms_are_gone(stale):
    assert stale not in TEX
    assert stale not in VARIANT


def test_restoring_the_stale_value_fails():
    restored = TEX.replace(
        "an equilibrium-rate effect of about 18 basis points",
        "an equilibrium-rate effect of about one basis point")
    ok, info = berger_currency_check(restored)
    assert not ok
    assert info["present_retired"]


def test_restoring_the_stale_section_pin_fails():
    restored = TEX.replace("\\citep[\\S4.10.2]{berger2026}",
                           "\\citep[\\S4.9.1]{berger2026}")
    ok, _ = berger_currency_check(restored)
    assert not ok


def test_provenance_sentence_required():
    """A silent renumber would hide that the estimate moved; say it in print."""
    for span in ("the January 2026 draft's",
                 "moved by more than an order of magnitude between the two"):
        assert span in TEX
        ok, _ = berger_currency_check(TEX.replace(span, ""))
        assert not ok, span


def test_bib_records_both_drafts():
    assert "1 bp in \\S4.9.1" in BIB
    assert "18 bps in \\S4.10.2" in BIB
    assert "March 2026 draft" in BIB


def test_r32_recorded_value_is_flagged_as_wrong():
    """R32's fact-check said 20 bps and gated it; the record must warn, since
    that branch will land with a wrong number behind a green gate."""
    rec = (ROOT / "specs"
           / "RECORD_R33_berger_currency_2026-07-31.md").read_text()
    assert "20 bps is wrong" in rec or "value of 20 bps is wrong" in rec
    assert "18 bps" in rec
