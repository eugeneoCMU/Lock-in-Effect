# DRAFT — WP-E item 3: §V gains the offstage load-bearing exhibits

**Status: DRAFT ONLY.** Nothing in this file has been applied. No `.tex`, gate, test, or letter line was
modified while producing it; the edits below were applied to an *in-memory copy* of
`paper/v18/revised_paper_v18.tex` only, to verify span survival and literal counts (§4). No runs, no pytest.

**Scope (PLAN_review2_fixes_2026-07-28 WP-E item 3):**
(a) `tab:oosfloor`, `tab:floorband`, `tab:lowband` move from App.~`app:floormech` into §V near their first
`\ref`; `tab:params` moves from App.~`app:params` into §V.B near its first `\ref`;
(b) the inference ladder becomes a small table (new `tab:ladder`) replacing the ladder prose;
(c) `tab:headline`'s marginal cell splits into *operative interval* + *sensitivity catalogue*.

Every `\label` is unchanged, so no `\ref` breaks. Every committed number keeps its value; no number is
added to the manuscript that the manuscript did not already print (see §2, ambiguity A4).

---

## 1. Pinned-span inventory — every gate span sourced from the text these edits touch

Method: `tools/liveness_gates.py` was parsed with `ast` and **every** string constant in it (all `*_SPANS`
dicts, `ZERO_COUNT`, `EXACTLY_ONE`, `LETTER_CURRENT_LITERALS`, `SUPERSEDED_CONTEXTUAL`, the inline
`tex.count(...)`/`in tex` literals) was intersected against the four float blocks, tex 76 (the
`tab:headline` marginal row), tex 357 (the `tab:uncertainty` headline row) and tex 364 (the ladder note).
Result below. "Survives" = the literal is byte-identical somewhere in the post-edit file.

### 1a. Spans on tex 364 (the ladder note — the only prose this draft rewrites)

| span | gate | kind | where it survives |
|---|---|---|---|
| `makes the convolved line a lower bound as well` | #105 `CONVOLVED_LINE_SPANS["lower_bound_inheritance"]` | presence, count 1 | **E5 NOTE_NEW**, same sentence, verbatim |
| `$+2.9$ to $+8.7$` | #73 count `>= 4` (file count 8) | count | **E4 ladder table**, "Wild-$t$, Webb" row, verbatim (count stays 8) |
| `binding layer` | #73 `"binding layer" in tex` | presence | E5 NOTE_NEW + E4 Status column (count 8 → 10) |
| `floor\_inference\_correction` | #73 `in tex` | presence | E4 caption + E5 NOTE_NEW (count 6 → 8) |

No other gate literal occurs on tex 364. In particular the ladder's own numbers
(`$+2.8$ to $+8.7$`, `$+2.4$ to $+9.2$`, `$+2.3$ to $+9.6$`, `$+2.3$ to $+9.1$`, `9{,}999`, `Bell--McCaffrey`,
`Herfindahl`, `$t(30)$`, `0.33`, `5.9`, `25.8`) are **committed but ungated** — which is exactly why they are
re-printed verbatim in E4 rather than paraphrased.

### 1b. Spans on tex 76 (`tab:headline` marginal row — split by E6)

| literal | gate | threshold | after E6 |
|---|---|---|---|
| `$+2.9$ to $+8.7$` | #73 | `>= 4` | 8 (unchanged; stays in cell 1, untouched) |
| `$[+2.9, +8.7]$` | (letter/prose form) | — | 3 (unchanged; stays in the operative-interval cell) |
| `$+3.5$ to $+13.1$` | #69 (form-conditional headline); letter literal | `>= 3` | 7 (unchanged; moves into note [a] verbatim) |
| `$+4.3$ to $+6.8$` | #57 (`oos_lits["range_pp"]`) | presence | 7 (unchanged; note [a]) |
| `$+11.2$`, `$-1.47$` | letter literals | presence | 9 / 7 (unchanged; note [a]) |
| `$+\$45.1$ billion` | #57 (`oos_lits["heldout"]`) | presence | 4 (unchanged; note [a]) |
| `form-conditional` | #69 `>= 3` | `>= 3` | 12 (unchanged) |
| `binding layer` | #73 | presence | retained in the operative-interval cell |

The catalogue text from `off-window floor range` through `floor-stability check $+\$45.1$ billion` is moved
**byte-identically** (E6 splices it after a colon, so not one character of it changes).

### 1c. Spans inside the four floats being relocated

| float | gate literal inside it | gate | effect of the move |
|---|---|---|---|
| `tab:lowband` | `\label{tab:lowband}` | #102 `ELASTICITY_DISCIPLINE_SPANS["curve_table"]` (whole-file) | none — whole block moves |
| `tab:lowband` | `\texttt{band\_low\_extension}` | #102 `curve_run_tag` (whole-file) | none |
| `tab:oosfloor` | `$+\$45.1$ billion`, `\texttt{oos\_identification}` | #57 (whole-file presence / `>= 1`) | none |
| `tab:floorband` | — | — | none |
| `tab:params` | — | — | none |

