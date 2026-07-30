# DRAFT — R32 Wave 2, cluster F: Section V.E assembly paragraph + tab:assembly

Conditions assigned: **C-18, C-26, C-39, C-40, C-41**. All five drafted; none refused.
Region: `paper/v18/revised_paper_v18.tex` line 333 (the `A seventh qualification` paragraph) and lines 335–355 (`tab:assembly`). Nothing outside that region is edited here; two **required companion edits** outside it are specified at the end and must land in the same commit.

Verified read-only. No repo script executed; gate #98's rule was re-implemented locally from the strings in `tools/liveness_gates.py:379–436` (not imported) and run against an in-memory copy of the edited manuscript.

**Gate #98 status after all eight edits: PASS** — one `A seventh qualification` paragraph, 15/15 `ASSEMBLY_SPANS` present in it, 4/4 `ASSEMBLY_TABLE_SPANS` present in the file. Both `tests/test_assembled_corrections_gate.py` benign-rewrite fixtures (`because this paper states each correction where it arises`, `What the assembly settles is where in the interval the mass sits`) survive byte-identically. `ZERO_COUNT` clean, `EXACTLY_ONE` clean, `HARDCODED_XREF` still 0/0 on all five patterns, `$+3.9$ to $+13.1$` still 0, `$+2.9$ to $+8.7$` still 8 (gate wants ≥4), `$+3.0$ to $+8.0$` still 5 (wants ≥2).

**Scope decision taken (C-39, limb 1):** the Ginnie-speed and vintage overlays are **changes of estimand, not corrections**. That is the decision already recorded in `tab:assembly` rows 3–4 (`.tex:346`), in the App.-O adjudication ledger (`.tex:1430`, "landed as a change of estimand — the Ginnie row is relabelled the same way, and neither overlay is a correction to the headline"), and in §V.B (`.tex:269/271`, "confines the identified marginal to …"). The only site that contradicted it was the assembly prose, which introduced the Ginnie rung under a generalisation about "every correction". Limb 2 (re-scoping the benchmark denominator and every recovery percentage) is **not** attempted.

**Judgement taken (C-40):** the attenuation row **qualifies** and is added. See the rationale under Edit 5 — no inclusion rule exists that excludes it while admitting the moving-share bracket, which is a transport sensitivity on the same imported coefficient and is already on the list.

---

