# DRAFT — Round 32 Wave 2, cluster G (denominators, scope-of-claim, expectations)

Assigned: C-31, C-36, C-37, C-42, C-43, C-44, C-45, C-46, C-62
Region worked: Sections I, III.B, VI.D, VII, Appendix O. Nothing outside it.
Target file (all edits): `paper/v18/revised_paper_v18.tex` (canonical). Every OLD span below occurs
**exactly once** in the canonical file **and exactly once** in `revised_paper_v18_long_abstract.tex`
(measured), so the coordinator's mirror is a straight second application. Line 31 is untouched.

Baseline line numbers as read this session (the inventory's numbers are pre-`66df169` and run ~6 low):
§I ¶52, tab:headline row 4 = line 79, tab:headline post-float notes = line 90, Definitions ¶ = line 92,
§III.B = 135–152, §VI.D = 588–627, tab:danish notes = line 625, §VII.B = line 641, App. O ¶1 = line 1401.

No condition in this cluster turned out to rest on a wrong premise, so there is no `## NOT DRAFTED`
block. Four conditions have limbs at sites **outside** this region (§V.B, §V.E, §VI.A, §VIII, §VIII.A);
those are listed under `## OUT-OF-REGION LIMBS` and were deliberately not drafted here.

---

## Edit 1 — quote the expectations denominator beside the cap-relative one in tab:headline's marginal row (C-31)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
an anchor convention rather than a central tendency; the range carries the identified content (Section~\ref{sec:identification}) & floor-read wild-cluster bootstrap-$t$
NEW:
an anchor convention rather than a central tendency; the range carries the identified content (Section~\ref{sec:identification}); every point of it is a share of the cap-relative benchmark, and the same $+\$42.6$ billion is 49\% of the \$87.8 billion expectations-based shortfall under the central intra-2022 allocation and 23\% under the settlement-aware one, each an allocation-conditional upper bound (Section~\ref{sec:method-benchmark}) & floor-read wild-cluster bootstrap-$t$
RATIONALE: C-31's prescribed fix is one clause in T1's off-window-marginal row; the row previously quoted only the cap-relative denominator, which §III.B itself declines to call a policy miss. The "allocation-conditional upper bound" tag carries §III.B's governing reading to the quoting site rather than restating a bare ratio.
LITERALS_INTRODUCED: none new to the manuscript. `49\%` and `23\%` are the two ratios already derived at §III.B (line 150: "roughly 23\% and 38\% respectively at the 75.6\% allocation"; "amounts to 49\% of the expectations-based shortfall"); `\$87.8` is `expectation_benchmark_results.json` `e_benchmark_b = 87.83158655603347`; `$+\$42.6$ billion` is the committed off-window marginal. Arithmetic re-checkable: 42.608/87.832 = 48.5% -> 49\%; 42.608/186.778 = 22.8% -> 23\%.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none. Line 79 carries no gate literal >= 20 chars (measured by AST-extracting every string constant in `tools/liveness_gates.py` and testing membership in the line). `\$42.6 billion on either denominator` (gate on §VII.B) is on line 641 and is untouched.

---

## Edit 2 — state the inequality-form scope condition where the Danish sign is declared forced (C-36)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
The zero-gap leg therefore must prepay faster, the Danish trapped balance must come in lower (\$687.8 billion against \$749.0 billion), and the gap must be positive.
NEW:
The zero-gap leg therefore must prepay faster, the Danish trapped balance must come in lower (\$687.8 billion against \$749.0 billion), and the gap must be positive. That premise is an inequality about this episode, not a property of the design, and it scopes what the exercise establishes: it holds because the book is closed at 2017--2021 originations and the window's market rate stood above essentially all of its coupons in essentially every month. Where a book's rate gap is mixed in sign---another cycle, another country, a portfolio open to new originations at the prevailing rate---the inequality fails and the sign becomes a composition question this design does not answer, since the elasticity is imported rather than estimated. Neither this sign nor the marginal's transports without re-checking it.
RATIONALE: C-36 asks for the scope condition attached to the Danish sign-invariance statement. Inserted immediately after the forcedness derivation and before the sweep sentence, so the forced-sign argument and its scope read as one unit. The hedge "essentially all ... essentially every" is copied from the register of the preceding clause in the same paragraph ("a negative gap in essentially every cell over essentially the whole window"), which is also what keeps it true of the 0.47% of exposure above 5.09% and of the panel's two uncovered months (`sign_forcing_stats_results.json` `window.uncovered_months = 2`).
LITERALS_INTRODUCED: none. No number appears in the new text; `2017--2021` is the sample's standing label (16 prior occurrences).
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: line 596 carries seven gate literals — `\% of exposure below the window-minimum` (DANISH `otm_premise`, f-string), `could not have come out otherwise` (`forcedness_stated`), `What is not forced is the magnitude` (`magnitude_is_the_content`), `44\% larger` (`vs_headline`), `danish\_offwindow\_floor`, `forced by construction`, `in-sample calibration point`. The insertion is between two complete sentences and splits none of them; all seven survive byte-identically (re-measured after the in-memory apply: counts unchanged).

---

## Edit 3 — state the gate suite's domain in Appendix O ¶1 (C-37)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
A green gate suite is therefore not self-certifying, and this table exists so the judgment itself can be audited.
NEW:
A green gate suite is therefore not self-certifying, and this table exists so the judgment itself can be audited. Its domain is narrower still: every gate reads the manuscript source and the frozen artifacts, so it can establish that a printed literal matches the artifact it came from and that the two sides of a claim have not moved apart, never that an artifact's own premise is sound. And one defect class it structurally could not see survived every round of it---text correctly derived and present in the source but positioned off the physical sheet, which only a render-layer check reading the built PDF could fail on.
RATIONALE: Sourced to the two docstrings and nothing else: `tools/liveness_gates.py:6-22` declares four gate classes, all of which read the .tex and the frozen artifacts (classes 1-2 are greps on the manuscript, class 3 is a manuscript-vs-manifest cross-check, class 4 is an abstract-scoped span check); `tools/render_gate.py:2-9` states that every gate in that file reads the .tex and the artifacts, none reads the built PDF, and that the off-sheet defect "survived every round because every literal was present and correctly derived IN THE SOURCE". This strengthens the appendix while conceding, which is why it is worth its words.
LITERALS_INTRODUCED: none. **No count is printed** — not the gate count (it moves every round) and not a test count (`tests/*.py` defines 293 `def test_` functions against a claimed 495 collected; the DA's "479" is unverifiable, per the inventory's own instruction).
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: `A green gate suite is therefore not self-certifying` (VERDICT_AUDIT_SPANS `epistemic`, gate #104) is inside OLD and is preserved byte-identically at the head of NEW; `\label{app:verdicts}` and `\label{tab:verdicts}` are elsewhere in the appendix and untouched.

---

## Edit 4 — retire the cross-leg ranking as a measurement and carry Batzer et al. to the ranking site (C-42, C-43)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
so the trade-off's binding cost is denominated in mobility rather than in institutional cash flow (Section~\ref{sec:conclusion}).
NEW:
so the trade-off's binding cost is denominated in mobility rather than in institutional cash flow (Section~\ref{sec:conclusion}). That ranking is an external-evidence ranking, not a within-paper measurement: I measure the institutional leg and import the mobility leg at an elasticity I never re-measure, so the two are nowhere expressed in one unit. The one household-side magnitude this paper carries is \citepos{batzer2024} roughly \$2.4 trillion of foregone capital gains (Section~\ref{sec:lit}), against an institutional gap of $+\$61.2$ billion---and the two are not commensurable: a stock of foregone gains on a counterfactual in which households relocate is not a cash flow over forty-two months. What the comparison supports is the ranking's direction, not the ratio.
RATIONALE: One edit discharges both conditions at the site where the ranking is actually asserted in §I. C-42's remedy is the asymmetry on the page (institutional leg measured, mobility leg imported), not a deletion of the ranking — the ranking still holds on external evidence. C-43 asks that the one household-side magnitude the paper carries appear where the ranking is asserted, with its scope stated. The final clause is deliberately weaker than a ratio claim: 2.4trn against 61.2bn is ~39x, but a stock against a 42-month flow does not license a ratio, so I state the direction and decline the ratio rather than printing "40x".
LITERALS_INTRODUCED: none new. `\$2.4 trillion` and `batzer2024` both come from §II line 100 (their only prior occurrence, verified: `batzer2024` count 1 before). `$+\$61.2$ billion` already occurs 17x. `forty-two` already occurs at line 92 ("nineteen of the forty-two QT months") and matches `fn:manifest`'s "42 active QT months". `\citepos` is defined at line 22 and used 18x.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: `the trade-off's binding cost is denominated in mobility` is inside OLD and survives byte-identically. Line 52's three gate literals (`$-\$89.4$ to $-\$117.7$ billion`, `\% of the benchmark)`, `forced rather than found`) all sit later in the same paragraph and are not crossed by the insertion.

---

## Edit 5 — scope the no-outcome-holdout claim to the cash-flow margin and record the infeasible half (C-44)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
One global property of the design should be stated here as well as in the limitations, because every number below inherits it: \emph{no outcome-holdout months exist anywhere in this paper}, without exception.
NEW:
One global property of the design should be stated here as well as in the limitations, because every number below inherits it: \emph{no outcome-holdout months exist anywhere in this paper}, without exception. That statement is scoped to the cash-flow margin, and the two halves of it are not equally repairable. The identified object has nothing to hold out: the marginal is a difference between two simulations, so no realized outcome corresponds to it, and the nineteen-month construction below can falsify the floor's temporal stability and nothing else. A holdout on the level's fit is conceivable but not attempted, since it would mean splitting the single cumulative path against one cap schedule that the benchmark is. The household margin admits outcome moments this design does not use, since it imports the mobility elasticity rather than estimating it (Section~\ref{sec:limitations}).
RATIONALE: The disclosure is carried into the claim, not deleted: the italic sentence stands, and the scope, the reason one half is impossible and the other merely not attempted, and the household-margin exception are added. The impossibility reason is the paper's own, taken verbatim in substance from §VII's floor-stability paragraph ("no realized prepayment from the held-out months enters either simulated leg, so the construction can falsify only the floor calibration's temporal stability, never the marginal against realized data"). I deliberately do **not** call the level-fit holdout infeasible, because it is not: it would require splitting the benchmark, which is a choice not a barrier — so it is recorded as conceivable-and-not-attempted, which is the honest version of C-44's "record it infeasible with the reason".
LITERALS_INTRODUCED: none.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: `no outcome-holdout months exist anywhere` (2 occurrences file-wide, line 92 and §VIII.A line 747) is inside OLD and preserved byte-identically; the `\emph{...}` delimiters are preserved. Line 92's other two gate literals (`above the clean band`, `in-sample calibration point`) are not crossed. Edit 6 below touches the third (`the nineteen-month floor variant ...`) and preserves it.

---

## Edit 6 — say what the nineteen-month construction actually holds out (C-44)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
the nineteen-month floor variant reported later is an input-stability check rather than an outcome holdout.
NEW:
the nineteen-month floor variant reported later is an input-stability check rather than an outcome holdout: what it holds out is calibration months, not the benchmark.
RATIONALE: C-44 requires the existing temporal holdout named at the site where the no-holdout criticism lands, "stating precisely what it holds out (calibration months, not the benchmark)". Ten words, appended after the pinned span rather than inside it.
LITERALS_INTRODUCED: none.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: `the nineteen-month floor variant reported later is an input-stability check rather than an outcome holdout` is the gate literal `holdout_relabelled_body` (RELOCATED_TO_BODY) **and** the target of the mutation `body_drops_holdout_relabel` in `tests/test_abstract_hedge_gate.py:183-186`. NEW contains it byte-identically as a prefix; only the terminal `.` becomes `:` **after** the pinned substring ends, so both the gate's `in tex` test and the test's `replace` mutation still see the exact string. Verified by re-measurement: count 1 before, 1 after.

---

## Edit 7 — name the fiscal incidence of the $1-P$ wedge in §VI.D (C-45)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
Both legs credit retired balance at par; under cash accounting the market-value buyback credit reverses the gap's sign, so the case as stated here stands on the benchmark's own face denomination, with the incidence bracket priced in Section~\ref{sec:pathb}.
NEW:
Both legs credit retired balance at par; under cash accounting the market-value buyback credit reverses the gap's sign, so the case as stated here stands on the benchmark's own face denomination, with the incidence bracket priced in Section~\ref{sec:pathb}. That incidence has a name. The $1-P$ wedge the U.S. rule collects from a moving household accrues to the bondholder, and the bondholder here is the SOMA portfolio, whose earnings reach the Treasury as remittances: under the cash-haircut reading the Danish rule hands that wedge to the households who move and takes it from general taxpayers. So the reversal prices a transfer changing direction, not a resource cost, and its welfare sign turns on the marginal value of public funds against that of household liquidity---neither of which this framework measures.
RATIONALE: C-45's economics are already in §V.B ("the $1-P$ wedge on bought-back face is exactly the par windfall a moving household pays the bondholder under the U.S. rule and keeps under the Danish one, so the cash-flow cost is the disappearance of a household-to-bondholder transfer, not an added resource cost"). What is missing everywhere is the identity of the bondholder — the SOMA portfolio, whose earnings are remitted to Treasury — and the welfare-sign statement. This is the §VI.D home for it; the §VIII "costs the Federal Reserve" sentence is out of region (see OUT-OF-REGION LIMBS).
LITERALS_INTRODUCED: none. `gap_face_b = 61.18834`, `early_face_E_b = 470.65325`, `gap_cash_range_b = [-117.660, -89.421]`, `code = "REVERSES"` are all already printed at §V.B; nothing new is quoted.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none inside OLD except `in-sample calibration point`, which is elsewhere on line 627 and not crossed. The BUYBACK_BRACKET_SPANS pins (`the balance-adjustment reading is the benchmark-consistent one`, `a household-to-bondholder transfer, not an added resource cost`, `the par windfall it would otherwise have extracted from moving households`, `The gap's sign is therefore incidence-conditional`) all live at §V.B line 273 and §VIII line 733; counts re-measured unchanged (1 -> 1 each). NEW introduces the distinct string `not a resource cost`, which is not on any ZERO_COUNT list.

---

## Edit 8 — carry the incidence into tab:danish's notes (C-45)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
Gap $=$ U.S. leg $-$ Danish leg; a negative gap means the Danish regime traps more than the U.S. regime.
NEW:
Gap $=$ U.S. leg $-$ Danish leg; a negative gap means the Danish regime traps more than the U.S. regime. Incidence: every leg is denominated at face, the benchmark's own denomination; under the cash-haircut reading of the market-value buyback the gap reverses sign (Section~\ref{sec:pathb}), and the wedge that reverses it is a transfer from the SOMA portfolio---hence from Treasury remittances---to the households who move, not a resource cost.
RATIONALE: C-45's fix names T13's notes explicitly, and the table is read standalone — every cell in its Gap column is a face-denominated number whose sign the cash reading flips. Placed at the end of the **unlettered preamble**, before `\quad a`, per the post-float note convention (unlettered general items first, then `\quad <letter> ` items). The note stays in the post-float paragraph; nothing moves inside the float.
LITERALS_INTRODUCED: none.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: line 625's two gate literals are `forced by construction` and `in-sample calibration point`, both in items b/c/d further along the same paragraph; neither is crossed.

---

## Edit 9 — add the missing ex-ante primary-rate offset to §VI.D's omission list (C-46)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
Each omission is a held-fixed feature of the U.S. leg, not a measured invariance.
NEW:
Each omission is a held-fixed feature of the U.S. leg, not a measured invariance. One further omission is a price rather than a feature, and its direction runs against the reported relief. Every figure here is ex-post, computed on a coupon stack originated under the U.S. payoff rule; under a market-value payoff rule the repurchase option is written into the bond series and priced into the coupon ex ante, so the same households would have borrowed at a higher rate for the life of the loan \citep{campbell2013,berg2018}. That premium is netted nowhere here---the only ex-ante rate term the transplant carries is Berger et al.'s roughly one-basis-point equilibrium shift, and it prices the refinance-in-place channel alone---so $+\$61.2$ billion is gross institutional relief, not a net social gain.
RATIONALE: The new item is placed **after** the existing "held-fixed feature" summary rather than inside the list, because a price is not a held-fixed feature and would falsify that sentence if folded into it. The signed direction is stated as a welfare/cost offset (the relief is gross of the ex-ante option premium borrowers would pay), **not** as a movement in the trapped-liquidity accounting — the accounting sign of an ex-ante coupon repricing is not computed anywhere and I do not assert one. The paper's own imported ex-ante rate term (Berger et al.'s ~1bp GE shift, §VI.D earlier in the subsection) is named so the reader can see it covers the refinance-in-place channel only.
LITERALS_INTRODUCED: none. "roughly one-basis-point" restates the existing "shifts the equilibrium mortgage rate by only about one basis point" in the same subsection; `$+\$61.2$ billion` already occurs 17x.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none inside OLD. Both bib keys exist and are already cited: `campbell2013` (`references.bib:605`, cited at line 735) and `berg2018` (`references.bib:50`, cited at lines 112 and 735) — nothing to add to the .bib, as C-46 states.