All four are whole-file checks; a float relocation is invisible to them.

### 1d. Spans NOT touched but adjacent (guard list for the applying agent)

- tex 312 (`A seventh qualification` …) carries **all of gate #98** (`ASSEMBLY_SPANS`, paragraph-scoped:
  `assembly_check` requires *exactly one* line starting with `A seventh qualification`) plus
  `posture_binding_layer` = "The widest layer that does have a coverage property is the floor reads' own
  sampling error, $+2.9$ to $+8.7$ points after wild-cluster correction". **E3 inserts floats *after* the
  `tab:assembly` float, never inside the paragraph line** — verified: the post-edit file still has exactly
  one such paragraph.
- tex 357 (`tab:uncertainty` headline row) carries gate #105's `pair` (`$[+2.80, +8.99]$`),
  `independence_caveat`, `comonotone_bound`. **Untouched by this draft** (E5 rewrites the *note*, not the row).
- tex 30 (abstract) carries gate #99 including the ordering assert. **Untouched** (verified byte-identical).
- `HARDCODED_XREF` bans literal `Table~N` / `Section~V.C` forms. All new prose uses `\ref` — verified 0 hits
  for all five patterns after the edits.

---

## 2. Ambiguities, and the choice taken

**A1. "§V.C" does not contain the ladder.** By the printed numbering §V.C is
`sec:pathb-fannie` (the Fannie replication) and contains no inference prose. The long ladder passage —
percentile demotion, CR2/CR3, Webb/Rademacher wild-$t$, WCR, $G^*$, Bell--McCaffrey df, leverage, $B$ — is
**tex 364, the second `\item` of `tab:uncertainty`'s `tablenotes`**, a float anchored by the §V.E paragraph at
tex 343. That is what E5 rewrites. A *second, shorter* ladder exists at **tex 592 (§VII.F)** carrying the
$G-1$ pair `$+3.0$ to $+8.6$` / `$+2.8$ to $+8.8$` from run `floor_inference_correction`; this draft leaves
tex 592 alone (see A5).

**A2. Which §V home for each float.** "Near its first `\ref`" resolves to:
`tab:params` → tex 253 (§V.B, the `eq:beta1` paragraph); `tab:floorband` → tex 277 (the `fig:band` caption,
§V.B); `tab:lowband` → tex 312 (§V.E assembly paragraph); `tab:oosfloor` → first §V `\ref` is tex 357
(`tab:uncertainty`), so it lands with `tab:lowband` immediately after the `tab:assembly` float.
*Alternative* (coordinator's call): put `tab:floorband` with the other two in §V.E so the three box exhibits
read as one block; the cost is that its only §V `\ref` (tex 277) then points forward across a subsection.

**A3. Float specifier.** The four blocks are `[H]` today (fine in an appendix, hostile in a dense §V — the
`46b294c` layout commit converted `tab:uncertainty`/`tab:estimators` to `[!t]` precisely to close orphan-page
gaps). E1 keeps `tab:params` at `[H]` (it is read against the parameter prose); E2/E3 change
`\begin{table}[H]` → `\begin{table}[!t]` for the three floor tables. This is a one-token change inside the
moved block and is flagged, not assumed: if the coordinator prefers a byte-identical move, drop the swap.
Either way §V gains ~90 typeset lines and the p.79/80 two-PDF split point must be recomputed.

**A4. CR1 is not printed, and this draft does not start printing it.** The task brief lists
"CR1/CR2/CR3 t-intervals". The manuscript has never printed a CR1 interval; the artifact has them
(`cr1_t_interval` = [+3.15, +8.35] at $t(30)$; `cr1_t_interval_df_bm` = [+2.75, +8.80] at df 6.2). Printing
them would be a **new committed literal**, which under the round-28 discipline needs its own landing rule.
Declined here; flagged for Eugene. Same reasoning declines CR3's own Bell--McCaffrey df (4.1 in the
artifact, never printed) — the ladder's df cell says "data-driven, CR3's own" and the table note says why one
df cannot serve both, which is the artifact's own `spec_deviations` finding stated in prose, not a new number.

**A5. The $G-1$ rows duplicate tex 592.** `$+3.0$ to $+8.6$` and `$+2.8$ to $+8.8$` currently occur once each
(tex 592). E4 prints them again in the ladder, so each goes 1 → 2. Neither is gated; the gain is a ladder a
referee can read in one place, the cost is a second maintenance site. *Alternative*: drop those two rows and
let the ladder start at the wild-$t$ rows. Recommend keeping them — the ladder's whole point is that the
demoted layer, the conventional-df layer and the small-sample layer are shown together.

