"""Battery for gate #111 (R33-B part 1: the empirical-CPR referent).

Every mutation is asserted non-vacuous before it is applied.
"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import cpr_referent_check  # noqa: E402

TEX = (ROOT / "paper" / "v18" / "revised_paper_v18.tex").read_text()
VARIANT = (ROOT / "paper" / "v18"
           / "revised_paper_v18_long_abstract.tex").read_text()
FOLDIN = json.loads((ROOT / "abm" / "data" / "runs"
                     / "run-2026-07-04-15yr-foldin" / "manifest.json").read_text())
CROSS = json.loads((ROOT / "abm" / "data"
                    / "cross_design_results.json").read_text())
REWEIGHT = json.loads((ROOT / "abm" / "data"
                       / "cross_design_reweight_results.json").read_text())

RETIRED = "Two implementations of this back-out exist in the pipeline"


def test_gate_passes_on_the_manuscript():
    ok, info = cpr_referent_check(TEX, FOLDIN, CROSS, REWEIGHT)
    assert ok, f"gate #111 fails on the shipped manuscript: {info}"


def test_variant_carries_the_landing():
    ok, info = cpr_referent_check(VARIANT, FOLDIN, CROSS, REWEIGHT)
    assert ok, f"gate #111 fails on the long-abstract variant: {info}"


def test_retired_two_implementations_fails():
    assert RETIRED not in TEX
    restored = TEX.replace(
        "Three implementations of this back-out exist in the pipeline",
        RETIRED)
    ok, info = cpr_referent_check(restored, FOLDIN, CROSS, REWEIGHT)
    assert not ok
    assert RETIRED in info["present_retired"]


def test_mechanism_clause_removal_fails():
    span = "keyed to the simulated population's own weighted coupon and mean age"
    assert span in TEX
    ok, _ = cpr_referent_check(TEX.replace(span, ""), FOLDIN, CROSS, REWEIGHT)
    assert not ok


def test_table_row_referent_removal_fails():
    span = "mean CPR 8.14\\% against its own 5.83\\% back-out"
    assert span in TEX
    ok, _ = cpr_referent_check(
        TEX.replace(span, "mean CPR 8.14\\%"), FOLDIN, CROSS, REWEIGHT)
    assert not ok


def test_table_note_scope_removal_fails():
    span = ("not on a common referent with the rest of the table, while "
            "every dollar column is")
    assert span in TEX
    ok, _ = cpr_referent_check(TEX.replace(span, ""), FOLDIN, CROSS, REWEIGHT)
    assert not ok


def test_referent_drift_fails():
    """A moved artifact must fail against the unmoved tex (anti-drift)."""
    c = copy.deepcopy(CROSS)
    c["variants"]["recalibrated"]["empirical_cpr_mean_pct"] = 6.01
    ok, _ = cpr_referent_check(TEX, FOLDIN, c, REWEIGHT)
    assert not ok


def test_production_referent_drift_fails():
    f = copy.deepcopy(FOLDIN)
    f["metrics"]["cpr_pct"]["empirical"]["mean"] = 5.55
    ok, _ = cpr_referent_check(TEX, f, CROSS, REWEIGHT)
    assert not ok


def test_collapsed_referents_fail():
    """If the three back-outs ever coincide, the disclosure is inert."""
    c = copy.deepcopy(CROSS)
    r = copy.deepcopy(REWEIGHT)
    prod = FOLDIN["metrics"]["cpr_pct"]["empirical"]["mean"]
    c["variants"]["recalibrated"]["empirical_cpr_mean_pct"] = prod
    for v in r["variants"].values():
        v["empirical_cpr_mean_pct"] = prod
    ok, info = cpr_referent_check(TEX, FOLDIN, c, r)
    assert not ok
    assert info["distinct_ok"] is False


def test_broken_common_benchmark_fails():
    """The printed claim is that the DOLLAR benchmark is common; police it."""
    c = copy.deepcopy(CROSS)
    c["variants"]["frozen"]["empirical_trapped_b"] += 1.0
    ok, info = cpr_referent_check(TEX, FOLDIN, c, REWEIGHT)
    assert not ok
    assert info["bench_ok"] is False