---

## Edit 10 — flag the ex-post basis in tab:danish's production-row note (C-46)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
which under this anchor is forced by construction rather than found: see Section~\ref{sec:abm-danish}.\par}
NEW:
which under this anchor is forced by construction rather than found: see Section~\ref{sec:abm-danish}. This row is ex-post on the U.S. coupon stack: no ex-ante repricing of the repurchase option into the coupon is netted from either leg, an omission signed against the reported relief (see text).\par}
RATIONALE: C-46's fix asks for the omission in T13's notes as well as the list. Appended to item d (the production estimate), which is the row the $+\$61.2$ billion comes from. "(see text)" follows the convention already used in item a of the same note.
LITERALS_INTRODUCED: none.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: `forced by construction` is inside OLD and preserved byte-identically; the `\par}` terminator of the post-float note paragraph is preserved.

---

## Edit 11 — recast the open timing question as possibly ill-posed, at the settlement-alignment variant (C-62)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
The decomposition is unchanged in substance, and the null still recovers the large majority of the benchmark under either convention.
NEW:
The decomposition is unchanged in substance, and the null still recovers the large majority of the benchmark under either convention. The variant also bears on the one question every estimator here leaves open. If the monthly series each estimator's path is scored against is a cash-arrival object---reported roll-off smeared by an agency remittance lag and, in its CPR form, clipped by a back-out whose non-negativity rule pins four months to exactly zero and posts the displaced mass into the next month's reading (Section~\ref{sec:method-benchmark}; Appendix~\ref{sec:robustness-seasonalfloor})---then a monthly path is not a behavioral object, and the path-level timing question may be ill-posed rather than a failure every estimator shares. I state it as a candidate account, not a finding: reporting mechanics and behavior arrive in the same series, and nothing here separates them.
RATIONALE: §VII.B is the in-region site where the reporting-and-remittance account is already *measured* (the settlement-aligned \$722.7bn benchmark, the $-5.5$\% re-basing, the remittance kernel), so the ill-posedness reading is stated where its evidence sits rather than asserted in a limitations list. It is framed as a candidate, per C-62's own wording, and it does **not** say the zero months flip the frozen timing rule — the rule's status (passed, with nothing claimed from the pass) is discussed in Appendix N and is untouched. The clause "in its CPR form" is load-bearing: the non-negativity clip is the CPR back-out's, not the dollar series' (§III.B line 137).
LITERALS_INTRODUCED: none. "four months" restates §III.B line 137 ("four months come in at exactly zero"), traced there to `h1_zero_months_diagnosis`.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: line 641 carries `\$42.6 billion on either denominator`, `settlement\_months\_benchmark` and `the QT window is half-open`, all earlier in the same paragraph; none is crossed, all re-measured at count 1 after. `the path-level timing question remains open for every estimator` (2 occurrences, §VIII lines 731 and 751) is **not** edited — my sentence adds a candidate account beside it and does not restate or weaken it.

