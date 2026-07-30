# DRAFT — Round 32 Wave 2, cluster D: "mechanical" (C-29, C-30, C-66)

READ-ONLY draft. Nothing in the worktree was modified. Every OLD span below was
measured with `str.count` against
`paper/v18/revised_paper_v18.tex` as it stands at the head of this worktree, and
every count in the CENSUS was measured on the in-memory result of applying all 33
edits in the order printed (script: `verify_w2_D.py`, result:
`result_w2_D.tex`, both in this scratchpad directory — outside the worktree).

---

## 0. CLASSIFICATION OF ALL 43 USES OF "mechanical"

`[Mm]echanical` (i.e. including the 5 adverbial `mechanically`) occurs **43 times**.
Verdicts: **PARTITION** = the word is carrying the paper's mechanical/elastic
partition and therefore asserting non-behavioral content; **ORDINARY** = ordinary
English ("automatic", "arithmetic", "by construction") about something that is not
the partition. 30 PARTITION / 13 ORDINARY.

| # | line | phrase | verdict |
|---|------|--------|---------|
| 1 | 44 | an elastic channel and a **mechanical** baseline | PARTITION |
| 2 | 44 | Most of the shortfall is **mechanical**. | PARTITION |
| 3 | 44 | overlap with the **mechanical** null's recovery | PARTITION |
| 4 | 58 | the hazard framework's margin over a **mechanical** model | PARTITION |
| 5 | 60 | decomposition ... into **mechanical** and elastic components | PARTITION |
| 6 | 60 | both components of the **mechanical** path | PARTITION |
| 7 | 78 | **Mechanical** null, $\beta_1 = 0$ (T1 row label) | PARTITION |
| 8 | 92 | its $\beta_1 = 0$ **mechanical** null (Definitions) | PARTITION |
| 9 | 94 | every non-**mechanical** adjudication | ORDINARY |
| 10 | 98 | this paper's **mechanical** null operationalizes | PARTITION |
| 11 | 110 | the shortfall accrues **mechanically** | PARTITION |
| 12 | 110 | the lock-in-versus-**mechanical** question | PARTITION |
| 13 | 150 | an anticipated **mechanical** component | PARTITION |
| 14 | 150 | the $\beta_1 = 0$ **mechanical** null recovers | PARTITION |
| 15 | 150 | the anticipated **mechanical** component in the large majority | PARTITION |
| 16 | 150 | the **mechanical**-majority threshold | PARTITION |
| 17 | 160 | **mechanically** inflates rate sensitivity | ORDINARY |
| 18 | 182 | a **mechanical** recalibration artifact | ORDINARY |
| 19 | 227 | the **mechanical** model recovers 97.8\% | PARTITION |
| 20 | 277 | discriminate the elasticity from the **mechanical** model | PARTITION |
| 21 | 315 | near-**mechanical** strength | ORDINARY |
| 22 | 319 | the **mechanical** model with the lock-in elasticity switched off | PARTITION |
| 23 | 323 | discriminate the elasticity from the **mechanical** model | PARTITION |
| 24 | 534 | what the level supports is the **mechanical** decomposition | PARTITION |
| 25 | 544 | mostly **mechanical**: a gap to a cap schedule | PARTITION |
| 26 | 548 | mostly **mechanical** by the decomposition above | PARTITION |
| 27 | 552 | the book's **mechanical** principal path | PARTITION |
| 28 | 641 | The shift is **mechanical** (half-open window arithmetic) | ORDINARY |
| 29 | 727 | a prepayment environment mostly **mechanical** relative to the caps | PARTITION |
| 30 | 731 | the shortfall against the phased caps is mostly **mechanical** | PARTITION |
| 31 | 731 | a bounded margin over that **mechanical** base | PARTITION |
| 32 | 737 | the cash-flow shortfall against the caps is mostly **mechanical** | PARTITION |
| 33 | 737 | mostly the **mechanical** arithmetic of scheduled amortization and baseline turnover | PARTITION |
| 34 | 751 | consistent with the **mechanical** decomposition above | PARTITION |
| 35 | 929 | This **mechanical** recalibration | ORDINARY |
| 36 | 1105 | not **mechanically** collinear with seasoning | ORDINARY |
| 37 | 1106 | below the **mechanical** $\beta_1 = 0$ null's 85.7\% | PARTITION |
| 38 | 1128 | narrower for the **mechanical** reason stated there | ORDINARY |
| 39 | 1144 | near-**mechanical** strength | ORDINARY |
| 40 | 1311 | raising the floor **mechanically** crowds out | ORDINARY |
| 41 | 1326 | That recalibration **mechanically** inflates | ORDINARY |
| 42 | 1346 | Both are structural or **mechanical** rather than changes in modeling philosophy | ORDINARY |
| 43 | 1401 | anything other than **mechanical** enforcement | ORDINARY |

Sites 1–8, 10–16, 19, 20, 22–27, 29–34 and 37 are edited below (30 sites).
Sites 9, 17, 18, 21, 28, 35, 36, 38–43 are left exactly as they are (13 sites).
Two words adjacent to the count are **not** in it and are **not** touched: the 13
uses of `mechanics`/`Mechanics` (sweep mechanics, censoring mechanics, the two
appendix titles — one of which, "the instability is the max form's censoring
mechanics", is gate #104's pinned row) and the 5 uses of `mechanic` (the ABM's
household mechanic).

