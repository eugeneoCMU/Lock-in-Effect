# Revision plan: mortgage lock-in and Federal Reserve MBS runoff

Source: the forty-point review supplied on October 5, 2026. The current manuscript is `paper/final/paper_final_v1.tex`. This plan distinguishes changes possible with reported evidence from new empirical work. Preserve the existing numerical results and archival detail until any replacement is independently verified.

## Priority 1 — Rebuild the argument with existing results (this edit)

1. **Lead with the estimand.** Retitle the paper, rewrite the abstract and opening around the observed $764.7 billion cap gap, the New York Fed's anticipated runoff, and the paired response-on versus response-off marginal. State that $42.6 billion is one specification's result, not a uniquely identified causal effect.
2. **Put assumption sensitivity beside the result.** Move the moving-share bracket ($\mu=0.25,0.50,1$), hard-maximum versus additive baseline, off-window floor range, and concave elasticity result into an early, compact results display. Identify each as a different assumption or estimand; do not present their endpoints as a statistical confidence interval.
3. **Separate uncertainty types.** Label the $+1.9$ to $+9.1$ point range as a conditional floor-measurement interval. Explain that baseline form, the share of voluntary prepayment receiving the imported mobility response, and external transport remain outside it.
4. **Make external validity visible.** State next to the main result that direct Freddie 2017–2021 conventional coverage is about 51% of SOMA face, with Fannie replication and Ginnie, vintage, coupon, and term treatments as extensions. State the housing-supply confound and lack of validated monthly dynamics once each in the main argument.
5. **Improve reader order.** Put the cap-versus-expected-versus-actual figure in the introduction, replace the early level-oriented elasticity figure with a specification-sensitivity figure, and keep the coupon-by-vintage allocation figure with its noncausal caption. Place the ABM, Danish counterfactual, model architecture, cross-design checks, Path A detail, portfolio-duration table, and original level-oriented figure in the appendix. Check all cross-references and preserve their unique qualifications.
6. **Tighten language.** Prefer “response-off counterfactual” to “null” in the abstract and introductory explanation, “cap interpretation and communication” to “cap design,” and round headline quantities to useful precision. Keep run identifiers and exact replication data in the technical appendices or README. A full manuscript-wide terminology and engineering-history cleanup belongs to the structural pass.

## Priority 2 — Research improvements requiring new evidence (not claimed in this edit)

1. Estimate or externally discipline the share of prepayment tied to home sales, $\mu$, separating moving from refinancing and other voluntary payoffs.
2. Identify baseline turnover with data less exposed to the same rate and inventory shock; use local inventory and affordability variation to test supply confounding.
3. Construct a SOMA-targeted loan sample by agency, vintage, coupon, and term, then rerun the paired counterfactual. Recompute floor-binding shares on that sample instead of relying only on aggregate post-stratification.
4. Resolve the native 15-year hazard treatment and report the 30-year core separately from portfolio scaling. Revisit calibrated FICO, LTV, burnout, and default terms only where they move the marginal materially.

## Priority 3 — Publication package

1. Separate a readable main paper, economically meaningful online appendix, and replication notes with run IDs, hashes, parity gates, and specification history. Preserve the archival source rather than deleting it.
2. Audit every cross-reference, figure/table number, recent citation, and current publication status before submission. Rebuild the PDF and inspect the opening pages and altered figures visually.

## Verification for this pass

- Check each moved or newly emphasized number against the existing manuscript tables and source artifacts.
- Run the LaTeX validator and compile the full manuscript; inspect unresolved references, overfull boxes, figure placement, and the rendered opening pages.
- Review the diff for accidental changes to model results or unrelated files.

## Status after the October 5 editorial pass

- **Applied in the manuscript:** review points 1--5, 7--8, 12, 16--17, 19--21, 23--25, 28--36, and 40 at the presentation level. The title, abstract, introduction, compact Table 1, conceptual runoff figure, specification-sensitivity figure, conclusion, and cap-policy framing now follow the paired marginal. ABM, Path A, Denmark, the duration table, and their detailed comparisons are in the appendix. The 51.0% direct-coverage limit and housing-supply confound are next to the result. Figure 3's model-allocation qualification remains intact.
- **Partly applied:** points 6, 13--15, 22, 26--27, 37, and 39. The off-window floor is described cautiously and the conditional interval is demoted, but the main paper still contains dense implementation history and several large technical tables. A publication-facing compression pass should move run IDs, specification history, and failed branches into a replication README while preserving quantitative qualifications. It should simplify calibrated covariates only after re-running the model, and separate a shorter main PDF from a focused online appendix.
- **Requires new empirical work:** points 3 (estimating $\mu$), 9--11 (SOMA-targeted sampling, floor-binding composition, and native 15-year treatment), and the proposed housing-supply identification improvement in point 7. Existing sensitivity results cannot substitute for those estimates.
- **Submission-stage checks:** points 18 and 38 call for prioritizing identification over more robustness tests and auditing recent references. A full source-by-source bibliography update was not part of this editorial pass.

The repository's older `liveness_gates.py` still pins several superseded prose decisions, including the previous title, abstract wording, and Danish claims in the conclusion. Its 14 failures are wording and location checks, not failures of the new LaTeX parser or PDF render checks. Update that gate suite only after the publication structure is accepted; do not restore superseded prose just to turn those checks green.
