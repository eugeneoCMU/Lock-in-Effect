# DRAFT — WP-E item 4 (policy section): cap-design promotion, band restatement, tab:wal move

**Status: DRAFT ONLY. Nothing applied, nothing run, no .tex touched, no gate or test touched.**
Drafted 2026-07-29 against `ed33a06` (worktree `paper-v18-review-plan-5b7b5e`).

**Source of the task:** `PLAN_review2_fixes_2026-07-28.md` WP-E item 4; underlying findings
REVIEW2 R3-W5 (state-contingent cap → band), the arbitrated cap-design split (REVIEW2
"Consensus analysis" → *promote the result; attribute the observation; claim only the
arithmetic*), and the WAL/normal-turnover ask the plan tags `R3-W3`.

---

## 0. Read this before applying: line numbers are stale by construction

The manuscript moved **three times while this draft was being written** (`9deda21` S8,
`31747c7` C6(ii), `9be0c34` I1): 1415 → 1416 → 1417 lines. Every line number below is
*as of `ed33a06`* and is informational only. **Every edit in §4 is anchored on a
string whose occurrence count is asserted — apply by anchor, re-derive the count first,
and never by line number.**

---

## 1. Target resolution: the plan says "§VII (policy)"; the policy material is §VI.B

Verified section numbering in the current tex: I Introduction, II Literature Review,
III Empirical Methodology, IV ABM, V Hazard Framework, **VI Discussion**, VII Robustness
Checks, VIII Conclusion. The REVIEW2 panel uses the same numbering (it cites "§VII.D's
synthetic companion", which is `sec:robustness-synthesis`). So **"§VII (policy)" in the
plan is a slip for §VI.B `sec:discussion-policy`** — that is where the cap-design
arithmetic, the state-contingent cap and the assumability/portability lever actually live
(`\subsection{Evaluating Alternative Securitization Policies}`, currently L450–L454).
`wal_table.py`'s docstring still says "§VII" for the same reason: the WAL material was a
§VII robustness subsection before round 26 moved it to the online appendix.

**Placement of the promoted subsection.** "Directly after the benchmark-complement
discussion" cannot be literal — the expectations-based complement is §III.B
(`sec:method-benchmark`, L146/L148) and the new subsection lives in the policy section.
The nearest in-region referent is §VI.A's benchmark paragraph (L444: "The \$764.7 billion
shortfall-versus-cap is, per the decomposition above, mostly mechanical: a gap to a cap
schedule that no plausible prepayment environment would have met"), which is also where
both existing WAL citations sit (L444, L446).

**Choice (primary):** the new subsection is inserted **between §VI.A
(`sec:discussion-fallout`) and §VI.B (`sec:discussion-policy`)** — i.e. directly after the
benchmark/duration paragraphs, and ahead of the contract-side levers. This is what
"promoted" means under the arbitration (three of five reviewers call the arithmetic the
citable core), and it puts `tab:wal` next to the §VI.A paragraphs that cite it.
**Fallback (Option P-B, one-line change):** insert it *after* `sec:discussion-policy`'s
assumability paragraph instead, which preserves the old "A second lever" ordering language
and is a smaller diff. Consequences of the primary choice are handled in §4 (E2 rewrites
the "A second lever" opener; the Danish subsection's "A third alternative acts on the
payoff rule itself rather than on the mortgage contract's portability or the redemption
cap" is order-agnostic and needs **no** edit under either option — verified).

---

## 2. Pinned-span inventory for the zones this touches

Method: every string constant ≥10 chars was extracted from `tools/liveness_gates.py` by
AST parse and tested against each target line; f-string-constructed pins (which the AST
scan cannot see whole) were read out of the gate bodies by hand. `tests/` was grepped for
`wal`, `discussion-policy`, `nyfed`, `1.7 to 1.9`, `computable` — **no test pins anything
in these zones** (the only `wal` hit in `tests/` is the word "walk" in a comment).

### 2.1 HARD pins inside the moved/edited material — must survive **verbatim**

| Pin | Gate | Where | Rule |
|---|---|---|---|
| `(5.61\%) & 9.1 & 8.2` | **#44** (`cross-check danish wal rows`) | `tab:wal` row "Danish rule-only leg, production anchor" | built by f-string from `wal_table_results.json`; the substring is row-internal, so **adding rows is safe, editing this row is not** |
| `(3.39\%) & 10.8 & 9.6` | **#44** | `tab:wal` row "Danish-level bracketing leg" | same |
| `0.6-year rule-only shortening` | **#44** | WAL closing prose (L1315) | prose stays in the appendix under this draft; if the closing prose is ever moved too, this literal must move with it |

Gate #44 reads `hazard/data/wal_table_results.json` and reconstructs the three literals at
run time. **Consequence: any edit that regenerates that artifact re-derives these pins.**
This is the single largest hazard in the "normal-turnover row" branch (see §3).

### 2.2 SOFT pins (whole-file presence/count, all `>=` or `in tex`) touched by this edit

- `"in-sample calibration point"` — presence-only, gate on `oos_identification`
  (`liveness_gates.py:1605`); present on L438/L448/L454/L601 and elsewhere. E2 keeps it.
- `"decomposition"` — appears in gate bodies as a dict key, not as a tex pin. No count.
- `$+2.1$ to $+13.2$` (6 sites), `88.7\%` (20), `85.7\%` (21), `\$740.6` (3),
  `1.7 to 1.9` (2), `$20--\$30` (1), `\$35 billion` (14) — **none is gate-counted**;
  all are preserved by E2 anyway.
- Banned-literal lists that the new text must not collide with (`ZERO_COUNT`,
  `EXACTLY_ONE`, `SUPERSEDED_CONTEXTUAL{'894.8': 'spec v3'}`): checked, **no collision**
  in any string drafted below. The round-28 `93.4\%` incident is the precedent — the gate
  suite catches these, but check before, not after.
- `HARDCODED_XREF`: literal `Table~N`, `Figure~N`, `Section~IV`, `Appendix~A`,
  `equation~(N)` forms are **zero-count gated**. All new cross-references below use
  `\ref{}`. Verified against every drafted string.

### 2.3 Pins in the same *neighbourhood* that this edit must NOT disturb

- **Gate #103 (buyback bracket)** spans live in the **conclusion** (L607/L611:
  `trilemma_conditional`, `dissolution_scope`, `conclusion_sign`, `reversal_range`,
  `run_tag`) and in §V's pathb paragraph. **This edit does not touch L607/L611.** If the
  applying session is tempted to harmonise the conclusion's cap language with the new
  subsection, stop: that is a separate, gate-pinned commit.
- **Gate #98** (assembly spans, incl. `posture_retired_range_carries`,
  `posture_binding_layer`) and **#99** (abstract spans) — §V and abstract; untouched.