**A6. The appendix pointer sentences become false and are repaired (E7).** `app:floormech` loses *all three*
of its tables and becomes prose-only, so tex 586 ("…and the full calibration-box tables are collected in
Appendix~…") and tex 1192 ("This appendix collects the sweep mechanics and full tables…") are corrected.
These are the only two sentences whose truth value the moves change (checked by reading every paragraph that
`\ref`s the four labels: tex 76, 253, 277, 312, 328, 357, 364, 590, 676, 734, 879, 919, 1194, 1196, 1233 —
all others speak through `\ref` and stay true).

**A7. `tab:headline` gains its first `tablenotes` block.** The `threeparttable` env is already there but
unused for notes; E6 adds `\begin{tablenotes}` and one `\tnote{a}` marker. *Alternative* considered and
rejected: a second tabular row ("… — sensitivity catalogue"), which reads as if the catalogue were another
*result* row rather than apparatus for the row above it.

**A8. Not in scope, noticed in passing:** tex 919 (App. `app:params` prose) contains a mangled sentence from
an earlier edit — "…the panel-estimated pair moves it to 101 --- in-window figures; … (run
`covariate\_ablation\_offwindow`).3\%;" — the "101" and the orphaned ".3\%" are two halves of "101.3\%"
with a clause spliced between them. Not touched here (it is not a WP-E edit) but it should be fixed before
the build.

---

## 3. The edit set

Apply in the order given. Every OLD string below is asserted `count == 1` in the pre-edit file.

### E1 — float move: `tab:params` (App. `app:params` → §V.B)

**CUT** the block at tex 921--947 (`\label{tab:params}`):

- first 60 chars: `
\begin{table}[H]
\centering
\footnotesize
\setlength{\tabco`
- last 60 chars: `tion prior \\
\bottomrule
\end{tabular}
\end{threeparttable}`
- `tex.count(block) == 1` (verified)
- length: 1304 chars, 27 lines

```tex

\begin{table}[H]
\centering
\footnotesize
\setlength{\tabcolsep}{4pt}
\begin{threeparttable}
\caption{Path B parameters.}
\label{tab:params}
\begin{tabular}{@{}llll@{}}
\toprule
Parameter & Value & Units & Provenance \\
\midrule
$\beta_1$ (central) & $0.069$ & per 100 bp gap & \eqref{eq:beta1} at $\delta = 0.065$ \citep{liebersohn2024} \\
$\delta$ band & $0.055$--$0.077$ & quarterly decline & \citet{liebersohn2024} \\
$P_q$ & $0.06$ & quarterly slot & turnover proxy (conversion auxiliary; not a measured quarterly mobility rate) \\
$\beta_F$ (FICO, z) & $-0.15$ & per SD & calibration prior; panel estimate $-0.39$ (see text) \\
$\beta_L$ (LTV, z) & $+0.10$ & per SD & calibration prior; panel estimate $+0.21$ (see text) \\
$\beta_B$ (burnout) & $-0.5$ & per unit of $B \in [0,1]$ & calibration prior \\
$\underline{h}$ (floor) & $0.0034$ & monthly SMM & 4\% annual CPR (involuntary turnover) \\
PSA speed & 100 & -- & industry seasoning convention \\
$h^{\mathrm{def}}_0$ & $3\times10^{-4}$ & monthly & calibration prior \\
$\gamma_r$ (rate stress) & $2.0$ & per decimal unit & calibration prior ($\approx$2\% per 100 bp) \\
$\gamma_F$ (FICO, z) & $-0.20$ & per SD & calibration prior \\
$\gamma_L$ (LTV, z) & $+0.25$ & per SD & calibration prior \\
\bottomrule
\end{tabular}
\end{threeparttable}
```

**INSERT** it (unchanged, `[H]` retained) as its own paragraph immediately after the §V.B paragraph that
first `\ref`s it (tex 253). Insertion anchor — the paragraph's final sentence, `count == 1`:

```
Prepaid balances settle to simulated SOMA cash flow in the month they occur; no settlement delay is modeled on this path.
```

i.e. new text = anchor line + blank line + block + blank line.

### E2 — float move: `tab:floorband` (App. `app:floormech` → §V.B)

**CUT** the block at tex 1231--1248 (`\label{tab:floorband}`):

- first 60 chars: `
\begin{table}[H]
\centering
\caption{The calibration box: l`
- last 60 chars: `2.1$ & $+2.3$ & $+2.4$ & 88.7\% \\
\bottomrule
\end{tabular}`
- `tex.count(block) == 1` (verified)
- length: 1376 chars, 18 lines

```tex

\begin{table}[H]
\centering
\caption{The calibration box: lock-in marginal over the $\beta_1 = 0$ null, in percentage points of the \$764.7 billion benchmark, across the involuntary-turnover floor and the Liebersohn--Rothstein band $\delta$. The 6.0\% row's level is reached only by the refi-contaminated pooled and 2019 anchors that Section~\ref{sec:robustness-floor} disqualifies; it is retained as a grid point, not a defensible anchor, and the box's lower edge should be read from the defensible off-window rows of Table~\ref{tab:oosfloor}. The bind column is the share of evaluated U.S. loan-months at which the floor lifts the hazard (central elasticity). Every marginal is basis-invariant (the underlying levels are standalone-scorer figures; both bases in Table~\ref{tab:bases}). Pre-committed runs; artifacts catalogued in Appendix~\ref{app:ledger}.}
\label{tab:floorband}
\begin{tabular}{lcccc}
\toprule
Floor (annual CPR) & $\delta = 5.5\%$ & $\delta = 6.5\%$ & $\delta = 7.7\%$ & Floor binds \\
\midrule
2.0\% & $+9.7$ & $+11.3$ & $+13.2$ & 3.9\% \\
3.0\% & $+9.3$ & $+10.8$ & $+12.6$ & 12.1\% \\
3.5\% & $+8.9$ & $+10.3$ & $+11.8$ & 21.6\% \\
4.0\% (production) & $+8.1$ & $+9.2$ & $+10.4$ & 36.3\% \\
4.5\% & $+6.7$ & $+7.5$ & $+8.4$ & 53.5\% \\
5.0\% & $+5.0$ & $+5.5$ & $+6.0$ & 69.1\% \\
6.0\% & $+2.1$ & $+2.3$ & $+2.4$ & 88.7\% \\
\bottomrule
\end{tabular}
```

