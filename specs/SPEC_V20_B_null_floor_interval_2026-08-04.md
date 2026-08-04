# DRAFT SPEC V20-B — floor sampling interval on the null's recovery (`null_floor_interval`)

**Status: ADOPTED 2026-08-04 by author instruction ("run all of them"); committed BEFORE the run per Protocol B5 / TECHNICAL §43. Executed in-session under the guarded-runner pattern.**

**Amendment log:**
- **V20-B-A1 (2026-08-04, before the run).** The drafted §1 named
  `bootstrap_pathb_cluster_draws*.csv` as the sampling input; that is the Path B
  stratum-cluster layer, not the floor read's. The floor read's sampling layer
  enters the paper through the committed floor-scale interval endpoints of
  `floor_inference_correction_results.json` (binding read R2, whose marginal-scale
  image is the quoted [+2.9, +8.7]). The runner therefore maps THOSE committed
  endpoints — wild-t plus the CR1/CR2/CR3 rungs — through a PCHIP built on the
  committed floor-sweep grid converted to the shared basis, exactly the
  floor_uncertainty.py construction for the marginal (same grid, same
  edge-truncation convention, same committed $B off-node tolerance). This is
  STRONGER than drafted: zero new sampling, endpoint mapping commutes through the
  monotone map, and G-B2's draw-hash check is replaced by sha-pins on the three
  committed input artifacts. G-B1's "bit-identical at the point" becomes: node
  reproduction exact to 1e-12 plus off-node agreement with the committed
  oos_identification null rows within floor_uncertainty's committed tolerance.

**Panel trace:** R1 Q8 (v19 panel, 2026-08-04). The rate-inelastic null's 85.7%
recovery carries a floor-range band (83.9–86.9% across the off-window floor range)
but not the floor read's sampling interval, while the marginal-side machinery
already prices that layer ([+2.9, +8.7] wild-cluster). Propagate the same layer to
the null's level.

---

## 1. DESIGN (pre-committed)

Re-use the committed floor-read cluster draws
(`hazard/data/bootstrap_pathb_cluster_draws*.csv`, the stratum-cluster scheme that
produced the binding marginal interval — same draws, no new resampling). For each
draw's floor value, score the β1 = 0 null's recovery on the benchmark-consistent
shared basis; report the wild-cluster bootstrap-t interval on the 85.7% exactly as
`tab:ladder` constructs it for the marginal (Webb weights, restricted inversion),
plus the percentile read labeled under-covering, for symmetry with the marginal row.

**Anchors:** production off-window floor 4.991%; production floor form; shared
basis; identical draw files (no re-draw — this spec adds zero sampling variation).

**Output:** `hazard/data/null_floor_interval_results.json`:
`null_recovery_interval_wildt`, `null_recovery_interval_pct`, per-draw vector hash.

## 2. PARITY GATES (abort, not warn)

- G-B1: at the point floor 4.991% the scorer must return the committed 85.7%
  bit-identically. Abort otherwise.
- G-B2: the draw-file hash must equal the committed marginal-interval draw hash
  (same sampling layer, not a cousin). Abort otherwise.

## 3. EXPECTATIONS + LANDING RULES (fixed ex ante)

- **Expected:** an interval containing 85.7, on the order of the floor-range band
  (roughly ±1–2pp); recovery moves one-for-one with the floor level, so the
  interval should be close to the band's width.
- **L1 (any outcome containing the point):** land in the `tab:headline` null-row
  uncertainty cell: "floor-read wild-cluster [X, Y]%" alongside the existing
  floor-range band; one clause in §V.E. The abstract's 85.7% is unchanged — the
  interval is a table object.
- **L2 (interval fails to contain 85.7):** wiring error by construction (G-B1
  passed at the point). STOP; no landing; diagnose in the amendment log.

## 4. GATE + TESTS AT LANDING

Next free gate number: cross-artifact tie from the table cell to
`null_floor_interval_results.json`. Tests: containment of the point; draw-hash
equality with the marginal layer; band-vs-interval consistency note in TECHNICAL.
