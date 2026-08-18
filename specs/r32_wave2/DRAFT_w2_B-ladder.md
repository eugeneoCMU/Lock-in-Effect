# R32 Wave 2 — Cluster B (ladder / binding-layer) draft edit set

Conditions covered: C-05 (in-region sites only), C-20, C-21, C-24 (in-region half), C-25, C-27, C-38 (in-region site + 3 routed companions), C-69.
Region: §V.E (`sec:identification`), `tab:uncertainty` + its post-float notes, `tab:ladder` + its post-float notes.
Nothing in the worktree was modified. Every OLD count below was measured with `str.count` on a fixed string; the CENSUS was measured on the in-memory edited file (all ten OLDs applied, each exactly once).

Line numbers are **current-file** (`paper/v18/revised_paper_v18.tex`, 2026-07-29 HEAD). The inventory's numbers are stale by +6 from `.tex:417` onward: `417→423`, `433→439`, `440→446`, `444→450`, `457→463`, `467→473`; `323` and `333` are unshifted.

Artifact keys used (all read, none run):
`hazard/data/floor_inference_correction_v2_results.json → reads["R2_2018_gap<=-0.0025_age>=12"]`, keys `cr1_t_interval`, `cr2_t_interval`, `cr3_t_interval`, `cr1_t_interval_df_bm`, `cr2_t_interval_df_bm`, `cr3_t_interval_df_bm`, `wild_t_rademacher`, `wild_t_webb`, `wcr_inverted`, `df_bm_by_estimator`, `G_star_css`, `h_max`, `leverages_h`, `n_clusters`.

Measured widths (pp), ascending, with truncation flags — this is the evidence base for C-20:

| rung | interval | width | truncated edge |
|---|---|---|---|
| percentile (demoted) | +3.0 to +8.0 | 5.044 | — |
| CR1 t | +3.1532 to +8.3499 | 5.1967 | none |
| CR2 t | +2.9740 to +8.5527 | 5.5787 | none |
| **Webb wild-t (quoted)** | **+2.8550 to +8.6780** | **5.8230** | **none** |
| Rademacher wild-t | +2.7963 to +8.7231 | 5.9268 | none |
| CR3 t | +2.7732 to +8.7744 | 6.0012 | none |
| CR1 t, Bell–McCaffrey | +2.7531 to +8.7962 | 6.0431 | none |
| **CR2 t, Bell–McCaffrey** | **+2.4098 to +9.1498** | **6.7400** | **none — widest untruncated** |
| restricted wild inversion | +2.2809 to +9.1093 | 6.8284 | **lower** (`mapped_at_pct` 6.0) |
| CR3 t, Bell–McCaffrey | +2.2809 to +9.5645 | 7.2836 | **lower** (`mapped_at_pct` 6.0) |

`df_bm_by_estimator` = {cr1 6.2462, cr2 5.0945, cr3 4.1030}; `G_star_css` 5.8717; `h_max` = `max_leverage` = 0.33233; `leverages_h` top three 0.3323 / 0.1717 / 0.1266 (sum 1.0), so the largest cluster carries a third of the total leverage and **twice** the next largest. Webb is the **third-narrowest of the nine undemoted rungs**; the two rungs wider than CR2-BM are both carried by a **lower**-edge grid clip.

---

## Edit 1 — strike the forced monotonicity from the identified-content list (C-38)
FILE: paper/v18/revised_paper_v18.tex
LINE: 323 (§V.E, first qualification)
OLD_COUNT_ASSERT: 1
OLD:
the identified content is the marginal's \emph{bounded range}, together with the monotone response across the Liebersohn--Rothstein band, and neither its point magnitude nor its sign
NEW:
the identified content is the marginal's \emph{bounded range}, and neither its point magnitude nor its sign
RATIONALE: The band's monotone response is forced by the same composition-of-monotone-maps argument the paragraph already uses to demote the 27-cell positivity check, so it cannot sit in the identified content beside the bounded range.
LITERALS_INTRODUCED: none.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none. (No gate or test literal is a substring of this OLD; checked by AST-extracting every string constant ≥20 chars from `tools/liveness_gates.py` and `tests/*.py` and testing substring membership against line 323.)

