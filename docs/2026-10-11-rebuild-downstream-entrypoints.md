# Downstream entry points after the corrected source rebuild

This is a code-path readiness note. No empirical calculation is performed by
this note. The source rebuild and its all-20-quarter gate must finish first.
Existing `hazard/data/`, archived research results and paper artifacts are
preserved. Native Fannie source reconstruction remains separately blocked.

## Required input gate

Validate every quarter with `run_freddie_rebuild.validate_completed`. Only then
run `combine_freddie_rebuild.combine` against
`output/research-rebuild/2026-10-11/`. Its default manifest is all 20 Freddie
quarters. The queued serial command already invokes this combiner on success;
do not start a second concurrent combiner or overwrite an existing combined
directory. Retain source exclusions, fixed cohort history, exact May-2022
snapshot, identified transition metadata and private source-ID checks.

The corrected combined paths are `combined/cohort_month_panel.parquet`,
`combined/loan_sample.parquet`, `combined/markov_transition_matrix.parquet`,
`combined/transition_diagnostics.json` and `combined/report.json`. Each next
stage needs new output paths, saved input/code/specification hashes and the
same declared population. The ordinary combined draw retains equal per-file
oversampling; it is not the older SOMA cell-targeted fresh draw.

## Calibration inputs already available

The frozen public mortgage-rate response is
`output/research-limits/2026-10-09/rebuild/fannie/MORTGAGE30US_201612_202510.csv`.
Its bytes currently match `rate_source.json` in the same directory. Preserve
the existing within-month mean construction and full saved floor grid. The
pure functions `fannie_floor_read.prep`, `grid_for` and `deep_otm`, and
`fannie_age_rebuild_audit.grids`/`verify_grid_parity`, provide the established
selection and comparison calculations. The latter driver documents the exact
weekly-to-monthly conversion and saved-grid parity gates.

Do not invoke `out_of_window_floor.main` unchanged: it reads the legacy panel,
retrieves rates again and writes to a historical result path. Likewise,
`fannie_age_rebuild_audit.run` is an existing Fannie age-only reconstruction,
not a native-source rebuild or the new Freddie calculation. Reuse their pure
calculations with explicit new input/output paths and frozen rates. Report
software and population changes separately; do not select a favorable floor.

## Retrospective scoring

`pathb_prediction_diagnostics.predict_path` supports the corrected history
contract by default. `make_covariates`, `strict_score` and `diagnose_groups`
provide reusable calculation components. The existing `main` instead reads
historical panel/sample paths and explicitly requests legacy history while
replaying its old selection exercise; it must not be used unchanged for the
corrected run. The existing floor candidates are 0, 2%, 3.5% and 4.991%, and
PSA candidates are 50%, 75% and 100%. Retain the recorded candidate and selection
boundaries; any distinct estimation exercise needs its own frozen protocol.

The historical conditioning macro file is
`output/review-revision/2026-10-07-checks/macro_frozen.parquet`. Verify its saved
hash and necessary fields before use. The scoring path uses the recorded
monthly conditioning convention, which is distinct from the floor grid's
within-month mean mortgage rate. Do not silently replace one convention with
the other. These are previously examined evaluation outcomes, not a new holdout.

## Corrected simulation API

`microsim_engine.run_qt_microsim` accepts explicit `loan_sample`, `macro`,
`transition_matrix` and `output` arguments. Its default corrected-input checks
require known terms, fixed historical burnout, an exact pre-QT snapshot and
identified transition metadata with a pre-QT estimation cutoff. Provide all
inputs explicitly, retain `allow_legacy_inputs=False`, and write each paired
leg separately. Hold loans, rates, seeds, accounting and other parameters fixed
between response-on and response-off runs. Preserve the imported response and
floor choices unless a separately frozen comparison explicitly varies them.

The historical `soma_fresh_pair.main` targets a different saved SOMA cell draw,
fetches macro/SOMA inputs and writes to its old results path. The lower-level
`stock_flow_accounting_comparison.simulate_accounting` also loads the cached
legacy transition matrix internally. Neither is a ready-made corrected-input
runner. A new wrapper must supply the rebuilt matrix and audited inputs and
reconcile voluntary, scheduled and default/other principal before interpretation.

No source rebuild alone resolves the Fannie access gap, sale/refinance labels,
causal response identification, or population transport to the entire SOMA book.