---

## CENSUS

Measured with `str.count` on the canonical file before, and on the in-memory result after applying all
eleven edits in order (E1..E11). Every OLD asserted at exactly 1 immediately before its own replace.

### Numeric literals and cited keys whose count moves
| string | before | after |
|---|---|---|
| `49\%` | 11 | 12 |
| `23\%` | 2 | 3 |
| `\$87.8` | 6 | 7 |
| `$+\$42.6$ billion` | 10 | 11 |
| `$+\$61.2$ billion` | 17 | 19 |
| `2017--2021` | 16 | 17 |
| `\$2.4 trillion` | 1 | 2 |
| `batzer2024` | 1 | 2 |
| `campbell2013` | 1 | 2 |
| `berg2018` | 2 | 3 |
| `forty-two` | 1 | 2 |
| `four months` | 3 | 4 |
| `nineteen-month` | 1 | 2 |
| `basis-point` | 2 | 3 |
| `1-P` | 3 | 4 |
| `holdout` | 33 | 34 |
| `\citepos` | 18 | 19 |

### New non-numeric strings (each previously absent)
| string | before | after |
|---|---|---|
| `taxpayer` | 0 | 1 |
| `Treasury remittances` | 0 | 1 |
| `ill-posed` | 0 | 1 |
| `not a resource cost` | 0 | 2 |
| `ex-post` | 0 | 2 |
| `remittance` | 3 | 6 |
| `SOMA portfolio` | 2 | 4 |

