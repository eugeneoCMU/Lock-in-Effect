# SPEC FP2-B1 — floor→marginal grid extension past 6.0% (`floor_grid_extension`)

**Status: ADOPTED 2026-08-29 by author instruction ("work on it???", this
chat, following the draft's presentation with recommendations). Adopts the
recommended options on every approval item: A2 grid includes 7.00; A3
two-anchor prediction bands; A4 R1 rows decensor with non-qualifying label;
A5 box-edge sentence as drafted in §5.4; A6 tab:oosfloor gains
provenance-marked extension rows. Committed BEFORE any run per Protocol
spec-before-run.**

**Amendment log:** 2026-09-05 (documentation only, no re-run) — §P4's "31
committed uncensored endpoints" is a miscount carried into the record: the run
enumerated **30** (`floor_grid_extension_results.json`,
`parity_gates.P4_blast_radius.n_endpoints_5_to_6` = 30; 31 is the few-cluster
design's cluster count). The bound, the tolerance and the reported movement are
unaffected. Line 84 is left verbatim as the frozen pre-run text; see
`specs/RECORD_fresh_panel2_batchB.md` §"Addendum 2026-09-05".

**Panel trace:** fresh-panel-2 f1, CONFIRMED CRITICAL (2026-08-29, workflow
`wf_c9ee855c-174`): the binding interval's lower endpoint is grid-censored. The
restricted inversion's floor-unit CI is [4.033460201564454, 6.181251547950084]%
(`floor_inference_correction_v2_results.json`,
`reads.R2_2018_gap<=-0.0025_age>=12.wcr_inverted`); the committed
floor→marginal grid (`floor_sweep_results.json`, floors {2.0, 3.0, 3.5, 4.0,
4.5, 5.0, 6.0}) ends at 6.0%, so the 6.1813% endpoint is mapped AT 6.0 and the
printed +2.3 is the 6.0-row value (2.280914554561832pp / $17.44325421351391B),
not a measurement. Also censored: CR3–BM at 6.115977687298146, two-way
t-interval at 6.025832302768929, month wild-t-Rademacher at 6.141792853297579
(v3 battery), and every lower endpoint of the non-qualifying R1 read (wcr at
6.6733). Batch A (RECORD_fresh_panel2_batchA.md) flagged the censoring at every
print site; this run measures what the flag disclosed.

---

## 1. DESIGN (pre-committed)

New runner `hazard/floor_grid_extension.py`, modeled on the committed
`band_low_extension.py` pattern: `floor_sweep` is IMPORTED and its `_run_scored`
convention reused verbatim — same committed 75k loan sample (40,234
window-start survivors), RNG_SEED 42, same ("US","Danish") regime tuple with
per-regime seed offsets, one shared macro frame fetched once, raw-basis scoring
via `extension_risk.score_extension_risk`, fresh runs, caches not consulted.
Does NOT touch `config.py` production defaults. Does NOT edit any .tex file.

Grid: paired legs (central p_q_shock_pct = 6.5, null p_q_shock_pct = 0.0) at
floor annual CPR in **{6.25, 6.50, 6.75, 7.00}%** — 8 engine runs — plus the
parity pair at 6.0% (§2 P1) — 10 runs total, ~25s each, ≈4–5 minutes.

- 6.75 covers every committed censored endpoint (max: R1 wcr 6.6733) AND the
  restricted inversion's own R0-grid ceiling (grid_hi_pct 6.7241619996822655),
  so nothing in the committed inference machinery can truncate at the new edge.
- **7.00 is a DEVIATION from the plan's {6.25, 6.50, 6.75}** (approval item
  A2): it makes the committed INDEPENDENT engine read at floor 6.91%
  (`oos_identification_results.json` instrument1 row 6.91, band 6.5: $5.686B /
  0.7435pp — never a knot, produced by a different committed run) an
  **interior fidelity point** for the extended PCHIP, testable at the existing
  $0.69B mapping-fidelity tolerance, in exactly the region that decides the
  new headline endpoint. Without 7.00 the 6.91 read stays out-of-support and
  can only serve a weak monotonicity check.

Output: `hazard/data/floor_grid_extension_results.json` (frozen after run);
per-run parquets under `hazard/data/floor_grid_extension/` (regenerable, not
committed). `floor_sweep_results.json` is NEVER mutated.

## 2. PARITY GATES (abort, not warn; on failure the JSON is written with
status GATE_FAILURE, exit NONZERO, nothing lands, and the disposition is
STOP-and-report to Eugene — never a tolerance reinterpretation)