- **Gate #100** (§IV lead order) — untouched.
- **Gate #101** (letter): `LETTER_CURRENT_LITERALS` must all still exist in the tex.
  E2 removes **no** literal from that list (checked item by item), and the abstract word
  count is untouched, so the letter needs **no** recount for this edit. It should still
  gain one sentence in §7 of the letter describing the structural move (see §7 below).

### 2.4 Label integrity

- New label `sec:discussion-capdesign` — **`capdesign` occurs 0 times** in the tex today.
- `\ref{sec:discussion-policy}` has exactly **2** occurrences: the label itself (L450) and
  the Introduction's contributions pointer (L59). E3 re-points L59; the label survives on
  the (retained) assumability subsection.
- `\ref{tab:wal}` has **3** occurrences (L777 App. B, L1288 WAL lead, L1320 fold-in
  appendix). All three keep resolving after the float moves — LaTeX `\ref` is
  position-independent; only the *direction* of the reference changes.
- `\ref{sec:robustness-wal}` has **4** occurrences (L263, L444, L446, L506). The section
  survives; only its table leaves. See §6 (A5) for the one honest wording consequence.

---

## 3. The normal-turnover row (R3-W3): sourcing verdict

### Verdict: **NOT DRAFTABLE WITHOUT A RUN.** No committed WAL exists at any
### normal-turnover speed, and the row cannot be computed from a committed number
### without executing `hazard/wal_table.py`.

