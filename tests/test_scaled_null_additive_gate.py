"""Battery for liveness gate #118 (R32 C-77: the Aladangady calibration is
form-conditional).

This landing's failure mode is PLACEMENT, not arithmetic. The additive member is
+8.5 points -- INSIDE the +2.9 to +8.7 binding interval, in its UPPER half --
while gate #98 pins the claim that every correction listed above that interval
falls in its LOWER half. Writing this member into the downward ladder would
falsify a pinned sentence without touching it, so the three relocation tests are
the ones that matter most here; the rest bind the printed literals to the two
artifacts and the verdict to the run's own gates.

Every mutation below was traced by hand and then simulated against the shipped
rule before this file was written: each one turns the gate red, and each kills
exactly the check named in its comment. A mutation whose damage is absorbed by
some OTHER pinned span is not a test, and there is none of those here.
"""
from __future__ import annotations

import copy
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import (  # noqa: E402
    SNHA_ADDITIVE_PROSE,
    TEX,
    snha_additive_check,
)

VARIANT_PATH = ROOT / "paper" / "v18" / "revised_paper_v18_long_abstract.tex"
MAX_PATH = ROOT / "hazard" / "data" / "scaled_null_housing_activity_results.json"
ADD_PATH = (ROOT / "hazard" / "data"
            / "scaled_null_housing_activity_additive_results.json")

# V20 closing-session rescope: the runindex row lives in replication_appendices.tex
_REPLAPPX = (ROOT / "paper" / "v18" / "replication_appendices.tex").read_text()
TEXT = TEX.read_text() + "\n" + _REPLAPPX
VARIANT = VARIANT_PATH.read_text() + "\n" + _REPLAPPX
MAXB = MAX_PATH.read_bytes()
A = json.loads(ADD_PATH.read_text())
MX = json.loads(MAXB)

LOWER_HALF = "every correction listed above falls in its lower half"
COUNTERWEIGHTS = "Upward: the additive form returns"
PASSAGE_END = "belongs with the counterweights above rather than with the ladder."
MAX_TAG = "\\texttt{scaled\\_null\\_housing\\_activity}"
ADD_TAG = "\\texttt{scaled\\_null\\_housing\\_activity\\_additive}"


def _passage(tex: str) -> str:
    i = tex.find(SNHA_ADDITIVE_PROSE)
    j = tex.find(PASSAGE_END, i)
    assert i != -1 and j != -1, "the additive passage is not in the manuscript"
    p = tex[i:j + len(PASSAGE_END)]
    assert tex.count(p) == 1, "the passage is not a single site"
    return p


def _check(tex=None, a=None, mx=None, mb=None):
    return snha_additive_check(TEXT if tex is None else tex,
                               A if a is None else a,
                               MX if mx is None else mx,
                               MAXB if mb is None else mb)


# --------------------------------------------------------------------------
# green on what ships
# --------------------------------------------------------------------------
def test_gate_passes_on_the_manuscript():
    ok, info = _check()
    assert ok, f"gate #118 fails on the shipped manuscript: {info}"


def test_variant_carries_it():
    ok, info = _check(tex=VARIANT)
    assert ok, f"gate #118 fails on the long-abstract variant: {info}"


# --------------------------------------------------------------------------
# THE relocation attacks. Every literal survives in the file in all three; the
# gate must still go red, because what these break is where the member sits.
# --------------------------------------------------------------------------
def test_relocating_the_member_into_the_downward_ladder_fails():
    """TRACE: the passage is lifted out and re-inserted immediately before the
    lower-half sentence, so the found-offsets become i_add < i_low < i_ctr. The
    ordering assert is `-1 < i_low < i_ctr < i_add`; its last comparison is
    False, so `ordered` is False and that is the SOLE bite -- all 21 lits are
    still satisfied (the text moved, it did not vanish), in_paragraph is still
    True (it moved within the same line), and every artifact check still passes.
    +8.5 is in the interval's upper half, so this is exactly the edit that would
    falsify gate #98's pinned lower-half sentence without editing it."""
    p = _passage(TEXT)
    assert TEXT.count(LOWER_HALF) == 1, "vacuous mutation"
    moved = TEXT.replace(p, "").replace(LOWER_HALF, p + " " + LOWER_HALF)
    assert moved != TEXT and len(moved) == len(TEXT) + 1
    ok, info = _check(tex=moved)
    assert not ok, f"the additive member must not be writable into the ladder: {info}"
    assert info["ordered"] is False and not info["missing"]


