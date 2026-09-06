# RECORD — v20 fresh-eyes shortening review: executed trims + decision menu

**Status:** review record + decision memo, 2026-08-04. Companion to
`RECORD_v20_compression_budget.md` (the executed Phase-3b program) and
`RESPONSE_v20_panel_draft.md` (PHASE-3b section). Method: the built main text
(`paper/v18/build_split/main_text_1-97.pdf`) was read front to back as a
referee would — the PDF first, the tex only afterwards — specifically to catch
the cross-section restatements nine section-local rewrite batches cannot see.
Every candidate below was then checked against the tex at HEAD and against the
gate/test pin surface (AST extraction of every string literal in
`tools/liveness_gates.py` + `tests/*.py`, membership-tested per candidate
span) before being classified.

**Suite state after the executed trims:** 128/128 gates PASS, 1,109 tests
pass, both variants rebuilt 0-undefined (140/141pp), `replication_appendices`
13pp 0-undefined, split boundary unchanged (Online Appendix banner still opens
p. 98; split re-cut 97/43), editions regenerated through the hard self-checks
with the footnote count re-pinned 3→2 (derivation comment in
`tools/editions/tex2md.py`). Main text ≈ −310 words against the pre-review
HEAD (≈ 46.3k words on the Phase-3b counting convention).

---

## 1. Executed — tier (a), redundancy-only, zero pins lost

Three cuts, both variants, anchored literal replacements. Each deletes a
*restatement* whose canonical statement survives elsewhere in the gated
corpus; the pin scanner found no gate or test literal inside any deleted span,
and the full suite was run after the edits (green first run).

**(a1) §V.B calibration footnote deleted (−≈150w).** The footnote on the
elasticity import ("The central 6.5\% is the midpoint of that band…")
duplicated, clause for clause, the body text beside it: the midpoint-adoption
sentence duplicates the sentence it hangs from; the transform-slot /
turnover-proxy / 1.5\%-zero-gap content duplicates the post-eq-(3) paragraph,
which is *stronger* (it quantifies the insensitivity over $P_q \in (0,
0.12]$); the Fonseca–Liu not-a-source-of-the-band scoping survives in richer
form in the §V.B import-consequences paragraph and §V.E's fifth
qualification. Consequence: manuscript footnotes 3→2 (fn:manifest and the
sec:method-abm payoff-rule footnote remain; both are label-referenced, so
numbering is automatic), tex2md WANT re-pinned.

