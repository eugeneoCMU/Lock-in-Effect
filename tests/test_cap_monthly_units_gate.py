"""Battery for gate #111 (R32 C-54: the cap result in $bn/month).

Same convention as the #105-#110 batteries: every mutation is verified
non-vacuous before it is applied.

The ratio and band tests carry the weight. C-54's claim is comparative -- "the
ceiling was near twice a rate the book could not passively reach" -- and a
comparison is what goes stale silently when one side moves. The artifact
perturbations therefore move each side independently and require the gate to
notice each time.
"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import cap_monthly_units_check  # noqa: E402

TEX = (ROOT / "paper" / "v18" / "revised_paper_v18.tex").read_text()
VARIANT = (ROOT / "paper" / "v18"
           / "revised_paper_v18_long_abstract.tex").read_text()
EB = json.loads((ROOT / "hazard" / "data"
                 / "expectation_benchmark_results.json").read_text())
BENCH = EB["cap_benchmark_b"]
LO, HI = 2.9, 8.7

CEILING = "\\$33.75 billion per month"
UNIFORM = "\\$17.6 billion per month"
SETTLED = "\\$20.0 billion per month"
RATIOS = "ratios of 1.91 and 1.69"
BAND = "\\$0.53 to \\$1.58 billion per month"
SCOPE = ("That band attaches to the identified marginal, not to the two "
         "projection levels")


def _ok(tex=None, eb=None, lo=LO, hi=HI):
    return cap_monthly_units_check(tex if tex is not None else TEX,
                                   eb if eb is not None else EB,
                                   (eb or EB)["cap_benchmark_b"], lo, hi)[0]


def test_gate_passes_on_the_manuscript():
    ok, info = cap_monthly_units_check(TEX, EB, BENCH, LO, HI)
    assert ok, f"gate #111 fails on the shipped manuscript: {info}"


def test_variant_carries_the_units():
    ok, info = cap_monthly_units_check(VARIANT, EB, BENCH, LO, HI)
    assert ok, f"gate #111 fails on the long-abstract variant: {info}"


def test_each_literal_is_individually_pinned():
    for lit in (CEILING, UNIFORM, SETTLED, RATIOS, BAND, SCOPE):
        assert lit in TEX, f"{lit!r} missing (vacuous mutation)"
        assert not _ok(tex=TEX.replace(lit, "")), f"{lit!r} is not pinned"


def test_ceiling_drift_fails():
    eb = copy.deepcopy(EB)
    eb["supplementary_projection_wedge"]["cap_target_window_b"] += 42.0
    assert not _ok(eb=eb), "a moved ceiling must fail against the unmoved tex"


def test_uniform_spread_drift_fails():
    eb = copy.deepcopy(EB)
    eb["window"]["projected_runoff_window_b"] += 42.0
    assert not _ok(eb=eb)


def test_settlement_aware_drift_fails():
    eb = copy.deepcopy(EB)
    eb["settlement_aware_allocation"]["projected_runoff_window_b"] += 42.0
    assert not _ok(eb=eb)


def test_benchmark_drift_breaks_the_band():
    """The band is derived from the benchmark, so the benchmark is bound too."""
    eb = copy.deepcopy(EB)
    eb["cap_benchmark_b"] += 100.0
    assert not _ok(eb=eb)


def test_binding_interval_drift_breaks_the_band():
    assert not _ok(lo=3.0), "the band must track the binding interval's low edge"
    assert not _ok(hi=9.0), "the band must track the binding interval's high edge"


def test_scope_disclaimer_is_required():
    """Without it the paragraph reads as though a projection had a CI."""
    assert SCOPE in TEX
    assert not _ok(tex=TEX.replace(SCOPE, "That band attaches to everything here"))


def test_ratios_are_the_arithmetic_ones():
    """A plausible-but-wrong ratio must not survive."""
    assert RATIOS in TEX
    assert not _ok(tex=TEX.replace(RATIOS, "ratios of 2.00 and 1.75"))


def test_derived_values_match_the_artifact():
    """Re-derive independently of the gate, so a self-consistent bug cannot pass."""
    M = 42
    assert round(EB["supplementary_projection_wedge"]["cap_target_window_b"] / M, 2) == 33.75
    assert round(EB["window"]["projected_runoff_window_b"] / M, 1) == 17.6
    assert round(EB["settlement_aware_allocation"]["projected_runoff_window_b"] / M, 1) == 20.0
    assert round(BENCH * LO / 100 / M, 2) == 0.53
    assert round(BENCH * HI / 100 / M, 2) == 1.58
