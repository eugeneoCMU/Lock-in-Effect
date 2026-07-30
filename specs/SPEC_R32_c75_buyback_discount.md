# SPEC — R32 / C-75: re-deriving the Danish buyback discount $D$

**Status: PRE-COMMITTED. Committed BEFORE the runner, and both before the run.**
Run tag: `buyback_discount_rederived`. Runner: `tools/buyback_discount_rederived_run.py` (not yet
written; this spec lands first and stands on its own).

---

## 1. The condition

C-75 (R2:M5, EIC:W8, R3:M3, DA:m2/A5, SY:X9/Z7/R9 — **CONSENSUS**, MAJOR, RUN + WORDING). The
discount $D$ at which the Danish leg's retired face is repurchased is **asserted, never derived**:
`hazard/buyback_credit_bracket.py:107` hard-codes `D_GRID = [0.32, 0.34, 0.36, 0.38]` and `:33`
calls it "the manuscript's committed proxy range". No derivation exists in the manuscript, in
`TECHNICAL.md`, or in the artifact spec. The condition: derive $D$ from the Danish leg's **own**
simulated cash flows at its **own** 5.61% CPR against the window market-rate path, and restate
every dependent figure.

R2 attaches an explicit **pre-talk precondition** to it: the $-\$89$/$-\$118$bn range is not to be
quoted aloud until this lands. That is why this spec is drafted first.

## 2. What is already known — DECLARED, NOT PREDICTED

Three things were computed during scoping, *before this spec existed*. Recording them as
"pre-commitments" would be dressing up known answers, which this round's rules forbid. They are
declared as measurements:

1. **The committed chain and its sensitivity.** `gap_cash(D) = 61.18833737010482 - D \times
   470.6532528541021`. On the committed grid it yields `gap_cash_range_b =
   [-117.65989871445402, -89.42070354320788]`, `verdict.code = "REVERSES"`. Re-pricing the *same
   chain* at R2's asserted 21–24% limb gives **$-42.36$bn at $D = 0.22$ and $-51.77$bn at
   $D = 0.24$** — every magnitude roughly halves and REVERSES survives. This is arithmetic on the
   existing chain with a plugged-in $D$; it is **not** a derivation of $D$, which is the whole
   point of the condition.
2. **The reversal threshold is exact and is not a prediction.**
   $D_{\mathrm{crit}} = 61.18833737010482 / 470.6532528541021 = \mathbf{0.130007254808}$. The
   verdict is REVERSES for $D > D_{\mathrm{crit}}$ and SPANS_ZERO/positive at or below it. Any
   reader can derive this line; stating it up front is what makes E4 below a falsifiable
   prediction rather than a retrofit.
3. **The committed grid's own provenance is approximately reproducible.** An independent zero-CPR
   PV of a 3.0% pass-through at a 6.8% market rate gives **~34.2%**, against R2's reported 36.5%
   and inside the committed `[0.32, 0.38]` span. So the committed grid is consistent with a
   *no-prepayment annuity PV at a representative state*. That identification is plausible but not
   exactly reproduced, and this spec does not claim it is. It is used only as a parity anchor
   (P4), never as a target.

**What is NOT known and is genuinely predicted below:** the value of $D$ that comes out of pricing
each month's retired face at its own prepayment-consistent PV. Nothing in scoping computed it.

## 3. Inputs, all committed

| object | path | value used |
|---|---|---|
| par gap | `danish_us_intercept_results.json:point` | `institutional_gap_shared_b = 61.18833737010482` (US `748.9678825340305` − DK `687.7795451639257`) |
| monthly paths | `microsim_results_us_intercept.parquet` | 42 rows, 2022-06-30 … 2025-11-30; `market_rate_pct`, `CPR_Danish`, `Danish_simulated_rolloff_b`, `weighted_sched_b` |
| early face | derived | $E = \sum_t \lvert\text{Danish rolloff}_t\rvert - \sum_t \text{sched}_t = 470.6532528541021$ |
| leg speed | `danish_us_intercept_results.json` | `mean_danish_cpr_pct = 5.613626373336359` (the printed 5.61%) |
| amortization machinery | `hazard/wal_table.py` (imported; `main()` never called) | `WAC = 0.0249`, `VINTAGE_SHARES`, `TERM_SPLIT`, `AGES_JUNE_2022`, `cell_wal` |
| committed grid (parity only) | `hazard/buyback_credit_bracket.py:107` | `D_GRID = [0.32, 0.34, 0.36, 0.38]` |

