# Comparison matrix version 2 — approved October 13, 2026

Purpose: compare structural specifications on identical corrected inputs without selecting an attractive result or replacing the published estimate.

The matrix contains 40 scenarios: two references, two response calibrations, two gap modes, and five assumed sensitive shares (0, .25, .5, .75, 1). `inherited_psa` uses the inherited zero-gap PSA100/covariate monthly probability. `matched_max_off` uses max(monthly floor, that probability), with annual floor .04991 converted by 1-(1-floor)^(1/12). Both references become intensities before mixture response; neither adds a floor after response. Neither is newly calibrated.

Run the existing hard-max pair/scoring and the additive-survival pair/scoring as separate benchmarks. Additive probability is 1-(1-monthly_floor)*(1-voluntary_probability); its own OFF baseline differs from max. Preserve all other simulation conventions, seed, initialization, default and principal accounting. Fixed annual floor .04991 and PSA100; validate but do not retune archived choices.

Positive-only mixture suppresses only unfavorable mortgage-rate gaps. The refinancing-preserving variant retains the existing assumption that favorable gaps boost the whole reference intensity. This is a structural sensitivity, not an estimated separate refinancing hazard. The exploratory sale/refinance module has no production hook.

Before writing complete results, require the automatic acceptance gate: exact scenario set, complete valid receipts and artifacts, matching coverage and scoring support, finite reconciled principal accounts, unchanged OFF paths within each reference, matched-reference OFF matching hard-max OFF, and zero-share positive-only ON equaling OFF. Apply the same nulls to aligned predictions. Failure writes failure status and does not create results.json. Gate validates artifacts and model comparisons; it cannot identify the assumed share, validate imported coefficients, or establish causality.

Run offline against completed corrected-source inputs. Do not edit the live pipeline's frozen files or switch model code during a run. New source estimates and the $42.6B published comparison remain separate until audited outputs justify a later revision.