**INSERT** immediately after `fig:band`'s `\end{figure}` (tex 279), the float whose caption carries its first
`\ref`. Insertion anchor, `count == 1`:

```
Table~\ref{tab:floorband} extends this band across the involuntary-turnover-floor grid.}
```

with the specifier swap of A3: `\begin{table}[H]` → `\begin{table}[!t]` (first line of the moved block only).

### E3 — float move: `tab:oosfloor` + `tab:lowband` (App. `app:floormech` → §V.E)

**CUT** the block at tex 1250--1275 (`\label{tab:oosfloor}`):

- first 60 chars: `
\begin{table}[H]
\centering
\footnotesize
\begin{threepartt`
- last 60 chars: ` read off one another.
\end{tablenotes}
\end{threeparttable}`
- `tex.count(block) == 1` (verified)
- length: 2486 chars, 26 lines

```tex

\begin{table}[H]
\centering
\footnotesize
\begin{threeparttable}
\caption{Out-of-sample floor anchors and the lock-in marginal each implies, in percentage points of the \$764.7 billion benchmark. Floors are exposure-weighted annualized turnover CPR on out-of-the-money cohort-months measured \emph{outside} the June 2022--November 2025 evaluation window (2017--2019 performance), except the final row, whose floor is calibrated on the window's own first nineteen months. Every row, that one included, reports its floor's \emph{full-window} marginal on a common basis; the held-out-months evaluation is given in the note. Contaminated anchors are reported for completeness and are not this paper's off-window anchor; the pooled anchor's 6.07\% measurement is evaluated at the box's adjacent 6.0\% grid row. Every marginal is basis-invariant and reproduces the committed production artifacts exactly at the 4\% row. Pre-committed run \texttt{oos\_identification}; artifact catalogued in Appendix~\ref{app:ledger}.}
\label{tab:oosfloor}
\begin{tabular}{llcccc}
\toprule
Floor anchor & Status & Floor & $\delta = 5.5\%$ & $\delta = 6.5\%$ & $\delta = 7.7\%$ \\
\midrule
2018 leg, gap $\leq -0.005$ & defensible & 4.70\% & $+6.1$ & $+6.8$ & $+7.5$ \\
2018 leg, gap $\leq -0.0025$ & defensible & 4.99\% & $+5.0$ & $+5.6$ & $+6.1$ \\
2018 leg, gap $\leq 0$ & defensible & 5.33\% & $+3.9$ & $+4.3$ & $+4.6$ \\
\midrule
Pooled 2017--2019 & refi-contaminated & 6.07\% & $+2.1$ & $+2.3$ & $+2.4$ \\
2019 leg, gap $\leq 0$ & refi-contaminated & 6.91\% & $+0.7$ & $+0.7$ & $+0.8$ \\
\midrule
In-window (production) & in-sample point & 4.00\% & $+8.1$ & $+9.2$ & $+10.4$ \\
Early-window calibration & full window\tnote{a} & 3.97\% & $+8.1$ & $+9.3$ & $+10.5$ \\
\bottomrule
\end{tabular}
\begin{tablenotes}[flushleft]\footnotesize
\item[a] Temporal holdout. The 3.97\% floor is calibrated on deeply out-of-the-money turnover in the window's first nineteen months (June 2022--December 2023). Summed over the strictly held-out remaining twenty-three months (January 2024--November 2025), which enter that calibration nowhere, the central-minus-null marginal is $+\$45.1$ billion at the central elasticity, against $+\$44.8$ billion at the production floor over the identical months. The table row above reports the same floor's full-window marginal, so that every row is comparable; the two quantities are different objects and should not be read off one another.
\end{tablenotes}
\end{threeparttable}
```

**CUT** the block at tex 1198--1223 (`\label{tab:lowband}`):

- first 60 chars: `
\begin{table}[H]
\centering
\caption{The lock-in marginal a`
- last 60 chars: ` & $+6.09$ \\
\bottomrule
\end{tabular}
\end{threeparttable}`
- `tex.count(block) == 1` (verified)
- length: 1731 chars, 26 lines