sha256 pins to be asserted live at run time:

```
26308a9ff7de7ca86f5753ba63129758cdf2b76907d84e5a6f30a16bfce70b32  hazard/wal_table.py
0cb900263d9d6a4f093e6aae1408b5cc55a52fee40771d008bf95a7127d2e7dc  hazard/buyback_credit_bracket.py
38041df75a57ff1e86f224e7085b5465e521f0b07b861ffcc9427139aa44b28a  hazard/data/microsim_results_us_intercept.parquet
b810a1dae636617f9417c6a343c55d67ec6c8659b7a3dfcb55e134b804e1aca7  hazard/data/danish_us_intercept_results.json
dba71c544f9b116848731d12983258538e697813388f7632887e1eaa84c35881  hazard/data/buyback_credit_bracket_results.json
```

## 4. Construction

**The mixed basis is inherited deliberately, not repaired.** $E$ nets the Danish leg's total
roll-off against the **U.S. leg's** scheduled path — that is the manuscript's own netting
convention behind its "roughly \$199 billion scheduled component", and `buyback_credit_bracket.py`
computes $E$ exactly that way. This run reproduces the convention rather than improving it, so
that the re-derived $D$ is the only thing that changes between the committed bracket and this one.
The runner must state this in its artifact.

For each window month $t = 1 \dots 42$:

- **Early face retired.**
  $F_t = \lvert\text{Danish\_simulated\_rolloff\_b}_t\rvert - \text{weighted\_sched\_b}_t$.
  By construction $\sum_t F_t = E$ (asserted as P2).
- **The book as of $t$.** Every (vintage, term) cell of `wal_table`'s single-pool tabulation, aged
  `AGES_JUNE_2022[vintage] + (t-1)` months, face-weighted by
  `VINTAGE_SHARES` $\times$ `TERM_SPLIT`.
- **Cash flows.** Level-payment at `WAC = 0.0249` with monthly
  $\mathrm{SMM}_t = 1-(1-\mathrm{CPR\_Danish}_t)^{1/12}$ applied to the surviving balance —
  **the identical recursion `wal_table.cell_wal` runs**, with the per-month principal vector
  $p_m$ retained instead of collapsed to a WAL.
- **Price.** $P_t = \sum_m (p_m + i_m)\,/\,(1 + y_t/12)^m$ per unit of month-$t$ balance, where
  $i_m$ is the month-$m$ interest on the surviving balance and $y_t =$
  `market_rate_pct`$_t\,/\,100$. Face-weighted across cells to a book price $P_t$.
- **Discount.** $D_t = 1 - P_t$, floored at nothing and capped at nothing — if a month prices
  **above** par, $D_t$ is negative and is reported as such.
- **Haircut.** $H = \sum_t D_t F_t$; face-weighted mean discount $\bar D = H / E$.
- **Cash gap.** $\text{gap\_cash} = \text{gap\_par} - H$, and equivalently
  $= 61.18833737010482 - \bar D \times 470.6532528541021$, which must agree to 1e-9 (P3).

The **face incidence is unchanged and is an identity, not a computation**:
$\text{gap\_face} = \text{gap\_par} = +\$61.19$bn. This run cannot and does not move it.

## 5. Pre-commitments

**STOP-class** (a failure means the construction is wrong; land nothing in the manuscript):

