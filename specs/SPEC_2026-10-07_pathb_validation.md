# Frozen retrospective cohort check, 2026-10-07

Freeze before scores: supplied Freddie panel; comparator training Jan-Dec 2023; evaluation Jan 2024-Sep 2025; vintages 2017-2021; cells vintage x 50bp note-coupon x FICO x LTV with positive pre-evaluation exposure and covariate support in saved sample. Path A/ML diagnostics have inspected these periods; this is not untouched.

Predict voluntary prepaid principal conditional on observed beginning-of-month cohort exposure, reconstructed from contiguous prior-month end exposure. Actual numerator is voluntary-payoff prior-UPB sum. Exclude scheduled/default/curtailment principal from BOTH outcome and prediction: separate realized flows unavailable. Exclude missing/noncontiguous/zero exposure and events>exposure with counts. No individual loan-ID split is possible in the ID-free panel; split by date, allowing repeated cohorts.

Candidates: (1) each cohort's 2023 prepaid principal / lagged exposure, (2) response-off, (3) response-on. Existing coefficients, 4.991% floor, 100 PSA, maximum form; sample-standardized cell FICO/LTV averages; Dec-2023 age advanced by time; Dec-2023 burnout advanced using predictions only. Realized mortgage rates condition predictions. Default hazard enters only existing competing-risk normalization.

Score cumulative principal, exposure-weighted rate RMSE/MAE, prediction/observation ratio, coupon-vintage ratios, and fixed half-years (last ends Sep-2025). Retain all candidates; no post-score calibration. At most this checks cohort-aggregated conditional one-step voluntary-principal prediction, not individual forward balance dynamics, moving elasticity, causality, or SOMA dollars. A prospective check requires genuinely unseen outcomes and risk sets frozen before access.
