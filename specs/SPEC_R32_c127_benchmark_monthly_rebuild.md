# SPEC — R32 / C-127: rebuilding the benchmark's monthly series at monthly frequency

**Status: PRE-COMMITTED. Committed BEFORE the runner, and both before the run.**
Run tag: `benchmark_monthly_rebuild`. Runner: `tools/benchmark_monthly_rebuild_run.py`.
New artifact: `hazard/data/benchmark_monthly_rebuild_results.json`.

**Eugene's scope decision, which the inventory required before any run, was given on 2026-07-30.**

---

## 1. The condition

C-127 (R2:M8, "Major **if sustained**", **NOT ARBITRATED** — the synthesizer never re-derived the
benchmark). The benchmark's monthly roll-off series is built by differencing weekly Wednesday
current-face levels: `hazard/macro.py:173–174` does `weekly["mbs_b"].resample("ME").last()` then
`.diff()`. That produces four clip-zero months — 2022-06, 2023-02, 2024-04, 2025-09 — which
`h1_zero_months_diagnosis.json` classifies `ARTIFACT` with `spike_followed_all_artifact = true`.

R2's objection: the series should be rebuilt from **published monthly SOMA principal-payment data,
or from CUSIP factor changes**, which would retire the four clip zeros and reopen the
monthly-timing question on a clean comparator.

The inventory's stated settling test: re-derive the 42-month total and compare to
`764.7482532227`. **Inside tolerance → timing-only, wording note. Outside → the benchmark is in
play and the round's scope changes.**

## 2. SOURCEABILITY — determined FIRST, and it decides most of the condition

Both of R2's proposed sources were probed live against the NY Fed markets API before this spec was
written. **DECLARED, NOT PREDICTED:**

1. **There is no monthly principal-payment endpoint.** `soma/summary.json` returns weekly rows
   carrying holdings **levels only** — fields are `asOfDate, agencies, bills, cmbs, frn, mbs,
   notesbonds, tips, tipsInflationCompensation, total`. No paydown, principal-payment or factor
   field. `soma/mbs/get/monthly.json` and `soma/agency/get/monthly.json` both return **HTTP 400**.
2. **The CUSIP route exists but carries the identical staleness.**
   `soma/mbs/get/asof/{date}.json` returns per-CUSIP `currentFaceValue` (16,333 rows at
   2024-04-24; 29,055 at the 2023-02 dates). Summing it across the 2023-02 clip:

   | as-of | CUSIPs | total |
   |---|---|---|
   | 2023-01-25 | 29,055 | $2,616.2734730824bn |
   | 2023-02-01 | 29,055 | $2,616.2734730824bn |
   | 2023-02-08 | 29,055 | $2,616.2734730824bn |
   | 2023-02-15 | 29,051 | $2,615.0506434440bn |
   | 2023-02-22 | 29,051 | $2,611.7887093756bn |

   The first three dates are **identical to ten decimal places on an identical CUSIP count**. The
   NY Fed republished the same holdings file three weeks running.

**So the clip is a property of the PUBLISHED DATA, not of the differencing method**, at least at
the month tested. Rebuilding from CUSIP factor changes cannot recover paydowns the source never
posted. That is the substance of the condition and it was established at scoping; recording it as
a prediction would be dressing up a known answer.

**What is NOT known and is genuinely predicted below:** whether the other three clip months behave
the same way, and whether a CUSIP-reconstructed 42-month total reproduces the committed benchmark.

## 3. Construction

For each of the 42 window months plus the four clip months' surrounding weeks:

- **Per-CUSIP reconstruction.** Pull `soma/mbs/get/asof/{d}.json` for every SOMA as-of date in
  2022-05 … 2025-12 (list from `soma/asofdates/list.json`). For consecutive as-of dates $d_{k-1},
  d_k$, decompose the change in total current face into
  - **paydown** — CUSIPs present in both, face declined;
  - **added** — CUSIPs present only in $d_k$;
  - **removed** — CUSIPs present only in $d_{k-1}$;
  - **increased** — CUSIPs present in both, face rose.
  The aggregate difference is the sum of the four. This is the decomposition the aggregate series
  cannot make, and it is the only thing the CUSIP route buys.
- **Monthly total.** Sum the paydown component by calendar month, and separately reproduce the
  committed method (`resample("ME").last().diff()`) from the same fetched levels.
- **Staleness detector.** A published week is **stale** when its CUSIP set and total face are
  identical to the previous week's. Report every stale week in the window, not only the four the
  committed diagnosis already names.
- **The settling comparison.** CUSIP-reconstructed 42-month window total against
  `764.7482532227`, and against `committed_anchors.benchmark_b` read live.