---

## 1. RECOMMENDATION: rename AND define, in that order of dependency

The task asks for one. My answer is that C-29 and C-30 are one fix, and I draft it
as one, for three reasons that are visible in the manuscript rather than matters of
taste.

1. **Defining alone cannot work, because the definition would be false.** The
   honest content of the object is "scheduled amortization plus baseline turnover
   held at its observed level". But the floor that sets that level is read off
   realized turnover which the paper itself says is partly behavioral (.tex:92,
   .tex:110, .tex:227) — so a definition of "mechanical" that is accurate has to say
   "and this is not a non-behavioral object", i.e. it has to concede that the word
   is the wrong word. A definition whose content contradicts its headword is worse
   than either fix alone.
2. **Renaming alone cannot work, because the new name is undefined too.** "No-elasticity
   null" is honest but opaque on first encounter, and C-30's raiser is that the
   partition is nowhere stated. T1's row label is read standalone.
3. **The two sites that carry the risk are the two the pair fixes together**: the
   first use (.tex:44) and T1's row label (.tex:78). Both are read out of context,
   both are one edit away, and C-29's own fix note says landing one without the
   other leaves the overclaim.

Vocabulary chosen, and why it is not new vocabulary:
- **`$\beta_1 = 0$ null`** wherever the object is being named (34 existing uses; the
  count rises to 40). At 6 sites the adjective simply comes off a name the sentence
  already carries.
- **`no-elasticity baseline` / `no-elasticity null`** at the 4 sites that need a name
  in words rather than in symbols: first use, T1's row label, and the two
  contribution/path statements in §I. This is C-29's own first suggestion.
- **`scheduled-plus-turnover`** at the 8 predicative and decomposition sites. This is
  the manuscript's own existing compound (3 prior uses: .tex:110 "the
  scheduled-plus-turnover decomposition my $\beta_1 = 0$ null quantifies", .tex:110
  again, .tex:582 "the book's projected scheduled-plus-turnover principal path").
  Using it means the rename introduces no new term at those sites at all.

