# SPEC — R32 / C-80: the 2018 depth ladder's shape

**Status: PRE-COMMITTED. Committed BEFORE the runner, and both before the run.**
Run tag: `depth_ladder_shape`. Runner: `tools/depth_ladder_shape_run.py`.

---

## 1. The condition, and why it is an opportunity rather than a repair

C-80 (R3:M6(b), SY:Z15, MAJOR **opportunity**). §VII.F already prints the five *nested* reads of
the 2018 depth ladder. What is absent is the **shape**: the per-bin CPR, the exposure behind each
bin, and the reading the shape licenses.

The shape is **out-of-window, out-of-episode, own-data evidence on the form fork**, which the
paper otherwise argues from semantics:

- A **floor on total turnover** (the production max form) censors the voluntary hazard once the
  gap is deep enough, so per-bin CPR **steps down and then plateaus** at the floor.
- An **additive competing-risks form** never censors, so per-bin CPR should **keep falling** with
  depth as the voluntary component shrinks toward zero.

These predictions differ, and the ladder can discriminate them.

## 2. This is a re-tabulation, and every value was computed at scoping

**Declared, not predicted.** Exposure-weighted differencing of the committed nested reads in
`matched_depth_reconciliation_results.json:step2_matched_depth_grid.OFF_2018_rising_rate` was
performed during scoping, before this spec. Recording it as a "prediction" would dress up a known
answer. The measured per-bin CPRs are:

| bin (gap) | per-bin CPR | exposure | share of gap≤0 | well-supported |
|---|---|---|---|---|
| (−0.0025, 0] | **7.092** | $206.41bn | 16.32% | yes |
| (−0.0050, −0.0025] | **6.986** | $136.68bn | 10.81% | yes |
| (−0.0075, −0.0050] | **4.669** | $467.85bn | 37.00% | yes |
| (−0.0100, −0.0075] | **4.654** | $310.18bn | 24.53% | yes |
| (−0.0150, −0.0100] | **5.143** | $94.37bn | 7.46% | **no** |
| (−0.0200, −0.0150] | **4.347** | $48.71bn | 3.85% | **no** |
| (−0.0250, −0.0200] | **3.606** | $0.27bn | 0.02% | **no** |
| ≤ −0.0250 (nested) | **0.000** | $0.013bn | 0.001% | **no** |

**The shape is a step then a plateau.** CPR falls from ~7.0 to ~4.66 between the second and third
bins and then stops falling: 4.669, 4.654, 5.143 across bins covering **69% of gap≤0 exposure**.

## 3. The finding this spec commits to reporting in full, including against itself

The plateau supports the **max** form and is inconsistent with the additive form's prediction of
continued decline. But the ladder does eventually fall — 4.347, 3.606, 0.000 — and an
additive-form advocate would point at exactly those cells. So the run must report **both**, and
must state the discriminating fact: the plateau covers 69% of exposure while every declining cell
below it holds **under 4%**, the last two under 0.03%, and all of them are flagged
`well_supported: false` by the committed artifact's own rule. The reading is therefore
**support-conditional, and the support runs strongly one way.** Reporting the plateau without
the tail would be cherry-picking; reporting the tail as if it were comparable evidence would be
worse.

## 4. Gates

- **P1 (the real check on my arithmetic).** The per-bin CPRs must **re-aggregate** to the
  committed nested reads: for every threshold $t$, the exposure-weighted mean of all bins at or
  below $t$ must reproduce `cpr_pct[t]` to 1e-9. Differencing is invertible, and this asserts the
  inversion. A slip in the differencing fails here before any number is printed.
- **P2** every cell re-read live from the artifact and asserted against the digits in §2;
  `well_supported` flags read from the artifact, never hard-coded.
- **P3** exposure shares monotonically decrease with depth (nested sets), and the shallowest
  equals 1.0.
- **W1** writes only `hazard/data/depth_ladder_shape_results.json`.

## 5. Landing rules

- **Branch A — gates pass.** Land a compact exhibit in §VII.F: per-bin CPR, exposure share and
  support flag, plus the two-sentence shape reading and the support-conditionality. New gate +
  tests. **No new estimation** — every input is committed.
- **Branch B — P1 fails.** Land nothing; the differencing is wrong and the inventory's published
  values (7.09/6.99/4.67/4.65/4.87) would need re-examination too. Commit a failure record.

## 6. A wording correction this run forces

The inventory's own summary gives the fifth value as **4.87**, reading the deepest *nested* cell
(≤−0.0100, CPR 4.869) rather than the *bin* (−0.0150,−0.0100], whose differenced CPR is
**5.143**. Both are correct objects; they are not the same object. The exhibit prints **bins**
throughout and says so, and this spec records the discrepancy so it is not mistaken for an error
later.
