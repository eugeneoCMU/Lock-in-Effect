# Adversarial verdict — C-formfork (C-04, C-22, C-23, C-28, C-32)

VERDICT: APPLY_WITH_LISTED_FIXES
edits_checked: 12

## COUNT_MISMATCHES (5)
1. OLD_COUNT_ASSERT: all 12 re-measured with str.count = exactly 1 in revised_paper_v18.tex AND in revised_paper_v18_long_abstract.tex. Sequential application of all 12 succeeds (no intra-cluster self-destruction). Lines: 150,150,227,227,333,532,727,731,731,737,737,737. NO FAILURE.

2. CENSUS: all 64 rows re-measured on the in-memory result. ZERO mismatches. Per-edit char/word deltas: all 12 exact; total +2,996 chars / +469 words as claimed.

3. Edit 5 PINNED_SPANS_CROSSED claims 'all twelve ASSEMBLY_SPANS' — the dict has 15 (6 ladder + 3 posture + 3 censor + 3 counter). Presence re-verified 15/15 before and after, so gate #98 is safe; the stated count is wrong.

4. Draft header says the file is 1,435 lines; str.split gives 1,436 fields (wc -l 1435). Immaterial.

5. Edit 5 says 94.8% is at lines 323/521/802 — confirmed; line 323's instance is the concave-gap variant's null, which is the same object (a beta_1=0 leg is invariant to a gap transform), so the 4th printing is consistent.


## REFUTED_CLAIMS (15)
1. EDIT 3 (hard) 'report no interior point' is FALSE about this manuscript. Interior mixture points are printed at three sites: tab:headline note a (line 90) '$+9.7$ at $s{=}0.25$, $+10.7$ at $s{=}0.4$'; line 323 'rises to $+9.7$ points by $s = 0.25$'; line 715 '$+7.5$ points by $s = 0.1$, $+9.7$ at $s = 0.25$, $+10.7$ at $s = 0.4$'. Counts: '$+9.7$' 4, '$+10.7$' 2.

2. EDIT 3 (hard) 'carry the additive endpoint ... beside every quotation of the headline' is FALSE. Measured: 21 lines quote $+5.6$ (25 occurrences); only 8 carry any additive companion (+11.2, the $+3.5$ to $+13.1$ hull, or the word 'additive'). Lines 46, 58, 79, 92, 110, 211, 342, 345, 368, 641, 717, 803, 1419 do not. The draft's own NOT-DRAFTED block concedes this.

3. EDIT 3 (hard) 'The calibration anchor does not discriminate' contradicts .tex:715 verbatim, twice: 'is the reading the calibration anchor supports' and 'the reading the deep-discount calibration anchors'.

4. EDIT 3 (hard) C-22's premise that the rule is unstated is largely refuted: .tex:715 already STATES it — 'The max form remains production for its semantics --- the floor as a minimum on \emph{total} turnover, the reading the deep-discount calibration anchors --- and because it is the measured form curve's conservative endpoint (below); the aggregate-level comparison is context for the level, not the selection rule for the marginal's form, since the design does not identify levels.' Edit 3 does not unify that rule; it replaces its primary ground (semantics) with a denial, and asserts 'What discriminates is conservatism on the identified object' where the paper's 'identified object' at .tex:227 is an INTERVAL, not a form.

5. EDIT 3 (medium, softening) 'the share itself is not identified anywhere in this design' erases the direction of three live disclosures: .tex:227 'the strictly-involuntary share---death, divorce, and forced relocation---is plausibly well under half'; .tex:323 'the paper's own floor semantics point at the hull's upper region, and the $s = 0$ headline is the curve's conservative endpoint'; .tex:715 'Section~\ref{sec:pathb}'s reading ... therefore does \emph{not} pull the marginal toward the max end'. Non-identification is weaker than, and points away from, what the paper already concedes.

6. EDIT 3 (medium, redundancy) 'which carries no decomposition of realized turnover into voluntary and involuntary parts' restates .tex:227's own 'no component decomposition exists in this design' (count 1) ~2,000 chars earlier in the SAME paragraph; and '$+11.2$ points at the off-window anchors, nearly floor-invariant' duplicates the same paragraph's 'moves the production marginal to $+11.25$ points and makes it nearly floor-invariant ($+11.29$ to $+11.21$ ...)' with a different number 1,000 chars away.

