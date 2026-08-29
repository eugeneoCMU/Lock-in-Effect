"""Battery for gate #112 (R32 C-81: the state-contingent cap's two-input grid).

The exhibit's point is a COMPARISON -- the designer's observable moves the implied
cap by less than the floor's own sampling error -- so the tests move each side of
that comparison independently, as with gate #111.

The rounding test is the unusual one and it exists because the run tripped it: the
true cut-spread is 1.1252, which rounds to 1.13, while the printed cells subtract
to 1.12. The manuscript prints the spread at ONE decimal so a reader who subtracts
the printed cells gets the printed spread. That property is asserted here.
"""
import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import state_contingent_cap_check  # noqa: E402

TEX = (ROOT / "paper" / "final" / "paper_final_v1.tex").read_text()
VARIANT = (ROOT / "paper" / "final"
           / "paper_final_v1_long_abstract.tex").read_text()
G = json.loads((ROOT / "hazard" / "data"
                / "state_contingent_cap_grid_results.json").read_text())


def test_gate_passes_on_the_manuscript():
    ok, info = state_contingent_cap_check(TEX, G)
    assert ok, f"gate #112 fails on the shipped manuscript: {info}"


def test_variant_carries_the_grid():
    ok, info = state_contingent_cap_check(VARIANT, G)
    assert ok, f"gate #112 fails on the long-abstract variant: {info}"


@pytest.mark.parametrize("cell", ["cut_0bp", "cut_25bp", "cut_50bp"])
def test_each_cell_drift_fails(cell):
    g = copy.deepcopy(G)
    g["cells"][cell]["achievable_b_per_month"] += 0.5
    ok, _ = state_contingent_cap_check(TEX, g)
    assert not ok, f"a drifted {cell} must fail against the unmoved tex"


@pytest.mark.parametrize("end", ["floor_4.177pct", "floor_5.8pct"])
def test_band_drift_fails(end):
    g = copy.deepcopy(G)
    g["band"][end]["achievable_b_per_month"] += 0.5
    ok, _ = state_contingent_cap_check(TEX, g)
    assert not ok


@pytest.mark.parametrize("key", ["E3_spread_across_cuts_b_per_month",
                                 "E3_spread_across_band_b_per_month"])
def test_spread_drift_fails(key):
    """Both sides of the comparison are bound, not just the levels."""
    g = copy.deepcopy(G)
    g["expectations"][key] += 0.4
    ok, _ = state_contingent_cap_check(TEX, g)
    assert not ok


def test_printed_cells_subtract_to_the_printed_spread():
    """No arithmetic trap: printed cells at 2dp must give the printed 1dp spread."""
    c = G["cells"]
    hi = round(c["cut_0bp"]["achievable_b_per_month"], 2)
    lo = round(c["cut_50bp"]["achievable_b_per_month"], 2)
    printed_spread = round(G["expectations"]["E3_spread_across_cuts_b_per_month"], 1)
    assert round(hi - lo, 1) == printed_spread, (
        f"printed cells subtract to {round(hi - lo, 1)} but the text prints "
        f"{printed_spread}")
    b = G["band"]
    bhi = round(b["floor_5.8pct"]["achievable_b_per_month"], 2)
    blo = round(b["floor_4.177pct"]["achievable_b_per_month"], 2)
    assert round(bhi - blo, 1) == round(
        G["expectations"]["E3_spread_across_band_b_per_month"], 1)


def test_the_finding_itself_holds():
    """E3: the observable buys less than the floor's own sampling error."""
    e = G["expectations"]
    assert e["E3_spread_across_cuts_b_per_month"] < e["E3_spread_across_band_b_per_month"]
    assert e["E3_pass"] is True


def test_observable_is_near_degenerate_and_declared():
    o = G["observable_declared_not_predicted"]
    assert o["near_degenerate"] is True
    shares = [v for v in o["otm_share_pct"].values()]
    assert min(shares) > 99.5, "the observable is supposed to be pinned near 100%"
    assert o["otm_share_pct"]["25"] == o["otm_share_pct"]["50"], (
        "the 25 and 50 bp cuts coincide on the 0.5% coupon grid")


def test_parity_and_monotonicity_flags_are_load_bearing():
    for key, holder in (("nine_rows_bit_identical_via_schedule", "parity"),
                        ("coupon_shares_sum_to_one", "parity"),
                        ("E1_monotone_in_floor", "expectations")):
        g = copy.deepcopy(G)
        g[holder][key] = False
        ok, _ = state_contingent_cap_check(TEX, g)
        assert not ok, f"{key} must be load-bearing"


def test_no_new_estimation_and_committed_cuts():
    s = G["spec"]
    assert s["no_new_estimation"] is True
    assert s["depth_cuts_bp"] == [0, 25, 50], (
        "the committed floor reads exist only at these cuts; 200/300/400 would "
        "require new estimation")


def test_scope_limit_is_stated():
    assert "two populations at two grains" in TEX
    assert "two populations" in G["scope_limit"].lower()