**(a2) §V.B moving-vs-refinancing mapping stated once, not twice (−≈95w).**
The paragraph opening "One more assumption travels with the import, and
nothing here tests it…" stated the estimand-vs-application mismatch (moving
probability applied to the total prepayment hazard) that the mixture-bracket
paragraph two paragraphs later restates in full as "a second mapping
assumption" — and then *prices* (runs `moving_share_bracket`,
`moving_share_bracket_offwindow`, 8 pinned spans, untouched). The first
statement is deleted; the paragraph now opens directly with its own content,
the two transport assumptions ("Two further transport assumptions" → "Two
transport assumptions"). The not-testable disclosure survives at the bracket
site ("No termination-reason field exists in the ingested data … a bracketing
parameter rather than an estimate").

**(a3) §VIII.A Status: cyclical-floor recap compressed to a pointer
(−≈115w).** The Status paragraph restated the full κ-grid read-out (+7.1 to
+9.4, 85.0\%, 98.0\%, $5.29B) that already appears, verbatim and gated, in
§V.B, the Table 7 notes, and Appendix M. Gate #(floor-cyclical) literals are
corpus-wide presence booleans ("85.0\%" etc. remain ×2 in corpus); the
replacement sentence keeps the status-inventory function and the corrected
reading ("floor dispersion under the hard maximum rather than cyclicality").

Not executed although candidate-adjacent: the four VIII.A limitation blocks
(Housing supply / Distributional / Sample scale / Data) are pin-free but
already near-minimal — each sentence is a distinct disclosure; cutting there
buys ~40w at real hedge risk. Reconciliation with the closing session's noted
residuals: the "~150w B08 trim" is (a1) in full; of the "~390w VIII trim",
(a3) takes the ~115w that is zero-risk, and the remainder is deliberately
*not* tier (a) — the envelope third-statement needs a documented gate re-sync
(→ b5) and the freeze-items are content deletions (→ c5).

---

## 2. Tier (b) — structural options (recommendations only, not landed)

Ranked by (page yield ÷ risk). "Relocate" means: move within the gated corpus
(manuscript online appendix or `replication_appendices.tex`), byte-preserving
pinned spans, per the batch-5/closing-session precedent — most gates are
corpus-wide presence/count checks and survive relocation; the known hazards
are the two ginnie mutant-ORDER tests (occurrence order across the corpus) and
any region-scoped gate, so each move needs the standard clone-run before
landing.

**(b1) Table 8 + its notes → online appendix (≈2pp main text).** The
12-rung inference ladder and its ~700w of notes (Bell–McCaffrey df, Webb vs
Rademacher coincidence mechanics, censored-rung accounting) are apparatus for
one number the text already carries three times (+2.9 to +8.7, Webb wild-t,
binding). Keep in main text: the one-sentence binding-layer statement + the
CR2/Bell–McCaffrey companion sentence (§V.E already carries both). Lost from
the main text: nothing — relocation. Gates: fewcluster/#125 spans and the
Table-8-notes pins are presence-based; re-sync risk LOW-MEDIUM. **Risk:
LOW-MEDIUM. Yield: ~2 local pp.**

**(b2) Table 1 cell compression (≈1.5pp).** The Uncertainty/bounds cells of
the Production-ABM, Danish, and household-side rows are 120–180-word essays
duplicating §VII.C, §VI.D and §VI.C. Compress each cell to the two or three
governing figures + exhibit pointer. This is the paper's front door; the
panel reads it first. Cells carry pinned spans (e.g. `null_floor_interval`
row), so this is a *rewrite* with per-cell pin preservation, batch-6 style.
**Risk: MEDIUM. Yield: ~1.5 local pp, disproportionate readability gain.**

**(b3) Notes-to-Table-7 "Calibration entries … moved out of the table body"
paragraph + the headline-marginal cell (≈1pp).** The cell currently holds a
~250-word parenthetical ladder; the catalogued variants (Fannie read,
form/transform, overlays, PSA span, attenuation triple) all restate Table 4
rows or §VII.F text. Compress cell to binding interval + calibration range +
"catalogued in Table 4"; relocate the catalogue paragraph to the online
appendix. **Risk: MEDIUM (dense pins, but relocation not rewording). Yield:
~1 local pp.**

**(b4) VII.B settlement-kernel arithmetic + VII.E demonstration-runs detail →
appendix (≈0.7pp).** Keep: both shifted-benchmark numbers ($722.7B/$739.4B),
the retention rationale, the curtailment identity + the Danish-scaling
*withdrawal* (a disclosure; stays). Relocate: the $42.0/$6.8/$23.4/$16.6B
edge accounting and the seasonal/regime-split/two-servicer demonstration
runs. `settlement_months_benchmark` / `realized_boundary_allocation` have
count-2 test asserts — relocation within the corpus preserves counts.
**Risk: MEDIUM. Yield: ~0.7 local pp.**

**(b5) Third statements of twice-said things (≈0.6pp total, several small
moves):**
- Fannie envelope caveat: stated in §V.C, Table 7 notes, *and* §VIII.A Model.
  Cut the VIII.A instance; needs one documented gate re-sync (the literal
  "whose envelope gate is " lives only there; the disclosure survives at two
  sites). Risk MEDIUM.
- Ablation list (burnout/FICO-LTV/delinquency): stated in §V.F, §VI intro,
  §VIII. The §VI-intro instance carries the unique dollar figures
  ($6.58B/$3.48B) — keep those, drop the repeated point-figures; or point VI
  at V.F. Risk MEDIUM (the VIII instance is 12-pin dense; leave it).
- §V.E fourth qualification's ~120w restatement of III.B's
  withdraw-the-presentation passage → compress to one sentence + pointer.
  Risk MEDIUM-HIGH (the "doubly conditional coincidence" family may be
  pinned; check before drafting).
- §V.B's two Graybill corroboration statements (mixture ¶ and
  import-consequences ¶) → one. ~50w. Risk MEDIUM.

**(b6) VI.B cap-grid mechanics → appendix (≈0.4pp).** Keep the implied-cap
numbers and the "observable is near-degenerate" verdict; relocate the
two-populations-two-grains machinery. `state_contingent_cap_grid` citation is
test-enforced — relocation preserves it. Risk MEDIUM.

Tier (b) total if all landed: **≈ 5.5–6.5 local pp ≈ 3,300–4,000 words.**

---

## 3. Tier (c) — content deletions (Eugene's call; none recommended
unilaterally)

