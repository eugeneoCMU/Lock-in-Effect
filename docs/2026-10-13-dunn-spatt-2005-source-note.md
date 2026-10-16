# Dunn–Spatt (2005): source and implementation boundary

Primary source checked October 13, 2026: [Wiley publisher page](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6229.2005.00132.x).

Verified metadata: Kenneth B. Dunn and Chester S. Spatt, “The Effect of Refinancing Costs and Market Imperfections on the Optimal Call Strategy and the Pricing of Debt Contracts,” *Real Estate Economics* 33(4), 595–617 (2005), DOI 10.1111/j.1540-6229.2005.00132.x. First published November 16, 2005.

The accessible abstract describes simultaneous MBS/loan valuation and borrower strategy across coupons, including all future refinancing costs. It also reports that loan value cannot exceed call price plus one round of refinancing costs. That valuation bound is background, not a constraint verified or imposed in the prototype.

Full text was not retrieved. Assumptions A3/A3′, statements on pages 601–602, and details about privately observed moving opportunities remain unverified and are not attributed to this paper in the manuscript. The earlier Dunn–Spatt (1985) contracting discussion is preserved as a separate contribution.

The manuscript uses the verified abstract to motivate a distinction between sale-related mortgage exits, refinancing, and other voluntary terminations. Its equations are proposed modeling choices. The prototype supplies components for future research; it neither fits these causes nor solves or reproduces the 2005 dynamic optimum. Aggregate voluntary payoff histories can incorporate historical refinancing incentives and costs, so they do not identify a rate-independent sale baseline. No direction of bias in the existing $42.6 billion result follows without a new model and recomputation.

The comparison specification uses two assumed references: `inherited_psa` (zero-gap PSA100 with borrower adjustments) and `matched_max_off` (the maximum of that probability and the monthly turnover floor). The planned corrected-source run crosses five shares, two response conversions, two gap treatments, and two references, yielding 40 mixture scenarios. The additive-survival legacy specification remains a separate benchmark. At identical states the matched reference equals the legacy maximum-form OFF hazard; matching complete OFF paths also requires identical inputs, simulation mode, seed, and transition rules. Only `positive_only` guarantees the zero-share ON/OFF identity; `preserve_refinancing` introduces an additional favorable-rate boost. None of these assumptions estimates the sale/refinance split.

Existing numerical findings, abstracts, and document dates are retained. Implemented comparison code is not evidence of completed source runs or validated revised dollars.
