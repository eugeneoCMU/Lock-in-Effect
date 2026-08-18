# R32 Task 3 — draft edit set: disclose the headline floor read's true support

TARGET FILE (all edits): `paper/v18/revised_paper_v18.tex`
MEASURED AGAINST: md5 `6eec4aa4b9d9e4c148e5cf22395721e7`, 482,665 bytes.

**CONCURRENCY WARNING — READ FIRST.** The file changed underneath me during this
session: at my first read it was 480,876 bytes; it is now 482,665. The diff
(`git diff -U0`) is a single 6-line insertion at line 619 — a `tablenotes`
block newly added to `tab:danish` by another R32 hand. None of my ten OLD
anchors sit near it, and all ten still count exactly 1 in the current file, but
every count in `## CENSUS` is measured against the md5 above and must be
re-measured if the file has moved again.

**ONE PREMISE IN THE BRIEF IS FALSE — see Edit 3.** `tab:oosfloor` has no
`tablenotes` environment *by deliberate design*, not by defect: round 31's
render repair (`tools/render_fix_r31.py`, CLASS_B) lifted the notes out of five
unbreakable floats — `tab:bases`, `tab:estimators`, `tab:danish`, `tab:ladder`,
`tab:oosfloor` — *because the tablenotes pushed the float over a page*, and the
transformation was baked into the canonical `.tex`. The note is not missing and
does print: it is the `\noindent{\footnotesize \emph{Notes to
Table~\ref{tab:oosfloor}.} a Temporal holdout. ...}` paragraph immediately after
the float, and its `a` marker pairs with the `\tnote{a}` in the row exactly as
`tab:danish`'s `a`--`d` markers pair with its own post-float paragraph. The
caption's promise is kept. I therefore draft Edit 3 as an *extension of that
paragraph* (Edit 3, recommended) and supply the in-float `tablenotes` form the
brief asked for as **Edit 3-ALT**, which reverses the round-31 CLASS_B repair
and risks the overfull float it was written to remove. Pick one, not both.

---

## Edit 1 — narrow the caption to what the headline rows actually measure (T3-caption)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
measured \emph{outside} the June 2022--November 2025 evaluation window (2017--2019 performance), except the final row, whose floor is calibrated on the window's own first nineteen months. Every row, that one included, reports its floor's \emph{full-window} marginal on a common basis; the held-out-months evaluation is given in the note.
NEW:
measured \emph{outside} the June 2022--November 2025 evaluation window, except the early-window calibration row, whose floor is calibrated on the window's own first nineteen months. The pooled and 2019-leg rows read 2017--2019 performance; the three 2018-leg rows that set the headline read 2018 reporting months on 2017-vintage cohorts, and every cohort-month they contain is aged twelve to twenty-four months, so no mature cell enters them. Every re-run row, the early-window one included, reports its floor's \emph{full-window} marginal on a common basis, and the held-out-months evaluation is given in the note; the age-standardized and Fannie rows are grid reads rather than paired re-runs, so they carry the central elasticity alone.
RATIONALE: `(2017--2019 performance)` described all off-window rows, but the
three rows that set the headline are one origination vintage read over 2018
reporting months on cohort-months aged 12--24 only. The row-identity reference
moves from "the final row" to "the early-window calibration row" because Edit 2
inserts rows above it, and the last two sentences scope the common-basis and
full-window claims off the two grid-read rows Edit 2 adds.
LITERALS_INTRODUCED: none. `2017-vintage` and `twelve to twenty-four months` are
words, sourced from `floor_inference_correction_v2_results.json`
`reads.R1_2018_gap<=+0.0000_age>=12 / R2_... / R3_....cluster_strata` (31/31/25
strata, every one prefixed `2017_`), from
`oos_identification_results.json` `instrument1_oow_floor.legs.2018_rising_rate.seasoning`
(`age[12,24)` = 155 cohort-months; `age[24,36)`, `age[36,60)`, `age[60,10000)`
all `n_cohort_months: 0`), and from
`floor_uncertainty_results.json` `part_b_age_standardization.off_window_selection`
= "2018 leg (201801..201812), gap<=-0.0025" for the reporting months.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: `the held-out-months evaluation is given in the note`
(not gate-pinned, but the caption promise this task is about) — preserved
byte-identically. No gate or test string is inside this OLD (`grep -F` over
`tools/liveness_gates.py` and `tests/` returns 0 for `2017--2019 performance`,
`the final row`, `Every row, that one included`).