## Edit 2 — put the band's monotone response on the positivity footing (C-38)
FILE: paper/v18/revised_paper_v18.tex
LINE: 323 (same paragraph, after the pinned sign sentence)
OLD_COUNT_ASSERT: 1
OLD:
This is why the reported range, and not the sign, carries the paper's identified content.
NEW:
This is why the reported range, and not the sign, carries the paper's identified content. The monotone response across the Liebersohn--Rothstein band is forced the same way: \eqref{eq:beta1} is monotone in $\delta$ and the hazard is monotone in $\beta_1$ at a gap that is negative in every cell, so the band's ordering is a composition of monotone maps. I retain the band sweep as a wiring check on that footing, not as identified content.
RATIONALE: Carries the disclosure rather than deleting it — the numbers and the sweep stay, their evidential status changes, mirroring the sentence the paragraph already uses for the twenty-seven cells ("verifies the specification ... rather than identifying the mechanism, and I retain it on that footing").
LITERALS_INTRODUCED: none (no numeric literal; `\eqref{eq:beta1}` is an existing label, 11 refs in file).
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: `"This is why the reported range, and not the sign, carries the paper's identified content."` is a pinned literal in `tools/liveness_gates.py`. NEW contains it **byte-identically as its prefix** (count stays 1). The neighbouring pins `"positive at every"` (gate needs ≥6 sites), `"verifies the specification"`, `"the panel ends two months before the window does"` are untouched.

## Edit 3 — nest the sampling interval inside the convention envelope, and name the within-layer choice (C-24, C-20)
FILE: paper/v18/revised_paper_v18.tex
LINE: 333 (§V.E ¶7, the assembly paragraph — must remain ONE line beginning "A seventh qualification")
OLD_COUNT_ASSERT: 1
OLD:
and the uncomposed pair falls near its bottom. I attach no posture
NEW:
and the uncomposed pair falls near its bottom. Those two spans are nested rather than alternative: the baseline-level convention just swept is the outer statement, and $+2.9$ to $+8.7$ is a sampling interval on the floor read alone, nested inside it at the production hard-maximum form, the 100~PSA ramp and the central elasticity $\delta = 6.5\%$. Which rung of that inner layer to quote is a further choice the rule does not settle: the ten rungs of Table~\ref{tab:ladder} span 5.0 to 7.3 points of width, and the Webb wild-$t$ read quoted here is the third-narrowest of the nine undemoted ones, with the widest untruncated comparator---CR2 at Bell--McCaffrey degrees of freedom, $+2.4$ to $+9.1$ points---standing beside it rather than behind it. I attach no posture
RATIONALE: C-24's "which object is outer and which is nested" said once, in ¶7, with the held-fixed conventions named in words (**not** as "$s = 0$": ¶7 already uses $s$ for the moving-share bracket at $s = 0.5/0.25/1$, where $s = 1$ is production, so printing "$s = 0$" for the floor-form blend in the same paragraph would collide). C-20's finding is stated where the selection rule lives, without touching the pinned rule sentence — the LAYER ranking in that sentence is correct; what the rule does not settle is which RUNG of the layer to quote.
LITERALS_INTRODUCED:
- `$+2.9$ to $+8.7$` (a further occurrence; `wild_t_webb.marginal_ci95_pp` = [2.8550, 8.6780], the value already printed 8× in the file)
- `100~PSA` (existing convention literal, `app:params` seasoning ramp; 2 → 5 occurrences after all edits)
- `5.0 to 7.3` (widths: percentile 5.0442 from the printed +3.0/+8.0 row, `cr3_t_interval_df_bm` width 7.2836)
- `$+2.4$ to $+9.1$` (`cr2_t_interval_df_bm.marginal_ci95_pp` = [2.40979, 9.14977]; already printed once as the table row)
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: the insertion point sits **between** `ASSEMBLY_SPANS["posture_lower_half"]` ("every correction listed above falls in its lower half") and `ASSEMBLY_SPANS["posture_retired_range_carries"]`; both survive byte-identically and in the same order, and gate #98 (`assembly_check`) checks membership + "exactly one paragraph starting with the opener", both of which hold (verified: the edited file still has exactly one line starting `A seventh qualification`). `test_headline_posture_gate.py::test_abstract_posture_agrees_with_section_ve` requires `"$+2.9$ to $+8.7$ points"` in that same line — the pinned occurrence (inside `posture_binding_layer`) is untouched; my new occurrence deliberately has no trailing " points" so it cannot be mistaken for it.