**The cap side is not touched.** The benchmark is realized-minus-cap; this run rebuilds only the
realized series. The cap schedule, the window bounds and the reinvestment-ceiling reading are all
out of scope, exactly as `settlement_months_benchmark`'s own residual note scopes itself.

## 4. Pre-commitments

**STOP-class:**

- **E1 — the committed method reproduces from the fetched levels.** Re-running
  `resample("ME").last().diff()` on the API's own weekly rows must reproduce the committed monthly
  series and the four clip zeros. If it does not, the fetch is not the series the paper uses and
  nothing downstream is interpretable.
- **E2 — the four-way decomposition is exhaustive.** paydown + added − removed + increased equals
  the aggregate week-over-week change to $10^{-6}$bn at every step.

**GENUINE predictions** (may fail; a miss lands with the miss named):

- **E3 — all four clip months are source-side.** Each of 2022-06, 2023-02, 2024-04 and 2025-09
  contains at least one **stale week** by the §3 detector. Basis: the 2023-02 clip is stale in the
  CUSIP file, and the committed diagnosis records `spike_followed_all_artifact = true` for all
  four. **Only 2023-02 was checked; the other three may differ.**
- **E4 — the settling test passes.** The CUSIP-reconstructed 42-month window total lands within
  **1%** of `764.7482532227`. That threshold is fixed here, before the run. Inside → R2's M8 is
  timing-only and the benchmark is not in play. Outside → it is, and the round's scope changes.
- **E5 — the reconstruction does not retire the zeros.** The paydown-component monthly series
  still shows a near-zero month wherever a stale week falls, because a republished file posts no
  paydowns. **If E5 fails — if the CUSIP route DOES retire the zeros — then R2 is right, the
  differencing method is the cause, and the monthly-timing question genuinely reopens.**

## 5. Gates

- **P1** the committed benchmark `764.7482532227` and the four clip months are read live from
  `h1_zero_months_diagnosis.json` and `expectation_benchmark_results.json`, never hard-coded.
- **P2** every as-of date fetched is recorded with its CUSIP count and total, so the staleness
  claim is auditable from the artifact alone.
- **P3** the cap arithmetic the inventory quotes is re-derived, not asserted:
  $3 \times 17.5 + 39 \times 35 = 1{,}417.5$ and $1{,}417.5 - 652.8 = 764.7$.
- **P4** network failure is **non-fatal and explicit**: if the API is unreachable the run records
  `sourced: false` with the reason and lands nothing. It must not fall back to WSHOMCB and pretend
  it rebuilt anything.
- **W1** writes **only** `hazard/data/benchmark_monthly_rebuild_results.json`; refuses to overwrite
  a differing file; **touches no `.tex` file and rewrites no committed artifact.**
- **No engine.** Network reads and arithmetic only.

## 6. Landing rules, per branch

- **Branch A — E3, E4 and E5 all hold.** The clip zeros are source-side, the total reconciles, and
  the reconstruction does not retire them. **Land a short disclosure**: the four zeros are a
  property of the published SOMA file — reproduced identically in the aggregate summary and in the
  per-CUSIP holdings — and are not an artifact of month-end differencing. This *strengthens*
  App. N's existing `ARTIFACT` classification by ruling out the alternative R2 named. New gate +
  test battery; `tab:runindex` row. **`.tex:137` is not restated** — the inventory's protection
  still binds, and in any case that line is the ABM appendix pointer, not the benchmark site (the
  inventory's line number is stale, like the others this round corrected).
- **Branch B — E4 fails (total outside 1%).** **The benchmark is in play.** Land nothing in the
  manuscript. Commit the artifact and a record, and escalate to Eugene: this is the branch the
  inventory says changes the round's scope, and it is not a coordinator decision.
- **Branch C — E5 fails (the CUSIP route retires the zeros).** R2's objection is **sustained**.
  Land the finding, re-open the monthly-timing question on the clean comparator, and escalate —
  App. N's `ARTIFACT` classification would need revisiting, which is a claim change, not a wording
  note.
- **Branch D — E3 misses on one or more months but E4 and E5 hold.** Land Branch A's disclosure
  scoped to the months it covers, and name the exceptions.
- **Branch E — P1–P4 or E1/E2 fails.** Land nothing; commit a failure record.

## 7. Scope limits this spec commits to stating

1. **This does not re-derive the cap side.** Only the realized series is rebuilt.
2. **A stale published week is not evidence about the Fed's actual paydowns** — it is evidence
   about the file. The run can show the zeros are source-side; it cannot show what the true
   monthly paydown was in a week the source did not post.
3. **R2's objection is recorded as NOT ARBITRATED throughout.** Whatever this run finds, the
   synthesizer never re-derived the benchmark, and the artifact must say the run settles the
   *sourceability* leg rather than adjudicating the referee exchange.
