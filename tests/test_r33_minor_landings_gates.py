"""Batteries for gates #112 (null balance path), #113 (Danish mean CPR),
and #114 (the 'within 45%' scope).

Findings 6, 7 and 8 of the §§IV--VI referee round. Every mutation is asserted
non-vacuous before it is applied.
"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import (  # noqa: E402
    danish_cpr_manifest_check,
    null_balance_path_check,
    within45_scope_check,
)

TEX = (ROOT / "paper" / "v18" / "revised_paper_v18.tex").read_text()
VARIANT = (ROOT / "paper" / "v18"
           / "revised_paper_v18_long_abstract.tex").read_text()
SHARED = json.loads((ROOT / "hazard" / "data"
                     / "shared_layer_scoring_results.json").read_text())
FOLDIN = json.loads((ROOT / "abm" / "data" / "runs"
                     / "run-2026-07-04-15yr-foldin" / "manifest.json").read_text())
BERGER = json.loads((ROOT / "abm" / "data" / "runs" / "run-2026-07-05-berger"
                     / "manifest.json").read_text())
STAGES = json.loads((ROOT / "figures" / "fig3_stage_levels.json").read_text())


# --- gate #112: the null's balance-path asymmetry -------------------------

def test_112_passes_on_both_editions():
    for tex, label in ((TEX, "main"), (VARIANT, "variant")):
        ok, info = null_balance_path_check(tex, SHARED)
        assert ok, f"gate #112 fails on {label}: {info}"


def test_112_disclosure_removal_fails():
    span = "upper bound on the compounding-consistent one"
    assert span in TEX
    ok, _ = null_balance_path_check(TEX.replace(span, ""), SHARED)
    assert not ok


def test_112_asymmetry_sentence_removal_fails():
    span = "The renormalisation is not symmetric in what it costs the two legs"
    assert span in TEX
    ok, _ = null_balance_path_check(TEX.replace(span, ""), SHARED)
    assert not ok


def test_112_direction_flip_fails():
    """If the null ever traps MORE than the central leg, 'upper bound' inverts."""
    s = copy.deepcopy(SHARED)
    s["results"]["no_lockin_null"]["us_trapped_b"] = (
        s["results"]["path_b_central"]["us_trapped_b"] + 1.0)
    ok, info = null_balance_path_check(TEX, s)
    assert not ok
    assert info["direction_ok"] is False


# --- gate #113: tab:danish mean-CPR cells vs their manifests --------------

def test_113_passes_on_both_editions():
    for tex, label in ((TEX, "main"), (VARIANT, "variant")):
        ok, info = danish_cpr_manifest_check(tex, FOLDIN, BERGER)
        assert ok, f"gate #113 fails on {label}: {info}"


def test_113_old_cells_restored_fail():
    for stale in ("11.68\\% / 47.10\\%", "11.76\\% / 3.40\\%"):
        assert stale not in TEX, f"{stale} should have been corrected"
    restored = TEX.replace("11.68\\% / 47.14\\%", "11.68\\% / 47.10\\%")
    ok, info = danish_cpr_manifest_check(restored, FOLDIN, BERGER)
    assert not ok
    assert "11.68\\% / 47.10\\%" in info["present_retired"]


def test_113_stale_prose_range_restored_fails():
    restored = TEX.replace("(3.36--3.39\\%, Table~\\ref{tab:danish})",
                           "(3.39--3.40\\%, Table~\\ref{tab:danish})")
    ok, _ = danish_cpr_manifest_check(restored, FOLDIN, BERGER)
    assert not ok


def test_113_manifest_drift_fails():
    """A drifted manifest must fail against the unmoved tex."""
    b = copy.deepcopy(BERGER)
    b["metrics"]["cpr_pct"]["danish"]["mean"] = 3.99
    ok, _ = danish_cpr_manifest_check(TEX, FOLDIN, b)
    assert not ok


def test_113_cells_are_the_manifest_values():
    assert f"{FOLDIN['metrics']['cpr_pct']['danish']['mean']:.2f}" == "47.14"
    assert f"{BERGER['metrics']['cpr_pct']['danish']['mean']:.2f}" == "3.36"


# --- gate #114: the 'within 45%' scope ------------------------------------

def test_114_passes_on_both_editions():
    for tex, label in ((TEX, "main"), (VARIANT, "variant")):
        ok, info = within45_scope_check(tex, STAGES)
        assert ok, f"gate #114 fails on {label}: {info}"


def test_114_scope_clause_removal_fails():
    span = "once the production corrections are applied"
    assert span in TEX
    ok, _ = within45_scope_check(TEX.replace(span, ""), STAGES)
    assert not ok


def test_114_counterexample_removal_fails():
    span = "the rational baseline at 71.1\\% does land within 45\\%"
    assert span in TEX
    ok, _ = within45_scope_check(TEX.replace(span, ""), STAGES)
    assert not ok


def test_114_goes_inert_if_baseline_moves_below_the_bar():
    """If the baseline ever falls outside 45 points, the caveat is moot."""
    s = copy.deepcopy(STAGES)
    s["stages"][0]["share_pct"] = 40.0
    ok, info = within45_scope_check(TEX, s)
    assert not ok
    assert info["counterexample_live"] is False
