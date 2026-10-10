# Fannie age-only reconstruction and effects on reported readings

Completed October 10, 2026, from the protocol frozen October 9.

Recombining all 24 preserved Fannie quarterly aggregates with loan-count age
weights changes the principal pooled 2017–2019 payoff reading from **5.522% to
5.544%**. It remains above the earlier 4.695–5.334% Freddie calibration band.
Some age-specific readings change materially. This is a verified correction
to the across-quarter age aggregation, not a complete raw-source payoff rebuild.

## What was reconstructed and checked

The input files cover acquisition quarters 2017Q1–2022Q4. The reconstructed
panel retains the same 2017–2021 origination universe and all 23,443 cell-month
keys. A replay using the legacy age rule first reproduced the original panel.
Then 14 saved floor-grid cells for each agency, 28 in total, were reproduced
using one frozen official FRED mortgage-rate series: all cohort counts agree
exactly and annualized rates meet the existing 0.001 percentage-point tolerance.
No new Fannie rate was interpreted before those gates passed.

The repaired production combiner changes 20,906 pooled mean ages. The mean
absolute change weighted by end-balance exposure is 3.07093 months, and the
largest change is 11.57950 months. Eight cells retain nonfinite mean ages.
Balances, original-balance sums, payoff numerators, loan counts, monthly payoff
rates and burnout all match the old panel exactly. No state-mode differences
occurred. The panel is saved separately from the original.

## Effects on the original fixed comparisons

All rates below annualize aggregate prepaid principal divided by aggregate
end-of-month exposure. Exposure is a sum of balances across months, in billion
dollar-months. Age selection refers to the cohort mean, not individual-loan ages.

- **2017–2019, gap at most -25 bp, mean age at least 12 months:**
  5.522% to 5.544%; 421 to 489 cohort-months; exposure 2,317.86465 to
  2,389.10445 billion dollar-months. The earlier across-agency disagreement
  remains; this calculation does not select a replacement Freddie floor.
- **Same window and gap, mean age at least 24 months:**
  10.136% to 9.523%; 71 to 92 cohort-months; exposure 27.52249 to
  84.30432 billion dollar-months.
- **2023–2024, gap at most -25 bp, mean age at least 12 months:**
  3.962% to 3.962% at the saved three-decimal precision; 6,322 to 6,307
  cohort-months. The age-24 reading changes from 4.151% to 4.044%, with
  5,685 to 5,816 cohort-months.
- **2023–2024, gap at most -200 bp:** the age-12 reading stays at 3.864%
  with identical support. The age-24 reading changes from 4.029% to 3.934%,
  with 3,586 to 3,725 cohort-months.

The aggregate result file retains all zero/-25/-50 bp comparisons, both age
thresholds, the -200 bp checks, and each cell's added/removed exposure. No
subgroup was selected after seeing these results.

The pooled 2017–2019 reconstruction above is distinct from the earlier
**pure-2018 older-origin acquisition-tail pilot**. In that different population,
the repaired age rule reclassified 99.05% of the exposure previously above the
24-month threshold. The two findings must not be described as contradictory or
merged into one estimate: their origin universe and calendar window differ.

## Limits that remain

The compact cells retain previously calculated payoff numerators. Without the
original histories, this recombination cannot establish whether input or join
ordering affected them, resolve duplicate or missing reporting months, or check
the original-balance fallback for first-observed payoff records. Counts of
individual loans with valid age are absent. Weighting each finite mean by its
reported loan count therefore assumes that count describes the observations
included in the mean; partial missingness within quarters remains unaudited.

The historical floor's end-balance denominator also differs from the opening
exposure used in prediction scoring and simulation. An individual-loan opening
risk-set calculation must accompany a full source rebuild. This age-only exercise
cannot identify a sale-specific turnover rate or justify transporting the floor
to the entire SOMA book.

## Reproducibility

Code: `hazard/fannie_age_rebuild_audit.py`. Aggregate before/after results,
source/code hashes, parity gates and all support changes:
`hazard/data/fannie_age_rebuild_2026-10-09_results.json`.
Local frozen rates, original-input manifest and reconstructed panel:
`output/research-limits/2026-10-09/rebuild/fannie/`.

The public rate source is
[FRED MORTGAGE30US, December 2016–October 2025](https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US&cosd=2016-12-01&coed=2025-10-31).
Weekly observations are averaged within calendar months, with no future filling.
Original inputs passed their post-run hash checks. Two initial attempts stopped
during module imports before computation; the successful run supplies the legacy
module search path and an unused key placeholder because public CSV retrieval
does not call the keyed FRED API. Their logs are retained.

This audit was implemented with AI assistance. An independent lineage review
distinguishes verified code paths from historical execution provenance; neither
the review nor the replay tests certify causal identification.
