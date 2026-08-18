"""Battery for gate #104 (round-26 verdict-adjudication audit, app:verdicts).

Mutations remove ALL occurrences (presence-gate power); every mutation is
verified non-vacuous first.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import (  # noqa: E402
    VERDICT_AUDIT_SPANS,
    verdict_audit_check,
)

# V20 closing-session rescope: app:ledger/app:verdicts live in the standalone
# replication_appendices.tex; the gated corpus is manuscript + that file.
TEX = ((ROOT / "paper" / "v18" / "revised_paper_v18.tex").read_text()
       + "\n" + (ROOT / "paper" / "v18" / "replication_appendices.tex").read_text())


def test_gate_passes_on_the_manuscript():
    ok, info = verdict_audit_check(TEX)
    assert ok, f"gate #104 fails on the shipped manuscript: {info}"


@pytest.mark.parametrize("key", sorted(VERDICT_AUDIT_SPANS))
def test_each_span_removal_fails(key):
    span = VERDICT_AUDIT_SPANS[key]
    assert span in TEX, f"vacuous mutation: span {key!r} not in manuscript"
    mutated = TEX.replace(span, "")
    ok, info = verdict_audit_check(mutated)
    assert not ok and key in info["missing"], (
        f"gate #104 survived removal of {key!r}")


def test_one_sided_table_fails():
    """The table's point is both directions. Stripping the for-headline row
    while keeping every against-headline row must trip the gate."""
    span = VERDICT_AUDIT_SPANS["row_for_headline"]
    mutated = TEX.replace(span, "")
    ok, info = verdict_audit_check(mutated)
    assert not ok and "row_for_headline" in info["missing"]


def test_variant_carries_the_spans_too():
    var = (ROOT / "paper" / "v18"
           / "revised_paper_v18_long_abstract.tex").read_text() \
    + "\n" + (ROOT / "paper" / "v18" / "replication_appendices.tex").read_text()  # V20 rescope
    ok, info = verdict_audit_check(var)
    assert ok, f"long-abstract variant missing spans: {info}"
