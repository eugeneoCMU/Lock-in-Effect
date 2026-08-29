"""Battery for gate #115 (R32 C-72: the month and two-way cluster rungs).

This exhibit's failure mode is a half-truth that reads as a clean answer.
"Month clustering widens the ladder" is true and, alone, misdescribes the run:
the month-clustered standard error came in SMALLER, so that rung widens on its
six-cluster reference distribution. State only that and the note reads as
"the month-level shock does not matter" -- one clause away from a two-way rung
whose standard error is 16% LARGER than the stratum one. So the tests bind
hardest on the sentences that argue against a clean confirmation (the
priced-not-dismissed lead, the two opposite standard-error facts, the E3
attribution that credits the specification rather than claiming a discovery,
the E4 miss, E5's unpredicted computability) and on the four counting claims
the landing moves or must leave standing.

Every mutation below was traced by hand and then executed against the check
before it was written down; the trace is in the docstring or comment.
"""
import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import (  # noqa: E402
    FLOOR_LADDER_READ,
    _MONTH_VARIANTS,
    month_twoway_clusters_check,
)

TEX = (ROOT / "paper" / "final" / "paper_final_v1.tex").read_text()
VARIANT = (ROOT / "paper" / "final"
           / "paper_final_v1_long_abstract.tex").read_text()
V2 = json.loads((ROOT / "hazard" / "data"
                 / "floor_inference_correction_v2_results.json").read_text())
V3 = json.loads((ROOT / "hazard" / "data"
                 / "floor_inference_correction_v3_results.json").read_text())

_OK, _INFO = month_twoway_clusters_check(TEX, V2, V3)
LITS = _INFO["lits"]
RD = V2["reads"][FLOOR_LADDER_READ]
MO = V3["rungs"]["month"]
TW = V3["two_way"]


def test_gate_passes_on_the_manuscript():
    assert _OK, f"gate #115 fails on the shipped manuscript: {_INFO['missing']}"


def test_variant_carries_it():
    ok, info = month_twoway_clusters_check(VARIANT, V2, V3)
    assert ok, f"gate #115 fails on the long-abstract variant: {info['missing']}"


@pytest.mark.parametrize("key", sorted(LITS))
def test_each_literal_removal_fails(key):
    """TRACE: every literal is checked by `v not in tex_nc -> missing`, so
    deleting all its occurrences forces missing != [] and ok=False. The
    `span in TEX` guard is what makes the mutation non-vacuous; run_credit_v3
    occurs three times (caption, note, run index) and all three go."""
    span = LITS[key]
    assert span in TEX, f"literal {key!r} absent (vacuous mutation)"
    ok, _ = month_twoway_clusters_check(TEX.replace(span, ""), V2, V3)
    assert not ok, f"gate #115 survives removal of {key!r}"


@pytest.mark.parametrize("printed,perturbed,n_sites", [
    # TRACE for every row: the perturbed string breaks the derived literal
    # named in the comment, so that key enters `missing` and ok=False.
    ("$+3.1$ to $+8.4$", "$+3.2$ to $+8.4$", 1),            # month_row
    ("$+2.3$ to $+9.3$", "$+2.3$ to $+9.4$", 1),            # two_way_row
    ("from 5.20 to 5.33 points of width",
     "from 5.20 to 5.34 points of width", 1),                # e3_widths
    ("18\\% \\emph{smaller}", "19\\% \\emph{smaller}", 1),  # se_shrinks
    ("16\\% \\emph{above}", "17\\% \\emph{above}", 1),      # se_grows_twoway
    ("$2^{6} = 64$", "$2^{6} = 32$", 1),                    # nc4_sign_vectors
    ("$1/64$", "$1/32$", 1),                                # nc4_floor
    ("degrees of freedom is 3.9",
     "degrees of freedom is 4.9", 1),                       # month_bm_below_four
    ("$\\min(G)-1 = 5$", "$\\min(G)-1 = 6$", 1),            # two_way_df
    ("the 137 cohort-months", "the 136 cohort-months", 1),  # note_month_unit
    ("clustered on the 31 strata",
     "clustered on the 32 strata", 1),                      # note_two_way_unit
    ("their 137 intersection cells",
     "their 138 intersection cells", 1),                    # note_two_way_unit
    ("two July cohort-months aside",
     "three July cohort-months aside", 1),                  # july_tail_disclosure
    # V20-N1: the rank phrase is retired; the two-site literal is now the
    # qualifying-rung-beside claim of the frozen-rule adjudication.
    ("the other qualifying rung, stands beside",
     "the other qualifying rung, sits beside", 2),           # widest_interior
])
def test_a_wrong_digit_fails(printed, perturbed, n_sites):
    assert TEX.count(printed) == n_sites, \
        f"{printed!r} occurs {TEX.count(printed)} times, expected {n_sites}"
    ok, _ = month_twoway_clusters_check(TEX.replace(printed, perturbed), V2, V3)
    assert not ok, f"gate #115 survives {printed!r} -> {perturbed!r}"