7. EDIT 3 (minor) The draft says it 'takes the third admissible route' of C-22. C-22's third route IS the fit route ('state that fit is doing partition work'), which Edit 3 explicitly refuses. Edit 3 is a fourth, uncommissioned route.

8. EDIT 5 (hard) 'so the ramp the paper runs is the worse-fitting of the two' is FALSE on the leg the paper reports. psa_level_sweep_results.json central legs at floor 4.991: cells['4.991|100|6.5'].share_pct = 100.3633 vs cells['4.991|75|6.5'].share_pct = 102.7975 — the production 100 PSA fits BETTER (|delta| 0.36 vs 2.80). True only on the null's own recovery, which the first half names and the 'so' clause drops.

9. EDIT 4 (medium) The pair mixes a floor change into the form change. 97.8% is max-form IN-SAMPLE (floor_form_results.json max@4.0 null.share_pct = 97.8342); 44.7% is additive OFF-WINDOW (floor 4.991). Same-floor form gaps: 41.91 pp in-sample (97.834 -> 55.927) and 50.09 pp off-window (94.792 -> 44.700). The printed pair implies 53.1 pp. Both are labeled, so it is a comparability defect, but the inference clause rests on it.

10. EDIT 4 (medium, softening) 'so the null's level is as form-dependent as the marginal' understates by ~9x. At 4.991 the marginal's form gap is 5.635 pp (5.5716 -> 11.2070) and the null level's is 50.09 pp standalone (85.70 -> 35.60 shared). The true claim is 'MORE form-dependent than the marginal'.

11. EDIT 4 (minor) Rationale claim 'at the anchor where the additive null was actually run' is false: floor_form_results.json additive@4.0 null.share_pct = 55.92743732152105 — the additive null WAS run in-sample. The draft's own coordinator note concedes it and gives the real reason (a 55.9 literal collision with the form-fork sentence's central-leg figure).

12. EDIT 10 vs EDIT 12 (hard) Contradiction created inside one paragraph (.tex:737). Edit 10: the evidence holds 'under its production floor form, and not under the additive form'. Edit 12: the policy conclusion holds 'on either form'. The paragraph's existing untouched sentence: 'What survives across forms is that the trade-off is modest, not that it is absent' (count 1 -> 1). Two of the three cannot stand; the existing sentence is the committed position, so 'and not under the additive form' is the overclaim.