def test_moving_the_member_ahead_of_the_counterweights_fails():
    """TRACE: the passage is re-inserted before the 'Upward:' list, giving
    i_low < i_add < i_ctr. `i_ctr < i_add` is False, so `ordered` is False and is
    again the sole bite. The member must be written WITH the counterweights it
    is filed under, not ahead of them."""
    p = _passage(TEXT)
    assert TEXT.count(COUNTERWEIGHTS) == 1, "vacuous mutation"
    moved = TEXT.replace(p, "").replace(COUNTERWEIGHTS, p + " " + COUNTERWEIGHTS)
    ok, info = _check(tex=moved)
    assert not ok, "the member must not precede the counterweight clause"
    assert info["ordered"] is False and not info["missing"]


def test_passage_must_stay_in_the_seventh_qualification_paragraph():
    """TRACE: the passage is removed from line 361 and appended as its own
    paragraph at end of file. The opener line still exists, so `paras` is still
    length 1 and every lit is still satisfied whole-file; `ordered` even stays
    True (i_add is now the largest offset). The sole bite is in_paragraph, which
    requires BOTH the opener sentence and the placement sentence to live inside
    paras[0]. This is the paragraph-split attack gate #98 exists for, aimed at
    the new passage."""
    p = _passage(TEXT)
    ok, info = _check(tex=TEXT.replace(p, "") + "\n\n" + p + "\n")
    assert not ok, "a new paragraph would escape the assembly the row belongs to"
    assert info["in_paragraph"] is False and not info["missing"]


def test_deleting_the_passage_fails():
    """TRACE: with the passage gone, ten lits (both_anchors, roots_pair, e3_bar,
    cut_additive, cut_production, where_it_lands, censoring_share,
    never_truncates, dominates_no_less, placement) go missing, i_add becomes -1
    so `ordered` is False, and in_paragraph is False. run_tag survives, because
    the tag is also in the tab:assembly row and in tab:runindex -- which is why
    run_tag alone was never allowed to stand for the passage."""
    ok, info = _check(tex=TEXT.replace(_passage(TEXT), ""))
    assert not ok
    assert "both_anchors" in info["missing"] and info["ordered"] is False


# --------------------------------------------------------------------------
# Every pinned span, one at a time. The comment on each names the single check
# it kills; all were simulated, and none is absorbed by another span.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("phrase", [
    # -> both_forms_biased. The scope lives in ONE sentence now, not two.
    "documents an upward bias under both forms",
    # -> production_scoped. Without it the retained verdict reads as unscoped
    #    and becomes false the moment the additive re-solve is stated.
    "under the production form the corrected member lies below the headline",
    # -> intro_counterpart (spec Branch A's V.E introducing sentence).
    "re-solved under the additive form, the calibrated companion below moves it up instead",
    # -> counterweight_pointer AND i_ctr = -1, so `ordered` goes False too.
    "the housing-activity calibration below, re-solved under that form, joins them",
    # -> closing_scoped. +8.5 is INSIDE the interval; the old closing clause
    #    ("counterweights sit above it") is false once it is filed with them.
    "the form-side counterweights sit at its top or above it",
    # -> max_pair. Pins the PRE-EXISTING production pair as a clause. A bare
    #    "$+0.9$" would have been satisfied by "$+0.9$ to $+15.6$" at .tex:361
    #    and a bare "$+3.5$" by the "$+3.5$ to $+13.1$" hull.
    "the marginal at $+0.9$ points at the headline floor and $+3.5$ at the in-sample calibration",
    # -> roots_pair. Scoped to the headline floor: at the 4.0% anchor the two
    #    roots coincide at 0.75625, so the pair is a 4.991%-only statement.
    "$\\phi^{*} = 0.756$ against $0.754$ at the headline floor",
    # -> both_anchors. "at both anchors" is a claim; the gate re-derives it.
    "$+8.5$ points at both anchors",
    # -> e3_bar. E3 was a genuine pre-commitment and it held; the bar is quoted.
    "clearing the $+4.0$-point bar fixed before the run",
    # -> cut_additive. A bare "$+11.2$" was already satisfied by the
    #    tab:uncertainty note at .tex:474.
    "cuts the additive form's own $+11.2$ to $+8.5$",
    # -> cut_production. A bare "$+5.6$" was satisfied at 27 other sites.
    "the production form's $+5.6$ to $+0.9$",
    # -> where_it_lands. The clause that does NOT contradict the sentence above
    #    it: production is below the HEADLINE at both anchors, and the interval
    #    split stays with the sentence that owns it.
    "above the headline at both anchors and near the top of the quoted interval under the additive form",
    # -> censoring_share. Pinned with its clause, because "94.4" alone would
    #    survive next to gate #98's own 68.8%/36.3% share sentence.
    "pinned to the floor in 94.4\\% of evaluated loan-months and the maximum truncates",
    # -> never_truncates. The bare words "survival scale" already occur once at
    #    .tex:746, which is why the lit is the longer clause.
    "combines the two hazards on the survival scale",
    # -> dominates_no_less. The claim the bind comparison licenses.
    "dominates no less often at the additive root",
    # -> placement AND in_paragraph (the sentence is half of in_paragraph).
    "belongs with the counterweights above rather than with the ladder",
    # -> row_both_numbers. THE hole the verifier found in the first draft:
    #    deleting this cell used to leave the gate green, because
    #    row_form_conditional survived and "$+0.9$"/"$+8.5$" survived in prose.
    "$+0.9$ (max) / $+8.5$ (additive)",
    # -> row_vs_cell. The header is "vs.\\ $+5.6$", so a bare "above" would have
    #    mixed referents inside one cell.
    "below the interval / above the headline",
    # -> row_form_conditional. "form-conditional" survives at 12 other sites, so
    #    the cross-check that wants count >= 3 is unaffected by this mutation.
    "form-conditional scaled-null variant; upward-bias entry under both forms",
    # -> row_roots.
    "roots $\\phi^{*} = 0.754$ and $0.756$ at the headline floor",
    # -> run_tag (3 sites: prose, tab:assembly, tab:runindex; all removed).
    "\\texttt{scaled\\_null\\_housing\\_activity\\_additive}",
])
def test_each_pinned_phrase_bites(phrase):
    assert phrase in TEXT, f"{phrase!r} missing from the manuscript (vacuous mutation)"
    ok, info = _check(tex=TEXT.replace(phrase, ""))
    assert not ok, f"{phrase!r} is not pinned: {info}"


