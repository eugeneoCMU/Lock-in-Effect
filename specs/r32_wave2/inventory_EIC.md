# R32 condition inventory — EDITOR-IN-CHIEF REPORT

Source: `REVIEW3_v18_panel_2026-07-29.md` lines 123–204 (context read: lines 1–122).
Verification base: worktree `.claude/worktrees/agency-mbs-runoff-qt-424945`, branch `claude/brave-shaw-b02840`, HEAD `a785f3d`, working tree CLEAN (so the .tex verified here is the committed one). All `.tex` line numbers are `paper/v18/revised_paper_v18.tex`. Page numbers from `paper/v18/build_split/revised_paper_v18.aux` + `/Count` in the split PDFs (main 94pp, online appendix 45pp — both confirm the EIC's basis-of-review header).
Measurement conventions used below: "paragraph" = blank-line-delimited block (this is the convention that reproduces the panel's character counts); "words" = whitespace tokens of the .tex source (includes markup, so they run ~5–10% above the panel's .md prose counts).

---

### C-EIC-01
raiser: EIC
severity: MAJOR (inferred — the report grades no item individually; RECOMMENDATION names this as item 1 of the five whose repair "would move this to Minor Revision without a single new run")
class: WORDING
panel_lines: 142, 158
condition: The title asserts the program fell short, which §III.B concedes the paper does not show; the title must be brought down to the composition claim the paper establishes (e.g. "…and the Composition of the Federal Reserve's Agency-MBS Runoff") or narrowed to "…Redemption-Cap Shortfall."
location: `.tex:24` (`\title{...}`); the conceding sentence is `.tex:150` (§III.B, final sentence)
verified: true — `.tex:24` is exactly `\title{Mortgage Lock-In and the Federal Reserve's Quantitative Tightening Shortfall}` and `.tex:150` contains verbatim "not by itself evidence that a stated policy objective was missed". One nuance the EIC does not mention: `.tex:92` ("Definitions used throughout") already defines "shortfall" as cap-relative ("denote the net shortfall of realized roll-off against the phased redemption caps"), so the term is stipulated even though the title reads as an assertion.
fix: Retitle. Scope of a retitle is four live files: `paper/v18/revised_paper_v18.tex:24`, `paper/v18/revised_paper_v18_long_abstract.tex`, `paper/v18/response_to_referees_round22.tex`, and — load-bearing — `tools/liveness_gates.py:168`, where the exact title string sits in the `EXACTLY_ONE` list and will fail the gate suite unless updated in the same commit. (`paper/v16/*`, `paper/v17/*` also contain the string; they are archived editions and should not be touched.)

### C-EIC-02
raiser: EIC
severity: MAJOR (inferred — item 2 of the five named in RECOMMENDATION)
class: WORDING
panel_lines: 159
condition: The abstract's second paragraph says "and it identifies levels only", which flatly contradicts §V.E's opening sentence; the intended sense is "levels, not monthly timing" and must be written that way.
location: `.tex:31` (abstract, second paragraph) vs `.tex:319` (§V.E opening)
verified: true — `.tex:31` contains "identifies levels only"; `.tex:319` opens "The design does not identify the aggregate recovery level: the level is floor-dominated…". The EIC's reading of the intended sense is corroborated by the gate that pins the phrase: `tools/liveness_gates.py:2133` registers it as `levels_only_abstract` inside the seasonal-floor (timing-concession) gate cluster, alongside `levels_only_body` = "restrict every claim in this paper to levels" — i.e. the phrase was authored as the abstract's expression of the *timing* concession.
fix: Replace "and it identifies levels only" with "and it identifies levels, not monthly timing" at `.tex:31`. Must be applied together with `tools/liveness_gates.py:2133`, which pins the old string byte-exactly, and with `paper/v18/revised_paper_v18_long_abstract.tex` (the variant differs from the master at line 31 only).

### C-EIC-03
raiser: EIC
severity: MAJOR (inferred — item 3 of the five named in RECOMMENDATION)
class: WORDING
panel_lines: 160
condition: The abstract leads with 85.7% and 91.3%, which are recovery *levels* — the object §V.E's first sentence says the design does not identify; the null's share must be stated as the composition claim it is rather than as an identified level.
location: `.tex:31` region — abstract paragraph 1 (`.tex:31` holds both figures); §V.E `.tex:319`
verified: true — abstract paragraph 1 gives "switch the lock-in response off and the model still accounts for 85.7\% of it" and "A loan-by-loan model run on Freddie Mac data accounts for 91.3\%."; §V.E:319 declares the level unidentified. (Partial mitigation the EIC does not credit: the 85.7% sentence already carries a mechanism clause — "because scheduled amortization and baseline turnover … fall short of a \$35 billion monthly ceiling however the rate-responsive margin behaves" — which is a composition statement in substance.)
fix: Recast the two abstract sentences so the null's 85.7% is stated as a decomposition/composition share and the 91.3% as an in-sample fit description, not as identified levels; keep the §V.E disclaimer's language so the abstract and `.tex:319` cannot be read against each other.

### C-EIC-04
raiser: EIC
severity: MAJOR (inferred — same weakness item as C-EIC-03, but a separate mechanical edit)
class: WORDING
panel_lines: 160
condition: Neither abstract figure carries a floor label or a basis label; both must be attached.
location: `.tex:31` (abstract); the labelled forms exist at `.tex:66` (tab:headline caption: "recovery percentages are quoted on the benchmark-consistent shared basis"), `.tex:78` ("85.7\% of benchmark at the headline off-window floor; 88.7\% in-sample"), `.tex:82` ("91.3\% at the headline off-window floor; 97.9\% in-sample")
verified: true — the abstract text at `.tex:31` contains neither "shared basis" nor any floor label; Table 1 rows 3 and 4 carry both, so the labels the abstract needs already exist as committed strings.
fix: Add the two labels inline in the abstract ("on the benchmark-consistent shared basis, at the off-window floor calibration"), reusing the committed wording from `.tex:66/78/82` so no new literal enters the manuscript.

### C-EIC-05
raiser: EIC
severity: MAJOR (inferred — item 4 of the five named in RECOMMENDATION; the EIC calls it "the finding that changes how the QT record is read")
class: WORDING
panel_lines: 140, 161
condition: The abstract omits the paper's most novel result — the expectations-based complement (\$87.8 billion, 11.5% of the cap-relative benchmark), which is affirmative contribution #2 in the introduction and row 2 of Table 1. One sentence is required.
location: `.tex:30–31` (abstract, omission); present at `.tex:60` (intro contribution #2), `.tex:77` (tab:headline row 2), `.tex:142/150/152` (§III.B), `.tex:590/613` (§VI.D), `.tex:795` (App. A), `.tex:1354` (App. N)
verified: true — "87.8" occurs at eight line-sites, none of them the abstract (`.tex:30–31`); `.tex:60` begins the contribution list and `.tex:77` is the Table 1 row, both as the EIC describes.
fix: One abstract sentence quoting the committed pair (\$87.8 billion / 11.5%) and naming it as measured against the Fed's own ex-ante projection rather than the cap. No new number is created — all literals already appear at `.tex:77`.

### C-EIC-06
raiser: EIC
severity: MAJOR (inferred — item 5 of the five named in RECOMMENDATION)
class: WORDING
panel_lines: 162
condition: +5.6 is defended as "an anchor convention rather than a central tendency" and §V.E attaches no posture to it, yet it is quoted as the paper's number throughout. Either drop the point from the abstract and title-level framing and report the interval, or defend the anchor on stated grounds.
location: `.tex:79` (tab:headline row 4, the "anchor convention" defense), `.tex:333` (§V.E "attach no posture"); the quoting sites are `.tex:31` (abstract), `.tex:46/58/92` (§I), `.tex:110` (§II), `.tex:211` (§V.A), `.tex:323 ×3 / 333 ×2 / 342 / 345 / 368 / 433` (§V.E), `.tex:524` (§V.F), `.tex:635` (§VII.B), `.tex:711 ×2 / 713` (§VII.F), `.tex:725/731` (§VIII), `.tex:797` (App. A), `.tex:1413` (App. O)
verified: partly — the two quoted defenses are verbatim at `.tex:79` and `.tex:333`, and the circulation complaint is *understated* (24 occurrences of `$+5.6$` across 21 lines). But two of the five sites the EIC names are wrong: §VI (`.tex:530–622`) contains no `+5.6` anywhere, so there is no "§VI.A welfare paragraph" instance; and Table 12 (tab:wal, `.tex:548–574`) prints no `+5.6` — the "5.6" at `.tex:560` is a *weighted-average life in years* (Production ABM, Nov. 2025), a numeric collision. The tab:wal row that does depend on the headline calibration is `.tex:565` (floor read 4.99%), which prints 9.5/8.6.
fix: Either (a) remove the point estimate from `.tex:31` and from the §I framing at `.tex:46/58` and quote `[+2.9, +8.7]` there, keeping +5.6 only where the anchor is being explained (`.tex:79`, `.tex:333`); or (b) write a stated defense of the anchor (why the mid-grid point is the reportable one) and drop the "no posture" disclaimer, which currently cancels the headline's own warrant. Whichever branch is taken must be applied consistently to §VIII (`.tex:725/731`) or the abstract and conclusion will disagree.

### C-EIC-07
raiser: EIC
severity: MAJOR (inferred — RECOMMENDATION makes "a stated resolution of the form fork" the sixth condition for Minor Revision; the CARROLL ROUND note calls it "the only question that can sink the defense")
class: CHECK
panel_lines: 163, 201
condition: The floor's functional-form fork roughly doubles the answer (+11.2 additive vs +5.6 max) and is left open; §V.B's own "strictly-involuntary share is plausibly well under half" points toward the additive end on the paper's measured mixture curve. The fork must be resolved (a stated selection rule) rather than disclosed.
location: §VII.F `.tex:709` (the whole fork lives in one 6,835-char paragraph); §V.B `.tex:227` and §I `.tex:92` carry the "plausibly well under half" reading
verified: true — `.tex:709` contains, verbatim: the additive marginal at the production floor (+11.25, a +2.05 shift past the ex-ante ±1-point immateriality threshold); near floor-invariance off-window (+11.22/+11.21/+11.19 at 4.695/4.991/5.334%); the mixture curve (+7.5 at s=0.1, +9.7 at s=0.25, +10.7 at s=0.4, "flat near $+11.2$ from $s = 0.6$ up"); the concession that "the near-coincidence defense of the max form at the deep-discount anchor does not extend to the shallow-gap off-window anchors"; and the explicit statement that the well-under-half reading "does *not* pull the marginal toward the max end". The level cost is also there (central additive leg recovers 55.9% vs 91.3% max-form at the 4.991% anchor).
fix: No new run is needed — `hazard/data/floor_form_mixture_results.json` and `floor_form_offwindow_results.json` already measure the curve and its endpoints. What is missing is a *selection rule* stated in the manuscript that does not rest on aggregate fit (the paper forecloses fit: "the design does not identify levels", `.tex:709`/`.tex:319`). Two admissible resolutions: (i) argue the semantics claim explicitly as a prior over s and report the marginal at that s; or (ii) promote the form-robust statement already written at the end of `.tex:709` ("roughly $+9$ to $+11$ points at the production floor" — note this is the *production-floor* form-robust band, not the off-window one) to headline status, which changes the abstract. Either way the choice must be stated once and inherited by `.tex:31` and `.tex:731`.

### C-EIC-08
raiser: EIC
severity: MAJOR (inferred — the alternative branch of weakness 6's own "Fix:")
class: WORDING
panel_lines: 163
condition: If the fork is not resolved, the abstract's topic sentence must be form-conditional rather than relegating form-conditionality to a fourth sentence.
location: `.tex:31` (abstract paragraph 2)
verified: partly — the abstract is *not* form-silent: sentence 2 already says "under its production floor form" and carries "a form-conditional hull of $+3.5$ to $+13.1$ points", and the final sentence says "the additive form roughly doubles the margin". What is unconditioned is the paragraph-2 topic sentence ("What lock-in itself adds is a range rather than a number") and the paragraph-1 sentences carrying 85.7%/91.3%. The EIC's "fourth sentence" is the fifth and last of paragraph 2.
fix: Move the form condition into the topic sentence of abstract paragraph 2 (and into the 85.7%/91.3% sentences, whose *levels* are the strongly form-dependent quantities: 91.3% max-form vs 55.9% additive at the same anchor, `.tex:709`). Coordinate with C-EIC-03/04 — all three are edits to `.tex:31`.

### C-EIC-09
raiser: EIC
severity: MAJOR (inferred — stated as a standalone weakness, item 7)
class: WORDING
panel_lines: 164
condition: §VIII concedes its own policy conclusion is an artifact of the form choice — the trilemma dissolution "reduces to 'the marginal is small'" and under the production form the marginal is "bounded small by construction" — so the conclusion must be *stated as* form-conditional, not restated flat after the concession.
location: §VIII `.tex:731` (4,470-char paragraph); the same concession also appears at `.tex:528` (§V.F)
verified: partly — the concession is verbatim at `.tex:731` ("reduces to ``the marginal is small''---and under the production floor form the marginal is bounded small by construction"), but the paragraph does *not* restate the conclusion flat afterwards: it continues "The dissolution is therefore a statement about a calibrated ceiling, not an independent finding, and it is form-conditional: under the disclosed additive form … roughly doubles to about $+11$ points … What survives across forms is that the trade-off is modest, not that it is absent." The live defect is ordering, not omission: the paragraph *opens* with the flat claim ("this paper's evidence is that they do not form the strict trilemma") ~2,900 characters before the qualification arrives.
fix: Reorder `.tex:731` so the form condition sits in its opening clause (or split the paragraph at "What this dissolution rests on is thinner than the framing suggests" with a `\paragraph` head, which also serves C-EIC-14). No new content is required — the qualifying sentences already exist and must not be deleted.

### C-EIC-10
raiser: EIC
severity: MINOR (inferred — not in the 1–5 blocking set; the fix the EIC names is wording-only)
class: REFERENCE
panel_lines: 165
condition: The Danish channel rests on one unrefereed source (`berger2026`, an SSRN working paper); the source's status must be flagged in text.
location: `paper/v18/references.bib:61–67`; the §VI.D importing paragraph is `.tex:586`
verified: partly — the bib entry is exactly as the EIC reports (`@misc{berger2026 … howpublished = {Working paper, {SSRN} abstract 6150766}`), but the manuscript already flags it once: §II `.tex:112` reads "\citet[\S3.2.3]{berger2026}, in a January 2026 SSRN working draft". What is missing is the flag at the §VI.D site (`.tex:586`) where the estimates are actually imported and the source's own counterfactual is overruled.
fix: Add the status clause at `.tex:586` reusing the §II wording ("a January 2026 SSRN working draft"), so the reader meets the caveat where the load is carried rather than 60pp earlier.

### C-EIC-11
raiser: EIC
severity: MINOR (inferred — wording-only fix, outside the 1–5 blocking set, but it is the EIC's "should a single-authored paper rest a channel dismissal on this" point)
class: WORDING
panel_lines: 165
condition: §VI.D overrules its source's US tax counterfactual on a single-authored legal reading; the tax point must be stated as one reading of US law that the paper does not adjudicate, not as a correction to the source.
location: §VI.D `.tex:586`
verified: true — `.tex:586` reads "per Berger et al.'s own counterfactual --- a characterization U.S. law does not support: a discount extinguishment is cancellation-of-debt income at ordinary rates, IRC \S 61(a)(11), and post-TCJA the assumed interest deduction overstates most households' marginal benefit; both corrections push the U.S.-transplant channel *below* Berger et al.'s already-small estimate". "does not support" and "both corrections" are exactly the assertive framing the EIC objects to.
fix: Rewrite the parenthesis at `.tex:586` as a reading rather than a correction ("on one reading of U.S. law — a discount extinguishment is cancellation-of-debt income … — a reading this paper does not adjudicate; under it, the channel falls further below Berger et al.'s already-small estimate, and it leaves the realized Danish evidence untouched either way"). The direction-of-effect sentence and the "neither touches the realized Danish evidence" clause must survive the edit.

### C-EIC-12
raiser: EIC
severity: MINOR (inferred — submission mechanics; blocking only for a double-blind venue, not for the talk)
class: META
panel_lines: 166
condition: `\author{Eugene Ong}` / `\affil{Carnegie Mellon University}` plus a live GitHub URL with an identifiable handle in Appendix A preclude double-blind submission; an anonymized master is required, with an archived DOI (Zenodo) standing in for the repo URL.
location: `.tex:25–26`; `.tex:758` (App. A, "Data and code availability")
verified: true — `.tex:25` `\author{Eugene Ong}`, `.tex:26` `\affil{Carnegie Mellon University}`, and `.tex:758` contains `\url{https://github.com/eugeneoCMU/Lock-in-Effect}` (handle `eugeneoCMU` is identifying).
fix: Produce an anonymized build variant (author/affil suppressed, `.tex:758` URL replaced by a DOI placeholder). Note this is a *new artifact*, not an edit to the master: the split/variant build machinery already produces `revised_paper_v18_long_abstract.tex`, so an `_anon` variant is the same pattern. Zenodo minting is an Eugene-only action (outside-repo publishing).

### C-EIC-13
raiser: EIC
severity: MAJOR (inferred — "Not defensible as submitted"; the RECOMMENDATION conditions sending it out on compression)
class: STRUCTURE
panel_lines: 170, 197
condition: Length is not defensible: ~43,200 words over 94pp of main text against a 12,000–15,000-word field norm, plus ~18,600 words of appendix; §V.B (6,710 words) and §V.E (5,543) hold an entire article between two headings, and subsection lengths span 134 to 6,710 words — a ~50× spread that shows structure is not carrying the load. Main text must come down to ~15,000 words.
location: whole main text `.tex:38–751`; the two outliers are §V.B `.tex:217–306` and §V.E `.tex:317–468`; the short pole is §VI.C `.tex:578–581`
verified: partly — every measurable component checks out to within a few percent, on .tex whitespace tokens: main text 45,192 tokens over 94 pages (`build_split/revised_paper_v18_main.pdf` `/Count 94`), appendix 20,291 tokens over 45 pages, §V.B 7,294 (pp.26–38), §V.E 6,193 (pp.41–52), §VI.C 127 (p.63) — a 57× spread. The panel's slightly lower figures are .md prose counts, so the direction and magnitude hold. The "12,000–15,000 field-journal norm" is an editorial assertion with nothing in-repo to check it against.
fix: Execute the five concrete cuts the EIC itemizes (C-EIC-17 … C-EIC-21). Note the hard constraint: 108 liveness gates and 495 tests pin hundreds of manuscript strings, so any cut must be a *move* (text relocated to an appendix, literals preserved) rather than a deletion — `tools/liveness_gates.py` matches on `tex` as one string, so relocation within the same file is gate-safe while deletion is not.

### C-EIC-14
raiser: EIC
severity: MAJOR (inferred — "a 2,200-word paragraph is a scoring fact, not a courtesy deduction"; Writing Quality scored 52)
class: STRUCTURE
panel_lines: 172, 179
condition: The paragraph architecture is not defensible: the longest body paragraph is 14,732 characters (~2,200 words) in §V.B, then 11,312 (§V.E), 10,696 (Appendix G), 8,051 (§V.B again); the EIC could not audit §V.B by reading and had to extract substrings. Oversized paragraphs must be split at their own topic boundaries with `\paragraph` heads.
location: `.tex:219–231` (§V.B, 14,732 chars), `.tex:319–323` (§V.E, 11,312), `.tex:1099–1100` (Appendix G / `app:ridge`, 10,696), `.tex:269` (§V.B, 8,051)
verified: partly — all four cited sizes reproduce exactly on blank-line-delimited blocks, and the §V.B block does typeset as one paragraph. Two corrections: (i) the 14,732-char block spans 13 source lines and includes three display equations (`eq:pathB`, `eq:default`, `eq:beta1`), so it is 1,977 whitespace tokens and its longest *uninterrupted* prose run is 7,348 chars at `.tex:231` — "~2,200 words" is ~11% high; (ii) "the four >6,000-character paragraphs" undercounts badly — 11 prose blocks exceed 6,000 chars (`.tex` lines 219, 319, 1099, 269, 277, 713, 709, 150, 590, 333, 315), plus two oversized table blocks (`.tex:1397`, `.tex:813`).
fix: Insert `\paragraph{...}` heads at topic boundaries in all 11 oversized prose blocks (not four). Cheapest high-value targets, because they are the ones a referee must audit: `.tex:219–231` (§V.B specification), `.tex:319–323` (§V.E first qualification), `.tex:709` (the form fork — also serves C-EIC-07), `.tex:731` (the conclusion — also serves C-EIC-09). Splitting a paragraph does not move any literal, so it is gate-neutral; the render gate (`tools/render_gate.py`) must still be re-run because float placement shifts.

### C-EIC-15
raiser: EIC
severity: MINOR (inferred — part of the Writing Quality judgment, no separate "Fix:" given)
class: WORDING
panel_lines: 172
condition: Sentences routinely nest four to six parentheticals and three or more em-dash asides; the nesting must come down.
location: main text `.tex:38–751`; worst offenders `.tex:731`, `.tex:433`, `.tex:227`, `.tex:349`
verified: true — 21 main-text sentences carry ≥4 parenthesized spans or ≥3 em-dash asides; the maxima are `.tex:731` (11 parenthesized spans in one sentence, though 3 of them are the trilemma's numbered legs "(1)(2)(3)") and `.tex:227` (6). So "routinely" is supported at roughly 21 sites, not as a pervasive property of all prose.
fix: De-nest the 21 sentences — promote the load-bearing parentheticals to their own sentences and demote the rest to footnotes or tablenotes. Every parenthetical carrying a committed number must be preserved verbatim somewhere in the same file (gate strings are matched against the whole `.tex`).

### C-EIC-16
raiser: EIC
severity: MINOR (inferred — cited as evidence inside the presentation judgment)
class: STRUCTURE
panel_lines: 172
condition: Table 8's cells run past 900 characters.
location: `tab:uncertainty` = Table 8, `.tex:420–437`; the offending row is `.tex:433`
verified: partly — the headline row `.tex:433` is 2,089 chars and its fourth cell (Calibration range) is 1,411 chars, so one cell is well past 900. But no other cell in the table exceeds 601 chars (row 431 is 410 chars total, row 432 253, row 435 455), so "cells" plural overstates: exactly one cell is over 900.
fix: Move the 1,411-char calibration-range cell's catalogue into the existing tablenote block at `.tex:440` (already 2,828 chars and already the table's prose annex), leaving a pointer in the cell — the same pattern `tab:ladder` uses at `.tex:467` and `tab:headline` at `.tex:90`. Text-preserving, so gate-safe.

### C-EIC-17
raiser: EIC
severity: MAJOR (inferred — the largest of the five prescribed cuts)
class: STRUCTURE
panel_lines: 175
condition: §IV + §VII.A + §VII.C + §VII.D must come down to ~2pp: report the ABM's negative result and the cross-design verdict in the main text and move the rest to the appendix. The EIC's grounds: the ABM is ~13% of the main text and 0% of the abstract, it admits no null (the two §IV.B readings give +270.4 and −105.3 points, disagreeing in sign), and its cross-design leg crosses the pre-committed undercutting threshold on all fifty seeds.
location: §IV `.tex:154–179` (pp.20–23), §VII.A `.tex:629–632` (p.69), §VII.C `.tex:637–686` (pp.71–74), §VII.D `.tex:687–690` (p.75)
verified: partly — three of the four supporting facts are exact: the sign-disagreeing null readings +270.4 / −105.3 are at `.tex:178` (§IV.B); "all fifty seeds classify as undercutting" is verbatim at `.tex:645`; and the abstract contains no ABM mention (zero "agent-based" in `.tex:30–31`). The "~13% of the main text" figure is high: the four subsections are 10 of 94 main pages (10.6%) and 4,363 of 45,192 tokens (9.7%); §IV alone is 4 pages / 3.7%. Also worth flagging for the coordinator: §VII.A is genuinely ABM material (`.tex:631` opens "The ABM's 10,000-household population…"), so the bundling is right even though the percentage is not.
fix: Retain in main text: the ABM's negative verdict, the +270.4/−105.3 no-null finding (`.tex:178`), and §VII.C's fifty-seed undercutting verdict (`.tex:645`). Relocate the construction/diagnostic prose of `.tex:631`, `.tex:637–644`, `.tex:646–686`, `.tex:687–690` to the ABM appendices (`sec:method-abm` `.tex:880`, `app:abmspec` `.tex:931`). Relocation only — `tab:crossdesign` is Table 14 and its literals are gate-pinned.

### C-EIC-18
raiser: EIC
severity: MAJOR (inferred — one of the five prescribed cuts)
class: STRUCTURE
panel_lines: 176
condition: §V.B must come down to ~2,500 words: move the κ-grid / floor-dispersion material to Appendix N (where its Jensen diagnosis already lives) and the Ginnie/vintage overlay construction to Appendix I.
location: §V.B `.tex:217–306` (7,294 tokens, pp.26–38); κ-grid/floor-dispersion prose at `.tex:263`, `.tex:265`, `.tex:267` (5,978 chars combined); Ginnie material distributed across the subsection (24 occurrences of "Ginnie" in the range); destinations Appendix N `sec:robustness-seasonalfloor` `.tex:1342` (Jensen diagnosis at `.tex:1350`) and Appendix I `app:composition` `.tex:1265`
verified: true — all four premises check: the subsection is the longest in the paper, the κ/dispersion paragraphs are exactly the three lines above, Appendix N already carries "a Jensen effect operating through the floor's combination rule" at `.tex:1350`, and Appendix I is the composition appendix.
fix: Move `.tex:263/265/267` into Appendix N adjacent to `.tex:1350`, and the Ginnie/vintage overlay construction into Appendix I, leaving one-sentence pointers. Both destinations already exist, so this is a pure relocation; verify afterwards that §V.B's remaining cross-references (`Section~\ref{sec:robustness-seasonalfloor}`, `app:composition`) still resolve in the direction the prose asserts.

### C-EIC-19
raiser: EIC
severity: MAJOR (inferred — one of the five prescribed cuts)
class: STRUCTURE
panel_lines: 177
condition: §V.E must come down to ~2,500 words, keeping the seven qualifications and Table 5 and moving the group-ablation placebo and the composition decomposition to an appendix.
location: §V.E `.tex:317–468` (6,193 tokens, pp.41–52); keep `tab:assembly` (Table 5) at `.tex:338` and the seven qualifications; move the group-ablation material at `.tex:323` / `.tex:325` and `fig:marginalcells` `.tex:410–415`
verified: true — §V.E is the second-longest subsection; the group-ablation decomposition is at `.tex:323` and its figure caption at `.tex:413` ("Group-ablation decomposition of the lock-in marginal over the vintage × coupon grid"); the composition qualification is the 3,979-char paragraph at `.tex:325` ("A fourth qualification concerns composition"); `tab:assembly` is Table 5 as the EIC says.
fix: Relocate `.tex:325` and the group-ablation prose+figure to `app:composition` (`.tex:1265`) or `app:floormech` (`.tex:1301`), leaving the qualification's verdict sentence in place so the "seven qualifications" count and the Table 27 ledger's cross-references stay true. The fourth qualification cannot be deleted (it is a disclosure) — only moved.

### C-EIC-20
raiser: EIC
severity: MAJOR (inferred — one of the five prescribed cuts)
class: STRUCTURE
panel_lines: 178
condition: §VI.D must come down to ~3pp, with the sweep mechanics and the redemption-validation confounds moved to an appendix.
location: §VI.D `.tex:582–622` (2,735 tokens, pp.63–68 = 6pp)
verified: true — the subsection currently runs six pages, so "→ ~3pp" is a halving; it contains the anchor/incidence sweep prose (`.tex:590`, 6,583 chars) that the cut targets.
fix: Move the sweep mechanics (`.tex:590` and neighbours) and the redemption-validation confounds to a new or existing appendix section (`SPEC_danish_redemption_validation_2026-07-28.md` documents the validation design, and `tab:danish` is Table 13). Keep in main text: the +\$61.2bn / −\$99.9bn / cash-haircut bracket and the forced-sign disclosure, all of which are quoted in §VIII (`.tex:727/731`).

### C-EIC-21
raiser: EIC
severity: MINOR (inferred — a one-line structural tidy inside the cut list)
class: STRUCTURE
panel_lines: 179
condition: §VI.C's 134 words must be folded into §VI.B.
location: §VI.C `sec:discussion-policy` `.tex:578–581` (127 tokens, p.63); destination §VI.B `sec:discussion-capdesign` `.tex:544–577`
verified: true — §VI.C is 127 whitespace tokens on one page, the shortest subsection in the paper and the short pole of the 57× spread; §VI.B immediately precedes it.
fix: Delete the `\subsection` head at `.tex:578` and append its paragraph to §VI.B, then repoint any `\ref{sec:discussion-policy}` in the `.tex`. Checked: no gate or test references `sec:discussion-policy`, and the only ordering assertions in the gate suite (`tools/liveness_gates.py:818–821`) concern `tab:ladder` rows, not section order — so this fold is gate-free apart from the label repoint.

### C-EIC-22
raiser: EIC
severity: MINOR (inferred — the CARROLL ROUND verdict is "Ready to present and defend as-is", conditioned on this one preparation)
class: META
panel_lines: 201
condition: Before the Carroll Round the author must rehearse a 60-second answer to "what is your number, and why isn't it +11?" — the form fork is the only question that can sink the defense.
location: n/a (talk preparation, not a manuscript site; the substance is §VII.F `.tex:709`)
verified: true as a statement of the panel's condition; not a manuscript premise, so nothing in-repo to falsify. The underlying asymmetry it rests on is verified under C-EIC-07.
fix: Draft the 60-second answer from the committed material at `.tex:709`: s=0 is the conservative endpoint of a *measured* curve (not a fitted choice), the max form's semantics is the deep-discount calibration's own reading, the additive form pays 43.5–45.3 points of aggregate level at every off-window anchor, and the form-robust statement is "+9 to +11 at the production floor / positive under every level, band and form tested". Eugene-only deliverable; it does not require a manuscript edit, but it is inconsistent to rehearse it while C-EIC-07 remains unstated in the paper.

---

## Anti-condition cross-check

None of the ten pre-adjudicated anti-conditions is raised by the EIC report. Specifically:
- Anti-condition 2 (abstract single paragraph): the EIC correctly treats the abstract as two paragraphs ("The abstract's second paragraph…", panel line 159); `\par` is at `.tex:31`. No row needed.
- Anti-condition 3 (no Table 27 row moved a number): the EIC asserts the *opposite* — its STRENGTHS item 3 credits the floor demotion with moving +9.2 → +5.6 and 97.9% → 91.3%. No row needed.
- Anti-condition 6 (paper headlines the Danish minimum): the EIC's SUMMARY quotes the Danish result as a range ("+\$61.2bn to +\$256.8bn … reversing under a cash-haircut reading"), so it does not raise the anti-condition. No row needed.
- Anti-conditions 1, 4, 5, 7, 8, 9 and item 10 (R2:M8) belong to other reviewers' sections; the EIC report does not mention them.
