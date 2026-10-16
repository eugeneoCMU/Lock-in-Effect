# Validation data exposure audit

Compact Freddie panel: 22,709 rows, vintages 2017-2021, outcomes January 2017-September 2025. Fields include current end exposure, voluntary prepaid prior balance, count, mean age, original balance, coarse covariates; no loan IDs, separate scheduled/default/curtailment components, or sale reasons.

2018 discount outcomes enter floor calibration. 2022-2025 outcomes were inspected for calibration/timing; `pathA_v4_holdout_results.json` and `ml_comparator_holdout_results.json` already score 2024 onward. The label holdout cannot make them untouched now. Old sample includes terminated loans; fresh May-2022 survivor sample has IDs but no subsequent performance histories. Twenty snapshots end before June-2022.

Decision: frozen retrospective cohort check per the new spec. Exclude unavailable Oct-Nov 2025. The panel's own rate divides by end exposure; reconstruct opening exposure from contiguous lag instead. Individual default/censoring and loan-ID disjointness cannot be checked and are not claimed. No raw/cloud processing required for this limited check.
