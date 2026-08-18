# DRAFT R29 — two length levers, as count-asserted OLD/NEW pairs

Drafting agent, read-only. Nothing tracked was modified; no repo script was executed; no git
mutation. All counts below were re-derived from the working tree at draft time (branch
`claude/brave-shaw-b02840`, manuscript `paper/v18/revised_paper_v18.tex`, 1,435 lines).

**Levers.** (a) Relocate `fig:abmpaths` and `fig:mc` from §IV to Appendix `sec:method-abm`
(flagged as available in `specs/DRAFT_WPE_sec3_sec4.md:409-412`). (b) Consolidate the §VII.F
inference-ladder recital to a pointer at `tab:ladder` (the follow-up named in
`specs/DRAFT_WPE_sec5_exhibits.md:526-529`).

**Rename-collision check (parallel agent, "involuntary-turnover floor" → "baseline turnover
floor"): CLEAR.** Every OLD string in this package contains **zero** occurrences of
`involuntary` — verified by literal `.count('involuntary')` on each OLD, not by eyeballing:

| OLD string | `involuntary` count |
| --- | --- |
| A1 (the §IV figure block, tex 173–189) | 0 |
| A2 (the appendix anchor, `\end{figure}` + the payoff-rules sentence) | 0 |
| A3a / A3b (the two §IV `\ref` sites) | 0 |
| B1 (the ladder recital, tex 737 chars 3170–3693) | 0 |

**One near miss, stated loudly so it is not tripped over:** the `fig:cprsurface` **caption**
(tex 918) contains `involuntary-turnover floor` and is the line *immediately above* lever (a)'s
insertion point. A2's OLD anchor deliberately starts at `\end{figure}` (tex 920) and does not
include tex 918, so the two packages do not overlap. **If the coordinator re-anchors A2 upward
onto the caption, the packages collide and must be sequenced.** As drafted they are
order-independent.

**Cross-checked against the rename agent's own draft** (`specs/DRAFT_R29_A2_floor_rename.md:41`,
which enumerates all 25 `involuntary-turnover floor` sites): tex **30, 47, 51, 91, 201, 240,
301, 336, 552, 607, 665, 729, 745, 749, 751, 765, 918, 930, 932, 1042, 1064, 1092, 1327, 1329**.
Intersect that with this package's edit lines — **159, 175–188, 737, 920, 922** — and the
intersection is **empty**. Note the two adjacencies that make the check worth doing rather than
assuming: **918** sits two lines above A2's anchor, and **729** sits in the same §VII.F
subsection as B1's target at **737**. Neither is touched. The two packages can be applied in
either order.

---

## 1. Edit sets, ordered for application

Apply in the order A1 → A2 → A3a → A3b → B1. A1 must precede A2 (A1 removes the block A2
re-inserts; applying A2 first makes A1's OLD non-unique — the two figure environments would
then exist twice).

### LEVER (a) — relocate `fig:abmpaths` + `fig:mc` to Appendix `sec:method-abm`

Captions, labels, `\includegraphics` options and float specifiers move **byte-identical**. The
only bytes that change anywhere in lever (a) are the two `\ref`-site parentheticals of A3a/A3b.

---

#### A1 — DELETE the two figure environments from §IV (tex 173–189)

Occurrences of OLD in the file: **1** (verified).

**OLD** (17 lines, 1,248 chars; begins at the `\end{figure}` that closes `fig:waterfall` and
ends at the `\subsection` line, so the blank-line hygiene is pinned by the anchor itself):

```
\end{figure}

\begin{figure}[H]
\centering
\includegraphics[width=0.9\textwidth]{fig10_abm_cpr_paths}
\caption{Production ABM simulated CPR against the empirical SOMA back-out over the QT window (frozen fold-in run, seed 42). The simulated path runs at roughly twice the empirical level and does not track its month-to-month shape; the annotated means, lag-0 $r$, and $R^2$ are the manifest values quoted in the text. This is the level-and-shape mismatch behind the negative path statistics; the cross-correlation structure across lags is in Figure~\ref{fig:ccf}.}
\label{fig:abmpaths}
\end{figure}

\begin{figure}[H]
\centering
\includegraphics[width=0.82\textwidth]{monte_carlo_trapped_liquidity}
\caption{Monte Carlo population-draw distribution of ABM trapped liquidity (50 seeds, fold-in specification; CPR surface rebuilt per draw). The seed-level dispersion (SD \$24.5 billion) dwarfs the distance between the frozen seed-42 production draw (\$91.0 billion, 34th percentile) and the seed mean (\$103.7 billion); the empirical benchmark of \$764.7 billion lies far outside the distribution's support, which is the visual form of the ABM's 10--17\% recovery band.}
\label{fig:mc}
\end{figure}

\subsection{Interpretation}\label{sec:abm-interp}
```

**NEW** (3 lines):

```
\end{figure}

\subsection{Interpretation}\label{sec:abm-interp}
```

---

#### A2 — INSERT the same two environments into Appendix `sec:method-abm`

**Insertion point chosen:** immediately after `fig:cprsurface`'s `\end{figure}` (tex 920) and
before the paragraph that opens `The simulation contrasts two institutional payoff rules.`
(tex 922).

**Why here.** `sec:method-abm` runs prose (903–913) → the precomputed CPR surface
`fig:cprsurface` (915–920) → the payoff-rule paragraph (922). The production run *interpolates
that surface month by month* to produce the simulated CPR path, and the seed distribution is
the dispersion of the dollar that path yields, so the appendix reads surface → path → seed
distribution as one causal chain, and the two moved floats land against the only prose in the
document that specifies the machinery they display. The alternative anchor (after tex 907, the
scale/seed-replication sentence) was rejected because it interrupts the annuity/decision-rule
derivation at 909–913.

