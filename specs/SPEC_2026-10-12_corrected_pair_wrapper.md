# Offline corrected Freddie paired simulation wrapper

Authorization: the user asked to work through the remaining rebuild inputs and
what needs to be done. This protocol is frozen before implementing the new
wrapper. Actual model execution remains gated on all 20 source quarters and
their complete, verified combined inputs. No source-worker or engine changes
are authorized by this wrapper.

1. Require explicit paths for the rebuild root, saved full monthly macro,
   recorded October 9 parameter freeze, archived monthly empirical CSV,
   downstream input inventory, monthly benchmark-reference JSON, and a new
   output directory. Reuse the all-quarter and combined-output validation in
   `calibrate_freddie_rebuild.validated_combined`. No network, raw source reads,
   input replacement, old output reuse, or default writes to `hazard/data`.
2. Validate the inventory's hashes for macro, parameter freeze, empirical CSV
   and monthly benchmark reference. Bind the macro to the parameter freeze's
   input hash. Preserve the recorded candidate grid and selected 3.5%/100 PSA
   retrospective choices as provenance only; do not reselect or substitute
   them for this separately recorded main pair.
3. Hold the main pair at annual floor 0.04991, 100 PSA, hard maximum floor,
   fractional prepayment, full moving response, US regime, seed 42, and response
   shock 0 versus 6.5 percent. Use the ordinary rebuilt sample with no SOMA cell
   reweighting. Set `allow_legacy_inputs=False` and provide the rebuilt matrix,
   full macro, loans and separate output paths explicitly to the existing
   engine. Refuse altered active hazard/default settings. Scope the floor
   override and monthly accounting instrumentation; restore both on every exit.
4. Keep the full macro frame. Its nearest observation to June 1, 2022 must be
   May 31, 2022 with holdings of 2707.446 billion dollars. Require every one of
   the 42 month ends June 2022 through November 2025. Public macro conditioning
   after September 2025 does not expand the Freddie outcome-read cutoff.
5. Rebuild empirical metrics with `hazard.macro.build_empirical_metrics` and
   the archived `Actual_Monthly_Rolloff_Billions` series supplied explicitly.
   Do not use the archived ABM CPR or a holdings-difference fallback. Match the
   archived rates, monthly caps and extension deltas, plus every monthly value
   in the saved benchmark's `committed_method_monthly_diff_b`. Require the
   764.7482532227002 billion dollar denominator through November 2025 within
   1e-8 billion, and monthly equality within 1e-8 billion (rates within 1e-10).
   The saved reference also contains December 2025. Select only the 42 declared
   QT months before decoding reference values and report excluded month labels;
   an extra reference month cannot extend the simulation or comparison window.
6. Before empirical replay or simulation, save a manifest of input, code,
   protocol and environment hashes and freeze this protocol in the new output.
   Run the two legs separately with identical inputs and random seed. Capture
   each existing engine step's opening/closing active balances, voluntary and
   scheduled cash, and default/other terminal transfers. Reconcile active and
   total claims using 1e-12 relative / 1e-5 dollar absolute tolerance. Preserve
   the engine's monthly observed-holdings reporting scale and distinguish it
   from the closed-pool cash figures. Default transfers are retained claims,
   not recovery cash; do not add unmodeled recovery, curtailment or additions.
7. Check every input/code/protocol hash again after both legs. Preserve partial
   output and a failure record if a gate fails; only write a successful result
   after both paths, monthly accounting identities and hashes pass. Report the
   response marginal as a conditional model comparison on the rebuilt known
   original-360-month population. Original note rates and original 360-month
   terms do not validate modified contracts. Population/source corrections,
   original-UPB fallbacks and explicitly recorded exclusions remain material.
   No causal interpretation, full-SOMA representativeness claim, new floor
   choice, headline promotion or paper replacement follows automatically.

## Declared sampling multiplicity clarification — October 12

The existing stratified sampler can draw with replacement. Bind both the number
of sampled rows and the number of unique loan IDs to the combined receipt.
Repeated copies of a loan ID are permitted only when their complete records are
identical; conflicting records fail the input gate. Preserve the draw, including
its multiplicities, in both legs rather than deduplicating it. Report sampled
rows, unique IDs, repeated draw rows and maximum ID multiplicity with results.
This clarification changes the input validation, not the sampling design or the
simulation parameters, and precedes any empirical use of this wrapper.