# --------------------------------------------------------------------------
# The run may not certify itself.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("floor", ["4", "4.991"])
def test_drifted_additive_marginal_fails(floor):
    """TRACE: +0.2 carries the anchor to 8.72 / 8.69, both printing 8.7, so
    `floor_invariant` fails at the 4.0% anchor and both_anchors / cut_additive /
    row_both_numbers fail at the 4.991% one. Either way red against unmoved tex."""
    d = copy.deepcopy(A)
    d["roots_additive"][floor]["marginal_pp"] += 0.2
    assert not _check(a=d)[0]


def test_drifted_additive_root_fails():
    """TRACE: 0.72 -> roots_pair looks for '0.720 against 0.754' and row_roots
    for 'and $0.720$'; neither is in the tex."""
    d = copy.deepcopy(A)
    d["roots_additive"]["4.991"]["phi_star"] = 0.72
    assert not _check(a=d)[0]


def test_no_root_fails():
    """TRACE: roots_ok short-circuits on no_root. A landing may not survive its
    own no-root -- that is Branch C, and it reads differently on the page."""
    d = copy.deepcopy(A)
    d["roots_additive"]["4.991"]["no_root"] = True
    assert not _check(a=d)[0]


def test_unconverged_fails():
    """TRACE: roots_ok requires converged on BOTH floors; this flips the 4.0% one."""
    d = copy.deepcopy(A)
    d["roots_additive"]["4"]["converged"] = False
    assert not _check(a=d)[0]


def test_residual_outside_tolerance_fails():
    """TRACE: |0.5| > tolerance_b 0.05, so roots_ok is False."""
    d = copy.deepcopy(A)
    d["roots_additive"]["4.991"]["residual_b"] = 0.5
    assert not _check(a=d)[0]


@pytest.mark.parametrize("block,key", [
    ("P1_additive_endpoint_parity", "4.991|0"),
    ("P1_additive_endpoint_parity", "4|6.5"),
    ("P2_max_form_parity", "4.991|6.5"),
])
def test_parity_false_fails(block, key):
    """TRACE: parity_ok is an `all` over both blocks; one False cell sinks it.
    P1 is E1, the STOP-class tie to the committed additive endpoints."""
    d = copy.deepcopy(A)
    d["parity_gates"][block][key]["pass"] = False
    assert not _check(a=d)[0], "a landing may not survive its own parity failure"


