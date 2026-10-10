# Ingestion repair: result lineage and claim qualifications

Independent local review of `6f4fa2f`, October 9, 2026. No raw or cloud loan
files were opened, no models were rerun, and no production artifact was changed.
This note is the only output of the review. File/line references describe that
revision; the recorded hashes describe the files inspected in this worktree.

The saved paired simulations use individual loan ages, not the repaired pooled
mean age. That separates their simulation inputs from the two repaired aggregate
calculations, but it does **not** separate their 4.991% floor calibration from
the legacy panel. The floor readings and retrospective scores need an audited
rebuild before they can be called ingestion-corrected estimates. The direction
and size of any change to the headline marginal are not established here.

## Lineage of the five reported objects

1. **Saved $42.6084 billion / +5.5716-point pair.** The off-window calculation
   reads `loan_sample.parquet` directly (`hazard/floor_form_offwindow.py:174–176`)
   and passes that frame into the loan simulation (`:110–125`). The original
   snapshot builder sorts pre-QT observations and retains the latest individual
   loan record, including its `loan_age` (`hazard/loan_sample.py:49–76`).
   `MicrosimPool` loads that column (`hazard/agents.py:129–131`), and the US
   hazard receives the individual age array (`hazard/competing_risks.py:170–177`).
   Neither repaired aggregation expression supplies these ages or simulated
   voluntary payoff amounts. However, the selected floor is loaded from the
   aggregate-derived OOS artifact (`hazard/floor_form_offwindow.py:149–160`).
   The appropriate current claim is a saved conditional calculation at a fixed
   4.991% annual floor, not a recalibrated result after the ingestion repairs.

2. **Fresh SOMA-cell-targeted $42.1761 billion / +5.5150-point pair.**
   `hazard/soma_fresh_pair.py:32–44` passes the fresh loan frame to the same
   paired engine. Its snapshot builder keeps loan-level ages and requires a
   positive-balance May 2022 observation (`hazard/soma_stream_snapshot.py:50–69,
   93–101`); the draw checks dates, term, balances and duplicate IDs
   (`hazard/soma_fresh_sample.py:47–54,83–85`). It uses the fixed legacy floor
   through `hazard/book_composition_marginal.py:61,192–200`. The saved result
   is `hazard/data/soma_fresh_pair_results.json:5–16`. The 47.5876% quantity
   describes listed-cell support in June 2022; the dollars use conditional
   whole-pool scaling and are not that slice's observed contribution. This
   remains a Freddie draw with an assumed note-to-security-coupon bridge.

3. **The 4.991% floor and related age-support/inference claims.** These depend
   directly on the aggregate panel. `hazard/oos_identification.py:305–321`
   reads it, `:355–362` selects on `mean_loan_age`, and `:449` chooses the
   2018, gap <= -25 bp, mean-age >=12 cell. The numerator is `prepaid_upb`;
   the denominator is contemporaneous `exposure_upb` (`:292–297`). Thus both
   the payoff-ordering repair and the age-aggregation repair can affect the
   reading, its sample membership, and the derived floor-inference results.
   A fixed-floor replay of the pair cannot certify this floor's empirical
   provenance. The manuscript's floor/support statements at
   `paper/final/journal_main_v2.tex:120` describe the saved calculation.

4. **Retrospective January 2024–September 2025 validation and the 3.5%
   diagnostic candidate.** The saved validation directly reads the aggregate
   panel for realized payoff principal, opening exposure, baseline speeds,
   initial mean ages and burnout (`hazard/pathb_cohort_validation.py:34–55`).
   Its 23.2141% overprediction and comparator ranking are scores on those
   legacy inputs, not repaired observations. The newer diagnostic also uses
   panel mean ages and initial burnout (`hazard/pathb_prediction_diagnostics.py:
   72–80`). Realized opening exposure and rates are conditioning information;
   the exercise remains retrospective, with selection on 2023 only, and is
   not a full balance-path forecast or validation of the response-off world.
   Correcting ages may have no direct PSA effect where every relevant age is
   already >=30, but that is a check to report, not grounds to skip rebuilding
   the payoff numerators and calibration/support inputs.

