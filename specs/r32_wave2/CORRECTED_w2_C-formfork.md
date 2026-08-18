# CORRECTED — R32 Wave 2, cluster C-formfork (C-04, C-22, C-23, C-28, C-32)

FILE (all edits): `paper/v18/revised_paper_v18.tex`, current bytes at HEAD `9f56755` (1,460 lines).
Every OLD below was re-measured with `str.count` on the **current** canonical file **and** on
`paper/v18/revised_paper_v18_long_abstract.tex`: **exactly 1 in each**. Sequential application of
all ten in the order printed succeeds in both files (no intra-cluster self-destruction).

**Re-anchoring result: 10 OLDs re-measured, 0 needed byte repair, but every line number moved.**
The drafts were written against a 1,435-line file; the paragraph splits and Appendix-O growth
shifted my region. Current lines: Edits 1,2 → **150** (was 150); Edits 4 → **227** (was 227);
Edit 5 → **355** (was 333); Edit 6 → **554** (was 532); Edit 7 → **749** (was 727); Edit 8 →
**753** (was 731); Edits 10,11,12 → **759** (was 737). Edit 5 still lands inside the single line
that starts `A seventh qualification` (gate #98 verified: 1 such line, 15/15 ASSEMBLY_SPANS
present before and after — the draft said "twelve", which was wrong; the verdict's count of 15 is
correct).

**No edit touches line 31.** Abstract is byte-identical, **323 → 323 words**, so gate #101's
letter-vs-abstract tie is untouched.

**Two edits dropped** (draft Edit 3, draft Edit 9). Ten remain. Edit numbering below is kept from
the draft so the verdict's findings map one-to-one.

---

