# DRAFT SPEC V20-A — compounding-consistent null (`compounding_consistent_null`)

**Status: DRAFT — awaiting author adoption. Protocol B5 / TECHNICAL §43: commit this
spec (promote `DRAFT_` → `SPEC_` with date) BEFORE any run. Author-only execution.**

**Amendment log:** none.

**Panel trace:** R1 W4 + Q3; EIC Q7; DA C2 (v19 panel, 2026-08-04). The engine
renormalizes both legs to realized holdings monthly, so recovery percentages cannot
compound error across months and the production marginal is an upper bound on the
compounding-consistent one — currently an admitted, unquantified bias disclosed in
the `tab:bases` (Table 11) notes. This run prices it.

---

## 1. DESIGN (pre-committed)

Re-score the production Path B central leg and the β1 = 0 rate-inelastic null with
monthly renormalization to realized holdings SWITCHED OFF: each leg evolves its own
counterfactual balance path from the June 2022 opening book (the dynamic-balance
scorer the Danish legs already implement). No other change of any kind.

**Anchors (all unchanged from production; full precision from committed artifacts):**
- Off-window floor 4.991% CPR (`oos_identification_results.json`,
  `instrument1_oow_floor.defensible_clean_floor.clean_mid_pct`).
- Central elasticity δ = 6.5%; production (max) floor form; s = 1; 100 PSA;
  production seed pairing (shared seeds across legs).

**Outputs (JSON artifact `hazard/data/compounding_null_results.json`):**
`central_recovery_cc`, `null_recovery_cc`, `marginal_cc_pp`, `marginal_cc_bn`,
plus the renormalized production triplet re-emitted by the same code path.

## 2. PARITY GATES (abort, not warn)

- G-A1: with renormalization switched back ON, the same code path must reproduce the
  committed production numbers bit-identically (85.7% / 91.3% / +5.6pp / $42.6B on
  the shared basis). Abort on any deviation: proves the only change is the scorer.
- G-A2: both legs share seeds and the balance-path engine; abort if leg configs
  differ anywhere but β1.

## 3. EXPECTATIONS + LANDING RULES (fixed ex ante)

Signing argument (Table 11 notes): the null is held to a balance path its own faster
prepayment would have drained, so **expected: `marginal_cc_pp` ≤ +5.6**.

- **L1** if +4.6 ≤ marginal_cc ≤ +5.6 (bias ≤ 1.0pp): land one sentence in the
  §V.E qualification list and update the Table 11 note from "an admitted,
  unquantified amount" to the priced value. No headline change.
- **L2** if marginal_cc < +4.6 (bias > 1.0pp): the compounding-consistent value
  becomes a named companion wherever the +5.6 anchor is quoted (abstract clause,
  `tab:headline` marginal cell, §V.E). The binding interval's caveat gains one
  sentence. This is the panel-facing outcome; do not soften it.
- **L3** if marginal_cc > +5.6: the upper-bound signing was wrong. STOP; no text
  lands; adjudicate the signing argument in the amendment log before any re-run.

## 4. GATE + TESTS AT LANDING

Reserve the next free liveness-gate number: live cross-artifact tie from the printed
sentence to `compounding_null_results.json` (no literal in the gate). Test battery:
artifact keys present; L1/L2/L3 branch consistency between artifact and prose;
G-A1 reproduction hash recorded in the manifest.
