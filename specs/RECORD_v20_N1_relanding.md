# RECORD — N1 re-landing: the binding interval under SPEC_V20_C's frozen rule

**Status:** landing plan, 2026-08-05, adopted by author instruction ("Apply the
frozen rule") after the v20 re-review panel's MAJOR finding N1. Written BEFORE
the edits, per house discipline. Companion to
`SPEC_V20_C_fewcluster_coverage_2026-08-04.md` and
`RECORD_v20_fresh_eyes_shortening_menu.md` §7.

## 1. The adjudication (facts, all verified against committed artifacts)

`hazard/data/fewcluster_coverage_results.json`:
- coverage (Gaussian/t5): webb_wild_t **90.84 / 91.42** — fails spec §3's
  pre-committed bar (≥93.0 / ≥91.0); rademacher 91.40/91.72 — fails; cr3_t
  90.88/91.96 — fails; **restricted_webb 94.34 / 95.08 — qualifies**; cr2_bm
  qualifies but is wider (mean width 0.00232 vs 0.00140 SMM).
- `qualifying = [cr2_bm, restricted_webb]`; `binding_construction =
  restricted_webb` (narrowest qualifying — the rule's own selection);
- `landing_branch = "L1_webb_retains"` — **wrong**: L1 requires the Webb
  wild-t itself to qualify. The artifact string stays unedited (sha-pinned
  replication object, per the `lag_interpretation` precedent); the manuscript,
  gate #125, and the verdict ledger record the corrected landing.

`hazard/data/floor_inference_correction_v2_results.json`, read R2 (mid-grid
anchor), rung `wcr_inverted`: marginal **[+2.2809, +9.1093] pp** (prints
**+2.3 to +9.1**), floor units **[4.0335%, 6.1813%]** (prints 4.033% to
6.181%). Webb rung for comparison: [+2.8550, +8.6780] pp; floor [4.1767%,
5.8003%].

**Landing (spec §3 + L2 semantics):** the quoted binding interval becomes the
restricted wild-cluster inversion's **[+2.3, +9.1]** everywhere the current
[+2.9, +8.7] is quoted *as binding*; the ladder note records why; gate #125
gains spec §4's live tie (manuscript interval == the construction named by
`binding_construction`). "Do not soften this landing."

Placement facts re-checked at the new interval (all survive): +5.6 sits just
below the midpoint (5.70); the additive scaled-null member +8.5 remains in the
upper half; the ϕ* production member +0.9 still falls outside; the lower edge
+2.3 remains above zero on every corrected read.

## 2. Manuscript edits (both variants; canonical-only where marked ABS)

| # | Site (canonical line) | Edit |
|---|---|---|
| M1 | Abstract L31 (ABS) | "+2.9 to +8.7 points under the production floor form" → "+2.3 to +9.1"; "(the floor read's sampling error at the central elasticity, wild-cluster on 31 clusters)" → name the restricted inversion |
| M2 | Intro L44 | interval + "which is the binding layer" sentence → new numbers + construction |
| M3 | Table 1 headline row L71 | interval, "(31 clusters; percentile read [+3.0,+8.0], under-covering; …)" retained; name construction |
| M4 | II L105 | "bounded between +2.9 and +8.7 points … (a wild-cluster interval …)" → new numbers |
| M5 | V.E q1 L296 | "puts the max-form member at +2.9 to +8.7 points after wild-cluster correction" → new numbers |
| M6 | V.E assembly L316 | the binding-interval sentence + the coverage sentence: attribute 94.3/95.1 to the restricted inversion, print Webb's 90.84/91.42 beside it, state the rule's selection; "the Webb wild-t read here is the fourth-narrowest…" ranking passage rewritten to the adjudicated framing |
| M7 | Table 7 cell L423 | interval; "width 0.39× the corrected floor read, meaning the Webb wild-t interval" → re-derive ratio vs restricted width (2.29/6.828 → 0.34×) or relabel; convolved line relabeled "(the Webb rung convolved with the loan/stratum layer)" — layer_convolution was run on Webb, not re-derivable |
| M8 | Table 7 notes L430 | "the headline row quotes the wild-t interval as the binding layer" → restricted inversion; percentile-demotion text unchanged |
| M9 | VI.B L544/L548 | designer units: floor image → "4.033% to 6.181%" (committed artifact); $/month band re-derived by the committed formula (764.7×pp/100/42): "$0.42 to $1.66 billion per month"; the state_contingent $15.02–17.88 cap mapping stays explicitly labeled as run at the Webb rung's endpoints (no committed restricted-endpoint mapping exists), with the direction note that the binding rung widens it |
| M10 | VII.F L688 | "the Webb wild-t interval of +2.9 to +8.7 points is the binding layer, its lower edge above zero" → restricted [+2.3, +9.1] |
| M11 | Conclusion L699 + L705 | both interval quotes |
| M12 | Ladder cluster L1224–1253 (app:floormech) | Table 8 Status column: restricted row becomes "primary; the binding layer (covers 94.3/95.1)", Webb row becomes "the committed construction; covers 90.8/91.4, below the pre-committed bar"; notes rewrite of the rank/primacy passage recording the adjudication ("the ladder note recording why") |
| M13 | replication_appendices tab:verdicts, V20-C row | adjudication column updated: rule selected restricted_webb; artifact's landing_branch string wrong and left unedited; quoted interval moved |
| M14 | response letters (md draft + round22 tex) | SPEC_V20_C item rewritten: the defense is by re-landing, not by the 94.3/95.1 as previously claimed; gate #101 literals re-synced |

## 3. Gate/test re-syncs (documented V20-N1 comments at every touch)

- gates: L458 (E13 literal), L519/584 (abstract phrase + range-before-point),
  L665 (ladder literals), L810–826/942–944/1115 (designer-units: keep
  Webb-tie for the floor/cap grid values, re-tie the $/month BAND to the new
  interval arithmetic), L1367–1430 (rank + "why Webb stays primary" →
  adjudicated framing), L1868 (placement comment), L6791 (interval count ≥4 →
  new literal), #125 (implement spec §4 live tie: manuscript quotes the
  interval of `binding_construction`, read from the artifact, no literal).
- tests: test_headline_posture (×2), test_scaled_null_additive (placement),
  test_cap_monthly_units (LO/HI 2.9/8.7 → 2.3/9.1; 0.53/1.58 → 0.42/1.66),
  test_floor_ladder_gate (4.177–5.800 stays Webb-tied — verify scope),
  test_month_twoway_clusters (rank claims re-pinned to the adjudicated text),
  test_response_letter_gate (if letter literals move).

## 4. Invariants

Suite green at every commit; both variants identical bodies; no artifact
edited; every placement/comparison claim re-verified at the new interval, not
assumed; editions + split recut LAST; adversarial refutation workflow before
the final commit; the verdict-ledger row update is the one permitted edit to
the migrated file (adjudication is its function).
