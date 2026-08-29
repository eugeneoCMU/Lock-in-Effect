"""Battery for gate #102 (round-26 elasticity-discipline exhibits).

Same convention as the other gate batteries: every mutation is verified
non-vacuous (the span must actually occur in the manuscript before it is
removed), so a renamed span cannot silently turn a test into a no-op.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import (  # noqa: E402
    ELASTICITY_DISCIPLINE_SPANS,
    elasticity_discipline_check,
)

TEX = (ROOT / "paper" / "final" / "paper_final_v1.tex").read_text()


def test_gate_passes_on_the_manuscript():
    ok, info = elasticity_discipline_check(TEX)
    assert ok, f"gate #102 fails on the shipped manuscript: {info}"


@pytest.mark.parametrize("key", sorted(ELASTICITY_DISCIPLINE_SPANS))
def test_each_span_removal_fails(key):
    # ALL occurrences are removed, because gate #102 is a presence gate and
    # that is the power it actually has. KNOWN LIMIT, found by this battery's
    # first run: curve_run_tag occurs twice (paragraph + table caption), so
    # deleting one site alone is not detected -- the same repeated-span limit
    # HANDOFF_round25 records for the duplicated paradigm hedge. Per-site
    # protection would be a count gate, deliberately not added: the caption
    # and paragraph travel together inside one table environment block.
    span = ELASTICITY_DISCIPLINE_SPANS[key]
    assert span in TEX, f"vacuous mutation: span {key!r} not in manuscript"
    mutated = TEX.replace(span, "")
    ok, info = elasticity_discipline_check(mutated)
    assert not ok and key in info["missing"], (
        f"gate #102 survived removal of {key!r}")


def test_variant_carries_the_spans_too():
    var = (ROOT / "paper" / "final"
           / "paper_final_v1_long_abstract.tex").read_text()
    ok, info = elasticity_discipline_check(var)
    assert ok, f"long-abstract variant missing spans: {info}"
