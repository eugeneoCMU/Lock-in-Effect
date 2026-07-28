# Score-improvement plan — panel dimensions → proposals, 2026-07-28

Companion to REREVIEW_v18_panel_2026-07-28.md and PLAN_v18_fixes_2026-07-28.md. Produced by a 12-agent propose+verify workflow: one proposer per rubric dimension (originality 66.3/20%, rigor 67.3/25%, evidence 73.3/25%, coherence 67.5/15%, writing 63.5/15%, plus EIC venue-fit 45 unweighted), each paired with an adversarial feasibility checker that verified every proposal's premise against the manuscript, its cost-class honesty, its collisions with standing decisions, and the plausibility of score impact. 39 proposals; 35 survived (14 keep, 21 amend), 4 killed on false premises or implausible impact. The coordinating session independently re-verified the load-bearing premises against the tex before this document was written (L96 "Two features separate my exercise"; zero contributions-enumeration language manuscript-wide; L102 "one validation strategy among several"; L194's 13.6% with no counterweight in-paragraph; L57 and L378 still calling calibration "the operative uncertainty"; L86's graybill2026 sole citation with its dangling sec:pathb pointer; L43 at 633 words / 13 parentheticals; L736–737 newpage+appendix with the bibliography at L1346–47; L431's three-primary-estimators tablenote).

## Legend and execution constraints