- **E1 — monthly decomposition is well posed.** $F_t > 0$ for all 42 months and
  $\lvert\sum_t F_t - E\rvert < 10^{-9}$. A negative $F_t$ would mean a month whose scheduled
  amortization exceeds the Danish leg's whole roll-off, and the netting convention would not
  survive at monthly grain.
- **E2 — the pricing primitive is monotone.** Holding CPR and age fixed, $D_t$ is strictly
  increasing in $y_t$; holding $y_t$ and age fixed, $D_t$ is strictly **decreasing** in CPR (faster
  prepayment pulls a discount bond toward par). A violation means the PV is mis-wired.

**GENUINE predictions** (may fail; a miss lands with the miss named):

- **E3 — the committed grid is uniformly too deep.** $D_t < 0.32$ at **every one of the 42
  months**, not merely on the face-weighted average. Rationale: the committed grid prices at a
  6.8% market rate against a window whose mean is 6.607% and whose minimum is 5.231%, and it
  prices at **zero** prepayment against a leg running 5.61% CPR. Both differences push $D$ down,
  so the committed floor should be cleared everywhere. **If even one month prices at or above
  0.32, this fails** — and the interesting case is the window's late high-rate months.
- **E4 — level.** $\bar D$ lands in $[0.13, 0.32)$: strictly below every committed grid point and
  strictly above $D_{\mathrm{crit}} = 0.130007$. The lower edge is the substantive one, because
  it is exactly the verdict-flipping threshold of §2.2. **I do not know $\bar D$ and this may
  fail in either direction.**
- **E5 — the verdict survives, smaller.** `gap_cash < 0` (REVERSES holds), **and**
  $\lvert\text{gap\_cash}\rvert < 89.42070354320788$ — strictly inside the committed range's near
  edge. E5 is implied by E4 arithmetically; it is stated separately because it is the claim the
  manuscript prints and the gate pins, and it must be checked as printed rather than inferred.

**The failure that would matter most, named in advance.** If $\bar D \le D_{\mathrm{crit}}$ the
verdict becomes SPANS_ZERO or positive, the "REVERSES at every proxy discount" line at `.tex:1470`
becomes **false as written**, and the incidence bracket stops reversing the gap at all. That is a
result that lands. It would *strengthen* the paper's face-accounting reading and retire a
concession — which is precisely why it must be pre-authorised here rather than adjudicated after
the fact.

## 6. Gates

- **P0** sha256 pins above asserted live; **P0a** AST check that importing `hazard/wal_table.py`
  binds names only (no module-level call); **P0b** every input artifact byte-identical after
  import and again at exit.
- **P1 (the machinery-identity gate).** For every (term, age, CPR) cell this runner prices, the
  WAL implied by its own retained principal vector $p_m$ equals `wal_table.cell_wal(term, age,
  cpr)` to $10^{-12}$. This is what certifies the cash flows being discounted are the committed
  amortization's cash flows and not a re-implementation. Additionally the `danish_us_intercept`
  row (CPR 0.0561) and the five `V15_PRINTED` parity pairs reproduce at the table's printed
  precision.
- **P2** $\sum_t F_t = E$ to 1e-9, and $E$, `gap_par`, `US_shared`, `DK_shared` all re-read live
  and asserted against `buyback_credit_bracket.py`'s header constants to 1e-9.
- **P3** the committed chain reproduces **bit-identically**: at each $D \in \{0.32, 0.34, 0.36,
  0.38\}$, `gap_par - D*E` equals the committed
  `buyback_credit_bracket_results.json:verdict.cash_rows` entry exactly, and the committed
  `gap_cash_range_b` endpoints are recovered. The new bracket must sit on the old chain with only
  $D$ changed.
- **P4 (provenance anchor, non-targeting).** The same PV primitive evaluated at **zero CPR, 3.0%
  coupon, 6.8% market** lands inside the committed grid's own span $[0.32, 0.38]$. This checks
  that the primitive reproduces where the committed grid came from. It is a **band check against
  the committed grid, not against the 34.2% scoping value**, so it cannot be tuned toward a
  remembered number.
