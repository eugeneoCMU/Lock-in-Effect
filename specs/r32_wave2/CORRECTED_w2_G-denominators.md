# CORRECTED — Round 32 Wave 2, cluster G (denominators, scope-of-claim, expectations)

Cluster: **G-denominators**. Conditions: C-31, C-36, C-42, C-43, C-44, C-45, C-46, C-62 (C-37 dropped — LANDED).
File (all edits): `paper/v18/revised_paper_v18.tex`. Mirror `paper/v18/revised_paper_v18_long_abstract.tex`
is a straight second application: **every OLD below counts exactly 1 in BOTH files** (measured).

**Re-anchored against current bytes** (HEAD `d1bf578`, 1,460 lines). Draft's 11 OLDs all still counted 1,
so **0 stale anchors needed repair** — but the draft's *line numbers* were all wrong (paragraph splits +
retitle moved everything: §I 52 unchanged, §V.E/§V.B splits pushed §VI.D 596→618, tab:danish notes 625→647,
§VII.B 641→663, App. O 1401→1426). **Two draft edits were dropped and two pairs merged: 11 → 7 edits.**
Line 31 untouched; abstract byte-identical at **323 words**; body **+648 words**.

Current line map for this cluster: §I ¶ = **52** · Definitions ¶ = **92** · §VI.D transplant ¶ = **618**
(carries BOTH Edit 2 and the old Edit 9 target) · tab:danish post-float notes = **647** · §VI.D
implications ¶ = **649** · §VII.B = **663**.

---

## Edit 1 — retire the cross-leg ranking as a within-paper measurement and carry Batzer to it (C-42, C-43)
LINE: 52 (§I, paragraph-final)
OLD_COUNT_ASSERT: 1
OLD:
```
which is the benchmark's own denomination (Section~\ref{sec:pathb}).
```
NEW:
```
which is the benchmark's own denomination (Section~\ref{sec:pathb}). The mobility-versus-cash-flow ranking above rests on external evidence, not on a within-paper comparison: I measure the institutional leg and import the mobility leg at an elasticity I never re-measure, so the two are nowhere commensurable. The one household-side magnitude I carry is \citepos{batzer2024} roughly \$2.4 trillion of foregone capital gains, computed on universal relocation and therefore an upper bound, and a stock of foregone gains is not a cash flow over forty-two months. The ranking's direction is what that supports; its ratio is not.
```
WHY: C-42 wants the asymmetry on the page (institutional leg measured, mobility leg imported) without
deleting a ranking that still holds on external evidence; C-43 wants the one household-side magnitude at
the ranking site with its scope. **Re-sited from the draft's mid-paragraph anchor to the paragraph's end**
so it no longer forward-references `$+\$61.2$ billion`, and the quotation is dropped entirely — the
paragraph's own anchor-determined / incidence-determined conditioning now precedes it.
FIX_FOLDED: refuted #7 ("nowhere expressed in one unit" → **"nowhere commensurable"** — both legs are
dollars, the defect is commensurability); refuted #8 (universal-relocation basis restored: "computed on
universal relocation and therefore an upper bound", faithful to §II line 100's "had they chosen to
relocate"); convention #6 (forward reference eliminated by relocation, and the `$+\$61.2$ billion`
re-quotation removed rather than moved).
LITERALS: `\$2.4 trillion` and `batzer2024` — both from the manuscript's own §II line 100
(`\citet{batzer2024} estimated that U.S. households would have faced roughly \$2.4 trillion in foregone
capital gains had they chosen to relocate`); no artifact read. `forty-two` matches `fn:manifest`'s 42
active QT months. **No new numeric literal.**
PINS: OLD contains **no** gate/test constant (AST-checked against all 2,375 ≥8-char string constants in
`tools/liveness_gates.py`, `tools/render_gate.py` and all 30 `tests/*.py`). Gate #71
`intro_para_carries_forcedness_and_flip` is paragraph-scoped on line 52 and re-verified True after apply:
line 52 is still the first line containing `$+\$61.2$ billion`, still carries `forced rather than found`
at index > 0, and still carries `$-\$99.9$ billion`.