- **P1 — 6.0% row bit-exact.** Fresh paired legs at 6.0 reproduce the
  committed row byte-for-byte: marginal $17.44325421351391B /
  2.280914554561832pp; central trapped_b 692.0878877790138, share_pct
  90.4987863473384, floor_bind_share 0.8874622428294053 of 1,683,124
  loan-months; null trapped_b 674.6446335654999, share_pct 88.21787179277656,
  floor_bind_share 0.6739729217811641. (The engine is deterministic and
  seeded; a miss means environment drift, and the extension cannot claim
  "same grid, extended.") The parity row is CHECKED, not merged — the
  extended mapping keeps the committed 6.0 row.
- **P2 — shape.** Marginal weakly decreasing in floor across
  {6.0, 6.25, 6.50, 6.75, 7.00} and every new row's marginal > 0 (the sign is
  forced; a violation is a wiring alarm).
- **P3 — 6.91 engine fidelity.** Extended PCHIP evaluated at 6.91 within
  $0.69B (equivalently 0.0902pp at $7.6475B/pp, the committed pair's implied
  scale) of the committed OOS engine read. This is the run's only genuinely
  out-of-sample check of interpolation quality above 6.0. (Dropped if A2 is
  declined; replaced by: row(6.75) marginal ≥ the 6.91 engine read.)
- **P4 — sub-6.0 blast radius.** Refitting PCHIP on the extended grid turns
  the 6.0 knot interior, changing the interpolant ONLY on (5.0, 6.0) — every
  piece below 5.0 is bit-identical, so the binding UPPER endpoint (floor
  4.033460, +9.109324011557733pp) cannot move; this is asserted, not assumed.
  Over the 31 committed uncensored endpoints with floors in (5.0, 6.0)
  (enumerated from the frozen v2/v3 artifacts), report max |Δpp| and |Δ$B|
  old-map vs extended-map; BLOCKING bound $0.69B / 0.0902pp (same fidelity
  tolerance); expectation: order 0.001–0.1pp.
- **P5 — inversion invariance.** The regenerated v2's SMM-level quantities and
  floor-unit CIs are bit-identical to committed (the mapping enters only at
  the floor→pp step; `wcr_inverted.smm_ci95` and `floor_ci95_pct` to 1e-15).
  N1 is not reopened, and this gate is what proves it.

## 3. EX-ANTE PREDICTIONS (reported hit/miss per repo convention; no gate)

**DEVIATION from the plan's point predictions** (approval item A3): two
committed anchors bracket the curve past 6.0 — the committed-grid PCHIP
endpoint derivative at 6.0 (−2.7553pp per +1pp floor; the plan's "≈ −2.75")
and the committed-engine secant 6.0→6.91 (−1.6895pp per +1pp floor, from the
6.91 OOS read — the curve flattens). Prediction = the interval the two anchors
span; the plan's ≈+1.8/+2.0/+2.2/+1.9 points are the slope-anchor edges.

| endpoint | floor % | predicted pp |
|---|---|---|
| two-way t-interval | 6.0258 | [+2.21, +2.24] |
| CR3–BM | 6.1160 | [+1.96, +2.09] |
| month wild-t-Rademacher | 6.1418 | [+1.89, +2.04] |
| **restricted inversion (binding)** | **6.1813** | **[+1.78, +1.97]** ($13.6–15.1B) |
| R1 wcr (non-qualifying read) | 6.6733 | [+0.43, +1.14] |

Predicted binding interval: **[+1.8 to +2.0, +9.1]**, lower endpoint below the
calibration box's +2.1 edge under either anchor (which is why §5's sentence is
pre-committed now, before the number exists).

## 4. MAPPING RULE + CODE CHANGES (ride in this spec)

- Interpolation rule UNCHANGED: monotone PCHIP through the frozen grid — now
  the committed 7 rows plus the 4 extension rows. No extrapolation; refusal
  semantics unchanged at the new edges [2.0, 7.0].
