# SPEC — R32 / C-128: pricing the realized-side window-boundary allocation

**Status: PRE-COMMITTED. Committed BEFORE the runner, and both before the run.**
Run tag: `realized_boundary_allocation`. Runner: `tools/realized_boundary_allocation_run.py`.
New artifact: `hazard/data/realized_boundary_allocation_results.json`.

**Eugene's scope decision was given on 2026-07-30, with C-127.**

---

## 1. The condition

C-128 (R2:M8 consequence ii, OPEN-UNARBITRATED under the same A-10 umbrella). §VII.B prices the
**cap-side** convolution at $-5.5\%$ and states, in terms, that "the realized series is untouched".
The boundary months have no partner month to cancel into, so the asymmetry is not symmetric between
the legs.

The sub-claim is verified in the artifact: `h1_zero_months_diagnosis.json`
`zero_months["2022-06"].me_last_diff_b = +1.9873` against `next_month_diff_b = 8.0913`, and the
pre-window Jan–May 2022 rise of \$92.3bn is stated in §III.B but used there for the anticipation
share, not for boundary allocation.

The inventory's stated fix: **a realized-side boundary sensitivity re-allocating the June-2022 and
November-2025 boundary paydowns across the posting-cycle seam, reported the way
`settlement_months_benchmark` already does for the cap side — same machinery, opposite leg.**

## 2. What is already committed — DECLARED, NOT PREDICTED

Read from `settlement_months_benchmark_results.json` at scoping:

| object | value |
|---|---|
| committed (calendar) benchmark | `764.7482532227002` |
| production settlement kernel | `[0.1, 0.6, 0.3]` |
| cap-side aligned benchmark | `722.7482532227002`, shift **−\$42.000bn**, −5.492% |
| slower kernel `[0.0,0.5,0.5]` | `712.2482532227002`, −\$52.5bn |
| faster kernel `[0.3,0.6,0.1]` | `736.7482532227002`, −\$28.0bn |
| cap total, calendar | `1417.5`; QT-active months **42** |
| why the cap loses only at the end | the pre-QT cap is **zero**, so the window's start loses nothing; Oct-2025 drops its lag-2 tap and Nov-2025 its lags 1–2, \$42.0bn exactly |

That last row is the whole asymmetry this condition is about, and it is why the realized leg cannot
behave the same way: **the realized series is not zero before the window.**
`hazard/config.py:67` sets `START_DATE = "2021-01-01"`, so seventeen pre-window months of realized
roll-off exist and can settle *into* the window.

Nothing about the realized-side alignment has been computed.

## 3. Construction

Same machinery, opposite leg. Let $K$ be the committed kernel $[0.1, 0.6, 0.3]$ over lags $0,1,2$.

- **Realized series.** Monthly SOMA MBS roll-off from `macro.fetch_soma_mbs_monthly()`, the
  production path, from `START_DATE` through `QT_END` — **including the pre-window months**, which
  the cap-side run had no analogue for.
- **Settlement-aligned realized.** $\tilde R_t = \sum_{\ell} K_\ell R_{t-\ell}$, summed over the
  42 window months. Mass from Mar–May 2022 settles *in*; mass from Oct–Nov 2025 settles *out*.
- **Three benchmarks, reported side by side:**
  1. `calendar` — both legs calendar. Must reproduce `764.7482532227002` (P1).
  2. `cap_only` — the committed run's leg. Must reproduce `722.7482532227002` (P2).
  3. `both_aligned` — cap **and** realized convolved. **The new object.**
- **Boundary decomposition.** Report separately the realized mass entering at the start and leaving
  at the end, so the net is auditable rather than asserted — the same courtesy the cap-side run
  extends with its `shift_explained_by_window_edge` string.
- **Kernel sensitivity.** All three of the committed kernels, so the new leg is bracketed exactly
  as the old one is.

## 4. Pre-commitments

**STOP-class:**

