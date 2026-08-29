"""Battery for gate #105 (round-28 C2 convolved sampling line).

Same convention as the #102/#103 batteries: mutations remove ALL occurrences
of a span, and every mutation is verified non-vacuous before it is applied.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import (  # noqa: E402
    CONVOLVED_LINE_SPANS,
    convolved_line_check,
)

TEX = (ROOT / "paper" / "final" / "paper_final_v1.tex").read_text()
VARIANT = (ROOT / "paper" / "final"
           / "paper_final_v1_long_abstract.tex").read_text()


def test_gate_passes_on_the_manuscript():
    ok, info = convolved_line_check(TEX)
    assert ok, f"gate #105 fails on the shipped manuscript: {info}"


@pytest.mark.parametrize("key", sorted(CONVOLVED_LINE_SPANS))
def test_each_span_removal_fails(key):
    span = CONVOLVED_LINE_SPANS[key]
    assert span in TEX, f"span {key!r} not in the manuscript (vacuous mutation)"
    mutated = TEX.replace(span, "")
    ok, _ = convolved_line_check(mutated)
    assert not ok, f"gate #105 survives removal of span {key!r}"


def test_variant_carries_the_spans_too():
    ok, info = convolved_line_check(VARIANT)
    assert ok, f"gate #105 fails on the long-abstract variant: {info}"
