# SPEC FP2-B2 — `layer_convolution` re-derivation on the restricted rung

**Status: ADOPTED 2026-08-29 by author instruction ("work on it???", this
chat, following the draft's presentation with recommendations). Adopts
construction α (restricted confidence distribution, item B1). Committed
BEFORE the run per Protocol spec-before-run. ORDER CONSTRAINT: executes only
after SPEC FP2-B1 has LANDED (runs done, v2/v3 artifacts regenerated) — on
the committed [2.0, 6.0] grid the floor-read layer's tail hits the same edge
and the convolution inherits the censoring it is supposed to cure.**

**Amendment log:** (none)

**Panel trace:** fresh-panel-2 f3, PARTIAL (2026-08-29). The committed
convolved pair [+2.7959, +8.9922] (`layer_convolution_results.json`
`.convolved_primary.ci95_pp`) was computed with the floor-read layer on the
DEMOTED Webb wild-t rung (9,999 t*-implied draws, 70 edge-truncated above
6.0%) and was never re-derived under the adjudicated restricted inversion. As
printed it is anti-conservative: 6.196pp wide, narrower than the 6.83pp
binding interval a faithful re-derivation must exceed. Batch A relabeled it "a
lower bound on the re-derived pair" and withdrew the one-number
recommendation; this run produces the re-derived pair so the recommendation
can return.

---

## 1. CONSTRUCTION (pre-committed; the fork is approval item B1)

**Option α (RECOMMENDED) — restricted confidence distribution as the floor
layer.** The restricted inversion retains R0 iff t_obs(R0) ∈
[q2.5, q97.5](t*(R0)) — equal-tailed (`floor_inference_correction_v2.py`
`wcr_invert`). Its exact confidence-distribution dual: over the same committed
401-point R0 grid (R̂ ± 5·SE_CR1, SMM scale), with the SAME single Webb weight
matrix (fresh `default_rng(42)`, drawn once, reused across the grid — the
committed MacKinnon–Webb practice), compute per grid point

    H(R0) = P*( t*(R0) ≤ t_obs(R0) ),   t_obs(R0) = (R̂ − R0)/SE_CR1,

the one-sided restricted bootstrap CDF. Retention ⇔ H(R0) ∈ [0.025, 0.975]
(up to the 9,999-draw discreteness), so H ties bit-exactly to the committed
retained set — gated, not assumed (§2 Q2). Floor-layer quantile function:
R0(u) = the first grid point with monotone-envelope H ≥ u (step function at
grid resolution, the same convention the committed CI itself is read off the
grid with). Monotone envelope = running max of H; max |H − envelope| is
reported and a value > 0.01 is a wiring alarm (STOP). Layer draws by
deterministic midpoint-rank enumeration, NO new RNG:

    u_b = (b − 0.5)/9999,  b = 1..9999;   M_b = PCHIP_ext( cpr_pct(R0(u_b)) )

with PCHIP_ext the B1-extended mapping (edge-truncation convention retained,
counts reported; expected 0 — the R0 grid ceiling 6.7242% < 7.0).

LOAN LAYER unchanged from the committed C2: d_j = m_j − 5.5715581829 over the
200 committed cluster draws; centering constant fixed ex ante as before.

CONVOLVED: exact outer sum {M_b + d_j}, 9,999 × 200, `np.add.outer`; report
2.5/97.5 percentiles in pp and $B, median, sd, width, width ratio vs the
re-derived binding interval. Secondary percentile line, dependence bracket
(independent sum = lower bound, comonotone sum = upper bound), and the
lower-bound-summand disclosure all carry over from C2 unchanged.

**Option β (fallback, NOT recommended)** — keep the committed Webb t* layer
and only extend the grid (decensors the 70 truncated draws). Cheaper and
zero new construction, but it does not discharge f3: the pair stays computed
on the demoted rung, the "lower bound on the re-derived pair" label cannot
retire, and the one-number recommendation cannot honestly return. Listed so
the fork is a decision, not a default.

## 2. PARITY GATES (abort, not warn; GATE_FAILURE + nonzero exit on miss)

- **Q0** — C2's P0/P1 carried verbatim: percentile replicate regeneration
  bit-exact at R2 (se_pp 0.3933971547430653, ci95_pct [4.368576777908708,
  6.003552252675821], 1e-9); loan draws CSV 200 rows, committed percentiles
  and sd reproduced.
- **Q1** — input freshness: reads the B1-REGENERATED v2 artifact; asserts its
  extended-map provenance (GRID_HI, mapping support max 7.0) and that
  `wcr_inverted.smm_ci95` equals the pre-B1 committed values bit-exactly
  (B1's P5 invariance, re-checked at the consumer).
- **Q2** — construction ties to the adjudicated interval: the H-implied
  retained set equals v2's committed retained set index-for-index over the
  401 grid; R0(0.025)/R0(0.975) reproduce the committed floor-unit CI
  endpoints exactly; their PCHIP_ext images reproduce the B1 re-derived
  binding interval endpoints to 1e-12. A construction that cannot reproduce
  the interval it convolves does not land.
- **Q3** — width sanity: convolved width > the re-derived binding interval
  width (a sum with an independent second layer must widen). On a miss:
  STOP, nothing lands (this was the anti-conservativeness that triggered f3).

## 3. EX-ANTE PREDICTIONS (hit/miss; no gate)

Floor layer ≈ the re-derived binding interval [≈+1.8–2.0, +9.11]; the loan
layer adds tails of roughly [−0.94, +1.35]pp at the 2.5/97.5 points (committed
deviations). Predicted convolved pair ≈ **[+1.2 to +1.7, +9.6 to +10.0]**,
width ≈ 8.3–8.7pp (> the ≈7.2pp re-derived binding width), truncation count 0
on the primary line.

## 4. LANDING RULES (fixed ex ante)

1. The new pair replaces [+2.80, +8.99] at .tex:308 and tab:uncertainty
   (both variants; abstract untouched — the convolution does not print
   there).
2. The "lower bound on the re-derived pair" label RETIRES iff the primary
   line's truncation count is 0; otherwise it converts to the accurate
   statement and the run is reported as partial.
3. The one-number recommendation returns, pre-committed to point at the
   re-derived convolved pair (the reader who wants one number for sampling
   error uses it; the binding interval remains the binding layer).
4. Gate #105 (`CONVOLVED_LINE_SPANS`) re-synced; `test_convolved_line_gate`
   imports the span, no separate edit.
5. Secondary lines (percentile companion, dependence bracket) land in the
   artifact; their tex treatment is unchanged from C2's (no new sites).
6. The committed `layer_convolution_results.json` is superseded, not
   mutated: the re-run writes fresh; the old artifact survives in git
   history per the freeze convention.

## 5. NOT REOPENED

The rung adjudication itself (fewcluster_coverage), the loan layer's
construction and centering constant, the dependence-independence framing, the
percentile layer's 4 tex sites. Changing the floor layer's rung to the
adjudicated one is the correction f3 named; nothing else moves.

## 6. APPROVAL ITEMS (Eugene)

- **B1** Construction fork: α restricted confidence distribution
  (recommended) vs β Webb-layer-on-extended-grid (label cannot retire).
- **B2** Adopt the spec (status line updated, committed before the run),
  after FP2-B1 lands.