5. **The prior Fannie floor read.** `hazard/fannie_floor_read.py:130–149`
   reads the Fannie aggregate panel and uses the same mean-age selection and
   payoff/end-exposure ratio (`:117–127`). The saved 5.522% reading is a pooled
   2017–2019 object compared with Freddie's pooled 5.185%; it is not a direct
   same-window comparison with the 2018-only 4.991% anchor
   (`hazard/data/fannie_floor_read_results.json:167–186`). The newer 2018
   acquisition-tail pilot neither replaces that read nor repairs the saved
   quarterly payoff numerators (`docs/2026-10-09-older-vintage-floor-support.md:
   94–107`). It must retain the later-acquisition selection, thin mature support
   and missing deep-discount overlap qualifications. The Fannie panel is not
   present under this worktree's `hazard/data/`; this review did not independently
   reopen the other local source location or certify its bytes.

The paired engine also reads a cached transition matrix
(`hazard/microsim_engine.py:110`; `hazard/markov.py:117–118`). Its estimator
uses aggregate `mode_state` and exposure, not the repaired mean ages or payoff
numerators (`hazard/markov.py:24–50`). It is a panel-related dependency, though
neither repair directly changes those estimator inputs. Preserve and hash it;
do not describe the complete paired pipeline as independent of all panel data.

## Remaining repair conditions, in priority order

- **Blocking for corrected-estimate claims: legacy saved artifacts remain.**
  The current Freddie panel and loan sample hashes exactly match the validation
  artifact's input hashes (`hazard/data/pathb_validation_2026-10-07_results.json:
  1516–1520`). No empirical magnitude for the source-ordering error follows
  from the synthetic regression test. Rebuild into a separate destination,
  preserve the legacy edition, and compare numerators, ages, support membership,
  calibration, scores and any resulting paired estimates before replacing claims.

- **Chronological order is necessary but does not establish a valid previous
  monthly balance.** `hazard/ingest.py:213–231` orders the lag within each loan
  but neither rejects duplicate loan-months nor requires consecutive months.
  A first observed payoff still falls back to original UPB. Missing/invalid
  balance rows are removed earlier (`:124–134`). Audit duplicate months,
  history gaps, first-row events and overlapping file membership before a
  rebuild; separately quantify affected payoff principal. These are remaining
  unguarded cases, not evidence that the current raw source contains them.

- **Count weighting is exact only when the count matches the age mean's
  nonmissing sample.** `hazard/ingest.py:235–237` computes a mean that excludes
  null ages but counts every row; `:254–256` and
  `hazard/fannie_replication.py:194–197` weight that mean by the full count.
  For example, one age 12 plus nine null ages in one file and one age 32 in
  another gives 13.818 under that rule, versus the known-age pooled mean 22.
  A finite-age sum/count (with an explicit missing-age policy) is needed for
  unconditional exact aggregation. Existing compact cells cannot recover these
  counts, and the all-missing-quarter tests do not cover partial missingness.
  The prior research note already declares this limitation; it is not a new
  demonstrated change to its empirical result.

- **The denominator distinction survives both repairs.** The old floor read
  annualizes payoff divided by end exposure; the conditional validation uses
  lagged opening exposure (`hazard/pathb_cohort_validation.py:10–20`). The
  simulation applies its hazard to active beginning balances
  (`hazard/competing_risks.py:117–118,185–187`). Preserve the legacy descriptive
  read for parity, but report a consistent opening-risk-set calculation and
  its coverage before treating the reconstructed floor as an observed monthly
  payoff probability. Merely correcting source order and mean age does not
  resolve this calibration convention.

## Evidence retained and checks still needed

The two current loan samples each contain 75,000 rows, 65 distinct loan ages
(0–64), and no missing ages; ages vary within vintage/coupon/FICO/LTV cells.
All fresh-sample records have reporting period `202205`. The older saved sample
does not retain reporting period, so its exact observation timing cannot be
audited from that cache alone. Current SHA256 values:

- Freddie panel: `c0feca1da96e97300d840c867494cc80ca8bbe97249c5fdeeb98761a015528e2`.
- Saved loan sample: `df4cb174b7251634126180cbbf78c2e64f83cff6578ec5d23118227cca1e3767`.
- Fresh loan sample: `718158f2bf41dfa6efb64365edcc37a36b1fb69ba88daf03f5e4dd9f964e1ce7`.
- Transition matrix: `70b57edb30df0e61bcfd494ad15b095318d7262588b86f0d8c8f7bd3b4ceed3d`.

The fresh-pair JSON records a sample-report path rather than a sample content
hash. Current code and sample inspection establish the input structure; complete
historical execution provenance still requires the separate run/preservation
manifests. Future runs should freeze exact source, parser, panel, sample,
transition, macro, parameter and output hashes together. No new outcomes were
opened and no revised parameter was selected in this audit. Tests, replay parity
and code-path separation do not identify moving share, validate the imported
elasticity, establish full-SOMA transport or turn either paired result into a
causal estimate.
