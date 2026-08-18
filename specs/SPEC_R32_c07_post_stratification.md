# SPEC — R32 C-07: post-stratify the 75,000-loan draw onto the book's coupon × vintage composition

**Status: SPEC COMMITTED, NOT YET RUN.** Written before any run, per the round's absolute
spec-before-run rule. C-07 is the last CRITICAL that arrived without a spec.

**Condition (inventory C-07).** "The central/null pair must be scored once on a pool
post-stratified to the book's coupon × vintage-group cells, and the resulting marginal
reported with its direction, so the headline stops being computed on a pool that is not a
probability sample of the book."

**This run may move the headline marginal against the author's interest. That outcome is
pre-authorised and lands (§7).**

---

## 1. The feasibility finding that shapes this spec, measured read-only before writing it

The condition asks for **coupon × vintage-group cells**. Measured against the repo:

- The **coupon marginal** of the book is available. `fetch_soma_mbs_cohorts`
  (`abm/fed_mbs_extension_risk.py`) parses SOMA CUSIPs into `(term_months, rounded coupon)`
  buckets with a face `weight` each.
- The **vintage marginal** of the book is available and committed:
  `composition_shift_results.json` → `committed_anchors.vintage_shares` =
  pre2017 0.106, 2017–19 0.060, 2020 0.163, 2021 0.439, 2022 0.231
  (source `hazard/wal_table.py VINTAGE_SHARES`, SOMA CUSIP tabulation).
- **The JOINT coupon × vintage distribution is NOT available.** In
  `fetch_soma_mbs_cohorts` the vintage information inside a `(term, coupon)` bucket is
  collapsed to a single value-weighted `origin_date`
  (`bucket_origin_w[key] / val`) before the cohort list is returned. The within-coupon
  vintage *distribution* is destroyed by that aggregation and is recoverable from no
  committed artifact.

**Therefore this run rakes to two marginals; it does not match a joint.** That is a real
weakening of the condition as literally worded and it must be stated wherever the result is
quoted: matching both marginals fixes the composition only up to the coupon×vintage
interaction, which this design does not observe. Calling the output a "coupon × vintage
cell match" would be false.

## 2. The support limit, which is prior to everything else

`loan_sample.parquet`'s vintages are **2017–2021** (`composition_shift_results.json`
`gates.G1_freddie_sample_integrity.vintage_range`). The book's **pre-2017 (10.6%) and 2022
(23.1%) = 33.7% of face have ZERO support in the draw** and cannot be created by
reweighting. So:

- The vintage target is the book's conditional mix **within 2017–2021**, renormalised:
  2017–19 **0.0906**, 2020 **0.2462**, 2021 **0.6631** (from 0.060/0.163/0.439 over 0.662).
- The 33.7% out-of-support share stays covered by `vintage_overlay`, exactly as today. This
  run does not touch it and must not be reported as if it did.

### 2.1 A literal collision that must not be conflated — checked, and real