def test_the_rank_claim_is_made_at_both_sites():
    """The Webb row's rank is stated at .tex:361 and .tex:501. A landing that
    repaired one site and not the other is precisely the defect this gate
    exists to catch, and no gate before #115 would have caught it.

    TRACE: deleting ONE occurrence leaves the literal present (so `missing`
    stays empty) but drops the count to 1, and the count == 2 conjunct fails.
    """
    # V20-N1: the two-site claim is now LITS["widest_interior"].
    assert TEX.count(LITS["widest_interior"]) == 2
    ok, _ = month_twoway_clusters_check(
        TEX.replace(LITS["widest_interior"], "", 1), V2, V3)
    assert not ok, "one repaired site and one deleted site passes the gate"


def test_a_reverted_rank_phrase_anywhere_fails():
    """TRACE: reverting one site to 'third-narrowest of the nine undemoted
    rungs' leaves the correct literal at the other site, so `missing` is empty
    and count == 2 fails (count is 1); the residual-'undemoted rungs' conjunct
    also fires, because stripping the correct phrase leaves the stale one."""
    stale = TEX.replace(LITS["webb_rank"],
                        "the third-narrowest of the nine undemoted rungs", 1)
    ok, _ = month_twoway_clusters_check(stale, V2, V3)
    assert not ok, "a reverted rank site survives the gate"


def test_the_refuted_attribution_cannot_return():
    """An earlier draft of this note claimed the widening came 'not through the
    channel that prediction named'. SPEC_R32_c72 §5 gives E3's rationale as
    '31 clusters drop to at most 12' -- the cluster-count channel, i.e. the one
    that delivered -- and pre-named the narrower-SE outcome as an allowed
    landing. Neither is a discovery, and the prose must not say otherwise.

    TRACE: swapping the credit clause for the refuted one removes
    e3_prediction_credit from the tex, so that key enters `missing`.
    """
    bad = TEX.replace(LITS["e3_prediction_credit"],
                      "but not through the channel that prediction named")
    ok, info = month_twoway_clusters_check(bad, V2, V3)
    assert not ok and "e3_prediction_credit" in info["missing"]


def test_the_censored_count_is_derived_from_the_artifacts():
    """Three of the eleven undemoted rungs are censored at the 6.0% edge, and
    all three are censored on the LOWER marginal edge only -- which is why all
    three print the same $+2.3$ and why the note says they run below it."""
    assert _INFO["n_censored"] == 3
    for c in (RD["cr3_t_interval_df_bm"], RD["wcr_inverted"], TW["t_interval"]):
        assert c["lower_pp_edge"]["truncated_at_grid_edge"] is True
        assert c["upper_pp_edge"]["truncated_at_grid_edge"] is False
        assert c["lower_pp_edge"]["mapped_at_pct"] == 6.0
        assert c["lower_pp_edge"]["floor_pct"] > 6.0
        assert c["marginal_ci95_pp"][0] == TW["t_interval"]["marginal_ci95_pp"][0]


