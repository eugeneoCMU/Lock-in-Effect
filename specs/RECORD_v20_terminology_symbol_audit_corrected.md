# Terminology and symbol audit — CORRECTED

Supersedes the text-dump audit of the same name. That audit was produced from
`final_paper.pdf`, not from source; every claim below has been re-checked against
`paper/v18/revised_paper_v18.tex` at b081a1b and against the run code and committed
artifacts. Verification: 48 agents, 40 claims, each read once and adversarially
re-checked once, disagreements adjudicated against source; the high-severity items
were then re-verified by hand.

Line numbers are `revised_paper_v18.tex`. Every cited line is **identical** in
`revised_paper_v18_long_abstract.tex`, so every edit below is applied twice.

---

## 0. What changed from the original audit

| Original claim | Verdict | Correction |
|---|---|---|
| Object 3 (floor-read clusters) is undefined; this BLOCKS everything | **REFUTED** | Its unit is the four-way stratum, recorded in code and in two artifacts. Nothing is blocked. |
| Five stratum-family objects | **REFUTED** | Two partitions. Objects 1 and 3 are the same one. Objects 4 and 5 are not stratum-family. |
| Rename object 3 to "[unit] cluster" | **REJECT** | It would break a true identity and four gate literals. |
| Rename object 2 to "draw cell" | **ACCEPT, for a different reason** | Not because 130 ≠ 296, but because its key is three-way. |
| `s` is overloaded three ways | **CONFIRMED**, damage understated | Also collides inside Table 1 and inside §V.E. |
| Rename bootstrap replicates to `R` | **BLOCKED** | `R` is recovered trapped liquidity, eq. (4). |
| §VIII.A gate item (ii) machine-checks equations and table notes | **REFUTED** | It checks five cross-reference regexes. No gate covers any equation body. |
| `floor_form_calibration_parity` spec addresses the fork | **REFUTED** | No such spec. The substance is real and is ledger item C-22. |
| 530 em-dashes against zero in v16.tex | **PARTLY** | 530 vs **14**. Both files have 0 literal U+2014. |
| Abstract 252 words, two over | **PARTLY** | 244 by the paper's own gate. No 250 ceiling is in force. |

---

## 1. The stratum family — two partitions, not five

The constructor tells the whole story:

```
hazard/stratum.py:6-14        f"{vintage}_{coupon_bps}_{fico_bucket}_{ltv_bucket}"   ← FOUR-way
hazard/loan_sample.py:39-46   vintage + "_" + coupon_bps + "_" + fico_bucket          ← THREE-way
```

Both write a column named `stratum_id`.

| # | Object | Partition | Count | Disposition |
|---|---|---|---|---|
| 1 | Path A estimation cells | four-way | 296 cells, 295 FE | keep "stratum" |
| 2 | Path B 75,000-loan draw + its cluster bootstrap | **three-way** | 130, 25.8 effective | **disclose the key**; may be called "draw stratum (three-way)" |
| 3 | Floor-read bootstrap clusters | four-way — *same as object 1* | 31 / 226 / 25 | keep "stratum cluster"; reconcile the count |
| 4 | SOMA raking margins | not a partition | 2 margins | unchanged |
| 5 | §V.D standardization cells | own axis | not stated | print the counts |

**Why the counts differ.** 296, 31, 226 and 25 are occupancy counts of *one* four-way
partition on one panel under different row selections — window, gap depth, age cut.
They reconcile exactly. 130 belongs to the second, three-way partition. The audit read
the count spread as evidence of distinct objects; it is evidence of one partition
observed on different subsamples plus one genuinely different key.

**Object 3 is not undefined.** `floor_uncertainty.py:204-206` hard-codes
`groupby("stratum")`; `floor_uncertainty_results.json` records
`cluster_unit = "4-way stratum (vintage x coupon-bps x fico_bucket x ltv_bucket;
stratum.build_stratum_id)"`; `floor_inference_correction_v2_results.json` enumerates
all 31 labels. The manuscript already calls them "the 31 strata" and
"the stratum-clustered one" in the Table 23 notes. What is missing is one clause
reconciling 31 to 296 — a clarity fix, not a blocker.

**The real defect is in object 2, and it is an error of fact.** :211 reads

> "…and a stratum identifier matching the Path A specification"