Each deletes measured results, qualifications, or robustness entries — the
never-delete-a-disclosure rule means every one of these is an authorial scope
decision with gate retirements to document.

**(c1) §V.E E13 assembly prose → Table 4 carries the assembly (≈1,200–1,500w
≈ 3pp).** The seventh qualification's prose "lines up" what Table 4 already
tabulates; its 54 pins and 15 run tags would need mass re-pointing at the
table. Biggest single win in the paper; also its highest-risk edit (the
batch-6 audit certified ~1,650w as the compression floor *for the prose as
retained* — going below means the table replaces the prose, a different
paper-architecture decision). The v20-companions VERBATIM sentences and the
fewcluster sentence must survive wherever the prose lands.

**(c2) §V.D episode-gradient forensics (≈500–700w ≈ 1.5pp).** Keep the
gradient, the standardized +3.44, the interval-covers verdict; delete the
age-band sub-analysis and pre-commitment post-mortems. Deletes real
adjudication history (R32 work).

**(c3) §VII.F transportable-lesson + depth-ladder-shape (≈650w ≈ 1.3pp).**
The "portable device" essay and the 2018-ladder shape test. Methods-essay
material a field journal might value and an empirical referee might cut.

**(c4) §VI.D upper-anchor apparatus (≈350w).** The realized-implied +$1,212B
anchor discussion and the IRC/tax-code directional-bracket reading. Both are
disclosures about a bracketing case, not the production estimate.

**(c5) §VIII.A Status freeze-items (ii)+(iv) + the what-remains-open list
(≈200w).** Submission-process bookkeeping ((ii) build hygiene, (iv) golden
fixture) vs. genuine integrity disclosures ((i) mixed spec labels, (iii) the
claims-versus-code audit — keep those two regardless).

**(c6) Second estimator's extension inventory in §IV.A (≈150w).** The
three-extension bridge is already figure-carried (Fig. 4); prose could state
only the artifact verdict. Gate #100's 8 pins sit in the section lead, not
here, but the stage numbers are gated — check first.

Tier (c) total if all taken: **≈ 3,000–3,500 words ≈ 6–7 local pp.**

---

## 4. Cross-section redundancy register (fresh-eyes findings)

Executed: (a1) footnote-vs-body; (a2) mapping assumption ×2 in §V.B; (a3)
cyclical-floor ×4 → ×3 canonical sites. Remaining, catalogued for tiers
(b5)/(c): envelope caveat ×3; ablation list ×3; withdraw-the-presentation ×2;
Graybill ×2-in-V.B (+II, +V.E pointer — those two are fine); Fonseca–Liu
anchor ×3 (V.B, V.E-q6, E13 — E13's is the assembly's by design);
censoring-shares (68.8/35.8/36.3) in V.E-q1 *and* E13 (~80w; E13 needs them
for the one-mechanism-read-twice argument — defensible); "null also peaks at
lag −3 / timing carries no credential" ×5 sites (V.B, V.E-q2, V.F, Table 9
notes, VII.C) — V.F's instance is gate-pinned ('Timing alone', 'defined and
bounded once'); at most one of the others could go.

