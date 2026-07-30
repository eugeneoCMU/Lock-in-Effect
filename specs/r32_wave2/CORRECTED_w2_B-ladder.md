# R32 Wave 2 — CORRECTED edit set, cluster B-ladder (C-05, C-20, C-21, C-24, C-25, C-27, C-38, C-69)

FILE for every edit: `paper/v18/revised_paper_v18.tex` in the worktree
`/Users/eugene/somthing/Lock In effect/Lock-in-Effect/.claude/worktrees/agency-mbs-runoff-qt-424945/`.
Nothing in the worktree was modified; no repo script was executed. All counts below were measured with
`str.count` on fixed strings against the **current** file (1,461 lines) and, for the after-column, on the
in-memory result of applying all 14 edits in order (each OLD matched exactly once).

**Re-anchoring result: 14 of 14 OLDs still count exactly 1 on current bytes — 0 byte-level repairs needed.**
Every line number moved, though; the draft's numbers are dead. Current anchors:
E1 L337 · E2 L343 · E3 L355 · E4 L355 · E5 L461 · E6 L468 · E7 L468 · E8 L472 · E8b L478 · E9 L485 ·
E10 L495 · routed R1 L287 · R2/R3 L554. Two CENSUS **baselines** in the draft were stale and are repaired
here: `6.0\%` was 17, is 19; the imported-band literal the draft planned to add (`5.5--7.7\%`) is the
tab:params form — the four body-prose sites use `5.5\%--7.7\%`, which is what E6 now uses.

Artifact: `hazard/data/floor_inference_correction_v2_results.json`,
`reads["R2_2018_gap<=-0.0025_age>=12"]` (read, not run). Confirmed from it, against the verdict:
`cr3_t_interval_df_bm.lower_pp_edge` = {floor_pct 6.115978, mapped_at_pct 6.0, truncated true};
`wcr_inverted.lower_pp_edge` = {floor_pct 6.181252, mapped_at_pct 6.0, truncated true}; both **upper**
edges interior (floors 3.852918 / 4.033460, truncated false); `cr2_t_interval_df_bm` **both** edges
interior (floors 5.953706 / 4.018509) at [2.409788, 9.149769]; `wild_t_webb.floor_ci95_pct`
[4.176744, 5.800285] brackets `point_cpr_pct` 4.990624; `leverages_h` top two 0.332331 / 0.171662
(ratio **1.9360**, sum 1.0); `G_star_css` 5.871714; `n_clusters` 31; top-level `spec` = "**Webb
six-point** wild-cluster bootstrap-t ... as the PRIMARY floor-read interval", `spec_source`
`specs/SPEC_round28_C1_C2_C3_C6.md SPEC C1`.

---

## Edit 1 — strike the forced monotonicity from the identified-content list (C-38)
OLD_COUNT_ASSERT: 1
OLD:
the identified content is the marginal's \emph{bounded range}, together with the monotone response across the Liebersohn--Rothstein band, and neither its point magnitude nor its sign
NEW:
the identified content is the marginal's \emph{bounded range}, and neither its point magnitude nor its sign
WHY: the band's monotone response is forced by the same composition-of-monotone-maps argument L343 already uses to demote the 27-cell positivity check, so it cannot sit in the identified content beside the bounded range.
FIX_FOLDED: none — unchanged from draft (OLD re-measured at 1 on L337).
LITERALS: none.
PINS: no gate/test constant is a substring of this OLD (AST sweep over `tools/liveness_gates.py` + `tests/*.py`, all string constants of length ≥ 6).

## Edit 2 — put the monotone response on the positivity footing, demoting the ORDERING not the sweep (C-38)
OLD_COUNT_ASSERT: 1
OLD:
This is why the reported range, and not the sign, carries the paper's identified content.
NEW:
This is why the reported range, and not the sign, carries the paper's identified content. The band's monotone response is forced the same way: \eqref{eq:beta1} is monotone in $\delta$ and the hazard is monotone in $\beta_1$ at that gap, so the band's ordering is a composition of monotone maps. I retain that ordering as a wiring check on the same footing, not as identified content; the sweep's endpoints stay the convention range they are.
WHY: carries the disclosure instead of deleting it — the numbers and the sweep stay, only the ordering's evidential status changes, mirroring the sentence three clauses earlier ("verifies the specification ... rather than identifying the mechanism, and I retain it on that footing").
FIX_FOLDED: CONVENTION_VIOLATIONS #2 — the draft demoted "the band sweep", whose endpoints are quoted as a live convention sensitivity range on L337 ("$+5.0$ to $+12.6$ points over the full band"), in tab:floorband, tab:oosfloor and tab:lowband. Now scoped to the ordering, with an explicit guard clause. Also folded the paragraph's own "the rate gap is negative in every cell of every sweep reported here" — the draft restated it; NEW points back with "at that gap" (concision).
LITERALS: none. `\eqref{eq:beta1}` is an existing label (`\label{eq:beta1}` count 1, 10 `\eqref` sites).
PINS: OLD **is** the pinned literal `"This is why the reported range, and not the sign, carries the paper's identified content."`; NEW reproduces it byte-identically as its prefix (count 1 → 1). The neighbouring pins `"positive at every"` (6 → 6, gate at :4140 needs ≥ 6), `"verifies the specification"`, `"the panel ends two months before the window does"` are outside OLD.

