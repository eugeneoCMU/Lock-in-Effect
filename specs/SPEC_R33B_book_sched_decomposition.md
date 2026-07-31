# SPEC — R33-B part 2: pricing the cross-design scheduled-amortization wedge

**Committed BEFORE the run. No result had been computed when this file was written.**
Date 2026-07-31. Run tag `r33b_book_sched`. Branch: **no new estimation** — the quantity
is an accounting decomposition over committed artifacts, not a re-simulation.

## 1. The question

§VII.C/§VII.D report the cross-design ABM recovering **59.3%** of the benchmark on the
committed draw, **60.2%** over fifty seeds (band 55.1--66.0, min 53.76), against a
pre-committed **50%** threshold, and state that it undercuts the paradigm reading **on
all fifty seeds**. R33-B part 1 established that this leg amortizes the *simulated
population's* composition (`_population_sched_series`, WAC 3.3608263%, mean age
22.2711mo) rather than the book's. The question is whether the threshold verdict and the
unanimity claim survive scoring on the book's own scheduled amortization.

## 2. Why this is an identity, not a re-run

In the `elif surface is not None` branch, `sched_smm` enters the simulated leg linearly:

```
US_Simulated_Monthly_Rolloff = -holdings_b * (monthly_cpr + sched_smm + curtailment_smm)
```

`holdings_b` is exogenous (WSHOMCB, identical across runs), `monthly_cpr` comes from the
CPR surface and does not depend on `sched_smm`, and trapped liquidity accumulates **net
and unclipped** (`fed_mbs_extension_risk.py:1201-1204`, verified: `cumsum` over
`where(qt_active, 0.0)`, no `clip`). Therefore, exactly:

```
Δtrapped = -Σ_t holdings_t · (sched_book_t - sched_pop_t)
```

The mobility-scale recalibration does not confound this: the floor search targets CPR at
an 8% market rate, a property of the surface and the engine, not of `sched_smm`.

## 3. Estimator (declared before running)

`Σ_t holdings_t · sched_book_t` for the **production cohort-weighted, term-aware** book
series is committed directly: `run-2026-07-04-15yr-foldin` manifest
`metrics.scheduled_amort_b.total = 260.02482165944826`.

`Σ_t holdings_t · sched_pop_t` is not committed, so it is estimated as
`Ĥ · Σ_t sched_pop_t`, where `sched_pop_t` is rebuilt exactly from
`scheduled_amortization_series(index, coupon=0.033608263, origin=QT_START-22mo,
term=360)` — the same pure function the runner uses — and `Ĥ` is the effective
holdings scale recovered two independent ways from the same manifest:

- `Ĥ_sched = scheduled_amort_b.total / (n_months · scheduled_amort_b.smm_mean_pct/100)`
- `Ĥ_curt  = curtailment_b.total   / (n_months · curtailment_b.smm_mean_pct/100)`

These use different SMM series (a seasoning annuity and an income-scaled flow), so their
agreement is a real check on the constant-holdings approximation rather than a tautology.

**Primary basis:** production cohort-weighted (this is the book's actual mechanical leg,
and the basis §VI.B means by "scheduled amortization is fixed by the book's composition").

**Secondary basis, reported but not verdict-bearing:** a single-pool book annuity at the
June-2022 SOMA book's own WAC, `composition_shift_results.json`
`soma_book.asof_june_2022.wac_face_weighted_pct`, with mean age share-weighted from that
same block's `vintage_year_shares` under a **mid-year origination** convention evaluated
at 2022-06-30, term 360. This isolates the *composition* wedge at a fixed functional
form; the primary basis additionally carries the term mix and cohort dispersion.

## 4. Parity gates (must pass before any verdict is read)

- **P1 — holdings-scale agreement:** `|Ĥ_sched - Ĥ_curt| / mean(Ĥ) < 2%`. Failure ⇒ T4.
- **P2 — committed quotes replay:** `cross_design_results.json` recalibrated
  `trapped_b = 453.5186133616682`, `share_pct = 59.30299434493775`;
  `empirical_trapped_b = 764.7482532227002`; seeds artifact
  `distributions['A_joint.recalibrated'].mean_pct = 60.20801984127922`,
  `min_pct = 53.75892234794354`. All to 1e-9. Failure ⇒ T4.
- **P3 — population parameters replay:** the rebuilt `sched_pop` must use the WAC and age
  recorded in `cross_design_reweight_results.json` `v1_recalibrated`
  (3.3608263 / 22.2711). Failure ⇒ T4.
- **P4 — direction:** the book series must amortize *faster* than the population series
  (`Σ sched_book > Σ sched_pop`). This is the prediction in §5; if it fails, the
  prediction failed and that must be reported as such rather than re-specified.

## 5. Direction prediction, recorded before running

**Recovery falls on the book basis.** The book's coupon is lower (≈2.47% vs 3.36%) and
its vintages older, and both raise scheduled amortization, so the book's scheduled leg
runs above the sample's; a faster scheduled leg means more simulated roll-off and fewer
trapped dollars. If recovery *rises*, the prediction failed and the landing must say so.

## 6. Landing rule (pre-committed; the verdict is read off the PRIMARY basis)

Let `Δ = Σ h·sched_book - Σ h·sched_pop` (expected > 0), and apply it to each leg:

- `share_committed = (453.5186 - Δ)/764.7483`
- `share_mean50 = (460.4398 - Δ)/764.7483`  (`distributions.mean_trapped_b`)
- `share_min50 = (min-seed trapped - Δ)/764.7483`

| branch | condition | landing |
|---|---|---|
| **T1** | `share_min50 ≥ 50%` | verdict and unanimity both survive. Disclosure only: state the book-basis figures beside the sample-basis ones at §IV l.160 and §VII.D. |
| **T2** | `share_mean50 ≥ 50% > share_min50` | verdict survives, **unanimity does not**. "undercutting on all fifty of them" and "all fifty seeds classify as undercutting" must be replaced by the book-basis count and band. |
| **T3** | `share_mean50 < 50%` | the undercut verdict is **basis-conditional**. §IV l.160's framing, §VII.D l.685 and l.717 all move; this is Eugene's call and the round becomes Major. Land the disclosure and escalate; do not silently rewrite the verdict. |
| **T4** | any of P1--P3 fails | **NOT_PRICEABLE.** Land nothing beyond R33-B part 1's disclosure and record why. |

Reported either way: Δ in dollars and points, both bases, the `Ĥ` bracket, and the age
sensitivity (book mean age ±3 months) on the secondary basis.

## 7. Known limits, stated before the result is seen

1. `Ĥ` treats the holdings path as separable from the SMM series. The two independent
   recoveries in P1 bound that error; the residual is a covariance term between holdings
   and the *difference* of two smooth annuities, which is second order.
2. The 50-seed application assumes Δ is seed-invariant. Population age varies across
   seeds (22.04--22.53mo per `cross_design_seeds_results.json`), so the runner must
   recompute Δ at the observed age extremes and report the spread as the seed-induced
   uncertainty in Δ.
3. This prices the *dollar* leg only. The empirical-CPR referent moves too (the back-out
   nets the same series), but that is a reporting-basis question already landed in part 1.
4. It is not a re-simulation. If Eugene wants the engine's own number, the run needs a
   FRED key and a pinned SOMA cohort table — neither is available in this environment,
   and the cohort table is frozen nowhere in the repo (see
   `RECORD_R33A_finding5_2026-07-31.md`).
