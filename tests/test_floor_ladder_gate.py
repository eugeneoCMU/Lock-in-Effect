"""Battery for gate #107 (round-30 E7/CR1: the CR1 rungs and the designer units).

Same convention as the #105/#106 batteries: mutations remove ALL occurrences of
a span, and every mutation is verified non-vacuous before it is applied. The
artifact block is the first in the suite to open
floor_inference_correction_v2_results.json, so it also pins the derivations the
two new rows and the floor-units clause are printed from.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import (  # noqa: E402
    FLOOR_LADDER_READ,
    FLOOR_LADDER_SPANS,
    floor_ladder_check,
)

TEX = (ROOT / "paper" / "v18" / "revised_paper_v18.tex").read_text()
VARIANT = (ROOT / "paper" / "v18"
           / "revised_paper_v18_long_abstract.tex").read_text()
ART = json.loads((ROOT / "hazard" / "data"
                  / "floor_inference_correction_v2_results.json").read_text())
RD = ART["reads"][FLOOR_LADDER_READ]


def test_gate_passes_on_the_manuscript():
    ok, info = floor_ladder_check(TEX)
    assert ok, f"gate #107 fails on the shipped manuscript: {info}"


@pytest.mark.parametrize("key", sorted(FLOOR_LADDER_SPANS))
def test_each_span_removal_fails(key):
    span = FLOOR_LADDER_SPANS[key]
    assert span in TEX, f"span {key!r} not in the manuscript (vacuous mutation)"
    ok, _ = floor_ladder_check(TEX.replace(span, ""))
    assert not ok, f"gate #107 survives removal of span {key!r}"


def test_variant_carries_the_spans_too():
    ok, info = floor_ladder_check(VARIANT)
    assert ok, f"gate #107 fails on the long-abstract variant: {info}"


def test_the_ladder_order_is_gated():
    row = FLOOR_LADDER_SPANS["cr1_conventional"] + " \\\\\n"
    assert TEX.count(row) == 1
    moved = TEX.replace(row, "", 1).replace(
        "CR3 $t$ & $+2.8$ to $+8.8$", row + "CR3 $t$ & $+2.8$ to $+8.8$", 1)
    ok, info = floor_ladder_check(moved)
    assert not ok and info["ordered"] is False


@pytest.mark.parametrize("printed,perturbed", [
    ("$+3.2$ to $+8.3$", "$+3.3$ to $+8.3$"),
    ("$+2.8$ to $+8.8$ & $t(6.2)$", "$+2.8$ to $+8.9$ & $t(6.2)$"),
    ("$t(6.2)$", "$t(6.3)$"),
    ("4.033\\% to 6.181\\%", "4.033\\% to 6.182\\%"),  # V20-N1: binding rung floor image
])
def test_a_wrong_digit_fails(printed, perturbed):
    assert TEX.count(printed) == 1, f"{printed!r} is not the single site"
    ok, _ = floor_ladder_check(TEX.replace(printed, perturbed))
    assert not ok, f"gate #107 survives {printed!r} -> {perturbed!r}"


def test_the_printed_cr1_rungs_are_the_artifact_rounded():
    c1 = RD["cr1_t_interval"]["marginal_ci95_pp"]
    c1b = RD["cr1_t_interval_df_bm"]["marginal_ci95_pp"]
    assert f"${c1[0]:+.1f}$ to ${c1[1]:+.1f}$" == "$+3.2$ to $+8.3$"
    assert f"${c1b[0]:+.1f}$ to ${c1b[1]:+.1f}$" == "$+2.8$ to $+8.8$"
    assert f"$t({RD['cr1_t_interval_df_bm']['df_used']:.1f})$" == "$t(6.2)$"
    assert RD["cr1_t_interval"]["t_crit"] == RD["t_crit_G_minus_1"]
    assert (RD["cr1_t_interval_df_bm"]["t_crit"]
            == RD["t_crit_df_bm_by_estimator"]["cr1"])


def test_the_conventional_rung_is_the_committed_run_bit_for_bit():
    """The caption credits CR1--CR3 at t(30) to floor_inference_correction."""
    v1 = json.loads((ROOT / "hazard" / "data"
                     / "floor_inference_correction_results.json").read_text())
    assert (v1["reads"][FLOOR_LADDER_READ]["cr1_t_interval"]["marginal_ci95_pp"]
            == RD["cr1_t_interval"]["marginal_ci95_pp"])


def test_the_printed_tie_with_cr3_is_not_an_identity():
    c1b = RD["cr1_t_interval_df_bm"]["marginal_ci95_pp"]
    cr3 = RD["cr3_t_interval"]["marginal_ci95_pp"]
    assert c1b != cr3, "the tablenote calls the tie an accident, not an identity"
    assert all(abs(a - b) < 0.05 for a, b in zip(c1b, cr3)), \
        "the rows no longer agree to the printed digit; the note is stale"


def test_cr1_is_the_narrowest_sandwich_and_carries_the_largest_bm_df():
    assert RD["se_cr1_smm"] < RD["se_cr2_smm"] < RD["se_cr3_smm"]
    d = RD["df_bm_by_estimator"]
    assert d["cr1"] > d["cr2"] > d["cr3"]


def test_the_designer_units_clause_is_the_webb_interval_in_floor_units():
    w = RD["wild_t_webb"]
    lo, hi = w["floor_ci95_pct"]
    assert f"{lo:.3f}\\% to {hi:.3f}\\%" == "4.177\\% to 5.800\\%"
    # V20-N1: the designer clause now QUOTES the binding rung (restricted
    # inversion); the Webb read above remains the cap grid's input.
    wc = RD["wcr_inverted"]
    wlo, whi = wc["floor_ci95_pct"]
    assert f"{wlo:.3f}\\% to {whi:.3f}\\%" == "4.033\\% to 6.181\\%"
    # the map is inverse: the LOW floor carries the HIGH marginal
    assert w["upper_pp_edge"]["floor_pct"] < w["lower_pp_edge"]["floor_pct"]
    assert abs(w["marginal_ci95_pp"][0] - 2.8549950653913494) < 1e-9
    assert abs(w["marginal_ci95_pp"][1] - 8.677971792194077) < 1e-9
    assert not w["lower_pp_edge"]["truncated_at_grid_edge"]
    assert not w["upper_pp_edge"]["truncated_at_grid_edge"]