Occurrences of OLD in the file: **1** (verified; the payoff-rules sentence is unique).

**OLD**:

```
\end{figure}

The simulation contrasts two institutional payoff rules.
```

**NEW** (the two environments verbatim from A1's OLD, with one blank line on each side):

```
\end{figure}

\begin{figure}[H]
\centering
\includegraphics[width=0.9\textwidth]{fig10_abm_cpr_paths}
\caption{Production ABM simulated CPR against the empirical SOMA back-out over the QT window (frozen fold-in run, seed 42). The simulated path runs at roughly twice the empirical level and does not track its month-to-month shape; the annotated means, lag-0 $r$, and $R^2$ are the manifest values quoted in the text. This is the level-and-shape mismatch behind the negative path statistics; the cross-correlation structure across lags is in Figure~\ref{fig:ccf}.}
\label{fig:abmpaths}
\end{figure}

\begin{figure}[H]
\centering
\includegraphics[width=0.82\textwidth]{monte_carlo_trapped_liquidity}
\caption{Monte Carlo population-draw distribution of ABM trapped liquidity (50 seeds, fold-in specification; CPR surface rebuilt per draw). The seed-level dispersion (SD \$24.5 billion) dwarfs the distance between the frozen seed-42 production draw (\$91.0 billion, 34th percentile) and the seed mean (\$103.7 billion); the empirical benchmark of \$764.7 billion lies far outside the distribution's support, which is the visual form of the ABM's 10--17\% recovery band.}
\label{fig:mc}
\end{figure}

The simulation contrasts two institutional payoff rules.
```

**Byte-identity assertion.** The caption/label/`includegraphics` bytes in A2's NEW are the same
bytes as in A1's OLD. Mechanical check after applying both:

```sh
diff <(git show HEAD:paper/v18/revised_paper_v18.tex | sed -n '175,187p') \
     <(sed -n '/^\\begin{figure}\[H\]$/,/^\\end{figure}$/p' paper/v18/revised_paper_v18.tex | \
       grep -A6 -B1 'fig10_abm_cpr_paths')   # inspect visually; the grep below is the hard gate
```

Hard gate (both must print `1`):

```sh
grep -c 'fig10_abm_cpr_paths' paper/v18/revised_paper_v18.tex
grep -c 'monte_carlo_trapped_liquidity' paper/v18/revised_paper_v18.tex
```

**Float specifier: keep `[H]`. Decision, with the reasoning.** `float` is loaded (preamble line
6) and **every one of the 13 figures in the manuscript is `[H]`**, so `[H]` is the document's
universal convention and changing it here would make the move non-byte-identical for a
cosmetic gain. `specs/DRAFT_WPE_sec5_exhibits.md:101` reaches the same judgment from the other
side — `[H]` is "fine in an appendix, hostile in a dense §V" — and the destination *is* an
appendix. **Typographic consequence, flagged not fixed:** three consecutive `[H]` floats will
then sit between tex 920 and the payoff-rules paragraph. Estimated stacked height at 1in
margins (6.5in text width): `fig:cprsurface` ≈ 1.9in + caption ≈ 1.1in; `fig:abmpaths` ≈ 2.86in
(aspect 0.488 at `0.9\textwidth`) + caption ≈ 0.75in; `fig:mc` ≈ 3.09in (aspect 0.579 at
`0.82\textwidth`) + caption ≈ 0.9in ≈ **10.6in against a 9in text block**, so LaTeX will break
the page inside the cluster and may leave one short page. If the coordinator dislikes that,
the single-character alternative is `\begin{figure}[H]` → `\begin{figure}[!t]` on the moved
blocks *only* (which forfeits byte-identity and is **not** what this draft recommends).

---

#### A3a — reader-courtesy pointer at the `fig:mc` site (tex 159)

Both `\ref`s stay valid after the move (`\ref` is location-independent), so A3a/A3b are
courtesy, not correctness. I recommend applying them: §IV now sends the reader to a float that
is ~50 printed pages away with no signal that it moved.

Occurrences of OLD: **1** (verified). Contains no gate span (see §4).

**OLD**: `point estimate (Figure~\ref{fig:mc}).`

**NEW**: `point estimate (Figure~\ref{fig:mc}, Appendix~\ref{sec:method-abm}).`

#### A3b — the same at the `fig:abmpaths` site (tex 159)

Occurrences of OLD: **1** (verified).

**OLD**: `no extension repairs it (Figure~\ref{fig:abmpaths}):`

**NEW**: `no extension repairs it (Figure~\ref{fig:abmpaths}, Appendix~\ref{sec:method-abm}):`

**Call made:** figure first, address second. The referent is the figure; the appendix is where
it lives. The brief's suggested ordering — `(Appendix~\ref{sec:method-abm},
Figure~\ref{fig:mc})` — is equally safe and equally gate-clean if the coordinator prefers it;
it just leads with the address. Either form keeps the `HARDCODED_XREF` gate at 0 (`\ref`, never
a literal number; `Appendix~\ref` does not match the `Appendix[~ ][AB]` pattern).

**Note on repetition:** tex 159 already closes with `Appendices~\ref{sec:method-abm},
\ref{sec:method-frictions}, ...`. A3a/A3b therefore put `sec:method-abm` in that paragraph
three times. In a 5,376-char paragraph this reads as signposting, not as an echo, but it is a
real judgment call and the coordinator may drop A3b (keeping A3a, the first of the two) if he
disagrees. Dropping either or both is gate-neutral.

---

### LEVER (b) — consolidate the §VII.F ladder recital to a pointer at `tab:ladder`

#### B1 — the single-occurrence edit at tex 737

Location: `\subsection{Floor and Elasticity-Band Sensitivity: The Calibration Box}`
(`sec:robustness-floor`), inside the 5,376-char single-line paragraph at tex 737, at character
offsets **3170–3693** (1-based). Note that tex 737 and tex 738 are **one LaTeX paragraph** (no
blank line between them); B1 touches only 737.

Occurrences of OLD in the file: **1** (verified).

**OLD** (524 chars, 79 words):

```
A percentile interval on 31 clusters is itself a lower bound, and a pre-committed correction (run \texttt{floor\_inference\_correction}; CR2/CR3 $t$-intervals and a Rademacher wild-cluster bootstrap-$t$, with the percentile layer reproduced bit-exactly as its parity gate) widens it mostly at the top: the wild-$t$ interval is $+2.9$ to $+8.7$ points (CR2 $+3.0$ to $+8.6$, CR3 $+2.8$ to $+8.8$), and it is the wild-$t$ interval this paper quotes as the binding layer, with the lower edge above zero on every corrected read.
```

**NEW** (386 chars, 56 words):

```
The percentile read under-covers at that cluster count and is demoted; the pre-committed correction (run \texttt{floor\_inference\_correction}) widens it mostly at the top, and the corrected ladder, with its degrees of freedom, is Table~\ref{tab:ladder}: the Webb wild-$t$ interval of $+2.9$ to $+8.7$ points is the binding layer, with the lower edge above zero on every corrected read.
```

**Saved: 138 chars, 23 words.**

#### What was cut, and why each cut is safe

| cut | disposition |
| --- | --- |
| `CR2 $+3.0$ to $+8.6$, CR3 $+2.8$ to $+8.8$` | **Redundant.** Both are `tab:ladder` rows (tex 469, 470) with their df and status. |
| `CR2/CR3 $t$-intervals and a Rademacher wild-cluster bootstrap-$t$` | **Redundant.** The `tab:ladder` caption (tex 460) already assigns each construction to its run tag: `floor\_uncertainty` (percentile), `floor\_inference\_correction` (Rademacher wild-$t$; CR2/CR3 at $t(30)$), `floor\_inference\_correction\_v2` (Webb primary, Bell–McCaffrey df, restricted inversion). |
| `A percentile interval on 31 clusters is itself a lower bound` | **Redundant, semantics preserved.** `tab:ladder` row 468 status reads `demoted; under-covers at 31 clusters`; `tab:uncertainty` note (tex 452) states the under-coverage at that cluster count. `31 clusters` is also already stated **earlier in the same sentence chain** at tex 737 (`31 clusters carry the 2018 leg`), which is what `at that cluster count` now refers back to. Whole-file `under-cover*` count is 6 (tex 30, 76, 109, 346, 452, 468) and does not move. |
| `with the percentile layer reproduced bit-exactly as its parity gate` | **The one genuinely unique clause dropped.** Not gate-pinned (no gate or test asserts any `bit-exact*` span against the tex — verified). `tab:ladder` row 471 carries the neighbouring replay claim (`the committed construction, replayed`). **Flagged for the coordinator in §6-F3**; if he wants it kept, append `(its percentile layer replays bit-exactly as a parity gate)` after the run tag — +56 chars, still a net cut. |

#### What was kept, and why

- `widens it mostly at the top` — an interpretive finding about the *shape* of the correction
  (the top edge moves 0.7pp, the bottom 0.1pp). Visible in `tab:ladder` but never stated there.
- `the binding layer` + `$+2.9$ to $+8.7$ points` — the posture, and the gate-relevant literal.
- `with the lower edge above zero on every corrected read` — the sign claim. Whole-file count of
  this span is 1; it stays 1.
- `run \texttt{floor\_inference\_correction}` — provenance, gate-pinned by presence.
- **`Webb`** added before `wild-$t$`. See §6-F2: this is a **deliberate accuracy repair**, not a
  wording drift.

#### Scope boundary — what B1 does *not* touch

The brief names five counted literals as living in this sentence. **Four of the five are not
inside B1's OLD at all** and are untouched by this package:

| literal | where in tex 737 | inside B1's OLD? |
| --- | --- | --- |
| `$+3.0$ to $+8.0$` | the percentile-interval clause, *before* offset 3170 | **no** |
| `open below $+4.3$` | the "Second," age-standardization clause, *after* offset 3693 | **no** |
| `84.0\% of weight imputed` | the "Second," clause, after 3693 | **no** |
| `binding layer` | inside OLD | yes — **kept verbatim in NEW** |
| `$+2.9$ to $+8.7$` | inside OLD | yes — **kept verbatim in NEW** |

The "First," clause's measured reads (`1000-replicate`, `0.39--0.46 points of CPR`,
`226 clusters`, `0.16--0.19 points`) and the whole "Second," clause (the age-standardization
*method*, the `an indicative bound rather than a measurement, but signed one way` hedge, and
`that endpoint is not a conservative floor`) are stated **only** at tex 737 and therefore
survive untouched. `tab:uncertainty` row 445 carries one-line versions of the age-standardized
result (`age-standardized floor 5.51\% $\to$ $+3.8$ (84\% imputed weight; band open below
$+4.3$)`), but that is a *different string* from the gate-pinned `84.0\% of weight imputed` and
carries none of the method or the hedge — which is exactly why the "Second," clause is **not**
a free deletion and is left alone.

---

## 2. Zero-slack literal ledger

Counts are whole-file on `paper/v18/revised_paper_v18.tex`, derived by fixed-string
`str.count`, not regex (the round-26 lesson: regex escaping silently under-counted
`$[+2.9, +8.7]$` to 0 on my first pass — the fixed-string recount found 3). "Gate min" is the
**minimum the shipped rule actually requires**, read out of the gate source, not assumed.

### Literals inside or adjacent to B1

| literal | now | in OLD | in NEW | after | gate rule (source) | min | verdict |
| --- | ---: | ---: | ---: | ---: | --- | ---: | --- |
| `$+3.0$ to $+8.0$` | 5 | 0 | 0 | **5** | `liveness_gates.py:4446` `tex.count(...) >= 2`; also `LETTER_CURRENT_LITERALS` (gate #101) | 2 | SAFE |
| `$+2.9$ to $+8.7$` | 8 | 1 | 1 | **8** | `:4447` `tex.count(...) >= 4`; `LETTER_CURRENT_LITERALS`; `ASSEMBLY_SPANS["posture_binding_layer"]` (tex 346) | 4 | SAFE |
| `$+2.9$ to $+8.7$ points` | 7 | 1 | 1 | **7** | `tests/test_headline_posture_gate.py:152`, scoped to the `A seventh qualification` line (tex 346) | 1 (scoped) | SAFE |
| `open below $+4.3$` | 3 | 0 | 0 | **3** | `:4450` presence | 1 | SAFE |
| `84.0\% of weight imputed` | **1** | 0 | 0 | **1** | `:4452` presence | 1 | **SAFE — zero slack.** The sole occurrence is at tex 737, outside B1's OLD. Any future edit to the "Second," clause must keep it. |
| `binding layer` | 10 | 1 | 1 | **10** | `:4451` presence | 1 | SAFE |
| `floor\_uncertainty` | 4 | 0 | 0 | **4** | `:4448` presence | 1 | SAFE |
| `floor\_inference\_correction` | 8 | 1 | 1 | **8** | `:4449` presence | 1 | SAFE |
| `above the clean band` | 4 | 0 | 0 | **4** | gate #86 `:4196` presence | 1 | SAFE |
| `an interaction of $-1.47$ points` | 3 | 0 | 0 | **3** | `:4373` presence; `LETTER_CURRENT_LITERALS` `$-1.47$` | 1 | SAFE |
| `above zero on every corrected read` | 1 | 1 | 1 | **1** | none | 0 | SAFE |

### AND-FORMS AND BRACKET FORMS — enumerated explicitly

The round-26 defect survived because `$+2.9$ and $+8.7$` was not recognized as a *different
string* from `$+2.9$ to $+8.7$`. All variants, counted separately:

| form | count | sites | in B1's OLD/NEW | gate |
| --- | ---: | --- | --- | --- |
| `$+2.9$ to $+8.7$` (to-form) | 8 | tex 45, 76, 336, 346, 472, 737, 749, 755 | OLD 1 / NEW 1 | `:4447` `>= 4` |
| `$+2.9$ and $+8.7$` (**and-form**) | 2 | tex **30 (abstract)**, 109 | 0 / 0 | `ELASTICITY_*`-adjacent span `liveness_gates.py:464` `"The design bounds it between $+2.9$ and $+8.7$ points"`; gate #99 `abstract.find("$+2.9$ and $+8.7$")` at `:513` (ORDERING assert) | 
| `$[+2.9, +8.7]$` (**bracket form**) | 3 | tex 76, 445, 821 | 0 / 0 | none directly; tex 445 is the `tab:uncertainty` headline row |
| `$[+3.0, +8.0]$` (bracket form of the percentile read) | 3 | tex 76, 445, 1417 | 0 / 0 | none |
| `$[+2.80, +8.99]$` (convolved pair) | 2 | tex 445, 1429 | 0 / 0 | gate #105 `CONVOLVED_LINE_SPANS["pair"]` — **not in either edit region** |

**B1 touches no and-form and no bracket form.** The abstract is untouched, so gate #99's
ordering find and gate #68's 248-word recount do not move.

### Literals whose count legitimately falls (none gate-pinned; each verified by grepping
`tools/liveness_gates.py` and `tests/` for the literal — zero hits)

| literal | 2 → 1 / 4 → 3 | surviving site | pinned anywhere? |
| --- | --- | --- | --- |
| `$+3.0$ to $+8.6$` | 2 → **1** | `tab:ladder` CR2 row, tex 469 | no |
| `$+2.8$ to $+8.8$` | 2 → **1** | `tab:ladder` CR3 row, tex 470 | no |
| `Rademacher` | 4 → **3** | tex 452, 460, 471 | no |
| `bit-exactly` | 7 → **6** | tex 278, 336, 346, 733, 1166, 1171 | no |

### The old pair `$+2.8$ ...` — the brief's explicit worry, resolved

`$+2.8$ to $+8.7$` occurs **exactly once**, at **tex 471**, which is the `tab:ladder`
`Wild-$t$, Rademacher` row (`the committed construction, replayed`). **It is not in tex 737 and
not in B1's OLD**, so B1 cannot touch it: count 1 → 1. No gate or test pins it (verified: zero
hits for `+8.7` in `tools/liveness_gates.py` outside the `$+2.9$ to $+8.7$` constants, and zero
hits in `tests/`). The Rademacher **secondary is therefore preserved by construction**, not by
care, which is the stronger guarantee. The related `$+2.8$ to $+8.8$` (CR3) *does* appear in
B1's OLD; it survives at tex 470 and is likewise unpinned.

---

## 3. Figure-numbering sweep (lever (a))

**Counter convention: continuous.** The preamble (tex 1–21) renews `\thesection` only
(`\Roman{section}`) and `\thesubsection`; there is **no** `\renewcommand{\thefigure}` and no
`\setcounter{figure}{0}` anywhere in the file. `\appendix` (tex 775) renumbers *sections* to
A, B, C… but leaves the figure counter running. Figures therefore number **1–13 continuously
across body and appendix**, and relocating two of them renumbers everything between the old
and new sites.

| # | before | after | shift |
| ---: | --- | --- | --- |
| 1 | `fig:architecture` | `fig:architecture` | — |
| 2 | `fig:benchmark` | `fig:benchmark` | — |
| 3 | `fig:recovery` | `fig:recovery` | — |
| 4 | `fig:waterfall` | `fig:waterfall` | — |
| 5 | `fig:abmpaths` | `fig:band` | **7 → 5** |
| 6 | `fig:mc` | `fig:marginalcells` | **8 → 6** |
| 7 | `fig:band` | `fig:gapsweep` | **9 → 7** |
| 8 | `fig:marginalcells` | `fig:crossdesign` | **10 → 8** |
| 9 | `fig:gapsweep` | `fig:cprsurface` | **11 → 9** |
| 10 | `fig:crossdesign` | **`fig:abmpaths`** | **5 → 10** |
| 11 | `fig:cprsurface` | **`fig:mc`** | **6 → 11** |
| 12 | `fig:ccf` | `fig:ccf` | — |
| 13 | `fig:marginaltiming` | `fig:marginaltiming` | — |

**Seven printed numbers move. Nothing pins any of them.** Sweep results:

- **A gate positively forbids printed figure numbers.** `HARDCODED_XREF`
  (`tools/liveness_gates.py:214-220`) requires `re.findall(r"Figure[~ ]\d", tex)` to return
  **0**, alongside `Table[~ ]\d`, `Section[~ ][IVX]+`, `Appendix[~ ][AB]` and
  `[Ee]quation[~ ]\(\d\)`. The manuscript is at 0 today and stays at 0 (A3a/A3b add `\ref`
  only). This gate is the reason the renumbering is a non-event: **the manuscript is
  structurally incapable of pinning a figure number.**
- `grep -rn 'Figure~\?[0-9]\|Figure [0-9]\|fig[0-9]\|monte_carlo' tools/liveness_gates.py
  tests/ paper/v18/response_to_referees_round22.tex` → **one hit**, `liveness_gates.py:194`
  `"abm/monte_carlo_simulation.py"`, which is a *figure-script path* in the
  no-hardcoded-literals allowlist, not a figure number and not a manuscript string.
- The response letter's current section (from tex 338) quotes no figure number and no figure
  label; `LETTER_CURRENT_LITERALS` (`:591-602`) is twelve numeric spans, none of them a figure
  reference.
- The filename↔number mapping is **already** desynced (`fig10_abm_cpr_paths` prints as Figure 5
  today, `fig1_recovery_by_estimator` as Figure 3), so no reader or script can be relying on
  it. After the move `fig10_abm_cpr_paths` becomes Figure 10, which is coincidentally *less*
  confusing.
- `app:ledger` (tex 779–800) lists superseded **values**, not figure numbers or filenames.
  `grep -o 'fig10_abm_cpr_paths\|monte_carlo_trapped_liquidity'` over the whole manuscript
  returns exactly the two `\includegraphics` lines.
- `\ref` integrity: `fig:abmpaths` has **1** reference and `fig:mc` has **1**, both in tex 159,
  matching the census at `specs/DRAFT_WPE_sec3_sec4.md:490`. Both remain live after the move
  (A3a/A3b modify the surrounding parenthetical, never the `\ref`). No dangling refs, no
  removed labels, no duplicate labels.

---

## 4. Gate-collision sweep

**Method.** Rather than eyeballing, I extracted **every** quoted string constant of length ≥ 8
from `tools/liveness_gates.py` and all 26 `tests/*.py` (both raw and `unicode_escape`-decoded)
and tested substring membership against each edit region. This is the only method that catches
a span I did not think to look for.

| region | gate/test spans found inside it |
| --- | --- |
| **A1/A2 figure block (tex 175–188)** | none. Only the generic tokens `production` and `statistics` matched, and both are whole-file `in tex` constants whose counts are **invariant under a move within the same file**. |
| **tex 159 (the §IV `\ref` paragraph)** | `"not kernel-free, and every figure reported here is the kernel-applied"` (`:170`), `"kernel is retained in production"` (`:175`), `"not kernel-free"` (`:146`), `"fifty-seed mean"` (`tests/test_abstract_hedge_gate.py:55`). **None overlaps** `(Figure~\ref{fig:mc})` or `(Figure~\ref{fig:abmpaths})`; A3a/A3b insert bytes strictly inside the two parentheticals. |
| **tex 737 (B1's paragraph)** | `an interaction of $-1.47$ points`, `floor\_inference\_correction`, `84.0\% of weight imputed`, `$+2.9$ to $+8.7$ points`, `above the clean band`, `floor\_uncertainty`, `open below $+4.3$`, `$+3.0$ to $+8.0$`, `binding layer`, `form-conditional`, `sampling`. Of these, **only** `floor\_inference\_correction`, `$+2.9$ to $+8.7$ points` and `binding layer` fall inside B1's OLD — and all three are **reproduced verbatim in NEW**. |

### Named gates

| gate | rule | verdict |
| --- | --- | --- |
| **#100** `abm_lead_check` (`:817-832`, `ABM_LEAD_SPANS` `:544-563`) | Paragraph-scoped: `[ln for ln in tex.split("\n") if ln.startswith("This section is a stress test")]`, requires exactly 1 such line, 8 spans present, `60.2\%` before `no specification tested here explains`, plus `ve_declines` whole-file. | **SAFE.** The opener line is **tex 155**, not 159 and not the figure block. Lever (a) deletes and re-inserts *whole lines* elsewhere; it cannot change tex 155, the paragraph count, or the intra-line ordering. `ve_declines` is whole-file and untouched. Mirrored by `tests/test_abm_lead_gate.py:45`. |
| **#98** `assembly_check` / `ASSEMBLY_SPANS` (`:378-421`) | Paragraph-scoped on `A seventh qualification` = **tex 346**. Holds `posture_binding_layer` (`... floor reads' own sampling error, $+2.9$ to $+8.7$ points after wild-cluster correction`) and `ladder_agestd` (`floor read of 5.51\% implies a marginal near $+3.8$`) and `ladder_fannie` (`5.52\%, brackets the marginal below the $+4.3$ edge`). | **SAFE.** Tex 346 is in §V.E, a different section from B1's tex 737. Confirmed by reading tex 346's opening bytes. This is the coordinator's correction, verified independently. |
| **#101** letter freshness (`:587-602`) | `LETTER_CURRENT_LITERALS` must each still be `in tex`. | **SAFE.** `$+3.0$ to $+8.0$` 5→5, `$+2.9$ to $+8.7$` 8→8, `$-1.47$` unmoved, and the other nine literals are outside both regions. The letter file itself is not edited. |
| **#102** `ELASTICITY_DISCIPLINE_SPANS` (`:616-630`) | 7 whole-file spans. | **SAFE.** They live at tex 399, 400, 850, 1314 (`band\_low\_extension`, `tab:lowband`, the curve/bracket values and postures) — none in tex 159, 175–188, or 737. |
| **#104** `VERDICT_AUDIT_SPANS` (`:670-679`) | 6 whole-file spans. | **SAFE.** `tab:verdicts`/`app:verdicts` at tex 1407; the row and epistemic spans are in `app:verdicts`. No overlap. |
| **#105** `CONVOLVED_LINE_SPANS` (`:690-705`) | 7 whole-file spans incl. `$[+2.80, +8.99]$`, `layer\_convolution`, `independence is assumed, not measured`. | **SAFE.** Sites are tex 336, 445, 854, 1429. Not in either edit region. B1 changes no bracket form. |
| **#106** `COUPON_CONVENTION_SPANS` (`:708-720`) | 5 whole-file spans. | **SAFE.** `That is a mixed-basis measurement` is tex 721; the rest are in §VII.E/appendix. No overlap. |
| **#73** floor uncertainty (`:4437-4460`) | The **binding gate for lever (b)**: `>= 2`, `>= 4`, and five presence checks (see §2). | **SAFE by margin 3 and 4** on the two counted literals; the three at-risk presence literals are all preserved. **Zero-slack item: `84.0\% of weight imputed` count 1, outside B1's OLD.** |
| **#86** out-of-agency floor read (`:4188-4196`) | `"above the clean band" in tex`. | **SAFE.** 4 → 4; the tex 737 occurrence is in the untouched "Second," clause. |
| **#99 / #68** abstract | Ordering + 248-word count. | **SAFE.** The abstract (tex 30) is untouched by both levers. |
| **no-hardcoded-xref** (`:903-907`) | All five patterns must return 0. | **SAFE.** A3a/A3b add `Appendix~\ref{...}` (does not match `Appendix[~ ][AB]`); B1's NEW adds `Table~\ref{tab:ladder}` (does not match `Table[~ ]\d`). Verified by running the five regexes against each NEW string: all 0. |
| paragraph-scoped rules, exhaustively | `grep -n 'startswith(' tools/liveness_gates.py tests/*.py` | Only **two** manuscript openers exist in the whole suite: `ABM_LEAD_OPENER` (tex 155) and `ASSEMBLY_OPENER` (tex 346), plus the same two mirrored in `tests/test_abm_lead_gate.py:45`, `tests/test_assembled_corrections_gate.py:46`, `tests/test_headline_posture_gate.py:150`. **Neither opener is in any edit region**, so no paragraph-scoped rule can fire on either lever. |

**Net: zero gates affected. No gate, test, or letter edit is required by this package.**

---

## 5. Length saved

| lever | chars | words | printed effect |
| --- | ---: | ---: | --- |
| (a) A1 removes from §IV | −1,248 | −143 | **≈ 0.9 page out of the main text** — the saving is *float real estate*, not characters: `fig:abmpaths` ≈ 2.86in + ~0.75in caption, `fig:mc` ≈ 3.09in + ~0.9in caption, plus float separation ≈ **8.2in of a 9in text block**. Matches `DRAFT_WPE_sec3_sec4.md:411`'s "roughly one page". |
| (a) A2 re-inserts into the appendix | +1,248 | +143 | ≈ 0.9 page added to Appendix `sec:method-abm`. |
| (a) A3a + A3b | +58 | +4 | nil |
| **(a) net** | **+58** | **+4** | **main text ≈ 1 page shorter; total document length unchanged.** |
| (b) B1 | **−138** | **−23** | ≈ 1½ printed lines. |
| **package net** | **−80** | **−19** | **≈ 1 page moved from body to appendix; ~1½ lines removed outright.** |

**Stated plainly, because it is the thing most likely to be misread:** lever (a) does **not**
shorten the paper. It moves ~1 page from the body to the appendix. It is a *main-text* lever
and pays only against a main-text page budget (and it shifts the p.79/80 two-PDF split point
noted at `DRAFT_WPE_sec5_exhibits.md:106`, which must be recomputed). Lever (b) is a genuine
but small deletion — 138 chars — because, as `DRAFT_WPE_sec5_exhibits.md:526-529` warned, the
sentence is dense with counted literals and only the ladder recital is actually free.

---

## 6. Flags for the coordinator

**F1 — `paper/v18/revised_paper_v18_long_abstract.tex` is a near-clone and will silently
desync.** It differs from the manuscript by **exactly one line** (tex 30, the abstract) — a
4-line diff, total. Its tex 159/179/186 are byte-identical to the manuscript's, so **every OLD
string in this package matches it too**. The round-close commit message records "variant
compiles" as a checked property. **Decide explicitly whether to mirror A1/A2/A3a/A3b/B1 into
the variant.** No gate reads the variant (`LETTER`/`TEX` paths in `liveness_gates.py` point at
`revised_paper_v18.tex` only), so nothing will catch the drift.

**F2 — B1's NEW says `Webb wild-$t$` where the OLD said `wild-$t$`. This is a deliberate
accuracy repair; approve or reject it consciously.** The OLD sentence introduces the correction
as "a Rademacher wild-cluster bootstrap-$t$" and then reports "the wild-$t$ interval is $+2.9$
to $+8.7$ points" — but per `tab:ladder`, **Rademacher is $+2.8$ to $+8.7$ (tex 471) and Webb is
$+2.9$ to $+8.7$ (tex 472, "primary; the binding layer")**. The OLD therefore attributes the
Webb number to a Rademacher construction. Naming Webb fixes the seam and agrees with tex 452
("the Rademacher and Webb constructions land with both endpoints within a tenth of a point")
and tex 460 ("The Webb-weight wild-cluster bootstrap-$t$ is the primary construction"). **If
you would rather this package change nothing substantive, delete the word `Webb ` from NEW** —
the literal ledger is unaffected either way (`$+2.9$ to $+8.7$` is present in both forms).

**F3 — one unique clause is dropped by B1:** `with the percentile layer reproduced bit-exactly
as its parity gate`. Unpinned, but genuinely stated nowhere else. Restore it, if wanted, as
`(run \texttt{floor\_inference\_correction}; its percentile layer replays bit-exactly as a
parity gate)` — +56 chars, net cut still 82.

**F4 — the `[H]` cluster.** Keeping `[H]` puts three consecutive float-here figures (~10.6in)
into a 9in text block at tex 920, so expect one page break inside the cluster and possibly one
short page. Byte-identity was prioritized over packing; see A2 for the one-character
alternative.

**F5 — `TECHNICAL.md:2677` is already stale and gets staler.** It reads
"`fig10_abm_cpr_paths` (fig:abmpaths, §III.A)"; the figure is in §IV today and moves to the
appendix under this package. Out of scope here (tracked file, not a manuscript edit), flagged
so it can be swept with the other doc de-staling.

**F6 — A3a/A3b are optional.** `\ref` remains valid without them. Drop both if you judge the
third `sec:method-abm` mention in tex 159 to be one too many; gate-neutral either way.

**F7 — application order is load-bearing.** A1 before A2. If A2 lands first, A1's OLD is no
longer unique and the Edit will fail (or, worse, match the wrong copy).

---

## 7. Post-apply verification checklist

Exact commands and expected outputs. Run from the repo root.

### 7.1 Structural (lever a)

```sh
# each moved figure exists exactly once
grep -c 'fig10_abm_cpr_paths'          paper/v18/revised_paper_v18.tex   # 1
grep -c 'monte_carlo_trapped_liquidity' paper/v18/revised_paper_v18.tex  # 1
grep -c '\\label{fig:abmpaths}'         paper/v18/revised_paper_v18.tex  # 1
grep -c '\\label{fig:mc}'               paper/v18/revised_paper_v18.tex  # 1

# both labels now sit AFTER \appendix, and after fig:cprsurface
grep -n '\\appendix\|\\label{fig:cprsurface}\|\\label{fig:abmpaths}\|\\label{fig:mc}' \
     paper/v18/revised_paper_v18.tex
#  expected order: \appendix  <  fig:cprsurface  <  fig:abmpaths  <  fig:mc

# both refs survive, in tex 159, exactly once each
grep -c 'Figure~\\ref{fig:abmpaths}' paper/v18/revised_paper_v18.tex     # 1
grep -c 'Figure~\\ref{fig:mc}'       paper/v18/revised_paper_v18.tex     # 1

# §IV no longer holds them: no figure env between fig:waterfall and \subsection{Interpretation}
awk '/\\label{fig:waterfall}/,/sec:abm-interp/' paper/v18/revised_paper_v18.tex | \
  grep -c 'begin{figure}'                                                 # 0

# blank-line hygiene: no run of 3+ newlines introduced
python3 -c "import re;print(len(re.findall(r'\n{3,}',open('paper/v18/revised_paper_v18.tex').read())))"
#  must equal the pre-apply value (record it before applying; it was 9 at the last
#  measured checkpoint per DRAFT_WPE_sec3_sec4.md:492)

# file length: net +58 chars, +4 words, line count unchanged at 1435
wc -lwc paper/v18/revised_paper_v18.tex
```

### 7.2 Literal ledger (lever b) — the hard gate

```sh
python3 - <<'PY'
src = open('paper/v18/revised_paper_v18.tex').read()
want = {
  # literal                          : (expected_after, gate_minimum)
  "$+3.0$ to $+8.0$"                 : (5, 2),
  "$+2.9$ to $+8.7$"                 : (8, 4),
  "$+2.9$ to $+8.7$ points"          : (7, 1),
  "$+2.9$ and $+8.7$"                : (2, 1),   # AND-FORM
  "$[+2.9, +8.7]$"                   : (3, 0),   # BRACKET FORM
  "$[+3.0, +8.0]$"                   : (3, 0),   # BRACKET FORM
  "$[+2.80, +8.99]$"                 : (2, 1),   # gate #105
  "open below $+4.3$"                : (3, 1),
  "84.0\\% of weight imputed"        : (1, 1),   # ZERO SLACK
  "binding layer"                    : (10, 1),
  "floor\\_uncertainty"              : (4, 1),
  "floor\\_inference\\_correction"   : (8, 1),
  "above the clean band"             : (4, 1),
  "an interaction of $-1.47$ points" : (3, 1),
  "above zero on every corrected read": (1, 0),
  "$+3.0$ to $+8.6$"                 : (1, 0),   # falls 2->1, unpinned
  "$+2.8$ to $+8.8$"                 : (1, 0),   # falls 2->1, unpinned
  "$+2.8$ to $+8.7$"                 : (1, 0),   # Rademacher secondary, UNTOUCHED
  "Rademacher"                       : (3, 0),   # falls 4->3, unpinned
}
bad = 0
for lit,(exp,mn) in want.items():
    n = src.count(lit)
    flag = "OK " if (n == exp and n >= mn) else "BAD"
    if flag == "BAD": bad += 1
    print(f"{flag} {n:>3} (want {exp}, min {mn})  {lit!r}")
print("FAILURES:", bad)
PY
```

Expect `FAILURES: 0`.

### 7.3 Gate-rule string logic, re-implemented (no run artifacts needed)

```sh
python3 - <<'PY'
import re
src = open('paper/v18/revised_paper_v18.tex').read()
nc  = re.sub(r"(?<!\\)%.*", "", src)
# no-hardcoded-xref (liveness_gates.py:214-220) -- all five must be 0
pats = {"TableN":r"Table[~ ]\d","FigureN":r"Figure[~ ]\d",
        "SecRoman":r"Section[~ ][IVX]+(?:\.[A-Z])?(?![a-zA-Z}])",
        "AppAB":r"Appendix[~ ][AB](?![a-zA-Z}])","EqN":r"[Ee]quation[~ ]\(\d\)"}
for k,p in pats.items(): print(k, len(re.findall(p, nc)))
# gate #100 / #98 paragraph openers: exactly one line each
for op in ("This section is a stress test", "A seventh qualification"):
    print(repr(op), sum(1 for l in nc.split("\n") if l.startswith(op)))
# gate #73's five presence checks + two counts
print("g73:", nc.count("$+3.0$ to $+8.0$") >= 2, nc.count("$+2.9$ to $+8.7$") >= 4,
      "floor\\_uncertainty" in nc, "floor\\_inference\\_correction" in nc,
      "open below $+4.3$" in nc, "binding layer" in nc,
      "84.0\\% of weight imputed" in nc)
# label/ref integrity
labs = re.findall(r"\\label\{([^}]+)\}", nc); refs = set(re.findall(r"\\ref\{([^}]+)\}", nc))
print("dup labels:", [l for l in set(labs) if labs.count(l) > 1])
print("dangling refs:", sorted(refs - set(labs)))
PY
```

Expect: all five xref patterns `0`; both openers `1`; `g73` all `True`; no duplicate labels;
no dangling refs.

### 7.4 Suite + build

```sh
python tools/liveness_gates.py     # 106 gates, ALL PASS — no gate edit is required
pytest tests/ -q                   # 451 passed
```

Build (tectonic): **130pp, 0 undefined references, no `Figure ??` / `Table ??`.** Then check
by eye: (i) §IV runs `fig:recovery` → `fig:waterfall` → `\subsection{Interpretation}` with no
orphaned float gap; (ii) Appendix `sec:method-abm` runs `fig:cprsurface` → `fig:abmpaths` →
`fig:mc` → the payoff-rules paragraph, with the page break falling inside the float cluster
rather than orphaning a caption; (iii) the two §IV parentheticals print as
`(Figure~10, Appendix~B)`-style text with real numbers, not `??`.

**Also recompute:** the p.79/80 two-PDF split point (`DRAFT_WPE_sec5_exhibits.md:106`) — lever
(a) moves ~1 page across it.

### 7.5 Response letter

No edit required. `LETTER_CURRENT_LITERALS` (`liveness_gates.py:591-602`) are all still in the
manuscript at ≥ their prior counts (§2), the letter's current section (from tex 338) quotes no
figure number and no figure label, and gate #101's abstract word count does not move because
the abstract is untouched.