**What the machinery is.** `hazard/wal_table.py` holds a hard-coded `SCENARIOS` dict of
nine speeds and writes `hazard/data/wal_table_results.json`; the printed table is exactly
that artifact's `rows`. The committed rows are: `scheduled_only` 0% → 14.7/12.6;
`empirical` 5.14% → 9.4/8.5; `abm` 11.68% → 6.0/5.6; `path_a` 3.34% → 10.9/9.7;
`path_a_specv3` 3.51% → 10.7/9.5; `path_b` 4.76% → 9.7/8.7; `no_shock_2021_speeds` 22.81%
→ 3.4/3.3; `danish_us_intercept` 5.61% → 9.1/8.2; `danish_level` 3.39% → 10.8/9.6.
**There is no tenth row and no normal-turnover scenario.**

**Committed pre-QT turnover *speeds* that exist** (so the run, if authorised, has an
anchor — this is the useful half of the finding):

| Candidate | Value | Committed at | Status |
|---|---|---|---|
| 2018 rising-rate leg, OTM, age≥12, three depths | **4.70 / 4.99 / 5.33 %** | `oos_identification_results.json → instrument1_oow_floor.defensible_clean_floor` (4.695/4.991/5.334); printed in `tab:oosfloor` at 2 dp | **defensible**; this is the paper's own headline floor band |
| Pooled 2017–2019, OTM, age≥12 | **6.07 %** | `out_of_window_floor_results.json → headline_out_of_window_floor_cpr_pct` = 6.065; printed `tab:oosfloor` | adjudicated **refi-contaminated** by the paper's own run |
| 2019 falling leg, OTM | **6.91 %** | same artifacts | **refi-contaminated** |
| 2021 realized (already the table's last row) | 22.81 % | `wal_table.py:58`, artifact | refi **boom**, not turnover |
| Ginnie/Fannie/Freddie CPR series 2017-06→2025-11 | monthly series | `hazard/data/gmar_dec25_cpr_series.json` | whole-market CPR **including refi**; any pre-QT mean would be a *new derived number*, and the series is cited in the paper only for the Ginnie−Freddie differential |

**The "~8% pre-QT norm" does not exist as a committed speed.** The only committed `8%` in
this neighbourhood is `abm_external_gates_results.json → floor_diagnostic.cpr_at_8pct_market
= 0.0`, which is *CPR at an 8% market rate*, not an 8% turnover speed. Do not use it.

**Why a committed speed still does not give a row.** Printing `(x\%) & W1 & W2` requires
`W1`,`W2`, which exist nowhere; producing them means adding a `SCENARIOS` entry and
executing `wal_table.py`. That is run-class, it is forbidden to agents by standing repo
rule, and it **rewrites `wal_table_results.json`, which gate #44 reads to reconstruct the
two Danish row pins** — the same class of hazard as C4's gate-#84 clobber. If Eugene wants
the printed row, it needs a spec with: (i) the chosen anchor and why; (ii) an
artifact-overwrite guard or a floor-tagged output path; (iii) a pre-committed statement
that the nine existing rows must come back **bit-identical** (they are deterministic, so
this is a real parity gate, not a formality); (iv) the landing rule for the row's label.

**And the anchor choice is itself contested**, which is a second reason the run-free
alternative is the better round-28 landing: every candidate is either the *floor* (OTM-
conditioned, i.e. the paper's own lower-bound object, not a "normal" speed), or
adjudicated contaminated, or whole-market including refinancing. A row labelled "normal
turnover" at 4.99% would be the floor wearing a different name — and the floor already
has a table.

### Run-free alternative, drafted below as **E4**: a tablenote

The tablenote states the benchmark and cites its source, introduces **zero new numeric
literals** (every value it quotes is already printed in `tab:oosfloor`), and discloses the
absence rather than papering over it. It also fixes the actual complaint: as printed, the
table's only non-QT comparator is a refinancing boom, and a reader has no turnover
reference at all.

---

## 4. The edit set — count-asserted old/new pairs

Conventions: `COUNT(old)` is the whole-file occurrence count of the anchor string **as of
`ed33a06`** and must be re-derived and re-asserted immediately before applying. The
manuscript is one paragraph per line; every "paragraph" below is a single unbroken line.

---

### E1 — float move for `tab:wal` (the float-move pair)

**E1a — DELETE at the old location** (online appendix, `sec:robustness-wal`).

- Block: the `table` environment whose caption line is
  `\caption{Approximate SOMA portfolio WAL by prepayment scenario (years).}`
  — `COUNT(caption line) = 1`.
- Bounds as of `ed33a06`: **L1290 `\begin{table}[H]` … L1314 `\end{table}`**, 25 lines,
  2803 bytes, `md5 = 9fd0992a211ac84a80f868284d6c8a63`.
  (Recompute the md5 before applying; it changes if E4 is applied first, and it changed
  once already during this drafting session.)
- Delete the 25 lines **and nothing else**. L1289 above it is blank and stays; L1315
  (`Read against the empirical column…`) follows immediately with no blank line and stays.
- The block moves **verbatim**, except for the single `\item` that E4 appends inside its
  `tablenotes` — apply E4 to the moved copy, not to the original, so the two edits do not
  race.

**E1b — INSERT at the new location**: as the first thing after the new subsection's ¶1
(E2b), separated by blank lines above and below. Keep `[H]`.

> **Float-placement flag.** The main text uses `[H]` for 37 floats and `[!t]` for 2
> (`tab:uncertainty`, `tab:estimators`, changed in `46b294c` precisely to close orphan-page
> gaps). A 25-line `[H]` table dropped into §VI will re-flow the main text's pagination and
> may re-open one of those gaps; the two-PDF split point recomputes as well. Rebuild and
> re-check page count at the end of the WP-E batch, not after this edit alone.

---

### E2 — promote the cap-design arithmetic to a named subsection

**E2a — DELETE the old cap paragraph.**

- `old` = the entire line beginning
  `A second lever, which I flag as speculative design space` — `COUNT = 1`
  (as of `ed33a06`: L454, 2330 bytes, `md5 = 06e5eedd588a…`), **together with the blank
  line immediately above it**.
- Nothing else on L450–L452 changes: the assumability paragraph and the
  `\subsection{Evaluating Alternative Securitization Policies}\label{sec:discussion-policy}`
  header both stay exactly as they are.

**E2b — INSERT the new subsection** immediately before
`\subsection{Evaluating Alternative Securitization Policies}\label{sec:discussion-policy}`
(`COUNT = 1`), separated by a blank line above and below. Full text, three lines
(header, ¶1, ¶2) plus the E1b float between ¶1 and ¶2:

```latex
\subsection{Redemption-Cap Design: The Ex-Ante Arithmetic}\label{sec:discussion-capdesign}

That the caps would sit above achievable runoff is not my observation: New York Fed staff projected \$20--\$30 billion in monthly principal payments in the month the \$35 billion ceiling took effect \citep{nyfed2022}. What this paper adds is the quantification and its ex-ante construction. The New York Fed's May 2022 baseline path supplies the test: it implied agency MBS runoff of \$740.6 billion over the window against the caps' \$1{,}417.5 billion, so the \$35 billion cap was set roughly 1.7 to 1.9 times as high as the Federal Reserve's own contemporaneous projection of achievable runoff, the multiple depending on the same disclosed intra-2022 allocation choice as the anticipated share (Section~\ref{sec:method-benchmark}). The decomposition measures the same distance from the other side: both components of the $\beta_1 = 0$ null (scheduled amortization from the book's coupon, age, and term composition, and baseline involuntary turnover at any assumed floor) recover 88.7\% of the realized shortfall at the in-sample calibration point and 85.7\% at the off-window floor, which is how far the fixed \$35 billion cap sat above the book's mechanical principal path. Table~\ref{tab:wal} prices that path in maturity units: under the empirical CPR the book's approximate weighted-average life is 9.4 years against 3.4 years at 2021 realized speeds, and the 3.4-year comparator is a refinancing-boom baseline rather than a turnover norm, so the speed that would have filled the cap is the one the window's rate configuration had already shut off.

[[ E1b: the tab:wal float environment, verbatim, goes here ]]

The design question that follows is speculative, and I flag it as design space rather than as a finding these estimates support. A cap indexed to the observable state of the outstanding stock (for example, to the share of the book sitting deeply below market coupon), or a standing policy of substituting Treasury runoff or outright MBS sales when passive runoff undershoots, would convert extension risk from a silent shortfall into an explicit, priced policy choice. What the decomposition supplies such a design is computable in advance of the cycle, but as a band rather than as a point: scheduled amortization is fixed by the book's composition, while the turnover floor is measured, and its defensible out-of-window reads run from 4.70\% to 5.33\% depending on the depth at which out-of-the-moneyness is cut, carrying the central-elasticity marginal from $+6.8$ points at the deepest cut to $+4.3$ at the shallowest (Table~\ref{tab:oosfloor}); the floor read's own sampling error widens the identified margin further (Section~\ref{sec:robustness-floor}). A cap intended to bind would therefore be set at or below the lower edge of the book's projected scheduled-plus-turnover principal path, with the identified elasticity margin ($+2.1$ to $+13.2$ points of the shortfall across the calibration box) as the behavioral band around it --- which is the form the Federal Reserve's own contemporaneous projection took, a range rather than a point. Nothing in my estimates identifies the welfare or market effects of such designs; active sales in particular would realize the mark-to-market losses that passive runoff defers. I record the option to mark where the design space lies, not to recommend a point in it.
```

**What E2 does and does not change.**

- **Preserved verbatim from the old paragraph:** `\$20--\$30 billion`, `\$35 billion`
  (×3 in the new text), `\$740.6 billion`, `\$1{,}417.5 billion`, `1.7 to 1.9 times`,
  `88.7\%` / `85.7\%`, `$+2.1$ to $+13.2$ points`, `computable in advance of the cycle`,
  the state-contingent-cap sentence, the active-sales caveat, and the closing
  "I record the option…" sentence. **No committed value changes.**
- **Restated (this is the R3-W5 repair):** `are computable in advance of the cycle` →
  `is computable in advance of the cycle, but as a band rather than as a point`, with the
  band exhibited from committed reads (4.70–5.33%, marginals +6.8 → +4.3, all already
  printed in `tab:oosfloor`) and the NY Fed's own $20–$30bn projection named as the
  precedent for a range.
- **Re-ordered (this is the arbitration):** the *anticipation* is credited to
  `nyfed2022` in the subsection's first clause; the *quantification* is claimed in the
  second. The arbitration was already landed in the Introduction at `ff80ed7`; this
  reproduces its logic at the body site rather than re-litigating it.
- **Split along the seam the arbitration implies:** ¶1 is the claimed arithmetic
  (a finding), ¶2 is the design space (explicitly speculative). The old paragraph blurred
  the two, which is why the contributions list can claim a result the body labels
  "speculative design space".
- **Dropped:** the opener's `A second lever` framing (the paragraph is no longer second).
  If Option P-B (placement after the assumability paragraph) is taken instead, restore
  `A second lever, which I flag as speculative design space rather than a finding this
  paper's estimates support, operates on the policy instrument rather than the mortgage
  contract: the redemption cap itself.` as ¶2's opening and delete ¶2's first sentence.

---

### E3 — companion pair, Introduction (required, not optional)

Without this, the paper says "computable in advance of the cycle" flatly in the
contributions list and "only as a band" in the body, and the contributions list points at
the subsection the cap material just left.

- `old` (`COUNT = 1`):
  `are computable in advance of the cycle (Sections~\ref{sec:identification} and~\ref{sec:discussion-policy})`
- `new`:
  `are computable in advance of the cycle, as a band rather than as a point (Sections~\ref{sec:identification} and~\ref{sec:discussion-capdesign})`

Line 59 carries no gate span (AST scan: only the generic substring `decomposition`, which
is a gate dict key, not a tex pin) and no test literal. It **is** the round-28 arbitration
sentence, so the edit is deliberately minimal: eight words and one label.

---

### E4 — the normal-turnover benchmark, as a tablenote (the run-free R3-W3 landing)

Append one `\item` to `tab:wal`'s `tablenotes`, in the **moved** copy of the float.

- `anchor` (`COUNT = 1`): `their components round independently.` — the last four words of
  the existing note item. Insert the new `\item` on the line **after** the line that ends
  with it, i.e. immediately before `\end{tablenotes}`.
- `new` (one line):

```latex
\item Turnover benchmark: the final row is a refinancing-boom baseline rather than a normal-turnover one --- 22.81\% is the 2021 realized speed, most of which is refinancing, and refinancing is what the QT window's rate configuration shut off. No row is printed at a normal-turnover speed. The paper's own out-of-window turnover measurement is the floor read (Table~\ref{tab:oosfloor}): defensible 2018 reads of 4.70\%, 4.99\% and 5.33\% by depth of out-of-the-moneyness, against refi-contaminated pooled 2017--2019 and 2019 anchors at 6.07\% and 6.91\%. The printed rows nearest that band are Path B's 4.76\% and the empirical 5.14\%, and this calculator is monotone in CPR, so a row anchored at the band's mid read would fall between their 9.7 and 9.4 years.
```

- **Numeric literals introduced: none that are new to the manuscript.** 4.70/4.99/5.33/
  6.07/6.91% and 4.76/5.14/9.7/9.4/22.81 are all already printed (`tab:oosfloor`,
  `tab:wal`). Counts move up by one each; every count gate in the suite is `>=`, and none
  of these strings appears in `ZERO_COUNT`, `EXACTLY_ONE` or `SUPERSEDED_CONTEXTUAL`.
- **The one inferential clause** is the last one ("monotone in CPR … would fall between
  their 9.7 and 9.4 years"). The premise is true both analytically (higher constant CPR
  returns principal earlier at every $t$) and observably (all nine committed rows are
  monotone), and the clause prints no number that is not already in the table. **If you
  want zero inference, delete from `and this calculator is monotone in CPR` to the end and
  close the sentence after `the empirical 5.14\%.`** Both variants are honest; the short
  one is more conservative, the long one is more useful to a practitioner.
- `\texttt{out\_of\_window\_floor}` is deliberately **not** cited here (the run tags live
  in `tab:runindex` under the round-19 convention, and `tab:oosfloor` already carries the
  `\texttt{oos\_identification}` citation in its caption). Do not add a run tag inline.

---

### E5 — appendix lead-in, so the moved table is not orphaned (recommended)

- `old` (`COUNT = 1`): `The mechanism the paper quantifies is duration extension, so I express it in maturity units. Table~\ref{tab:wal} reports the SOMA book's approximate weighted-average life (WAL) under scheduled amortization only, under the empirical CPR path, and under each estimator's implied path, at the QT window's start and end.`
- `new`: `The mechanism the paper quantifies is duration extension, so I express it in maturity units. Table~\ref{tab:wal}, printed with the cap-design arithmetic in Section~\ref{sec:discussion-capdesign}, reports the SOMA book's approximate weighted-average life (WAL) under scheduled amortization only, under the empirical CPR path, and under each estimator's implied path, at the QT window's start and end; this appendix documents its construction and reads it against each estimator.`

The closing WAL prose (`Read against the empirical column…`, which carries gate #44's
`0.6-year rule-only shortening` pin) **stays in the appendix, untouched**. That is the
conservative split: the exhibit is promoted, its derivation and its estimator-error
reading stay offstage, and no gate #44 literal moves.

---

### E6 — optional micro-pair: relabel the no-shock row

Cheapest possible fix to the same complaint, applicable with or without E4.

- `old` (`COUNT = 1`): `No-shock counterfactual, 2021 realized speeds (22.81\%) & 3.4 & 3.3 \\`
- `new`: `No-shock counterfactual, 2021 realized (refinancing-boom) speeds (22.81\%) & 3.4 & 3.3 \\`

Not gate-pinned (#44 pins only the two Danish rows). Value unchanged. Take it only if E4's
long variant is *not* taken, otherwise the note says it twice.

---

### E7 — ⚖ OPTIONAL, needs Eugene: state the band in floor units from the floor's own bootstrap

R3-W5's literal ask is "a band derived from the floor's own bootstrap". E2's band is
derived from the floor's **depth grid** (`tab:oosfloor`), which is committed and already
printed. The bootstrap band exists too, but **only in the artifact**:
`floor_inference_correction_v2_results.json → reads.R2_2018_gap<=-0.0025_age>=12.wild_t_webb`
gives `upper_pp_edge.floor_pct = 4.176744…` and `lower_pp_edge.floor_pct = 5.800285…` —
i.e. the Webb wild-cluster interval that produces the printed `$+2.9$ to $+8.7$` margin is,
**in floor units, 4.177% to 5.800%**, with the headline 4.991% read inside it.

If taken, append to E2b ¶2 after "(Table~\ref{tab:oosfloor})":
`; the same floor read's wild-cluster interval, expressed in the units a cap designer would have to plug in, runs from 4.177\% to 5.800\%`

**Why this is ⚖ and not applied by default:** it prints **two numeric literals the
manuscript has never printed**. Under the repo's own discipline that needs (i) a gate that
re-derives both from the artifact (the natural home is the C1/#105 battery, which already
reads this file), (ii) a test, and (iii) a decision that the floor-scale rendering of the
binding interval is a thing the paper wants to print at all — it makes the interval's
inverse mapping visible (a *higher* floor gives a *smaller* marginal), which is honest but
is a presentation call. Rounding convention if taken: 3 dp, matching the manuscript's floor
convention (`4.991\%`, `4.695\%`, `5.334\%`, `3.972\%`, `6.910\%`).

---

## 5. Literal census (assert before and after)

| Literal | Before (`ed33a06`) | After E1–E5 | Note |
|---|---|---|---|
| `\$20--\$30` | 1 | 1 | moved, not duplicated (¶2 refers to it as "a range rather than a point") |
| `1.7 to 1.9` | 2 | 2 | L59 + new ¶1 |
| `\$740.6` | 3 | 3 | |
| `1{,}417.5` | 2 | 2 | |
| `computable in advance` | 2 | 2 | both now band-qualified (E2b ¶2, E3) |
| `$+2.1$ to $+13.2$` | 6 | 6 | |
| `88.7\%` / `85.7\%` | 20 / 21 | 20 / 21 | |
| `\ref{sec:discussion-policy}` | 2 | 1 + label | E3 re-points the Introduction |
| `capdesign` | 0 | 3 | label + 2 refs (E3, E5) |
| `4.70\%` | 1 | 3 | +E2b ¶2, +E4 |
| `5.33\%` | 5 | 7 | +E2b ¶2, +E4 |
| `4.99\%` | 2 | 3 | +E4 |
| `6.07\%` / `6.91\%` | in `tab:oosfloor` | +1 each | E4 |
| `$+6.8$` / `$+4.3$` | 9 / 16 | +1 each | E2b ¶2 |
| `refinancing-boom` | 1 | 3 | E2b ¶1, E4 (4 if E6 is taken — then drop E4's long variant) |
| `22.81\%` | 2 | 3 | E4 |
| `(5.61\%) & 9.1 & 8.2` | 1 | 1 | **gate #44 — must not change** |
| `(3.39\%) & 10.8 & 9.6` | 1 | 1 | **gate #44 — must not change** |
| `0.6-year rule-only shortening` | 1 | 1 | **gate #44 — stays in the appendix** |
| binding-interval family (`$+2.9$ to $+8.7$` ×8, and-form ×2, bracket ×3) | — | unchanged | this edit adds and removes none |

**Zero-slack rule reminder:** re-derive the binding-interval census (including and-forms)
before the commit even though this edit does not touch it — the round-26 defect survived
exactly because an and-form was not counted.

---

## 6. Ambiguities and the choices made

- **A1 — "§VII (policy)" does not exist.** Resolved to §VI.B `sec:discussion-policy`
  (§1). If Eugene meant a *renumbering* (policy promoted to its own top-level section),
  say so: that is a different, larger edit and it collides with `HARDCODED_XREF` nothing
  but does move every subsequent section number in the letter's prose.
- **A2 — "directly after the benchmark complement".** The complement is §III.B; a policy
  subsection cannot sit after it. Read as "directly after §VI.A's benchmark/duration
  paragraphs", which is also where the WAL citations are. Fallback Option P-B given.
- **A3 — the arbitration is already partly landed.** L59 (round 28 `ff80ed7`) already
  credits `nyfed2022` and claims only the arithmetic. This draft **builds on it**: the
  body site now mirrors the same split, and E3 is the only change to L59 (band + label).
  No re-litigation of the contributions list.
- **A4 — "speculative" vs "contribution".** The old paragraph opened by calling the whole
  cap discussion "speculative design space rather than a finding this paper's estimates
  support" while the Introduction lists the cap-design arithmetic as affirmative
  contribution #3. E2 resolves this by splitting: the arithmetic is a finding (¶1), the
  *design* is speculative (¶2, wording preserved). If Eugene disagrees, the alternative is
  to soften contribution #3 instead — but that is posture and belongs to him.
- **A5 — the moved table leaves its section behind.** After E1, `sec:robustness-wal` is a
  construction-and-reading appendix whose exhibit is in the main text. E5 says so in one
  clause. Two callers cite *tablenote facts* through the section ref rather than the table
  (L263's "pre-2017 vintages another 10.6\%; Appendix~\ref{sec:robustness-wal}"; L1320's
  "Table~\ref{tab:wal}'s note reconciles…"). Both still resolve; L263 would read better as
  `Table~\ref{tab:wal}`, but it sits inside the paragraph S8 has just rewritten
  (`9deda21`) and I am not proposing to re-open it in this batch.
- **A6 — how much of the WAL material moves.** Choice: **float only**. Moving the
  closing prose too would carry gate #44's `0.6-year rule-only shortening` pin into the
  main text and would drag the estimator-error reading (an §V-flavoured discussion) into
  the policy section. If Eugene wants the whole subsection promoted, that is a different
  pair set and gate #44's prose literal must be re-anchored in the same commit.
- **A7 — R3-W3's provenance.** The label `R3-W3` appears **only in the plan**, not in
  `REVIEW2_v18_panel_2026-07-28.md` (R3's numbered findings there are W1, W2, W4, W5). The
  substance is nonetheless real and verifiable from the tex: the table's only non-QT
  comparator is a refi boom. Flagged so the response letter does not cite a finding number
  the referee never wrote.

---

## 7. What the applying session must do (checklist)

1. `git pull`/re-read the tex — it moved three times during this drafting session; re-derive
   every `COUNT` and the E1a md5.
2. Apply E1a → E2a → E2b → E1b (into E2b) → E4 (into the moved float) → E3 → E5.
3. Re-assert the §5 census, including the binding-interval and-forms.
4. Run the gate suite. **Expected: all pass, no gate edit required** — this edit changes
   no gate-pinned span (§2.1 pins are preserved byte-for-byte; §2.2 pins are `>=` or
   presence-only). If anything fails, stop: it means a pin was mis-inventoried here.
5. Run the test suite (451 tests as of `9be0c34`). No test fixture should need changing.
6. **Letter:** §7 of `response_to_referees_round22.tex` gains one sentence naming the
   structural move and the band restatement. No literal in `LETTER_CURRENT_LITERALS` is
   removed by this edit and the abstract is untouched, so **no recount is required** —
   but re-run gate #101 to confirm rather than asserting it.
7. Rebuild (tectonic) and re-check pagination and the two-PDF split point after the whole
   WP-E batch, not after this edit alone.

## 8. If Eugene wants the printed normal-turnover row after all

Spec-before-run, per the standing protocol. Minimum contents: chosen anchor (recommended:
the defensible 2018 band's mid read, labelled as what it is — an *out-of-window turnover
floor*, not a "normal turnover" speed) with the reason the label matters; the
`wal_table.py` `SCENARIOS` patch committed **before** the run; an output guard so
`wal_table_results.json` cannot be clobbered without the nine committed rows returning
bit-identical (gate #44 reconstructs two of its three pins from that file); a
pre-committed landing rule for the row's label and for the prose sentence at
`Read against the empirical column…`; and a pre-committed statement of what the row is
allowed to be used for (a maturity-unit rendering of the floor, not a new estimate).
