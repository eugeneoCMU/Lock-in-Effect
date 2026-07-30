# DRAFT — Round 32 Wave 2, cluster E (composition)

Conditions assigned: **C-06, C-63, C-64, C-65**
Region: `tab:composition` (Table 25), §VII.E (`sec:robustness-hybrid`), the sampling appendix (`app:params`)
Target file: `paper/v18/revised_paper_v18.tex` (canonical). Nothing in the worktree was modified.

5 edits drafted (C-06 ×1, C-63 ×1, C-64 ×3). **C-65 NOT DRAFTED** — see the block at the end.

Line numbers as of the read: `app:params` = 1017, its attrition paragraph = 1091; §VII.E full-book sentence = 707;
`tab:composition` caption = 1277, header/panel-(a) rows = 1283–1288, in-float notes = 1300.
(The inventory's `.tex:1085` / `.tex:701` / `.tex:1279–1283` / `.tex:1294` have all shifted by the Wave-1 landings.)

---

## Edit 1 — App. `app:params` states the sampler's allocation rule, that the draw is not a probability sample of the book, and both bases of its vintage composition (C-06)

FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1

OLD:
```
Attrition accounting: of the 75,000 sampled loans, 34,734 prepaid and 32 defaulted before the QT window opens
```

NEW:
```
Sampling design: the draw is not a probability sample of the SOMA book, and the allocation rule is why. A pool built at four times the target size takes an equal allocation from each quarterly Freddie origination file; the pool is then drawn down to 75,000 loans proportionally within stratum, and every retained loan carries weight one (\texttt{hazard/loan\_sample.py}). Nothing in that chain reweights toward the book, and two consequences bind the censoring that sets the marginal. Each origination year from 2017 through 2021 takes 20.0\% of the draw by count, so 2017--19 is 60.0\% of it against 6.0\% of book face and 2021 is 20.0\% against 43.9\%; on origination balance the same two shares are 55.5\% and 22.3\% (Table~\ref{tab:composition}), and neither basis is the one aggregation applies --- that is the surviving-balance share at the window open, which shifts weight from 2017--19 toward 2021 because the older vintages had prepaid down further by June 2022. The 2022 vintage, 23.1\% of book face, has no support in the draw at all, and the draw's 3.86\% mean note rate sits above the book's 2.49\% pass-through coupon. Both tilts move the rate-gap distribution the floor takes its maximum against, and this paper does not sign either: Section~\ref{sec:robustness-hybrid}'s coupon reweight rescales the aggregate level and leaves the marginal bit-invariant, so it does not test a composition effect that runs through the floor's bind share. Attrition accounting: of the 75,000 sampled loans, 34,734 prepaid and 32 defaulted before the QT window opens
```

RATIONALE: C-06 was upgraded to CRITICAL because the rule is nowhere in the manuscript. The insertion prepends the disclosure to the paragraph that already describes the draw (attrition accounting), so sampling design → attrition → loan-months → floor bind reads as one account of the same object; the `Sampling design:` lead-in mirrors the paragraph's existing `Attrition accounting:` habit. It names the rule (equal per quarterly file, proportional draw-down within stratum, weight one), the two censoring-relevant tilts, and the fact that neither printed basis is the weighting the aggregation applies. Both magnitudes are basis-labelled, so anti-condition A-15's unlabelled "factor of ten" rhetoric is not reproduced.

LITERALS_INTRODUCED:
- `20.0\%` (×2), `60.0\%` — count shares implied by the equal-allocation rule (`hazard/loan_sample.py:97`, `:164`) and by `loan_sample.parquet` vintage counts 15,002/14,999/15,001/14,997/15,001 (task brief; not in the frozen JSON — see UNVERIFIED)
- `55.5\%`, `22.3\%` — `composition_shift_results.json` → `freddie.sample.vintage_group_shares_upb_weighted` = 0.5551051 / 0.2231810
- `6.0\%`, `43.9\%`, `23.1\%` — `committed_anchors.vintage_shares` (`2017-19` 0.06, `2021` 0.439, `2022` 0.231); all three already occur elsewhere in the .tex
- `3.86\%` — `freddie.sample.mean_coupon_pct` = 3.864892813333333 (and `gates.G1_freddie_sample_integrity.sample_wac_parity`)
- `2.49\%` — `committed_anchors.book_cohort_wac_pct`
- `75,000` (already in the OLD span, count unchanged)

LITERALS_REMOVED: none.

PINNED_SPANS_CROSSED: `Attrition accounting: of the 75,000 sampled loans, 34,734 prepaid and 32 defaulted before the QT window opens` is reproduced byte-identically as the tail of NEW. The new phrase `leaves the marginal bit-invariant` deliberately does **not** contain gate #106's pinned span `the identified marginal bit-invariant` (that span stays at its single site in `tab:bases`' post-float note). `Appendix~\ref{...}`/`Section~\ref{...}` forms only, so `HARDCODED_XREF` stays at zero.

---

## Edit 2 — §VII.E names the object behind the 3.9% origin (C-63)

FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1

OLD:
```
The Path A and Path B headline recoveries are balance-weighted estimates on the Freddie sample's composition, whose weighted-average coupon (3.9\%) sits above the SOMA book's (2.49\%).
```

NEW:
```
The Path A and Path B headline recoveries are balance-weighted estimates on the composition of the Freddie object each path uses: Path A the full 2017--2021 origination universe, Path B the 75,000-loan draw, whose unweighted mean note rate of 3.86\% sits above the book's 2.49\% face-weighted pass-through coupon. The origin of the Path B reweight is that draw; the bucket shares Table~\ref{tab:composition} prints beside the book are the universe's, exposure-weighted at the window open, and the two are different populations.
```

RATIONALE: The old sentence had two defects that C-63 covers. It called the figure a "weighted-average coupon" when §V.B already records it as the *unweighted* mean of borrower note rates (3.8649 is `mean_coupon_pct`, a plain mean over 75,000 loans), and it said "the Freddie sample" where Path A uses the origination universe and Path B the draw — the same conflation Table 25 commits. The replacement names both objects, attributes the WAC to the draw, and says which population T25's bucket shares belong to.

LITERALS_INTRODUCED:
- `3.86\%` — `freddie.sample.mean_coupon_pct` = 3.864892813333333
- `2.49\%` — `committed_anchors.book_cohort_wac_pct` (was already in this sentence as `(2.49\%)`)

LITERALS_REMOVED: `3.9\%` at this site (whole-file count 12 → 11 with Edit 5, see CENSUS); `weighted-average coupon` 6 → 5.

PINNED_SPANS_CROSSED: none inside OLD. Gate #106's `the bound tightens by an order of magnitude` and the `107.0\% to 109.1\%` / `121.5\% to 127.5\%` / `107.2\%` literals all sit later in the same source line and are untouched. Gate `dispersion_split` requires `3.9\%` **somewhere** in the .tex; it survives at 9 other sites (including its own at lines 1356/1394 beside `96.1\%`), so removing this one is safe.

---

## Edit 3 — tab:composition caption declares the three populations (C-64)

FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1

OLD:
```
\caption{Composition comparison. Panel (a): hazard estimation universe (Freddie Mac, exposure-weighted at the June 2022 window open) versus the SOMA agency-MBS book (CUSIP-level holdings, anchor-gated). Panel (b):
```

NEW:
```
\caption{Composition comparison. Panel (a): the two Freddie objects the hazard paths use --- the estimation universe Path A is fitted on (exposure-weighted at the June 2022 window open) and, indented beneath it, the 75,000-loan draw Path B simulates (on count weights and on origination balance) --- against the SOMA agency-MBS book (CUSIP-level holdings, anchor-gated). The three are distinct populations; only the universe rows enter the PSI column, and no row differences one population against another. Panel (b):
```

RATIONALE: C-64's core requirement is that the table stop presenting two populations as one. The caption now enumerates the three objects, says which rows are which, and states that the PSI column belongs to the universe rows only — so the added draw rows cannot be read as a second PSI comparison.

LITERALS_INTRODUCED: none (`75{,}000` appears as `75,000` in prose form; the numeral already occurs 30+ times in the file).
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none. Gate #38 checks only the PSI literals (`2.54`, `4.33`, `2.29`, `PSI 0.018`, `PSI 0.005`) and `\texttt{composition\_shift}` ≥ 1; all untouched.

---

## Edit 4 — tab:composition panel (a) gains the draw's own vintage and coupon rows, on both bases (C-64)

FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1

OLD:
```
Dimension & Sample (\%) & Book (\%) & PSI; committed consequence \\
\midrule
\multicolumn{4}{@{}l}{\emph{(a) Estimation universe vs SOMA book}} \\
Agency & UMBS 100.0; Ginnie 0.0 & UMBS 79.6; Ginnie 20.4 & 2.54; static bound \$20--47B, overlay differential $+\$38.5$B \\
Vintage & pre-2017: 0.0; 2017--19: 12.5; 2020: 37.3; 2021: 50.2; 2022: 0.0 & 10.6; 6.0; 16.3; 43.9; 23.1 & 4.33; vintage residual bound \$11.7 billion \\
Coupon & $<3.0\%$: 18.0; 3.0--4.0\%: 68.2; $\geq 4.0\%$: 13.8 & 73.9; 18.7; 7.3 & 2.29; full-book reweighting 107.0\% $\to$ 109.1\% \\
```

NEW:
```
Dimension & Freddie side (\%) & Book (\%) & PSI; committed consequence \\
\midrule
\multicolumn{4}{@{}l}{\emph{(a) Freddie side vs SOMA book: estimation-universe rows, with Path B's draw indented beneath}} \\
Agency & UMBS 100.0; Ginnie 0.0 & UMBS 79.6; Ginnie 20.4 & 2.54; static bound \$20--47B, overlay differential $+\$38.5$B \\
Vintage & pre-2017: 0.0; 2017--19: 12.5; 2020: 37.3; 2021: 50.2; 2022: 0.0 & 10.6; 6.0; 16.3; 43.9; 23.1 & 4.33; vintage residual bound \$11.7 billion \\
\quad Path B draw & \emph{count}: 0.0; 60.0; 20.0; 20.0; 0.0 \newline \emph{orig.\ balance}: 0.0; 55.5; 22.2; 22.3; 0.0 & & no PSI; equal allocation per origination quarter, never reweighted (Appendix~\ref{app:params}) \\
Coupon & $<3.0\%$: 18.0; 3.0--4.0\%: 68.2; $\geq 4.0\%$: 13.8 & 73.9; 18.7; 7.3 & 2.29; full-book reweighting 107.0\% $\to$ 109.1\% \\
\quad Path B draw & \emph{count}: 7.1; 34.7; 58.2 \newline \emph{orig.\ balance}: 7.9; 38.4; 53.7 & & no PSI; draw WAC 3.86\%; the reweight moves the level, not the marginal \\
```

RATIONALE: Two indented sub-rows, each carrying both bases, is the minimal change that satisfies C-64 without a fifth column (the four `p{}` widths already total 15.1 cm). The draw's zero support at pre-2017 and 2022 becomes visible in the same row order as the book column. The `Sample (\%)` header was the source of the two-populations-as-one reading and becomes `Freddie side (\%)`; every panel-(a) row is then identified as universe (unindented) or draw (indented). The coupon sub-row's consequence cell records what the printed 107.0 → 109.1 consequence does *not* cover — the marginal — which is the fact C-07 rests on.

LITERALS_INTRODUCED:
- vintage draw, count `0.0; 60.0; 20.0; 20.0; 0.0` — equal-allocation rule + parquet vintage counts (see UNVERIFIED)
- vintage draw, orig. balance `0.0; 55.5; 22.2; 22.3; 0.0` — `freddie.sample.vintage_group_shares_upb_weighted` 0.5551051 / 0.2217139 / 0.2231810, with 0.0 for pre-2017 and 2022 from `gates.G1_freddie_sample_integrity.vintage_range = [2017, 2021]`
- coupon draw, count `7.1; 34.7; 58.2` — `freddie.sample.coupon_shares_count_weighted` bucketed on the same rounded-coupon convention as the printed universe row: 7.093 / 34.703 / 58.204
- coupon draw, orig. balance `7.9; 38.4; 53.7` — `freddie.sample.coupon_shares_upb_weighted` bucketed identically: 7.886 / 38.434 / 53.681
- `3.86\%` — `freddie.sample.mean_coupon_pct`

LITERALS_REMOVED: none. `2.54`, `4.33`, `2.29`, `13.8`, `68.2`, `18.0`, `12.5; 2020: 37.3; 2021: 50.2`, `107.0\% $\to$ 109.1\%`, `\$20--47B`, `$+\$38.5$B`, `\$11.7 billion` all reproduced byte-identically.

PINNED_SPANS_CROSSED: gate #38's PSI literals `2.54`, `4.33`, `2.29` are inside OLD and reproduced byte-identically. `53.7` is A-07's basis-sensitive number and is printed **only** on the origination-balance row, with `58.2` beside it on the count row and the bucket convention named in the note (Edit 5), so it is never unqualified. Anti-condition A-07 satisfied.

**One new LaTeX construct:** `\newline` occurs 0 times in the current .tex. It is standard inside a `p{}` column and only forces the wrap where the basis changes. If the coordinator prefers zero new constructs, replacing each ` \newline ` with `; ` leaves the cells correct and lets the column wrap on its own.

---

## Edit 5 — tab:composition note repaired: WAC attributed to the draw, every basis named, and the conservative-signing claim scoped (C-64)

FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1

OLD:
```
\item \emph{Notes:} Sample coupon shares are exposure-weighted universe-panel shares at the window open; the sample WAC is 3.9\% against the book's 2.49\%. Every shift is signed in the same conservative direction: the out-of-sample segments prepaid faster, so trapped liquidity is if anything overstated (Section~\ref{sec:pathb}). Panel (b) uses
```

NEW:
```
\item \emph{Notes:} Three populations appear in panel (a) and none is mixed within a row: the unindented rows are the hazard estimation universe, exposure-weighted at the window open; the indented rows are the 75,000-loan Path B draw, on count weights and on origination balance; the Book column is SOMA face. Coupon buckets are rounded-coupon buckets on every side, which is why the draw's $\geq 4.0\%$ share reads 53.7\% on origination balance and 58.2\% by count. The WAC pair is mixed-basis, as Section~\ref{sec:pathb} records: the draw's 3.86\% is the unweighted mean of borrower note rates, the book's 2.49\% the face-weighted mean of security pass-through coupons. Every shift is signed in the same conservative direction: the out-of-sample segments prepaid faster, so trapped liquidity is if anything overstated (Section~\ref{sec:pathb}). That signing covers observed speeds in the segments outside the draw's support; it does not cover what the draw's composition within 2017--2021 does to the floor's bind share, which no committed run scores (Appendix~\ref{app:params}). Panel (b) uses
```

RATIONALE: The note is where C-64's confirmed defect lives — "Sample coupon shares are exposure-weighted universe-panel shares" and "the sample WAC is 3.9\%" put the universe panel and the draw in one sentence with one label. The replacement separates the three populations, attributes the WAC to the draw with its basis, and names the rounded-coupon bucketing so `53.7` and `58.2` cannot be read as competing values of one quantity. The conservative-signing disclosure is preserved byte-identically and then *scoped* rather than deleted: it is a claim about realized speeds in the out-of-support segments, and it is not a claim about the censoring-mediated composition effect that C-07's run exists to score. Without that scope clause the new draw rows would sit directly under a sentence that appears to sign them.

LITERALS_INTRODUCED:
- `53.7\%`, `58.2` — the same bucket sums as Edit 4 (`coupon_shares_upb_weighted` 53.681, `coupon_shares_count_weighted` 58.204)
- `3.86\%` — `freddie.sample.mean_coupon_pct`

LITERALS_REMOVED: `3.9\%` at this site. `2.49\%` retained.

PINNED_SPANS_CROSSED: `Every shift is signed in the same conservative direction: the out-of-sample segments prepaid faster, so trapped liquidity is if anything overstated (Section~\ref{sec:pathb}).` and `Panel (b) uses` reproduced byte-identically. No gate or test matches any string in this OLD span (checked `aggregates-only`, `Composition comparison`, `conservative direction`, `prepaid faster`, `Sample coupon shares`, `exposure-weighted universe-panel` against `tools/liveness_gates.py` and `tests/*.py`: zero hits). Note stays **in-float** (`tablenotes`) — `tab:composition` is not one of the five tables Round 31 moved to post-float notes.

---

## NOT DRAFTED — C-65

Two independent reasons, and the first is the one that binds.

**1. All three of C-65's sites are outside my assigned region.** The condition's `location` is `.tex:31` (abstract), the T1 marginal cell (`.tex:79`, now ~`:85`), and §V.E (`.tex:333`, now ~`:339`). My region is `tab:composition`, §VII.E and the sampling appendix. Drafting OLD spans at those three sites would collide with a sibling drafter and, at line 31, would move the abstract against gate #101's word-count tie to the response letter. I am not touching them.

**2. C-65 is the declared fallback and the preferred fix landed.** The inventory records it as "the fallback, not the preferred fix"; my brief states it applies "if the row cannot be added". The row *can* be added and is Edit 4. Note, however, that the inventory's own trigger is *`Absent C-07`*, and C-07 is a Wave-3 run that has not executed — so on the inventory's wording the trigger is still live even after Edit 4. That is a live gap, not a closed one, and it is in DECISION_NEEDED below.

**What Edit 1 does discharge, inside my region:** the substance of the conditioning statement now exists at the disclosure site — "the draw is not a probability sample of the SOMA book", both tilts named with their bases, and "this paper does not sign either", with the reason the existing coupon reweight cannot sign them. What is *not* discharged is the propagation to the three headline-quoting sites, which is C-65's whole point.

Also, for the record, one thing I did not do: R2 signs the two limbs (seasoning inflationary through the floor gate, gap-depth deflationary through $H(1-d)$). The inventory records that neither is signed anywhere in the .tex, and no committed artifact signs them, so Edit 1 says the directions are unsigned rather than reproducing R2's signs.

---

## CENSUS

Measured with `str.count` on the file as read and on the in-memory result after applying all five edits in order (helper: `scratchpad/r32/check_w2E.py`). All five OLD spans are unique (count == 1).

| literal / pinned phrase | before | after |
|---|---|---|
| `3.9\%` | 12 | 11 |
| `3.86\%` | 0 | 4 |
| `2.49\%` | 9 | 10 |
| `53.7\%` | 0 | 1 |
| `58.2` | 0 | 2 |
| `60.0\%` | 1 | 2 |
| `20.0\%` | 0 | 2 |
| `55.5\%` | 0 | 1 |
| `22.3\%` | 0 | 1 |
| `22.2\%` | 0 | 0 (table cell is bare `22.2;`) |
| `34.7` | 0 | 1 |
| `38.4` | 0 | 1 |
| `7.9;` | 0 | 1 |
| `7.1;` | 0 | 1 |
| `23.1\%` | 5 | 6 |
| `43.9\%` | 1 | 2 |
| `6.0\%` | 17 | 18 |
| `2.54` | 1 | 1 |
| `4.33` | 1 | 1 |
| `2.29` | 4 | 4 |
| `PSI 0.018` | 1 | 1 |
| `PSI 0.005` | 1 | 1 |
| `13.8` | 3 | 3 |
| `68.2` | 1 | 1 |
| `18.0;` | 1 | 1 |
| `12.5; 2020: 37.3; 2021: 50.2` | 1 | 1 |
| `107.0\% $\to$ 109.1\%` | 1 | 1 |
| `\texttt{composition\_shift}` | 2 | 2 |
| `Sample (\%)` | 1 | 0 |
| `Freddie side (\%)` | 0 | 1 |
| `Estimation universe vs SOMA book` | 1 | 0 |
| `weighted-average coupon` | 6 | 5 |
| `Attrition accounting: of the 75,000 sampled loans` | 1 | 1 |
| `1,683,124` | 6 | 6 |
| `40,234` | 5 | 5 |
| `96.1\%` | 3 | 3 |
| `not a probability sample` | 0 | 1 |
| `no PSI;` | 0 | 2 |
| `\quad Path B draw` | 0 | 2 |
| `\newline` | 0 | 2 |

Gate-pinned spans, all unchanged at count 1:

| pinned span | gate | before | after |
|---|---|---|---|
| `the bound tightens by an order of magnitude` | #106 `COUPON_CONVENTION_SPANS` | 1 | 1 |
| `That is a mixed-basis measurement` | #106 | 1 | 1 |
| `not the corrected number` | #106 | 1 | 1 |
| `the identified marginal bit-invariant` | #106 | 1 | 1 |
| `98.1\% (97.6--99.1 across the legs; run \texttt{coupon\_convention\_reweight})` | #106 | 1 | 1 |
| `note rate less the vintage guarantee fee and base servicing, $\Delta = 0.80$ points` | #106 | 1 | 1 |
| `Every shift is signed in the same conservative direction` | (unpinned, preserved anyway) | 1 | 1 |

`bit-invariant` alone goes 4 → 5 (Edit 1's `leaves the marginal bit-invariant`); the pinned longer form stays at 1.
Source line count 1435 → 1437 (two added table rows).
`ZERO_COUNT` (24 phrases) and `EXACTLY_ONE` (4 phrases): no edit introduces or duplicates any of them.
`HARDCODED_XREF`: all new cross-references use `Table~\ref{}` / `Section~\ref{}` / `Appendix~\ref{}`; the file uses `Appendix~` 80× and `App.~` 0×, so I used the long form.

---

## UNVERIFIED

1. **The draw's count-basis vintage shares (`20.0` each, `60.0` for 2017–19).** Not in any frozen artifact. `composition_shift_results.json` carries only `n_loans = 75000`, `gates.G1_freddie_sample_integrity.weight_sum = 75000.0` and `vintage_range = [2017, 2021]`. The shares come from the brief's `loan_sample.parquet` counts (15,002 / 14,999 / 15,001 / 14,997 / 15,001 → 20.003 / 19.999 / 20.001 / 19.996 / 20.001) and are independently implied by the allocation rule at `hazard/loan_sample.py:97` and `:164`. **Confirmed by:** a `group_by("vintage").len()` on `hazard/data/loan_sample.parquet`. I did not read the parquet (outside the .tex/.json/.csv read permission).
2. **"the surviving-balance share at the window open, which shifts weight from 2017--19 toward 2021"** (Edit 1). The direction, not a number. Corroborated by the paper's own two objects — the universe panel drops 2017–19 to 12.47% on exposure weights against 55.51% of the draw's origination balance — and by the attrition accounting (34,734 of 75,000 prepaid before the window, concentrated in the higher-coupon 2017–19 cohorts through the 2020–21 refi wave). **Confirmed by:** a balance-weighted vintage group_by on the draw at the June 2022 snapshot. A-15's actual values (27.05% / 42.31%) exist in no artifact I can read, so I state the direction and print neither.
3. **"which no committed run scores"** (Edit 5) and **"does not test a composition effect that runs through the floor's bind share"** (Edit 1). Rests on C-07's `verified: true` finding that the coupon reweight rescales aggregate output and leaves the marginal bit-invariant, which the manuscript itself asserts in `tab:bases`' note. **Confirmed by:** an inventory of committed run artifacts for any that post-stratifies the pool onto book cells; I read only `composition_shift_results.json`.
4. **LaTeX build.** Two added rows plus a longer caption and note change `tab:composition`'s height; the float is `[H]` so it will not migrate, but the page count may go 130 → 131. `\newline` in a `p{}` column is standard but appears nowhere else in this file. **Confirmed by:** the coordinator's build (0 undefined, page count, `tab:composition` still on one page).
5. **Book coupon bucket row (`73.9; 18.7; 7.3`)** — untouched by me and not re-derived; it is the pre-existing printed row.

---

## WORD_COUNT_IMPACT

**No edit touches line 31.** Verified programmatically: `lines[30]` is byte-identical before and after all five edits, and the abstract still measures **294 words**. Net abstract word change: **0**. Gate #101's tie to the response letter's claimed count is unaffected, and the long-abstract variant needs no mirroring for this cluster (none of my five OLD spans is in the abstract).

Body word count rises by roughly 250 words: ~215 in `app:params` (Edit 1), ~40 in §VII.E (Edit 2), ~55 in the caption (Edit 3), ~75 in the note (Edit 5), minus ~30 removed.

---

## DECISION_NEEDED

1. **C-65's three quoting sites are still bare.** The inventory's trigger is "Absent C-07", and C-07 is Wave 3 — so adding Edit 4's row does not by itself retire C-65. Someone must own the abstract (`:31`), the T1 marginal cell, and §V.E, and the abstract clause costs words against the 294 gate #101 pins. Eugene's call whether the conditioning clause goes in all three, in T1 and §V.E only, or waits for C-07.
2. **`3.9\%` vs `3.86\%` for the same object.** §V.B (`.tex:269`, outside my region) still reads "sample WAC 3.9\%" and "3.9\% is the unweighted mean of borrower note rates". Both are correct roundings of 3.8649, but the paper will now carry two. Either harmonize §V.B to `3.86\%` (and its "sample WAC" phrasing to "the draw's mean note rate"), or push my three sites back to `3.9\%` and lose the precision the table note wants. I recommend harmonizing §V.B, which also fixes its "sample" ambiguity — but it is a sibling's region.
3. **Whether to print A-15's window-open balance shares (27.05% / 42.31%).** They are the weighting the aggregation actually applies and would make the vintage row complete; they exist in no frozen artifact, so printing them means either a parquet read or a small derivation artifact. Edit 1 currently states the object and the direction without them.
4. **`\newline` in the two new table cells.** First use in the file. Keep, or fall back to `; ` and let the `p{4.7cm}` column wrap where it likes.
5. **Panel labelling churn.** I kept the row names `Agency` / `Vintage` / `Coupon` unchanged and did the population labelling in the panel header, caption and note. The stricter reading of C-64 ("each row labelled") would rename them `Vintage, universe` etc.; that costs three more literals of churn inside a gate-#38 row and I judged it unnecessary once the indent convention is stated three times. Overrule if you want the row names explicit.
