"""The paradigm reading is WITHDRAWN, and the withdrawal must travel.

Background. Section VII.C fixed a 50% recovery threshold before the run, above
which "the paradigm interpretation advanced in Sections IV--VIII" would be
undercut. The real-covariate leg returned 59.3% on the committed draw, 60.2%
over fifty seeds (undercutting on all fifty), and 76.3% once the sample carries
the SOMA book's own composition. The paper's response used to stop at a hedge
about ATTRIBUTION -- "cannot, on that test alone, be cleanly attributed to
modeling paradigm" -- which is a statement that the test was inconclusive, not
a statement that the pre-committed reading fell. A reviewer reading the
pre-registration meets the threshold, meets the crossing, and then finds the
claim still standing three sections later.

The withdrawal is now stated where the test lives (VII.C), pointed at from the
section that advanced the reading (IV's lead) and from the conclusion. This
battery pins all three, because a hedge is exactly what a later compression
pass would mistake the withdrawal for and delete.

Note what is NOT asserted here: the paper does not claim "the contrast is not a
paradigm effect". Withdrawing a claim and asserting its negation are different
acts, and liveness_gates.ABM_LEAD_SPANS["bound_verdict_wording"] deliberately
pins the weaker "cannot attribute" verdict. Both must hold at once.
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TEX = (ROOT / "paper" / "final" / "paper_final_v1.tex").read_text()
VARIANT = (ROOT / "paper" / "final"
           / "paper_final_v1_long_abstract.tex").read_text()

BOTH = pytest.mark.parametrize("tex", [TEX, VARIANT], ids=["canonical", "variant"])

WITHDRAWAL = "I therefore withdraw the paradigm reading as a claim of this paper."
IV_POINTER = "The paradigm reading this section was written to advance is withdrawn"
CONCLUSION_POINTER = "On the paradigm question itself I make no claim"


@BOTH
def test_withdrawal_is_stated_once_where_the_test_lives(tex):
    assert tex.count(WITHDRAWAL) == 1, (
        "the VII.C withdrawal sentence is the whole point of the fix; it must "
        "be present exactly once, in the subsection that ran the test")


@BOTH
def test_withdrawal_carries_its_reason(tex):
    """The threshold, the crossing, and the refusal to narrow post hoc."""
    i = tex.find(WITHDRAWAL)
    window = tex[i:i + 1200]
    assert "pre-committed to a threshold before the run" in window
    assert "on all fifty seeds" in window
    assert "narrowing it is what the pre-commitment architecture exists to prevent" in window


@BOTH
def test_the_two_surviving_results_are_named_and_disclaimed(tex):
    """Withdrawing the paradigm claim must not withdraw the ABM sections."""
    i = tex.find(WITHDRAWAL)
    window = tex[i:i + 1200]
    assert "neither is a claim about modeling paradigm" in window
    assert "no synthetic-population household-choice specification tested here explains" in window
    assert "no estimator in this paper reproduces the monthly path" in window


@BOTH
def test_section_iv_and_the_conclusion_follow(tex):
    assert tex.count(IV_POINTER) == 1, "Section IV's lead must record the withdrawal"
    assert tex.count(CONCLUSION_POINTER) == 1, "the conclusion must record it too"


@BOTH
def test_attribution_hedge_still_stands_beside_the_withdrawal(tex):
    """Withdrawal is not the negation. Both statements coexist by design."""
    assert "cannot, on that test alone, be cleanly attributed to modeling paradigm" in tex


@BOTH
def test_the_precommitted_threshold_is_still_quoted(tex):
    """If the threshold ever leaves the paper, the withdrawal loses its warrant."""
    assert "above the 50\\% threshold fixed before that run" in tex
    assert "60.2\\% averaged over fifty seeds" in tex
    assert "76.3\\%" in tex


@BOTH
@pytest.mark.parametrize("mutation", [
    WITHDRAWAL,
    IV_POINTER,
    CONCLUSION_POINTER,
])
def test_deleting_any_leg_is_detectable(tex, mutation):
    """Each pinned span must actually be load-bearing, not incidentally true."""
    mutated = tex.replace(mutation, "", 1)
    assert mutated != tex
    assert mutation not in mutated or tex.count(mutation) > 1