def test_the_rungs_printed_wider_are_exactly_the_censored_ones():
    """The note's sentence is a set claim, not a count claim. Widths: cr2_bm
    6.739981 < restricted 6.828409 < two_way 7.058133 < cr3_bm 7.283615, and
    those three are exactly the censored set.

    TRACE: narrowing the two-way rung to [3.5, 8.0] (width 4.5) leaves it
    censored but drops it out of printed_wider, so printed_wider (2 members)
    != censored_set (3 members) and ok=False, while n_censored stays 3.
    """
    d = copy.deepcopy(V3)
    d["two_way"]["t_interval"]["marginal_ci95_pp"] = [3.5, 8.0]
    ok, info = month_twoway_clusters_check(TEX, V2, d)
    assert not ok and info["n_censored"] == 3


def test_the_widest_interior_rung_is_unmoved_by_this_landing():
    """The note keeps calling CR2 at Bell--McCaffrey df the widest rung with
    both endpoints interior. The month rung is the one that could have
    falsified that, so the comparison is made explicitly and the guard is
    exercised.

    TRACE: widening the month rung to [1.0, 9.0] (width 8.0, interior on both
    edges) makes it the widest interior rung, so widest_interior becomes
    'month_cr1' and the == 'cr2_bm' conjunct fails.
    """
    assert _INFO["widest_interior"] == "cr2_bm"
    m = MO["cr1_t_interval"]["marginal_ci95_pp"]
    c = RD["cr2_t_interval_df_bm"]["marginal_ci95_pp"]
    assert (m[1] - m[0]) < (c[1] - c[0])
    d = copy.deepcopy(V3)
    d["rungs"]["month"]["cr1_t_interval"]["marginal_ci95_pp"] = [1.0, 9.0]
    ok, info = month_twoway_clusters_check(TEX, V2, d)
    assert not ok and info["widest_interior"] == "month_cr1"


def test_e3_widened_but_the_month_standard_error_shrank():
    """Half the finding: the month rung widens on degrees of freedom while its
    standard error comes in SMALLER."""
    e3 = V3["expectations"]
    assert e3["E3_month_widens"] is True
    assert e3["E3_month_cr1_width_pp"] > e3["E3_committed_cr1_width_pp"]
    assert MO["se_cr1_smm"] < RD["se_cr1_smm"]
    assert MO["t_crit_G_minus_1"] > RD["t_crit_G_minus_1"]
    # held at the committed df, the month rung would have been NARROWER
    assert (MO["se_cr1_smm"] * RD["t_crit_G_minus_1"]
            < RD["se_cr1_smm"] * RD["t_crit_G_minus_1"])


def test_the_two_way_standard_error_is_larger_not_smaller():
    """The other half, and the one a 'the shock does not matter' reading
    suppresses: clustering on both margins at once raises the variance by a
    third (V_2way / V_stratum = 1.340) and the standard error by 16%."""
    assert TW["se_2way_smm"] > RD["se_cr1_smm"]
    assert round((TW["se_2way_smm"] / RD["se_cr1_smm"] - 1) * 100) == 16
    assert abs(RD["se_cr1_smm"] ** 2 - TW["V_stratum"]) < 1e-20
    assert TW["V_2way"] > TW["V_stratum"]
    # and both new rungs are wider than the CR1 rung they re-cluster
    cr1 = RD["cr1_t_interval"]["marginal_ci95_pp"]
    for c in (MO["cr1_t_interval"], TW["t_interval"]):
        w = c["marginal_ci95_pp"]
        assert (w[1] - w[0]) > (cr1[1] - cr1[0])


def test_a_shrunken_two_way_se_fails_the_gate():
    """TRACE: setting se_2way_smm = 0.0002 makes grow_pct =
    round((0.0002/0.0003053670536820312 - 1)*100) = -35, so the derived literal
    becomes '-35\\% \\emph{above} the stratum-clustered one', which is not in
    the tex -> se_grows_twoway enters `missing`; the
    se_2way_smm > se_cr1_smm conjunct fails independently."""
    d = copy.deepcopy(V3)
    d["two_way"]["se_2way_smm"] = 0.0002
    ok, info = month_twoway_clusters_check(TEX, V2, d)
    assert not ok and "se_grows_twoway" in info["missing"]


def test_e4_missed_and_the_manuscript_says_so():
    assert V3["expectations"]["E4_upper_endpoint_truncates"] is False
    for edge in ("lower_pp_edge", "upper_pp_edge"):
        assert MO["cr1_t_interval"][edge]["truncated_at_grid_edge"] is False
    assert TW["t_interval"]["lower_pp_edge"]["truncated_at_grid_edge"] is True
    assert LITS["e4_miss"] in TEX