---

## Edit 2 — scope the forced Danish sign to this episode's rate-gap inequality (C-36)
LINE: 618 (§VI.D, after the wiring-check sentence)
OLD_COUNT_ASSERT: 1
OLD:
```
I retain both as wiring checks and read neither as evidence.
```
NEW:
```
I retain both as wiring checks and read neither as evidence. That premise is an inequality about this episode, not a property of the design. It holds because the simulated book is closed at 2017--2021 originations and the window's market rate stood above essentially all of its coupons in essentially every month; where a book's rate gap is mixed in sign---another cycle, a portfolio open to new originations at the prevailing rate---the inequality fails and the sign becomes a composition question this design does not answer, since the elasticity is imported rather than estimated. Neither this sign nor the marginal transports without re-checking that inequality.
```
WHY: C-36's scope condition on the sign-invariance claim, stated where the forcedness derivation sits.
The hedge register ("essentially all … essentially every") is copied from the same paragraph's own
`negative gap in essentially every cell over essentially the whole window`, which is what keeps it true
of the 0.47% of exposure above the window minimum.
FIX_FOLDED: convention #4 (cohesion — **relocated** from between the forced-positivity conclusion and
the "on top of that" sentence to after `read neither as evidence.`, the verifier's own suggested landing;
the "Sweeping … on top of that" chain is now intact and the block runs into `What is not forced is the
magnitude`); convention #9 ("Neither this sign nor the marginal's transports … it" → **"nor the marginal
transports without re-checking that inequality"**, non-elliptical, unambiguous referent); convention #11
("the book" → **"the simulated book"**, so it cannot be read as the SOMA book, of which 2017–2021 is
false — 2022 + pre-2017 are 23.1% + 10.6% of book face, .tex:269). Also tightened 101 → 94 added words
by folding the "Where a book's rate gap…" sentence onto the preceding one with a semicolon.
LITERALS: none. `2017--2021` is the sample's standing label (18 prior occurrences).
PINS: OLD contains no gate constant. The insertion is between two complete sentences; line 618's seven
pinned spans (`could not have come out otherwise`, `What is not forced is the magnitude`,
`\% of exposure below the window-minimum`, `44\% larger`, `danish\_offwindow\_floor`,
`forced by construction`, `in-sample calibration point`) all re-measured unchanged, and no line is split
or joined (1,460 → 1,460 lines), so gate #71's paragraph scope on this line is preserved.

---

## Edit 3 — scope the no-outcome-holdout disclosure without weakening it (C-44)
LINE: 92 (`\paragraph{Definitions used throughout.}`)
OLD_COUNT_ASSERT: 1
OLD:
```
One global property of the design should be stated here as well as in the limitations, because every number below inherits it: \emph{no outcome-holdout months exist anywhere in this paper}, without exception.
```
NEW:
```
One global property of the design should be stated here as well as in the limitations, because every number below inherits it: \emph{no outcome-holdout months exist anywhere in this paper}, without exception. Its unavoidability is scoped to the cash-flow margin. The identified object has nothing to hold out: the marginal is a difference between two simulations, so no realized outcome corresponds to it. A holdout on the level's fit is conceivable but not attempted, since it would mean splitting the benchmark itself---a single cumulative path against one cap schedule. The household margin does admit outcome moments this design does not use, since it imports the mobility elasticity rather than estimating it (Section~\ref{sec:limitations}).
```
WHY: The disclosure is carried into the claim, not deleted — the italic sentence stands verbatim and
gains why one half is impossible, why the other is merely not attempted, and the household-margin
exception. I keep "conceivable but not attempted" rather than calling the level-fit holdout infeasible,
because splitting the benchmark is a choice, not a barrier.
FIX_FOLDED: refuted #6 ("That statement is scoped to the cash-flow margin" mis-locates it — the
statement is true everywhere; **"Its unavoidability is scoped to the cash-flow margin"**);
convention #8 (unparseable "one cap schedule that the benchmark is" → **"splitting the benchmark
itself---a single cumulative path against one cap schedule"**); convention #7 (the
"nineteen-month construction below can falsify the floor's temporal stability and nothing else" clause is
**deleted** — redundant with Edit 4 three sentences later, and ambiguous against the existing
"Path~A trains on nineteen of the forty-two QT months"). 105 → 80 added words.
LITERALS: none.
PINS: `outcome-holdout` appears in **no** gate or test source (grepped `tools/liveness_gates.py` and
`tests/`: 0 hits) — the draft over-claimed a pin here. The `\emph{...}` delimiters and the italic
sentence are byte-identical regardless. `above the clean band` (5) and `in-sample calibration point` (41)
elsewhere on line 92 are not crossed; both re-measured unchanged.