- `matched_depth_reconciliation.FloorMapping` gains **opt-in**
  `extended=True` reading `floor_grid_extension_results.json`; default False
  is bit-preserving for every other consumer (mdr itself, any uncommitted
  caller). Constructor asserts the extension artifact's 6.0 parity row equals
  the committed row before merging.
- `floor_inference_correction_v2.py`: mapping constructed extended; GRID_HI
  6.0 → 7.0 (or derived from `mapping.x.max()`); docstring truncation
  convention "[2.0, 6.0]" updated; `truncated_at_grid_edge` recomputed under
  the new support (expected censored set after extension: EMPTY among
  committed endpoints). Committed parity pins (COMMITTED_*) unchanged — they
  gate SMM-level and frozen-input quantities only.
- `floor_inference_correction_v3.py`: same pattern. The P4 truncation probe at
  floor 7.5 stays 7.5 — still past the new edge, still probing the convention.
- `layer_convolution.py` changes belong to SPEC FP2-B2, not here.

## 5. LANDING RULES (fixed ex ante)

1. Same interpolation rule, extended support (§4); v2/v3 artifacts
   regenerated; the re-derived binding interval replaces [+2.3, +9.1] at
   every print site (~10 sites × 2 variants; abstract canonical-only per
   gate #99).
2. Batch-A censoring flags come OUT wherever the endpoint decensors; a flag
   stays only where truncation remains (expected: nowhere among printed
   rungs).
3. R1 read rows decensor too, labeled as the non-qualifying read they already
   are (plan recommendation, adopted; approval item A4).
4. **Box-edge sentence, pre-committed before the number** (wording approval
   item A5): "The lower endpoint now sits below the calibration box's $+2.1$
   edge. The two objects measure different things --- the box scores
   calibration choices on a committed grid; the interval prices sampling
   error in the floor read --- and the manuscript already ranks the interval
   as the binding uncertainty statement, so the box is not re-anchored and no
   box literal moves."
5. The calibration box [+2.1, +13.2] is structurally untouched: extension
   runs are δ=6.5-only, so no box cell (floor × band) exists to add. No box
   literal moves at any site.
6. Flow-terms band recomputed mechanically from the new endpoint via the
   committed conversion (slope-anchor prediction: the $0.42/mo lower edge
   falls to ≈$0.33; actual from the run).
7. `tab:oosfloor` gains the extension rows with a provenance marker
   (committed sweep vs 2026-08 extension) — the mapping the inference now
   rests on should not use rows the exhibit hides (approval item A6).
8. Ladder note converts from censoring adjudication to extension record;
   history preserved per the verdict-appendix convention.
9. Gates/tests re-synced in Phase 3 per the plan (#125 literal, #115 battery
   rewrite incl. `n_censored`, cap_monthly_units LO/HI, ladder pins at
   liveness_gates.py:464/525/590/671, count ≥4 at :6897, abstract/letter
   word-count anchors). AST pin scan before every edit; full pytest +
   liveness gates green before done.

## 6. NOT REOPENED (and what proves it)

- N1 adjudication: floor-unit inversion untouched (gate P5, bit-exact).
- `fewcluster_coverage`: not re-run; `binding_construction="restricted_webb"`,
  `landing_branch="L1_webb_retains"` (the disclosed-wrong sha-pinned string)
  left unedited.
- `floor_uncertainty` percentile layer [+3.0, +8.0]: frozen, its 4 tex sites
  untouched; its 26-draw clip is disclosed where it is already disclosed.
- `floor_sweep_results.json`, `oos_identification_results.json`: read, never
  written.

## 7. APPROVAL ITEMS (Eugene)

- **A1** Adopt the spec (status line updated, committed before any run).
- **A2** Grid {6.25, 6.50, 6.75, **7.00**} (recommended; enables P3) vs the
  plan-literal {6.25, 6.50, 6.75} (P3 degrades to a one-sided check).
- **A3** Two-anchor prediction bands (§3) vs the plan's slope-anchor points.
- **A4** R1 rows decensor with non-qualifying label (recommended).
- **A5** Box-edge sentence wording (§5.4) — authorial voice.
- **A6** `tab:oosfloor` gains provenance-marked extension rows (recommended)
  vs a note-only treatment.
