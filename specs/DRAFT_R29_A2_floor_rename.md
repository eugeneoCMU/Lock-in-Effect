# DRAFT — Round 29, WP-A2: global floor rename

**Status:** DRAFT for coordinator verification. Nothing in the repo was modified by the
drafting agent; every count below was re-derived from the working tree at
`claude/brave-shaw-b02840` (HEAD `6b10972`) and re-checked against an **in-memory**
simulation of the full edit package (no repo script was executed; `tools/liveness_gates.py`
was read and *parsed* with `ast`, never imported or run).

**Target name (plan literal):** `baseline turnover floor` (long form, unhyphenated).
**Short form (this draft's recommendation):** `turnover floor`.
**Reserved:** `involuntary` survives only in strictly-involuntary senses.

---

## 0. Headline numbers

| quantity | value |
|---|---|
| `involuntary` occurrences in `revised_paper_v18.tex` (case-insensitive) BEFORE | **90** (86 lowercase + `Involuntary floor` ×2 + `Involuntary Floor` ×1 + `INVOLUNTARY\_CPR\_ANNUAL` ×1) |
| …renamed away | **73** |
| …deliberately re-introduced | **2** (L91 mapping parenthetical; L240 `not a strictly involuntary component`) |
| …AFTER | **19** (all KEEP; enumerated in §1.3) |
| supporting edits that touch no `involuntary` token | **5** (P3b ×2, P3c ×2, C1 ×1) |
| `revised_paper_v18_long_abstract.tex` | **identical pair list, identical counts** (73 + 5) |
| gate span constants re-pinned | **2** |
| test literals re-pinned | **3** (+3 optional key/docstring renames) |
| abstract word count (gate #101 tokenizer) | **248 → 248, UNCHANGED** |
| letter word-count claim | **no edit forced** |
| figure scripts baking the old term | **none** |

---

## 1. Occurrence ledger

### 1.1 `paper/v18/revised_paper_v18.tex` — form census (re-derived)

Longest-match partition of all 90 occurrences (sums to 90):

| form | n | lines |
|---|---|---|
| `involuntary-turnover floor` | 25 | 30, 47, 51, 91, 201, 240, 301, 336, 552, 607, 665, 729, 745, 749, 751, 765, 918, 930, 932, 1042, 1064, 1092, 1327, 1329 |
| `involuntary floor` | 25 | 91, 109×3, 149, 191, 216, 274, 336×2, 607, 638, 640, 749, 751, 755, 765, 797, 882, 1319, 1329, 1351, 1361, 1375 |
| (unclassified / bespoke) | 12 | 86, 276×2, 282, 607, 669, 733×3, 1012, 1357, 1369 |
| `strictly-involuntary` | 6 | 91, 240, 336, 733, 851 |
| `involuntary turnover` (standalone) | 6 | 191, 263, 276×2, 607, 1319 |
| `baseline involuntary turnover` | 5 | 30, 43, 59, 109, 566 |
| `involuntary-floor` | 3 | 791, 865, 879 |
| `strictly involuntary` | 2 | 91, 240 |
| `Involuntary floor` | 2 | 221, 1000 |
| `involuntary turnover floor` (unhyphenated) | 1 | 51 |
| `involuntary-turnover-floor` (fully hyphenated) | 1 | 295 |
| `Involuntary Floor` | 1 | 1349 (section title) |
| `INVOLUNTARY\_CPR\_ANNUAL` | 1 | 1353 |

> Note vs. the brief's census: the brief's "`involuntary-turnover` not followed by ` floor` ×1"
> is L295 `involuntary-turnover-floor grid`; the brief's "standalone `involuntary turnover` ~×6"
> is exactly 6. Both confirmed. Total `involuntary-turnover` = 26 = 25 + 1.

### 1.2 RENAME classification (73 sites)

| id | sites | disposition |
|---|---|---|
| P1 | 5 | `baseline involuntary turnover` → `baseline turnover` (the paper already uses bare "baseline turnover" for this object at L240/244/745/755) |
| P2 | 2 | `an involuntary-turnover floor` → `a baseline turnover floor` (**article change**, L201, L745) |
| P3 | 23 | `involuntary-turnover floor` → `baseline turnover floor` |
| P4 | 1 | `involuntary turnover floor` → `baseline turnover floor` (L51) |
| P5 | 1 | `involuntary-turnover-floor` → `baseline-turnover-floor` (L295, attributive before "grid") |
| P6 | 4 | `an involuntary floor` → `a turnover floor` (**article change**, L109 ×3, L1319) |
| P7 | 21 | `involuntary floor` → `turnover floor` |
| P8 | 2 | `Involuntary floor` → `Turnover floor` (table rows L221, L1000) |
| P9 | 1 | `Involuntary Floor` → `Turnover Floor` (section title L1349) |
| P10 | 3 | `involuntary-floor` → `turnover-floor` (L791, L865, L879) |
| P11a–e | 5 | standalone `involuntary turnover` → `baseline turnover`, per-site (L191, L263, L276 ×2, L607) |
| P12b–f | 5 | bespoke: `involuntary semantics`→`semantics`; `involuntary band`→`turnover band`; `involuntary tail`→`turnover tail`; `the involuntary and voluntary hazards`→`the floor and the voluntary hazard`; `this involuntary profile`→`this floor profile` |
| P12a | 1 | `the floor's involuntary share` → `the floor's **strictly-**involuntary share` (L86) — the token survives, the site is fixed |
| R1, R2 | 0 | the two definitional recasts (L91, L240) run on already-renamed text and consume no occurrence; each **adds one back** — R1 the mapping parenthetical `(sometimes called an involuntary-turnover floor)`, R2 the phrase `not a strictly involuntary component of it` |

Arithmetic: 5+2+23+1+1+4+21+2+1+3+5+5+1 = **73** occurrences consumed by the mechanical/bespoke
pairs (P12a's 1 is consumed but re-emitted with a `strictly-` prefix, so it is a KEEP site in §1.3).
R1 and R2 add 2 back. Net **90 − 73 + 2 = 19** residual — matches the measured post-apply count.
P3b, P3c and C1 consume no `involuntary` occurrence at all.

### 1.3 KEEP ledger — the 19 surviving `involuntary` tokens (post-apply, verified)

| line | surviving text | reason |
|---|---|---|
| 86 | `mixture curve in the floor's strictly-involuntary share` | strictly-involuntary share (P12a made this explicit) |
| 91 | `` (sometimes called an involuntary-turnover floor) `` | **deliberate**: the one term-mapping parenthetical, first definition site |
| 91 | `…cash-out refinancings with strictly involuntary events` | strictly-involuntary events |
| 91 | `the strictly-involuntary share is plausibly well under half` | strictly-involuntary share |
| 240 | `not a strictly involuntary component of it` | R2's new wording; strictly-involuntary sense |
| 240 | `alongside strictly involuntary events` | strictly-involuntary events |
| 240 | `the strictly-involuntary share---death, divorce, and forced relocation---` | strictly-involuntary share |
| 240 | `not consequences of a strictly-involuntary decomposition` | strictly-involuntary decomposition |
| 276 | `to the extent that involuntary moves are themselves suppressed` | genuinely involuntary moves (death/divorce/relocation) co-varying with the cycle |
| 276 | `a clean voluntary-versus-involuntary decomposition` | the decomposition the design declines |
| 282 | `the involuntary buyout channel (CDR 2.1\% versus 0.4\%…)` | Ginnie buyout channel — strictly involuntary by construction |
| 336 | `a measured mixture curve in the floor's strictly-involuntary share` | strictly-involuntary share |
| 733 | `under which involuntary and voluntary hazards add` | the **additive** form's own premise is that the floor is an independent involuntary competing cause; the paragraph makes it explicit via `$s$` |
| 733 | `adding a 4\% involuntary hazard to moderate voluntary hazards` | same additive-form premise |
| 733 | `entering as an additive competing involuntary cause` | `$s$` is *defined* as the strictly-involuntary share |
| 733 | `the strictly-involuntary share is plausibly well under half` | strictly-involuntary share |
| 851 | `a measured curve in its strictly-involuntary share` | run-registry description of `floor\_form\_mixture` |
| 1319 | `A floor meant to capture involuntary turnover---death, divorce, relocation---should be approximately flat in loan age` | the age-flatness diagnostic reasons **from** the strictly-involuntary core; glossed in place. **FLAGGED — see §6.3** |
| 1353 | `\texttt{INVOLUNTARY\_CPR\_ANNUAL}` | code identifier in `hazard/config.py`; renaming it is run-class |

### 1.4 `paper/v18/revised_paper_v18_long_abstract.tex`

Verified byte-identical to the canonical file except line 30 (both before and after the rename).
Line 30 carries exactly 2 occurrences:

* `…because scheduled amortization and baseline involuntary turnover undershoot a \$35 billion monthly cap…` — consumed by **P1** (the replace-all count of 5 covers it).
* `Re-anchoring the involuntary-turnover floor that dominates the level outside the evaluation window…` — consumed by **P3** (the count of 23 covers it).

**Therefore the variant needs NO separate pair list.** Apply the *identical ordered pair list*
with the *identical expected counts*; simulation confirms the post-apply files differ at line 30
only, and the gate-C4 "variant differs from canonical in the abstract line only" check still passes.

### 1.5 `tools/liveness_gates.py`

| line | text | class |
|---|---|---|
| 268 | comment `# the null's recovery rests on amortization AND baseline involuntary turnover` | comment — follow for hygiene |
| 269–270 | `ABSTRACT_HEDGES["null_mechanical_components"]` span | **RE-PIN (required)** |
| 476–478 | `ABSTRACT_POSTURE["corrections_framed"]` span | **RE-PIN (required)** |
| 1555 | comment `# Panel revision (gate #56): out-of-window involuntary-turnover floor anchor —` | comment |
| 1646 | comment `# Panel revision (gate #58): seasonalized involuntary floor and the timing` | comment |
| 4548 | comment `# the ABM's involuntary floor is not a term in its move rule, it is PRODUCED by` | comment |

**Whole-file sweep for anything else that would fire.** An `ast.parse` walk over every string
constant in the file (parse, not import) returns exactly the two spans above as the only literals
containing `involuntary`. Cross-checked in the other direction: every string literal in
`tools/liveness_gates.py` and `tests/*.py` that is currently a substring of the canonical `.tex`
was tested against the post-rename `.tex`; **exactly four break**, all four intended (§3).
Additionally verified against the post-rename text:

* `ZERO_COUNT` — none of the 19 phrases appears (still 0 hits each). In particular
  `"that band presupposed an empirically admissible turnover level"` is unaffected.
* `EXACTLY_ONE` — all 4 phrases still count exactly 1.
* `LETTER_CURRENT_LITERALS` — all 16 literals still present in the manuscript.
* `HARDCODED_XREF`, `SHARE_LITERALS`, `LEDGER_REQUIRED`, `KERNEL_TEX_PHRASE`, `FIGURE_FORBIDDEN`,
  `SUPERSEDED_CONTEXTUAL` — numeric or unrelated; no overlap with any rename site.
* Gate #98 `ASSEMBLY_SPANS` / `ASSEMBLY_TABLE_SPANS`, gate #100 `ABM_LEAD_SPANS`,
  gate #102 `ELASTICITY_DISCIPLINE_SPANS`, `BUYBACK_BRACKET_SPANS`, `VERDICT_AUDIT_SPANS`,
  `CONVOLVED_LINE_SPANS` — **no overlap** with any rename site (confirmed by the substring sweep).
* No regex in the file matches on floor/turnover wording (the only text-extracting regexes are
  the comment stripper `(?<!\\)%.*` and `taken it to (\d+) words`).

### 1.6 `tests/`

| file:line | text | class |
|---|---|---|
| `test_abstract_hedge_gate.py:58` | `HANDOFF_PHRASES` entry `"baseline involuntary turnover"` | **RE-PIN (required)** — the test asserts this phrase is a substring of some gated span |
| `test_abstract_hedge_gate.py:123` | mutation key `"drops_involuntary_turnover"` | optional rename (must move with :149) |
| `test_abstract_hedge_gate.py:124` | mutation source string | **RE-PIN (required)** — otherwise `.replace()` is a no-op and the mutation test stops testing |
| `test_abstract_hedge_gate.py:149` | `MUTATION_NAMES` entry `"drops_involuntary_turnover"` | optional rename (paired with :123) |
| `test_headline_posture_gate.py:75` | reordered-abstract mutation string | **RE-PIN (required)** — the test asserts `info["missing"] == []`, so the mutation must carry the *new* `corrections_framed` span |
| `test_headline_posture_gate.py:86` | (same string, continuation line) | part of the same literal |
| `test_headline_posture_gate.py:96` | docstring quoting the span | comment/docstring — follow |
| `test_floor_cyclical.py:4` | module docstring `"the constant 4% involuntary-turnover floor"` | docstring — follow |
| `test_floor_cyclical_law.py:54` | trailing comment `# 4% annual involuntary CPR` | comment — follow |
| `test_floor_cyclical_law.py:128` | docstring `"kappa > 0 means involuntary turnover RISES"` | docstring — follow |
| `test_units_conventions.py:43` | `from config import INVOLUNTARY_CPR_ANNUAL` | **KEEP** — code identifier |
| `test_units_conventions.py:73` | comment `# involuntary floor, so the ratio is…` | comment — follow |

`test_response_letter_gate.py` has no `involuntary` site and needs **no edit** (see §4).

### 1.7 `paper/v18/response_to_referees_round22.tex`

`LETTER_CURRENT_SECTION = "\section{Changes since this response was drafted}"` is at **line 338**.

| line | text | disposition |
|---|---|---|
| 79 | `involuntary floor retained: \texttt{competing\_risks.py} passes a zeroed rate gap` | **DO NOT TOUCH** — before line 338, frozen history |
| 383 | `involuntary floor is not a term in its move rule at all but a \emph{product} of it,` | **RENAME → `turnover floor`** — inside the current section, present tense, mirrors tex L191 |
| 523 | `involuntary floor in 68.8\% of evaluated loan-months, against 36.3\% at the in-sample` | **RENAME → `turnover floor`** — inside the current section, mirrors tex L336 |

Gate #101's letter rule is three narrow checks: (a) the retired hull literal only inside its
historical marker, (b) the stated abstract word count equals the recomputed one, (c) every
`LETTER_CURRENT_LITERALS` entry appears in `current` **and** in the manuscript. **None of the three
is phrase-sensitive to the rename**, so 383/523 are consistency edits, not gate-forced ones. They
are still recommended: the current section speaks in the present tense about the manuscript, and
leaving `involuntary floor` there re-introduces the exact label the panel flagged, in the document
the referees read.

---

## 2. Count-asserted OLD/NEW pairs, in application order

Apply to **both** `paper/v18/revised_paper_v18.tex` and
`paper/v18/revised_paper_v18_long_abstract.tex` with the **same expected counts**.
Order matters where noted. All strings are exact LaTeX (`\%` is a literal backslash-percent
in the file; `` `` `` / `` '' `` are the TeX quote pairs).

### 2.1 Mechanical replace-all pairs (count-asserted)

| # | OLD | NEW | n |
|---|---|---|---|
| **P1** | `baseline involuntary turnover` | `baseline turnover` | **5** |
| **P2** | `an involuntary-turnover floor` | `a baseline turnover floor` | **2** |
| **P3** | `involuntary-turnover floor` | `baseline turnover floor` | **23** |
| **P3b** | `the seasoning baseline, and the baseline turnover floor` | `the seasoning baseline, and the turnover floor` | **2** |
| **P3c** | `the 4\% baseline turnover floor both frameworks impose` | `the 4\% turnover floor both frameworks impose` | **2** |
| **P4** | `involuntary turnover floor` | `baseline turnover floor` | **1** |
| **P5** | `involuntary-turnover-floor` | `baseline-turnover-floor` | **1** |
| **P6** | `an involuntary floor` | `a turnover floor` | **4** |
| **P7** | `involuntary floor` | `turnover floor` | **21** |
| **P8** | `Involuntary floor` | `Turnover floor` | **2** |
| **P9** | `Involuntary Floor` | `Turnover Floor` | **1** |
| **P10** | `involuntary-floor` | `turnover-floor` | **3** |

Ordering constraints (all verified by simulation):

* **P1 before P11\*** — otherwise the standalone-`involuntary turnover` pairs would collide with the
  `baseline`-prefixed ones.
* **P2 before P3**, **P6 before P7** — the article fix must consume its sites first; otherwise the
  determiner is left wrong (`an baseline turnover floor` / `an turnover floor`).
* **P3 before P3b and P3c** — P3b/P3c operate on already-renamed text (collision repairs, §6.1).
* P4/P5/P8/P9/P10 are order-independent (disjoint strings).

Sites for the two article pairs, for the coordinator's spot check:
**P2** = L201 (`proportional above an involuntary-turnover floor`), L745
(`both are anchored to an involuntary-turnover floor read off discount-cohort turnover`).
**P6** = L109 ×3 (`plus an involuntary floor calibrated from`, `at an involuntary floor measured off`,
`and an involuntary floor read from realized`), L1319 (`not an involuntary floor`, itself further
edited by P12g below).

### 2.2 Anchored single-occurrence pairs — standalone `involuntary turnover` (n=1 each)

| # | line | OLD | NEW |
|---|---|---|---|
| **P11a** | 191 | `anchored to observed involuntary turnover and lands at 85.7` | `anchored to observed baseline turnover and lands at 85.7` |
| **P11b** | 263 | `4\% annual CPR (involuntary turnover)` | `4\% annual CPR (baseline turnover)` |
| **P11c** | 276 | `the specification treats involuntary turnover as acyclical` | `the specification treats baseline turnover as acyclical` |
| **P11d** | 276 | `is in-window involuntary turnover that the off-window floor` | `is in-window baseline turnover that the off-window floor` |
| **P11e** | 607 | `treats involuntary turnover and rate-elastic moving as separable` | `treats baseline turnover and rate-elastic moving as separable` |

The sixth standalone site (L1319) is a **KEEP** — see §1.3 and §6.3.

### 2.3 Anchored single-occurrence pairs — bespoke sites (n=1 each)

| # | line | OLD | NEW | rationale |
|---|---|---|---|---|
| **P12a** | 86 | `mixture curve in the floor's involuntary share` | `mixture curve in the floor's strictly-involuntary share` | matches L336 and L851, which already say "strictly-involuntary share" for the same object; bare "involuntary share" is now ambiguous |
| **P12b** | 607 | `motivated by the floor's involuntary semantics` | `motivated by the floor's semantics` | L240 already uses the bare form ("Where the floor's semantics do institutional work"); keeping "involuntary" here would restate the retired claim |
| **P12c** | 669 | `inside the observed 4--5\% involuntary band` | `inside the observed 4--5\% turnover band` | the empirical 4–5% band is a turnover band |
| **P12d** | 1012 | `so the involuntary tail sets a natural floor` | `so the turnover tail sets a natural floor` | ABM appendix; the object is the residual turnover tail |
| **P12e** | 1357 | `Production combines the involuntary and voluntary hazards by a hard maximum` | `Production combines the floor and the voluntary hazard by a hard maximum` | this is the **max** form, where the floor is a floor on total turnover, not a competing involuntary cause; the L733 additive-form sentences are KEEP for exactly the opposite reason |
| **P12f** | 1369 | `Fourth, this involuntary profile peaks in June` | `Fourth, this floor profile peaks in June` | the contrast with `\emph{voluntary}` later in the sentence is preserved and now reads floor-vs-voluntary |
| **P12g** | 1319 | `a refinancing-inflated composite, not a turnover floor,` | `a refinancing-inflated composite, not a baseline turnover read,` | **runs after P6/P7.** A bare "not a turnover floor" would blunt the claim: the point is that the pooled 6.1% is not an admissible *read* of the floor, and under the new name the floor does include cash-out refi, so "read" is the accurate noun |

### 2.4 Recast definitional sentences (apply AFTER §2.1–2.3)

Both anchors below are stated in **post-mechanical** form (i.e. after P3 has already turned the
old label into `baseline turnover floor`). Each occurs exactly once. Verified: **zero numeric
literals change** in either sentence.

#### R1 — tex line 91, first definition site

OLD (post-P3):
```
The ``baseline turnover floor'' label is a modeling reading of that measured object rather than a decomposition of it: what these reads measure
```

NEW:
```
The ``baseline turnover floor'' (sometimes called an involuntary-turnover floor) names that measured object without decomposing it: what these reads measure
```

Everything after `what these reads measure` is **untouched**, so clauses (i) and (ii) survive
byte-identically:
`…is total deep-discount-cohort turnover, which mixes discretionary life-cycle moves and cash-out
refinancings with strictly involuntary events, and the strictly-involuntary share is plausibly well
under half (Section~\ref{sec:pathb}), a share the mixture curve of
Section~\ref{sec:robustness-floor} prices directly.`

Job flip: the sentence no longer apologises for a label ("is a modeling reading … rather than a
decomposition"); it says the name is literal ("names that measured object without decomposing it"),
carries the (iii) term mapping in the parenthetical, and hands off to the unchanged content and
share clauses. Hedge scope untouched: `plausibly well under half` and its `(Section~\ref{sec:pathb})`
scope are not in the edited span.

Rendered result (verified from the simulation):
```
…is the soft one (Section~\ref{sec:robustness-floor}). The ``baseline turnover floor'' (sometimes called an involuntary-turnover floor) names that measured object without decomposing it: what these reads measure is total deep-discount-cohort turnover, which mixes discretionary life-cycle moves and cash-out refinancings with strictly involuntary events, and the strictly-involuntary share is plausibly well under half (Section~\ref{sec:pathb}), a share the mixture curve of Section~\ref{sec:robustness-floor} prices directly.
```

#### R2 — tex line 240, Path B specification

OLD (post-P3):
```
$\underline{h} = 1-(1-0.04)^{1/12} \approx 0.0034$, representing death, divorce, and forced relocation. That label is a modeling reading, not a measured decomposition: deep-discount-cohort turnover at this level includes discretionary life-cycle moves and cash-out refinancings alongside strictly involuntary events, no component decomposition exists in this design, and the strictly-involuntary share is plausibly well under half.
```

NEW:
```
$\underline{h} = 1-(1-0.04)^{1/12} \approx 0.0034$. It floors total turnover, not a strictly involuntary component of it: deep-discount-cohort turnover at this level includes discretionary life-cycle moves and cash-out refinancings alongside strictly involuntary events, no component decomposition exists in this design, and the strictly-involuntary share---death, divorce, and forced relocation---is plausibly well under half.
```

What moved and why:

* `representing death, divorce, and forced relocation` was a gloss on the *whole* floor; under the
  literal name that gloss is wrong. The same six words are **retained verbatim** as an em-dash gloss
  on `the strictly-involuntary share`, which is what they actually describe. No words invented, none
  lost. Em-dash convention `---` with no surrounding spaces, matching the same line's
  `institutional work---selecting`.
* `That label is a modeling reading, not a measured decomposition:` → `It floors total turnover, not
  a strictly involuntary component of it:` — the apology becomes the positive statement of content
  (i), keeping the same `X, not Y:` shape and the same colon hand-off to the three unchanged clauses.
* Numeric literals `4\%`, `$\underline{h} = 1-(1-0.04)^{1/12} \approx 0.0034$` are outside the edited
  region on the left and preserved byte-identically.
* Hedge scope: `plausibly well under half` still scopes only to `the strictly-involuntary share`;
  the em-dash gloss is inside the same noun phrase and does not widen it.

The following sentence (`Where the floor's semantics do institutional work---selecting the
U.S.-intercept Danish anchor…the operative premise is only that baseline turnover cannot fall below
its observed deep-discount level when the payoff rule changes, which the total-turnover reading
supports`) is **unchanged** and now reads as direct support for the new name — it already says
"baseline turnover".

### 2.5 Collision mitigation (see §6.1)

| # | line | OLD | NEW | n |
|---|---|---|---|---|
| **C1** | 240 | `The baseline hazard follows the 100~PSA seasoning ramp` | `The baseline hazard $h_0$ follows the 100~PSA seasoning ramp` | **1** |

### 2.6 Letter pairs (`paper/v18/response_to_referees_round22.tex`)

| # | line | OLD | NEW | n |
|---|---|---|---|---|
| **L1** | 383 | `involuntary floor is not a term in its move rule at all but a \emph{product} of it,` | `turnover floor is not a term in its move rule at all but a \emph{product} of it,` | 1 |
| **L2** | 523 | `involuntary floor in 68.8\% of evaluated loan-months, against 36.3\% at the in-sample` | `turnover floor in 68.8\% of evaluated loan-months, against 36.3\% at the in-sample` | 1 |

Line 79 must remain untouched; after L1/L2 the letter's `involuntary` count is **exactly 1**, at
line 79, inside the frozen §1–§6.

**Optional (needs Eugene):** one sentence in the current section recording the rename, e.g. after
the §7 paragraph that discusses the floor. It introduces no numeric literal, so gate #101(c) is
unaffected:
```
The floor is now named for what it measures. ``Involuntary-turnover floor'' overstated the
decomposition, and the manuscript now calls it the baseline turnover floor throughout, with the
strictly-involuntary share treated as the unidentified quantity it is.
```

---

## 3. Pinned-span re-pin table

All four are the *only* literals in `tools/liveness_gates.py` + `tests/*.py` that are substrings of
the current `.tex` and cease to be substrings of the renamed `.tex` (exhaustive `ast` sweep).

| file:line | constant | OLD | NEW |
|---|---|---|---|
| `tools/liveness_gates.py:269-270` | `ABSTRACT_HEDGES["null_mechanical_components"]` | `"scheduled amortization and baseline "` `"involuntary turnover"` | `"scheduled amortization and baseline turnover"` |
| `tools/liveness_gates.py:476-478` | `ABSTRACT_POSTURE["corrections_framed"]` | `"every correction I can measure to the involuntary-turnover floor "` `"or to the accounting basis moves it down within the range rather "` `"than up"` | `"every correction I can measure to the baseline turnover floor "` `"or to the accounting basis moves it down within the range rather "` `"than up"` |
| `tests/test_abstract_hedge_gate.py:58` | `HANDOFF_PHRASES` entry | `"baseline involuntary turnover",` | `"baseline turnover",` |
| `tests/test_abstract_hedge_gate.py:124` | `"drops_involuntary_turnover"` mutation source | `"scheduled amortization and baseline involuntary turnover (itself "` `"read from realized, partly behavioral turnover) fall short"` | `"scheduled amortization and baseline turnover (itself "` `"read from realized, partly behavioral turnover) fall short"` |
| `tests/test_headline_posture_gate.py:75` | reordered-abstract mutation, opener | `" \\noindent Baseline involuntary turnover (itself read from realized, "` | `" \\noindent Baseline turnover (itself read from realized, "` |
| `tests/test_headline_posture_gate.py:86` | same literal, corrections clause | `"measure to the involuntary-turnover floor or to the accounting basis "` | `"measure to the baseline turnover floor or to the accounting basis "` |

`test_headline_posture_gate.py:75/86` is one literal spanning both lines; it is **not** a substring
of the tex (it is a synthetic reordering), which is why the substring sweep does not surface it —
but `test_point_before_range_fails` asserts `info["missing"] == []`, so if the mutation does not
carry the *new* `corrections_framed` span the test fails on the wrong assertion. Required.

`tests/test_headline_posture_gate.py:100-102` uses `ABSTRACT_POSTURE["corrections_framed"]` by
reference and **follows automatically** — no edit.

### Comment / docstring hygiene (not gate-bearing, recommended in the same commit)

| file:line | change |
|---|---|
| `tools/liveness_gates.py:268` | `…AND baseline involuntary turnover` → `…AND baseline turnover` |
| `tools/liveness_gates.py:1555` | `out-of-window involuntary-turnover floor anchor` → `out-of-window baseline turnover floor anchor` |
| `tools/liveness_gates.py:1646` | `seasonalized involuntary floor` → `seasonalized turnover floor` |
| `tools/liveness_gates.py:4548` | `the ABM's involuntary floor is not a term` → `the ABM's turnover floor is not a term` |
| `tests/test_abstract_hedge_gate.py:123,149` | mutation key `drops_involuntary_turnover` → `drops_baseline_turnover` (**both lines together**, or neither — `test_mutation_list_matches_definitions` compares the two) |
| `tests/test_headline_posture_gate.py:96` | docstring `` `to the involuntary-turnover floor or to the accounting basis` `` → `` `to the baseline turnover floor or to the accounting basis` `` |
| `tests/test_floor_cyclical.py:4` | `the constant 4% involuntary-turnover floor` → `the constant 4% baseline turnover floor` |
| `tests/test_floor_cyclical_law.py:54` | `# 4% annual involuntary CPR` → `# 4% annual baseline-turnover CPR` |
| `tests/test_floor_cyclical_law.py:128` | `kappa > 0 means involuntary turnover RISES` → `kappa > 0 means baseline turnover RISES` |
| `tests/test_units_conventions.py:73` | `# involuntary floor, so the ratio…` → `# turnover floor, so the ratio…` |

`tests/test_units_conventions.py:43,76` (`INVOLUNTARY_CPR_ANNUAL`) — **KEEP**, code identifier.

---

## 4. Abstract word count derivation

**Gate:** `#101`, `letter_check()` at `tools/liveness_gates.py:792`.
**Extraction (replicated by inspection, not executed):**

1. `tex_nc = re.sub(r"(?<!\\)%.*", "", tex)` — strip unescaped `%` comments.
2. `_i = tex_nc.find("\\begin{abstract}")`, `_j = tex_nc.find("\\end{abstract}", _i+1)`.
3. `abstract = tex_nc[_i + len("\\begin{abstract}"):_j]`.
4. **`words = len(abstract.split())`** — plain whitespace split (`abstract_hedge_check`,
   `tools/liveness_gates.py:875`). No LaTeX stripping: `\noindent` and `\par` each count as a word,
   and any hyphenated compound counts as **one** token.
5. `letter_check` compares `int(re.findall(r"taken it to (\d+) words", letter)[0])` to that number.

**OLD count: 248.** The two abstract tokens containing `involuntary` are at split-indices 77 and 193:

```
[..., 'amortization', 'and', 'baseline', 'involuntary', 'turnover', '(itself', 'read', ...]
[..., 'measure',      'to',  'the',      'involuntary-turnover', 'floor', 'or', 'to', ...]
```

**Per-edit delta under `str.split()`:**

| edit | old tokens | new tokens | Δ |
|---|---|---|---|
| P1 at index 77 | `baseline` `involuntary` `turnover` = 3 | `baseline` `turnover` = 2 | **−1** |
| P3 at index 193 | `involuntary-turnover` `floor` = 2 (the hyphen is not whitespace) | `baseline` `turnover` `floor` = 3 | **+1** |

**Net delta 0. NEW count: 248.** Confirmed by re-running the replicated tokenizer over the
post-rename text.

**Consequences:**

* `paper/v18/response_to_referees_round22.tex:328` — `have taken it to 248 words` **stays as is**.
  No letter edit is forced by the word count.
* `tests/test_response_letter_gate.py:104` — the wrong-count list
  `["263","328","341","352","359","366","367","280","424","226","235"]` **stays as is**. 248 does
  **not** join it; 248 remains the true count.
* No test asserts the abstract word count as a literal other than through the letter string.

**Long-abstract variant:** 572 → 572 words by the same arithmetic (P1 −1 at
`baseline involuntary turnover undershoot`, P3 +1 at `Re-anchoring the involuntary-turnover
floor`). No gate reads the variant's word count (only `abstract_hedge_check`'s `words > 150` guard,
which is satisfied), but the invariance is worth recording.

---

## 5. Post-apply verification checklist

### 5.1 Counts that must be ZERO (both `.tex` files)

```
grep -o "involuntary floor"           paper/v18/revised_paper_v18.tex | wc -l   # 0
grep -o "Involuntary floor"           paper/v18/revised_paper_v18.tex | wc -l   # 0
grep -o "Involuntary Floor"           paper/v18/revised_paper_v18.tex | wc -l   # 0
grep -o "involuntary-floor"           paper/v18/revised_paper_v18.tex | wc -l   # 0
grep -o "involuntary turnover floor"  paper/v18/revised_paper_v18.tex | wc -l   # 0
grep -o "involuntary-turnover-floor"  paper/v18/revised_paper_v18.tex | wc -l   # 0
grep -o "baseline involuntary"        paper/v18/revised_paper_v18.tex | wc -l   # 0
grep -oE "an [Bb]aseline|an turnover|a involuntary" paper/v18/revised_paper_v18.tex | wc -l  # 0
```
Repeat all eight for `revised_paper_v18_long_abstract.tex`.

### 5.2 Counts that must be EXACTLY ONE

```
grep -o "involuntary-turnover floor" paper/v18/revised_paper_v18.tex | wc -l    # 1  (L91 mapping parenthetical)
grep -o "involuntary-turnover"       paper/v18/revised_paper_v18.tex | wc -l    # 1  (same site)
grep -o "involuntary turnover"       paper/v18/revised_paper_v18.tex | wc -l    # 1  (L1319 KEEP)
```

### 5.3 Totals

| grep | before | after |
|---|---|---|
| `grep -oi "involuntary"` (canonical) | 90 | **19** |
| `grep -oi "involuntary"` (variant) | 90 | **19** |
| `grep -o "baseline turnover floor"` | 0 | **22** |
| `grep -o "turnover floor"` | 30 | **55** |
| `grep -o "turnover-floor"` | 5 | **8** |
| `grep -o "baseline turnover"` | 5 | **38** |
| `grep -o "baseline hazard"` | 5 | **5** |
| `grep -o "seasoning baseline"` | 5 | **5** |
| `grep -oi "involuntary" paper/v18/response_to_referees_round22.tex` | 3 | **1** (line 79) |

### 5.4 Structural invariants

* `diff` of the two `.tex` files (after normalising line 30 to a placeholder) must be **empty** —
  i.e. gate C4's "variant differs in the abstract line only" holds. Verified in simulation:
  the only differing line index is **30**.
* Line counts of the two files must remain equal (they are: unchanged by every pair).
* `\label{sec:robustness-seasonalfloor}` (line 1349) is unchanged by P9 — only the title words move.
  Verified no gate or test pins `Seasonalizing` or that label's title text.

### 5.5 Numeric-literal preservation

A full multiset comparison of `re.findall(r"\d+\.?\d*", tex)` before and after the package returns
**exactly one difference: `'0'` gains +1**, from the `$h_0$` subscript introduced by **C1**.
Every other numeric token in the file is preserved with identical multiplicity. If C1 is dropped,
the multiset is **identical**.

**R1's edited span contains no numeral at all** — the replaced fragment runs from
``The ``baseline turnover floor'' label`` to `what these reads measure`, and every number in that
sentence and its neighbours (`3.8--3.9\%`, `4.70--5.33\%`, `5.51\%`, `84\%`, `5.52\%`) lies outside
it, untouched.

**R2's edited span** begins immediately after
`$\underline{h} = 1-(1-0.04)^{1/12} \approx 0.0034$`, which is reproduced byte-identically as the
anchor's opening; `4\%` sits just before it, outside the span.

Whole-file fixed-string counts for every numeral in or adjacent to the two recast sentences,
**as measured on the pre-edit file** — each must be identical after the package:

| literal (fixed string) | count before |
|---|---|
| `$\underline{h} = 1-(1-0.04)^{1/12} \approx 0.0034$` | 1 |
| `4\%` | 101 |
| `0.04` | 7 |
| `0.0034` | 2 |
| `1/12` | 3 |
| `-0.5` | 12 |
| `[0.61, 1]` | 1 |
| `3.8--3.9\%` | 2 |
| `4.70--5.33\%` | 3 |
| `5.51\%` | 6 |
| `84\%` | 5 |
| `5.52\%` | 7 |
| `2023--24` | 5 |
| `100~PSA` | 2 |
| `0.2 percentage points` | 1 |
| `6\%` | 74 |
| `36\%` | 6 |
| `1,683,124` | 6 |
| `\$764.7 billion` | 31 |
| `$+9.2$` | 26 |
| `$+5.6$` | 25 |

These are **substring** counts (so e.g. `4\%` is inflated by `24\%`, `84\%`, …); that is fine — the
invariant being checked is exact preservation, not semantic uniqueness. Re-derive with a
fixed-string count (`grep -oF -- '<literal>' paper/v18/revised_paper_v18.tex | wc -l`, or
`text.count(literal)`), **not** with `grep -E`, which would treat `$`, `+`, `[`, `\` as
metacharacters and silently return the wrong number. The §5.5 multiset check above subsumes this
table and is the stronger test; this table exists so a spot check is cheap.

### 5.6 Gate/test re-derivation

* `ZERO_COUNT`: all 19 phrases → 0 hits (verified in simulation).
* `EXACTLY_ONE`: all 4 phrases → 1 hit (verified).
* `LETTER_CURRENT_LITERALS`: all 16 present in the post-rename manuscript (verified).
* Every string literal in `tools/liveness_gates.py` and `tests/*.py` that was a substring of the
  pre-rename `.tex` is still a substring of the post-rename `.tex`, **except** the four listed
  in §3 (verified by exhaustive `ast` sweep).
* Gate #101 must report `actual_words=248` and `claimed_words=['248']`.

### 5.8 Composition check on the new forms

`baseline turnover floor` = 22 = P2(2) + P3(23) + P4(1) − P3b(2) − P3c(2).
`turnover floor` (lowercase, 55) = 22 embedded in the long form + P6(4) + P7(21) + 4 pre-existing
bare + P3b(2) + P3c(2). `Turnover floor`/`Turnover Floor` (3, capitalised) are not counted by a
lowercase grep — check them separately.

### 5.7 Residual: nothing to regenerate

`grep -ri involuntary figures/` returns **0**; `abm/monte_carlo_simulation.py` contains **0**;
no `label=`/`title=`/`xlabel`/`ylabel`/`legend` string in `abm/*.py` or `figures/*.py` contains the
term. **No figure PNG bakes in the old label, so there is no run-class residual from this rename.**
The `involuntary` hits in `hazard/*.py` and `abm/*.py` are all the config identifier
`INVOLUNTARY_CPR_ANNUAL` and its comments — out of scope, renaming them is run-class.

---

## 6. Flags — collisions, judgment calls, and what needs Eugene's eyes

### 6.1 `baseline turnover floor` vs `baseline hazard` — the real collision, mitigated

`$h_0$`, the 100 PSA seasoning ramp, is called **"the baseline hazard"** 5× in the manuscript, and
one of those 5 sits in **the same paragraph as the floor's definition** (tex line 240, ~2,900 chars
after R2). After the rename that paragraph names two different objects "baseline". Mitigation
**C1** pins the symbol to the phrase:
`The baseline hazard $h_0$ follows the 100~PSA seasoning ramp`. Minimal, adds no prose, and $h_0$
is already the symbol used in `\eqref{eq:pathB}` immediately above.

*Alternative if Eugene prefers no new symbol in that sentence:* `The seasoning baseline follows the
100~PSA ramp` — the paper already uses "seasoning baseline" 5× for exactly this object. This
changes `baseline hazard` 5→4 and touches two more words. **C1 is the draft's recommendation;
this alternative is flagged, not applied.**

The other 4 `baseline hazard` sites are far from any floor discussion (Section VI hybrid, the
Danish rate-gap swap, the PSA-baseline cross-design sentence, the open-questions list) — checked,
no ambiguity introduced.

**Secondary "baseline" proximities**, repaired rather than flagged:

* **P3b** (L552, L749): `scheduled amortization, the seasoning baseline, and the baseline turnover
  floor` — a three-item list with two "baseline"s. Repaired to the short form:
  `…the seasoning baseline, and the turnover floor`.
* **P3c** (L51, L607): both sentences already contain `Denmark's baseline mobility` /
  `Danish baseline mobility` before reaching the floor. Repaired to the short form. As a bonus this
  makes all four "Danish mean CPR sits below the 4% floor" statements (L51, L607, L638, L797)
  use the identical phrase `the 4\% turnover floor`, which they did not before.

### 6.2 Short-form policy — and why it is not an invention

`involuntary floor` ×25 needs a consistent short form. The draft uses **`turnover floor`**. This is
**not new vocabulary**: the manuscript already uses bare `turnover floor` at L159, L595, L665,
L1327 and `turnover-floor` at L665, L701, L705, L928 — **eight** pre-existing sites, all for this
exact object. (`grep -o "turnover floor"` = 30 = 26 `involuntary`-prefixed + 4 bare;
`grep -o "turnover-floor"` = 5 = 4 bare + 1 inside L295's `involuntary-turnover-floor`.)
The rename therefore *unifies* an existing long/short pair rather than introducing one:

* long form `baseline turnover floor` — definitions, first mentions, exhibits, notation tables (22 sites);
* short form `turnover floor` — running prose (25 renamed + 4 pre-existing + 4 short-form repairs);
* `the floor` — 116 pre-existing bare uses, untouched.

`baseline involuntary turnover` → `baseline turnover` is likewise not an invention: L240, L244,
L745 and L755 already say "baseline turnover" for this object, including inside the very sentence
R2 leaves untouched ("the operative premise is only that **baseline turnover** cannot fall below its
observed deep-discount level"). **This is the strongest single argument that the plan literal is the
right name: the paper already reaches for it whenever it has to state the premise precisely.**

### 6.3 Sites where the rename argues against itself — needs Eugene

1. **L1319, the seasoning diagnostic (KEEP).**
   `A floor meant to capture involuntary turnover---death, divorce, relocation---should be
   approximately flat in loan age.` This whole disqualification of the pooled 2017–2019 read
   reasons *from* a strictly-involuntary core (death/divorce/relocation are age-flat; refinancing is
   not). It is a genuine strictly-involuntary use and is glossed in place, so the draft keeps it —
   but a reader arriving from the recast L91/L240 may ask why the floor is "meant to capture
   involuntary turnover" when the definition says it measures total turnover. The honest reading is
   that the *diagnostic* targets the involuntary core while the *floor* is the total; that is not
   said anywhere. **Recommend Eugene decide** whether to (a) leave it, (b) insert `strictly` before
   `involuntary`, or (c) recast to `A floor whose deep-discount reads are uncontaminated by
   refinancing should be approximately flat in loan age`. The draft applies (a).

2. **L1319, the conclusion (P12g).** `not an involuntary floor` cannot become `not a turnover floor`
   — the pooled 6.1% *is* turnover; the claim is that it is not an admissible read of the floor.
   Draft renders it `not a baseline turnover read`. This is a **new noun** ("read"), though the
   paper uses `realized-turnover reads` at L91 and `the floor read's sampling error` in the
   abstract. Flagged because it is the one place where the rename forces a substantive rewording of
   a claim rather than a label.

3. **L733 vs L1357 — asymmetric treatment of the same-looking phrase.** L733 keeps
   `involuntary and voluntary hazards add` / `4\% involuntary hazard` / `additive competing
   involuntary cause`; L1357 renames `combines the involuntary and voluntary hazards`. The rule
   applied: under the **additive** form the floor genuinely *is* modelled as an independent
   strictly-involuntary competing cause (and L733 defines `$s$` as that share three sentences
   later), whereas L1357 describes the **max** form, where the floor is a floor on total turnover
   and "involuntary" is only the old label. The asymmetry is deliberate and defensible but will look
   like an inconsistency to anyone grepping. **Eugene should confirm the rule before it ships.**

4. **L86 `strictly-` insertion (P12a).** Strictly a consistency fix, not a rename; it makes the
   §I summary line agree with L336 and L851. Drop it if the coordinator wants the package confined
   to renames — nothing depends on it.

5. **L1012 `involuntary tail` → `turnover tail` (P12d).** ABM appendix; "turnover tail" is a
   phrase the paper has not used before. Alternative: `the residual moving tail`. Low stakes,
   flagged for taste.

6. **L295 `involuntary-turnover-floor grid` → `baseline-turnover-floor grid` (P5).** The plan
   literal is unhyphenated, but this is an attributive compound modifying "grid" and the paper
   hyphenated it before. Keeping the hyphens preserves the existing convention; a coordinator who
   wants the plan literal read strictly would write `baseline turnover floor grid`, which is a
   four-noun pile-up. Draft keeps the hyphens.

### 6.4 Not a collision, but worth recording

* `Involuntary floor` at tex L221 becomes `Turnover floor` in a table row whose next cell reads
  `none (stratum fixed effects set **baseline** levels)`. The Title-case *short* form avoids the
  clash; using the long form here would have created one. Same reasoning at L1000.
* Gate #99's `corrections_framed` span is the abstract's load-bearing sentence and it is
  **canonical-scoped** (the archived long-abstract variant predates it), so re-pinning it does not
  need a matching change in the variant's line 30. Gate #68's `null_mechanical_components`, by
  contrast, **is** applied to every manuscript on disk (C4) — its new value
  `scheduled amortization and baseline turnover` is verified present in **both** abstracts after
  the rename (canonical: `…and baseline turnover (itself read from realized…`; variant:
  `…and baseline turnover undershoot a \$35 billion monthly cap…`).
* Nothing in the package touches a run, a manifest, an artifact, or a config constant.