---

## Edit 2 — promote the two corrections into `tab:oosfloor` as rows (T3-rows)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
2019 leg, gap $\leq 0$ & refi-contaminated & 6.91\% & $+0.7$ & $+0.7$ & $+0.8$ \\
\midrule
In-window (production)
NEW:
2019 leg, gap $\leq 0$ & refi-contaminated & 6.91\% & $+0.7$ & $+0.7$ & $+0.8$ \\
\midrule
2018 leg, age-standardized & indicative bound\tnote{b} & 5.51\% & --- & $+3.8$ & --- \\
Fannie Mae, pooled off-window & cross-agency read\tnote{c} & 5.52\% & --- & $+2.3$ to $+4.3$ & --- \\
\midrule
In-window (production)
RATIONALE: the two corrections that put the floor above the clean band's top
were prose-only; as rows they sit beside the reads they correct. Both are grid
reads, not paired re-runs, so the two flanking elasticity columns are dashed and
the status column plus notes `b`/`c` carry what each one is. The block sits
above the in-window block so that Edit 1's "early-window calibration row" is
still the last row.
LITERALS_INTRODUCED:
- `5.51\%` — `floor_uncertainty_results.json`
  `part_b_age_standardization.adjusted_floor_pct` = 5.507748455937158.
- `$+3.8$` — same file, `part_b_age_standardization.adjusted_marginal_at_6.5.marginal_pp`
  = 3.7731962212253927 (and already the paper's own figure at two other sites).
- `5.52\%` — `fannie_floor_read_results.json` `comparison.fannie_headline_cpr_pct`
  = 5.522.
- `$+2.3$ to $+4.3$` — the two committed grid rows either side of 5.52%, i.e.
  this table's own `2018 leg, gap $\leq 0$` cell at $\delta = 6.5\%$ ($+4.3$;
  `oos_identification_results.json` `instrument1_marginal_table`, floor 5.334,
  band "6.5") and its `Pooled 2017--2019` cell at the box's adjacent 6.0\% row
  ($+2.3$). The paper already states this bracket in prose as
  "between the 5.334\% row's $+4.27$ points and the 6.0\% row's $+2.28$".
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: `6.91\%` is asserted present by `liveness_gates.py:1734`
(`has_5161`) — preserved byte-identically; its count is unchanged at 5.
`tab:oosfloor` itself is pinned by zero gates and zero tests (independently
re-checked: `grep -F oosfloor tools/liveness_gates.py tests/` → 0 hits).

---

## Edit 3 — notes b and c for the new rows, in the paper's post-float note convention (T3-notes) **[RECOMMENDED]**
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
the two quantities are different objects and should not be read off one another.\par}
NEW:
the two quantities are different objects and should not be read off one another. \quad b The 2018 leg's age-bucket reads reweighted to the in-window deep-discount population's age mix, its empty mature buckets imputed from the in-window age gradient: 84.0\% of the weight is imputed, so this is an indicative bound and not a measurement (run \texttt{floor\_uncertainty}). \quad c The committed off-window selection rule applied to the Fannie Mae panel at gap $\leq -0.0025$ over the pooled 2017--2019 period, not to the 2018 leg: the like-for-like Freddie read of that cell is 5.185\%, so the agency difference is 0.337 points of CPR and the rest of the distance from the 2018 leg's 4.991\% is period (run \texttt{fannie\_floor\_read}). Both correction rows are read off the committed floor-to-marginal grid rather than re-run.\par}
RATIONALE: gives the two new rows their notes in the exact form
`render_fix_r31.notes_paragraph` generates (`\quad ` between lettered items —
`tab:danish` and `tab:bases` are the precedent, 21 `\quad` separators in the
file), so the notes print with the float's markers and nothing re-enters the
unbreakable float. Note `c` names the like-for-like Freddie parity so the reader
can see the agency effect is 0.337 points and the rest of the distance from the
clean read is period.
LITERALS_INTRODUCED:
- `84.0\%` (of imputed weight) — `floor_uncertainty_results.json`
  `part_b_age_standardization.imputed_weight_share` = 0.8398743947117693.