## Edit 4 — say plainly that the externally anchored member lies outside the quoted interval (C-69)
FILE: paper/v18/revised_paper_v18.tex
LINE: 333 (§V.E ¶7, the scaled-null companion)
OLD_COUNT_ASSERT: 1
OLD:
The variant documents an upward bias; the corrected member lies below the headline, at the bottom of the seasoning-ramp span just swept.
NEW:
The variant documents an upward bias; the corrected member lies below the headline and outside the quoted $+2.9$ to $+8.7$ interval, at the bottom of the seasoning-ramp span just swept---a pre-committed externally anchored calibration landing outside the interval this paper quotes, which is a fact about what that interval prices and not about the sign.
RATIONALE: The paragraph already prints the root ($\phi^{*} = 0.754$) and the $+0.9$/$+3.5$ pair; the word C-69 asks for — *outside* — was the one thing it never said. The consequence clause keeps the exclusion from reading as a contradiction of the sign result, and Edit 3 (three sentences earlier) has already told the reader what the interval prices.
LITERALS_INTRODUCED: `$+2.9$ to $+8.7$` (one further occurrence, same source as Edit 3). No new numeric value: $+0.9$ at the headline floor is already in this paragraph (`scaled_null_housing_activity_results.json` root["4.991"] `marginal_pp` 0.8979 < 2.855, so "outside" is arithmetic on committed values, not a new read).
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none in this OLD. (`"the corrected member lies below the headline (downward)"` is a *different* string, in the App. O ledger at line 1430; untouched. The `psa_level_sweep`/`fonseca2024` pins earlier in the paragraph are untouched.)