```tex

\begin{table}[H]
\centering
\caption{The lock-in marginal as a curve in the imported elasticity. Paired central-minus-null runs at each quarterly mobility decline $\delta$ (the elasticity import of Section~\ref{sec:pathb}, mapped to $\beta_1$ via \eqref{eq:beta1}), with the floor and every other production convention held fixed, at the in-sample 4.0\% floor and the off-window 4.991\% headline floor (run \texttt{band\_low\_extension}; the band-cell rows reproduce the committed production and off-window cells within the sweep tolerance of $\pm\$0.01$ billion). The $\delta = 0$ rows are the $\beta_1 = 0$ nulls, so their marginal is zero by construction; $\delta = 3.25\%$ is half the adopted central; $\{5.5, 6.5, 7.7\}\%$ is the adopted Liebersohn--Rothstein band.}
\label{tab:lowband}
\footnotesize
\begin{threeparttable}
\begin{tabular}{@{}rrrrrr@{}}
\toprule
& & \multicolumn{2}{c}{In-sample floor (4.0\%)} & \multicolumn{2}{c}{Off-window floor (4.991\%)} \\
\cmidrule(lr){3-4}\cmidrule(lr){5-6}
$\delta$ (\%) & $\beta_1$ & marginal (\$B) & (pp) & marginal (\$B) & (pp) \\
\midrule
0.00 & $0.0000$ & $0.0$ & $0.00$ & $0.0$ & $0.00$ \\
1.00 & $-0.0103$ & $+12.8$ & $+1.67$ & $+9.4$ & $+1.23$ \\
2.00 & $-0.0206$ & $+24.9$ & $+3.26$ & $+17.7$ & $+2.31$ \\
3.00 & $-0.0311$ & $+36.4$ & $+4.76$ & $+24.9$ & $+3.25$ \\
3.25 & $-0.0337$ & $+39.1$ & $+5.12$ & $+26.5$ & $+3.47$ \\
4.00 & $-0.0417$ & $+47.1$ & $+6.16$ & $+31.0$ & $+4.06$ \\
5.00 & $-0.0523$ & $+57.1$ & $+7.46$ & $+36.3$ & $+4.74$ \\
5.50 & $-0.0577$ & $+61.7$ & $+8.07$ & $+38.6$ & $+5.05$ \\
6.50 & $-0.0686$ & $+70.3$ & $+9.20$ & $+42.6$ & $+5.57$ \\
7.70 & $-0.0817$ & $+79.5$ & $+10.39$ & $+46.6$ & $+6.09$ \\
\bottomrule
\end{tabular}
\end{threeparttable}
```

**INSERT** both (oosfloor first, then lowband, blank line between), with the A3 specifier swap, immediately
after the `tab:assembly` float and before `fig:marginalcells`. Insertion anchor — the last four lines of
`tab:assembly`, `count == 1`:

```
Fonseca--Liu anchor & $+11.5$ & above & counterweight, conservative-band evidence \\
\bottomrule
\end{tabular}
\end{table}
```