### Numeric literals deliberately NOT moved
`99.53` 2 -> 2 · `par windfall` 2 -> 2 · `5.61\%` 6 -> 6 · `4.76\%` 9 -> 9 · `\$687.8 billion` 1 -> 1 ·
`44\% larger` 3 -> 3 · `$-\$89.4$ to $-\$117.7$ billion` 4 -> 4 · `outcome holdout` 2 -> 2 ·
`in-sample calibration point` 41 -> 41 · `Table~\ref{tab:danish}` 9 -> 9

### Gate/test-pinned spans (all 1 -> 1 unless noted; every one re-measured after the apply)
`A green gate suite is therefore not self-certifying` (#104 `epistemic`) ·
`the nineteen-month floor variant reported later is an input-stability check rather than an outcome holdout` (RELOCATED_TO_BODY `holdout_relabelled_body`; `tests/test_abstract_hedge_gate.py:183`) ·
`no outcome-holdout months exist anywhere` 2 -> 2 ·
`\% of exposure below the window-minimum` (DANISH `otm_premise`) ·
`could not have come out otherwise` (`forcedness_stated`) ·
`What is not forced is the magnitude` (`magnitude_is_the_content`) ·
`44\% larger` 3 -> 3 (`vs_headline`) ·
`the balance-adjustment reading is the benchmark-consistent one`, `not an added resource cost` (BUYBACK_BRACKET_SPANS) ·
`\$42.6 billion on either denominator`, `settlement\_months\_benchmark`, `the QT window is half-open` (§VII.B) ·
`forced by construction` 2 -> 2 · `forced rather than found` · `danish\_offwindow\_floor` 2 -> 2 ·
`above the clean band` 5 -> 5 · `the trade-off's binding cost is denominated in mobility`

### Global invariants re-measured after the apply
- All 19 `ZERO_COUNT` phrases still count 0 (including `equal in size to the lock-in marginal` and `three independent legs`).
- All 4 `EXACTLY_ONE` phrases still count 1.
- `HARDCODED_XREF`: the five forbidden patterns (`Table \d`, `Figure \d`, `Section [IVX]+`, `Appendix [AB]`, `Equation (\d)`) match nothing in any NEW string; every cross-reference added goes through `\ref`.
- Line count unchanged (1436 -> 1436); no paragraph split or join, so every paragraph-scoped gate keeps its line.
- Line 31 byte-identical.
- Both files: each OLD occurs exactly once in `revised_paper_v18.tex` **and** exactly once in `revised_paper_v18_long_abstract.tex`.

---

## UNVERIFIED

1. **PDF-side effects.** +834 words (~1.5 pages of body text) across five floats-adjacent sites. I could not build or run the render gate (read-only, and `tools/*` may not be executed), so I cannot confirm no float is pushed off a page. `tools/render_gate.py:44` sets `EXPECTED_PAGES = {"revised_paper_v18.pdf": None}  # informational only`, so the page count itself will not fail — but off-sheet positioning would. Confirmed by: one `tectonic` build plus `tools/render_gate.py`, by the coordinator.
2. **Edit 1's row height.** tab:headline is a `longtable`, so it breaks across pages and the +41 words in column 2 cannot overflow a float box. Not measured against the built page.
3. **Whether §III.B needs anything for C-31.** I read line 150 as the *source* of the two ratios and their governing upper-bound reading, not as a site needing an edit — it already states `49\%`/`80\%`, the fall to `23\%`/`38\%` at the 75.6% allocation, and the allocation-conditional-upper-bound sentence that "govern[s] every site at which these ratios appear". If the coordinator reads C-31 as also requiring a change at line 150, that is a judgement call I did not make.
4. **The ~39x Batzer/Danish ratio.** 2400/61.2 = 39.2, so "~40x" (the inventory's phrasing) is arithmetically right; I declined to print it because the numerator is a stock and the denominator a 42-month flow. If Eugene wants the ratio on the page, Edit 4's last sentence is where it goes.
5. **`tests/` beyond the hedge-gate file.** I grepped `tests/*.py` for every span I touch and found exactly one hit (`test_abstract_hedge_gate.py:183`, handled in Edit 6). I did not read all 451 tests.

---

## WORD_COUNT_IMPACT

**No edit touches line 31.** The abstract is byte-identical before and after (verified by string comparison
of line 31 across the in-memory result), so its 294-word count and gate #101's tie to the response
letter are both undisturbed. **Abstract word delta: 0.**

Body word delta: **+834** words total, by edit —
E1 +41 · E2 +101 · E3 +88 · E4 +95 · E5 +105 · E6 +10 · E7 +90 · E8 +48 · E9 +112 · E10 +33 · E11 +111.

---

## OUT-OF-REGION LIMBS (deliberately not drafted; they need the §V/§VI.A/§VIII owner)

These are limbs of my own conditions whose only remaining site lies outside Sections I / III.B / VI.D /
VII / Appendix O. I did not write OLD spans for them, to avoid colliding with a sibling drafter.

- **C-31, abstract limb.** The abstract quotes only the cap-relative share. C-31's fix pairs one abstract clause with the T1 row I drafted; the abstract clause is C-33's territory (and C-33/C-34/C-35 are one sequenced abstract edit). Any clause added there changes the 294-word count.
- **C-36, §V.E limb (line 323) and §VIII limb.** Line 323 is where `99.53\%`/`5.2311\%` are printed and where the identified-content sentence lives; C-36 asks for the same scope sentence there and a scope clause in §VIII. Edit 2 covers the Danish site only. Note for whoever takes line 323: C-38 also edits that sentence, so sequence them.
- **C-42/C-43, §VI.A (line 542) and §VIII (line 733) limbs.** §VI.A carries the double declination ("I do not translate the \$764.7 billion shortfall into welfare terms"); §VIII carries the leg-(2)-vs-(3) sentence. Edit 4 puts the asymmetry and the Batzer magnitude in §I only.
- **C-44, §VIII.A limb (line 747).** `no outcome-holdout months exist anywhere in this paper` recurs there verbatim, followed by "The neares[t]..." — the same scoping clause belongs there. Edits 5-6 scope the §I occurrence only, so the two sites will read differently until that lands.
- **C-45, §VIII limb (line 733).** `as reserve drain the rule costs the Federal Reserve exactly the par windfall it would otherwise have extracted from moving households` is the sentence C-45 says obscures the incidence, and it is gate-pinned (BUYBACK_BRACKET_SPANS `conclusion_sign`) — so the fiscal-incidence paragraph must be added **beside** it, not by rewriting it.
- **C-62, §VIII.A limb (line 751) and §V.F limbs (lines 528/532 in the inventory's numbering).** `the path-level timing question remains open for every estimator` sits at lines 731 and 751; the ill-posedness recast belongs at 751 too. Edit 11 states it once, in §VII.B, where the evidence is.

---

## SIBLING-DRAFTER INTERACTION (checked, not assumed)

I diffed my eleven OLD spans against `DRAFT_w2_D-mechanical.md`, `DRAFT_w2_E-composition.md` and
`DRAFT_task3.md` in the shared scratchpad. **No OLD span is shared.** Two adjacencies the coordinator
should sequence rather than worry about:

- **Line 92 is edited by both me (Edits 5, 6) and W2-D (its C-30 definitions edit).** The three OLD
  spans are disjoint substrings of the same paragraph and none contains another. W2-D's own census
  lists my Edit 6 pin as "unchanged", so either order works; applying W2-D first is marginally safer
  because its edit is the earlier substring in the line.
- **W2-D renames the partition vocabulary globally (`mechanical` 42 -> 13, T1's "Mechanical null" row
  label -> "No-elasticity").** None of my OLD spans and none of my NEW text contains `mechanical`,
  `Mechanical` or `mechanical-majority`, so the rename cannot stale my spans and my insertions cannot
  reintroduce the retired word. My Edit 1 is in tab:headline **row 4** (the off-window-marginal row);
  W2-D's label edit is row 3. Disjoint.
