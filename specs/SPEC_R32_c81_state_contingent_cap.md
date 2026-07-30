# SPEC — R32 / C-81: the state-contingent cap's two-input table

**Status: PRE-COMMITTED. Committed BEFORE the runner, and both before the run.**
Run tag: `state_contingent_cap_grid`. Runner: `tools/state_contingent_cap_run.py`.

---

## 1. The condition

C-81 (R3:M4(b), MAJOR, RUN — **re-tabulation, no new estimation**). §VI.B raises indexing the
cap "to the share of the book sitting deeply below market coupon" and stops. The condition: that
proposal supplies **no function from the observable to a cap level**. What is required is a
two-input grid — book out-of-the-money share at depth cuts × turnover-floor band — mapping to
achievable monthly principal and hence to an implied cap.

This lands beside C-54, which put the same paragraph's result into $bn/month.

## 2. A deviation from the condition's own grid, and why

The inventory proposes cuts at **200/300/400 bp**. This spec uses **0 / 25 / 50 bp** instead,
because those are the cuts at which the paper's floor reads actually exist:
`oos_identification_results.json:instrument1_oow_floor.defensible_clean_floor` carries exactly
three reads, `clean_hi_pct = 5.334` (`gap <= 0`), `clean_mid_pct = 4.991` (`gap <= -0.0025`) and
`clean_lo_pct = 4.695` (`gap <= -0.005`), with `primary_point_selection = gap<=-0.0025_age>=12`.
The gap is a decimal rate fraction, so those are 0, 25 and 50 bp of out-of-the-moneyness.
Reading the grid at 200/300/400 bp would require **new floor reads**, which is new estimation and
is exactly what this condition forbids.

## 3. Inputs, all committed

| object | path | value used |
|---|---|---|
| book composition | `composition_shift_results.json:soma_book.asof_june_2022` | face `$2,700.5637bn`, WAC `2.4710%`, `coupon_shares` (11 buckets, 0.5% grid) |
| reference market rate | `sign_forcing_stats_results.json:statistics.window_min_mortgage30us_pct` | `5.231111111111111` |
| floor reads + band | `oos_identification_results.json` | 5.334 / 4.991 / 4.695; wild-cluster interval **4.177–5.800** at the mid cut |
| amortization machinery | `hazard/wal_table.py` (imported, `main()` never called) | WAC 0.0249, `VINTAGE_SHARES`, `TERM_SPLIT`, `AGES_JUNE_2022` |

## 4. Construction

For depth cut $d \in \{0, 25, 50\}$ bp:

- **Observable.** $s(d)$ = book face share with coupon $\le$ (reference rate $- d$).
- **Floor.** $f(d)$ = the committed read at that cut.
- **Achievable passive principal.** Per (vintage, term) cell at its June-2022 age, on
  `wal_table`'s own level-payment schedule at WAC 2.49%: monthly principal = scheduled principal
  + $\mathrm{SMM}(f)\times$(surviving balance $-$ scheduled), with
  $\mathrm{SMM} = 1-(1-f)^{1/12}$, averaged over the 42 window months and scaled by book face.
- **Implied cap** = that achievable monthly principal — the level at which a cap stops binding.
- **Band.** The same computation at the mid cut's wild-cluster endpoints 4.177% and 5.800%.

## 5. Pre-commitments — and one declared non-prediction

**DECLARED, NOT PREDICTED.** The observable limb was computed during scoping, *before this spec
was written*, from the committed artifact. Recording it as a "prediction" would be dressing up a
known answer, which this round's rules forbid. The measured values are:

| cut | coupon threshold | OTM share |
|---|---|---|
| 0 bp | 5.2311% | **99.9082%** |
| 25 bp | 4.9811% | **99.5853%** |
| 50 bp | 4.7311% | **99.5853%** |

The 25 and 50 bp cuts coincide because the book's coupons sit on a 0.5% grid, so no bucket falls
between the two thresholds. **The observable is therefore near-degenerate: it is pinned above
99.5% at every cut and does not discriminate.** That is a finding about the proposal, and it
lands whichever way the rest falls.

**GENUINE pre-commitments** (the achievable-principal limb has NOT been computed):

- **E1 (ordering).** Achievable monthly principal is strictly increasing in the floor:
  $A(4.695) < A(4.991) < A(5.334)$, and the band satisfies $A(4.177) < A(4.991) < A(5.800)$.
  A violation is a **STOP** — it would mean the amortization is not monotone in CPR.
- **E2 (level).** Achievable principal lands in **$14–26 bn/month**, i.e. materially below the
  $33.75bn/month ceiling C-54 prints, at every grid point. Rationale: C-54's projected runoff
  averaged $17.6–20.0bn/month over the same window and the same book.
- **E3 (the condition's substantive question).** The spread in achievable principal across the
  three depth cuts is **smaller** than the spread across the mid-cut floor band. If E3 holds, the
  designer's observable buys less than the floor's own sampling error, and the indexing proposal
  is not merely weak but dominated by measurement uncertainty. **I do not know this in advance
  and it may fail.**

## 6. Gates

- **P0** sha pins on `wal_table.py` and its frozen companion; **P0a** AST import-safety check;
  **P0b** artifacts byte-identical after import and at exit.
- **P1 (the parity gate C-81 names).** All **nine committed `tab:wal` rows** reproduced
  bit-identically through the same amortization primitives this runner uses, plus
  `extension_years_vs_no_shock` and `rule_only_wal_shortening_years`. This is what certifies the
  monthly-principal extraction is the committed machinery and not a re-implementation.
- **P2** floor reads and the ordering `lo < mid < hi` read live from the floor artifact;
  `primary_point_selection` unchanged.
- **P3** book shares sum to 1 within 1e-9; reference rate matches the pinned digits.
- **W1** writes **only** `hazard/data/state_contingent_cap_grid_results.json`; refuses to
  overwrite a differing file.

## 7. Landing rules, per branch

- **Branch A — gates pass, E1–E3 hold.** Land a compact two-input table (or a tablenote-sized
  grid) in §VI.B beside C-54's $bn/month sentence, stating the implied cap at each cell, the
  near-degenerate observable, and the E3 comparison. New gate + test battery.
- **Branch B — gates pass, E2 and/or E3 miss.** **Land anyway**, with the pre-committed band or
  claim quoted beside the realized value and the miss named in the text.
- **Branch C — P0/P0a/P0b/P1/P2/P3 or E1 fails.** Land **nothing** in the manuscript; commit the
  runner output and a failure record.

## 8. Scope limit this spec commits to stating

The observable $s(d)$ is computed on the **SOMA book's bucketed coupon distribution**, while the
floor read $f(d)$ is estimated on the **Freddie loan-level panel's** gaps. They are two
populations and two grains, and the table must say so rather than implying one object was cut
three ways. The 0.5% coupon bucketing is also what makes the 25 and 50 bp cuts coincide; a
finer book tabulation is not available from the CUSIP parse.