## Edit 1 — state the assembly's inclusion rule and carve the two overlays out of "correction" (C-40, C-39)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
Holding the production hard-maximum form and the imported elasticity fixed, every correction to the floor or to the accounting basis moves the headline down.
NEW:
Holding the production hard-maximum form and the imported elasticity fixed, every correction to the floor or to the accounting basis moves the headline down. What sits on the list is fixed by a rule rather than by direction: a reading enters if this paper scores this marginal, over the full window, under a committed run or a committed grid read, labelled with the floor it is scored at and the input it moves, and nothing clearing that bar is held out for running the wrong way --- the survival-selection attenuation included (below). Two of the entries are not corrections at all: the Ginnie-speed and vintage overlays hand a share of the book back, the Ginnie share to its own published speed and the out-of-window vintages to a zero marginal, and re-score the marginal on what remains, so each is the headline scaled by what it retains, $0.797\times$ and $0.6645\times$, with only $0.002$ and $0.001$ points of either move specific to the overlay rather than to the share arithmetic; what they say is what the headline becomes on a narrower book, not that the headline is too high.
RATIONALE: C-40 asks for an inclusion rule, C-39 for one estimand decision applied consistently; both bear on the same sentence, since the sentence generalises over "every correction" and the list under it contains two entries that are not corrections. The rule is stated as direction-neutrality plus a scoring bar ("this marginal, over the full window, under a committed run or a committed grid read"), which is what excludes the temporal-holdout `$+\$45.1$` figure (a 23-held-out-month sum, which `tab:oosfloor`'s note already calls a different object) and the covariate ablation (a level swing) without excluding anything that runs the wrong way.
LITERALS_INTRODUCED:
- `$0.797\times$` — `ginnie_overlay_offwindow_results.json` `marginal_scale_vs_conventional = 0.7975182199226121`; the printed form already exists at `.tex:90` and `.tex:271`.
- `$0.6645\times$` — `vintage_overlay_results.json` `marginal_scale_vs_retained = 0.6644737240199917`; printed form already exists at `.tex:1430`.
- `$0.002$` — `ginnie_overlay_offwindow_results.json` `ginnie_specific_marginal_component_pp = 0.0021157340096635835`.
- `$0.001$` — `vintage_overlay_results.json` `vintage_specific_marginal_component_pp = 0.001041906299988682`.
- Arithmetic check (not printed): $5.5716 \times 0.7975 = 4.4434$ = the `$+4.4$` rung; $5.5716 \times 0.6645 = 3.702$ = the `$+3.7$` vintage row.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none inside this OLD. Downstream effect on gate #98's `posture_lower_half` ("every correction listed above falls in its lower half"): unchanged bytes, and the carve-out makes it *more* precise, since the two overlays are now explicitly not corrections. The paragraph-scoped opener is untouched.

---

## Edit 2 — state the Fannie comparison on one basis at the assembly site (C-26)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
and the Fannie Mae read of the same selection rule on the pooled off-window period, 5.52\%, brackets the marginal below the $+4.3$ edge of the clean band (above).
NEW:
and the Fannie Mae read of the same selection rule on the pooled off-window period, 5.52\%, brackets the marginal below the $+4.3$ edge of the clean band (above) --- a comparison that holds on the pooled period's basis alone, where the like-for-like Freddie read is 5.19\% rather than the 2018 leg's 4.991\%, so 0.337 points of the distance from the clean anchor is agency and the rest is period.
RATIONALE: the "same off-window cell" description is already retired at this site and at `tab:uncertainty` (`.tex:439` now carries "its like-for-like Freddie counterpart 5.185\% rather than the 2018 leg's 4.991\%"), but the assembly — the one place whose purpose is to line the reads up — still lines 5.52\% up beside 4.991\% and 5.51\% without the counterpart, so a reader takes it as a fifth read of one object. This is the remaining C-26 site.
LITERALS_INTRODUCED:
- `5.19\%` — `fannie_floor_read_results.json` `out_of_window_2017_2019` Freddie parity 5.185\% ($n = 438$); the rounded form already appears twice at `.tex:323`.
- `0.337` — same block, `difference_pp` (5.522 − 5.185); already appears at `.tex:323` and `.tex:439`.
- `4.991\%` — committed clean-leg point anchor (`oos_identification_results.json` `clean_floor_point_pct`).
- Arithmetic check (not printed): 5.522 − 4.991 = 0.531, of which 0.337 agency and 0.194 period, which is exactly the split `.tex:323` already states.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: `ASSEMBLY_SPANS["ladder_fannie"] = "5.52\\%, brackets the marginal below the $+4.3$ edge"` is inside this OLD and is preserved **byte-identically** (the insertion is after "(above)", 44 characters downstream of the span's end).

---

## Edit 3 — state the anchor-selection rule and show it against the five-read extension (C-18)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
Carrying the overlay's $0.797$ scaling up to the age-standardized floor projected a marginal near $+3.0$;
NEW:
The anchor is a counting rule and not a pick among the reads: the mid-grid 4.991\% is the median of the run's three committed depth cuts, and extending the 2018 ladder to the two further cuts the ex-ante 10\% support rule admits leaves the clean band unchanged while moving the median of the reads to 4.869\%, between the grid's 4.695\% and 4.991\% rows and therefore a marginal above the headline rather than below it (run \texttt{matched\_depth\_reconciliation}). Carrying the overlay's $0.797$ scaling up to the age-standardized floor projected a marginal near $+3.0$;
RATIONALE: C-18 is the evidence that decides C-17, and the paper's standing name for the anchor — "mid-grid anchor", used at eight sites (`.tex:46, 79, 110, 345, 450, 717, 731, 737`) — is never cashed out into a rule. `.tex:719` already prints the two extra reads and says the band is unchanged, but never says why 4.991\% is the anchor nor what the five reads' median is. The sentence lands the rule at the site where the anchor's standing is argued, and the extension is shown to run *up*, which is the honest direction.
LITERALS_INTRODUCED:
- `4.991\%` as the median of three: `matched_depth_reconciliation_results.json` `step2_matched_depth_grid.OFF_2018_rising_rate.depths` gives the three committed cuts of `oos_identification_results.json`'s `anchor_grid` as 5.334 (gap ≤ 0), 4.991 (≤ −0.0025), 4.695 (≤ −0.005) — median 4.991. Also = the middle depth cut, so "median" and "mid-grid" name the same object.
- `4.869\%` — same block, gap ≤ −0.01, `well_supported = true` at exposure share 0.113374 > the 0.10 rule; five-read median of `clean_band_under_extended_ladder.well_supported_reads_pct = [5.334, 4.991, 4.695, 4.722, 4.869]`. Already printed once at `.tex:719`.
- `4.695\%` — clean-band lower edge, already printed 4×.
- "leaves the clean band unchanged" — `clean_band_under_extended_ladder.band_unchanged_by_extension = true`.
- "a marginal above the headline": monotone from the committed mapping, `floor_to_marginal_mapping.engine_reads` 4.695 → +6.771 pp and 4.991 → +5.572 pp, so a 4.869\% read lies strictly between +5.6 and +6.8.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none. The gate-#98 literal `new_reads` and `clean_band` (in the matched-depth cross-check at `tools/liveness_gates.py:3963–3981`) are substring checks satisfied at `.tex:719`; adding a second citation of `\texttt{matched\_depth\_reconciliation}` moves that gate's `md_claims` count 2 → 3 against a `>= 1` threshold.

---

## Edit 4 — attribute the assembly's one-directionality to its cause and to the unrun correction (C-41)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
so nothing follows from them about what fraction of the dollar marginal the uncensored months carry.
NEW:
so nothing follows from them about what fraction of the dollar marginal the uncensored months carry. That the floor side runs one way is one mechanism read more than once rather than a series of independent verdicts, and it is also an absence: the floor is total deep-discount-cohort turnover rather than a strictly involuntary component of it, so it carries the housing-activity level of the period it is read on, and re-reading it at the window's own level --- the one floor-side correction I can name that would move the anchor down and the marginal up --- is a read this paper holds no activity measure to make.
RATIONALE: the sentence lands immediately after the "one mechanism read twice … raising the floor is what crowds the elasticity out" argument and its censoring-share disclaimer, so the cause is stated before the consequence is drawn. It is a disclosure **addition**: nothing existing is softened or deleted, and the pinned lower-half posture keeps its bytes. The upward correction is named (an activity-matched floor read, C-71's wave-3 run) and its infeasibility here is stated without asserting the external activity comparison, which is not verifiable from the repository.
LITERALS_INTRODUCED: none — zero numeric tokens.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none inside this OLD. `censor_truncated` and `censor_unweighted` sit immediately upstream and are untouched; the insertion point is the sentence boundary after `censor_unweighted`'s clause. `test_benign_rewrites_stay_green`'s fixture `What the assembly settles is where in the interval the mass sits` begins immediately after the insertion and is preserved byte-identically.
NOTE ON HEDGE SCOPE: "the one floor-side correction I can name" mirrors the abstract's existing "every correction I can measure". Do not tighten it to "the one floor-side correction": exhaustiveness is not established.

---

## Edit 5 — put the survival-selection attenuation on the downward side of the assembly (C-40)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
and mildly super-proportional because censored contributions do not scale with $s$.
NEW:
and mildly super-proportional because censored contributions do not scale with $s$. The survival-selection attenuation of the same imported coefficient is a bracket of the same kind and belongs on this side: $a = S^{\theta}$ at the measured pre-window survival share carries the marginal from $+5.1$ to $+3.7$ over $\theta = 0.25$ to $1$ (run \texttt{attenuation\_sensitivity}), with $\theta$ free (Section~\ref{sec:pathb}) --- a different axis from the elasticity band, not a widening of it.
RATIONALE: this is the substantive C-40 call. The exclusion ground now printed at `.tex:439` — "a transport sensitivity on the imported coefficient, kept out of the assembly on that ground" — does not discriminate: the moving-share bracket in the immediately preceding clause is also a transport sensitivity on the same imported coefficient (`.tex:231` names both as "further transport assumptions [that] travel with the import"; `.tex:261` introduces the bracket as pricing "what the elasticity applies to"), it is also a bracket in a free parameter, and it is on the list. The sub-band $\delta = 3.25\%$ member and the Fonseca anchor are also moves of the imported coefficient and are on the list. I found no rule that keeps the attenuation out while admitting those three, and the paragraph's own claim two sentences earlier is that "Specification choices that are not floor corrections run both ways, and this assembly now lines both directions up" — which a withheld downward member falsifies. Adding it costs no evidential ground: the grid, the mapping and the free-parameter caveat are already printed at `.tex:231` and `.tex:439`; only its membership changes.
LITERALS_INTRODUCED:
- `$+5.1$` / `$+3.7$` at `$\theta = 0.25$ to $1$` — `attenuation_sensitivity_results.json` `monotonicity["4.991"].marginal_pp_ordered = [5.5716, 5.0955, 4.6177, 3.7037]` against `a_grid_descending = [1.0, 0.8558, 0.7324, 0.5365]`, i.e. $\theta = 0/0.25/0.5/1$. Both endpoints already printed at `.tex:231` and `.tex:439`.
- `$a = S^{\theta}$` — `selection_identity.form`, $S = 40{,}234/75{,}000 = 0.5364533$ (`S_numerator`/`S_denominator`).
- "$\theta$ free" — `selection_identity.free_parameter_note` ("theta is not estimated in this design"); `.tex:231` already says "$\theta$ is not estimable in this design and is displayed as the free parameter".
- "a different axis from the elasticity band, not a widening of it" — the artifact's own `not_an_elasticity_band_widening` instruction, carried verbatim in content.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none. `counter_additive`, `counter_fonseca` and `counter_three_readings` all sit in the same sentence chain and are untouched; the insertion is at a sentence boundary between the Downward list and "A calibrated companion prices the omitted housing-activity level term".
**REQUIRES the two companion edits at the end of this file.** Without them the manuscript says both "listed" and "kept out of the assembly".

---

## Edit 6 — tab:assembly gains the attenuation row (C-40)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
Moving-share bracket, $s = 0.25$, off-window & $+1.8$ & below the interval & the bracket's deep stress; edge by construction \\
NEW:
Moving-share bracket, $s = 0.25$, off-window & $+1.8$ & below the interval & the bracket's deep stress; edge by construction \\ Survival-selection attenuation, $\theta = 0.25$ to $1$ & $+5.1$ to $+3.7$ & below & bracket in a free parameter: $a = S^{\theta}$ on the imported coefficient, $\theta$ not estimable here; a different axis from the elasticity band (run \texttt{attenuation\_sensitivity}) \\
RATIONALE: placed with the other brackets rather than beside the concave row, so the row reads as what it is and its `$+5.1$` endpoint is not mistaken for the concave transform's `$+5.1$`. The marginal column is given as the range over $\theta$, not as a triple, so it cannot read as three point estimates, and the `$+3.7$` endpoint cannot be confused with the vintage overlay's `$+3.7$` two rows up (different object, different column content). The "vs. $+5.6$" cell is `below` for both endpoints (5.0955 and 3.7037).
LITERALS_INTRODUCED: as Edit 5; no new full-precision values.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none — `ASSEMBLY_TABLE_SPANS` pins only `\label{tab:assembly}`, the paragraph anchor, the composed row and the Fonseca row, all untouched. Row-cell count on line 349 goes 18 → 21 ` & ` separators, i.e. 6 → 7 four-column rows; `$` count stays even.
BUILD NOTE: `tab:assembly` is `[H]` and cannot float. One extra row plus the ~430 words the paragraph gains may push the float; check the 130-page build for an overfull page here, and if it breaks, the cheapest lever is dropping "; a different axis from the elasticity band" from the row (the prose carries it).

---

## Edit 7 — tab:assembly row 2 says what "mid-grid" means (C-18)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
Off-window re-anchor & $+5.6$ & headline & mid-grid anchor inside the binding interval \\
NEW:
Off-window re-anchor & $+5.6$ & headline & mid-grid anchor (median of the three committed depth cuts) inside the binding interval \\
RATIONALE: C-18's location list names this row. The paper's term "mid-grid anchor" is kept — it is used at eight sites and dropping it here would leave `tab:assembly` the only site not using it — and glossed with the rule Edit 3 states in prose.
LITERALS_INTRODUCED: none.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none.

---

## Edit 8 — tab:assembly's Fannie row carries the like-for-like counterpart (C-26)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
Fannie floor read (5.52\%) & below $+4.3$ & below & bracketing; second agency, pooled period \\
NEW:
Fannie floor read (5.52\%) & below $+4.3$ & below & bracketing; second agency, pooled period; like-for-like Freddie 5.19\% \\
RATIONALE: the row already says "pooled period", which retires cell identity, but the table is a lining-up exhibit and the 5.52\% sits two rows under a 4.991\%-based ladder. The counterpart makes the one-basis reading available in the exhibit itself.
LITERALS_INTRODUCED: `5.19\%` — as Edit 2.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none.

---

## CENSUS

Fixed-string counts over the whole canonical file, measured with `str.count` on the in-memory result of applying Edits 1–8 in order.

| literal / phrase | before | after |
|---|---|---|
| `0.797` | 5 | 6 |
| `$0.797\times$` | 2 | 3 |
| `0.6645` | 1 | 2 |
| `$0.6645\times$` | 1 | 2 |
| `$0.002$` | 3 | 4 |
| `$0.001$` | 0 | 1 |
| `5.19\%` | 2 | 4 |
| `4.991\%` | 17 | 20 |
| `0.337` | 2 | 3 |
| `4.869\%` | 1 | 2 |
| `4.695\%` | 4 | 5 |
| `10\% support rule` | 1 | 2 |
| `$+5.1$` | 5 | 7 |
| `$+3.7$` | 5 | 7 |
| `mid-grid` | 9 | 10 |
| `median` | 16 | 19 |
| `S^{\theta}` | 2 | 4 |
| `survival-selection` | 1 | 3 |
| `free parameter` | 3 | 4 |
| `overlay-specific` | 0 | 0 |
| `\texttt{attenuation\_sensitivity}` | 3 | 5 |
| `\texttt{matched\_depth\_reconciliation}` | 2 | 3 |
| `5.334\%` | 5 | 5 |
| `5.52\%` | 8 | 8 |
| `5.51\%` | 7 | 7 |
| `$+4.4$` | 8 | 8 |
| `$+9.2$` | 25 | 25 |
| `$+5.6$` | 25 | 25 |
| `$+3.8$` | 5 | 5 |
| `$+1.8$` | 1 | 1 |
| `$+2.9$ to $+8.7$` | 8 | 8 |
| `$+3.0$ to $+8.0$` | 5 | 5 |
| `$+3.5$ to $+13.1$` | 7 | 7 |
| `$+3.9$ to $+13.1$` | 0 | 0 |
| `change of estimand` | 3 | 3 |
| `not a correction` | 3 | 3 |
| `kept out of the assembly` | 2 | 2 (→ 0 with the companion edits) |

Structural:

| object | before | after |
|---|---|---|
| assembly paragraph, words | 968 | 1401 |
| assembly paragraph, chars | 6,252 | 8,805 |
| whole document, words | 66,783 | 67,266 (+483) |
| abstract (line 31) | untouched, 294 words | untouched, 294 words |
| gate #98 `ASSEMBLY_SPANS` present | 15/15 | 15/15 |
| gate #98 `ASSEMBLY_TABLE_SPANS` present | 4/4 | 4/4 |
| `A seventh qualification` paragraphs | 1 | 1 |
| `tab:assembly` body rows on line 349 | 6 | 7 |

---

## REQUIRED COMPANION EDITS — OUTSIDE MY REGION, MUST LAND WITH EDITS 5–6

Adding the attenuation row falsifies the two sites that record its exclusion. Both spans are unique, neither is gate- or test-pinned (`grep` for `kept out of the assembly` in `tools/` and `tests/` returns nothing). I have **not** drafted them as edits because they sit in `tab:uncertainty`'s headline row and in App. O, where C-24/C-25/C-27 drafters are working; exact bytes for the coordinator:

**Companion A — `.tex:439`, `tab:uncertainty` headline row (count 1):**
OLD: `(run \texttt{attenuation\_sensitivity}; a transport sensitivity on the imported coefficient, kept out of the assembly on that ground)`
NEW: `(run \texttt{attenuation\_sensitivity}; a transport sensitivity on the imported coefficient, listed in Table~\ref{tab:assembly} as a bracket in $\theta$ rather than as a correction)`

**Companion B — `.tex:1430`, App. O adjudication ledger (count 1):**
OLD: `Enforced: reported as committed; kept out of the assembly (a transport sensitivity on an imported coefficient, not a correction to the paper's own object) (neutral)`
NEW: `Enforced: reported as committed; listed in the assembly as a bracket in $\theta$ rather than as a correction (a transport sensitivity on an imported coefficient, and $\theta$ is not estimable) (downward)`

The ledger's trailing direction label moves `(neutral)` → `(downward)`; `(neutral)` goes 13 → 12 and `(downward)` 1 → 2. Neither label is counted by any gate. If the coordinator declines the companion edits, **drop Edits 5 and 6** and re-open C-40 — the alternative branch (a stated rule that the attenuation fails) is not available on the evidence recorded under Edit 5.

---

## UNVERIFIED

1. **The five-read median's marginal in points.** C-18's block quotes "~+6.0pp by the printed delta = 6.5 column". No committed artifact carries a floor→marginal read at 4.869\%: `floor_sweep_results.json`'s grid is {2, 3, 3.5, 4, 4.5, 5, 6}\% and the 4.695/4.991 reads in `matched_depth_reconciliation_results.json` are PCHIP interpolations of it. I therefore printed the bracketing statement (between the 4.695\% and 4.991\% rows, hence above the headline) instead of a `+6.0` literal. Confirmed by: `floor_to_marginal_mapping.engine_reads` 4.695 → 6.771 pp, 4.991 → 5.572 pp. If the coordinator wants the number printed, it needs a PCHIP read the committed artifacts do not contain.
2. **Whether the activity-matched floor read is *the* only upward floor-side correction.** C-71's severity line asserts it; I could not verify exhaustiveness, so Edit 4 says "the one floor-side correction I can name". Confirmed only in part: that the floor is total deep-discount-cohort turnover (hence activity-level dependent) is the paper's own wording at `.tex:92` and `.tex:227`.
3. **The external activity comparison (2018 vs the window).** Not asserted anywhere in Edit 4. C-71 records the 5.34M/4.09M existing-home-sales figures as external NAR data absent from the repository; "existing-home sales" does not occur in the .tex. Edit 4's direction claim is therefore conditional on nothing — it says only that re-reading at the window's activity level *would* move the anchor down and the marginal up, which is the direction the activity-dependence implies, without claiming which period was more active. Confirming it needs the external series.
4. **Build effect.** I did not compile. The paragraph gains ~430 words and `tab:assembly` (an `[H]` float) gains one row; a page-break check at this site is required.
5. **Long-abstract variant.** Not inspected beyond the coordinator's statement that it differs only at line 31. None of my eight OLD spans is on line 31, so all eight should apply to the variant unchanged; the coordinator's mirror step should confirm the eight counts of 1 there too.

---

## WORD_COUNT_IMPACT

**No edit touches line 31.** The abstract is byte-identical before and after (verified: `t.split("\n")[30] == new.split("\n")[30]`), so it remains 294 words and gate #101's tie to the response letter's claimed count is unaffected.

Body word delta: **+483 words** (assembly paragraph +433, `tab:assembly` +50). If the length queue binds, the cheapest cuts that keep every condition satisfied are (a) Edit 1's parenthetical "with only $0.002$ and $0.001$ points of either move specific to the overlay rather than to the share arithmetic" (−22 words, but then "scaled by what it retains" loses its evidence), and (b) Edit 5's closing clause "--- a different axis from the elasticity band, not a widening of it" (−13 words, but that clause is the artifact's own standing instruction and the table row would then be its only carrier).

C-41's fix line also asks for the clause to be "mirrored in the abstract's hedge". I did not touch the abstract, and I do not think it needs touching: it already reads "every correction **I can measure** to the baseline turnover floor or to the accounting basis moves it down within the range rather than up", which carries exactly the "the unmeasured ones need not" content C-41 (§2.2) asks for. Flagging rather than acting, since the abstract is another drafter's region.