def test_only_the_unprinted_rademacher_month_variant_censors():
    """The miss statement is scoped to the PRINTED row for a reason: the month
    rung's Rademacher variant does reach past 6.0% (floor 6.141792853297579).
    If any other month-axis variant started truncating, 'Among the month rung's
    own variants only the unprinted Rademacher one' would go stale.

    TRACE: flagging cr2_t_interval's lower edge truncated makes the derived
    list ['cr2_t_interval', 'wild_t_rademacher'] != ['wild_t_rademacher'].
    """
    trunc = [k for k in _MONTH_VARIANTS
             if MO[k]["lower_pp_edge"]["truncated_at_grid_edge"]
             or MO[k]["upper_pp_edge"]["truncated_at_grid_edge"]]
    assert trunc == ["wild_t_rademacher"]
    assert MO["wild_t_rademacher"]["lower_pp_edge"]["floor_pct"] > 6.0
    d = copy.deepcopy(V3)
    d["rungs"]["month"]["cr2_t_interval"]["lower_pp_edge"][
        "truncated_at_grid_edge"] = True
    ok, _ = month_twoway_clusters_check(TEX, V2, d)
    assert not ok


def test_nc4_is_the_artifacts_own_resolution_floor():
    r = MO["wild_t_rademacher"]
    assert r["distinct_sign_vectors"] == 2 ** V3["feasibility"]["G_month"]
    assert abs(r["resolution_floor_p"] - 1 / 64) < 1e-15
    assert r["NC4_resolution_disclosure"] is True
    assert V3["not_computable"][
        "NC4_rademacher_resolution_floor"]["triggered"] is True
    # and the stratum leg, at 31 clusters, carries no such floor
    assert V3["rungs"]["stratum_committed"]["wild_t_rademacher"][
        "NC4_resolution_disclosure"] is False


def test_the_month_bm_df_is_below_the_rules_own_threshold():
    """NC-1's stated rationale for stopping at G < 5 is that Bell--McCaffrey df
    would then be below 4. The trigger did not fire (G = 6) but the substantive
    threshold was crossed anyway (3.9301121142080606 < 4), and the note says so.

    TRACE: raising df_bm_by_estimator.cr1 to 4.5 rewrites the derived literal
    to 'is 4.5, below the four ...', which is not in the tex, and also fails
    the df < threshold - 1 conjunct.
    """
    thr = V3["not_computable"]["NC1_too_few_month_clusters"]["threshold"]
    assert thr == 5
    assert MO["df_bm_by_estimator"]["cr1"] < thr - 1
    assert V3["not_computable"][
        "NC1_too_few_month_clusters"]["triggered"] is False
    d = copy.deepcopy(V3)
    d["rungs"]["month"]["df_bm_by_estimator"]["cr1"] = 4.5
    ok, info = month_twoway_clusters_check(TEX, V2, d)
    assert not ok and "month_bm_below_four" in info["missing"]


def test_the_july_disclosure_is_the_supports_own():
    """Section V.E says the 2018 leg is read in August--December; the read in
    fact populates six months, July first with two cohort-months. The landing
    reconciles them, and the reconciliation is the artifact's.

    TRACE: filling 201807 to 30 cohort-months makes 201808 (24) the sparse
    month, so the derived literal names August rather than July and enters
    `missing`; the order-of-magnitude conjunct fails too.
    """
    cmpm = V3["feasibility"]["cohort_months_per_month"]
    assert list(cmpm) == V3["feasibility"]["months"]
    assert cmpm["201807"] == 2
    assert sum(cmpm.values()) == MO["n_cohort_months"] == 137
    assert cmpm["201807"] * 10 < min(v for k, v in cmpm.items()
                                     if k != "201807")
    d = copy.deepcopy(V3)
    d["feasibility"]["cohort_months_per_month"]["201807"] = 30
    ok, info = month_twoway_clusters_check(TEX, V2, d)
    assert not ok and "july_tail_disclosure" in info["missing"]