## Edit 3 — nest the sampling interval inside the convention envelope, and name the within-layer choice (C-24, C-20)
OLD_COUNT_ASSERT: 1
OLD:
and the uncomposed pair falls near its bottom. I attach no posture
NEW:
and the uncomposed pair falls near its bottom. The convention span and the sampling interval are nested rather than alternative: the seasoning-ramp sweep is the outer statement, and $+2.9$ to $+8.7$ is a sampling interval on the floor read alone, nested inside it at the production 100~PSA ramp. Which rung of that inner layer to quote is a further choice the rule does not settle: the Webb wild-$t$ read quoted here is the third-narrowest of the nine undemoted rungs, and the widest rung with both endpoints interior to the floor grid---CR2 at Bell--McCaffrey degrees of freedom, $+2.4$ to $+9.1$ points---stands beside it rather than behind it. I attach no posture
WHY: C-24's outer/nested statement said once, where the selection rule lives; C-20's finding stated as a within-layer choice, which is what it is — the rule's LAYER ranking in the pinned sentence is correct and untouched.
FIX_FOLDED: REFUTED #8 (the antecedent) — "Those two spans" took the wrong nearest antecedent ($+3.0$ to $+8.0$ and $+2.9$ to $+8.7$); the two are now named. REFUTED #7 — the draft's "the ten rungs of Table~\ref{tab:ladder} span 5.0 to 7.3 points of width" quoted a grid-censored maximum three sentences before E10 discloses the censoring; **dropped entirely** rather than qualified (the literal `5.0 to 7.3` now never enters the file: 0 → 0). CONVENTION_VIOLATIONS #4 — the draft re-stated "the production hard-maximum form ... the central elasticity", which this same paragraph's opener fixes at offset 259 of L355 ("Holding the production hard-maximum form and the imported elasticity fixed"); dropped, leaving only the ramp, which the opener does **not** fix and which is the whole nesting fact. "untruncated" replaced by "with both endpoints interior to the floor grid" so the phrase cannot be read as the draft's inverted truncation story.
LITERALS:
- `$+2.9$ to $+8.7$` — one further occurrence; `wild_t_webb.marginal_ci95_pp` [2.854995, 8.677972], already printed 8× in the file.
- `100~PSA` — existing convention literal (2 sites). Licensed without a new read by this paragraph's own arithmetic: `scaled_null_housing_activity` root $\phi^{*}=0.754$ is printed as "effectively 75.4 PSA" and the $\phi=1$ cells reproduce the committed values, so production $\phi=1$ is 100 PSA; `app:params` prints the 100 PSA seasoning ramp.
- `$+2.4$ to $+9.1$` — `cr2_t_interval_df_bm.marginal_ci95_pp` [2.409788, 9.149769], `lower_pp_edge.truncated_at_grid_edge` false, `upper_pp_edge.truncated_at_grid_edge` false. Already printed once, as the tab:ladder row.
PINS: the insertion sits between `ASSEMBLY_SPANS["posture_lower_half"]` ("every correction listed above falls in its lower half") and `["posture_retired_range_carries"]`; both survive byte-identically **and in order**. All 15 ASSEMBLY_SPANS + 4 ASSEMBLY_TABLE_SPANS stay at count 1 (verified by AST-extracting the dicts). L355 still `startswith("A seventh qualification")` and is still the only such line (gate #98). `test_headline_posture_gate` needs `"$+2.9$ to $+8.7$ points"` in that line — the pinned occurrence inside `posture_binding_layer` is untouched; my new occurrence deliberately carries no trailing " points" (that literal stays at 7).

## Edit 4 — say the externally anchored member lies outside the quoted interval, SCOPED to the headline floor (C-69)
OLD_COUNT_ASSERT: 1
OLD:
The variant documents an upward bias; the corrected member lies below the headline, at the bottom of the seasoning-ramp span just swept.
NEW:
The variant documents an upward bias; the corrected member lies below the headline, at the bottom of the seasoning-ramp span just swept, and at the headline floor it falls outside the quoted $+2.9$ to $+8.7$ interval---an externally anchored calibration the quoted interval does not cover, not a challenge to the sign; at the in-sample calibration it falls inside.
WHY: the paragraph already prints the root ($\phi^{*}=0.754$) and the $+0.9$/$+3.5$ pair; *outside* was the one word it never said. The trailing clause keeps the exclusion from reading as a contradiction of the sign result.
FIX_FOLDED: REFUTED #3 — the draft's unscoped "outside" was **false of the second member the same antecedent covers**: `scaled_null_housing_activity_results.json` root["4.991"].marginal_pp 0.8979 is outside [2.855, 8.678] but root["4"].marginal_pp 3.4680 is inside. Now scoped to the headline floor, and the in-sample member's containment is disclosed rather than dropped (7 words, and it is the honest half of C-69). CONVENTION_VIOLATIONS #4 — "outside" appeared twice in the draft's one sentence; now once ("does not cover" carries the second).
LITERALS: `$+2.9$ to $+8.7$` (one further occurrence, same artifact source as E3). No new numeric value: both $+0.9$ and $+3.5$ are already in this paragraph, and inside/outside is arithmetic on committed values.
PINS: no gate/test constant is a substring of OLD. (`"the corrected member lies below the headline (downward)"` is a different string, in the App. O ledger; untouched. The `psa_level_sweep`/`fonseca2024`/`aladangady2024` pins in this paragraph are outside OLD.)

## Edit 5 — T8 headline row: scope "binding layer", name the held-fixed conventions, exclude transport (C-05, C-24, C-27)
OLD_COUNT_ASSERT: 1
OLD:
(the binding layer, and a sampling interval on the floor read alone rather than on the elasticity;
NEW:
(the binding layer among those with a coverage property---the unestimated baseline-level convention spans wider---and a sampling interval on the floor read alone at the production hard-maximum form and the 100~PSA ramp, pricing neither the elasticity nor the read-to-read spread across the floor reads in the next column;
WHY: C-05 at the inventory's `.tex:433` (now L461), reusing the scope formulation already in the file so a cell read on its own cannot overstate the ranking; the cell's own calibration column carries both things the interval does not price, so the exclusion is a pointer, not a new disclosure.
FIX_FOLDED: CONVENTION_VIOLATIONS #4 — the draft said "in the next column" twice in one cell; the first is now "the unestimated baseline-level convention", which is the file's own existing wording (App. O scope site, count 1) rather than a new phrasing.
LITERALS: `100~PSA` (see E3). No numeric value introduced; the cell keeps `$[+2.9, +8.7]$pp`, `$\delta = 6.5\%$`, `$[+3.0, +8.0]$pp`, `$[+4.63, +6.92]$pp`, `$0.39\times$`, `25.8`, `$[+2.80, +8.99]$pp`, `$8.12$pp`.
PINS: gate #105's `"independence is assumed, not measured"` and `"under maximal positive dependence the width is $8.12$pp"` sit later in the same cell, both 1 → 1. The gate at :4616–4621 needs `count("$+3.0$ to $+8.0$") >= 2` (5 → 5), `count("$+2.9$ to $+8.7$") >= 4` (8 → 10) and `"binding layer" in tex` (10 → 10; the phrase is extended, never replaced).

## Edit 6 — Notes to T8: scope the interval, name what it is a sampling interval AROUND, and rule out an elasticity layer (C-05, C-25, C-27)
OLD_COUNT_ASSERT: 1
OLD:
and the headline row quotes the wild-$t$ interval as the binding layer. That interval prices one layer: the floor read's own sampling error, propagated through the frozen floor-to-marginal grid at the central elasticity $\delta = 6.5\%$, so none of its width comes from the elasticity, which is swept separately in the calibration column and in Table~\ref{tab:lowband}.
NEW:
and the headline row quotes the wild-$t$ interval as the binding layer among those with a coverage property. That interval prices one layer: the floor read's own sampling error around the 4.991\% point read, propagated through the frozen floor-to-marginal grid at the production hard-maximum form, the 100~PSA ramp and the central elasticity $\delta = 6.5\%$, so none of its width comes from the elasticity, which is swept separately in the calibration column and in Table~\ref{tab:lowband} --- swept over the published 5.5\%--7.7\% range as a convention, not estimated, so no layer of this paper's accounting prices sampling error in the elasticity itself.
WHY: C-05's scope and C-25's stronger claim (no layer anywhere prices elasticity sampling error) land in the note where the interval is claimed. Stays a post-float `\noindent{\footnotesize ... \par}` paragraph; nothing moves into the float.
FIX_FOLDED: REFUTED #2 — the draft's "none of them enters it" was **false of the 4.991\% read**: `wild_t_webb.floor_ci95_pct` [4.176744, 5.800285] brackets `point_cpr_pct` 4.990624, so the interval IS the sampling distribution around that read. NEW names it as such, which makes the transport exclusion precise without a separate sentence. CONVENTION_VIOLATIONS #5 — `5.5--7.7\%` (tab:params form) replaced by the body-prose form `5.5\%--7.7\%` (4 existing sites).
LITERALS:
- `4.991\%` — one further occurrence; `point_cpr_pct` 4.990624 (17 → 18; already this table's calibration-column read).
- `5.5\%--7.7\%` — one further occurrence; the imported band, `liebersohn2024`, printed at §II, §V.B ×2 and §VII (4 → 5).
- `100~PSA` (see E3). No new numeric value.
PINS: this note also carries `"floor\_inference\_correction"`, `"it does not bracket floor cyclicality"`, `"makes the convolved line a lower bound as well"`, `"$+11.22$ to $+11.27$"` — all outside OLD, all 1 → 1. Every `%` in NEW is escaped, so the gates' `re.sub(r'(?<!\\)%.*','')` normalisation is unaffected.

## Edit 7 — the Rademacher–Webb near-identity stops being a stability claim (C-21)
OLD_COUNT_ASSERT: 1
OLD:
The ladder's reads agree: the Rademacher and Webb constructions land with both endpoints within a tenth of a point, a re-printing rather than a substantive move, while the small-sample degrees of freedom and the restricted inversion are wider, all agreeing in location and none crossing zero.
NEW:
The ladder's reads agree in location and none crosses zero, and the closest agreement among them carries no information: the Rademacher and Webb constructions land with both endpoints within a tenth of a point, a re-printing rather than a substantive move, because both are sign-symmetric reweightings of the same residuals, so each bootstrap distribution turns on the draw's sign for the one cluster carrying a third of the total leverage---nearly twice the next largest (Table~\ref{tab:ladder}). Their coincidence re-prints that cluster's influence instead of testing it. The small-sample degrees of freedom and the restricted inversion are wider.
WHY: the agreement was framed as the ladder's corroboration; the corroboration that survives — location and zero-exclusion — leads the sentence, and the near-identity now carries the mechanical reason it is uninformative. Nothing numeric is deleted.
FIX_FOLDED: REFUTED #5 — "symmetric two-signed reweightings" is Rademacher-accurate and Webb-**in**accurate (top-level `spec`: "Webb **six-point** wild-cluster bootstrap-t"); now "sign-symmetric reweightings" / "the draw's sign", both true of six-point Webb. REFUTED #6 — `leverages_h` ratio is 1.9360, so "twice" overstated; now "nearly twice". CONVENTION_VIOLATIONS #3 — the 0.33 leverage, the 5.9 effective clusters and the 31 nominal clusters live in the Notes to tab:ladder, not here; a `Table~\ref{tab:ladder}` pointer now sources the fraction.
LITERALS: none. "a third of the total leverage" and "nearly twice the next largest" are words read off `leverages_h` (0.332331 of `sum_h` 1.0; next 0.171662; ratio 1.9360). The printed gap is 0.0587pp lower / 0.0451pp upper — under a tenth of a point, as already printed.
PINS: `"a re-printing rather than a substantive move"` matches no gate/test constant but is kept verbatim anyway (1 → 1). `"The ladder's reads agree"` 1 → 1.

## Edit 8 — tab:ladder caption carries the binding-layer scope, and stops calling rungs layers (C-05, layer/rung convention)
OLD_COUNT_ASSERT: 1
OLD:
\caption{The inference ladder on the binding layer. Every row prices one layer
NEW:
\caption{The inference ladder on the binding layer---binding among the layers with a coverage property; the unestimated baseline-level convention spans wider. Every row is one rung on that layer
WHY: C-05 at the inventory's `.tex:444` (now L472), reusing the file's existing scope formulation verbatim; and the caption's own next clause already defines the single layer all rows share ("--- the floor read's own sampling error ... ---"), so "one rung on that layer" is what it meant.
FIX_FOLDED: CONVENTION_VIOLATIONS #1 — the draft inserted "layers with a coverage property" one clause from "Every row prices one layer", putting both senses of *layer* in one caption while E3/E10 call the same rows rungs. Paired with E8b, prose and table now agree and the pre-existing conflation is reduced, not worsened.
LITERALS: none.
PINS: gate #107 pins `FLOOR_LADDER_SPANS["run_credit"]` = `\texttt{floor\_inference\_correction} (Rademacher wild-$t$; CR1--CR3 at $t(30)$)` in this caption's last sentence — outside OLD, 1 → 1. `"Every row prices one layer"` matches no gate/test constant (AST-verified, all string constants length ≥ 6).

## Edit 8b — tab:ladder column header: Layer -> Rung (layer/rung convention) — NEW, not in the draft
OLD_COUNT_ASSERT: 1
OLD:
Layer & Marginal (pp) & Degrees of freedom & Status
NEW:
Rung & Marginal (pp) & Degrees of freedom & Status
WHY: the header was the source of the conflation the conventions name. Four characters, one column, no width risk (the column is set by "Restricted wild-cluster inversion", 34 chars).
FIX_FOLDED: CONVENTION_VIOLATIONS #1 (the half the draft left undone).
LITERALS: none.
PINS: `"Layer & Marginal"` and the full header string match **no** gate or test constant — AST-extracted every string constant of length ≥ 6 from `tools/liveness_gates.py` and `tests/*.py` (1,830 at length ≥ 14; the ≥ 6 sweep is what the census below reports) and neither appears. Both `.count(...) == 1` asserts in `tests/test_floor_ladder_gate.py` are over `FLOOR_LADDER_SPANS["cr1_conventional"] + " \\\\\n"` (1 → 1) and the four printed values (all 1 → 1); `tests/test_assembled_corrections_gate.py`'s is over ASSEMBLY_TABLE_SPANS (all 1 → 1).

## Edit 9 — Webb row status cell says it is not the widest (C-20, C-05) — WIDTH-CONTINGENT
OLD_COUNT_ASSERT: 1
OLD:
Wild-$t$, Webb & $+2.9$ to $+8.7$ & bootstrap, $B = 9{,}999$ & primary; the binding layer
NEW:
Wild-$t$, Webb & $+2.9$ to $+8.7$ & bootstrap, $B = 9{,}999$ & primary; the binding layer, not the widest
WHY: the row that names itself primary should not let a reader infer it is the ladder's conservative end.
FIX_FOLDED: none — unchanged from draft; the verdict did not attack it.
LITERALS: none.
PINS: OLD contains the pinned `$+2.9$ to $+8.7$`, reproduced byte-identically in NEW (file count 8 → 10, and the only gate reading it needs ≥ 4). Gate #107's two `.index()` ordering asserts re-evaluated on the edited text: `cr1_conventional` < `"CR2 $t$ & $+3.0$ to $+8.6$"` TRUE; `cr1_bell_mccaffrey` < `"CR2 $t$, Bell--McCaffrey"` TRUE.
**COORDINATOR DECISION:** drop if the rebuild reports an overfull `\hbox` on tab:ladder — the status cell goes from 25 to 42 characters against today's widest, "demoted; under-covers at 31 clusters" (36), in a plain `@{}llll@{}` tabular. C-20 is fully carried by E3 and E10 without it. I cannot build (read-only).

## Edit 10 — Notes to tab:ladder: why wild rather than Bell–McCaffrey, the wider interior rung, and the censoring in the right direction (C-20)
OLD_COUNT_ASSERT: 1
OLD:
That concentration is why the wild-cluster correction is applied and the percentile read demoted.\par}
NEW:
That concentration is why the wild-cluster correction is applied and the percentile read demoted. It does not rank the wild construction against the Bell--McCaffrey degrees of freedom, and I do not claim it does: the wild rows re-draw cluster-level weights at that same leverage profile, the Bell--McCaffrey rows keep the sandwich and correct the reference distribution's degrees of freedom for it, and at 5.9 effective clusters neither correction dominates. So the Webb row is the primary read and the interval this paper quotes, but it is the third-narrowest of the nine undemoted rungs, and the widest rung with both endpoints interior to the floor grid---CR2 at Bell--McCaffrey degrees of freedom, $+2.4$ to $+9.1$ points---belongs beside it rather than behind it. The two rungs printed wider still understate their own width: CR3 at Bell--McCaffrey degrees of freedom and the restricted inversion have \emph{lower} endpoints at floors above the committed grid's 6.0\% end and are censored to it, and the marginal falls as the floor rises, so both run below the $+2.3$ printed; their upper endpoints are interior.\par}
WHY: C-20's substantive fix, in the note that already carries $G^{*} = 5.9$, $h_{\max} = 0.33$ and the 31 clusters, so the reason lands where its inputs are. It takes the concession route *and* quotes the wider rung.
FIX_FOLDED: REFUTED #1 (the verdict's most serious) — the draft said the two widest rungs "reach $+2.3$ only because their \emph{lower} endpoints clip the 6.0\% end", which reads as a discount and **inverts the artifact**. The clip raises those lower endpoints: uncensored floors are 6.115978 (CR3-BM) and 6.181252 (WCR), the marginal falls as the floor rises, so the true lower ends are **below** +2.2809 and the printed spread is **narrower** than the truth. NEW states it as an understatement ("understate their own width ... both run below the $+2.3$ printed"). REFUTED #4 — "the wild rows build their reference distribution by re-drawing the leverage profile" is mechanically wrong and contradicted E7 three lines earlier; now "re-draw cluster-level weights at that same leverage profile". Under concision, the draft's two new floor literals (6.12\%/6.18\%) were dropped in favour of "at floors above the committed grid's 6.0\% end", which says the same thing with no new number.
LITERALS:
- `$+2.4$ to $+9.1$` — `cr2_t_interval_df_bm.marginal_ci95_pp` [2.409788, 9.149769]; both edges `truncated_at_grid_edge` false (floors 5.953706 / 4.018509).
- `$+2.3$` — one further occurrence; `cr3_t_interval_df_bm.marginal_ci95_pp[0]` = `wcr_inverted.marginal_ci95_pp[0]` = 2.280915, both `lower_pp_edge.truncated_at_grid_edge` true, `mapped_at_pct` 6.0.
- `6.0\%` — one further occurrence; `mapped_at_pct` 6.0, the committed floor grid's upper end.
- "5.9", "third-narrowest", "nine undemoted rungs" reuse `G_star_css` 5.871714 (already printed here as 5.9) and the measured widths (percentile 5.0442, CR1-t 5.1967, CR2-t 5.5787, **Webb 5.8230**, Rademacher 5.9268, CR3-t 6.0012, CR1-BM 6.0431, CR2-BM 6.7400, WCR 6.8284, CR3-BM 7.2836 — Webb third-narrowest of the nine undemoted, CR2-BM widest with both edges interior).
PINS: this note carries three gate-#107 spans — `FLOOR_LADDER_SPANS["df_ownership"]`, `["cr1_is_the_baseline"]`, `["printed_tie_is_not_an_identity"]` — all preceding OLD, all 1 → 1. NEW introduces none of `$+3.2$ to $+8.3$`, `$+2.8$ to $+8.8$ & $t(6.2)$`, `$t(6.2)$`, `4.177\% to 5.800\%` (each stays exactly 1, as `tests/test_floor_ladder_gate.py` asserts); that is why it spells "CR2 at Bell--McCaffrey degrees of freedom" instead of reusing the row labels, and never prints a bare `$t(6.2)$`. Stays a post-float paragraph.

---

## COORDINATOR-ROUTED — C-38's three companion sites (OUTSIDE my region)

C-38 is "strike the clause at all four sites". One is §V.E (E1–E2). These three are §V.B and §V.F. Each OLD
re-measured at exactly 1 on current bytes; none contains a gate/test constant; none touches
`"positive at every"` (stays 6). With all three applied, the file's `monotone response` count goes 4 → 1
(the survivor is E2's re-statement as a wiring check) — which is what "all four sites" means.

- **§V.B, L287.** OLD: `The defensible verification claims are the bounded interval the calibration box implies and the monotone response across that band reported below;` → NEW: `The defensible verification claim is the bounded interval the calibration box implies;`
- **§V.F, L554 (first).** OLD: `limits to the marginal's bounded interval and the band's monotone response` → NEW: `limits to the marginal's bounded interval`
- **§V.F, L554 (second).** OLD: `the design identifies the marginal and the band's monotone response, not the lag structure` → NEW: `the design identifies the marginal, not the lag structure`

---

## CENSUS

Measured with `str.count` on the current file, and on the in-memory result of all 14 edits (each OLD
matched exactly once). Line count 1,461 → 1,461. Line 31 byte-identical, 323 words. Whole-file whitespace
token delta **+471** (the draft's was +532; the concision cuts in E3 and E6 removed 61).

| literal / pinned phrase | before | after |
|---|---|---|
| `$+2.9$ to $+8.7$` | 8 | **10** (E3, E4; gate :4617 needs ≥ 4) |
| `$+2.9$ to $+8.7$ points` | 7 | 7 = |
| `$[+2.9, +8.7]$` | 3 | 3 = |
| `$+2.4$ to $+9.1$` | 1 | **3** (E3, E10) |
| `$+2.3$` | 7 | **8** (E10) |
| `$+3.0$ to $+8.0$` | 5 | 5 = (gate :4616 needs ≥ 2) |
| `binding layer` | 10 | 10 = (every site kept; four gained a scope clause) |
| `binding among the layers with a coverage property` | 1 | **2** (E8; not gate-pinned) |
| `5.5\%--7.7\%` | 4 | **5** (E6) |
| `5.5--7.7\%` | 1 | 1 = (tab:params form, untouched) |
| `100~PSA` | 2 | **5** (E3, E5, E6) |
| `hard-maximum` | 1 | **3** (E5, E6) |
| `4.991\%` | 17 | **18** (E6) |
| `5.51\%` | 7 | 7 = (draft would have made it 8; sentence dropped) |
| `5.52\%` | 8 | 8 = (same) |
| `6.0\%` | **19** (draft said 17 — stale) | **20** (E10) |
| `5.0 to 7.3` | 0 | 0 = (draft would have made it 1; dropped) |
| `undemoted` | 0 | **2** (E3, E10) |
| `third-narrowest` | 0 | **2** (E3, E10) |
| `rung` | 0 | **7** (E3 ×2, E8, E8b, E10 ×3) |
| `monotone response` | 4 | **1** (E1 + R1 + R2 + R3 strike four, E2 re-states one) |
| `Layer & Marginal` | 1 | **0** (E8b) |
| `Rung & Marginal` | 0 | **1** (E8b) |
| `Every row prices one layer` | 1 | **0** (E8) |
| `Every row is one rung on that layer` | 0 | **1** (E8) |
| `a re-printing rather than a substantive move` | 1 | 1 = |
| `The ladder's reads agree` | 1 | 1 = (now continues "in location and none crosses zero") |
| `$t(6.2)$` | 1 | 1 = (test asserts == 1) |
| `$+3.2$ to $+8.3$` | 1 | 1 = (test asserts == 1) |
| `4.177\% to 5.800\%` | 1 | 1 = (test asserts == 1) |
| `$+2.8$ to $+8.8$ & $t(6.2)$` | 1 | 1 = (test asserts == 1) |
| `FLOOR_LADDER_SPANS["cr1_conventional"] + " \\\\\n"` | 1 | 1 = (test asserts == 1) |
| `CR2 $t$, Bell--McCaffrey` | 1 | 1 = | 
| `CR2 $t$ & $+3.0$ to $+8.6$` | 1 | 1 = |
| `CR3 $t$ & $+2.8$ to $+8.8$` | 1 | 1 = |
| `This is why the reported range, ... identified content.` | 1 | 1 = |
| `every correction listed above falls in its lower half` | 1 | 1 = |
| `under maximal positive dependence the width is $8.12$pp` | 1 | 1 = |
| `independence is assumed, not measured` | 1 | 1 = |
| `it does not bracket floor cyclicality` | 1 | 1 = |
| `makes the convolved line a lower bound as well` | 1 | 1 = |
| `an accident of this leverage profile, not an identity` | 1 | 1 = |
| `the 6.2 and 5.1 shown are CR1's and CR2's, and CR3's own is smaller still` | 1 | 1 = |
| `\texttt{floor\_inference\_correction} (Rademacher wild-$t$; CR1--CR3 at $t(30)$)` | 1 | 1 = |
| `positive at every` | 6 | 6 = (gate :4140 needs ≥ 6) |
| `$+3.9$ to $+13.1$` | 0 | 0 = (gate :4320 asserts == 0) |
| lines starting `A seventh qualification` | 1 | 1 = (gate #98) |
| lines starting `This section is a stress test` | 1 | 1 = (gate #100) |

**Full pin sweep.** I AST-extracted every string constant of length ≥ 6 from `tools/liveness_gates.py`
and all 30 `tests/*.py`, then diffed `str.count` before/after on the LaTeX-comment-stripped text (the
gates' own `re.sub(r'(?<!\\)%.*','')`; every `%` I add is escaped). **21** constants change count, and
19 of them are generic English/markup fragments used as membership tests, not counted objects
(`production` 223→226, `interval` 90→95, `sampling` 55→58, `headline` 167→168, `hazard` 238→239,
`residual` 30→31, `agreement` 15→16, `external` 35→36, `primary` 14→15, `quoted` 21→24, `nested` 0→2,
`weight` 147→149, `spans ` 21→23, `against ` 233→234, `, and ` 659→666, ` points` 291→293, `$ points`
189→191, `$ to $` 100→104, `$ to $+` 84→88). The two substantive ones are `$+2.9$ to $+8.7$` 8→10
(gate needs ≥ 4, no exact-count assert anywhere) and `$+2.9$` 16→18. **All four exact-count asserts in
the suite are over collections that stay at 1.** All 15 ASSEMBLY_SPANS, 4 ASSEMBLY_TABLE_SPANS,
8 FLOOR_LADDER_SPANS and 8 ABSTRACT_POSTURE values stay at count 1 except `hull_in_abstract`, which was
already 3 and stays 3. Both gate-#107 `.index()` orderings hold.

## DROPPED

1. **E3's width range** — "the ten rungs of Table~\ref{tab:ladder} span 5.0 to 7.3 points of width".
   Dropped, not qualified. The 7.3 is `cr3_t_interval_df_bm`'s **censored** width, so quoting it bare
   three sentences before E10 discloses the censoring was REFUTED #7; and the sentence's work (a wider
   coverage-bearing rung exists) is done by the CR2-BM comparator that follows. Literal `5.0 to 7.3`
   never enters the file.
2. **E3's re-statement of the held-fixed conventions** — "at the production hard-maximum form, the
   100~PSA ramp and the central elasticity $\delta = 6.5\%$" cut to "at the production 100~PSA ramp".
   Redundant: the same paragraph's opener at L355 offset 259 already says "Holding the production
   hard-maximum form and the imported elasticity fixed". Only the ramp is new information, and only the
   ramp is load-bearing for the nesting claim.
3. **E6's standalone transport sentence** — "Nor does the interval price read-to-read transport: the
   three off-window floor reads---the 4.991\% point read, the 5.51\% age-standardized read and the
   5.52\% Fannie Mae read---are disclosed in the calibration column, and none of them enters it."
   Dropped on two grounds: it was **false** of the 4.991\% read (REFUTED #2), and once corrected it
   restates what E5's cell says 7 lines earlier about the same table. The corrected content survives as
   three words inside E6's kept sentence — "around the 4.991\% point read" — which is a stronger and
   shorter statement of the same exclusion. Saves the 5.51\%/5.52\% re-prints.
4. **E6's three-sentence elasticity paragraph** compressed to one appended clause. "No sampling error
   from the imported elasticity enters any layer of the ladder ... nothing in this design propagates a
   standard error from it" restated the note's own preceding clause ("none of its width comes from the
   elasticity") and the tab:ladder caption's ("no row's width comes from the elasticity"). What was
   genuinely new — that the band is swept as a convention, so there is no elasticity layer to price — is
   now one clause. `\citepos{liebersohn2024}` dropped with it: §II already attributes the band, and its
   "depending on specification" is the paper's own licence for "published ... range".
5. **E2's demotion of the sweep** narrowed to the ordering — see FIX_FOLDED there.
6. **E10's two floor literals** (6.12\%, 6.18\%) dropped in favour of "at floors above the committed
   grid's 6.0\% end". No new number, same fact.
7. **Nothing was MOOT.** None of my ten OLDs targeted a retired "mechanical" string, the abstract, the
   tab:composition header, the §VII.E WAC sentence, or any of the split paragraph seams — all 14
   re-measured at exactly 1 on current bytes.

## COLLISIONS

Line-level warnings against the current file:

1. **L355 — E3 and E4 (severe).** This is the assembly paragraph carrying all 15 ASSEMBLY_SPANS and it
   is A-posture's canonical territory (C-24's posture verb, the hull sentence, the $+5.6$ posture clause).
   E3's OLD ends at "I attach no posture", the first four words of the posture sentence A-posture most
   likely holds; E4's OLD abuts the `fonseca2024`/`aladangady2024` counterweight run. **Apply B-ladder's
   L355 edits first, or re-anchor.** Whoever applies second must re-count.
2. **L343 — E2.** OLD is the gate-pinned "This is why the reported range ..." sentence, a natural target
   for A-posture (range-carries posture) and for any drafter holding the sign-forcing demotion. Same
   sequencing risk. (Note the paragraph splits moved this off L337, so E1 and E2 are now on **different**
   lines — that collision is gone.)
3. **L554 — routed R2 and R3 (severe).** Both are on one 4 KB+ line that also carries the 88.7\%/85.7\%
   shared-basis figures and the "within 2.1\%" calibration-mixing sentence — G-denominators and
   F-assembly territory. Two sibling edits to that line collide. Route deliberately.
4. **L287 — routed R1.** §V.B's Path B verification-claim paragraph (E-composition / whoever holds it),
   and one of the three §V.B paragraphs the round-32 splits created, so any drafter working from
   pre-split line numbers will mis-anchor here.
5. **L461 — E5.** tab:uncertainty's headline marginal row: E5 edits the sampling cell; G-denominators or
   a T8 holder may edit the calibration cell of the same row. Different cell, same line — sequence.
6. **L472 / L478 / L485 — E8, E8b, E9.** Three edits inside one float. If any sibling re-flows tab:ladder
   (float placement, column spec), E8b's header and E9's status cell must be re-anchored after it.
7. **`100~PSA` 2 → 5 and `hard-maximum` 1 → 3.** If X1 (the ramp qualifier for T1's uncertainty cell)
   also adds these, the coordinator should check no site says it twice in one cell.

## OPEN

1. **PDF geometry — unresolved, needs Eugene or the coordinator's build.** E9 takes tab:ladder's widest
   status cell from 36 to 42 characters in a plain `@{}llll@{}` tabular; E6, E7 and E10 lengthen two
   post-float note paragraphs. E9 is explicitly droppable; C-20 survives without it.
2. **Whether Liebersohn–Rothstein publish a standard error on the mobility coefficient.** C-25's
   inventory entry names this as the settling check. E6 therefore claims only what I verified — that
   *this design* prices no elasticity sampling error and the band is a published range swept as a
   convention. It does **not** claim the source publishes no SE. Reading the source would settle whether
   a fourth layer is constructible.
3. **The `100~PSA` / `hard-maximum` production labels** are derived, not recorded:
   `floor_inference_correction_v2_results.json` records neither key. The derivation is the manuscript's
   own ($\phi^{*}=0.754$ printed as "effectively 75.4 PSA", $\phi=1$ reproducing committed values ⇒
   production = 100 PSA) plus `scaled_null`'s recorded `floor_mode 'max'` / `psa_speed 100.0`. If the
   coordinator wants this pinned to the ladder run itself, it is not in that artifact.
4. **C-05's five out-of-region sites** — inventory `.tex:46`, `:66`/`:79`/`:81` (T1 caption and row 4),
   `:713`/`:719`, `:1412`/`:1418` (App. O ledger; note App. O grew ~165 words, so those two are shifted).
   Not drafted: `:66`/`:79` additionally need X1's ramp qualifier in T1's uncertainty cell. My edits leave
   `binding layer` at 10, so nothing there is disturbed.
5. **C-24's T1 note-a catalogue** (add the PSA span and the scaled-null companion) and its abstract verb
   amendment — outside my region, not drafted.
6. **C-20's abstract site is C-01's.** Nothing here touches the abstract (L31 byte-identical, 323 words),
   so if the abstract still implies the quoted interval is the widest coverage-bearing read, that stays
   open after this set.
7. **"Pre-committed" for Webb-as-primary is now sourceable** but I did not use it: the artifact's
   top-level `spec` names Webb "as the PRIMARY floor-read interval" and `spec_source` is
   `specs/SPEC_round28_C1_C2_C3_C6.md SPEC C1`. E10 still says "the primary read and the interval this
   paper quotes", which the caption already asserts. Upgrading to "pre-committed" is available if the
   coordinator wants it; I left it out for concision.