It does not match: three fields against four. Under the paper's own global definition
at :999 ("strata *s* are the 296 observed four-way cells of vintage × coupon × FICO
bucket × LTV bucket"), the "130 strata" of :411 and :991 and the "within stratum" of
:939 all assert something false about the draw. The divergence is disclosed nowhere in
the manuscript or in TECHNICAL.md.

---

## 2. Symbol collisions

### 2.1 `s` — three meanings, two contradictory production values — CONFIRMED

| Use | Sites | Production |
|---|---|---|
| Path A stratum index | :878, :999, :1003 | index (the only use with a notation-table entry) |
| Moving-share bracket | :80, :229, :316, :333, :551 | s = 1 |
| Floor-form mixture share | :87, :296, :682, :684 | s = 0 |

Damage is worse than the original audit found. It named Table 1 notes against Table 4.
The collision also fires **inside a single exhibit** — Table 1's body row at :80
(moving-share, production s = 1) against Table 1's own notes at :87 (floor mixture,
production s = 0), seven source lines apart — and **inside a single subsection**, §V.E
:296 (+9.7 at s = 0.25) against :316 (+1.82 at s = 0.25), same units, same floor,
values 5.3× apart.

The verbal tags do not disambiguate. :88 splits floor turnover into discretionary moves
and strictly involuntary events, so "strictly-involuntary share" and "moving-share"
read as complements of one decomposition when they are unrelated legs of the model.

**Rename the floor-mixture `s` → `\omega`.** It is the cheap side: 15 tokens on four
lines, no gate pins any of them. The moving-share `s` is pinned by gate #102
(`liveness_gates.py:704-706`) and cross-referenced in
`tests/test_danish_interest_only_share_gate.py:264`, so moving *that* one requires a
coordinated gate edit — a separate decision, not a mechanical edit.

`\psi` is **rejected**: PSI is a live, gate-pinned acronym at :1175/:1181/:1192-1195.
`\omega` is free (0 occurrences anywhere under `paper/`).

### 2.2 `a`, `\theta`, `S` — the attenuation identity `a = S^\theta` collides on all three

- `a` — loan age in the seasoning spline (eq. 1, Table 14) **and** the attenuation
  factor, 12 lines apart in the same subsection. Table 14 defines only the age sense,
  and its note at :906 ("no coefficient symbol is reused across them") reads as a
  global guarantee it does not make.
- `\theta` — ABM mobility-desire scale **and** the gamma-frailty parameter.
- `S` — expected-stay horizon (`:839`, 60 months) **and** a dimensionless survival
  share (`:1222`, 40,234/75,000).

Rename the **frailty/attenuation** side at :225, :316, :333, :1222 and
`replication_appendices.tex:200`, not the ABM scale. Gate-safe: no gate pins
`S^{\theta}`.

Replacement symbols — collision-checked:

| Candidate | Status |
|---|---|
| `\omega`, `\vartheta`, `\xi`, `\varsigma` | free (0 occurrences) |
| `\nu` | free but sits beside `$v_t$` at the same visual weight — avoid |
| `R` | **blocked** — recovered trapped liquidity, :290 and eq. (4) :292; also `R²` in 7 places |
| `A`, `\alpha_S` | **blocked** — `A(P,r,n)` at :792; `\alpha_s` is the Path A stratum FE at :886 |
| `\psi` | **blocked** — PSI acronym, gate-pinned |
| `\theta`, `\phi` | live |

### 2.3 `B` — CONFIRMED

Cohort burnout state `B_{s(i),t}` (eq. 1) against the replicate count. The same
quantity is also typeset two ways: roman "(B $= 9{,}999$)" at :430, math
"$B = 9{,}999$" at :1240-41, in a paper where math-italic `B` is the burnout state.

### 2.4 What the original audit missed

- **`\sigma` is triple-overloaded across the paper's own two symbol tables**: rate
  stress `$\sigma_{i,t}$` at :898 (tab:hazard-notation), log-normal dispersions
  `$\sigma = 0.45$` / `$0.35$` at :832-833 (tab:abmparams), and a share `$\sigma$` of
  the Danish leg at :563. Two of the three senses are formally tabled, one table apart.
- **`\lambda` carries three objects**: loss aversion (:840), cause intensities
  `$\lambda_p$`/`$\lambda_d$` (:946), ridge penalty (:1005, :1074, :1123).
- `\kappa` — confirmed single-use, no conflict.
- The floor identity at :682 is well-formed in source (`\underline{h}` survives; the
  dump flattened it), but its gloss says "hazards add", which is wrong for the
  survival-scale composition it writes.

---

## 3. Non-terminology defects found during verification

1. **:211 is factually false** (§1 above). Highest priority in this document.
2. **Table 23's caption contradicts its own note and body.** The caption still calls
   the Webb wild-*t* "the primary construction and the interval this paper quotes";
   the note and the status column say Webb falls below the pre-committed bar and the
   restricted inversion is what the paper quotes. The N1 re-landing moved the binding
   interval to [+2.3, +9.1] and the caption did not follow.
