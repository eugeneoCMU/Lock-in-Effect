# DRAFT — Round 32 Wave 2, cluster A (headline posture): C-17, C-19, C-67

Region: the abstract (line 31), Table 1 (`tab:headline`, lines 64--90) and the Introduction
(`\section{Introduction}` at line 38, ending at line 96; `Definitions used throughout` (92) and
`How to read this paper` (94) sit inside it).

Nothing in the worktree was modified and no repo script was executed. Every count below was measured
with `str.count` / `len(abstract.split())` on the canonical file and on the in-memory result of
applying the three edits in order. Applying all three changes **lines 31, 46 and 79 and no others**
(verified by a line-by-line diff of the in-memory result).

---

## DECISION NEEDED — C-17 (the posture)

C-17 offers two branches. They are not symmetric: one of them cannot be executed as a wording change
at all. I draft branch **B** and record branch A so Eugene can overrule.

**Branch A — drop the point, print only the range.**
- Cost 1: it is a gate rewrite, not a wording change. Gate #99's shipped rule
  (`tools/liveness_gates.py:505-519`) *requires* the point in the abstract:
  `ABSTRACT_POSTURE["point_named_inside"] = "Inside that range, $+5.6$ points, or \$42.6 billion, is
  the value at the calibration I headline"`, and the rule additionally asserts
  `abstract.find("$+2.9$ and $+8.7$") < abstract.find("$+5.6$ points")`, which is unsatisfiable once
  the point is gone. `tests/test_headline_posture_gate.py` then breaks in three places:
  `test_deleting_any_span_fails[point_named_inside]` inverts, the file's own load-bearing case
  `test_point_before_range_fails` (lines 71--92) loses its subject, and
  `test_shipped_manuscript_passes` goes red. Branch A means retiring the gate that exists to keep the
  point *named inside* the range — i.e. undoing round 24b/24c rather than completing it.
- Cost 2: `\$42.6 billion` is the only figure in the abstract that gives the paper's bottom line
  ("the institutional cash-flow cost is small") a magnitude. Without it the abstract states a
  points-range against a `\$764.7 billion` benchmark and no dollar figure for the object measured.
  It is also a disclosure — the reader's only way to know what the production configuration returns.
- Cost 3: 25 whole-file occurrences of `$+5.6$` propagate, including `tab:oosfloor`'s 4.99\% row and
  `tab:assembly`, where +5.6 is a cell of a measured table and not a framing choice.