`vintage_overlay_results.json` carries `shares.retained = 0.663`, and its meaning is
**1 − 0.337, the in-support share of book FACE** (`source: hazard/wal_table.py
VINTAGE_SHARES`; the artifact's own `share_used` is 0.337). The renormalised **2021** share
this spec derives in §2 is **0.6631**. These are two different objects that agree to three
decimals by coincidence. The run must never quote one for the other, and the manuscript
sentence must not put them in the same clause without naming both.

## 3. Method — raking on the pool's balance weights

The existing seam is `MicrosimPool.reweight_to_soma_coupons(soma_cohorts, coupon_convert)`
(`hazard/agents.py`), which is **coupon-only**: it multiplies member balances by
`soma_share / current_balance_share` per 0.5% bucket, then `scale_to_holdings` restores the
total. The pool already carries `self.vintage` (`hazard/agents.py:125`), read today only by
that function's converter argument.

This run generalises it to two margins by **iterative proportional fitting** on the
per-loan balance weights, in a NEW runner. Nothing in `hazard/agents.py` is edited.

1. Convert the sample's borrower NOTE rate onto the SOMA PASS-THROUGH basis with the same
   converter the committed coupon work uses, on a LOCAL COPY (`self.coupon` is never
   reassigned — this is the round-28 G2 design and is what keeps the hazard inputs fixed).
2. Bucket both sides on the same 0.5% grid; restrict to `term_months == 360`.
3. Vintage groups: `2017-19` (2017, 2018, 2019), `2020`, `2021`.
4. IPF: alternately rescale weights so the balance share of each coupon bucket equals the
   SOMA coupon share, and the balance share of each vintage group equals the renormalised
   §2 target. Iterate to `max |share − target| < 1e-10` on both margins or 200 sweeps.
5. `scale_to_holdings` to restore total UPB to Fed holdings, exactly as the coupon-only path
   does. **The level is therefore not what moves; the composition is.**

**Convergence is not assumed.** IPF on two margins over a support with structural zeros can
fail to converge. If it does not reach 1e-10 in 200 sweeps, that is recorded and the run
lands under Branch C.

## 4. What is run

At the headline off-window floor **4.991%**, production floor form, everything else at
production convention:

- **(i) post-stratified pair** — central (δ = 6.5%) and null (β₁ = 0) on the raked pool.
- **(ii) vintage-only pair** — the same at the vintage margin alone, reported as the
  decomposition limb, because the coupon margin alone is already known to leave the marginal
  bit-invariant (§VII.E, `coupon_convention_reweight`). Without (ii) a null result cannot be
  attributed.

## 5. Parity gates — all must pass before any reweighted leg is believed

| gate | assertion |
|---|---|
| **P1** unweighted parity | the same harness with NO reweighting reproduces `psa_level_sweep_results.json` `cells["4.991\|100\|*"].trapped_b` to < 10⁻⁹ \$B |
| **P2** margins actually hit | after IPF, both the coupon-bucket and the vintage-group balance shares equal their targets to < 10⁻¹⁰; **recomputed inside the run from the committed artifacts, never taken from this file** |
| **P3** no-op detection | the post-stratified pair must differ from the unweighted pair by **more than \$1B** on at least one leg; a bit-invariant result is **GATE_FAILURE, not a finding**, because §VII.E already shows the coupon margin alone is bit-invariant and an unreached vintage margin would look identical |
| **P4** bind-share parity | the UNWEIGHTED central leg reproduces the committed 68.8% floor-bind share over 1,683,124 evaluated loan-months (tolerance 0.001), so the bind diagnostic is known good before it is read on the reweighted pool |
| **P5** total preserved | total UPB after `scale_to_holdings` equals the unweighted run's to < 10⁻⁶ relative |
| **P6** coupon untouched | `pool.coupon` is bit-identical before and after reweighting (the converter is applied to a local copy only) |
| **P7** frozen artifacts | sha256 of every file under `hazard/data/` unchanged before and after, except the one new output (the gitignored `floor_sweep/` scratch directory is excluded and that exclusion is recorded in the artifact) |

`P3` is the anti-gaming gate. Without it a silently unreached vintage margin returns
"no change", which is precisely the comfortable answer.

## 6. Output

`hazard/data/book_composition_marginal_results.json`. **Refuse to write if it exists.**
Carries: the two targets and the achieved margins, the IPF iteration count and convergence,
both legs' `trapped_b` / `share_pct` / `floor_bind_share` for the post-stratified,
vintage-only and unweighted pairs, the marginal in pp for each, every gate result, the
pre-committed expectation of §7 with a `prediction_held` boolean, and the branch taken.

## 7. Pre-committed expectation — direction AND band, committed here before the run

**Direction: the marginal FALLS relative to +5.5716.** The reasoning, so it cannot be
rewritten afterwards: raking moves balance weight out of 2017–19 (27.0% of surviving balance
in the draw against a 9.1% conditional target) and into 2021 (42.3% against 66.3%). The 2021
cohort is the deepest out-of-the-money and the least seasoned, so its voluntary hazard is the
lowest; under the production hard-maximum form the floor binds wherever the voluntary hazard
sits below it, and the marginal is **zero wherever the floor binds on both legs**. The
central leg is already floor-pinned in 68.8% of evaluated loan-months at this floor. Shifting
mass toward the cohort that binds most should therefore shrink the marginal.

**Band: `marginal_pp` in [+2.5, +5.0].** Anchored on the paper's own share-scaling proxy:
`vintage_overlay` returns +3.7 by pure share arithmetic. This run differs from that proxy by
the censoring interaction, which can go either way, so the band is set wide enough to admit
that interaction and narrow enough to be falsifiable. **Outside the band, the result is
reported as landing outside a pre-committed band, with this paragraph quoted.**

**If the marginal RISES, that is a failed prediction and is reported as one**, in the
manuscript sentence and not only in the artifact — and it would also make the §V.E and
abstract claim that every measurable correction "moves it down within the range rather than
up" false, which must then be restated exactly as Task 11's spec requires, not deleted.

## 8. Landing rules — one per branch, committed in advance

- **Branch A — all gates pass, IPF converged.** Land the post-stratified marginal in §V.E's
  assembly discussion and as a `tab:assembly` row with its sign, under the inclusion
  disclosure C-40 established (`dcd6fc4`). State in the same breath: (a) that it rakes to two
  marginals and does not match a joint, because the joint is unobserved; (b) that 33.7% of
  book face is out of the draw's support and stays with `vintage_overlay`. Report the number
  **whichever way it falls**.
- **Branch B — gates pass but IPF converged only on one margin.** Land the vintage-only
  result (limb (ii)) with the coupon margin's failure recorded, and say the composition
  correction is identified on one margin only.
- **Branch C — any parity gate fails, or IPF does not converge.** Record **NOT_FEASIBLE** in
  `specs/RECORD_R32_c07_infeasible.md` with the failing gate and the numerical reason. The
  honest alternative that lands instead: one sentence in §V.E stating that the draw cannot be
  post-stratified onto the book's composition, with the specific reason, so the reader is not
  left to assume it was never attempted. The existing composition disclosure (`2ec6a8e`) and
  `vintage_overlay` stand unchanged.
- **In every branch**, the §7 prediction is reported against the outcome, and
  `prediction_held` false is stated in the manuscript sentence.

**No branch permits deleting the composition disclosure.** It is a disclosure; the round's
first anti-gaming rule forbids removing it to satisfy a criticism.

## 9. What this run does not settle

- The coupon×vintage **interaction** (§1) — unobserved, and named as such.
- The 33.7% **out-of-support** face (§2) — covered by `vintage_overlay`, not by this.
- The **agency** margin (Ginnie 20.4% of SOMA face) — a different dimension, covered by
  `ginnie_overlay`; R30 already recorded the Ginnie × vintage intersection NOT_FEASIBLE
  (`specs/RECORD_R30_ginnie_vintage_infeasible.md`), and nothing here reopens it.
- The **form** fork — orthogonal; run under the production form only.