def test_form_not_restored_fails():
    """TRACE: P4 restored is asserted `is True`; False sinks parity_ok. An
    unrestored floor form would contaminate every later run in the tree."""
    d = copy.deepcopy(A)
    d["parity_gates"]["P4_restoration_and_bind_anchor"]["restored"] = False
    assert not _check(a=d)[0]


def test_e2_false_fails():
    d = copy.deepcopy(A)
    d["expectations"]["E2_root_exists_both_floors"] = False
    assert not _check(a=d)[0]


def test_e3_false_fails():
    d = copy.deepcopy(A)
    d["expectations"]["E3_pass"] = False
    assert not _check(a=d)[0]


def test_e3_bar_is_derived_from_the_artifact():
    """TRACE: the printed bar is f"$+{E3_bar_pp:.1f}$"; moving it to 5.0 makes
    the e3_bar lit look for '$+5.0$-point bar', which is not in the tex. The
    quoted pre-commitment cannot drift away from the one that was recorded."""
    d = copy.deepcopy(A)
    d["expectations"]["E3_bar_pp"] = 5.0
    assert not _check(a=d)[0]


# --------------------------------------------------------------------------
# The comparator is the COMMITTED max run -- by value and by bytes.
# --------------------------------------------------------------------------
def test_comparator_is_the_committed_max_run():
    """TRACE: the additive artifact carries its own copy of the max-form root.
    The gate reads the committed run for every printed max literal and checks
    the copy against it to 1e-12, so a divergence in the copy alone (the tex is
    untouched, every lit still passes) must still fail -- via `tie`."""
    d = copy.deepcopy(A)
    d["committed_max_form"]["4.991"]["marginal_pp"] = 8.4
    ok, info = _check(a=d)
    assert not ok, f"the cross-artifact tie is not live: {info}"
    assert info["cross_artifact_tie"] is False and not info["missing"]


def test_comparator_sha_pin_is_live():
    """TRACE: max_bytes is hashed and compared to the additive run's own P0 pin
    for hazard/data/scaled_null_housing_activity_results.json. Feeding stale
    bytes leaves every lit, the tie (mx is unchanged) and every artifact check
    green, so `comparator_sha_ok` is the sole bite."""
    ok, info = _check(mb=b'{"stale": true}')
    assert not ok
    assert info["comparator_sha_ok"] is False and info["cross_artifact_tie"] is True


def test_the_printed_bind_share_is_derived():
    """TRACE: 94.4% must come out of the max artifact, not out of the gate. Both
    the committed run and the additive run's copy are moved to 0.9001 so `tie`
    still holds; the censoring_share lit then looks for '90.0\\%' and fails."""
    d, m = copy.deepcopy(A), copy.deepcopy(MX)
    m["root"]["4.991"]["floor_bind_share"] = 0.9001
    d["committed_max_form"]["4.991"]["floor_bind_share"] = 0.9001
    ok, info = _check(a=d, mx=m)
    assert not ok, "the censoring share is a literal, not a derivation"
    assert "censoring_share" in info["missing"]


def test_dominating_no_less_often_is_live():
    """TRACE: nothing PRINTS the additive bind share (94.8% already denotes the
    null leg's 100-PSA recovery share in this paragraph), so the only thing
    holding the 'dominates no less often' clause honest is the comparison
    0.9480 >= 0.9444. Dropping it to 0.80 leaves every lit green and must still
    fail -- via `no_less_often`."""
    d = copy.deepcopy(A)
    d["roots_additive"]["4.991"]["floor_bind_share"] = 0.80
    ok, info = _check(a=d)
    assert not ok, "the 'no less often' clause must be tied to the two artifacts"
    assert not info["missing"]


def test_the_in_sample_max_marginal_is_derived():
    """TRACE: the +3.5 in the retained sentence comes from the committed max run.
    Move it (and the copy, so `tie` holds) to 3.9 and max_pair fails."""
    d, m = copy.deepcopy(A), copy.deepcopy(MX)
    m["root"]["4"]["marginal_pp"] = 3.9
    d["committed_max_form"]["4"]["marginal_pp"] = 3.9
    ok, info = _check(a=d, mx=m)
    assert not ok and "max_pair" in info["missing"]


def test_the_max_root_is_derived():
    """TRACE: 0.754 appears in the prose pair and in the tab:assembly row; moving
    the committed root (and the copy) to 0.70 kills roots_pair and row_roots."""
    d, m = copy.deepcopy(A), copy.deepcopy(MX)
    m["root"]["4.991"]["phi_star"] = 0.70
    d["committed_max_form"]["4.991"]["phi_star"] = 0.70
    ok, info = _check(a=d, mx=m)
    assert not ok and {"roots_pair", "row_roots"} <= set(info["missing"])