**Guard:** the insertion point is *after* `\end{table}`, never inside tex 312. `assembly_check` (gate #98)
requires exactly one line beginning `A seventh qualification`; verified still 1 post-edit.

### E4 — NEW small table: the inference ladder (`tab:ladder`)

**INSERT** immediately after the `tab:uncertainty` float and before `\subsection{Interpretation}`.
Insertion anchor, `count == 1`:

```
\end{tablenotes}
\end{threeparttable}
\end{table}

\subsection{Interpretation}
```

(new text = the three closing lines, a blank line, the block below, a blank line, then `\subsection{Interpretation}`.)

```tex
\begin{table}[!t]
\centering
\caption{The inference ladder on the binding layer. Every row prices one layer --- the floor read's own sampling error, propagated through the frozen floor-to-marginal grid at the central elasticity $\delta = 6.5\%$ --- so no row's width comes from the elasticity, which is swept separately in Table~\ref{tab:lowband}. All reads are on the 2018 leg's mid-grid anchor, which 31 stratum clusters carry. The Webb-weight wild-cluster bootstrap-$t$ is the primary construction and the interval this paper quotes; the percentile read is reported demoted rather than as a competing interval. Runs \texttt{floor\_uncertainty} (percentile), \texttt{floor\_inference\_correction} (Rademacher wild-$t$; CR2/CR3 at $t(30)$), and \texttt{floor\_inference\_correction\_v2} (Webb primary, Bell--McCaffrey degrees of freedom, restricted inversion).}
\label{tab:ladder}
\footnotesize
\begin{threeparttable}
\begin{tabular}{@{}llll@{}}
\toprule
Layer & Marginal (pp) & Degrees of freedom & Status \\
\midrule
Percentile cluster bootstrap & $+3.0$ to $+8.0$ & --- (1000-replicate) & demoted; under-covers at 31 clusters \\
CR2 $t$ & $+3.0$ to $+8.6$ & $t(30)$, $G-1$ & conventional df \\
CR3 $t$ & $+2.8$ to $+8.8$ & $t(30)$, $G-1$ & conventional df \\
Wild-$t$, Rademacher & $+2.8$ to $+8.7$ & bootstrap, $B = 9{,}999$ & the committed construction, replayed \\
Wild-$t$, Webb & $+2.9$ to $+8.7$ & bootstrap, $B = 9{,}999$ & primary; the binding layer \\
CR2 $t$, Bell--McCaffrey & $+2.4$ to $+9.2$ & $t(5.1)$, data-driven & small-sample df \\
CR3 $t$, Bell--McCaffrey & $+2.3$ to $+9.6$ & data-driven, CR3's own & small-sample df \\
Restricted wild-cluster inversion & $+2.3$ to $+9.1$ & 401-point grid inversion & agrees in location \\
\bottomrule
\end{tabular}
\begin{tablenotes}[flushleft]\footnotesize
\item The Bell--McCaffrey degrees of freedom are data-driven and estimator-specific, so one value cannot serve both cluster-robust variants: the 5.1 shown is CR2's, and CR3's own is smaller. The effective cluster count is 5.9 by the same Herfindahl-inverse convention as the loan/stratum scheme's 25.8, against 31 nominal clusters, and the run's recorded maximum single-cluster leverage is 0.33, ten times an equal 31-cluster share. That concentration is why the wild-cluster correction is applied and the percentile read demoted.
\end{tablenotes}
\end{threeparttable}
\end{table}
```

Every printed value is a committed literal already in the file or in the note E5 replaces: percentile
`$+3.0$ to $+8.0$` (tex 592), CR2/CR3 at $t(30)$ (tex 592), Rademacher `$+2.8$ to $+8.7$`, Webb
`$+2.9$ to $+8.7$`, CR2/CR3 at Bell--McCaffrey df, WCR `$+2.3$ to $+9.1$`, `9{,}999`, `5.1`, `5.9`, `25.8`,
`0.33`, 31 clusters, 401-point inversion (all tex 364). No new number (A4).

### E5 — the ladder prose becomes a pointer (replaces tex 364)

**OLD** (`count == 1`, the whole line — the manuscript is one paragraph per line):

```tex
\item Both cluster bootstraps above rest on few clusters: 31 carry the floor read, and the loan/stratum scheme's 130 strata are unequal enough to be worth 25.8 effective ones. Percentile cluster bootstraps are known to under-cover at cluster counts in that range; run \texttt{floor\_inference\_correction} reports the corrections for the floor read (CR2/CR3 $t(30)$ intervals and a Rademacher wild-cluster bootstrap-$t$), and the headline row quotes the wild-$t$ interval as the binding layer. That interval prices one layer: the floor read's own sampling error, propagated through the frozen floor-to-marginal grid at the central elasticity $\delta = 6.5\%$, so none of its width comes from the elasticity, which is swept separately in the calibration column and in Table~\ref{tab:lowband}. No such correction is run for the loan/stratum scheme, whose interval is still better read as a lower bound on sampling uncertainty than as calibrated 95\% coverage; one input to the convolved line being a lower bound makes the convolved line a lower bound as well. The secondary corrected reads agree with the wild-$t$ layer: under the Webb-weight primary construction of run \texttt{floor\_inference\_correction\_v2}: the Rademacher construction reads $+2.8$ to $+8.7$, the Webb re-read $+2.9$ to $+8.7$ --- both endpoints within a tenth of a point, a re-printing rather than a substantive move --- while the secondary reads at the small-sample Bell--McCaffrey degrees of freedom (5.1, against $t(30)$; effective cluster count 5.9 by the same Herfindahl-inverse convention as the loan/stratum scheme's 25.8) are wider: CR2 $+2.4$ to $+9.2$, CR3 $+2.3$ to $+9.6$, and the restricted wild-cluster inversion $+2.3$ to $+9.1$, all agreeing in location and none crossing zero. The bootstrap imposes the point estimate as the data-generating truth over unrestricted residuals (B $= 9{,}999$), studentizes on the floor's own scale, and maps endpoints through the frozen floor-to-marginal grid. Leverage is concentrated rather than diffuse: the run's recorded maximum single-cluster leverage is 0.33, ten times an equal 31-cluster share. That concentration is why the wild-cluster correction is applied and the percentile read demoted.
```

**NEW:**

```tex
\item Both cluster bootstraps above rest on few clusters: 31 carry the floor read, and the loan/stratum scheme's 130 strata are unequal enough to be worth 25.8 effective ones. Percentile cluster bootstraps are known to under-cover at cluster counts in that range; run \texttt{floor\_inference\_correction} and its Webb-weight successor \texttt{floor\_inference\_correction\_v2} correct the floor read, Table~\ref{tab:ladder} sets the corrected ladder out layer by layer with its degrees of freedom, and the headline row quotes the wild-$t$ interval as the binding layer. That interval prices one layer: the floor read's own sampling error, propagated through the frozen floor-to-marginal grid at the central elasticity $\delta = 6.5\%$, so none of its width comes from the elasticity, which is swept separately in the calibration column and in Table~\ref{tab:lowband}. No such correction is run for the loan/stratum scheme, whose interval is still better read as a lower bound on sampling uncertainty than as calibrated 95\% coverage; one input to the convolved line being a lower bound makes the convolved line a lower bound as well. The ladder's reads agree: the Rademacher and Webb constructions land with both endpoints within a tenth of a point, a re-printing rather than a substantive move, while the small-sample degrees of freedom and the restricted inversion are wider, all agreeing in location and none crossing zero. The bootstrap imposes the point estimate as the data-generating truth over unrestricted residuals (B $= 9{,}999$), studentizes on the floor's own scale, and maps endpoints through the frozen floor-to-marginal grid.
```

What is preserved verbatim: the few-cluster framing and `25.8`; the gate-#105 span
`makes the convolved line a lower bound as well` inside its own sentence; the one-layer scoping sentence
(`the floor read's own sampling error, propagated through the frozen floor-to-marginal grid at the central
elasticity $\delta = 6.5\%$`); `both endpoints within a tenth of a point, a re-printing rather than a
substantive move`; `all agreeing in location and none crossing zero`; and the whole DGP / studentization /
mapping sentence with `B $= 9{,}999$`. What leaves: the eight interval literals and the df/leverage
parentheticals — all of them re-printed in E4.

### E6 — `tab:headline`: operative interval + sensitivity catalogue

**OLD** — third cell of the marginal row (tex 76), `count == 1`:

```tex
floor-read wild-cluster bootstrap-$t$ $[+2.9, +8.7]$, the binding layer (31 clusters; percentile read $[+3.0, +8.0]$, under-covering); off-window floor range $+4.3$ to $+6.8$ (max form; $+3.9$ to $+7.5$ joint with the band); additive form $+11.2$, floor-invariant; form-conditional hull $+3.5$ to $+13.1$, upper end from a 61.2\%-recovery cell and not read as an equally credentialed member (the concave transform and the additive form do not compose additively: jointly $+9.2$, interaction $-1.47$); mixture curve in the floor's involuntary share: $+9.7$ at $s{=}0.25$, $+10.7$ at $s{=}0.4$ (run \texttt{floor\_form\_mixture}); Ginnie overlay $+4.4$ (conventional-share scaling $0.797\times$); floor-stability check $+\$45.1$ billion \\
```

**NEW** — cell keeps the operative interval only, and gains a note marker:

```tex
floor-read wild-cluster bootstrap-$t$ $[+2.9, +8.7]$, the binding layer (31 clusters; percentile read $[+3.0, +8.0]$, under-covering; the corrected ladder and its degrees of freedom are Table~\ref{tab:ladder})\tnote{a} \\
```

**AND INSERT** the note into the existing `threeparttable`, between `\end{tabular}` and
`\end{threeparttable}`. Insertion anchor, `count == 1`:

```
\bottomrule
\end{tabular}
\end{threeparttable}
\end{table}

\paragraph{Definitions used throughout.}
```

```tex
\begin{tablenotes}[flushleft]\footnotesize
\item[a] Sensitivity catalogue for the headline marginal, each entry a committed figure derived where it is cited and none of them a sampling interval: off-window floor range $+4.3$ to $+6.8$ (max form; $+3.9$ to $+7.5$ joint with the band); additive form $+11.2$, floor-invariant; form-conditional hull $+3.5$ to $+13.1$, upper end from a 61.2\%-recovery cell and not read as an equally credentialed member (the concave transform and the additive form do not compose additively: jointly $+9.2$, interaction $-1.47$); mixture curve in the floor's involuntary share: $+9.7$ at $s{=}0.25$, $+10.7$ at $s{=}0.4$ (run \texttt{floor\_form\_mixture}); Ginnie overlay $+4.4$ (conventional-share scaling $0.797\times$); floor-stability check $+\$45.1$ billion.
\end{tablenotes}
```

The catalogue substring is byte-identical to the OLD cell from `off-window floor range` to
`floor-stability check $+\$45.1$ billion` — the splice is a colon before it and a period after it.

### E7 — the two pointer sentences the moves falsify

**E7a OLD** (tex 586, §VII.F), `count == 1`:

```
The sweep mechanics, the marginal-as-a-curve exhibit, the contamination separation behind the off-window anchors, and the full calibration-box tables are collected in Appendix~\ref{app:floormech}; what follows are the readings the headline interval rests on.
```

**E7a NEW:**

```
The sweep mechanics and the contamination separation behind the off-window anchors are collected in Appendix~\ref{app:floormech}; the exhibits they produce --- the calibration box (Table~\ref{tab:floorband}), the marginal as a curve in the elasticity (Table~\ref{tab:lowband}), and the out-of-sample anchors (Table~\ref{tab:oosfloor}) --- are in Section~\ref{sec:hazard}, and what follows are the readings the headline interval rests on.
```

**E7b OLD** (tex 1192, App. `app:floormech` opener), `count == 1`:

```
This appendix collects the sweep mechanics and full tables of the calibration box of Section~\ref{sec:robustness-floor}: the floor-level sweep, the marginal as a curve in the imported elasticity, the separation of the two refinance contaminations behind the off-window floor anchors, and the out-of-sample anchor table.
```

**E7b NEW:**

```
This appendix collects the mechanics behind the calibration box of Section~\ref{sec:robustness-floor}: the floor-level sweep, the marginal as a curve in the imported elasticity, the separation of the two refinance contaminations behind the off-window floor anchors, and the out-of-sample anchor construction. The three exhibits themselves are read where the headline is set, in Section~\ref{sec:hazard} (Tables~\ref{tab:floorband}, \ref{tab:lowband}, and~\ref{tab:oosfloor}).
```

---

## 4. Post-edit count ledger (measured on the in-memory application of E1--E7)

Unchanged (the ones that matter): `$+2.9$ to $+8.7$` 8; `$[+2.9, +8.7]$` 3; `$+2.9$ and $+8.7$` 2 (abstract
untouched, and the ordering assert holds because the abstract is byte-identical); `$+3.5$ to $+13.1$` 7;
`$+3.9$ to $+13.1$` 0; `$+4.3$ to $+6.8$` 7; `$[+2.80, +8.99]$` 2; `$[+4.63, +6.92]$` 2;
`$[+8.27, +10.19]$` 5; `$[+9.17, +9.23]$` 6; `$+11.2$` 9; `$+11.5$` 4; `form-conditional` 12;
`$+\$45.1$ billion` 4; `$-1.47$` 7; `68.8\%` 3; `35.8\%` 3; `60.2\%` 9; `76.3\%` 7; `12.6\%` 5;
`$+2.8$ to $+8.7$` 1; `$+2.4$ to $+9.2$` 1; `$+2.3$ to $+9.6$` 1; `$+2.3$ to $+9.1$` 1; `0.33` 5; `25.8` 4;
`Herfindahl` 1; every `LETTER_CURRENT_LITERALS` entry still present; `ZERO_COUNT` all 0; `EXACTLY_ONE` all 1;
`894.8` still labeled.

Increased (all thresholds are `>=`; no upper bound exists for any of these):

| literal | before | after | why |
|---|---|---|---|
| `$+3.0$ to $+8.0$` | 4 | 5 | percentile row in the ladder (gate `>= 2`) |
| `binding layer` | 8 | 10 | ladder Status cell + E5 note (gate: presence) |
| `$+3.0$ to $+8.6$` | 1 | 2 | CR2 $t(30)$ ladder row (A5) |
| `$+2.8$ to $+8.8$` | 1 | 2 | CR3 $t(30)$ ladder row (A5) |
| `floor\_inference\_correction` | 6 | 8 | ladder caption + E5 note (gate `in tex`) |
| `floor\_uncertainty` | 3 | 4 | ladder caption (gate `in tex`) |
| `9{,}999` | 1 | 3 | two ladder rows + E5 note |
| `Bell--McCaffrey` | 1 | 4 | caption, two rows, ladder note |
| `$t(30)$` | 2 | 3 | two ladder rows + caption |

**Gate-span sweep:** every string constant of every `*_SPANS` dict in `tools/liveness_gates.py` that is
present in the current manuscript is still present after E1--E7 (**0 losses**). `\begin`/`\end` parity for
`table`/`threeparttable`/`tablenotes`/`tabular` is balanced. All five `HARDCODED_XREF` patterns: 0 hits.
File grows 1417 → 1450 lines (the new float + the two new `tablenotes` blocks).

## 5. Apply / verify recipe (for the applying agent)

1. Apply E1--E7 in order, in **one** commit with nothing else in it.
2. `python tools/liveness_gates.py` — expect ALL PASS, no gate/test/letter edit required by this package
   (no pinned span moves, no counted literal falls, no letter literal disappears, abstract untouched → the
   226/248-word recount does not move).
3. `pytest tests/ -q` — the manuscript-reading batteries (`test_headline_posture_gate.py`,
   `test_assembled_corrections_gate.py`, `test_convolved_line_gate.py`, `test_elasticity_discipline_gate.py`,
   `test_verdict_audit_gate.py`, `test_coupon_convention_gate.py`) are span-presence + mutation tests and are
   satisfied by §1's sweep; none of them hard-codes a table's *location*.
4. Build (tectonic) and check: no `Table ??`, float order sane, and recompute the two-PDF split page (A3).
5. Response letter: nothing in §7's current-state literal list changes. If the coordinator takes A5's
   alternative (drop the $G-1$ rows), nothing changes there either.

## 6. Deliberately not done here

- No `tab:uncertainty` **row** edits (tex 357) — the round-28 C1/C2 landings pinned that cell; the ladder is
  additive to it, not a replacement for it.
- No edit to tex 592's §VII.F ladder sentence; if the coordinator wants a single ladder site, the follow-up
  is to shorten tex 592 to a pointer at `tab:ladder` — a separate, posture-free edit with its own count
  re-derivation (it holds `open below $+4.3$`, `84.0\% of weight imputed`, `binding layer` and both
  `$+3.0$ to $+8.0$`/`$+2.9$ to $+8.7$` occurrences, so it is *not* a free deletion).
- No CR1 row, no CR3 Bell--McCaffrey df value (A4).
- No renumbering bookkeeping for `tab:crosswalk`/`tab:runindex` — both address exhibits by `\ref`, verified.
