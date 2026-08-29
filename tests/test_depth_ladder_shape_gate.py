"""Battery for gate #114 (R32 C-80: the 2018 depth ladder's shape).

This exhibit's failure mode is cherry-picking. The plateau supports the paper's
own production form, so the tests bind hardest on the parts that argue the other
way: the falling tail, the bin that rises, and the not-a-test caveat.
"""
import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import depth_ladder_shape_check  # noqa: E402

TEX = (ROOT / "paper" / "final" / "paper_final_v1.tex").read_text()
VARIANT = (ROOT / "paper" / "final"
           / "paper_final_v1_long_abstract.tex").read_text()
D = json.loads((ROOT / "hazard" / "data"
                / "depth_ladder_shape_results.json").read_text())
BINS = {b["bin"]: b for b in D["bins"]}


def test_gate_passes_on_the_manuscript():
    ok, info = depth_ladder_shape_check(TEX, D)
    assert ok, f"gate #114 fails on the shipped manuscript: {info}"


def test_variant_carries_it():
    ok, info = depth_ladder_shape_check(VARIANT, D)
    assert ok, f"gate #114 fails on the long-abstract variant: {info}"


@pytest.mark.parametrize("b", list(BINS))
def test_each_bin_drift_fails(b):
    d = copy.deepcopy(D)
    for x in d["bins"]:
        if x["bin"] == b:
            x["cpr_pct"] += 0.5
    ok, _ = depth_ladder_shape_check(TEX, d)
    assert not ok, f"a drifted {b} must fail against the unmoved tex"


@pytest.mark.parametrize("phrase", [
    "not well supported",
    "rather than falling",
    "not as a resolution of the fork",
])
def test_each_counter_disclosure_is_pinned(phrase):
    """The parts that argue against the paper's own form must be undeletable."""
    assert phrase in TEX, f"{phrase!r} missing (vacuous mutation)"
    ok, _ = depth_ladder_shape_check(TEX.replace(phrase, ""), D)
    assert not ok, f"{phrase!r} is not pinned"


def test_differencing_inverts():
    """P1: the run's own inversion check must have passed, to 1e-9."""
    assert D["parity"]["differencing_inverts_to_nested_reads"] is True
    worst = max(v["abs_diff"] for v in D["inversion_check"].values())
    assert worst < 1e-9, f"inversion drifted to {worst}"


def test_the_shape_is_actually_a_step_then_plateau():
    """Re-derived here, not read from the summary string."""
    b = BINS
    shallow = [b["(-0.0025,+0.0000]"]["cpr_pct"], b["(-0.0050,-0.0025]"]["cpr_pct"]]
    plateau = [b["(-0.0075,-0.0050]"]["cpr_pct"], b["(-0.0100,-0.0075]"]["cpr_pct"]]
    assert min(shallow) - max(plateau) > 2.0, "the step should be large"
    assert abs(plateau[0] - plateau[1]) < 0.10, "the plateau should be flat"


def test_the_rising_bin_is_not_a_decline():
    """The bin after the plateau rises; that is the point of quoting it."""
    assert BINS["(-0.0150,-0.0100]"]["cpr_pct"] > BINS["(-0.0100,-0.0075]"]["cpr_pct"]


def test_tail_is_thin_and_flagged():
    tail = [b for b in D["bins"] if not b["well_supported"]]
    assert tail, "there is supposed to be an unsupported tail"
    assert D["shape"]["tail_exposure_share"] < 0.15
    for b in tail:
        assert b["well_supported"] is False


def test_plateau_coverage_is_the_conservative_both_edges_rule():
    """A bin counts as supported only if BOTH edges are -- stricter than source."""
    assert D["shape"]["plateau_exposure_share"] > 0.5
    assert BINS["(-0.0150,-0.0100]"]["well_supported"] is False


def test_no_new_estimation():
    assert D["spec"]["no_new_estimation"] is True
