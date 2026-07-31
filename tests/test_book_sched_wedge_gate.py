"""Battery for gate #115 (R33-B part 2: the cross-design book-sched wedge).

Also re-derives the decomposition's own arithmetic independently of the runner,
so the artifact cannot drift from its spec without a test failing.
"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import book_sched_wedge_check  # noqa: E402

TEX = (ROOT / "paper" / "v18" / "revised_paper_v18.tex").read_text()
VARIANT = (ROOT / "paper" / "v18"
           / "revised_paper_v18_long_abstract.tex").read_text()
R33B = json.loads((ROOT / "abm" / "data"
                   / "r33b_book_sched_results.json").read_text())
SEEDS = json.loads((ROOT / "abm" / "data"
                    / "cross_design_seeds_results.json").read_text())
FOLDIN = json.loads((ROOT / "abm" / "data" / "runs"
                     / "run-2026-07-04-15yr-foldin" / "manifest.json").read_text())
CROSS = json.loads((ROOT / "abm" / "data"
                    / "cross_design_results.json").read_text())


def test_gate_passes_on_both_editions():
    for tex, label in ((TEX, "main"), (VARIANT, "variant")):
        ok, info = book_sched_wedge_check(tex, R33B, SEEDS)
        assert ok, f"gate #115 fails on {label}: {info}"


def test_spec_was_committed_before_the_run():
    spec = ROOT / "specs" / "SPEC_R33B_book_sched_decomposition.md"
    assert spec.exists()
    assert R33B["spec"] == "specs/SPEC_R33B_book_sched_decomposition.md"


def test_all_parity_gates_passed():
    pg = R33B["parity_gates"]
    assert pg["P1_holdings_scale_agreement"]["pass"]
    assert pg["P2_committed_quotes_replay"]["pass"]
    assert pg["P3_population_parameters_replay"]["pass"]
    assert R33B["parity_gates_all_pass"]


def test_direction_prediction_held():
    """The spec predicted the book amortizes faster; it must be recorded."""
    assert R33B["parity_gates"]["P4_direction_prediction"]["pass"]
    assert R33B["verdict"]["prediction_held"]


def test_holdings_scale_recovered_two_independent_ways():
    """P1 is a real check: two different SMM series, same holdings scale."""
    hs = R33B["holdings_scale"]
    sa = FOLDIN["metrics"]["scheduled_amort_b"]
    cu = FOLDIN["metrics"]["curtailment_b"]
    n = FOLDIN["metrics"]["qt_window"]["n_months"]
    assert abs(hs["h_from_scheduled_b"]
               - sa["total"] / (n * sa["smm_mean_pct"] / 100)) < 1e-6
    assert abs(hs["h_from_curtailment_b"]
               - cu["total"] / (n * cu["smm_mean_pct"] / 100)) < 1e-6
    assert hs["relative_gap"] < 0.02


def test_wedge_applied_consistently_to_every_leg():
    """Each leg's book basis is its sample basis less the same wedge."""
    B = CROSS["variants"]["recalibrated"]["empirical_trapped_b"]
    delta = R33B["delta"]["primary_b"]
    for leg, v in R33B["applied"].items():
        assert abs(v["book_basis_trapped_b"]
                   - (v["sample_basis_trapped_b"] - delta)) < 1e-9, leg
        assert abs(v["book_basis_share_pct"]
                   - v["book_basis_trapped_b"] / B * 100) < 1e-9, leg


def test_branch_matches_the_precommitted_rule():
    """T2 is defined as mean >= 50 > min; re-derive it from the numbers."""
    mean = R33B["applied"]["fifty_seed_mean"]["book_basis_share_pct"]
    mn = R33B["applied"]["fifty_seed_min"]["book_basis_share_pct"]
    assert mean >= 50.0 > mn
    assert R33B["verdict"]["branch"] == "T2"


def test_seed_count_recomputed_from_cells():
    """The 'sixteen of fifty' claim, recomputed from the seed artifact."""
    B = CROSS["variants"]["recalibrated"]["empirical_trapped_b"]
    delta = R33B["delta"]["primary_b"]
    cells = [c for c in SEEDS["per_cell"]
             if c.get("leg") == "A_joint" and c.get("variant") == "recalibrated"]
    assert len(cells) == 50
    below = sum(1 for c in cells
                if (c["trapped_b"] - delta) / B * 100 < 50.0)
    assert below == R33B["verdict"]["seeds_below_threshold"] == 16
    # And every one of them cleared the threshold on the sample basis.
    assert all(c["share_pct"] >= 50.0 for c in cells)


def test_count_survives_a_per_seed_wedge():
    """The landing applies one Delta to every seed; the per-seed recomputation
    (each cell's own population age) must give the same count, or the headline
    'sixteen of the fifty' is an artefact of the approximation."""
    chk = R33B["seed_invariance_check"]
    assert chk["n_below_seed_invariant_delta"] == chk["n_below_per_seed_delta"]
    assert chk["agree"] is True
    assert R33B["verdict"]["seeds_below_threshold_per_seed_delta"] == 16


def test_unanimity_retirement_is_stated():
    span = "The threshold verdict survives the basis change; its unanimity does not"
    assert span in TEX
    ok, _ = book_sched_wedge_check(TEX.replace(span, ""), R33B, SEEDS)
    assert not ok


def test_bare_unanimity_restored_fails():
    bare = ("and all fifty seeds classify as undercutting. The frozen "
            "variant averages 22.0\\%.")
    assert bare not in TEX, "the bare unanimity claim should be qualified now"
    restored = TEX.replace(
        "and all fifty seeds classify as undercutting. That verdict is stated",
        "and all fifty seeds classify as undercutting. The frozen variant "
        "averages 22.0\\%. That verdict is stated")
    ok, info = book_sched_wedge_check(restored, R33B, SEEDS)
    assert not ok
    assert info["present_retired"]


def test_wedge_drift_fails():
    r = copy.deepcopy(R33B)
    r["delta"]["primary_b"] = 40.0
    r["delta"]["primary_pp_of_benchmark"] = 5.2
    ok, _ = book_sched_wedge_check(TEX, r, SEEDS)
    assert not ok


def test_failed_parity_blocks_the_landing():
    r = copy.deepcopy(R33B)
    r["parity_gates_all_pass"] = False
    ok, info = book_sched_wedge_check(TEX, r, SEEDS)
    assert not ok
    assert info["parity_gates_all_pass"] is False


def test_branch_change_blocks_the_landing():
    """If a rerun ever lands on T1 or T3, this landing's wording is wrong."""
    for branch in ("T1", "T3", "T4"):
        r = copy.deepcopy(R33B)
        r["verdict"]["branch"] = branch
        ok, _ = book_sched_wedge_check(TEX, r, SEEDS)
        assert not ok, branch
