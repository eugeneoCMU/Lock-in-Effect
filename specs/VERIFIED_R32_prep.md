# Coordinator-verified facts for the R32 plan (verified in-session, not taken from the panel)

## R2 — the basis mix at .tex:709 — CONFIRMED REAL, with the correct replacement derived

Current text (byte-exact, count 1 in `paper/v18/revised_paper_v18.tex`):
```
while the central leg's recovery falls from 91.3\% to 55.9\% along the way, the level cost the additive end pays
```

Artifact `hazard/data/floor_form_mixture_results.json`, key `cells."<floor>|<s>|<delta>".share_pct`.
**`share_pct` is the STANDALONE basis.** Proof: `cells."4.991|0|6.5".share_pct = 100.36328284662208`,
and the manuscript states the central leg recovers **91.3% on the SHARED basis** at the same floor/form
(s=0, delta=6.5). 100.36 != 91.3, and 100.4 is the paper's own standalone figure for that cell.

Relevant cells (floor 4.991 = the headline off-window calibration):
| s | delta=0 (null leg) | delta=6.5 (central leg) |
|---|---|---|
| 0 (max form)      | 94.79172466371236 | 100.36328284662208 |
| 1 (additive form) | 44.69959732600039 |  55.90661839965657 |

So the sentence pairs **91.3 (shared)** with **55.9 (standalone)** — a mixed-basis comparison.
Magnitude of the understatement: standalone fall is 100.4 - 55.9 = **44.5pp**; the sentence's mixed
pairing reads as 91.3 - 55.9 = 35.4pp, i.e. it **understates the additive form's level cost by ~9pp**.
The panel's claim is upheld exactly.

**Fix options, both single-basis (implementer picks one and states the basis in the clause):**
- Standalone, directly quotable from the artifact: `falls from 100.4\% to 55.9\%`
- Shared: requires deriving the shared-basis counterpart of the s=1 cell (the shared basis nets a
  common $69.6bn curtailment flow from every U.S. leg). DO NOT print the panel's "46.8" without
  deriving it from the artifact first — it is not a key in this file.

Also note for the same fork: the DA's / synthesis's **35.6% shared** for the additive null is a
DIFFERENT quantity (the null leg, delta=0, s=1). At floor 4.991 the artifact's standalone null at
s=1 is 44.69959732600039; 35.6 is its shared-basis counterpart as cited by the panel. Verify by
derivation before printing.

## R1 — abstract clauses (byte-exact, `.tex:31`, count 1 each)

- Self-refuting pair CONFIRMED: the abstract contains `it identifies levels only.` while the body
  contains `does not identify levels.` Both present, count 1 each.
- The bounding clause, byte-exact:
```
The design bounds it between $+2.9$ and $+8.7$ points under its production floor form (the floor read's sampling error at my central elasticity; a wild-cluster interval on 31 clusters; the percentile read under-covers),
```
- The mechanical clause opens `switch the lock-in response off and the model still accounts for 85.7\%`
  — currently carries no form label.

## R3 — Table 6 caption

`2017--2019 performance` occurs exactly **1** time in the .tex. The three rows that set the headline
are the 2018 leg reads; per the artifact's own seasoning block the clean leg carries cohort-months
only in age bands [0,12) and [12,24) and **zero** at >=24, with verdict string
`CLEAN_BY_CONSTRUCTION_MATURE_TEST_NOT_COMPUTABLE`. So the caption's blanket "2017-2019 performance"
is wrong for those rows and must be narrowed.

## R4 — beta_1 sign

`0.0817` occurs exactly **1** time in the .tex, so the "two printings with opposite signs" claim
needs re-derivation against the actual Table 3 and Table 7 cells before any edit — the sign defect
may be between a table cell and a prose statement rather than between two table cells.
DO NOT edit on the panel's word alone; locate both printings first.

## Build/verification baseline at plan time (measured this session)

- HEAD `d5465d2`, tree clean, 2 commits unpushed relative to `origin/main`.
- ALL GATES PASS (108) | 495 tests | ALL RENDER CHECKS PASS (139pp / 94pp main / 45pp appendix / 140pp variant).
- Render gate: `python3 tools/render_gate.py` — must stay at 0 off-page items after every edit.
- Variant invariant: canonical and long-abstract differ at **line 31 only** (the abstract).

## R4 — the beta_1 sign — CONFIRMED REAL, but the panel's proposed fix is WRONG. Full diagnosis:

Three artefacts of the same parameter, two sign conventions:

1. **`eq:beta1` (`.tex:228`)** defines it WITH A LEADING MINUS:
   `\beta_1 = -\ln\!\left[\frac{1-\big(1-(1-\delta)\,P_q\big)^{1/3}}{1-\big(1-P_q\big)^{1/3}}\right]`
   The bracketed ratio is < 1 (the shock lowers the hazard), so `ln(ratio) < 0` and the leading
   minus makes **beta_1 POSITIVE** under the manuscript's own definition.
2. **`eq:pathB` (`.tex:220`)** uses the SIGNED gap: `exp(\beta_1 g_{i,t} + ...)`, and `g` is negative
   when the borrower is locked in. Positive beta_1 x negative g = suppression. **Self-consistent.**
3. **`tab:params`** prints `$\beta_1$ (central) & $0.069$` — POSITIVE. **Correct per eq:beta1.**
4. **`tab:lowband`** prints the whole column NEGATIVE: `6.50 & $-0.0686$`, and nine rows like it.
   This matches the PRODUCTION CODE, `hazard/literature_hazard.py:32 rothstein_beta1`, which returns
   `math.log(h_shocked / h_base)` — i.e. **WITHOUT** eq:beta1's leading minus, hence negative.

**So neither printing is a computational error; the manuscript prints one symbol under two
conventions.** A referee sees `+0.069` in one table and `-0.0686` in another for the same parameter
at the same delta.

**Correct fix (do NOT "flip the printed signs" blindly, and do NOT touch the code or eq:beta1):**
harmonise `tab:lowband`'s beta_1 column to the manuscript's own definition in eq:beta1 — print the
nine values POSITIVE — and add one sentence to the table note recording that the production helper
returns the same quantity with the opposite sign (so a replicator reading `rothstein_beta1` is not
confused). The marginal ($B and pp) columns are untouched: they are functions of |beta_1| through
the engine and do not change. Then add a gate asserting the `tab:params` and `tab:lowband`
delta = 6.5 entries agree in sign.

**Zero-slack exposure (measured, fixed-string counts):** the nine column literals
`0.0103 0.0206 0.0311 0.0337 0.0417 0.0523 0.0577 0.0686 0.0817` occur in the .tex 1,1,1,1,1,1,1,2,1
times and are pinned by **ZERO** gates and **ZERO** tests. `0.0686` occurs twice (the table row plus
the unrounded `\beta_1 = 0.0686$ (unrounded $0.068571...` prose site) — the prose site already
prints it POSITIVE, which is further evidence that positive is the manuscript's intended convention
and `tab:lowband` is the outlier.

**Lesson for the plan:** the panel wrote "add the sign note to Table 7 (or flip the printed signs)".
Flipping without reading eq:beta1 and `rothstein_beta1` would have produced a table that contradicts
the production code with no note explaining why. Every condition gets derived from source before it
is implemented.
