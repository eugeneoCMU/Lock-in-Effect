# Adversarial verdict — B-ladder (§V.E, tab:uncertainty, tab:ladder) — C-05, C-20, C-21, C-24, C-25, C-27, C-38, C-69

VERDICT: APPLY_WITH_LISTED_FIXES
edits_checked: 13

## COUNT_MISMATCHES (2)
1. NONE. All ten numbered OLDs measured exactly 1 with str.count on fixed strings (E1 L323, E2 L323, E3 L333, E4 L333, E5 L439, E6 L446, E7 L446, E8 L450, E9 L463, E10 L473). The three coordinator-routed OLDs also measured exactly 1 (L277, L532 x2).

2. CENSUS: all 39 rows I re-measured on the edited in-memory file reproduce the draft's before/after EXACTLY, including $+2.9$ to $+8.7$ 8->10, $+2.4$ to $+9.1$ 1->3, $+2.3$ 7->8, 100~PSA 2->5, hard-maximum 1->4, 4.991\% 17->18, 5.51\% 7->8, 5.52\% 8->9, 6.0\% 17->18, binding layer 10->10, positive at every 6->6, line count 1435->1435, line 31 byte-identical. WORD_COUNT_IMPACT '+532 whitespace tokens' reproduces exactly (532). No mismatch found anywhere.


## REFUTED_CLAIMS (8)
1. EDIT 10 — TRUNCATION DIRECTION USED BACKWARDS (most serious). NEW says CR3-BM and the restricted inversion 'reach $+2.3$ only because their \emph{lower} endpoints clip the 6.0\% end of the committed floor grid', which reads as a discount: those rungs only LOOK wide because of a grid artifact. The artifact says the opposite. cr3_t_interval_df_bm.lower_pp_edge.floor_pct = 6.1160 and wcr_inverted.lower_pp_edge.floor_pct = 6.1813, both mapped_at_pct = 6.0. The marginal is DECREASING in the floor (tab:oosfloor: 4.991->+5.57, 5.51->+3.8, 5.52->+2.3..+4.3), so at the uncensored floors those lower endpoints run BELOW +2.28. The clip makes the two widest rungs NARROWER than they are, so it cannot be the reason they 'reach' +2.3. Required restatement: their lower endpoints are censored at the grid's 6.0\% end, so +2.3 understates how low they run (upper endpoints, at floors 3.853\% and 4.033\%, are interior). This matters because C-20's whole point is that wider coverage-bearing rungs exist; the current phrasing turns the disclosure into a defence.