3. **`replication_appendices.tex` ships a retired interval** labelled "Binding layer" —
   Webb's [+2.9, +8.7], which the manuscript says is no longer binding.
4. **:492 dangles.** "the trade-off named in this paper's title" against a title that
   names no trade-off — collateral from the 2026-08-05 title revert. This is also the
   answer to the original audit's open "Securitization Trade-Off framing is absent"
   item: the framing left with the old title, and this clause is what it left behind.
5. **:721 quotes the Ginnie overlay at +7.3 unlabelled.** That is the in-sample value
   (9.20 × 0.797); the off-window counterpart is +4.4. The original audit justified
   this as covered by an "unlabelled reads as in-sample" convention — no such
   convention exists, and :294 makes the off-window floor the headline, so the
   unlabelled figure defaults the wrong way in the paper's conclusion.
6. **Two incompatible trios in one sentence at :496** — the lead-in names servicer
   behaviour, updated-equity dynamics and equity extraction; the enumeration that
   follows gives loan-level heterogeneity, servicer behaviour and burnout.

---

## 4. Editing mechanics — corrected

**Do not** bare find-and-replace on `stratum` or on `s`. For `stratum` the hazard is
four gate literals at `liveness_gates.py:845, :1567, :1569, :1592` (plus :1549), and
the capitalised `Stratum` (4 hits, including the §V.D subsection title at :283). For
`s`, gate #102 carries three `$s$`-bearing pins. `31 clusters` is pinned by 3 gates and
2 tests — preserve that literal verbatim when adding the reconciliation clause.

**Verification is `tools/liveness_gates.py` (128 gates) and pytest (~1,110 collected
from 616 functions across 46 files).** A symbol rename trips gates #102, #109, #94 and,
for `stratum`, #107 and #115.

**The gate gap that matters:** equation bodies (`eq:pathB` :212, `eq:pathA` :1000) and
`tab:hazard-notation` are pinned by **no gate**, so an equation-only rename passes
green. Check those by eye or add a gate. The original audit's claim that §VIII.A item
(ii) machine-checks equations and table notes is wrong in both directions — item (ii)
is five zero-count regexes for hardcoded cross-references
(`liveness_gates.py:266-273`).

**Every `.tex` edit is applied twice**, to `revised_paper_v18.tex` and
`revised_paper_v18_long_abstract.tex`, which the gates glob via `TEX_VARIANTS`
(`liveness_gates.py:42`).

---

## 5. Disposition

### Executable with no run and no gate edit

| # | Item | Sites |
|---|---|---|
| 1 | Correct the false stratum-key claim | :211 |
| 2 | Disclose the three-way draw key | :939, echoes :411, :991 |
| 3 | Reconcile 31 to 296 | :688 |
| 4 | Rename floor-mixture `s` → `\omega` | :87, :296, :682, :684 |
| 5 | Name the top-leverage cluster | :1253 |
| 6 | Label the Ginnie +7.3 as in-sample | :721 |
| 7 | Fix the dangling title clause | :492 |
| 8 | Fix the "hazards add" gloss | :682 |
| 9 | Fix Table 23's stale caption | :1228 |
| 10 | Fix the shipped binding-layer row | `replication_appendices.tex` |
| 11 | Reconcile the two trios | :496 |

The top-leverage cluster is recoverable and needs no run: from
`floor_inference_correction_v2_results.json`, `cluster_strata[argmax(leverages_h)]` on
the binding read is **`2017_400_740+_≤80`** — 2017 vintage, 4.00% coupon, FICO 740+,
LTV ≤ 80 — at leverage 0.3323, **33.2%** of total and **1.94×** the next largest
(the same cohort at LTV > 80, 0.1717). Tie any gate to the argmax, not to a literal.

### Lockstep only (gate literals must move in the same commit)

- Renaming the moving-share `s` — gate #102, three pins.
- Renaming `stratum` at :1247/:1253 — gates #107/#115, four literals.

### Not to be done

- Cutting the abstract hull clause — gate #99 fails outright, and it deletes a
  deliberate form-conditionality hedge. No 250-word ceiling is in force.
- Amending `TECHNICAL.md:1805`. It is a correct, dated record of v16 *as assembled on
  2026-07-13*; the 14 prose em-dashes re-entered in rounds 18b/19. Amending it would
  replace a true record with a false one. Add a dated pointer if anything.
- Creating a spec named `floor_form_calibration_parity`.

### ROUND 2 — LANDED as 28d65c4 (symbol collisions)

The `a = S^{\theta}` attenuation identity collided on **all three** of its
symbols, so renaming it fixed three collisions in one edit on four lines:

