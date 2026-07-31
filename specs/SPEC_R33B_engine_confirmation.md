# SPEC — R33-B part 2, engine confirmation of the book-sched wedge

**Committed BEFORE the run.** Date 2026-07-31. Run tag `r33b_engine_confirmation`.
Addendum to `SPEC_R33B_book_sched_decomposition.md`, whose T2 verdict is already landed.

## 1. Why this run exists

The landed wedge (**$63.88bn = 8.35pp**, branch T2, 16 of 50 seeds below the threshold)
comes from an accounting decomposition, not the engine. The decomposition is exact given
that `sched_smm` enters the simulated roll-off linearly and trapped liquidity accumulates
net and unclipped, but two of its inputs were estimated rather than measured: the
effective holdings scale `Ĥ` (recovered two ways, agreeing to 0.36%) and the assumption
that swapping the scheduled series leaves the CPR path untouched.

Both blockers that prevented an engine run are now gone: the production cohort book is
recovered and pinned (`abm/data/soma_cohorts_2026-07-01.json`, validated to 2.7e-13
against the manifest's scheduled series), and a FRED key is available. So the engine can
be asked directly.

**This run cannot re-open the T2 adjudication.** T2 was fixed before the decomposition
ran and is landed. This run either confirms the magnitude or reveals that the
decomposition was wrong, and the landing rule below says what happens in each case.

## 2. Design

Two legs, identical in every respect except the scheduled-amortization series passed as
`sched_smm_override` to `fed.compute_metrics`:

- **PARITY leg** — `_population_sched_series(df0.index, loans)`, exactly what
  `cross_design_test.run_variant` passes today.
- **BOOK leg** — the cohort-weighted, term-aware series rebuilt from the pinned
  2026-07-01 cohort book, i.e. `Σ_c w_c · scheduled_amortization_series(index,
  coupon_c, origin_c, term_c)`.

Everything else is held: the same cached recalibrated surface, the same
`mobility_scale = 36085.9375`, the same settlement-lag kernel, the same SOMA roll-off
source, the same 42-month window.

## 3. Parity gate G0 — a hard precondition, declared before running

Live FRED is not the frozen macro frame: the R30 log records a scale test halted by a
FRED revision. So the PARITY leg must reproduce the committed cross-design values before
the BOOK leg means anything:

- `trapped_b == 453.5186133616682` and `share_pct == 59.30299434493775`, tolerance
  **1e-6** absolute on dollars and percent;
- `empirical_trapped_b == 764.7482532227002`, same tolerance.

**If G0 fails, the confirmation is INCONCLUSIVE and nothing is re-landed.** The observed
drift is reported as-is. I will not widen this tolerance to obtain a result — the R30
precedent (scale-test parity halted rather than loosened) is the standing rule.

## 4. Landing rule, fixed before the run

Let `Δ_engine = trapped_parity − trapped_book` and `Δ_decomp = 63.8803470149806`.

| branch | condition | consequence |
|---|---|---|
| **E1** | G0 passes and \|Δ_engine − Δ_decomp\| ≤ **$3.0bn** (≈0.4pp of benchmark) | The decomposition is confirmed. Keep every landed number; record the engine figure beside it as corroboration. |
| **E2** | G0 passes and the difference is **$3.0--$10.0bn**, with the T2 branch unchanged (book mean ≥ 50% > book min) | Confirmed in direction and branch, imprecise in magnitude. Restate the manuscript's wedge on the **engine** figure and say the decomposition approximated it. |
| **E3** | G0 passes and either the difference exceeds **$10.0bn** or the T2 branch changes | The decomposition was materially wrong. Retract the wedge figures from the manuscript, re-land on the engine result, and record the failure as a failed method rather than editing the thresholds. |
| **E4** | G0 fails | INCONCLUSIVE. Nothing re-landed; the drift is reported and the decomposition stands on its own stated terms. |

**Direction prediction:** `Δ_engine > 0` (the book amortizes faster, so the book leg traps
less), and I expect E1 — the decomposition's two approximations are second order. If
`Δ_engine ≤ 0` the prediction failed and that must be reported as such.

## 5. Recorded limits

1. The CPR surface is the cached recalibrated one; this run does not re-search the
   mobility scale, which is correct because the floor search targets CPR at an 8% market
   rate and is not a function of `sched_smm`.
2. The engine leg answers the committed draw only. The fifty-seed count stays the
   decomposition's, applied per seed, since re-running fifty engine seeds is a different
   and much larger run.
3. Live FRED may have revised any series since the frozen runs. G0 is the detector, and
   its failure is an outcome, not an obstacle to be removed.
