# Adversarial verdict — G-denominators

VERDICT: APPLY_WITH_LISTED_FIXES
edits_checked: 11

## COUNT_MISMATCHES (0)

## REFUTED_CLAIMS (8)
1. Edit 8 (tab:danish unlettered preamble) — HARD REFUTATION. It asserts table-wide that 'under the cash-haircut reading of the market-value buyback the gap reverses sign'. buyback_credit_bracket_results.json .spec = 'incidence bracket on the production rule-only pair', and gap_cash(D) = gap_par − D·E is SUBTRACTIVE (D=0.32: 61.188 − 150.609 = −89.421), so it cannot reverse an already-negative gap. tab:danish rows b and c print Gap = −$728.4B and −$99.9B; row a (+$925.5B) is unpriced. The claim is false for 2 of 4 rows and unmeasured for a 3rd. Its rationale ('every cell in its Gap column is a face-denominated number whose sign the cash reading flips') is refuted by the same artifact. Fix: merge into item d (where Edit 10 already lands) or scope to 'the production rule-only gap'.

2. Edit 11 — 'reported roll-off smeared by an agency remittance lag'. Refuted by .tex:641, which explicitly denies that attribution: 'Agency remittance is itself a deterministic lag of roughly one month, so that profile is not a description of the remittance cycle: it is an empirical smearing kernel over the months in which a given month's prepayment decisions arrive as cash.' Fix: 'smeared over the months in which a month's prepayment decisions arrive as cash'.

3. Edit 1 — the printed denominator does not support the second ratio. The cell prints '$87.8 billion expectations-based shortfall ... and 23\% under the settlement-aware one'. 23% is 42.608/186.778 (settlement-aware E-benchmark = 839.5299 − 652.7517 = 186.778, expectation_spread_variants_results.json g2.reconstructed_settlement_window_b). 23% × $87.8bn = $20bn ≠ $42.6bn. §III.B supplies the missing reason ('because that shortfall is itself allocation-dependent, the ratio falls as the anticipated share falls'); the cell omits it. Fix: add 'on a larger, allocation-dependent shortfall' or drop $87.8bn from the cell.

4. Edit 3 — 'every gate reads the manuscript source and the frozen artifacts'. Sourced to render_gate.py's docstring but untrue of the suite: gate #101 reads paper/v18/response_to_referees_round22.tex (liveness_gates.py:588, 961) and the figure-script gates read figures/make_figures.py, figures/make_ccf_data.py, abm/monte_carlo_simulation.py (FIGURE_SCRIPTS, read at :1097). The domain conclusion survives; the universal does not. Fix: 'every gate reads text — the manuscript, the response letter, the figure scripts — against the frozen artifacts'.

5. Edit 9 — 'so $+\$61.2$ billion is gross institutional relief, not a net social gain' is a signed-relief statement planted on line 596, which contains zero occurrences of 'incidence', 'face' or 'cash'. buyback_credit_bracket_results.json .verdict.manuscript_action: 'Restate the counterfactual's cash-flow claim as incidence-conditional wherever stated as signed relief.' Fix: 'gross institutional relief on the benchmark's face denomination'.

6. Edit 5 — 'That statement is scoped to the cash-flow margin' mis-locates the scope. 'No outcome-holdout months exist anywhere in this paper, without exception' is true everywhere; C-44's verified note says it 'is unavoidable only for the cash-flow margin'. Fix: 'Its unavoidability is scoped to the cash-flow margin'.

7. Edit 4 — 'the two are nowhere expressed in one unit' is contradicted by the next sentence, which sets $2.4 trillion against $+\$61.2$ billion; both are dollars. The defect is commensurability, not units. Fix: 'nowhere commensurable'.

8. Edit 4 — the $2.4trn scope loses C-43's 'universal-relocation basis'; 'a counterfactual in which households relocate' matches §II line 100's 'had they chosen to relocate' but drops the all-households sense that makes the figure an upper bound. Low severity.


## PIN_VIOLATIONS (0)

## CONVENTION_VIOLATIONS (12)
1. Edit 1 — the target cell already reads '$+2.9$ to $+8.7$ points, basis-invariant'; Edit 1 appends 'every point of it is a share of the cap-relative benchmark'. Both are true on different axes (curtailment-netting basis vs benchmark denominator; expectation_benchmark_results.json basis_load_bearing.reading requires the cap-basis statement, and §III.B carries it), but inside one ~80-word cell they read as a contradiction, and the brief's convention forbids attaching a basis label to a marginal. Fix: drop the clause, or write 'cap-benchmark denominated' and let 'basis-invariant' keep the netting sense.

2. Edit 1 — hedge scope truncated. §III.B's governing form is 'an allocation-conditional upper bound on lock-in's share of a mixed lock-in-and-rate-path surprise, not as a partition of that surprise'. Edit 1 keeps only 'each an allocation-conditional upper bound' — the object of the bound is dropped. Fix: '...upper bound on lock-in's share of a mixed surprise'.