```
a = S^\theta   ->   \eta = S_{\mathrm{pre}}^{\xi}      :225, :316, :333, :1222
                                                        + replication_appendices.tex:200
```

The **frailty** side was renamed, not the ABM side: `\theta` owns 11 sites
including a four-row `tab:abmparams` block and the binary-search range, against
the frailty's four lines. `S_{\mathrm{pre}}` leaves the ABM's bare `S = 60`
untouched. Every target string was verified pinned by **zero** gates and zero
tests before editing.

`\sigma`: the sharp collision was bare-vs-bare — :219 (rate stress magnitude)
against :563 (Danish share). Renamed the Danish share to `\chi`; rate stress
keeps `\sigma` as the senior tabled use, and the log-normal `\sigma = 0.45/0.35`
of `tab:abmparams` is contextually bound and untouched. This one **was** pinned:
lockstep edit to `liveness_gates.py:2606` and
`tests/test_danish_interest_only_share_gate.py:69`, one literal each, same commit.

`\lambda`: **REFUTED, no edit.** Bare `\lambda` is exclusively loss aversion; the
other two senses are always subscripted (`\lambda_p`/`\lambda_d`,
`\lambda_{\mathrm{ridge}}`). Subscripts disambiguate — editing would have been churn.

Post-edit separation verified identical in both variants: `\theta` 11 (ABM only),
`\sigma` 7 (rate stress + log-normal only), `\xi` 14 / `\eta` 5 (frailty only),
`\chi` 2, residual `a = S^` zero. PDF glyph counts match source exactly.

### ROUND 3 — LANDED as 1fb1350 (last collision closed) + the §V.D counts

**Moving-share `s` → `\mu`.** After the mixture rename to `\omega`, two senses of
bare `$s$` remained: the Path A stratum index and the moving-share bracket. Renamed
the bracket, keeping `$s$` for the stratum — the senior use and the only one with a
notation-table entry. 24 tokens across exactly five lines (:80 ×3, :229 ×14, :316 ×4,
:333 ×2, :551 ×1), applied line-scoped with per-line expected counts asserted so the
four stratum-sense tokens at :682/:878/:999/:1003 could not be caught by accident.
Lockstep, same commit: gate #102's three literals at `liveness_gates.py:704-706`,
after verifying no test hardcodes them.

**Result: exactly four standalone math `$s$` tokens remain, all the stratum index.**
The symbol is single-valued.

**`tab:hazard-notation`** gained a fourth block, *Convention and transport
parameters*: `\mu`, `\omega`, the cyclical floor variant
`\underline{h}_t = 4\%(1+\kappa z_t)`, `\eta = S_{\mathrm{pre}}^{\xi}`,
`S_{\mathrm{pre}}`, `\xi`. The table defined none of them before. Its note claimed
"no coefficient symbol is reused across them" — true, but scoped to coefficients
while reading as a global guarantee; it now says so.

**§V.D standardization-cell counts landed, verified against artifacts** (they were
held back in round 1 as unverified): `episode_confrontation_within_results.json`
gives axis `vintage|fico_bucket|ltv_bucket`, `n_cells = 22`, `n_common_cells = 18`;
`episode_gradient_age_bands_results.json` gives `n_cells = 29` on the age-augmented
axis with the same 18 in common. Both now printed at :287.

**Gate-design note.** The gate covering that passage builds its literals with
f-strings (`liveness_gates.py:1773-1774`), so an AST string-literal scan does not
see them. Both survived because the insertions fell outside the pinned spans — but
that was checked by reading the gate, not by the scan. This is the repo's known
blind-spot class and it is still live.

**Symbol state after three rounds:** `s` = stratum index only; `\theta` = ABM
mobility scale only; `\sigma` = rate stress + log-normal dispersion only; `\mu`,
`\omega`, `\eta`, `\xi`, `S_{\mathrm{pre}}`, `\chi` each single-valued; `\lambda`
untouched and correct. **No live symbol overload remains.**

**Not done, and off the list:** the `stratum` rename at :1247/:1253. It was the
original audit's proposal and this record refutes it — objects 1 and 3 are the same
partition, so "stratum cluster" is the right name.

### ROUND 4 — CLOSEOUT, landed as 46e80e9 and f546c76

Ten further edits, all verified against the current file (line numbers from the
earlier rounds had already drifted — the six notation rows moved :1240 to :1248).

- Replicate counts no longer print a bare italic `B`, which is the burnout state
  `B_{s(i),t}` in eq. (1): roman at :430 and math-italic in two ladder rows, all
  now "9{,}999 replications". The genuinely different 999 at :316 was already a word.