- **P5** the window is 42 months, `mean(CPR_Danish)` re-read live equals `5.613626373336359` to
  1e-12, and `market_rate_pct` min/max are recorded in the artifact.
- **W1** writes **only** `hazard/data/buyback_discount_rederived_results.json`; refuses to
  overwrite a differing file; **touches no `.tex` file and does not rewrite
  `buyback_credit_bracket_results.json`.**

## 7. Landing rules, per branch

- **Branch A — all gates pass, E1–E5 hold.** Land the re-derived bracket. Concretely:
  (i) restate the range at `.tex:52`, the T1 row `.tex:85`, and every dependent site
  (`.tex:656` notes to `tab:danish`, `.tex:658`, `.tex:766`, `.tex:1470`);
  (ii) **update gate #103** — `BUYBACK_BRACKET_SPANS["reversal_range"]` in
  `tools/liveness_gates.py` currently pins the literal `"$-\$89.4$ to $-\$117.7$ billion"` and
  `tests/test_buyback_incidence_gate.py::test_each_span_removal_fails` asserts each span is
  present. **The gate is updated to the re-derived range, never bypassed or deleted**;
  (iii) add a sentence stating that $D$ is now derived from the leg's own 5.61% speed and the
  window's own rate path rather than asserted at a representative state, and that the committed
  proxy grid was uniformly too deep;
  (iv) new gate + test battery pinning the re-derived range, $\bar D$, and $D_{\mathrm{crit}}$;
  (v) `tab:runindex` row.
  C-49's band and C-51's mechanics sentence land with it.
- **Branch B — all gates pass, E3 and/or E4 miss but E5 holds (REVERSES survives).** **Land
  anyway.** Same edits as Branch A, with the pre-committed band quoted beside the realized value
  and the miss named in the text.
- **Branch C — E5 fails: $\bar D \le D_{\mathrm{crit}}$, the verdict no longer REVERSES.**
  **Land anyway, and land the harder version.** The `.tex:1470` adjudication row
  ("REVERSES at every proxy discount") is restated as falsified-by-re-derivation; the incidence
  bracket is reported as spanning zero or failing to reverse; §VI.D's and §VIII's
  incidence-conditional hedges are re-scoped to say the reversal was an artifact of an asserted
  discount. Gate #103's `reversal_range` span is replaced by a span pinning the *new* verdict.
  This is the branch that most changes the paper and it is pre-authorised in full.
- **Branch D — P0/P0a/P0b/P1/P2/P3/P4/P5 or E1/E2 fails.** Land **nothing** in the manuscript.
  Commit the runner output and a failure record under `specs/`. The committed bracket stands and
  R2's pre-talk precondition stays unmet — which must be said plainly rather than quietly
  dropped.

## 8. Scope limits this spec commits to stating

1. **This prices the discount, not the option.** The manuscript's standing concession at
   `.tex:658` — that under a market-value payoff rule the repurchase option would be priced into
   the coupon ex ante, an omission signed *against* the reported relief — is untouched by this
   run and must remain stated. Re-deriving $D$ narrows the bracket; it does not close that gap.
2. **One anchor only.** The production U.S.-intercept leg is the only committed pair with a
   monthly decomposition. The off-window $+\$28.2$bn cell and the Danish-level bracketing anchor
   are **out of scope**, and any restatement must be scoped to the in-sample production pair
   exactly as the committed bracket already is.
3. **Two grains, stated.** $D_t$ is priced on the SOMA book's single-pool vintage tabulation at a
   2.49% WAC, while $F_t$ comes from the microsimulated Freddie panel's roll-off. These are two
   populations, as they already are in the committed $E$; the run inherits that seam and names it
   rather than implying one object was priced end to end.
4. **The scheduled leg carries no discount.** Scheduled amortization is contractual cash at par
   under both rules — the committed bracket's assumption, preserved here unchanged.