def test_the_additive_phi1_leg_is_derived():
    """TRACE: the +11.2 the calibration cuts FROM is the additive run's own
    phi=1 leg; moving it to 12.0 kills cut_additive."""
    d = copy.deepcopy(A)
    d["roots_additive"]["4.991"]["additive_marginal_at_phi1_pp"] = 12.0
    ok, info = _check(a=d)
    assert not ok and "cut_additive" in info["missing"]


def test_the_production_phi1_leg_is_derived():
    """TRACE: the +5.6 the calibration cuts FROM is the committed max run's
    ladder cell at phi=1, not the headline literal; moving it kills
    cut_production even though '$+5.6$' still occurs 27 times in the file."""
    m = copy.deepcopy(MX)
    m["ladder"]["4.991|1"]["marginal_pp"] = 6.0
    ok, info = _check(mx=m)
    assert not ok and "cut_production" in info["missing"]


# --------------------------------------------------------------------------
# What the prose claims, re-derived here rather than trusted.
# --------------------------------------------------------------------------
def test_both_anchors_agree_to_the_printed_decimal():
    lo = A["roots_additive"]["4"]["marginal_pp"]
    hi = A["roots_additive"]["4.991"]["marginal_pp"]
    assert f"{lo:.1f}" == f"{hi:.1f}" == "8.5"
    assert abs(lo - hi) < 0.1


def test_the_additive_member_is_inside_the_binding_interval():
    """The prose says 'near the top of the quoted interval', never above it: the
    member is 8.4912 against an upper edge of 8.7."""
    assert 2.9 < A["roots_additive"]["4.991"]["marginal_pp"] < 8.7
    assert A["roots_additive"]["4.991"]["marginal_pp"] > (2.9 + 8.7) / 2


def test_the_collapse_is_form_specific():
    """E3's substance: the max form's +0.90 does not survive the form switch."""
    assert MX["root"]["4.991"]["marginal_pp"] < 1.0
    assert (A["roots_additive"]["4.991"]["marginal_pp"]
            > A["expectations"]["E3_bar_pp"])


def test_the_calibration_cuts_both_forms():
    """The row stays an upward-bias entry under BOTH forms, which is what lets
    the retained sentence carry the scope once."""
    r5 = A["roots_additive"]["4.991"]
    assert r5["marginal_pp"] < r5["additive_marginal_at_phi1_pp"]
    assert MX["root"]["4.991"]["marginal_pp"] < MX["ladder"]["4.991|1"]["marginal_pp"]


def test_the_root_barely_moves_at_the_headline_floor():
    """'barely moves the root' is the claim; 0.756 against 0.754. E4 recorded the
    DIRECTION as deliberately unpredicted, which is why the prose reports the
    move and says so rather than scoring it."""
    assert abs(A["roots_additive"]["4.991"]["phi_star"]
               - MX["root"]["4.991"]["phi_star"]) < 0.01


def test_the_two_roots_coincide_at_the_in_sample_anchor():
    """At the 4.0% anchor the two forms land on the SAME root, so '0.756 against
    0.754' is a 4.991%-only statement. Both the prose and the tab:assembly row
    say 'at the headline floor'; this test is why a later pass may not quietly
    restate the pair as holding at both anchors."""
    assert A["roots_additive"]["4"]["phi_star"] == MX["root"]["4"]["phi_star"]
    assert "$0.756$ at the headline floor" in TEXT


def test_tag_counting_is_prefix_safe():
    """The additive tag contains the max tag as a STEM; closing the brace is what
    keeps a max-tag count from silently absorbing the additive sites. No gate
    counts either tag today, but the next one to try will get this wrong."""
    assert MAX_TAG not in ADD_TAG
    # Two sites, not three: the tab:assembly row's own run credit was dropped
    # when the rebuild showed the grown row pushed that page 4.48pt over an
    # overfull \vbox. The credit was the most redundant part of the cell -- the
    # run is cited in the §V.E prose and carries its own tab:runindex row -- and
    # gate #118's run_tag conjunct is a whole-file presence check, so it still
    # sees both. The counts stay pinned so the next pass notices if a site moves.
    assert TEXT.count(ADD_TAG) == 2 and VARIANT.count(ADD_TAG) == 2
    assert TEXT.count(MAX_TAG) == 4 and VARIANT.count(MAX_TAG) == 4
