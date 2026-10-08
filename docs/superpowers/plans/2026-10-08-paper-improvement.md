# Mortgage Lock-In Paper Improvement Implementation Plan

> **For agentic workers:** Work through the tasks in order. Preserve the current manuscript and research artifacts before revising them; check each numerical claim against its source.

**Goal:** Turn the October 5 manuscript into a shorter, easier-to-review paper whose main result and limits are supported by clearly traceable evidence.

**Current source:** `paper/final/paper_final_v1.tex` and its October 5 PDF (`output/pdf/paper_final_v1.pdf`, 143 pages). This plan concerns this checkout. A separate revision in another worktree must be compared before either version is treated as authoritative.

**Scientific boundary:** The $764.7 billion cap gap is observed accounting; $42.6 billion / +5.6 percentage points is a conditional response-on minus response-off model result. The $1.9–9.1 point interval covers floor measurement under fixed structural choices. Direct Freddie conventional vintage coverage is 51.0% of SOMA face. None is a fully identified Fed-wide causal effect.

## Task 1 — Freeze the baseline and make a claim ledger

- [ ] Preserve the current TeX, PDF, bibliography, figures, and source artifacts in a versioned snapshot without resetting or cleaning the working tree.
- [ ] Record each headline number, denominator, period, population, accounting convention, model assumptions, and source artifact in a short claim ledger. Include $764.7B, $87.8B, 85.7%, 91.3%, $42.6B, +1.8/+3.4/+5.6/+11.2 pp, floor intervals, 51.0% coverage, and the Ginnie/vintage extensions.
- [ ] Compare this checkout with the newer journal draft in the other active worktree. Mark text and analyses already implemented there; carry forward verified improvements without silently replacing unique qualifications or newer research.

**Done when:** A reviewer can trace every abstract and main-results number to a named calculation and determine which manuscript is the editing base.

## Task 2 — Build a short main paper from existing evidence

**Files:** Revise `paper/final/paper_final_v1.tex` or a new publication-facing TeX file; preserve the archival source. Keep detailed material in an online appendix and replication notes.

- [ ] Set a target of roughly 25–35 pages for the main paper, excluding references and online appendix. Treat this as an editorial target, not a reason to cut qualifications.
- [ ] Keep the main line in this order: question and estimand; cap versus expected versus actual runoff; data and coverage; paired model; central result; assumption sensitivity; validation; policy interpretation; limitations.
- [ ] Move run histories, parameter inventories, ABM, Path A, Danish counterfactual, and secondary sensitivity tables out of the main argument unless a result changes its interpretation. Keep short pointers to the appendix.
- [ ] Give the main paper one compact display that distinguishes observed accounting, the central conditional marginal, moving-share and baseline-form alternatives, and floor-measurement uncertainty. Do not merge them into a single confidence interval.
- [ ] Remove repeated explanations and exact run identifiers from the main text after confirming their unique facts remain in the appendix or replication notes.

**Done when:** A new reader can state the estimand, the +5.6-point anchor, and its two dominant assumptions after reading the abstract, introduction, and first results display; the shorter PDF preserves the evidence trail.

## Task 3 — Improve the most consequential empirical inputs

These are separate research gates. Do not replace the current result with a new estimate until the new data and reruns pass their checks.

- [ ] **Moving share:** Find loan-level payoff-reason or property-transaction evidence that separates sale-related payoff from refinancing and other voluntary prepayment for a population and period relevant to the modeled loans. Define the numerator and denominator before estimation. If access is unavailable, retain the 25%/50%/100% bracket and explicitly label it assumed.
- [ ] **SOMA composition:** Construct or document the joint agency × vintage × coupon × term distribution of the SOMA book. Quantify matched support before weighting. Rerun response-on and response-off on the same supported cells and report direct-support and extrapolated results separately. Do not infer full-book coverage from marginal weights alone.
- [ ] **Turnover floor:** Re-estimate a baseline outside the rate-shock window with matched discount depth, loan age, and available housing-activity measures. Show the exposure and imputation share of every cell. Recompute both legs at each supported floor; compare hard-maximum and additive forms at the same anchor.
- [ ] **Validation:** Evaluate cumulative and monthly predictions against the same face-value accounting basis and a simple cohort-speed baseline. Retain adverse results. Call any previously inspected period a retrospective check, not a fresh holdout.

**Done when:** Each new input has a reproducible artifact, its sample support is explicit, and a paired rerun shows how much the reported marginal changes. If a gate fails, keep the existing conditional result and state the unresolved limit.

## Task 4 — Rewrite interpretation around the results that survive

- [ ] Update the title, abstract, introduction, results, conclusion, and captions from the verified claim ledger after Task 3. State which figures are observed, imported, calibrated, simulated, or assumed.
- [ ] Put the 51.0% direct-coverage boundary beside every portfolio-wide interpretation, and separate conventional-subbook results from full-book extensions.
- [ ] State that the imported moving response does not by itself separate financing lock-in from inventory or affordability; avoid a standalone causal share of the cap gap.
- [ ] Keep cumulative cash-flow claims separate from monthly timing, household welfare, and reserves-drained claims. Tie the policy recommendation to cap communication and expected cash-flow ranges.
- [ ] Audit recent literature and institutional citations source by source, including the Fed projection and phase-in accounting.

**Done when:** Abstract, figures, tables, and conclusion agree on one estimand and no caption implies more identification or population coverage than the methods establish.

## Task 5 — Publication and independent-review gate

- [ ] Validate the TeX and bibliography with `python3 tools/tex_validate.py <main-tex> --bib paper/final/references.bib`; compile using the repository's documented Tectonic workflow, then split the main paper and online appendix with `tools/split_pdf.py`.
- [ ] Run applicable research tests, `tools/liveness_gates.py`, and `tools/render_gate.py`; update stale text-pinning gates only after verifying that they encode superseded prose rather than substantive requirements. Report all remaining failures and typography warnings.
- [ ] Inspect the rendered opening, every altered figure/table, appendix boundary, references, and cross-references. Confirm every numerical line in the claim ledger against the final PDF.
- [ ] Give the short PDF and appendix to a reader who has not seen the project history. Ask for the stated estimand, top three weaknesses, and whether the central table can be read without coaching. Revise once based on substantive misunderstandings.

**Done when:** The delivered main PDF, appendix, source, claim ledger, and verification report all refer to the same version; any failed gate or unverified empirical claim is stated plainly.

## Priority and stopping rule

First complete Tasks 1–2: they improve readability and prevent version confusion without claiming new identification. Task 3 is the route to a materially stronger empirical paper; prioritize moving-share measurement, then joint SOMA support and turnover-floor identification. Task 4 follows verified results. Task 5 is required before circulation. Do not add more robustness variants unless they resolve one of these named uncertainties.