## Edit 5 — T8 headline row: scope "binding layer", name the held-fixed conventions, exclude transport (C-05, C-24, C-27)
FILE: paper/v18/revised_paper_v18.tex
LINE: 439 (`tab:uncertainty`, headline marginal row, sampling column)
OLD_COUNT_ASSERT: 1
OLD:
(the binding layer, and a sampling interval on the floor read alone rather than on the elasticity;
NEW:
(the binding layer among those with a coverage property---the baseline-level convention in the next column spans wider---and a sampling interval on the floor read alone at the production hard-maximum form and the 100~PSA ramp, pricing neither the elasticity nor the read-to-read spread across the floor reads in the next column;
RATIONALE: C-05 at the site the inventory lists as `.tex:433`; the scope is the one already used at line 423, compressed for a table cell. The cell's own calibration column carries both things it does not price (the PSA convention range, and the three floor reads), so the exclusion is a pointer, not a new disclosure.
LITERALS_INTRODUCED: `100~PSA` (existing convention literal; see Edit 3). No numeric value introduced.
LITERALS_REMOVED: none. The cell keeps `$[+2.9, +8.7]$pp`, `$\delta = 6.5\%$`, `$[+3.0, +8.0]$pp`, `$[+4.63, +6.92]$pp`, `$0.39\times$`, `25.8`, `$[+2.80, +8.99]$pp`, `$8.12$pp`.
PINNED_SPANS_CROSSED: gate #105 (`convolved_line_check`) pins `"independence is assumed, not measured"` and `"under maximal positive dependence the width is $8.12$pp"`, both later in the same cell and untouched. Gate at `:4616-4621` needs `tex.count("$+3.0$ to $+8.0$") >= 2`, `tex.count("$+2.9$ to $+8.7$") >= 4` and `"binding layer" in tex` — all still satisfied (counts 2 and 10; the phrase "binding layer" is deliberately kept, not replaced, so its file count stays 10).

## Edit 6 — Notes to T8: no elasticity sampling error anywhere in the ladder; the layer does not price transport (C-25, C-27, C-05)
FILE: paper/v18/revised_paper_v18.tex
LINE: 446 (post-float `Notes to Table~\ref{tab:uncertainty}` paragraph — stays post-float per the round-31 convention)
OLD_COUNT_ASSERT: 1
OLD:
and the headline row quotes the wild-$t$ interval as the binding layer. That interval prices one layer: the floor read's own sampling error, propagated through the frozen floor-to-marginal grid at the central elasticity $\delta = 6.5\%$, so none of its width comes from the elasticity, which is swept separately in the calibration column and in Table~\ref{tab:lowband}.
NEW:
and the headline row quotes the wild-$t$ interval as the binding layer among those with a coverage property. That interval prices one layer: the floor read's own sampling error, propagated through the frozen floor-to-marginal grid at the production hard-maximum form, the 100~PSA ramp and the central elasticity $\delta = 6.5\%$, so none of its width comes from the elasticity, which is swept separately in the calibration column and in Table~\ref{tab:lowband}. No sampling error from the imported elasticity enters any layer of the ladder: the 5.5--7.7\% band is \citepos{liebersohn2024} own across-specification range, swept as a convention on both legs, and nothing in this design propagates a standard error from it. Nor does the interval price read-to-read transport: the three off-window floor reads---the 4.991\% point read, the 5.51\% age-standardized read and the 5.52\% Fannie Mae read---are disclosed in the calibration column, and none of them enters it.
RATIONALE: C-25 and C-27 in the note where the interval is claimed. Both are stated as facts about *this* design's propagation, not about the source's statistics — the source's own description ("depending on specification", §II and §V.B) is what licenses "across-specification range". C-05's qualifier added at the site the inventory lists as `.tex:440`.
LITERALS_INTRODUCED:
- `5.5--7.7\%` (second occurrence; the imported band, already printed at `app:params`/§V.B)
- `4.991\%`, `5.51\%`, `5.52\%` (one further occurrence each; all three already printed in this table's calibration column — 4.991 the 2018-leg point read, 5.51 the age-standardized read, 5.52 the Fannie read)
- `100~PSA` (see Edit 3)
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: this note carries `"floor\_inference\_correction"`, `"it does not bracket floor cyclicality"`, `"makes the convolved line a lower bound as well"`, `"$+11.22$ to $+11.27$"`; all outside this OLD and untouched. `\citepos` is defined at line 22 of both files.

## Edit 7 — the Rademacher–Webb near-identity stops being a stability claim (C-21)
FILE: paper/v18/revised_paper_v18.tex
LINE: 446 (same note, next sentence)
OLD_COUNT_ASSERT: 1
OLD:
The ladder's reads agree: the Rademacher and Webb constructions land with both endpoints within a tenth of a point, a re-printing rather than a substantive move, while the small-sample degrees of freedom and the restricted inversion are wider, all agreeing in location and none crossing zero.
NEW:
The ladder's reads agree in location and none crosses zero, and the closest agreement among them carries no information: the Rademacher and Webb constructions land with both endpoints within a tenth of a point, a re-printing rather than a substantive move, because both weight schemes are symmetric two-signed reweightings of the same residuals, so each bootstrap distribution turns on the sign drawn for the one cluster carrying a third of the total leverage---twice the next largest. Their coincidence re-prints that cluster's influence instead of testing it. The small-sample degrees of freedom and the restricted inversion are wider.
RATIONALE: The agreement was framed as the ladder's corroboration ("The ladder's reads agree:"); the corroboration that survives is location and zero-exclusion, which the new lead sentence keeps. The near-identity now carries the mechanical reason it is uninformative, and the endpoint comparison stays as a re-printing statement only. Nothing numeric is deleted.
LITERALS_INTRODUCED: none. "a third of the total leverage" and "twice the next largest" are words, both read off `leverages_h` (0.33233 of a total of 1.0; next largest 0.17170, ratio 1.94). The gap the sentence describes is 0.0587pp (lower) and 0.0451pp (upper) — under a tenth of a point, as printed.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none — `"a re-printing rather than a substantive move"` is not gate-pinned (confirmed: no gate/test literal matches) but is kept verbatim anyway, count 1 → 1.

## Edit 8 — `tab:ladder` caption carries the binding-layer scope (C-05)
FILE: paper/v18/revised_paper_v18.tex
LINE: 450 (`tab:ladder` caption)
OLD_COUNT_ASSERT: 1
OLD:
\caption{The inference ladder on the binding layer. Every row prices one layer
NEW:
\caption{The inference ladder on the binding layer---binding among the layers with a coverage property; the unestimated baseline-level convention spans wider. Every row prices one layer
RATIONALE: C-05 at the site the inventory lists as `.tex:444`, reusing the line-423 formulation verbatim so a caption read on its own cannot overstate the ranking.
LITERALS_INTRODUCED: none.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: gate #107 pins `FLOOR_LADDER_SPANS["run_credit"]` = `"\texttt{floor\_inference\_correction} (Rademacher wild-$t$; CR1--CR3 at $t(30)$)"` in this caption's last sentence — outside this OLD, byte-identical after the edit (count 1 → 1).

## Edit 9 — Webb row status cell says it is not the widest (C-20, C-05) — WIDTH-CONTINGENT
FILE: paper/v18/revised_paper_v18.tex
LINE: 463 (`tab:ladder`, Webb row)
OLD_COUNT_ASSERT: 1
OLD:
Wild-$t$, Webb & $+2.9$ to $+8.7$ & bootstrap, $B = 9{,}999$ & primary; the binding layer
NEW:
Wild-$t$, Webb & $+2.9$ to $+8.7$ & bootstrap, $B = 9{,}999$ & primary; the binding layer, not the widest
RATIONALE: The row that names itself primary should not let a reader infer it is the ladder's conservative end. Deliberately six characters longer than the current widest status cell ("demoted; under-covers at 31 clusters", 36 chars) because `tab:ladder` uses plain `llll` columns and grows with its widest cell.
LITERALS_INTRODUCED: none.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none in this row. The gate #107 ordering assert indexes `"CR1 $t$ & $+3.2$ to $+8.3$ & $t(30)$, $G-1$ & no leverage adjustment"`, `"CR2 $t$ & $+3.0$ to $+8.6$"`, `"CR1 $t$, Bell--McCaffrey & ..."` and `"CR2 $t$, Bell--McCaffrey"` — all unmoved, all still unique.
**COORDINATOR DECISION:** drop this edit if the rebuild reports an overfull `\hbox` on `tab:ladder`; C-20 is fully carried by Edits 3 and 10 without it. I could not build the PDF (read-only).

## Edit 10 — Notes to `tab:ladder`: why wild rather than Bell–McCaffrey, and the wider untruncated rung beside it (C-20)
FILE: paper/v18/revised_paper_v18.tex
LINE: 473 (post-float `Notes to Table~\ref{tab:ladder}` paragraph)
OLD_COUNT_ASSERT: 1
OLD:
That concentration is why the wild-cluster correction is applied and the percentile read demoted.\par}
NEW:
That concentration is why the wild-cluster correction is applied and the percentile read demoted. It does not rank the wild construction against the Bell--McCaffrey degrees of freedom, and I do not claim it does: the wild rows build their reference distribution by re-drawing the leverage profile, the Bell--McCaffrey rows keep the sandwich and correct the reference distribution's degrees of freedom for that same profile, and at 5.9 effective clusters neither correction dominates the other. So the Webb row is the primary read and the interval this paper quotes, but it is the third-narrowest of the nine undemoted rungs, and the widest untruncated rung---CR2 at Bell--McCaffrey degrees of freedom, $+2.4$ to $+9.1$ points---belongs beside it rather than behind it. The two wider rungs are carried by a grid edge: CR3 at Bell--McCaffrey degrees of freedom and the restricted inversion reach $+2.3$ only because their \emph{lower} endpoints clip the 6.0\% end of the committed floor grid, while both upper endpoints are interior to it.\par}
RATIONALE: C-20's substantive fix, in the note that already carries $G^{*} = 5.9$ and $h_{\max} = 0.33$ — so the reason lands where its inputs are. It takes the concession route *and* quotes the wider rung: no ranking is claimed at 5.9 effective clusters, the untruncated wider comparator is quoted, and the truncation of the two widest rungs is disclosed on the **lower** edge (A-17), which is where the artifact puts it.
LITERALS_INTRODUCED:
- `$+2.4$ to $+9.1$` (`cr2_t_interval_df_bm.marginal_ci95_pp` = [2.40979, 9.14977]; `lower_pp_edge.truncated_at_grid_edge = false`, `upper_pp_edge.truncated_at_grid_edge = false`)
- `$+2.3$` (one further occurrence; `cr3_t_interval_df_bm.marginal_ci95_pp[0]` = `wcr_inverted.marginal_ci95_pp[0]` = 2.280915, both with `lower_pp_edge.truncated_at_grid_edge = true`, `mapped_at_pct = 6.0`)
- `6.0\%` (one further occurrence; `mapped_at_pct` 6.0 — the committed floor grid's upper end)
- "5.9" and "third-narrowest"/"nine undemoted rungs" reuse values already in this note (`G_star_css` 5.8717) and the width table above.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: this note carries three gate-#107 spans — `FLOOR_LADDER_SPANS["df_ownership"]`, `["cr1_is_the_baseline"]`, `["printed_tie_is_not_an_identity"]`. All precede the OLD and are byte-identical after the edit (each count 1 → 1). Also checked: `tests/test_floor_ladder_gate.py::test_a_wrong_digit_fails` asserts `TEX.count(...) == 1` for `"$+3.2$ to $+8.3$"`, `"$+2.8$ to $+8.8$ & $t(6.2)$"`, `"$t(6.2)$"`, `"4.177\% to 5.800\%"` — my text introduces none of those four strings, and all four stay at exactly 1. That is why this note spells the rungs "CR2 at Bell--McCaffrey degrees of freedom" rather than reusing the row labels, and never prints a bare `$t(6.2)$`.

---

## COORDINATOR-ROUTED — C-38's three companion sites (OUTSIDE my region; not numbered edits)

C-38's condition is "strike the clause at all four sites". One site is §V.E (Edits 1–2). The other three are §V.B and §V.F, outside my region — if no sibling drafter holds them, they must move with Edits 1–2 or the paper will list the same forced monotonicity as identified content two subsections later. Each OLD below is unique (count 1, fixed-string measured); none contains a gate/test literal, and none touches `"positive at every"` (gate at `:4140` needs ≥6 sites).

- **§V.B, line 277.** OLD: `The defensible verification claims are the bounded interval the calibration box implies and the monotone response across that band reported below;` → NEW: `The defensible verification claim is the bounded interval the calibration box implies;`
- **§V.F, line 532 (first).** OLD: `limits to the marginal's bounded interval and the band's monotone response` → NEW: `limits to the marginal's bounded interval`
- **§V.F, line 532 (second).** OLD: `the design identifies the marginal and the band's monotone response, not the lag structure` → NEW: `the design identifies the marginal, not the lag structure`

---

## CENSUS

Measured with `str.count` on the file before, and on the in-memory result after applying all ten edits in order (each OLD matched exactly once). Rows marked `=` are unchanged.

| literal / pinned phrase | before | after |
|---|---|---|
| `$+2.9$ to $+8.7$` | 8 | **10** (Edits 3, 4; gate `:4617` needs ≥4) |
| `$+2.9$ to $+8.7$ points` | 7 | 7 = |
| `$[+2.9, +8.7]$` | 3 | 3 = |
| `$+2.4$ to $+9.1$` | 1 | **3** (Edits 3, 10) |
| `$+2.3$` | 7 | **8** (Edit 10) |
| `$+3.0$ to $+8.0$` | 5 | 5 = (gate `:4616` needs ≥2) |
| `binding layer` | 10 | 10 = (every site kept; four gained a scope clause) |
| `binding among the layers with a coverage property` | 1 | **2** (Edit 8; not gate-pinned) |
| `the identified content is the marginal's \emph{bounded range}, together with the monotone response` | 1 | **0** (Edit 1) |
| `monotone response across the Liebersohn--Rothstein band` | 1 | 1 = — **note:** the count is deliberately unchanged; Edit 1 removes it from the identified-content list and Edit 2 re-states it as a wiring check. The structural change is the move, not the count. |
| `5.5--7.7\%` | 1 | **2** (Edit 6) |
| `100~PSA` | 2 | **5** (Edits 3, 5, 6) |
| `hard-maximum` | 1 | **4** (Edits 3, 5, 6) |
| `4.991\%` | 17 | **18** (Edit 6) |
| `5.51\%` | 7 | **8** (Edit 6) |
| `5.52\%` | 8 | **9** (Edit 6) |
| `6.0\%` | 17 | **18** (Edit 10) |
| `5.0 to 7.3` | 0 | **1** (Edit 3) |
| `undemoted` | 0 | **2** (Edits 3, 10) |
| `third-narrowest` | 0 | **2** (Edits 3, 10) |
| `a re-printing rather than a substantive move` | 1 | 1 = |
| `The ladder's reads agree` | 1 | 1 = (now continues "in location and none crosses zero") |
| `$t(6.2)$` | 1 | 1 = (test asserts ==1) |
| `$+3.2$ to $+8.3$` | 1 | 1 = (test asserts ==1) |
| `4.177\% to 5.800\%` | 1 | 1 = (test asserts ==1) |
| `$+2.8$ to $+8.8$ & $t(6.2)$` | 1 | 1 = (test asserts ==1) |
| `CR2 $t$, Bell--McCaffrey` | 1 | 1 = (gate #107 indexes it) |
| `CR2 $t$ & $+3.0$ to $+8.6$` | 1 | 1 = |
| `CR3 $t$ & $+2.8$ to $+8.8$` | 1 | 1 = |
| `ASSEMBLY_SPANS["posture_binding_layer"]` (full string) | 1 | 1 = |
| `every correction listed above falls in its lower half` | 1 | 1 = |
| `no interior member is privileged, ... what the design delivers` | 1 | 1 = |
| `This is why the reported range, and not the sign, carries the paper's identified content.` | 1 | 1 = |
| `the 6.2 and 5.1 shown are CR1's and CR2's, and CR3's own is smaller still` | 1 | 1 = |
| `is the standard error the wild rows studentize with, ... rather than competing reads` | 1 | 1 = |
| `an accident of this leverage profile, not an identity` | 1 | 1 = |
| `\texttt{floor\_inference\_correction} (Rademacher wild-$t$; CR1--CR3 at $t(30)$)` | 1 | 1 = |
| `in the units a cap designer would have to plug in` | 1 | 1 = |
| `wild-cluster interval runs from 4.177\% to 5.800\%` | 1 | 1 = |
| `under maximal positive dependence the width is $8.12$pp` | 1 | 1 = |
| `A seventh qualification` | 1 | 1 = (still exactly one line starts with it — gate #98's paragraph count) |
| `Three things stop the list` | 1 | 1 = |

Also verified on the edited text: all 15 `ASSEMBLY_SPANS` and all 4 `ASSEMBLY_TABLE_SPANS` values are still present **and unique** (count 1 each); line count unchanged (no line added or removed); line 31 byte-identical.

## UNVERIFIED

1. **PDF geometry.** I cannot build. Edit 9 widens `tab:ladder`'s widest status cell by 6 characters in a plain `llll` tabular; Edits 6 and 10 lengthen two post-float note paragraphs. What would confirm: the rebuild's overfull-hbox log and a page-count check. Edit 9 is marked droppable for exactly this reason.
2. **Whether Liebersohn–Rothstein publish a standard error on the mobility coefficient.** C-25's inventory entry names this as the settling check. My Edit 6 therefore claims only what I verified — that *this design* propagates no sampling error from the import, and that the 5.5–7.7% band is the source's across-specification range (the paper's own description at §II and §V.B, "depending on specification"). It does **not** claim the source publishes no SE. Reading the source would settle whether a fourth layer is constructible.
3. **"Pre-committed" for the Webb-primary construction.** I did not verify a pre-registration document for Webb-as-primary, so Edit 10 says "the primary read and the interval this paper quotes" (which the existing caption already asserts) rather than "pre-committed". Confirmable from the run spec that `floor_inference_correction_v2`'s `studentizer` field cites as "SPEC C1.2(4)".
4. **C-05's five out-of-region sites** — the inventory's `.tex:46`, `:66` (T1 caption), `:79`/`:81` (T1 row 4), `:713`/`:719`, `:1412`/`:1418` (App. O ledger). Not drafted: outside my region, and `:66`/`:79` additionally need X1's ramp qualifier in T1's uncertainty cell, which belongs with whoever holds T1. My edits leave the file's `binding layer` count at 10, so nothing there is disturbed.
5. **C-24's T1 note-a catalogue** (add the PSA span and the scaled-null companion) and its abstract verb amendment — outside my region, not drafted.
6. **C-20's abstract site** is C-01, another drafter's; nothing here changes the abstract, so if the abstract still implies the quoted interval is the widest coverage-bearing read, that remains open after this edit set.

## WORD_COUNT_IMPACT

No edit touches line 31. The abstract is unchanged: **abstract word delta 0**, so gate #101's letter-vs-abstract count tie and the 294-word figure are unaffected. Body length grows by **+532 whitespace tokens** (measured `len(new.split()) - len(old.split())` on the whole file; prose words are somewhat fewer, since the count includes markup) across §V.E, the T8 headline row, and the two post-float note paragraphs. Also measured on the result: `"positive at every"` stays at 6 sites (gate `:4140` needs ≥6), the line count is unchanged, and line 31 is byte-identical.
