"""Battery for gate #106 (round-28 G2 coupon-convention companion)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import (  # noqa: E402
    COUPON_CONVENTION_SPANS,
    coupon_convention_check,
)

TEX = (ROOT / "paper" / "v18" / "revised_paper_v18.tex").read_text()
VARIANT = (ROOT / "paper" / "v18"
           / "revised_paper_v18_long_abstract.tex").read_text()


def test_gate_passes_on_the_manuscript():
    ok, info = coupon_convention_check(TEX)
    assert ok, f"gate #106 fails on the shipped manuscript: {info}"


@pytest.mark.parametrize("key", sorted(COUPON_CONVENTION_SPANS))
def test_each_span_removal_fails(key):
    span = COUPON_CONVENTION_SPANS[key]
    assert span in TEX, f"span {key!r} not in the manuscript (vacuous mutation)"
    mutated = TEX.replace(span, "")
    ok, _ = coupon_convention_check(mutated)
    assert not ok, f"gate #106 survives removal of span {key!r}"


def test_variant_carries_the_spans_too():
    ok, info = coupon_convention_check(VARIANT)
    assert ok, f"gate #106 fails on the long-abstract variant: {info}"
