# SPEC — R32 / C-94: a note-rate-basis row for tab:wal's empirical path

**Status: PRE-COMMITTED. Written and committed BEFORE the runner, and both before the run.**
Run tag: `wal_note_rate_basis`. Runner: `tools/wal_note_rate_basis_run.py`.

---

## 1. The condition, and what is actually wrong

C-94 (R2 minor 2, MINOR, STRUCTURE). `tab:estimators` already prints all three bases for the
empirical SOMA CPR — "mean CPR 5.14\% (ABM-basis back-out; hazard-basis 5.52\%, 5.79\% at the
note-rate WAC)" — while `tab:wal`'s empirical row uses **5.14\% alone**. So the corrected
basis is disclosed but never becomes the comparator: every duration statement in the paper is
read off a row computed on the ABM-basis back-out.

The note-rate WAC is the *physically* correct convention for an amortization calculation: the
borrower's note rate is what amortizes the loan, and `wal_table.py` amortizes at `WAC = 0.0249`,
a pass-through coupon. The paper itself calls the note-rate leg "the corrected amortization
basis" (run `coupon_convention_amortization`) at the Theil table.

**What is NOT being attempted.** R2's single-pool 7.72 → 7.25-year recomputation is not
reproducible from committed artifacts and is not comparable to this table's blended 9.4. This
spec does not try to reproduce it. The structural point — the comparator must be available at
the corrected basis, with each row's basis named — is what lands.

## 2. Inputs, pinned

| object | path | sha256 |
|---|---|---|
| calculator | `hazard/wal_table.py` | `26308a9ff7de7ca86f5753ba63129758cdf2b76907d84e5a6f30a16bfce70b32` |
| frozen companion | `hazard/data/wal_table_results.json` | `1aeaf45b47e6622d02dcf55470ca740902beb45292454726c9d859a9cc2bf18a` |
| basis source | `hazard/data/coupon_convention_amortization_results.json` | `700489452b691f8ad0235ccb6a3af2c52089fca19fe267faf36ece0184926174` |

The calculator is **imported, never executed as a program**; `main()` is its only writer and is
never called. A changed calculator or a changed frozen artifact is a **STOP, not a re-baseline**.

**The CPR.** `hazard_legs.delta_080.mean_cpr_pct = 5.785664704297843` — the 0.80pp
g-fee-plus-servicing wedge leg, which that run's own spec names primary, and the value the
manuscript prints as 5.79\%. It is read **live from the artifact**, not written as a literal in
the runner; the runner asserts the read value against the pinned digits.
Companion committed on the same artifact: `hazard_legs.committed_0250.mean_cpr_pct =
5.518089009047279` (the "hazard-basis 5.52\%").

**Precision convention.** 2-decimal percent (`0.0579`), exactly as all nine committed
scenarios (`path_b` is `0.0476` from 4.763...). Gate P3 asserts the *printed* row does not
depend on this choice.

## 3. Pre-committed expectations

Derived by linear interpolation from **already-committed printed rows only**, before the run:
`empirical` 5.14\% → 9.4 / 8.5 and `danish_us_intercept` 5.61\% → 9.1 / 8.2 give a local slope
of −0.3 / 0.47 ≈ **−0.64 yr per CPR point** at both dates. From 5.14 to 5.79 is +0.65 points.

- **E1 (level).** WAL June 2022 ∈ **[8.8, 9.2]**, Nov 2025 ∈ **[7.9, 8.3]**.
  Central expectation **9.0 / 8.1**.
- **E2 (the stake).** Basis effect at June 2022 = `empirical(5.14%) − note_rate(5.79%)`
  predicted **≈ 0.4 years**, band **[0.2, 0.6]**. The pre-committed reading: this is **the same
  order as** the 0.6-year Danish rule-only WAL effect the paper reports. If it lands below 0.2
  the condition's stake claim is wrong and I say so.
- **E3 (monotonicity, STOP-class).** The note-rate row must be **strictly shorter** than the
  5.14\% empirical row at both dates. A higher constant CPR cannot lengthen WAL in this
  calculator. A violation means the calculator is not behaving monotonically and **nothing
  lands**.

**An unfavourable result still lands.** E1/E2 are predictions, not conditions of landing.

## 4. Gates

- **P0** — both sha pins match; **P0a** — the calculator's module body only binds names
  (AST check, so importing cannot touch the filesystem); **P0b** — the frozen artifact is
  byte-identical after the import and again at exit.
- **P1** — all nine committed rows recomputed **bit-identically** against the frozen artifact,
  plus `extension_years_vs_no_shock` and `rule_only_wal_shortening_years`.
- **P2** — the basis artifact's sha matches, and the two CPRs read out of it equal the pinned
  full-precision digits above; the note-rate leg must exceed the hazard-basis leg (else the
  wedge has the wrong sign).
- **P3** — the printed row is identical whether computed from the 2-decimal CPR or the
  full-precision one.
- **W1** — write guard. The runner writes **only**
  `hazard/data/wal_note_rate_basis_results.json`, and refuses to overwrite a differing
  existing file. A re-run that reproduces the committed artifact exactly is a no-op.

## 5. Landing rules, per outcome branch

- **Branch A — all gates pass, E1 and E2 hold.** Land: one row in `tab:wal` at the note-rate
  basis; a `tab:wal` tablenote sentence naming **which basis each row uses**; a `tab:runindex`
  row; a new liveness gate tying the printed row to the artifact (no literal in the gate); a
  test battery. Record in TECHNICAL.
- **Branch B — all gates pass, E1 and/or E2 misses.** **Land anyway**, and state the miss in
  the tablenote and in TECHNICAL with the pre-committed band quoted beside the realized value.
- **Branch C — any of P0/P0a/P0b/P1/P2/P3/E3 fails.** Land **nothing** in the manuscript.
  Commit the runner output and a failure record.

## 6. A limitation this spec commits to stating rather than papering over

The 6.0-year extension is `empirical − no_shock_2021_speeds`. The no-shock row's 22.81\% is a
2021 **FRED/SOMA back-out on the ABM basis**; there is no committed note-rate counterpart of
it. This run therefore **does not recompute the extension on the note-rate basis**, because
differencing a note-rate WAL against an ABM-basis WAL would mix conventions inside a single
statistic — the exact defect C-94 exists to remove. The tablenote says so. What the new row
licenses is a **like-for-like basis sensitivity of the empirical row itself** (E2), not a
restated extension.
