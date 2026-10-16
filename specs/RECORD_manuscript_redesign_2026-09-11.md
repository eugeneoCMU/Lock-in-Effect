# Record: Mortgage Lock-In Manuscript Redesign

## Decision

The conference title remains *Mortgage Lock-In and the Federal Reserve's Quantitative Tightening Shortfall*. The journal-facing paper is now a mortgage-lock-in quantification paper applied to Federal Reserve agency-MBS runoff. It does not present the ABM-versus-hazard comparison as a separate contribution and does not claim to identify a new causal elasticity.

## Main-paper result hierarchy

1. The MBS-specific cap-relative runoff gap is $764.748 billion.
2. The New York Fed's contemporaneous projection anticipated most of that gap; the central expectations-relative gap is $87.8 billion.
3. The loan-level model's rate-insensitive null accounts for 85.7% of the cap-relative benchmark under the headline production form.
4. The production-form lock-in marginal has a binding off-window floor interval of +1.9 to +9.1 points, with a $42.6 billion anchor inside it.
5. The joint floor-elasticity box is +2.1 to +13.2 points.
6. The additive form produces a larger marginal of approximately 11 points, so functional form is part of the result.

## Disposition

- The former introduction, estimator inventory, and eight-page core-results table were replaced by a focused introduction and one-page results table.
- The former literature review was replaced by a section organized around lock-in identification, mortgage cash flows, and Federal Reserve runoff.
- Publication-facing references to Path B were replaced by Loan-Level Prepayment Model.
- The ABM remains in the main paper only as adverse supporting evidence; its full mechanics remain in the Online Appendix.
- Path A remains a diagnostic rather than a coequal estimator; its details remain online.
- The Danish counterfactual is a policy extension; its incidence and transition limitations remain explicit and its details remain online.
- The old main text remains inside a non-typeset preservation block in both canonical sources, and the frozen pre-redesign PDF remains under `paper/final/build_split/`.

## Verification contract

Both editions must build from the shared `journal_main_v2.tex` body. The canonical abstract is journal-facing; the long-abstract edition retains its historical long abstract. The main paper is double-spaced and the bibliography and Online Appendix are single-spaced. The split must be detected from the Online Appendix banner. All existing numerical gates remain authoritative unless a wording-only gate is deliberately re-scoped to the new abstract.

## Page-count note

The approved target was approximately 35--45 pages including references. The fresh double-spaced main build is 34 pages. The one-page underage is retained because restoring technical narration solely to hit 35 pages would weaken the redesign; the paper contains the approved substantive sections and exhibits.
