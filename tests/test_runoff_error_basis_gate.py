"""Battery for gate #109 (R33-A: runoff-error column on both bases)."""
import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import runoff_error_basis_check  # noqa: E402

TEX = (ROOT / "paper" / "v18" / "revised_paper_v18.tex").read_text()
VARIANT = (ROOT / "paper" / "v18"
           / "revised_paper_v18_long_abstract.tex").read_text()
SHARED = json.loads((ROOT / "hazard" / "data"
                     / "shared_layer_scoring_results.json").read_text())
CALIB = json.loads((ROOT / "hazard" / "data"
                    / "calibration_reconciliation_results.json").read_text())
CONCAVE = json.loads((ROOT / "hazard" / "data"
                      / "concave_marginal_results.json").read_text())
EXPECT = json.loads((ROOT / "hazard" / "data"
                     / "expectation_benchmark_results.json").read_text())

RETIRED_SMALLEST = (
    "carries the smallest error of any leg here on the standalone "
    "scorer: $+\\$2.8$ billion, 0.4\\% of realized runoff"
)
RETIRED_PATHA = (
    "overshoots the benchmark by \\$164.1 billion---its terminal "
    "cumulative runoff error, and a 25.1\\% under-prediction"
)


def test_gate_passes_on_the_manuscript():
    ok, info = runoff_error_basis_check(TEX, SHARED, CALIB, CONCAVE, EXPECT)
    assert ok, f"gate #109 fails on the shipped manuscript: {info}"


def test_variant_carries_the_landing():
    ok, info = runoff_error_basis_check(VARIANT, SHARED, CALIB, CONCAVE, EXPECT)
    assert ok, f"gate #109 fails on the long-abstract variant: {info}"


def test_shared_pair_removal_fails():
    pair = "$+2.8$ / $-66.8$"
    assert pair in TEX, "headline shared pair missing (vacuous mutation)"
    ok, _ = runoff_error_basis_check(
        TEX.replace(pair, "$+2.8$"), SHARED, CALIB, CONCAVE, EXPECT)
    assert not ok


def test_third_of_six_removal_fails():
    span = "third of six rather than first"
    assert span in TEX
    ok, _ = runoff_error_basis_check(
        TEX.replace(span, ""), SHARED, CALIB, CONCAVE, EXPECT)
    assert not ok


def test_crosswalk_row_removal_fails():
    span = "Cum.\\ runoff error (six hazard legs)"
    assert span in TEX
    ok, _ = runoff_error_basis_check(
        TEX.replace(span, ""), SHARED, CALIB, CONCAVE, EXPECT)
    assert not ok


def test_retired_smallest_restored_fails():
    assert RETIRED_SMALLEST not in TEX
    # Drop the corrected ranking sentence and put the old one back.
    restored = TEX.replace(
        "And the column's basis decides its ranking.",
        "And the headline off-window central leg, at 91.3\\% shared, "
        + RETIRED_SMALLEST + " And the column's basis decides its ranking.",
    )
    ok, info = runoff_error_basis_check(
        restored, SHARED, CALIB, CONCAVE, EXPECT)
    assert not ok
    assert RETIRED_SMALLEST in info["present_retired"]


def test_retired_patha_restored_fails():
    assert RETIRED_PATHA not in TEX
    restored = TEX.replace(
        "Path A overshoots the benchmark by \\$164.1 billion on its "
        "standalone scorer",
        "Path A " + RETIRED_PATHA + " of the \\$652.8 billion of runoff "
        "actually realized---REPLACE Path A overshoots the benchmark by "
        "\\$164.1 billion on its standalone scorer",
    )
    ok, info = runoff_error_basis_check(
        restored, SHARED, CALIB, CONCAVE, EXPECT)
    assert not ok
    assert any("164.1" in s for s in info["present_retired"])


def test_anchor_drift_fails():
    c = copy.deepcopy(CALIB)
    for row in c["floor_table"]:
        if row["floor_annual_cpr_pct"] == 4.991:
            row["miss_vs_benchmark_pp"] = 1.0  # was ~8.73
    ok, info = runoff_error_basis_check(TEX, SHARED, c, CONCAVE, EXPECT)
    assert not ok
    assert info["anchor_ok"] is False


def test_netting_break_fails():
    s = copy.deepcopy(SHARED)
    s["results"]["path_b_central"]["us_trapped_b"] -= 1.0
    ok, info = runoff_error_basis_check(TEX, s, CALIB, CONCAVE, EXPECT)
    assert not ok
    assert info["netting_ok"] is False


def test_marginals_untouched():
    assert "$+5.6$ points ($+\\$42.6$ billion)" in TEX
    assert "$+9.2$ points ($+\\$70.3$ billion)" in TEX
    stripped = TEX.replace("$+5.6$ points ($+\\$42.6$ billion)", "")
    ok, info = runoff_error_basis_check(
        stripped, SHARED, CALIB, CONCAVE, EXPECT)
    assert not ok
    assert info["marginal_ok"] is False