- `h^{\mathrm{vol}}` occurred exactly once in the manuscript, inside the identity
  at :682, defined nowhere. Now a notation row, with `h^{\mathrm{prep}}_{i,t}` and
  `h^{\mathrm{def}}_{i,t}` beside it — the table had defined the *derived* hazard
  while omitting both *primary* displayed ones.
- The identity's left-hand side was a bare `$h$` bound to nothing — the only
  standalone math `h` in the file. Now `h^{\mathrm{prep}}`, which is house style
  and matches what `literature_hazard.py:113-115` assigns.
- `\phi^{*}` at :316: **not the arithmetic slip it was reported as.** The artifact
  gives 0.75390625 at the 4.991% floor and 0.75625 at 4.0%; every printed numeral
  rounds correctly. The defect was scope — an unqualified "the root" carried across
  two anchors — fixed by naming the floor. Adding the second root was **rejected**:
  :316 already prints 0.756 four sentences later for the *additive* root, and
  `tests/test_scaled_null_additive_gate.py:427-433` exists to forbid restating that
  pair as holding at both anchors.
- "band" carried the floor axis and the elasticity axis in one phrase at :690 and
  :219; "stratum-cluster" read as the three-way draw stratum at :920 and :287.
  Both disambiguated.

### The terminology table — LANDED (Eugene's go, round 5)

`tab:terminology` is in, as a `longtable` in the house idiom, placed beside
`tab:hazard-notation`. Nine rows, ordered by damage with **stratum first** — it is
the overload that produced an actual false statement in the manuscript (:211).
Cost: 141→143pp canonical, 142→144pp variant.

All four blockers below were resolved before landing, and two of the corrections
were themselves corrected on verification:

- The **anchor** gloss now reads "the middle of the three depth cuts fixed before
  the reads" — verified: `floor_uncertainty_results.json` carries exactly three
  2018 reads (gap ≤ +0.0000 / −0.0025 / −0.0050) and the mid-grid anchor is R2.
- The **cell** row splits the two grids, both verified by direct count: the
  **21-cell** calibration box (`tab:floorband`, seven floors × three elasticities)
  and the **27-cell** off-window floor × elasticity-band grid (`oos_identification`,
  nine floors × three bands).
- **DROPPED as unverifiable:** the proposed "10,176 training cells / 423 in 20
  zero-event strata / unbalanced against 296 × 36 = 10,656". None of those numbers
  occurs anywhere in the manuscript and I could not source them from an artifact.
  The row says "a stratum-month observation" without a count.
- `tools/editions/tex2md.py` `WANT["tables"]` 24 → 25, same commit. The converter
  re-run confirms it counts 25.

**One thing the suite caught that no reader did:** the drafted tablenote reused the
phrase "their 137 intersection cells", which
`tests/test_month_twoway_clusters_gate.py:97` asserts occurs exactly **once** — it
is the single-site anchor of a mutation battery. Duplicating it broke the test.
Fixed by rewording the note ("the 137 cells where those two intersect"), not by
touching the test. The full suite is the only thing that would have caught this;
no pin grep would have, because the assertion is about *uniqueness*, not presence.

### The terminology table — original blocker list (all now resolved)

The word census is sound: *cell*, *band*, *anchor*, *basis*, *stratum*, *floor*,
*form*, *draw* and *null* are each genuinely overloaded, and the manuscript has no
glossary today. But the drafted table must **not** be pasted as written. Four
blockers, all verified:

1. The *anchor* row must read "the middle of the three depth cuts fixed before the
   reads" — the drafted gloss was wrong.
2. The *cell* row conflates two grids: the 21-cell calibration box (`tab:floorband`)
   and the 27-cell off-window floor × band grid (`oos_identification`). It must also
   note the panel is unbalanced — 10,176 stratum-months against 296 × 36 = 10,656.
3. Adding a table requires bumping `tools/editions/tex2md.py:38` `'tables': 24` → 25
   **in the same commit**, or the editions converter's hard self-check fails.
4. At ~63 lines it should probably be a `longtable`, as `tab:uncertainty` is, and
   needs a build to confirm it does not overflow its float.

It is a content deliverable that changes what the paper claims about its own
vocabulary, so it is Eugene's call, not a mechanical landing.

### Author-only

The floor-form posture call — headline at the `s = 0` endpoint versus promoting the
form-robust band. Disclosed at :296 and :682 and in the abstract; ledger item C-22,
whose only unresolved limb is this choice. No run is warranted:
`floor_form_mixture_results.json` and `floor_form_offwindow_results.json` already
measure the curve and both endpoints.
