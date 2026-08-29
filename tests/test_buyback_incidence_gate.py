"""Battery for gate #103 (round-26 buyback incidence bracket).

Same convention as the gate #102 battery: mutations remove ALL occurrences
of a span (a presence gate's actual power), and every mutation is verified
non-vacuous before it is applied.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import (  # noqa: E402
    BUYBACK_BRACKET_SPANS,
    buyback_bracket_check,
)

TEX = (ROOT / "paper" / "final" / "paper_final_v1.tex").read_text()


def test_gate_passes_on_the_manuscript():
    ok, info = buyback_bracket_check(TEX)
    assert ok, f"gate #103 fails on the shipped manuscript: {info}"


@pytest.mark.parametrize("key", sorted(BUYBACK_BRACKET_SPANS))
def test_each_span_removal_fails(key):
    span = BUYBACK_BRACKET_SPANS[key]
    assert span in TEX, f"vacuous mutation: span {key!r} not in manuscript"
    mutated = TEX.replace(span, "")
    ok, info = buyback_bracket_check(mutated)
    assert not ok and key in info["missing"], (
        f"gate #103 survived removal of {key!r}")


def test_reverting_to_the_signed_claim_fails():
    """The exact reversion this gate exists for: restore the conclusion's
    signed 'modestly improved (3)' reading in place of the bracket."""
    old = "while its effect on (3) is incidence-conditional"
    assert old in TEX
    mutated = TEX.replace(old, "and modestly \\emph{improved} (3)")
    ok, info = buyback_bracket_check(mutated)
    assert not ok and "trilemma_conditional" in info["missing"]


def test_variant_carries_the_spans_too():
    var = (ROOT / "paper" / "final"
           / "paper_final_v1_long_abstract.tex").read_text()
    ok, info = buyback_bracket_check(var)
    assert ok, f"long-abstract variant missing spans: {info}"
