# RECORD R30 — Ginnie x vintage composed overlay: NOT_FEASIBLE (estimand), no run, no manuscript edit

**Verdict: NOT_FEASIBLE.** Not because the run cannot be executed — it can — but because the cell it would report has no observable content. The composed number is predictable from committed shares to within ~0.002pp, and the one quantity that would distinguish it from that arithmetic (the intersection's own prepayment speed) does not exist in any source on disk or in any published series I can locate.

**Recommendation to the coordinator: land this record only. No run. No manuscript edit.** Rationale in section 6.

Verified against worktree `.claude/worktrees/agency-mbs-runoff-qt-424945`, manuscript `paper/v18/revised_paper_v18.tex` (1,437 lines), 2026-07-29. All artifact reads are pure file reads; no repo script was executed.

---

## 1. Two corrections to recon R4

Both matter for the verdict, and the second matters for anything anyone later tries to print.

### 1.1 The blocking inputs are NOT absent — R4's headline blocker is worktree-local

R4 returned `RUN_NEEDED_INPUTS_ABSENT` on the strength of the three gitignored S8 inputs being missing. They are missing **here**, and present **in the main checkout**. Verified by direct `ls` at both paths:

| input | this worktree | main checkout `/Users/eugene/somthing/Lock In effect/Lock-in-Effect/hazard/data/` |
|---|---|---|
| `floor_form_offwindow/microsim_max_floor4.991pct_pq6.5.parquet` | absent (dir does not exist) | **present** |
| `floor_form_offwindow/microsim_max_floor4.991pct_pq0.parquet` | absent | **present** |
| `fannie_quarters/` (24 cells + manifest) | absent (dir does not exist) | **present, 50 files** |
| `cohort_month_panel_fannie.parquet` | absent | **present** |

(`.gitignore:56,58,70`. The main checkout also carries the `microsim_additive_floor4.991pct_pq{0,5.5,6.5,7.7}` legs.)

So "inputs absent" is a statement about where the agent was standing, not about the repo. A composed run is mechanically feasible today in the main checkout, with committed machinery (`overlay_leg` / `own_series` / `shared` in `ginnie_cpr_overlay.py` and `ginnie_overlay_offwindow.py`; the blend template in `vintage_overlay.py`). The record must not rest on a false blocker — the real one is in section 4.

### 1.2 R4's expectation band overstates its own precision

R4 reported the composed marginal as **[+2.868, +2.874]pp = [$21.93, $21.98]B**. The arithmetic reproduces exactly, but it **mixes two share bases**, and the gap between them is larger than the band it prints.

The intersection interval is computed on the *artifact* basis (`agency_shares` / `vintage_group_shares` in `composition_shift_results.json`, as-of 2026-07-15). The union share is then formed against the *nominal* overlay shares (Ginnie 0.204, vintage 0.337 from `wal_table.py VINTAGE_SHARES`). Those disagree:

- Ginnie: nominal 0.204 vs artifact 0.20420609672911058 (0.0206pp apart)
- vintage: nominal 0.337 vs artifact 0.10646144874776454 + 0.231953826784626 = 0.338415276 (0.1415pp apart)

Carrying each basis through consistently, with intersection I in [0.055753407475, 0.056891329946] and marginal 5.57155818290974pp:

| basis | band | width |
|---|---|---|
| A: nominal shares (R4's) | [+2.8680, +2.8743]pp | 0.0063pp |
| B: artifact shares | [+2.8589, +2.8653]pp | 0.0063pp |

Centres 2.8711 vs 2.8621 — a **0.0090pp basis gap, 1.4x the 0.0063pp band width**. A three-decimal band whose stated width is narrower than the ambiguity it silently resolved is not a defensible printed object. The honest envelope over both bases is **[+2.859, +2.874]pp = [$21.86, $21.98]B**, and even that is an expectation, not a measurement.

A related basis seam, pre-existing and already disclosed: the joint cells are keyed by vintage **group**, so `GNMA|...|2022` is 2022-and-later, while the manuscript's 23.1% is the vintage **year** share (`vintage_year_shares.2022` = 0.23129478111342439 vs `vintage_group_shares.2022` = 0.231953826784626; the 0.0659pp difference is 2023-26 dribble).

---

## 2. What exists: the cross-tab is real but truncated

The round-28 ruling recorded in the artifact — `vintage_overlay_results.json` -> `composed_with_ginnie`:

```
status: "NOT_COMPUTED"
reason: "agency x vintage cross-tab incomplete: the 2022 x Ginnie intersection is 2.4pp of book
         face ... but the pre-2017 x Ginnie intersection is not in the committed artifact"
```

Round 28 also left a standing instruction, `specs/SPEC_round28_D_F1_I1_I3_J2_S8.md:533`: "**NO composed Ginnie x vintage cell is specified or claimed.** ... A composed cell therefore requires the full agency x vintage cross-tab to be verified first — **flag it, do not run it.**" This record discharges that instruction: the cross-tab is now verified (as a bound, section 2), and the answer is still do not run it (sections 4-5).

Note the line references have staled. The artifact's `reason` string cites `revised_paper_v18.tex:1156`, the spec cites "tex 1148"; the sentence now sits at **line 1275**. The text is unchanged — only its address moved.

The ruling is true **as an exact point** and false as a bound. `composition_shift_results.json` -> `soma_book.latest.joint_cells_min_share_0p1pct` holds 55 cells keyed `agency|term|coupon|vintage_group`, as-of 2026-07-15 (a second 65-cell grid exists for the June-2022 as-of). Cells below 0.1% of book face are dropped: listed mass 0.991788, unlisted 0.008212.

Aggregated to agency x vintage group (listed cells only), reproduced independently from the artifact:

| | pre2017 | 2017-19 | 2020 | 2021 | 2022 |
|---|---|---|---|---|---|
| GNMA | 0.032179 | 0.012401 | 0.050186 | 0.084728 | 0.023575 |
| UMBS | 0.072208 | 0.044548 | 0.110900 | 0.354265 | 0.206797 |

Four `GNMA|30yr|*|pre2017` cells **are** listed (coupons 3.0/3.5/4.0/4.5 = 0.013956970631708011 / 0.013216560791056662 / 0.003942212866504323 / 0.0010629090170267011; sum 0.032178653306). Marginal-residual arithmetic over the same file closes the rest:

- unlisted GNMA mass = 0.20420609672911058 − 0.20306895733581637 = 0.001137139393
- unlisted pre2017 mass = 0.002074574588; unlisted 2022-group mass = 0.001582491967

giving **GNMA x pre2017 in [3.2179%, 3.3316%]** and **GNMA x off-window-vintage (2022 + pre2017) in [5.5753%, 5.6891%]** of book face (both capped by total unlisted GNMA mass, which binds against the 0.3657% vintage-side slack).

An exact point is unobtainable *in principle* for this book: `composition_shift.py` fetches SOMA CUSIP rows live and caches nothing ("no cached fallback", module header; `JOINT_CELL_MIN_SHARE = 0.001` at line 348, grid emitted at line 679), so a re-run tabulates the **current** as-of, a different book than the committed 2026-07-15 snapshot. The interval is the terminal form the committed data supports.

---

## 3. Provenance of the manuscript's 23.1 / 20.7 / 2.4

Sentence at `paper/v18/revised_paper_v18.tex:1275` (char offset 911 in a 1,615-char line):

> The joint agency$\times$vintage cells settle the one netting question the marginals leave open: of the 2022 vintage's 23.1\% of book face, 20.7\% is conventional and 2.4\% is the Ginnie intersection, so vintage and agency marginals cannot be added without double-counting that cell.

- 23.1 = `vintage_year_shares.2022` = 0.23129478111342439 (year basis)
- 20.7 = sum of listed `UMBS|*|*|2022` cells = 0.206797 (group basis, listed-only)
- 2.4 = sum of the six listed `GNMA|30yr|*|2022` cells = 0.023575 (group basis, listed-only)

The printed literals sum consistently (20.7 + 2.4 = 23.1), though the underlying listed sums give 23.04% against a 23.13% year share — the 0.09pp residual is unlisted-cell truncation (0.158pp) net of 2023-26 dribble (0.066pp). This is already disclosed: `specs/SPEC_round28_D_F1_I1_I3_J2_S8.md:573` records "Covered face `0.23037` against the vintage's `0.231954` group share — **99.3% cell coverage**", which is exactly the listed 2022-group sum reproduced in section 2. Pre-existing, disclosed, not a defect introduced here, and no reason to touch the sentence.

---

## 4. The real blocker: the intersection cell has no observable speed

Even with every input staged, the composed overlay cannot score its own distinguishing cell.

**No Ginnie-by-vintage prepayment series exists.** `gmar_dec25_cpr_series.json` — the only Ginnie speed source in the repo — is agency-aggregate: 102 monthly points for `cpr`/`cdr`/`crr` x {fannie, freddie, ginnie}, extracted from GMAR Dec-2025 Figures 12/13/14. There is **no vintage dimension** (the only "2020"/"2021" strings in the file are month labels). I searched every JSON under `hazard/data/` for a Ginnie-and-vintage co-occurrence; eight files match on both tokens, and none carries a by-vintage Ginnie series:

- `composition_shift_results.json` — face **shares**, not speeds
- `vintage_residual_bound_results.json`, `vintage_1516_subleg_results.json`, `vintage_overlay_results.json` — Fannie-sourced vintage speeds; Ginnie appears only as a share or a bound anchor
- `ginnie_bound.json`, `ginnie_cpr_overlay_results.json`, `ginnie_overlay_offwindow_results.json`, `gmar_dec25_cpr_series.json` — Ginnie aggregate only

The vintage legs are Fannie (`fannie_quarters/`, acquisition-file cells); the Ginnie leg is published-aggregate GMAR. **They do not intersect in any observed data.** The [5.58%, 5.69%] cell would necessarily be scored by the full-universe Ginnie series — a proxy layered on the already-disclosed proxies (Fannie speeds standing in for the SOMA book; the pre-2017 leg being a seasoned tail; the 2022 leg being full-year against an H1-tilted face). The composed cell can never be cleaner than that proxy, and the proxy is precisely the dimension the composition is supposed to resolve.

---

## 5. And the run would return an answer already known

The two existing overlays are, on their own evidence, near-pure share rescalings:

| overlay | realized scale | nominal retained share | overlay-specific component |
|---|---|---|---|
| Ginnie off-window | 0.7975182199226121 | 0.796 | **+0.0021157340096635835 pp** |
| Vintage off-window | 0.6644737240199917 | 0.663 | **+0.001041906299988682 pp** |

Against a 5.57155818290974pp conventional off-window marginal, the *entire* overlay-specific content is ~0.002pp and ~0.001pp — under 0.04% of the estimate. `vintage_overlay_results.json` says so in its own committed verdict: "pure share scaling"; its `expectation_check` block pre-committed a scale band [0.655, 0.672] and landed at 0.6645.

So a composed run would return ~5.57 x retained, i.e. the section-1.2 envelope, plus an overlay-specific term of order 0.002pp — which is **a third of the 0.0063pp band width and a fifth of the 0.0090pp basis gap**. The run cannot resolve its own basis ambiguity, let alone say anything the committed shares do not.

This is the substantive verdict: mechanically `RUN_NEEDED_INPUTS_PRESENT`, substantively `NOT_FEASIBLE` — a run that consumes the frozen 4.991% legs to report a number already implied by two committed share constants, while its one novel cell rests on an unobservable speed.

---

## 6. Manuscript decision: no edit

**Recommendation: land this record only.** Five reasons, in descending force:

1. **The negative claim is already complete.** Line 1275 states the intersection exists, gives its size, and draws the operative consequence ("cannot be added without double-counting that cell"). Nothing about the disclosure is wrong or missing.
2. **The constructive resolution is not a measurement.** The [+2.859, +2.874]pp envelope is committed-share arithmetic. Round-28 discipline forbids printing it as a run result, and it is not one.
3. **Its precision is illusory** (section 1.2): the basis gap exceeds the band width. Any printed form either overstates precision or needs a paragraph of basis caveat to be honest — a poor trade for a number that changes no conclusion.
4. **The non-additivity is already recorded twice in committed artifacts**, so the paper's claim is backed without new prose: `vintage_overlay_results.json` caveat ("the vintage face shares span the full book INCLUDING Ginnie collateral, so this overlay and the Ginnie overlay overlap on Ginnie's out-of-window vintages; they are not additive — see composed_with_ginnie") and `vintage_residual_bound_results.json` caveat ("one-dimensional bounds, not additive").
5. **Standing bias against prose that adds no measured content.** A third `tab:assembly` row would compound two change-of-estimand rows with a third that is neither run nor identified — re-scoping the marginal onto ~51.5% of book face while the 5.6% intersection is scored by proxy. That weakens the table's meaning rather than extending it.

**If the coordinator overrules and wants something landed anyway**, the minimum defensible form is a bound, not a point, and it belongs in the same sentence rather than in `tab:assembly` — e.g. appending to line 1275: *"...that cell, which the committed grid bounds at 5.6--5.7\% of book face."* That adds two literals (`5.6`, `5.7`), both already present in the file (counts in section 7), and claims only what section 2 proves. I do **not** recommend it: it restates the existing sentence's own point at the cost of a bound the reader cannot use.

---

## 7. Zero-slack ledger

**Literals added or touched by this record: zero.** No `.tex` edit is proposed. This file is inert to the gates — `tools/liveness_gates.py` reads the manuscript and `hazard/data/*.json`, never `specs/*.md` (its only `.md` references are TECHNICAL.md mentions inside comments, lines 4 and 10). Gates remain 106/106, tests 451, build 129pp.

Whole-file counts in `paper/v18/revised_paper_v18.tex`, this session (2026-07-29), for the literals any future edit at this site would touch — **re-derive immediately before any edit, including and-forms**:

| literal | count |
|---|---|
| `23.1` | 6 |
| `20.7` | 1 |
| `2.4` | 29 |
| `5.57` | 5 |
| `2.9` | 23 |
| `5.6` | 54 |
| `5.7` | 29 |
| `21.9` | 0 |
| `51.5` | 0 |

Full-precision sources for every value quoted above:

| value | source |
|---|---|
| 5.57155818290974 (marginal pp) | `hazard/data/ginnie_overlay_offwindow_results.json` -> `conventional_offwindow.marginal_pp` |
| 764.7482532227002 (benchmark $B) | same file's sibling anchor; `vintage_overlay_results.json` -> `committed_anchors.benchmark_b` |
| 0.20420609672911058 (GNMA share) | `composition_shift_results.json` -> `soma_book.latest.agency_shares.GNMA` |
| 0.10646144874776454 / 0.231953826784626 | same -> `vintage_group_shares.{pre2017,2022}` |
| 0.23129478111342439 | same -> `vintage_year_shares.2022` |
| 0.20306895733581637 / 0.032178653306 / 0.055753407475 | sums over `joint_cells_min_share_0p1pct` (55 cells) |
| 0.7975182199226121 / 0.0021157340096635835 | `ginnie_overlay_offwindow_results.json` -> `marginal_scale_vs_conventional`, `ginnie_specific_marginal_component_pp` |
| 4.443419164229439 / 33.98097044180736 | same -> `overlay_offwindow.primary.{marginal_pp,marginal_b}` |
| 0.6644737240199917 / 0.001041906299988682 | `vintage_overlay_results.json` -> `marginal_scale_vs_retained`, `vintage_specific_marginal_component_pp` |
| 3.702154014392093 / 28.312158156677583 | same -> `primary.{marginal_pp,marginal_b}` |
| 0.204 / 0.337 / 0.663 (nominal) | `hazard/wal_table.py:41` VINTAGE_SHARES; `vintage_overlay_results.json` -> `shares` |

---

## 8. What would have to change to reopen this

Not a staging problem — the inputs are already in the main checkout. Reopening requires **new observed data**, specifically one of:

1. A **Ginnie-by-vintage prepayment series** — a GMAR issue (or Recursion extract) breaking CPR out by origination cohort, or Ginnie pool-level factor data tabulated to cohort. This alone converts the composed cell from proxied to observed and is the binding requirement.
2. A **cached SOMA CUSIP snapshot at the committed as-of**, if an exact rather than bounded intersection is ever wanted. Note this is strictly secondary: it sharpens a 0.114pp-wide interval that is already narrower than the estimand defect in (1).

Absent (1), any composed run remains a share multiplication wearing a run tag. That is the finding.

**Key paths:** `hazard/data/composition_shift_results.json`, `hazard/data/vintage_overlay_results.json`, `hazard/data/ginnie_overlay_offwindow_results.json`, `hazard/data/ginnie_cpr_overlay_results.json`, `hazard/data/gmar_dec25_cpr_series.json`, `hazard/data/vintage_residual_bound_results.json`, `hazard/vintage_overlay.py:80-99` (blocking input check), `hazard/composition_shift.py:348,679`, `specs/SPEC_round28_D_F1_I1_I3_J2_S8.md:494-538`, `paper/v18/revised_paper_v18.tex:1275`, `hazard/wal_table.py:41`, `.gitignore:56,58,70`.
