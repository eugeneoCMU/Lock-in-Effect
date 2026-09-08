"""Battery for gate #126 (the floor-form mixture curve) and for gate #57's
scoped in-sample demotion check.

WHY THIS GATE EXISTS. Ledger C-22 -- the paper's headline posture -- turns
entirely on this artifact: the headline +5.6 is the omega = 0 endpoint of the
curve it measures, and the case for and against moving the headline is made
from its interior. Until gate #126 landed, `grep -rn floor_form_mixture
tools/ tests/` returned EMPTY. Every number in that decision was read by no
gate and no test, so a drifted print or a flipped orientation would have
shipped green.

WHY THE CHECK DERIVES RATHER THAN PINS. The curve values are computed from the
artifact and matched against the manuscript, so a stale copy fails instead of
passing. The mutations below therefore attack BOTH sides -- the printed text
and the artifact -- because a gate that only reads one of them is a gate that
cannot tell drift from agreement.

GATE #57's HOLE, recorded. Its `insample_demoted` limb was a bare whole-file
presence check for "in-sample calibration point". That string survives any
headline reversal -- the phrase appears in the appendices regardless -- so the
limb asserted nothing about demotion. `test_old_unscoped_rule_missed_the_reversal`
below documents the hole by construction: it asserts the OLD rule passes the
exact mutation the NEW rule catches.
"""
import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import (  # noqa: E402
    ABSTRACT_BOUNDS,
    FFM_RESULTS,
    _abstract_of,
    floor_form_mixture_check,
)

TEX_FILE = ROOT / "paper" / "final" / "paper_final_v1.tex"
APPX_FILE = ROOT / "paper" / "final" / "replication_appendices.tex"


@pytest.fixture(scope="module")
def tex():
    """The gate's real corpus: manuscript + the shipped replication appendices."""
    return TEX_FILE.read_text() + "\n" + APPX_FILE.read_text()


@pytest.fixture(scope="module")
def ffm():
    return json.loads(FFM_RESULTS.read_text())


def test_baseline_passes(tex, ffm):
    ok, info = floor_form_mixture_check(tex, ffm)
    assert ok, f"gate #126 is red on the shipped tree: {info}"
    assert info["missing"] == []


# --------------------------------------------------------------------------
# Manuscript-side drift. Each mutation moves ONE printed figure.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("old,new,what", [
    ("$+10.7$ at $\\omega = 0.4$", "$+10.8$ at $\\omega = 0.4$",
     "VII.F's curve value at the paper-semantics point"),
    ("$+9.7$ at $\\omega{=}0.25$", "$+9.8$ at $\\omega{=}0.25$",
     "Table 1's notes"),
    ("$+7.5$ points by $\\omega = 0.1$", "$+7.6$ points by $\\omega = 0.1$",
     "the curve's first interior point"),
])
def test_a_drifted_print_fails(tex, ffm, old, new, what):
    mutated = tex.replace(old, new, 1)
    assert mutated != tex, f"mutation did not apply: {what}"
    ok, _ = floor_form_mixture_check(mutated, ffm)
    assert not ok, f"gate #126 accepted a drifted print of {what}"


def test_flipping_the_orientation_fails(tex, ffm):
    """The endpoints are the whole posture. Swapping which one is production
    inverts C-22's meaning while leaving every numeral in place."""
    mutated = tex.replace(
        "$\\omega = 0$ is the production hard maximum, $\\omega = 1$ the additive form",
        "$\\omega = 1$ is the production hard maximum, $\\omega = 0$ the additive form", 1)
    assert mutated != tex
    ok, _ = floor_form_mixture_check(mutated, ffm)
    assert not ok, "gate #126 accepted a flipped orientation"


def test_deleting_the_transmission_sentence_fails(tex, ffm):
    """The asymmetry -- 3.63 points of floor sensitivity under the max form
    against 0.04 under the additive -- is what makes the binding interval's
    width a property of the form choice. A concision pass must not take it."""
    mutated = tex.replace(
        "moves the marginal by $-3.63$ points under the production form and "
        "by $-0.04$ under the additive one", "moves the marginal", 1)
    assert mutated != tex
    ok, _ = floor_form_mixture_check(mutated, ffm)
    assert not ok, "gate #126 accepted deletion of the transmission asymmetry"


def test_dropping_the_run_citation_fails(tex, ffm):
    mutated = tex.replace("\\texttt{floor\\_form\\_mixture}", "the mixture run")
    assert mutated != tex
    ok, _ = floor_form_mixture_check(mutated, ffm)
    assert not ok, "gate #126 accepted a manuscript with no run-tag citation"


# --------------------------------------------------------------------------
# Artifact-side drift. A gate that only reads the manuscript cannot tell
# agreement from a shared error.
# --------------------------------------------------------------------------
def test_a_drifted_artifact_fails(tex, ffm):
    mutated = copy.deepcopy(ffm)
    mutated["cells"]["4.991|0|6.5"]["marginal_pp"] = 7.0
    ok, _ = floor_form_mixture_check(tex, mutated)
    assert not ok, "gate #126 accepted an artifact whose endpoint left the headline"


def test_a_collapsed_asymmetry_fails(tex, ffm):
    """If the max form stopped censoring, the posture argument would change.
    The gate must notice rather than keep printing the old sentence."""
    mutated = copy.deepcopy(ffm)
    mutated["cells"]["4|0|6.5"]["marginal_pp"] = 5.60
    ok, _ = floor_form_mixture_check(tex, mutated)
    assert not ok, "gate #126 accepted a collapsed floor-transmission asymmetry"


def test_a_failed_parity_run_fails(tex, ffm):
    mutated = copy.deepcopy(ffm)
    mutated["parity_gates_all_pass"] = False
    ok, _ = floor_form_mixture_check(tex, mutated)
    assert not ok, "gate #126 accepted an artifact whose own parity gates failed"


# --------------------------------------------------------------------------
# Gate #57's scoped limb.
# --------------------------------------------------------------------------
REVERSAL = ("with $+9.2$ points, \\$70.3 billion, the in-sample point, inside it")
CURRENT = ("with $+5.6$ points, \\$42.6 billion, the production form's "
           "endpoint, inside it")


def test_abstract_extractor_agrees_with_the_hedge_gate(tex):
    """_abstract_of must cut the same environment gate #68 measures. The first
    cut of it used a two-backslash lookbehind and truncated at the abstract's
    first escaped percent, which silently shortened it to 78 words."""
    from liveness_gates import abstract_hedge_check
    _, ab = abstract_hedge_check(TEX_FILE.read_text())
    assert len(_abstract_of(TEX_FILE.read_text()).split()) == ab["words"]
    assert ABSTRACT_BOUNDS == ("\\begin{abstract}", "\\end{abstract}")


def test_scoped_rule_catches_a_headline_reversal(tex):
    mutated = tex.replace(CURRENT, REVERSAL, 1)
    assert mutated != tex, "the abstract's point clause moved; re-sync this battery"
    ab = _abstract_of(mutated)
    scoped_ok = "$+5.6$" in ab and "$+9.2$" not in ab
    assert not scoped_ok, "the scoped rule accepted an in-sample headline"


def test_old_unscoped_rule_missed_the_reversal(tex):
    """Documents the hole gate #57 shipped with, so it cannot come back."""
    mutated = tex.replace(CURRENT, REVERSAL, 1)
    assert mutated != tex
    assert "in-sample calibration point" in mutated, (
        "the OLD unscoped rule would have PASSED this reversal -- that is the "
        "hole; if this assert ever fails the phrase moved and the record needs "
        "updating, not the gate")