## Edit 1 — form-label the two null recoveries at the §III.B convergence withdrawal (C-04)
OLD_COUNT_ASSERT: 1
OLD:
and I now report the projection range and the null's recovery as two separately stated quantities.
NEW:
and I now report the projection range and the null's recovery as two separately stated quantities. Both recoveries are production-floor-form reads: under the additive form the null recovers 35.6\% on the benchmark-consistent basis at the headline floor (44.7\% standalone; Section~\ref{sec:robustness-floor}), so the projection is being compared against one form's null rather than against a form-invariant object.
WHY: the convergence-withdrawal argument is a comparison against the null's *level*, and both
quoted levels (88.7\%, 85.7\%) are one form's. One clause conditions both and supplies the
additive counterpart.
FIX_FOLDED: convention violation 6 (C-04's own rule — the shared figure is now printed with its
standalone companion rather than bare). The basis label used, `benchmark-consistent basis`, is the
line's own label for the shared basis 700 characters earlier ("the 88.7\% the $\beta_1 = 0$
mechanical null recovers on the benchmark-consistent basis"), so no new basis vocabulary enters.
LITERALS: `35.6\%` — `floor_form_mixture_results.json` `cells["4.991|1|0"].share_pct = 44.69959732600039`
standalone, minus the committed `shared_pct = standalone_pct - 9.0964` → 35.6032 shared (identical
object to `floor_form_offwindow_results.json` additive row floor 4.991 `null_share_pct = 44.6996`).
`44.7\%` — the same artifact field, standalone; already printed once at line 737 in that sense.
PINS: none inside this OLD. The two gate-#63 literals on the same line (`they require the
uniform-spread allocation, because the settlement-aware allocation puts the anticipated share at
75.6\%`, `clears by 13.2 points in-sample and 10.1 points`) and RELOCATED_TO_BODY's
`surprise_share_allocated_body` sit outside the span and re-measure 1 → 1.

---

## Edit 2 — condition the surviving-agreement sentence and name the cap-placement inference (C-32, C-04)
OLD_COUNT_ASSERT: 1
OLD:
The agreement that survives is coarse and is the one I rely on: both objects put the anticipated mechanical component in the large majority of the shortfall.
NEW:
The agreement that survives is coarse and is the one I rely on: under the production floor form both objects put the anticipated mechanical component in the large majority of the shortfall. That majority is a fact about where the caps were set rather than about the size of the rate response --- the caps sat above any prepayment path this book could have delivered --- so leading with it understates lock-in, and the reading that speaks to mortgage markets is the marginal's share of the expectations-based shortfall, reported below.
WHY: this is the sentence the whole coarse-agreement claim rests on, and the additive null recovers
35.6\% — not a majority — so the claim needs the form condition. C-32's inference (leading with
the majority understates lock-in) is landed once, here, where the majority is first asserted in
the body, and points at the 49\%/80\% expectations ratios already on this same line.
FIX_FOLDED: refuted_claim 14 (the Edit 1 / Edit 2 seam — the surviving-agreement sentence was left
unconditioned while Edit 1 established a 35.6\% non-majority one sentence earlier); convention
violation 3 (the cap-placement inference now appears **once**, not three times). Also folds a
finding the verifier could not have had: the landed `no-elasticity baseline` definition explicitly
disowns the mechanics/behavior framing ("What the partition separates is that baseline from that
increment, **not mechanics from behavior** ... so the baseline is not a non-behavioral object and I
do not call it one"). The draft's wording — "rather than about how households responded to rates"
— would have contradicted that definition. Reworded to cap placement vs. **the size of the rate
response**, which the definition permits.
LITERALS: none. `understates lock-in` 0 → 1; `the marginal's share of the expectations-based
shortfall` 0 → 1; no numeric token added.
PINS: none inside this OLD. Em-dash style matched to the site: line 150 uses 4 spaced ` --- ` and
0 unspaced, so the inserted dashes are spaced.

---

## Edit 4 — form-label the in-sample null level quoted in §V.B, at one floor (C-04)
OLD_COUNT_ASSERT: 1
OLD:
which shows the mechanical model recovers 97.8\% of the benchmark under the standalone scorer (88.7\% on the shared accounting basis).
NEW:
which shows the mechanical model recovers 97.8\% of the benchmark under the standalone scorer (88.7\% on the shared accounting basis). Those are production-floor-form levels: under the additive form the same null recovers 44.7\% at the off-window floor against the production form's 94.8\%, both on the standalone scorer (Section~\ref{sec:robustness-floor}).
WHY: this is the §V.B sentence arguing that a substantial share of the aggregate level rides on the
floor, and it quotes the null's level bare four sentences after the form fork is introduced.
FIX_FOLDED: refuted_claim 9 — the draft paired max-form **in-sample** (97.8\%) against additive
**off-window** (44.7\%), implying a 53.1 pp form gap that is neither of the two real ones. The
comparison is now inside one floor (4.991): 44.7\% vs 94.8\%, both standalone, both from the same
artifact row set, a true 50.1 pp gap. Refuted_claim 10 (softening, "as form-dependent as the
marginal") is folded by **deleting the inference clause** rather than strengthening it: line 737
already says "The aggregate level, by contrast, is strongly form-dependent (the additive central
leg recovers 67.2\% at the production floor, versus 107.0\% under the max form...)", so restating
the comparative here would be redundant. Refuted_claim 11 was a rationale error only; the real
reason for quoting off-window is the 55.9 collision the draft's own coordinator note gives (the
additive in-sample null is 55.93\% standalone, and 55.9\% is already committed in the tex for the
additive **central** leg at 4.991 — a same-literal/different-object collision).
LITERALS: `44.7\%` — `floor_form_offwindow_results.json` additive floor 4.991 `null_share_pct =
44.6996`, standalone. `94.8\%` — same artifact, max floor 4.991 `null_share_pct = 94.7917`,
standalone; already 3× in the file (lines 355, 542, 828), all the same object.
PINS: none.

---

## Edit 5 — deny aggregate fit as a defense of the 100 PSA convention (C-28)
OLD_COUNT_ASSERT: 1
OLD:
(run \texttt{psa\_level\_sweep}), a span with no coverage property --- it is a range over a convention I did not estimate, and its endpoints are not draws from anything.
NEW:
(run \texttt{psa\_level\_sweep}), a span with no coverage property --- it is a range over a convention I did not estimate, and its endpoints are not draws from anything. Aggregate fit is not available as a defense of the 100~PSA convention: at the off-window floor the $\beta_1 = 0$ null recovers 101.9\% of the benchmark under the standalone scorer at 75~PSA against 94.8\% at the production 100, while the central leg's recovery is closer to the benchmark at 100 (100.4\%) than at 75, so the two legs rank the ramps opposite ways.
WHY: the sweep entry prints only the marginal span, leaving aggregate fit silently available as an
implicit defense of the production ramp. It is not available, because the two legs rank the ramps
in opposite directions.
FIX_FOLDED: refuted_claim 8 — the draft's "so the ramp the paper runs is the worse-fitting of the
two" is FALSE on the leg the paper reports. Verified from source: `psa_level_sweep_results.json`
`cells["4.991|100|6.5"].share_pct = 100.36328` vs `cells["4.991|75|6.5"].share_pct = 102.79752`,
so the production 100 fits **better** on the central leg (|Δ| 0.36 vs 2.80) while the null fits
better at 75 (101.94 vs 94.79). The claim is now the true, stronger one: fit does not select.
LITERALS: `101.9\%` — `psa_level_sweep_results.json` `cells["4.991|75|0"].share_pct = 101.94149`,
standalone; count 0 → 1 (verdict cleared it as repo-unique for this object). `94.8\%` —
`cells["4.991|100|0"].share_pct = 94.79172`, standalone; 3 → 5 across Edits 4 and 5. `100.4\%` —
`cells["4.991|100|6.5"].share_pct = 100.36328`, standalone; already the committed literal for
exactly this object in `tab:bases` line 542 ("Path B, central (off-window floor) & 100.4\% &
91.3\%") and line 828, so 3 → 4 is a re-print. **`102.8\%` deliberately not printed**: it
currently denotes a different object (the scrambled-month shape-retention range, lines 1379/1417);
the central leg's direction is stated with its own committed number instead.
PINS: this OLD is inside the gate-#98 assembly paragraph (line 355, `ASSEMBLY_OPENER = "A seventh
qualification"`). Re-measured on the result: exactly **1** line starts with the opener and **15 of
15** ASSEMBLY_SPANS are present. `posture_binding_layer` ("The widest layer that does have a
coverage property is the floor reads' own sampling error, $+2.9$ to $+8.7$ points after
wild-cluster correction") begins immediately after the insertion and is byte-identical. The shipped
`assembly_check` has no ordering assert, so inserting between two spans is safe.

---

## Edit 6 — form-label the null's two levels in §V.F's timing sentence (C-04)
OLD_COUNT_ASSERT: 1
OLD:
and 85.7\% at the off-window floor (Table~\ref{tab:bases}).
NEW:
and 85.7\% at the off-window floor (Table~\ref{tab:bases}), both under the production floor form; under the additive form the null recovers 35.6\% at that floor (Section~\ref{sec:robustness-floor}).
WHY: C-04's §V.F site. The `\ref{tab:bases}` pointer stays attached to the production-form figures,
because `tab:bases` carries no additive rows.
FIX_FOLDED: convention violation 5 — the draft's "both under the production floor form and 35.6\%
at that floor under the additive one" yoked a prepositional phrase to a percentage across a
`both ... and` correlative. Recast as the verifier's fix: semicolon, then a full clause. The
governing `on the shared basis` earlier in the sentence correctly labels 35.6\% (C-04's rule
satisfied by inheritance, not by a bare figure).
LITERALS: `35.6\%` — same provenance as Edit 1.
PINS: none inside this OLD; the gate-#63 literal `a miss of 8.7 points` is elsewhere on line 554
and re-measures 1 → 1.

---

## Edit 7 — form-label §VIII's first statement of the majority (C-04)
OLD_COUNT_ASSERT: 1
OLD:
interacting with a prepayment environment mostly mechanical relative to the caps: the $\beta_1 = 0$ null recovers 85.7\% of the benchmark at the headline calibration under any rate response above the baseline turnover it embeds, and
NEW:
interacting with a prepayment environment mostly mechanical relative to the caps: under the production floor form the $\beta_1 = 0$ null recovers 85.7\% of the benchmark (35.6\% under the additive form) at the headline calibration under any rate response above the baseline turnover it embeds, and
WHY: the conclusion's first statement of the majority carried no form condition.
FIX_FOLDED: convention violation 1 (hedge scope) — the parenthetical is moved from **after** the
max-form-specific hedge "under any rate response above the baseline turnover it embeds" to
immediately after `85.7\% of the benchmark`, matching the landed abstract's placement. The hedge is
the max form's censoring property; the additive form never censors, so the hedge must not appear to
scope the additive figure. Convention violation 3 — the cap-placement gloss the draft added here is
**removed**; it now appears once, at Edit 2.
LITERALS: `(35.6\% under the additive form)` — byte-identical reuse of the landed abstract
parenthetical.
PINS: none.

---

## Edit 8 — form-label the null's two levels where §VIII disciplines the contrast (C-04)
OLD_COUNT_ASSERT: 1
OLD:
The composition of that recovery, however, disciplines what the contrast can mean: the $\beta_1 = 0$ null recovers 85.7\% on the same basis at the headline floor and 88.7\% in-sample,
NEW:
The composition of that recovery, however, disciplines what the contrast can mean: under the production floor form the $\beta_1 = 0$ null recovers 85.7\% on the same basis at the headline floor (35.6\% under the additive form) and 88.7\% in-sample,
WHY: "on the same basis" labels the accounting basis; the form label was the missing half.
FIX_FOLDED: convention violation 7 (ordering) — the parenthetical now sits on the headline-floor
figure it corresponds to, not trailing the in-sample one.
LITERALS: `(35.6\% under the additive form)` — as Edit 7.
PINS: none inside this OLD.

---

## Edit 10 — condition the trilemma paragraph's opening clause (C-23)
OLD_COUNT_ASSERT: 1
OLD:
and this paper's evidence is that they do not form the strict trilemma a three-way ``trade-off'' would imply:
NEW:
and this paper's evidence, under its production floor form (the additive form roughly doubles the margin at issue), is that they do not form the strict trilemma a three-way ``trade-off'' would imply:
WHY: C-23's live defect is ordering — the 4,470-character paragraph opened flat and the
qualification arrived ~2,900 characters later. The condition now sits in the opening clause.
FIX_FOLDED: refuted_claim 12 — the draft's "and not under the additive form" contradicted both
Edit 12 and the paragraph's own untouched committed sentence "What survives across forms is that
the trade-off is modest, not that it is absent". Refuted_claim 13 — the draft's denial was also
over-broad, covering legs (1) and (3), which are not form-conditional. The verifier's stated fix is
adopted verbatim in substance: it conditions without denying. Rendered with commas + parentheses
rather than em-dashes so the clause does not add a nested dash pair to a line that already carries
four.
LITERALS: none.
PINS: gate #103 `dissolution_scope` ("trade off sharply under face accounting") and
`trilemma_conditional` ("while its effect on (3) is incidence-conditional") are later on line 759,
untouched, 1 → 1 each. All 8 BUYBACK_BRACKET_SPANS and all 6 VERDICT_AUDIT_SPANS re-measure
unchanged.

---

## Edit 11 — move the additive counterweight to the concession itself (C-23)
OLD_COUNT_ASSERT: 1
OLD:
reduces to ``the marginal is small''---and under the production floor form the marginal is bounded small by construction. Because \eqref{eq:pathB} combines the turnover floor with the voluntary hazard by a hard maximum, switching the elasticity off can raise the hazard by no more than the excess of the $\beta_1 = 0$ hazard over the floor, and by nothing at all where the floor binds on the $\beta_1 = 0$ leg itself, 14.3\% of loan-months at the in-sample calibration point (Section~\ref{sec:identification}). The dissolution is therefore a statement about a calibrated ceiling, not an independent finding, and it is form-conditional: under the disclosed additive form, which never censors the elasticity, the same counterfactual roughly doubles to about $+11$ points (Section~\ref{sec:robustness-floor}).
NEW:
reduces to ``the marginal is small''---and under the production floor form the marginal is bounded small by construction; under the disclosed additive form, which never censors the elasticity, the same counterfactual is about $+11$ points and nearly floor-invariant (Section~\ref{sec:robustness-floor}). Because \eqref{eq:pathB} combines the turnover floor with the voluntary hazard by a hard maximum, switching the elasticity off can raise the hazard by no more than the excess of the $\beta_1 = 0$ hazard over the floor, and by nothing at all where the floor binds on the $\beta_1 = 0$ leg itself, 14.3\% of loan-months at the in-sample calibration point (Section~\ref{sec:identification}). The dissolution is therefore a statement about a calibrated ceiling, not an independent finding, and it is form-conditional.
WHY: the additive counterweight must sit **at** the concession, not four sentences after it.
Nothing is deleted: the clause is relocated, "and it is form-conditional" survives as the sentence
that names the dimension, and "roughly doubles" is not lost (Edit 10 carries it into the paragraph
opener). "nearly floor-invariant" is added because a floor-invariant counterweight is what makes
the concession bite. No paragraph split — that is C-87's business and would move a float.
FIX_FOLDED: convention violation 8, accepted as the verifier judged it ("defensible"); the
comparative and the number now sit at the paragraph's two load-bearing positions rather than one.
Unchanged from draft otherwise.
LITERALS: none. `$+11$` 3 → 3 (one occurrence relocated, none added); `$+11.2$` unchanged at 9;
`roughly doubles` 2 → 2 (one removed here, one added by Edit 10); `14.3\%` 2 → 2.
PINS: `bounded small by construction` (C-23's own verbatim quote) reproduced byte-identically,
1 → 1. `and it is form-conditional` reproduced, 1 → 1. Whole-file `form-conditional` unchanged at
12 (gate #69 wants ≥3).

---

## Edit 12 — carry the condition into the policy sentence that leans on smallness (C-23)
OLD_COUNT_ASSERT: 1
OLD:
The binding constraint against adopting such a rule is therefore not a mobility--cash-flow trade-off but the TBA liquidity premium described above.
NEW:
The binding constraint against adopting such a rule is therefore, on either form, not a mobility--cash-flow trade-off but the TBA liquidity premium described above.
WHY: C-23's last requirement. "on either form" is what the paragraph already commits to one
sentence earlier ("What survives across forms is that the trade-off is modest, not that it is
absent"), so this makes the inheritance explicit without asserting anything new — and, with Edit
10 no longer denying the additive form, the three statements are now mutually consistent.
FIX_FOLDED: refuted_claim 12, resolved on the Edit 10 side; Edit 12 stands as drafted.
LITERALS: none.
PINS: none.

---

## CENSUS

Measured with `str.count` on the current canonical file and on the in-memory result of applying all
ten edits in order. Not estimated.

| literal / pinned span | before | after |
|---|---|---|
| `85.7\%` | 21 | 21 |
| `88.7\%` | 20 | 20 |
| `97.8\%` | 6 | 6 |
| `35.6\%` | 1 | 5 |
| `(35.6\% under the additive form)` | 1 | 3 |
| `44.7\%` | 1 | 3 |
| `94.8\%` | 3 | 5 |
| `101.9\%` | 0 | 1 |
| `100.4\%` | 3 | 4 |
| `102.8\%` | 2 | 2 |
| `67.2\%` | 1 | 1 |
| `107.0\%` | 20 | 20 |
| `14.3\%` | 2 | 2 |
| `$+11.2$` | 9 | 9 |
| `$+11$` | 3 | 3 |
| `$+5.6$` | 25 | 25 |
| `$+9.7$` | 4 | 4 |
| `$+10.7$` | 2 | 2 |
| `$+2.9$ to $+8.7$` | 8 | 8 |
| `$+3.5$ to $+13.1$` | 7 | 7 |
| `production floor form` | 5 | 10 |
| `under the production floor form` | 3 | 7 |
| `additive form` | 21 | 27 |
| `form-conditional` | 12 | 12 |
| `and it is form-conditional` | 1 | 1 |
| `bounded small by construction` | 1 | 1 |
| `roughly doubles` | 2 | 2 |
| `on either form` | 0 | 1 |
| `mostly mechanical` | 5 | 5 |
| `mechanical` | 38 | 38 |
| `no-elasticity baseline` | 3 | 3 |
| `benchmark-consistent basis` | 2 | 3 |
| `understates lock-in` | 0 | 1 |
| `the marginal's share of the expectations-based shortfall` | 0 | 1 |
| `where the Committee set the ceiling` | 0 | 0 |
| `about how households behaved` | 0 | 0 |
| `100~PSA` | 2 | 3 |
| `75~PSA` | 0 | 1 |
| `(run \texttt{psa\_level\_sweep})` | 2 | 2 |

Gate-structure re-measurement on the result (dicts/lists AST-extracted from
`tools/liveness_gates.py`, evaluated against the in-memory result):

| structure | n | diffs |
|---|---|---|
| `ZERO_COUNT` | 19 | none |
| `EXACTLY_ONE` | 4 | none |
| `ASSEMBLY_SPANS` (gate #98) | 15 | none; 15/15 present, exactly 1 line starts `A seventh qualification` |
| `RELOCATED_TO_BODY` | 9 | none |
| `BUYBACK_BRACKET_SPANS` (#103) | 8 | none |
| `VERDICT_AUDIT_SPANS` (#104) | 6 | none |
| `LETTER_CURRENT_LITERALS` (#101) | 16 | none |
| `ABSTRACT_HEDGES` / `ABSTRACT_POSTURE` (#68/#99) | 2 / 8 | none |
| `SUPERSEDED_CONTEXTUAL` | 1 | none (`894.8` unaffected by the new `94.8\%`) |
| `HARDCODED_XREF` (5 regexes) | — | 0 hits before, 0 after |

Full string-constant sweep: **2,357** distinct constants of length ≥8 AST-extracted from
`tools/liveness_gates.py` and all 30 `tests/*.py`. **0 lost** (no count>0 → count==0), **0 gained
from zero**, and **no constant whose before-count was 1 changed at all** — which clears the hard
`count(...) == 1` asserts in `tests/test_assembled_corrections_gate.py` (table spans) and
`tests/test_floor_ladder_gate.py` (ladder rows and the single printed site). Only 8 generic
substrings move: `production` 223→232, `additive` 52→58, `standalone` 37→40, `recovers ` 41→45,
`against ` 233→237, `\% of the benchmark` 31→32, `headline` 167→168, `expectations` 14→15. None is
in `ZERO_COUNT` or `EXACTLY_ONE`.

Structural: line count **1,460 → 1,460** (no split, no new line). Abstract line 31 **byte-identical,
323 → 323 words**. New cross-refs use `Section~\ref{sec:robustness-floor}` and
`\ref{sec:identification}`; both `\label`s exist (1 each). No bare `%` introduced.

Size: **+1,667 characters / +250 words**, all body. Per edit (chars/words): 1 +316/+40,
2 +377/+63, 4 +224/+28, 5 +363/+63, 6 +139/+18, 7 +65/+10, 8 +65/+10, 10 +90/+14, 11 +11/+1,
12 +17/+3. By section: §III.B +693, §V.B +224, §V.E +363, §V.F +139, §VIII +248 characters. That
is **1,329 characters and 219 words lighter than the draft**, entirely from the two drops and from
deleting three redundant clauses.

---

## DROPPED

**Draft Edit 3 — the §V.B form-selection rule (C-22). DROPPED as redundant + refuted.**
The rule is **already stated**, at line 737 (§VII.F), in one sentence: "The max form remains
production for its semantics --- the floor as a minimum on \emph{total} turnover, the reading the
deep-discount calibration anchors --- and because it is the measured form curve's conservative
endpoint (below); the aggregate-level comparison is context for the level, not the selection rule
for the marginal's form, since the design does not identify levels." I confirmed that byte string
in the current file. So C-22's premise ("the rule is unstated") fails, and the concision rule
applies. Beyond redundancy the draft's version carried four independently disqualifying defects the
verifier established and I re-confirmed against current bytes: (i) "report no interior point" is
false — interior mixture points are printed at line 90 (`tab:headline` note a), line 355, and line
737 (`$+9.7$` count 4, `$+10.7$` count 2); (ii) "carry the additive endpoint beside every
quotation of the headline" is false — 21 lines quote `$+5.6$`, only 8 carry any additive companion;
(iii) "The calibration anchor does not discriminate" directly contradicts line 737 twice; (iv) "the
share itself is not identified anywhere in this design" is *weaker* than and points away from three
live disclosures (line 227 "the strictly-involuntary share ... is plausibly well under half", line
355, line 737), i.e. it softens a true claim. Its one non-redundant sub-clause ("which carries no
decomposition of realized turnover into voluntary and involuntary parts") restates line 227's own
"no component decomposition exists in this design" ~2,000 characters earlier in the same paragraph.
Nothing is drafted in its place: **C-22 is a posture call for Eugene** (see OPEN), not a wording
gap.

**Draft Edit 9 — third copy of the cap-placement inference in §VIII. DROPPED as redundant.**
It attaches the gloss "which is a fact about where the ceiling was set and not about how households
behaved" to the clause "because the caps sat far above what any plausible prepayment environment
would have delivered" — i.e. it restates the clause it modifies, and the E-benchmark counterweight
C-32 asks for already follows in the existing `---though` continuation on line 753. With Edit 2
landing the inference once and Edit 7's copy removed, `where the Committee set the ceiling` and
`about how households behaved` both stay at **0**. Dropping it also removes a collision with
D-mechanical's line-753 OLD ("the shortfall against the phased caps is mostly mechanical, because
the caps sat far above").

**Not drafted, unchanged from the draft's position:** C-04's three sites outside my region
(`tab:headline` line 78 and its uncertainty catalogue, §VI.B, §VII.F line 737); the `tab:bases`
rows at lines 542/545, which are a wave-4 exhibits call; and the PSA sweep's `expectation_check`
record (verified 3-for-3 in band at floor 4.0, 0-for-3 off window with the bands
[1.5,2.5]/[8.5,10.0]/[11.0,14.0] — but the current sentence makes no expectation claim, so C-28
requires no repair there; available as a one-clause addition to Edit 5 if wanted:
`and all three off-window cells landed outside their pre-committed bands`).

---

## COLLISIONS

Measured by extracting every sibling OLD from the other clusters' current draft/corrected files and
counting it on my result. **Zero sibling OLDs are broken by my edits** (every one that counted 1
before still counts 1 after).

1. **D-mechanical — MANDATORY ORDER: apply C BEFORE D.** Three of D's OLDs sit *inside* my OLD
   spans and would destroy them if D lands first: (a) `both objects put the anticipated mechanical
   component in the large majority of the shortfall.` (line 150, inside my Edit 2's OLD);
   (b) `consistent with the no-lock-in null of Section~\ref{sec:hazard-interp}, which shows the
   me...` (line 227, overlapping Edit 4's OLD); (c) `interacting with a prepayment environment
   mostly mechanical relative to the caps` (line 749, the head of Edit 7's OLD). All three of my
   NEWs reproduce D's OLDs byte-identically (verified: each counts 1 on my result), so D applies
   cleanly *after* me. The reverse order fails.
2. **Line-level sequencing warnings (same 5–7 KB line, no span intersection):** line **150** —
   Edits 1, 2 + four D OLDs; line **227** — Edit 4 + one D OLD; line **355** — Edit 5 + two
   B-ladder CORRECTED OLDs + five F-assembly OLDs; line **554** — Edit 6 alone; line **749** —
   Edit 7 + one D OLD; line **753** — Edit 8 + two D OLDs; line **759** — Edits 10, 11, 12 + two D
   OLDs. A coordinator applying by whole-line replacement must sequence these; applying by
   fixed-string replacement is order-free except for the D constraint in item 1.
3. **Cross-cluster region, §V.E line 355 (Edit 5).** That line is F-assembly's declared region and
   overlaps B-ladder's binding-layer passage; C-28's own inventory location list names `.tex:333`
   (now 355), so the site is condition-sanctioned, but the cluster split does not give §V.E to C.
   Coordinator's call. My insertion sits between `...not draws from anything.` and
   `posture_binding_layer`, intersecting no F or B span.
4. **Contested region, §III.B line 150 (Edits 1, 2).** G-denominators claims §III.B. G's CORRECTED
   OLDs land at lines 52, 92, 618, 647, 649, 663 — **no live collision**.
5. **No overlap** with A-posture (lines 31, 46, 79) or E-composition (line 1115; its `tab:composition`
   OLDs already landed and count 0).

---

## OPEN

1. **C-22 is unresolved and is Eugene's call, not a drafting one.** With Edit 3 dropped, the
   condition's remaining live content is resolution option (ii): promote the form-robust "roughly
   $+9$ to $+11$ points at the production floor" to headline status. I did not draft it — it is a
   posture change, it abandons the off-window headline (the form-robust band exists only at the
   *production* floor; at the off-window anchors the forms return $+5.6$ and $+11.2$ and no
   form-robust point exists), and it would rewrite the abstract, which gate #101 ties to the
   response letter's word count. The alternative reading — that the rule is already stated at line
   737 and C-22 should be closed as REFUTED — is what I recommend, and the coordinator can close it
   by citing that sentence.
2. **Suite green not proven.** I ran no repo script (prohibited). Every gate/test span I could
   locate — 2,357 AST-extracted string constants plus a re-implementation of the shipped
   `assembly_check` scoping rule — was re-measured, but I cannot rule out a gate whose span I did
   not find. The coordinator must run `tools/liveness_gates.py` and pytest after applying.
3. **Float placement / page count.** +1,667 characters across five sections on a 130pp build can
   move a float. The heaviest single addition is Edit 2 (+377 chars on line 150, §III.B) and Edit 5
   (+363 chars inside the §V.E assembly paragraph, which sits in the middle of the section-V float
   stack). Confirmed only by a `tectonic` build and a page-count / 0-undefined check. If the page
   count must be held, Edit 2's middle clause (`--- the caps sat above any prepayment path this book
   could have delivered ---`) is the one compressible span; the two clauses it cannot lose are the
   form condition and "leading with it understates lock-in".
4. **`101.9\%` is the cluster's only genuinely new numeric token** (0 → 1). The verifier cleared it
   as repo-unique for this object. I did not independently re-grep the markdown/txt editions or
   figure captions.
5. **R2:M8 (benchmark monthly frequency) remains unarbitrated** and no edit here touches it.
6. **The landed `no-elasticity baseline` definition constrains C-32's vocabulary.** It says
   explicitly that the partition separates baseline from increment, "not mechanics from behavior",
   and that the baseline "is not a non-behavioral object and I do not call it one". Edit 2 is
   worded to respect that. If a sibling cluster lands a cap-placement gloss phrased as "not about
   how households behaved", it will contradict the definition — worth a coordinator check across
   the D-mechanical and A-posture edit sets. Note the **abstract** already carries a nearby
   formulation ("most of that gap was never about behavior", hedged by "(itself read from realized,
   partly behavioral turnover)"), which is A-posture's region, not mine.
