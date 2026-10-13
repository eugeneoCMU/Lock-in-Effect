# Separate mixture alternative

Approved in the implementation chat on October 13, 2026. Reuse the corrected
Freddie pipeline and retain existing model benchmarks. No manuscript estimate
is replaced and no protected source file, frozen wrapper, or receipt is edited.

Monthly reference probability is existing PSA100 age baseline times FICO, LTV,
and modeled burnout adjustments, evaluated at zero rate gap. This is a candidate
reference schedule, not an estimated neutral-rate counterfactual. Reject values
outside [0,1), convert to intensity -log(1-p), and multiply by
(1-s)+s*exp(-gamma*max(-100*rate_gap,0)), where rate_gap=coupon-market.
No turnover floor is added. Share grid: 0, .25, .5, .75, 1; shares are assumptions.

OFF sets gamma=0. ON uses either -log(.935) (illustrative) or the negative of
the existing quarterly-to-monthly response coefficient (legacy conversion).
Using a monthly probability-ratio coefficient on intensity is an explicit
calibration assumption. The default is legacy conversion for comparability.
Positive-only is the proposed model. A separately labeled preserve_refinancing
variant multiplies total intensity by exp(gamma*max(100*rate_gap,0)). It preserves
an incentive channel, not exact legacy probability-level predictions.

Use unchanged corrected-input, macro, benchmark, seed and accounting gates.
Record both reported holdings-scaled principal and closed-pool cash principal.
Default and amortization rules are fixed; realized amounts can differ by leg.
No source reconstruction, network access or parameter selection in the runner.
Run only on complete verified combined inputs; synthetic tests are not estimates.
All temporary in-process adapters restore their prior bindings even on failure.
The adapter is serial and must not be used concurrently in a shared process.
