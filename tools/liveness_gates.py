#!/usr/bin/env python3
"""
Liveness gates: manuscript-vs-artifact checks as a runnable script
(pre-submission freeze item (iii) mechanized; see TECHNICAL.md §22).

Exit 0 iff ALL gates pass; each gate prints PASS/FAIL. Four gate classes:

1. Zero-count greps — phrases that must be ABSENT from the manuscript
   (retired claims, superseded numbers, and stale framing; each phrase's
   retirement is recorded in TECHNICAL.md §12.1/§22.4 or the run ledger).
2. Exactly-one greps — sentences that must be PRESENT exactly once
   (the ratified title and load-bearing provenance sentences).
3. Manuscript-vs-manifest cross-checks — a claim in the tex and a flag in
   a frozen run manifest must agree; failing when either side flips
   without the other (the defect class a review round caught in the
   Danish counterfactual's description).
4. Abstract-scoped hedge spans — contiguous hedge-to-claim spans that must
   be PRESENT inside the abstract environment specifically, since the same
   phrases recur in the body and would satisfy a whole-file count on their
   own (the defect class that let three misattributed-projection abstracts
   pass this suite).

Run:  python3 tools/liveness_gates.py
"""
from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEX = ROOT / "paper" / "v18" / "revised_paper_v18.tex"
# ROUND 22 (C4): every manuscript variant on disk, not just the canonical one.
# paper/v18/revised_paper_v18_simple_abstract.tex was byte-identical to the
# canonical file except for its abstract, was UNTRACKED, and was therefore
# entirely ungated -- run against gate #68's shipped rule it failed with 5 of 8
# spans missing, silently reversing round 20's calibration-label discipline and
# round 21's Danish dual label. A variant that ships is a variant that must be
# checked, so the abstract gate is applied to all of them.
TEX_VARIANTS = sorted((ROOT / "paper" / "v18").glob("revised_paper_v18*.tex"))
MANIFEST = ROOT / "abm" / "data" / "runs" / "run-2026-07-04-15yr-foldin" / "manifest.json"
FANNIE_RESULTS = ROOT / "hazard" / "data" / "fannie_replication_results.json"
OVERLAY_RESULTS = ROOT / "hazard" / "data" / "ginnie_cpr_overlay_results.json"
DECOMP_RESULTS = ROOT / "hazard" / "data" / "marginal_decomposition_results.json"
ABMEXT_RESULTS = ROOT / "abm" / "data" / "abm_external_gates_results.json"
EXPECT_RESULTS = ROOT / "hazard" / "data" / "expectation_benchmark_results.json"
VINTAGE_RESULTS = ROOT / "hazard" / "data" / "vintage_residual_bound_results.json"
THEIL_RESULTS = ROOT / "figures" / "theil_data.json"
MLCOMP_RESULTS = ROOT / "hazard" / "data" / "ml_comparator_holdout_results.json"
COMPSHIFT_RESULTS = ROOT / "hazard" / "data" / "composition_shift_results.json"
FREEZE_RESULTS = ROOT / "abm" / "data" / "freeze_sensitivity_results.json"
ISOTONIC_RESULTS = ROOT / "hazard" / "data" / "landmark_isotonic_results.json"
MARGMONTH_RESULTS = ROOT / "hazard" / "data" / "marginal_monthly_decomposition_results.json"
INTERP_RESULTS = ROOT / "abm" / "data" / "interp_spot_check_results.json"
SMD_RESULTS = ROOT / "abm" / "data" / "smd_two_moment_results.json"
WALTAB_RESULTS = ROOT / "hazard" / "data" / "wal_table_results.json"
WALNT_RESULTS = ROOT / "hazard" / "data" / "wal_normal_turnover_results.json"
WALNRB_RESULTS = ROOT / "hazard" / "data" / "wal_note_rate_basis_results.json"
SCCG_RESULTS = ROOT / "hazard" / "data" / "state_contingent_cap_grid_results.json"
MTC_RESULTS = ROOT / "hazard" / "data" / "marginal_transaction_counts_results.json"
DLS_RESULTS = ROOT / "hazard" / "data" / "depth_ladder_shape_results.json"
EPAGE_RESULTS = (ROOT / "hazard" / "data"
                 / "episode_gradient_age_bands_results.json")
ECWITHIN_RESULTS = (ROOT / "hazard" / "data"
                    / "episode_confrontation_within_results.json")
COUPONAMORT_RESULTS = (ROOT / "hazard" / "data"
                       / "coupon_convention_amortization_results.json")
CURTDEMO_RESULTS = ROOT / "hazard" / "data" / "curtailment_profile_demo_results.json"
SPREADVAR_RESULTS = ROOT / "hazard" / "data" / "expectation_spread_variants_results.json"
DANBOUND_RESULTS = ROOT / "hazard" / "data" / "danish_discount_bound.json"
SUBGROUP_RESULTS = ROOT / "hazard" / "data" / "subgroup_marginals_results.json"
REGIME_RESULTS = ROOT / "hazard" / "data" / "regime_split_marginal_results.json"
GROUPCAL_RESULTS = ROOT / "hazard" / "data" / "grouped_calibration_results.json"
FONSECA_RESULTS = ROOT / "hazard" / "data" / "fonseca_band_anchor_results.json"
V1516_RESULTS = ROOT / "hazard" / "data" / "vintage_1516_subleg_results.json"
DTI_RESULTS = ROOT / "abm" / "data" / "dti_threshold_sweep_results.json"
COHORTTIMING_RESULTS = ROOT / "abm" / "data" / "cohort_timing_diagnostic_results.json"
OOWFLOOR_RESULTS = ROOT / "hazard" / "data" / "out_of_window_floor_results.json"
OOSIDENT_RESULTS = ROOT / "hazard" / "data" / "oos_identification_results.json"
SEASFLOOR_RESULTS = ROOT / "hazard" / "data" / "seasonal_floor_timing_results.json"
B3TIMING_RESULTS = ROOT / "hazard" / "data" / "b3_timing_scores.json"
FCPERM_RESULTS = ROOT / "hazard" / "data" / "floor_cyclical_permutation_results.json"
SUBPLACEBO_RESULTS = ROOT / "hazard" / "data" / "subgroup_marginals_placebo_results.json"
SYNTHNULL_RESULTS = ROOT / "hazard" / "data" / "synthetic_companion_null_results.json"
PATHAPERM_RESULTS = ROOT / "hazard" / "data" / "pathA_seasonal_permutation_results.json"
SYNTHCOMP_RESULTS = ROOT / "hazard" / "data" / "synthetic_companion_results.json"
PATHAADOPT_RESULTS = ROOT / "hazard" / "data" / "pathA_seasonal_adoption_results.json"
SEASGAP_RESULTS = ROOT / "hazard" / "data" / "seasonality_concave_gap_results.json"
# The dollar benchmark, read from a THIRD module's artifact so that gates
# #60/#61/#62 can check each artifact's own share/level arithmetic against a
# number none of them wrote. Without this, share_pct and trapped_b can be
# moved together inside one artifact and stay mutually consistent while
# denoting a different quantity than the one the manuscript reports.
EXTRISK_RESULTS = ROOT / "hazard" / "data" / "extension_risk_results.json"
# Independently-produced artifacts used ONLY as cross-ties in gates #58/#59:
# each is written by a different module than the one under test, so agreement
# between them cannot be manufactured by the module being checked.
NULL_RESULTS = ROOT / "hazard" / "data" / "no_lockin_null_results.json"
FLOORSWEEP_RESULTS = ROOT / "hazard" / "data" / "floor_sweep_results.json"
FLOORFORM_RESULTS = ROOT / "hazard" / "data" / "floor_form_results.json"
FLOORCYC_RESULTS = ROOT / "hazard" / "data" / "floor_cyclical_results.json"
CALIBRECON_RESULTS = ROOT / "hazard" / "data" / "calibration_reconciliation_results.json"
SIGNSTATS_RESULTS = ROOT / "hazard" / "data" / "sign_forcing_stats_results.json"
PANEL_PATH = ROOT / "hazard" / "data" / "cohort_month_panel.parquet"
MATCHEDDEPTH_RESULTS = ROOT / "hazard" / "data" / "matched_depth_reconciliation_results.json"
# The monthly MORTGAGE30US series gate #65 rebuilds the discount-gap column
# from. It is written by b0_variance_decomposition.py -- a DIFFERENT module
# than the one under test -- so the rate history the depth ladder is cut on
# cannot be manufactured by matched_depth_reconciliation.py itself.
B0VAR_RESULTS = ROOT / "hazard" / "data" / "b0_variance_decomposition.json"
DANUSINT_RESULTS = ROOT / "hazard" / "data" / "danish_us_intercept_results.json"
BBCB_RESULTS = ROOT / "hazard" / "data" / "buyback_credit_bracket_results.json"
BDR_RESULTS = (ROOT / "hazard" / "data"
               / "buyback_discount_rederived_results.json")
DIOS_RESULTS = (ROOT / "hazard" / "data"
                / "danish_interest_only_share_results.json")
RBA_RESULTS = (ROOT / "hazard" / "data"
               / "realized_boundary_allocation_results.json")
BMR_RESULTS = (ROOT / "hazard" / "data"
               / "benchmark_monthly_rebuild_results.json")
# Gate #121/#122 cross-ties. SMB owns the two committed benchmarks C-128
# must reproduce; H1Z owns the four clip months and the ARTIFACT verdict
# C-127 strengthens; EXPECT owns the cap-relative benchmark both rest on.
# None is written by the run under test, so agreement cannot be faked
# from inside either new artifact.
SMB_RESULTS = (ROOT / "hazard" / "data"
               / "settlement_months_benchmark_results.json")
H1Z_RESULTS = ROOT / "hazard" / "data" / "h1_zero_months_diagnosis.json"
REFISWEEP_RESULTS = ROOT / "abm" / "data" / "refi_sweep_results.json"
SHAREDLAYER_RESULTS = ROOT / "hazard" / "data" / "shared_layer_scoring_results.json"
MARGDECOMP_RESULTS = ROOT / "hazard" / "data" / "marginal_decomposition_results.json"
EXPECT_RESULTS = ROOT / "hazard" / "data" / "expectation_benchmark_results.json"


def _gates_ok(gates: dict) -> bool:
    """True iff every in-run gate entry reports pass (dict with 'pass', bool, or nested)."""
    def one(v):
        if isinstance(v, dict):
            if "pass" in v:
                return bool(v["pass"])
            return all(one(x) for x in v.values())
        return bool(v)
    return all(one(v) for v in gates.values())

ZERO_COUNT = [
    "production specification omits",
    "never route the same loan-month",
    "behavioral gate is future work",
    "Two items are bound",
    "10.26",
    "stranding an estimated",
    "roughly 13\\% of the benchmark",
    "That mortgage lock-in slowed",
    "1.3 years too long",
    # Round-20 retractions. The first two are the false depth claim gate #65
    # replaces (the deep off-window cell EXISTS -- it is noise, not missing)
    # and the double-counting "three legs" phrasing (pooled_2017_2019 contains
    # both 2018 and 2019, so there are two independent legs). The third is the
    # forced sign-stability claim relabeled as an orientation check (B3).
    "no cohort reaches the two-point discount depth",
    "the off-window grid stops at half a point",
    "three independent legs",
    "stable in sign across both hazard specifications",
    # The Fannie replication must never be described as having failed; the
    # relabel narrows what its PASS demonstrates, it does not retract it.
    "does not replicate",
    # The Danish rule-only gap is 44% larger than the headline marginal, not
    # equal to it; the bare equality held only against the demoted in-sample point.
    "equal in size to the lock-in marginal",
    # Round-21 (panel minor, copyedit p21): the kernel sentence's "say
    # otherwise" attached to the wrong clause and read as the manifests
    # contradicting "not kernel-free". Sentence rewritten; ambiguous phrase
    # retired. The kernel-applied fact stays pinned via KERNEL_TEX_PHRASE and
    # the EXACTLY_ONE replacement below.
    "frozen manifests say otherwise",
    # Round-21 T3 (patha_sign_test): the bias-respecting test does not reject
    # H0: beta_g <= 0 under any construction, so the triangulation claim is
    # retired; the fits are "directionally consistent", nothing stronger.
    "sign-triangulated by two in-sample estimates",
    # Round-22 C1: the externally anchored variant's 150.6% WAS pre-committed to
    # the 50% band -- spec commit 335797a says it "is evaluated against the SAME
    # pre-registered bands", contains no admissibility precondition anywhere, and
    # pre-registered the floor diagnostic as reported "whichever direction it
    # moves"; the artifact records classification_external "undercuts_paradigm".
    # The exclusion formulation contradicted both and must not return. The
    # qualification may be kept, but only labelled as post hoc (enforced in the
    # external-gates cross-check above).
    "is not scored against the 50\\% undercutting band",
    "that band presupposed an empirically admissible turnover level",
    # R32 C-75: the four-point proxy grid is history, not the operative basis
    # the printed cash figure stands on. These three phrasings each said it was.
    "at the committed proxy discounts",
    "at the paper's own proxy discounts",
    "across the committed 32--38\\% discount grid",
]

EXACTLY_ONE = [
    "\\title{Mortgage Lock-In and the Composition of the Federal Reserve's Agency-MBS Runoff}",
    # Round-21 rewrite of the kernel sentence (replaces the retired
    # "frozen manifests say otherwise" pin above).
    "not kernel-free, and every figure reported here is the kernel-applied",
    "9.96\\% of home value",
    "against the fold-in specification's code",
]

KERNEL_TEX_PHRASE = "kernel is retained in production"

# --- Post-freeze consistency pass (2026-07-14) ------------------------------
# Superseded spec v3 figures that must stay out of the tex except where
# explicitly labeled, ledger-completeness checks, and figure-script
# hardcoded-literal gates (the defect class the pass existed to kill:
# figure generators must READ committed artifacts, never carry the numbers).

# "894.8" (the spec v3 composed Path A) may appear only within 120 chars of
# a "spec v3" label; the unlabeled form was the §VII.F defect.
SUPERSEDED_CONTEXTUAL = {"894.8": "spec v3"}

# The Appendix A run ledger must record the Path A spec v3 -> v4 supersession.
LEDGER_SECTION = "\\section{Superseded Figures and Run Ledger}"
LEDGER_REQUIRED = ["spec v3", "121.5"]

FIGURE_SCRIPTS = [
    "figures/make_figures.py",
    "figures/make_ccf_data.py",
    "abm/monte_carlo_simulation.py",
]

# Benchmark shares (% of the $764.7B benchmark) and headline dollar figures
# that have ever been displayed in a figure; none may be hardcoded in a
# figure script (values arrive via json/manifest reads).
SHARE_LITERALS = [
    "119.7", "894.8", "117.0", "110.6", "112.4", "121.5", "127.5",
    "107.0", "109.1", "97.9", "96.9", "106.0", "100.04", "88.7",
    "59.3", "20.9", "11.9", "11.1", "71.1", "54.9", "45.1", "33.7",
    "764.7", "915.0", "915.1", "928.9", "905.1", "818.5", "834.6",
    "974.7", "91.0", "84.5", "453.5", "159.5", "765.1",
]

# The retracted timing convention may not reappear in any figure script.
FIGURE_FORBIDDEN = ["model CPR leads", "model leads", "TBA settlement"]

# Freeze item (ii), LaTeX half: every cross-reference goes through \ref —
# a hardcoded "Table 7" / "Section V.C" literal would silently drift when
# floats renumber. Comments are stripped before matching.
HARDCODED_XREF = {
    "Table N literal": r"Table[~ ]\d",
    "Figure N literal": r"Figure[~ ]\d",
    "Section roman literal": r"Section[~ ][IVX]+(?:\.[A-Z])?(?![a-zA-Z}])",
    "Appendix letter literal": r"Appendix[~ ][AB](?![a-zA-Z}])",
    "Equation (N) literal": r"[Ee]quation[~ ]\(\d\)",
}

# --- Round-20 (gate #68): ABSTRACT-SCOPED HEDGE SPANS -----------------------
# The abstract is the only part of the paper most readers will read, and it was
# the only part with no literal gate on its hedges. Four candidate abstracts were
# drafted this round; three of them misattributed the ex-ante projection (to the
# author, or to a generic "consensus") or dropped the "large majority" qualifier,
# and the suite passed all three.
#
# Two design points, both load-bearing:
#
# (i) SCOPED TO THE ABSTRACT, not the file. These phrases occur 1-26 times in the
#     body ("recalibrated" alone appears 26 times), so a whole-file count gate is
#     satisfied by body prose even when the abstract has dropped the hedge
#     entirely. The gate reads the abstract environment and nothing else.
#
# (ii) CONTIGUOUS SPANS, not proximity windows. A hedge can be relocated into a
#      neighbouring decoy sentence and still sit inside any tolerable +/-N-char
#      window while the claim it was hedging goes bare -- "...anticipated the
#      realized shortfall. The large majority of the book is fixed-rate." passes
#      a proximity gate and says the opposite thing. Binding the minimal span
#      that joins hedge to claim is what makes the hedge non-relocatable.
ABSTRACT_BOUNDS = ("\\begin{abstract}", "\\end{abstract}")
ABSTRACT_HEDGES = {
    # the projection is the FED'S, and it anticipated MOST -- not all -- of the
    # shortfall. Dropping either half is the misattribution this gate exists for.
    # ONE span, not two: an earlier cut of this gate checked the attribution
    # ("The Federal Reserve's own ex-ante projection") and the hedge
    # ("anticipated the large majority...") as INDEPENDENT entries, which let an
    # adversary open a sentence boundary at the seam and reattribute the verb --
    # "...projection is described in the appendix. My model anticipated the large
    # majority of the realized shortfall." -- with both fragments still present.
    # That is the exact defect this gate was written to kill, and it passed.
    # ROUND-27 option-2 cut: the expectations pair (attribution + denominator
    # switch) LEFT the abstract with its hedges; both are body-pinned below
    # (fed_projection_body, surprise_denominator_body), each a SINGLE span
    # joining attribution/switch to its hedge so the seam attack the round-24
    # battery documented has no boundary to open.
    # the denominator switch, and the allocation the half-share is conditional on
    # ROUND-23: extended. The old surprise_share_allocated span carried
    # "genuine surprise" and moved to the body with the allocation detail, which
    # left the denominator switch pinned but the OBJECT it switches to unpinned
    # -- an abstract could have said "...rather than the never-binding cap,
    # lock-in accounts for roughly a quarter to a half of the shortfall" and
    # passed. The span now runs to the object.
    # "small" scopes to the institutional cash-flow cost only; the mobility cost
    # is real, and the abstract must not let the two be read as one
    "cost_scoped_institutional": "The institutional cash-flow cost is small",
    # the null's recovery rests on amortization AND baseline turnover
    "null_mechanical_components": "scheduled amortization and baseline "
                                  "turnover",
    # ROUND 22 (3d): the ABM-vs-hazard contrast must not be attributed to
    # modeling paradigm in the abstract. This is the hedge the concision handoff
    # named as the highest-value ungated abstract hedge; pinning it BEFORE any
    # compression pass touches the abstract is the point.
    #
    # ROUND-24: the ABM RETURNED to the abstract. Round 23's cut left the model
    # occupying Section IV and Appendix A while the abstract did not mention it
    # at all, which HANDOFF_round24 §6 records as an inconsistency that round
    # introduced. The claim is back, so by this gate's own scoping argument its
    # hedges come back with it -- the body pins below stay, because the body
    # still makes the claim too, and neither dict is a substitute for the other.
    #
    # Every span here must hold in the ARCHIVED long-abstract variant as well,
    # since gate C4 applies this dict to every manuscript on disk and that
    # variant's abstract is an archive that must not be rewritten to suit a new
    # pin. That is what fixes the wording below: it is the widest binding of
    # hedge to claim that occurs verbatim in both abstracts.
    #
    # KNOWN SEAM, measured rather than assumed: the recalibration hedge and the
    # two recovery numbers cannot be joined into one span, because the long
    # abstract carries a frozen-seed clause between them. An adversary can
    # therefore open a sentence boundary at that seam. The seam mutation in
    # tests/test_abstract_hedge_gate.py exists so this is a known, tested limit
    # and not a discovery for a later round.
    # ROUND-27 abstract cut (author-directed): the ABM and cross-design
    # readings LEFT the abstract with their hedges, per the round-23
    # hedges-travel-with-claims rule. Their four abstract-scoped spans
    # (abm_seed_averaged, crossdesign_recalibrated,
    # crossdesign_seed_and_reweight, paradigm_attribution_hedged) moved to
    # RELOCATED_TO_BODY twins -- see that dict below.
}

# ROUND-23: the abstract was cut from 574 to 263 words and five claims LEFT it
# (the ABM level, the cross-design variant, the nineteen-month floor check, the
# paradigm attribution, and the named intra-2022 allocations). Their hedges left
# WITH them -- a hedge only has to travel with the claim it scopes, and the
# abstract no longer makes those claims. But the hedges must still be pinned
# somewhere a reader meets them, or this was a deletion of five protections
# rather than a relocation. These are checked against the BODY (the file with
# the abstract environment removed), which is the mirror image of the scoping
# argument at the top of this block: whole-file counts are too weak for an
# abstract claim, and abstract scoping is simply wrong for a body claim.
RELOCATED_TO_BODY = {
    # the ABM number is a seed mean, not a single run  (was abm_seed_averaged)
    "abm_seed_averaged_body": "13.6\\% on the fifty-seed mean",
    # the cross-design variant was refit, so it is not a clean out-of-sample read
    "crossdesign_recalibrated_body": "A cross-design variant of the ABM "
                                     "recalibrated on real loan covariates",
    # the nineteen-month check is INPUT stability, not an outcome holdout
    "holdout_relabelled_body": "the nineteen-month floor variant reported later "
                               "is an input-stability check rather than an "
                               "outcome holdout",
    # the ABM-vs-hazard contrast is not cleanly a paradigm effect
    "paradigm_attribution_hedged_body": "be cleanly attributed to modeling "
                                        "paradigm rather than to calibration "
                                        "and data source",
    # ROUND-27 abstract cut: the cross-design seed hedge and the book-
    # composition reweight left the abstract with their claims; each is
    # pinned against its body statement (SS IV lead; tab:headline caption).
    "crossdesign_seed_body": "60.2\\% averaged over fifty seeds---above the "
                             "50\\% threshold",
    "crossdesign_reweight_body": "76.3\\% at the book's composition",
    # ROUND-27 option-2 cut: the expectations pair's body pins. Each joins
    # the attribution (resp. the denominator switch) to its hedge in ONE
    # span, so a seam attack that opens a sentence boundary between them
    # deletes the span and is caught by span presence.
    "fed_projection_body": "The New York Fed's May 2022 staff baseline "
                           "already anticipated the large majority of the "
                           "realized cap-shortfall",
    "surprise_denominator_body": "projection rather than the non-binding cap, "
                                 "the lock-in channel accounts for roughly "
                                 "half the genuine surprise under the central "
                                 "allocation",
    # the quarter/half split is allocation-conditional, and both are named
    "surprise_share_allocated_body": "they require the uniform-spread "
                                     "allocation, because the settlement-aware "
                                     "allocation puts the anticipated share at "
                                     "75.6\\%",
}


# --- Round-24 (gate #98): THE ASSEMBLED CORRECTIONS ------------------------
# Every downward correction to the headline marginal was disclosed in the
# section that produced it and nowhere together, so a referee performed the
# assembly and the paper did not. Section V.E now performs it.
#
# PARAGRAPH-SCOPED, for the same reason gate #68 is abstract-scoped: each of
# these literals already occurs elsewhere in the file, so a whole-file count is
# satisfied by the very scattering this paragraph exists to end. The manuscript
# is one paragraph per line, so the paragraph IS a line and the gate binds the
# line -- which also kills the relocation attack, since a paragraph split moves
# half the spans off it.
#
# Four things are pinned, and each is a way the paragraph could rot:
#   (a) the LADDER -- drop a rung and the assembly stops being an assembly;
#   (b) the POSTURE -- "upper-middle member ... rather than its center" is the
#       commitment the round was asked for, and a concision pass that deletes
#       it leaves the ladder with no conclusion;
#   (c) the CENSORING FRAMING -- "truncated at the floor rather than erased"
#       plus the unweighted-count disclaimer. HANDOFF_round22 §8.2 records that
#       the obvious reading ("the estimate rests on a third of the data") is
#       false on two independent counts, and it is the reading a reader
#       supplies unprompted. Losing the disclaimer re-opens it;
#   (d) the COUNTERWEIGHT -- the additive form, the Fonseca anchor, and the
#       three declined readings all run the other way. Without them the
#       paragraph is a one-sided case for a smaller number, which is not what
#       the evidence says.
ASSEMBLY_OPENER = "A seventh qualification"
ASSEMBLY_SPANS = {
    # (a) the ladder, in order
    "ladder_insample": "in-sample calibration returns $+9.2$ points",
    "ladder_headline": "outside the window returns the headline $+5.6$",
    "ladder_overlay": "overlay at that same floor returns $+4.4$",
    "ladder_agestd": "floor read of 5.51\\% returns a measured marginal of $+3.7$, "
                     "against the $+3.8$ its position on the frozen grid implies",
    "ladder_fannie": "5.52\\%, brackets the marginal below the $+4.3$ edge",
    # ROUND-27 B5: the joint cell was run under the pre-committed landing rule
    # (b5_joint_cell: composed +2.928pp, deviation -0.07 from the +3.0
    # projection, interaction ~0 vs proportional; all parity gates PASS).
    # The rung is now a measured composed point, and the span pins the run
    # tag + measurement so a wording pass cannot demote it back to projection.
    "ladder_composed": "run under a pre-committed landing rule (run "
                       "\\texttt{b5\\_joint\\_cell}) and measures $+2.9$ points",
    # (b) the posture, bound to the interval it is a posture about.
    #     ROUND-26 re-derivation: the corrected interval's midpoint is 5.76,
    #     so +5.57 sits just BELOW it; ROUND-28 (DA-C2) RETIRED the posture:
    #     the symmetric assembly lines downward specification variants up
    #     beside the upward counterweights, and the pinned claim is now that
    #     no interior member is privileged (the range carries).
    "posture_retired_range_carries": "no interior member is privileged, and the range "
                                     "rather than any point is what the design delivers",
    # ROUND-28 (R1-W1 / C3 branch a): the ranking is now scoped — the PSA
    # baseline-level convention spans wider but has no coverage property; the
    # floor read is the widest layer WITH one, and that scoping is pinned.
    "posture_binding_layer": "The widest layer that does have a coverage property is the "
                             "floor reads' own sampling error, $+2.9$ to $+8.7$ points "
                             "after wild-cluster correction",
    "posture_lower_half": "every correction listed above falls in its lower half",
    # (c) the censoring share (HANDOFF_round24 §4) and the framing that
    #     HANDOFF_round22 §8.2 exists to protect. The share and its framing are
    #     pinned as separate spans on purpose: the share without the framing is
    #     the false reading, and the framing without the share is a disclaimer
    #     about nothing.
    "censor_share": "pinned to the floor in 68.8\\% of evaluated loan-months, against 36.3\\%",
    "censor_truncated": "truncated at the floor rather than erased",
    "censor_unweighted": "unweighted loan-month counts rather than balance-weighted shares",
    # (d) the counterweight, without which this is a one-sided case
    "counter_additive": "the additive form returns $+11.2$ points at the same off-window "
                        "anchors",
    "counter_fonseca": "$+11.5$ points at the production floor",
    "counter_three_readings": "point to a larger lock-in channel, not a smaller one",
}

# ROUND-27: tab:assembly tabulates the assembly the paragraph builds in prose.
# Whole-file spans (the table is its own lines, not the paragraph's): the label,
# the paragraph's anchor sentence, and the two rows a hostile edit would most
# plausibly corrupt -- the composed row (must NOT read as reporting a composed
# point; the no-composed-point discipline is gate-#104-pinned) and the Fonseca
# row (a counterweight, NOT a declined reading -- the checker caught that
# mislabel before it shipped).
ASSEMBLY_TABLE_SPANS = {
    "table_label": "\\label{tab:assembly}",
    "table_anchor": "Table~\\ref{tab:assembly} tabulates this assembly",
    "table_row_composed": "measured composed lower member (run \\texttt{b5\\_joint\\_cell})",
    "table_row_fonseca": "counterweight, conservative-band evidence",
}


# --- Round-24b (gate #99): THE ABSTRACT LEADS WITH THE RANGE ---------------
# Section V.E's seventh qualification argues that the identified content is the
# range and that $+5.6$ is an upper-middle member of it. Until this round the
# abstract, the introduction, Table 1 and the conclusion all led with the point
# and carried the range afterwards, so the front of the paper argued against its
# own Section V.E. Fixing the four sites is worth nothing if the next concision
# pass quietly puts the point back in front, which is what this gate is for.
#
# CANONICAL-ONLY, and that is a deliberate exception to gate C4's rule that
# every abstract check runs against every manuscript on disk. The archived
# long-abstract variant makes the same commitment in its own words ("a bounded
# range for the elasticity's contribution, not a pinned magnitude"), and no span
# expressing THIS abstract's version occurs verbatim in it. The alternatives
# were to rewrite an archive to suit a new pin, or to leave the posture
# unpinned; a canonical-scoped dict is better than either, and putting these in
# ABSTRACT_HEDGES would simply have failed the variant.
#
# The ORDERING assert is the load-bearing half. Every span below survives an
# abstract that states the point first and the range second -- which is exactly
# the arrangement this round removed -- so a span check alone would not have
# caught the defect it exists to prevent.
ABSTRACT_POSTURE = {
    "range_not_number": "What lock-in itself adds is a range rather than a number",
    # ROUND-26 full restatement: the binding layer is the wild-cluster
    # bootstrap-t interval from run floor_inference_correction; the percentile
    # read is demoted to a labeled mention inside the same parenthetical.
    "interval": "The design bounds it between $+2.9$ and $+8.7$ points",
    # ROUND-28 (DA-C3): the abstract must say WHAT the interval bounds. "pins"
    # claimed the design pinned the elasticity's contribution; the interval is
    # the floor read's sampling error at a FIXED elasticity, which contributes
    # zero width. Pinned as its own span so a concision pass cannot delete the
    # referent while keeping the interval.
    "interval_referent": "the floor read's sampling error at my central elasticity",
    "point_named_inside": "Inside that range, $+5.6$ points, or \\$42.6 billion, is the "
                          "value at the calibration I headline",
    # ROUND 32: the frame is still load-bearing -- the additive form (+11.2) and
    # the Fonseca anchor (+11.5) move the marginal UP -- but the claim it used to
    # protect ('moves it down') is now FALSE and has been restated. Task 11's
    # activity leg is a MEASURED correction to the baseline turnover floor that
    # moves the marginal up +5.11 points, so 'only floor and accounting-basis
    # corrections run one way' no longer holds. The pin now protects the two-way
    # statement instead of the one-way one.
    "corrections_framed": "the corrections I can measure to the baseline turnover "
                          "floor or to the accounting basis no longer all run one way",
    # ROUND-26: the panel's two strongest correlated findings (DA-C1 + R1-W1,
    # both verified) were that the abstract quoted the interval without its
    # form conditionality and without its few-cluster inferential status.
    # Both now travel with the interval IN the abstract, and these pins keep
    # them there: the qualifier span binds the sampling caveat to the pinned
    # interval sentence, and the hull span keeps the form dimension stated
    # where the max-form interval is stated. Canonical-scoped like the rest
    # of this dict (the archived variant predates both).
    # ROUND-27 abstract cut: qualifier compressed (wild-cluster status and
    # under-coverage kept; the demoted percentile literal now lives in the
    # body only, x4), hull restored to the of-form inside the interval
    # sentence.
    "interval_qualifier": "a wild-cluster interval on 31 clusters; the "
                          "percentile read under-covers",
    "hull_in_abstract": "form-conditional hull of $+3.5$ to $+13.1$ points",
    # ROUND-26 B8 (DA-M3): the abstract's mechanical-null sentence scoped
    # "however households react to rates" without marking that the floor it
    # rests on is itself calibrated from realized -- partly behavioral --
    # turnover. The qualifier travels with the null claim; canonical-scoped
    # because the archived variant's abstract predates it.
    "null_floor_behavioral": "itself read from realized, partly behavioral "
                             "turnover",
}


def abstract_posture_check(tex: str) -> tuple[bool, dict]:
    """Gate #99's rule, as a function so the battery exercises the shipped rule."""
    tex_nc = re.sub(r"(?<!\\)%.*", "", tex)
    _i = tex_nc.find(ABSTRACT_BOUNDS[0])
    _j = tex_nc.find(ABSTRACT_BOUNDS[1], _i + 1)
    found = _i != -1 and _j != -1
    abstract = tex_nc[_i + len(ABSTRACT_BOUNDS[0]):_j] if found else ""
    missing = sorted(k for k, v in ABSTRACT_POSTURE.items() if v not in abstract)
    # the range must be stated BEFORE the point it contains
    i_range = abstract.find("$+2.9$ and $+8.7$")
    i_point = abstract.find("$+5.6$ points")
    ordered = i_range != -1 and i_point != -1 and i_range < i_point
    return (found and not missing and ordered,
            {"found": found, "missing": missing, "ordered": ordered,
             "i_range": i_range, "i_point": i_point})


# --- Round-24c (gate #100): SECTION IV LEADS WITH THE CROSS-DESIGN ---------
# Section IV used to open with the production 13.6% and mention the cross-design
# leg as a qualifier three sections later, so it read as if 13.6% were the
# result. It is not: the same rule on real structural covariates recovers 60.2%
# over fifty seeds, above the 50% threshold fixed BEFORE that run at which this
# section's paradigm reading is undercut, and undercutting on all fifty. The
# section now leads with that and frames the production estimate as the
# synthetic-population special case.
#
# This whole reframing was, before this gate, entirely unpinned prose -- the
# case HANDOFF_round22 §4.2 warns about, where a green suite says nothing
# because no literal moved. Paragraph-scoped for gate #98's reason.
#
# THE THREE BOUNDS ARE THE POINT. Round 23 caught the reweight being quoted
# one-sidedly (the same reweight moves the FROZEN leg down to 12.6%), and the
# behavioral layer stays synthetic in both legs. A lead that keeps 76.3% and
# drops either bound is exactly the overclaim this gate exists to prevent, and
# it is the cheapest edit anyone would make to this paragraph.
#
# The ORDERING assert carries the "leads with" half: every span below survives a
# paragraph that states the negative verdict first and the cross-design
# afterwards, which is the arrangement round 24c removed.
ABM_LEAD_OPENER = "This section is a stress test"
ABM_LEAD_SPANS = {
    "leads_with_scope": "the first thing to report about it is what its own cross-design leg "
                        "establishes about its scope",
    "crossdesign_level": "60.2\\% averaged over fifty seeds",
    "threshold_precommitted": "above the 50\\% threshold fixed before that run",
    "reweighted": "76.3\\% once the sample is reweighted to the SOMA book's own coupon "
                  "composition",
    # bound 1: the reweight cuts both ways (round-23 catch)
    "bound_frozen_leg": "the same reweight moves the frozen-calibration leg the other way, "
                        "down to 12.6\\%",
    # bound 2: this is not a real population
    "bound_behavioral_synthetic": "no leg here replaces a synthetic behavioral population "
                                  "with a real one",
    # bound 3: the verdict is "cannot attribute", not "is not a paradigm effect"
    "bound_verdict_wording": "cannot, on that test alone, be cleanly attributed to modeling "
                             "paradigm",
    # and the verdict the section actually delivers, confined
    "verdict_confined": "What this section falsifies is therefore a \\emph{synthetic-population} "
                        "household-choice specification",
}


# --- Round-24c (gate #101): THE RESPONSE LETTER MUST NOT GO STALE ----------
# `response_to_referees_round22.tex` was drafted on 26 July and not sent. By the
# next day it stated a form-conditional hull the manuscript had already widened
# (+3.9 vs +3.5) and an abstract word count off by 96. Nothing checked it,
# because every gate in this file reads the manuscript.
#
# That is the highest-stakes rot in the repository: the manuscript's errors are
# caught by 100 checks, and the letter's errors go to a referee.
#
# The letter is PARTLY HISTORICAL, so "every literal must match the manuscript"
# would be the wrong rule -- §1-§6 legitimately describe the state at the time
# the report was answered. The rule is therefore three narrow ones, each aimed
# at a way the letter actually rotted or could:
#
#   (a) the retired hull literal may appear ONLY inside the sentence that marks
#       it historical. This is the exact defect that was found;
#   (b) the letter's claim about the abstract's length must equal the abstract's
#       actual length, recomputed here rather than trusted;
#   (c) every current-state figure §7 quotes must still exist in the manuscript.
#       §7 is the section that speaks in the present tense, so it is the section
#       that must track.
LETTER = ROOT / "paper" / "v18" / "response_to_referees_round22.tex"
LETTER_CURRENT_SECTION = "\\section{Changes since this response was drafted}"
LETTER_RETIRED_HULL = "$+3.9$ to $+13.1$"
LETTER_HISTORICAL_MARKER = "range that stood at\nthe time at $+3.9$ to $+13.1$ points. That range has since widened"
LETTER_CURRENT_LITERALS = [
    "$+3.5$ to $+13.1$",   # the hull, as it now stands
    "$+3.0$ to $+8.0$",    # the demoted percentile read (still quoted, labeled)
    "$+2.9$ to $+8.7$",    # the corrected binding layer the posture is stated against
    "$+3.53$", "$+10.83$",  # the cell that widened it, and the concave ceiling
    "$+270.4$", "$-105.3$",  # the ABM null's sign disagreement
    "68.8\\%", "35.8\\%",   # the censoring shares, central and null legs
    "60.2\\%", "76.3\\%", "12.6\\%",  # cross-design, and the reweight's other side
    "$-1.47$",              # the interaction that forbids a composed point
    "$-\\$51.0$ billion",  # the buyback bracket's cash-incidence figure, re-derived
    "$+11.2$", "$+11.5$",   # the two corrections that run the other way
]


# --- Round-26 (gate #102): THE ELASTICITY-DISCIPLINE EXHIBITS --------------
# The round-26 panel's consensus-3 finding (R1-W3 / R2-W2 / DA-C2, verified
# CONFIRMED) was that the imported elasticity is undisciplined by the paper's
# own data and the manuscript never showed what the marginal would be at any
# smaller elasticity or narrower hazard share. Two pre-committed runs now
# price both dimensions (band_low_extension: the marginal as a curve in the
# elasticity below the adopted band; moving_share_bracket: the gap response
# confined to a share s of the voluntary hazard), and these spans keep the
# exhibits, their run tags, their key values, and their descriptive posture
# in the manuscript. Whole-file presence: each span is unique prose, not a
# scattered literal, so paragraph scoping buys nothing here.
ELASTICITY_DISCIPLINE_SPANS = {
    "curve_run_tag": "\\texttt{band\\_low\\_extension}",
    "curve_table": "\\label{tab:lowband}",
    "curve_half_central": "$+5.1$ points ($+\\$39.1$ billion) at the in-sample "
                          "floor and $+3.5$ points ($+\\$26.5$ billion) at the "
                          "headline off-window floor",
    # the posture sentence is the load-bearing half: without it the curve
    # reads as identifying the elasticity, which it does not.
    "curve_posture": "prices the dependence on the imported elasticity rather "
                     "than identifying it",
    "bracket_run_tag": "\\texttt{moving\\_share\\_bracket}",
    "bracket_values": "$+\\$37.7$ billion ($+4.9$ points) at $s = 0.5$ and "
                      "$+\\$19.2$ billion ($+2.5$ points) at $s = 0.25$",
    "bracket_posture": "$s$ is a bracketing parameter rather than an estimate",
}


# --- Round-26 (gate #103): THE BUYBACK INCIDENCE BRACKET -------------------
# The conclusion asserted a signed leg-(3) improvement (+$61.2B) while the
# manuscript's own pathb paragraph recorded the market-value buyback credit
# as the largest un-priced channel, exceeding the gap. Run
# buyback_credit_bracket priced both incidence readings from committed
# artifacts (verdict REVERSES), R32's buyback_discount_rederived then
# replaced that run's asserted discount grid with one derived from the
# leg's own prepayment path (gate #117), and the paper states the gap's
# sign as incidence-
# conditional at every site that previously stated signed relief. These
# spans keep that statement from quietly reverting to the signed claim.
BUYBACK_BRACKET_SPANS = {
    "run_tag": "\\texttt{buyback\\_credit\\_bracket}",
    "reversal_point": "$-\\$51.0$ billion",
    "pathb_sign": "The gap's sign is therefore incidence-conditional",
    # ROUND-26 denomination resolution: the two incidences answer two
    # QUESTIONS. The benchmark is a face-value object (SOMA current face vs
    # par caps), so balance-adjustment is the benchmark-consistent reading;
    # the cash reversal prices the foregone par windfall from moving
    # households -- a transfer, not a resource cost. These pins keep both
    # halves of that resolution from being separated.
    "conclusion_sign": "the par windfall it would otherwise have extracted "
                       "from moving households",
    "denomination_resolution": "the balance-adjustment reading is the "
                               "benchmark-consistent one",
    "transfer_not_cost": "a household-to-bondholder transfer, not an added "
                         "resource cost",
    "trilemma_conditional": "while its effect on (3) is incidence-conditional",
    # the dissolution claim must stay scoped to face accounting
    "dissolution_scope": "trade off sharply under face accounting",
}


# --- Round-26 (gate #104): THE VERDICT-ADJUDICATION AUDIT ------------------
# DA-M2: verdict adjudication involves post-run judgment in both directions,
# and a green suite is not self-certifying. Appendix app:verdicts is the
# census of every non-mechanical adjudication. These spans pin the table,
# the epistemic sentence that gives it its point, and one row from EACH
# direction, so the table cannot quietly become a one-sided list.
VERDICT_AUDIT_SPANS = {
    "table": "\\label{tab:verdicts}",
    "appendix": "\\label{app:verdicts}",
    "epistemic": "A green gate suite is therefore not self-certifying",
    "row_for_headline": "the instability is the max form's censoring mechanics",
    "row_against_own_pass": "the 11.06-point envelope judged too wide to carry "
                            "information",
    "intro_pointer": "tabulates every such rule together with how its outcome "
                     "was adjudicated after the run",
}


def verdict_audit_check(tex: str) -> tuple[bool, dict]:
    """Gate #104's rule, as a function so a battery can exercise it."""
    tex_nc = re.sub(r"(?<!\\)%.*", "", tex)
    missing = sorted(k for k, v in VERDICT_AUDIT_SPANS.items()
                     if v not in tex_nc)
    return (not missing), {"missing": missing}


CONVOLVED_LINE_SPANS = {
    # ROUND-28 C2 (gate #105): the convolved sampling line is a labeled second
    # line, never a replacement. What the gate protects is the LABELING: the
    # pair without the independence caveat overstates what was measured; the
    # caveat without the comonotone bound understates how wrong independence
    # could be; and the lower-bound inheritance is what stops the line being
    # read as calibrated coverage.
    "run_tag": "\\texttt{layer\\_convolution}",
    "pair": "$[+2.80, +8.99]$",
    "independence_caveat": "independence is assumed, not measured",
    "comonotone_bound": "under maximal positive dependence the width is $8.12$pp",
    "one_number_reading": "the interval a reader who wants one number for "
                          "sampling error should use",
    "non_substitution": "an assumption rather than a measurement",
    "lower_bound_inheritance": "makes the convolved line a lower bound as well",
}


COUPON_CONVENTION_SPANS = {
    # ROUND-28 G2 (gate #106): the composed cell is basis-dependent and the
    # manuscript now says so everywhere it prints it. What the gate protects:
    # (a) the corrected companion 98.1 with its run tag; (b) the mixed-basis
    # labeling of the committed 100.0/100.04 (without it the old reading
    # returns); (c) the not-the-corrected-number clause; (d) the tightened
    # coupon bound; (e) the marginal's bit-invariance claim.
    "companion": "98.1\\% (97.6--99.1 across the legs; run "
                 "\\texttt{coupon\\_convention\\_reweight})",
    "mixed_basis_label": "That is a mixed-basis measurement",
    "not_corrected": "not the corrected number",
    "bound_tightens": "the bound tightens by an order of magnitude",
    "marginal_invariant": "the identified marginal bit-invariant",
    "conversion_def": "note rate less the vintage guarantee fee and base "
                      "servicing, $\\Delta = 0.80$ points",
}


FLOOR_LADDER_SPANS = {
    # ROUND-30 E7/CR1 (gate #107): the ladder's baseline rung and the floor
    # read's interval in the units a cap is set in. What the gate protects:
    # (a) both CR1 rungs, cell for cell, against the artifact they are rounded
    # from; (b) the tablenote's three claims about CR1 (df ownership, that it
    # is the narrowest sandwich and the wild rows' studentizer, and that its
    # Bell--McCaffrey row coinciding with CR3's conventional-df row is a
    # printed accident and not an identity) --- without that sentence the
    # table shows two rows with identical intervals and no reason; (c) the
    # run-tag credit, which is only honest because the t(30) rung is
    # bit-identical in the committed run; (d) the designer-units restatement,
    # which is the SAME read's Webb interval expressed in floor units, so a
    # drift between it and the $+2.9$ to $+8.7$ the paper quotes is a defect.
    "cr1_conventional": "CR1 $t$ & $+3.2$ to $+8.3$ & $t(30)$, $G-1$ & no "
                        "leverage adjustment",
    "cr1_bell_mccaffrey": "CR1 $t$, Bell--McCaffrey & $+2.8$ to $+8.8$ & "
                          "$t(6.2)$, data-driven & small-sample df",
    "df_ownership": "the 6.2 and 5.1 shown are CR1's and CR2's, and CR3's own "
                    "is smaller still",
    "cr1_is_the_baseline": "is the standard error the wild rows studentize "
                           "with, so its two rows are the ladder's baseline "
                           "rather than competing reads",
    "printed_tie_is_not_an_identity": "an accident of this leverage profile, "
                                      "not an identity",
    "run_credit": "\\texttt{floor\\_inference\\_correction} (Rademacher "
                  "wild-$t$; CR1--CR3 at $t(30)$)",
    "designer_frame": "in the units a cap designer would have to plug in",
    "designer_units": "wild-cluster interval runs from 4.177\\% to 5.800\\%",
    # R32 C-72: SPEC_R32_c72 §8 Branch A requires FLOOR_LADDER_SPANS to be
    # EXTENDED, never replaced, when new rows land. These two are the month and
    # two-way rows, byte-identical to gate #115's derived month_row/two_way_row.
    # Deliberately literal-only HERE: #107 opens v2's artifact and nothing else,
    # and the v3 derivation of these same cells (and of the whole ladder's
    # bookkeeping) lives in gate #115. tests/test_floor_ladder_gate.py's
    # test_each_span_removal_fails is parametrized over sorted(FLOOR_LADDER_SPANS)
    # and covers both automatically; that file needs no edit.
    "ladder_month_row": "CR1 $t$, month clusters & $+3.1$ to $+8.4$ & "
                        "$t(5)$, $G-1$ & wider on df alone",
    "ladder_two_way_row": "Two-way, stratum $\\times$ month & $+2.3$ to $+9.3$ "
                          "& $t(5)$, $\\min(G)-1$ & lower edge censored",
}

FLOOR_LADDER_READ = "R2_2018_gap<=-0.0025_age>=12"


def coupon_convention_check(tex: str) -> tuple[bool, dict]:
    """Gate #106's rule, as a function so a battery can exercise it."""
    tex_nc = re.sub(r"(?<!\\)%.*", "", tex)
    missing = sorted(k for k, v in COUPON_CONVENTION_SPANS.items()
                     if v not in tex_nc)
    info: dict = {"missing": missing}
    art = ROOT / "hazard" / "data" / "coupon_convention_reweight_results.json"
    if not art.exists():
        return False, {**info, "artifact": "MISSING"}
    cc = json.loads(art.read_text())
    legs = cc.get("legs", {})
    p0 = legs.get("central_phi_0", {})
    art_ok = (
        cc.get("status") == "OK"
        and cc.get("parity_gates_all_pass") is True
        and abs(p0.get("share_pct_shared", 0) - 98.1131) < 0.01
        and all(v.get("pass") is True
                for k, v in cc.get("parity_gates", {}).items()
                if k.startswith("G3c_invariance"))
        and any(k.startswith("G3c_invariance")
                for k in cc.get("parity_gates", {}))
    )
    info["artifact_ok"] = art_ok
    return (not missing) and art_ok, info


def convolved_line_check(tex: str) -> tuple[bool, dict]:
    """Gate #105's rule, as a function so a battery can exercise it."""
    tex_nc = re.sub(r"(?<!\\)%.*", "", tex)
    missing = sorted(k for k, v in CONVOLVED_LINE_SPANS.items()
                     if v not in tex_nc)
    info: dict = {"missing": missing}
    art = ROOT / "hazard" / "data" / "layer_convolution_results.json"
    if not art.exists():
        return False, {**info, "artifact": "MISSING"}
    lc = json.loads(art.read_text())
    prim = lc.get("convolved_primary", {})
    ci = prim.get("ci95_pp", [None, None])
    art_ok = (
        lc.get("status") == "OK"
        and lc.get("parity_gates_all_pass") is True
        and ci[0] is not None
        and f"[{ci[0]:+.2f}, {ci[1]:+.2f}]" == "[+2.80, +8.99]"
        and prim.get("width_pp", 0) > 5.822976726802727
        and lc.get("floor_invariance_probe", {}).get("within_tolerance") is True
    )
    info["artifact_ok"] = art_ok
    return (not missing) and art_ok, info


def floor_ladder_check(tex: str) -> tuple[bool, dict]:
    """Gate #107's rule, as a function so a battery can exercise it."""
    tex_nc = re.sub(r"(?<!\\)%.*", "", tex)
    missing = sorted(k for k, v in FLOOR_LADDER_SPANS.items()
                     if v not in tex_nc)
    info: dict = {"missing": missing}
    if missing:
        return False, info
    ordered = (tex_nc.index(FLOOR_LADDER_SPANS["cr1_conventional"])
               < tex_nc.index("CR2 $t$ & $+3.0$ to $+8.6$")
               and tex_nc.index(FLOOR_LADDER_SPANS["cr1_bell_mccaffrey"])
               < tex_nc.index("CR2 $t$, Bell--McCaffrey"))
    info["ordered"] = ordered
    art = ROOT / "hazard" / "data" / "floor_inference_correction_v2_results.json"
    if not art.exists():
        return False, {**info, "artifact": "MISSING"}
    fi = json.loads(art.read_text())
    rd = fi.get("reads", {}).get(FLOOR_LADDER_READ, {})
    cr1 = rd.get("cr1_t_interval", {})
    cr1bm = rd.get("cr1_t_interval_df_bm", {})
    cr3 = rd.get("cr3_t_interval", {})
    webb = rd.get("wild_t_webb", {})
    c1 = cr1.get("marginal_ci95_pp") or [None, None]
    c1b = cr1bm.get("marginal_ci95_pp") or [None, None]
    wf = webb.get("floor_ci95_pct") or [None, None]
    dfbm = rd.get("df_bm_by_estimator", {})
    if None in (c1[0], c1b[0], wf[0]):
        return False, {**info, "artifact": "INCOMPLETE"}
    df1 = cr1bm.get("df_used", 0.0)
    art_ok = (
        fi.get("status") == "OK"
        and fi.get("parity_gates_all_pass") is True
        and rd.get("n_clusters") == 31
        # the two CR1 rungs reproduce their printed cells from full precision
        and f"${c1[0]:+.1f}$ to ${c1[1]:+.1f}$" == "$+3.2$ to $+8.3$"
        and f"${c1b[0]:+.1f}$ to ${c1b[1]:+.1f}$" == "$+2.8$ to $+8.8$"
        and cr1.get("df_used") == 30.0
        and cr1.get("df_kind") == "G_minus_1"
        and cr1bm.get("df_kind") == "bell_mccaffrey_imbens_kolesar"
        and f"$t({df1:.1f})$" == "$t(6.2)$"
        # neither CR1 rung is carried by a grid-edge truncation
        and not any(cell[edge]["truncated_at_grid_edge"]
                    for cell in (cr1, cr1bm)
                    for edge in ("lower_pp_edge", "upper_pp_edge"))
        # the tablenote's three claims about CR1
        and dfbm["cr1"] > dfbm["cr2"] > dfbm["cr3"]
        and rd["se_cr1_smm"] < rd["se_cr2_smm"] < rd["se_cr3_smm"]
        and c1b != cr3.get("marginal_ci95_pp")
        # the designer-units clause is the SAME read's Webb interval in floor
        # units, and the floor-to-marginal map is inverse
        and f"{wf[0]:.3f}\\% to {wf[1]:.3f}\\%" == "4.177\\% to 5.800\\%"
        and webb["upper_pp_edge"]["floor_pct"] < webb["lower_pp_edge"]["floor_pct"]
        and abs(webb["marginal_ci95_pp"][0] - 2.8549950653913494) < 1e-9
        and abs(webb["marginal_ci95_pp"][1] - 8.677971792194077) < 1e-9
    )
    info["artifact_ok"] = art_ok
    return ordered and art_ok, info


def wal_normal_turnover_check(tex, wnt, oos):
    """Gate #108's rule, as a function so a battery can exercise it.

    Round-30 D2: the normal-turnover WAL row must be the committed artifact's, the
    artifact's anchor must still be the floor artifact's headline read, its parity
    against the frozen calculator must have passed, and the sentence the run
    falsified must not come back.
    """
    r = wnt["rows"]["turnover_floor_oow_mid"]
    lit_row = (f"({r['mean_cpr_pct']:.2f}\\%) & {r['wal_june_2022']:.1f} & "
               f"{r['wal_nov_2025']:.1f}")
    anchor = (oos["instrument1_oow_floor"]["defensible_clean_floor"])
    par = wnt["parity"]
    ok = (bool(par["nine_rows_bit_identical"])
          and bool(par["frozen_artifact_untouched"])
          and bool(par["printed_row_precision_insensitive"])
          and bool(wnt["expectations"]["E1_pass"])
          and wnt["spec"]["anchor_full_precision_pct"] == anchor["clean_mid_pct"]
          and tex.count("\\texttt{wal\\_normal\\_turnover}") >= 1
          and lit_row in tex
          and "No row is printed at a normal-turnover speed." not in tex)
    return ok, {"lit_row": lit_row, "present": lit_row in tex,
                "tag_citations": tex.count("\\texttt{wal\\_normal\\_turnover}"),
                "anchor_pct": wnt["spec"]["anchor_full_precision_pct"],
                "stale_sentence_gone":
                    "No row is printed at a normal-turnover speed." not in tex}



def cap_monthly_units_check(tex, eb, bench, binding_lo_pp, binding_hi_pp):
    """Gate #111's rule (R32, C-54): SS VI.B's result in the units of a cap decision.

    C-54 asked for the cap result restated in $bn/month with a band, because a
    cap is set in $bn/month and the paper stated it only in window totals. Every
    literal below is DERIVED here from the committed benchmark artifact and the
    binding interval -- none is written into this gate -- so a rerun that moved
    the projections cannot leave a stale monthly figure standing in SS VI.B.

    Two things beyond arithmetic are bound. (i) The RATIOS, because "the ceiling
    was near twice the achievable rate" is the sentence's claim and a ratio drifts
    silently when either side moves. (ii) The scope disclaimer: the band belongs
    to the identified marginal, NOT to the two projection levels, which are
    accounting constructions with no sampling interval. Without that sentence the
    paragraph reads as though a projection had a confidence interval.
    """
    M = 42
    proj = eb["window"]["projected_runoff_window_b"] / M
    sett = eb["settlement_aware_allocation"]["projected_runoff_window_b"] / M
    cap = eb["supplementary_projection_wedge"]["cap_target_window_b"] / M
    lo = bench * binding_lo_pp / 100.0 / M
    hi = bench * binding_hi_pp / 100.0 / M
    lits = {
        "cap_ceiling": f"\\${cap:.2f} billion per month" in tex,
        "uniform_spread": f"\\${proj:.1f} billion per month" in tex,
        "settlement_aware": f"\\${sett:.1f} billion per month" in tex,
        "ratios": f"ratios of {cap / proj:.2f} and {cap / sett:.2f}" in tex,
        "marginal_band": f"\\${lo:.2f} to \\${hi:.2f} billion per month" in tex,
        "band_scope_disclaimer": (
            "That band attaches to the identified marginal, not to the two "
            "projection levels") in tex,
    }
    return all(lits.values()), {"missing": sorted(k for k, v in lits.items() if not v),
                                "cap_per_month": round(cap, 2),
                                "achievable_per_month": (round(proj, 1), round(sett, 1))}


def depth_ladder_shape_check(tex, d):
    """Gate #114's rule (R32, C-80): the 2018 depth ladder's shape.

    Derives every printed per-bin CPR and the plateau coverage from the run
    artifact. Beyond presence it binds the TWO QUALIFICATIONS, because this
    exhibit's failure mode is cherry-picking: the plateau supports the paper's
    own production form, so the tail that argues the other way, and the
    not-a-test caveat, are exactly what a later edit would be tempted to drop.
    """
    bins = {b["bin"]: b for b in d["bins"]}
    sh = d["shape"]
    def pct(x):
        return f"{x:.2f}\\%"
    lits = {
        "bin1": pct(bins["(-0.0025,+0.0000]"]["cpr_pct"]) in tex,
        "bin2": pct(bins["(-0.0050,-0.0025]"]["cpr_pct"]) in tex,
        "bin3": pct(bins["(-0.0075,-0.0050]"]["cpr_pct"]) in tex,
        "bin4": pct(bins["(-0.0100,-0.0075]"]["cpr_pct"]) in tex,
        "rising_bin": pct(bins["(-0.0150,-0.0100]"]["cpr_pct"]) in tex,
        "tail1": pct(bins["(-0.0200,-0.0150]"]["cpr_pct"]) in tex,
        "tail2": pct(bins["(-0.0250,-0.0200]"]["cpr_pct"]) in tex,
        "plateau_coverage": f"{sh['plateau_exposure_share']*100:.1f}\\%" in tex,
        "tail_disclosed": "not well supported" in tex,
        "rises_not_falls": "rather than falling" in tex,
        "not_a_test": "not as a resolution of the fork" in tex,
        "run_tag": "\\texttt{depth\\_ladder\\_shape}" in tex,
    }
    ok = all(lits.values()) and all(d["parity"].values())
    return ok, {"missing": sorted(k for k, v in lits.items() if not v),
                "plateau_cov_pct": round(sh["plateau_exposure_share"] * 100, 1),
                "tail_cov_pct": round(sh["tail_exposure_share"] * 100, 2)}


def marginal_transaction_counts_check(tex, m):
    """Gate #113's rule (R32, C-76 + C-82): the marginal in transaction counts.

    Every printed count is DERIVED here from the run artifact. Three properties
    beyond presence are bound, because each is a way the exhibit could go wrong
    quietly:

    (i) the UPPER-BOUND framing, since s=1 is a convention and dropping the word
    turns a bound into an estimate; (ii) the DENOMINATOR disclosure, since using
    the all-loan mean instead of the surviving mean would roughly double every
    count and the text is what warns a reader; (iii) the NOT-COMPUTED disclosure
    about the 2022-2024 decline, since silently dropping it would leave the
    condition looking satisfied when its comparator was never sourced.
    """
    c1 = m["cells"]["s_1"]
    ch = m["cells"]["s_0.5"]
    cq = m["cells"]["s_0.25"]
    cmp_ = m["comparator"]
    lits = {
        "book_count": f"{round(c1['book_foregone_payoffs'], -2):,.0f}".replace(",", "{,}") in tex,
        "per_year": f"{round(c1['book_foregone_payoffs_per_year'], -2):,.0f}".replace(",", "{,}") in tex,
        "bracket_half": f"{round(ch['book_foregone_payoffs'], -2):,.0f}".replace(",", "{,}") in tex,
        "bracket_quarter": f"{round(cq['book_foregone_payoffs'], -2):,.0f}".replace(",", "{,}") in tex,
        "surviving_denominator": f"\\${m['spec']['denominator_surviving_mean']:,.0f}".replace(",", "{,}") in tex,
        "n_surviving": f"{m['spec']['n_surviving']:,}".replace(",", "{,}") in tex,
        "upper_bound_framing": "upper bound" in tex,
        "denominator_warning": "would roughly double the count" in tex,
        "decline_not_computed": "cannot be formed without assuming" in tex,
        "run_tag": "\\texttt{marginal\\_transaction\\_counts}" in tex,
    }
    if cmp_.get("sourced"):
        share_lo = c1["share_of_2025_run_rate_lo"] * 100
        share_hi = c1["share_of_2025_run_rate_hi"] * 100
        lits["share_of_run_rate"] = f"{share_lo:.1f}--{share_hi:.1f}\\%" in tex
    ok = (all(lits.values())
          and all(m["parity"].values())
          and bool(m["expectations"]["E1_counts_increase_in_s"]))
    return ok, {"missing": sorted(k for k, v in lits.items() if not v),
                "book_count": round(c1["book_foregone_payoffs"]),
                "comparator_sourced": bool(cmp_.get("sourced")),
                "E3_pass": m["expectations"]["E3_pass"]}


def state_contingent_cap_check(tex, g):
    """Gate #112's rule (R32, C-81): the state-contingent cap's two-input grid.

    Every literal is DERIVED here from the run artifact -- the three cell levels,
    the two band ends, and BOTH spreads -- so a rerun that moved any of them
    cannot leave a stale number in SS VI.B.

    The spreads are the point of the exhibit (the observable buys less than the
    floor's own sampling error), and they are printed at ONE decimal on purpose:
    the true cut-spread is 1.1252, which rounds to 1.13, while the printed cells
    subtract to 1.12. Printing 1.13 beside cells that give 1.12 would hand a
    reader an arithmetic error. The gate therefore pins the 1-dp form, and a test
    asserts the printed cells still subtract to it.
    """
    c, b = g["cells"], g["band"]
    e = g["expectations"]
    lits = {
        "cell_0bp": f"\\${c['cut_0bp']['achievable_b_per_month']:.2f}" in tex,
        "cell_25bp": f"\\${c['cut_25bp']['achievable_b_per_month']:.2f}" in tex,
        "cell_50bp": f"\\${c['cut_50bp']['achievable_b_per_month']:.2f}" in tex,
        "band_lo": f"\\${b['floor_4.177pct']['achievable_b_per_month']:.2f}" in tex,
        "band_hi": f"\\${b['floor_5.8pct']['achievable_b_per_month']:.2f}" in tex,
        "cut_spread": (f"about \\${e['E3_spread_across_cuts_b_per_month']:.1f} billion "
                       "per month") in tex,
        "band_spread": f"about \\${e['E3_spread_across_band_b_per_month']:.1f} billion" in tex,
        "degenerate_observable": "near-degenerate" in tex,
        "two_grains_scope_limit": "two populations at two grains" in tex,
        "run_tag": "\\texttt{state\\_contingent\\_cap\\_grid}" in tex,
    }
    ok = (all(lits.values())
          and bool(g["parity"]["nine_rows_bit_identical_via_schedule"])
          and bool(g["parity"]["coupon_shares_sum_to_one"])
          and bool(g["expectations"]["E1_monotone_in_floor"])
          and bool(g["observable_declared_not_predicted"]["near_degenerate"]))
    return ok, {"missing": sorted(k for k, v in lits.items() if not v),
                "cells_b_per_month": [round(c[k]["achievable_b_per_month"], 2)
                                      for k in ("cut_0bp", "cut_25bp", "cut_50bp")],
                "E3_pass": e["E3_pass"]}


def wal_note_rate_basis_check(tex, wnrb, amort):
    """Gate #110's rule (R32, C-94), as a function so a battery can exercise it.

    tab:wal used to print the empirical path on ONE basis (the 5.14% ABM-basis
    back-out) while tab:estimators disclosed three, so the corrected amortization
    basis was disclosed and never became the comparator. The note-rate row now
    closes that, and this gate binds four things.

    (i) The printed row is the artifact's, built here from the artifact rather
    than written as a literal, so a rerun that moved the row cannot leave a stale
    pair standing in the table. (ii) The BASIS EFFECT stated in the tablenote is
    re-derived from the committed empirical row and the new one, because that
    difference -- not either level -- is the quantity C-94 is about, and a
    comparison is exactly what drifts silently when one side moves. (iii) A live
    cross-artifact tie: the CPR this run used must still be the coupon-convention
    run's own note-rate leg, so the two artifacts cannot drift apart unnoticed.
    (iv) The parity and monotonicity flags the runner set.

    The mixed-basis extension disclaimer is asserted present: it is the sentence
    that stops a reader differencing the note-rate row against the ABM-basis
    no-shock row, which would reintroduce the defect this row removes.
    """
    nr = wnrb["rows"]["empirical_note_rate_basis"]
    emp = wnrb["comparators"]["empirical_abm_basis_committed"]
    lit_row = (f"({nr['mean_cpr_pct']:.2f}\\%) & {nr['wal_june_2022']:.1f} & "
               f"{nr['wal_nov_2025']:.1f}")
    lit_emp = (f"({emp['mean_cpr_pct']:.2f}\\%) & {emp['wal_june_2022']:.1f} & "
               f"{emp['wal_nov_2025']:.1f}")
    d_june = round(emp["wal_june_2022"] - nr["wal_june_2022"], 1)
    d_nov = round(emp["wal_nov_2025"] - nr["wal_nov_2025"], 1)
    lit_effect = (f"shortens the empirical path by {d_june:.1f} years at the "
                  f"window's open and {d_nov:.1f} at its close")
    par, exp = wnrb["parity"], wnrb["expectations"]
    live_cpr = amort["hazard_legs"]["delta_080"]["mean_cpr_pct"]
    tie_ok = wnrb["spec"]["note_rate_cpr_full_precision_pct"] == live_cpr
    disclaimer = ("no committed note-rate", "mix conventions inside one statistic")
    disc_ok = all(s in tex for s in disclaimer)
    ok = (bool(par["nine_rows_bit_identical"])
          and bool(par["read_artifacts_untouched"])
          and bool(par["printed_row_precision_insensitive"])
          and bool(exp["E3_strictly_shorter_than_5p14_row"])
          and tie_ok and disc_ok
          and lit_row in tex and lit_emp in tex
          and lit_effect in tex
          and tex.count("\\texttt{wal\\_note\\_rate\\_basis}") >= 1)
    return ok, {"lit_row": lit_row, "row_present": lit_row in tex,
                "abm_row_present": lit_emp in tex,
                "effect_present": lit_effect in tex, "lit_effect": lit_effect,
                "cross_artifact_tie": tie_ok, "disclaimer_present": disc_ok,
                "tag_citations": tex.count("\\texttt{wal\\_note\\_rate\\_basis}")}


def beta1_sign_check(tex: str) -> tuple[bool, dict]:
    """Gate #109's rule (round 32, C-R4): the manuscript prints beta_1 under ONE
    sign convention.

    The panel saw $0.069$ in tab:params and $-0.0686$ in tab:lowband for the same
    parameter at the same delta and proposed flipping the printed signs. Reading
    the source first showed why that would have been wrong: eq:beta1 defines
    beta_1 WITH a leading minus, so it is positive under the manuscript's own
    definition, and eq:pathB multiplies it by the signed gap, which is negative
    for a locked-in borrower -- so a positive beta_1 suppresses prepayment and
    tab:params was already correct. tab:lowband was printing the convention of
    the production helper hazard/literature_hazard.py:rothstein_beta1, which
    returns ln(h_shocked/h_base) WITHOUT that minus. Neither was a computational
    error; one symbol was being printed under two conventions.

    So this gate asserts AGREEMENT, not a sign: whatever sign tab:params states
    for the central beta_1, every tab:lowband cell carries the same one. That is
    the property the objection was about, and it survives a later round choosing
    to restate eq:beta1 the other way round -- which a hardcoded "must be
    positive" gate would not.
    """
    m = re.search(r"\$\\beta_1\$ \(central\) & \$(-?)([0-9.]+)\$", tex)
    params_sign = 0 if m is None else (-1 if m.group(1) else 1)
    i = tex.find(r"\label{tab:lowband}")
    j = tex.find(r"\end{tabular}", i) if i != -1 else -1
    # the float runs past \end{tabular}, and the replicator note lives in the
    # tablenotes block between there and \end{threeparttable} -- so the cells are
    # read from the tabular and the note is looked for over the whole float.
    k = tex.find(r"\end{threeparttable}", i) if i != -1 else -1
    body = tex[i:j] if (i != -1 and j != -1) else ""
    float_txt = tex[i:k] if (i != -1 and k != -1) else ""
    # the delta and beta_1 columns lead each row: "6.50 & $0.0686$ & ..."
    cells = [float(sign + digits) for sign, digits in
             re.findall(r"^\s*[0-9.]+ & \$(-?)([0-9.]+)\$ &", body, re.M)]
    nonzero = [c for c in cells if c != 0.0]
    signs = {1 if c > 0 else -1 for c in nonzero}
    ok = (m is not None and body != "" and len(nonzero) == 9
          and len(signs) == 1 and signs == {params_sign}
          and "rothstein" in float_txt)
    return ok, {"params_sign": params_sign, "lowband": nonzero,
                "lowband_signs": sorted(signs), "cells_found": len(cells),
                "replicator_note": "rothstein" in float_txt}

def buyback_bracket_check(tex: str) -> tuple[bool, dict]:
    """Gate #103's rule, as a function so a battery can exercise it."""
    tex_nc = re.sub(r"(?<!\\)%.*", "", tex)
    missing = sorted(k for k, v in BUYBACK_BRACKET_SPANS.items()
                     if v not in tex_nc)
    return (not missing), {"missing": missing}


def elasticity_discipline_check(tex: str) -> tuple[bool, dict]:
    """Gate #102's rule, as a function so a battery can exercise it."""
    tex_nc = re.sub(r"(?<!\\)%.*", "", tex)
    missing = sorted(k for k, v in ELASTICITY_DISCIPLINE_SPANS.items()
                     if v not in tex_nc)
    return (not missing), {"missing": missing}


def letter_check(tex: str) -> tuple[bool, dict]:
    """Gate #101's rule, as a function so a battery can exercise it."""
    if not LETTER.exists():
        return False, {"exists": False}
    letter = LETTER.read_text()
    i = letter.find(LETTER_CURRENT_SECTION)
    current = letter[i:] if i != -1 else ""
    # (a) the retired hull literal, only where it is marked historical
    hull_hits = letter.count(LETTER_RETIRED_HULL)
    hull_ok = hull_hits == 0 or (hull_hits == 1
                                 and LETTER_HISTORICAL_MARKER in letter)
    # (b) the stated abstract length must equal the measured one
    _, ab = abstract_hedge_check(tex)
    claimed = re.findall(r"taken it to (\d+) words", letter)
    words_ok = len(claimed) == 1 and int(claimed[0]) == ab["words"]
    # (c) every current-state figure must still be in the manuscript
    drifted = [lit for lit in LETTER_CURRENT_LITERALS
               if lit in current and lit not in tex]
    absent = [lit for lit in LETTER_CURRENT_LITERALS if lit not in current]
    return (i != -1 and hull_ok and words_ok and not drifted and not absent,
            {"exists": True, "has_current_section": i != -1, "hull_ok": hull_ok,
             "claimed_words": claimed, "actual_words": ab["words"],
             "drifted": drifted, "absent": absent})


def abm_lead_check(tex: str) -> tuple[bool, dict]:
    """Gate #100's rule, as a function so the battery exercises the shipped rule."""
    tex_nc = re.sub(r"(?<!\\)%.*", "", tex)
    paras = [ln for ln in tex_nc.split("\n") if ln.startswith(ABM_LEAD_OPENER)]
    line = paras[0] if len(paras) == 1 else ""
    missing = sorted(k for k, v in ABM_LEAD_SPANS.items() if v not in line)
    # the cross-design must be stated BEFORE the negative verdict it scopes
    i_cross = line.find("60.2\\%")
    i_verdict = line.find("no specification tested here explains")
    ordered = i_cross != -1 and i_verdict != -1 and i_cross < i_verdict
    # and Section V.E must still DECLINE the same number, or the consistency
    # paragraph below the lead is talking about something that is not there
    ve_declines = "the third is a recovery level, which this design does not identify" in tex_nc
    return (len(paras) == 1 and not missing and ordered and ve_declines,
            {"paragraphs": len(paras), "missing": missing, "ordered": ordered,
             "ve_declines": ve_declines})


def assembly_check(tex: str) -> tuple[bool, dict]:
    """Gate #98's rule, as a function so the perturbation battery exercises THE
    SHIPPED RULE rather than a copy of it (gate #68's header explains why that
    distinction is not pedantry)."""
    tex_nc = re.sub(r"(?<!\\)%.*", "", tex)
    paras = [ln for ln in tex_nc.split("\n") if ln.startswith(ASSEMBLY_OPENER)]
    line = paras[0] if len(paras) == 1 else ""
    missing = sorted(k for k, v in ASSEMBLY_SPANS.items() if v not in line)
    table_missing = sorted(k for k, v in ASSEMBLY_TABLE_SPANS.items()
                           if v not in tex_nc)
    return (len(paras) == 1 and not missing and not table_missing,
            {"paragraphs": len(paras), "missing": missing,
             "table_missing": table_missing})


def abstract_hedge_check(tex: str) -> tuple[bool, dict]:
    """Gate #68's rule, as a function so the perturbation battery can exercise
    THE SHIPPED RULE instead of a copy of it.

    This is not decoration. The first cut of this gate was validated by a
    prototype that redefined ABSTRACT_HEDGES locally; the prototype reported
    every adversarial variant caught while the design it encoded still had the
    seam hole, because a test that mirrors the implementation can only confirm
    the implementation's own assumptions. Anything checking this gate must
    import it from here.
    """
    tex_nc = re.sub(r"(?<!\\)%.*", "", tex)
    _i = tex_nc.find(ABSTRACT_BOUNDS[0])
    _j = tex_nc.find(ABSTRACT_BOUNDS[1], _i + 1)
    found = _i != -1 and _j != -1
    abstract = tex_nc[_i + len(ABSTRACT_BOUNDS[0]):_j] if found else ""
    missing = sorted(k for k, v in ABSTRACT_HEDGES.items() if v not in abstract)
    # ROUND-23: the five spans that left the abstract with their claims are
    # enforced against the BODY. Checking them against the whole file would be
    # the exact weakness this gate's header rejects for abstract claims, only
    # inverted: the abstract is a subset of the file, so a whole-file count
    # would be satisfiable by an abstract that still carried them. Removing the
    # abstract environment makes the body check independent of the abstract.
    body = (tex_nc[:_i] + tex_nc[_j:]) if found else tex_nc
    missing_body = sorted(k for k, v in RELOCATED_TO_BODY.items() if v not in body)
    words = len(abstract.split())
    # the 263-word abstract is deliberate (round 23); 150 still catches a
    # truncated or mis-located environment, which is what this guard is for.
    scoped = found and words > 150
    return (found and scoped and not missing and not missing_body,
            {"found": found, "words": words, "scoped": scoped,
             "missing": missing, "total": len(ABSTRACT_HEDGES),
             "missing_body": missing_body, "total_body": len(RELOCATED_TO_BODY)})



# --- R32 (gate #115), C-72: THE MONTH AND TWO-WAY CLUSTER RUNGS ------------
# C-72's complaint was that the committed cluster unit on the floor read is
# cross-sectional only (4-way stratum), so a month-level common shock hitting
# every stratum at once is invisible to every rung of tab:ladder. Run
# floor_inference_correction_v3 re-clusters the SAME R2 read on the six
# calendar months the 2018 leg populates, and on both margins at once
# (Cameron-Gelbach-Miller), and the two rungs land in the ladder.
#
# The condition is discharged by PRICING the shock, not by dismissing it, and
# the two halves of that answer pull opposite ways -- which is exactly why they
# are pinned separately here. The month-clustered CR1 standard error comes in
# SMALLER than the stratum-clustered one (so that rung widens on its
# six-cluster reference distribution alone), while the Cameron-Gelbach-Miller
# two-way standard error comes in LARGER (so that rung widens because the
# variance genuinely rose). A tightening pass that kept only the first half
# would land "the common shock does not matter" one clause away from a row
# whose variance is a third higher. Both comparisons are asserted here against
# the artifacts, and the prose sentence that leads with "priced here rather
# than dismissed" is its own pinned span.
#
# Nothing numeric below is a manuscript literal. Every printed cell, every
# width, both standard-error ratios, the sign-vector count, the month support
# AND the ladder's own bookkeeping (how many undemoted rungs there are, which
# is narrowest, how many are censored at the grid edge) are DERIVED from the
# two committed artifacts -- because this landing moves four counting claims
# that were true before it and would go quietly false after it:
#
#   (i)   the Webb row's rank among the undemoted rungs (third of nine ->
#         fourth of eleven), and it is stated at TWO sites;
#   (ii)  how many rungs are censored at the 6.0% grid edge (two -> three) --
#         checked as a SET equality against the rungs printed wider than
#         CR2-BM, not as a count that could match by luck;
#   (iii) which rung is the widest with both endpoints interior -- CR2 at
#         Bell-McCaffrey df, UNCHANGED by this landing, and the gate proves
#         that rather than assuming it, because the month rung is the one that
#         could have falsified it;
#   (iv)  Section V.E's "the 2018 leg is read in August--December", which the
#         six-month support contradicted until the July disclosure landed.
#
# The three disclosures a tightening pass cuts first are pinned individually:
# the E3 attribution (the specification gave the cluster-count rationale AND
# pre-named the narrower-SE outcome, so neither is a discovered refutation),
# the E4 MISS (the printed month rung's lower edge is NOT censored; only its
# unprinted Rademacher variant reaches past the edge), and NC-1's substantive
# threshold (the realized Bell-McCaffrey df is below four even though the
# G < 5 trigger did not fire).
#
# Every word-for-count lookup goes through _CARD/_ORD, which fall back to
# digits: a drifted artifact must take this gate RED via a missing literal, not
# abort the whole run with a KeyError.

FICV2_RESULTS = (ROOT / "hazard" / "data"
                 / "floor_inference_correction_v2_results.json")
FICV3_RESULTS = (ROOT / "hazard" / "data"
                 / "floor_inference_correction_v3_results.json")

MONTH_TWOWAY_SPANS = {
    # the cluster units, named where a reader meets the rungs
    "caption_recluster": "the last two rungs re-cluster that same read on the "
                         "six calendar months it populates and on both margins "
                         "at once",
    # C-72's ACTUAL answer. Without this sentence the note reads as
    # "the shock does not matter", which the two-way rung refutes.
    "priced_not_dismissed": "so the month-level shock is priced here rather "
                            "than dismissed",
    # E3's attribution, corrected: SPEC_R32_c72 §5 gives the cluster-count
    # rationale verbatim ("31 clusters drop to at most 12"), so the prediction's
    # named channel is the channel that delivered.
    "e3_prediction_credit": "as I pre-committed it would and for the reason "
                            "the specification gave, the drop from 31 clusters "
                            "to six",
    # ...and the same spec bullet pre-named the narrower-SE outcome, so the
    # variance result is not a discovered refutation either.
    "e3_spec_allowed": "Its variance runs the other way, which that "
                       "specification allowed",
    # the narrower-SE half, scoped to the cluster unit it holds at
    "e3_mechanism": "so at this cluster unit the common shock adds no "
                    "variance, and the widening is the six-cluster reference "
                    "distribution alone",
    # E5: computability was a first-class branch, not a prediction
    "e5_not_predicted": "whether it would be computable at all I deliberately "
                        "did not predict",
    # E4, landed as the miss it is
    "e4_miss": "and it is not---both endpoints of the printed rung are "
               "interior, and of the two new rows only the two-way one censors",
    # ...with the one month-axis interval that DOES truncate named, so the
    # miss statement cannot be read past its own scope
    "rademacher_scope": "Among the month rung's own variants only the "
                        "unprinted Rademacher one reaches past that edge.",
    # NC-4: why Webb stays primary at this cluster unit
    "nc4_webb_primary": "which is why the Webb six-point weights are primary "
                        "here, as they are above",
    "run_credit_v3": "\\texttt{floor\\_inference\\_correction\\_v3}",
    # the claim this landing must leave standing, checked live below
    "widest_interior": "widest rung with both endpoints interior to the floor "
                       "grid---CR2 at Bell--McCaffrey degrees of freedom",
}

_ORDINAL_WORDS = {1: "first", 2: "second", 3: "third", 4: "fourth",
                  5: "fifth", 6: "sixth", 7: "seventh", 8: "eighth",
                  9: "ninth", 10: "tenth", 11: "eleventh", 12: "twelfth"}
_CARDINAL_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
                   6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
                   11: "eleven", 12: "twelve"}

_MONTH_NAMES = {"01": "January", "02": "February", "03": "March",
                "04": "April", "05": "May", "06": "June", "07": "July",
                "08": "August", "09": "September", "10": "October",
                "11": "November", "12": "December"}

# every interval object the month rung produces, printed or not
_MONTH_VARIANTS = ("cr1_t_interval", "cr1_t_interval_df_bm", "cr2_t_interval",
                   "cr2_t_interval_df_bm", "cr3_t_interval",
                   "cr3_t_interval_df_bm", "wild_t_rademacher", "wild_t_webb")


def _CARD(n):
    """Cardinal word, or the digits if the count leaves the prose's range --- a
    gate must go RED on a drifted artifact, never raise."""
    return _CARDINAL_WORDS.get(n, str(n))


def _ORD(n):
    return _ORDINAL_WORDS.get(n, f"{n}th")


def month_twoway_clusters_check(tex, v2, v3):
    """Gate #115's rule (R32, C-72), as a function so a battery can exercise it."""
    tex_nc = re.sub(r"(?<!\\)%.*", "", tex)
    rd = v2.get("reads", {}).get(FLOOR_LADDER_READ, {})
    mo = v3["rungs"]["month"]
    tw = v3["two_way"]
    e3 = v3["expectations"]
    G = v3["feasibility"]["G_month"]

    # The ELEVEN undemoted rungs tab:ladder prints. WHICH rungs the table shows
    # is a table-design fact and is listed here; every WIDTH and every
    # truncation flag below is the artifacts'.
    rungs = {
        "cr1": rd["cr1_t_interval"], "cr2": rd["cr2_t_interval"],
        "cr3": rd["cr3_t_interval"], "rademacher": rd["wild_t_rademacher"],
        "webb": rd["wild_t_webb"], "cr1_bm": rd["cr1_t_interval_df_bm"],
        "cr2_bm": rd["cr2_t_interval_df_bm"],
        "cr3_bm": rd["cr3_t_interval_df_bm"],
        "restricted": rd["wcr_inverted"], "month_cr1": mo["cr1_t_interval"],
        "two_way": tw["t_interval"],
    }

    def width(c):
        lo, hi = c["marginal_ci95_pp"]
        return hi - lo

    def censored(c):
        return bool(c["lower_pp_edge"]["truncated_at_grid_edge"]
                    or c["upper_pp_edge"]["truncated_at_grid_edge"])

    def cell(c):
        lo, hi = c["marginal_ci95_pp"]
        return f"${lo:+.1f}$ to ${hi:+.1f}$"

    rank = sorted(rungs, key=lambda k: width(rungs[k])).index("webb") + 1
    n_censored = sum(censored(c) for c in rungs.values())
    interior = {k: width(v) for k, v in rungs.items() if not censored(v)}
    widest_interior = max(interior, key=interior.get)
    # the note says the rungs printed WIDER than CR2-BM are exactly the
    # censored ones; that is a set identity, not a count coincidence
    printed_wider = {k for k, v in rungs.items()
                     if width(v) > width(rungs["cr2_bm"])}
    censored_set = {k for k, v in rungs.items() if censored(v)}
    stratum_only = {k: v for k, v in rungs.items()
                    if k not in ("month_cr1", "two_way")}
    stratum_censored = {k for k, v in stratum_only.items() if censored(v)}
    stratum_widest = set(sorted(stratum_only,
                                key=lambda k: width(stratum_only[k]))
                         [-len(stratum_censored):]) if stratum_censored else set()
    month_censoring = {k: bool(mo[k]["lower_pp_edge"]["truncated_at_grid_edge"]
                               or mo[k]["upper_pp_edge"]["truncated_at_grid_edge"])
                       for k in _MONTH_VARIANTS}
    shrink_pct = round((1 - mo["se_cr1_smm"] / rd["se_cr1_smm"]) * 100)
    grow_pct = round((tw["se_2way_smm"] / rd["se_cr1_smm"] - 1) * 100)
    rad = mo["wild_t_rademacher"]
    nc1_thresh = v3["not_computable"]["NC1_too_few_month_clusters"]["threshold"]
    months = v3["feasibility"]["months"]
    cmpm = v3["feasibility"]["cohort_months_per_month"]
    sparse = min(cmpm, key=cmpm.get)
    dense = [m for m in months if m != sparse]

    def name(m):
        return _MONTH_NAMES[m[4:]]

    lits = dict(MONTH_TWOWAY_SPANS)
    lits["month_row"] = (
        f"CR1 $t$, month clusters & {cell(mo['cr1_t_interval'])} & "
        f"$t({mo['cr1_t_interval']['df_used']:.0f})$, $G-1$ & "
        "wider on df alone")
    lits["two_way_row"] = (
        f"Two-way, stratum $\\times$ month & {cell(tw['t_interval'])} & "
        f"$t({tw['df_2way']})$, $\\min(G)-1$ & lower edge censored")
    lits["note_month_unit"] = (
        f"the month rung groups the {mo['n_cohort_months']} cohort-months by "
        f"the {_CARD(G)} calendar months the 2018 leg populates, "
        f"{name(months[0])} to {name(months[-1])}")
    # the artifact's own method string SUBTRACTS the intersection term; the
    # prose has to say so, because this note is the only place the reader is
    # told what the rung is
    lits["note_two_way_unit"] = (
        f"the two-way rung adds the CR1 variance clustered on the "
        f"{tw['G_stratum']} strata to the one clustered on those "
        f"{_CARD(tw['G_month'])} months and subtracts the one "
        f"clustered on their {tw['G_intersection_cells']} intersection cells")
    lits["two_way_df"] = f"$\\min(G)-1 = {tw['df_2way']}$"
    lits["e3_widths"] = (f"from {e3['E3_committed_cr1_width_pp']:.2f} to "
                         f"{e3['E3_month_cr1_width_pp']:.2f} points of width")
    lits["se_shrinks"] = (f"{shrink_pct}\\% \\emph{{smaller}} than the "
                          "stratum-clustered one")
    lits["se_grows_twoway"] = (f"{grow_pct}\\% \\emph{{above}} the "
                               "stratum-clustered one")
    lits["month_bm_below_four"] = (
        f"is {mo['df_bm_by_estimator']['cr1']:.1f}---below the "
        f"{_CARD(nc1_thresh - 1)} my pre-committed "
        "too-few-clusters rule was written to protect")
    lits["nc1_trigger_quiet"] = (f"that rule's own $G < {nc1_thresh}$ trigger "
                                 "did not fire")
    # Section V.E's month range, reconciled against the read's actual support
    lits["july_tail_disclosure"] = (
        f"read in {name(dense[0])}--{name(dense[-1])}---"
        f"{_CARD(cmpm[sparse])} {name(sparse)} cohort-months aside---")
    lits["nc4_sign_vectors"] = (f"$2^{{{G}}} = "
                                f"{int(rad['distinct_sign_vectors'])}$ "
                                "distinct Rademacher sign vectors")
    lits["nc4_floor"] = ("cannot resolve below "
                         f"$1/{int(round(1 / rad['resolution_floor_p']))}$")
    lits["webb_rank"] = (f"the {_ORD(rank)}-narrowest of the "
                         f"{_CARD(len(rungs))} undemoted rungs")
    lits["censored_count"] = (f"The {_CARD(n_censored)} rungs printed "
                              "wider still understate their own width")
    lits["two_widest_censored"] = (
        f"as the {_CARD(len(stratum_censored))} widest stratum rungs "
        "already are")

    missing = sorted(k for k, v in lits.items() if v not in tex_nc)
    ok = (
        not missing
        # the rank claim is made at BOTH sites, and no stale rank phrase is
        # left anywhere: every "undemoted rungs" in the file is the right one
        and tex_nc.count(lits["webb_rank"]) == 2
        and "undemoted rungs" not in tex_nc.replace(lits["webb_rank"], "")
        # the claim this landing must NOT have falsified
        and widest_interior == "cr2_bm"
        # "the three rungs printed wider still ... are censored to it"
        and printed_wider == censored_set
        # the censored stratum rungs really are its widest ones
        and stratum_censored == stratum_widest
        # E3 passed on width, at BOTH new cluster units
        and bool(e3["E3_month_widens"])
        and e3["E3_month_cr1_width_pp"] > e3["E3_committed_cr1_width_pp"]
        and width(rungs["month_cr1"]) > width(rungs["cr1"])
        and width(rungs["two_way"]) > width(rungs["cr1"])
        # ...and the two variance channels run OPPOSITE ways. Both halves, or
        # the note is a half-truth in whichever direction survives.
        and mo["se_cr1_smm"] < rd["se_cr1_smm"]
        and mo["t_crit_G_minus_1"] > rd["t_crit_G_minus_1"]
        and tw["se_2way_smm"] > rd["se_cr1_smm"]
        # NC-1's substantive threshold was crossed even though it did not fire
        and mo["df_bm_by_estimator"]["cr1"] < nc1_thresh - 1
        # E4 missed, and the two rows' truncation is as printed
        and e3["E4_upper_endpoint_truncates"] is False
        and not censored(rungs["month_cr1"])
        and censored(rungs["two_way"])
        and not rungs["two_way"]["upper_pp_edge"]["truncated_at_grid_edge"]
        # ...and the ONE month-axis interval that does truncate is the
        # unprinted Rademacher variant the note names
        and [k for k, v in month_censoring.items() if v] == ["wild_t_rademacher"]
        # feasibility was measured before any interval was read, and the
        # branches that would have forbidden a printed row did not fire
        and bool(v3["feasibility"]["computed_before_any_interval_was_read"])
        and bool(e3["E1_stratum_replay_bit_identical"])
        and bool(e3["E2_feasibility_before_outcome"])
        and bool(e3["E5_two_way_computability_not_predicted"])
        and bool(tw["computable"]) and tw["V_2way"] > 0
        and tw["df_2way"] == min(tw["G_stratum"], tw["G_month"]) - 1
        and not v3["not_computable"]["NC1_too_few_month_clusters"]["triggered"]
        and not v3["not_computable"]["NC2_two_way_variance_non_positive"]["triggered"]
        and not v3["not_computable"]["NC3_both_endpoints_off_grid"]["triggered"]
        and bool(v3["not_computable"]["NC4_rademacher_resolution_floor"]["triggered"])
        and v3["status"] == "OK"
        # P3: the substitution is visible, and it is the SAME read
        and mo["cluster_column_grouped_on"] == "month"
        and mo["n_clusters"] == G == len(v3["feasibility"]["months"])
        and mo["n_cohort_months"] == rd["n_cohort_months"]
        and abs(mo["point_cpr_pct"] - rd["point_cpr_pct"]) < 1e-12
        # the "two July cohort-months aside" disclosure is the support's own:
        # the sparse month is the first one and is an order of magnitude below
        # every other, and the per-month counts exhaust the read
        and sparse == months[0]
        and sum(cmpm.values()) == mo["n_cohort_months"]
        and cmpm[sparse] * 10 < min(cmpm[m] for m in dense)
    )
    return ok, {"missing": missing, "lits": lits, "G_month": G,
                "webb_rank": rank, "n_undemoted": len(rungs),
                "n_censored": n_censored, "widest_interior": widest_interior,
                "se_shrink_pct": shrink_pct, "se_grow_pct": grow_pct}


# --- Round-32 / C-78 (gate #119): THE EPISODE GRADIENT WITH LOAN AGE HELD
#     FIXED. Reads EPAGE_RESULTS and ECWITHIN_RESULTS (declared at :63).
EPISODE_AGE_BANDS_SPANS = {
    # (1) the clause C-78 was written against, now naming the dimension.
    "age_named_in_the_clause": "loan age now among them",
    # (2)-(4) the three sentences that carry the result AGAINST this paper.
    # These are what a later tightening pass would trim first, so they are
    # pinned as prose and not only as numbers.
    "point_survives_interval_does_not":
        "The interval moves against the exhibit even as the point survives",
    "branch_reclassified": "from a gap that persists to one that closes",
    "no_longer_separated":
        "the gradient is no longer separated from the model's implication by "
        "its own sampling interval",
    # (5) the E3 miss, which is what makes the age control a real control
    # rather than a relabelling of vintage. HEDGED WORDING, pinned hedged:
    # 60.6% of shallow exposure still sits in single-band vintages, so the
    # honest claim is "not MERELY a relabelling", and that is what is bound.
    "collinearity_miss_named":
        "age is not merely a relabelling of vintage in this book",
    # (6) SPEC section 8.3 -- the one scope limit the spec commits to STATING
    # in the manuscript rather than delegating to the artifact: the age cut is
    # held, not swept. C-92 (the floor's flatness in loan age) is still open,
    # so a reader must not be able to over-read this run as having tested the
    # cut's location.
    "age_cut_held_disclosed":
        "stratifies above the cut rather than testing where it sits",
    # (7)-(8) gate #75's RAW literals, asserted here as well. Spec section 7
    # Branch A: gate #75 is EXTENDED, never replaced, and the raw exhibit
    # staying raw under this landing is the property being protected.
    # DELIBERATE DOUBLE-PIN: a round that legitimately moves the raw numbers
    # now fails BOTH gates. Same hazard class as
    # BUYBACK_BRACKET_SPANS["reversal_range"] vs LETTER_CURRENT_LITERALS.
    # Recorded in TECHNICAL section 49 and in the C-78 ledger row so the next
    # round finds both sites.
    "raw_gradient_survives_gate_75": "$+4.20$ CPR points",
    "raw_ci_survives_gate_75": "$[+3.59, +4.66]$",
}


def episode_age_bands_check(tex: str, a: dict, w: dict) -> tuple[bool, dict]:
    """Gate #119's rule (R32, C-78): the episode gradient with loan age held fixed.

    C-78 put 12-month loan-age strata into the standardization cell that
    .tex:331's hedge was written against. Two results came back and BOTH have to
    stay in the manuscript, which is the entire reason this gate exists.

    (i) The POINT survives. The standardized gradient is still well clear of the
    model-implied value with age in the cell, and the identity limb puts only a
    small slice of the raw gradient on age composition.

    (ii) The INTERVAL does not. The age-augmented 95% CI COVERS the implied
    value where the committed one excluded it, which on
    episode_confrontation_within's own pre-committed branch map (that runner,
    lines 202-216) is "GAP CLOSES MATERIALLY", not "GAP PERSISTS".

    (ii) is the finding that costs this paper, so it is bound three ways: the
    printed interval is DERIVED here from the artifact; the coverage SENTENCE is
    a pinned span; and the coverage PROPERTY (lo <= implied <= hi, with the
    committed lo > implied) is RECOMPUTED here rather than trusted. If a rerun
    ever moved the CI back off the implied value the gate fails and forces the
    sentence to change instead of leaving a false claim standing; if an editor
    deletes the sentence it fails too.

    Every numeric literal is derived -- the new numbers from the age-band
    artifact, the contrast pair ($+3.44$, $[+1.17, +5.14]$) from the COMMITTED
    within artifact -- so the two runs cannot drift apart in print. G7's
    selection parity is likewise tied LIVE to the committed run's own selection
    counts rather than to literals written here.

    SCOPE. This gate covers the spec's Branch A landing and nothing more: the
    .tex:331 clause, a tab:runindex row, this gate, its battery. tab:assembly's
    composition row and Section V.E's sixth qualification are NOT touched and
    NOT pinned here -- re-scoping either is Branch C's disposition and is
    posture-adjacent besides (episode_confrontation_within.py:208-210 marks that
    assembly row "Eugene signs"). Both stay true as written: the assembly row
    prints the COMMITTED run's point ($+3.4$ vs implied $+0.9$, "above
    (directional)") and carries no interval, and the sixth qualification
    attributes its $+3.44$ to that same run in the same parenthesis. The
    interval claim landed here is scoped to the age-augmented cell in its own
    sentence, so it contradicts neither.

    One artifact property is asserted with NO printed counterpart: se_pp rising
    against the committed run. Nothing in the manuscript says "noisier" -- the
    percentile interval NARROWS in width (3.748 vs 3.971 points) while shifting
    down, so no widening or noise claim is made anywhere and none is gated. The
    assertion is kept as a cheap drift tripwire, redundant with the printed
    interval (both come out of the same bootstrap), and it is documented here so
    a later round does not mistake it for the anchor of a word.
    """
    tex_nc = re.sub(r"(?<!\\)%.*", "", tex)
    missing = [f"span:{k}" for k in sorted(EPISODE_AGE_BANDS_SPANS)
               if EPISODE_AGE_BANDS_SPANS[k] not in tex_nc]

    la, lb = a["limb_a"], a["limb_b"]
    wla = w["limb_a"]
    g = la["standardized_gradient_pp"]
    lo, hi = la["ci95_pp"]
    iw = la["imputed_weight_share"]
    wg = wla["standardized_gradient_pp"]
    wlo, whi = wla["ci95_pp"]
    impl = a["committed_reference"]["model_implied_pp"]
    total = lb["full_cell_committed"]["total_pp"]
    com_b = lb["full_cell_committed"]["between_composition_pp"]
    age_b = lb["age_only"]["between_composition_pp"]
    aug_b = lb["age_augmented_full"]["between_composition_pp"]
    bm = a["age_bands"]["band_months"]
    e = a["expectations"]

    lits = {
        "band_width":
            f"adding {bm}-month age bands to the standardization cell" in tex_nc,
        "age_point": f"leaves the gradient at ${g:+.2f}$ points" in tex_nc,
        # the manuscript's PRE-EXISTING +3.44 sentence, re-derived here from the
        # committed artifact so the two runs cannot drift apart in print
        "committed_point": f"leaves the gradient at ${wg:+.2f}$ points" in tex_nc,
        # one contextual literal for the age-only limb: the component, the total
        # it is a share of, and the share itself, in the order they are printed
        "age_only_and_share": (
            f"puts ${age_b:+.2f}$ of the raw ${total:+.2f}$ --- "
            f"${age_b / total * 100:.1f}\\%$ --- on seasoning composition") in tex_nc,
        "composition_moves": (
            f"moving total composition from ${com_b:+.2f}$ to "
            f"${aug_b:+.2f}$") in tex_nc,
        # the whole CI claim in one derived literal: the age interval, its
        # imputed weight, the coverage, and the committed interval it displaces
        "age_ci_and_coverage": (
            f"it runs $[{lo:+.2f}, {hi:+.2f}]$ (imputed weight share "
            f"${iw * 100:.1f}\\%$), covering the implied ${impl:+.2f}$ where "
            f"the committed $[{wlo:+.2f}, {whi:+.2f}]$ excluded it") in tex_nc,
        "collinearity_bar": (
            f"at least ${e['E3_collinearity_min'] * 100:.0f}\\%$ of the "
            f"primary selection's shallow exposure") in tex_nc,
        "collinearity_measured":
            f"the realized share is ${e['E3_measured'] * 100:.1f}\\%$" in tex_nc,
        "runindex_row": (
            f"seasoning composition at ${age_b:+.2f}$ of ${total:+.2f}$, and an "
            f"age-augmented interval that covers the model-implied "
            f"${impl:+.2f}$") in tex_nc,
        # two sites: the .tex:331 prose and the tab:runindex row
        # SCOPED, not counted. This was count(tag) >= 2, calibrated when the tag
        # sat at exactly two sites; a third citation (the tab:assembly Status
        # cell) made removing any ONE of them leave the threshold satisfied, so
        # the removal test stopped biting. The prose/assembly citation form and
        # the tab:runindex row are now checked separately -- runindex_row pins
        # the row's own text -- so neither can be dropped behind the other and
        # the rule survives a fourth citation.
        "run_tag": "(run \\texttt{episode\\_gradient\\_age\\_bands})" in tex_nc,
    }
    missing += sorted(k for k, v in lits.items() if not v)

    pg = a["parity_gates"]
    sel, wsel = pg["G7_selection_parity"], w["selection"]
    covers = bool(lo <= impl <= hi)
    excluded = bool(wlo > impl)
    art_ok = (
        a["status"] == "OK"
        and a["branch_landed"] == "A"
        and all(bool(v) for v in pg["G0_G4"].values())
        and bool(pg["G5_frozen_artifact_reproduction"])
        and all(bool(v["exact"])
                for v in pg["G6_axis_machinery_reproduces_committed"].values())
        # G7 tied live to the committed run's own selection, not to literals
        and all(sel[k] == wsel[k] for k in ("n_strata_total", "n_strata_bucketed",
                                            "n_strata_primary", "n_rows_primary"))
        # E2, STOP-class: the decomposition telescopes on EVERY axis reported,
        # and every axis decomposes the SAME total
        and all(abs(v["identity_residual"]) < 1e-12 for v in lb.values())
        and all(abs(v["total_pp"] - total) < 1e-12 for v in lb.values())
        and bool(e["E4_pass"]) and bool(e["E5_standardized_above_bar"])
        # the two readings the prose states, recomputed here rather than trusted
        and covers                      # the age-augmented CI COVERS the implied
        and excluded                    # the committed CI EXCLUDED it
        and g > impl                    # the point still stands above the model
        and g > a["committed_reference"]["half_raw_bar_pp"]
        # drift tripwire only -- redundant with the printed interval, and NO
        # printed word depends on it (see the docstring)
        and la["se_pp"] > wla["se_pp"]
        # E3 missed, and missed in the direction that makes the control real
        and e["E3_pass"] is False
        and e["E3_measured"] < e["E3_collinearity_min"]
        # the spec section 8.3 disclosure the prose now carries, tied to the
        # artifact: AGE0_MIN held at production, bands cut on one date, and the
        # within-stratum limit still declared
        and a["spec"]["age_cut_held"] == 24
        and bool(a["spec"]["bands_cut_on_one_date"])
        and "NOT COMPUTABLE" in a["spec"]["not_within_stratum"]
    )
    return (not missing) and art_ok, {
        "missing": missing,
        "artifact_ok": art_ok,
        "age_point_pp": round(g, 4),
        "age_ci_pp": [round(lo, 4), round(hi, 4)],
        "covers_implied": covers,
        "committed_excluded": excluded,
        "age_only_share_pct": round(age_b / total * 100, 2),
    }


# --- R32 / C-77 artifacts (gate #118). TWO of them on purpose: the committed
# max-form run is read SEPARATELY so the new artifact cannot certify its own
# comparator. These may sit with the other *_RESULTS constants (after
# DLS_RESULTS, tools/liveness_gates.py:63) or here; both are module level and
# evaluated before main() either way.
SNHAADD_RESULTS = (ROOT / "hazard" / "data"
                   / "scaled_null_housing_activity_additive_results.json")
SNHAMAX_RESULTS = (ROOT / "hazard" / "data"
                   / "scaled_null_housing_activity_results.json")


# --- R32 / C-77 (gate #118): THE ALADANGADY CALIBRATION IS FORM-CONDITIONAL --
# The housing-activity reconciliation was solved only under the production
# hard-maximum floor form, and the tab:assembly row carried its +0.9 as though
# the reading were form-invariant. Re-solved under the additive form (run
# scaled_null_housing_activity_additive) the root barely moves at the headline
# floor -- 0.756 against 0.754 -- while the surviving marginal lands at +8.5
# points at BOTH anchors (8.4912 and 8.5227). So the calibration documents an
# upward bias under either form, and only WHERE the corrected member falls is a
# form choice.
#
# Four things this gate binds past presence, because each is a way this landing
# could go wrong quietly:
#
# (i)   PLACEMENT. +8.5 sits in the UPPER half of the +2.9 to +8.7 binding
#       interval -- INSIDE it, about 0.2 below the upper edge, NOT above it.
#       Gate #98 pins "every correction listed above falls in its lower half",
#       a claim scoped to the ladder ABOVE the binding-interval sentence, so
#       writing this member up into that ladder would falsify a pinned sentence
#       without editing it. The ordering assert requires the passage to appear
#       AFTER the lower-half sentence and AFTER the counterweight clause it
#       belongs with; in_paragraph requires it to stay inside the seventh-
#       qualification paragraph rather than escape into a new one.
# (ii)  THE MECHANISM. What separates the forms is censoring, not a slacker
#       floor: the floor exceeds the volitional hazard NO LESS OFTEN at the
#       additive root (0.9480) than at the max root (0.9444) -- it simply stops
#       truncating. That comparison is asserted against the two artifacts
#       rather than printed, because "94.8\%" already denotes the null leg's
#       100-PSA recovery share in this same paragraph and a second referent for
#       it would be a trap for a later reader.
# (iii) NO BARE NUMERALS. Every printed literal is checked inside the clause it
#       belongs to. "$+0.9$", "$+3.5$", "$+5.6$" and "$+11.2$" each already
#       occur at unrelated sites ("$+0.9$ to $+15.6$", "$+3.5$ to $+13.1$", the
#       headline, the tab:uncertainty note at .tex:474), so a bare-numeral
#       check would pass on a manuscript that had lost the sentence it was
#       meant to pin. That is the hole the C-77 verifier found in the draft.
# (iv)  THE COMPARATOR. The max-form legs are read from the COMMITTED max run,
#       never from the additive run's copy of them; the copy is checked against
#       it to the bit, and the committed file's BYTES are checked against the
#       sha the additive run recorded for what it was scored against. If the
#       max run is ever re-run this gate fails loudly rather than silently
#       comparing a stale +0.9.
#
# NOTE: the additive run tag CONTAINS the max tag as a stem, so every tag
# comparison here closes the brace -- "...activity\_additive}" does not contain
# "...activity}". A battery test asserts that property, because the next gate to
# count either tag will get it wrong otherwise.
SNHA_ADDITIVE_PROSE = "Re-solving the same condition under the additive form"


def snha_additive_check(tex, a, mx, max_bytes):
    """Gate #118's rule (R32, C-77), as a function so the battery exercises THE
    SHIPPED RULE rather than a copy of it (gate #68's header explains why that
    distinction is not pedantry).

    a         -- the additive re-solve's artifact.
    mx        -- the COMMITTED max-form artifact, parsed from max_bytes.
    max_bytes -- its raw bytes, so the comparator can be sha-pinned against the
                 additive run's own P0 record of what it was scored against.

    hashlib is imported locally rather than at module scope on purpose: this
    landing is one of six applied in the same wave and the shared import block
    is the one place they would collide.
    """
    import hashlib
    tex = re.sub(r"(?<!\\)%.*", "", tex)
    r4, r5 = a["roots_additive"]["4"], a["roots_additive"]["4.991"]
    c4, c5 = a["committed_max_form"]["4"], a["committed_max_form"]["4.991"]
    m4, m5 = mx["root"]["4"], mx["root"]["4.991"]
    prod_phi1_pp = mx["ladder"]["4.991|1"]["marginal_pp"]
    add_phi1_pp = r5["additive_marginal_at_phi1_pp"]
    lits = {
        # the PRE-EXISTING production pair the landing now leans on
        "max_pair": (f"the marginal at $+{m5['marginal_pp']:.1f}$ points at the "
                     f"headline floor and $+{m4['marginal_pp']:.1f}$ at the "
                     "in-sample calibration") in tex,
        # the landing's own passage
        "both_anchors": f"$+{r5['marginal_pp']:.1f}$ points at both anchors" in tex,
        "roots_pair": (f"$\\phi^{{*}} = {r5['phi_star']:.3f}$ against "
                       f"${m5['phi_star']:.3f}$ at the headline floor") in tex,
        "e3_bar": (f"clearing the $+{a['expectations']['E3_bar_pp']:.1f}$-point "
                   "bar fixed before the run") in tex,
        "cut_additive": (f"cuts the additive form's own $+{add_phi1_pp:.1f}$ to "
                         f"$+{r5['marginal_pp']:.1f}$") in tex,
        "cut_production": (f"the production form's $+{prod_phi1_pp:.1f}$ to "
                           f"$+{m5['marginal_pp']:.1f}$") in tex,
        "where_it_lands": ("above the headline at both anchors and near the top "
                           "of the quoted interval under the additive form") in tex,
        "censoring_share": (f"pinned to the floor in "
                            f"{m5['floor_bind_share'] * 100:.1f}\\% of evaluated "
                            "loan-months and the maximum truncates") in tex,
        "never_truncates": "combines the two hazards on the survival scale" in tex,
        "dominates_no_less": "dominates no less often at the additive root" in tex,
        "placement": ("belongs with the counterweights above rather than with "
                      "the ladder") in tex,
        # the scope repairs a landing may not lose
        "both_forms_biased": "documents an upward bias under both forms" in tex,
        "production_scoped": ("under the production form the corrected member "
                              "lies below the headline") in tex,
        "intro_counterpart": ("re-solved under the additive form, the calibrated "
                              "companion below moves it up instead") in tex,
        "counterweight_pointer": ("the housing-activity calibration below, "
                                  "re-solved under that form, joins them") in tex,
        # +8.5 is INSIDE the interval, so the paragraph's closing clause had to
        # stop saying the counterweights sit above it
        "closing_scoped": ("the form-side counterweights sit at its top or "
                           "above it") in tex,
        # the tab:assembly row -- the edit the condition names, in three cells
        "row_both_numbers": (f"$+{m5['marginal_pp']:.1f}$ (max) / "
                             f"$+{r5['marginal_pp']:.1f}$ (additive)") in tex,
        "row_vs_cell": "below the interval / above the headline" in tex,
        "row_form_conditional": ("form-conditional scaled-null variant; "
                                 "upward-bias entry under both forms") in tex,
        "row_roots": (f"roots $\\phi^{{*}} = {m5['phi_star']:.3f}$ and "
                      f"${r5['phi_star']:.3f}$ at the headline floor") in tex,
        "run_tag": "\\texttt{scaled\\_null\\_housing\\_activity\\_additive}" in tex,
    }
    # (i) the additive member is written WITH the counterweights, after the
    #     lower-half posture it would otherwise falsify
    i_low = tex.find("every correction listed above falls in its lower half")
    i_ctr = tex.find("the housing-activity calibration below, re-solved under "
                     "that form, joins them")
    i_add = tex.find(SNHA_ADDITIVE_PROSE)
    ordered = -1 < i_low < i_ctr < i_add
    paras = [ln for ln in tex.split("\n") if ln.startswith(ASSEMBLY_OPENER)]
    in_paragraph = (len(paras) == 1 and SNHA_ADDITIVE_PROSE in paras[0]
                    and ("belongs with the counterweights above rather than "
                         "with the ladder") in paras[0])
    # the run's own gates: a landing may not survive its own failures
    roots_ok = all((not r["no_root"]) and r["converged"]
                   and abs(r["residual_b"]) <= r["tolerance_b"]
                   for r in (r4, r5))
    pg = a["parity_gates"]
    parity_ok = (
        all(v["pass"] for v in pg["P1_additive_endpoint_parity"].values())
        and all(v["pass"] for v in pg["P2_max_form_parity"].values())
        and pg["P3_baseline_identity"]["vs_h0_psa"] == 0.0
        and pg["P3_baseline_identity"]["vs_baseline_hazard"] == 0.0
        and pg["P4_restoration_and_bind_anchor"]["restored"] is True
        and abs(pg["P5_ratio_recomputed"] - 1.272727272727273) < 1e-12
        and abs(pg["P5_floor_read_live_pct"] - 4.991) < 1e-9)
    # (iv) the comparator is the COMMITTED max run, by value AND by bytes
    tie = all(abs(c[k] - m[k]) < 1e-12
              for c, m in ((c4, m4), (c5, m5))
              for k in ("phi_star", "marginal_pp", "floor_bind_share",
                        "required_lift_b"))
    sha_ok = (hashlib.sha256(max_bytes).hexdigest()
              == pg["P0_sha_pins"]["hazard/data/"
                                   "scaled_null_housing_activity_results.json"])
    # (ii) the two claims that are arguments rather than literals
    floor_invariant = f"{r4['marginal_pp']:.1f}" == f"{r5['marginal_pp']:.1f}"
    no_less_often = r5["floor_bind_share"] >= m5["floor_bind_share"]
    ok = (all(lits.values()) and ordered and in_paragraph and roots_ok
          and parity_ok and tie and sha_ok and floor_invariant and no_less_often
          and bool(a["expectations"]["E2_root_exists_both_floors"])
          and bool(a["expectations"]["E3_pass"]))
    return ok, {"missing": sorted(k for k, v in lits.items() if not v),
                "ordered": ordered, "in_paragraph": in_paragraph,
                "cross_artifact_tie": tie, "comparator_sha_ok": sha_ok,
                "floor_invariant": floor_invariant,
                "additive_pp": (round(r4["marginal_pp"], 4),
                                round(r5["marginal_pp"], 4)),
                "bind_max_then_additive": (round(m5["floor_bind_share"], 4),
                                           round(r5["floor_bind_share"], 4))}


1# --- R32 C-74 (gate #116): THE GINNIE SHARE'S GAP RESPONSE, BRACKETED ------
# The committed overlay scores the 20.4% Ginnie face share by the observed
# Ginnie speed in BOTH Path B legs, so that share's central-minus-null
# difference is exactly zero and the marginal correction is pure
# conventional-share scaling (0.797x). C-74 asks for a WEAKER Ginnie marginal
# MEASURED rather than NONE ASSUMED. What this design can deliver is a bracket,
# not a measurement, and the two ways the exhibit can be overclaimed are exactly
# what a concision pass would cut, so both are pinned:
#
#   (a) THE RISE IS FORCED. A share contributing exactly zero must contribute
#       more at any positive response, so the corrected scaling exceeds the
#       committed 0.797x by arithmetic. Reporting that as a finding would repeat
#       the error the paper already names about its own headline sign.
#   (b) A LEVEL DOES NOT IDENTIFY A SLOPE. The measured object is a level
#       difference in voluntary speed at the same window rate path; the
#       elasticity is a slope; the mapping between them is assumed. The BRACKET
#       is the result and no cell in it is a measured Ginnie marginal.
#
# The two paths below belong with the other *_RESULTS constants near the top of
# the module (OVERLAY_RESULTS is line 45); they sit here only so the gate lands
# as one contiguous block.
GINNIEATT_RESULTS = (ROOT / "hazard" / "data"
                     / "ginnie_overlay_attenuated_results.json")
GINNIEOFF_RESULTS = (ROOT / "hazard" / "data"
                     / "ginnie_overlay_offwindow_results.json")

# PROSE spans, and deliberately so. They are pinned to the ONE line carrying
# both the run tag and the 0.797 clause, so relocating an honesty clause to a
# footnote fails the gate even when the words survive elsewhere in the file.
# Every NUMBER this gate checks is derived inside the check from the run
# artifact and tied live to the two COMMITTED Ginnie artifacts, so no cell
# literal lives in this file and a rerun that moved a cell cannot be papered
# over by editing a dict.
GINNIE_ATTENUATED_SPANS = {
    # the construction, and that it is a transplant rather than a
    # Ginnie-specific estimate (spec SS8.2 -- without this the bracket reads as
    # a measurement on Ginnie collateral, which this design cannot deliver)
    "transplant": "transplanted, not estimated on Ginnie collateral",
    "identity_defines_the_fraction": "with the wedge fixed by requiring that a "
                                     "full-strength Ginnie response return the "
                                     "un-overlaid marginal",
    # HONESTY CONSTRAINT (b): a LEVEL does not identify a SLOPE. Four spans,
    # because the failure mode is a later pass keeping the numbers and dropping
    # the scope, after which a reader quotes one cell as the measured Ginnie
    # marginal.
    "level_scope": "a level, and a voluntary-only one",
    "level_not_slope": "An elasticity is a slope, and nothing here maps a level "
                       "onto one",
    "bracket_not_chosen": "so I bracket the mapping rather than choose it",
    "no_single_cell": "none of the four is a measured Ginnie marginal",
    # spec SS8.3: the published series is full-universe Ginnie collateral while
    # SOMA's holdings are seasoned and low-coupon, so the overlay if anything
    # OVERSTATES the correction. That direction carries into the speed ratio.
    "full_universe_overstatement": "read off the same full-universe series with "
                                   "the same overstatement",
    # the open sign was pre-authorised BOTH ways (spec SS5 E4); if the a > 1
    # reading is quoted it must be labelled amplification, not re-described as
    # attenuation (spec SS7 Branch C)
    "amplification_named": "which is amplification, not attenuation",
    # HONESTY CONSTRAINT (a): the rise above the committed scaling is FORCED.
    # Dropping this turns a tautology into a finding -- the same error the paper
    # already names about its own headline sign.
    "rise_is_forced": "is arithmetic, not evidence",
    "forced_mechanism": "a share contributing exactly zero must contribute more "
                        "at any positive response",
    "rest_nothing_on_it": "and I rest nothing on it",
    # the supplement SCOPES the committed +4.4 estimand; it does not correct it
    "scopes_not_corrects": "stands unrevised, scoped by the bracket rather than "
                           "corrected by it",
}

# WHOLE-FILE spans: the cross-reference the bracket adds at the assumability
# sentence in SS I, and the hedge that sentence's next clause carries. They are
# pinned TOGETHER on purpose. The cross-reference without "ceilings, not sizes"
# would read as SIZING the assumption carve-out, and nothing in this design
# measures realized take-up (spec SS8.5). The spec's Branch A wording -- "so the
# carve-out is small" -- was therefore NOT landed; this pair is what replaces it.
GINNIE_ATTENUATED_FILE_SPANS = {
    "assumability_link": "to bracket what a Ginnie share that is not gap-inert "
                         "would contribute, on a mapping it assumes rather than "
                         "measures",
    "ceilings_not_sizes": "Both bounds are ceilings, not sizes",
}


def ginnie_attenuated_check(tex, g, ov, gof):
    """Gate #116's rule (R32, C-74): the Ginnie share's gap response, bracketed.

    Every printed literal is DERIVED here from the run artifact, and the a = 0
    cell is tied LIVE to both committed Ginnie artifacts at full precision, so a
    rerun that moved any cell cannot leave a stale digit in SS V.B and a wrong
    number cannot be introduced by editing this file alone.

    Beyond presence this binds the exhibit's two honesty constraints AND THEIR
    ORDER, because each is what a concision pass would cut and each is the
    difference between a scoped bracket and an overclaim:

    (i) THE RISE IS FORCED. Under the committed overlay the Ginnie share
    contributes exactly zero marginal, so the corrected scaling exceeds the
    committed 0.797x for every positive response, by arithmetic.

    (ii) A LEVEL DOES NOT IDENTIFY A SLOPE. What the series measures is a level
    difference in voluntary speed at the same window rate path; the elasticity
    is a slope; nothing maps one onto the other. The BRACKET is the result and
    no single cell is a measured Ginnie marginal.

    The printed sequence must come first, then (i), then (ii): a rewrite that
    leads with the bracket verdict and buries the forced-rise disclaimer after
    it reads as a finding followed by a hedge, which is the reverse of what the
    spec commits to. That order is asserted, not just the presence.

    A third span keeps this a SCOPING of the committed 0.797x estimand rather
    than a correction of it: the +4.4 overlay member is accurate as printed and
    stays unrevised.

    The printed 0.797x is NOT typed here. It is rebuilt from the in-sample
    scaling (marginal(0) / M_full = 0.797226 -> "0.797"), and the off-window
    scaling is separately asserted to agree with it to better than 5e-4, which
    is finer than the printed precision. The manuscript's own off-window value
    is 0.797518, which rounds to 0.798; the paper prints 0.797 at five sites and
    that pre-existing rendering is not this gate's to change.

    The run tag is separately required to occur at least twice (prose +
    tab:runindex), and the two whole-file spans keep the SS I cross-reference
    and its hedge alive together.
    """
    tex_nc = re.sub(r"(?<!\\)%.*", "", tex)
    tag = "\\texttt{ginnie\\_overlay\\_attenuated}"
    lines = [ln for ln in tex_nc.split("\n") if tag in ln and "0.797" in ln]
    info: dict = {"prose_lines": len(lines)}
    if len(lines) != 1:
        return False, {**info, "missing": ["prose_line"], "artifact_ok": None,
                       "ordered": None, "in_sample_pp": [], "off_window_pp": [],
                       "E3_pass": None}
    line = lines[0]

    order = ("M0_committed", "M2_primary_1_over_r", "M1_no_differential",
             "M3_amplification_r")
    ins, off = g["bracket_in_sample"], g["bracket_off_window"]
    ins_pp = [ins[k]["marginal_pp"] for k in order]
    off_pp = [off[k]["marginal_pp"] for k in order]
    a0 = ins["M0_committed"]["a"]
    a2 = ins["M2_primary_1_over_r"]["a"]
    a1 = ins["M1_no_differential"]["a"]
    a3 = ins["M3_amplification_r"]["a"]
    m, p, e = g["measurement"], g["parity"], g["expectations"]
    r = m["speed_ratio_r_freddie"]
    conv_off = gof["conventional_offwindow"]["marginal_pp"]
    scale_off0 = gof["marginal_scale_vs_conventional"]
    scale_ins0 = ins_pp[0] / m["m_full_in_sample_pp"]

    def seq(v):
        return f"${v[0]:+.1f}$, ${v[1]:+.1f}$, ${v[2]:+.1f}$ and ${v[3]:+.1f}$"

    lits = {k: v in line for k, v in GINNIE_ATTENUATED_SPANS.items()}
    lits.update({k: v in tex_nc
                 for k, v in GINNIE_ATTENUATED_FILE_SPANS.items()})
    lits.update({
        "in_sample_sequence": f"{seq(ins_pp)} points across those four" in line,
        "off_window_sequence": seq(off_pp) in line,
        "grid_attenuated": f"${a2 * 100:.1f}$\\% of the conventional response" in line,
        "grid_unit": f"${a1 * 100:.0f}$\\% (no differential)" in line,
        "grid_amplified": (f"${a3 * 100:.1f}$\\% (proportional-hazard "
                           "preservation") in line,
        "ratio_stated": f"${r:.3f}$ times as fast" in line,
        "ratio_in_rationale": f"a book running ${r:.3f}$ times faster" in line,
        "differential": (f"runs ${m['crr_differential_ginnie_minus_freddie_pp']:.2f}$ "
                         "points above Freddie's") in line,
        "window_months": f"the window's {p['P2_window_months']} months" in line,
        "forced_scale_literal": (f"rises above the committed ${scale_ins0:.3f}\\times$ "
                                 "at every positive response") in line,
        # SCOPED to the index row itself. In tab:runindex a row OPENS with the
        # tag followed by " & "; in prose and in tab:assembly the tag appears as
        # "(run <tag>)". So this binds the index entry regardless of how many
        # times the run is cited elsewhere -- the count >= 2 it replaces went
        # blind the moment a third citation landed.
        "run_tag_indexed": (tag + " & ") in tex_nc,
    })

    # the printed differential and ratio must fall out of the window means the
    # run recorded, not out of a constant
    wm = p["P2_window_mean_crr_pct"]
    derived_ok = (
        abs((wm["ginnie"] - wm["freddie"])
            - m["crr_differential_ginnie_minus_freddie_pp"]) < 1e-9
        and abs(wm["ginnie"] / wm["freddie"] - r) < 1e-9
    )
    # the grid is 0, 1/r, 1, r -- derived, so a runner that hard-coded 0.814
    # would fail here
    a_grid_ok = (a0 == 0.0 and a1 == 1.0
                 and abs(a2 * r - 1.0) < 1e-9 and a3 == r)
    # THE PARITY ANCHOR, live and cross-artifact: the a = 0 cell IS the committed
    # overlay at both calibrations, bit for bit, and its off-window ratio IS the
    # 0.797 scaling the committed run wrote
    anchor_ok = (ins_pp[0] == ov["variants"]["crr_only"]["marginal_pp"]
                 and off_pp[0] == gof["overlay_offwindow"]["primary"]["marginal_pp"]
                 and abs(p["P1_crr_only_marginal_pp"]
                         - ov["variants"]["crr_only"]["marginal_pp"]) < 1e-12
                 and abs(off_pp[0] / conv_off - scale_off0) < 1e-12)
    # the identity that makes the fraction mean what its name says: a full
    # response returns the un-overlaid marginal at BOTH calibrations, and the
    # off-window arm is bound to the committed run's own conventional leg
    ident = p["P3_marginal_at_a1_vs_M_full"]
    tol = ident["tol_pp"]
    identity_ok = (abs(ident["in_sample"][0] - ident["in_sample"][1]) <= tol
                   and abs(ident["off_window"][0] - ident["off_window"][1]) <= tol
                   and abs(ins_pp[2] - m["m_full_in_sample_pp"]) <= tol
                   and abs(off_pp[2] - conv_off) <= tol)
    # monotone, and every SCALING past the first strictly above it: the
    # arithmetic the prose calls forced, re-derived rather than read off a flag,
    # and compared multiplier-to-multiplier as the prose now states it
    mono = (all(x < y for x, y in zip(ins_pp, ins_pp[1:]))
            and all(x < y for x, y in zip(off_pp, off_pp[1:])))
    s_ins = [x / m["m_full_in_sample_pp"] for x in ins_pp]
    s_off = [x / conv_off for x in off_pp]
    forced = (all(s > s_ins[0] for s in s_ins[1:])
              and all(s > s_off[0] for s in s_off[1:]))
    # the printed 0.797 stands for both calibrations; they must agree inside the
    # printed precision or the single literal is misleading
    scale_agreement_ok = abs(scale_off0 - scale_ins0) < 5e-4

    # ORDER: numbers, then the forced-rise disclaimer, then the bracket verdict
    i_seq = line.find(seq(off_pp))
    i_forced = line.find(GINNIE_ATTENUATED_SPANS["rise_is_forced"])
    i_cell = line.find(GINNIE_ATTENUATED_SPANS["no_single_cell"])
    ordered = -1 < i_seq < i_forced < i_cell

    art_ok = (
        bool(p["P0b_artifacts_byte_identical"])
        and p["P2_window"] == ["2022-06", "2025-11"]
        and p["P2_window_months"] == 42
        and abs(p["P4_comparator_shift_pp"]) < p["P4_tol_pp"]
        and derived_ok and a_grid_ok and anchor_ok and identity_ok
        and mono and forced and scale_agreement_ok
        and bool(e["E1_a0_reproduces_committed_overlay"])
        and bool(e["E2_monotone_in_a"])
        and bool(e["E5_rise_is_forced_not_a_finding"])
        and bool(g["spec"]["no_engine_runs"])
    )
    ok = all(lits.values()) and art_ok and ordered
    return ok, {**info,
                "missing": sorted(k for k, v in lits.items() if not v),
                "artifact_ok": art_ok,
                "ordered": ordered,
                "in_sample_pp": [round(v, 4) for v in ins_pp],
                "off_window_pp": [round(v, 4) for v in off_pp],
                "E3_pass": bool(e["E3_pass"])}


# --- R32 C-75 (gate #117): THE RE-DERIVED BUYBACK DISCOUNT -----------------
# The committed bracket's discount was ASSERTED: buyback_credit_bracket.py:107
# hard-codes D_GRID = [0.32, 0.34, 0.36, 0.38] and :33 calls it "the
# manuscript's committed proxy range". Run buyback_discount_rederived prices
# each month's retired face at its own prepayment-consistent PV, off the leg's
# own CPR path and the window's own rate path, and the answer is a POINT: the
# committed range was a range only because the asserted grid had four points.
#
# Every printed figure is DERIVED below, and every committed constant it rests
# on is tied LIVE to two artifacts this run did not write --- the committed
# bracket's own results and danish_us_intercept's --- so no number the gate
# enforces is a literal typed into this file. What is written out is the prose
# those figures would be meaningless without, and six properties beyond
# presence, each a way this could quietly rot back:
#
#   (a) the SUPERSEDED RANGE must be gone. It was live at five .tex sites, and
#       one of them (the trilemma paragraph) printed a HYPHENATED variant that
#       gate #103's substring never matched -- so #103 would have stayed green
#       over a retired figure. Absence is therefore checked in both spellings;
#   (b) the POINT-NOT-RANGE statement, because a reader who finds one number
#       where a range used to be will assume a range was narrowed, rather than
#       that its width was never estimated in the first place;
#   (c) the ZERO-MONTHS fact, which is what makes "the committed grid was
#       uniformly too deep" a measurement rather than a statement about an
#       average;
#   (d) the PROVENANCE HEDGE. The spec (SS2.3, SS6/P4) calls the no-prepayment
#       reading of the committed grid "plausible but not exactly reproduced"
#       and uses it as a non-targeting band check. Both the consistency
#       wording and the hedge that scopes it are pinned, so the clause cannot
#       be upgraded into a finding the run does not carry;
#   (e) the D_crit OWNERSHIP clause. D_crit is gap_par/E on the committed
#       chain, declared in the spec BEFORE the run so that E4 was falsifiable.
#       Without the ownership clause the threshold reads as an output of the
#       re-derivation, which would retrofit the prediction;
#   (f) gap_face, which this run CANNOT move. It is an identity, and a later
#       edit that helpfully "updates" it alongside the cash figure would be
#       wrong. Pinning it here is cheap insurance against that edit.
#
# The two-grain disclosure (SS8.3: D_t is priced on the SOMA book's single-pool
# tabulation while F_t comes from the microsimulated panel's roll-off) is
# pinned for the same reason: the run inherits that seam and the spec commits
# the landing to naming it rather than implying one object was priced end to
# end.
BUYBACK_DISCOUNT_SPANS = {
    "run_tag": "\\texttt{buyback\\_discount\\_rederived}",
    "asserted_not_derived": "The committed grid was asserted, not derived",
    "prepay_consistent": "prices each month's retired face at its own "
                         "prepayment-consistent present value",
    "wac_basis": "aged to that month at the 2.49\\% weighted-average coupon",
    "two_grains": "The price and the face come from two populations",
    "seam_inherited": "the seam the committed early-face netting already "
                      "carries, inherited here rather than repaired",
    "point_not_range": "That is a point, not a range",
    "zero_months": "none of the forty-two months reaches the committed "
                   "grid's floor",
    "no_prepay_provenance": "consistent with a no-prepayment annuity priced "
                            "at a representative state",
    "provenance_not_exact": "plausible rather than exactly reproduced",
    "verdict_survives": "shrinks the reversal without retiring it",
    "d_crit_ownership": "arithmetic on the committed chain, fixed before the "
                        "run rather than produced by it",
}

# the grid's own length, spelled the way the paragraph spells it; .get() so an
# out-of-range grid yields a numeral that will simply miss, never a KeyError.
_GRID_WORDS = {1: "one", 2: "two", 3: "three", 4: "four",
               5: "five", 6: "six", 7: "seven", 8: "eight"}


def buyback_discount_rederived_check(tex, d, cb_art, dan):
    """Gate #117's rule (R32, C-75): the buyback discount, re-derived."""
    tex_nc = re.sub(r"(?<!\\)%.*", "", tex)
    r, p, cb = d["rederived"], d["parity"], d["committed_bracket"]
    bv = cb_art["verdict"]
    pt = dan["point"]
    grid = cb["D_GRID"]
    anchor = p["P4_provenance_anchor"]
    months = d["months"]
    E = p["P2_E_b"]
    gap_par = p["P2_committed_constants"]["gap_par"]["got"]
    dbar = r["face_weighted_mean_discount"]
    gc = r["gap_cash_b"]
    n_pts = _GRID_WORDS.get(len(grid), len(grid))

    lits = dict(BUYBACK_DISCOUNT_SPANS)
    lits.update({
        "dbar": f"face-weighted mean of {dbar * 100:.1f}\\%",
        "haircut": f"\\${r['haircut_b']:.1f} billion haircut",
        "gap_cash": f"cash gap of $-\\${abs(gc):.1f}$ billion",
        "monthly_range": (f"from {r['monthly_D_min'] * 100:.1f}\\% "
                          f"to {r['monthly_D_max'] * 100:.1f}\\%"),
        "grid_span": (f"the committed {grid[0] * 100:.0f}--"
                      f"{grid[-1] * 100:.0f}\\% span was a range only by "
                      f"virtue of a {n_pts}-point asserted grid"),
        "provenance": (f"returns {anchor['discount'] * 100:.1f}\\% at zero "
                       f"prepayment on a "
                       f"{anchor['state']['coupon'] * 100:.1f}\\% coupon "
                       f"against a {anchor['state']['market'] * 100:.1f}\\% "
                       f"market rate"),
        "own_state": (f"the leg itself prepays at "
                      f"{p['P5_mean_danish_cpr_pct']:.2f}\\% against a window "
                      f"averaging {p['P5_market_rate_pct']['mean']:.2f}\\%"),
        "d_crit": (f"the verdict turns at a "
                   f"{r['D_crit'] * 100:.1f}\\% discount"),
        # CONTEXTFUL ON PURPOSE. The bare literal occurs 19x in the manuscript,
        # so pinning it would go green over the very edit item (f) of this
        # header says it guards against: a later hand "updating" the single
        # face-accounting site alongside the cash figure. Verified: this phrase
        # occurs exactly once in both variants.
        "gap_face_unmoved": (f"the gap stands at $+\\${r['gap_face_b']:.1f}$ "
                             "billion under the balance-adjustment reading"),
    })
    missing = sorted(k for k, lit in lits.items() if lit not in tex_nc)

    # (a) both spellings the superseded range was live in
    retired = [lit for lit in ("$-\\$89.4$ to $-\\$117.7$ billion",
                               "$-\\$89.4$-to-$-\\$117.7$ billion")
               if lit in tex_nc]

    # the committed constants, tied to the two artifacts that own them
    cash_rows = bv["cash_rows"]
    tie_ok = (
        pt["institutional_gap_shared_b"] == gap_par == r["gap_face_b"]
        and pt["us_trapped_shared_b"]
        == p["P2_committed_constants"]["us_shared"]["got"]
        and pt["danish_trapped_shared_b"]
        == p["P2_committed_constants"]["dk_shared"]["got"]
        and pt["mean_danish_cpr_pct"] == p["P5_mean_danish_cpr_pct"]
        == p["P2_committed_constants"]["mean_danish_cpr_pct"]["got"]
        and [row["D"] for row in cash_rows] == grid
        and bv["gap_cash_range_b"] == cb["gap_cash_range_b"]
        and bv["code"] == cb["code"]
        and bv["early_face_E_b"] == E
        and bv["gap_face_b"] == r["gap_face_b"] == gap_par
        and all(p["P3_chain_bit_identical"][f"D_{row['D']}"]["committed"]
                == row["gap_cash_b"]
                and p["P3_chain_bit_identical"][f"D_{row['D']}"]["got"]
                == row["gap_cash_b"]
                for row in cash_rows)
    )

    e4_lo, e4_hi = d["expectations"]["E4_band"]
    art_ok = (
        len(grid) == 4
        and p["P0a_wal_table_import_safe"] is True
        and p["P0b_artifacts_byte_identical_after_import"] is True
        and p["P1_schedule_wal_equals_cell_wal"]["max_abs_diff"] < 1e-12
        and all(x["pass"] is True for x in p["P1_v15_printed"].values())
        and all(x["got"] == x["want"]
                for x in p["P2_committed_constants"].values())
        and all(x["exact"] is True
                for x in p["P3_chain_bit_identical"].values())
        # P4: the primitive reproduces where the committed grid came from,
        # as a band check against the grid itself and at the ZERO-CPR state
        and grid[0] < anchor["discount"] < grid[-1]
        and anchor["state"]["cpr"] == 0.0
        and len(months) == d["spec"]["window_months"] == 42
        # (c) uniformly too deep, month by month and not on the average
        and r["months_at_or_above_committed_floor"] == 0
        and all(m["below_committed_grid_floor"] is True for m in months)
        and max(m["discount_D"] for m in months) < grid[0]
        # E1: the monthly decomposition telescopes and is well posed
        and abs(sum(m["early_face_b"] for m in months) - E) < 1e-9
        and min(m["early_face_b"] for m in months) > 0
        # every printed aggregate re-derived from the 42 rows
        and abs(sum(m["discount_D"] * m["early_face_b"] for m in months) / E
                - dbar) < 1e-12
        and abs(r["haircut_b"] / E - dbar) < 1e-12
        # the chain is the committed one with ONLY D changed
        and abs(gc - (gap_par - dbar * E)) < 1e-9
        and abs(r["D_crit"] - gap_par / E) < 1e-12
        and r["D_crit"] < min(m["discount_D"] for m in months)
        # the three scope statements the prose makes, made by the artifact
        and "2.49% WAC" in d["spec"]["method"]
        and "two populations" in d["spec"]["grain_note"]
        and cb["provenance"].startswith("asserted, never derived")
        and "before the run" in r["D_crit_note"]
        # (f) the face incidence is an identity this run cannot move
        and r["gap_face_b"] == gap_par
        # the verdict as printed: still reversing, strictly inside the
        # committed range's near edge
        and r["verdict_code"] == "REVERSES" and gc < 0
        and abs(gc) < abs(cb["gap_cash_range_b"][1])
        and all(d["expectations"][k] is True for k in (
            "E1_monthly_face_positive_and_telescopes", "E2_pv_monotone",
            "E3_every_month_below_committed_grid_floor", "E4_pass",
            "E5_reverses_and_smaller"))
        and e4_lo <= d["expectations"]["E4_dbar"] < e4_hi
    )
    return (not missing and not retired and tie_ok and art_ok,
            {"missing": missing, "retired_range_present": retired,
             "cross_artifact_tie": tie_ok, "artifact_ok": art_ok,
             "dbar_pct": round(dbar * 100, 4), "gap_cash_b": round(gc, 4),
             "months_at_floor": r["months_at_or_above_committed_floor"]})


# --- R32 C-79 (gate #120): THE DANISH LEG WITH AN INTEREST-ONLY SHARE ------
# The concession at .tex:629 said the Danish interest-only share "would cut
# scheduled amortization ... and so move the shortfall in the opposite
# direction from the payoff rule". Run danish_interest_only_share turns that
# direction into a crossing: zeroing scheduled amortization on a share sigma
# of the DANISH leg alone carries the face gap along gap_par - sigma*sched,
# which crosses zero at 30.8%, and carrying the deferred balance forward at
# the Danish leg's own speed lifts the crossing to 34.3%. Denmark's own
# verified share (45%) is above both, so the gap reverses under FACE
# accounting -- a different reversal from C-75's cash-haircut one, by a
# different mechanism.
#
# Every printed figure below is DERIVED from the run's artifact, and every
# committed constant it rests on is tied LIVE to two artifacts this run did
# not write (danish_us_intercept's point, and the committed buyback bracket's
# early face), so no number this gate enforces is a literal typed into this
# file. Beyond presence, six properties, each a way this could quietly rot:
#
#   (a) THE OLD CONCESSION AND THE OLD FLAT FACE SENTENCE MUST STAY GONE.
#       Both are checked by absence. The second is the D4 site: ".tex:660
#       previously read "gross institutional relief under face accounting,
#       not a net social gain" full stop, which after this run reads as
#       unconditional. Reverting either one turns this gate red;
#   (b) THE BREAK-EVEN IS THE DELIVERABLE, and it is stated BEFORE the
#       imported share. The crossing needs no external input; the 45% is a
#       pre-window, whole-market, deferred-amortisation read. File order is
#       checked, not merely presence, because a later edit that leads with
#       the import would make an imported institutional parameter the claim;
#   (c) THE THREE LIMITS TRAVEL. Every line that prints "45% of outstanding
#       mortgage volumes" must carry all four limit spans. This is what stops
#       the share being quoted a second time somewhere bare;
#   (d) THE DOUBLE-COUNTING ACCOUNT MUST STAY RETRACTED. An earlier draft
#       said stacking C-75's cash haircut and this face reversal "would
#       charge the same dollars twice". That is FALSE: E = dk_total - sched
#       already excludes the scheduled dollars the IO share removes, so the
#       pools are DISJOINT; what they share is a balance path, and at
#       sigma > 0 the deferred balance's own prepayment ADDS to the early
#       face, so a naive sum UNDERSTATES the haircut. Every occurrence of
#       "the same dollars twice" must therefore sit under a "rather than";
#   (e) NO JOINT CELL. The artifact's sigma grid is pinned to the committed
#       grid plus the two break-evens, so a composed cell cannot appear in it
#       and then be quoted;
#   (f) THE CHAIN, re-derived cell by cell: gap1 = gap_par - sigma*sched,
#       gap2 = gap1 + offset, sigma = 0 returns gap_par exactly with a zero
#       offset, both orders strictly decreasing in sigma, and each break-even
#       cell returning zero at its own order.
DANISH_IO_SHARE_SPANS = {
    "run_tag": "\\texttt{danish\\_interest\\_only\\_share}",
    # the sign was the manuscript's own; this run gets no credit for it
    "no_credit_for_sign": "the direction was already conceded here",
    # C-74's defect, named: a share scored in BOTH legs contributes zero
    "danish_leg_only": "scoring it in both legs would neutralize it exactly",
    "us_zero_held_fixed": "the U.S. leg's effective zero stays held fixed",
    # the inherited basis seam, disclosed rather than repaired
    "basis_note": "the U.S. leg's scheduled path over the window and this "
                  "paper's own proxy for the scheduled component",
    # P4: the second-order term is reported BESIDE the first, never folded in
    "second_order_separate": "the offset is reported beside the first-order "
                             "effect rather than folded into it",
    "offset_open_ex_ante": "it was the one limb I could not sign in advance",
    "limit_prewindow": "pre-window (February 2020 against a June "
                       "2022--November 2025 window)",
    "limit_deferred": "deferred amortisation (\\emph{afdragsfrihed}), "
                      "conventionally capped at ten years",
    "limit_not_permanent": "the share of volume currently \\emph{in} an "
                           "interest-only period and not a permanent product "
                           "feature",
    "limit_population": "whole-market outstanding volumes rather than the "
                        "owner-occupied thirty-year callable segment",
    "breakeven_needs_nothing": "it is arithmetic on the committed chain and "
                               "needs no Danish input",
    "breakeven_is_reported": "which is why I lead with it",
    "accounting_layer": "the hazard is untouched and only the amortization "
                        "path moves",
    "not_a_resimulation": "not what a re-simulated interest-only book would "
                          "return",
    # the D4 re-scopes, at the table and at the closing sentence
    "tablenote_scope": "the row holds the Danish product mix fixed",
    "face_scope": "gross institutional relief under face accounting and a "
                  "held-fixed Danish product mix",
    "face_scope_why": "what carries the relief is not face accounting alone "
                      "but face accounting on a transplant that changes the "
                      "payoff rule and nothing else",
    # the non-composition account, in the corrected direction
    "no_stack": "The two reversals do not stack",
    "shared_balance_path": "but they share a balance path",
    "understatement": "understate the haircut, not double-count it",
    "no_joint_cell": "Their sum is not the joint cell, and no joint cell is "
                     "run here",
    "citation": "\\citep{nationalbanken2020}",
}

# The two sentences this landing RETIRES. The first is the unmeasured
# concession; the second is the unconditional face-accounting claim.
DANISH_IO_RETIRED = (
    "which would cut scheduled amortization, the null's largest component, "
    "and so move the shortfall in the opposite direction from the payoff rule",
    "is gross institutional relief under face accounting, not a net social "
    "gain",
)


def danish_interest_only_share_check(tex, io, dan, cb):
    """Gate #120's rule (R32, C-79): the Danish leg with an interest-only share."""
    tex_nc = re.sub(r"(?<!\\)%.*", "", tex)
    p, be, s45 = io["parity"], io["break_even"], io["at_sourced_share"]
    src, exp = io["source"], io["expectations"]
    pt, bv = dan["point"], cb["verdict"]
    gap_par = p["P1_gap_par"]
    sched = p["P1_sched_total_b"]
    E = p["P1_buyback_identity_E_b"]
    cpr = p["P3_mean_danish_cpr_pct"]
    # the SOURCED share, with the artifact's own fallback so an unsourced
    # branch-D artifact cannot raise here -- it fails art_ok instead
    share = s45["io_share"]
    off45 = s45["second_order_offset_b"]
    be1, be2 = be["first_order"], be["second_order"]
    cells = sorted(io["cells"].values(), key=lambda c: c["io_share"])

    sourced_lit = f"{share * 100:.0f}\\% of outstanding mortgage volumes"
    crossing1 = f"crosses zero at an interest-only share of {be1 * 100:.1f}\\%"

    lits = dict(DANISH_IO_SHARE_SPANS)
    lits.update({
        "sched_basis": (f"cuts the face gap by $\\sigma$ times "
                        f"\\${sched:.2f} billion"),
        "crossing_first": crossing1,
        "crossing_second": f"lifts the crossing to {be2 * 100:.1f}\\%",
        # CONTEXTFUL ON PURPOSE, all three of these. The bare numerals
        # collide: "30.8" is also the bootstrap understatement factor
        # (30.8x, three sites) and "$+\\$19.2$ billion" is gate #102's
        # moving-share bracket cell, so a bare-numeral pin would be
        # ambiguous and could go green over the wrong site.
        "danish_speed": (f"the Danish leg's own {cpr:.2f}\\% speed returns "
                         f"\\${off45:.1f} billion of extra early roll-off at "
                         f"a {share * 100:.0f}\\% share"),
        "gap_at_sourced": (f"the face gap is "
                           f"$-\\${abs(s45['gap_second_order_b']):.1f}$ "
                           f"billion after that feedback"),
        "sourced_share": f"interest-only loans at {sourced_lit}",
        "tablenote_crossing": (f"above a Danish interest-only share of "
                               f"{be2 * 100:.1f}\\% the face gap reverses too"),
        "conclusion_crossing": (f"the interest-only crossing above sits at "
                                f"{be2 * 100:.1f}\\%"),
        "disjoint_pools": (f"the \\${E:.1f} billion of early face the buyback "
                           f"credit haircuts is Danish roll-off net of the "
                           f"scheduled component"),
        "feedback_size": (f"the deferred balance's own prepayment "
                          f"(\\${off45:.1f} billion at a "
                          f"{share * 100:.0f}\\% share) adds to it"),
    })
    missing = sorted(k for k, lit in lits.items() if lit not in tex_nc)
    retired = [lit for lit in DANISH_IO_RETIRED if lit in tex_nc]

    # (b) the break-even is stated BEFORE the imported share. .find(), never
    # .index(): a missing span must leave this False, not raise.
    i_cross = tex_nc.find(crossing1)
    i_src = tex_nc.find(lits["sourced_share"])
    order_ok = 0 <= i_cross < i_src

    # (c) the limits travel with EVERY printing of the imported share
    limit_keys = ("limit_prewindow", "limit_deferred", "limit_not_permanent",
                  "limit_population")
    src_lines = [ln for ln in tex_nc.split("\n") if sourced_lit in ln]
    limits_travel = bool(src_lines) and all(
        all(lits[k] in ln for k in limit_keys) for ln in src_lines)

    # (d) the double-counting account must stay retracted -- enforced by
    # ABSENCE, not by a negated restatement. An earlier draft explained the
    # non-composition as "would charge the same dollars twice". That is FALSE:
    # E = dk_total - sched already EXCLUDES the scheduled dollars an
    # interest-only share removes, so the two pools are disjoint and nothing is
    # charged twice. The first version of THIS gate required the phrase to be
    # present in negated form, which put the false account on the page for a
    # skimming reader to carry away. It is now required to be absent outright;
    # the true balance-path account that replaces it is pinned separately by
    # no_stack / shared_balance_path / understatement / no_joint_cell, so
    # deleting the retraction still turns the gate red.
    same_dollars_ok = "the same dollars twice" not in tex_nc

    # the committed constants, tied to the two artifacts that own them
    tie_ok = (
        gap_par == pt["institutional_gap_shared_b"]
        and cpr == pt["mean_danish_cpr_pct"]
        and E == bv["early_face_E_b"]
        and gap_par == bv["gap_face_b"]
    )

    # (e) the grid is the committed one plus the two break-evens: no joint
    # cell can be hiding in it
    grid_ok = sorted(round(c["io_share"], 12) for c in cells) == sorted(
        {0.0, 0.10, 0.20, 0.30, 0.45, 0.50,
         round(be1, 12), round(be2, 12)})
    c1 = io["cells"].get(f"sigma_{be1:.6f}")
    c2 = io["cells"].get(f"sigma_{be2:.6f}")
    e3_lo, e3_hi = exp["E3_band"]

    art_ok = (
        io["run_tag"] == "danish_interest_only_share"
        and io["spec"]["no_engine_runs"] is True
        and io["spec"]["window_months"] == 42
        and len(p["P0_sha_pins"]) == 3
        and p["P0b_artifacts_byte_identical"] is True
        and p["P3_sched_positive_every_month"] is True
        and p["P4_second_order_reported_separately"] is True
        and grid_ok
        # (f) the chain, cell by cell, with ONLY sigma moving
        and all(abs(c["gap_first_order_b"]
                    - (gap_par - c["io_share"] * sched)) < 1e-9
                for c in cells)
        and all(abs(c["gap_second_order_b"]
                    - (c["gap_first_order_b"] + c["second_order_offset_b"]))
                < 1e-12 for c in cells)
        # E1: sigma = 0 is the parity anchor, exactly, at both orders
        and cells[0]["io_share"] == 0.0
        and cells[0]["second_order_offset_b"] == 0.0
        and abs(cells[0]["gap_first_order_b"] - gap_par) < 1e-12
        and abs(cells[0]["gap_second_order_b"] - gap_par) < 1e-12
        # E2: strictly decreasing at both orders, offset strictly rising
        and all(a["gap_first_order_b"] > b["gap_first_order_b"]
                for a, b in zip(cells, cells[1:]))
        and all(a["gap_second_order_b"] > b["gap_second_order_b"]
                for a, b in zip(cells, cells[1:]))
        and all(a["second_order_offset_b"] < b["second_order_offset_b"]
                for a, b in zip(cells, cells[1:]))
        # both crossings really cross, at their own order
        and abs(be1 * sched - gap_par) < 1e-12
        and c1 is not None and abs(c1["gap_first_order_b"]) < 1e-9
        and c2 is not None and abs(c2["gap_second_order_b"]) < 1e-9
        # the offset can only RAISE the bar, and the import clears both
        and be1 < be2 < share
        and abs(s45["gap_first_order_b"] - (gap_par - share * sched)) < 1e-9
        and off45 > 0
        and s45["gap_second_order_b"] < 0 and s45["reverses"] is True
        # the imported share is SOURCED, and its three limits are the
        # artifact's own rather than this file's
        and src.get("sourced") is True
        and src.get("io_share") == share
        and src.get("publisher") == "Danmarks Nationalbank"
        and src.get("publication_date") == "2020-02-04"
        and (f"{share * 100:.0f} per cent of outstanding mortgage volumes"
             in src.get("verbatim", ""))
        and len(src.get("limits", [])) == 3
        and any("PRE-WINDOW" in x for x in src.get("limits", []))
        and any("DEFERRED AMORTISATION" in x for x in src.get("limits", []))
        and any("whole-market" in x for x in src.get("limits", []))
        # the expectations, as the spec fixed them before the run
        and e3_lo < be2 <= e3_hi
        and exp["E3_sigma_star_second_order"] == be2
        and all(exp[k] is True for k in (
            "E1_anchor_exact", "E2_monotone_both_orders", "E3_pass",
            "E4_sourced_share_reverses_under_face_accounting"))
    )
    return (not missing and not retired and order_ok and limits_travel
            and same_dollars_ok and tie_ok and art_ok,
            {"missing": missing, "retired_present": retired,
             "breakeven_before_import": order_ok,
             "limits_travel": limits_travel,
             "double_counting_retracted": same_dollars_ok,
             "cross_artifact_tie": tie_ok, "artifact_ok": art_ok,
             "grid_ok": grid_ok,
             "breakeven_pct": (round(be1 * 100, 4), round(be2 * 100, 4)),
             "gap_at_sourced_b": round(s45["gap_second_order_b"], 4)})

# --- R32 C-128 (gate #121): THE REALIZED-SIDE BOUNDARY ALLOCATION ---------
# Section VII.B prices the CAP-side settlement convolution at -$42.0bn
# (-5.5%) and says, in terms, that "the realized series is untouched". That
# leg is not symmetric. The pre-QT cap is ZERO, so convolving it can only lose
# mass at the window's END; the realized series is non-zero before the window,
# so seventeen pre-QT months of roll-off exist to settle INTO its start. Run
# realized_boundary_allocation convolves BOTH legs. The two edge effects
# partially offset -- $4.5bn in against $21.2bn out, giving back $16.6bn of
# the cap-side $42.0bn -- so the benchmark lands at $739.4bn, a -$25.4bn
# shift, 3.32% of the committed benchmark and inside the pre-fixed 10% bar.
#
# Every printed figure is DERIVED from the artifact, and the two committed
# benchmarks this run had to reproduce are tied LIVE to
# settlement_months_benchmark -- an artifact this run did not write -- so no
# number this gate enforces is a literal typed into this file. Beyond
# presence, four properties, each a way this could quietly rot:
#
#   (a) THE CAP-ONLY ACCOUNT MUST STILL COME FIRST. The committed convention
#       is the cap-side one and the both-aligned figure is a rider on it.
#       File order is checked, not merely presence, because an edit that led
#       with -$25.4bn would make a sensitivity read as the committed number;
#   (b) THE OFFSET IS DECOMPOSED, NOT ASSERTED. mass_in - mass_out must equal
#       both_aligned - cap_only for EVERY kernel, AND mass_out must re-derive
#       from benchmark_monthly_rebuild's own monthly series -- a run C-128
#       never reads. The second half is not decoration. REPAIRED 2026-07-30:
#       the first version of this run weighted the last pre-window month by
#       k[1] instead of k[1]+k[2] and then defined mass_out as the residual
#       r_tot_cal + mass_in - r_tot_set, so mass_in - mass_out collapsed to
#       r_tot_set - r_tot_cal for ANY mass_in and this clause was VACUOUS. It
#       shipped $4.5bn/$21.2bn for eight hours when the true masses are
#       $6.8bn/$23.4bn. The identity alone still cannot see a CORRELATED shift
#       in both masses -- which is exactly the shape that bug had -- so the
#       external anchor is what makes this clause bite;
#   (c) THE PRE-COMMITMENT SPLIT MUST SURVIVE. E3 fixed the DIRECTION before
#       the run and deliberately left the residual's SIGN open. Prose
#       claiming the sign was predicted turns this red;
#   (d) THE THRESHOLD IS THE ARTIFACT'S. E4's 10% bar is read from the run
#       and never typed here, and the realized-side shift must clear it.
RBA_SPANS = {
    "run_tag": "\\texttt{realized\\_boundary\\_allocation}",
    "direction": "moves the benchmark less, not more",
    "why_asymmetric": "The pre-QT cap is zero, so the cap leg loses mass only "
                      "at the window's end",
    "sign_open": "the sign of the residual deliberately was not",
    "direction_precommitted": "That the two edge effects would partially "
                              "offset was fixed before the run",
    "stays_calendar": "the production convention remains calendar on both legs",
    "not_a_rebasing": "stays a disclosed sensitivity rather than a re-basing",
    # The both-legs block sits between the cap-only figures and the sentence
    # that reads them, so the referent must be NAMED. Landing this block
    # unnamed left "the variant" pointing at the both-legs leg, whose
    # re-basing factor is 1.034, under a sentence asserting 1.058.
    "cap_only_referent": "What the cap-only variant establishes",
    "cap_only_referent_2": "The cap-only variant also bears",
    # the tab:runindex row, pinned by its DESCRIPTION rather than by the
    # tag: the tag also sits in the prose citation, so a tag-only pin
    # would stay green over a deleted row.
    "runindex_row": "Window-boundary allocation priced on the realized "
                    "leg as well as the cap",
}


def realized_boundary_allocation_check(tex, rba, smb, bmr):
    """Gate #121's rule (R32, C-128): the realized-side boundary allocation."""
    tex_nc = re.sub(r"(?<!\\)%.*", "", tex)
    par, leg, exp = rba["parity"], rba["legs"], rba["expectations"]
    pro, slow, fast = leg["production"], leg["slower"], leg["faster"]
    both = pro["benchmark_both_aligned_b"]
    shift_both = pro["shift_both_b"]
    cap_edge = pro["cap_edge_loss_b"]
    m_in = abs(pro["realized_boundary_mass_in_b"])
    m_out = abs(pro["realized_boundary_mass_out_b"])
    pct = abs(pro["shift_both_pct_of_committed"])
    give_back = abs(pro["shift_cap_only_b"]) - abs(shift_both)
    pw = par["P4_pre_window_months"]
    # The prose spells out how far back the kernel REACHES, not how many
    # pre-window months happen to exist. Those are different numbers and the
    # manuscript briefly conflated them: 17 months exist (START_DATE), but a
    # length-3 kernel can only ever see len(k)-1 = 2 of them, so 15 of the 17
    # contribute exactly zero to every field this gate checks. Deriving the
    # word from the kernel means the span tracks the quantity that matters.
    reach = len(par["P3_kernel"]) - 1
    reach_word = {2: "two", 3: "three", 4: "four"}.get(reach, str(reach))

    cap_only_lit = ("the benchmark moves by exactly that \\$42.0 billion")

    lits = dict(RBA_SPANS)
    lits.update({
        "pre_window": (f"the {reach_word} months the kernel reaches back into "
                       f"settle into its start"),
        "boundary_decomp": (f"the realized leg gains \\${m_in:.1f} billion "
                            f"there against \\${m_out:.1f} billion leaving at "
                            f"the end"),
        "gives_back": (f"giving back \\${give_back:.1f} billion of the "
                       f"cap-side \\${cap_edge:.1f} billion"),
        "both_aligned": f"lands the benchmark at \\${both:.1f} billion",
        # CONTEXTFUL ON PURPOSE. "3.3" and the bracket endpoints are common
        # numerals in this manuscript; a bare-numeral pin could go green over
        # an unrelated site.
        "shift": (f"a shift of $-\\${abs(shift_both):.1f}$ billion or "
                  f"$-{pct:.1f}$\\%"),
        "bracket": (f"bracket at $-\\${abs(fast['shift_both_b']):.1f}$ and "
                    f"$-\\${abs(slow['shift_both_b']):.1f}$ billion"),
        "threshold_share": (f"at {pct:.1f}\\% of the committed benchmark the "
                            f"boundary treatment"),
    })
    missing = sorted(k for k, lit in lits.items() if lit not in tex_nc)

    # (a) the committed cap-only account still leads. .find(), never .index():
    # a missing span must leave this False rather than raise.
    i_cap = tex_nc.find(cap_only_lit)
    i_both = tex_nc.find(lits["direction"])
    order_ok = 0 <= i_cap < i_both

    # the two committed benchmarks belong to a run this one did not write
    tie_ok = (
        par["P2_committed_calendar"] == smb["calendar_benchmark_b"]
        and par["P2_committed_cap_only"] == smb["legs"]["production"]["benchmark_b"]
        and par["P1_calendar_reproduces"] == smb["calendar_benchmark_b"]
        and par["P1_cap_only_reproduces"] == smb["legs"]["production"]["benchmark_b"]
        and par["P3_kernel"] == smb["kernel_production"]
        and par["P3_n_qt_active_months"] == smb["n_qt_active_months"]
        and par["E2_cap_edge_loss_b"] == smb["window_edge_cap_mass_lost_b"]
    )

    # (b) the decomposition, re-derived for every kernel rather than read off
    # the production row's summary
    decomp_ok = all(
        abs((lg["realized_boundary_mass_in_b"] - lg["realized_boundary_mass_out_b"])
            - (lg["benchmark_both_aligned_b"] - lg["benchmark_cap_only_b"])) < 1e-6
        and abs(lg["shift_both_b"]
                - (lg["benchmark_both_aligned_b"] - smb["calendar_benchmark_b"])) < 1e-9
        and abs(lg["shift_cap_only_b"]
                - (lg["benchmark_cap_only_b"] - smb["calendar_benchmark_b"])) < 1e-9
        # E3 for every kernel: aligning both legs moves LESS than cap-only
        and abs(lg["shift_both_b"]) < abs(lg["shift_cap_only_b"])
        for lg in (pro, slow, fast))

    # THE ANCHOR. mass_out re-derived from benchmark_monthly_rebuild's own
    # monthly series, which C-128 never reads: the month i places before the
    # window end loses sum(k[i+1:]) past it. The window's own months are taken
    # from that artifact too (its first clip month IS the window's opening
    # month), so no date is typed here. This pins one side of the
    # decomposition ABSOLUTELY, which the P5 identity cannot do.
    net = bmr["monthly_net_rolloff_b"]
    months = sorted(net)
    i0 = months.index(bmr["parity"]["P1_clip_months"][0])
    win_months = months[i0:i0 + bmr["spec"]["window_months"]]
    anchor_ok = len(win_months) == bmr["spec"]["window_months"] and all(
        abs(lg["realized_boundary_mass_out_b"]
            + sum(sum(lg["kernel"][i + 1:]) * net[win_months[-1 - i]]
                  for i in range(len(lg["kernel"]) - 1))) < 1e-6
        for lg in (pro, slow, fast))

    art_ok = (
        rba["run_tag"] == "realized_boundary_allocation"
        and rba["status"] == "OK"
        and rba["pre_committed"] is True
        and rba["spec"]["no_engine_runs"] is True
        and rba["spec"]["production_convention_stays_calendar"] is True
        and rba["spec"]["kernel_imported_not_estimated"] is True
        and par["P5_boundary_decomposition_sums"] is True
        # P4: a kernel of length 3 needs at least 3 pre-window months, or the
        # run would have convolved against zeros and fabricated the asymmetry
        and pw >= len(par["P3_kernel"])
        and decomp_ok
        # (c) the direction was predicted; the SIGN was deliberately not
        and exp["E3_both_moves_less_than_cap_only"] is True
        and exp["E3_sign_deliberately_not_predicted"] is True
        and exp["E3_shift_both_b"] == shift_both
        and exp["E3_shift_cap_only_b"] == pro["shift_cap_only_b"]
        # (d) the disclosure bar is the artifact's own, and it is cleared
        and exp["E4_pass"] is True
        and abs(exp["E4_shift_share_of_committed"]
                - abs(shift_both) / smb["calendar_benchmark_b"]) < 1e-12
        and exp["E4_shift_share_of_committed"] < exp["E4_max_share"]
        and abs(pct / 100.0 - exp["E4_shift_share_of_committed"]) < 1e-12
    )
    return (not missing and order_ok and tie_ok and art_ok and anchor_ok,
            {"missing": missing, "cap_only_leads": order_ok,
             "cross_artifact_tie": tie_ok, "artifact_ok": art_ok,
             "decomposition_ok": decomp_ok, "mass_out_anchored": anchor_ok,
             "both_aligned_b": round(both, 4),
             "shift_both_b": round(shift_both, 4),
             "share_pct": round(pct, 4)})


# --- R32 C-127 (gate #122): THE BENCHMARK'S MONTHLY SERIES, REBUILT --------
# The benchmark's realized series is built by differencing weekly Wednesday
# current-face levels, which yields four exact-zero months. R2's objection was
# that rebuilding from published monthly SOMA principal payments, or from
# per-CUSIP factor changes, would retire them and reopen the monthly-timing
# question on a clean comparator. Run benchmark_monthly_rebuild probed both
# routes. NEITHER is usable: there is no monthly principal-payment endpoint
# (both return HTTP 400; the summary carries levels only), and the per-CUSIP
# route recovers face LEVELS, not principal -- gross declines run $2,186bn
# against a $652.8bn net, ~3.35x, because face also falls on reinvestment
# settlement and roll. Netted, it reproduces the committed month-end
# differencing to 6.8e-11 bn and returns the same four low months.
#
# This landed on BRANCH D, not Branch A: E3 predicted all four clip months
# would carry a stale published week and 2022-06 carries none. The manuscript
# therefore states the exception, and states that staleness is ORDINARY --
# 59 of 192 weeks and 36 of 44 months carry one -- rather than diagnostic.
# Three properties beyond presence:
#
#   (a) THE EXCEPTION MAY NOT BE ROUNDED AWAY. A later edit tightening this
#       to "all four" is the exact overclaim Branch D exists to prevent, so
#       "three of the four" and the June-2022 exception are both pinned, and
#       the artifact's own E3 flag must stay False;
#   (b) STALENESS MAY NOT BE PROMOTED TO A MECHANISM. The ordinary-rather-
#       than-diagnostic clause and its two counts are required, and the
#       counts are DERIVED from the artifact's own stale-week map;
#   (c) THE ZEROS ARE TIED TO THE RUN THAT OWNS THEM. Each clip month's
#       rebuilt net roll-off must equal the NEGATION of
#       h1_zero_months_diagnosis's raw month-end diff, an artifact this run
#       did not write, and that run's ARTIFACT verdict must still stand.
BMR_SPANS = {
    "run_tag": "\\texttt{benchmark\\_monthly\\_rebuild}",
    "probed": "was probed rather than assumed, and neither route is usable",
    "no_monthly": "No monthly SOMA principal-payment series is published",
    "levels_only": "the summary endpoint carries holdings levels only, and "
                   "both monthly endpoints return HTTP 400",
    "levels_not_principal": "recovers face levels rather than principal "
                            "payments",
    "why_gross": "since face also falls on reinvestment settlement and roll",
    # (a) the Branch-D scoping, both halves
    "three_of_four": "Three of the four sit on a week the New York Fed "
                     "republished unchanged and June 2022 does not",
    # (b) staleness is not a mechanism
    "not_diagnostic": "republication is ordinary rather than diagnostic",
    "scope": "what the rebuild establishes is that the alternative source is "
             "unavailable and the zeros survive it, not a second mechanism",
    # same reasoning as gate #121: pin the row's description, not its tag
    "runindex_row": "rebuilt from per-CUSIP SOMA holdings: sourceability "
                    "of the alternative constructions",
}

# The overclaim this gate exists to keep out. Branch D turns on 2022-06
# carrying NO stale week; any prose asserting all four do is false.
BMR_OVERCLAIM = (
    "all four clip months",
    "each of the four sits on a week",
    "all four sit on a week",
)


def benchmark_monthly_rebuild_check(tex, bmr, h1z, expect):
    """Gate #122's rule (R32, C-127): the benchmark's monthly series rebuilt."""
    tex_nc = re.sub(r"(?<!\\)%.*", "", tex)
    par, exp, src = bmr["parity"], bmr["expectations"], bmr["sourceability"]
    stale = bmr["stale_weeks_by_month"]
    net = bmr["monthly_net_rolloff_b"]
    clip = list(par["P1_clip_months"])
    rows = h1z["parity_gates"]["P1_zeros_reproduce"]["rows"]

    n_weeks = par["P4_weeks_retrieved"]
    n_months = len(net)
    n_stale_weeks = sum(len(v) for v in stale.values())
    n_stale_months = len(stale)
    recon = exp["E4_reconstructed_window_total_b"]
    implied = exp["E4_implied_realized_total_b"]
    gross = exp["gross_declines_b"]
    median = exp["E5_window_median_paydown_b"]
    pays = [exp["E5_clip_month_paydowns_b"][m] for m in clip]

    lits = dict(BMR_SPANS)
    lits.update({
        "gross_vs_net": (f"gross face declines run \\${gross:,.0f} billion "
                         f"against a \\${implied:.1f} billion net").replace(
                             ",", "{,}"),
        "weeks": f"netted over {n_weeks} weekly as-of dates",
        # the reconciliation, printed at the precision that makes it a
        # reconciliation rather than a rounding
        "reconciles": (f"reproduces the committed month-end differencing, "
                       f"\\${recon:.4f} billion against \\${implied:.4f} "
                       f"billion"),
        "low_months": (f"returns the same four low months at "
                       f"$-\\${abs(pays[0]):.1f}$, \\${pays[1]:.1f}, "
                       f"\\${pays[2]:.1f} and \\${pays[3]:.1f} billion "
                       f"against a \\${median:.1f} billion window median"),
        # (b) DERIVED counts -- a changed stale map moves these literals
        "stale_counts": (f"{n_stale_weeks} of those {n_weeks} weeks and "
                         f"{n_stale_months} of the {n_months} months they "
                         f"span carry one"),
    })
    missing = sorted(k for k, lit in lits.items() if lit not in tex_nc)
    overclaimed = [lit for lit in BMR_OVERCLAIM if lit in tex_nc]

    # (c) each clip month's rebuilt net roll-off is the NEGATION of the
    # month-end diff owned by h1_zero_months_diagnosis
    tie_ok = (
        sorted(clip) == sorted(rows)
        and all(abs(net[m] + rows[m]["raw_me_diff_b"]) < 1e-6 for m in clip)
        and all(rows[m]["clip_binds"] is True for m in clip)
        and h1z["verdict"]["outcome"] == "ARTIFACT"
        and h1z["classification_summary"]["spike_followed_all_artifact"] is True
        and par["P1_committed_benchmark_b"] == expect["cap_benchmark_b"]
    )

    # the counts the prose prints are the artifact's own map, recomputed
    counts_ok = (
        n_stale_weeks == sum(len(v) for v in stale.values())
        and all(w in [x["asof"] for x in bmr["weeks"]]
                for v in stale.values() for w in v)
        and n_weeks == len(bmr["weeks"]) == par["P4_asof_dates"]
    )

    art_ok = (
        bmr["run_tag"] == "benchmark_monthly_rebuild"
        and bmr["status"] == "OK"
        and bmr["spec"]["cap_side_untouched"] is True
        and bmr["spec"]["no_engine_runs"] is True
        and bmr["spec"]["window_months"] == 42
        and not par["P4_fetch_failures"]
        and par["E2_decomposition_exhaustive"] is True
        and counts_ok
        # sourceability: BOTH of R2's routes, as the run found them
        and src["summary_has_paydown_field"] is False
        and src["monthly_principal_payment_series_available"] is False
        and all(v == "400" for v in src["monthly_endpoints"].values())
        # E4: the settling test, inside its own pre-fixed tolerance
        and exp["E4_pass"] is True
        and exp["E4_month_end_reproduces_exactly"] is True
        and abs(recon - implied) == exp["E4_abs_diff_b"]
        and abs(recon - implied) < exp["E4_tol_frac"] * implied
        # E5: the reconstruction does NOT retire the zeros
        and exp["E5_reconstruction_still_shows_low_months"] is True
        and all(abs(p) < 0.5 * median for p in pays)
        # (a) BRANCH D. 2022-06 carries no stale week and the artifact says so
        and exp["E3_all_clip_months_have_a_stale_week"] is False
        and sum(1 for m in clip
                if exp["E3_stale_weeks_in_clip_months"][m]) == len(clip) - 1
        and not exp["E3_stale_weeks_in_clip_months"]["2022-06"]
        # gross is not net, by the factor the comment records
        and gross > 3 * implied
    )
    return (not missing and not overclaimed and tie_ok and art_ok,
            {"missing": missing, "overclaimed": overclaimed,
             "cross_artifact_tie": tie_ok, "artifact_ok": art_ok,
             "counts_ok": counts_ok,
             "stale": f"{n_stale_weeks}/{n_weeks}wk {n_stale_months}/{n_months}mo",
             "reconciles_to_b": f"{abs(recon - implied):.2e}"})


def main() -> int:
    tex = TEX.read_text()
    failures = 0

    for phrase in ZERO_COUNT:
        n = tex.count(phrase)
        ok = n == 0
        failures += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] zero-count {phrase!r}: {n}")

    for phrase in EXACTLY_ONE:
        n = tex.count(phrase)
        ok = n == 1
        failures += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] exactly-one {phrase!r}: {n}")

    import re
    tex_nc = re.sub(r"(?<!\\)%.*", "", tex)
    for label, pat in HARDCODED_XREF.items():
        n = len(re.findall(pat, tex_nc))
        ok = n == 0
        failures += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] no-hardcoded-xref {label}: {n}")

    # --- Post-freeze pass gates ---------------------------------------------
    for phrase, label in SUPERSEDED_CONTEXTUAL.items():
        bad = 0
        start = 0
        while (idx := tex.find(phrase, start)) != -1:
            window = tex[max(0, idx - 120): idx + 120]
            if label not in window:
                bad += 1
            start = idx + len(phrase)
        ok = bad == 0
        failures += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] superseded-unless-labeled "
              f"{phrase!r} (label {label!r}): {bad} unlabeled")

    lstart = tex.find(LEDGER_SECTION)
    lend = tex.find("\\section{", lstart + 1) if lstart != -1 else -1
    ledger = tex[lstart:lend] if lstart != -1 and lend != -1 else ""
    for needle in LEDGER_REQUIRED:
        ok = lstart != -1 and needle in ledger
        failures += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] ledger-contains {needle!r}")

    for rel in FIGURE_SCRIPTS:
        src = (ROOT / rel).read_text()
        hits = [lit for lit in SHARE_LITERALS
                if re.search(rf"(?<![\d.]){re.escape(lit)}(?!\d)", src)]
        ok = not hits
        failures += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] figure-script-no-share-literals "
              f"{rel}: {hits if hits else 0}")
        fhits = [p for p in FIGURE_FORBIDDEN if p in src]
        ok = not fhits
        failures += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] figure-script-no-retracted-timing "
              f"{rel}: {fhits if fhits else 0}")

    manifest = json.loads(MANIFEST.read_text())
    flag = bool(manifest.get("pipeline", {}).get("apply_settlement_lag_kernel"))
    phrase_present = KERNEL_TEX_PHRASE in tex
    ok = flag == phrase_present
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check settlement-lag kernel: "
        f"manifest apply_settlement_lag_kernel={flag}, "
        f"tex {KERNEL_TEX_PHRASE!r} present={phrase_present} "
        f"(must agree; either side flipping without the other fails)"
    )

    # Run-citation convention (re-synced 2026-07-19): each run is cited by its
    # \texttt{<tag>} identifier. Since the round-19 revision these tags live in
    # the Appendix run-index / crosswalk tables (tab:runindex, tab:crosswalk)
    # rather than inline as "run \texttt{<tag>}" (repository identifiers were
    # deliberately removed from the narrative). The cross-checks below therefore
    # count \texttt{<tag>} and require >= 1 (a run may be tagged in both a table
    # and inline, e.g. out_of_window_floor); the printed value literals carry the
    # anti-drift guarantee that the tex number equals the frozen artifact's.
    # Round-14 W4: the manuscript's Fannie replication sentences must agree
    # with the committed artifact — the envelope gate must actually have
    # passed, and the printed marginal must be the artifact's, rounded as
    # printed (+$XX.X billion / +X.XX points). Same manifest-vs-tex contract
    # as the settlement-lag gate: either side moving without the other fails.
    fannie = json.loads(FANNIE_RESULTS.read_text())
    env = fannie["gates"]["gate_envelope"]
    claims = tex.count("\\texttt{fannie\\_replication}")
    marg_b = f"+\\${fannie['path_b']['lockin_marginal_b']:.1f}"
    marg_pp = f"+{fannie['path_b']['lockin_marginal_share_pp']:.2f}"
    ok = (bool(env["pass"]) and claims >= 1
          and marg_b in tex and marg_pp in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check fannie replication: "
        f"artifact envelope pass={env['pass']}, tex run-citation count="
        f"{claims} (want >=1), marginal literals {marg_b!r}/{marg_pp!r} "
        f"present={marg_b in tex}/{marg_pp in tex}"
    )

    # Round-15 Q2: the Ginnie CPR overlay sentences must agree with the
    # committed artifact — G1 parity passed, the differential attribution
    # verdict is inside_static_bound, and the printed corrected shares and
    # differential are the artifact's, rounded as printed.
    ov = json.loads(OVERLAY_RESULTS.read_text())
    g3d = ov["gates"]["G3_static_bound"]["differential_attribution"]
    prim = ov["variants"]["primary"]
    claims = tex.count("\\texttt{ginnie\\_cpr\\_overlay}")
    lit_central = f"{prim['central']['share_shared_pct']:.1f}\\%"
    lit_null = f"{prim['null']['share_shared_pct']:.1f}\\%"
    lit_diff = f"+\\${g3d['primary_minus_placebo_b']:.1f}"
    ok = (bool(ov["gates"]["G1_parity"]["pass"])
          and g3d["verdict_differential"] == "inside_static_bound"
          and claims >= 1
          and lit_central in tex and lit_null in tex and lit_diff in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check ginnie overlay: "
        f"G1 pass={ov['gates']['G1_parity']['pass']}, differential verdict="
        f"{g3d['verdict_differential']}, tex run-citation count={claims} "
        f"(want >=1), literals {lit_central!r}/{lit_null!r}/{lit_diff!r} "
        f"present={lit_central in tex}/{lit_null in tex}/{lit_diff in tex}"
    )

    # Round-15 Q3: the marginal-decomposition sentences must agree with the
    # committed artifact — parity gates passed, the additivity verdict is
    # shares_readable, and the printed composition shares are the artifact's.
    dec = json.loads(DECOMP_RESULTS.read_text())
    g3 = dec["gates"]["G3_additivity"]
    claims = tex.count("\\texttt{marginal\\_decomposition}")
    cells = dec["cells"]
    top = max(c["share_of_sum_pct"] for c in cells)
    v2021 = sum(c["marginal_b"] for c in cells if c["vintage"] >= 2020)
    v_share = v2021 / g3["sum_cells_b"] * 100
    ok = (bool(dec["gates"]["G1_central_parity"]["pass"])
          and bool(dec["gates"]["G2_null_parity"]["pass"])
          and g3["verdict"] == "shares_readable"
          and claims >= 1
          and all(c["marginal_b"] > 0 for c in cells)
          and abs(v_share - 72) < 1 and abs(top - 21) < 1)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check marginal decomposition: "
        f"G1/G2 pass, verdict={g3['verdict']}, tex run-citation count={claims} "
        f"(want >=1), all-cells-positive={all(c['marginal_b'] > 0 for c in cells)}, "
        f"2020-21 share {v_share:.1f}% (printed 72%), max cell {top:.1f}% "
        f"(printed 21%)"
    )

    # Round-15 Q4: the ABM external-gates sentences must agree with the
    # committed artifact — both gates passed, and the printed recovery and
    # mobility scales are the artifact's, rounded as printed.
    ext = json.loads(ABMEXT_RESULTS.read_text())
    claims = tex.count("\\texttt{abm\\_external\\_gates}")
    lit_share = f"{ext['results']['external']['share_pct']:.1f}\\%"
    scale_ext = ext["external_parameters"]["mobility_scale_external"]
    lit_scale = f"{scale_ext:,.0f}".replace(",", "{,}")
    # ROUND 22: the artifact's own PRE-COMMITTED classification must be stated,
    # and the admissibility qualification that sets it aside must be labelled
    # post hoc. The spec commit (335797a) pre-registered the floor diagnostic as
    # "reported alongside whatever the recovery number is, whichever direction it
    # moves" and contains ZERO occurrences of "admissib"; the artifact records
    # classification_external == "undercuts_paradigm" with
    # registered_before_results True. The manuscript previously wrote that the
    # 150.6% "is not scored against the 50% undercutting band", contradicting
    # both. The old gate passed through that contradiction because it never read
    # classification_external — which is why it is read here.
    ext_class_ok = (ext["classification_external"] == "undercuts_paradigm"
                    and bool(ext["preregistration"]["registered_before_results"]))
    ext_posthoc_ok = ("formulated after the result was seen" in tex
                      and "labelled post-run qualification" in tex)
    ok = (bool(ext["gates"]["G1_harness_parity"]["pass"])
          and bool(ext["gates"]["G2_anchor"]["pass"])
          and bool(ext["floor_diagnostic"]["violates_observed_floor"])
          and claims >= 1 and lit_share in tex and lit_scale in tex
          and ext_class_ok and ext_posthoc_ok)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check abm external gates: "
        f"G1/G2 pass, floor-violation={ext['floor_diagnostic']['violates_observed_floor']}, "
        f"tex run-citation count={claims} (want >=1), literals "
        f"{lit_share!r}/{lit_scale!r} present={lit_share in tex}/{lit_scale in tex}, "
        f"precommitted-classification={ext['classification_external']} "
        f"stated-and-labelled-posthoc={ext_posthoc_ok}"
    )

    # Round-15 Q10: the expectations-benchmark sentences must agree with the
    # committed artifact — the threshold must have survived, parity must be
    # inside tolerance, and the printed literals must be the artifact's,
    # rounded as printed.
    exp = json.loads(EXPECT_RESULTS.read_text())
    claims = tex.count("\\texttt{expectation\\_benchmark}")
    wedge = exp["supplementary_projection_wedge"]
    lit_proj = f"\\${exp['window']['projected_runoff_window_b']:.1f}"
    lit_e = f"\\${exp['e_benchmark_b']:.1f}"
    lit_wedge_share = f"{wedge['expected_share_of_realized_cap_shortfall_pct']:.1f}\\%"
    max_parity = max(abs(v) for v in exp["gates"]["ii_cap_parity"].values())
    saa = exp["settlement_aware_allocation"]
    lit_h1 = f"\\${saa['h1_2022_realized_rise_b']:.1f}"
    lit_alt = f"{saa['expected_share_of_realized_cap_shortfall_pct']:.1f}\\%"
    ok = (bool(exp["threshold"]["mechanical_majority_survives"])
          and bool(saa["threshold_survives"])
          and max_parity <= 0.01
          and claims >= 1
          and lit_proj in tex and lit_e in tex and lit_wedge_share in tex
          and lit_h1 in tex and lit_alt in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check expectation benchmark: "
        f"threshold survives={exp['threshold']['mechanical_majority_survives']}, "
        f"max parity |diff|={max_parity:.1e}pp, tex run-citation count={claims} "
        f"(want >=1), literals {lit_proj!r}/{lit_e!r}/{lit_wedge_share!r} "
        f"present={lit_proj in tex}/{lit_e in tex}/{lit_wedge_share in tex}"
    )

    # Round-16 W2: the vintage-residual-bound sentences must agree with the
    # committed artifact — all four in-run gates passed, the pre-committed
    # verdict/sign are as printed, and the printed segment speeds and dollar
    # bound are the artifact's, rounded as printed.
    vin = json.loads(VINTAGE_RESULTS.read_text())
    vr = vin["results"]
    claims = tex.count("\\texttt{vintage\\_residual\\_bound}")
    lit_bound = f"\\${vr['bound_b']:.1f} billion"
    lit_2022 = f"{vr['segments']['vintage_2022']['cpr_pct']:.2f}\\%"
    lit_pre = f"{vr['segments']['pre_2017']['cpr_pct']:.2f}\\%"
    lit_sampled = f"{vr['segments']['sampled_2017_2021']['cpr_pct']:.2f}\\%"
    ok = (all(bool(g["pass"]) for g in vin["gates"].values())
          and vr["interpretation"]["verdict"] == "below_ginnie_bound"
          and vr["sign_direction"] == "overstates_trapped"
          and claims >= 1
          and lit_bound in tex and lit_2022 in tex and lit_pre in tex
          and lit_sampled in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check vintage residual bound: "
        f"in-run gates all pass={all(bool(g['pass']) for g in vin['gates'].values())}, "
        f"verdict={vr['interpretation']['verdict']}, sign={vr['sign_direction']}, "
        f"tex run-citation count={claims} (want >=1), literals "
        f"{lit_bound!r}/{lit_sampled!r}/{lit_2022!r}/{lit_pre!r} present="
        f"{lit_bound in tex}/{lit_sampled in tex}/{lit_2022 in tex}/{lit_pre in tex}"
    )

    # Round-16 W4: the Theil dynamic-fit sentences and appendix table must
    # agree with the committed artifact — all nine in-run gates passed and
    # the printed U statistics and Path B / ABM error shares are the
    # artifact's, rounded as printed.
    thl = json.loads(THEIL_RESULTS.read_text())
    est = thl["estimators"]
    claims = tex.count("\\texttt{make\\_theil\\_data}")
    # ROUND-28 G2-B: tab:theil's Path A/B columns are refreshed to the
    # note-rate-WAC amortization basis (run coupon_convention_amortization,
    # pre-committed sub-branch of landing (i)); the Path B literals now come
    # from that artifact's converted block, the ABM column stays committed.
    cca = json.loads((ROOT / "hazard" / "data"
                      / "coupon_convention_amortization_results.json").read_text())
    ccb = cca["timing"]["path_b"]["theil_converted"]
    lit_u1_pathb = f"{ccb['u1_levels']:.3f}"
    lit_u2_abm = f"{est['abm']['u2_diffs']:.3f}"
    lit_pathb_var = f"{ccb['decomp']['levels']['var_share']:.1f}\\%"  # stored in percent
    lit_abm_bias_tbl = f"{est['abm']['decomp']['levels']['bias_share']:.1f}"
    ok = (all(bool(g["pass"]) for g in thl["gates"].values())
          and cca.get("status") == "OK" and cca.get("gates_all_pass") is True
          and tex.count("\\texttt{coupon\\_convention\\_amortization}") >= 2
          and claims >= 1
          and lit_u1_pathb in tex and lit_u2_abm in tex
          and lit_pathb_var in tex and lit_abm_bias_tbl in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check theil dynamic fit: "
        f"in-run gates all pass={all(bool(g['pass']) for g in thl['gates'].values())}, "
        f"tex run-citation count={claims} (want >=1), literals "
        f"{lit_u1_pathb!r}/{lit_u2_abm!r}/{lit_pathb_var!r}/{lit_abm_bias_tbl!r} "
        f"present={lit_u1_pathb in tex}/{lit_u2_abm in tex}/"
        f"{lit_pathb_var in tex}/{lit_abm_bias_tbl in tex}"
    )

    # Round-16 W6: the flexible-learner comparator sentences must agree with
    # the committed artifact — parity and sanity gates passed, the
    # pre-committed overall verdict is as printed, and the printed holdout
    # RMSEs are the artifact's, rounded as printed.
    mlc = json.loads(MLCOMP_RESULTS.read_text())
    hgb = mlc["learners"]["hgb_poisson"]
    glm = mlc["learners"]["poisson_glm"]
    claims = tex.count("\\texttt{ml\\_comparator\\_holdout}")
    lit_hgb_w = f"{hgb['rmse_weighted_pp']:.1f} points"
    lit_hgb_u = f"{hgb['rmse_unweighted_pp']:.1f} against 37.9"
    lit_glm = f"{glm['rmse_weighted_pp']:.1f} and {glm['rmse_unweighted_pp']:.1f} points"
    ok = (all(bool(g["pass"]) for g in mlc["gates"].values())
          and mlc["interpretation"]["overall_verdict"]
              == "flexible_fit_helps_no_headline_change"
          and claims >= 1
          and lit_hgb_w in tex and lit_hgb_u in tex and lit_glm in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check ml comparator holdout: "
        f"in-run gates all pass={all(bool(g['pass']) for g in mlc['gates'].values())}, "
        f"verdict={mlc['interpretation']['overall_verdict']}, tex run-citation "
        f"count={claims} (want >=1), literals {lit_hgb_w!r}/{lit_hgb_u!r}/{lit_glm!r} "
        f"present={lit_hgb_w in tex}/{lit_hgb_u in tex}/{lit_glm in tex}"
    )

    # Round-17 R17-B (gate #38): the composition-shift appendix table must
    # agree with the committed artifact — all in-run gates passed and the
    # printed PSI values are the artifact's, rounded as printed.
    cs = json.loads(COMPSHIFT_RESULTS.read_text())
    svb = cs["comparisons"]["sample_vs_book"]
    xag = cs["comparisons"]["freddie_vs_fannie"]
    claims = tex.count("\\texttt{composition\\_shift}")
    lits = [f"{svb['agency']['psi']:.2f}", f"{svb['vintage']['psi']:.2f}",
            f"{svb['coupon']['psi']:.2f}", f"PSI {xag['state']['psi']:.3f}",
            f"PSI {xag['fico']['psi']:.3f}"]
    ok = (_gates_ok(cs["gates"]) and claims >= 1
          and all(l in tex for l in lits))
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check composition shift: "
        f"in-run gates all pass={_gates_ok(cs['gates'])}, tex run-citation "
        f"count={claims} (want >=1), PSI literals {lits} present="
        f"{[l in tex for l in lits]}"
    )

    # Round-17 R17-C (gate #39): the freeze-sensitivity paragraph must agree
    # with the committed artifact — all gates passed, the floor invariance
    # held at every share, and the printed dollars are the artifact's.
    fz = json.loads(FREEZE_RESULTS.read_text())
    p1 = fz["part1"]["legs"]
    p2 = fz["part2"]["legs"]
    claims = tex.count("\\texttt{freeze\\_sensitivity}")
    lits = [f"\\${p1['freeze_off']['trapped_b']:.1f} billion",
            f"\\${p1['trigger_100bp']['trapped_b']:.1f} to "
            f"\\${p1['trigger_200bp']['trapped_b']:.1f} billion",
            f"\\${p2['share_0.100000']['leg']['trapped_b']:.1f} billion",
            f"\\${p2['share_0.182600']['leg']['trapped_b']:.1f} billion",
            f"\\${p2['share_0.300000']['leg']['trapped_b']:.1f} billion",
            f"+\\${fz['part1']['freeze_contribution']['trapped_b']:.1f}"]
    ok = (_gates_ok(fz["gates"]) and claims >= 1
          and all(l in tex for l in lits))
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check freeze sensitivity: "
        f"in-run gates all pass={_gates_ok(fz['gates'])}, tex run-citation "
        f"count={claims} (want >=1), literals present={[l in tex for l in lits]}"
    )

    # Round-17 R17-D (gate #40): the isotonic-recalibration sentence must
    # agree with the committed artifact — gates passed, verdict as printed.
    iso = json.loads(ISOTONIC_RESULTS.read_text())
    isoc = iso["isotonic_recalibration"]
    claims = tex.count("\\texttt{landmark\\_isotonic\\_holdout}")
    lits = [f"to {isoc['rmse_weighted_pp']:.2f} points",
            f"RMSE at {isoc['rmse_unweighted_pp']:.1f}",
            f"$-{abs(isoc['r2_unweighted']):.3f}$"]
    ok = (_gates_ok(iso["gates"])
          and iso["interpretation"]["overall_verdict"] == "no_material_change"
          and claims >= 1 and all(l in tex for l in lits))
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check landmark isotonic: "
        f"in-run gates all pass={_gates_ok(iso['gates'])}, "
        f"verdict={iso['interpretation']['overall_verdict']}, tex run-citation "
        f"count={claims} (want >=1), literals present={[l in tex for l in lits]}"
    )

    # Round-17 R17-L (gate #41): the marginal-timing sentences must agree
    # with the committed artifact — gates passed, thirds/peak/buckets as
    # printed, and the app:theil null terminal is the artifact's.
    mm = json.loads(MARGMONTH_RESULTS.read_text())
    th = mm["part_a"]["thirds"]["shares_pct"]
    cb = mm["part_b"]["coupon_buckets"]
    claims = tex.count("\\texttt{marginal\\_monthly\\_decomposition}")
    lit_thirds = f"{th[0]:.1f}\\%/{th[1]:.1f}\\%/{th[2]:.1f}\\%"
    lit_peak = f"\\${mm['part_a']['peak']['m_b']:.2f} billion"
    lit_buckets = (f"{cb['<3.0%']['share_of_cells_sum_pct']:.1f}\\%/"
                   f"{cb['3.0-4.0%']['share_of_cells_sum_pct']:.1f}\\%/"
                   f"{cb['>=4.0%']['share_of_cells_sum_pct']:.1f}\\%")
    lit_null = f"-\\${abs(mm['part_a']['null_cumulative_error_b_derived'][-1]):.1f}"
    ok = (_gates_ok(mm["gates"])
          and mm["part_b"]["additivity"]["verdict"] == "monthly_shares_readable"
          and claims >= 1
          and lit_thirds in tex and lit_peak in tex and lit_buckets in tex
          and lit_null in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check marginal monthly: "
        f"in-run gates all pass={_gates_ok(mm['gates'])}, "
        f"verdict={mm['part_b']['additivity']['verdict']}, tex run-citation "
        f"count={claims} (want >=1), literals "
        f"{lit_thirds!r}/{lit_peak!r}/{lit_buckets!r}/{lit_null!r} present="
        f"{lit_thirds in tex}/{lit_peak in tex}/{lit_buckets in tex}/{lit_null in tex}"
    )

    # Round-17 R17-J (gate #42): the interpolation spot-check sentence must
    # agree with the committed artifact — reconstruction gates passed and
    # the printed non-kink max and weighted mean are the artifact's.
    isc = json.loads(INTERP_RESULTS.read_text())
    claims = tex.count("\\texttt{interp\\_spot\\_check}")
    nonkink = isc["midpoint_check"]["summary"]["non_kink"]["us"]["max_abs_pp"]
    wmean = isc["realized_check"]["weighted"]["us"]["mean_abs_monthly_pp"]
    lit_nk = f"at most {nonkink:.2f} points"
    lit_wm = f"{wmean:.2f} points of CPR over the window"
    ok = (_gates_ok(isc["gates"]) and claims >= 1
          and lit_nk in tex and lit_wm in tex
          and "August--November 2022" in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check interp spot check: "
        f"reconstruction gates all pass={_gates_ok(isc['gates'])}, tex "
        f"run-citation count={claims} (want >=1), literals {lit_nk!r}/{lit_wm!r} "
        f"present={lit_nk in tex}/{lit_wm in tex}"
    )

    # Round-17 R17-K (gate #43): the SMD paragraph must agree with the
    # committed artifact — gates passed, verdict joint_fit_infeasible, and
    # the printed fitted point and scored recovery are the artifact's.
    smd = json.loads(SMD_RESULTS.read_text())
    fit = smd["fitted"]
    claims = tex.count("\\texttt{smd\\_two\\_moment}")
    lit_m1 = f"{fit['M1']:.4f}"
    lit_m2 = f"{fit['M2']:.4f}"
    lit_rec = f"{smd['scored_at_fit']['share_pct']:.1f}\\% of benchmark"
    lit_pi0 = f"{fit['pi0_realized_point_mass'] * 100:.1f}\\%"
    ok = (_gates_ok(smd["gates"])
          and smd["verdict"] == "joint_fit_infeasible"
          and claims >= 1
          and lit_m1 in tex and lit_m2 in tex and lit_rec in tex
          and lit_pi0 in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check smd two-moment: "
        f"in-run gates all pass={_gates_ok(smd['gates'])}, "
        f"verdict={smd['verdict']}, tex run-citation count={claims} (want >=1), "
        f"literals {lit_m1!r}/{lit_m2!r}/{lit_rec!r}/{lit_pi0!r} present="
        f"{lit_m1 in tex}/{lit_m2 in tex}/{lit_rec in tex}/{lit_pi0 in tex}"
    )

    # Round-17 R17-E (gate #44): the two Danish WAL rows must agree with the
    # committed artifact rows and the derived rule-only shortening.
    wt = json.loads(WALTAB_RESULTS.read_text())
    rows = wt["rows"]
    dus = rows["danish_us_intercept"]
    dlv = rows["danish_level"]
    lit_dus = (f"({dus['mean_cpr_pct']:.2f}\\%) & {dus['wal_june_2022']:.1f} & "
               f"{dus['wal_nov_2025']:.1f}")
    lit_dlv = (f"({dlv['mean_cpr_pct']:.2f}\\%) & {dlv['wal_june_2022']:.1f} & "
               f"{dlv['wal_nov_2025']:.1f}")
    lit_short = f"{wt['rule_only_wal_shortening_years']:.1f}-year rule-only shortening"
    ok = lit_dus in tex and lit_dlv in tex and lit_short in tex
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check danish wal rows: literals "
        f"{lit_dus!r}/{lit_dlv!r}/{lit_short!r} present="
        f"{lit_dus in tex}/{lit_dlv in tex}/{lit_short in tex}"
    )

    # Round-17 follow-up R17-I (gate #45): the curtailment-demonstration
    # sentence must agree with the committed artifact — gates passed, the
    # identity held, and the printed netted totals/wedges are the artifact's.
    cpd = json.loads(CURTDEMO_RESULTS.read_text())
    claims = tex.count("\\texttt{curtailment\\_profile\\_demo}")
    seas = cpd["results"]["seasonal"]
    regi = cpd["results"]["regime_split"]
    lits = [f"\\${seas['netted_b']:.2f} and \\${regi['netted_b']:.2f} billion",
            f"{seas['wedge_pp']:.2f} and {regi['wedge_pp']:.2f} points"]
    ok = (cpd["status"] == "ok" and _gates_ok(cpd["gates"])
          and bool(cpd["demonstration"]["identity_holds"])
          and claims >= 1 and all(l in tex for l in lits))
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check curtailment profile demo: "
        f"status={cpd['status']}, identity_holds="
        f"{cpd['demonstration']['identity_holds']}, tex run-citation "
        f"count={claims} (want >=1), literals present={[l in tex for l in lits]}"
    )

    # Round-17 follow-up R17-M (gate #46): the spread-variants sentence must
    # agree with the committed artifact — parity gates passed, threshold
    # survives at every variant, and the printed range is the artifact's.
    spv = json.loads(SPREADVAR_RESULTS.read_text())
    claims = tex.count("\\texttt{expectation\\_spread\\_variants}")
    var = spv["variants"]
    share = lambda k: var[k]["expected_share_of_realized_cap_shortfall_pct"]
    lit_2022 = (f"{min(share('v1_2022_linear_back_ramp'), share('v4_2022_linear_front_ramp')):.1f}--"
                f"{max(share('v1_2022_linear_back_ramp'), share('v4_2022_linear_front_ramp')):.1f}\\%")
    lit_2025 = (f"{share('v2_2025_all_front'):.1f}--"
                f"{spv['diagnostic']['d1_2025_linear_back_ramp']['expected_share_of_realized_cap_shortfall_pct']:.1f}\\%")
    lit_brk = f"{share('v3_2025_all_december'):.1f}\\%"
    all_survive = (all(bool(v["threshold_survives"]) for v in var.values())
                   and bool(spv["diagnostic"]["d1_2025_linear_back_ramp"]["threshold_survives"]))
    g1s = spv["gates"]["g1_uniform_central_parity"]["status"]
    g2s = spv["gates"]["g2_settlement_aware_parity"]["status"]
    ok = (g1s == "PASS" and g2s == "PASS"
          and all_survive and claims >= 1
          and lit_2022 in tex and lit_2025 in tex and lit_brk in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check spread variants: "
        f"parity g1/g2={g1s}/{g2s}, "
        f"all-survive={all_survive}, tex run-citation count={claims} (want >=1), "
        f"literals {lit_2022!r}/{lit_2025!r}/{lit_brk!r} present="
        f"{lit_2022 in tex}/{lit_2025 in tex}/{lit_brk in tex}"
    )

    # Round-17 follow-up R17-E (gate #47): tab:discount's five rows must
    # agree with the filled-grid artifact — flips as printed, deltas all zero.
    dbd = json.loads(DANBOUND_RESULTS.read_text())
    runs = dbd["runs"]
    ok_flips = all(
        ("{:,}".format(runs[k]["flipped_loan_months"]).replace(",", "{,}") + " of 1{,}683{,}082") in tex
        for k in ("spread_25bp", "spread_50bp", "spread_75bp", "spread_100bp")
    )
    ok_zero = all(v == 0.0 for v in dbd["deltas_vs_baseline_b"].values())
    ok = ok_flips and ok_zero
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check danish grid fill: "
        f"flip literals present={ok_flips}, all deltas zero={ok_zero} "
        f"(grid {sorted(dbd['spreads_bp'])})"
    )

    # Round-18 R18-A (gate #48): subgroup marginal decomposition — verdict,
    # in-run parity/additivity gates, and the printed intensity literals.
    sg = json.loads(SUBGROUP_RESULTS.read_text())
    claims = tex.count("\\texttt{subgroup\\_marginals}")
    ok = (sg["verdict_overall"] == "broad_based_all_dimensions"
          and _gates_ok(sg["gates"]) and claims >= 1
          and "0.88--1.26" in tex and "0.93--1.06" in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check subgroup marginals: "
        f"verdict={sg['verdict_overall']}, in-run gates ok={_gates_ok(sg['gates'])}, "
        f"tex run-citation count={claims} (want >=1), intensity literals present="
        f"{'0.88--1.26' in tex}/{'0.93--1.06' in tex}"
    )

    # Round-18 R18-G (gate #50): regime-split marginal — bit-exact unit-factor
    # parity, the printed h0/floor spans, and the non-cancellation framing.
    rs = json.loads(REGIME_RESULTS.read_text())
    claims = tex.count("\\texttt{regime\\_split\\_marginal}")
    h0lo, h0hi = rs["results"]["h0_span_pp"]
    fl_lo, fl_hi = min(rs["results"]["floor_marginal_pps"]), max(rs["results"]["floor_marginal_pps"])
    ok = (_gates_ok(rs["gates"]) and claims >= 1
          and rs["results"]["verdict_h0"] == "material_sensitivity"
          and f"$+{h0lo:.1f}$ to $+{h0hi:.1f}$ points" in tex
          and f"$+{fl_lo:.1f}$ through $+{fl_hi:.1f}$ points" in tex
          and "scales the marginal rather than cancelling" in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check regime-split marginal: "
        f"in-run gates ok={_gates_ok(rs['gates'])}, verdict={rs['results']['verdict_h0']}, "
        f"tex run-citation count={claims} (want >=1), span literals "
        f"+{h0lo:.1f}/+{h0hi:.1f} and +{fl_lo:.1f}/+{fl_hi:.1f} present="
        f"{f'$+{h0lo:.1f}$ to $+{h0hi:.1f}$ points' in tex}/"
        f"{f'$+{fl_lo:.1f}$ through $+{fl_hi:.1f}$ points' in tex}"
    )

    # Round-18 R18-I (gate #51): danish 125/150bp grid fill — the two new
    # printed rows agree with the artifact, grid spans 0-150bp, prose updated.
    ok_new = all(
        ("{:,}".format(runs[k]["flipped_loan_months"]).replace(",", "{,}") + " of 1{,}683{,}082") in tex
        for k in ("spread_125bp", "spread_150bp")
    )
    ok = (ok_new and sorted(dbd["spreads_bp"]) == [0, 25, 50, 75, 100, 125, 150]
          and ok_zero and "25--150 bp" in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check danish 125/150bp fill: "
        f"new-row literals present={ok_new}, grid={sorted(dbd['spreads_bp'])}, "
        f"all deltas zero={ok_zero}, prose span updated={'25--150 bp' in tex}"
    )

    # Round-18 R18-J (gate #52): grouped calibration — in-run gates, verdict,
    # and the printed holdout ratios/pooled figures are the artifact's.
    gc = json.loads(GROUPCAL_RESULTS.read_text())
    claims = tex.count("\\texttt{grouped\\_calibration}")
    ths = gc["train_holdout_split"]["holdout_2024H1_2025H2"]
    lit_pred = "{:.2f}".format(ths["wmean_pred_cpr_pp"])
    lit_obs = "{:.2f}".format(ths["wmean_obs_cpr_pp"])
    ok = (_gates_ok(gc["gates"]) and claims >= 1
          and gc["interpretation"]["verdict"] == "temporal_drift_post_boundary"
          and "0.64, 0.57, 0.44, 0.43" in tex
          and lit_pred in tex and lit_obs in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check grouped calibration: "
        f"in-run gates ok={_gates_ok(gc['gates'])}, verdict="
        f"{gc['interpretation']['verdict']}, tex run-citation count={claims} "
        f"(want >=1), holdout literals present={'0.64, 0.57, 0.44, 0.43' in tex}/"
        f"{lit_pred in tex}/{lit_obs in tex}"
    )

    # Round-18 R18-B (gate #53): fonseca band anchor — in-run gates, placement
    # above the L&R high edge, and the printed marginal/edge literals.
    fb = json.loads(FONSECA_RESULTS.read_text())
    claims = tex.count("\\texttt{fonseca\\_band\\_anchor}")
    pl = fb["placement"]
    hi_edge_b = pl["lr_band_marginal_b_5.5_to_7.7"][-1]
    lit_fb_b = "$+\\${:.1f}$ billion".format(pl["fonseca_marginal_b"])
    lit_fb_pp = "($+{:.1f}$ points)".format(pl["fonseca_marginal_pp"])
    lit_edge = "$+\\${:.1f}$ billion".format(hi_edge_b)
    ok = (fb["gates_all_pass"] and claims >= 1
          and pl["vs_lr_band"] == "above_lr_high_edge"
          and lit_fb_b in tex and lit_fb_pp in tex and lit_edge in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check fonseca band anchor: "
        f"gates_all_pass={fb['gates_all_pass']}, placement={pl['vs_lr_band']}, "
        f"tex run-citation count={claims} (want >=1), literals "
        f"{pl['fonseca_marginal_b']:.1f}/{pl['fonseca_marginal_pp']:.1f}/{hi_edge_b:.1f} present="
        f"{lit_fb_b in tex}/{lit_fb_pp in tex}/{lit_edge in tex}"
    )

    # Round-18 R18-K (gate #54): 2015-16 vintage subleg — in-run parity to the
    # committed bound and the printed exposure-share literal.
    vs = json.loads(V1516_RESULTS.read_text())
    claims = tex.count("\\texttt{vintage\\_1516\\_subleg}")
    seg = vs["results"]["vintage_2015_2016_specific"]
    lit_share = "99.99\\%"
    ok = (vs["status"] == "PASS" and _gates_ok(vs["gates"]) and claims >= 1
          and "{:.2f}".format(seg["exposure_share_within_pre2017_pct"]) == "99.99"
          and lit_share in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check vintage 2015-16 subleg: "
        f"status={vs['status']}, in-run gates ok={_gates_ok(vs['gates'])}, "
        f"tex run-citation count={claims} (want >=1), share "
        f"{seg['exposure_share_within_pre2017_pct']:.2f} printed={lit_share in tex}"
    )

    # Round-18 R18-C (gate #49): DTI threshold sweep — in-run gates, floor
    # re-anchored in band at every threshold, and the printed trapped literals.
    dti = json.loads(DTI_RESULTS.read_text())
    claims = tex.count("\\texttt{dti\\_threshold\\_sweep}")
    legs = dti["legs"]
    lit_36 = "\\${:.1f} ".format(legs["dti_0.36"]["trapped_b"])
    lit_50 = "\\${:.1f} billion".format(legs["dti_0.50"]["trapped_b"])
    floor_in_band = all(v["in_band"] for v in dti["floor_retention"]["per_dti"].values())
    ok = (dti["status"] == "OK" and _gates_ok(dti["gates"]) and claims >= 1
          and floor_in_band and lit_36 in tex and lit_50 in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check DTI threshold sweep: "
        f"status={dti['status']}, in-run gates ok={_gates_ok(dti['gates'])}, "
        f"floor in-band all thresholds={floor_in_band}, tex run-citation "
        f"count={claims} (want >=1), trapped literals present={lit_36 in tex}/{lit_50 in tex}"
    )

    # Round-18 R18-L / E3 (gate #55): cohort timing diagnostic — in-run gates,
    # aggregate parity anchors reproduced, and the printed cohort-range literals.
    ct = json.loads(COHORTTIMING_RESULTS.read_text())
    claims = tex.count("\\texttt{cohort\\_timing\\_diagnostic}")
    anc = ct["aggregate_anchors_reproduced"]
    ct_gates = ct["gates"]
    ct_gates_ok = (all(g.get("pass") for g in ct_gates) if isinstance(ct_gates, list)
                   else _gates_ok(ct_gates))
    ok = (ct["status"] == "success" and ct_gates_ok and claims >= 1
          and abs(anc["abm_ccf_lag0"] - (-0.3183375411255578)) < 1e-9
          and abs(anc["pathb_delta_velocity_lag0"] - (-0.9428012605757549)) < 1e-9
          and "$-0.05$ to $-0.16$" in tex and "$-0.87$ and $-0.94$" in tex
          and "reproducing the aggregate $-0.318$" in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check cohort timing diagnostic: "
        f"status={ct['status']}, in-run gates ok={ct_gates_ok}, "
        f"anchors abm/pathb reproduced="
        f"{abs(anc['abm_ccf_lag0'] - (-0.3183375411255578)) < 1e-9}/"
        f"{abs(anc['pathb_delta_velocity_lag0'] - (-0.9428012605757549)) < 1e-9}, "
        f"tex run-citation count={claims} (want >=1), cohort-range literals present="
        f"{'$-0.05$ to $-0.16$' in tex}/{'$-0.87$ and $-0.94$' in tex}"
    )

    # Panel revision (gate #56): out-of-window baseline turnover floor anchor —
    # the run behind §VII.I's provenance check must agree with the committed
    # artifact (pre-committed does-not-corroborate verdict, headline CPR and the
    # in-window validation reproduced), and be cited once in the tex with its
    # printed literals. The lone floor claim that previously carried no gate.
    oow = json.loads(OOWFLOOR_RESULTS.read_text())
    claims = tex.count("\\texttt{out\\_of\\_window\\_floor}")
    oow_head = oow["headline_out_of_window_floor_cpr_pct"]
    inw_deep = oow["in_window_deep_OTM_validation"]["gap<=-0.02_age>=12"]["cpr_pct"]
    has_61 = "6.1\\%" in tex
    has_3839 = "3.8--3.9\\%" in tex
    # v17: the undifferentiated "5.1--6.1%" out-of-the-money grid range is
    # retired. §VII.I now separates the refi-contaminated pooled/2019 reads from
    # the defensible 2018 rising-rate leg, so the gate tracks the split instead.
    has_5161 = "4.70--5.33\\%" in tex and "6.91\\%" in tex
    has_dir = "$+2.1$ to $+2.4$" in tex
    ok = (oow["gate_verdict"] == "DOES_NOT_CORROBORATE"
          and abs(oow_head - 6.065) < 1e-3
          and abs(inw_deep - 3.84) < 1e-3
          and oow["production_floor_pct"] == 4.0
          and claims >= 1
          and has_61 and has_3839 and has_5161 and has_dir)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check out-of-window floor: "
        f"verdict={oow['gate_verdict']}, headline={oow_head} (want 6.065), "
        f"in-window deep-OTM={inw_deep} (want 3.84), tex run-citation count={claims} "
        f"(want >=1), literals present={has_61}/{has_3839}/{has_5161}/{has_dir}"
    )

    # v17 (gate #57): out-of-sample identification of the lock-in marginal. The
    # headline marginal is now the off-window-floor figure, so the run behind it
    # must agree with the manuscript on every printed quantity: the parity gate
    # against the committed production anchors, the hard wiring checks, the
    # clean-floor band and its marginal, the held-out-months marginal, and the
    # sign-robustness verdict. Also asserts the paper does not silently reinstate
    # a point estimate for a floor the run reports as only range-identifiable.
    oos = json.loads(OOSIDENT_RESULTS.read_text())
    oos_h = oos["headline_oos_marginal"]
    oos_hold = oos["instrument2_temporal_holdout"]["at_calibrated_floor_h_cal"]
    oos_claims = tex.count("\\texttt{oos\\_identification}")
    oos_by_floor = {
        round(r["floor_annual_cpr_pct"], 3): r["band"]["6.5"]["marginal_pp"]
        for r in oos["instrument1_marginal_table"]
    }
    oos_lits = {
        "point_b": "$+\\$42.6$ billion" in tex,
        "point_pp": "$+5.6$" in tex,
        "range_pp": "$+4.3$ to $+6.8$" in tex,
        "heldout": "$+\\$45.1$ billion" in tex,
        "insample_demoted": "in-sample calibration point" in tex,
        "clean_band": "4.70--5.33\\%" in tex,
    }
    oos_ok = (
        oos["parity_all_pass"]
        and all(oos["self_checks_hard_wiring"].values())
        # manuscript-printed values must match the artifact
        and abs(oos_h["clean_marginal_b_point_at_6.5"] - 42.6) < 0.05
        and abs(oos_h["clean_marginal_pp_point_at_6.5"] - 5.6) < 0.05
        and oos_h["clean_floor_band_pct"] == [4.695, 5.334]
        and abs(oos_by_floor[4.695] - 6.8) < 0.05
        and abs(oos_by_floor[5.334] - 4.3) < 0.05
        # 0.05 == the one-decimal rounding tolerance, not a widened one: the
        # artifact reads 45.145, which prints as 45.1. An earlier draft printed
        # 45.2 and slackened this gate to 0.06 to admit it; that inverted the
        # gate's purpose, so the bound is back at the house standard.
        and abs(oos_hold["heldout_marginal_b"] - 45.1) < 0.05
        and oos_hold["heldout_sign_positive"]
        and oos_hold["additivity_ok"]
        and abs(oos_h["in_sample_production_point_b"] - 70.345) < 0.01
        and oos["step4_sign_robustness"]["all_floor_x_band_cells_positive"]
        # the run reports a range, not a point: the paper must say so
        and oos["verdict"]["single_floor_identifiable"] is False
        and oos_claims >= 1
        and all(oos_lits.values())
    )
    failures += 0 if oos_ok else 1
    print(
        f"[{'PASS' if oos_ok else 'FAIL'}] cross-check OOS identification: "
        f"parity={oos['parity_all_pass']}, hard-checks="
        f"{all(oos['self_checks_hard_wiring'].values())}, "
        f"point={oos_h['clean_marginal_b_point_at_6.5']:.2f}B/"
        f"{oos_h['clean_marginal_pp_point_at_6.5']:.2f}pp (want 42.6/5.6), "
        f"band={oos_h['clean_floor_band_pct']}, "
        f"heldout={oos_hold['heldout_marginal_b']:.2f}B (want 45.1), "
        f"all-cells-positive="
        f"{oos['step4_sign_robustness']['all_floor_x_band_cells_positive']}, "
        f"tex run-citation count={oos_claims} (want >=1), "
        f"literals={ {k: v for k, v in oos_lits.items() if not v} or 'all present'}"
    )

    # Panel revision (gate #58): seasonalized turnover floor and the timing
    # concession. Section~\ref{sec:robustness-seasonalfloor} makes three kinds of
    # claim that can drift independently of the run, so the gate binds all three:
    # (i) the constant-4.0%/4.5% control legs reproduce the committed production
    # anchors BITWISE — if they ever stop doing so the whole subsection is
    # measuring a different microsimulation than the paper's headline; (ii) the
    # four legs' marginals as printed in tab:seasonalfloor; and (iii) the two
    # placebo families that carry the argument, since the subsection's thesis is
    # that the movement is floor dispersion rather than calendar timing and that
    # the frozen timing rule has no power. The adjudicated verdict string is
    # asserted directly: the artifact records the rule as MET AS WRITTEN, so
    # nothing but the verdict distinguishes "the rule passed" from "the pass is
    # uninformative", and the manuscript's levels-only restriction rests on the
    # latter. NOTE ON THE RETENTION SHARE: an early draft of the write-up quoted
    # 93.4% retention from a three-permutation probe. The committed fourteen-draw
    # family reads 89.21%, the manuscript prints 89.2%, and this gate binds the
    # artifact — the larger number is retired and must not reappear.
    sf = json.loads(SEASFLOOR_RESULTS.read_text())
    b3 = json.loads(B3TIMING_RESULTS.read_text())
    sf_claims = tex.count("\\texttt{seasonal\\_floor\\_timing}")
    sf_par = sf["parity_gates"]
    # (i) bit-exact parity: four flat_4.0 anchors + two flat_4.5 anchors
    sf_parity_keys = [
        "flat_4.0::central_trapped_b", "flat_4.0::null_trapped_b",
        "flat_4.0::lockin_marginal_b", "flat_4.0::lockin_marginal_share_pp",
        "flat_4.5::lockin_marginal_b", "flat_4.5::lockin_marginal_share_pp",
    ]
    sf_parity_ok = (
        len(sf_par) == len(sf_parity_keys)
        and all(k in sf_par and sf_par[k]["pass_bitwise"] and sf_par[k]["abs_diff"] == 0.0
                for k in sf_parity_keys)
        and sf["parity_gates_all_pass"] and sf["parity_gates_bitwise"]
        and sf["month_sequence_self_check_pass"]
    )
    # the B3 parity gate must be scored against the committed Theil file, not a
    # hardcoded constant — assert the recorded provenance of every "want".
    b3_par = b3["parity_gate"]
    b3_parity_ok = (
        b3["parity_gate_pass"]
        and all(v["pass"] and v["abs_diff"] == 0.0
                and v["want_source"].startswith("theil_data.json:estimators.path_b")
                for v in b3_par.values())
    )
    # ---- HARDENING: DERIVE, DON'T READ ---------------------------------
    # Everything below recomputes, from the per-leg / per-draw PRIMITIVES, each
    # aggregate this gate previously took on faith from the module that wrote
    # it. A stored headline is now required to equal the value the gate derives
    # independently, so a module that miscomputes its own summary FAILS here
    # instead of certifying itself. IDENT_TOL is the arithmetic-identity
    # tolerance; every identity below was verified to close at exactly 0.0 when
    # this hardening was written, and every cross-artifact tie asserted with
    # "==" was verified BIT-EXACT, so the tolerance is slack, not a fudge.
    IDENT_TOL = 1e-9
    sf_lr = sf["legs_run"]
    sf_flat40_b = sf_lr["flat_4.0"]["lockin_marginal_b"]
    sf_flat40_pp = sf_lr["flat_4.0"]["lockin_marginal_share_pp"]
    b3_perm = b3["permutation_null"]
    b3_byperm = b3_perm["by_permutation"]
    sf_tc = sf["timing_criterion"]

    def _frozen_rule(u2, r):
        """The frozen rule evaluated from its own two inputs: U2<1 AND r>0.

        Every stored pass/verdict flag in both artifacts is checked against
        THIS, so a flag that contradicts the numbers it claims to summarize
        fails the gate.
        """
        return (u2 < 1.0) and (r > 0.0)

    # (H1) accounting identity: every leg's marginal is central minus null, in
    # both units. This is what makes "marginal" mean what the paper says.
    sf_marg_identity_ok = all(
        abs((v["central"]["trapped_b"] - v["null"]["trapped_b"])
            - v["lockin_marginal_b"]) < IDENT_TOL
        and abs((v["central"]["share_pct"] - v["null"]["share_pct"])
                - v["lockin_marginal_share_pp"]) < IDENT_TOL
        for v in sf_lr.values()
    )
    # (H2) the frozen-rule verdict, derived per leg and per draw, matched
    # against every stored flag: the four legs' central and null families in
    # seasonal_floor_timing, the same four legs rescored in b3, b3's beta1=0
    # null-leg verdicts, all 14 permutations, and both 12-rotation families.
    sf_rule_ok = (
        all(_frozen_rule(t["u2_diffs"], t["detrended_lag0_r"])
            == t["timing_pass"]
            == (t["u2_below_1"] and t["detrended_lag0_r_positive"])
            for leg in sf_lr.values() for t in (leg["central"]["timing"],
                                                leg["null"]["timing"]))
        and all(_frozen_rule(sf_tc["by_leg"][k]["u2_diffs"],
                             sf_tc["by_leg"][k]["detrended_lag0_r"])
                == sf_tc["by_leg"][k]["timing_pass"]
                and _frozen_rule(sf_tc["by_leg_null_pq0"][k]["u2_diffs"],
                                 sf_tc["by_leg_null_pq0"][k]["detrended_lag0_r"])
                == sf_tc["by_leg_null_pq0"][k]["timing_pass"]
                for k in sf_lr)
        and all(_frozen_rule(s["u2_diffs"], s["detrended_lag0_r"])
                == (s["verdict"] == "PASS")
                == (s["u2_lt_1"] and s["detrended_r_positive"])
                for s in (b3["scores_primary"][k] for k in sf_lr))
        and all(_frozen_rule(v["u2_diffs"], v["detrended_lag0_r"])
                == (v["verdict"] == "PASS")
                for v in b3["null_leg_scores"]["by_leg"].values())
        and all(_frozen_rule(v["u2_diffs"], v["detrended_lag0_r"])
                == (v["verdict"] == "PASS") for v in b3_byperm.values())
        and all(_frozen_rule(v["u2_diffs"], v["detrended_lag0_r"])
                == (v["verdict"] == "PASS")
                for leg in ("shape_only", "prereg_4.5")
                for v in b3["rotation_placebo"]["by_base_leg"][leg]
                        ["by_rotation"].values())
        # ...and the two DERIVED verdict-level summaries the manuscript quotes
        and [k for k in sf_lr if sf_tc["by_leg"][k]["timing_pass"]] \
            == b3["seasonal_legs_passing"] == ["shape_only", "prereg_4.5"]
        and (all(sf_tc["by_leg"][k]["timing_pass"]
                 for k in ("shape_only", "prereg_4.5"))
             == b3["frozen_rule_met_as_written"] is True)
        and sum(1 for v in b3["null_leg_scores"]["by_leg"].values()
                if v["verdict"] == "PASS") == b3["null_leg_scores"]["n_clearing"] == 2
    )
    # (H3) the permutation family, derived draw by draw. The retention share of
    # each draw must equal its own effect divided by the true shape effect, and
    # the true shape effect must itself be shape_only minus flat_4.0 — so the
    # 89.2% the manuscript prints is forced by the 14 recorded marginals rather
    # than asserted beside them.
    sf_true_shape_b = sf_lr["shape_only"]["lockin_marginal_b"] - sf_flat40_b
    sf_perm_mb = [v["lockin_marginal_b"] for v in b3_byperm.values()]
    sf_perm_eff = [v - sf_flat40_b for v in sf_perm_mb]
    sf_perm_sh = [e / sf_true_shape_b for e in sf_perm_eff]
    sf_perm_derived_ok = (
        len(b3_byperm) == 14
        and abs(sf_true_shape_b - b3_perm["true_shape_effect_b"]) < IDENT_TOL
        and abs(sf_true_shape_b
                - sf["placebo_summary"]["true_shape_effect_b"]) < IDENT_TOL
        and all(abs((v["lockin_marginal_b"] - sf_flat40_b)
                    - v["effect_vs_flat40_b"]) < IDENT_TOL
                and abs((v["lockin_marginal_b"] - sf_flat40_b)
                        / sf_true_shape_b
                        - v["share_of_true_shape_effect_retained"]) < IDENT_TOL
                for v in b3_byperm.values())
        and abs(sum(sf_perm_sh) / len(sf_perm_sh)
                - sf["placebo_summary"]["permutation"]
                    ["share_of_shape_effect_retained_mean"]) < IDENT_TOL
        and abs(min(sf_perm_sh)
                - sf["placebo_summary"]["permutation"]
                    ["share_of_shape_effect_retained_min"]) < IDENT_TOL
        and abs(max(sf_perm_sh)
                - sf["placebo_summary"]["permutation"]
                    ["share_of_shape_effect_retained_max"]) < IDENT_TOL
        and abs(sum(sf_perm_mb) / len(sf_perm_mb)
                - sf["placebo_summary"]["permutation"]["marginal_b_mean"]) < IDENT_TOL
        and abs(min(sf_perm_mb)
                - sf["placebo_summary"]["permutation"]["marginal_b_min"]) < IDENT_TOL
        and abs(max(sf_perm_mb)
                - sf["placebo_summary"]["permutation"]["marginal_b_max"]) < IDENT_TOL
        # the DERIVED pass count and its membership, against the stored list
        and [n for n, v in b3_byperm.items() if v["verdict"] == "PASS"]
            == sf["placebo_summary"]["permutation"]["permutations_clearing_frozen_rule"]
            == b3_perm["permutations_clearing_frozen_rule"]
        and sum(1 for v in b3_byperm.values() if v["verdict"] == "PASS")
            == sf["placebo_summary"]["permutation"]["n_clearing_frozen_rule"]
            == b3_perm["n_clearing_frozen_rule"] == 3
        and abs(min(v["u2_diffs"] for v in b3_byperm.values())
                - sf["placebo_summary"]["permutation"]["best_permutation_u2"]) < IDENT_TOL
        # the two files must carry the SAME draws (different modules wrote them)
        and all(sf["placebo_permutation"][n]["lockin_marginal_b"]
                == v["lockin_marginal_b"]
                and sf["placebo_permutation"][n]["central_timing"]["u2_diffs"]
                == v["u2_diffs"]
                and sf["placebo_permutation"][n]["central_timing"]["detrended_lag0_r"]
                == v["detrended_lag0_r"]
                for n, v in b3_byperm.items())
    )
    # (H4) the rotation family, derived rotation by rotation: the wrong-month
    # pass COUNT is recomputed by excluding the identity and re-evaluating the
    # rule, and rot00 is required to reproduce the true leg bitwise.
    sf_rot_derived_ok = True
    for _leg in ("shape_only", "prereg_4.5"):
        _rp = b3["rotation_placebo"]["by_base_leg"][_leg]
        _byr = _rp["by_rotation"]
        _S = sf["placebo_summary"]["rotation"][_leg]
        _true_u2 = sf_tc["by_leg"][_leg]["u2_diffs"]
        _true_r = sf_tc["by_leg"][_leg]["detrended_lag0_r"]
        _wrong = [n for n in _byr if n != "rot00"]
        _wpass = [n for n in _wrong if _byr[n]["verdict"] == "PASS"]
        sf_rot_derived_ok = sf_rot_derived_ok and (
            len(_byr) == _rp["n_rotations"] == _S["n_rotations"] == 12
            and len(_wrong) == _S["n_wrong_month_rotations"] == 11
            and len(_wpass) == _S["n_wrong_month_rotations_passing"] == 1
            and _wpass == _S["wrong_month_rotations_passing"]
            and abs(len(_wpass) / len(_wrong)
                    - _S["placebo_pass_rate_wrong_month_only"]) < IDENT_TOL
            # the identity rotation IS the true profile — derived, not asserted
            and (_byr["rot00"]["u2_diffs"] == _true_u2
                 and _byr["rot00"]["detrended_lag0_r"] == _true_r)
                == _S["identity_rot00_reproduces_true_leg"] is True
            # "beats the true profile on U2" re-evaluated from the U2 values
            and all((_byr[n]["u2_diffs"] < _true_u2)
                    == _byr[n]["beats_true_profile_on_u2"] for n in _byr)
            and {n: _byr[n]["u2_diffs"] for n in _wrong
                 if _byr[n]["beats_true_profile_on_u2"]} \
                == _S["wrong_month_rotations_beating_true_u2"]
            # both files must carry the same rotations
            and all(sf["placebo_rotation"][_leg][n]["central_timing"]["u2_diffs"]
                    == _byr[n]["u2_diffs"]
                    and sf["placebo_rotation"][_leg][n]["central_timing"]
                        ["detrended_lag0_r"] == _byr[n]["detrended_lag0_r"]
                    for n in _byr)
        )
    # (H5) the Jensen split must be a partition of the shape effect: leakage is
    # derived from the convexity-matched leg, the dispersion share is its
    # complement, and the two shares must sum to exactly one.
    _J = b3["jensen_equivalent_flat"]
    _SJ = sf["placebo_summary"]["jensen_flat"]
    sf_leak_b = _J["measured_marginal_b"] - sf_flat40_b
    sf_jensen_derived_ok = (
        _J["flat40_marginal_b"] == sf_flat40_b
        and _J["measured_marginal_b"] == sf["placebo_jensen_flat"]["lockin_marginal_b"]
        and abs(sf_leak_b - _J["level_leakage_b"]) < IDENT_TOL
        and abs(sf_leak_b - _SJ["effect_vs_flat40_b"]) < IDENT_TOL
        and abs(sf_leak_b / sf_true_shape_b
                - _SJ["share_of_shape_effect_from_level_leakage"]) < IDENT_TOL
        and abs((1.0 - sf_leak_b / sf_true_shape_b)
                - _SJ["share_of_shape_effect_from_floor_dispersion"]) < IDENT_TOL
        and abs(_SJ["share_of_shape_effect_from_level_leakage"]
                + _SJ["share_of_shape_effect_from_floor_dispersion"] - 1.0) < IDENT_TOL
    )
    # (H6) level + shape + interaction == total, with the INTERACTION forced to
    # be the residual rather than an independent field, in both units; and the
    # 30.85% path-wise interaction share derived from its own two moments.
    _D = sf["decomposition"]
    _L = b3["level_shape_interaction"]
    _lev = sf_lr["flat_4.5"]["lockin_marginal_b"] - sf_flat40_b
    _shp = sf_lr["shape_only"]["lockin_marginal_b"] - sf_flat40_b
    _tot = sf_lr["prereg_4.5"]["lockin_marginal_b"] - sf_flat40_b
    _levp = sf_lr["flat_4.5"]["lockin_marginal_share_pp"] - sf_flat40_pp
    _shpp = sf_lr["shape_only"]["lockin_marginal_share_pp"] - sf_flat40_pp
    _totp = sf_lr["prereg_4.5"]["lockin_marginal_share_pp"] - sf_flat40_pp
    _W = _L["path_wise_monthly_cpr_pp"]
    sf_decomp_ok = (
        abs(_lev - _D["level_flat45_minus_flat40"]["delta_marginal_b"]) < IDENT_TOL
        and abs(_shp - _D["shape_shapeonly_minus_flat40"]["delta_marginal_b"]) < IDENT_TOL
        and abs(_tot - _D["total_prereg45_minus_flat40"]["delta_marginal_b"]) < IDENT_TOL
        and abs((_tot - _lev - _shp)
                - _D["interaction_total_minus_level_minus_shape"]["delta_marginal_b"]) < IDENT_TOL
        and all(abs(a - _L["marginal_b"][n]) < IDENT_TOL for a, n in
                ((_lev, "level"), (_shp, "shape"), (_tot, "total"),
                 (_tot - _lev - _shp, "interaction")))
        and all(abs(a - _L["marginal_share_pp"][n]) < IDENT_TOL for a, n in
                ((_levp, "level"), (_shpp, "shape"), (_totp, "total"),
                 (_totp - _levp - _shpp, "interaction")))
        # closure: the three parts must reconstitute the total exactly
        and abs((_L["marginal_b"]["level"] + _L["marginal_b"]["shape"]
                 + _L["marginal_b"]["interaction"]) - _L["marginal_b"]["total"]) < IDENT_TOL
        and abs(_W["mean_abs_interaction_residual"] / _W["mean_abs_total_movement"]
                - _W["interaction_share_of_total_movement"]) < IDENT_TOL
    )
    # (H7) CROSS-ARTIFACT TIES — the strongest checks here, because the files on
    # each side were produced by different modules in different runs. All four
    # are bit-exact.
    _row45 = [r for r in json.loads(FLOORSWEEP_RESULTS.read_text())["rows"]
              if abs(r["floor_annual_cpr_pct"] - 4.5) < 1e-9][0]
    _nl = json.loads(NULL_RESULTS.read_text())
    _tb = json.loads(THEIL_RESULTS.read_text())["estimators"]["path_b"]
    sf_cross_ok = (
        # flat_4.0 leg IS the production no-lock-in null run, all six anchors
        sf_lr["flat_4.0"]["central"]["trapped_b"] == _nl["central_trapped_b"]
        and sf_lr["flat_4.0"]["null"]["trapped_b"] == _nl["null_trapped_b"]
        and sf_lr["flat_4.0"]["central"]["share_pct"] == _nl["central_share_pct"]
        and sf_lr["flat_4.0"]["null"]["share_pct"] == _nl["null_share_pct"]
        and sf_flat40_b == _nl["lockin_marginal_b"]
        and sf_flat40_pp == _nl["lockin_marginal_share_pp"]
        # flat_4.5 leg IS the 4.5% row of the committed floor sweep
        and sf_lr["flat_4.5"]["lockin_marginal_b"] == _row45["lockin_marginal_b"]
        and sf_lr["flat_4.5"]["lockin_marginal_share_pp"] == _row45["lockin_marginal_share_pp"]
        and sf_lr["flat_4.5"]["central"]["trapped_b"] == _row45["central"]["trapped_b"]
        and sf_lr["flat_4.5"]["null"]["trapped_b"] == _row45["null"]["trapped_b"]
        # b3's parity "want" is the committed Theil file, read here independently
        and all(b3_par[k]["want"] == _tb[k] and b3_par[k]["got"] == _tb[k]
                for k in ("u1_levels", "u2_diffs", "u1_detrended"))
        # ...and b3's own scoring of the production leg reproduces that file
        and all(b3["scores_primary"]["flat_4.0"][k] == _tb[k]
                for k in ("u1_levels", "u2_diffs", "u1_detrended"))
        # CONSISTENCY, NOT INDEPENDENCE (round-20 correction). A prior report
        # described the b3 <-> seasonal_floor_timing pair below as an
        # INDEPENDENT cross-artifact tie. It is not: hazard/b3_timing_rescore.py
        # reads seasonal_floor_timing_results.json at lines 162 and 684, so the
        # two sides of this comparison share a source and cannot corroborate
        # each other. What it does catch is b3 mangling the legs it ingested —
        # a real failure mode, and worth binding — so the check stays, under its
        # correct name. The genuinely independent ties in this block are the
        # ones against theil_data.json, no_lockin_null_results.json and the
        # committed floor sweep, which b3 does not read.
        and all(b3["scores_primary"][k][f] == sf_lr[k]["central"]["timing"][f]
                for k in sf_lr
                for f in ("u1_levels", "u2_diffs", "u1_detrended",
                          "detrended_lag0_r"))
        and all(sf["theil_baseline_cross_check"][k]["got"]
                == sf_lr["flat_4.0"]["central"]["timing"][k]
                for k in ("u1_levels", "u2_diffs", "u1_detrended"))
    )
    sf_derived_ok = (
        sf_marg_identity_ok and sf_rule_ok and sf_perm_derived_ok
        and sf_rot_derived_ok and sf_jensen_derived_ok and sf_decomp_ok
        and sf_cross_ok
    )
    # ---- end hardening --------------------------------------------------
    # (ii) the four legs' marginals, at the manuscript's printed precision
    sf_legs = {k: (v["lockin_marginal_b"], v["lockin_marginal_share_pp"])
               for k, v in sf["legs_run"].items()}
    sf_legs_want = {
        "flat_4.0": (70.345, 9.20), "flat_4.5": (57.642, 7.54),
        "shape_only": (65.448, 8.56), "prereg_4.5": (54.305, 7.10),
    }
    sf_legs_ok = all(
        k in sf_legs and abs(sf_legs[k][0] - w[0]) < 0.0005
        and abs(sf_legs[k][1] - w[1]) < 0.005
        for k, w in sf_legs_want.items()
    )
    # (iii) placebo families
    sf_perm = sf["placebo_summary"]["permutation"]
    sf_rot = sf["placebo_summary"]["rotation"]
    # NOTE: every quantity compared to a manuscript literal below is the value
    # the gate DERIVED above from the primitives, not the stored aggregate. The
    # stored aggregate is separately required (in sf_derived_ok) to equal it, so
    # the .tex, the summary field and the raw draws must all agree.
    sf_perm_ok = (
        len(b3_byperm) == sf_perm["n"] == 14
        and abs(sum(sf_perm_sh) / len(sf_perm_sh) - 0.892) < 0.0005
        and abs(min(sf_perm_sh) - 0.699) < 0.0005
        and abs(max(sf_perm_sh) - 1.028) < 0.0005
        and sum(1 for v in b3_byperm.values() if v["verdict"] == "PASS") == 3
    )
    sf_rot_ok = all(
        len([n for n in b3["rotation_placebo"]["by_base_leg"][leg]["by_rotation"]
             if n != "rot00"]) == sf_rot[leg]["n_wrong_month_rotations"] == 11
        and len([n for n, v in b3["rotation_placebo"]["by_base_leg"][leg]
                 ["by_rotation"].items()
                 if n != "rot00" and v["verdict"] == "PASS"]) \
            == sf_rot[leg]["n_wrong_month_rotations_passing"] == 1
        and sf_rot[leg]["identity_rot00_reproduces_true_leg"]
        for leg in ("shape_only", "prereg_4.5")
    )
    sf_jensen = sf["placebo_summary"]["jensen_flat"]
    sf_jensen_ok = (
        abs(sf_leak_b / sf_true_shape_b - 0.039) < 0.0005
        and abs(1.0 - sf_leak_b / sf_true_shape_b - 0.961) < 0.0005
        and abs(sf_jensen["share_of_shape_effect_from_level_leakage"] - 0.039) < 0.0005
        and abs(sf_jensen["share_of_shape_effect_from_floor_dispersion"] - 0.961) < 0.0005
    )
    sf_verdict_ok = (
        b3["verdict"] == "CONCEDE_LEVELS_ONLY"
        and b3["frozen_rule_met_as_written"] is True
        and b3["frozen_rule_has_discriminating_power"] is False
    )
    sf_lits = {
        "parity_central": "\\$818.530 billion" in tex,
        "parity_null": "\\$748.185 billion" in tex,
        "marg_flat40": "$+\\$70.345$ billion" in tex,
        "marg_flat45": "$+57.642$" in tex and "$+7.54$" in tex,
        "marg_shape": "$+65.448$" in tex and "$+8.56$" in tex,
        "marg_prereg": "$+54.305$" in tex and "$+7.10$" in tex,
        "shape_effect": "$-\\$4.897$ billion" in tex,
        "perm_share": "89.2\\%" in tex,
        "rot_count": "1 of 11 wrong-month rotations" in tex,
        "dispersion_split": "3.9\\%" in tex and "96.1\\%" in tex,
        # the verdict, in the manuscript's own words, in body and abstract
        "levels_only_body": "restrict every claim in this paper to levels" in tex,
        # ROUND-32 (C-R1a): the abstract's bare "identifies levels only" was
        # self-refuting beside Section V.E's "does not identify levels" -- the
        # word carried the TIMING concession here and the LEVEL claim there,
        # with nothing signposting the difference. The abstract now states both
        # truths, and this pin follows the timing half to its new wording.
        "levels_only_abstract": "not a level and not monthly timing" in tex,
        # the retired early-draft retention share must not reappear
        "no_stale_934": "93.4\\%" not in tex,
    }
    # the $-4.897B shape effect the manuscript prints must be the DERIVED
    # difference of two run legs, not a field
    sf_shape_lit_ok = abs(sf_true_shape_b - (-4.897)) < 0.0005
    sf_ok = (sf_parity_ok and b3_parity_ok and sf_legs_ok and sf_perm_ok
             and sf_rot_ok and sf_jensen_ok and sf_verdict_ok
             and sf_derived_ok and sf_shape_lit_ok
             and sf_claims >= 1 and all(sf_lits.values()))
    failures += 0 if sf_ok else 1
    print(
        f"[{'PASS' if sf_ok else 'FAIL'}] cross-check seasonal floor timing: "
        f"derived-not-read={sf_derived_ok} "
        f"(marg-identity={sf_marg_identity_ok}, frozen-rule-rederived={sf_rule_ok}, "
        f"perm={sf_perm_derived_ok}, rot={sf_rot_derived_ok}, "
        f"jensen={sf_jensen_derived_ok}, decomp={sf_decomp_ok}, "
        f"cross-artifact={sf_cross_ok}), "
        f"parity bitwise={sf_parity_ok} (6 anchors), b3 parity-from-file={b3_parity_ok}, "
        f"legs={sf_legs_ok} "
        f"({sf_legs['flat_4.0'][0]:.3f}/{sf_legs['flat_4.5'][0]:.3f}/"
        f"{sf_legs['shape_only'][0]:.3f}/{sf_legs['prereg_4.5'][0]:.3f}B), "
        f"permutation retention="
        f"{sf_perm['share_of_shape_effect_retained_mean']:.4f} (want 0.892), "
        f"rotation wrong-month passes="
        f"{sf_rot['shape_only']['n_wrong_month_rotations_passing']}/"
        f"{sf_rot['shape_only']['n_wrong_month_rotations']}, "
        f"verdict={b3['verdict']}, tex run-citation count={sf_claims} (want >=1), "
        f"literals={ {k: v for k, v in sf_lits.items() if not v} or 'all present'}"
    )

    # Panel revision (gate #59): the floor-cyclicality ATTRIBUTION. The kappa
    # grid of floor_cyclical.py was written up as a bracket on the floor's
    # co-movement with the rate cycle; floor_cyclical_permutation.py shows the
    # span is predominantly order-free dispersion under eq. (3)'s hard maximum,
    # and Section~\ref{sec:pathb} now says so. This gate exists because that
    # correction is a claim about DECOMPOSITION, and a decomposition is exactly
    # the kind of number that drifts silently: every share below is a ratio of
    # two run outputs, so a rerun that moved either leg would leave the prose
    # arithmetically wrong while every individual marginal still looked fine.
    # Four things are bound. (i) BOTH parity gates, because the attribution is
    # worthless unless the decomposing run is the same microsimulation as the
    # committed cells: bit-exact equality (not tolerance) on all seven
    # floor_cyclical cells, plus the INDEPENDENT additive cross-gate scored
    # against floor_form_results.json, which is the only check that certifies
    # the FLOOR_MODE switch the mechanism test turns on. (ii) The two headline
    # shares the manuscript leads with — 85.0% of the span surviving a
    # time-order scramble, 98.0% of it eliminated by the rule swap. (iii) The
    # low-endpoint three-way split 13.3/71.0/15.7 and the +0.161pp high
    # endpoint, since these are what license the sentence that the high endpoint
    # "is production" and that 84.3% of the low one is order-free. (iv) The
    # realized clip means, because they are a CORRECTION to a false statement
    # (the earlier text asserted the window mean was pinned at 4% everywhere;
    # it is not, in exactly the two |kappa| = 0.5 cells that set the low end).
    # The surviving co-movement signal is bound too, in both directions: the
    # true marginal must lie outside the permutation range in all six cells
    # (else the cyclicality claim is overstated) and the largest time-order
    # component must match the $5.29B the manuscript quotes as its cap (else it
    # is understated). ROUND 20: all of the above is now computed from
    # fcp["runs"], the 93 raw per-draw records, rather than from the module's
    # own per-cell summaries — see (K0) — and the ten prose figures in the
    # cyclicality-signal paragraph are reconstructed and matched against the
    # .tex rather than searched for as fixed strings. NOTE: this gate must never
    # be relaxed to make a rerun fit. The artifact is the authority; the
    # manuscript is what gets edited.
    fcp = json.loads(FCPERM_RESULTS.read_text())
    fcp_h = fcp["headline"]
    fcp_pk = fcp["per_kappa"]
    fcp_claims = tex.count("\\texttt{floor\\_cyclical\\_permutation}")
    # ---- HARDENING: DERIVE, DON'T READ ---------------------------------
    # Same discipline as gate #58. Every headline aggregate is recomputed here
    # from the per-kappa primitives and required to equal the stored value, and
    # the decomposition is required to CLOSE: for every kappa the three
    # components must sum to the departure and the three shares to 100%, with
    # each component itself re-derived from the leg it is defined by (flat
    # equivalent, permutation mean, realized cell). Nothing in this block can be
    # satisfied by a module writing its own answer into its own summary. Every
    # identity closed at exactly 0.0 and every "==" tie was bit-exact when this
    # was written; FCP_TOL is slack, not a fudge.
    FCP_TOL = 1e-9
    # ---- (K0) RAW-DRAW RECONSTRUCTION (round-20 hardening) --------------
    # Before this block existed, every "derived" quantity in this gate bottomed
    # out in floor_cyclical_permutation.py's OWN per-cell summaries. fcp["runs"]
    # — the 93-entry per-draw log that is the artifact's only primitive record,
    # 7 true + 7 flat_equiv + 7 additive + 72 permutation draws — was never
    # read. A SELF-CONSISTENT miscomputation therefore passed: moving one cell's
    # permutation mean to an eleven-of-twelve-draw value and making every
    # downstream split, share and retained-share agree with it left the gate
    # green, as did corrupting an individual draw's marginal, its kappa_key or
    # its kind. Both holes are closed here. Every per-cell aggregate is
    # recomputed FROM THE DRAWS and the stored summary is required to equal it,
    # and the draw log is required to be well-formed FIRST — counts, cell
    # membership against the committed grid, kind partition, FLOOR_MODE
    # partition, rep partition, no duplicates, no orphans, totals reconciling to
    # 93 — so the reconstruction cannot be gamed by adding, deleting or
    # re-labelling draws instead of by editing them.
    FCP_KEYS = ("-0.5", "-0.25", "-0.1", "+0", "+0.1", "+0.25", "+0.5")
    FCP_PERM_KEYS = tuple(k for k in FCP_KEYS if k != "+0")
    FCP_SINGLE_KINDS = ("true", "flat_equiv", "additive")
    # kind -> the FLOOR_MODE that kind is DEFINED by. The additive leg is the
    # mechanism test itself: a draw labelled "additive" that actually ran under
    # FLOOR_MODE=max (or the reverse) would make the 98.0% rule-swap share mean
    # nothing, so the label and the mode are tied here rather than trusted.
    FCP_KIND_MODE = {"true": "max", "flat_equiv": "max", "perm": "max",
                     "additive": "additive"}
    fcp_runs = fcp["runs"]
    _draws = {(k, kind): [] for k in FCP_KEYS for kind in FCP_KIND_MODE}
    _ids = set()
    fcp_runs_wellformed = True
    for _r in fcp_runs:
        _slot = (_r.get("kappa_key"), _r.get("kind"))
        if _slot not in _draws:      # orphan: unknown cell or unknown kind
            fcp_runs_wellformed = False
            continue
        if _r.get("floor_mode") != FCP_KIND_MODE[_r["kind"]]:
            fcp_runs_wellformed = False   # leg ran under the wrong rule
        _id = (_r["kappa_key"], _r["kind"], _r["rep"])
        if _id in _ids:              # duplicate draw
            fcp_runs_wellformed = False
        _ids.add(_id)
        _draws[_slot].append(_r)
    fcp_runs_wellformed = (
        fcp_runs_wellformed
        and len(fcp_runs) == 93 and len(_ids) == 93
        # the kind partition, exhaustive and exact: 7 + 7 + 7 + 72 == 93
        and all(len(_draws[(k, kind)]) == 1
                for k in FCP_KEYS for kind in FCP_SINGLE_KINDS)
        and all(_draws[(k, kind)][0]["rep"] == -1
                for k in FCP_KEYS for kind in FCP_SINGLE_KINDS)
        and all(len(_draws[(k, "perm")]) == 12 for k in FCP_PERM_KEYS)
        # kappa=0 nests production and has nothing to permute
        and len(_draws[("+0", "perm")]) == 0
        # kappa_key membership against the COMMITTED grid, both directions
        and set(r["kappa_key"] for r in fcp_runs) == set(FCP_KEYS)
        and sorted(round(float(k), 6) for k in FCP_KEYS) \
            == sorted(round(float(g), 6) for g in fcp["kappa_grid"])
        # every permutation cell carries reps 0..11 exactly once
        and all(sorted(r["rep"] for r in _draws[(k, "perm")]) == list(range(12))
                for k in FCP_PERM_KEYS)
        and sum(len(v) for v in _draws.values()) == 93
        and sum(1 for r in fcp_runs if r["kind"] == "perm") == 72
        and sum(1 for r in fcp_runs if r["kind"] in FCP_SINGLE_KINDS) == 21
    )

    def _draw(_k, _kind):
        return _draws[(_k, _kind)][0]

    def _perm_b(_k):
        return [r["marginal_b"] for r in _draws[(_k, "perm")]]

    def _perm_pp(_k):
        return [r["marginal_pp"] for r in _draws[(_k, "perm")]]

    # (K0b) every stored per-cell summary field EQUALS the raw draws it claims
    # to summarize. Bit-exact ("==") on the single-run legs, which are literally
    # copies of one draw; FCP_TOL on the permutation moments, which are sums
    # over twelve doubles and therefore order-sensitive in the last bit.
    fcp_raw_ok = fcp_runs_wellformed
    for _k in FCP_KEYS:
        _c = fcp_pk[_k]
        _t = _draw(_k, "true")
        _f = _draw(_k, "flat_equiv")
        _a = _draw(_k, "additive")
        fcp_raw_ok = fcp_raw_ok and (
            _t["marginal_b"] == _c["committed_marginal_b"]
            and _t["marginal_pp"] == _c["committed_marginal_pp"]
            and _t["floor_path_mean_pct"] == _c["floor_path_mean_pct"]
            and _t["floor_path_sd_pct"] == _c["floor_path_sd_pct"]
            and _f["marginal_b"] == _c["flat_equiv_marginal_b"]
            and _f["marginal_pp"] == _c["flat_equiv_marginal_pp"]
            and abs(_f["floor_path_mean_pct"]
                    - _c["convexity_matched_flat_pct"]) < FCP_TOL
            and _f["floor_path_sd_pct"] < 1e-12     # the flat leg IS flat
            and _a["marginal_b"] == _c["additive_marginal_b"]
            and _a["marginal_pp"] == _c["additive_marginal_pp"]
            # the additive leg walks the SAME realized floor path as the true
            # leg; only the combination rule differs. That is what makes the
            # 98.0% a rule effect rather than a different-path effect.
            and _a["floor_path_mean_pct"] == _t["floor_path_mean_pct"]
            and _a["floor_path_sd_pct"] == _t["floor_path_sd_pct"]
            # the clip flag is a property of the realized path, not a free
            # field: it is set exactly where the non-negativity clip pushed the
            # window mean off the production 4%
            and _c["clip_bound"] == (abs(_t["floor_path_mean_pct"] - 4.0) > FCP_TOL)
        )
        if _k == "+0":
            continue
        _pb, _pp_ = _perm_b(_k), _perm_pp(_k)
        _mean_b = sum(_pb) / len(_pb)
        _var = sum((x - _mean_b) ** 2 for x in _pb) / (len(_pb) - 1)
        fcp_raw_ok = fcp_raw_ok and (
            len(_pb) == _c["n_perm"] == 12
            and abs(_mean_b - _c["perm_marginal_b_mean"]) < FCP_TOL
            and min(_pb) == _c["perm_marginal_b_min"]
            and max(_pb) == _c["perm_marginal_b_max"]
            and abs(_var ** 0.5 - _c["perm_marginal_b_sd"]) < FCP_TOL
            and abs(sum(_pp_) / len(_pp_) - _c["perm_marginal_pp_mean"]) < FCP_TOL
            and min(_pp_) == _c["perm_marginal_pp_min"]
            and max(_pp_) == _c["perm_marginal_pp_max"]
            # every permutation preserves the multiset of monthly floor values,
            # hence its mean and sd, exactly. That is what "order-free" MEANS,
            # and a draw that failed to preserve it is not a permutation.
            and all(abs(r["floor_path_mean_pct"]
                        - _t["floor_path_mean_pct"]) < 1e-12
                    and abs(r["floor_path_sd_pct"]
                            - _t["floor_path_sd_pct"]) < 1e-12
                    for r in _draws[(_k, "perm")])
        )
    # (K0c) the grid aggregates and the three-way split, rebuilt from the draws.
    # Everything downstream in this gate now reads THESE, not the cells.
    _r_true_b = {k: _draw(k, "true")["marginal_b"] for k in FCP_KEYS}
    _r_true_pp = {k: _draw(k, "true")["marginal_pp"] for k in FCP_KEYS}
    _r_add_pp = {k: _draw(k, "additive")["marginal_pp"] for k in FCP_KEYS}
    _r_flat_b = {k: _draw(k, "flat_equiv")["marginal_b"] for k in FCP_KEYS}
    _r_flat_pp = {k: _draw(k, "flat_equiv")["marginal_pp"] for k in FCP_KEYS}
    _r_pmean_b = {k: sum(_perm_b(k)) / 12 for k in FCP_PERM_KEYS}
    _r_base_b = _r_true_b["+0"]
    # the artifact's own decomposition_note, evaluated on raw draws:
    # level = flat_equiv - base; dispersion = mean(perm) - base;
    # residual = dispersion - level; order = departure - dispersion.
    _r_level_b = {k: _r_flat_b[k] - _r_base_b for k in FCP_PERM_KEYS}
    _r_disp_b = {k: _r_pmean_b[k] - _r_base_b for k in FCP_PERM_KEYS}
    _r_resid_b = {k: _r_disp_b[k] - _r_level_b[k] for k in FCP_PERM_KEYS}
    _r_order_b = {k: (_r_true_b[k] - _r_base_b) - _r_disp_b[k]
                  for k in FCP_PERM_KEYS}
    fcp_raw_split_ok = all(
        abs(_r_level_b[k]
            - fcp_pk[k]["three_way_split_b"]["level_equivalence"]) < FCP_TOL
        and abs(_r_resid_b[k]
                - fcp_pk[k]["three_way_split_b"]["residual_dispersion"]) < FCP_TOL
        and abs(_r_order_b[k]
                - fcp_pk[k]["three_way_split_b"]["time_order"]) < FCP_TOL
        and abs(_r_disp_b[k] / (_r_true_b[k] - _r_base_b)
                - fcp_pk[k]["retained_share_of_departure"]) < FCP_TOL
        for k in FCP_PERM_KEYS
    )
    fcp_raw_ok = fcp_raw_ok and fcp_raw_split_ok
    # ---- end raw-draw reconstruction ------------------------------------
    fcp_cells = list(fcp_pk.values())
    fcp_pcells = [c for c in fcp_cells if "n_perm" in c]
    fcp_base_b = fcp_pk["+0"]["committed_marginal_b"]
    fcp_base_pp = fcp_pk["+0"]["committed_marginal_pp"]
    # (K1) per-cell decomposition identities. departure, level, dispersion and
    # order are each re-derived from the legs that DEFINE them, then required to
    # sum back to the departure and to the printed shares.
    fcp_ident_ok = True
    for _c in fcp_cells:
        _dep_b = _c["committed_marginal_b"] - fcp_base_b
        _dep_pp = _c["committed_marginal_pp"] - fcp_base_pp
        fcp_ident_ok = fcp_ident_ok and (
            abs(_dep_b - _c["departure_from_kappa0_b"]) < FCP_TOL
            and abs(_dep_pp - _c["departure_from_kappa0_pp"]) < FCP_TOL
        )
        if "n_perm" not in _c:
            continue
        _s = _c["three_way_split_b"]
        _lvl = _c["flat_equiv_marginal_b"] - fcp_base_b       # level alone
        _disp = _c["perm_marginal_b_mean"] - fcp_base_b       # order-free total
        _res = _disp - _lvl                                    # dispersion beyond level
        _ord = _dep_b - _disp                                  # what order adds
        _mag = abs(_s["level_equivalence"]) + abs(_s["residual_dispersion"]) \
            + abs(_s["time_order"])
        _p = _c["three_way_split_pct_of_magnitude"]
        fcp_ident_ok = fcp_ident_ok and (
            abs(_lvl - _s["level_equivalence"]) < FCP_TOL
            and abs(_res - _s["residual_dispersion"]) < FCP_TOL
            and abs(_ord - _s["time_order"]) < FCP_TOL
            # THE closure condition: the three components ARE the departure
            and abs((_s["level_equivalence"] + _s["residual_dispersion"]
                     + _s["time_order"]) - _c["departure_from_kappa0_b"]) < FCP_TOL
            # each share is its component's share of total magnitude...
            and all(abs(100.0 * abs(_s[_n]) / _mag - _p[_n]) < FCP_TOL for _n in _s)
            # ...and the three shares exhaust 100%
            and abs(sum(_p.values()) - 100.0) < 1e-6
            # the order-free share is exactly the two non-order shares
            and abs((_p["level_equivalence"] + _p["residual_dispersion"])
                    - _c["order_free_share_pct_of_magnitude"]) < 1e-6
            # the retained share is dispersion over departure, not a free field
            and abs(_disp / _dep_b - _c["retained_share_of_departure"]) < FCP_TOL
            # "true outside the permutation range" re-evaluated from the range
            and ((_c["perm_marginal_b_min"] <= _c["committed_marginal_b"]
                  <= _c["perm_marginal_b_max"])
                 == (_c["perm_marginal_pp_min"] <= _c["committed_marginal_pp"]
                     <= _c["perm_marginal_pp_max"])
                 == _c["true_within_perm_range"])
        )
    # (K2) the headline block, every field recomputed from the RAW DRAWS of
    # (K0c) — not from the per-kappa cells, which are themselves now only
    # checked against the draws rather than trusted as sources.
    _cmin = min(_r_true_pp.values())
    _cmax = max(_r_true_pp.values())
    _cspan = _cmax - _cmin
    _pmin = min(min(_perm_pp(k)) for k in FCP_PERM_KEYS)
    _pmax = max(max(_perm_pp(k)) for k in FCP_PERM_KEYS)
    _amin = min(_r_add_pp.values())
    _amax = max(_r_add_pp.values())
    _fmin = min(_r_flat_pp.values())
    _fmax = max(_r_flat_pp.values())
    _g = fcp["grid_ranges_pp"]
    _n_outside = sum(1 for k in FCP_PERM_KEYS
                     if not (min(_perm_b(k)) <= _r_true_b[k] <= max(_perm_b(k))))
    _max_order = max(abs(v) for v in _r_order_b.values())
    fcp_headline_derived_ok = (
        abs(_cspan - fcp_h["committed_range_span_pp"]) < FCP_TOL
        and abs(_cspan - _g["max_mode_true"]["span"]) < FCP_TOL
        and abs(_cmin - _g["max_mode_true"]["min"]) < FCP_TOL
        and abs(_cmax - _g["max_mode_true"]["max"]) < FCP_TOL
        and _g["max_mode_true"] == _g["committed_reported"]
        and abs((_pmax - _pmin) - fcp_h["permuted_range_span_pp"]) < FCP_TOL
        and abs(_pmin - fcp["pooled_permuted_range_pp"]["min"]) < FCP_TOL
        and abs(_pmax - fcp["pooled_permuted_range_pp"]["max"]) < FCP_TOL
        and sum(c["n_perm"] for c in fcp_pcells) \
            == fcp["pooled_permuted_range_pp"]["n"] == 72
        and all(c["n_perm"] == fcp["n_perm_per_kappa"] == 12 for c in fcp_pcells)
        # the two headline SHARES, recomputed as ratios of the derived spans
        and abs((_pmax - _pmin) / _cspan
                - fcp_h["share_of_committed_range_span_surviving_time_scramble"]) < FCP_TOL
        and abs((_amax - _amin) - fcp_h["additive_range_span_pp"]) < FCP_TOL
        and abs((_amax - _amin) / _cspan
                - fcp_h["share_of_committed_range_span_surviving_additive_mode"]) < FCP_TOL
        and abs(100.0 * (1.0 - (_amax - _amin) / _cspan)
                - fcp_h["range_span_eliminated_by_switching_max_to_additive_pct"]) < FCP_TOL
        # the two shares are complements: surviving + eliminated == 100%
        and abs(100.0 * fcp_h["share_of_committed_range_span_surviving_additive_mode"]
                + fcp_h["range_span_eliminated_by_switching_max_to_additive_pct"]
                - 100.0) < 1e-6
        and abs(_amin - _g["additive_mode"]["min"]) < FCP_TOL
        and abs(_amax - _g["additive_mode"]["max"]) < FCP_TOL
        and abs((_amax - _amin) - _g["additive_mode"]["span"]) < FCP_TOL
        and abs(_fmin - _g["flat_equiv_under_max"]["min"]) < FCP_TOL
        and abs(_fmax - _g["flat_equiv_under_max"]["max"]) < FCP_TOL
        # the three COUNTS the manuscript leans on, all recomputed
        and _n_outside == fcp_h["n_kappa_cells_with_true_outside_permutation_range"] == 6
        and len(fcp_pcells) == fcp_h["n_kappa_cells_with_permutations"] == 6
        and abs(_max_order - fcp_h["max_abs_time_order_component_b"]) < FCP_TOL
        and sum(1 for c in fcp_cells if c["clip_bound"]) \
            == fcp_h["n_clip_bound_cells"] == 2
        and len(fcp_cells) == len(fcp["kappa_grid"]) == 7
    )
    # (K3) CROSS-ARTIFACT TIES. The committed cells, the additive cross-gate and
    # the kappa=0 baseline each come from a DIFFERENT module's committed file,
    # so these cannot be satisfied by floor_cyclical_permutation.py alone.
    _fc_cells = {round(c["kappa"], 6): c
                 for c in json.loads(FLOORCYC_RESULTS.read_text())["cells"]}
    _ff_add4 = [r for r in json.loads(FLOORFORM_RESULTS.read_text())["rows"]
                if r["form"] == "additive"
                and abs(r["floor_annual_cpr_pct"] - 4.0) < 1e-9][0]
    _nl2 = json.loads(NULL_RESULTS.read_text())
    fcp_cross_ok = (
        # all seven committed cells, bit-exact against floor_cyclical_results
        len(_fc_cells) == 7
        and all(round(c["kappa"], 6) in _fc_cells
                and c["committed_marginal_b"]
                == _fc_cells[round(c["kappa"], 6)]["lockin_marginal_b"]
                and c["committed_marginal_pp"]
                == _fc_cells[round(c["kappa"], 6)]["lockin_marginal_share_pp"]
                and c["reproduced_marginal_b"] == c["committed_marginal_b"]
                and c["reproduced_marginal_pp"] == c["committed_marginal_pp"]
                and c["bit_exact_vs_committed"] is True
                # the clip flag too — it is the correction this gate certifies
                and c["clip_bound"] == _fc_cells[round(c["kappa"], 6)]["clip_bound"]
                for c in fcp_cells)
        # the additive kappa=0 cell IS floor_form's additive@4% row
        and fcp_pk["+0"]["additive_marginal_b"] == _ff_add4["lockin_marginal_b"]
        and fcp_pk["+0"]["additive_marginal_pp"] == _ff_add4["lockin_marginal_share_pp"]
        and fcp["parity_gate_additive_cross_check"]["got_b"] \
            == _ff_add4["lockin_marginal_b"]
        # the kappa=0 baseline the whole decomposition is measured FROM is the
        # production no-lock-in null run
        and fcp_base_b == _nl2["lockin_marginal_b"]
        and fcp_base_pp == _nl2["lockin_marginal_share_pp"]
        # a zero-dispersion cell must have zero departure and a flat equivalent
        # identical to the baseline — the decomposition's own origin check
        and fcp_pk["+0"]["floor_path_sd_pct"] == 0.0
        and fcp_pk["+0"]["departure_from_kappa0_b"] == 0.0
        and fcp_pk["+0"]["flat_equiv_marginal_b"] == fcp_base_b
    )
    fcp_derived_ok = (fcp_raw_ok and fcp_ident_ok and fcp_headline_derived_ok
                      and fcp_cross_ok)
    # ---- end hardening --------------------------------------------------
    # (i) parity, both gates
    fcp_parity_ok = (
        fcp["parity_gate_bitexact_all_pass"]
        and len(fcp["parity_gate_bitexact_cells"]) == 7
        and all(v["pass_bitwise"] and v["abs_diff_b"] == 0.0
                and v["abs_diff_pp"] == 0.0
                for v in fcp["parity_gate_bitexact_cells"].values())
        and fcp["parity_gate_additive_cross_check"]["pass"]
        and fcp["parity_gate_additive_cross_check"]["want_source"].startswith(
            "floor_form_results.json")
        # TOLERANCE NOTE (round 20). An earlier report claimed this 5e-6 slack
        # had been replaced by a bit-exact check. It had not been. It is now:
        # the tie to the artifact itself is already asserted bit-exact in
        # fcp_cross_ok (got_b == floor_form's additive@4% row), and what is
        # checked HERE is the six-decimal figure the manuscript prints, so the
        # honest form is exact equality AT THAT PRECISION rather than a
        # tolerance band around it. round(86.02249228630046, 6) == 86.022492.
        and round(fcp["parity_gate_additive_cross_check"]["got_b"], 6) \
            == 86.022492
    )
    # (ii) the two headline shares, at the manuscript's printed precision.
    # Compared against the values DERIVED above from the per-kappa cells, so the
    # .tex, the headline block and the raw grid must all agree.
    fcp_share_ok = (
        abs((_pmax - _pmin) / _cspan - 0.8496) < 0.00005
        and abs(100.0 * (1.0 - (_amax - _amin) / _cspan) - 98.03) < 0.005
        and fcp["n_perm_per_kappa"] == 12
        and sum(c["n_perm"] for c in fcp_pcells) == 72
        and abs(_pmin - 7.1987) < 0.00005
        and abs(_pmax - 9.1232) < 0.00005
        and abs(_amin - 11.2208) < 0.00005
        and abs(_amax - 11.2654) < 0.00005
        and abs((_amax - _amin) - 0.0446) < 0.00005
        and abs(_cmin - 7.0947) < 0.00005
        and abs(_cmax - 9.3598) < 0.00005
    )
    # (iii) the endpoint decomposition
    lo = fcp_pk["+0.5"]
    lo_split = lo["three_way_split_pct_of_magnitude"]
    hi = fcp_pk["-0.1"]
    fcp_split_ok = (
        abs(lo["departure_from_kappa0_b"] + 16.089) < 0.0005
        and abs(lo["three_way_split_b"]["level_equivalence"] + 2.1413) < 0.00005
        and abs(lo["three_way_split_b"]["residual_dispersion"] + 11.4211) < 0.00005
        and abs(lo["three_way_split_b"]["time_order"] + 2.5263) < 0.00005
        and abs(lo_split["level_equivalence"] - 13.3) < 0.05
        and abs(lo_split["residual_dispersion"] - 71.0) < 0.05
        and abs(lo_split["time_order"] - 15.7) < 0.05
        and abs(lo["order_free_share_pct_of_magnitude"] - 84.3) < 0.05
        and abs(hi["departure_from_kappa0_b"] - 1.234) < 0.0005
        and abs(hi["departure_from_kappa0_pp"] - 0.161) < 0.0005
    )
    # (iv) the clip correction: pinning is broken in exactly the two |k|=0.5 cells
    fcp_clip_ok = (
        fcp_h["n_clip_bound_cells"] == 2
        and fcp_pk["-0.5"]["clip_bound"] and fcp_pk["+0.5"]["clip_bound"]
        and not any(fcp_pk[k]["clip_bound"]
                    for k in ("-0.25", "-0.1", "+0", "+0.1", "+0.25"))
        and abs(fcp_pk["-0.5"]["floor_path_mean_pct"] - 4.0005) < 0.00005
        and abs(fcp_pk["+0.5"]["floor_path_mean_pct"] - 4.0828) < 0.00005
        and abs(lo["convexity_matched_flat_pct"] - 4.0977) < 0.00005
    )
    # the surviving co-movement signal, bounded from both sides
    # both counts and the cap are the DERIVED values, not the stored headline
    fcp_signal_ok = (
        len(fcp_pcells) == 6
        and _n_outside == 6
        and abs(_max_order - 5.289) < 0.0005
        and all(fcp_pk[k]["three_way_split_b"]["time_order"] > 0
                for k in ("-0.5", "-0.25", "-0.1"))
        and all(fcp_pk[k]["three_way_split_b"]["time_order"] < 0
                for k in ("+0.1", "+0.25", "+0.5"))
        and fcp["verdict"].startswith("RANGE IS PREDOMINANTLY ORDER-FREE")
        # neighbour audit: the v17 headline must be recorded as unexposed
        and "NOT exposed" in fcp["neighbour_exposure_audit"]["oos_identification"]
    )
    # (A3/A4) The prose numbers that were previously checked for PRESENCE only,
    # or not checked at all, are now RECONSTRUCTED from the raw draws and the
    # reconstruction is what gets searched for in the .tex. A rerun that moved
    # any of these ten figures makes the derived string stop matching, so the
    # manuscript can no longer print a stale number that happens to still be
    # spelled the same way. The formatting mirrors the manuscript's own
    # notation exactly, including its sign and dollar conventions.
    def _bfmt(v):
        """Manuscript notation for a signed billion figure: +\\$5.29 / -\\$1.42."""
        return f"{'+' if v >= 0 else '-'}\\${abs(v):.2f}"

    # six time-order components (A3), previously one presence-only string
    _order_str = (
        f"${_bfmt(_r_order_b['-0.5'])}$, ${_bfmt(_r_order_b['-0.25'])}$, and "
        f"${_bfmt(_r_order_b['-0.1'])}$ billion at $\\kappa = -0.5$, $-0.25$, "
        f"$-0.1$, and ${_bfmt(_r_order_b['+0.1'])}$, "
        f"${_bfmt(_r_order_b['+0.25'])}$, and ${_bfmt(_r_order_b['+0.5'])}$ "
        f"billion at $+0.1$, $+0.25$, $+0.5$"
    )
    # the three permuted sign-gaps and the true |kappa|=0.5 spread (A4): four
    # numbers written into the manuscript with NO gate coverage of any kind
    _r_signgap_b = {a: abs(_r_pmean_b["-" + a] - _r_pmean_b["+" + a])
                    for a in ("0.1", "0.25", "0.5")}
    _r_true_spread_b = _r_true_b["-0.5"] - _r_true_b["+0.5"]
    _signgap_str = (
        f"by only $\\${_r_signgap_b['0.1']:.2f}$, $\\${_r_signgap_b['0.25']:.2f}$, "
        f"and $\\${_r_signgap_b['0.5']:.2f}$ billion at $|\\kappa| = 0.1$, "
        f"$0.25$, and $0.5$, against a true spread of "
        f"$\\${_r_true_spread_b:.2f}$ billion at $|\\kappa| = 0.5$"
    )
    _asym_str = (
        f"(${_bfmt(_r_true_b['-0.5'])}$ billion at $\\kappa = -0.5$ against "
        f"${_bfmt(_r_true_b['+0.5'])}$ billion at $+0.5$)"
    )
    # the manuscript's monotonicity claim, evaluated rather than assumed
    fcp_order_monotone_ok = (
        abs(_r_order_b["-0.5"]) > abs(_r_order_b["-0.25"]) > abs(_r_order_b["-0.1"])
        and abs(_r_order_b["+0.5"]) > abs(_r_order_b["+0.25"]) > abs(_r_order_b["+0.1"])
    )
    fcp_lits = {
        "scramble_share": "85.0\\%" in tex,
        "additive_share": "98.0\\%" in tex,
        "perm_span": "$+7.20$ to $+9.12$" in tex,
        "committed_span": "$+7.09$ to $+9.36$" in tex,
        "additive_span": "$+11.22$ to $+11.27$" in tex
                         and "a span of $0.045$ points" in tex,
        "low_departure": "$-\\$16.09$ billion" in tex,
        "low_split": ("$-\\$2.14$ billion (13.3\\%)" in tex
                      and "$-\\$11.42$ billion (71.0\\%)" in tex
                      and "$-\\$2.53$ billion (15.7\\%)" in tex
                      and "84.3\\%" in tex),
        "high_endpoint": "$+\\$1.23$ billion" in tex and "$+0.16$ points" in tex,
        "perm_bracket_count": "0 of 72 draws" in tex,
        # DERIVED, not literal: all six components rebuilt from fcp["runs"]
        "order_components": _order_str in tex,
        # DERIVED: the four tex figures that carried no coverage before round 20
        "permuted_sign_gaps_and_true_spread": _signgap_str in tex,
        "asymmetry": _asym_str in tex,
        "signal_cap": f"at most \\${_max_order:.2f} billion" in tex,
        "clip_means": "4.0005\\%" in tex and "4.0828\\%" in tex,
        "convexity_flat": "4.0977\\%" in tex,
        # the uncertainty table must not relabel this as a cyclicality bracket
        "tab_relabelled": "within-run floor dispersion $+7.1$ to $+9.4$" in tex,
        "tab_disclaimer": "it does not bracket floor cyclicality" in tex,
        # the retired reading must not reappear anywhere
        "no_stale_cyclicality_bracket":
            "floor cyclicality in either direction of co-movement is bounded"
            not in tex,
    }
    fcp_ok = (fcp_parity_ok and fcp_share_ok and fcp_split_ok and fcp_clip_ok
              and fcp_signal_ok and fcp_derived_ok and fcp_order_monotone_ok
              and fcp_claims >= 1 and all(fcp_lits.values()))
    failures += 0 if fcp_ok else 1
    print(
        f"[{'PASS' if fcp_ok else 'FAIL'}] cross-check floor cyclicality "
        f"attribution: derived-not-read={fcp_derived_ok} "
        f"(raw {len(fcp_runs)}-draw reconstruction={fcp_raw_ok}, "
        f"runs well-formed={fcp_runs_wellformed}, per-cell closure="
        f"{fcp_ident_ok}, headline-rederived="
        f"{fcp_headline_derived_ok}, cross-artifact={fcp_cross_ok}), "
        f"parity bitexact(7)+additive-cross={fcp_parity_ok} "
        f"(additive kappa0 "
        f"{fcp['parity_gate_additive_cross_check']['got_b']:.6f}B), "
        f"scramble share="
        f"{fcp_h['share_of_committed_range_span_surviving_time_scramble']:.4f} "
        f"(want 0.8496), additive elimination="
        f"{fcp_h['range_span_eliminated_by_switching_max_to_additive_pct']:.2f}% "
        f"(want 98.03), low-endpoint split="
        f"{lo_split['level_equivalence']:.1f}/"
        f"{lo_split['residual_dispersion']:.1f}/{lo_split['time_order']:.1f}, "
        f"high endpoint={hi['departure_from_kappa0_pp']:+.3f}pp, "
        f"clip means={fcp_pk['-0.5']['floor_path_mean_pct']:.4f}/"
        f"{fcp_pk['+0.5']['floor_path_mean_pct']:.4f}%, "
        f"true-outside-perm="
        f"{fcp_h['n_kappa_cells_with_true_outside_permutation_range']}/"
        f"{fcp_h['n_kappa_cells_with_permutations']}, "
        f"max|order|=${_max_order:.3f}B (derived), sign-gaps $"
        f"{_r_signgap_b['0.1']:.2f}/{_r_signgap_b['0.25']:.2f}/"
        f"{_r_signgap_b['0.5']:.2f}B vs true spread $"
        f"{_r_true_spread_b:.2f}B, "
        f"tex run-citation count={fcp_claims} (want >=1), "
        f"literals={ {k: v for k, v in fcp_lits.items() if not v} or 'all present'}"
    )

    # Panel revision (gate #60): the group-ablation verdict's DISCRIMINATING
    # POWER. subgroup_marginals.py returns "broad_based" on all three grids and
    # Section~\ref{sec:identification} used to read that label as the finding.
    # subgroup_marginals_placebo.py shows the label does not discriminate — a
    # RANDOM three-way partition earns it too — and that the informative
    # quantity is the DIRECTION of the band comparison, which inverts the old
    # reading: the economic groupings disperse MORE than chance, not less. This
    # gate exists because that correction is a comparison of two dispersions,
    # and a comparison is exactly what drifts silently: either side could move
    # on a rerun and leave the prose arithmetically wrong while each individual
    # band still looked sane. Four things are bound. (i) All three parity gates
    # bit-exact, because a placebo is worthless unless it is the SAME
    # microsimulation as the committed run — G1/G2 against the imported central
    # and null anchors, and G3 against the committed FICO cells read out of
    # subgroup_marginals_results.json, which is the only check that certifies
    # the placebo loop is the committed loop and not a re-implementation.
    # (ii) The 12/12 count, since "a partition with no economic content earns
    # the label" is false the moment any draw fails. (iii) Both bands and the
    # ordering between them, DERIVED from the per-partition records rather than
    # read from the module's own summary, so a self-consistent miscomputation
    # cannot pass. (iv) The committed side re-read from the committed artifact,
    # not from the placebo module's copy of it, so the two sides of the
    # comparison cannot both be written by the same run. NOTE: this gate must
    # never be relaxed to make a rerun fit. The artifact is the authority; the
    # manuscript is what gets edited.
    spb = json.loads(SUBPLACEBO_RESULTS.read_text())
    spb_sum = spb["summary"]
    spb_parts = spb["placebo_partitions"]
    spb_anch = spb["committed_anchors"]
    spb_claims = tex.count("\\texttt{subgroup\\_marginals\\_placebo}")
    SPB_TOL = 1e-12
    # The committed verdict band and additivity tolerance, imported from
    # subgroup_marginals.py as the placebo module itself imports them. The
    # verdict label is re-derived from these below, never read.
    SPB_BAND_LO, SPB_BAND_HI = 0.5, 2.0
    SPB_ADDITIVITY_TOL_FRAC = 0.10
    _sg = json.loads(SUBGROUP_RESULTS.read_text())
    _bench = float(json.loads(EXTRISK_RESULTS.read_text())["empirical_trapped_b"])
    _T = spb_anch["total_marginal_b"]

    # (i) parity, all three exact-equality gates. The stored anchor LEVELS are
    # compared to the committed anchors, not merely reported as differing by
    # zero: a recorded diff of 0.0 is a claim about a subtraction nobody
    # re-performed, so it survives any move of the level it was subtracted from.
    spb_g = spb["gates"]
    spb_parity_ok = (
        spb_g["G1_central_parity"]["trapped_b"] == spb_anch["central_trapped_b"]
        and spb_g["G2_null_parity"]["trapped_b"] == spb_anch["null_trapped_b"]
        and spb_g["G1_central_parity"]["diff_b"] == 0.0
        and spb_g["G2_null_parity"]["diff_b"] == 0.0
        and spb_g["G1_central_parity"]["pass"] and spb_g["G2_null_parity"]["pass"]
        and spb_g["G3_committed_fico_cell_reproduction"]["pass"]
        and len(spb_g["G3_committed_fico_cell_reproduction"]["cells"]) == 3
        and all(c["bit_exact"] and c["abs_diff_b"] == 0.0
                for c in spb_g["G3_committed_fico_cell_reproduction"]["cells"])
    )
    # The committed anchors themselves cross-read from the COMMITTED artifact,
    # and their own arithmetic re-closed against the third-module benchmark.
    # The anchor LEVELS must tie to an independently-produced third artifact, not
    # only to each other: binding the difference alone lets both sides move
    # together (+$20B to each preserves the marginal and passed before this).
    _nlr = json.loads(NULL_RESULTS.read_text())
    spb_anchors_ok = (
        spb_anch == _sg["committed_anchors"]
        and spb_anch["central_trapped_b"] == _nlr["central_trapped_b"]
        and spb_anch["null_trapped_b"] == _nlr["null_trapped_b"]
        and abs(_T - (spb_anch["central_trapped_b"] - spb_anch["null_trapped_b"]))
        <= SPB_TOL
        and abs(spb_anch["total_marginal_pp"] - _T / _bench * 100) <= 1e-9
        and float(spb["benchmark_b"]) == _bench
        and float(_sg["benchmark_b"]) == _bench
    )
    # G3's committed side re-read from the COMMITTED artifact, not the placebo's
    # copy -- AND the committed grid's own cell arithmetic re-derived, so the
    # two artifacts cannot be moved together into a shared falsehood.
    _sg_fico = {c["cell"]: c["marginal_b"] for c in _sg["grids"]["fico_bucket"]["cells"]}
    spb_cross_ok = (
        all(c["committed_marginal_b"] == _sg_fico[c["cell"]]
            and c["got_marginal_b"] == _sg_fico[c["cell"]]
            for c in spb_g["G3_committed_fico_cell_reproduction"]["cells"])
        and all(
            abs(sum(c["marginal_b"] for c in g["cells"]) - g["sum_cells_b"]) <= SPB_TOL
            and all(
                abs(c["share_of_sum_pct"]
                    - c["marginal_b"] / g["sum_cells_b"] * 100) <= SPB_TOL
                and abs(c["intensity"]
                        - c["share_of_sum_pct"] / c["balance_share_pct"]) <= SPB_TOL
                and abs(c["marginal_pp"] - c["marginal_b"] / _bench * 100) <= SPB_TOL
                for c in g["cells"])
            and abs(g["intensity_min"] - min(c["intensity"] for c in g["cells"]))
            <= SPB_TOL
            and abs(g["intensity_max"] - max(c["intensity"] for c in g["cells"]))
            <= SPB_TOL
            for g in _sg["grids"].values())
    )

    # (ii)+(iii) DERIVE, DON'T READ. Every quantity below is rebuilt from
    # placebo_partitions[].cells[].marginal_b and balance_share_pct -- the only
    # primitives in the file -- and the stored summary is required to equal the
    # rebuild. This is what closes the self-consistent-miscomputation class: a
    # summary and its downstream fields can be moved together to agree with each
    # other, but they cannot be made to agree with the per-cell dollars unless
    # the arithmetic actually holds.
    spb_n = len(spb_parts)
    _widths = [p["intensity_max"] - p["intensity_min"] for p in spb_parts]
    _n_broad = sum(1 for p in spb_parts if p["verdict"] == "broad_based")

    def _spb_part_ok(p):
        cells = p["cells"]
        sum_b = sum(c["marginal_b"] for c in cells)
        if abs(sum_b - p["sum_cells_b"]) > SPB_TOL or sum_b == 0:
            return False
        # every per-cell derived column rebuilt from the two primitives
        for c in cells:
            if abs(c["share_of_sum_pct"] - c["marginal_b"] / sum_b * 100) > SPB_TOL:
                return False
            if abs(c["intensity"]
                   - c["share_of_sum_pct"] / c["balance_share_pct"]) > SPB_TOL:
                return False
            if abs(c["marginal_pp"] - c["marginal_b"] / _bench * 100) > SPB_TOL:
                return False
        imin = min(c["intensity"] for c in cells)
        imax = max(c["intensity"] for c in cells)
        resid = _T - sum_b
        # the verdict label and BOTH of its inputs re-derived from the cells
        sign_ok = all(c["marginal_b"] > 0 for c in cells)
        band_ok = all(SPB_BAND_LO <= c["intensity"] <= SPB_BAND_HI for c in cells)
        add_ok = abs(resid) <= SPB_ADDITIVITY_TOL_FRAC * _T
        return (
            abs(p["intensity_min"] - imin) <= SPB_TOL
            and abs(p["intensity_max"] - imax) <= SPB_TOL
            and abs(p["intensity_band_width"] - (imax - imin)) <= SPB_TOL
            and abs(p["residual_b"] - resid) <= SPB_TOL
            and abs(p["residual_frac_of_total"] - resid / _T) <= SPB_TOL
            and p["sign_homogeneous"] is sign_ok
            and p["intensity_band_ok"] is band_ok
            and p["additivity_verdict"] == ("shares_readable" if add_ok
                                            else "approximate_only")
            and p["verdict"] == ("broad_based" if (sign_ok and band_ok)
                                 else "materially_heterogeneous")
            and len(cells) == 3
            and sum(c["n_loans"] for c in cells) == 75_000
            and all(c["n_loans"] > 0 for c in cells)
        )

    _absfr = [abs(p["residual_frac_of_total"]) for p in spb_parts]
    spb_derived_ok = (
        spb_n == spb["n_placebo"] == 12
        and spb["n_cells"] == 3
        and sorted(p["partition_index"] for p in spb_parts) == list(range(12))
        and all(_spb_part_ok(p) for p in spb_parts)
        and _n_broad == spb_sum["n_broad_based"] == 12
        and spb_sum["n_partitions"] == spb_n
        and abs(spb_sum["placebo_band_width_max"] - max(_widths)) <= SPB_TOL
        and abs(spb_sum["placebo_band_width_min"] - min(_widths)) <= SPB_TOL
        and abs(spb_sum["placebo_band_width_median"]
                - statistics.median(_widths)) <= SPB_TOL
        and abs(spb_sum["placebo_abs_residual_frac_min"] - min(_absfr)) <= SPB_TOL
        and abs(spb_sum["placebo_abs_residual_frac_max"] - max(_absfr)) <= SPB_TOL
        and abs(spb_sum["placebo_intensity_min"]
                - min(p["intensity_min"] for p in spb_parts)) <= SPB_TOL
        and abs(spb_sum["placebo_intensity_max"]
                - max(p["intensity_max"] for p in spb_parts)) <= SPB_TOL
        and abs(spb_sum["committed_band_width"]
                - (spb_sum["committed_intensity_max"]
                   - spb_sum["committed_intensity_min"])) <= SPB_TOL
    )
    # (iv) the committed band re-derived from the committed artifact itself
    _c_imin = min(g["intensity_min"] for g in _sg["grids"].values())
    _c_imax = max(g["intensity_max"] for g in _sg["grids"].values())
    _c_absfr = [abs(g["residual_b"]) / _T for g in _sg["grids"].values()]
    spb_committed_ok = (
        abs(spb_sum["committed_intensity_min"] - _c_imin) <= SPB_TOL
        and abs(spb_sum["committed_intensity_max"] - _c_imax) <= SPB_TOL
        and abs(spb_sum["committed_abs_residual_frac_min"] - min(_c_absfr)) <= 1e-9
        and abs(spb_sum["committed_abs_residual_frac_max"] - max(_c_absfr)) <= 1e-9
    )
    # the INVERSION itself: committed must be strictly wider than every draw
    _spb_ratio = spb_sum["committed_band_width"] / max(_widths)
    spb_inversion_ok = (
        spb["verdict_discrimination"] == "verdict_does_not_discriminate"
        and spb["verdict_direction"] == "committed_disperses_more_than_chance"
        and spb_sum["committed_band_width"] > max(_widths)
    )
    # Manuscript literals DERIVED from the artifact at the precision the prose
    # prints, then required to be present. A hard-coded string can only assert
    # that the prose has not changed; a derived string additionally fails when
    # the ARTIFACT moves, which is the drift that leaves the .tex stale.
    spb_lits = {
        "placebo_band": f"{spb_sum['placebo_intensity_min']:.3f}--"
                        f"{spb_sum['placebo_intensity_max']:.3f}" in tex,
        "placebo_widest": f"spans {max(_widths):.3f}" in tex,
        "committed_span": f"span {spb_sum['committed_band_width']:.3f}" in tex,
        "committed_band": f"lies in {spb_sum['committed_intensity_min']:.2f}--"
                          f"{spb_sum['committed_intensity_max']:.2f}" in tex,
        "dispersion_ratio": _spb_ratio >= 30.0 and "more than thirty times wider" in tex,
        "all_twelve": spb_n == 12 and "in all twelve" in tex,
        "n_loans": f"{75_000:,} loans" in tex,
        "residual": f"residuals of {max(_absfr) * 100:.2f} percent" in tex
                    and f"{min(_absfr) * 100:.2f}" == f"{max(_absfr) * 100:.2f}",
        "no_stale_label_reading": "does not, on its own, discriminate" in tex,
    }
    spb_ok = (spb_parity_ok and spb_anchors_ok and spb_cross_ok and spb_derived_ok
              and spb_committed_ok and spb_inversion_ok
              and spb_claims >= 1 and all(spb_lits.values()))
    failures += 0 if spb_ok else 1
    print(
        f"[{'PASS' if spb_ok else 'FAIL'}] cross-check subgroup verdict "
        f"discriminating power: parity bitexact(G1/G2/G3)={spb_parity_ok} "
        f"(G3 cross-read from committed artifact={spb_cross_ok}), "
        f"derived-not-read={spb_derived_ok}, committed-band-rederived="
        f"{spb_committed_ok}, broad_based {_n_broad}/{spb_n} (want 12/12), "
        f"placebo band {spb_sum['placebo_intensity_min']:.4f}-"
        f"{spb_sum['placebo_intensity_max']:.4f} (widest draw "
        f"{max(_widths):.4f}) vs committed "
        f"{spb_sum['committed_intensity_min']:.4f}-"
        f"{spb_sum['committed_intensity_max']:.4f} "
        f"(width {spb_sum['committed_band_width']:.4f}, "
        f"{_spb_ratio:.1f}x), anchors-cross-read={spb_anchors_ok}, "
        f"inversion={spb_inversion_ok}, tex run-citation count={spb_claims} "
        f"(want >=1), literals="
        f"{ {k: v for k, v in spb_lits.items() if not v} or 'all present'}"
    )

    # Panel revision (gate #61): the symmetric companion test's MISSING NULL.
    # synthetic_companion.py reports a 106.0% synthetic recovery and
    # Section~\ref{sec:robustness-synthesis} used to read that LEVEL as
    # substantially strengthening the paradigm claim. Every other recovery level
    # in this paper is explicitly demoted as floor-dominated; this was the one
    # place a level was still doing evidential work, and the reason was that
    # nobody had run its beta1 = 0 leg. synthetic_companion_null.py runs it. The
    # claim is now a DIFFERENTIAL, which is a difference of two run outputs and
    # therefore drifts silently if either leg moves. Three things are bound.
    # (i) The parity gate, bit-exact against the COMMITTED companion artifact
    # re-read here rather than trusted from the null module's own echo of it —
    # the null is about a different simulation unless the central leg is
    # literally the committed cell. (ii) That the null leg really is beta1 = 0
    # and differs in nothing else: both the recorded beta1 and the shock
    # percentage are checked, so a leg that merely used a small beta1 cannot
    # pass. (iii) The differential itself, RE-DERIVED from the two legs rather
    # than read from the module's summary, together with the pre-committed
    # verdict and the real-book 18.3-point precedent the manuscript leans on.
    scn = json.loads(SYNTHNULL_RESULTS.read_text())
    scn_c, scn_n = scn["central"], scn["null_beta1_0"]
    scn_d = scn["differential"]
    scn_claims = tex.count("\\texttt{synthetic\\_companion\\_null}")
    SCN_TOL = 1e-9
    _sc = json.loads(SYNTHCOMP_RESULTS.read_text())["two_by_two"]["hazard_synthetic_pathB"]
    _scn_bench = float(json.loads(EXTRISK_RESULTS.read_text())["empirical_trapped_b"])
    scn_pg = scn["parity_gate"]
    scn_parity_ok = (
        scn_pg["pass"] and scn_pg["bit_exact"]
        and scn_pg["abs_diff_trapped_b"] == 0.0
        and scn_pg["abs_diff_share_pct"] == 0.0
        # cross-read: the committed side comes from the COMMITTED artifact
        and scn_c["trapped_b"] == float(_sc["trapped_b"])
        and scn_c["share_pct"] == float(_sc["share_pct"])
        and scn_c["cpr_r_lag0"] == float(_sc["cpr_r_lag0"])
        # BOTH recorded sides of the parity gate bound to real quantities. The
        # committed side was previously unbound entirely: the gate trusted a
        # recorded zero difference between two numbers it never looked at.
        and scn_pg["committed_trapped_b"] == float(_sc["trapped_b"])
        and scn_pg["committed_share_pct"] == float(_sc["share_pct"])
        and scn_pg["central_trapped_b"] == scn_c["trapped_b"]
        and scn_pg["central_share_pct"] == scn_c["share_pct"]
    )
    scn_null_is_null_ok = (
        scn_n["beta1"] == 0.0 and scn_n["p_q_shock_pct"] == 0.0
        and scn_c["beta1"] != 0.0 and scn_c["p_q_shock_pct"] == 6.5
    )
    # DERIVE, DON'T READ. The load-bearing addition is the level/share identity
    # on EACH leg against the third-module benchmark. Without it, a leg's
    # share_pct can be moved and every downstream field re-closed around it --
    # which silently rewrites the differential while the artifact stays
    # internally consistent and the manuscript keeps printing the old number.
    scn_levels_ok = (
        abs(scn_c["share_pct"] - scn_c["trapped_b"] / _scn_bench * 100) <= SCN_TOL
        and abs(scn_n["share_pct"] - scn_n["trapped_b"] / _scn_bench * 100) <= SCN_TOL
        # and the two legs must be scored on one and the same benchmark
        and abs(scn_c["share_pct"] / scn_c["trapped_b"]
                - scn_n["share_pct"] / scn_n["trapped_b"]) <= 1e-12
    )
    _rb = scn["real_book_reference"]
    _rb_src = next(r for r in json.loads(FLOORSWEEP_RESULTS.read_text())["rows"]
                   if r["floor_annual_cpr_pct"] == 4.0)
    _rb_bench = float(json.loads(EXTRISK_RESULTS.read_text())["empirical_trapped_b"])
    _rb_oos = next(t for t in json.loads(
        OOSIDENT_RESULTS.read_text())["instrument1_marginal_table"]
        if abs(t["floor_annual_cpr_pct"] - _rb["off_window_floor_pct"]) < 1e-6)
    scn_derived_ok = (
        abs(scn_d["marginal_pp"] - (scn_c["share_pct"] - scn_n["share_pct"])) <= SCN_TOL
        and abs(scn_d["marginal_b"] - (scn_c["trapped_b"] - scn_n["trapped_b"])) <= SCN_TOL
        and abs(scn_d["null_share_of_central_pct"]
                - scn_n["share_pct"] / scn_c["share_pct"] * 100) <= SCN_TOL
        and scn["verdict"] == "level_reading_unsupported"
        and scn_d["marginal_pp"] <= scn["material_differential_threshold_pp"]
        # the threshold itself is pre-committed and may not be relaxed to fit
        and scn["material_differential_threshold_pp"] == 25.0
        # The precedent the manuscript quotes must be the one stored, its own
        # arithmetic must close, and — the defect this replaces — BOTH LEGS MUST
        # BE ON ONE ACCOUNTING BASIS. The stored block used to hardcode a
        # standalone central (107.0) against a shared null (88.7) for a spurious
        # 18.3pp gap. Both legs are now cross-read from the committed floor
        # sweep's 4.0% row, so a future edit cannot reinstate a cross-basis
        # difference without this gate failing: the values are not compared to a
        # magic number but to the third-party artifact they must equal.
        and _rb["central_share_pct"] == _rb_src["central"]["share_pct"]
        and _rb["null_share_pct"] == _rb_src["null"]["share_pct"]
        and abs(_rb["differential_pp"]
                - (_rb["central_share_pct"] - _rb["null_share_pct"])) <= 1e-9
        # basis-invariance of the gap is what licenses quoting it on either
        # basis: re-derive it on the SHARED basis and require the same number
        and abs(_rb["differential_pp"] - (
            (_rb_src["central"]["trapped_b"] - _rb_src["null"]["trapped_b"])
            / _rb_bench * 100.0)) <= 1e-9
        # the superseded cross-basis figure must stay recorded as superseded and
        # must not be the live one
        and _rb["superseded_cross_basis_differential_pp"] == 18.3
        and abs(_rb["differential_pp"] - 18.3) > 8.0
        # the gap is NOT floor-invariant, so the off-window leg is carried too
        # and must trace to the committed OOS table
        and _rb["off_window_differential_pp"] == _rb_oos["band"]["6.5"]["marginal_pp"]
        and _rb["off_window_differential_pp"] < _rb["differential_pp"]
    )
    # Manuscript literals DERIVED from the artifact at printing precision.
    scn_lits = {
        "central_recovery": f"recovers {scn_c['share_pct']:.1f}\\% of the benchmark" in tex,
        "null_recovery": f"recovers {scn_n['share_pct']:.1f}\\%" in tex,
        "differential_pp": f"differential of {scn_d['marginal_pp']:.1f} points" in tex,
        "differential_b": f"\\${scn_d['marginal_b']:.1f} billion" in tex,
        "precedent": f"{_rb['differential_pp']:.1f}-point real-book gap" in tex,
        "precedent_legs": f"{_rb['central_share_pct']:.1f}\\%" in tex
                          and f"null's {_rb['null_share_pct']:.1f}\\%" in tex,
        # the cross-basis error must be named in the manuscript, not silently
        # swapped, and the off-window leg must travel with the in-sample one.
        # The literal no longer requires the words "an earlier draft": the body
        # was de-narrativized so that draft history lives only in the run ledger
        # (Appendix), which catalogues this 18.3-point entry. What this gate
        # protects is unchanged -- the superseded value and its characterization
        # as a basis error must still be named in the manuscript.
        "precedent_basis_error_disclosed":
            f"put that gap at "
            f"{_rb['superseded_cross_basis_differential_pp']:.1f} points, which was "
            f"an error of basis rather than of arithmetic" in tex,
        "precedent_both_calibrations":
            f"the real-book gap is {_rb['differential_pp']:.1f} points at the "
            f"in-sample calibration point and "
            f"{_rb['off_window_differential_pp']:.1f} points at the off-window "
            f"floor" in tex,
        "cpr_lag0": f"to $-{abs(scn_c['cpr_r_lag0']):.2f}$ at lag 0" in tex,
        "no_stale_strengthened":
            "as substantially strengthened by this result" not in tex,
        "demoted_language": "rather than substantially strengthened by its level" in tex,
    }
    scn_ok = (scn_parity_ok and scn_null_is_null_ok and scn_levels_ok
              and scn_derived_ok and scn_claims >= 1 and all(scn_lits.values()))
    failures += 0 if scn_ok else 1
    print(
        f"[{'PASS' if scn_ok else 'FAIL'}] cross-check synthetic companion "
        f"null: parity bitexact={scn_parity_ok} (central "
        f"{scn_c['trapped_b']:.6f}B / {scn_c['share_pct']:.4f}%), "
        f"null-is-beta1-zero={scn_null_is_null_ok} "
        f"(null {scn_n['share_pct']:.4f}%), level-share-identity={scn_levels_ok}, "
        f"derived-not-read={scn_derived_ok}, "
        f"differential {scn_d['marginal_pp']:+.4f}pp / "
        f"{scn_d['marginal_b']:+.4f}B vs threshold "
        f"{scn['material_differential_threshold_pp']}pp -> {scn['verdict']}, "
        f"tex run-citation count={scn_claims} (want >=1), literals="
        f"{ {k: v for k, v in scn_lits.items() if not v} or 'all present'}"
    )

    # Panel revision (gate #62): Path A's spec-v4 seasonal adoption, permutation
    # tested. The adoption was written up as three joint improvements over spec
    # v3 — correlation, peak lag, and recovery — all credited to the eleven
    # month dummies, and no null was ever run. pathA_seasonal_permutation.py
    # runs it, and the two halves point OPPOSITE ways, which is precisely why
    # this gate is here: a later editor tidying the prose could easily drop one
    # half and keep the other. The correlation-and-lag claim SURVIVES on the
    # conjunctive criterion (1 of 64, p = 0.031) and the recovery attribution
    # FAILS (calendar-invariant across the same 64 draws). Five things are
    # bound. (i) All three parity gates bit-exact, cross-read from the COMMITTED
    # adoption and seasonality artifacts rather than trusted from this module's
    # echo. (ii) The JOINT count and its p-value, re-derived from the per-draw
    # rows — this is the primary statistic and the one an earlier audit got
    # wrong by scoring the two components separately. (iii) That the joint count
    # never exceeds either component count, which is an arithmetic necessity and
    # therefore a cheap detector of a mis-scored criterion. (iv) The recovery
    # span, re-derived from the rows, since "the level was never
    # calendar-attributable" is false the moment that span opens up. (v) The
    # refit-only and clawback figures, because the non-decomposability claim is
    # an identity between three numbers and must close exactly. The scope
    # disclaimer is bound too: Path A is excluded from the headline by
    # pre-committed specification, and NO floor or clipping artifact is claimed
    # here (Path A never calls prepay_hazard and the log_mu upper clip never
    # binds), so a future edit cannot quietly promote this into a floor finding.
    pap = json.loads(PATHAPERM_RESULTS.read_text())
    pap_pg = pap["parity_gates"]
    pap_prim = pap["permutation_families"][pap["primary_family"]]
    pap_sec = pap["permutation_families"]["secondary"]
    pap_claims = tex.count("\\texttt{pathA\\_seasonal\\_permutation}")
    PAP_TOL = 1e-9
    _ad = json.loads(PATHAADOPT_RESULTS.read_text())
    _sg_prod = json.loads(SEASGAP_RESULTS.read_text())["path_a_seasonality"]["production"]
    _pap_bench = float(json.loads(EXTRISK_RESULTS.read_text())["empirical_trapped_b"])
    _prod_b = pap["true_legs"]["production_specv3"]["trapped_b"]
    pap_parity_ok = (
        pap_pg["pass"]
        and pap_pg["P1_production"]["abs_diff_b"] == 0.0
        and pap_pg["P2_seasonal"]["abs_diff_b"] == 0.0
        and pap_pg["P3_seasonal_timing"]["abs_diff_r_lag0"] == 0.0
        and pap_pg["P3_seasonal_timing"]["got_best_lag"] == -2
        # cross-read: committed sides come from the COMMITTED artifacts
        and pap_pg["P1_production"]["committed_b"] == float(_sg_prod["trapped_b"])
        and pap_pg["P2_seasonal"]["committed_b"] == float(_ad["v4_trapped_b"])
        and pap_pg["P3_seasonal_timing"]["committed_r_lag0"] == float(_ad["v4_r_lag0"])
        and pap_pg["P3_seasonal_timing"]["committed_best_lag"] == int(_ad["v4_best_lag"])
        # RECOMPUTE the difference rather than trusting the stored zero: an
        # abs_diff of 0.0 is a claim about a subtraction, and the gate must
        # perform that subtraction itself or the got side is unbound.
        and pap_pg["P1_production"]["got_b"] == pap_pg["P1_production"]["committed_b"]
        and pap_pg["P2_seasonal"]["got_b"] == pap_pg["P2_seasonal"]["committed_b"]
        and pap_pg["P3_seasonal_timing"]["got_r_lag0"]
        == pap_pg["P3_seasonal_timing"]["committed_r_lag0"]
        and pap_pg["P3_seasonal_timing"]["got_best_lag"]
        == pap_pg["P3_seasonal_timing"]["committed_best_lag"]
        # and the parity legs must be the same numbers the run actually scored
        and pap_pg["P1_production"]["got_b"] == _prod_b
        and pap_pg["P2_seasonal"]["got_b"]
        == pap["true_legs"]["seasonal_specv4"]["trapped_b"]
        and pap_pg["P3_seasonal_timing"]["got_r_lag0"]
        == pap["true_legs"]["seasonal_specv4"]["r_lag0"]
        and pap_pg["P3_seasonal_timing"]["got_best_lag"]
        == pap["true_legs"]["seasonal_specv4"]["best_lag"]
    )
    # the true legs' own share/level arithmetic, against the third-module benchmark
    pap_legs_ok = (
        float(pap["benchmark_b"]) == _pap_bench
        and all(abs(leg["share_pct"] - leg["trapped_b"] / _pap_bench * 100) <= PAP_TOL
                for leg in (pap["true_legs"]["production_specv3"],
                            pap["true_legs"]["seasonal_specv4"]))
        and abs(pap["true_legs"]["reported_seasonal_effect_b"]
                - (pap["true_legs"]["seasonal_specv4"]["trapped_b"] - _prod_b)) <= PAP_TOL
        and all(
            abs(leg["share_pct"] - leg["trapped_b"] / _pap_bench * 100) <= PAP_TOL
            and abs(leg["effect_b"] - (leg["trapped_b"] - _prod_b)) <= PAP_TOL
            and abs(leg["recovery_pct"] - leg["share_pct"]) <= PAP_TOL
            for leg in pap["decomposition"].values())
    )
    # DERIVE, DON'T READ: rebuild the joint statistic from the per-draw rows.
    _true_r0 = pap["true_legs"]["seasonal_specv4"]["r_lag0"]
    _v3_r0 = pap["true_legs"]["specv3_reference_r_lag0"]

    def _fam_ok(fam, want_n):
        rows = fam["rows"]
        j = fam["PRIMARY_STATISTIC_joint"]
        d = fam["diagnostics_marginal_components"]
        n_j = sum(1 for r in rows if r["r_lag0"] > _true_r0 and r["best_lag"] == -2)
        n_r = sum(1 for r in rows if r["r_lag0"] > _true_r0)
        n_l = sum(1 for r in rows if r["best_lag"] == -2)
        n_v3 = sum(1 for r in rows if r["r_lag0"] > _v3_r0)
        recov = [r["recovery_pct"] for r in rows]
        eff = [r["effect_b"] for r in rows]
        rl = [r["r_lag0"] for r in rows]
        return (
            len(rows) == fam["n_perm"] == want_n
            and sorted(r["perm_index"] for r in rows) == list(range(want_n))
            # every draw is a genuine permutation of the twelve effects
            and all(sorted(r["order"]) == list(range(12)) for r in rows)
            and all(r["order"] != list(range(12)) for r in rows)
            and len({tuple(r["order"]) for r in rows}) == want_n
            # every per-row derived column rebuilt from trapped_b, the only
            # primitive a draw produces
            and all(
                abs(r["share_pct"] - r["trapped_b"] / _pap_bench * 100) <= PAP_TOL
                and abs(r["recovery_pct"] - r["share_pct"]) <= PAP_TOL
                and abs(r["effect_b"] - (r["trapped_b"] - _prod_b)) <= PAP_TOL
                # the stored win flags must agree with the scored criterion,
                # so a row cannot be labelled a win it did not earn
                and r["beats_true_r_lag0"] is (r["r_lag0"] > _true_r0)
                and r["lag_is_minus2"] is (r["best_lag"] == -2)
                and r["joint_win"] is (r["beats_true_r_lag0"] and r["lag_is_minus2"])
                for r in rows)
            and n_j == j["n_joint_wins"] == sum(1 for r in rows if r["joint_win"])
            and n_r == d["n_beating_true_r_lag0"]
            and n_l == d["n_with_best_lag_minus2"]
            and n_v3 == d["n_beating_specv3_r_lag0_-0.444"]
            # arithmetic necessity: the conjunction cannot beat either component
            and n_j <= n_r and n_j <= n_l
            and abs(j["p_one_sided"] - (n_j + 1) / (want_n + 1)) <= PAP_TOL
            # every summary block re-derived from the rows
            and abs(fam["recovery_pct"]["min"] - min(recov)) <= PAP_TOL
            and abs(fam["recovery_pct"]["max"] - max(recov)) <= PAP_TOL
            and abs(fam["recovery_pct"]["mean"] - sum(recov) / want_n) <= 1e-9
            and abs(fam["recovery_pct"]["span_pp"] - (max(recov) - min(recov))) <= PAP_TOL
            and abs(fam["effect_b"]["min"] - min(eff)) <= PAP_TOL
            and abs(fam["effect_b"]["max"] - max(eff)) <= PAP_TOL
            and abs(fam["effect_b"]["mean"] - sum(eff) / want_n) <= 1e-9
            and abs(fam["effect_b"]["sd"] - statistics.stdev(eff)) <= 1e-9
            and abs(fam["r_lag0_span"]["min"] - min(rl)) <= PAP_TOL
            and abs(fam["r_lag0_span"]["max"] - max(rl)) <= PAP_TOL
        )

    pap_derived_ok = _fam_ok(pap_prim, 64) and _fam_ok(pap_sec, 16)
    pap_joint_ok = (
        pap_prim["PRIMARY_STATISTIC_joint"]["n_joint_wins"] == 1
        # p = (n_joint + 1) / (N + 1) = 2/65 at the observed single win
        and abs(pap_prim["PRIMARY_STATISTIC_joint"]["p_one_sided"] - 2 / 65) <= 1e-6
        and pap_prim["PRIMARY_STATISTIC_joint"]["p_one_sided"] <= pap["alpha"]
        # the threshold is pre-committed and may not be relaxed to fit: reading
        # alpha out of the artifact under test lets a run widen its own bar
        # (the defect gate #61 avoids by pinning 25.0 at :2105)
        and pap["alpha"] == 0.05
        and pap["verdict_calendar_alignment"] == "calendar_alignment_supported"
        # the independent family must also return a single win
        and pap_sec["PRIMARY_STATISTIC_joint"]["n_joint_wins"] == 1
    )
    pap_recovery_ok = (
        pap["verdict_recovery"] == "recovery_is_calendar_invariant"
        and pap_prim["recovery_pct"]["span_pp"] <= pap["recovery_invariance_tol_pp"]
        # the adopted level must lie INSIDE the scramble span, else the level
        # is distinguishable from an arbitrary reassignment after all. The
        # adopted level is READ FROM THE TRUE LEG, not hard-coded, so this
        # containment cannot be preserved by sliding the span past a constant.
        and pap_prim["recovery_pct"]["min"]
        <= pap["true_legs"]["seasonal_specv4"]["share_pct"]
        <= pap_prim["recovery_pct"]["max"]
    )
    _dc = pap["decomposability"]
    pap_decomp_ok = (
        _dc["is_decomposable_as_production_plus_seasonality"] is False
        and abs(_dc["refit_only_effect_b"]
                - pap["decomposition"]["refit_only_zero_months"]["effect_b"]) <= PAP_TOL
        # the identity must close: reported = refit_only + clawback
        and abs(_dc["reported_seasonal_effect_b"]
                - (_dc["refit_only_effect_b"]
                   + _dc["month_multiplier_clawback_b"])) <= PAP_TOL
        and abs(_dc["reported_seasonal_effect_b"]
                - (pap["true_legs"]["seasonal_specv4"]["trapped_b"]
                   - pap["true_legs"]["production_specv3"]["trapped_b"])) <= PAP_TOL
    )
    pap_scope_ok = (
        pap["defect_class_1_scope"]["prepay_hazard_called_by_path_a"] is False
        and pap["defect_class_1_scope"]["predict_hazard_log_mu_upper_binds"] == 0
    )
    # Manuscript literals DERIVED from the artifact at printing precision, so
    # that an artifact rerun which no longer matches the prose is detected here
    # rather than shipped. String presence alone cannot see that drift.
    _WORD = {16: "sixteen", 64: "sixty-four"}
    _pj = pap_prim["PRIMARY_STATISTIC_joint"]
    _pd = pap_prim["diagnostics_marginal_components"]
    _prec = pap_prim["recovery_pct"]
    _seas = pap["true_legs"]["seasonal_specv4"]
    pap_lits = {
        "joint_count": f"win {_pj['n_joint_wins']} of {pap_prim['n_perm']} draws" in tex,
        "joint_p": f"one-sided $p$ of {_pj['p_one_sided']:.3f}" in tex,
        "components_diagnostic":
            f"separately, {_pd['n_beating_true_r_lag0']} and "
            f"{_pd['n_with_best_lag_minus2']} of {pap_prim['n_perm']}, "
            f"are diagnostics only" in tex,
        "second_family":
            f"{_WORD[pap_sec['n_perm']]}-draw family at a different seed" in tex,
        "same_family_scrambles":
            f"those same {pap_prim['n_perm']} scrambles" in tex,
        "recovery_span": f"{_prec['min']:.2f}--{_prec['max']:.2f}\\%" in tex,
        "recovery_range": f"range of {_prec['span_pp']:.2f} points" in tex,
        "adopted_level": f"contains the adopted {_seas['share_pct']:.1f}\\%" in tex,
        "seasonal_total": f"\\${_seas['trapped_b']:.1f} billion" in tex,
        "r_lag0_pair": f"from $-{abs(pap['true_legs']['production_specv3']['r_lag0']):.3f}$ "
                       f"to $-{abs(_seas['r_lag0']):.3f}$" in tex,
        "refit_only": f"$+\\${_dc['refit_only_effect_b']:.2f}$ billion" in tex,
        "clawback": f"$-\\${abs(_dc['month_multiplier_clawback_b']):.2f}$ billion" in tex,
        "net_effect": f"$+\\${_dc['reported_seasonal_effect_b']:.2f}$ billion" in tex,
        "no_stale_recovery_credit":
            "with the peak moving from lag $-3$ to $-2$ and the recovery to 121.5\\%"
            not in tex,
    }
    pap_ok = (pap_parity_ok and pap_legs_ok and pap_derived_ok and pap_joint_ok
              and pap_recovery_ok and pap_decomp_ok and pap_scope_ok
              and pap_claims >= 1 and all(pap_lits.values()))
    failures += 0 if pap_ok else 1
    print(
        f"[{'PASS' if pap_ok else 'FAIL'}] cross-check Path A seasonal "
        f"permutation: parity bitexact(P1/P2/P3)={pap_parity_ok} "
        f"(prod {pap_pg['P1_production']['got_b']:.6f}B, seas "
        f"{pap_pg['P2_seasonal']['got_b']:.6f}B, r0 "
        f"{pap_pg['P3_seasonal_timing']['got_r_lag0']:+.6f} lag "
        f"{pap_pg['P3_seasonal_timing']['got_best_lag']}), "
        f"leg-share-identity={pap_legs_ok}, "
        f"derived-not-read={pap_derived_ok}, JOINT "
        f"{pap_prim['PRIMARY_STATISTIC_joint']['n_joint_wins']}/64 p="
        f"{pap_prim['PRIMARY_STATISTIC_joint']['p_one_sided']:.4f} "
        f"[diag r0-beats "
        f"{pap_prim['diagnostics_marginal_components']['n_beating_true_r_lag0']}, "
        f"lag-2 "
        f"{pap_prim['diagnostics_marginal_components']['n_with_best_lag_minus2']}] "
        f"-> {pap['verdict_calendar_alignment']}, secondary "
        f"{pap_sec['PRIMARY_STATISTIC_joint']['n_joint_wins']}/16, "
        f"recovery {pap_prim['recovery_pct']['min']:.4f}-"
        f"{pap_prim['recovery_pct']['max']:.4f}% "
        f"(span {pap_prim['recovery_pct']['span_pp']:.4f}pp) -> "
        f"{pap['verdict_recovery']}, decomposability closed={pap_decomp_ok} "
        f"(refit-only {_dc['refit_only_effect_b']:+.4f}B, clawback "
        f"{_dc['month_multiplier_clawback_b']:+.4f}B, net "
        f"{_dc['reported_seasonal_effect_b']:+.4f}B), "
        f"no-floor-artifact-claimed={pap_scope_ok}, "
        f"tex run-citation count={pap_claims} (want >=1), literals="
        f"{ {k: v for k, v in pap_lits.items() if not v} or 'all present'}"
    )

    # Panel revision (gate #63): the HEADLINE CALIBRATION MIX. The marginal was
    # demoted to the off-window floor (~4.991%) while every recovery figure
    # stayed at the in-window 4.0% — so "recovers 97.9%, within 2.1% of the
    # benchmark" was being quoted alongside a marginal measured 1pp of floor
    # away. calibration_reconciliation.py puts both on one floor. What this
    # gate binds is the ARITHMETIC that licenses the move, not prose, because
    # the whole correction rests on a single claim: that the two accounting
    # bases differ by one additive layer that does not depend on the CPR path.
    # (i) The basis map must be exactly the committed shared-layer artifact's
    # own curtailment netting and cap benchmark — read from THAT artifact, not
    # from the reconciliation's echo of it. (ii) The map must reproduce the
    # committed 4.0% shared anchors 97.9365/88.7381 bit-exactly from the
    # committed standalone 107.0326/97.8342, and this gate performs the
    # subtraction itself rather than trusting a stored diff of 0.0. (iii) The
    # layer must be path-invariant across all five committed estimators; if a
    # future scorer change makes curtailment path-dependent, carrying it to an
    # unrun floor becomes illegitimate and this gate must fail LOUDLY rather
    # than let the extrapolation stand. (iv) Every standalone leg in the floor
    # table must equal the committed OOS marginal table's own value, so no
    # floor can be silently re-simulated into this artifact. (v) The miss is
    # re-derived as 100 minus the central share. (vi) The 88.7-vs-88.5
    # convergence must be reported against BOTH allocations, and the artifact
    # must NOT still assert convergence at the headline floor — the 0.2-point
    # coincidence is an in-window artifact and a later editor must not be able
    # to reinstate it by editing one field.
    cr = json.loads(CALIBRECON_RESULTS.read_text())
    _sl = json.loads(SHAREDLAYER_RESULTS.read_text())["results"]
    _fs_rows = json.loads(FLOORSWEEP_RESULTS.read_text())["rows"]
    _oos_tab = json.loads(OOSIDENT_RESULTS.read_text())["instrument1_marginal_table"]
    _exp = json.loads(EXPECT_RESULTS.read_text())
    _md_g3 = json.loads(MARGDECOMP_RESULTS.read_text())["gates"]["G3_additivity"]
    CR_TOL = 1e-9
    _bm = cr["basis_map"]
    _slc = _sl["path_b_central"]
    # (i) map read from the third-party artifact
    cr_map_ok = (
        _bm["curtailment_netted_b"] == float(_slc["curtailment_netted_b"])
        and _bm["cap_benchmark_b"] == float(_slc["empirical_trapped_b"])
        and abs(_bm["offset_pp"]
                - _bm["curtailment_netted_b"] / _bm["cap_benchmark_b"] * 100.0) < CR_TOL
    )
    # (ii) reproduce the committed 4.0% anchors by performing the arithmetic here
    _fs4 = next(r for r in _fs_rows if r["floor_annual_cpr_pct"] == 4.0)
    def _shared(b):
        return (b - _bm["curtailment_netted_b"]) / _bm["cap_benchmark_b"] * 100.0
    cr_parity_ok = (
        cr["gates"]["A_committed_4pct_parity"]["all_pass"]
        and abs(_shared(_fs4["central"]["trapped_b"])
                - float(_slc["share_pct"])) < CR_TOL
        and abs(_shared(_fs4["null"]["trapped_b"])
                - float(_sl["no_lockin_null"]["share_pct"])) < CR_TOL
        and _fs4["central"]["share_pct"] == float(_slc["standalone_share_pct"])
        and _fs4["null"]["share_pct"] == float(_sl["no_lockin_null"]["standalone_share_pct"])
    )
    # (iii) path-invariance of the layer across every committed estimator
    _curts = {v["curtailment_netted_b"] for v in _sl.values()}
    _caps = {v["empirical_trapped_b"] for v in _sl.values()}
    cr_invariance_ok = (
        cr["gates"]["B_layer_path_invariance"]["pass"]
        and len(_curts) == 1 and len(_caps) == 1
        # the spread the invariance is asserted ACROSS must be real, or the
        # claim is vacuous
        and (max(v["standalone_share_pct"] for v in _sl.values())
             - min(v["standalone_share_pct"] for v in _sl.values())) > 20.0
    )
    # (iv)/(v) every row traceable to the committed OOS table; miss re-derived
    cr_rows_ok = True
    for _r in cr["floor_table"]:
        _src = next(
            (t for t in _oos_tab
             if abs(t["floor_annual_cpr_pct"] - _r["floor_annual_cpr_pct"]) < 1e-6),
            None,
        )
        if _src is None:
            cr_rows_ok = False
            break
        _c65 = _src["band"]["6.5"]
        cr_rows_ok &= (
            _r["standalone"]["central_trapped_b"] == _c65["central_trapped_b"]
            and _r["standalone"]["null_trapped_b"] == _src["null_trapped_b"]
            and _r["marginal_b"] == _c65["marginal_b"]
            and _r["marginal_pp"] == _c65["marginal_pp"]
            and abs(_r["shared"]["central_share_pct"]
                    - _shared(_c65["central_trapped_b"])) < CR_TOL
            and abs(_r["shared"]["null_share_pct"]
                    - _shared(_src["null_trapped_b"])) < CR_TOL
            and abs(_r["miss_vs_benchmark_pp"]
                    - (100.0 - _r["shared"]["central_share_pct"])) < CR_TOL
        )
    _head = next(r for r in cr["floor_table"]
                 if abs(r["floor_annual_cpr_pct"] - 4.991) < 1e-6)
    _prod = next(r for r in cr["floor_table"]
                 if abs(r["floor_annual_cpr_pct"] - 4.0) < 1e-6)
    # the correction only exists if the miss actually grows; pin the direction
    cr_direction_ok = (
        _prod["miss_vs_benchmark_pp"] < 2.5
        and _head["miss_vs_benchmark_pp"] > 8.0
        and _head["shared"]["central_share_pct"] < _prod["shared"]["central_share_pct"]
    )
    # (vi) convergence reported on BOTH allocations and NOT reasserted
    _cv = cr["convergence_88_7_vs_88_5"]
    cr_conv_ok = (
        _cv["allocations"]["uniform_spread_pre_committed_pct"]
        == float(_exp["supplementary_projection_wedge"][
            "expected_share_of_realized_cap_shortfall_pct"])
        and _cv["allocations"]["settlement_aware_pct"]
        == float(_exp["settlement_aware_allocation"][
            "expected_share_of_realized_cap_shortfall_pct"])
        and abs(_cv["at_4pct_in_window_floor"]["gap_vs_uniform_pp"]) < 0.25
        and abs(_cv["at_headline_floor"]["gap_vs_uniform_pp"]) > 2.0
        and abs(_cv["at_headline_floor"]["gap_vs_settlement_aware_pp"]) > 9.0
        and "cannot be reported as a convergence" in _cv["verdict"]
    )
    # the S1--S6 restatements must stay tied to their own source artifacts
    _rs = cr["restatements"]
    cr_restate_ok = (
        _rs["S6_additivity_residual"]["residual_frac_of_total"]
        == float(_md_g3["residual_frac_of_total"])
        and _rs["S6_additivity_residual"]["claim_true_as_written"] is False
        and _rs["S5_intensity_range"]["recomputed_max"] > 1.5
        and abs(_rs["S1_flat_floor_share"]["corrected_pct_of_headline"]
                - 4.897 / _head["marginal_b"] * 100.0) < 1e-6
        and _rs["S2_vintage_bound_fraction"]["corrected_fraction_of_headline"] > 0.25
        and _rs["S4_cross_basis_gap"]["single_basis_gap_at_headline_pp"]
        == _head["marginal_pp"]
    )
    # (vii) the headline_calibration block is a SUMMARY of the floor table, and
    # a summary is exactly where a self-consistent drift hides: every field
    # inside it can be moved together so that the block agrees with itself and
    # with the prose while contradicting the primitives it claims to summarize.
    # So no field here is read as given — each is re-derived from the floor
    # table rows, and the band edges are re-derived as the min and max over the
    # clean-band rows rather than trusted as a stored pair.
    _edges = [r for r in cr["floor_table"] if r["role"] == "clean band edge"]
    _cent_edges = [r["shared"]["central_share_pct"] for r in _edges]
    _null_edges = [r["shared"]["null_share_pct"] for r in _edges]
    _miss_edges = [r["miss_vs_benchmark_pp"] for r in _edges]
    _h = cr["headline_calibration"]
    cr_summary_ok = (
        len(_edges) == 2
        and _h["floor_annual_cpr_pct"] == _head["floor_annual_cpr_pct"]
        and _h["central_shared_share_pct"] == _head["shared"]["central_share_pct"]
        and _h["null_shared_share_pct"] == _head["shared"]["null_share_pct"]
        and _h["miss_vs_benchmark_pp"] == _head["miss_vs_benchmark_pp"]
        and _h["marginal_b"] == _head["marginal_b"]
        and _h["marginal_pp"] == _head["marginal_pp"]
        and _h["central_shared_share_band_pct"] == [min(_cent_edges), max(_cent_edges)]
        and _h["null_shared_share_band_pct"] == [min(_null_edges), max(_null_edges)]
        and _h["miss_vs_benchmark_band_pp"] == [min(_miss_edges), max(_miss_edges)]
        # the headline point must sit INSIDE its own band, or the band is not a
        # band around it
        and min(_cent_edges) <= _h["central_shared_share_pct"] <= max(_cent_edges)
        # the superseded claim must stay named as superseded, so the retraction
        # cannot be quietly converted back into an assertion
        and "97.9" in _h["superseded_claim"]
        and "in-window calibration" in _h["corrected_claim"]
    )
    # (viii) Manuscript literals DERIVED from the artifact at the manuscript's
    # own printing precision. Without this the entire correction is unbound in
    # the direction that matters most: the artifact could be recomputed, or the
    # prose reverted to the superseded 97.9%/2.1-point reading, and nothing
    # would notice. Both calibrations are bound at once, because the defect
    # being gated is precisely the MIXING of the two — a literal check that
    # bound only the headline would let the in-sample labels rot away.
    _lo, _hi = _h["central_shared_share_band_pct"]
    _s1 = _rs["S1_flat_floor_share"]
    _s2 = _rs["S2_vintage_bound_fraction"]
    _s5 = _rs["S5_intensity_range"]
    _s6 = _rs["S6_additivity_residual"]
    cr_lits = {
        # ROUND-23: these four were abstract phrasings. The 263-word abstract
        # keeps the two headline levels (null and central) and drops the range
        # and the in-sample point, so the checks now bind the BODY sentences
        # that carry all four -- V.C's paired statement and the Discussion
        # opener. The numbers are still derived from the artifact, not typed.
        "body_central":
            f"recovers {_h['central_shared_share_pct']:.1f}\\% of the benchmark "
            f"on the shared basis at the off-window floor" in tex,
        "body_band":
            f"({_lo:.1f}--{_hi:.1f}\\% across its range)" in tex,
        "body_insample":
            f"against {_prod['shared']['central_share_pct']:.1f}\\% at the "
            f"in-window calibration" in tex,
        "abstract_null_and_central_kept":
            f"still accounts for {_h['null_shared_share_pct']:.1f}\\% of it" in tex
            and f"accounts for {_h['central_shared_share_pct']:.1f}\\%." in tex,
        "miss_both_calibrations":
            f"the miss is {_h['miss_vs_benchmark_pp']:.1f} points on the headline "
            f"calibration and {_prod['miss_vs_benchmark_pp']:.1f} points on the "
            f"in-sample one" in tex,
        "miss_standalone": f"a miss of {_h['miss_vs_benchmark_pp']:.1f} points" in tex,
        "headline_marginal_b": f"$+\\${_h['marginal_b']:.1f}$ billion" in tex,
        "headline_marginal_pp": f"$+{_h['marginal_pp']:.1f}$ percentage points" in tex,
        # S1: the same absolute bound restated against the headline marginal
        "S1_share_of_headline":
            f"{_s1['corrected_pct_of_headline']:.1f}\\% of the "
            f"$+\\${_h['marginal_b']:.1f}$ billion headline marginal" in tex,
        # S2: the vintage bound as a fraction of BOTH marginals
        "S2_both_fractions":
            f"({_s2['corrected_fraction_of_headline'] * 100:.1f}\\% of the "
            f"off-window \\${_h['marginal_b']:.1f} billion; a sixth, "
            f"{_s2['as_printed_fraction_of_in_sample'] * 100:.1f}\\%, of the "
            f"in-sample \\${_prod['marginal_b']:.1f} billion)" in tex,
        "S5_intensity_range":
            f"from ${_s5['recomputed_min']:.2f}\\times$ to "
            f"${_s5['recomputed_max']:.2f}\\times$" in tex,
        "S6_residual":
            f"sum to within {_s6['residual_pct_of_total']:.2f}\\% of the "
            f"paired-run total" in tex,
        "settlement_aware_share":
            f"anticipated share at "
            f"{_cv['allocations']['settlement_aware_pct']:.1f}\\%" in tex,
        "convergence_retracted_gaps":
            f"clears by "
            f"{_cv['at_4pct_in_window_floor']['gap_vs_settlement_aware_pp']:.1f} "
            f"points in-sample and "
            f"{_cv['at_headline_floor']['gap_vs_settlement_aware_pp']:.1f} points"
            in tex,
    }
    cr_claims = tex.count("\\texttt{calibration\\_reconciliation}")
    cr_ok = (cr["gates"]["all_pass"] and cr_map_ok and cr_parity_ok
             and cr_invariance_ok and cr_rows_ok and cr_direction_ok
             and cr_conv_ok and cr_restate_ok and cr_summary_ok
             and cr_claims >= 1 and all(cr_lits.values()))
    failures += 0 if cr_ok else 1
    print(
        f"[{'PASS' if cr_ok else 'FAIL'}] cross-check headline calibration "
        f"reconciliation: basis-map-from-source={cr_map_ok} "
        f"(-${_bm['curtailment_netted_b']:.6f}B / ${_bm['cap_benchmark_b']:.6f}B "
        f"= -{_bm['offset_pp']:.4f}pp), 4%-parity-bitexact={cr_parity_ok} "
        f"(central {_prod['shared']['central_share_pct']:.4f}%, null "
        f"{_prod['shared']['null_share_pct']:.4f}%), "
        f"layer-path-invariant={cr_invariance_ok}, "
        f"rows-trace-to-oos={cr_rows_ok}, direction={cr_direction_ok} "
        f"(miss {_prod['miss_vs_benchmark_pp']:.2f}pp at 4.0% -> "
        f"{_head['miss_vs_benchmark_pp']:.2f}pp at 4.991%; central "
        f"{_head['shared']['central_share_pct']:.2f}%, marginal "
        f"{_head['marginal_b']:+.2f}B/{_head['marginal_pp']:+.2f}pp), "
        f"convergence-retired={cr_conv_ok} (null "
        f"{_cv['at_headline_floor']['null_shared_share_pct']:.2f}% vs uniform "
        f"{_cv['at_headline_floor']['gap_vs_uniform_pp']:+.2f}pp vs "
        f"settlement-aware "
        f"{_cv['at_headline_floor']['gap_vs_settlement_aware_pp']:+.2f}pp), "
        f"restatements-tied={cr_restate_ok} (S5 "
        f"{_rs['S5_intensity_range']['recomputed_min']:.3f}-"
        f"{_rs['S5_intensity_range']['recomputed_max']:.3f}x, S6 "
        f"{_rs['S6_additivity_residual']['residual_pct_of_total']:.2f}%), "
        f"summary-rederived-from-rows={cr_summary_ok} (band "
        f"{_h['central_shared_share_band_pct'][0]:.2f}-"
        f"{_h['central_shared_share_band_pct'][1]:.2f}%), "
        f"tex run-citation count={cr_claims} (want >=1), literals="
        f"{ {k: v for k, v in cr_lits.items() if not v} or 'all present'}"
    )

    # Panel revision (gate #64): the SIGN-FORCING STATISTICS' PROVENANCE. The
    # five figures §V rests the sign demotion on were computed in session and
    # written straight into the .tex, with no committed artifact behind them —
    # the one sourcing rule every other run in this repo has been held to.
    # sign_forcing_stats.py promotes them. This gate binds the artifact to the
    # manuscript literals BY DERIVING each expected string from the artifact at
    # the manuscript's own printing precision, so the .tex cannot drift from
    # the data in either direction. Three further things are bound. (i) The
    # coupon column's DECIMAL scale, because the whole computation turns on it:
    # a percent-scale threshold query returns a meaningless 100.00% and would
    # silently "confirm" the claim. This gate asserts the panel's coupon range
    # really is decimal and that the reported shares are NOT 100%. (ii) The
    # coverage shortfall — 40 of 42 window months — must remain disclosed and
    # must remain a shortfall, so nobody can quietly claim full coverage. (iii)
    # The window minimum must exceed the thresholds the shares are cut at,
    # which is what makes those shares out-of-the-money shares at all; if a
    # data revision moved the minimum below them the statistics would still
    # compute but would no longer mean what §V says they mean.
    ss = json.loads(SIGNSTATS_RESULTS.read_text())
    # RECOMPUTE the four panel-derived statistics from the panel itself rather
    # than reading the module's own echo of them. Reading ss["statistics"] and
    # deriving the .tex literals from it means a module that miscomputed its
    # own numbers is ratified, not caught -- the defect class that recurred in
    # gates #59 and #60-#62. The coupon column is DECIMAL-scaled; a percent
    # threshold silently matches everything, so assert the scale first.
    import pandas as _pd
    _pan = _pd.read_parquet(PANEL_PATH, columns=["reporting_period", "coupon", "exposure_upb"])
    _pan["_rp"] = _pan["reporting_period"].astype(int)
    _w = _pan[(_pan._rp >= 202206) & (_pan._rp <= 202511) & (_pan.coupon > 0)]
    _tot = float(_w.exposure_upb.sum())
    _recomp = {
        "exposure_weighted_mean_coupon_pct": float((_w.coupon * _w.exposure_upb).sum()) / _tot * 100.0,
        "exposure_share_le_4_79_pct": float(_w[_w.coupon <= 0.0479].exposure_upb.sum()) / _tot * 100.0,
        "exposure_share_le_5_09_pct": float(_w[_w.coupon <= 0.0509].exposure_upb.sum()) / _tot * 100.0,
        "covered_window_months": int(_w._rp.nunique()),
    }
    _ss_recomp_ok = (
        float(_pan.coupon.max()) <= 0.075 + 1e-12          # decimal scale, not percent
        and all(abs(_recomp[k] - ss["statistics"][k]) <= 1e-6 for k in
                ("exposure_weighted_mean_coupon_pct", "exposure_share_le_4_79_pct",
                 "exposure_share_le_5_09_pct"))
        and _recomp["covered_window_months"] == ss["statistics"]["covered_window_months"]
        # the shares must not be the degenerate 100% a percent-scale query returns
        and _recomp["exposure_share_le_4_79_pct"] < 99.9
    )
    ss_st = ss["statistics"]
    ss_win = ss["window"]
    ss_scale = ss["source"]["coupon_column_scale"]
    ss_gates_ok = ss["gates"]["all_pass"]
    # (i) decimal scale, and the shares are not the degenerate 100%
    ss_scale_ok = (
        0.0 <= ss_scale["min"] and ss_scale["max"] <= 0.1
        and ss_st["exposure_share_le_4_79_pct"] < 100.0
        and ss_st["exposure_share_le_5_09_pct"] < 100.0
        and "decimal-scaled" in ss_scale["reading"]
    )
    # (ii) coverage disclosed and still short
    ss_cov_ok = (
        ss_win["window_months"] == 42
        and ss_win["panel_covered_months"] == 40
        and ss_win["uncovered_months"] == 2
        and ss_st["covered_window_months"] == ss_win["panel_covered_months"]
        and ss_win["panel_last_covered"] == "2025-09-01"
    )
    # (iii) the minimum dominates the thresholds the shares are cut at
    ss_otm_ok = all(
        ss_st["window_min_mortgage30us_pct"] > t
        for t in ss["printed_thresholds_pct"]
    )
    # manuscript literals DERIVED from the artifact at printing precision
    ss_lits = {
        "covered_months": (
            f"Over the forty window months the cohort panel covers" in tex
            and ss_win["panel_covered_months"] == 40
        ),
        "mean_coupon":
            f"exposure-weighted mean coupon on the surviving book is "
            f"{ss_st['exposure_weighted_mean_coupon_pct']:.3f}\\%" in tex,
        "share_479":
            f"with {ss_st['exposure_share_le_4_79_pct']:.2f}\\% of exposure at "
            f"or below {ss['printed_thresholds_pct'][0]:.2f}\\%" in tex,
        "share_509":
            f"and {ss_st['exposure_share_le_5_09_pct']:.2f}\\% at or below "
            f"{ss['printed_thresholds_pct'][1]:.2f}\\%" in tex,
        "window_min":
            f"against a window-minimum 30-year rate of "
            f"{ss_st['window_min_mortgage30us_pct']:.4f}\\%" in tex,
        "coverage_disclosed": "the panel ends two months before the window does" in tex,
        "sign_still_demoted":
            "This is why the reported range, and not the sign, carries the "
            "paper's identified content." in tex,
    }
    # S7's actual defect was provenance, not accuracy: the five figures were
    # correct but cited no run. The manuscript must carry the run citation, on
    # the same footing as every other run in this repo.
    ss_claims = tex.count("\\texttt{sign\\_forcing\\_stats}")
    ss_ok = (ss_gates_ok and ss_scale_ok and ss_cov_ok and ss_otm_ok
             and _ss_recomp_ok
             and ss_claims >= 1 and all(ss_lits.values()))
    failures += 0 if ss_ok else 1
    print(
        f"[{'PASS' if ss_ok else 'FAIL'}] cross-check sign-forcing statistics "
        f"provenance: artifact-gates={ss_gates_ok} (mean coupon "
        f"{ss_st['exposure_weighted_mean_coupon_pct']:.3f}%, "
        f"{ss_st['exposure_share_le_4_79_pct']:.2f}% <=4.79%, "
        f"{ss_st['exposure_share_le_5_09_pct']:.2f}% <=5.09%, window min "
        f"{ss_st['window_min_mortgage30us_pct']:.4f}%), "
        f"decimal-scale={ss_scale_ok} (coupon range "
        f"{ss_scale['min']:.3f}-{ss_scale['max']:.3f}), "
        f"coverage-disclosed={ss_cov_ok} "
        f"({ss_win['panel_covered_months']}/{ss_win['window_months']} months, "
        f"panel ends {ss_win['panel_last_covered']}), "
        f"min-dominates-thresholds={ss_otm_ok}, "
        f"tex run-citation count={ss_claims} (want >=1), literals="
        f"{ {k: v for k, v in ss_lits.items() if not v} or 'all present'}"
    )

    # Round-20 (gate #65): the MATCHED-DEPTH DECOMPOSITION of the floor
    # demotion. §VII.D now retracts a flat factual error (it claimed no
    # off-window cohort reaches the two-point discount depth; the cell exists
    # and holds 35 cohort-months) and replaces it with an exposure-collapse
    # argument, then gives a WINDOW/DEPTH split the paper had never computed.
    # Both are load-bearing against the hostile "the whole demotion is a depth
    # artifact" reading, so both are bound here under the discipline gates
    # #58-#64 arrived at only after each was first reported hardened and was
    # not: (i) every aggregate is DERIVED from per-record primitives, never
    # read from the artifact's own summary; (ii) the depth grid is RECOMPUTED
    # from cohort_month_panel.parquet -- the committed source -- against a rate
    # history taken from a THIRD module's artifact, so neither the panel cut
    # nor the gap column can be manufactured by the module under test; (iii)
    # the 10% exposure-support rule and the depth ladder are PINNED here, not
    # read from the artifact whose admissibility claims they adjudicate (the
    # defect gate #62 carried, reading its own alpha); (iv) the floor LEVELS,
    # not merely their differences, are tied to oos_identification's
    # independently produced reads (the defect gate #60 carried); and (v) every
    # manuscript literal is DERIVED at the manuscript's own printing precision.
    md = json.loads(MATCHEDDEPTH_RESULTS.read_text())
    # PINNED ex ante -- these are the adjudicating constants, and reading them
    # from the artifact under test would let a run relax its own support rule
    # to admit a cell holding 0.02% of its exposure.
    MD_DEPTHS = (0.0, -0.0025, -0.005, -0.0075, -0.01, -0.015, -0.02, -0.025)
    MD_SUPPORT = 0.10
    MD_AGE = 12.0
    MD_LEGS = {
        "OFF_pooled_2017_2019": (201701, 201912),
        "OFF_2018_rising_rate": (201801, 201812),
        "OFF_2019_falling_rate": (201901, 201912),
        "IN_in_window_calibration_202206_202312": (202206, 202312),
        "IN_in_window_full_qt_202206_202509": (202206, 202509),
    }
    import numpy as _np
    from scipy.interpolate import PchipInterpolator as _Pchip
    _b0series = json.loads(B0VAR_RESULTS.read_text())["series"]
    _rate = {r["period"].replace("-", ""): float(r["mortgage30us_pct"])
             for r in _b0series}
    _mp = _pd.read_parquet(PANEL_PATH, columns=[
        "coupon", "reporting_period", "exposure_upb", "prepaid_upb", "mean_loan_age"])
    _mp["_rp"] = _mp["reporting_period"].astype(int)
    _mp = _mp[(_mp.coupon > 0) & (_mp.exposure_upb > 0)].copy()
    _mp["_mkt"] = _mp["_rp"].astype(str).map(_rate)
    _mp = _mp[_mp._mkt.notna()].copy()
    _mp["_gap"] = _mp.coupon - _mp._mkt / 100.0

    def _md_cell(lo, hi, thr):
        s = _mp[(_mp._rp >= lo) & (_mp._rp <= hi) & (_mp._gap <= thr)
                & (_mp.mean_loan_age >= MD_AGE)]
        e = float(s.exposure_upb.sum())
        if e <= 0:
            return {"cpr": None, "upb": 0.0, "n": 0}
        smm = float(s.prepaid_upb.sum()) / e
        return {"cpr": round((1 - (1 - smm) ** 12) * 100, 3), "upb": e, "n": int(len(s))}

    _MG = {}
    for _leg, (_lo, _hi) in MD_LEGS.items():
        _cells = {t: _md_cell(_lo, _hi, t) for t in MD_DEPTHS}
        _base = _cells[0.0]["upb"]
        for t in MD_DEPTHS:
            _cells[t]["share"] = _cells[t]["upb"] / _base if _base > 0 else 0.0
            # well-supported is decided by the PINNED rule, never by the flag
            _cells[t]["sup"] = _cells[t]["share"] >= MD_SUPPORT
        _MG[_leg] = _cells
    _mdgrid = md["step2_matched_depth_grid"]
    md_grid_ok = (
        sorted(_mdgrid) == sorted(MD_LEGS)
        and abs(md["support_rule"]["min_exposure_share_of_gap0"] - MD_SUPPORT) < 1e-12
        and all(
            sorted(round(c["gap_threshold"], 6) for c in _mdgrid[leg]["depths"].values())
            == sorted(round(t, 6) for t in MD_DEPTHS) for leg in MD_LEGS)
        and all(
            _mdgrid[leg]["depths"][f"{t:+.4f}"]["cpr_pct"] == _MG[leg][t]["cpr"]
            and _mdgrid[leg]["depths"][f"{t:+.4f}"]["n_cohort_months"] == _MG[leg][t]["n"]
            and abs(_mdgrid[leg]["depths"][f"{t:+.4f}"]["exposure_upb"]
                    - _MG[leg][t]["upb"]) <= 1e-3
            and bool(_mdgrid[leg]["depths"][f"{t:+.4f}"]["well_supported"]) == _MG[leg][t]["sup"]
            for leg in MD_LEGS for t in MD_DEPTHS)
    )
    # floor -> marginal mapping rebuilt from the INDEPENDENT committed sweep
    _sw = json.loads(FLOORSWEEP_RESULTS.read_text())
    _xs = _np.array([r["floor_annual_cpr_pct"] for r in _sw["rows"]], float)
    _ys = _np.array([r["lockin_marginal_b"] for r in _sw["rows"]], float)
    _o = _np.argsort(_xs)
    _P = _Pchip(_xs[_o], _ys[_o])
    _LO, _HI = float(_xs.min()), float(_xs.max())

    def _M(f):
        return None if (f is None or f < _LO or f > _HI) else float(_P(f))

    # the mapping must reproduce oos_identification's INDEPENDENT engine reads
    _oos = json.loads(OOSIDENT_RESULTS.read_text())
    _bench = json.loads(EXPECT_RESULTS.read_text())["cap_benchmark_b"]
    _eng_err = [abs(_M(round(float(r["floor_annual_cpr_pct"]), 4))
                    - r["band"]["6.5"]["marginal_b"])
                for r in _oos["instrument1_marginal_table"]
                if _M(round(float(r["floor_annual_cpr_pct"]), 4)) is not None]
    md_map_maxerr = max(_eng_err)
    md_map_ok = md_map_maxerr < 1.0
    # decomposition DERIVED from the recomputed floors through that mapping
    _IN, _OFF, _L19 = ("IN_in_window_calibration_202206_202312",
                       "OFF_2018_rising_rate", "OFF_2019_falling_rate")
    _f_in_deep = _MG[_IN][-0.02]["cpr"]
    _f_in_shal = _MG[_IN][-0.0025]["cpr"]
    _f_off_shal = _MG[_OFF][-0.0025]["cpr"]
    md_total_b = _M(_f_off_shal) - _M(_f_in_deep)
    md_depth_b = _M(_f_in_shal) - _M(_f_in_deep)
    md_window_b = _M(_f_off_shal) - _M(_f_in_shal)
    md_wshare, md_dshare = md_window_b / md_total_b, md_depth_b / md_total_b
    md_matched_point = _M(_f_in_shal)
    _pa = md["step3_decomposition"]["path_a_depth_first"]
    md_decomp_ok = (
        abs(_pa["window_component_b"] - md_window_b) <= 0.01
        and abs(_pa["depth_component_b"] - md_depth_b) <= 0.01
        and abs(md["step3_decomposition"]["total_move_b"] - md_total_b) <= 0.01
        and abs(md_depth_b + md_window_b - md_total_b) <= 0.01
        and abs(md["verdict"]["matched_depth_in_sample_comparison_point_b"]
                - md_matched_point) <= 0.01
        and md_wshare > md_dshare          # WINDOW dominates -- derived, not read
        # the verdict block is a SUMMARY and was previously unchecked against
        # step3: perturbation P3 swapped the window and depth components inside
        # it, leaving it self-consistent, and the gate still passed.
        and abs(md["verdict"]["window_component_b"] - md_window_b) <= 0.01
        and abs(md["verdict"]["depth_component_b"] - md_depth_b) <= 0.01
        and abs(md["verdict"]["depth_share_admissible_path"] - md_dshare) <= 1e-6
        and abs(_pa["depth_share_of_total"] - md_dshare) <= 1e-6
        and abs(_pa["window_share_of_total"] - md_wshare) <= 1e-6
    )
    # anchor LEVELS tied to an independently produced artifact, not just their
    # difference: the in-window deep read and the whole off-window clean band
    # must equal oos_identification's own committed reads.
    _oos_in = _oos["instrument2_temporal_holdout"]["calibration_floor"]["reads"]
    _oos_hl = _oos["headline_oos_marginal"]
    md_levels_ok = (
        _oos_in["gap<=-0.02_age>=12"]["cpr_pct"] == _f_in_deep
        and _oos_in["gap<=0_age>=12"]["cpr_pct"] == _MG[_IN][0.0]["cpr"]
        and _oos_hl["clean_floor_point_pct"] == _f_off_shal
        and _oos_hl["clean_floor_band_pct"] == [_MG[_OFF][-0.005]["cpr"],
                                                _MG[_OFF][0.0]["cpr"]]
    )
    # deepest well-supported COMMON depth, and the three-step cross-check
    _common = [t for t in MD_DEPTHS if _MG[_IN][t]["sup"] and _MG[_OFF][t]["sup"]]
    _deepest = min(_common)
    _s1 = _M(_MG[_IN][_deepest]["cpr"]) - _M(_f_in_deep)
    _s2 = _M(_MG[_OFF][_deepest]["cpr"]) - _M(_MG[_IN][_deepest]["cpr"])
    _s3 = _M(_f_off_shal) - _M(_MG[_OFF][_deepest]["cpr"])
    md_w3, md_d3 = _s2 / md_total_b, (_s1 + _s3) / md_total_b
    md_three_ok = (_deepest == -0.01 and md_w3 > md_d3
                   and abs(md["step3_decomposition"]
                           ["three_step_via_deepest_common_depth"]
                           ["window_share_of_total"] - md_w3) <= 1e-6)
    # the reverse ordering is REFUSED, and refused for the pinned reason
    md_refusal_ok = (
        not _MG[_OFF][-0.02]["sup"]
        and _MG[_OFF][-0.02]["share"] < MD_SUPPORT
        and bool(md["step3_decomposition"]["shapley_average_refused"])
        and not bool(md["step3_decomposition"]["path_b_window_first"]["admissible"])
    )
    # extended ladder leaves the committed clean band unchanged -- DERIVED
    _ws = [_MG[_OFF][t]["cpr"] for t in MD_DEPTHS if _MG[_OFF][t]["sup"]]
    md_band = [min(_ws), max(_ws)]
    md_mb = sorted((_M(md_band[0]), _M(md_band[1])))
    # ...and the artifact's OWN clean-band block must agree with the derivation.
    # Without this the block is a free-floating summary: perturbation P4 rewrote
    # point_marginal_b and marginal_band_b to invented values and the gate
    # still passed, because nothing read them.
    _cb = md["clean_band_under_extended_ladder"]
    md_band_ok = (
        len(_ws) == 5 and md_band == _oos_hl["clean_floor_band_pct"]
        and all(md_band[0] < r < md_band[1]
                for r in (_MG[_OFF][-0.0075]["cpr"], _MG[_OFF][-0.01]["cpr"]))
        and _cb["extended_well_supported_band_pct"] == md_band
        and _cb["committed_band_pct"] == md_band
        and bool(_cb["band_unchanged_by_extension"])
        and sorted(_cb["well_supported_reads_pct"]) == sorted(_ws)
        and _cb["point_floor_pct"] == _f_off_shal
        and abs(_cb["point_marginal_b"] - _M(_f_off_shal)) <= 0.01
        and all(abs(a - b) <= 0.01
                for a, b in zip(sorted(_cb["marginal_band_b"]), md_mb))
    )
    # matched-depth leg comparison -- DERIVED over the pinned support rule
    _adj = [t for t in MD_DEPTHS if _MG[_OFF][t]["sup"] and _MG[_L19][t]["sup"]]
    md_spreads = [round(abs(_MG[_L19][t]["cpr"] - _MG[_OFF][t]["cpr"]), 3) for t in _adj]
    md_mismatch = round(_MG[_L19][0.0]["cpr"] - _MG[_OFF][-0.0025]["cpr"], 3)
    md_legs_ok = (
        len(_adj) == 4
        # non-monotone in depth, and the deepest-but-one spread EXCEEDS the
        # mismatched spread the earlier argument rested on: this is what makes
        # "the legs agree once depth is matched" a cherry-pick, so it is bound.
        and not all(md_spreads[i] >= md_spreads[i + 1] for i in range(len(md_spreads) - 1))
        and max(md_spreads) > md_mismatch
        # pooled is NOT a third independent leg -- asserted from the PINNED
        # windows, not from the artifact's own note about itself
        and (MD_LEGS["OFF_pooled_2017_2019"][0] <= MD_LEGS[_OFF][0]
             and MD_LEGS[_OFF][1] <= MD_LEGS["OFF_pooled_2017_2019"][1]
             and MD_LEGS["OFF_pooled_2017_2019"][0] <= MD_LEGS[_L19][0]
             and MD_LEGS[_L19][1] <= MD_LEGS["OFF_pooled_2017_2019"][1])
        and bool(md["step4_contamination_at_matched_depth"]["pooled_is_not_independent"])
    )
    # manuscript literals DERIVED from the recomputation at printing precision
    _min_gap = float(_mp[(_mp._rp >= MD_LEGS[_OFF][0]) & (_mp._rp <= MD_LEGS[_OFF][1])
                         & (_mp.mean_loan_age >= MD_AGE)]._gap.min())
    _dc = _MG[_OFF][-0.02]
    _ladder = [_MG[_OFF][t]["share"] for t in MD_DEPTHS[:7]]
    _insample_b = _oos["parity_gates"]["lockin_marginal_b"]["got"]
    _oos_point_b = _oos_hl["clean_marginal_b_point_at_6.5"]
    md_lits = {
        "min_gap": f"$-{abs(_min_gap) * 100:.2f}$ points" in tex,
        "deep_cell_read":
            f"{_dc['n']} cohort-months reading {_dc['cpr']:.3f}\\% annual CPR" in tex,
        "exposure_ladder":
            (f"{_ladder[0] * 100:.0f}\\%, "
             + ", ".join(f"{s * 100:.1f}\\%" for s in _ladder[1:6])
             + f", and {_ladder[6] * 100:.2f}\\%") in tex,
        "deep_cell_dollars":
            (f"\\${_dc['upb'] / 1e9:.3f} billion of "
             f"\\${_MG[_OFF][0.0]['upb'] / 1e9:,.1f} billion").replace(",", "{,}") in tex,
        "support_rule":
            f"at least {MD_SUPPORT * 100:.0f}\\% of its gap-$\\leq$-0 exposure" in tex,
        "total_move":
            (f"$-\\${abs(md_total_b):.3f}$ billion, or "
             f"$-{abs(md_total_b) / _bench * 100:.3f}$ points") in tex,
        "window_component":
            (f"$-\\${abs(md_window_b):.3f}$ billion "
             f"($-{abs(md_window_b) / _bench * 100:.3f}$ points, "
             f"{md_wshare * 100:.1f}\\%") in tex,
        "depth_component":
            (f"$-\\${abs(md_depth_b):.3f}$ billion "
             f"($-{abs(md_depth_b) / _bench * 100:.3f}$ points, "
             f"{md_dshare * 100:.1f}\\%") in tex,
        "three_step": f"{md_w3 * 100:.1f}\\% window and {md_d3 * 100:.1f}\\% depth" in tex,
        "matched_point":
            (f"$+\\${md_matched_point:.1f}$ billion, not the "
             f"$+\\${_insample_b:.1f}$ billion") in tex,
        "demotion_split":
            (f"\\${abs(md_window_b):.1f} billion of the "
             f"\\${_insample_b - _oos_point_b:.1f} billion") in tex,
        "refusal_share": f"retains {_dc['share'] * 100:.2f}\\% of its exposure" in tex,
        "mapping_fidelity": f"within \\${md_map_maxerr:.2f} billion" in tex,
        "clean_band": f"[{md_band[0]:.3f}\\%, {md_band[1]:.3f}\\%]" in tex,
        "new_reads":
            (f"{_MG[_OFF][-0.0075]['cpr']:.3f}\\% at gap $\\leq -0.75$ points, "
             f"{_MG[_OFF][-0.01]['cpr']:.3f}\\% at gap $\\leq -1$ point") in tex,
        "marginal_band":
            (f"\\${md_mb[0]:.2f} to \\${md_mb[1]:.2f} billion around the "
             f"\\${_M(_f_off_shal):.2f} billion point") in tex,
        "rejection_read": f"{_MG[_L19][0.0]['cpr']:.3f}\\%" in tex,
        "mismatched_spread": f"{md_mismatch:.3f}-point spread" in tex,
        "adjudicable_spreads":
            (", ".join(f"{s:.3f}" for s in md_spreads[:-1])
             + f", and {md_spreads[-1]:.3f} points") in tex,
        "leg2019_collapse":
            (f"\\${_MG[_L19][0.0]['upb'] / 1e9:,.0f} billion at gap $\\leq$ 0 to "
             f"\\${_MG[_L19][-0.005]['upb'] / 1e9:.0f} billion by half a point and "
             f"\\${_MG[_L19][-0.015]['upb'] / 1e9:.2f} billion").replace(",", "{,}") in tex,
        "gap0_verdict": f"{md_spreads[0]:.3f} points above 2018" in tex,
        "unadjudicable": "unadjudicable below gap $\\leq$ 0 rather than refuted" in tex,
    }
    md_claims = tex.count("\\texttt{matched\\_depth\\_reconciliation}")
    md_ok = (md_grid_ok and md_map_ok and md_decomp_ok and md_levels_ok
             and md_three_ok and md_refusal_ok and md_band_ok and md_legs_ok
             and md_claims >= 1 and all(md_lits.values()))
    failures += 0 if md_ok else 1
    print(
        f"[{'PASS' if md_ok else 'FAIL'}] cross-check matched-depth "
        f"reconciliation: grid-recomputed-from-panel={md_grid_ok} "
        f"(40 cells, rate series cross-read from b0_variance_decomposition, "
        f"support rule PINNED at {MD_SUPPORT:.2f}), mapping-rebuilt-from-sweep="
        f"{md_map_ok} (max |mapped-engine| ${md_map_maxerr:.4f}B), "
        f"decomp-derived={md_decomp_ok} (window -${abs(md_window_b):.3f}B "
        f"{md_wshare * 100:.1f}% vs depth -${abs(md_depth_b):.3f}B "
        f"{md_dshare * 100:.1f}%, matched-depth point ${md_matched_point:.3f}B), "
        f"levels-cross-tied-to-oos={md_levels_ok}, three-step={md_three_ok} "
        f"(deepest common {_deepest}, {md_w3 * 100:.1f}/{md_d3 * 100:.1f}), "
        f"reverse-ordering-refused={md_refusal_ok} "
        f"(off deep share {_dc['share'] * 100:.3f}% < {MD_SUPPORT * 100:.0f}%), "
        f"extended-ladder-band-unchanged={md_band_ok} ({md_band}), "
        f"legs-non-monotone={md_legs_ok} (spreads {md_spreads} vs mismatched "
        f"{md_mismatch}), tex run-citation count={md_claims} (want >=1), "
        f"literals={ {k: v for k, v in md_lits.items() if not v} or 'all present'}"
    )

    # Round-20 (gate #66): the DANISH POSITIVITY RELABEL. danish_us_intercept
    # defines the Danish moving hazard as the production U.S. hazard AT A ZERO
    # RATE GAP; the U.S. book carries a negative gap in essentially every cell;
    # the hazard is monotone in the gap. The zero-gap leg therefore MUST prepay
    # faster, the Danish trapped balance MUST come in lower, and the gap MUST
    # be positive -- at every sweep point, since extra refinance-in-place only
    # adds Danish prepayment. The positivity and its sweep-robustness are
    # forced by construction. What is NOT forced is the magnitude, and the
    # bracketing Danish-LEVEL anchor flips the sign outright. This gate binds
    # (i) the forcedness PREMISE by recomputing the out-of-the-money exposure
    # share from the panel rather than trusting the prose, (ii) the sign
    # robustness by DERIVING every sweep gap from the two trapped balances
    # instead of reading sweep_sign_robust, (iii) the trapped LEVELS, not only
    # the gap between them, so the two anchors cannot be moved together, (iv)
    # the FLIP against an independently produced artifact, and (v) the
    # disclosure itself: every "positive at every" sentence in the manuscript
    # must sit next to a statement of why the check cannot fail.
    dui = json.loads(DANUSINT_RESULTS.read_text())
    rfs = json.loads(REFISWEEP_RESULTS.read_text())
    _shl = json.loads(SHAREDLAYER_RESULTS.read_text())
    _pt = dui["point"]
    dn_us_b, dn_dk_b = _pt["us_trapped_shared_b"], _pt["danish_trapped_shared_b"]
    dn_gap_b = dn_us_b - dn_dk_b                       # DERIVED, not read
    dn_sweep_gaps = [dn_us_b - s["danish_trapped_shared_b"] for s in dui["sweep"]]
    dn_dk_path = [s["danish_trapped_shared_b"] for s in dui["sweep"]]
    dn_forced_ok = (
        abs(dn_gap_b - _pt["institutional_gap_shared_b"]) < 1e-6
        and all(g > 0 for g in dn_sweep_gaps)
        # the sweep can only ADD Danish prepayment, which is what makes the
        # sign-robustness mechanical rather than evidential
        and all(dn_dk_path[i] > dn_dk_path[i + 1] for i in range(len(dn_dk_path) - 1))
        and dn_dk_b < dn_us_b
        and "AT ZERO RATE GAP" in dui["spec"].upper()
        # the U.S. anchor LEVEL, not merely the gap, is tied to an
        # independently produced artifact (shared_layer_scoring writes the same
        # Path B central trapped balance) and to the dollar benchmark. Binding
        # only the difference let perturbation P7 slide both anchors together
        # by $0.04B -- under the manuscript's printing precision -- undetected,
        # which is the defect gate #60 originally carried.
        and abs(dn_us_b - _shl["results"]["path_b_central"]["us_trapped_b"]) < 1e-9
        and abs(_pt["us_share_shared_pct"] - dn_us_b / _bench * 100.0) < 1e-9
        and abs(dn_dk_b - (dn_us_b - _pt["institutional_gap_shared_b"])) < 1e-9
        and all(abs(s["gap_hybrid_us_intercept_b"]
                    - (dn_us_b - s["danish_trapped_shared_b"])) < 1e-9
                for s in dui["sweep"])
    )
    # the premise: the U.S. book really is out of the money almost everywhere.
    # Recomputed from the panel against sign_forcing_stats' own committed
    # thresholds, so §VIII's "97.40%" cannot drift out from under the argument.
    _sfs = json.loads(SIGNSTATS_RESULTS.read_text())
    _wmin = _sfs["statistics"]["window_min_mortgage30us_pct"]
    _qw = _mp[(_mp._rp >= 202206) & (_mp._rp <= 202511)]
    _qtot = float(_qw.exposure_upb.sum())
    # The premise is "below the WINDOW MINIMUM", so cut at _wmin -- not at
    # printed_thresholds_pct[0] (=4.79), which is a strictly TIGHTER cut and
    # yields 97.40%. Binding the tighter value here enforced a mislabel in the
    # manuscript rather than catching it.
    dn_otm_share = float(_qw[_qw.coupon <= _wmin / 100.0]
                         .exposure_upb.sum()) / _qtot * 100.0
    dn_premise_ok = (
        dn_otm_share > 90.0
        # tie to the field that MATCHES the cut: the window-minimum share, not
        # the tighter 4.79 share (97.40%), which is what produced the mislabel
        and abs(dn_otm_share
                - _sfs["supplementary"]["exposure_share_le_window_min_pct"]) <= 1e-6
        and _wmin > _sfs["printed_thresholds_pct"][0]
    )
    # the FLIP, read from a different module's artifact
    _lvl = [s for s in rfs["sweep"]
            if s["refi_inplace_cpr"] == rfs["best_estimate_refi"]][0]["gap_pathB_b"]
    dn_flip_ok = (_lvl < 0 < dn_gap_b) and rfs["breakeven_refi"]["path_b"] > 0
    _oos_point = _oos["headline_oos_marginal"]["clean_marginal_b_point_at_6.5"]
    dn_lits = {
        "trapped_levels":
            f"\\${dn_dk_b:.1f} billion against \\${dn_us_b:.1f} billion" in tex,
        "gap_and_share":
            (f"$+\\${dn_gap_b:.1f}$ billion "
             f"({dn_gap_b / _bench * 100:.1f}\\% of the benchmark)") in tex,
        "sweep_ceiling":
            f"$+\\${max(dn_sweep_gaps):,.1f}$ billion".replace(",", "{,}") in tex,
        "danish_level_flip": f"$-\\${abs(_lvl):.1f}$ billion" in tex,
        "breakeven": f"{rfs['breakeven_refi']['path_b'] * 100:.1f}\\% CPR" in tex,
        "mean_cprs": (f"{_pt['mean_danish_cpr_pct']:.2f}\\%" in tex
                      and f"{_pt['mean_us_cpr_pct']:.2f}\\%" in tex),
        "otm_premise": f"{dn_otm_share:.2f}\\% of exposure below the window-minimum" in tex,
        # the equality with the lock-in marginal held only against the DEMOTED
        # in-sample point; against the headline the Danish gap is 44% larger
        "vs_headline": f"{(dn_gap_b / _oos_point - 1) * 100:.0f}\\% larger" in tex,
        "forcedness_stated": "could not have come out otherwise" in tex,
        "magnitude_is_the_content": "What is not forced is the magnitude" in tex,
        # ROUND-23: was an ORDERING check on the abstract (the flip had to be
        # stated before the forced positive). The Danish counterfactual left the
        # 263-word abstract, so the protection moves to the first place a reader
        # now meets the gap: the introduction. Ordering alone would be the wrong
        # relocation -- the intro's paragraph is long and a reader does not skim
        # it the way they skim an abstract -- so this binds the stronger
        # property instead: the paragraph that first states the positive gap must
        # ALSO carry the forcedness statement and the sign flip. It cannot be
        # satisfied by disclosing them a section later.
        "intro_para_carries_forcedness_and_flip": any(
            ("$+\\$61.2$ billion" in _para
             and "forced rather than found" in _para
             and "$-\\$99.9$ billion" in _para)
            for _para in tex.split("\n")
            if "$+\\$61.2$ billion" in _para) and (
            # and the first mention anywhere is that same paragraph
            next(_p for _p in tex.split("\n") if "$+\\$61.2$ billion" in _p)
            .find("forced rather than found") > 0),
        # and Table 1, where a reader meets the number, must carry it too
        "table1_disclosed": (
            "positivity is forced by the zero-gap anchor, so the refinancing "
            "sweep cannot flip it; the Danish-level bracketing anchor does, at "
            f"$-\\${abs(_lvl):.1f}$ billion") in tex,
    }
    # CONTEXTUAL: no "positive at every ..." sentence anywhere in the paper may
    # stand without a statement of why the check cannot fail. This is what stops
    # the relabel from being quietly undone one site at a time.
    _forced_markers = (
        "forced by construction", "forced by the zero-gap anchor",
        "cannot be overturned by this sweep", "cannot let fail",
        "verifies the specification", "checks the specification",
    )
    dn_unqualified = []
    _s = 0
    while (_i := tex.find("positive at every", _s)) != -1:
        _win = tex[max(0, _i - 450): _i + 450]
        if not any(m in _win for m in _forced_markers):
            dn_unqualified.append(_i)
        _s = _i + 1
    # ROUND-23: was >= 7. The abstract's instance left with the claim it
    # qualified -- the 263-word abstract no longer says the margin is positive at
    # every combination, so it no longer needs to say that check is forced. The
    # REAL protection here is dn_unqualified (no unqualified instance anywhere),
    # which is untouched; this count is a completeness proxy and 6 is the new
    # complete set.
    dn_context_ok = not dn_unqualified and tex.count("positive at every") >= 6
    dn_claims = tex.count("\\texttt{danish\\_us\\_intercept}")
    dn_ok = (dn_forced_ok and dn_premise_ok and dn_flip_ok and dn_context_ok
             and dn_claims >= 1 and all(dn_lits.values()))
    failures += 0 if dn_ok else 1
    print(
        f"[{'PASS' if dn_ok else 'FAIL'}] cross-check danish forced-positivity "
        f"relabel: forcedness-derived={dn_forced_ok} (gap ${dn_gap_b:.4f}B from "
        f"${dn_us_b:.4f}B - ${dn_dk_b:.4f}B; all {len(dn_sweep_gaps)} sweep gaps "
        f"positive; danish trapped monotone decreasing in refi), "
        f"otm-premise-recomputed={dn_premise_ok} ({dn_otm_share:.2f}% of exposure "
        f"<= {_sfs['printed_thresholds_pct'][0]:.2f}%, window min {_wmin:.4f}%), "
        f"flip-cross-read={dn_flip_ok} (danish-level anchor ${_lvl:.4f}B, "
        f"breakeven {rfs['breakeven_refi']['path_b'] * 100:.2f}% CPR), "
        f"no-unqualified-sweep-claims={dn_context_ok} "
        f"({tex.count('positive at every')} sites, {len(dn_unqualified)} unqualified), "
        f"danish-vs-headline +{(dn_gap_b / _oos_point - 1) * 100:.1f}%, "
        f"tex run-citation count={dn_claims} (want >=1), literals="
        f"{ {k: v for k, v in dn_lits.items() if not v} or 'all present'}"
    )

    # Round-20 (gate #67): the FANNIE ENVELOPE'S WIDTH. The pre-committed
    # acceptance envelope spans 11.06 points around a 9.20-point Freddie
    # estimate -- it would have accepted a replication 77% below or 43% above,
    # so its PASS is close to uninformative and the manuscript now says so.
    # The AGREEMENT is a different matter and is not being retracted: 17.6M
    # staged Fannie loans landing 0.52 points from the Freddie point is real
    # evidence. This gate binds the width and the tolerances so the disclosure
    # cannot be dropped, and pins the Freddie reference the agreement is
    # measured against to the INDEPENDENT committed sweep, so the agreement
    # cannot be improved by moving the thing it is measured from.
    _fan = json.loads(FANNIE_RESULTS.read_text())
    _env = _fan["gates"]["gate_envelope"]
    _pf = _fan["gates"]["parity_freddie"]
    # PINNED ex ante. The envelope is the PRE-COMMITMENT the replication was
    # judged against, so reading its edges out of the artifact that reports the
    # verdict would let a rerun move the goalposts and still print a PASS
    # (the defect gate #62 carried). Perturbation P9 narrowed the box to
    # [8.0, 9.5] -- i.e. manufactured an informative-looking gate after the
    # fact -- and only the manuscript literal caught it.
    FN_BOX = (2.113539257759882, 13.17046899604594)
    fn_box_pinned_ok = (abs(_env["box_min"] - FN_BOX[0]) < 1e-12
                        and abs(_env["box_max"] - FN_BOX[1]) < 1e-12)
    fn_width = FN_BOX[1] - FN_BOX[0]
    fn_fred_pp = (_pf["central_trapped_b"]["got"]
                  - _pf["null_trapped_b"]["got"]) / _bench * 100.0
    _sw4 = [r for r in _sw["rows"] if r["floor_annual_cpr_pct"] == 4.0][0]
    fn_ref_ok = abs(fn_fred_pp - _sw4["lockin_marginal_share_pp"]) < 1e-9
    # DERIVED from the Fannie leg's own trapped balances, never read from
    # lockin_marginal_share_pp: perturbation P8 moved central_trapped_b by
    # $20B and left the stored marginal alone, and the gate passed because it
    # trusted the summary.
    _fpb = _fan["path_b"]
    fn_fannie_b = _fpb["central_trapped_b"] - _fpb["null_trapped_b"]
    fn_fannie_pp = fn_fannie_b / _bench * 100.0
    fn_internal_ok = (
        abs(_fpb["lockin_marginal_b"] - fn_fannie_b) < 1e-6
        and abs(_fpb["lockin_marginal_share_pp"] - fn_fannie_pp) < 1e-9
        and abs(_fpb["central_share_pct"]
                - _fpb["central_trapped_b"] / _bench * 100.0) < 1e-9
        and abs(_fpb["null_share_pct"]
                - _fpb["null_trapped_b"] / _bench * 100.0) < 1e-9
        and abs(_env["marginal_pp"] - fn_fannie_pp) < 1e-9
        # in_envelope is RE-ADJUDICATED here against the pinned box
        and bool(_env["in_envelope"]) == (FN_BOX[0] <= fn_fannie_pp <= FN_BOX[1])
    )
    fn_agree = abs(fn_fred_pp - fn_fannie_pp)
    fn_low = (fn_fred_pp - _env["box_min"]) / fn_fred_pp * 100.0
    fn_high = (_env["box_max"] - fn_fred_pp) / fn_fred_pp * 100.0
    # the relabel is only honest if the gate really is this loose AND the
    # agreement really is this tight; both are asserted, not just printed.
    fn_shape_ok = (fn_width > 10.0 and fn_agree < 1.0 and bool(_env["in_envelope"])
                   and bool(_env["pass"]) and fn_fannie_pp > 0)
    fn_lits = {
        "envelope_box": f"{_env['box_min']:.2f} to {_env['box_max']:.2f} points" in tex,
        "envelope_width": f"{fn_width:.2f}-point window" in tex,
        "tolerances": f"{fn_low:.0f}\\% below it or {fn_high:.0f}\\% above" in tex,
        "agreement": f"{fn_agree:.2f} points from the Freddie point" in tex,
        "staged": f"{_fan['universe']['staged_loans_total'] / 1e6:.1f} million" in tex,
        "gate_disowned": "I do not treat its passing as evidence" in tex,
        "agreement_kept": "is the part of this exercise that is reassuring" in tex,
    }
    # the width disclosure must travel with the claim: §VII.B, the limitations
    # section, and the conclusion each quote the number where a reader meets it.
    fn_sites = tex.count(f"{fn_width:.2f}")
    fn_ok = (fn_ref_ok and fn_shape_ok and fn_box_pinned_ok and fn_internal_ok
             and fn_sites >= 3 and all(fn_lits.values()))
    failures += 0 if fn_ok else 1
    print(
        f"[{'PASS' if fn_ok else 'FAIL'}] cross-check fannie envelope width: "
        f"freddie-ref-cross-tied-to-sweep={fn_ref_ok} ({fn_fred_pp:.6f}pp derived "
        f"from parity rows), envelope [{_env['box_min']:.2f}, {_env['box_max']:.2f}] "
        f"= {fn_width:.2f}pp wide (accepts {fn_low:.0f}% low / {fn_high:.0f}% high, "
        f"box PINNED={fn_box_pinned_ok}), agreement {fn_agree:.4f}pp on "
        f"{_fan['universe']['staged_loans_total']:,} staged loans "
        f"(marginal DERIVED from trapped levels, internal-consistency="
        f"{fn_internal_ok}), gate-still-passes={fn_shape_ok}, "
        f"width disclosed at {fn_sites} sites "
        f"(want >=3), literals="
        f"{ {k: v for k, v in fn_lits.items() if not v} or 'all present'}"
    )

    # Round-20 (gate #68): the ABSTRACT'S HEDGES. See ABSTRACT_HEDGES above for
    # why this is scoped to the abstract environment and why the spans are
    # contiguous rather than proximity-windowed.
    # the rule lives in abstract_hedge_check() so tests exercise it, not a copy
    ab_ok, _ab = abstract_hedge_check(tex)
    failures += 0 if ab_ok else 1
    print(
        f"[{'PASS' if ab_ok else 'FAIL'}] abstract-hedge spans: "
        f"abstract-located={_ab['found']} ({_ab['words']} words, "
        f"scoped-not-whole-file={_ab['scoped']}), "
        f"{_ab['total'] - len(_ab['missing'])}/{_ab['total']} abstract spans "
        f"present, missing={_ab['missing'] or 'none'}; "
        f"{_ab['total_body'] - len(_ab['missing_body'])}/{_ab['total_body']} "
        f"relocated body spans present, "
        f"missing_body={_ab['missing_body'] or 'none'}"
    )

    # ROUND 22 (C4): the same rule, applied to EVERY manuscript variant on disk.
    # See TEX_VARIANTS. A variant that is not the canonical file is still a
    # variant someone can compile and submit, and the short-abstract variant that
    # motivated this failed 5 of 8 spans while the suite reported ALL GATES PASS.
    # ROUND-22, second pass: checking the variant's ABSTRACT was not enough. The
    # short-abstract file was a Jul-23 copy whose BODY then went stale by 291
    # lines while round 22 corrected the canonical manuscript -- so it passed
    # this gate while still carrying the false fig:gapsweep caption, the
    # mislabelled discount table and every other defect the round repaired. A
    # variant must therefore differ from the canonical file in the ABSTRACT LINE
    # ONLY; anything else means it has drifted and must be regenerated.
    _canon_lines = TEX.read_text().split("\n")
    var_bad = []
    for _p in TEX_VARIANTS:
        if _p == TEX:
            continue
        _txt = _p.read_text()
        _v_ok, _v = abstract_hedge_check(_txt)
        if not _v_ok:
            var_bad.append(f"{_p.name}: hedges {_v['missing'] or 'unscoped'}")
        _vl = _txt.split("\n")
        if len(_vl) != len(_canon_lines):
            var_bad.append(f"{_p.name}: body drift ({len(_vl)} lines vs "
                           f"{len(_canon_lines)} canonical)")
        else:
            _diff = [i + 1 for i in range(len(_vl)) if _vl[i] != _canon_lines[i]]
            _non_abstract = [n for n in _diff if _canon_lines[n - 1].strip()[:9] != "\\noindent"]
            if _non_abstract:
                var_bad.append(f"{_p.name}: body drift at lines "
                               f"{_non_abstract[:8]}{'…' if len(_non_abstract) > 8 else ''}")
    var_ok = not var_bad
    failures += 0 if var_ok else 1
    print(
        f"[{'PASS' if var_ok else 'FAIL'}] abstract-hedge spans, non-canonical "
        f"variants: {len(TEX_VARIANTS) - 1} checked, "
        f"failing={var_bad or 'none'}"
    )

    # ------------------------------------------------------------------
    # Round-21 (gate #69): FORM-CONDITIONAL HEADLINE. floor_form_offwindow ran
    # the additive floor form at the committed off-window clean-band anchors;
    # its T1 verdict (additive marginal within 0.06pp of its production-floor
    # value) means the +9.2->+5.6 demotion is max-form censoring mechanics, so
    # the manuscript must carry the form-conditional hull wherever the
    # headline marginal is quoted. This gate pins the artifact (parity pass +
    # T1 + the hull endpoints) and requires the tex literals.
    HAZ_DATA = ROOT / "hazard" / "data"
    ffo = json.loads((HAZ_DATA / "floor_form_offwindow_results.json").read_text())
    ffo_ok = (ffo["parity_gates_all_pass"] and ffo["t1_form_conditional_demotion"]
              and abs(ffo["designated_interval_pp"][0] - 3.891507360127463) < 1e-9
              and abs(ffo["designated_interval_pp"][1] - 13.09774126267503) < 1e-9)
    # ROUND-23: the designated hull MOVED. floor_form_offwindow's
    # designated_interval_pp [3.8915, 13.0977] is still correct for what that
    # run measured -- the LOG-LINEAR transform -- and is still pinned above.
    # But concave_hull_band_ends closed the concave transform over the same
    # off-window floor x band grid and one cell (max form, 5.334% floor, band
    # 5.5) came in at +3.5294pp, below that lower edge. The published hull is
    # therefore the union over all 36 off-window cells, and the tex literal
    # that must be present is the WIDENED one. Pinning the old literal here
    # would now pin a superseded number.
    ffo_tex_ok = (tex.count("$+3.5$ to $+13.1$") >= 3
                  and tex.count("$+3.9$ to $+13.1$") == 0
                  and "floor\\_form\\_offwindow" in tex
                  and tex.count("form-conditional") >= 3)
    ok = ffo_ok and ffo_tex_ok
    failures += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] cross-check form-conditional headline: "
          f"artifact parity+T1={ffo_ok} (hull [{ffo['designated_interval_pp'][0]:.4f}, "
          f"{ffo['designated_interval_pp'][1]:.4f}]pp), tex hull-count="
          f"{tex.count('$+3.5$ to $+13.1$')} (want >=3, widened by "
          f"concave_hull_band_ends), run-tag="
          f"{'floor_form_offwindow' if ffo_tex_ok else 'MISSING'}")

    # Round-21 (gate #70): CONCAVE MARGINAL. concave_marginal ran the paired
    # legs under the concave transform (never run before); T1 verdict: the
    # transform moves the marginal past the +/-1pp materiality convention, so
    # "not load-bearing" must stay scoped to the level in the tex.
    cm = json.loads((HAZ_DATA / "concave_marginal_results.json").read_text())
    cm_ok = (cm["parity_gates_all_pass"] and cm["t1_load_bearing"]
             and abs(cm["concave_marginal_pp_at_4"] - 7.8741354244354085) < 1e-9
             and abs(cm["concave_marginal_pp_at_offwindow_point"] - 5.056147332383432) < 1e-9)
    cm_tex_ok = ("not load-bearing for the level" in tex
                 and "$+7.87$" in tex and "$+5.06$" in tex
                 and "concave\\_marginal" in tex)
    ok = cm_ok and cm_tex_ok
    failures += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] cross-check concave marginal: "
          f"artifact parity+T1={cm_ok} (+{cm['concave_marginal_pp_at_4']:.4f}pp @4%, "
          f"+{cm['concave_marginal_pp_at_offwindow_point']:.4f}pp @4.991%), "
          f"tex literals={'ok' if cm_tex_ok else 'MISSING'}")

    # ITEM 7d (gate #86): OUT-OF-AGENCY FLOOR READ. The floor is the binding
    # parameter and was read off one agency. The Fannie read lands at 5.52% --
    # ABOVE the clean band's 5.334% top and 0.01pp from the age-standardised
    # Freddie read of 5.508%. This gate pins the T2 verdict and the Freddie
    # parity that makes it meaningful, because the tempting later edit is to
    # present 5.52% as "close to" the band rather than outside it.
    ffr = json.loads((HAZ_DATA / "fannie_floor_read_results.json").read_text())
    ffr_c = ffr["comparison"]
    ffr_ok = (ffr["parity_gates_all_pass"]
              and ffr["verdict"] == "T2"
              and ffr_c["fannie_inside_clean_band"] is False
              and abs(ffr_c["fannie_headline_cpr_pct"] - 5.522) < 1e-6
              and abs(ffr_c["freddie_headline_cpr_pct"] - 5.185) < 1e-6
              and ffr_c["fannie_headline_n"] >= 30)
    ffr_tex_ok = ("fannie\\_floor\\_read" in tex
                  and "5.52\\%" in tex
                  and "above the clean band" in tex)
    ok = ffr_ok and ffr_tex_ok
    failures += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] cross-check out-of-agency floor read: "
          f"artifact={ffr_ok} (fannie {ffr_c['fannie_headline_cpr_pct']}% vs "
          f"freddie {ffr_c['freddie_headline_cpr_pct']}%, inside clean band="
          f"{ffr_c['fannie_inside_clean_band']}, {ffr['verdict']}), "
          f"tex literals={'ok' if ffr_tex_ok else 'MISSING'}")

    # ITEM 7b (gate #87): CURTAILMENT DIFFERENTIAL ON THE PRODUCTION LEG. The
    # committed +$0.77B was measured on the dk_level BRACKETING cache. On the
    # production us_intercept leg it reverses to -$1.68B and crosses the $1B
    # materiality threshold, so the "immaterial throughout" claim is withdrawn.
    # Pinned because the withdrawal is the fragile part: the +$0.77B figure is
    # still in the paper (correctly attributed) and could easily be re-promoted.
    cds = json.loads((HAZ_DATA
                      / "curtailment_danish_scaling_us_intercept_results.json").read_text())
    cds_runs = {r["scale"]: r for r in cds["runs"]} if "runs" in cds else {}
    cds_unit = cds_runs.get(1.0, {})
    cds_ok = (abs(cds_unit.get("curtailment_differential_b", 0.0)
                  - (-1.6801)) < 5e-3)
    cds_tex_ok = ("$-\\$1.68$" in tex
                  and "Danish-level bracketing} leg" in tex
                  and "withdraw the claim that the curtailment differential is immaterial" in tex)
    ok = cds_ok and cds_tex_ok
    failures += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] cross-check curtailment differential on "
          f"production leg: artifact={cds_ok} "
          f"(unit-scale differential "
          f"{cds_unit.get('curtailment_differential_b', float('nan')):+.4f}B), "
          f"tex literals={'ok' if cds_tex_ok else 'MISSING'}")

    # ROUND-22 (gate #85): PRODUCTION-SPEC SCALE TEST. VII.A's original check ran
    # the household mechanic in isolation at 15.616% mean CPR against the
    # production ABM's 11.761 -- 3.9 points hot -- with no script, artifact or
    # gate anywhere in the repo. The rerun carries the full production spec. Its
    # FIRST execution halted at the committed-CSV parity tier on uniform FRED
    # drift; rather than widen that tolerance (the move round-22 C1 retracts
    # elsewhere) a second pre-commitment gates the per-seed SPREAD of the drift
    # while only reporting its level. This gate pins that distinction, because
    # the tempting simplification is to drop it and quietly re-point parity.
    pst = json.loads((ROOT / "abm" / "data"
                      / "production_scale_test_results.json").read_text())
    pst_g = pst["gates"]
    pst_ok = (pst.get("status") == "OK"
              and pst.get("verdict_tier") == "T1"
              and bool(pst_g["G2b_fresh_baseline_drift_uniform"]["pass"])
              and bool(pst_g["G0e_benchmark_bitexact"]["pass"])
              and bool(pst_g["G1b_intra_run_determinism"]["pass"])
              and bool(pst_g["G3_floor_retention"]["pass"]))
    pst_tex_ok = ("production\\_scale\\_test" in tex
                  and "12.66\\%" in tex and "12.18\\%" in tex
                  and "15.6\\%" in tex)
    ok = pst_ok and pst_tex_ok
    failures += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] cross-check production scale test: "
          f"artifact={pst_ok} (status {pst.get('status')}, "
          f"{pst.get('verdict_tier')}, fresh-baseline drift uniform), "
          f"tex literals={'ok' if pst_tex_ok else 'MISSING'}")

    # ROUND-22 (gate #84): PATH B STRATUM-CLUSTER BOOTSTRAP. The committed
    # within-stratum scheme holds the 130 strata fixed, so between-stratum
    # composition variance was never drawn and the paper reported that the loan
    # draw "contributes essentially no uncertainty". Drawing the strata widens
    # the marginal interval by 36.9x. The verdict is still T1 -- the floor read
    # remains the binding layer -- so what this gate protects is the RETRACTION:
    # the 37x understatement and the effective-cluster caveat are the parts an
    # editor would most plausibly trim as technical detail.
    bpc = json.loads((HAZ_DATA / "bootstrap_pathb_cluster_results.json").read_text())
    bpc_m = bpc["marginal_pp"]
    bpc_c = bpc["comparison"]
    bpc_ok = (bpc["parity_gates_all_pass"]
              and bpc["verdict"] == "T1"
              and bpc["n_reps"] == 200
              and abs(bpc_m["p2_5"] - 4.630919609903703) < 1e-6
              and abs(bpc_m["p97_5"] - 6.924433300615744) < 1e-6
              # the floor read must remain the binding layer (ratio < 0.5)
              and bpc_c["width_ratio_vs_floor_read"] < 0.5
              # the understatement is the finding; guard its order of magnitude
              and bpc_c["R1_width_ratio_vs_within_stratum"] > 20.0
              and bpc_c["R2_committed_point_inside"] is True
              and abs(bpc["cluster_structure"]["effective_n_clusters"]
                      - 25.77710660741266) < 1e-6)
    bpc_tex_ok = ("bootstrap\\_pathb\\_cluster" in tex
                  and "$[+4.63, +6.92]$" in tex
                  and "factor of $37$" in tex
                  and "25.8" in tex)
    ok = bpc_ok and bpc_tex_ok
    failures += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] cross-check Path B cluster bootstrap: "
          f"artifact={bpc_ok} (marginal [{bpc_m['p2_5']:+.4f}, {bpc_m['p97_5']:+.4f}]pp, "
          f"width ratio vs floor-read {bpc_c['width_ratio_vs_floor_read']:.3f}, "
          f"vs within-stratum {bpc_c['R1_width_ratio_vs_within_stratum']:.1f}x, "
          f"{bpc['verdict']}), tex literals={'ok' if bpc_tex_ok else 'MISSING'}")

    # ROUND-22 (gate #83): CROSS-DESIGN SEED SWEEP. Every cross-design number in
    # the paper was a single seed-42 draw, and the paper crosses its own
    # pre-committed 50% threshold with it. The 50-seed sweep VINDICATES the
    # reading (mean 60.2%, all 50 seeds undercutting, committed draw at the 48th
    # percentile), so what this gate protects is the DISCLOSURE: the band is wide
    # enough that S1b required reporting it, and a compression pass that drops
    # "60.2" or the band would put the paper back to asserting a threshold
    # crossing from one draw.
    cds = json.loads((ROOT / "abm" / "data" / "cross_design_seeds_results.json").read_text())
    cds_rec = cds["distributions"]["A_joint.recalibrated"]
    cds_ok = (cds["parity_gates_all_pass"]
              and cds_rec["n"] == 50
              and abs(cds_rec["mean_pct"] - 60.20801984127922) < 1e-9
              and abs(cds_rec["sd_pct"] - 3.30918815316194) < 1e-9
              and abs(cds_rec["percentiles_pct"]["p2.5"] - 55.09710819371802) < 1e-9
              and abs(cds_rec["percentiles_pct"]["p97.5"] - 66.04559875123523) < 1e-9
              # the whole point: the verdict must not depend on the seed
              and cds_rec["mean_pct"] >= 50.0)
    cds_602_count = tex.count("60.2\\%")
    cds_tex_ok = ("cross\\_design\\_seeds" in tex
                  and cds_602_count >= 3
                  and "55.1--66.0\\%" in tex)
    ok = cds_ok and cds_tex_ok
    failures += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] cross-check cross-design seed sweep: "
          f"artifact={cds_ok} (n={cds_rec['n']}, mean {cds_rec['mean_pct']:.3f}%, "
          f"sd {cds_rec['sd_pct']:.3f}pp, band "
          f"{cds_rec['percentiles_pct']['p2.5']:.1f}-"
          f"{cds_rec['percentiles_pct']['p97.5']:.1f}%), tex 60.2-count="
          f"{cds_602_count} (want >=3), literals="
          f"{'ok' if cds_tex_ok else 'MISSING'}")

    # ROUND-22 (gate #82): BURNOUT ABLATION. The manuscript quoted this ablation
    # at four sites with NO artifact, NO script and NO gate; the three printed
    # literals reproduced the MINIMUM over 100 replicates of
    # permutation_test_ablate_orig, an experiment that permutes origination time.
    # The real run lands within 0.02B of the claim -- the number was right by
    # coincidence -- so the gate pins the ARTIFACT and the two facts the run
    # added, not merely the surviving literal.
    ba = json.loads((HAZ_DATA / "burnout_ablation_results.json").read_text())
    ba_prod = ba["ablation_at_production_floor"]
    ba_off = ba["ablation_at_offwindow_floor"]
    ba_ok = (ba["parity_gates_all_pass"]
             and ba["t1_manuscript_literal_stands"]
             # the forensic identification must stay in the artifact: this is the
             # only record of WHERE the original number came from
             and abs(ba["provenance_audit"]["perm_min_trapped_b"]
                     - 811.911646619444) < 1e-9
             and abs(ba_prod["delta_pp"] - (-0.8607272887573743)) < 1e-9
             and abs(ba_off["delta_pp"] - (-0.4547025015657056)) < 1e-9)
    ba_tex_ok = ("burnout\\_ablation" in tex
                 and "$-0.86$pp" in tex and "$-0.45$pp" in tex
                 # the calibration mismatch the run exposed must stay disclosed
                 and "68.8\\%" in tex)
    ok = ba_ok and ba_tex_ok
    failures += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] cross-check burnout ablation: "
          f"artifact={ba_ok} ({ba_prod['delta_pp']:+.4f}pp @4.0%, "
          f"{ba_off['delta_pp']:+.4f}pp @4.991%, T1="
          f"{ba['t1_manuscript_literal_stands']}), tex literals="
          f"{'ok' if ba_tex_ok else 'MISSING'}")

    # ROUND-22 (gate #81): CONCAVE x ADDITIVE JOINT CELL. The hull was a hull
    # over floor FORMS at the log-linear transform only, and tab:uncertainty
    # listed "additive form +11.2" and "concave transform +5.1" as parallel
    # entries -- which presumes they add. The joint cell says they do not: the
    # interaction is -1.47pp at the headline anchor, past the project's own
    # +/-1.0pp convention. The hull itself survives (T1), so this gate pins the
    # SEPARABILITY REFUTATION, which is the part a compression pass would lose:
    # the two entries could easily be re-separated by an editor who reads them
    # as independent, and nothing else in the suite would notice.
    caj = json.loads((HAZ_DATA / "concave_additive_marginal_results.json").read_text())
    caj_ok = (caj["parity_gates_all_pass"]
              and caj["t1_hull_stands"]
              # separability must remain REFUTED-as-measured, not None (T3) and
              # not silently flipped to True by a re-run on different inputs
              and caj["s1_separable"] is False
              and abs(caj["interaction"]["4991"]["interaction_pp"]
                      - (-1.4697431160061782)) < 1e-9
              and caj["interaction"]["4991"]["material"] is True)
    caj_tex_ok = ("concave\\_additive\\_marginal" in tex
                  and "$+9.25$" in tex and "$+9.22$" in tex
                  and "an interaction of $-1.47$ points" in tex
                  and "do not add" in tex)
    ok = caj_ok and caj_tex_ok
    failures += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] cross-check concave x additive joint cell: "
          f"artifact={caj_ok} (T1 hull stands, +"
          f"{caj['interaction']['4']['interaction_pp']:+.4f}/"
          f"{caj['interaction']['4991']['interaction_pp']:+.4f}pp interaction, "
          f"separable={caj['s1_separable']}), tex literals="
          f"{'ok' if caj_tex_ok else 'MISSING'}")

    # Round-21 (gate #71): DANISH GAP AT THE HEADLINE FLOOR. The rule-only
    # (us_intercept) gap now exists at the off-window floor: +$28.20B, 0.662x
    # the off-window marginal. The tex must quote it beside the in-sample
    # +$61.2B wherever the Danish figure appears at headline level, and the
    # abstract's Danish sentence must carry both calibration labels.
    dof = json.loads((HAZ_DATA / "danish_offwindow_floor_results.json").read_text())
    dof_ok = (dof["parity_gates_all_pass"]
              and abs(dof["rule_only_gap_offwindow_shared_b"] - 28.204687540179634) < 1e-6
              and abs(dof["gap_over_offwindow_marginal"] - 0.6619514365853162) < 1e-9)
    dof_count_282 = tex.count("$+\\$28.2$ billion")
    # ROUND-23: was the abstract's "$+\\$28$ billion at the off-window
    # calibration". The Danish counterfactual left the abstract, so the label is
    # bound to the body sentence that states the same gap against the same
    # marginal (VII.F and the Conclusion both carry it).
    dof_abs_label = ("the rule-only gap is $+\\$28.2$ billion, 34\\% below "
                     "that marginal") in tex
    dof_runtag = "danish\\_offwindow\\_floor" in tex
    dof_tex_ok = dof_count_282 >= 2 and dof_runtag and dof_abs_label
    ok = dof_ok and dof_tex_ok
    failures += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] cross-check danish offwindow gap: "
          f"artifact parity={dof_ok} (gap ${dof['rule_only_gap_offwindow_shared_b']:.2f}B, "
          f"ratio {dof['gap_over_offwindow_marginal']:.3f}), tex 28.2-count="
          f"{dof_count_282} (want >=2), abstract label="
          f"{'ok' if dof_abs_label else 'MISSING'}")

    # Round-21 (gate #72): GINNIE OVERLAY AT THE HEADLINE FLOOR. The overlay x
    # off-window cell exists; the marginal correction is pure conventional-
    # share scaling (0.7975x), series-independent. The tex must carry the
    # overlay pair beside the headline marginal.
    gof = json.loads((HAZ_DATA / "ginnie_overlay_offwindow_results.json").read_text())
    gof_ok = (abs(gof["overlay_offwindow"]["primary"]["marginal_pp"] - 4.443419164229439) < 1e-9
              and abs(gof["marginal_scale_vs_conventional"] - 0.7975182199226121) < 1e-9
              and all(v["pass"] for v in gof["parity_gates"].values()))
    gof_tex_ok = ("ginnie\\_overlay\\_offwindow" in tex
                  and "$+4.4$-point marginal" in tex
                  and "overlay-scored member" in tex)
    ok = gof_ok and gof_tex_ok
    failures += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] cross-check ginnie overlay offwindow: "
          f"artifact={gof_ok} (marginal +{gof['overlay_offwindow']['primary']['marginal_pp']:.4f}pp, "
          f"scale {gof['marginal_scale_vs_conventional']:.4f}), tex literals="
          f"{'ok' if gof_tex_ok else 'MISSING'}")


    # Round-21 (gate #73): FLOOR UNCERTAINTY. floor_uncertainty bootstrapped
    # every floor read (cluster = 4-way strata) and age-standardized the
    # off-window floor. Verdicts: the BINDING uncertainty on the off-window
    # marginal is the floor's sampling error (95% CI [+2.97, +8.02]pp, wider
    # than the depth-cut band), and the age-standardized floor (5.508%, 84.0%
    # imputed weight) sits above the clean band top, so the band is open
    # below +4.3. The tex must carry the sampling CI, the binding-layer
    # relabel of Table 8, and the open-below statement.
    fu = json.loads((HAZ_DATA / "floor_uncertainty_results.json").read_text())
    fu_mf4 = fu["part_a_sampling_uncertainty"]["mf4_binding_uncertainty"]
    fu_pb = fu["part_b_age_standardization"]
    fu_ok = (fu["parity_gates_all_pass"]
             and fu_mf4["binding_uncertainty"] == "sampling"
             and abs(fu_mf4["sampling_ci95_pp"][0] - 2.974329560125351) < 1e-9
             and abs(fu_mf4["sampling_ci95_pp"][1] - 8.01850965353176) < 1e-9
             and abs(fu_pb["adjusted_floor_pct"] - 5.507748455937158) < 1e-9
             and abs(fu_pb["imputed_weight_share"] - 0.8398743947117693) < 1e-9)
    fu_tex_ok = (tex.count("$+3.0$ to $+8.0$") >= 2
                 and tex.count("$+2.9$ to $+8.7$") >= 4
                 and "floor\\_uncertainty" in tex
                 and "floor\\_inference\\_correction" in tex
                 and "open below $+4.3$" in tex
                 and "binding layer" in tex
                 and "84.0\\% of weight imputed" in tex)
    ok = fu_ok and fu_tex_ok
    failures += 0 if ok else 1
    fu_count = tex.count("$+3.0$ to $+8.0$")
    print(f"[{'PASS' if ok else 'FAIL'}] cross-check floor uncertainty: "
          f"artifact={fu_ok} (binding={fu_mf4['binding_uncertainty']}, CI "
          f"[{fu_mf4['sampling_ci95_pp'][0]:.3f}, {fu_mf4['sampling_ci95_pp'][1]:.3f}]pp, "
          f"age-std {fu_pb['adjusted_floor_pct']:.3f}%), tex CI-count={fu_count} "
          f"(want >=2), literals={'ok' if fu_tex_ok else 'MISSING'}")


    # Round-21 (gate #74): PATH A SIGN TEST. patha_sign_test ran the
    # bias-respecting H0: beta_g <= 0 test the Table 6 note had deferred.
    # Verdict T3: no rejection under any construction (BCa 0.093/0.412,
    # permutation 0.241) -> the manuscript must not claim an in-sample sign,
    # "sign-triangulated" is retired, and the elasticity's evidential basis
    # is the external literature alone.
    pst = json.loads((HAZ_DATA / "patha_sign_test_results.json").read_text())
    pst_ok = (pst["parity_gates_all_pass"]
              and pst["verdict"]["branch"] == "T3"
              and abs(pst["verdict"]["p_bootstrap_stratum"] - 0.09281663473114488) < 1e-12
              and abs(pst["verdict"]["p_bootstrap_temporal"] - 0.41183595966445363) < 1e-12
              and abs(pst["verdict"]["p_permutation_primary"] - 0.24120603015075376) < 1e-12)
    pst_runtag = "patha\\_sign\\_test" in tex
    pst_tex_ok = (pst_runtag and tex.count("$p = 0.093$") >= 1
                  and "not statistically distinguishable from zero under bias-respecting" in tex
                  and "evidential basis is the external literature alone" in tex)
    pst_retired = "sign-triangulated by two in-sample estimates" not in tex
    ok = pst_ok and pst_tex_ok and pst_retired
    failures += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] cross-check Path A sign test: "
          f"artifact parity+T3={pst_ok} (p 0.093/0.412/0.241), tex literals="
          f"{'ok' if pst_tex_ok else 'MISSING'}, "
          f"'sign-triangulated' retired={pst_retired}")


    # Round-21 (gate #75): EPISODE CONFRONTATION. episode_confrontation ran
    # the cumulative cross-cohort gap-gradient test + power analysis. Verdict
    # T5 (ex-ante residual branch): realized gradient +4.198pp, CI
    # [+3.585, +4.656], permutation p 0.005 -- signed, significant, but
    # ~4.5x the model-implied +0.937pp, so a confound signature, not
    # corroboration; no abstract verb change. The tex must report the
    # exhibit with the confound reading and leave the timing nulls standing.
    ec = json.loads((HAZ_DATA / "episode_confrontation_results.json").read_text())
    ec_pa = ec["part_a"]["primary_age_matched"]
    ec_ok = (ec["parity_gates_all_pass"]
             and ec["verdict"]["branch"] == "T5"
             and abs(ec_pa["realized_gradient_pp"] - 4.198179219676357) < 1e-9
             and abs(ec_pa["gradient_bootstrap"]["ci95_pp"][0] - 3.5852591750975797) < 1e-9
             and abs(ec_pa["implied_gradient_pp"]["mid"] - 0.9371125522400376) < 1e-9
             and abs(ec["part_b"]["permutation"]["p_value_one_sided"] - 0.004975124378109453) < 1e-12
             and abs(ec["part_b"]["power_at_named_betas"]["mid"]["power_injected"] - 0.675) < 1e-9)
    ec_tex_ok = ("episode\\_confrontation" in tex
                 and "$+4.20$ CPR points" in tex
                 and "$[+3.59, +4.66]$" in tex
                 and "$+0.94$ points at the central" in tex
                 and "unusable as a measurement of its size" in tex
                 and "monthly-timing nulls above stand unchanged" in tex)
    ok = ec_ok and ec_tex_ok
    failures += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] cross-check episode confrontation: "
          f"artifact parity+T5={ec_ok} (gradient +{ec_pa['realized_gradient_pp']:.3f}pp, "
          f"implied +{ec_pa['implied_gradient_pp']['mid']:.3f}, perm p "
          f"{ec['part_b']['permutation']['p_value_one_sided']:.4f}, power "
          f"{ec['part_b']['power_at_named_betas']['mid']['power_injected']:.3f}), "
          f"tex literals={'ok' if ec_tex_ok else 'MISSING'}")

    # Round-21 (gate #76): CROSS-DESIGN COMPOSITION REWEIGHT. Verdict T1:
    # reweighting to the SOMA composition RAISES the recalibrated variant
    # (59.30 -> 76.34; re-draw 70.64) and lowers the frozen (20.86 -> 12.56;
    # re-draw 36.04): the mismatch understated the recovery, the undercut
    # verdict survives. The tex must quantify the component beside every
    # headline 59.3% and the "isolates" sentence must be gone.
    cdr = json.loads((ROOT / "abm" / "data" / "cross_design_reweight_results.json").read_text())
    cv = cdr["variants"]
    cdr_ok = (cdr["interpretive_threshold"]["band"] == "T1"
              and abs(cv["v1_recalibrated"]["share_pct"] - 59.30299434493775) < 1e-9
              and abs(cv["v3_reweighted_recalibrated"]["share_pct"] - 76.34415260068252) < 1e-6
              and abs(cv["v2_reweighted_frozen"]["share_pct"] - 12.561542534955805) < 1e-6
              and abs(cdr["v3_recalibrated_scale"] - 32187.5) < 1e-9)
    cdr_count = tex.count("76.3\\%")
    cdr_tex_ok = (cdr_count >= 4
                  and "cross\\_design\\_reweight" in tex
                  and "understated rather than manufactured" in tex
                  and "isolates the effect of real structural heterogeneity" not in tex)
    ok = cdr_ok and cdr_tex_ok
    failures += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] cross-check cross-design reweight: "
          f"artifact T1={cdr_ok} (V3 {cv['v3_reweighted_recalibrated']['share_pct']:.2f}%, "
          f"V2 {cv['v2_reweighted_frozen']['share_pct']:.2f}%, scale "
          f"{cdr['v3_recalibrated_scale']:.1f}), tex 76.3-count={cdr_count} "
          f"(want >=4), literals={'ok' if cdr_tex_ok else 'MISSING'}")

    # ROUND-23 (gate #94): NO ABM COUNTERPART TO THE beta_1 = 0 NULL.
    # The paper compares the ABM with Path B on LEVELS while insisting elsewhere
    # that levels do not identify. The reason is structural and must stay stated:
    # the ABM's turnover floor is not a term in its move rule, it is PRODUCED by
    # calibrating theta against the penalty-bearing rule, so zeroing the penalty
    # removes the floor with the channel. This gate pins the artifact's NON-EXISTENCE
    # conclusion and the two anchoring conventions that disagree in SIGN -- the sign
    # disagreement is the whole finding, so it is asserted, not just the magnitudes.
    # It also pins the honesty label: the probe carries no pre-committed threshold
    # (the candidates were executed while scoping), and the tex says so.
    anf = json.loads((ROOT / "abm" / "data"
                      / "abm_null_feasibility_results.json").read_text())
    anf_anchor = anf["floor_anchor_cpr_at_8pct"]
    anf_imp = anf["implied_marginal"]
    anf_ok = (anf["gates_all_pass"]
              and anf["conclusion"] == "NOT_FEASIBLE"
              # never let this be re-labelled as a pre-committed estimate
              and anf["pre_committed"] is False
              and anf["mode"] == "feasibility_probe"
              # central sits in the 4-5% floor band; the frozen null blows through it
              and 0.04 <= anf_anchor["central"] <= 0.05
              and anf_anchor["null_frozen"] > 0.30
              and 0.04 <= anf_anchor["null_reanchored"] <= 0.05
              # the finding: the two defensible conventions differ in SIGN
              and anf_imp["null_frozen"]["marginal_pp"] > 0
              > anf_imp["null_reanchored"]["marginal_pp"]
              # and neither is anywhere near an interpretable recovery level
              and anf["legs"]["null_frozen"]["share_explained_pct"] < -100.0
              and anf["legs"]["null_reanchored"]["share_explained_pct"] > 100.0)
    anf_tex_ok = ("abm\\_null\\_feasibility" in tex
                  and "$-259.4$\\%" in tex and "$+116.3$\\%" in tex
                  and "$+270.4$ and $-105.3$ points" in tex
                  # the structural reason, not just the numbers
                  and "admits no counterpart to the $\\beta_1 = 0$ null" in tex
                  and "they disagree in sign, and neither is interpretable" in tex
                  # the honesty label must travel with the citation
                  and "a feasibility probe, not a pre-committed estimate" in tex)
    ok = anf_ok and anf_tex_ok
    failures += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] cross-check ABM null feasibility: "
          f"artifact={anf_ok} ({anf['conclusion']}, anchor "
          f"{anf_anchor['central']:.4f}/{anf_anchor['null_frozen']:.4f}/"
          f"{anf_anchor['null_reanchored']:.4f}, implied "
          f"{anf_imp['null_frozen']['marginal_pp']:+.1f}pp vs "
          f"{anf_imp['null_reanchored']['marginal_pp']:+.1f}pp), tex literals="
          f"{'ok' if anf_tex_ok else 'MISSING'}")

    # ROUND-23 (gate #95): THE FORM x TRANSFORM HULL IS NOW CLOSED, AND IT WIDENED.
    # concave_hull_band_ends ran the concave transform's 16 unrun off-window
    # cells, taking the {form x transform} x {floor x band} product to 36 of 36.
    # T2 fired at exactly the corner its spec named ex ante: a downward-signed
    # transform, evaluated at the band's low edge and the highest defensible
    # floor, undercuts the log-linear lower edge. This gate pins the verdict,
    # the offending cell, and the fact that the UPPER edge did not move -- the
    # last of which is what stops anyone re-widening the top from this run.
    chb = json.loads((HAZ_DATA / "concave_hull_band_ends_results.json").read_text())
    chb_cells = chb["cells"]
    chb_low = chb["new_hull_pp_all_36_offwindow_cells"][0]
    chb_hi = chb["new_hull_pp_all_36_offwindow_cells"][1]
    chb_ok = (chb["parity_gates_all_pass"]
              and chb["pre_committed"] is True
              and chb["t2_hull_widens"] is True
              and chb["n_cells_outside_committed_hull"] == 1
              # the offending cell, named exactly
              and "max|5.334|5.5" in chb["cells_outside_committed_hull"]
              and abs(chb_cells["max|5.334|5.5"]["marginal_pp"]
                      - 3.5293843684633197) < 1e-6
              # the widened hull, and an unmoved upper edge
              and abs(chb_low - 3.5293843684633197) < 1e-6
              and abs(chb_hi - 13.09774126267503) < 1e-9
              # all 18 concave cells present, and the grid actually closed
              and len(chb_cells) == 18)
    chb_tex_ok = ("concave\\_hull\\_band\\_ends" in tex
                  and "$+3.53$ points" in tex
                  and "thirty-six of thirty-six" in tex
                  # the upper edge must stay explained, not silently retained
                  and "$+10.83$" in tex
                  # and the superseded framing must be gone
                  and "not shown \\emph{complete}" not in tex)
    ok = chb_ok and chb_tex_ok
    failures += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] cross-check concave hull band ends: "
          f"artifact={chb_ok} (T2, {chb['n_cells_outside_committed_hull']}/18 outside, "
          f"hull [{chb_low:.4f}, {chb_hi:.4f}]pp, offender max|5.334|5.5 "
          f"{chb_cells['max|5.334|5.5']['marginal_pp']:+.4f}pp), tex literals="
          f"{'ok' if chb_tex_ok else 'MISSING'}")

    # ROUND-23 (gate #96): IS THE DENOMINATOR A CONVENTION ARTIFACT?
    # $764.7B is the denominator of every percentage in the paper, and until this
    # run nothing tested whether it depended on netting cash-arrival months
    # against the cap for the same month. It does, by -5.5% -- and the shift is
    # ENTIRELY mechanical: the half-open window drops cap convolved past its last
    # month. This gate pins that the shift equals the dropped cap mass EXACTLY,
    # because that identity is what makes the shift non-behavioural. It also pins
    # that the calendar convention stays production (pre-committed under every
    # branch) so the variant cannot later be promoted to the headline.
    smb = json.loads((HAZ_DATA / "settlement_months_benchmark_results.json").read_text())
    smb_prod = smb["legs"]["production"]
    smb_ok = (smb["gates_all_pass"]
              and smb["pre_committed"] is True
              and smb["production_convention_stays_calendar"] is True
              and smb["t2_disclosed_sensitivity"] is True
              # the calendar leg still reproduces the committed benchmark exactly
              and abs(smb["calendar_benchmark_b"] - 764.7482532227002) < 1e-9
              and abs(smb_prod["benchmark_b"] - 722.7482532227002) < 1e-6
              # the identity that makes the shift mechanical rather than behavioural
              and abs(abs(smb_prod["shift_b"])
                      - smb["window_edge_cap_mass_lost_b"]) < 1e-9
              and abs(smb["window_edge_cap_mass_lost_b"] - 42.0) < 1e-6
              # the kernel is the committed one, not a fitted one
              and smb["kernel_production"] == [0.1, 0.6, 0.3])
    smb_tex_ok = ("settlement\\_months\\_benchmark" in tex
                  and "\\$722.7 billion" in tex
                  and "$-5.5$\\%" in tex
                  # the mechanical explanation must travel with the number
                  and "the QT window is half-open" in tex
                  # and the dollar-invariance, which is the actual reassurance
                  and "\\$42.6 billion on either denominator" in tex)
    ok = smb_ok and smb_tex_ok
    failures += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] cross-check settlement-months benchmark: "
          f"artifact={smb_ok} (T2, settlement ${smb_prod['benchmark_b']:.4f}B vs "
          f"calendar ${smb['calendar_benchmark_b']:.4f}B, shift "
          f"{smb_prod['shift_pct_of_committed']:+.3f}%, all mechanical), "
          f"tex literals={'ok' if smb_tex_ok else 'MISSING'}")

    # ROUND-23 (gate #97): THE DTI NON-MONOTONICITY IS A RE-CALIBRATION ARTIFACT.
    # dti_threshold_sweep put production 43% at the MINIMUM of its own sweep, which
    # reads badly. Decomposition shows why: the floor-retention rule re-calibrates
    # the mobility scale only where the fixed-scale floor leaves [4,5]%, and across
    # these thresholds that fires exactly once, at 50%. Hold the scale still and the
    # sweep is monotone. This gate pins the monotone frozen row, the size of the
    # re-calibration channel, and -- most important -- the no-op identity at 36/43%
    # that is what identifies the channel at all. It also pins that no headline moved.
    dnd = json.loads((ROOT / "abm" / "data"
                      / "dti_nonmonotonicity_decomposition_results.json").read_text())
    dnd_frozen = dnd["frozen_row_trapped_b"]
    dnd_chan = dnd["recalibration_channel_b"]
    dnd_ok = (dnd["gates_all_pass"]
              and dnd["pre_committed"] is True
              and dnd["t1_artifact"] is True
              and dnd["frozen_row_monotone"] is True
              and dnd["headline_untouched"] is True
              # monotone strictly decreasing as the wall loosens
              and dnd_frozen["0.36"] > dnd_frozen["0.43"] > dnd_frozen["0.5"]
              and abs(dnd_frozen["0.5"] - 46.372) < 0.05
              # the no-op identity: frozen == recalibrated where the rule did not fire
              and abs(dnd_chan["0.36"]) < 1e-9 and abs(dnd_chan["0.43"]) < 1e-9
              # and the whole rebound is the re-calibration
              and dnd_chan["0.5"] < -70.0
              # drift was a uniform level shift, else the differences do not cancel
              and dnd["upstream_drift_spread_b"] < 1.0)
    dnd_tex_ok = ("dti\\_nonmonotonicity\\_decomposition" in tex
                  and "$-\\$73.4$ billion" in tex
                  and "bit-identical at 36 and 43\\%" in tex
                  and "5.09\\%" in tex)
    ok = dnd_ok and dnd_tex_ok
    failures += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] cross-check DTI non-monotonicity: "
          f"artifact={dnd_ok} (T1 artifact, frozen row "
          f"{dnd_frozen['0.36']:.1f}/{dnd_frozen['0.43']:.1f}/{dnd_frozen['0.5']:.1f}B "
          f"monotone, recal channel @50% {dnd_chan['0.5']:+.2f}B), tex literals="
          f"{'ok' if dnd_tex_ok else 'MISSING'}")

    # ROUND-24 (gate #98): THE ASSEMBLED CORRECTIONS. Every downward correction
    # to the headline marginal was disclosed in the section that produced it and
    # nowhere together, so a referee performed the assembly and the paper did
    # not. Section V.E now performs it. This gate is PARAGRAPH-SCOPED for the
    # same reason gate #68 is abstract-scoped: each of these literals already
    # occurs elsewhere in the file, so a whole-file count is satisfied by the
    # very scattering this paragraph exists to end. The file is one paragraph
    # per line, so the paragraph is a line, and the gate binds the line.
    #
    # Four things are pinned, and each is a way the paragraph could rot:
    #   (a) the LADDER -- drop a rung and the assembly stops being an assembly;
    #   (b) the POSTURE -- "upper-middle member ... rather than its center" is
    #       the commitment the round was asked for, and a concision pass that
    #       deletes it leaves the ladder with no conclusion;
    #   (c) the CENSORING FRAMING -- "truncated at the floor rather than erased"
    #       and the unweighted-count disclaimer. HANDOFF_round22 §8.2 records
    #       that the obvious reading ("the estimate rests on a third of the
    #       data") is false on two independent counts, and it is the reading a
    #       reader supplies unprompted. Losing the disclaimer re-opens it;
    #   (d) the COUNTERWEIGHT -- the additive form and the three declined
    #       readings run the other way. Without them the paragraph is a
    #       one-sided case for a smaller number, which is not what the evidence
    #       says.
    asm_ok, _asm = assembly_check(tex)
    failures += 0 if asm_ok else 1
    print(f"[{'PASS' if asm_ok else 'FAIL'}] assembled corrections paragraph (V.E): "
          f"paragraphs={_asm['paragraphs']} (want 1), "
          f"{len(ASSEMBLY_SPANS) - len(_asm['missing'])}/{len(ASSEMBLY_SPANS)} "
          f"spans present, missing={_asm['missing'] or 'none'}")

    post_ok, _post = abstract_posture_check(tex)
    failures += 0 if post_ok else 1
    print(f"[{'PASS' if post_ok else 'FAIL'}] abstract leads with the range (gate #99): "
          f"{len(ABSTRACT_POSTURE) - len(_post['missing'])}/{len(ABSTRACT_POSTURE)} spans "
          f"present, range-before-point={_post['ordered']} "
          f"(idx {_post['i_range']} vs {_post['i_point']}), "
          f"missing={_post['missing'] or 'none'}")

    abml_ok, _abml = abm_lead_check(tex)
    failures += 0 if abml_ok else 1
    print(f"[{'PASS' if abml_ok else 'FAIL'}] Section IV leads with the cross-design (gate "
          f"#100): {len(ABM_LEAD_SPANS) - len(_abml['missing'])}/{len(ABM_LEAD_SPANS)} spans "
          f"present, cross-design-before-verdict={_abml['ordered']}, "
          f"V.E-still-declines={_abml['ve_declines']}, missing={_abml['missing'] or 'none'}")

    let_ok, _let = letter_check(tex)
    failures += 0 if let_ok else 1
    print(f"[{'PASS' if let_ok else 'FAIL'}] response letter tracks the manuscript (gate "
          f"#101): retired-hull-confined={_let.get('hull_ok')}, abstract-words "
          f"claimed={_let.get('claimed_words')} actual={_let.get('actual_words')}, "
          f"drifted={_let.get('drifted') or 'none'}, absent={_let.get('absent') or 'none'}")

    eld_ok, _eld = elasticity_discipline_check(tex)
    failures += 0 if eld_ok else 1
    print(f"[{'PASS' if eld_ok else 'FAIL'}] elasticity-discipline exhibits (gate #102): "
          f"{len(ELASTICITY_DISCIPLINE_SPANS) - len(_eld['missing'])}/"
          f"{len(ELASTICITY_DISCIPLINE_SPANS)} spans present, "
          f"missing={_eld['missing'] or 'none'}")

    bb_ok, _bb = buyback_bracket_check(tex)
    failures += 0 if bb_ok else 1
    cl_ok, _cl = convolved_line_check(tex)
    failures += 0 if cl_ok else 1
    cc_ok, _cc = coupon_convention_check(tex)
    failures += 0 if cc_ok else 1
    fl_ok, _fl = floor_ladder_check(tex)
    failures += 0 if fl_ok else 1
    print(f"[{'PASS' if cc_ok else 'FAIL'}] coupon-convention companion (gate #106): "
          f"{len(COUPON_CONVENTION_SPANS) - len(_cc['missing'])}/"
          f"{len(COUPON_CONVENTION_SPANS)} spans present, "
          f"artifact_ok={_cc.get('artifact_ok')}, "
          f"missing={_cc['missing'] or 'none'}")
    print(f"[{'PASS' if fl_ok else 'FAIL'}] floor-read ladder and designer "
          f"units (gate #107): "
          f"{len(FLOOR_LADDER_SPANS) - len(_fl['missing'])}/"
          f"{len(FLOOR_LADDER_SPANS)} spans present, "
          f"ordered={_fl.get('ordered')}, "
          f"artifact_ok={_fl.get('artifact_ok')}, "
          f"missing={_fl['missing'] or 'none'}")
    _ficv2 = json.loads(FICV2_RESULTS.read_text())
    _ficv3 = json.loads(FICV3_RESULTS.read_text())
    mtw_ok, _mtw = month_twoway_clusters_check(tex, _ficv2, _ficv3)
    failures += 0 if mtw_ok else 1
    print(f"[{'PASS' if mtw_ok else 'FAIL'}] month and two-way cluster rungs "
          f"(gate #115): G_month={_mtw['G_month']}, "
          f"webb_rank={_mtw['webb_rank']}/{_mtw['n_undemoted']} undemoted, "
          f"censored={_mtw['n_censored']}, "
          f"widest_interior={_mtw['widest_interior']}, "
          f"se_month={_mtw['se_shrink_pct']}% smaller, "
          f"se_2way={_mtw['se_grow_pct']}% larger, "
          f"missing={_mtw['missing'] or 'none'}")
    _wnt = json.loads(WALNT_RESULTS.read_text())
    _oos_wnt = json.loads((ROOT / "hazard" / "data"
                           / "oos_identification_results.json").read_text())
    wnt_ok, _wn = wal_normal_turnover_check(tex, _wnt, _oos_wnt)
    failures += 0 if wnt_ok else 1
    print(f"[{'PASS' if wnt_ok else 'FAIL'}] normal-turnover WAL row (gate #108): "
          f"row_present={_wn['present']}, tag_citations={_wn['tag_citations']}, "
          f"anchor_pct={_wn['anchor_pct']}, "
          f"stale_sentence_gone={_wn['stale_sentence_gone']}")
    _eb_cap = json.loads(EXPECT_RESULTS.read_text())
    cmu_ok, _cmu = cap_monthly_units_check(tex, _eb_cap, _eb_cap["cap_benchmark_b"], 2.9, 8.7)
    failures += 0 if cmu_ok else 1
    print(f"[{'PASS' if cmu_ok else 'FAIL'}] cap result in $bn/month (gate #111): "
          f"ceiling={_cmu['cap_per_month']}, "
          f"achievable={_cmu['achievable_per_month']}, "
          f"missing={_cmu['missing'] or 'none'}")
    _dls = json.loads(DLS_RESULTS.read_text())
    dls_ok, _dl = depth_ladder_shape_check(tex, _dls)
    failures += 0 if dls_ok else 1
    print(f"[{'PASS' if dls_ok else 'FAIL'}] 2018 depth ladder shape (gate #114): "
          f"plateau_cov={_dl['plateau_cov_pct']}%, tail_cov={_dl['tail_cov_pct']}%, "
          f"missing={_dl['missing'] or 'none'}")
    _snha_max_bytes = SNHAMAX_RESULTS.read_bytes()
    _snha = json.loads(SNHAADD_RESULTS.read_text())
    _snha_max = json.loads(_snha_max_bytes)
    snha_ok, _sn = snha_additive_check(tex, _snha, _snha_max, _snha_max_bytes)
    failures += 0 if snha_ok else 1
    print(f"[{'PASS' if snha_ok else 'FAIL'}] Aladangady calibration is "
          f"form-conditional (gate #118): additive {_sn['additive_pp']}pp at the "
          f"two anchors, bind (max, additive)={_sn['bind_max_then_additive']}, "
          f"ordered={_sn['ordered']}, in_paragraph={_sn['in_paragraph']}, "
          f"cross_artifact_tie={_sn['cross_artifact_tie']}, "
          f"comparator_sha_ok={_sn['comparator_sha_ok']}, "
          f"missing={_sn['missing'] or 'none'}")
    _mtc = json.loads(MTC_RESULTS.read_text())
    mtc_ok, _mt = marginal_transaction_counts_check(tex, _mtc)
    failures += 0 if mtc_ok else 1
    print(f"[{'PASS' if mtc_ok else 'FAIL'}] marginal in transaction counts (gate #113): "
          f"book_count={_mt['book_count']:,}, "
          f"comparator_sourced={_mt['comparator_sourced']}, "
          f"E3_pass={_mt['E3_pass']}, missing={_mt['missing'] or 'none'}")
    _epab = json.loads(EPAGE_RESULTS.read_text())
    _ecw = json.loads(ECWITHIN_RESULTS.read_text())
    epab_ok, _ep = episode_age_bands_check(tex, _epab, _ecw)
    failures += 0 if epab_ok else 1
    print(f"[{'PASS' if epab_ok else 'FAIL'}] episode gradient with loan age "
          f"held fixed (gate #119): point={_ep['age_point_pp']}pp, "
          f"CI={_ep['age_ci_pp']}, covers_implied={_ep['covers_implied']}, "
          f"committed_excluded={_ep['committed_excluded']}, "
          f"age_only_share={_ep['age_only_share_pct']}%, "
          f"artifact_ok={_ep['artifact_ok']}, "
          f"missing={_ep['missing'] or 'none'}")
    _sccg = json.loads(SCCG_RESULTS.read_text())
    sccg_ok, _sc = state_contingent_cap_check(tex, _sccg)
    failures += 0 if sccg_ok else 1
    print(f"[{'PASS' if sccg_ok else 'FAIL'}] state-contingent cap grid (gate #112): "
          f"cells={_sc['cells_b_per_month']} $bn/month, E3_pass={_sc['E3_pass']}, "
          f"missing={_sc['missing'] or 'none'}")
    _wnrb = json.loads(WALNRB_RESULTS.read_text())
    _amort = json.loads(COUPONAMORT_RESULTS.read_text())
    wnrb_ok, _wb = wal_note_rate_basis_check(tex, _wnrb, _amort)
    failures += 0 if wnrb_ok else 1
    print(f"[{'PASS' if wnrb_ok else 'FAIL'}] note-rate-basis WAL row (gate #110): "
          f"row_present={_wb['row_present']}, "
          f"abm_row_present={_wb['abm_row_present']}, "
          f"basis_effect_present={_wb['effect_present']}, "
          f"cross_artifact_tie={_wb['cross_artifact_tie']}, "
          f"disclaimer={_wb['disclaimer_present']}, "
          f"tag_citations={_wb['tag_citations']}")
    _gat = json.loads(GINNIEATT_RESULTS.read_text())
    _gov_c74 = json.loads(OVERLAY_RESULTS.read_text())
    _goff_c74 = json.loads(GINNIEOFF_RESULTS.read_text())
    gat_ok, _ga = ginnie_attenuated_check(tex, _gat, _gov_c74, _goff_c74)
    failures += 0 if gat_ok else 1
    print(f"[{'PASS' if gat_ok else 'FAIL'}] Ginnie response bracket (gate #116): "
          f"in-sample={_ga['in_sample_pp']}pp, off-window={_ga['off_window_pp']}pp, "
          f"ordered={_ga['ordered']}, E3_pass={_ga['E3_pass']}, "
          f"artifact_ok={_ga['artifact_ok']}, missing={_ga['missing'] or 'none'}")
    print(f"[{'PASS' if cl_ok else 'FAIL'}] convolved sampling line (gate #105): "
          f"{len(CONVOLVED_LINE_SPANS) - len(_cl['missing'])}/"
          f"{len(CONVOLVED_LINE_SPANS)} spans present, "
          f"artifact_ok={_cl.get('artifact_ok')}, "
          f"missing={_cl['missing'] or 'none'}")
    print(f"[{'PASS' if bb_ok else 'FAIL'}] buyback incidence bracket (gate #103): "
          f"{len(BUYBACK_BRACKET_SPANS) - len(_bb['missing'])}/"
          f"{len(BUYBACK_BRACKET_SPANS)} spans present, "
          f"missing={_bb['missing'] or 'none'}")

    b1_ok, _b1 = beta1_sign_check(tex)
    failures += 0 if b1_ok else 1
    print(f"[{'PASS' if b1_ok else 'FAIL'}] beta_1 sign agreement (gate #109): "
          f"tab:params sign={_b1['params_sign']:+d}, "
          f"tab:lowband cells={_b1['cells_found']} "
          f"signs={_b1['lowband_signs']}, "
          f"replicator_note={_b1['replicator_note']}")

    _bdr = json.loads(BDR_RESULTS.read_text())
    _bbcb = json.loads(BBCB_RESULTS.read_text())
    _bdan = json.loads(DANUSINT_RESULTS.read_text())
    bdr_ok, _bd = buyback_discount_rederived_check(tex, _bdr, _bbcb, _bdan)
    failures += 0 if bdr_ok else 1
    print(f"[{'PASS' if bdr_ok else 'FAIL'}] re-derived buyback discount (gate "
          f"#117): Dbar={_bd['dbar_pct']}%, gap_cash={_bd['gap_cash_b']} $bn, "
          f"months_at_or_above_floor={_bd['months_at_floor']}, "
          f"retired_range={_bd['retired_range_present'] or 'gone'}, "
          f"cross_artifact_tie={_bd['cross_artifact_tie']}, "
          f"artifact_ok={_bd['artifact_ok']}, "
          f"missing={_bd['missing'] or 'none'}")

    # R32 C-79 (gate #120). Reuses the two artifacts loaded just above --
    # danish_us_intercept owns gap_par and the Danish mean CPR, the committed
    # buyback bracket owns the early face -- so the tie is to runs this one
    # did not write. Every field printed below is computed by the call above
    # it; nothing here reads a variable that does not yet exist.
    _dios = json.loads(DIOS_RESULTS.read_text())
    dios_ok, _di = danish_interest_only_share_check(tex, _dios, _bdan, _bbcb)
    failures += 0 if dios_ok else 1
    print(f"[{'PASS' if dios_ok else 'FAIL'}] Danish interest-only share (gate "
          f"#120): break-evens={_di['breakeven_pct']}%, "
          f"gap_at_sourced={_di['gap_at_sourced_b']} $bn, "
          f"breakeven-stated-first={_di['breakeven_before_import']}, "
          f"limits-travel={_di['limits_travel']}, "
          f"double-counting-retracted={_di['double_counting_retracted']}, "
          f"grid_ok={_di['grid_ok']}, "
          f"retired={_di['retired_present'] or 'gone'}, "
          f"cross_artifact_tie={_di['cross_artifact_tie']}, "
          f"artifact_ok={_di['artifact_ok']}, "
          f"missing={_di['missing'] or 'none'}")

    # R32 C-128 (gate #121). The two committed benchmarks this run had to
    # reproduce belong to settlement_months_benchmark, loaded here rather
    # than re-derived, so the tie is to a run this one did not write.
    _rba = json.loads(RBA_RESULTS.read_text())
    _smb121 = json.loads(SMB_RESULTS.read_text())
    _bmr = json.loads(BMR_RESULTS.read_text())
    rba_ok, _rb = realized_boundary_allocation_check(tex, _rba, _smb121, _bmr)
    failures += 0 if rba_ok else 1
    print(f"[{'PASS' if rba_ok else 'FAIL'}] realized boundary allocation "
          f"(gate #121): both_aligned={_rb['both_aligned_b']} $bn, "
          f"shift={_rb['shift_both_b']} $bn ({_rb['share_pct']}%), "
          f"cap_only_leads={_rb['cap_only_leads']}, "
          f"decomposition={_rb['decomposition_ok']}, "
          f"mass_out_anchored={_rb['mass_out_anchored']}, "
          f"cross_artifact_tie={_rb['cross_artifact_tie']}, "
          f"artifact_ok={_rb['artifact_ok']}, "
          f"missing={_rb['missing'] or 'none'}")

    # R32 C-127 (gate #122), BRANCH D. The clip months and the ARTIFACT
    # verdict this disclosure strengthens belong to h1_zero_months_diagnosis;
    # the cap-relative benchmark belongs to expectation_benchmark.
    _h1z = json.loads(H1Z_RESULTS.read_text())
    _xb122 = json.loads(EXPECT_RESULTS.read_text())
    bmr_ok, _bm = benchmark_monthly_rebuild_check(tex, _bmr, _h1z, _xb122)
    failures += 0 if bmr_ok else 1
    print(f"[{'PASS' if bmr_ok else 'FAIL'}] benchmark monthly rebuild "
          f"(gate #122): reconciles to {_bm['reconciles_to_b']} $bn, "
          f"stale={_bm['stale']}, counts_ok={_bm['counts_ok']}, "
          f"overclaimed={_bm['overclaimed'] or 'none'}, "
          f"cross_artifact_tie={_bm['cross_artifact_tie']}, "
          f"artifact_ok={_bm['artifact_ok']}, "
          f"missing={_bm['missing'] or 'none'}")

    va_ok, _va = verdict_audit_check(tex)
    failures += 0 if va_ok else 1
    print(f"[{'PASS' if va_ok else 'FAIL'}] verdict-adjudication audit (gate #104): "
          f"{len(VERDICT_AUDIT_SPANS) - len(_va['missing'])}/"
          f"{len(VERDICT_AUDIT_SPANS)} spans present, "
          f"missing={_va['missing'] or 'none'}")

    print(f"\n{'ALL GATES PASS' if failures == 0 else f'{failures} GATE(S) FAILED'}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