- `5.185\%` — `fannie_floor_read_results.json` `comparison.freddie_headline_cpr_pct`.
- `0.337` — same file, `comparison.difference_pp`.
- `4.991\%` — `oos_identification_results.json`
  `instrument1_oow_floor.defensible_clean_floor.clean_mid_pct` = 4.991 (already
  14 times in the file).
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: this OLD is the tail of the `a` note, which contains the
gate-pinned `$+\$45.1$ billion` (`liveness_gates.py:1769`) and `$+\$44.8$
billion` — both untouched and outside the OLD. `84.0\% of weight imputed`
(gate #73, `liveness_gates.py:4622`) lives elsewhere and is not disturbed; my
new wording is `84.0\% of the weight is imputed`, a different string, so the
pinned one still counts 1.

---

## Edit 3-ALT — the in-float `tablenotes` form the brief asked for (T3-notes-alt) **[NOT RECOMMENDED — reverses round-31 CLASS_B]**
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
\bottomrule
\end{tabular}
\end{threeparttable}
\end{table}

\noindent{\footnotesize \emph{Notes to Table~\ref{tab:oosfloor}.} a Temporal holdout. The 3.97\% floor is calibrated on deeply out-of-the-money turnover in the window's first nineteen months (June 2022--December 2023). Summed over the strictly held-out remaining twenty-three months (January 2024--November 2025), which enter that calibration nowhere, the central-minus-null marginal is $+\$45.1$ billion at the central elasticity, against $+\$44.8$ billion at the production floor over the identical months. The table row above reports the same floor's full-window marginal, so that every row is comparable; the two quantities are different objects and should not be read off one another.\par}

NEW:
\bottomrule
\end{tabular}
\begin{tablenotes}[flushleft]\footnotesize
\item[a] Temporal holdout. The 3.97\% floor is calibrated on deeply out-of-the-money turnover in the window's first nineteen months (June 2022--December 2023). Summed over the strictly held-out remaining twenty-three months (January 2024--November 2025), which enter that calibration nowhere, the central-minus-null marginal is $+\$45.1$ billion at the central elasticity, against $+\$44.8$ billion at the production floor over the identical months. The table row above reports the same floor's full-window marginal, so that every row is comparable; the two quantities are different objects and should not be read off one another.
\item[b] The 2018 leg's age-bucket reads reweighted to the in-window deep-discount population's age mix, its empty mature buckets imputed from the in-window age gradient: 84.0\% of the weight is imputed, so this is an indicative bound and not a measurement (run \texttt{floor\_uncertainty}).
\item[c] The committed off-window selection rule applied to the Fannie Mae panel at gap $\leq -0.0025$ over the pooled 2017--2019 period, not to the 2018 leg: the like-for-like Freddie read of that cell is 5.185\%, so the agency difference is 0.337 points of CPR and the rest of the distance from the 2018 leg's 4.991\% is period (run \texttt{fannie\_floor\_read}). Both correction rows are read off the committed floor-to-marginal grid rather than re-run.
\end{tablenotes}
\end{threeparttable}
\end{table}

RATIONALE: the literal thing the brief asked for — all three notes inside the
threeparttable, the post-float paragraph deleted, the `a` text carried across
byte-identically. Mutually exclusive with Edit 3. Do not apply it without a
build: round 31 moved these notes out because they made the float unbreakable
and over-tall, and `tab:oosfloor` will now carry two more notes than it did
then.
LITERALS_INTRODUCED: as Edit 3.
LITERALS_REMOVED: none — every literal in the `a` note is carried over verbatim.
PINNED_SPANS_CROSSED: `$+\$45.1$ billion` (gate, `liveness_gates.py:1769`) and
`$+\$44.8$ billion` are inside this OLD and are reproduced byte-identically in
the NEW. Whole-file counts of both are unchanged (4 and 2).

---

## Edit 4 — retire the "two independent lines" argument and state the read's support (T3-support-A, primary site)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
That is above the clean band's 5.334\% top, and it sits 0.01 points from the age-standardized read of 5.51\% that the same table already flags. Two independent lines---one an imputation-heavy age standardization on Freddie, the other a direct read on a second agency's book---therefore point to the same place, and both point above the band.
NEW:
That is above the clean band's 5.334\% top, but it is not a second read of the clean leg: the committed rule applied off window covers the pooled 2017--2019 period, whose Freddie counterpart is the 5.19\% just quoted rather than the 2018 leg's 4.991\%, so the agency difference is 0.337 points of CPR (5.522\% against 5.185\%) and the rest of the distance from the clean read is period. The age-standardized read of 5.51\% that the same table already flags lands 0.01 points away, but it perturbs something else again---an age correction to the 2018 leg itself, on 84.0\% imputed weight---so the near-coincidence of the two is not a second measurement of either. What they share is direction: both sit above the clean band's top, and both say the clean read understates the mature book's turnover. That direction is what the clean leg cannot test on its own. The 2018 leg holds no out-of-the-money cohort-month past the twenty-four-month age cut, so its mature-seasoning test is not computable rather than passed (Appendix~\ref{app:floormech}), and the one age contrast it does support is confounded by the PSA ramp. Where a mature contrast is measurable at all---two agencies, two rate regimes, three depth cuts---it runs one way in twelve cells of twelve, the age-$\geq$-24 read the higher one in each: in window, where the rate configuration suppresses refinancing as it did on the 2018 leg, by 0.08 and 0.19 points of CPR on Freddie and Fannie; on the refi-contaminated pooled 2017--2019 period, by 3.74 and 4.61 points, which bounds the correction from above rather than measuring it (run \texttt{fannie\_floor\_read}). A floor read taken entirely on cohort-months aged twelve to twenty-four therefore sits below the mature book's baseline turnover, and the marginal it implies sits above the one a mature book would give: the error is signed against the headline, and its size is not priced anywhere in this paper.
RATIONALE: the retired claim presented two different perturbations landing 0.01
apart as mutual corroboration; the Fannie figure is the same *selection rule* on
a different *period*, whose like-for-like Freddie counterpart is 5.185%, so most
of its distance from 4.991% is pooling, and the age-standardized figure carries
84% imputed weight. What survives is the shared direction, and this is the site
that supplies the evidence for it, because the cross-agency mature cells come
from the run cited two sentences earlier. The PSA-confounded 1.558-point ramp
inside the 2018 leg is explicitly excluded as evidence, per the artifact's
`ramp_rise_is_psa_confounded: true`.
LITERALS_INTRODUCED:
- `0.337`, `5.522\%`, `5.185\%` — `fannie_floor_read_results.json`
  `comparison.difference_pp / fannie_headline_cpr_pct / freddie_headline_cpr_pct`.
- `84.0\%` — `floor_uncertainty_results.json`
  `part_b_age_standardization.imputed_weight_share` = 0.8398743947117693.
- `0.08` and `0.19` — same file's Fannie counterpart
  `fannie_floor_read_results.json`, `books.freddie.in_window_2023_2024`
  `gap<=-0.0025_age>=12` 3.922 → `..._age>=24` 4.002 (+0.080) and
  `books.fannie....` 3.962 → 4.151 (+0.189).
- `3.74` and `4.61` — same file, `books.freddie.out_of_window_2017_2019`
  `gap<=-0.0025_age>=12` 5.185 → `..._age>=24` 8.920 (+3.735) and
  `books.fannie....` 5.522 → 10.136 (+4.614).
- "twelve cells of twelve" — the 2 agencies x 2 regimes
  (`out_of_window_2017_2019`, `in_window_2023_2024`) x 3 gap cuts of the same
  artifact; the `age>=24` read exceeds the `age>=12` read in all twelve
  (Freddie oow 6.065→10.995, 5.185→8.920, 5.073→8.920; Freddie in-window
  3.922→4.002, 3.922→4.002, 3.921→4.001; Fannie oow 6.403→11.895, 5.522→10.136,
  5.373→10.136; Fannie in-window 3.963→4.151, 3.962→4.151, 3.961→4.149).
- "not computable rather than passed" — `oos_identification_results.json`
  `instrument1_oow_floor.legs.2018_rising_rate.contamination`:
  `mature_test_computable: false`, `mature_rise_pp_24_vs_12: null`, verdict
  `CLEAN_BY_CONSTRUCTION_MATURE_TEST_NOT_COMPUTABLE`.
LITERALS_REMOVED: `Two independent lines` 1 → 0; `point to the same place` 1 → 0.
No numeric literal drops (`5.334\%` 5 → 5, `5.51\%` and `0.01 points` retained).
PINNED_SPANS_CROSSED: `above the clean band` (gate #86,
`liveness_gates.py:4366`) occurs inside this OLD as `above the clean band's
5.334\% top`; NEW keeps that clause byte-identically and adds a second
occurrence, so the whole-file count rises 4 → 5. `Freddie's 5.19\%` is outside
the OLD and untouched. Nothing else in this OLD appears in
`tools/liveness_gates.py` or `tests/`.

---

## Edit 5 — the assembly paragraph's Fannie rung says what the read is (T3-fannie-1)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
and the independent Fannie Mae read of the same off-window cell, 5.52\%, brackets the marginal below the $+4.3$ edge of the clean band (above)
NEW:
and the Fannie Mae read of the same selection rule on the pooled off-window period, 5.52\%, brackets the marginal below the $+4.3$ edge of the clean band (above)
RATIONALE: "the same off-window cell" is the description the coordinator
verified as wrong — same selection rule, different period. "independent" goes
with it, because independence from the 2018 leg is what the phrase was claiming
and what is not true of the period.
LITERALS_INTRODUCED: none.
LITERALS_REMOVED: none (`5.52\%` and `$+4.3$` both retained in place).
PINNED_SPANS_CROSSED: **`ASSEMBLY_SPANS["ladder_fannie"]` =
`5.52\%, brackets the marginal below the $+4.3$ edge` is inside this OLD and is
preserved BYTE-IDENTICALLY. No re-pin is needed.** Verified by rebuilding the
paragraph in memory and re-running the shipped rule's own predicate: the span is
present, exactly once, and `assembly_check`'s paragraph count is still 1. The
sibling test `tests/test_assembled_corrections_gate.py`'s
`HANDOFF_COMMITMENTS` requires `5.52\%` inside the assembly paragraph — it is.

---

## Edit 6 — the same repair in `tab:uncertainty`'s floor-correction cell (T3-fannie-2)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
independent Fannie Mae read of the same off-window cell 5.52\% (run \texttt{fannie\_floor\_read}), above the clean band and bracketing the marginal below $+4.3$
NEW:
Fannie Mae read of the same selection rule on the pooled off-window period 5.52\% (run \texttt{fannie\_floor\_read}), above the clean band and bracketing the marginal below $+4.3$, its like-for-like Freddie counterpart 5.185\% rather than the 2018 leg's 4.991\%, so most of that distance is period and not agency
RATIONALE: the second of the two wrong descriptions, in the table a reader
consults for the sensitivity catalogue; the parity read is named so the cell
stands on its own.
LITERALS_INTRODUCED: `5.185\%` (`fannie_floor_read_results.json`
`comparison.freddie_headline_cpr_pct`); `4.991\%` (already 14 times in file;
`oos_identification_results.json` `...defensible_clean_floor.clean_mid_pct`).
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: `above the clean band` (gate #86) and
`\texttt{fannie\_floor\_read}` (gate #86) are both inside this OLD and both
preserved byte-identically.

---

## Edit 7 — the support statement where the band is priced into the headline (T3-support-B)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
the defensible off-window floor places the contribution in the box's interior, at roughly $+5.6$ points, not at $+2.1$ to $+2.4$.
NEW:
the defensible off-window floor places the contribution in the box's interior, at roughly $+5.6$ points, not at $+2.1$ to $+2.4$. Every read in that band is taken on cohort-months aged twelve to twenty-four, the only ages the 2018 leg contains, so the leg's mature-seasoning test is not computable rather than passed (Appendix~\ref{app:floormech}); where the mature contrast is measurable it runs one way in every cell (Section~\ref{sec:identification}), which puts the band below the mature book's baseline turnover and the marginal it implies above what that book would give.
RATIONALE: this is the paragraph that converts the band into the headline
marginal, so a reader who meets the band as an input meets its support in the
same breath. Compact, and points at Edit 4 for the figures rather than
repeating them.
LITERALS_INTRODUCED: none.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none (`grep -F` of this OLD over `tools/liveness_gates.py`
and `tests/` returns 0). The existing paragraph text is untouched; the sentence
is appended.

---

## Edit 8 — the introduction's floor inventory (T3-support-C)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
4.70--5.33\% on the off-window 2018 leg, 5.51\% under an imputation-heavy age standardization (84\% imputed weight, an indicative bound derived from the same 2018 leg), and 5.52\% on an independent out-of-agency Fannie Mae read; the last two lines sit above the clean band, which is why the band's lower edge is the soft one
NEW:
4.70--5.33\% on the off-window 2018 leg (all of it on cohort-months aged twelve to twenty-four, so that leg's mature-seasoning test is not computable rather than passed), 5.51\% under an imputation-heavy age standardization (84\% imputed weight, an indicative bound derived from the same 2018 leg), and 5.52\% on an out-of-agency Fannie Mae read of the pooled off-window period; the last two lines sit above the clean band, as does every mature-versus-young turnover contrast the data make measurable, which is why the band's lower edge is the soft one
RATIONALE: the introduction is where most readers meet the band, and this
sentence is the paper's inventory of what the floor has been measured at. The
existing soft-lower-edge statement is kept verbatim and strengthened rather than
replaced; "independent" is dropped from the Fannie clause and the period named,
matching Edits 5 and 6.
LITERALS_INTRODUCED: none.
LITERALS_REMOVED: none — `4.70--5.33\%` (gates `liveness_gates.py:1734` and
`:1771`), `5.51\%`, `84\%` and `5.52\%` all retained; `4.70--5.33\%` count
stays 3.
PINNED_SPANS_CROSSED: `4.70--5.33\%` is inside this OLD and preserved
byte-identically (it is gate #58's `has_5161` and gate #57's
`oos_lits["clean_band"]`). `above the clean band` (gate #86) is inside and
preserved.

---

## Edit 9 — connect the appendix's existing not-computable disclosure to the direction evidence (T3-support-D)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
and its one computable age contrast (3.78\% to 5.33\% across the twelve-month cut) is confounded by the PSA ramp, on which young loans genuinely turn over less.
NEW:
and its one computable age contrast (3.78\% to 5.33\% across the twelve-month cut) is confounded by the PSA ramp, on which young loans genuinely turn over less, so it is not evidence about the contrast the leg is missing. The out-of-agency read is: in every cell where a mature contrast exists at all, mature turnover is the higher one, and Section~\ref{sec:identification} reports by how much.
RATIONALE: `app:floormech` already states the empty-mature fact and the
PSA confound (the disclosure I was told to find and not duplicate) but stops
before saying what direction the missing contrast has. This adds only the link;
the figures stay at their single home in Edit 4. The 1.558-point ramp is
explicitly denied evidential status here, matching
`contamination.ramp_rise_is_psa_confounded: true`.
LITERALS_INTRODUCED: none.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none (`3.78\%` and `5.33\%` both preserved byte-identically
inside the retained clause; counts unchanged at 1 and 7).

---

## Edit 10 — `tab:assembly`'s Fannie row status (T3-fannie-3) **[OPTIONAL]**
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
Fannie floor read (5.52\%) & below $+4.3$ & below & bracketing, second agency \\
NEW:
Fannie floor read (5.52\%) & below $+4.3$ & below & bracketing; second agency, pooled period \\
RATIONALE: the third site where the Fannie read is described as if it were the
clean leg's own cell. Two words; drop it if the coordinator wants the edit set
confined to the two sites named in the brief.
LITERALS_INTRODUCED: none.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: `ASSEMBLY_TABLE_SPANS` pins `table_label`,
`table_anchor`, `table_row_composed` (`measured composed lower member (run
\texttt{b5\_joint\_cell})`) and `table_row_fonseca` (`counterweight,
conservative-band evidence`). This row is none of them; all four are untouched
and still present.

---

## CENSUS

Fixed-string counts over `paper/v18/revised_paper_v18.tex`, md5
`6eec4aa4b9d9e4c148e5cf22395721e7`. BEFORE = measured on the current file;
AFTER = measured on the file with Edits 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 applied
in that order (Edit 3, the recommended post-float form; Edit 3-ALT column
where it differs). Every count below was produced by `str.count` on the
in-memory result, not estimated.

| fixed string | BEFORE | AFTER | AFTER if 3-ALT |
|---|---|---|---|
| `2017--2019 performance` | 1 | 1 | 1 |
| `the final row` | 2 | 1 | 1 |
| `Every row, that one included` | 1 | 0 | 0 |
| `the held-out-months evaluation is given in the note` | 1 | 1 | 1 |
| `the same off-window cell` | 2 | 0 | 0 |
| `Two independent lines` | 1 | 0 | 0 |
| `point to the same place` | 1 | 0 | 0 |
| `independent out-of-agency Fannie Mae read` | 1 | 0 | 0 |
| `bracketing, second agency` | 1 | 0 | 0 |
| `above the clean band` | 4 | 5 | 5 |
| `clean band` | 7 | 8 | 8 |
| `4.70--5.33\%` | 3 | 3 | 3 |
| `6.91\%` | 5 | 5 | 5 |
| `5.52\%` | 7 | 8 | 8 |
| `5.51\%` | 6 | 7 | 7 |
| `5.185\%` | 0 | 3 | 3 |
| `5.522\%` | 0 | 1 | 1 |
| `0.337` | 0 | 2 | 2 |
| `Freddie's 5.19\%` | 1 | 1 | 1 |
| `5.19` | 1 | 2 | 2 |
| `84.0\%` | 3 | 5 | 5 |
| `84.0\% of weight imputed` | 1 | 1 | 1 |
| `84\%` | 5 | 5 | 5 |
| `4.991\%` | 14 | 17 | 17 |
| `5.334\%` | 5 | 5 | 5 |
| `5.33\%` | 7 | 7 | 7 |
| `3.78\%` | 1 | 1 | 1 |
| `3.97\%` | 4 | 4 | 4 |
| `0.08` | 1 | 2 | 2 |
| `0.19` | 19 | 20 | 20 |
| `3.74` | 0 | 1 | 1 |
| `4.61` | 0 | 1 | 1 |
| `$+3.8$` | 4 | 5 | 5 |
| `$+2.3$ to $+4.3$` | 0 | 1 | 1 |
| `$+2.3$` | 6 | 7 | 7 |
| `$+4.3$` | 17 | 18 | 18 |
| `$+3.0$ to $+8.0$` | 5 | 5 | 5 |
| `$+2.9$ to $+8.7$` | 8 | 8 | 8 |
| `$+3.5$ to $+13.1$` | 7 | 7 | 7 |
| `$+3.9$ to $+13.1$` | 0 | 0 | 0 |
| `open below $+4.3$` | 3 | 3 | 3 |
| `$+\$45.1$ billion` | 4 | 4 | 4 |
| `$+\$44.8$ billion` | 2 | 2 | 2 |
| `$+\$42.6$ billion` | present | present | present |
| `$+4.3$ to $+6.8$` | present | present | present |
| `0.01 points` | 1 | 1 | 1 |
| `twelve to twenty-four` | 1 | 5 | 5 |
| `twenty-four-month` | 1 | 2 | 2 |
| `2017-vintage` | 0 | 1 | 1 |
| `not computable` | 3 | 6 | 6 |
| `mature` | 2 | 16 | 16 |
| `points of CPR` | 3 | 6 | 6 |
| `selection rule` | 2 | 5 | 5 |
| `pooled off-window` | 0 | 4 | 4 |
| `grid read` | 0 | 1 | 1 |
| `indicative bound` | 3 | 5 | 5 |
| `age-$\geq$-24` | 1 | 2 | 2 |
| `age-$\geq$-12` | 1 | 1 | 1 |
| `\texttt{fannie\_floor\_read}` | 2 | 4 | 4 |
| `\texttt{floor\_uncertainty}` | 4 | 5 | 5 |
| `\tnote{` | 9 | 11 | 11 |
| `\begin{tablenotes}` | 13 | 13 | **14** |
| `\end{tablenotes}` | 13 | 13 | **14** |
| `\begin{threeparttable}` | 20 | 20 | 20 |
| `Notes to Table` | 7 | 7 | **6** |
| `Table~\ref{tab:oosfloor}` | 10 | 10 | **9** |
| `three independent legs` (ZERO_COUNT) | 0 | 0 | 0 |
| file length (chars) | 482,665 | 486,688 | 486,685 |

Pinned-phrase re-checks run against the assembled result (all pass):
`ASSEMBLY_SPANS["ladder_fannie"]` present exactly once and inside the single
`A seventh qualification` paragraph; `ASSEMBLY_SPANS["ladder_agestd"]` present
in the same paragraph; `assembly_check`'s paragraph count = 1;
`ASSEMBLY_TABLE_SPANS` all four present; gate #86's three tex literals
(`fannie\_floor\_read`, `5.52\%`, `above the clean band`) present; gate #73's
four (`$+3.0$ to $+8.0$` >= 2, `$+2.9$ to $+8.7$` >= 4, `open below $+4.3$`,
`84.0\% of weight imputed`) satisfied; gate #57's six `oos_lits`
(`$+\$42.6$ billion`, `$+5.6$`, `$+4.3$ to $+6.8$`, `$+\$45.1$ billion`,
`in-sample calibration point`, `4.70--5.33\%`) present; gate #71's
`$+3.5$ to $+13.1$` >= 3 and `$+3.9$ to $+13.1$` == 0 satisfied.

---

## UNVERIFIED

1. **The `tab:oosfloor` "missing tablenotes" defect is not a defect.** Round 31's
   `tools/render_fix_r31.py` lists `tab:oosfloor` in `CLASS_B` — "tablenotes
   push the float over" — and the repair was baked into the canonical `.tex`
   (`PLAN_review2_fixes_2026-07-28.md:170` records it, and all five CLASS_B
   tables plus both CLASS_A tables carry their notes as post-float paragraphs
   today; the `\quad a ... \quad b` separator form is exactly what
   `notes_paragraph()` emits). The `\tnote{a}` marker is therefore not orphaned:
   it pairs with the `a` item in the paragraph directly below the float, the
   same way `tab:danish`'s `a`--`d` do. I have drafted both forms and recommend
   the post-float one. WHAT WOULD SETTLE IT: a build of the ALT variant showing
   no overfull float and no page-count regression on the `tab:oosfloor` page —
   which I cannot run.
2. **A concurrent editor is touching this file.** It gained 1,789 bytes during
   my session (a new `tablenotes` block inserted into `tab:danish` at line 619,
   which now has notes in *both* places). All ten of my OLD anchors still count
   exactly 1, but every count above is tied to md5
   `6eec4aa4b9d9e4c148e5cf22395721e7`. WHAT WOULD SETTLE IT: re-measure the
   census before applying. Note also that whoever added the `tab:danish`
   tablenotes has re-floated a CLASS_B table, which bears on item 1.
3. **`\tnote{b}` / `\tnote{c}` in a float whose notes live outside it.** This is
   the convention `tab:danish` already uses (four such markers), so I believe it
   typesets, but I cannot compile to confirm the new markers render as
   superscript letters and not as a `threeparttable` error.
4. **Column overflow of the two new rows.** `tab:oosfloor`'s spec is `{llcccc}`
   at `\footnotesize`; my new anchor labels ("Fannie Mae, pooled off-window") and
   the widest new cell (`$+2.3$ to $+4.3$`) are comparable in width to existing
   entries, but `tab:oosfloor` is not a `p{}` table and I cannot measure the
   rendered width. WHAT WOULD SETTLE IT: one build. If it runs past the margin,
   `tab:oosfloor` is a CLASS_C candidate for the same treatment `tab:assembly`
   got.
5. **"twelve cells of twelve" excludes two further cells that also run the same
   way.** `fannie_floor_read_results.json` also carries
   `in_window_deep_OTM_validation` (`gap<=-0.02`) for both agencies, where
   mature turnover is again higher (Freddie 3.840 → 3.909; Fannie 3.864 →
   4.029). I kept the count at twelve to match the grid the sentence describes
   (2 agencies x 2 regimes x 3 depth cuts). If the coordinator prefers
   "fourteen of fourteen", both extra cells are verified above.
6. **No committed run prices the size of the disclosed error.** The sentence
   says so explicitly ("its size is not priced anywhere in this paper"), which
   is a claim about the repository, not about an artifact. I checked the obvious
   candidates — `oos_identification`, `floor_uncertainty`,
   `floor_inference_correction_v2`, `fannie_floor_read` — and none re-runs the
   paired legs at a mature-corrected floor: the age-standardized 5.51% read is
   the closest thing and it is a grid read on 84% imputed weight. WHAT WOULD
   SETTLE IT: a sweep of `hazard/data/*.json` for a run that re-anchors the
   floor on a mature-only cell, which I did not exhaustively do.
