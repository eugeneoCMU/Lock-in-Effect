# CORRECTED — R32 Wave 2, cluster F-assembly (C-18, C-26, C-39, C-40, C-41)

FILE for every edit: `paper/v18/revised_paper_v18.tex` (worktree `agency-mbs-runoff-qt-424945`).
Read-only work. No repo script executed, no pytest, nothing in the worktree written. Gate rules were re-implemented locally from AST-extracted string constants in `tools/liveness_gates.py`, `tests/test_assembled_corrections_gate.py` and `tests/test_floor_ladder_gate.py`, then run against an in-memory copy.

**Re-anchoring result: 11 of 11 OLD spans (7 in-region + 4 companions) still count exactly 1 on the current bytes. 0 byte-anchors needed repair.** Only line numbers moved: draft's 333 → **355**, 345 → **367**, 348 → **370**, 349 → **371**, 439 → **461**, 1430 → **1455**, 271 → **279**. All 11 also count 1 in `revised_paper_v18_long_abstract.tex`.

Draft's 8 edits → **7 kept (5 in-region + 2 companions rewritten) + 2 new companions; 1 whole edit and 4 sub-claims dropped.** Word delta **+316** (draft was +483). Line 31 untouched.

Gate state after all 11: 1 `A seventh qualification` paragraph, 15/15 `ASSEMBLY_SPANS` inside it, 4/4 `ASSEMBLY_TABLE_SPANS` in file, `ZERO_COUNT` 19/19 unchanged at 0, `EXACTLY_ONE` 4/4 unchanged at 1, `HARDCODED_XREF` 0/0 on all five regexes, `SUPERSEDED_CONTEXTUAL` unchanged, all four `test_assembled_corrections_gate.py` fixtures still count 1, no `test_floor_ladder_gate.py` constant touched (those all sit in `tab:ladder`, B-ladder's region).

---

## Edit 1 — the assembly's Fannie rung carries its like-for-like Freddie counterpart (C-26)
OLD_COUNT_ASSERT: 1
OLD:
and the Fannie Mae read of the same selection rule on the pooled off-window period, 5.52\%, brackets the marginal below the $+4.3$ edge of the clean band (above).
NEW:
and the Fannie Mae read of the same selection rule on the pooled off-window period, 5.52\%, brackets the marginal below the $+4.3$ edge of the clean band (above), its like-for-like Freddie counterpart 5.19\% rather than the 2018 leg's 4.991\%.
WHY: the assembly is the one exhibit whose purpose is to line the reads up, and it lines 5.52\% up beside a 4.991\%-anchored ladder without the counterpart, so the rung reads as a fifth read of one object. Fourteen words, no decomposition.
FIX_FOLDED: V:CONVENTION_VIOLATIONS #1 — the draft's "holds on the pooled period's **basis** alone" is gone; "basis" in this paragraph means the accounting basis, and marginals carry no basis label. V:CONVENTION_VIOLATIONS #4 (redundancy) — the draft's "0.337 points of the distance ... is agency and the rest is period" is dropped; that decomposition is already at line 339 and in the `tab:oosfloor` post-float note at line 406, and Companion 8 puts the corrected form at line 461.
LITERALS: `5.19\%` = `fannie_floor_read_results.json` `comparison.freddie_headline_cpr_pct` 5.185, printed rounded exactly as line 339 prints it ("against Freddie's 5.19\%"). `4.991\%` = `oos_identification_results.json` `instrument1_oow_floor.defensible_clean_floor.clean_mid_pct`.
PINS: `ASSEMBLY_SPANS["ladder_fannie"]` = `5.52\%, brackets the marginal below the $+4.3$ edge` is inside OLD and is reproduced byte-identically; the insertion starts after `(above)`. No other pinned span, test fixture or `EXACTLY_ONE` literal is inside OLD. The `.` after `(above)` becomes `,` — AST-checked against all 15 `ASSEMBLY_SPANS`, all 4 table spans and all 4 test fixtures: none contains `(above)`.

---

## Edit 2 — the anchor convention is shown not to flatter the headline (C-18)
OLD_COUNT_ASSERT: 1
OLD:
Carrying the overlay's $0.797$ scaling up to the age-standardized floor projected a marginal near $+3.0$;
NEW:
The anchor convention does not flatter the headline: extending the depth ladder to the five reads the 10\% support rule admits puts the middle of them at 4.869\%, below the adopted 4.991\%, and a lower floor implies a marginal above the headline rather than below it (run \texttt{matched\_depth\_reconciliation}). Carrying the overlay's $0.797$ scaling up to the age-standardized floor projected a marginal near $+3.0$;
WHY: the assembly's own ladder rests on the mid-grid anchor and never says the anchor is not a downward-flattering pick. Line 741 prints the extension and the unchanged band but never says which way the extension moves the anchor or the marginal — that is the only new content here, and it runs *up*.
FIX_FOLDED: V:REFUTED #2 — "median", "central tendency" and "a counting rule and not a pick" are all gone. `defensible_clean_floor.primary_point_selection = "gap<=-0.0025_age>=12"` records a **pick**, and line 79 pins the anchor as "an anchor convention rather than a central tendency"; the corrected sentence asserts neither a median rule nor a centre. V:CONVENTION_VIOLATIONS #4 — the draft's restatement of "leaves the clean band unchanged" is dropped (line 741 already states it, with both extra reads); the definition limb is dropped too (see DROPPED).
LITERALS: `4.869\%` = `matched_depth_reconciliation_results.json` `clean_band_under_extended_ladder.well_supported_reads_pct = [5.334, 4.991, 4.695, 4.722, 4.869]`, middle of the five = 4.869; already printed once at line 741. `10\% support rule` = the phrase at line 742, `support_rule` MD_SUPPORT 0.10. Direction from `floor_to_marginal_mapping.engine_reads`: 4.695 → +6.771 pp, 4.991 → +5.572 pp, so a 4.869\% read lies strictly above the headline. No new full-precision value; **no `+6.0` literal printed** — no committed artifact carries a floor→marginal read at 4.869\% (see OPEN).
PINS: no pinned span, test fixture or `EXACTLY_ONE` literal inside OLD. `ASSEMBLY_SPANS["ladder_headline"]` and `["ladder_agestd"]` sit on either side and are untouched. `md_claims` for the matched-depth cross-check goes 2 → 3 against a `>= 1` threshold.

---

## Edit 3 — the floor side's one-directionality attributed to an absence, with the sign scoped and the channel separated (C-41)
OLD_COUNT_ASSERT: 1
OLD:
The variant documents an upward bias; the corrected member lies below the headline, at the bottom of the seasoning-ramp span just swept.
NEW:
The variant documents an upward bias; the corrected member lies below the headline, at the bottom of the seasoning-ramp span just swept. That the floor side runs one way is also an absence: the floor is a level of total turnover rather than of a strictly involuntary component of it (Section~\ref{sec:pathb}), so it carries the activity of the period it is read on, and re-reading it at the window's own level enters at the floor rather than at the seasoning ramp just scaled, so it cuts the other way --- a lower anchor raises the marginal. It is the one floor-side correction I can name that would move the headline up, and it turns on whether the window's turnover level is the lower of the two, which I do not measure here.
WHY: C-41 asks for the one-directionality to be attributed rather than left as a tally. The unmeasured upward floor-side correction is the honest half of that attribution, and it is a disclosure addition: nothing existing is softened or deleted.
FIX_FOLDED: V:REFUTED #6 — the signed direction is now explicitly conditional ("it turns on whether the window's turnover level is the lower of the two, which I do not measure here"); the draft asserted it flat while its own UNVERIFIED §3 claimed it was unconditional. V:REFUTED #7 — **the anchor is relocated** from before the Aladangady passage to immediately after it, so the channel distinction is a backward reference, and the two housing-activity channels are separated in the text ("enters at the floor rather than at the seasoning ramp just scaled, so it cuts the other way"); as drafted the paragraph asserted housing activity biasing the marginal both ways with no distinction and a forward reference. V:CONVENTION_VIOLATIONS #4 — "one mechanism read more than once" deleted (line 355 already says "one mechanism read twice" three sentences upstream); the floor's total-turnover nature is compressed to a `\ref` because lines 92 and 227 already state it in full.
LITERALS: none — zero numeric tokens.
PINS: no pinned span inside OLD. `ASSEMBLY_SPANS["counter_three_readings"]` (`point to a larger lock-in channel, not a smaller one`) begins immediately after the insertion and is preserved byte-identically; `censor_truncated` / `censor_unweighted` / `censor_share` are far upstream and untouched. Test fixture `What the assembly settles is where in the interval the mass sits` no longer abuts the insertion (it did in the draft) and still counts 1.
HEDGE SCOPE: "the one floor-side correction I can name" stays as scoped — exhaustiveness is not established and must not be tightened to "the one floor-side correction".

---

## Edit 4 — the survival-selection attenuation joins the downward side in prose (C-40)
OLD_COUNT_ASSERT: 1
OLD:
and mildly super-proportional because censored contributions do not scale with $s$.
NEW:
and mildly super-proportional because censored contributions do not scale with $s$. The survival-selection attenuation of the same imported coefficient is a bracket of the same kind and belongs on this side: $a = S^{\theta}$ at the measured pre-window survival share carries the marginal from $+5.1$ at $\theta = 0.25$ to $+3.7$ at $\theta = 1$ (run \texttt{attenuation\_sensitivity}), with $\theta$ free (Section~\ref{sec:pathb}) --- a different axis from the elasticity band, not a widening of it.
WHY: the substantive C-40 call. The printed exclusion ground at line 461 — "a transport sensitivity on the imported coefficient" — does not discriminate: the moving-share bracket in the immediately preceding clause is a transport sensitivity on the same imported coefficient and a bracket in a free parameter, and it is on the list; so are the $\delta = 3.25\%$ sub-band member and the Fonseca anchor. The paragraph's own claim two sentences earlier ("this assembly now lines both directions up") is falsified by a withheld downward member. Membership is all that changes: the grid, the mapping and the free-parameter caveat are already printed at lines 233 and 461.
FIX_FOLDED: V:REFUTED #9 (numeric homonyms) — each endpoint now carries its $\theta$ inline ("$+5.1$ at $\theta = 0.25$ to $+3.7$ at $\theta = 1$"), so neither can bind to `tab:assembly`'s concave-transform `$+5.1$` or vintage-overlay `$+3.7$`. V:REFUTED #10 confirmed the figures sound and they are unchanged.
LITERALS: `$+5.1$` / `$+3.7$` at `$\theta = 0.25$` / `$\theta = 1$` — `attenuation_sensitivity_results.json` `monotonicity["4.991"].marginal_pp_ordered = [5.5716, 5.0955, 4.6177, 3.7037]` against `a_grid_descending = [1.0, 0.8558, 0.7324, 0.5365]`, i.e. $\theta = 0/0.25/0.5/1$. Both endpoints already printed at lines 233 and 461. `$a = S^{\theta}$` — `selection_identity.form`; $S = 40{,}234/75{,}000$ (`S_numerator`/`S_denominator`) — the paper's own attrition figure, not swapped. "$\theta$ free" — `selection_identity.free_parameter_note`; line 233 already says $\theta$ is not estimable. "a different axis from the elasticity band, not a widening of it" — `not_an_elasticity_band_widening`.
PINS: none inside OLD. `counter_additive`, `counter_fonseca`, `counter_three_readings` are in the same sentence chain and untouched. `Section~\ref{sec:pathb}` (label line 217) matches none of the five `HARDCODED_XREF` regexes — re-checked on the after-file, 0/0.
DEPENDS ON: Companions 9 and 10. Without them the manuscript says both "listed" and "kept out of the assembly".

---

## Edit 5 — tab:assembly gains the attenuation row (C-40)
OLD_COUNT_ASSERT: 1
OLD:
Moving-share bracket, $s = 0.25$, off-window & $+1.8$ & below the interval & the bracket's deep stress; edge by construction \\
NEW:
Moving-share bracket, $s = 0.25$, off-window & $+1.8$ & below the interval & the bracket's deep stress; edge by construction \\ Survival-selection attenuation, $\theta = 0.25$ to $1$ & $+5.1$ to $+3.7$ & below & bracket in $\theta$ on the imported coefficient ($a = S^{\theta}$, $\theta$ not estimable here); a different axis from the elasticity band (run \texttt{attenuation\_sensitivity}) \\
WHY: placed with the other brackets, not beside the concave row, so the row reads as what it is. The marginal cell is the range over $\theta$, never a triple. Both endpoints (5.0955, 3.7037) are below 5.5716, so the `vs. $+5.6$` cell is `below`.
FIX_FOLDED: V:REFUTED #9 — the Status cell now **leads** with "bracket in $\theta$", and the Reading cell's `$\theta = 0.25$ to $1$` runs in the same order as the marginal cell's `$+5.1$ to $+3.7$`, so the endpoint-to-$\theta$ mapping is readable off the row. The draft's longer cell is shortened by 6 words. Residual homonym risk is not zero — see OPEN.
LITERALS: as Edit 4; no new full-precision value. The caption's claim "Every value repeats a committed figure from the text of this subsection" stays true because Edit 4 prints both endpoints in the subsection.
PINS: none. `ASSEMBLY_TABLE_SPANS` pins `\label{tab:assembly}`, `Table~\ref{tab:assembly} tabulates this assembly`, `measured composed lower member (run \texttt{b5\_joint\_cell})` and `counterweight, conservative-band evidence` — the third is on the same line 371 but is not inside OLD; all four verified present after. Line 371 goes 18 → 21 ` & ` separators (6 → 7 four-column rows); `$` count stays even. No column width added; **no note moved into the float** (`tab:assembly` has no post-float note and none is created).

---

## Edit 6 — tab:assembly row 2 glosses "mid-grid" (C-18)
OLD_COUNT_ASSERT: 1
OLD:
Off-window re-anchor & $+5.6$ & headline & mid-grid anchor inside the binding interval \\
NEW:
Off-window re-anchor & $+5.6$ & headline & mid-grid anchor (the middle of the three depth cuts fixed before the reads) inside the binding interval \\
WHY: C-18's location list names this row, and the table is read standalone. The paper's term "mid-grid anchor" is kept (9 sites) and glossed.
FIX_FOLDED: V:REFUTED #2 — "median of the three committed depth cuts" is gone. The gloss is now the abstract's own wording, added at line 31 after the draft was written ("the middle of the three depth cuts fixed before the reads"), which asserts a grid position rather than a central tendency and therefore does not collide with line 79's pinned "an anchor convention rather than a central tendency".
LITERALS: none. `middle of the three` 1 → 2; `mid-grid` unchanged at 9.
PINS: none inside OLD.

---

## Edit 7 — tab:assembly's Fannie row carries the counterpart (C-26)
OLD_COUNT_ASSERT: 1
OLD:
Fannie floor read (5.52\%) & below $+4.3$ & below & bracketing; second agency, pooled period \\
NEW:
Fannie floor read (5.52\%) & below $+4.3$ & below & bracketing; second agency, pooled period; like-for-like Freddie 5.19\% \\
WHY: five words. The row already says "pooled period", which retires cell identity, but the 5.52\% sits two rows under a 4.991\%-anchored ladder and the exhibit is read standalone.
FIX_FOLDED: none — unchanged from draft (the verdict raised nothing against it).
LITERALS: `5.19\%` — as Edit 1.
PINS: none inside OLD.
CHEAPEST DROP: if the length or width queue binds, this is the first cut — line 461 and Edit 1 both carry the counterpart.

---

# COMPANION EDITS — OUTSIDE MY REGION, REQUIRED

Each still counts 1 on current bytes and in the long-abstract variant. Coordinator: apply only if no sibling cluster has claimed the same span (see COLLISIONS).

## Edit 8 — repair a false arithmetic claim at line 461 (raised by the verifier, C-26)
OLD_COUNT_ASSERT: 1
OLD:
so most of that distance is period and not agency
NEW:
so 0.337 points of that distance is agency and the rest is period
WHY: the claim as printed is **arithmetically false**. `fannie_floor_read_results.json` `comparison`: Fannie 5.522, Freddie parity 5.185, `difference_pp` 0.337 (agency); 5.185 − 4.991 = 0.194 (period). Agency is the larger part, 0.337 of 0.531. Without this repair Edit 1 would put a true statement of the same comparison 100 lines from a false one.
FIX_FOLDED: V:REFUTED #4. The draft cited line 461 approvingly and did not notice.
LITERALS: `0.337` — `comparison.difference_pp`; the NEW wording mirrors line 339's and line 406's existing form ("so the agency difference is 0.337 points of CPR and the rest of the distance ... is period"), so no new phrasing enters the paper.
PINS: none inside OLD. No `tab:uncertainty` pinned span (#102/#103/#104 `VERDICT_AUDIT_SPANS`) contains it — AST-checked.
REGION: line 461, `tab:uncertainty` headline row — **B-ladder / E**.

## Edit 9 — line 461's attenuation exclusion ground becomes its inclusion ground (C-40)
OLD_COUNT_ASSERT: 1
OLD:
(run \texttt{attenuation\_sensitivity}; a transport sensitivity on the imported coefficient, kept out of the assembly on that ground)
NEW:
(run \texttt{attenuation\_sensitivity}; a transport sensitivity on the imported coefficient, listed in Table~\ref{tab:assembly} as a bracket in $\theta$ rather than as a correction)
WHY: Edits 4–5 falsify the exclusion. The disclosure is carried into the claim, not deleted: it is still named a transport sensitivity on an imported coefficient.
FIX_FOLDED: the draft's Companion A, unchanged in substance.
LITERALS: none.
PINS: none. `kept out of the assembly` is not read by any gate or test (AST-checked over `tools/liveness_gates.py`, `tests/*.py`); it goes 2 → 0.
REGION: line 461 — **B-ladder / E**. Distinct substring from Edit 8; both can land.

## Edit 10 — App. O ledger row agrees (C-40)
OLD_COUNT_ASSERT: 1
OLD:
Enforced: reported as committed; kept out of the assembly (a transport sensitivity on an imported coefficient, not a correction to the paper's own object) (neutral)
NEW:
Enforced: reported as committed; listed in the assembly as a bracket in $\theta$ rather than as a correction (a transport sensitivity on an imported coefficient, and $\theta$ is not estimable) (downward)
WHY: the ledger must agree with the assembly.
FIX_FOLDED: the draft's Companion B, unchanged in substance.
LITERALS: none. `(neutral)` 13 → 12, `(downward)` 1 → 2; neither label is counted by any gate, and #104's two direction-rows are untouched.
PINS: none.
REGION: line 1455, App. O adjudication ledger — **G-denominators**.

## Edit 11 — §V.B states the estimand rule C-39 requires (C-39)
OLD_COUNT_ASSERT: 1
OLD:
and the marginal correction is pure conventional-share scaling ($0.797\times$)
NEW:
and the overlay marginal is pure conventional-share scaling ($0.797\times$) --- a change of estimand, a re-scoring onto the conventional sub-book, rather than a correction to the headline
WHY: C-39's condition is that the rule be stated **once in §V.B** and that the ledger agree with it. `change of estimand` / `not a correction` occur only at line 368 (`tab:assembly`) and line 1455 (ledger); §V.B never states it and this clause **contradicts** it by calling the overlay marginal a correction. This is where C-39 is discharged — not in the §V.E prose, where the label is already carried by the two table cells.
FIX_FOLDED: V:REFUTED #5. It also replaces the draft's whole Edit 1 (see DROPPED) at one-eighth the words.
LITERALS: none new. `change of estimand` 3 → 4, `the marginal correction` 1 → 0.
PINS: none inside OLD. No `ASSEMBLY_SPANS`, `EXACTLY_ONE`, `ZERO_COUNT` or test constant contains it.
REGION: line 279, §V.B — **C-formfork / D-mechanical**.

---

## CENSUS

Fixed-string counts with `str.count` over the whole file, before and after applying Edits 1–11 in order to an in-memory copy. Measured, not estimated.

| literal / phrase | before | after |
|---|---|---|
| `5.19\%` | 2 | 4 |
| `4.991\%` | 17 | 19 |
| `4.869\%` | 1 | 2 |
| `10\% support rule` | 1 | 2 |
| `middle of the three` | 1 | 2 |
| `0.337` | 2 | 3 |
| `$+5.1$` | 5 | 7 |
| `$+3.7$` | 5 | 7 |
| `S^{\theta}` | 2 | 4 |
| `survival-selection` | 1 | 2 |
| `Survival-selection` | 1 | 2 |
| `not estimable` | 1 | 3 |
| `a different axis from the elasticity band` | 0 | 2 |
| `\texttt{attenuation\_sensitivity}` | 3 | 5 |
| `\texttt{matched\_depth\_reconciliation}` | 2 | 3 |
| `change of estimand` | 3 | 4 |
| `not a correction` | 3 | 2 |
| `the marginal correction` | 1 | 0 |
| `kept out of the assembly` | 2 | 0 |
| `most of that distance` | 1 | 0 |
| `(neutral)` | 13 | 12 |
| `(downward)` | 1 | 2 |
| `strictly involuntary` | 4 | 5 |
| `mid-grid` | 9 | 9 |
| `free parameter` | 3 | 3 |
| `5.185` | 3 | 3 |
| `5.52\%` | 8 | 8 |
| `5.51\%` | 7 | 7 |
| `$+1.8$` | 1 | 1 |
| `$+4.4$` | 8 | 8 |
| `$+5.6$` | 25 | 25 |
| `$+9.2$` | 25 | 25 |
| `$+11.2$` | 9 | 9 |
| `$+11.5$` | 4 | 4 |
| `$+2.9$` | 16 | 16 |
| `$0.797\times$` | 2 | 2 |
| `0.6645` | 1 | 1 |
| `$+2.9$ to $+8.7$` | 8 | 8 |
| `$+3.0$ to $+8.0$` | 5 | 5 |
| `$+3.5$ to $+13.1$` | 7 | 7 |
| `$+3.9$ to $+13.1$` | 0 | 0 |

Structural:

| object | before | after |
|---|---|---|
| assembly paragraph, words | 968 | 1200 |
| assembly paragraph, chars | 6,252 | 7,654 |
| whole document, words | 67,819 | 68,135 (**+316**) |
| abstract, line 31 | byte-identical, 323 words | byte-identical, 323 words |
| `A seventh qualification` paragraphs | 1 | 1 |
| gate #98 `ASSEMBLY_SPANS` in that paragraph | 15/15 | 15/15 |
| gate #98 `ASSEMBLY_TABLE_SPANS` in file | 4/4 | 4/4 |
| `ZERO_COUNT` (19) | all 0 | all 0, none changed |
| `EXACTLY_ONE` (4) | all 1 | all 1, none changed |
| `HARDCODED_XREF` (5 regexes) | 0 | 0 |
| `test_assembled_corrections_gate.py` fixtures (4) | 1 each | 1 each |
| `tab:assembly` body rows (line 371 block) | 6 | 7 |
| `tab:assembly` post-float note | none | none (unchanged) |

**Line 31 is not touched** (`t.split("\n")[30] == new.split("\n")[30]` → True), so gate #101's tie between the abstract's 323 words and the response letter's claimed count is unaffected. `touches_line31: false`.

---

## DROPPED

1. **Draft Edit 1 in full** (the inclusion rule + the "two of the entries are not corrections" carve-out, ~150 words). Reasons, all four independent:
   - **Self-falsifying** (V:REFUTED #3): the stated bar is cleared by `psa_level_sweep`, `covariate_ablation_offwindow` and `floor_form_mixture`, none of which is a `tab:assembly` row, and the mixture runs upward, tripping the rule's own "nothing held out for running the wrong way" clause. I re-checked the draft's escape ("the covariate ablation is a level swing") and it fails — the reported quantity is a marginal move at a labelled floor. No discriminating clause is available from source.
   - **Mis-attributed literals** (V:REFUTED #1, confirmed from source): `ginnie_specific_marginal_component_pp` 0.0021157 = 4.443419 − 4.441303 (primary − `gse_placebo`) and `vintage_specific_marginal_component_pp` 0.0010419 = 3.702154 − 3.701112 (primary − `sampled_placebo`) — primary-minus-**placebo** components, not residuals against share arithmetic. Those residuals are ~4× larger and near-equal: 4.443419 − 0.796×5.571558 = 0.0085 and 3.702154 − 0.663×5.571558 = 0.0082. The draft's sentence was false.
   - **Imprecise** (V:REFUTED #8): `expectation_check.scale_relative_deviation_vs_retained_pct = 0.222` and `nominal_retained_share = 0.663` against `scale 0.6645` — the scale is not the retained share.
   - **Redundant + mis-sited** (V:REFUTED #5): the estimand label is already carried at line 368 (both overlay rows: "change of estimand ... not a correction") and line 1455 (ledger). C-39's condition requires it in **§V.B**, where it is not merely absent but contradicted. Replaced by Edit 11.
   Consequence: the forward reference "--- the survival-selection attenuation included (below)" (V:CONVENTION_VIOLATIONS #2) and the order defect of naming entries before listing them, with "vintage" having no antecedent on line 355 (V:CONVENTION_VIOLATIONS #3), both vanish with it.
2. **Draft Edit 2's decomposition clause** ("so 0.337 points of the distance from the clean anchor is agency and the rest is period"). Already at **line 339** ("so the agency difference is 0.337 points of CPR and the rest of the distance from the clean read is period") and in the `tab:oosfloor` post-float note at **line 406**; Edit 8 restores the correct form at line 461. Three sites are enough.
3. **Draft Edit 3's definition limb** ("the mid-grid 4.991\% is the median of the run's three committed depth cuts" + "leaves the clean band unchanged"). The definition landed in the **abstract at line 31** after the draft was written; the band-unchanged claim with both extra reads is at **line 741**. Edit 6 carries the gloss into the exhibit at 10 words.
4. **Draft Edit 4's "one mechanism read more than once" clause.** Line 355 already says "The floor-level corrections and the censoring share are one mechanism read twice" three sentences upstream (V:CONVENTION_VIOLATIONS #4).
5. **Draft Edit 4's restatement of the floor as total turnover.** Lines 92 and 227 already state it at length ("It floors total turnover, not a strictly involuntary component of it: deep-discount-cohort turnover at this level includes discretionary life-cycle moves and cash-out refinancings..."). Compressed to a `\ref{sec:pathb}` pointer.
6. **The draft's proposed line-90 companion** ("Sensitivity catalogue ... Ginnie overlay $+4.4$"). Line 90 does not call the overlay a correction — filing it in a sensitivity catalogue is not a label contradiction, and C-39's condition names §V.B and the ledger, both now covered.

Net: 167 words of the draft's +483 removed while every condition keeps a carrier.

---

## COLLISIONS

Line-level warnings. **F must be applied before B-ladder and C-formfork**, or any sibling anchor carrying neighbouring context on line 355 will stale.

1. **Line 355** (Edits 1–4) is inside two sibling regions as declared: **B-ladder** ("§V.E ... the inference-ladder and binding-layer passages" — `posture_binding_layer` is on this line and Edits 3/4 insert on either side of the surrounding sentences) and **C-formfork** ("§V, the form fork" — line 355 carries `$+3.5$ to $+13.1$` ×1). No byte overlap with F's OLDs. Note that Edit 1's OLD **ends** exactly where Edit 2's OLD **begins** — adjacent, non-overlapping, both count 1; they must be applied as separate replacements, not merged.
2. **Line 355 must stay one line.** Gate #98 is paragraph-scoped and needs all 15 `ASSEMBLY_SPANS` on it; `test_assembled_corrections_gate.py::test_paragraph_split_fails` exists precisely to catch a split. No sibling may split it.
3. **Line 461** — Edits 8 and 9, region **B-ladder / E**. Two distinct substrings in the same `tab:uncertainty` headline row. Edit 8 is a factual repair the verifier raised, not an F condition; if B-ladder is already repairing it, drop F's Edit 8 and keep theirs. Edits 4–5 **cannot land without Edit 9**.
4. **Line 1455** — Edit 10, region **G-denominators**. Edits 4–5 cannot land without it.
5. **Line 279** — Edit 11, region **C-formfork / D-mechanical**. If a sibling rewrites that clause, C-39 needs its estimand label folded into their wording instead.
6. **Line 46** carries the introduction's twin of the §V.E sentence ("every correction I can measure to the floor or to the accounting basis moves..."), region **A-posture**. F no longer edits either twin (draft Edit 1 dropped), so the two stay consistent by default — but if A-posture rewrites line 46's twin, line 355's unedited twin must move with it.
7. **Line 79** (Table 1) pins "an anchor convention rather than a central tendency", region **A-posture**. Edit 6's gloss is compatible by construction; A-posture must not replace that phrase with a central-tendency wording.

---

## OPEN

1. **C-40's inclusion-rule limb is not discharged and I could not discharge it truthfully.** No rule I can state from source admits the seven `tab:assembly` brackets and the attenuation while excluding `psa_level_sweep`, `covariate_ablation_offwindow` and `floor_form_mixture`, all three of which score a marginal at a labelled floor under a committed run. The caption's "the form-conditional hull ... deliberately not restated here" covers the mixture only if the mixture is a hull member, which I did not verify. Direction-neutrality — the substance C-40 wants — is already asserted in the paragraph ("Specification choices that are not floor corrections run both ways, and this assembly now lines both directions up") and demonstrated by the four upward rows (+9.2, +11.2, +11.5, gradient). **Coordinator's call:** (a) accept the substantive discharge (Edits 4–5 + companions) and leave the rule unstated; (b) add a one-sentence non-exhaustiveness disclosure naming those three runs and their own sites; (c) add three rows. I recommend (a) or (b); (b) costs ~30 words.
2. **Residual numeric homonym in `tab:assembly`** (V:REFUTED #9). `$+5.1$` also labels the concave-transform row and `$+3.7$` the vintage-overlay row. Edit 4's inline $\theta$ labels and Edit 5's $\theta$-leading Status cell make the binding recoverable but not impossible to mis-read. Printing `$+5.10$`/`$+3.70$` would remove it at the cost of two new precision forms — I judged that worse. Flagging, not acting.
3. **Build / render.** Not compiled — no repo script run. `tab:assembly` is `[H]`, its declared widths already sum to ~17.1cm against ~16.5cm textwidth, and `tests/test_render_gate.py` names "the tab:assembly defect" (x=620 > 612). Edit 5 adds a row, not width; the paragraph gains 232 words. The 130-page build and `render_gate` must be checked at this site. Cheapest lever if it breaks: delete "; a different axis from the elasticity band" from Edit 5's row (Edit 4's prose carries it), then Edit 7's five words.
4. **No `+6.0` figure for the five-read middle.** C-18's block quotes "~+6.0pp by the printed delta = 6.5 column"; no committed artifact carries a floor→marginal read at 4.869\% (`floor_sweep_results.json`'s grid is {2, 3, 3.5, 4, 4.5, 5, 6}\%; the 4.695/4.991 reads are PCHIP interpolations). Edit 2 therefore prints the direction, not the number. Printing it needs a new PCHIP read — a run, so Eugene's call.
5. **The activity comparison behind Edit 3 is external.** "existing-home sales" occurs 0 times in the .tex and C-71 records the 5.34M/4.09M NAR figures as data the repository does not hold. Edit 3 now states the mechanism and scopes the sign on an unmeasured premise; settling it needs the external series (Eugene).
6. **C-41's "mirror the hedge in the abstract" line not acted on.** Line 31 already reads "every correction **I can measure** to the baseline turnover floor or to the accounting basis moves it down within the range rather than up", which carries the content; and line 31 is another drafter's region and gate #101's word-count anchor. Flagging.
7. **Long-abstract variant.** All 11 OLDs count 1 in `revised_paper_v18_long_abstract.tex`; the coordinator's mirror step should re-confirm after application.
