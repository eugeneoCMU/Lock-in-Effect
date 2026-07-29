# SPEC H1 — zero-months mechanism diagnosis (`h1_zero_months_diagnosis`)

Pre-committed BEFORE the probe runs (2026-07-29). REVIEW2 / PLAN WP-H1: trace the
four exact-zero months in the SOMA back-out (June 2022, February 2023, April 2024,
September 2025 — manuscript, seasonal-floor appendix) to their mechanism; the
landing rule below maps outcome → action. The appendix already prototypes the
pair-conserving repair and shows it flips both seasonal legs from pass to concede;
the paper's standing position is CONCEDE_LEVELS_ONLY. Nothing in this probe can
strengthen a timing claim; it can only explain the zeros and decide where the
concession is stated.

## Construction (verified against `hazard/macro.py:150-177`)

The benchmark's monthly rolloff = `resample("ME").last()` of the NY Fed SOMA
summary weekly `mbs` series (as-of dates), then `.diff()` — i.e. the change
between the LAST as-of observation of adjacent calendar months. The probe
re-fetches the same URL with the same filter (`mbs` nonzero), reproduces the
monthly series, and for each zero month `m` examines every weekly observation in
`(last_asof(m-1), last_asof(m)]`.

## Classification per zero month (fixed ex ante)

- **F (flat / factor-posting artifact):** all weekly `mbs_b` in the span are equal
  to the month-(m−1) close (max |step| < $0.005B) → the reporting series did not
  update inside the month; the paydown posts into month m+1's first observation.
- **A (alignment artifact):** intra-month steps ≥ $0.005B occur but the ME-last
  diff is < $0.005B in absolute value → offsetting postings around the month edge.
- **G (genuine):** neither F nor A degenerately (steps present, diff ≈ their sum,
  and month m+1 is NOT a spike ≥ 1.5× the trailing-6-month mean |diff|).

Pair-conservation read (reported, not gated): |diff(m) + diff(m+1)| vs the
trailing-6-month mean |pair total|.

## Parity gates (BLOCKING)

- **P1** the four manuscript zero months reproduce as |diff| < $0.005B from the
  live fetch. Any miss → STOP-DATA-REVISION: land nothing, alarm.
- **P2** the spike figure the manuscript quotes (up to 14.01% annualized after
  three of the zeros) is consistent: the max annualized CPR-scale spike over the
  three post-zero months, computed exactly as `build_empirical_metrics` does
  (|rolloff|/holdings − sched(2.5%), clip, ×12×100), reproduces 14.01 ± 0.05.

## Landing rule per outcome (pre-committed)

- **Outcome ARTIFACT (≥3 of 4 classified F or A, including all three
  spike-followed zeros):** wording-class only. (i) The appendix's zero-months
  sentence gains the measured mechanism clause. (ii) The §III.B and §VI.B sites
  that quote monthly-timing descriptors each gain one clause stating the monthly
  benchmark cannot adjudicate timing (citing the appendix's five diagnostics),
  promoted from the appendix. NO re-score of any timing exhibit; the peak-lag
  descriptors stay as descriptors of the published series; no committed number
  moves. The pair-conserving repair stays an appendix diagnostic, not a series
  replacement (repairing 7 of 41 first differences is a smoothing choice, not a
  measurement).
- **Outcome MIXED/GENUINE (any G, or <3 artifact):** the appendix's artifact
  framing is weakened for the G months (stated per month); the concession stands
  on the five diagnostics alone; same §III.B/§VI.B promotion (the concession is
  independent of the mechanism); still no re-score.
- Either outcome: verdicts-table row + runindex row + letter sentence.

## Artifact

`hazard/data/h1_zero_months_diagnosis.json`: mode, status, spec, parity_gates,
per-zero-month {weekly observations in span, steps, classification, next-month
diff, pair total, trailing mean}, spike_check, classification_summary, verdict
{outcome, manuscript_action}, runtime_s. Frozen on write.

## MUST NOT CHANGE

`hazard/macro.py`; any committed artifact; any timing exhibit number; the
appendix's five diagnostics and its frozen-rule reporting; the CONCEDE_LEVELS_ONLY
posture (this probe can only add mechanism, never subtract concession).

---

## POST-RUN AMENDMENT H1-A1 (labeled, 2026-07-29 — first run stopped on P1 as designed)

P1's operationalization was WRONG: it targeted zeros of the raw ME-last rolloff
diff. The manuscript's "four exact-zero months in the SOMA back-out" are zeros of
the BACK-OUT CPR — `clip((|rolloff|/holdings − sched_smm), 0)` — i.e. months where
the reported rolloff falls below the scheduled-amortization floor and the
non-negativity clip pins the month at exactly zero. First-run measurements (raw
diffs −$4.48/−$3.70/−$3.63/+$1.99B vs sched-amort ≈ $4.9B/mo; next-month diffs
−$25.7/−$30.1/−$29.2B ≥ 1.5× trailing means; P2 spike 14.07 ≈ 14.01 PASS).
**Amended P1:** back-out CPR == 0.0 exactly at the four months AND the unclipped
value < −0.01 pp/mo·12·100 margin (proves the clip binds). **Amended
classification:** CLIP-BOUND (artifact) = unclipped negative + next-month rolloff
≥ 1.5× trailing mean |diff| (June 2022 variant: net POSITIVE diff at window open —
settlement overlap with residual reinvestment purchases — same clip mechanism).
Landing rule, outcome mapping, and MUST-NOT-CHANGE unchanged. The mechanism
sentence for the ARTIFACT landing becomes: the zeros are clip-induced
month-boundary allocation artifacts, with the displaced mass appearing in the
following month's reading (pair totals conserved in dollars).