13. EDIT 10 (medium) Over-broad scope: the opening claim covers all three legs, including (1) TBA liquidity and the '(1) prioritized at real cost to (2)' finding, neither form-conditional. Only the (2)/(3) dissolution is (gate #103's dissolution_scope comment: 'the dissolution claim must stay scoped to face accounting'). Suggest 'under its production floor form (the additive form roughly doubles the margin at issue)' — conditions without denying.

14. EDITS 1+2 seam (medium) Edit 1 establishes the additive null recovers 35.6% (not a majority) at the headline floor; the very next sentence, Edit 2's OLD, is left UNCONDITIONED — 'both objects put the anticipated mechanical component in the large majority of the shortfall' — and Edit 2 then adds a causal gloss ('the majority is large because the caps were set above any prepayment path this book could have delivered') that holds only under the production form. C-04's verified note is precisely that 'A null recovering 35.6% does not partition the object being decomposed'. The surviving-agreement sentence is the site most needing the condition and neither edit gives it one.

15. SUPPORTED (no fault): 44.700 standalone / 35.6035 shared IS the additive null at floor 4.991 (floor_form_mixture cells['4.991|1|0'], s=1==additive per spec/orientation). s=0 IS the curve's minimum at 4.991 (5.5716, rising monotone to peak 11.2411 at s=0.8, 11.2070 at s=1; plateau_within_0.1pp true). Additive marginal 11.2193/11.2070/11.1929 at 4.695/4.991/5.334 confirms '+11.2, nearly floor-invariant'. 101.9415 and 94.7917 confirmed; 101.9415 - 9.0964 = 92.845 matches C-04's stated 92.8 shared at 75 PSA. expectation_check verified 3-for-3 at floor 4.0, 0-for-3 off window with exactly the draft's bands. '101.9' occurs nowhere else in the repo except the review panel and the inventory, same object — the draft's UNVERIFIED item 3 is now CLEARED.


## PIN_VIOLATIONS (8)
1. NONE LOST. Full sweep: 2,186 distinct string constants of length >=10 extracted with ast from tools/liveness_gates.py and all 30 tests/*.py; zero go from count>0 to count==0. Only generic substrings change: 'production' 222->229, 'decomposition' 54->55, 'standalone' 37->39, '\% of the benchmark' 31->32, 'expectations' 14->15 — none in ZERO_COUNT or EXACTLY_ONE.

2. Re-implemented and ran the SHIPPED rules on the result: gate #98 assembly_check = (True, paragraphs 1, missing [], table_missing []); 15/15 ASSEMBLY_SPANS present including posture_binding_layer immediately after Edit 5's insertion. assembly_check has NO ordering assert, so inserting between two spans is safe.

3. Gate #68/#99: abstract 294 -> 294 words; ABSTRACT_HEDGES missing []; ABSTRACT_POSTURE spans and the range-before-point ordering untouched.

4. RELOCATED_TO_BODY: missing [] before and after, including surprise_denominator_body ('projection rather than the non-binding cap, the lock-in channel accounts for roughly half the genuine surprise under the central allocation'), which begins immediately after Edit 9's insertion point, and surprise_share_allocated_body on Edit 1's line.

5. Gate #101 letter_check: all 16 LETTER_CURRENT_LITERALS unchanged; the letter's claimed abstract length still equals the measured 294.

6. Gate #103 BUYBACK_BRACKET_SPANS on Edit 10's line: dissolution_scope 1->1, trilemma_conditional 1->1. Gate #104 VERDICT_AUDIT_SPANS unchanged.

7. ZERO_COUNT (19 phrases) all 0 before and after; EXACTLY_ONE (4 phrases) all 1 before and after; SUPERSEDED_CONTEXTUAL '894.8' unaffected by the new '94.8\%'.

8. HARDCODED_XREF: 0 regex hits on the result. All new cross-refs use Section~\ref{sec:robustness-floor} / \ref{sec:identification}; both labels exist. No bare % introduced, so the (?<!\\)%.* comment strip cannot eat new text.


## CONVENTION_VIOLATIONS (9)
1. HEDGE SCOPE (Edit 7): '(35.6\% under the additive form)' is placed AFTER the max-form-specific hedge 'under any rate response above the baseline turnover it embeds'. That hedge is the max form's censoring property; the additive form never censors, so it does not carry to the additive figure. The landed abstract puts the parenthetical immediately after the number ('still accounts for 85.7\% of it (35.6\% under the additive form), because ...'). Move it directly after '85.7\% of the benchmark'.

2. SOFTENING A TRUE CLAIM: Edit 3's non-identification framing (see refuted_claims) and Edit 4's 'as form-dependent as the marginal'.

3. REDUNDANCY / metadiscourse (Edits 2, 7, 9): three new near-verbatim copies of the same cap-placement inference — 'a fact about where the Committee set the ceiling rather than about how households responded to rates', 'a statement about where the Committee set the ceiling rather than about how households behaved', 'a fact about where the ceiling was set and not about how households behaved'. Measured 'where the Committee set the ceiling' 0->2, 'about how households behaved' 0->2. C-32 asks for the inference where the majority is FIRST stated. DROP Edit 9: it restates the clause it attaches to ('the caps sat far above what any plausible prepayment environment would have delivered') and the E-benchmark counterweight C-32 wants already follows in the existing '---though' clause.

4. PUNCTUATION HABIT (Edit 3): line 227 uses 6 unspaced em-dashes and ZERO spaced ones; Edit 3 introduces 2 spaced ' --- '.

5. GRAMMAR (Edit 6): '..., both under the production floor form and 35.6\% at that floor under the additive one' — the 'both ... and ...' correlative yokes a prepositional phrase to a percentage. Fix: '---both under the production floor form; under the additive form the null recovers 35.6\% at that floor'.

6. C-04's OWN FIX RULE (Edits 1, 6, 7): C-04 says if the shared 35.6% is quoted, derive it in text or quote standalone only. No edit derives it. Edit 6/8 inherit a governing 'shared basis'/'same basis'; Edit 1's neighbour 85.7% is unlabeled and Edit 7's site labels neither (matching the landed abstract). Minimum fix: Edit 1 reads '35.6\% on the same basis (44.7\% standalone)'.

7. ORDERING (Edit 8): '(35.6\% at the headline floor under the additive form)' trails '88.7\% in-sample' rather than the headline-floor figure it corresponds to.

8. C-23 LITERAL (Edit 11): the condition names '+11.2 points, floor-invariant' at the concession; Edit 11 writes '$+11$' plus 'nearly floor-invariant'. Defensible (it preserves the existing literal), but moving 'roughly doubles' to the opening clause puts the comparative ~2,900 chars from the number it doubles — a partial reversal of the ordering fix C-23 asks for. 'roughly doubles' count 2->2 verified.

9. CLEAN: no post-float note (tab:bases/estimators/danish/ladder/oosfloor) is touched or moved into a float; no disclosure deleted (Edit 11 relocates, net literals preserved); no marginal given a basis label; no anti-condition acted on (Webb, two-paragraph abstract, Table 27, 53.7%, 40,234, beta_1 signs, R2:M8 all untouched); the 44.70/35.6 non-majority cell is used correctly as the additive null.


## COLLISIONS (6)
1. HARD, ORDER-DEPENDENT — 3 of my OLDs are destroyed if D-mechanical applies FIRST. (a) Edit 2's OLD contains 'both objects put the anticipated mechanical component in the large majority of the shortfall.' — D's OLD is exactly that sentence, NEW = 'both objects put the anticipated component ...'. (b) Edit 4's OLD contains 'which shows the mechanical model recovers 97.8\% of the benchmark under the standalone scorer' — D's NEW = 'which shows that null recovers 97.8\% ...'. (c) Edit 7's OLD begins 'interacting with a prepayment environment mostly mechanical relative to the caps' — D's NEW = 'mostly scheduled-plus-turnover relative to the caps'. All three are SAFE if C applies BEFORE D: verified that each C NEW reproduces D's OLD byte-identically. MANDATORY ORDER: C before D.

2. BENIGN in both orders: Edit 9's OLD overlaps D's 'the shortfall against the phased caps is mostly mechanical, because the caps sat far above' only on the shared tail 'because the caps sat far above', which neither NEW alters.

3. SAME 5KB LINE (no span intersection, but a coordinator applying by line must sequence): line 150 (Edits 1,2 + 4 D edits), line 227 (Edits 3,4 + 1 D edit), line 731 (Edits 8,9 + 2 D edits), line 737 (Edits 10,11,12 + 2 D edits).

4. CROSS-CLUSTER REGION — Edit 5 is at line 333, which is sec:identification (§V.E), the gate-#98 assembly paragraph. That is F-assembly's declared region AND B-ladder's ('the inference-ladder and binding-layer passages'); the insertion lands directly before posture_binding_layer. C-28's inventory location list does name .tex:333, so the site is condition-sanctioned, but the cluster split does not give §V.E to C.

5. CONTESTED REGION — Edits 1 and 2 are at line 150, §III.B sec:method-benchmark, i.e. the expectations/denominator passage that G-denominators claims ('Sections I, III.B, ... the denominator, scope-of-claim and expectations passages'). G's actual draft does NOT touch line 150, so no live collision.

6. NO OVERLAP with A-posture (lines 31, 46, 79) or E-composition (lines 707, 1091, 1277, 1283, 1300), verified by span intersection against the canonical file.


## NOTES
Mechanics are clean: 12/12 OLDs unique in both files, all 64 census rows exact, no pinned span lost across 2,186 gate/test constants, gates #68/#98/#99/#101/#103/#104 re-run green on the result, abstract 294->294 (no edit on line 31). The failures are substantive. DROP Edit 3: four false or contradictory claims ("report no interior point", "beside every quotation of the headline", "the calibration anchor does not discriminate", non-identification of s) against .tex:90/227/323/715, which already state the rule C-22 asks for. DROP Edit 9 (third copy of one clause). FIX before applying: Edit 5's "worse-fitting" (central leg 100.36 vs 102.80 says the opposite), Edit 4's mixed-floor pair and "as form-dependent as", Edit 7's parenthetical placed inside a max-form hedge, Edit 10's "not under the additive form" (contradicts Edit 12 and .tex:737), Edit 6's grammar. Apply C BEFORE D-mechanical or Edits 2/4/7 fail.