**Two flags, no edit made (meaning-changing; Eugene's call):**
1. Conclusion opening (¶2 of §VIII): "This paper's central empirical finding,
   established in Section V **under the synthetic household population
   specified in Section III**, is the rate-inelastic decomposition" — the
   qualifier belongs to the *contrast* (as the closing paragraph correctly
   has it), not to the decomposition, which is established on real Freddie
   data. Reads as a drafting slip; a referee will trip on it.
2. In the built main text, Tables 4, 5, 6, 8, 9 float *after* the references
   (pp. 93–97). Referees notice. A `\FloatBarrier` before the bibliography
   (or endfloat discipline) fixes it at zero word cost but repaginates — do
   it together with whatever tier-(b) set lands.

---

## 5. Page arithmetic toward the panel's ≤50pp

Conversion: local engine ≈ 1.17× cloud pages (closing-session ruler).

| State | Main text (local) | ≈ Cloud |
|---|---|---|
| At review start | 97pp / ≈46.6k words | ≈83pp |
| After tier (a) (landed) | 97pp / ≈46.3k words (boundary unchanged) | ≈83pp |
| + full tier (b) | ≈90–91pp | ≈77–78pp |
| + full tier (c) | ≈84–85pp | ≈72pp |

The EIC's ≤45–50pp implies ≈28–30k words. After (a)+(b)+(c) the main text
sits ≈42k words / ≈72 cloud pp. **The remaining ~12–14k words to target are
not reachable by cuts that respect the pinned-disclosure floor** — the
Phase-3b batches already certified per-section floors (E13, R31/R34, D21 each
audited infeasible below their landed lengths). The honest statement to the
panel is the one already in the response letter: the compression floor is set
by the disclosure apparatus. If ≤50pp is a hard constraint, the remaining
instrument is structural, not editorial — a companion-paper split (V.E/VII.F
inference apparatus as a methods companion, or the Danish counterfactual as a
standalone note), which is a publication-strategy decision, not a cut.

---

## 6. ADDENDUM 2026-08-05 — tier (b) EXECUTED on "continue"

Landed (both variants, opus-inline-drafted, workflow-refuted by 4 group
refuters + a completeness critic, 2 blocking + 8 advisory findings all
applied):

- **b1 ✓** tab:ladder + its notes → app:floormech, byte-identical, with the
  receiving appendix's scope sentence extended per the critic.
- **b3 ✓** the headline-row calibration catalogue (Table 7 notes tail) →
  app:floormech as a \paragraph; the headline cell's what-it-prices
  parenthetical compressed with the read-to-read exclusion restored as an
  appended notes sentence (the refuter caught that the cut deleted its only
  corpus instance).
- **b2 partial ✓** Table 1: Production-ABM and household-side cells
  compressed (the Danish cell is pinned wall-to-wall — 9 gate spans — and
  was left whole). Refuters corrected two defects in my own compression:
  the 5.7–6.3\% run-rate share had been mis-scoped onto the bracket counts
  (it belongs to the grossed $s=1$ bound), and the same-households
  non-additivity rationale had been dropped corpus-wide.
- **b4 half ✓** VII.E curtailment demonstration runs → app:params (lead-in
  anchored to the VII.E identity per the refuter). **The VII.B settlement-edge
  relocation was REVERTED by gate design:** gate #121 asserts the cap-only
  \$42.0B account *leads* the both-legs direction sentence in reading order
  (`cap_only_leads`), and its `why_asymmetric` span is byte-pinned — the gate
  is not stale; it encodes intended presentation. Reverted, not re-synced.
- **b5 partial ✓** V.E fourth-qualification withdraw-restatement compressed
  to a pointer — and the refuter exposed a pre-existing defect: the
  "Section III.B itself judges the less faithful" attribution was STALE
  (III.B never made the judgment; git pickaxe confirms). The judgment is now
  stated once, in III.B, at the unpinned allocation-contrast sentence.
  Graybill dedup landed with the transitive object restored. The
  **envelope third-statement dedup is withdrawn from the menu**: gate #67
  pins the 11.06-width disclosure at five contextful sites by design ("no
  site can be deleted behind the others" — the conclusion clause was the
  round-20 relabel's point).
- **Float fix ✓** \clearpage before the bibliography: Tables 4–9 no longer
  trail the references (References now open p. 90).
- Skipped by judgment: b6 (VI.B cap-grid — pinned and panel-central EIC-Q5
  content) and the ablation-list dedup (pin-dense at 2 of 3 sites).

**State after (a)+(b):** main text ≈44.9k words (program convention;
−~1.7k today), built **95pp local main text** (banner p. 96), documents
139/140/13pp, 0-undefined; editions clean at the pinned counts
{24/13/8/2/42}; split recut 1–95 / 96–139; 128/128 gates, 1,109 tests,
green at every group boundary. Cloud-equivalent ≈ 81pp. The §5 arithmetic
otherwise stands: what remains of (b) is ~1pp of small dedups; the distance
to ≤50pp cloud is tier (c) plus, decisively, the companion-paper split.

## 7. ADDENDUM 2026-08-05 (2) — re-review verdict + small-fix batch

Five-seat re-review of the 95pp build (personas pinned from v19): **MINOR
REVISION, panel mean 73.8** (v19: Major, 68.1); DA closed 4/5 CRITICALs, C5
partial, zero new CRITICALs. Package: `~/Downloads/revised_paper_v20_REREVIEW.md`
(+ uncommitted worktree copy). The panel's verified small fixes are LANDED
(this addendum's commit): abstract "up to roughly half … upper bounds by
construction" + the cost sentence's third condition (zero-refinance edge;
closes DA-C5; abstract 229→244w, letter + gate #101 + test battery re-synced);
the conclusion-thesis garble repaired (real-Freddie-data attribution; the
any-rate-response clause moved back onto the caps claim); "falls
disproportionately" matching the measured tilt; 9 stale `sec:pathb` references
retargeted to `app:params`/`sec:abm-danish` for the relocated
buyback-incidence material; the standalone document's banner now carries the
manuscript's real title; Table 7's null row gains the [80.6, 88.4]\%
propagated interval; the deferred floats are flushed adjacent to §V.E/V.F
(Tables at pp. 49–53; main text 96pp, banner p. 97, split recut 1–96/97–140;
cost: +1 page); tex2md's longtable-caption and orphaned-brace leaks fixed
(editions clean, 0 residual). **NOT landed — the round's one MAJOR (N1),
which is an authorial spec adjudication:** §V.E's 94.3/95.1 coverage defense
belongs to the restricted-inversion rung; the quoted plain Webb wild-t
[+2.9, +8.7] covers 90.84/91.42 in `fewcluster_coverage_results.json`, below
SPEC_V20_C §3's pre-committed ≥93.0 Gaussian bar, and gate #125's
`branch_L1` does not implement the spec's §4 live tie. The spec's own L2
landing would move the quoted binding interval; the alternative is an
explicit adjudicated deviation in the verdict ledger. Either way the choice
is Eugene's and is recorded here rather than taken.

**Pointer added 2026-09-05.** That choice was made: N1 landed the same day under the frozen rule — `specs/RECORD_v20_N1_relanding.md` §4 ("EXECUTED (2026-08-05, same day, single batch)") — carrying the quoted binding interval to `[+2.3, +9.1]`. FP2 Batch B then decensored the lower endpoint on 2026-08-29 and the binding interval has read **`[+1.9, +9.1]`** since (`specs/RECORD_fresh_panel2_batchB.md`), with Webb's `[+2.8, +8.7]` reported beside it. Every `[+2.9, +8.7]` above is therefore historical.

## 8. Verification log for the landed trims

- Pin scan: AST string-literal extraction over `tools/liveness_gates.py` +
  `tests/*.py` (7,541 literals ≥10 chars); zero literals intersect any
  deleted span; the a3 replacement re-checked for corpus counts
  ("85.0\%"/"98.0\%"/"5.29"/"+7.1"/"+9.4" all remain ≥2×).
- `python3 tools/liveness_gates.py`: 128/128 PASS.
- `python3 -m pytest tests/ -q`: 1,109 passed.
- tectonic builds (local engine): canonical 140pp, long-abstract 141pp,
  replication_appendices 13pp; all logs 0 undefined.
- Editions: tex2md hard self-checks OK with counts
  {tables 24, figures 13, equations 8, footnotes 2, headings 42}; md2txt OK.
- Split re-cut from the fresh build: main text 1–97, online appendix 98–140
  (banner verified on the cut's first page); artifact set refreshed in
  `paper/v18/build_split/` (untracked, per convention).