3. Edit 8 — a row-specific incidence claim is placed in tab:danish's table-wide unlettered preamble (which carries only the sign convention and the Gap definition). The post-float paragraph itself is correctly preserved and nothing moves into the float; the violation is the preamble/lettered-item split.

4. Edit 2 — cohesion break. The next existing sentence reads 'Sweeping the refinance-in-place input ... only adds Danish prepayment on top of that'; Edit 2 inserts 647 bytes of transportability material between the forced-positivity conclusion and that 'that'. Fix: relocate the block after 'is forced by construction as well' or after 'I retain both as wiring checks and read neither as evidence.'

5. Edit 9 — same class. The next existing sentence reads 'I therefore report the rule-only gap as a band'; 'therefore' followed from the omissions summary, which Edit 9's ex-ante-premium block now separates from it.

6. Edit 4 — forward reference. It quotes '$+\$61.2$ billion' two sentences BEFORE line 52's own first statement of it ('Recalibrating ... reduces this ... to $+\$61.2$ billion (8\% of the benchmark)'), so the paragraph introduces the figure twice and G's earlier mention carries none of the anchor/incidence conditionality the paragraph then supplies. Relocating within the paragraph is safe: gate 'intro_para_carries_forcedness_and_flip' is paragraph-scoped and I confirmed it passes either way.

7. Edits 5 and 6 — redundant and ambiguous. Edit 5's 'the nineteen-month construction below can falsify the floor's temporal stability and nothing else' restates Edit 6's 'what it holds out is calibration months, not the benchmark' three sentences later in the same paragraph; and 'the nineteen-month construction below' is ambiguous against the next existing sentence's 'Path~A trains on nineteen of the forty-two QT months', a different object. Fix: drop the clause from Edit 5, keep Edit 6.

8. Edit 5 — 'splitting the single cumulative path against one cap schedule that the benchmark is' is unparseable. Fix: 'splitting the benchmark itself — a single cumulative path against one cap schedule'.

9. Edit 2 — 'Neither this sign nor the marginal's transports without re-checking it.' Elliptical possessive with a singular verb and an ambiguous 'it'. Fix: 'Neither this sign nor the marginal's transports without re-checking that inequality.'

10. Edit 11 — 'the one question every estimator here leaves open' asserts it is the only open question. Fix: 'the path-level timing question every estimator here leaves open'.

11. Edit 2 — 'the book is closed at 2017--2021 originations' is the Freddie estimation universe, not the SOMA book (2022 + pre-2017 vintages are 23.1% + 10.6% of book face, .tex:269). Line 323 uses the identical phrase, so the reuse is precedented, but in §VI.D 'the book' reads as the SOMA book. Low.

12. Edits 9/10 — 'ex-post' is new to the manuscript ('ex post' 0, 'ex-post' 0 before; 'ex-ante' 35, 'ex ante' 22). The hyphenated form matches house style; flagged only for confirmation.


## COLLISIONS (3)
1. Edit 1 OLD ('an anchor convention rather than a central tendency; the range carries the identified content (Section~\ref{sec:identification}) & floor-read wild-cluster bootstrap-$t$', line 79) OVERLAPS A-posture's Edit 3 OLD on the 52-byte substring 'an anchor convention rather than a central tendency;'. Order-safe as drafted — A-posture inserts BEFORE the shared bytes and G appends AFTER them, so each preserves the other's anchor and either order applies. But line 79 is tab:headline, A-posture's declared region, and both edits load the SAME cell (~80 words today, +55 combined). G's sibling check covered only D-mechanical, E-composition and task3; A-posture and C-formfork were written after G's draft.

2. Edit 5 OLD and Edit 6 OLD (both line 92) sit inside the '\paragraph{Definitions used throughout.}' paragraph, which the brief assigns to D-mechanical. Line 92 is now edited by four spans across three drafters (G ×2, A-posture Edit 5 'returns $+5.6$ points and is the headline)', D-mechanical Edit 1). I verified all four are pairwise disjoint substrings and none contains another, so any order applies cleanly.

3. No overlap with C-formfork, E-composition or task3. G correctly declined §III.B line 150 (its UNVERIFIED #3), which C-formfork edits twice and D-mechanical four times — that abstention avoided a three-way collision.


## NOTES
Measurement is exceptionally clean: all 11 OLDs count exactly 1 in canonical AND the long-abstract variant, byte offsets pairwise disjoint, and every one of the 34 census rows matched before/after on str.count — zero mismatches. I AST-extracted all 2,375 string constants (>=8 chars) from liveness_gates.py, render_gate.py and all 30 tests/*.py and counted each before/after: no drops. Re-ran the text-side gate logic on the applied file: ZERO_COUNT 19/19=0, EXACTLY_ONE 4/4=1, HARDCODED_XREF all 0, 894.8 window clean, "positive at every" 6 sites 0 unqualified, intro_para forcedness gate True, ASSEMBLY/ABM_LEAD paragraph-scoped intact, abstract 294 words byte-identical (line 31 untouched, gate #101 safe), all 8 \ref targets exist, no stray &/\\/unescaped %. Body +834 words, per-edit deltas exact. Edit 8 must be re-sited before applying — it prints a claim false for two of four tab:danish rows.