- **E1 — both committed legs reproduce.** `calendar` returns `764.7482532227002` and `cap_only`
  returns `722.7482532227002`, each to $10^{-9}$, read live from the committed artifact. A miss
  means the realized series or the kernel is not the committed one and nothing else is comparable.
- **E2 — the cap-side edge loss re-derives.** \$42.000bn from $0.30 \times 35 + 0.90 \times 35$,
  computed rather than quoted.

**GENUINE predictions** (may fail; a miss lands with the miss named):

- **E3 — aligning both legs moves the benchmark LESS than aligning the cap alone.** The realized
  leg gains pre-window mass at the start where the cap gains nothing, so the two edge effects
  partially offset: $\lvert\text{both\_aligned} - 764.748\rvert < 42.0$. **The sign of the
  residual is not predicted** — whether `both_aligned` sits above or below the calendar benchmark
  depends on the realized path's shape at the two edges, which I have not computed.
- **E4 — the result stays a T2 disclosed sensitivity.** $\lvert\text{both\_aligned} -
  764.748\rvert$ is under **10%** of the committed benchmark, i.e. the boundary treatment does not
  move the headline. Basis: the cap-side leg came in at 5.492% and the realized leg's edge mass is
  of the same order as the cap's. **This may fail, and if it does the boundary allocation is
  material rather than a disclosure.**

## 5. Gates

- **P1/P2** the two committed benchmarks reproduce (E1), read live from
  `settlement_months_benchmark_results.json`.
- **P3** the kernel is read live and asserted `[0.1, 0.6, 0.3]`; the QT-active month count is 42.
- **P4** the realized series covers the pre-window months — assert at least 3 months before
  `QT_START` are present, since a kernel of length 3 needs them; if they are absent the run STOPS
  rather than silently convolving against zeros, which would fabricate the very asymmetry it is
  measuring.
- **P5** the boundary decomposition sums: mass-in − mass-out equals
  `both_aligned − cap_only` to $10^{-6}$bn.
- **W1** writes **only** `hazard/data/realized_boundary_allocation_results.json`; refuses to
  overwrite a differing file; rewrites no committed artifact; edits no `.tex`.
- **No engine.**

## 6. Landing rules, per branch

- **Branch A — gates pass, E3 and E4 hold.** Land one sentence in §VII.B beside the existing
  $-5.5\%$: aligning the realized leg as well as the cap moves the benchmark by less, because the
  realized series is non-zero before the window and the cap is not, and the residual stays a
  disclosed sensitivity. This **closes C-128 the way the inventory says to close it** — "if the
  movement is inside the existing tolerance, say so once and close it." New gate + test battery;
  `tab:runindex` row.
- **Branch B — E3 fails (both-aligned moves MORE than cap-only).** Land it. The offsetting
  intuition is wrong and the boundary asymmetry compounds rather than cancels; report the number
  and the decomposition that produced it, with the pre-committed direction quoted beside it.
- **Branch C — E4 fails (movement ≥10% of the benchmark).** **Escalate.** A boundary convention
  that moves the benchmark by that much is not a disclosure, and whether it changes the production
  convention is Eugene's call, not the coordinator's. Land the artifact and a record; land nothing
  in the manuscript.
- **Branch D — P1–P5 or E1/E2 fails.** Land nothing; commit a failure record.

## 7. Scope limits this spec commits to stating

1. **Month-alignment only.** Like the cap-side run, this revisits neither the cap schedule, the
   SOMA series' construction (that is C-127), the window bounds, nor the reinvestment-ceiling
   reading of the cap.
2. **The production convention stays calendar under every branch**, exactly as the cap-side run
   committed. This is a sensitivity, not a re-basing.
3. **The kernel is imported, not estimated.** `[0.1, 0.6, 0.3]` is the committed settlement-lag
   convention; this run does not re-derive it and its three-kernel bracket is the only uncertainty
   carried on it.