**Branch B — keep the point, defend the anchor on a stated rule, withdraw the refusal. RECOMMENDED.**
+5.6 is not a point estimate and never was: it is the value the model returns at one calibration
(floor 4.991\%, $\delta = 6.5\%$) — a coordinate of the grid. The paper is already most of the way
here (T1: "an anchor convention rather than a central tendency"; §I: "it is the range and not that
value that the design delivers"; §VIII lines 731/737: "the value at the mid-grid anchor inside it").
Two things are missing, and both are inside my region:

1. **The anchor has never been defended, only labelled.** It is defensible on a rule that was fixed
   before the reads: 4.991\% is the *middle of the three pre-committed 2018 depth cuts*
   (`floor_inference_correction_v2_results.json`: R1 gap $\le 0$ = 5.334239649398553, R2 gap $\le
   -0.0025$ = 4.990624060575566, R3 gap $\le -0.005$ = 4.695495330057254), and R2 was named the
   primary object *ex ante* (that artifact's `spec`: "Reads R1-R4 (R5 excluded ex ante), primary
   object R2"). Stating that turns "anchor convention" from an epithet into a rule. Edit 3.
2. **The front matter never says what the point *is*.** Edit 1 says it: that calibration's
   coordinate, not a central tendency.

The incoherence X3 scored as "net negative" is local and identifiable, and it is not the printing of
+5.6. §V.E states a posture — "the headline sits just below that interval's midpoint, while every
correction listed above falls in its lower half and the uncomposed pair falls near its bottom" — and
then, one clause later, denies having one: "I attach no posture to where $+5.6$ sits among these
readings". Branch B keeps the true statement and withdraws the false refusal.

Branch B **moves no gate and no test.** Every pinned span survives byte-identically, verified below,
including `ASSEMBLY_SPANS["posture_retired_range_carries"]` — whose text ("no interior member is
privileged, and the range rather than any point is what the design delivers") *is* branch B's claim.

**Companion edit required outside my region.** §V.E (currently line 333) is a sibling drafter's
region, so I did not draft it as an edit block, but branch B is half-executed without it — which is
exactly the state X3 penalised:

```
OLD: I attach no posture to where $+5.6$ sits among these readings: with the downward specification variants lined up below beside the upward counterweights, no interior member is privileged, and the range rather than any point is what the design delivers
NEW: The posture I attach is about the mass, not the point: with the downward specification variants lined up below beside the upward counterweights, no interior member is privileged, and the range rather than any point is what the design delivers
```

`ASSEMBLY_SPANS["posture_retired_range_carries"]` begins at "no interior member is privileged" and is
preserved byte-identically; `ASSEMBLY_SPANS["ladder_headline"]` sits elsewhere on the same line and is
untouched; `tests/test_headline_posture_gate.py::test_abstract_posture_agrees_with_section_ve`
(line 153) checks the same span and still passes. That edit takes `$+5.6$` from 2 to 1 on line 333
and 25 to 24 whole-file.

---

## Edit 1 — the abstract states what the point is, and admits the composed cell (C-17, C-19)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
is the value at the calibration I headline, and every correction I can measure to the baseline turnover floor or to the accounting basis moves it down within the range rather than up.
NEW:
is the value at the calibration I headline---that calibration's coordinate, not a central tendency---and every correction I can measure to the baseline turnover floor or to the accounting basis moves it down within the range rather than up, two of them jointly to $+2.9$ points under a pre-committed rule: the range's lower endpoint by coincidence, not by construction.
RATIONALE: Branch B's posture, stated where readers take their posture from, plus C-19's promotion of
the measured composed cell (run `b5_joint_cell`) into the abstract as the assembly's operative lower
member. The clause after the colon is what keeps the abstract's two `$+2.9$`s from reading as one
number: the composed cell (2.9282) and the Webb lower endpoint (2.8550) print the same figure and are
unrelated objects. Nothing is softened — the sentence still says the point is the calibration's
value and that every measurable floor/basis correction moves it down; it now also says how far down
the two that were composed go.
LITERALS_INTRODUCED: one new `$+2.9$` occurrence =
`b5_joint_cell_results.json:adjudication.composed_pp = 2.928173869093058` (identically
`overlay_agestd.primary.marginal_pp`), `adjudication.verdict = "LANDS_AS_COMPOSED_LOWER_MEMBER"`,
`pre_committed = true`, `interaction_vs_proportional_pp = 0.00023293540786362144`. No other numeral
enters the abstract.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED:
- `ABSTRACT_POSTURE["point_named_inside"]` ends at "...the value at the calibration I headline" —
  preserved byte-identically (the em-dash follows it, unspaced).
- `ABSTRACT_POSTURE["corrections_framed"]` (the whole "every correction ... rather than up" span) —
  preserved byte-identically. `test_frame_dropped_from_the_corrections_claim_fails` still fires.
- Gate #99's ordering assert: re-measured on the result, `$+2.9$ and $+8.7$` at abstract offset 865
  precedes the first `$+5.6$ points` at 1386; `missing = []`, `ordered = True`.
- `test_benign_rewrites_stay_green` fixtures "however the rate-responsive margin behaves" and "The
  cost to households who could not move is real." are untouched (editing either makes that test fail
  as stale).

## Edit 2 — Table 1 row 4 carries the composed cell (C-19)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
an anchor convention rather than a central tendency; the range carries the identified content
NEW:
an anchor convention rather than a central tendency; the age-standardized floor read composed with the Ginnie-speed overlay, under a pre-committed landing rule (run \texttt{b5\_joint\_cell}), lands at $+2.9$ points, this interval's lower endpoint by coincidence and not by construction; the range carries the identified content
RATIONALE: C-19's first branch at the site it names. Row 4 named the interior +5.6 and no lower
member; it now names the one composition that was actually run, with both ingredients (already
present in T1's own apparatus: the 5.51\% age-standardized read in the definitions paragraph, the
Ginnie overlay $+4.4$ in note a) and with the numerical coincidence flagged in the same cell as the
interval it coincides with. The row's ordering is preserved: interval, then anchor, then composed
lower member, then the range-carries-the-content clause.
LITERALS_INTRODUCED: one new `$+2.9$` = `b5_joint_cell_results.json:adjudication.composed_pp =
2.928173869093058`; run tag `b5\_joint\_cell` 6 -> 7. The "age-standardized floor read" is the same
run's `agestd_floor_pct = 5.507748455937158` (printed as 5.51\% at line 92) and the "Ginnie-speed
overlay" its `committed_ratio_4991 = 0.7975182199226121` (printed as $0.797$ in §V.E and note a).
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none. `liveness_gates.py` and `tests/*.py` contain no occurrence of "anchor
convention", "mid-grid anchor" or "carries the identified content". The `\tnote{a}` marker and
note a's text are untouched, and the note stays in its post-float paragraph (round-31 convention —
not moved back into the float).

## Edit 3 — the design's resolution stated once, and the anchor's rule stated (C-67, C-17)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
which is the binding layer (Section~\ref{sec:robustness-floor}). The value at the mid-grid anchor inside that interval is $+5.6$ points
NEW:
which is the binding layer (Section~\ref{sec:robustness-floor}). Neither endpoint is resolved to the decimal I print it at: across the ten rungs that price that one layer the lower endpoint runs from $+2.3$ to $+3.2$ points and the upper from $+8.0$ to $+9.6$ (Table~\ref{tab:ladder}), while switching the bootstrap's weight scheme moves each by less than a tenth, so I read each endpoint as good to a few tenths rather than to the decimal it carries, and no argument here turns on a one-decimal difference between rungs. The value at the mid-grid anchor inside that interval---the middle of the three pre-committed 2018 depth cuts, and the read named primary before any of them ran---is $+5.6$ points
RATIONALE: C-67 asks for the resolution to be stated ONCE; §I is where the interval first appears at
one decimal, so a statement there governs every later quoting site (T1 row 4, T8, T9) without
repeating itself. Layer/rung discipline is respected: one layer (the floor read's own sampling
error), ten rungs pricing it. The four endpoint literals are printed cells of `tab:ladder`, so the
sentence adds no number a reader cannot check in the table it cites. The appositive supplies C-17's
missing half: the anchor is the middle of three pre-committed cuts, not a preference.
LITERALS_INTRODUCED: no numeral new to the file. `$+2.3$` 7 -> 8, `$+3.2$` 1 -> 2, `$+8.0$` 5 -> 6,
`$+9.6$` 2 -> 3, each an existing `tab:ladder` cell (`$+2.3$` = CR3--Bell-McCaffrey and restricted-
inversion lower ends; `$+3.2$` = CR1 $t$ lower end; `$+8.0$` = percentile upper; `$+9.6$` =
CR3--Bell-McCaffrey upper). Provenance for the spread claim,
`floor_inference_correction_v2_results.json:reads.R2_2018_gap<=-0.0025_age>=12` plus
`verdict.committed_percentile_pp`: widths 5.044 / 5.197 / 5.579 / 5.823 (Webb, primary) / 5.927 /
6.001 / 6.043 / 6.740 / 6.828 / 7.284; lower endpoints 2.2809--3.1532, uppers 8.0185--9.5645. "moves
each by less than a tenth" = `verdict.abs_delta_lower_pp = 0.0587`, `abs_delta_upper_pp = 0.0451`,
against `endpoint_tol_pp = 0.1` (Rademacher -> Webb) — the same fact `tab:ladder`'s note already
states in its own words ("land with both endpoints within a tenth of a point"). "The middle of the
three pre-committed 2018 depth cuts" = R1 5.334239649398553 / R2 4.990624060575566 / R3
4.695495330057254, median R2; "named primary before any of them ran" = that artifact's `spec`,
"Reads R1-R4 (R5 excluded ex ante), primary object R2".
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none. The `$+5.6$` in the OLD span is retained. The gate at
`liveness_gates.py:4617` requires `tex.count("$+2.9$ to $+8.7$") >= 4`: 8 before, 8 after.
`LETTER_CURRENT_LITERALS` (`:592-600`) requires `$+3.0$ to $+8.0$`, `$+2.9$ to $+8.7$`, `$+3.5$ to
$+13.1$`, `$-1.47$` etc. to remain in the manuscript — all present and untouched.

---

## CENSUS

`str.count` on the whole canonical file, before -> after all three edits.

| literal / pinned span | before | after |
|---|---|---|
| `$+2.9$` | 16 | 18 |
| `$+2.9$ to $+8.7$` | 8 | 8 |
| `$+5.6$` | 25 | 25 |
| `\$42.6 billion` | 3 | 3 |
| `$+42.6$` | 1 | 1 |
| `$+2.3$` | 7 | 8 |
| `$+3.2$` | 1 | 2 |
| `$+8.0$` | 5 | 6 |
| `$+9.6$` | 2 | 3 |
| `b5\_joint\_cell` | 6 | 7 |
| `by coincidence` | 1 | 3 |
| `Ginnie-speed overlay` | 4 | 5 |
| `pre-committed landing rule` | 3 | 4 |
| `pre-committed rule` | 0 | 1 |
| `depth cuts` | 2 | 3 |
| `mid-grid anchor` | 7 | 7 |
| `an anchor convention rather than a central tendency` | 1 | 1 |
| `the range carries the identified content` | 1 | 1 |
| `Inside that range, $+5.6$ points, or \$42.6 billion, is the value at the calibration I headline` | 1 | 1 |
| `every correction I can measure to the baseline turnover floor or to the accounting basis moves it down within the range rather than up` | 1 | 1 |
| `What lock-in itself adds is a range rather than a number` | 1 | 1 |
| `The design bounds it between $+2.9$ and $+8.7$ points` | 1 | 1 |
| `the floor read's sampling error at my central elasticity` | 1 | 1 |
| `a wild-cluster interval on 31 clusters; the percentile read under-covers` | 1 | 1 |
| `form-conditional hull of $+3.5$ to $+13.1$ points` | 1 | 1 |
| `itself read from realized, partly behavioral turnover` | 1 | 1 |
| `outside the window returns the headline $+5.6$` (ASSEMBLY) | 1 | 1 |
| `no interior member is privileged, and the range rather than any point is what the design delivers` | 1 | 1 |
| `The widest layer that does have a coverage property is the floor reads' own sampling error, $+2.9$ to $+8.7$ points after wild-cluster correction` | 1 | 1 |
| `run under a pre-committed landing rule (run \texttt{b5\_joint\_cell}) and measures $+2.9$ points` | 1 | 1 |

Rule re-runs on the in-memory result: `abstract_posture_check` -> `missing = []`, `ordered = True`;
`tex.count("$+2.9$ to $+8.7$") = 8`; lines changed = **[31, 46, 79]**.

---

## UNVERIFIED

1. **C-67's "0.06pp weight-scheme wobble"** appears nowhere in the .tex and I did not print it. What
   I verified is what I take the raiser to have meant: the *bootstrap* weight scheme
   (Rademacher -> Webb) moves the lower endpoint by 0.0587 and the upper by 0.0451 points
   (`floor_inference_correction_v2_results.json:verdict`). If R1 meant a *portfolio* weight scheme
   (UPB- vs count-weighted), that is a different object and Edit 3 does not address it. Confirm from
   R1's own source line.
2. **C-67's "credible to about half a point" is not supported as written**, so I did not draft it. At
   the headline read the ten rungs' lower endpoints span 0.87 points and their uppers 1.55 — "half a
   point" understates the disagreement. Edit 3 says "good to a few tenths" and prints the observed
   spread instead, which is both weaker per-endpoint and honest about the disagreement.
3. **`tab:ladder` does not disclose that its two widest rungs have a grid-truncated lower endpoint.**
   Verified: `cr3_t_interval_df_bm` and `wcr_inverted` both carry
   `lower_pp_edge.truncated_at_grid_edge = True`, both clipping at `mapped_at_pct = 6.0` (the floor
   grid's upper edge) to `marginal_pp = 2.2809`; every other rung is untruncated at both ends. The
   table prints both as `$+2.3$` unflagged. This bears on C-67 — a clipped endpoint cannot be
   compared at one decimal — but `tab:ladder` is §III, outside my region. Whoever holds C-18/C-20
   should draft it. Edit 3 quotes the clipped `$+2.3$` as the low end of the *observed* spread, which
   is a lower bound on the true spread and so stays true under any disclosure.
4. **`$+5.6$` circulation: I measure 25 whole-file occurrences; the inventory says 24 across 21
   lines.** One occurrence of difference, most likely a counting convention. Branch B leaves it at
   25 (24 after the §V.E companion edit), so nothing turns on it.
5. **Line 717's "centered at $+5.6$ points"** (§VI, outside my region) is the one remaining word a
   hostile reader can quote as a centrality claim. It is arithmetically true of the band it is
   attached to (`$+4.3$ to $+6.8$`, midpoint 5.55) and false of the sampling interval (midpoint
   5.79 — which is why §V.E says the headline "sits just below that interval's midpoint"). Under
   branch B I would leave it: it is a true statement about a named band, and deleting it would delete
   a disclosure. Coordinator's call.
6. **Response letter.** Gate #101 parses `taken it to (\d+) words` from
   `paper/v18/response_to_referees_round22.tex` and compares it to the live abstract count. That
   literal must become **319** or gate #101 goes red. I did not read or edit the letter.
7. **Long-abstract variant.** Edit 1 touches line 31, the only line where the two files differ, so it
   must be hand-mirrored rather than span-replaced. Edits 2 and 3 apply verbatim to both files.
8. **Not addressed by design.** C-17's fix names `$+5.6$` sites at §VIII (lines 731, 737). I read
   both: they already say "the value at the mid-grid anchor inside it" / "$+5.6$ at the mid-grid
   anchor inside it", which is branch B's own formulation, so no conclusion edit is needed and the
   abstract and conclusion will agree.

---

## WORD_COUNT_IMPACT

Edit 1 touches line 31. Abstract word count under gate #101's own rule
(`len(abstract.split())` on the comment-stripped text between `\begin{abstract}` and
`\end{abstract}`): **294 -> 319, delta +25.** Edits 2 and 3 do not touch line 31.

Composition of the +25: +5 for the posture aside (unspaced em-dashes, so "headline---that" and
"tendency---and" add no tokens of their own), +20 for the composed-cell clause and the gloss that
keeps its `$+2.9$` distinct from the interval's.

If +25 is too much, the cheapest trims in order of least damage: (a) `pre-committed rule` ->
nothing, i.e. "two of them jointly to $+2.9$ points: the range's lower endpoint by coincidence, not
by construction" (-4, drops the credential that makes the cell quotable); (b) drop ", not by
construction" (-4, weakens the de-conflation the clause exists for); (c) drop the posture aside
(-5, but then the abstract states branch B nowhere, which is most of C-17). I recommend none of the
three and would rather trim elsewhere in the abstract in a separate, deliberate pass.