2. EDIT 6 — 'none of them enters it' is FALSE for one of the three reads it lists. The wild-t interval IS the sampling distribution around the 4.991\% point read: wild_t_webb lower/upper floor edges are 5.8003\% and 4.1767\%, bracketing 4.991. Only the 5.51\% age-standardized and 5.52\% Fannie reads are excluded. (The inventory's own C-27 prose is equally loose; the draft inherited it.) Fix: name the interval as a sampling interval AROUND the 4.991\% read, then say neither of the other two reads enters it.

3. EDIT 4 — 'the corrected member lies below the headline and outside the quoted $+2.9$ to $+8.7$ interval' is FALSE of the second member the same sentence's antecedent covers. The paragraph prints TWO corrected members: scaled_null_housing_activity_results.json root['4.991'].marginal_pp = 0.8979 (+0.9, headline floor) and root['4'].marginal_pp = 3.4680 (+3.5, in-sample calibration). +3.5 is INSIDE [+2.9, +8.7]. The pre-edit singular 'the corrected member' was already loose; adding 'outside the quoted interval' converts looseness into a false claim. Fix: scope it — 'at the headline floor the corrected member lies outside the quoted interval'.

4. EDIT 10 — 'the wild rows build their reference distribution by re-drawing the leverage profile' is mechanically wrong. A wild-cluster bootstrap holds the leverage profile FIXED and re-draws cluster-level weights on the residuals. It also contradicts Edit 7's own (correct) account three lines earlier ('turns on the sign drawn for the one cluster'). Fix: 'by re-drawing cluster-level weights at that same leverage profile'.

5. EDIT 7 — 'both weight schemes are symmetric two-signed reweightings' and 'the sign drawn' are Rademacher-accurate and Webb-inaccurate. floor_inference_correction_v2_results.json spec: 'Webb six-point wild-cluster bootstrap-t'. Webb draws from six values, not two signs. Fix: 'sign-symmetric reweightings' / 'the draw's sign for the one cluster'.

6. EDIT 7 — 'twice the next largest' overstates. leverages_h top two are 0.33233 and 0.17166, ratio 1.9360. 'nearly twice' is exact and costs one word. ('a third of the total leverage' checks out: sum_h = 1.0000000000000002.)

7. EDIT 3 — '5.0 to 7.3 points of width' quotes a grid-CENSORED maximum with no qualifier, three sentences before Edit 10 discloses that the 7.3 endpoint is censored. Either qualify here or drop the upper figure. (Widths themselves check out: percentile 5.0442, CR3-BM 7.2836; Webb 5.8230 IS third-narrowest of the nine undemoted rungs, and CR2-BM 6.7400 IS the widest with both edges truncated_at_grid_edge=false — that part of C-20 is correctly carried.)

8. EDIT 3 — 'Those two spans' takes the wrong nearest antecedent. The two spans most recently printed in the pinned sentence are the percentile read $+3.0$ to $+8.0$ and $+2.9$ to $+8.7$; the intended pair (the 75-150 PSA convention span and the sampling interval) is two clauses further back. Name them.


## PIN_VIOLATIONS (4)
1. NONE. I ast-extracted all 1,657 string constants of length >=16 from tools/liveness_gates.py and tests/*.py and diffed str.count before/after on the LaTeX-comment-stripped text (the gates' own re.sub(r'(?<!\\)%.*','') normalisation; every new % in the edits is escaped). Exactly one pinned count changes: '$+2.9$ to $+8.7$' 8 -> 10, and the only gate reading it needs >= 4 (tools/liveness_gates.py:4617). No gate asserts an exact count on it.

2. All 15 ASSEMBLY_SPANS + 4 ASSEMBLY_TABLE_SPANS + 8 FLOOR_LADDER_SPANS + 8 ABSTRACT_POSTURE values stay at count 1 (hull_in_abstract stays 3). ASSEMBLY_SPANS['posture_binding_layer'], ['posture_lower_half'], ['posture_retired_range_carries'] all survive byte-identically and in order inside line 333, which still startswith 'A seventh qualification' and is still the ONLY such line (gate #98 assembly_check passes).

3. floor_ladder_check's two .index() ordering asserts re-evaluated on the edited text: cr1_conventional < 'CR2 $t$ & $+3.0$ to $+8.6$' TRUE, cr1_bell_mccaffrey < 'CR2 $t$, Bell--McCaffrey' TRUE. Edits 3 and 10 deliberately spell 'CR2 at Bell--McCaffrey degrees of freedom' so they cannot become an earlier first-index for the pinned row string; verified count 1 -> 1.

4. tests/test_floor_ladder_gate.py's ==1 asserts hold: '$+3.2$ to $+8.3$', '$+2.8$ to $+8.8$ & $t(6.2)$', '$t(6.2)$', '4.177\% to 5.800\%' all 1 -> 1. tests/test_headline_posture_gate.py::test_abstract_posture_agrees_with_section_ve holds: line 333 still carries '$+2.9$ to $+8.7$ points' and the range-carries span. Gate #105's convolved-line spans and gate at :4140 ('positive at every' >= 6, stays 6) unaffected. The three routed edits add no pin change either (re-checked with all 13 applied).


## CONVENTION_VIOLATIONS (6)
1. LAYER/RUNG CONFLATION LEFT STANDING INSIDE THE CAPTION EDIT 8 REWRITES. tab:ladder's first column header is literally 'Layer' and the caption's next sentence is 'Every row prices one layer', while Edit 8 inserts 'binding among the layers with a coverage property' into that same caption and Edits 3 and 10 call the same rows 'rungs'. After the edit set, 'layer' carries the uncertainty-source sense and the estimator sense one clause apart, and prose disagrees with the table it points at. The header string 'Layer & Marginal (pp) & Degrees of freedom & Status' is NOT gate-pinned (count 1 -> 1, absent from every gate constant), so this is cheap to reconcile — e.g. header 'Rung', caption 'Every row is one rung on that layer'. The draft is on the right side of the convention and simply stops halfway.

2. EDIT 2 OVER-DEMOTES A LIVE DISCLOSURE. 'I retain the band sweep as a wiring check on that footing, not as identified content' demotes the SWEEP; only its MONOTONICITY is forced. The sweep's endpoints are quoted as a convention sensitivity range in the same paragraph ('$+5.0$ to $+12.6$ points over the full band'), in tab:floorband, tab:oosfloor's delta columns and tab:lowband. Fix: 'I retain the band's monotone response as a wiring check...'. Otherwise a reader can cite this sentence to discount the band columns the paper depends on.

3. EDIT 7 places its mechanical claim in a note with none of its inputs. 'the one cluster carrying a third of the total leverage' lands in the Notes to tab:uncertainty; the 0.33 leverage, the 5.9 effective clusters and the 31 nominal clusters live in the Notes to tab:ladder. Add a pointer (Table~\ref{tab:ladder}) or the reader meets an unsourced fraction.

4. Register/concision (Eugene's voice): Edit 5 says 'in the next column' TWICE in one cell; Edit 4 says 'outside' twice in one sentence ('outside the quoted ... interval' then 'landing outside the interval this paper quotes'); Edit 3 re-states 'the production hard-maximum form ... the central elasticity' that this paragraph's own opener ('Holding the production hard-maximum form and the imported elasticity fixed') fixes ~700 characters earlier.

5. Edit 6 introduces '5.5--7.7\%' where the three body-prose sites use '5.5\%--7.7\%' (the '5.5--7.7\%' form exists only in tab:params). Prefer the prose form in a note.

6. NO anti-condition acted on: Webb is never called narrowest; the abstract is untouched (line 31 byte-identical, \par intact); no beta_1 sign flipped; the 44.70/35.6 failing cell, 40,234, the 53.7\% basis and the Table-27 rows are all untouched; post-float notes stay post-float (Edits 6, 7, 10 all edit the \noindent{\footnotesize ...\par} paragraphs in place and nothing moves into a float).


## COLLISIONS (4)
1. Edits 3 and 4 are both mid-line-333 — the assembly paragraph that carries ALL 15 ASSEMBLY_SPANS and is A-posture's canonical territory. If A-posture also edits line 333 (C-24's posture verb, the hull sentence, the +5.6 posture clause), whichever set applies second will find its anchor intact only if the other set did not touch these exact bytes. Edit 3's OLD ends at 'I attach no posture', which is the first four words of the posture sentence A-posture most likely holds; Edit 4's OLD abuts the fonseca/aladangady counterweight run. Apply B-ladder's line-333 edits FIRST or re-anchor.

2. Edits 1 and 2 are both mid-line-323 (§V.E's 'Three qualifications' paragraph). Edit 2's OLD is the gate-pinned sentence 'This is why the reported range, and not the sign, carries the paper's identified content.' — a natural target for A-posture (range-carries posture) and for any drafter holding the sign-forcing demotion. Same sequencing risk.

3. The three COORDINATOR-ROUTED C-38 spans are explicitly OUTSIDE B-ladder: L277 is §V.B (E-composition / whoever holds the Path B verification-claim paragraph) and L532 is §V.F, where the same line carries the 88.7\%/85.7\% shared-basis figures and the 'within 2.1\%' calibration-mixing sentence — F-assembly and G-denominators territory. Both L532 OLDs are on ONE 4KB+ line, so two sibling edits to that line collide. Route deliberately, do not apply blind.

4. Edit 5 edits row 439 of tab:uncertainty (headline marginal, sampling cell). G-denominators or a T8 holder may edit the same row's calibration cell — different cell, same line, so anchors must be sequenced.


## NOTES
Mechanically the cleanest draft I have verified this round: 13/13 OLDs unique, every CENSUS row reproduces exactly, +532 tokens exact, zero pinned spans lost, both floor_ladder orderings hold, gate #98 and both posture tests hold, abstract untouched. C-20's hard part is genuinely carried (Webb third-narrowest of nine; CR2-BM widest untruncated). But four substantive claims fail: the grid-truncation reasoning runs backwards (the clip makes the two widest rungs NARROWER, so it cannot explain their width), '+3.5 at the in-sample calibration' is inside the interval Edit 4 declares the corrected member outside, the 4.991% read does enter the interval Edit 6 says none of the three enters, and the wild bootstrap does not re-draw the leverage profile. Fix those four, scope Edit 2 to the monotone response, reconcile Layer/Rung in the caption Edit 8 already opens, then apply. UNVERIFIED: the '100~PSA / hard-maximum' label is inferred from the production config recorded in scaled_null (P7_restoration floor_mode 'max', psa_speed 100.0) — floor_inference_correction_v2_results.json records neither key; and Edit 9's overfull-hbox risk (42-char status cell vs 36 today) needs a build.