If the coordinator will only land part of this, land edits **1, 2, 3, 10 and 21**
(definitions block, first-use gloss, the naked "Most of the shortfall is
mechanical", T1's row label, the §V by-construction gloss). That subset is
self-coherent and covers every standalone-read site; the remaining 25 are the
consistency pass.

---

## 2. THE EDITS

## Edit 1 — Definitions paragraph: define the partition, drop the adjective from the object's name (C-30 (+C-29))
FILE: paper/v18/revised_paper_v18.tex  (line 92)
OLD_COUNT_ASSERT: 1
OLD:
and the \emph{lock-in marginal} is the difference between the central simulation and its $\beta_1 = 0$ mechanical null, the paper's identified object, whose operative uncertainty is the calibration-and-form envelope of Table~\ref{tab:uncertainty} rather than any sampling interval.
NEW:
and the \emph{lock-in marginal} is the difference between the central simulation and its $\beta_1 = 0$ null, the paper's identified object, whose operative uncertainty is the calibration-and-form envelope of Table~\ref{tab:uncertainty} rather than any sampling interval. The $\beta_1 = 0$ leg is the \emph{no-elasticity baseline}: it carries scheduled amortization from the book's own coupon, age, and term composition together with baseline turnover held at its observed level, and the marginal is the imported elasticity's increment above it. What the partition separates is that baseline from that increment, not mechanics from behavior---the floor is measured on realized turnover that is itself partly behavioral, so the baseline leg is not a non-behavioral object and I do not call it one.
RATIONALE: C-30's required sentence, at the definitions block: it states the null's CONTENT (scheduled amortization plus baseline turnover at its observed level) and the marginal as the elasticity's increment above it, then denies the mechanics-versus-behavior reading on the paper's own ground (the floor is read off partly behavioral turnover). Also drops "mechanical" from the object's name here, so the defined term and the name agree.
LITERALS_INTRODUCED: none (no numeric literal added or removed)
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: OLD contains no gate/test span. Nearby pinned spans in the same paragraph ("the nineteen-month floor variant reported later is an input-stability check rather than an outcome holdout", "in-sample calibration point", "above the clean band") are outside the OLD and untouched; verified present after, counts unchanged.

## Edit 2 — First use (§I): gloss the partition by content, not by construction (C-30)
FILE: paper/v18/revised_paper_v18.tex  (line 44)
OLD_COUNT_ASSERT: 1
OLD:
switching the lock-in elasticity off partitions the realized shortfall between an elastic channel and a mechanical baseline, and the elasticity's causal content
NEW:
switching the lock-in elasticity off partitions the realized shortfall between an elastic channel and a no-elasticity baseline (scheduled amortization plus baseline turnover held at its observed level; the floor that sets that level is itself read off realized, partly behavioral turnover, so the baseline is not a non-behavioral object), and the elasticity's causal content
RATIONALE: C-30's first-use gloss. The main clause already carries "elasticity switched off"; the parenthetical supplies the half that was missing (baseline turnover held at its observed level) and the explicit refusal of "non-behavioral". Named "no-elasticity baseline" so the first use and the definitions block use one term.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: OLD contains no gate/test span. The abstract-scoped pin 'scheduled amortization and baseline turnover' occurs later on the same line and is untouched (whole-file count 4 -> 4).

## Edit 3 — First use (§I): the naked partition claim (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 44)
OLD_COUNT_ASSERT: 1
OLD:
Most of the shortfall is mechanical.
NEW:
Most of the shortfall sits in that baseline.
RATIONALE: "Most of the shortfall is mechanical." is the sentence a reader meets before any definition, and it is the one that reads as "not behavior". "That baseline" picks up the immediately preceding clause's "regardless of any rate response above that baseline", so the referent is explicit and the claim's content is unchanged.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: none in OLD.

## Edit 4 — First use (§I): the null's name in the NY-Fed-overlap sentence (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 44)
OLD_COUNT_ASSERT: 1
OLD:
a range wide enough that its overlap with the mechanical null's recovery carries no precision.
NEW:
a range wide enough that its overlap with the $\beta_1 = 0$ null's recovery carries no precision.
RATIONALE: The object already has an unambiguous name in this paper ($\beta_1 = 0$ null, 34 prior uses); using it here removes the assertion without adding vocabulary.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: OLD sits after the pinned span "The New York Fed's May 2022 staff baseline already anticipated the large majority of the realized cap-shortfall", which is outside the OLD and untouched.

## Edit 5 — §I framing: two estimators read the level, one draws the partition (C-66)
FILE: paper/v18/revised_paper_v18.tex  (line 50)
OLD_COUNT_ASSERT: 1
OLD:
I reach this decomposition through two structurally distinct estimators, a 10,000-household agent-based model and a loan-level hazard framework, that disagree sharply about how much household choice explains. The decomposition the hazard framework supports is the paper's central empirical result;
NEW:
I run two structurally distinct estimators, a 10,000-household agent-based model and a loan-level hazard framework, that disagree sharply about how much household choice explains. Both read the aggregate level; only one draws the partition. The ABM has no $\beta_1 = 0$ counterpart to difference against (Section~\ref{sec:abm}), and inside the hazard framework the partition is Path~B's, Path~A being excluded from every headline range (Section~\ref{sec:patha}). The decomposition the hazard framework supports is the paper's central empirical result;
RATIONALE: C-66's scoping at the site where the decomposition is introduced. "I reach this decomposition through two ... estimators" is false as written: the ABM has no $\beta_1 = 0$ counterpart and Path A is excluded from every headline range, so the partition is Path B's alone. States both exclusions with pointers rather than re-arguing them.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: OLD contains no gate/test span. Deliberately does NOT reuse gate #94's pinned wording "admits no counterpart to the $\beta_1 = 0$ null" (§IV, whole-file count 1 -> 1); this sentence says "has no $\beta_1 = 0$ counterpart to difference against" so the pin stays unique.

## Edit 6 — §I framing: the second framing sentence (C-66)
FILE: paper/v18/revised_paper_v18.tex  (line 58)
OLD_COUNT_ASSERT: 1
OLD:
This paper quantifies the mechanics of this shortfall using two structurally distinct estimators. The first is
NEW:
This paper quantifies the mechanics of this shortfall using two structurally distinct estimators, and partitions it with one of them. The first is
RATIONALE: Same scoping at the second verbatim framing sentence. Kept "quantifies the mechanics of this shortfall" intact (ordinary-language use, not in the partition set) and added only the scoping clause.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: none in OLD.

## Edit 7 — §I: margin over the null, not over "a mechanical model" (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 58)
OLD_COUNT_ASSERT: 1
OLD:
so the hazard framework's margin over a mechanical model is $+5.6$ points
NEW:
so the hazard framework's margin over that null is $+5.6$ points
RATIONALE: The same sentence has just named the object ("the null that switches off the lock-in elasticity (the $\beta_1 = 0$ null)"), so "that null" is both shorter and exact.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: OLD contains no gate/test span; the abstract-scoped 'A cross-design variant of the ABM recalibrated on real loan covariates' and '13.6\% on the fifty-seed mean' are elsewhere on the line and untouched.

## Edit 8 — §I contribution 1: name the two components (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 60)
OLD_COUNT_ASSERT: 1
OLD:
First, a decomposition of the QT mortgage-runoff shortfall into mechanical and elastic components, with the elastic part
NEW:
First, a decomposition of the QT mortgage-runoff shortfall into a no-elasticity baseline and an elastic component, with the elastic part
RATIONALE: The contribution is the decomposition itself, so this is the site where the partition's name does the most work. "a no-elasticity baseline and an elastic component" states the construction without asserting non-behavioral content.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: none in OLD.

## Edit 9 — §I contribution 3: the cap-design path (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 60)
OLD_COUNT_ASSERT: 1
OLD:
and both components of the mechanical path a binding cap would have to sit below
NEW:
and both components of the no-elasticity path a binding cap would have to sit below
RATIONALE: The sentence itself lists the two components immediately after, so the adjective was carrying an unearned claim rather than information.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: none in OLD (the em-dash list that follows, incl. 'scheduled amortization from the book's coupon, age, and term composition', is outside).

## Edit 10 — T1 row label (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 78)
OLD_COUNT_ASSERT: 1
OLD:
Mechanical null, $\beta_1 = 0$ (Section~\ref{sec:identification}; Table~\ref{tab:bases})
NEW:
No-elasticity null, $\beta_1 = 0$ (Section~\ref{sec:identification}; Table~\ref{tab:bases})
RATIONALE: C-29 says start here: T1 is read standalone, so its row label asserts the partition with no definition anywhere near it. "No-elasticity null, $\beta_1 = 0$" names the same object by its construction.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: OLD contains no gate/test span; the pinned '\% of benchmark' is in the value column, outside the OLD (whole-file count 13 -> 13).

## Edit 11 — §III.A heading (C-66)
FILE: paper/v18/revised_paper_v18.tex  (line 120)
OLD_COUNT_ASSERT: 1
OLD:
\subsection{Two Structurally Distinct Estimators}\label{sec:method-estimators}
NEW:
\subsection{Two Structurally Distinct Estimators, One Decomposition}\label{sec:method-estimators}
RATIONALE: Scopes the framing at the heading a reader meets before the two estimators are described. Checked for pins first: no literal in tools/liveness_gates.py or tests/*.py contains "Structurally Distinct", "structurally distinct" or "sec:method-estimators", and the .tex contains no \nameref.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: none. \label{sec:method-estimators} is preserved byte-identically; §IV's separate heading "A Structurally Distinct Estimator" (.tex:180) is untouched.

## Edit 12 — §II: the Chernov split (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 98)
OLD_COUNT_ASSERT: 1
OLD:
the same turnover-versus-rate-response split this paper's mechanical null operationalizes on the cash-flow side.
NEW:
the same turnover-versus-rate-response split this paper's $\beta_1 = 0$ null operationalizes on the cash-flow side.
RATIONALE: Name the object rather than assert its content, in a sentence whose whole point is that the split is turnover-versus-rate-response.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: none in OLD.

## Edit 13 — §II: how the shortfall accrues (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 110)
OLD_COUNT_ASSERT: 1
OLD:
is the state in which the shortfall accrues mechanically, so their composition and my null recovery
NEW:
is the state in which the shortfall accrues regardless of any rate response above that baseline, so their composition and my null recovery
RATIONALE: "accrues mechanically" is the adverbial form of the same overclaim. The replacement is the paper's own idiom for the true content ("regardless of any rate response above that baseline", cf. .tex:44) and states the condition rather than the character.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: OLD contains no gate/test span; the pinned 'scheduled amortization and baseline turnover' and '$+2.9$ and $+8.7$' occur elsewhere on the line and are untouched.

## Edit 14 — §II: the question Eyal et al. do not speak to (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 110)
OLD_COUNT_ASSERT: 1
OLD:
so it does not speak to the lock-in-versus-mechanical question I take up here.
NEW:
so it does not speak to the lock-in-versus-baseline-turnover question I take up here.
RATIONALE: Names the contrast by its content. "lock-in-versus-baseline-turnover" is the paper's own vocabulary after the R29 rename.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: none in OLD.

## Edit 15 — §III.B: the cap-relative tension (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 150)
OLD_COUNT_ASSERT: 1
OLD:
so a shortfall measured against them mixes an anticipated mechanical component with genuine surprise.
NEW:
so a shortfall measured against them mixes an anticipated component with genuine surprise.
RATIONALE: "anticipated" already carries the whole claim in this sentence — the component is anticipated, which is what makes it not surprise. Dropping the adjective removes an assertion and loses nothing.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: OLD retains the pinned 'genuine surprise' byte-identically (whole-file count 4 -> 4).

## Edit 16 — §III.B: the withdrawn near-equality (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 150)
OLD_COUNT_ASSERT: 1
OLD:
the 88.5\% sits 0.2 points from the 88.7\% the $\beta_1 = 0$ mechanical null recovers on the benchmark-consistent basis
NEW:
the 88.5\% sits 0.2 points from the 88.7\% the $\beta_1 = 0$ null recovers on the benchmark-consistent basis
RATIONALE: Object name only; the retraction's arithmetic is untouched.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: OLD contains the literals 88.5\% / 0.2 / 88.7\% and preserves all three byte-identically; the pinned 'they require the uniform-spread allocation, because the settlement-aware allocation puts the anticipated share at 75.6\%' is later on the line and untouched.

## Edit 17 — §III.B: the agreement that survives (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 150)
OLD_COUNT_ASSERT: 1
OLD:
both objects put the anticipated mechanical component in the large majority of the shortfall.
NEW:
both objects put the anticipated component in the large majority of the shortfall.
RATIONALE: Same as edit 15: "anticipated" is the operative word; the adjective added an assertion the sentence does not support.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: OLD retains the pinned 'large majority' byte-identically (whole-file count 6 -> 6).

## Edit 18 — §III.B: the surviving threshold's name (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 150)
OLD_COUNT_ASSERT: 1
OLD:
the mechanical-majority threshold survives at every allocation.
NEW:
the large-majority threshold survives at every allocation.
RATIONALE: Renames the threshold to the paper's own phrase for what it measures — .tex:150 already says "leaving the large-majority reading ... unchanged" three sentences earlier. NOTE for the coordinator: the artifact key stays `mechanical_majority_survives` in expectation_benchmark_results.json and gate #? reads that JSON key, not the .tex, so this rename cannot break it; the naming divergence between artifact and manuscript is deliberate and worth a line in the run ledger if you want it traceable.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: OLD contains no gate/test span. Verified: the only occurrence of 'mechanical_majority' anywhere in tools/ is the JSON key read at tools/liveness_gates.py:1250 and printed at :1259; no .tex span pin exists.

## Edit 19 — §V.B (Path B specification): the no-lock-in null's recovery (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 227)
OLD_COUNT_ASSERT: 1
OLD:
consistent with the no-lock-in null of Section~\ref{sec:hazard-interp}, which shows the mechanical model recovers 97.8\% of the benchmark under the standalone scorer
NEW:
consistent with the no-lock-in null of Section~\ref{sec:hazard-interp}, which shows that null recovers 97.8\% of the benchmark under the standalone scorer
RATIONALE: The clause has just named the object ("the no-lock-in null of Section~\ref{sec:hazard-interp}"), so "that null" is the referent and the adjective was redundant as well as overclaiming.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: OLD retains the pinned '\% of the benchmark' byte-identically (whole-file count 31 -> 31).

## Edit 20 — §V.B: the timing lead cannot discriminate (first site) (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 277)
OLD_COUNT_ASSERT: 1
OLD:
so the lead cannot discriminate the elasticity from the mechanical model. Second, propagating
NEW:
so the lead cannot discriminate the elasticity from the $\beta_1 = 0$ null. Second, propagating
RATIONALE: Object name. Disambiguated from the near-identical §V sentence by the following "Second, propagating" (the §V twin runs "Third, the marginal's"), so the OLD is unique.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: OLD contains no gate/test span; this line's many pinned literals ('$[+4.63, +6.92]$', 'factor of $37$', 'patha\_sign\_test', ...) are all outside it.

## Edit 21 — §V.E: the parenthetical gloss, by content (C-30)
FILE: paper/v18/revised_paper_v18.tex  (line 319)
OLD_COUNT_ASSERT: 1
OLD:
and the $\beta_1 = 0$ null (the mechanical model with the lock-in elasticity switched off) already recovers 85.7\%
NEW:
and the $\beta_1 = 0$ null (the elasticity switched off, baseline turnover held at its observed level) already recovers 85.7\%
RATIONALE: C-30 names this as the closest existing gloss and its defect: it defines the null by construction ("the mechanical model with the elasticity switched off") rather than by content. The replacement is C-30's own proposed wording, and it removes the assertion at the same time.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: OLD retains '85.7\%' and the pinned '\% of the benchmark' byte-identically.

## Edit 22 — §V.E: the timing lead cannot discriminate (second site) (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 323)
OLD_COUNT_ASSERT: 1
OLD:
so the lead cannot discriminate the elasticity from the mechanical model. Third, the marginal's
NEW:
so the lead cannot discriminate the elasticity from the $\beta_1 = 0$ null. Third, the marginal's
RATIONALE: Object name. Disambiguated by the following "Third, the marginal's".
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: OLD contains no gate/test span. This is the heaviest-pinned line in the manuscript (26 gate/test literals incl. '$+2.9$ to $+8.7$', '$+3.5$ to $+13.1$', '\texttt{layer\_convolution}'); none intersects the OLD, and all 26 verified present with unchanged counts after.

## Edit 23 — §V.F (Interpretation): what the level supports (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 534)
OLD_COUNT_ASSERT: 1
OLD:
so what the level supports is the mechanical decomposition, with the named mechanisms bounded small
NEW:
so what the level supports is the scheduled-plus-turnover decomposition, with the named mechanisms bounded small
RATIONALE: "the scheduled-plus-turnover decomposition" is the paper's own existing name for this object (.tex:110, and .tex:582 uses "scheduled-plus-turnover principal path"), so this is a rename onto vocabulary already in the manuscript rather than a new coinage.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: none in OLD.

## Edit 24 — §VI.A (Dual Systemic Fallout): the shortfall-versus-cap (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 544)
OLD_COUNT_ASSERT: 1
OLD:
is, per the decomposition above, mostly mechanical: a gap to a cap schedule that no plausible prepayment environment would have met.
NEW:
is, per the decomposition above, mostly scheduled-plus-turnover: a gap to a cap schedule that no plausible prepayment environment would have met.
RATIONALE: Predicative rename; the colon that follows already glosses the content and is preserved verbatim.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: none in OLD.

## Edit 25 — §VI.A (welfare paragraph): the accounting gap (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 548)
OLD_COUNT_ASSERT: 1
OLD:
it is an accounting gap against a cap schedule, mostly mechanical by the decomposition above
NEW:
it is an accounting gap against a cap schedule, mostly scheduled-plus-turnover by the decomposition above
RATIONALE: Predicative rename; the disclosure that follows ("neither a lower nor an upper bound on the welfare cost") is untouched.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: OLD contains no gate/test span; the pinned '$+\$42.6$ billion' and 'in-sample calibration point' are later on the line.

## Edit 26 — §VI.B (cap design): the book's principal path (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 552)
OLD_COUNT_ASSERT: 1
OLD:
which is how far the fixed \$35 billion cap sat above the book's mechanical principal path.
NEW:
which is how far the fixed \$35 billion cap sat above the book's scheduled-plus-turnover principal path.
RATIONALE: Renames onto the exact form the paper already uses at .tex:582 ("the book's projected scheduled-plus-turnover principal path"), so the two cap-design sites now match.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: OLD retains '\$35 billion' byte-identically.

## Edit 27 — §VIII opening sentence (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 727)
OLD_COUNT_ASSERT: 1
OLD:
interacting with a prepayment environment mostly mechanical relative to the caps
NEW:
interacting with a prepayment environment mostly scheduled-plus-turnover relative to the caps
RATIONALE: The conclusion's first sentence is quoted more than any other; the colon immediately quantifies it (85.7\%), so the compressed compound is carried by the clause that follows. Least graceful of the renames — flagged in DECISION_NEEDED.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: OLD retains nothing pinned; 'baseline turnover' later in the sentence is untouched (whole-file count rises 40 -> 43 only from edits 1, 2, 21).

## Edit 28 — §VIII: what delivers the level (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 731)
OLD_COUNT_ASSERT: 1
OLD:
the shortfall against the phased caps is mostly mechanical, because the caps sat far above
NEW:
the shortfall against the phased caps is mostly scheduled-plus-turnover, because the caps sat far above
RATIONALE: Predicative rename; the causal clause ("because the caps sat far above ...") is preserved and is the content.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: OLD contains no gate/test span; the pinned 'projection rather than the non-binding cap, the lock-in channel accounts for roughly half the genuine surprise under the central allocation' follows the OLD and is untouched.

## Edit 29 — §VIII: the margin over the base (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 731)
OLD_COUNT_ASSERT: 1
OLD:
the lock-in elasticity's contribution is a bounded margin over that mechanical base rather than a pinned one
NEW:
the lock-in elasticity's contribution is a bounded margin over that baseline rather than a pinned one
RATIONALE: "that baseline" refers to the object the previous clause just described (scheduled amortization, the seasoning baseline, the turnover floor), so the reference is intact.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: OLD contains no gate/test span; '$+2.9$ to $+8.7$' follows and is untouched (count unchanged).

## Edit 30 — §VIII (trilemma paragraph): the cash-flow shortfall (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 737)
OLD_COUNT_ASSERT: 1
OLD:
while the cash-flow shortfall against the caps is mostly mechanical --- a composition
NEW:
while the cash-flow shortfall against the caps is mostly scheduled-plus-turnover --- a composition
RATIONALE: Predicative rename inside the trilemma paragraph; the composition disclosure that follows the em-dash is preserved verbatim.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: OLD contains no gate/test span; the pinned 'while its effect on (3) is incidence-conditional', 'trade off sharply under face accounting' and 'scheduled amortization and baseline turnover' are elsewhere on the line, all verified present after.

## Edit 31 — §VIII: the duration extension's arithmetic (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 737)
OLD_COUNT_ASSERT: 1
OLD:
The duration extension itself, however, is mostly the mechanical arithmetic of scheduled amortization and baseline turnover
NEW:
The duration extension itself, however, is mostly the arithmetic of scheduled amortization and baseline turnover
RATIONALE: Here the sentence spells the content out immediately ("of scheduled amortization and baseline turnover"), so the adjective is pure assertion. Deleting it preserves the abstract-scoped pin 'scheduled amortization and baseline turnover' byte-identically.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: OLD CONTAINS the gate span 'scheduled amortization and baseline turnover' (ABSTRACT_POSTURE key null_mechanical_components). NEW preserves it byte-identically; whole-file count 4 -> 4.

## Edit 32 — §VIII.A (Limitations): what the synthetic result is consistent with (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 751)
OLD_COUNT_ASSERT: 1
OLD:
which is consistent with the mechanical decomposition above rather than with a loan-level-mechanisms reading.
NEW:
which is consistent with the scheduled-plus-turnover decomposition above rather than with a loan-level-mechanisms reading.
RATIONALE: Renames onto the manuscript's own "scheduled-plus-turnover decomposition", matching edit 23 so both synthesis sites read the same.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: OLD contains no gate/test span; the pinned 'be cleanly attributed to modeling paradigm rather than to calibration and data source' is earlier on the line.

## Edit 33 — Appendix (Path A percentile block): the null's 85.7\% (C-29)
FILE: paper/v18/revised_paper_v18.tex  (line 1106)
OLD_COUNT_ASSERT: 1
OLD:
below the mechanical $\beta_1 = 0$ null's 85.7\%
NEW:
below the $\beta_1 = 0$ null's 85.7\%
RATIONALE: Object name only.
LITERALS_INTRODUCED: none
LITERALS_REMOVED: none
PINNED_SPANS_CROSSED: OLD retains '85.7\%' byte-identically.

---

## CENSUS

All counts are `str.count` on the whole file: BEFORE on the worktree's
`revised_paper_v18.tex`, AFTER on the in-memory result of applying all 33 edits.

| string (fixed) | before | after | note |
|---|---|---|---|
| `mechanical` | 42 | 13 | 42 -> 13: 29 lowercase partition uses removed here; the 30th is the capitalised T1 row label, counted in the next row |
| `Mechanical` | 1 | 0 | T1 row label only; now `No-elasticity` |
| `mechanically` | 5 | 4 | one adverbial partition use removed (.tex:110); 4 ordinary uses kept |
| `mechanics` | 11 | 12 | +1: the definitions sentence says "not mechanics from behavior" |
| `Mechanics` | 2 | 2 | two appendix titles, untouched |
| `mechanical-majority` | 1 | 0 | renamed to `large-majority` |
| `large-majority` | 1 | 2 | the .tex already used it once at .tex:150 |
| `large majority` | 6 | 6 | PINNED (test_abstract_hedge_gate); unchanged |
| `no-elasticity` | 0 | 4 | new term: 4 sites (.tex:44, 60, 78, 92) |
| `scheduled-plus-turnover` | 3 | 11 | manuscript's own compound; 3 -> 11 |
| `$\beta_1 = 0$ null` | 34 | 40 | +6 |
| `$\beta_1 = 0$` | 46 | 52 | +6 (edits 1, 4, 5, 12, 20, 22) |
| `structurally distinct` | 5 | 5 | unchanged (edits 5, 6 keep the phrase) |
| `Structurally Distinct` | 2 | 2 | unchanged; edit 11 extends the heading, not the phrase |
| `scheduled amortization and baseline turnover` | 4 | 4 | PINNED (ABSTRACT_POSTURE null_mechanical_components); unchanged |
| `admits no counterpart to the $\beta_1 = 0$ null` | 1 | 1 | PINNED (gate #94); unchanged, deliberately not duplicated |
| `itself read from realized, partly behavioral turnover` | 1 | 1 | PINNED (ABSTRACT_POSTURE null_floor_behavioral); unchanged |
| `partly behavioral` | 3 | 5 | +2 from edits 1 and 2; the pinned abstract phrase above is one of the originals |
| `baseline turnover` | 40 | 43 | +3 from edits 1, 2, 21 |
| `genuine surprise` | 4 | 4 | PINNED; unchanged |
| `the instability is the max form's censoring mechanics` | 1 | 1 | PINNED (gate #104); unchanged |
| `the nineteen-month floor variant reported later is an input-stability check rather than an outcome holdout` | 1 | 1 | PINNED; same paragraph as edit 1; unchanged |
| `trade off sharply under face accounting` | 1 | 1 | PINNED (gate #103); same line as edits 30, 31; unchanged |
| `while its effect on (3) is incidence-conditional` | 1 | 1 | PINNED (gate #103); unchanged |
| `\texttt{layer\_convolution}` | 3 | 3 | PINNED (gate #105); same line as edit 22; unchanged |
| `$+2.9$ to $+8.7$` | 8 | 8 | unchanged |
| `$+3.0$ to $+8.0$` | 5 | 5 | unchanged |
| `$+3.5$ to $+13.1$` | 7 | 7 | unchanged |
| `$+5.6$` | 25 | 25 | unchanged |
| `$+\$42.6$ billion` | 10 | 10 | unchanged |
| `85.7\%` | 21 | 21 | unchanged |
| `88.7\%` | 20 | 20 | unchanged |
| `88.5\%` | 10 | 10 | unchanged |
| `97.8\%` | 6 | 6 | unchanged |
| `115.3\%` | 2 | 2 | unchanged |
| `\% of the benchmark` | 31 | 31 | unchanged |
| `\% of benchmark` | 13 | 13 | unchanged |
| `in-sample calibration point` | 41 | 41 | unchanged |
| `no-lock-in null` | 1 | 1 | unchanged (edit 19 leans on it as the antecedent) |
| `the mechanical model` | 4 | 0 | all four gone |
| `mostly mechanical` | 5 | 0 | all five gone |
| `\label{sec:method-estimators}` | 1 | 1 | unchanged (edit 11 keeps the label byte-identical) |
| `\label{tab:bases}` | 1 | 1 | unchanged (edit 10 keeps the ref) |

Regex counts (same two files):

- `[Mm]echanical` — **43 before, 13 after**. The 13 are exactly the 13 ORDINARY
  rows of the table in §0 (.tex lines 94, 160, 182, 315, 641, 929, 1105, 1128,
  1144, 1311, 1326, 1346, 1401), verified by re-enumerating the result.
- `[Mm]echanical(?!ly)` — 38 before, 9 after.

Whole-file integrity checks run on the result:

- **Line 31 (the abstract) byte-identical**: True. Line count 1436 -> 1436.
- **Every string literal of length >= 10 in `tools/liveness_gates.py` and
  `tests/*.py` that occurs in the .tex still occurs in the result: 0 lost.**
  Only two such literals change COUNT, both harmlessly: `baseline turnover`
  40 -> 43 (edits 1, 2, 21) and `decomposition` 54 -> 53 (edit 5 drops one).
  `decomposition` is only ever used in the gate file as a JSON key
  (`tools/liveness_gates.py:2039, 3189, 3274`), never as a .tex span, and every
  gate that pins spans tests membership rather than count.
- **Numeric-token multiset**: the only change is +6 `0` and +6 `1`, which are
  exactly the six added `$\beta_1 = 0$` tokens. No printed figure, percentage or
  dollar amount is added, removed or altered anywhere in the edit set.

- **Per-edit pinned-span containment**, measured by testing every gate/test string
  literal (length >= 10) against each OLD span. Only these OLD spans contain one, and
  every one is preserved byte-identically in the NEW:
  edit 5 (`decomposition`, `estimators`), edit 6 (`estimators`),
  edit 7 (`$+5.6$ points`), edit 8 (`decomposition`), edit 11 (`estimators`),
  edit 15 (`genuine surprise`), edit 17 (`large majority`),
  edit 19 (`\% of the benchmark`, `standalone`), edit 23/24/25 (`decomposition`),
  edit 31 (`scheduled amortization and baseline turnover`, `baseline turnover`),
  edit 32 (`decomposition`). No other OLD span touches a pinned literal.

---

## UNVERIFIED

1. **Whether the .tex compiles.** I did not build, and I am not permitted to. Two
   edits are the ones to eyeball in the PDF: edit 11 lengthens the §III.A subsection
   heading ("Two Structurally Distinct Estimators, One Decomposition"), which affects
   the table of contents and any running head; and edit 1 adds ~80 words to the
   already very long "Definitions used throughout" paragraph on p. 4-5, which may
   reflow the T1 float. Neither adds a float, a label or a reference.
2. **The response letter.** `paper/v18/response_to_referees_round22.tex` uses
   "mechanical" 6 times (lines 264, 326, 329, 485, 564, 585). Gate #101's letter
   check (`LETTER_CURRENT_LITERALS`, `tools/liveness_gates.py:592-603`) is a list of
   NUMERIC literals only, so none of those 6 can break a gate — but if the letter is
   going out with this round, its §7 will describe the manuscript in a vocabulary the
   manuscript no longer uses. I did not draft letter edits (out of my region).
3. **The long-abstract variant.** Per the brief the coordinator mirrors. All 33 OLD
   spans are outside line 31, so all 33 should apply to the variant unchanged, but I
   did not measure them against that file.
4. **The markdown/txt editions.** Not regenerated, not measured.
5. **"scheduled-plus-turnover" as a predicate adjective** (edits 24, 25, 27, 28, 30)
   reads compressed. The manuscript already uses the compound substantively
   ("a payments mix of scheduled-plus-turnover running below \$35 billion", .tex:110)
   so it is within its habits, but this is a style call, not a verified fact.

---

## WORD_COUNT_IMPACT

**No edit touches line 31.** Line 31 is byte-identical before and after (verified by
direct comparison), so the abstract remains **294 words** and gate #101's tie between
the response letter's claimed count and the abstract's actual count is unaffected.
Net abstract word change: **0**.

Body word change, measured: **+172 words** on the whole file (66,783 -> 66,955).
Of that, +164 is front matter — line 92 (the definitions paragraph) +81, line 44 +36,
line 50 +36, line 58 +6, line 60 +3, line 120 +2, line 78 +0 — and the remaining +8 is
the 26 body/appendix renames combined (mostly edit 13, which spells out
"regardless of any rate response above that baseline"). Front matter is where R32's
page budget is tightest; flagged in DECISION_NEEDED.

---

## DECISION_NEEDED (Eugene's judgement, not wording)

1. **"no-elasticity" vs "observed-turnover" vs "rate-insensitive"** as the object's
   name in words. I chose `no-elasticity` (C-29's first suggestion) because it is the
   only one of the three that is exactly true: the object switches off one imported
   coefficient and changes nothing else. `observed-turnover` overstates — the floor's
   off-window read is not the observed in-window level. `rate-insensitive` is false
   above the floor for the seasoning ramp. Worth a one-line confirmation because the
   term then appears in T1.
2. **The artifact/manuscript naming divergence** created by edit 18: the JSON key
   stays `mechanical_majority_survives` while the manuscript says "large-majority
   threshold". Gates read the key, so nothing breaks, but the crosswalk in
   Appendix~\ref{app:ledger} may want a line.
3. **Edit 27** (§VIII's opening sentence: "a prepayment environment mostly
   scheduled-plus-turnover relative to the caps") is the least graceful rename in the
   set. Alternative, one clause longer: "a prepayment environment whose shortfall
   against the caps was mostly scheduled amortization and baseline turnover". I did
   not draft the alternative because it duplicates the abstract-pinned string.
4. **+164 front-matter words** against R32's length pressure. Edit 1 (the definitions
   sentence, +81) is the compressible one if the budget binds; it can lose its third
   sentence and still satisfy C-30, at the cost of dropping the explicit "not a
   non-behavioral object" refusal — which is the half the panel actually asked for.
5. **Whether to carry the rename into the response letter** (see UNVERIFIED 2).