- **cost_class:** *wording* (executable under the frozen-content rules; zero numbers/hedges/claims change) · *structural* (moves/adds exhibits or paragraphs, results frozen) · *run* (needs a pre-committed run, spec-before-run) · *posture* (changes what the paper claims — Eugene's call only) · *external* (needs data/verification outside the repo).
- **Sequencing, non-negotiable:** the re-review's queued repairs NEW-1..NEW-6 land FIRST (several proposals below share commits or line-number anchors with them). Any edit near headline literals or gate-pinned spans = tex+gates+tests+letter in ONE commit. Any line-count change = regenerate the long-abstract variant. Zero-slack recount after every batch. Nothing in this file changes a number or a hedge scope unless it is marked posture.

## Priority index

| # | Dimension | Priority | Cost | Verdict | Proposal |
|---|---|---|---|---|---|
| 1 | Rigor | HIGH | run | keep | Pre-commit B5's manuscript disposition before the joint-cell run executes |
| 2 | Evidence | HIGH | structural | amend | Give the Fannie replication an exhibit: tab:estimators row + Freddie-vs-Fannie table in V.B |
| 3 | Evidence | HIGH | wording | keep | Make the 51% coverage statement lead with the quantified bound, not the gap |
| 4 | Evidence | HIGH | wording | keep | Redeem the Graybill pointer at the elasticity's defense sites (tex 280, 365) |
| 5 | Originality | HIGH | structural | amend | Complete the §II differentiation paragraph: two separations → the full panel-credited set |
| 6 | Originality | HIGH | structural | amend | Add an affirmative contributions paragraph to §I (the manuscript has none) |
| 7 | Originality | HIGH | posture | amend | Claim the cross-design/symmetric-companion pair as a methodological contribution |
| 8 | Coherence | HIGH | structural | amend | Split §I's results paragraph (tex 43) into claim-then-qualification blocks at three seams |
| 9 | Coherence | HIGH | wording | keep | Give §V's opening levels contrast (tex 194) the cross-design counterweight |
| 10 | Coherence | HIGH | wording | amend | Repair the two stale three-layer hierarchy summaries (tex 57, 378) |
| 11 | Writing | HIGH | wording | amend | Unstack the abstract's interval sentence, word-count-neutral |
| 12 | Writing | HIGH | wording | amend | Give "floor read" a referent at first abstract use |
| 13 | Writing | HIGH | structural | amend | Break the L43 monolith into four paragraphs; footnote its two heaviest parentheticals |
| 14 | Structure | HIGH | structural | amend | Wave 2b move #1: Path A estimation detail (V.D) → Online Appendix |
| 15 | Structure | HIGH | structural | amend | Ship the Online Appendix as a separate PDF (split point at L736) |
| 16 | Structure | HIGH | structural | keep | One-page "How to read this paper" guide in the front matter, pointer-only |
| 17 | Rigor | MEDIUM | structural | amend | Inference ladder as an exhibit + the unsurfaced cluster-leverage diagnostic |
| 18 | Rigor | MEDIUM | wording | amend | Replace tab:verdicts' binary taxonomy with three categories |
| 19 | Rigor | MEDIUM | wording | keep | Move the Graybill corroboration to the point of use (tex 245, 621) |
| 20 | Evidence | MEDIUM | wording | amend | Assemble the floor's measurement stack where the floor is defined (tex 80) |
| 21 | Evidence | MEDIUM | run | amend | 2022-vintage exclusion: proxy bound → direct simulation on the staged Fannie ingest |
| 22 | Originality | MEDIUM | wording | amend | Foreground the design-crossing pair in the methodological-positioning paragraph (L102) |
| 23 | Originality | MEDIUM | wording | keep | Add a what-this-paper-adds sentence to §II's Danish paragraph (L98) |
| 24 | Coherence | MEDIUM | structural | amend | Give §V.E's seventh-qualification assembly (tex 369) a compact table form |
| 25 | Coherence | MEDIUM | wording | keep | Promote the SMD two-moment infeasibility into §IV's Interpretation (tex 188) |
| 26 | Writing | MEDIUM | wording | amend | Extend the round-26 wording protocol to the appendices (tex 739–1349) |
| 27 | Writing | MEDIUM | structural | keep | Diet the fig:gapsweep caption (260 words) to ~90 words + a Notes block |
| 28 | Structure | MEDIUM | structural | amend | Wave 2b move #2: three orphan diagnostic exhibits with ≤1 caller each |
| 29 | Structure | MEDIUM | posture | keep | Split the Calibration Box (VII.F) — the block the EIC actually named |
| 30 | Structure | MEDIUM | posture | keep | Submission-variant short abstract via the existing variant machinery |
| 31 | Rigor | LOW | wording | keep | Name the SMD two-moment infeasibility in §IV's verdict paragraph |
| 32 | Evidence | LOW | wording | amend | Anchor the conclusion's "mostly mechanical" claim to its external evidence (tex 720) |
| 33 | Originality | LOW | wording | amend | Reframe the expectations complement's introduction from patch-note voice (L136) |
| 34 | Coherence | LOW | structural | keep | Split the conclusion's opening mega-paragraph (tex 714) at two seams |
| 35 | Writing | LOW | posture | keep | One paragraph break inside the abstract |

---

## Rigor (25%)

67.3/100; R1 gave 58. The panel's three named residuals: no outcome-holdout months exist anywhere, the never-run B5 joint cell, and verdict adjudication that is post-hoc in both directions.

### 1. Pre-commit B5's manuscript disposition BEFORE the queued joint-cell run executes

**Priority HIGH / Cost run / Verdict keep.**

**What.** The B5 run (Ginnie overlay × age-standardized 5.51% floor) is queued with a committed spec; what is NOT yet committed is what happens to the manuscript under each outcome. Extend the spec with an ex-ante landing rule, MOVES-style like the 0.5pp interval rule that governed floor_inference_correction: (i) if the composed marginal falls within the pre-stated ±1pp of the projected ~+3.0 (the interaction convention of concave_additive_marginal), it lands as the composed lower member at the four disclosure sites and the seventh-qualification list re-closes around it; (ii) if outside, a named escalation (e.g. the +5.6 abstract mention acquires the panel's alternative remedy) — decided now, not after the number is seen; (iii) tab:verdicts gains a row whose "Rule as committed" column is written and committed before execution, making it the table's first prospectively-enforced entry. Pre-decide the abstract +5.6 disposition (tex 30, "Inside that range, +5.6 points… is the value at the calibration I headline") under each branch.

**Where.** Landing sites verified: tex 255 ("have never been run against each other; I report them separately and give no composed point"), tex 369 ("a composition neither run establishes, would put the marginal near +3.0… I report no composed point"), tex 660 ("I have not run them jointly… I do not report that composition as an estimate"), headline-table row tex 392 ("never run jointly with it, so no composed point is reported"), verdict row tex 1334 ("Enforced: no composed point is reported anywhere"), abstract tex 30.

**Rationale.** Two of the panel's three named rigor residuals are the never-run B5 cell and post-hoc adjudication in both directions. Running B5 discharges the first; running it under a fully ex-ante disposition rule discharges an instance of the second — the newest adjudication becomes the first one a referee can verify was written before the outcome existed. Without the landing rule, executing B5 actually WORSENS the adjudication complaint: a fifth number would arrive and be dispositioned after the fact. The gate-pinned "no composed point is reported anywhere" span (tex 1334) makes silent landing impossible anyway — the rule converts that constraint into displayed rigor.

**Collisions.** Builds on the ALREADY-QUEUED B5 run — this is the protocol layer, not a re-proposal. Landing a composed point flips the gate-pinned "no composed point" spans at tex 255/369/392/660/1334 simultaneously (gate #104 battery mutates all occurrences); branch (ii) touches the abstract (+5.6 is inside ABSTRACT_POSTURE's neighborhood, gate #99, letter word-count recount) — the abstract branch is a posture call and must be Eugene's, taken at spec time.

**Checker: premise verified** — every cited "no composed point" span exists verbatim (tex 30, 255, 369, 392, 660, 1328, 1334 read in full); PLAN B5 confirms the queued spec pre-commits the ~+3.0 expectation and the ±1pp convention but commits NO manuscript disposition, with the abstract remedy explicitly parked as Eugene's; the 0.5pp MOVES precedent (verdicts row tex 1328) is real; HANDOFF_round26 §3 confirms the gate #104 battery, the zero-slack recount and gate #101's letter recount; REVIEW lines 41 and 69 confirm the post-hoc-adjudication residual and the "genuinely never-run cell".

### 17. Give the inference ladder exhibit status: percentile / CR2 / CR3 / wild-t in one small table, plus the unsurfaced cluster-leverage diagnostic

**Priority MEDIUM / Cost structural / Verdict amend.**

**What.** Add a four-row mini-table (layer; interval; clusters/df; status — "under-covers, demoted" / "secondary" / "secondary" / "binding") in §VII robustness-floor next to the derivation, and surface the max-single-cluster-leverage 0.33 diagnostic recorded in the committed floor_inference_correction artifact as one sentence in the tex 399 tablenote ("31 carry the floor read… no single cluster's removal moves the read by more than a third of its spread", per the artifact's own field). No new run: CR2 (+3.0 to +8.6) and CR3 (+2.8 to +8.8) are already quoted in-text at tex 660; the leverage number is a landed-artifact field never surfaced (grep "leverage" = 0 hits file-wide).

**Where.** Tex 660 (the entire ladder currently lives in one parenthetical inside the manuscript's densest paragraph: "CR2/CR3 t-intervals and a Rademacher wild-cluster bootstrap-t… CR2 +3.0 to +8.6, CR3 +2.8 to +8.8"); tablenote tex 399 (names CR2/CR3 but quotes no numbers and no leverage); tab:headline row tex 392 (quotes only wild-t and percentile).

**Rationale.** R1's 58 was driven by the interval's inferential status. The fix is executed and MOVES was honored — but a re-scoring referee has to excavate it from a 30-line paragraph to learn that all three corrections agree, the lower edge stays above zero on every corrected read, and no single cluster drives the 31-cluster read. Rigor scores are assigned on what is legible, and the few-cluster concern is exactly the residual R1 would probe next ("31 clusters — is one cluster carrying it?"). The leverage sentence answers a question the paper currently leaves open despite having already computed the answer.

**Collisions.** Re-quoting [+2.8,+8.7] or [+3.0,+8.0] in a new exhibit moves the zero-slack counts (×7 binding; ×5 demoted, "do not grow" per HANDOFF_round26 §3) — tex+gates+tests+letter in one commit, gates #98/#99-adjacent. Cheaper variant that avoids the literal collision: quote only CR2/CR3 (unpinned) and the leverage figure in the tablenote, referencing the binding interval without restating it.

**Checker amendment.** Execute the proposal's own "cheaper variant" as the primary form: add CR2 (+3.0 to +8.6), CR3 (+2.8 to +8.8) — unpinned literals, grep-verified absent from the zero-slack list — to the tex 399 tablenote, referencing the binding wild-t interval without restating it. The leverage sentence is conditional: first open the floor_inference_correction artifact, confirm the field exists, and quote its own name and definition; do not land the "removal moves the read by no more than a third of its spread" gloss unless the artifact computes a leave-one-out delta, which "leverage" does not imply — leverage is an influence weight, not a leave-one-out delta measured in units of the interval's spread, and landing that sentence as drafted risks a false quantitative claim in the headline tablenote. The four-row mini-table is a second step only if Eugene accepts the zero-slack recount (tex+gates+tests+letter in one commit, gates #98/#99 adjacency).

### 18. Replace tab:verdicts' binary taxonomy with three categories; the mislabeled seasonal row is evidence the binary cannot classify its own contents

**Priority MEDIUM / Cost wording / Verdict amend.**

**What.** Beyond the queued NEW-4 one-row relabel: redefine the caption's legend (tex 1317) from the binary ("Enforced" vs "every other entry is a post-run judgment") to three classes — (1) Enforced: rule applied as written and the verdict follows from the rule; (2) Pass upheld, claim withheld: rule met as written, the pass reported, and the claim then discounted on post-run diagnostics, direction stated; (3) Post-run reinterpretation/supersession. Rows 1326 (27-cell positivity "Pass weakened"), 1327 (Fannie envelope "Pass weakened") and 1333 (seasonal timing, currently mislabeled "Enforced") all belong to class 2 — three of sixteen rows describe the identical mode the binary has no name for, which is why the mislabel happened.

**Where.** Caption tex 1317 ("'Enforced' means the committed rule was applied exactly as written; every other entry is a post-run judgment"); rows tex 1326, 1327 ("Pass weakened…"), 1333 ("Enforced: monthly timing conceded, levels only"); body tex 1274 ("That rule is met as written by both seasonal legs… I nonetheless claim nothing from the pass, because five diagnostics computed afterwards show the rule cannot discriminate").

**Rationale.** The audit table exists to answer the DA's post-hoc-adjudication charge; a taxonomy that misclassifies its own rows undercuts exactly the property the exhibit certifies. Naming "pass upheld, claim withheld" as a first-class category turns the paper's most distinctive adjudication behavior — refusing to claim from passes its own diagnostics discredit, always against interest — from an unclassifiable anomaly into displayed method. A rigor scorer reading the corrected table sees 3/16 rows of conservative discretion labeled as such, rather than one row contradicting the caption. Strictly more responsive than the queued single-row fix, and costs three labels and a caption.

**Collisions.** Gate #104 pins tab:verdicts spans and its battery mutates all occurrences — caption + row-label edits need gates/tests updated in the same commit. Row 1327 contains the zero-slack "11.06" literal (×5): relabel the category word only, do not touch the interval clause. No claim strength changes; direction tags all survive.

**Checker amendment.** Demote to priority LOW and execute only as a rider on the NEW-4 commit (one gate #104 battery touch instead of two). Correct the framing: the binary's catch-all absorbs rows 1326/1327 (both are correctly labeled under "every other entry is a post-run judgment, with its direction stated"); what lacks a name is specifically "rule enforced, pass reported, claim withheld", which is why row 1333 got the "Enforced" label. Relabel the category word only on rows 1326/1327/1333 — row 1327's "11.06-point envelope" clause is a zero-slack literal (×5 per HANDOFF §3) and must not be touched. Caption gains the third class definition; all direction tags survive unchanged. After NEW-4's minimal relabel the table is already self-consistent, so the incremental referee movement is small (the re-review rated the finding Minor and B7 FULLY_ADDRESSED otherwise) — not a kill, because naming the enforced-pass-then-claim-withheld mode is a genuine legibility gain in the exhibit whose whole point is adjudication accuracy.

### 19. Move the Graybill transaction-data corroboration to the point of use; the lit-review's forward pointer currently dangles

**Priority MEDIUM / Cost wording / Verdict keep.**

**What.** graybill2026 (independent 7–11%/pp sale-hazard response from transaction records, no credit-record overlap) is cited exactly once, in the lit review at tex 86, ending with a promise — "(Section~\ref{sec:pathb})" — that §III/Path B never redeems (grep: one occurrence file-wide). Add one cite sentence at each elasticity-discipline site: (i) tex 245, the moving-share bracket, where Graybill is maximally probative because their estimand IS the moving margin — the s-component the bracket varies — so the s=1 production convention's downside bracket is corroborated externally on the very hazard component in question; (ii) tex 621, where the paper concedes "the band's lower edge is a literature boundary rather than an evidential one" — it can now add that the band's location (though not its lower edge) is independently corroborated from data that never touch credit records, while keeping the in-sample non-rejection sentence untouched.

**Where.** Tex 86 (sole cite, dangling pointer to sec:pathb); tex 245 (moving-share bracket paragraph, "s is a bracketing parameter rather than an estimate"); tex 621 (band-extension paragraph feeding tab:lowband at tex 623–648).

**Rationale.** The DA-C2 core ("the elasticity is one paper's specification range, and the paper's own data cannot find it") is the elasticity residual the queued items do not touch. The corroboration already sits in the manuscript — quarantined where a rigor scorer reads context, absent where they read method. One sentence at the point of use converts "imported from a single paper" into "imported and independently corroborated on the moving margin", at zero run cost and zero result change; it also repairs a broken forward promise a careful referee will notice. Scope discipline: it corroborates the band's location, not the in-sample non-rejection — the sentence must not soften "cannot reject zero", which stays as written.

**Collisions.** Tex 621/245 paragraphs carry gate #102 spans (band_low_extension / moving_share_bracket exhibits) — screen insertions against the pinned spans; no zero-slack literals involved. Quoting Graybill's 7–11%/pp is external-source content, not a repo result, so results-frozen is not implicated.

**Checker: premise verified** — grep confirms graybill2026 appears exactly once file-wide at tex 86, in a sentence ending "(Section~\ref{sec:pathb})" that §III never redeems; tex 245's "s is a bracketing parameter rather than an estimate" and tex 621's "literature boundary" / "cannot reject zero" both read in full; HANDOFF §1 confirms gate #102 covers the elasticity exhibits; PLAN B9 confirms graybill2026 verified against FRB Philadelphia WP 26-33. Cost "wording" is honest narrowly, because the proposal itself fences the one way it could become posture (corroborate the band's LOCATION only).

### 31. Name the SMD two-moment infeasibility in §IV's verdict paragraph as the falsification the recalibration parameter cannot rescue

**Priority LOW / Cost wording / Verdict keep.**

**What.** Add one sentence to the §IV closing verdict paragraph (tex 188), after the cross-design either-or and before the hand-off to sec:hazard: the simulated-minimum-distance two-parameter fit (tex 595) returns joint infeasibility with the verdict vocabulary fixed before execution, and its near-fit overshoots the benchmark at 107.1% — a falsification that does not run through the free recalibration scale, unlike every other ABM leg. Point to the §VII paragraph rather than moving it (a move would grow §IV against B1 and risk the #100 order gate).

**Where.** Tex 188 (§IV verdict: currently cites only the scale-sensitivity replication from sec:robustness, never the SMD result); tex 595 (the SMD paragraph: "moment set, admissibility bands, distance, and verdict vocabulary all fixed before execution… The near-fit… recovers 107.1%"); ledger row tex 828.

**Rationale.** R3's rigor 63 rests on ABM validation, and the panel's own arbitration said the SMD infeasibility is "under-leveraged as the section's cleanest falsification" precisely because it is immune to the recalibration degree of freedom that qualifies the cross-design result. The sentence costs nothing, changes no result, and puts the strongest pre-committed ABM test where the reviewer who scores the ABM's rigor actually reads. Smallest mover on this list, but the only queued-item-free lever aimed at R3 rather than R1.

**Collisions.** Gate #100 asserts §IV order (cross-design-before-verdict): the sentence must be inserted inside the existing verdict paragraph without reordering, and tex 188's paragraph should be screened for pinned spans. 107.1% is not on the zero-slack list (appears tex 390, 595) but re-quoting it adds an occurrence — verify no presence-count gate tracks it before committing.

**Checker: premise verified** — tex 188 cites only "Section VII's scale-sensitivity replication" and never the SMD result; tex 595 matches verbatim; ledger row tex 828 exists; REVIEW line 64 quotes "under-leveraged as the section's cleanest falsification" verbatim and line 20 gives R3 rigor 63. One self-neutralized slip: "107.1" appears at three raw-tex lines (280, 390, 595), not two — but 280/390 are the [107.0, 107.1] bootstrap-interval endpoints, a different quantity, and the proposal's own instruction to verify presence-count gates before committing absorbs the miscount.

---

## Evidence (25%)

73.3/100, the highest core score; R1 is the low scorer at 66. The Data verdict (73) caps on direct coverage of ~51% of book face — "bounded rather than closed".

### 2. Give the Fannie replication an exhibit: a row in tab:estimators plus a compact Freddie-vs-Fannie table in Section V.B

**Priority HIGH / Cost structural / Verdict amend.**

**What.** Add a "Hazard Path B, Fannie Mae external replication" row to tab:estimators (central $821.0B / 107.4%, null 98.7%, marginal +8.68pp; path-correlation cells dashed with a note that the committed replication artifact carries headline statistics only, per the license posture stated at tex 295 and 743). Optionally add a 6-row two-column Freddie/Fannie table at the end of Section V.B: central, null, marginal ($B and pp), off-window floor read (5.19% vs 5.52%), sample construction (75k drawn from 17.6M / 24 quarters), max PSI 0.018. Every number is committed and already in prose; no run.

**Where.** tab:estimators rows at tex 421–427 (verified: benchmark, ABM, Path B, concave, Path A, two cross-design rows — no Fannie row); source paragraph tex 295; existing fragments at tex 70 (tab:headline uncertainty column), tex 398 (tab:uncertainty tablenote), tex 730 (limitations), tex 1193–1197 (app:composition panel b, online appendix).

**Rationale.** The panel's own "What's good" #3 is the 17.6M-loan same-pipeline replication landing 0.52 points from Freddie — and it is the only headline-adjacent evidence object with essentially no exhibit presence. tab:estimators is the table a scoring reviewer extracts; today it shows three estimators and two ABM variants but omits the paper's strongest external check. R1 (evidence 66, the low scorer) reads exhibits, not buried tablenotes; prominence proportional to weight is precisely what the dimension brief asks and is a pure re-presentation of committed values.

**Collisions.** tab:estimators tablenotes are inside the 316 gate-pinned-span checklist; do NOT quote the 11.06 envelope width in the new exhibit (zero-slack literal, exactly ×5) and keep 13.6%/60.2% counts untouched. A new exhibit grows main text against the B1 restructure direction (one small table; B1 wave 2b relocation is the open offset). Near headline literals, so tex+gates+tests in one commit, and the unsent letter's section 7 should gain the item (rides with queued NEW-5a).

**Checker amendment.** Add the Fannie row as proposed, but: (1) rewrite tablenote tex 431's opening enumeration ("three primary estimators and the two cross-design variants") in the same commit and screen it against the 316-span checklist — the current sentence becomes false with a sixth substantive row; (2) place null 98.7% and marginal +8.68pp in the Path-diagnostics column (the table has no null/marginal columns), dash the correlation cell with the license note (tex 295/743); (3) drop the "zero exhibit presence" framing — the accurate premise is absence from the extraction table (tab:estimators), while fragments exist at tex 70, 222, 398 and app:composition panel (b); the optional V.B table should cross-reference rather than duplicate panel (b)'s PSI rows. Do not quote the 11.06 envelope (×5 zero-slack) or the binding interval (×7) in the new exhibit; tex+gates+tests+letter (section 7, riding with NEW-5a) in one commit.

### 3. Make the 51% coverage statement lead with the quantified bound, not the gap

**Priority HIGH / Cost wording / Verdict keep.**

**What.** Rewrite the last sentence of the tab:headline caption from the unquantified pointer "Each exclusion is bounded by an external-speed overlay (Section V.B)" to state the bounds where the 51.0% is stated: the 20.4% Ginnie share bounded at $20–47B by published observed speeds (overlay-measured differential +$38.5B, inside the bound), the 33.7% out-of-window vintages at $11.7B (1.5% of benchmark) by observed Fannie cohort speeds, each signed toward overstating trapped liquidity. Echo one clause in the limitations Data paragraph (tex 728), which currently discloses only the 15-year exclusion while the coverage figure and its bounds sit in the separate Status paragraph (tex 732).

**Where.** tab:headline caption, tex 57 (verified: leads with the 33.7%/20.4%/51.0% netting, defers bounds to an unquantified final pointer); bound values verified at tex 253 ($20–47B Ginnie, $11.7B vintage, both signed conservative), tex 255 (+$38.5B overlay differential), tex 1188–1189 (tab:composition final column); tex 728 and 732 (limitations split).

**Rationale.** The panel's Data verdict (73) quotes exactly this: "direct coverage is ~51% of book face, bounded rather than closed." The underlying fact is stronger than its first presentation: every excluded segment carries a committed, external-data, signed bound totaling at most ~6–8% of benchmark, and both bounds are conservative in direction. A reviewer who meets 51.0% plus its dollar bounds in the same sentence scores a quantified-coverage design; one who meets 51.0% plus a pointer scores a hole. All numbers committed; zero new claims.

**Collisions.** The caption sits directly above gate-pinned tab:headline rows and the 51.0%/33.7%/20.4% spans are plausibly in the 316-span checklist — screen the edit against it and ship tex+gates+tests in one commit. Must not soften "bounded rather than closed": the bound statement stays a bound, not a closure claim (hedge scope preserved).

**Checker: premise verified** — tex 57's caption read in full, final sentence confirmed as an unquantified pointer; bound values and their signs confirmed at tex 253/255 and tabulated at raw tex 1188–1189 ("static bound $20--47B, overlay differential +$38.5B"; "vintage residual bound $11.7 billion"); the tex 728/732 limitations split is real; panel review line 40 gives Data 73 with "bounded rather than closed" verbatim.

### 4. Redeem the Graybill pointer: surface the transaction-data corroboration at the elasticity's defense sites

**Priority HIGH / Cost wording / Verdict keep.**

**What.** Section II's Graybill sentence (tex 86) ends "(Section~\ref{sec:pathb})" — but sec:pathb never mentions graybill2026. Add one sentence at the imported-elasticity defense paragraph (tex 280), after the fonseca2024 anchor: graybill2026's independent transaction-record estimate (sale hazard cut roughly 7–11% per pp of rate gap, housing-market-equilibrium setting, no credit-record overlap with either agency sample) spans the adopted 5.5–7.7% band from a third, methodologically disjoint pipeline. Extend the fifth qualification's clause at tex 365 from "with \citet{fonseca2024} as independent corroboration" to name both corroborating sources. Keep the framing as band corroboration, exactly as tex 86 already states it.

**Where.** tex 86 (verified: sole graybill2026 body citation, with a forward pointer to sec:pathb); tex 280 (verified: "the elasticity's evidential basis is the external literature alone", fonseca as the only out-of-band anchor); tex 365 (verified: fifth qualification names fonseca only); tex 621 (band_low_extension paragraph, optional third site).

**Rationale.** The imported elasticity is this dimension's most-attacked object (verified finding #7, CONFIRMED; DA C2: "measures nothing it did not put in by hand"). The paper already owns an independent corroboration from data that never touch credit records — added this round for exactly this fight — but it is quarantined in the literature review where no scoring reviewer weighs it. R1 and the DA form their evidence judgment at tex 280/365; a corroboration they never see there does zero work. This also repairs a dangling internal promise (tex 86 points to a section that is silent).

**Collisions.** "The elasticity's evidential basis is the external literature alone" is a load-bearing hedge span (gate #98/#102 neighborhood): Graybill IS external literature, so the added sentence preserves its scope, but the edit must be screened against the pinned-span checklist. Boundary: folding Graybill into the "adopted band is the conservative one" argument (tex 367) would strengthen a committed claim — that variant is posture, not wording, and is not what is proposed here.

**Checker: premise verified** — grep gives a single graybill2026 hit at line 86 with the unhonored forward pointer; tex 280's "external literature alone" hedge and fonseca-only anchor confirmed; tex 365's fifth qualification names fonseca only; tex 367 read as the posture boundary the proposal correctly quarantines; panel review line 68 (finding #7 CONFIRMED) and line 74 (DA C2 verbatim).

### 20. Assemble the floor's four-read measurement stack where the floor is defined

**Priority MEDIUM / Cost wording / Verdict amend.**

**What.** Add one to two sentences to the Definitions paragraph (tex 80), where the two floor calibrations are introduced, stating that the floor is a measured object with four independent realized-turnover reads — the in-window discount-cohort read (3.8–3.9%, flat across seasoning cuts), the off-window 2018-leg band (4.70–5.33%), the age-standardized read (5.51%), and the out-of-agency Fannie read (5.52%) — with the honest coda the paper already commits to: the two independent reads sit above the clean band, which is why the band's lower edge is the soft one and the headline is quoted off-window.

**Where.** tex 80 (verified: defines in-sample and off-window floor calibrations with no mention of their measurement basis or replications); the four reads verified at tex 652 (in-window 3.8–3.9% "flat across seasoning cuts"), tex 654–656 (2018 leg 4.70–5.33%), tex 352 (age-standardized 5.51% and Fannie 5.52%, "two independent lines… point to the same place"); null-defense sites at tex 30, 43, 96.

**Rationale.** The mechanical null carries 85.7% of the answer and rests entirely on the floor; the DA's residual attack (finding #9: the floor "embeds behavioral turnover") scores against evidence sufficiency. The paper's actual defense — the floor is measured several independent ways from realized turnover, including a second agency — exists but is assembled nowhere; a reader at the definitions site sees a calibrated constant. One compact stack statement converts "calibrated parameter" into "measured quantity with an out-of-agency replication" at the exact point every downstream null claim inherits it. Must include the reads-above-band concession to avoid cherry-picked agreement — which the paper already states at tex 352, so no posture change.

**Collisions.** The Definitions paragraph is dense with pinned definitional spans (floor calibrations, "trapped liquidity", marginal definition) — screen against the checklist. The added stack must carry the tex 352 concession (independent reads above the band bracket the marginal below +4.3) intact, or it becomes a strengthening edit and flips to posture.

**Checker amendment.** Recast the stack with the paper's own labels: the floor has realized-turnover reads at four sites — in-window 3.8–3.9% (flat across seasoning cuts), off-window 2018-leg band 4.70–5.33%, an imputation-heavy age-standardized read of 5.51% (84% imputed weight, indicative bound) and an independent out-of-agency Fannie read of 5.52% — of which the last two are the mutually independent pair (tex 352's committed phrasing). Do NOT claim "four independent realized-turnover reads": tex 660 calls the age-standardized read "an indicative bound rather than a measurement" and it derives from the 2018 leg, so it is not independent of read #2. Keep the concession intact (both independent lines sit above the clean band, so the band's lower edge is the soft one) but do not attach "which is why the headline is quoted off-window" to it — the off-window headline is motivated by the in-window calibration circularity already stated in the same paragraph. Screen every added sentence against the pinned definitional spans in tex 80. Without these fixes the edit strengthens the floor's evidential standing beyond commitments and flips to posture.

### 21. Convert the 2022-vintage coverage exclusion from proxy bound to direct simulation on the already-staged Fannie ingest

**Priority MEDIUM / Cost run / Verdict amend.**

**What.** A pre-committed segment run: Path B (committed floor, band and conventions) on the Fannie 2022-origination cohort — data already staged (the replication ingest spans acquisition quarters 2017Q1–2022Q4, tex 295) — reported as a bounding overlay on the 23.1%-of-face 2022 vintage, replacing the $11.7B observed-speed proxy with a modeled segment estimate. No headline change: the production universe stays 2017–2021; the deliverable is a tightened vintage bound and a defensible statement that direct or directly-simulated evidence now spans ~74% of book face (51.0 + 23.1).

**Where.** Exclusion and bound verified at tex 57 (caption: 2022 cohort 23.1% of face), tex 253 ("the vintage dimension carries no bound of either kind" until the observed-speed bound; 2022 vintage "originated near or above prevailing market rates"), tex 732 ("Replication alone could not retire the vintage residual"); data availability at tex 295 (24 quarters through 2022Q4, 17.6M loans).

**Rationale.** This is the only proposal that moves the underlying fact rather than its presentation: the Data score's stated cap is the 51% direct coverage, and the largest single exclusion is sitting on data the project has already ingested and staged. A modeled 2022-segment read also tests the paper's own qualitative claim that the 2022 cohort's lock-in state "differs qualitatively" — either way the vintage residual stops being proxy-only. Cost-classed honestly as a run, not external data.

**Collisions.** Spec-before-run discipline, and never mid-review-session. The 2017–2021 production universe is a standing design commitment — this must land as a bounding overlay, not a universe change (a universe change is posture). Coverage literals (51.0%, 23.1%, the $11.7B bound) would all need restatement across tex 57/253/732 with gates in the same commit. Operational note from the repo record: 2022 refi-wave quarters are ~5× staging size; the low-memory staging path exists.

**Checker amendment.** Keep the run, respec the deliverable: (1) report the segment result as a modeled bounding overlay BESIDE the retained $11.7B observed-speed bound (which is realized external data and stays at tex 253/732/1189), never as its replacement; (2) state coverage netted on the book's own agency × vintage joint cells — the increment is the conventional 2022 intersection only, not 23.1%, so compute it from the same joint-cell machinery that produced 51.0% rather than asserting ~74% (the "51.0 + 23.1" arithmetic double-counts the Ginnie × 2022 intersection, exactly the netting error tex 57's caption warns against); (3) the ex-ante spec must disclose the acquisition-window truncation (originations acquired after 2022Q4 absent — late-2022 originations acquired in 2023 are missing, mitigated by the SOMA 2022 face's H1 tilt at tex 253) and pre-commit the interpretation as a mechanically-dominated overlay, since the imported elasticity was estimated on locked-in negative-gap borrowers and this cohort sits near or above the money (tex 253's "differs qualitatively"); (4) spec-before-run, never mid-review-session, production universe unchanged, and every touched coverage literal at tex 57/253/732 ships with gates+tests in the same commit; use the low-memory staging path for the 5× refi-wave quarters.

### 32. Anchor the conclusion's "mostly mechanical" claim to its external evidence

**Priority LOW / Cost wording / Verdict amend.**

**What.** The conclusion's trilemma verdict (tex 720) asserts "the cash-flow shortfall against the caps is mostly mechanical" on the model's authority alone. Add one clause citing the two external anchors the introduction already uses: the Fed staff composition record (na2024: roughly half scheduled, remainder mostly turnover, tex 96) and the NY Fed ex-ante 75.6–88.5% projection range (tex 43, tab:headline row 2) — phrased as independent corroboration of the composition, with the paper's own no-agreement-claim discipline (tex 354) preserved.

**Where.** tex 720 (verified: null defense with no external citation); external anchors verified at tex 96 (na2024 composition, "the same fact expressed against the two denominators"), tex 43 and tex 66 (tab:headline row: 75.6–88.5%), tex 354 (the committed refusal to claim numerical convergence).

**Rationale.** Panel strength #2 is that the mechanical decomposition is "externally anchored" — but the anchoring appears in the introduction and Section II, while the conclusion, the other place a scoring reviewer reads closely, defends the null model-internally. Evidence sufficiency is scored partly on whether load-bearing claims carry their evidence at the point of assertion; this is a one-clause re-presentation of corroboration already in the paper.

**Collisions.** Tex 720 carries pinned interval literals — any edit to that paragraph is tex+gates+tests+letter in ONE commit (HANDOFF_round26 §3). The clause must respect the tex 354 discipline: composition corroboration, not numerical convergence (the 88.5%-vs-88.7% proximity is explicitly disclaimed).

**Checker amendment.** Proceed as proposed, with the collision field corrected: tex 720's pinned literals are the ×7 binding interval $+2.8$ to $+8.7$ and the calibration box $+2.1$ to $+13.2$ — the +3.5-to-+13.1 hull does NOT appear on that line (grep-verified). The one-commit tex+gates+tests+letter rule applies regardless. The added clause must mirror tex 96's two-denominators framing (composition corroboration, not numerical convergence) and must not restate either pinned interval.

---

## Originality (20%)

66.3/100; EIC 64 and R2 63 are the low scorers, R3 the high at 70. The panel's D2 arbitration credits four genuine contributions (dollar bound, cap-design arithmetic, expectations complement, Danish correction) — of which §II states one plus the window extension, and §I states none affirmatively.

### 5. Complete the §II differentiation paragraph: from two separations to the full panel-credited set

**Priority HIGH / Cost structural / Verdict amend.**

**What.** At tex L96, the paragraph referees will quote ends: "Two features separate my exercise from theirs. First, [the decomposition]… Second, I extend the same shortfall-against-cap construction… to the full June 2022 to November 2025 window." Rework this into a four-item enumeration, keeping items 1–2 and adding, as restatements of already-committed claims: (3) the expectations complement — "Third, I measure the shortfall against the Federal Reserve's own ex-ante projection as well as against the cap, separating the anticipated mechanical component (75.6--88.5%) from genuine surprise (Section~\ref{sec:method-benchmark})"; and (4) the cap-design reading — "Fourth, the decomposition turns the staff observation that the caps were not binding into an arithmetic statement about cap design: scheduled amortization and the involuntary floor (itself read from realized, partly behavioral turnover) undershoot a $35 billion monthly ceiling in essentially every month, so a cap at that level could not have bound under any household response (Sections~\ref{sec:identification}, \ref{sec:conclusion})". Demote the window extension to last — it is the weakest differentiator. Both added items quote only claims already committed at L30 (abstract), L43, L136, L714 and L720; no new number, no new hedge scope.

**Where.** Raw tex L96 (§II, the "Closest to this paper" paragraph; wrapped copy physical 227–243). Source claims verified at L30, L43, L136, L138, L714, L720.

**Rationale.** This is the paper's differentiation-from-the-Fed-literature statement — the exact sentence the re-review calls "a spot referees quote" (NEW-1). It currently concedes the mechanism and then offers only the decomposition plus window-extension arithmetic, omitting two of the four contributions the panel's own grade sheet judged genuine (expectations complement, cap-design arithmetic). An originality referee scoring "what does this add over na2024/perli2024?" reads exactly here and finds the paper claiming less than the panel already granted it.

**Collisions.** Same sentence neighborhood as the QUEUED NEW-1 repair (L96 still carries the stale bare "$+3.0$ and $+8.0$") — execute in the same commit. If the binding interval [+2.8,+8.7] is quoted here, the ×7 zero-slack count moves: tex+gates+tests+letter in ONE commit (HANDOFF_round26 §3). The "under any household response" restatement must carry B8's behavioral-turnover qualifier (as drafted). Item (3)'s phrasing avoids a negative-existence claim about the staff record; if Eugene wants "which no staff note constructs", that is a literature claim needing external verification.

**Checker amendment.** Execute as drafted in the same commit as NEW-1, with two changes: (1) in item (3), either restate without the literal ("the large majority of the realized shortfall") or, if 75.6--88.5% is quoted, screen the new occurrence against the gate covering that span (gate #33 lineage) in the same commit — that literal is absent from HANDOFF §3's zero-slack list but is gate-covered at 9 occurrences, and the collision field omitted it; (2) the paragraph does not end where the proposal says — it closes with the eyal2026 differentiation sentence, which the rework must preserve intact after the four-item enumeration.

### 6. Add an affirmative contributions paragraph to §I (the manuscript currently has none)

**Priority HIGH / Cost structural / Verdict amend.**

**What.** Insert one new source line after the L51 estimator paragraph (before L53's "Table~\ref{tab:headline} collects…"): a five-item signposted enumeration of the panel-credited contributions, each a one-clause restatement pointing at its section and quoting NO pinned literals: (1) the decomposition of the QT shortfall into mechanical and elastic components, with the elastic part delivered as a bounded margin (Sections IV–V); (2) the expectations-based complement measuring the shortfall against the Fed's own ex-ante projection (Section III); (3) the cap-design arithmetic — caps set above what any plausible prepayment path could deliver (Sections V, VIII); (4) the paired cross-design validation — real covariates into the ABM, synthetic population into the hazard framework, thresholds fixed ex ante (Section VII); (5) the order-of-magnitude correction and incidence pricing of the Danish counterfactual (Sections VI.C, V). Optionally soften L43's negative framing ("This paper's contribution is not that mechanism but its decomposition") to point forward to the list.

**Where.** New line between raw tex L52 and L53 (wrapped physical 120–121); the negation sentence at L43 (wrapped physical 56–57).

**Rationale.** Grep-verified: the manuscript contains no "first to", "novel", "to my knowledge" or contributions enumeration anywhere; the only front-matter contribution sentence is a negation, and the actual contribution content is dispersed through the L43 paragraph the re-review flags for qualification density (residual issue 4). Referees scoring originality look for an enumerated claim-set; EIC (64) and R2 (63) are the low scorers and both read front matter. This raises legibility of existing claims without strengthening any of them.

**Collisions.** New source line: long-abstract variant must be regenerated (identical-line-count rule, HANDOFF §3); one-paragraph-per-line discipline. L43 neighborhood holds the QUEUED NEW-2 posture-clause repair and gate #98's posture span — touch L43 only in coordination with that repair. Keep interval/percentage literals out of the list or zero-slack counts move (60.2% ×10, 76.3% ×8, 13.6% ×11). Grows main text by ~one paragraph against B1's page-reduction direction — name it in the letter if §7 gains the courtesy items (NEW-5a).

**Checker amendment.** In item (4), scope the threshold clause to the leg that has it: "…real covariates into the ABM under interpretive thresholds fixed ex ante, synthetic population into the hazard framework (Section VII)" — do NOT claim ex-ante thresholds for the symmetric companion; only the cross-design leg has them (raw L555/557/595), while the companion section (L599–601) contains no threshold, ex-ante or pre-commit language, so stating it pair-wide would claim more than the frozen record. Everything else as drafted, with the L43 touch deferred to the NEW-2 commit.

### 7. Claim the cross-design/symmetric-companion pair as a methodological contribution to ABM validation (posture — Eugene's call)

**Priority HIGH / Cost posture / Verdict amend.**

**What.** In the §I contributions list and/or at L102, upgrade the description of the paired design-crossing to an explicit methodological claim, scoped to the cited taxonomy: e.g. "the paired design-crossing — the same decision rule on real covariates, the same survival structure on a fully synthetic population, with interpretive thresholds fixed before each run — is offered as a validation design in its own right; it is not, to my knowledge, a named member of the empirical-validation taxonomy of \citet{fagiolo2007} or the estimation literature of \citet{grazzini2017,platt2020}." This claims MORE than the paper currently claims anywhere.

**Where.** Raw tex L102 (closing ABM-side sentence, wrapped physical 276–278) and/or the new §I contributions line. Current maximal claim verified: L102 calls the ABM work "one validation strategy among several"; the pair itself appears only descriptively at L115 (caption), L549, L599.

**Rationale.** R3 — the panel's ABM-validation specialist and its highest originality scorer (70) — independently called the pair "a methodological contribution to ABM validation practice", and the brief flags it as under-sold. This is the one item where a reviewer has already asserted more novelty than the paper claims, so claiming it is low-risk relative to typical posture moves and directly attacks the "incremental-plus" verdict: it converts a robustness section into a named exportable method. The scoped "to my knowledge… in the cited taxonomy" phrasing keeps it checkable, matching the paper's audit culture.

**Collisions.** New novelty claim — Eugene's call by the standing rules. The negative-existence clause should get an external literature check against the three cited papers before landing. If placed in the abstract it collides with the 366-word gate-pinned abstract (do not); body placement avoids that. No zero-slack literals involved if percentages are not quoted.

**Checker amendment.** Reword the design description to "with interpretive thresholds fixed before the cross-design runs" (or drop the clause), since the symmetric companion test has no ex-ante threshold in the committed record (L599–601 carries none; only L555 does). Make the external literature check against the three cited papers a HARD PRECONDITION for landing the "not, to my knowledge, a named member" clause, not merely advisable — a scoped to-my-knowledge claim that fails a check against three papers the manuscript itself cites would be a self-inflicted wound in a paper whose brand is auditability. Remains Eugene's posture call.

### 22. Foreground the design-crossing pair in the methodological-positioning paragraph (descriptive only)

**Priority MEDIUM / Cost wording / Verdict amend.**

**What.** Extend L102's final sentence — "…within which the pre-committed falsification design of Section~\ref{sec:abm} is one validation strategy among several" — with one descriptive sentence naming the paired design-crossing: the ABM's decision rule re-run on real loan covariates (Section~\ref{sec:robustness-crossdesign}) and the hazard framework's survival structure re-estimated on the fully synthetic population (Section~\ref{sec:robustness-synthesis}), varied one at a time, in both directions. Pure description of existing design facts; no novelty adjective. This is the fallback/complement if #7's posture upgrade is declined.

**Where.** Raw tex L102 (wrapped physical 264–278). Pair currently described only at L115 (fig:architecture caption, wrapped 299–301), L549 (wrapped 1534–1538), L599–601 (wrapped 1635–1648).

**Rationale.** A methods-literate referee reads L102 for the paper's methodological self-positioning and currently finds self-demotion ("one strategy among several") with the paper's actual methodological machinery absent — it lives in a figure caption and §VII, where it scores as robustness, not contribution. Making the pair visible where methodological positioning happens moves R3-archetype scoring without claiming anything new.

**Collisions.** Do not quote 60.2%/76.3% (zero-slack ×10/×8). L102 is otherwise unpinned by the interval literals; screen against the 316-span pin checklist as with all body edits. Subsumed by #7 if that posture call is taken.

**Checker amendment.** Two factual repairs are required before the sentence is wording-class. (1) Attribute the confound to the paper's own design, not to the taxonomy: the draft's "the confound that taxonomy leaves open — paradigm versus data source" misattributes it to fagiolo2007, whereas the manuscript locates it in this paper's two-estimator design (L110: "the data-source difference remains an unresolved confound"; L551: "flags an unresolved confound between this paper's two estimators"). Use e.g. "The instrument this paper uses for its own unresolved paradigm-versus-data-source confound (Section~\ref{sec:method-estimators}) is a paired design-crossing: …". (2) Do not claim ex-ante thresholds for the companion leg — write "with interpretive thresholds fixed ex ante on the cross-design leg". With both fixes the sentence is pure description of committed design facts, correctly flagged as subsumed by #7.

### 23. Add a what-this-paper-adds sentence to §II's Danish paragraph

**Priority MEDIUM / Cost wording / Verdict keep.**

**What.** Close L98 with one sentence stating the paper's addition to the strand it currently only imports from: "What this strand supplies is the rule and the slope; what it lacks for the question here is a priced U.S. counterfactual. Section~\ref{sec:abm-danish} scores the rule-only transplant on the SOMA book directly — at an order of magnitude below a mechanism-extrapolated read — and Section~\ref{sec:pathb} prices the buyback credit's incidence, which decides whether the institutional gap survives the accounting." No dollar literal quoted; the order-of-magnitude and incidence claims restate L45, L716 and the gate-#103 content.

**Where.** Raw tex L98 (wrapped physical 245–248). Source claims verified at L45 (wrapped 86–94), L716 (wrapped 1942–1956), L74 (tab:headline row, wrapped 159–161).

**Rationale.** The Danish magnitude correction is one of the four contributions the panel's grade sheet calls genuine, yet §II's Danish paragraph reads as pure importation (berg2018's rule, berger2026's slope) with the paper's own addition unstated, and the conclusion frames it as an erratum ("retires a superseded figure", L716). One sentence converts it from correction-of-self to discipline-of-a-policy-counterfactual in the section an originality referee scans for differentiation.

**Collisions.** "What it lacks" is scoped to the two cited papers — verifiable against them, not a field-wide negative. Avoid quoting +$61.2B: gate #103's batteries mutate ALL occurrences of pinned spans, so a new occurrence changes battery coverage (HANDOFF §3). Coordinate incidence phrasing with the QUEUED NEW-3 repair (§VI.C's missing incidence qualifier) so the two additions use identical scope language.

**Checker: premise verified** — L98 read as pure importation with no statement of the paper's own addition; L45's "reduces this by an order of magnitude" and its incidence pointer, L716's "retires a superseded figure" and the face/cash bracket, and the tab:headline Danish row at L74 all confirmed; the scoped negative rests on L98's own committed characterization that berger2026 "estimate no moving level for U.S. households under a Danish payoff rule"; greps show "61.2" ×22 (which is why not quoting it matters) and "28.2" ×3; REREVIEW B3 and NEW-3 confirm the incidence sites and the coordination requirement.

### 33. Reframe the expectations complement's introduction from patch-note voice to designed-object voice

**Priority LOW / Cost wording / Verdict amend.**

**What.** At L136, replace the opening "The cap-relative basis now carries an expectations-based complement, addressing a tension in the cap-relative construction itself:" with "I construct a second, expectations-based benchmark alongside the cap-relative one, because the cap-relative construction carries a tension the complement addresses:". Zero numbers, zero hedge scopes; the rest of the paragraph (including the withdrawn-convergence disclosure) is untouched.

**Where.** Raw tex L136, opening clause (wrapped physical 346–347).

**Rationale.** "Now carries" is revision-history deixis: it presents the panel-credited expectations complement as a bolt-on added to fix a problem, which is exactly the "robustness byproduct" framing the originality dimension penalizes. First-person constructed-object voice matches Eugene's prose style and costs nothing. Low value alone, but it is the derivation site #5's item (3) will point at, so the two should land together.

**Collisions.** The same paragraph contains the gate-pinned withdrawn-convergence span ("I withdraw the presentation") and the 75.6--88.5% spans — the edit as drafted touches neither, but the commit must be screened against the 316-span checklist like every body edit. No abstract or letter interaction.

**Checker amendment.** The drafted replacement's final clause must read "a tension the complement **addresses**", not "resolves" — the paragraph's own closing concession states the ratios are upper bounds because the projection may already embed lock-in, so "resolves" would upgrade address→resolve and strengthen a bounded claim, breaking the zero-claim-strength promise. Otherwise land as drafted, in the same commit as #5.

---

## Coherence (15%)

67.5/100. The panel's core complaint is qualification-stacking that obscures the argument line, with the organizing 13.6-vs-91.3 levels contrast the paper's own epistemology disallows as the named instance.

### 8. Split §I's results paragraph (tex 43) into a claim-then-qualification block at three verified seams

**Priority HIGH / Cost structural / Verdict amend.**

**What.** Restructure the single paragraph at tex 43 into four paragraphs (each on its own tex line, preserving the one-paragraph-per-line convention) without changing a word of any qualification. Verified seams: (1) end the claim block after "…a range wide enough that its overlap with the mechanical null's recovery carries no precision." (contribution + mechanical null + Fed ex-ante corroboration); (2) range-and-status block from "The elasticity's identified footprint is therefore a bounded margin…" through "Neither figure is the entire shortfall (Section~\ref{sec:identification})." — keeping the binding-layer span, the +5.6 posture sentence and the +9.2 in-sample sentence co-paragraph; (3) apparatus block from "A pre-committed sweep of the two calibration inputs…" through the "(``Pre-committed,'' here and throughout…)" parenthetical; (4) estimator block from "I reach this through two structurally distinct estimators…". Only permitted wording change: the deixis repair "I reach this" → "I reach this decomposition" at seam 4 (a claim sentence, not a qualifier). All parentheticals survive verbatim.

**Where.** tex 43 (verified in full; the paragraph runs from "That the lock-in effect slowed…" to "…supporting diagnostic rather than a clean paradigm contrast"). Sequence AFTER the queued NEW-2 repair lands, since NEW-2 rewrites the stale "upper-middle member" clause inside this same line.

**Rationale.** This is the re-review's surviving A2 residual stated verbatim ("§I's main results paragraph (L43) remains one paragraph carrying ~15 parenthetical qualifications") and the panel's core coherence complaint. The split makes the argument line legible — claim, then range, then status apparatus, then estimator architecture — while every hedge keeps its exact wording and scope. A coherence grader re-reading §I sees the same content as an argument instead of a wall.

**Collisions.** Line 43 becomes ~4 lines, renumbering everything below — do this after all queued NEW-1..NEW-6 repairs (which cite line numbers) land, and re-anchor any line-referencing tooling. No literal counts change (zero-slack list unaffected), so the letter is untouched. Paragraph-split deixis is the VII.I risk class HANDOFF flags; the three seams were chosen so no qualifier's referent crosses a boundary ("therefore" opening block 2 is rhetorical, not referential).

**Checker amendment.** Correct the collision field: NO gate anchors in tex 43, so the split itself needs no gate or test changes — gate #98 is paragraph-scoped to the line opening "A seventh qualification" (tex 369), gate #99 is abstract-scoped, gate #100 anchors on the §IV lead opener (tex 142), and the posture_middle_member span text does not occur in tex 43 at all (tex 43 carries the OLD posture wording, which is NEW-2's whole finding). The edit therefore needs only line-renumbering hygiene, hence sequencing after NEW-1..NEW-6. Keep the seam-2 grouping (interval + posture + point co-paragraph) but justify it on coherence grounds — the range-first posture assembly the re-review calls deliberate must survive as one unit — not on gate scoping. If NEW-2 imports the gate-echoed posture language ("a middle member of an interval whose measured corrections concentrate below it") into tex 43, that is still not gate-relevant (gate #98 binds only the tex-369 line), but the two sites must stay word-consistent. Retain the "I reach this" → "I reach this decomposition" deixis repair. Note the checker counts 13 open-parens, not ~15.

### 9. Give §V's opening levels contrast (tex 194) the cross-design counterweight it currently lacks

**Priority HIGH / Cost wording / Verdict keep.**

**What.** At tex 194, after "(fifty-seed mean 13.6\%)", append one clause restating §IV's committed verdict with a pointer, e.g.: ", a contrast that Section~\ref{sec:abm}'s own cross-design leg shows cannot, on that test alone, be cleanly attributed to modeling paradigm (Section~\ref{sec:robustness-crossdesign})". Quote NO literals: 60.2\% (count 10) and 76.3\% (count 8) are zero-slack-pinned and must not grow; the clause carries only the verdict language and the cross-reference.

**Where.** tex 194 (verified: §V opening paragraph, "This is the estimator on which the paper's central decomposition rests…"). Cross-checked: 13.6\% sites without counterweight are 194 (organizing prose), 164/422 (inside §IV, governed by tex 142's lead), 765/787 (run ledger).

**Rationale.** The panel's #1 coherence complaint is that the organizing 13.6-vs-91.3 levels contrast is one the paper's own epistemology disallows; round 24c fixed §IV's lead (verified at tex 142: "that result governs how everything below should be read"), and the intro site (tex 51) already carries the counterweight — but §V's front door (tex 194) re-commits the bare contrast three pages after §IV disavowed it. This is the exact residual the panel's verification narrowed the finding to ("the production 13.6\% still appears without the cross-design figure at some body sites"), and it sits at the one remaining organizing site. One clause closes it.

**Collisions.** Adds one occurrence of the "cleanly attributed" verdict phrasing (also at tex 142, 714) — not in the zero-slack list, but verify no battery pins that phrase count before committing. No pinned literals touched; 13.6\% count stays 11 (the clause adds none).

**Checker: premise verified** — tex 194 opens §V (\section at raw 192), contains the 91.3\% / 11.9\% / 13.6\% contrast and has zero cross-design or "cannot be cleanly attributed" language anywhere in the paragraph; tex 142's governed lead and tex 51's counterweight both confirmed; REVIEW line 64 quotes the residual verbatim; "cleanly attributed" is absent from the zero-slack list, ZERO_COUNT and EXACTLY_ONE, and gate #100 pins the phrase paragraph-scoped to tex 142 only; grep -o counts confirm 13.6\%=11, 76.3\%=8, 60.2\%=10. One immaterial slip: "cleanly attributed" already occurs at 5 sites (tex 30, 142, 714, 734, 1336), not the 2 the parenthetical implies — covered by the proposal's own verify-before-commit instruction.

### 10. Repair the two stale three-layer hierarchy summaries (tex 57, 378) so the uncertainty hierarchy is stated once, canonically

**Priority HIGH / Cost wording / Verdict amend.**

**What.** The paper's two canonical hierarchy statements still describe THREE layers with calibration operative, while seven sites say the floor read's wild-cluster interval is "the binding layer". Verified contradiction: tex 378 says "consolidates the three uncertainty layers… (sampling, simulation seed, and calibration)… the operative uncertainty on every headline quantity is calibration", and the tab:headline caption (tex 57) says "sampling and simulation-seed noise are negligible…; the calibration box is the operative uncertainty" — yet tab:uncertainty's own headline row (tex 392) and tablenote (tex 399) quote the wild-t interval as the binding layer. Fix: (a) recast tex 378's closing clause to name the floor read's propagated sampling error as the binding layer on the headline marginal, pointing at Section~\ref{sec:robustness-floor}; (b) tex 57's caption gains the matching clause; (c) tag the two prose re-derivation sites — tex 352's third qualification ("…governs the interval") and tex 660 — with the pointer "(the hierarchy of Table~\ref{tab:uncertainty})" so repeated statements read as one apparatus, not new doubts. No interval literals added anywhere.

**Where.** tex 57 (tab:headline caption, verified), tex 378 (verified), tags at tex 352 and tex 660 (both verified). The re-review's B2 site audit covered lines carrying the literal — 378/57 carry no literal, which is how they escaped the restatement, exactly as L96 did (NEW-1).

**Rationale.** This is the brief's "stated once canonically vs re-derived inline" question, and it is sharper than a style issue: the canonical sites currently CONTRADICT the seven binding-layer sites. A reviewer who complained the honesty apparatus fights the narrative will find the apparatus also fights itself at its own summary table. Same defect class as queued NEW-1/NEW-2 (variant-phrased site missed by the literal sweep); harmonizing to the committed round-26 promotion strengthens no claim and weakens no hedge.

**Collisions.** Adds "binding layer" occurrences (currently 7; phrase not in the zero-slack list — verify no gate counts it). Interval literals deliberately excluded so the ×7/×5 counts are untouched and the letter stays current. If Eugene reads a three→four layer recount as a posture recharacterization rather than a stale-summary repair, it is his call — but the content is already committed at tex 392/399 inside the very table these sentences summarize.

**Checker amendment.** Resolve the layer-count framing BEFORE editing: the drafted fix is internally inconsistent — it recasts to FOUR layers with the floor read's propagated error as a separate layer while its own added clause says the binding layer is "within it" (within calibration), and the table files that error under **Sampling**, not calibration. Recommended resolution: keep the three-layer enumeration and scope the summary instead — tex 378: "…sampling error on the estimators is negligible at the paper's reporting precision, and the operative uncertainty on every headline quantity is calibration — except the headline marginal, where the binding layer is the floor read's own propagated sampling error (Section~\ref{sec:robustness-floor}), the layer Table~\ref{tab:uncertainty}'s headline row quotes." Matching one-clause exception in the tex 57 caption. This avoids both the "within calibration" misfiling and the four-layer recount that triggers the posture question. Correct the site list: the seven "binding layer" literal sites are tex 43, 68, 369, 392, 399, 660, 1328 — tex 352 does NOT carry the literal (its variant is "the calibration box, not simulation noise, governs the interval"); keep its pointer tag as proposed, since its variant phrasing is real. Pointer tags at 352/660 are safe as verified. Gate note: the posture_binding_layer span is a longer literal paragraph-scoped to tex 369, and the phrase itself is not gate-pinned.

### 24. Give §V.E's seventh-qualification assembly (tex 369) a compact table form, prose retained verbatim

**Priority MEDIUM / Cost structural / Verdict amend.**

**What.** Insert a small table (tab:assembly) between the tex-369 paragraph and the figure at tex 371, tabulating the assembly the paragraph builds in prose: rows = in-sample point +9.2 (above headline); off-window re-anchor +5.6 (headline); Ginnie overlay +4.4 (below, measured); age-standardized floor 5.51\% → ~+3.8 (below, indicative, 84\% imputed weight); Fannie read 5.52\% → below +4.3 (below, bracketing, not restated); overlay × age-std composition ~+3.0 (below, "not reported as an estimate — no joint cell"); concave × additive joint cell +9.2 with interaction −1.47 (composition evidence); additive form +11.2 (above, counterweight); Fonseca anchor +11.5 (above). Columns: Reading / Marginal (pp) / Direction vs +5.6 / Status / Section. Caption states that every value repeats a committed figure and that the binding interval and hull are deliberately NOT restated here (pointer to the text and tab:uncertainty). One sentence appended at the very end of tex 369, away from the mid-paragraph pinned spans: "Table~\ref{tab:assembly} tabulates this assembly." Not one qualification word is deleted.

**Where.** New exhibit after tex 369 (paragraph verified in full), before the figure at tex 371; anchor sentence at the end of tex 369. Values cross-checked against tex 367, 369, 392, 660.

**Rationale.** The paragraph itself promises the view "a reader who lines them up sees" — but delivers it as a ~600-word wall in which the directional structure (five corrections below, two counterweights above, composition evidence in between) must be reconstructed by the reader. The table shows that structure at a glance, which is precisely what a coherence grader means by "the argument line is hard to follow"; and because the paragraph stays verbatim, no hedge moves. It also survives a future wave 2b intact (the table anchors the main text if assembly prose ever relocates).

**Collisions.** Grows the paper — runs against B1's direction (flag to Eugene; one third-page table vs 25pp target). Excludes the three pinned intervals ($+2.8$ to $+8.7$ ×7, $+3.0$ to $+8.0$ ×5, $+3.5$ to $+13.1$ ×7) by design so the letter/gates are untouched; verify +4.4/+3.8/+11.2/+11.5/−1.47 occurrence counts against gate batteries before committing (not in the zero-slack list, but #102–#104 batteries mutate all occurrences). Sequence with the queued B5 joint-cell run: its result replaces the "no joint cell" status of the composition row, so either land the table after B5 or mark the row "run pending". Per the NEW-6b lesson, actually \ref the table (no orphan label).

**Checker amendment.** Fix the Fonseca row label to "counterweight — conservative-band evidence (band choice defended in the sixth-qualification paragraph), **not** a declined reading": tex 367's three declined readings are Path A's fitted coefficient, the episode-confrontation gradient and the cross-design recovery level; Fonseca +11.5 is the band-choice counterweight, and shipping the "declined" label would introduce a factual error into a new exhibit. Re-check every Status cell against tex 367/369 wording before commit. Add to collisions the real cost the proposal omits: each tabulated value acquires a new restatement site (~10 committed values), so the same commit must extend gate coverage to the table (cheapest: a small exact-string dict over the table rows, or fold the rows into the #102–#104 battery scope) — without that, the table is a new rot surface in the paper's densest gate zone. Keep: prose verbatim, anchor sentence appended to the END of the tex-369 line (never a split — gate #98 binds the line; appending is verified gate-safe because assembly_check is substring-per-line), land after B5 or mark the composed row "run pending", and \ref the table. Score impact is the weakest of the high/medium tier: no panel item requests it, and it runs against B1.

### 25. Promote the SMD two-moment infeasibility into §IV's Interpretation as the falsification that bypasses recalibration

**Priority MEDIUM / Cost wording / Verdict keep.**

**What.** At tex 188, after "…the behavioral layer stays synthetic in both legs, so the alternative is narrowed rather than eliminated.", insert one sentence restating the committed tex-595 verdict with no numbers: "One falsification of this family does not run through the free recalibration scale at all: the pre-committed two-moment simulated-minimum-distance fit of Section~\ref{sec:robustness-crossdesign} finds the structural family jointly infeasible against the two external moments, and its near-fit overshoots the benchmark rather than approaching it."

**Where.** tex 188 (§IV.C Interpretation, verified). Source verdict verified at tex 595 ("The verdict is joint infeasibility… the near-fit… recovers 107.1\% of benchmark, far above the pre-committed cross-design bands"); currently the only other trace is the run-ledger row at tex 828 — §IV never mentions it.

**Rationale.** Panel item 3's surviving residual says this exactly: "the SMD two-moment infeasibility (which does not run through the free recalibration parameter) is under-leveraged as the section's cleanest falsification." §IV titles itself a falsification test, then argues its either-or (missing mechanism vs missing population) without its one falsification result that is immune to the recalibration confound the cross-design caveat worries about. One pointer sentence closes the loop between the section's thesis and its strongest evidence — a direct argument-line repair that strengthens no claim (the verdict already stands at tex 595 at full strength).

**Collisions.** None known: no literals added (107.1\% deliberately not quoted), no pinned spans touched. Verify "jointly infeasible"/"joint infeasibility" is not a battery-counted span before committing.

**Checker: premise verified** — the insertion anchor exists verbatim in tex 188 and §IV nowhere mentions the SMD result (grep: "simulated-minimum-distance" only at tex 595 and ledger row 828); tex 595's verdict text confirmed, and 595 sits inside sec:robustness-crossdesign (raw 549–599) so the \ref is correct; REVIEW line 64 quotes the residual verbatim; collision verified empty — "jointly infeasible" has 0 tex occurrences, the gates check the run artifact's verdict string joint_fit_infeasible (liveness_gates.py:1151–1161) rather than prose, and no gate span anchors in tex 188's neighborhood.

### 34. Split the conclusion's opening mega-paragraph (tex 714) at two verified seams

**Priority LOW / Cost structural / Verdict keep.**

**What.** Same treatment as the §I split, scoped to the conclusion: break tex 714 into three paragraphs at (1) after "…to the same 2023--24 read (Section~\ref{sec:pathb})." (thesis + two-findings frame), (2) after "…excluded from headline figures, Section~\ref{sec:patha})." (the estimator contrast), leaving (3) "The composition of that recovery, however, disciplines what the contrast can mean…" through the cross-design close as the qualification block — which keeps the paragraph's pinned spans ($+2.8$ to $+8.7$, $+3.0$ to $+8.0$, 76.3\%) together in one paragraph. Zero word changes; flag the one boundary deixis "that recovery" (referent 91.3\% ends the immediately preceding paragraph, so it survives the split).

**Where.** tex 714 (verified in full: single line from "The shortfall of the Federal Reserve's mortgage runoff…" to "…the path-level timing question remains open for every estimator").

**Rationale.** The conclusion's first paragraph chains thesis, both findings, the null, the ablation bounds, the ex-ante-projection reading and the full binding-interval restatement into one ~450-word unit — the same qualification-stacking defect the panel scored down in §I, at the other site referees read closely. Lower yield than the §I split only because graders weight the introduction more heavily.

**Collisions.** tex 714 hosts one site each of the ×7 binding interval and ×5 percentile counts plus a 76.3\% site: splitting changes no counts, but if any gate scopes those spans to a paragraph, tests re-anchor in the same commit. Same renumbering caution as the §I split — sequence after the queued NEW repairs.

**Checker: premise verified** — tex 714 read in full (~470 words); both seam strings and block 3's opener confirmed verbatim and in order; the three pinned spans all sit inside block 3 so nothing crosses a boundary and no count changes; the "that recovery" referent sits in block 2's final sentence and survives; only two paragraph-scoped checks exist in liveness_gates.py (openers at tex 369 and tex 142) and gate #99 is abstract-bounded, so nothing anchors on the conclusion line — the collision caution is safe surplus. One-paragraph-per-line convention preserved.

---

## Writing (15%)

63.5/100, the lowest core score. The panel's standing complaints: the 366-word single-paragraph abstract (CONFIRMED, panel-unanimous, EIC Critical), paragraph-length captions, and §I's qualification density — the one writing-score site the round-26 wording pass left structurally unchanged.

### 11. Unstack the abstract's interval sentence: one inference layer per sentence, word-count-neutral

**Priority HIGH / Cost wording / Verdict amend.**

**What.** At tex L30, replace the single sentence "The design pins it between $+2.8$ and $+8.7$ points under its production floor form (a wild-cluster interval on the floor read's 31 clusters; the narrower percentile read, $+3.0$ to $+8.0$, under-covers), with a form-conditional hull of $+3.5$ to $+13.1$ points, and it identifies levels only: no claim about month-to-month timing survives its own placebo tests." with three sentences, one inference layer each: "The design pins it between $+2.8$ and $+8.7$ points under its production floor form: a wild-cluster interval on the floor read's 31 clusters (the narrower percentile read, $+3.0$ to $+8.0$, under-covers). The form-conditional hull is wider, $+3.5$ to $+13.1$ points. The design identifies levels only: no claim about month-to-month timing survives its own placebo tests." Every pinned literal ($+2.8$ and $+8.7$; $+3.0$ to $+8.0$; $+3.5$ to $+13.1$), the under-coverage qualifier and the levels-only qualifier survive verbatim; the 366 total is preserved.

**Where.** tex L30 (abstract), verified; the sentence sits between "…a range rather than a number." and "Inside that range, $+5.6$ points…".

**Rationale.** The re-review's A2 verdict names this exact spot: "The abstract parses coherently on one careful read; its congestion point is the interval sentence." The sentence currently stacks three inference layers (binding wild-cluster interval, demoted percentile read, form-conditional hull) plus a two-clause nested parenthetical before reaching its main verb's completion. It is the first hard sentence a writing scorer hits, in the exhibit they weight most. Unstacking it is pure repunctuation: no number, no hedge, no order change — the range still precedes the +5.6 point, satisfying the committed order.

**Collisions.** Abstract edits are gate-adjacent: gate #101 recomputes the 366 word count and the letter must be recounted in the same commit (HANDOFF_round26 §3); gate #99's ordering literal is `$+2.8$ and $+8.7$` and survives verbatim; the `$+3.0$ to $+8.0$` demoted-mention count must stay exactly 5 (do not delete, do not grow) and the hull count exactly 7 — both preserved; the long-abstract variant must be regenerated under its rule (canonical with line 30 swapped, identical line count, difference on line 30 only).

**Checker amendment.** Correct the internal count: both segments are 55 words under `wc -w` (verified), not 45 — still exactly neutral, so 366 is preserved as claimed. Keep "wider" — it costs nothing — and DELETE the word-banking contingency, whose arithmetic is backwards (dropping "wider" would make the abstract 365 and need a +1, not a −1 trim). Add one collision: HANDOFF §1 records ABSTRACT_POSTURE = 7 canonical-scoped spans pinned to the abstract; the restructure changes punctuation inside the wild-cluster parenthetical, so if any span covers that text, gates+tests travel in the same commit as tex+letter.

### 12. Give "floor read" a referent at first abstract use: swap to "involuntary-turnover floor's", wc-neutral

**Priority HIGH / Cost wording / Verdict amend.**

**What.** In the same L30 parenthetical, replace "the floor read's 31 clusters" with "the involuntary-turnover floor's 31 clusters". Token count is identical (the/floor/read's → the/involuntary-turnover/floor's; hyphenated compounds count once under `wc -w`, which gate #101 uses), so the gloss fits inside 366 with zero net change. This makes the abstract's first floor mention the full name, and turns the later sentence "every correction I can measure to the involuntary-turnover floor or to the accounting basis" (currently the term's orphaned first full appearance) into a back-reference. If the swap reads too loose — strictly, the 31 clusters belong to the floor's off-window re-measurement, not the floor itself — the equally wc-neutral alternative "the floor re-measurement's 31 clusters" keeps the measurement nuance. Optional word bank: the later mention can become "to that floor or" (−1 word).

**Where.** tex L30, the parenthetical "(a wild-cluster interval on the floor read's 31 clusters; …)", verified; the later referent "to the involuntary-turnover floor or to the accounting basis" also verified in L30.

**Rationale.** The re-review states the defect verbatim: a cold reader hits "the floor read's 31 clusters" "with no prior referent for 'floor read'". The abstract never mentions the floor before this point and never says it was re-measured, so "read" is jargon with nothing to attach to — precisely the illegible-honesty pattern the panel scored down. The qualifier content (wild-cluster, 31 clusters, under-coverage) is untouched; only the noun naming the object changes.

**Collisions.** Same gate cluster as the interval-sentence restructure — gate #101 + letter recount in the same commit, `$+3.0$ to $+8.0$` count 5 sits in the same parenthetical and must not be disturbed, long-abstract variant regeneration. Land both abstract edits in one commit to trigger the recount machinery once.

**Checker amendment.** Add to collisions: HANDOFF §1's ABSTRACT_POSTURE = 7 canonical-scoped spans — "the floor read's 31 clusters" plausibly sits inside a pinned span, in which case gates+tests join the tex+letter commit. Otherwise land as written, in the same single commit as the interval-sentence restructure so the recount machinery (gate #101, letter, long-abstract variant) fires once. Token equivalence and the −1 trim arithmetic both verified.

### 13. Break the L43 monolith into four paragraphs and footnote its two heaviest parentheticals (verbatim)

**Priority HIGH / Cost structural / Verdict amend.**

**What.** Tex L43 is one 633-word paragraph carrying 13 parenthetical spans (both counts verified by direct count). Split it at three seams that track its argumentative arcs, with zero word changes: (1) after "…its overlap with the mechanical null's recovery carries no precision." (mechanical composition); (2) after "…reported here as the in-sample calibration point rather than the headline." (the bounded margin and headline); (3) after the close of the pre-committed definition parenthetical "…how its outcome was adjudicated after the run.)" (pre-commitment apparatus), leaving the two-estimators arc as the fourth paragraph. Additionally demote, verbatim, the two parentheticals that are apparatus rather than results into footnotes: the ~55-word "(``Pre-committed,'' here and throughout, means … adjudicated after the run.)" definition and the ~33-word "(sampling 95\% confidence interval $[+9.17, +9.23]$ points from a 200-replicate paired loan-level bootstrap; … Table~\ref{tab:uncertainty})". That removes ~90 words of parenthetical load from the reading line and cuts in-line parentheticals from 13 to 11 without deleting a character of content.

**Where.** tex L43 (§I main results paragraph), read in full; seam sentences verified verbatim.

**Rationale.** The re-review singles this out: "§I's qualification density (L43) is the one writing-score site the wording pass left structurally unchanged, apparently deliberately." The deliberateness is about preserving the range-first assembly ORDER, which gates #99/#100 pin — and a paragraph split preserves order exactly while giving the referee four breath points instead of none. This is the paragraph a writing scorer will cite as "qualification-stacked prose"; it is also where they decide whether the honesty is legible or merely present.

**Collisions.** Heavy gate adjacency: NEW-2's queued repair already edits L43's posture clause, so this must land in the same commit as (or strictly after) NEW-2; L43 is one of the seven `$+2.8$ to $+8.7$` zero-slack sites; gates #99/#100 assert order (preserved); footnoting the Pre-committed definition relocates the intro's signpost to app:verdicts (credited under B7) from paragraph body to footnote — still §I, but worth a deliberate call; splitting shifts all line numbers below 43, so tex+gates+tests in ONE commit per repo discipline.

**Checker amendment.** Correct the gate-#98 gloss: the span is the re-derived posture ("a middle member of an interval whose measured corrections concentrate below it", per HANDOFF §1); L43's "upper-middle member" clause is the STALE text NEW-2 fixes, not the gate span. Land the split in the same commit as (or strictly after) NEW-2 so the split does not fossilize the stale clause. Note explicitly that the split renumbers every line below 43 — the queued repairs NEW-1 (L96), NEW-3, NEW-4 (L1333), NEW-6a (L1211) are anchored by line number, so either land them first or re-derive their anchors. The B7 signpost demotion (Pre-committed definition to a footnote) stays flagged as a deliberate author call, as written.

### 26. Extend the round-26 frozen-content wording protocol to the appendices (tex 739–1349), the authorized untouched half

**Priority MEDIUM / Cost wording / Verdict amend.**

**What.** Run the same 81-edit-class wording-only pass, under the same frozen-content validation, over the appendix range the round-26 pass deliberately skipped. First port the validator into repo tooling: HANDOFF_round26 §4.3 records that the pin-extraction fix (no-decrease for single-token pins, exact-count for prose spans) lives only in the scratchpad applier. Verified first targets: (a) L1264's in-line forensic provenance — "…I state the basis because an earlier module docstring described the profile as in-window and was wrong" — moves verbatim to a footnote (disclosure kept, reading line cleared); (b) fig:cprsurface's 141-word caption at L870, the appendix twin of the gapsweep caption problem, diets to caption + notes; (c) the seven relocated units (L853, L876, L977–8, L1209, L1216, L1247, L1260) were drafted as main-text subsections and never passed the protocol — sweep them for deixis beyond the queued NEW-6a instance at L1211 and for main-text-register openings; (d) the run-ledger prose at L741–852.

**Where.** tex 739–1349 (from the online-appendix designation at L739 through app:verdicts at L1311); specific verified sites L870, L1211, L1264, and the relocated-unit openings listed.

**Rationale.** The re-review's A2 verdict is PARTIALLY_ADDRESSED explicitly because "appendices deliberately untouched" — and B1's relocation just moved four robustness units plus spec blocks INTO that untouched half, so the share of referee reading that never received the wording pass grew this round. A referee scoring writing does not stop scoring at p.87; the "forensic reconciliations" complaint (panel item 5) now largely lives in the appendix. This is the highest-volume wording-class lever left, and the protocol plus validator already exist.

**Collisions.** Zero-slack literals have appendix sites: `positive at every` includes L759 (run ledger), and several count-pinned percentages have appendix occurrences — the validator's exact-count mode must run file-wide, not range-wide; batteries #102/#103/#104 mutate ALL occurrences of their spans (presence-gate power, known limit); coordinate with queued NEW-4 (L1333 row label) and NEW-6a/6b so the same lines are not edited twice.

**Checker amendment.** Relabel the bundle honestly: (c) the deixis/register sweep and (d) the run-ledger prose are wording-class; (a) the L1264 footnote demotion and (b) the L870 caption diet are STRUCTURAL and take the same one-commit discipline as the gapsweep diet. Correct the collision detail: appendix-range zero-slack exposure is 13.6% (×2) and 11.06 (×1) plus "positive at every" at L759; 60.2%/76.3% have NO appendix occurrences — the file-wide exact-count validator requirement stands regardless. Prerequisite step one: port the scratchpad applier's pin-extraction fix (HANDOFF §4.3) into repo tooling before any edit lands.

### 27. Diet the fig:gapsweep caption (260 words) to ~90-word caption + a Notes block, all disclosures verbatim

**Priority MEDIUM / Cost structural / Verdict keep.**

**What.** Restructure the L503 caption into the paper's existing table idiom (short caption + notes, as tab:danish already does at L511+): the caption keeps sentence 1 (what is swept, both anchors), the two anchor results with "positive at every sweep point" intact, and the takeaway sentence "The anchor, not the refinance channel, decides the sign." (~90 words). A \footnotesize Notes paragraph under the figure receives, verbatim: the forced-positivity clause ("that positivity is forced by the zero-gap anchor and cannot be overturned by this sweep, since additional refinance-in-place only raises Danish prepayment further"), the superseded-$925.5B comparison sentences, the ceiling values, and the upper-half disclosure through "Those points are retained only to show the direction of the sweep." No sentence is deleted or reworded — the forced-positivity content also exists in fuller form in body L498 ("forced by construction… I retain both as wiring checks and read neither as evidence"), so nothing becomes single-sourced by the move.

**Where.** tex L500–505 (caption at L503, \label at L504), verified in full; duplicated body treatment at L498 verified.

**Rationale.** The panel's original complaint was "paragraph-length captions"; round 26 fixed the intro caption (161 words) and left fig:gapsweep as the new longest at 260. A caption is scored as furniture — a referee who hits a 260-word caption re-registers the original complaint no matter what the body says. Caption-vs-notes is exactly the legibility move the paper already uses for every threeparttable: the disclosure stays adjacent to the figure and verbatim, but the caption reads in one breath.

**Collisions.** `positive at every` count is 6 file-wide with L503 as a site — the phrase must survive intact in the short caption (or the count moves and gates/tests/letter travel in one commit); §VI.C is the region where queued NEW-3 adds the missing incidence/denomination language — land this diet in the same commit to avoid editing the region twice; gate #103's buyback-bracket battery mutates all occurrences of its spans in this neighborhood.

**Checker: premise verified** — L503 is exactly 260 words (`wc -w`) and contains verbatim every clause the proposal routes, including the ceiling values (+$1,038.9B/+$972.0B) and the retained takeaway; body L498's fuller forced-by-construction treatment confirms nothing becomes single-sourced; tab:danish's one-line caption at L511 with tablenotes at L523–530 confirms the idiom precedent; "positive at every" = 6 at lines 43/280/498/503/528/759; re-review names fig:gapsweep as the new longest at 260 words and panel review line 66 carries the paragraph-length-caption complaint (EIC Critical).

### 35. One paragraph break inside the abstract (posture: alters the designed single-paragraph form)

**Priority LOW / Cost posture / Verdict keep.**

**What.** Insert a single paragraph break in the abstract after "…accounts for 91.3\%." and before "What lock-in itself adds is a range rather than a number." — separating the what-happened/mechanical arc from the what-lock-in-adds arc. Implementation detail that matters: use an inline \par token rather than a blank line, so the abstract remains one tex source line and the long-abstract variant rule ("canonical with line 30 swapped; identical line count; difference on line 30 only") still holds. The \par token adds one word to `wc -w` (366 → 367), so this is NOT word-count-neutral under gate #101's recomputation; every prose word, qualifier and literal is byte-identical.

**Where.** tex L30, at the verified seam "…run on Freddie Mac data, accounts for 91.3\%. What lock-in itself adds…".

**Rationale.** Panel item 5 (CONFIRMED, panel-unanimous, EIC Critical) names "single-paragraph abstract" as a standing writing complaint, separately from length. The ≤150-word remedy was declined and stays declined; this is the only remaining response to the "single-paragraph" half of the complaint that costs zero prose. Marked posture, not wording, because it changes the designed form of a gate-pinned exhibit and the count: that is the author's call, and honestly the panel may still want the length, but this is the cheapest visible concession available on this line-item.

**Collisions.** Collides with the shape (not the letter) of the standing 366-words-by-design decision — the decision fixed content and count, not paragraphing, but it is adjacent and flagged as such; gate #101 word count changes (366 → 367 under `wc -w`) so letter recount in the same commit and the mutation literal re-anchored (HANDOFF §4.2 warns the word-count battery went vacuous when counts changed); many venues force single-paragraph abstracts at typesetting, so the break may not survive production — worth deciding before, not after, the venue choice.

**Checker: premise verified** — the seam exists verbatim at L30 and panel review line 66 reads "[CONFIRMED] … 328-word single-paragraph abstract … Panel-unanimous; EIC Critical"; the cost class is the honest one precisely because the count changes and the proposal does not smuggle it as wording; HANDOFF §4 item 2 confirms the word-count battery went vacuous twice when counts changed, so re-anchoring the mutation literal is required; the single-tex-line \par implementation genuinely preserves the long-abstract variant rule. Implementation note for the executor: the post-break paragraph takes default \parindent, and the long-abstract variant's own line 30 should carry a matching break.

---

## Structure / venue fit (unweighted)

EIC venue fit 45/100 — unweighted in the 68, but the lowest number on the sheet. Its two named components are the page count and the abstract; the re-review holds B1 half-satisfied because the forensic layer the panel actually named stayed in the reading line.

### 14. Wave 2b move #1: Path A estimation detail (V.D) to the Online Appendix — highest yield per unit of deixis risk

**Priority HIGH / Cost structural / Verdict amend.**

**What.** Move the Path A block (L297–345: eq:pathA at L300–302, the 295-fixed-effects and spec-v4 paragraphs L305–308, tab:pathadiag L310–331, the path-caution paragraph L333, fig:ccf L335–340, moving-block bootstrap L342, Theil pointer L344) verbatim to the Online Appendix, landing adjacent to app:ridge (L1076), which already holds the Path A estimation panel and ridge device. Keep a one-paragraph stub in V.D stating the verdict ($928.9B/121.5% standalone, corroboration only, excluded from headline figures) with an Appendix pointer. Net ~6pp of the ~6.9pp block (char-count estimate 28,437 chars).

**Where.** Source block L297–345 (verified: subsection head L297, tab:pathadiag caption L312 self-describes "aggregate-level corroboration exhibit excluded from the [headline]"); landing zone after L1076 (app:ridge). Callers: 26 main-text + 8 appendix refs to sec:patha; a grep of all 26 main-text contexts shows they are overwhelmingly parenthetical "(Section~\ref{sec:patha})" — the same mechanical Section→Appendix repoint wave 1 did for 23 callers. External exhibit callers: fig:ccf has exactly one (L169, §IV); tab:pathadiag has none outside the block.

**Rationale.** This is the largest main-text block that is (a) self-declared non-headline corroboration, (b) grep-verified to contain ZERO zero-slack literals in L297–345, and (c) nearly deixis-free (parenthetical callers, one external exhibit ref). It is exactly the "results-and-qualifications prose" wave 2b is authorized to move, at wave-1 (moves-only) risk rather than rewrite-class risk. Takes main text 87→~81pp, and the EIC's "forensic subsections in main text" complaint loses its second-biggest exhibit. tab:estimators (L425) and tab:bases (L448) keep the Path A rows in the reading line, so the two-estimator design claim (§III.A) is untouched.

**Collisions.** No zero-slack literal moves (verified empty grep over L297–345). The stub paragraph is new prose — must pass the frozen-content rule (no claim strengthening). Line-count changes force long-abstract variant regeneration (canonical line-30-swap machinery handles it). Screen the 316 gate-pinned-span checklist for spans inside L297–345 before moving; if any gate literal names "Section" near sec:patha, gates+tests ride in the same commit.

**Checker amendment.** Execute as written with three additions: (1) either keep the L333 paragraph (cross-estimator detrending + the +4.20 episode_confrontation gradient) in main text as the block's survivor, or give §V.E L367's "realized cross-cohort gap gradient" clause an explicit Appendix~\ref pointer in the same commit — L333 is not Path A detail, it is the paper's one realized-data lock-in-direction exhibit and the only non-parenthetical dependency on the block, so moving it silently strands a main-text back-reference; (2) the move must be strictly verbatim: the block carries ~15 presence-pinned gate spans (seasonal-permutation battery, liveness_gates.py:2985–3002) that pass on whole-file presence but fail on paraphrase, and the stub must not reconstruct the gate-FORBIDDEN phrase "with the peak moving from lag $-3$ to $-2$ and the recovery to 121.5\%" (negative gate at :3000); (3) decide explicitly whether the \subsection head + sec:patha label move (wave-1 style, all 22 external callers repointed Section→Appendix) or stay as the stub's head — the proposal is ambiguous between the two.

### 15. Ship the Online Appendix as a separate PDF — the split point already exists at L736

**Priority HIGH / Cost structural / Verdict amend.**

**What.** Compile once, then split the PDF at the p.87/88 boundary (qpdf/pdfpages): main.pdf = pp.1–87 + references; online_appendix.pdf = pp.88–122 keeping continued page numbers (standard OA practice). Both halves come from ONE compilation, so the main→appendix Appendix~\ref calls and the appendix-half \ref calls resolve to correct printed numbers; only cross-half hyperlinks go dead (cosmetic). Add the split command to the build script and a one-line packaging note wherever submission materials are staged.

**Where.** The boundary is already mechanically clean: L736 "\newpage", L737 "\appendix", L739 banner "The appendices that follow, through Appendix~\ref{app:verdicts}, are for online publication" (all verified). The wave-2a designation did the textual work; this is the packaging step it points at.

**Rationale.** This changes the submission calculus more than any single relocation: the EIC scored the manuscript economics of a 116pp monolith; an editor receiving main.pdf sees an 87pp paper plus a separately-attached OA — the format field journals actually receive and the exact remedy shape the EIC named ("apparatus to online appendix"). The re-review already treats pp.88–122 as designated OA; this makes the designation physically true at submission time. Combined with #14 it puts a ~81pp main PDF in front of the venue decision without touching a single frozen result.

**Collisions.** None in the tex, as drafted. The packaging note should keep the "122pp total (main text ends p.87)" framing so gate #101's letter tracking sees no figure change. If the letter gains a sentence announcing the two-file packaging, that is the NEW-5a courtesy-item edit already queued — fold it there, not in a separate letter touch.

**Checker amendment.** Keep the two-PDF packaging, with corrections: (1) the references print at document end (\bibliography at L1346–47, AFTER the appendices), so "main.pdf = pp.1–87 + references" is not a single-boundary split — either move the two bibliography lines above L737 \appendix (one mechanical tex edit; natbib collects appendix cites regardless of position, then regenerate the long-abstract variant to match) or qpdf-extract non-contiguous ranges (1–87 + refs pages) and duplicate the refs into both halves. The first is cleaner and should be stated as the plan, which retires the "zero tex edits" claim. (2) Correct the caller arithmetic: 61 main-text Appendix~\ref calls resolve (89 is the whole-file count), and the 173 refs in the appendix half resolve because both halves come from one compilation — the argument stands, the labels were wrong. (3) The response letter currently makes no page-count claim at all (0 hits for page counts or "Online Appendix"), so the only letter interaction is the NEW-5a courtesy item, exactly as the proposal already routes it.

### 16. One-page "How to read this paper" guide in the front matter, pointer-only (zero numeric literals)

**Priority HIGH / Cost structural / Verdict keep.**

**What.** Insert one new source line after L80 (the "Definitions used throughout" paragraph) and before §II (L82): a \paragraph{How to read this paper.} giving (i) the short referee path — §§I–III for claim and design, §V.B for the operative estimator, §V.E for what is and is not identified, §VII.F for calibration sensitivity, §VIII for the bottom line; (ii) the statement that everything after L739's banner is online-only apparatus (ledger, specs, verdict audit), with Appendix~\ref pointers; (iii) where each qualification class lives (the seven qualifications: §V.E; floor/form sensitivity: §VII.F; adjudication audit: app:verdicts). Written with NO numeric literals — pointers only — so no zero-slack count can move.

**Where.** Insertion point verified: L80 is the definitions paragraph closing the front matter; L82 opens §II. tab:headline (L55–78) already maps each result to its owning section (rows verified at L65–74), so the guide complements rather than duplicates it: the table maps results, the guide maps the READ. No roadmap currently exists ("proceeds as follows" / "organized as follows": zero grep hits file-wide).

**Rationale.** The venue-fit score is a traversal judgment: 87pp with no stated path reads as 87pp of obligation. A one-page guide converts it into a ~35pp core read with labeled optional layers — directly the difference between "disqualifying economics" and "long but navigable" for an EIC deciding fit. It costs ~0.7pp against the page goal, which is why it must be pointer-only and one paragraph; its yield is on the dimension being scored, not the page count.

**Collisions.** New source line changes line count → regenerate the long-abstract variant (identical-line-count gate is against the canonical, satisfied by regeneration). Keep zero numeric literals or the zero-slack recount and gate #101 letter sync trigger. Do not let the guide characterize the interval or posture (gate #98/#99 spans stay untouched).

**Checker: premise verified** — L80 is the "Definitions used throughout" paragraph, §II opens at L82, tab:headline rows L65–74 map results to owning sections, and the file has zero "proceeds/organized as follows" roadmap text anywhere; every named stop exists (V.B=sec:pathb L229, V.E=sec:identification L346, VII.F=sec:robustness-floor L615, VIII=Conclusion L712, OA banner L739); gate #98's posture span and gate #99's abstract-order gate (liveness_gates.py:337–399) touch no front matter. Nit: the "one-page" title vs one-paragraph body.

### 28. Wave 2b move #2: three orphan diagnostic exhibits with ≤1 caller each (tab:discount, input-timing diagnosis, fig:marginaltiming)

**Priority MEDIUM / Cost structural / Verdict amend.**

**What.** Move to the Online Appendix: (a) tab:discount and its frame (L259–276, the Danish discount-rate diagnostic whose ΔCPR/Δtrapped columns are all 0.00 — archetypal OA material), keeping the L257 sentence that cites it (L257 is a gate #103 incidence-bracket site and STAYS); (b) the input-timing diagnosis paragraphs L289–291; (c) fig:marginaltiming and its paragraph L356–363, keeping the levels-only concession sentence in V.E prose. Combined ~2.5–3pp.

**Where.** Verified: tab:discount L259–276 (one caller, L257, adjacent); L289–291 close V.B; fig:marginaltiming L356–363 inside V.E (one caller, L356 itself). Zero-slack literal grep over L259–276 and L289–291: empty. Landing: L259–291 material beside app:params (L971, Path B parameterization); fig:marginaltiming beside the ledger's timing material.

**Rationale.** These are the lowest-caller, zero-pinned-literal fragments of "results-and-qualifications prose" left in §V — each moves whole with at most one mechanical pointer repair. Together with #14, main text lands ~78pp. Honest arithmetic: wave 2b at moves-only risk stalls around 78pp; the remaining distance to the EIC's 55–60 runs through the Calibration Box and V.E forensics (#29) or through condensation the concision round proved dangerous — which is why #15 and #30 carry the rest of the venue-fit load.

**Collisions.** L257 must not move (gate #103 pins the incidence bracket there); split the exhibit from its citing sentence carefully. fig:marginaltiming's caption restates timing non-claims — moving it must not delete the V.E prose concession ("identifies levels only" is abstract-pinned posture; the L356 paragraph's concession sentence stays).

**Checker amendment.** Price the risk class honestly as "moves plus three small deixis repairs", executed in the same commit as the moves — NOT "the same risk class as wave 1": (1) rewrite L333's opening clause to "Extending the input-timing diagnosis of Appendix~\ref{app:params} to the cohort level" (or keep L291 with the Path A block if #14 also runs, so the two land adjacently) — L333 currently opens with a bare deixis onto L291 that breaks when L291 moves; (2) the fig:marginaltiming move splits the L356 paragraph — an intra-paragraph split, the class the handoff prices above moves-only — so keep the full final sentence ("per the pre-committed posture… fit diagnostics, not timing credentials") in V.E verbatim and screen the split against the 316-span checklist; (3) leave a one-clause pointer in V.B where L289 stood ("the peak alignment supports no settlement interpretation; Appendix~\ref{…}") so the non-claim survives in the reading line beside the retained peak-lag report at L278; (4) drop the "head of the L257 paragraph" claim — gate #103's spans sit mid-to-late in that paragraph and are file-wide presence-checked, and the operative instruction (L257 stays whole) is unaffected.

### 29. Split the Calibration Box (VII.F) — the block the EIC actually named

**Priority MEDIUM / Cost posture / Verdict keep.** Partially reverses a wave-1 keep decision, so it is Eugene's call.

**What.** Keep in main text: the binding-layer paragraphs — L650 (form test → hull), L658 (off-window re-run), L660 (anchor decomposition; carries wild-cluster binding-interval machinery), L661–663 (matched-depth + months-dimension instrument) — plus a compact verdict paragraph. Move to OA: the sweep mechanics L617–621, tab:lowband L623–648, the contamination-separation prose L652–656, tab:floorband L665–682, tab:oosfloor L684–709. Yield ~4–5pp of the 7.3pp block, taking main text to ~73–74pp when stacked on #14 and #28.

**Where.** All verified: subsection at L615; tables at L623–648 (tab:lowband), L665–682 (tab:floorband), L684–709 (tab:oosfloor); binding-layer prose at L650/L658/L660/L663. Callers: 35 main-text + 19 appendix refs to sec:robustness-floor — the heaviest caller load of any candidate, which is why this ranks after the low-risk moves despite being the EIC's named block (re-review B1: "the forensic layer the panel actually named (Calibration Box, the L369 qualification assembly) stays in the reading line").

**Rationale.** The re-review states B1 is only half-satisfied BECAUSE this block (and L369) stayed. No sequence of low-risk moves closes the EIC gap while VII.F holds 7.3pp of floor-sweep forensics in the reading line. But wave 1 kept it with a stated rationale ("forensics share lines with binding-layer machinery — splitting is not a move"), and the split touches gate #102-pinned tab:lowband and the L660 binding-interval neighborhood — so proposing it as routine relocation would misprice it. It is the one lever that moves the 45 materially beyond ~78pp, offered honestly as a posture decision. L369 itself (the seventh-qualification assembly, now hosting the re-derived "middle member" posture and gate #98's span) should NOT move — it is the paper's epistemic spine and maximal-collision text.

**Collisions.** Direct: partially reverses the wave-1 "VII.I stays" decision (stated rationale on record). tab:lowband is gate #102-pinned; L660 carries binding-layer machinery adjacent to the $+2.8$-to-$+8.7$ zero-slack literal; hull literal at L650 is one of the ×7 count. Any execution = tex+gates+tests+letter in ONE commit, plus the 316-span screen. Paragraph splits here are exactly the deixis-repair class the handoff prices as a dedicated session.

**Checker: premise verified** — the most carefully priced proposal in the set, and every premise survives: the line map is exact (tables at 623–648/665–682/684–709, labels at 626/668/689); the three zero-slack literals in VII.F sit exclusively on the KEPT lines (650 hull; 660 wild-cluster + percentile; 663 hull) and the five move spans are literal-free; the 35 main + 19 appendix counts are exact; the re-review B1 quotation is verbatim; gate #102's tab:lowband pin is presence-based, so a verbatim move survives; the explicit L369 non-move matches gate #98's paragraph scope. The score case is the strongest of the set — the re-review states B1 is half-satisfied BECAUSE this block stayed.

### 30. Submission-variant short abstract via the existing variant machinery

**Priority MEDIUM / Cost posture / Verdict keep.** The other named component of the EIC's complaint.

**What.** The repo already maintains revised_paper_v18_long_abstract.tex as "canonical with line 30 swapped". Add a third build variant whose line 30 is a ≤150-word submission abstract (range-first, cross-design counterweight, levels-only concession — the gate #99 order logic compressed), used ONLY in the submission packaging of #15; the canonical 366-word abstract remains the paper of record and the working-paper edition. This does not edit the canonical line 30.

**Where.** Canonical abstract at L30 (verified: 366 words carrying the wild-cluster interval, demoted percentile, hull, null-floor clause — every disclosure gate-pinned as ABSTRACT_POSTURE spans). The EIC's venue-fit sentence names the abstract alongside the page count; relocations cannot touch this component at all.

**Rationale.** Honest accounting: the 45 has two named components — pages and abstract. The relocation and packaging proposals exhaust the first. Most target venues hard-cap abstracts near 100–150 words; a 366-word single-paragraph abstract fails desk formatting at essentially every field journal regardless of its epistemics. A variant preserves the standing decision for the canonical document while making submission mechanically possible. But a ≤150-word abstract cannot carry all seven pinned disclosures, so choosing WHICH survive is a claim-strength decision — squarely Eugene's, and the panel's ≤150 remedy was explicitly declined, so this is a reversal-in-spirit even as a variant.

**Collisions.** Head-on with the standing decision "abstract is 366 words by design; ≤150-word remedy declined". Gate #99 (range-before-point order), the 7 ABSTRACT_POSTURE spans, and gate #101's letter recount are all defined against the canonical line 30 — a variant either gets variant-scoped gate exemptions (gate change in the same commit) or fails the suite. The variant-regeneration rule ("difference on line 30 only") extends naturally, but the gates were not written for a second swap.

**Checker: premise verified** — `sed -n 30p | wc -w` = 366 and all four named disclosures located verbatim; revised_paper_v18_long_abstract.tex confirmed present; the original review's item 5 names the abstract alongside the page count as the panel-unanimous manuscript-economics defect. The proposal reverses a standing decision and correctly labels it posture with the collision named head-on, including that compressing the seven pinned disclosures is Eugene's claim-strength decision. Collision mechanics err conservative: gates run on the canonical, but three test files also read the variant (test_buyback_incidence_gate.py:50, test_elasticity_discipline_gate.py:47, test_verdict_audit_gate.py:48), so a third sanctioned file needs test extension in the same commit — slightly different from "gate exemptions", same one-commit consequence.

---

## Killed proposals (do not resurrect without new evidence)

These four are negative results worth keeping.

### K1. Rigor — "Score Path B's LEVEL on the held-out 23 months: the one outcome-holdout constructible from committed artifacts" (HIGH / run)

**Checker's reason, in full.** The load-bearing premise — "realized prepayment enters only as the scoring denominator; the floor, the loan sample, and the elasticity touch no held-out month" — is false for the LEVEL. Tex 461, which the proposal never cites, states: "The engine renormalises the simulated pool to realized Fed holdings every month, so a leg's dollar roll-off is a rate applied to an exogenous level and its balance path cannot drift from the realized one. No recovery percentage here is a balance-path fit… each is close to a restatement of that leg's window-mean CPR against the empirical 5.14%… it is a limit on what any of these levels can corroborate." Realized Fed holdings over Jan 2024–Nov 2025 embed realized held-out prepayment, and they enter BOTH simulated legs multiplicatively every month. A "level holdout" derived from the committed artifacts or a re-run of the existing harness therefore scores a quantity that already contains the outcome inside its simulated legs — a scaled CPR restatement with partial circularity, not an outcome holdout. That kills the entire score lever: the proposed rewrite of the tex 80/730 "no outcome-holdout months exist anywhere… without exception" disclosure to "one rate-path-conditional outcome holdout exists for the level" would be an overclaim contradicted by the paper's own tex 461 framing — the conditionality is the realized balance path, not just the rate path. A rigor referee who traced the engine (as the panel's DA demonstrably does) would score this as a manufactured holdout, moving the dimension DOWN. The edit list is also incomplete: the outcome-holdout/"without exception" language lives at tex 80, 663 AND 730 (grep-verified), and tex 663's "a floor-stability check rather than an outcome holdout" characterization would need a level/marginal split too. Resurrection would require a dynamic-balance engine mode (the Danish leg's, tex 461) for the U.S. legs — a new construction with level semantics incomparable to every other recovery percentage in the paper, nothing like the proposed no-engine derivation.

### K2. Originality — "State the cap-design arithmetic as a design result in §III, not only in the conclusion's last paragraphs" (MEDIUM / wording)

**Checker's reason, in full.** The premise is false. The rationale rests on "the design reading surfaces only in the conclusion's final paragraphs, after 80+ pages" — but the abstract (L30) already states "scheduled amortization and baseline involuntary turnover (itself read from realized, partly behavioral turnover) fall short of a $35 billion monthly ceiling however households react to rates", and §I (L43) states the null "would have undershot a $35 billion monthly cap regardless of any household response to rates". An originality referee scoring off §§I–III meets the design arithmetic on page 1 and again in the introduction; L138's benchmark-defense paragraph not repeating it is not a legibility gap that moves a score. The proposal also duplicates P1's item (4), which places the same cap-design reading in §II in the same revision wave — landing both adds a third front-matter restatement of one claim, growing §III against the B1 direction for no incremental originality credit (the panel already scored cap-design arithmetic as a genuine contribution). The location facts it cites are accurate (L138's two-reasons defense verified; the appended-sentence anchor "…the reduction the mortgage structure delivered." exists mid-paragraph), but a correct location does not rescue a false motivating premise.

### K3. Evidence — "Plot the Ginnie-vs-Freddie observed-speed series behind the composition bound" (LOW / run)

**Checker's reason, in full.** Premise and cost class both check out (tex 255 describes the extracted June 2017–November 2025 series from the December 2025 GMAR; the paper's 13 figures, enumerated by grep, include no external-speed plot; "run" is the honest class). It dies on criterion four: the score impact is implausible. Every evidential quantity the figure would draw (window-mean 2.1pp differential, the two snapshots, the $20–47B containment) is already stated in prose at tex 253/255 and tabulated at tex 1188, and the panel's Data complaint is coverage ("bounded rather than closed"), which visualizing published speeds does not address. An online-appendix figure in a 122pp document — behind a bound a scoring referee already meets in the main text, requiring run-class spec ceremony plus the worktree's figure-PNG staging — buys visibility, not evidence; the proposal's own rationale concedes "modest score effect", and if the caption edit (#3) lands, the quantified bound is already at the point of scoring.

### K4. Structure — "Methods-paper split: app:ledger + app:verdicts + the pre-commitment protocol exposition" (LOW / external)

**Checker's reason, in full.** Killed on criterion (4), by the proposal's own honest accounting. The premises are true (app:ledger at L741 running to L851, app:verdicts at L1311–1349, OA banner L739, exactly 53 "pre-committed" occurrences in L37–735) — but both seam sections already sit in the Online Appendix, outside the p.87 main text the EIC scores, so the split changes nothing a referee scoring structure sees this round. The one in-paper payoff it gestures at (compressing the 53 in-text protocol asides against a citable methods paper) is explicitly deferred to "a future wording pass" with its own pin screening — i.e. the only score-bearing action is NOT what this proposal proposes. Its sequencing constraint (after the letter is sent, to avoid a referee asking why the audit apparatus left a paper under review) pushes any effect past the current review cycle entirely, and it restates the round-25 recommendation shape already on record rather than adding an executable step. Strategic publication advice, not a structure-score proposal; it belongs in a venue-strategy discussion with Eugene, not in this ranked list.

---

## Execution dedup note (coordinator addition, verified against the tex)

Two repairs appear under two dimensions each and must be executed ONCE, not twice:

1. **Graybill corroboration** — rigor's "move to the point of use" (targets tex 245/621) and evidence's "redeem the pointer" (targets tex 280/365) both repair the same dangling L86 `(Section~\ref{sec:pathb})` pointer; grep confirms `graybill2026` appears nowhere in the Path B region (tex 243–295). Execute as ONE edit set: pick the sites from both proposals that survive review together, and retire the L86 forward pointer's dangle in the same commit. Both entries' hedge constraint is identical: "the elasticity's evidential basis is the external literature alone" keeps its scope (Graybill IS external literature).
2. **SMD two-moment infeasibility promotion** — rigor's LOW entry and coherence's MEDIUM entry both insert near-identical sentences at the SAME point, tex 188 (§IV interpretation). Landing both verbatim would duplicate the sentence. Execute the coherence variant (MEDIUM, slightly fuller) once; count the rigor entry satisfied by it.

Verified by the coordinating session before this file entered the repo: tex 461's renormalization sentence (the K1 kill's load-bearing fact) verbatim; the outcome-holdout/"without exception" disclosures at exactly tex 80, 663, 730; tex 188's content; the Graybill absence from tex 243–295.

---

## Execution log — 2026-07-28, same day (Eugene: "1 yes, 2 yes, 3 no, 4 yes")

The queued re-review repairs landed first, per this file's sequencing rule:
- **NEW-2 + NEW-6a** (`5e5dee6`): L43's stale posture clause replaced with the L369 phrasing verbatim; the promoted appendix section's "This subsection" deixis fixed. Gate #104's `intro_pointer`, the L43 "positive at every" occurrence, and its binding-interval literal all preserved.
- **NEW-1** (`c5f68b2`) — **executed literal-neutral**: the binding interval entered §II in its and-form (`$+2.8$ and $+8.7$`, the abstract's own form), so the ×7/×5 zero-slack counts never moved and no gate/test/letter update was needed. The percentile's bare and-form is gone; a wild-cluster qualifier and under-coverage label are in the sentence.
- **NEW-3** (`8e2bb50`): §VI.C's summary now carries the incidence scope and denomination resolution with a pointer to the pricing section; the conclusion's par-crediting cross-ref re-aimed from `sec:abm-danish` to `sec:pathb`. Gate #103's `conclusion_sign` span untouched.
- **NEW-4** (`431a8db`): the seasonal-timing verdict row relabeled `Pass weakened: rule met as written; the timing claim withheld, levels only (against the headline)` — matching the caption's own taxonomy and the sibling rows' label.
- **NEW-5** (`95d9f6c`): letter §7 gains an eighth (presentational) item covering the online appendix, both elasticity exhibits, and the audit table; "Four of the **eight** items"; the "Two things"/"Three things" enumeration reconciled with manuscript L369, `$+11.2$`/`$+11.5$` kept inside the §7 window.

Then the approved posture set:
- **Posture #4** (`d600273`): inline `\par` at the "accounts for 91.3%." seam; abstract 366→367 words; letter recount and BOTH hard-coded test literals updated in the same commit; **366 added to the wrong-count parametrization** (the round-26 lesson: the wrong-count list carries every count that was ever true). 436 tests.
- **Posture #1** (`a6db8dd`): the paired design-crossing claimed at the L102 tail as a validation design in its own right; the ex-ante-thresholds clause scoped to the cross-design leg only; **indirect inference named as the nearest relative** per the external literature check (verdict SUPPORTED-WITH-CAVEAT: Platt 2020 and the Fagiolo-authors' JASSS companion read in full text; the 2017 successor survey and the 2024 JASSS overview also checked; none names the pair).
- **Posture #2** (`1a6287d`): VII.F split — the sweep-mechanics paragraphs, `tab:lowband`, the contamination-separation paragraphs, `tab:floorband`, and `tab:oosfloor` moved verbatim to a new `app:floormech`; a pointer paragraph in VII.F; **two positional-deixis repairs on kept lines** (the "stability threshold above" and "2019 leg was rejected above" callers now cite the appendix). Manuscript now 1356 lines.
- **Posture #3: declined by Eugene.** No submission-variant abstract; the ≤150-word remedy stays declined.

**Final state: 104 gates ALL PASS · 436 tests · zero-slack counts unchanged (7/5/7/5/6/8/10/11/0) · build 123pp, 0 undefined refs · conclusion p.78 · Online Appendix pp.85–123 · app:floormech p.105 · main text ends ~p.84 (was 87).** Everything else in this file — the wording/structural survivor set — remains unexecuted and is the natural queue for a next session; observe the dedup note above.