def test_the_stratum_rungs_replayed_bit_identically():
    """E1: v3's stratum leg must reproduce v2's R2 rungs exactly, or the run is
    an environment alarm and nothing it printed is quotable."""
    p = V3["parity"]["P1_stratum_rung_replays_v2"]
    for k in ("cr1_t_interval", "cr1_t_interval_df_bm", "cr3_t_interval",
              "wild_t_webb_floor_ci95_pct"):
        assert p[k]["exact"] is True
        assert p[k]["got"] == p[k]["want"]
    assert (p["df_bm_by_estimator"]["got"]
            == p["df_bm_by_estimator"]["want"] == RD["df_bm_by_estimator"])
    assert V3["rungs"]["stratum_committed"]["se_cr1_smm"] == RD["se_cr1_smm"]


def test_the_month_rung_really_clustered_on_months():
    """P3: the cluster substitution is visible, and the read is unchanged."""
    assert MO["cluster_column_grouped_on"] == "month"
    assert MO["n_clusters"] == 6 == len(V3["feasibility"]["months"])
    assert MO["cluster_labels"] == V3["feasibility"]["months"]
    assert MO["n_cohort_months"] == RD["n_cohort_months"] == 137
    assert abs(MO["point_cpr_pct"] - RD["point_cpr_pct"]) < 1e-12


def test_the_two_way_variance_is_positive_and_was_not_truncated_to_zero():
    """NC-2 did not fire; the zero-truncation fix was refused, not applied.
    E5 recorded computability as unpredicted, and the note says so rather than
    presenting it as a result."""
    assert TW["V_2way"] > 0
    assert abs(TW["V_2way"] - (TW["V_stratum"] + TW["V_month"]
                               - TW["V_intersection"])) < 1e-18
    assert TW["df_2way"] == min(TW["G_stratum"], TW["G_month"]) - 1 == 5
    assert TW["G_intersection_cells"] == MO["n_cohort_months"]
    assert V3["not_computable"][
        "NC2_two_way_variance_non_positive"]["triggered"] is False
    assert V3["expectations"][
        "E5_two_way_computability_not_predicted"] is True


def test_a_drifted_artifact_fails_against_the_unmoved_tex():
    """TRACE: +0.5 on the month rung's upper endpoint reprints the cell as
    '$+3.1$ to $+8.9$', so month_row enters `missing`."""
    d = copy.deepcopy(V3)
    d["rungs"]["month"]["cr1_t_interval"]["marginal_ci95_pp"][1] += 0.5
    ok, info = month_twoway_clusters_check(TEX, V2, d)
    assert not ok and "month_row" in info["missing"]


def test_a_wider_month_rung_would_break_the_rank_claim():
    """If the month rung stopped slotting between CR1 (5.196667) and CR2
    (5.578726), Webb's rank would move and both prose sites would go stale.

    TRACE: [2.0, 8.0] is width 6.0 -- ABOVE webb's 5.822977 and below cr3's
    6.001182 -- so Webb becomes third of eleven and the derived webb_rank
    literal stops matching. (A NARROWER mutation such as [4.0, 8.0] would not
    bite on the rank at all: at width 4.0 the month rung is still narrower than
    Webb, so webb_rank stays 4. That was the drafted test's defect.)
    """
    d = copy.deepcopy(V3)
    d["rungs"]["month"]["cr1_t_interval"]["marginal_ci95_pp"] = [2.0, 8.0]
    ok, info = month_twoway_clusters_check(TEX, V2, d)
    # V20-N1: the manuscript no longer prints a rank claim, so rank drift is
    # informational rather than gate-failing; the gate must still REPORT the
    # moved rank (fourth -> third of eleven).
    assert info["webb_rank"] == 3


def test_the_gate_goes_red_not_boom_on_an_out_of_range_count():
    """A gate that raises aborts every gate after it. TRACE: setting 201807 to
    24 cohort-months puts the cardinal-word lookup out of the 1--12 table;
    _CARD falls back to '24', the literal stops matching, and the gate returns
    ok=False instead of KeyError."""
    d = copy.deepcopy(V3)
    d["feasibility"]["cohort_months_per_month"]["201807"] = 24
    ok, info = month_twoway_clusters_check(TEX, V2, d)
    assert not ok and "july_tail_disclosure" in info["missing"]