---

## Edit 4 — say what the nineteen-month construction holds out (C-44)
LINE: 92
OLD_COUNT_ASSERT: 1
OLD:
```
the nineteen-month floor variant reported later is an input-stability check rather than an outcome holdout.
```
NEW:
```
the nineteen-month floor variant reported later is an input-stability check rather than an outcome holdout: what it holds out is calibration months, not the benchmark.
```
WHY: C-44 requires the existing temporal holdout named where the no-holdout criticism lands, stating
precisely what it holds out. Ten words.
FIX_FOLDED: none — unchanged from draft (the verifier endorsed keeping this and dropping Edit 3's
duplicate clause instead).
LITERALS: none.
PINS: `the nineteen-month floor variant reported later is an input-stability check rather than an outcome
holdout` **is** a pinned constant (AST-confirmed present in the extracted set; gate literal
`holdout_relabelled_body` under RELOCATED_TO_BODY, and the mutation target of
`tests/test_abstract_hedge_gate.py`). NEW reproduces it byte-identically as a prefix — only the terminal
`.` becomes `:`, **after** the pinned substring ends. Re-measured: 1 → 1. `input-stability check`
(also pinned) 1 → 1. `nineteen-month` 1 → 1.

---

## Edit 5 — name the fiscal incidence and the missing ex-ante coupon premium (C-45, C-46)
LINE: 649 (§VI.D implications paragraph, paragraph-final)
OLD_COUNT_ASSERT: 1
OLD:
```
Both legs credit retired balance at par; under cash accounting the market-value buyback credit reverses the gap's sign, so the case as stated here stands on the benchmark's own face denomination, with the incidence bracket priced in Section~\ref{sec:pathb}.
```
NEW:
```
Both legs credit retired balance at par; under cash accounting the market-value buyback credit reverses the gap's sign, so the case as stated here stands on the benchmark's own face denomination, with the incidence bracket priced in Section~\ref{sec:pathb}. The $1-P$ wedge the U.S. rule collects from a moving household accrues to the bondholder, and here the bondholder is the SOMA portfolio, whose earnings reach the Treasury as remittances: the cash-haircut reading hands that wedge to the households who move and takes it from general taxpayers. So the reversal prices a transfer changing direction, not a resource cost, and its welfare sign turns on the marginal value of public funds against that of household liquidity---neither of which this framework measures. One further omission is a price rather than a held-fixed feature of the U.S. leg, and its direction runs against the reported relief. Every figure here is ex-post, on a coupon stack originated under the U.S. payoff rule; under a market-value payoff rule the repurchase option is written into the bond series and priced into the coupon ex ante, so the same households would have borrowed at a higher rate for the life of the loan \citep{campbell2013,berg2018}. That premium is netted nowhere, and the only ex-ante rate term the transplant carries---Berger et al.'s roughly one-basis-point equilibrium shift---prices the refinance-in-place channel alone. So $+\$61.2$ billion is gross institutional relief under face accounting, not a net social gain.
```
WHY: **Merges draft Edits 7 and 9.** §V.B already has the wedge economics; what is missing everywhere is
the *bondholder's identity* (the SOMA portfolio, remitting to Treasury) and the welfare-sign statement —
that is C-45. C-46's ex-ante coupon premium is a *price*, not a held-fixed feature, so it is stated
beside the omission list rather than inside its "held-fixed feature" summary, which it would falsify.
Both belong in the paragraph that says what the counterfactual revises.
FIX_FOLDED: refuted #5 (the signed-relief sentence was planted on line 618, which contains zero
occurrences of `incidence`, `face` or `cash`; **re-sited to line 649**, which contains
`face denomination`, `cash accounting` and `incidence bracket` — this resolves the finding more
directly than the verifier's own patch, and the sentence now reads "gross institutional relief **under
face accounting**, not a net social gain", so the relief is stated basis-conditionally as
`buyback_credit_bracket_results.json .verdict.manuscript_action` requires); convention #5 (cohesion —
the block no longer separates line 618's omission summary from its `I therefore report … as a band`
sentence; that "therefore" chain is untouched).
LITERALS: none new. `$+\$61.2$ billion` already occurs 17×. "roughly one-basis-point" restates the same
subsection's existing "shifts the equilibrium mortgage rate by only about one basis point". `campbell2013`
(`references.bib:605`) and `berg2018` (`references.bib:50`) are both already cited — no `.bib` change.
The $1-P$/face/cash quantities (`gap_face_b = 61.18834`, `gap_cash_range_b = [-117.660, -89.421]`,
`code = "REVERSES"`, `buyback_credit_bracket_results.json`) are printed at §V.B and **not re-quoted here**.
PINS: OLD contains no gate constant. The BUYBACK_BRACKET_SPANS pins live at §V.B and §VIII
(`a household-to-bondholder transfer, not an added resource cost`,
`the balance-adjustment reading is the benchmark-consistent one`,
`the par windfall it would otherwise have extracted from moving households`,
`The gap's sign is therefore incidence-conditional`) — all re-measured unchanged. NEW's `not a resource
cost` is a distinct string from the pinned `not an added resource cost` (which stays at 1) and is on no
ZERO_COUNT list. `par windfall` 2 → 2.

---

## Edit 6 — carry the incidence and the ex-post basis into tab:danish's **item d** (C-45, C-46)
LINE: 647 (post-float `Notes to Table~\ref{tab:danish}`, item d)
OLD_COUNT_ASSERT: 1
OLD:
```
which under this anchor is forced by construction rather than found: see Section~\ref{sec:abm-danish}.\par}
```
NEW:
```
which under this anchor is forced by construction rather than found: see Section~\ref{sec:abm-danish}. This row is face-denominated and ex-post on the U.S. coupon stack: under the cash-haircut reading its gap reverses sign, and the wedge that reverses it is a transfer from the SOMA portfolio to moving households rather than a resource cost (Section~\ref{sec:pathb}); and no ex-ante repricing of the repurchase option into the coupon is netted from either leg, an omission signed against the reported relief (see text).\par}
```
WHY: **Merges draft Edits 8 and 10** onto the single row the claims are true of — item d, the production
rule-only pair, which is the row `$+\$61.2$ billion` comes from. The table reads standalone, so it needs
both the sign-reversal incidence and the ex-post basis; it points at the body rather than restating it.
FIX_FOLDED: refuted #1 **(hard refutation, fully accepted)** — the draft put "the gap reverses sign"
in tab:danish's *table-wide unlettered preamble*, where it is false for rows b and c (Gap = $-\$728.4$B
and $-\$99.9$B; `gap_cash(D) = gap_par − D·E` is subtractive, so it cannot reverse an already-negative
gap) and unpriced for row a (+\$925.5B). `buyback_credit_bracket_results.json .spec` is "incidence
bracket on the production rule-only pair", i.e. **row d only**. The claim is now scoped to that row and
the false table-wide sentence is gone; convention #3 (preamble/lettered-item split — the preamble is
left carrying only the sign convention and the Gap definition).
LITERALS: none.
PINS: `forced by construction` is inside OLD and preserved byte-identically (file count 2 → 2). The
post-float `\par}` terminator is preserved and **nothing moves into the float** (Round-31 convention).
Item b/c pins (`in-sample calibration point`) are further along the same paragraph and not crossed.

---

## Edit 7 — recast the path-level timing question as possibly ill-posed (C-62)
LINE: 663 (§VII.B, settlement-alignment variant)
OLD_COUNT_ASSERT: 1
OLD:
```
The decomposition is unchanged in substance, and the null still recovers the large majority of the benchmark under either convention.
```
NEW:
```
The decomposition is unchanged in substance, and the null still recovers the large majority of the benchmark under either convention. The variant also bears on the path-level timing question every estimator here leaves open. If the monthly series each estimator's path is scored against is a cash-arrival object---reported roll-off smeared over the months in which a month's prepayment decisions arrive as cash and, in its CPR form, clipped by a back-out whose non-negativity rule pins four months to exactly zero and posts the displaced mass into the following month's reading (Section~\ref{sec:method-benchmark})---then a monthly path is not a behavioral object, and the timing question may be ill-posed rather than a failure every estimator shares. I state that as a candidate account, not a finding: reporting mechanics and behavior arrive in the same series, and nothing here separates them.
```
WHY: §VII.B is where the reporting-and-arrival account is already *measured* (settlement-aligned
\$722.7B, the $-5.5$\% re-basing, the smearing kernel), so the ill-posedness reading is stated where its
evidence sits. Framed as a candidate per C-62's own wording. It does **not** touch the frozen
monthly-timing rule's status, and it does not restate or weaken
`the path-level timing question remains open for every estimator` (2 sites, §VIII).
FIX_FOLDED: refuted #2 ("smeared by an agency remittance lag" is denied by the same line —
"Agency remittance is itself a deterministic lag of roughly one month, so that profile is **not** a
description of the remittance cycle"; now **"smeared over the months in which a month's prepayment
decisions arrive as cash"**, the manuscript's own formulation); convention #10 ("the one question every
estimator here leaves open" asserted uniqueness → **"the path-level timing question every estimator here
leaves open"**).
LITERALS: none. "four months … exactly zero … posts the displaced mass into the following month's
reading" is §III.B line 137 verbatim in substance (traced there to run
`h1\_zero\_months\_diagnosis`); I use the manuscript's "following" not the draft's "next". The
`Appendix~\ref{sec:robustness-seasonalfloor}` pointer was dropped for concision — line 137 already
carries it.
PINS: OLD contains three constants — `large majority`, `decomposition`, `recovers ` — all reproduced
byte-identically as NEW's prefix. Line 663's other pins (`\$42.6 billion on either denominator`,
`settlement\_months\_benchmark`, `the QT window is half-open`) sit earlier in the same paragraph and are
not crossed; all re-measured unchanged.

---

## CENSUS

Fixed-string `str.count` on the current file (A) and on the in-memory result after applying E1–E7 in
order (B). Every OLD asserted `== 1` immediately before its own replace. **1,460 → 1,460 lines** — no
paragraph split or join, so every paragraph-scoped gate keeps its line.

### Gate/test-pinned spans: AST-extracted **all 2,375** string constants ≥8 chars from `tools/liveness_gates.py`, `tools/render_gate.py` and all 30 `tests/*.py`; counted each in A and B
**Exactly 6 changed, all increases of generic substrings, zero drops:**

| constant | A | B |
|---|---|---|
| ` billion` | 375 | 376 |
| `$ billion` | 145 | 146 |
| `$+\$61.2$ billion` | 17 | 18 |
| `against ` | 233 | 238 |
| `comparison` | 26 | 27 |
| `external` | 36 | 37 |

None is a uniqueness pin. The only hard `count(...) == 1` asserts are
`tests/test_floor_ladder_gate.py:52,66` (ladder rows / printed values) and
`tests/test_assembled_corrections_gate.py:91` (ASSEMBLY table spans) — had any of those spans moved it
would appear in the table above; none did. `$+\$61.2$ billion` is not count-asserted (17 before).

### Named pins re-measured
`the nineteen-month floor variant reported later is an input-stability check rather than an outcome holdout` 1 → 1 ·
`input-stability check` 1 → 1 · `forced by construction` 2 → 2 · `forced rather than found` 1 → 1 ·
`could not have come out otherwise` 1 → 1 · `What is not forced is the magnitude` 1 → 1 ·
`44\% larger` 3 → 3 · `$-\$99.9$ billion` 7 → 7 · `outcome holdout` 2 → 2 ·
`in-sample calibration point` 41 → 41 · `above the clean band` 5 → 5 · `positive at every` 6 → 6 ·
`A seventh qualification` 1 → 1 (gate #98) · `This section is a stress test` 1 → 1 (gate #100) ·
`A green gate suite is therefore not self-certifying` 1 → 1 (gate #104, untouched) ·
`par windfall` 2 → 2 · `Table~\ref{tab:danish}` 9 → 9

### Literals and keys whose count moves
| string | A | B | source |
|---|---|---|---|
| `\$2.4 trillion` | 1 | 2 | .tex §II line 100 |
| `batzer2024` | 1 | 2 | `references.bib`, already cited |
| `campbell2013` | 1 | 2 | `references.bib:605`, already cited |
| `berg2018` | 2 | 3 | `references.bib:50`, already cited |
| `$+\$61.2$ billion` | 17 | 18 | committed Danish rule-only gap |
| `2017--2021` | 18 | 19 | sample's standing label |
| `forty-two` | 1 | 2 | `fn:manifest` 42 active QT months |
| `four months` | 3 | 4 | `h1_zero_months_diagnosis` (via .tex:137) |
| `basis-point` | 2 | 3 | Berger GE shift, same subsection |
| `1-P` | 3 | 4 | §V.B |
| `\citepos` | 18 | 19 | macro, line 22 |
| `holdout` | 33 | 34 | — |
| `SOMA portfolio` | 2 | 4 | — |
| `remittance` | 3 | 4 | — |
| `ex ante` | 22 | 23 | — |
| `commensurab` | 1 | 2 | distinct claim from line 723's |

### New strings (previously absent)
`taxpayer` 0 → 1 · `ill-posed` 0 → 1 · `not a resource cost` 0 → 1 · `ex-post` 0 → 2 ·
`universal relocation` 0 → 1. **`ex-post`**: hyphenated to match house style (`ex-ante` 35 vs
`ex ante` 22); verifier's convention #12 was a flag for confirmation only — confirmed.

### Deliberately NOT moved
`49\%` 12 → 12 · `23\%` 2 → 2 · `\$87.8` 6 → 6 · `$+\$42.6$ billion` 10 → 10 · `99.53` 2 → 2 ·
`\$687.8 billion` 1 → 1 · `$-\$89.4$ to $-\$117.7$ billion` 4 → 4 · `nineteen-month` 1 → 1 ·
`ex post` (unhyphenated) 0 → 0 · `Treasury remittances` 0 → 0 (the draft's census row was wrong — my
text reads "reach the Treasury as remittances")

### Global invariants after apply
- Line 31 **byte-identical**; abstract **323 words**; gate #101's tie to the response letter undisturbed.
  **Abstract word delta: 0. Body word delta: +648** (E1 +84 · E2 +94 · E3 +80 · E4 +10 · E5 +197 ·
  E6 +66 · E7 +117). Draft was +834; the merges and trims took out 186.
- Gate #71 `intro_para_carries_forcedness_and_flip` re-evaluated on B: **True** (line 52 still first,
  `forced rather than found` at index > 0, `$-\$99.9$ billion` present).
- HARDCODED_XREF: the five forbidden patterns (`Table \d`, `Figure \d`, `Section [IVX]+`,
  `Appendix [AB]`, `Equation (\d`) match nothing in any NEW string; every cross-reference goes through
  `\ref`. All five labels used (`sec:pathb`, `sec:limitations`, `sec:abm-danish`,
  `sec:method-benchmark`) exist exactly once.
- **Mirror**: all 7 OLDs count exactly 1 in `revised_paper_v18_long_abstract.tex` too; same +648 words,
  1,460 → 1,460 lines, line 31 untouched there as well.

---

## DROPPED

1. **Draft Edit 3 — Appendix O gate-suite domain (C-37). MOOT/LANDED.** The brief says C-37 landed, and
   the current line 1426 already carries a richer version immediately after the draft's own OLD:
   "Its domain is narrower still … The suite checks three things … **It checks no premise.** … Nor did it
   see the page: a suite of 108 green gates once coexisted with roughly 919 text items set off the
   physical sheet across nine pages …". Everything my draft proposed is there and better sourced. Zero
   words.

2. **Draft Edit 1 — expectations denominator in tab:headline's marginal row (C-31). DROPPED as
   REDUNDANT + collateral.** Four independent reasons, in order of weight:
   - **tab:headline already carries the expectations denominator as its own row**, two rows above the
     marginal row: line 77 reads `Expectations-based complement (Section~\ref{sec:method-benchmark}) &
     \$87.8 billion, 11.5\% of the cap-relative benchmark & Fed's ex-ante projection implied
     75.6--88.5\% of the cap-shortfall, by intra-2022 allocation`. C-31's "quote the expectations
     denominator beside the cap-relative one" is satisfied *within the table* already.
   - **The ratio and its governing hedge are at §III.B line 150** verbatim: "the identified lock-in
     marginal amounts to 49\% of the expectations-based shortfall under the central uniform-spread
     construction at the headline off-window floor ($+\$42.6$ billion), or 80\% at the in-sample
     calibration point", then "each ratio is to be read as an allocation-conditional upper bound on
     lock-in's share of a mixed lock-in-and-rate-path surprise, not as a partition of that surprise".
   - **That governing sentence enumerates its quoting sites** — "they govern every site at which these
     ratios appear --- the introduction, this section, and the conclusion ---". Adding a **fourth**
     quoting site in Table 1 makes the enumeration incomplete, and repairing it means editing line 150,
     which C-formfork edits twice and D-mechanical four times. The verifier explicitly credited G's
     abstention from line 150 for avoiding a three-way collision; I keep it.
   - The verifier's own three findings on this edit (refuted #3: 23\% is 42.608/186.778, a *different*
     denominator, so "\$87.8 billion … and 23\% under the settlement-aware one" is false arithmetic on
     the printed denominator; convention #1: the cell already reads "basis-invariant" and the brief
     forbids attaching a basis label to a marginal; convention #2: the hedge object was truncated) plus
     collision #1 (A-posture loads the *same* ~80-word cell, +55 words) mean any surviving version costs
     ~45 words in an already-overloaded cell for content the table and §III.B both carry.

   **Ready-to-apply text if the coordinator overrules me** (fixes all three findings; OLD counts 1 as of
   this measurement, but A-posture's Edit 3 loads the same cell — verify order first):
   OLD `the range carries the identified content (Section~\ref{sec:identification}) & floor-read`
   → NEW `the range carries the identified content (Section~\ref{sec:identification}); on the expectations-based denominator of row 3 rather than the cap, $+\$42.6$ billion is 49\% of that \$87.8 billion shortfall, to be read as an allocation-conditional upper bound on lock-in's share of a mixed lock-in-and-rate-path surprise, falling as the anticipated share falls (Section~\ref{sec:method-benchmark}) & floor-read`
   — and then line 150's site enumeration needs `Table~\ref{tab:headline}` added.

3. **Draft Edits 8 and 10 merged into one (Edit 6)**, and **draft Edits 7 and 9 merged into one
   (Edit 5)**. Both merges were forced by verifier findings (refuted #1 re-sites Edit 8 onto item d
   where Edit 10 already lands; refuted #5 + convention #5 re-site Edit 9 onto line 649 where Edit 7
   already lands) and both are net concision wins.

4. **Nothing else was drafted for the out-of-region limbs** (C-31 abstract, C-36 §V.E line ~334 and
   §VIII, C-42/C-43 §VI.A and §VIII, C-44 §VIII.A, C-45 §VIII, C-62 §VIII.A). Unchanged from the draft's
   OUT-OF-REGION LIMBS list, except that the draft's line numbers for them are all stale — §V.E's old
   line 323 is now six paragraphs.

---

## COLLISIONS

1. **`line 79` / tab:headline — RESOLVED by my drop.** A-posture's Edit 3 loads the same cell and shares
   the 52-byte substring `an anchor convention rather than a central tendency;`. Dropping my Edit 1
   removes the overlap entirely: **G no longer touches line 79.** A-posture applies unconditionally.
2. **`line 92` — three drafters, four spans, warning only.** My Edits 3 and 4, A-posture's Edit 5
   (`returns $+5.6$ points and is the headline)`), D-mechanical's Edit 1. I re-verified all four OLDs are
   pairwise-disjoint substrings of the same paragraph and none contains another; **any order applies.**
   Note that my Edit 3 shortened (the deleted "nineteen-month construction below" clause), which removes
   the ambiguity D-mechanical's definitions edit would otherwise sit next to.
3. **`line 618` — two of my own edits.** Edit 2 inserts at byte ~4,041 of the line; nothing else of mine
   is on 618 any more (draft Edit 9 moved to 649). No sibling draft touches 618 per my diff of
   `DRAFT_w2_D-mechanical.md`, `DRAFT_w2_E-composition.md`, `DRAFT_task3.md`. **Warning for the
   coordinator:** 618 is one ~1,000-word paragraph carrying gate #71's co-occurrences; any sibling edit
   that *splits* it breaks that gate.
4. **`line 647` and `line 649` — G only.** No sibling span.
5. **`line 663` — G only.** No sibling span.
6. **`line 150` (§III.B) — G declines, as before.** C-formfork edits it twice, D-mechanical four times.
   My dropped Edit 1's optional repair would add a seventh; do not apply it without re-anchoring against
   those two.
7. **Line 52 — G only** (my Edit 1 is paragraph-final; no sibling draft anchors there).

---

## OPEN

1. **C-31 is now undischarged at the table site, by my judgment, not by omission.** Coordinator's call.
   The full replacement text and the line-150 enumeration repair it would require are in DROPPED #2. My
   read: the condition is already satisfied by tab:headline's own row 3 (line 77) plus §III.B line 150,
   and paying ~45 words plus a seven-way line-150 collision to restate it is the wrong trade this round.
2. **PDF-side effects — unverified, needs the coordinator.** +648 words across five sites, two of them
   float-adjacent (tab:danish's post-float note at 647, and 649 immediately after it). I cannot build or
   run `tools/render_gate.py`. Given Appendix O's own disclosure that 108 green gates coexisted with
   ~919 off-sheet items, one `tectonic` build plus the render gate is the only check that matters here.
   Edit 6 lengthens a post-float note by 66 words — the exact defect class Round 31 moved notes out of
   floats to avoid, though out-of-float notes reflow rather than overflow.
3. **Edit 5 is 197 words in one paragraph-final block.** It discharges C-45 and C-46 together at the
   right site, but if the round wants a harder concision cut, the two sentences most droppable are
   "So the reversal prices a transfer changing direction … neither of which this framework measures"
   (−48; but that is C-45's welfare-sign requirement) and the `\citep{campbell2013,berg2018}` clause's
   second half (−20). I did not cut either because both are the substance of their conditions.
4. **The ~39× Batzer/Danish ratio (2400/61.2) is still declined.** Edit 1 says "The ranking's direction
   is what that supports; its ratio is not." A stock of foregone gains against a 42-month flow does not
   license a ratio. If Eugene wants "~40×" on the page, Edit 1's last sentence is where it goes — one
   sentence, and it needs his sign-off, not mine.
5. **R2:M8 (benchmark monthly frequency) remains UNARBITRATED** and Edit 7 does not touch it: the edit
   states the ill-posedness as a *candidate account* and leaves the frozen monthly-timing rule's status
   (Appendix N) alone.
6. **`ex-post` enters the manuscript for the first time** (2 occurrences, both mine). Hyphenated to match
   `ex-ante` (35) over `ex ante` (22). Trivially reversible if Eugene prefers the open form.
