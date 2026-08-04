# DRAFT SPEC V20-C — few-cluster coverage simulation (`fewcluster_coverage`)

**Status: DRAFT — awaiting author adoption; promote to `SPEC_` with date before any
run. Author-only execution. NOTE: this spec can change the paper's quoted binding
interval; read §3 before adopting.**

**Amendment log:** none.

**Panel trace:** R1 W3 + Q1 (v19 panel, 2026-08-04); DA C3 (adjacent). The floor
read rests on 31 nominal clusters worth 5.9 effective (Herfindahl-inverse) with
maximum single-cluster leverage 0.33. The paper quotes the Webb wild-cluster
bootstrap-t [+2.9, +8.7] as the binding layer over the wider CR2/CR3
Bell–McCaffrey reads ([+2.4, +9.1], [+2.3, +9.6]) — a choice asserted, not
defended. This run defends it or replaces it, by pre-committed rule.

---

## 1. DESIGN (pre-committed)

Monte Carlo calibrated to the actual floor-read design:
- G = 31 clusters with the empirical cluster sizes and the empirical design matrix
  (leverage profile reproduced, max leverage 0.33), taken from the committed
  floor-read regression inputs.
- DGP: cluster random effects with intra-cluster correlation matched to the
  point-estimated value from the production read; disturbance scale matched to the
  residual variance; true coefficient = the production point estimate. Secondary
  DGP cell: heavy-tailed (t5) disturbances, same moments, as a robustness cell.
- S = 5,000 simulation draws; B = 999 bootstrap replications within each draw.
- Constructions evaluated, nominal 95%: percentile bootstrap; CR1-t(G−1); CR2 + BM
  dof; CR3 + BM dof; Webb wild-t; Rademacher wild-t; restricted wild-t inversion.
- Oracle cell (known-variance interval) as harness sanity.

**Output:** `hazard/data/fewcluster_coverage_results.json`: per-construction
empirical coverage and mean width, both DGP cells, oracle coverage.

## 2. PARITY GATES (abort, not warn)

- G-C1: oracle coverage in [94.0, 96.0] in both DGP cells; abort otherwise (the
  harness itself is miscalibrated).
- G-C2: the simulated design matrix's effective cluster count must equal 5.9 ± 0.1
  and max leverage 0.33 ± 0.01 against the committed values; abort otherwise.

## 3. DECISION RULE + LANDING (fixed ex ante — this is the part with teeth)

**Binding layer := the narrowest construction whose Gaussian-cell coverage ≥ 93.0%
AND heavy-tail-cell coverage ≥ 91.0%.**

- **L1 (Webb wild-t qualifies):** it retains binding status; land one sentence in
  §V.E and a `tab:ladder` note reporting its simulated coverage; no number changes.
- **L2 (Webb fails, a BM sandwich qualifies):** the qualifying read becomes the
  quoted binding interval EVERYWHERE the current [+2.9, +8.7] appears — abstract,
  `tab:headline`, §V.E, conclusion — with the ladder note recording why. If that
  read is CR3+BM, the quoted range becomes [+2.3, +9.6]. Do not soften this landing.
- **L3 (nothing qualifies):** quote the widest bias-respecting read with an
  explicit under-coverage warning in the same sentence; record in the amendment log.

## 4. GATE + TESTS AT LANDING

Next free gate number: the quoted binding interval in the manuscript must equal the
construction selected by the artifact's decision-rule field (live tie, no literal).
Tests: gate fires on artificial artifact perturbation (all three landing branches);
oracle-coverage bounds; leverage-profile equality.
