# Economics-review revision: editable local package

Edition dated October 7, 2026; final verification October 8, 2026. This package contains the current manuscript, editable LaTeX and figures, the preserved reviewed sources, aggregate research results, analysis code, specifications, and verification/disposition documents. It does not claim an identified causal effect or full-SOMA representative estimate.

## Read first

- `output/pdf/lock-in-effect-economics-review-revision-2026-10-07.pdf`: combined paper and online appendix.
- `output/pdf/lock-in-effect-economics-review-main-2026-10-07.pdf`: main paper, including references.
- `output/pdf/lock-in-effect-economics-review-online-appendix-2026-10-07.pdf`: appendix with original page numbering.
- `docs/2026-10-06-claims-and-results-ledger.md`: current scientific claims, denominators and limits.
- `docs/2026-10-07-review-fix-register.md`: all twelve review findings and their dispositions.
- `docs/2026-10-07-revision-verification.md`: test, build, render, provenance, preservation and review evidence.

## Edit and build the paper

The standard wrapper is `paper/final/paper_final_v1.tex`. It inputs `journal_main_v2.tex` and `review_appendix.tex`; generated `review_*_table.tex` and `review_validation_detail.tex` files supply the numerical exhibits. The long-abstract wrapper has the same body. The bibliography is `paper/final/references.bib`. Referenced figures live in `figures/`.

From the package root, using Python 3 with the repository's research dependencies and Tectonic (verified with 0.15.0):

```sh
python3 tools/build_review_exhibits.py
python3 figures/make_specification_sensitivity.py
python3 tools/tex_validate.py paper/final/paper_final_v1.tex --bib paper/final/references.bib
mkdir -p paper/final/build_review_revision
tectonic --keep-logs --keep-intermediates -o paper/final/build_review_revision paper/final/paper_final_v1.tex
tectonic --keep-logs --keep-intermediates -o paper/final/build_review_revision paper/final/paper_final_v1_long_abstract.tex
python3 tools/split_pdf.py paper/final/build_review_revision
python3 tools/render_gate.py
python3 tools/liveness_gates.py
python3 -m pytest tests/ -q --no-header -rs
```

The three versioned delivery PDFs are copies of the validated standard build and its detected-boundary split. Rebuilding does not automatically overwrite those delivery files. `package-manifest.json` records all packaged files and hashes, excluding itself.

## Research inputs and reproducibility limits

The delivered LaTeX can be compiled from included sources, figures and bibliography without loan-level data. Exhibit regeneration uses included aggregate JSON outputs. The public macro snapshot and original NY Fed workbook/source trail are included under `output/review-revision/`.

Loan-level Freddie samples, raw downloads, compact survivor snapshots, the small-cell cohort panel, and the row-level validation score file are **not included** in this package. A full research replay requires the user's separately obtained local inputs matching the saved hashes. The full repository test result was obtained in the preserved local research environment with those inputs; an input-free extraction is not expected to reproduce every data-dependent repository test. No credentials or `.env` files are included. A local package is not authorization to publish proprietary inputs or the working manuscript.

New scoped drivers are `hazard/stock_flow_accounting_comparison.py`, `hazard/pathb_cohort_validation.py`, and `hazard/coupon_bridge_sensitivity.py`. Their dated specifications describe scope, freezing and exclusions. Existing production hazard/transition routines were instrumented without modification. Each new result is separately named; historical frozen outputs are preserved. The bridge driver's optional missing-target snapshot audit currently references the original local snapshot location; all three delivered bridges are fully supported and did not invoke that fallback.

## Preserved edition and tests

`paper/final/reviewed_archive/` contains exact reviewed sources, including obsolete narrative and references, for historical checks. It is not the current manuscript or a separate ready-to-build document: its original relative figure paths belonged to the pre-revision directory. The reviewed original PDF and source manifest are retained under `output/review-revision/2026-10-07-baseline/`.

Legacy wording gates intentionally inspect that preserved edition. Current publication gates inspect expanded current sources, precise results, semantic reference destinations and rendered pages. The final report separates these scopes. The old main README and historical response letters describe earlier research rounds and do not supersede this revision README or claims ledger.
