# SPEC — R32 / C-76: the marginal in transaction counts

**Status: PRE-COMMITTED. Committed BEFORE the runner, and both before the run.**
Run tag: `marginal_transaction_counts`. Runner: `tools/marginal_transaction_counts_run.py`.

---

## 1. The condition

C-76 (R3:M1/M2, DA:S1, SY:X5/Y1/R12 — **consensus**, MAJOR). The central-minus-null differential
must be converted into a **count of foregone payoffs**, with the moving-share bracket applied,
grossed to the whole market by the SOMA exposure share, and set against realized existing-home-
sale volume × the mortgage-financed share — **verdict stated whichever way it falls**.

It is the paper's first outcome-side external check and the only unit in which the household leg
becomes commensurable. **C-82 (Table 1's household row) is blocked on it.**

## 2. The comparator is NOT SOURCEABLE, and this spec says so before the run

Tested against the live FRED API on this project's key, before writing this spec:

- **`EXHOSLUSM495S`** (existing home sales) returns **13 observations, 2025-06-01 onward only**.
  There is no 2022–2024 history on this account, exactly as the continuation handoff warned.
- **`HSN1F`** has full history but is **new** one-family home sales — a new-home sale retires no
  existing mortgage, so it is the wrong comparator and is not substituted.
- `fonseca2026` (NBER 35237) supplies the **40% drop in U.S. existing home sales between 2022
  and 2024**, verified verbatim, but as a *percentage*; its own source is FRED/NAR and it does
  not state extractable levels. A percentage cannot be turned into a count without a level.

**Consequence, pre-committed:** the run computes the count and expresses it against the **one
level it can source** — the 2025 existing-home-sale run rate from FRED — and **does not compute
a "share of the 2022–2024 decline"**, because pinning the 2022 level would require assuming
2024 ≈ 2025. That assumption is not made. The missing statistic is recorded as infeasible with
its reason, not silently replaced by a weaker one.

## 3. Inputs, all committed

| object | source | value |
|---|---|---|
| marginal by moving share | `moving_share_bracket_offwindow_results.json` | null 724.9181; s=0.25/0.5/1 → 738.8455 / 750.6252 / 767.5265 ($bn) |
| representative balance | `loan_sample.parquet`, surviving loans only | mean of `balance > 0` |
| SOMA book face | `composition_shift_results.json:soma_book.asof_june_2022` | $2,700.5637bn |
| window | — | 42 months |
| comparator level | FRED `EXHOSLUSM495S`, 2025 observations | fetched live, recorded in the artifact |

**Denominator choice, stated because it matters.** The count uses the mean balance of
**surviving** loans (`balance > 0`), not the all-loan mean. The all-loan mean (126,812.61)
averages in prepaid loans at zero balance and would roughly **double** the implied count. A
payoff retires a live balance, so the surviving mean is the correct divisor and the all-loan
mean would be a mistake.

## 4. Construction

For each moving share $s \in \{0.25, 0.5, 1\}$:

1. marginal $M(s)$ = cell trapped $-$ null trapped, in $bn.
2. **book-level foregone payoffs** = $M(s) \times 10^9 / \bar{b}$, $\bar{b}$ = surviving mean balance.
3. **whole-market gross-up** = book count $/\ \sigma$, where $\sigma$ = SOMA book face / total
   1–4 family mortgage debt. **$\sigma$ is not a committed artifact of this repo**, so the run
   reports the gross-up as a *range* over $\sigma \in [0.20, 0.22]$ and labels it a bracket, not
   a point.
4. annualize by $\times 12/42$.
5. express against the sourced 2025 existing-home-sale run rate.

## 5. Pre-commitments

- **E1 (ordering, STOP-class).** Counts strictly increase in $s$. A violation means the bracket
  is wired backwards.
- **E2 (level).** The $s=1$ whole-market annualized count lands in **150k–400k payoffs/year**.
  Derivation: $42.6$bn / ~$237k ≈ 180$k over 42 months ≈ 51k/yr at book scale, grossed by
  ~1/0.21.
- **E3 (the substantive one).** The $s=1$ annualized count is **under 10%** of the sourced 2025
  existing-home-sale run rate — i.e. the identified lock-in marginal accounts for a small
  minority of transaction volume, not a majority. **I do not know this and it may fail.**

`s=1` is the paper's production convention and makes the count an **upper bound** on the moving
component; the text must say so.

## 6. Gates

- **P1** the three cells and the null re-read live from the committed artifact and asserted
  against the pinned digits; ordering null < s=0.25 < s=0.5 < s=1.
- **P2** surviving-balance denominator recomputed from the parquet and asserted > the all-loan
  mean (guards the wrong-divisor mistake).
- **P3** the marginal at $s=1$ reproduces the headline **$+5.6$pp / $+\$42.6$bn** at printing
  precision — ties this run to the paper's own headline.
- **P4** the FRED fetch either succeeds and is recorded with its observation dates, or the run
  records `comparator_sourced: false` and **still lands** the count.
- **W1** writes only `hazard/data/marginal_transaction_counts_results.json`.

## 7. Landing rules

- **Branch A** — gates pass, E1–E3 hold: land the count with its bracket in §VI.A, the upper-
  bound framing, the unsourceable-decline disclosure, and a `tab:runindex` row. Then **C-82**
  becomes unblocked and Table 1 gets its household row.
- **Branch B** — gates pass, E2 and/or E3 miss: land anyway with the miss named.
- **Branch C** — P1/P2/P3 or E1 fails: land nothing; commit a failure record.
