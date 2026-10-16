# Mortgage Lock-In Manuscript Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a 35--45 page journal-facing mortgage lock-in paper, retain a substantial referee-facing online appendix, and preserve the complete research record.

**Architecture:** Keep the conference title, define its MBS-specific outcome immediately, and organize the article around the lock-in marginal from the loan-level prepayment model. Separate the cap-relative gap, expectations-relative gap, and model-based lock-in marginal; place the production and additive floor forms in the main identification argument; and convert the ABM and Danish counterfactual into supporting exercises.

**Tech Stack:** LaTeX, Python/pytest manuscript gates, Tectonic, pypdf, and the repository's TeX, reference, split, and render validators.

**Spec:** `docs/superpowers/specs/2026-09-10-manuscript-compression-design.md`

## Global Constraints

- Keep the conference title unchanged.
- Define "quantitative-tightening shortfall" as the cap-relative agency-MBS runoff gap, not overall QT performance.
- Treat the lock-in marginal as the primary model-based estimand; do not claim a newly identified causal elasticity.
- Present the production and additive floor forms as first-order assumptions in the main paper.
- Preserve every protected claim and every adverse or null result identified in the design.
- Keep both manuscript editions synchronized apart from the approved abstract difference.
- Do not change numerical claims merely to simplify exposition.
- Relocate technical material before removing duplicate prose.
- Use anchored, count-checked edits and test each section batch before proceeding.
- Do not push or open a pull request unless Eugene asks.

---

### Task 1: Create the disposition ledger and preservation gate

**Files:**
- Create: `specs/RECORD_manuscript_redesign_2026-09-11.md`
- Create: `paper/final/manuscript_redesign_manifest.json`
- Create: `tests/test_manuscript_redesign.py`

**Interfaces:**
- Consumes: current main sections, appendix sections, labels, exhibits, and protected claims.
- Produces: explicit `source_blocks` and `protected_claims` dispositions used by every later task.

- [ ] Write a failing test requiring every current section label to appear in `source_blocks`, every block to have one of `main`, `appendix`, `records`, `delete-duplicate`, or `delete-obsolete`, and every deletion to name the surviving statement.
- [ ] Run `python3 -m pytest tests/test_manuscript_redesign.py -q` and confirm failure because the manifest is absent.
- [ ] Create the JSON manifest and readable Markdown ledger with source label, destination, protected claims, exhibits, and reason.
- [ ] Add tests for the unchanged title, the three distinct empirical objects, both floor forms, adverse ABM findings, monthly-validation limitation, and Danish sign/incidence limitation.
- [ ] Run the redesign test to green and commit with `Define the mortgage lock-in redesign ledger`.

### Task 2: Rewrite the abstract and introduction

**Files:**
- Modify: both `paper/final/paper_final_v1*.tex` editions
- Modify: manifest, ledger, redesign test, and affected liveness gates

**Interfaces:**
- Consumes: approved paper identity and current introduction.
- Produces: concise abstract and four-to-five-page introduction using the six-move structure in the design.

- [ ] Add failing tests requiring the unchanged title, an explicit MBS-specific definition of the title's shortfall, separate cap and expectations benchmarks, imported-elasticity language, lock-in marginal, production/additive form dependence, and model-based-not-causal boundary.
- [ ] Run the redesign, abstract-hedge, headline-posture, floor-form, and printed-value tests; confirm the new budget/posture tests fail on the current introduction.
- [ ] Rewrite the canonical abstract and introduction; remove estimator catalogs, run narration, policy detail, and the multi-page Table 1.
- [ ] Apply the same body to the long-abstract edition while retaining its approved abstract distinction.
- [ ] Re-scope wording-dependent gates only after their protected claims are verified in the approved destination.
- [ ] Run targeted tests, both TeX validators, and liveness gates; commit with `Focus the paper on the lock-in marginal`.

### Task 3: Consolidate institutional setting and literature

**Files:**
- Modify: both manuscript editions, manifest, ledger, and redesign test

**Interfaces:**
- Consumes: current literature review and institutional material distributed through the introduction and discussion.
- Produces: three-to-four-page section covering lock-in evidence, prepayment/MBS cash flows, Fed runoff, and the missing portfolio translation.

- [ ] Add a failing section-budget and citation-family test.
- [ ] Run it and confirm the current literature span exceeds the approved scope.
- [ ] Rewrite around the three literature families and one missing translation; move model histories and detailed Danish/TBA material to their later destinations.
- [ ] Synchronize editions, update dispositions, run citation/reference validation and targeted gates, and commit with `Consolidate the lock-in and runoff literature`.

### Task 4: Build the data and empirical-benchmarks section

**Files:**
- Modify: both manuscript editions, manifest, ledger, and redesign test

**Interfaces:**
- Consumes: current empirical methodology and benchmark material.
- Produces: five-to-six-page section separating direct observations, calibration, reweighting, proxy overlays, and extrapolation.

- [ ] Add failing tests requiring distinct definitions of $764.748 billion, $87.8 billion, and the lock-in marginal; the 51.0% joint-cell direct-coverage statement; accounting-basis invariance of the marginal; and expectations-benchmark qualifications.
- [ ] Verify failure on the approved section structure or budget.
- [ ] Rewrite the benchmark construction, data, sample coverage, and accounting basis; move allocation grids, implementation history, and secondary diagnostics to the appendix.
- [ ] Update dispositions and run benchmark, coupon-convention, curtailment, composition, printed-value, TeX, and liveness checks.
- [ ] Commit with `Clarify the empirical benchmarks and sample coverage`.

### Task 5: Rewrite the loan-level decomposition

**Files:**
- Modify: both manuscript editions, manifest, ledger, redesign test, and affected liveness gates

**Interfaces:**
- Consumes: current hazard Sections V.A--V.F.
- Produces: seven-to-nine-page **Loan-Level Prepayment Model** section centered on the central-minus-null marginal.

- [ ] Add failing tests requiring imported-elasticity provenance, baseline floor, competing risks, central and zero-elasticity simulations, production and additive equations, portfolio-dollar mapping, and the model-based-not-causal statement.
- [ ] Run redesign plus marginal, elasticity, floor-form, assembled-corrections, inference, and printed-value gates; confirm posture/budget failure.
- [ ] Replace publication-facing `Path B` language with `Loan-Level Prepayment Model`; retain repository run identifiers only in replication material.
- [ ] Move parameter histories, full inference ladders, run narration, and Path A details to the online appendix.
- [ ] Retain Path A only as an aggregate diagnostic with its exclusion and poor path fit.
- [ ] Synchronize, validate, and commit with `Center the loan-level model on the lock-in marginal`.

### Task 6: Rewrite results and decisive validation

**Files:**
- Modify: both manuscript editions, manifest, ledger, redesign test, and consolidated exhibits

**Interfaces:**
- Consumes: current identification, robustness, Fannie, Ginnie, composition, and ABM sections.
- Produces: six-to-eight-page results section plus five-to-seven-page form/calibration/validation section.

- [ ] Add failing tests requiring the production interval and anchor, cross-form result, calibration surface, uncertainty hierarchy, Fannie status, excluded-book overlays, no outcome holdout, weak monthly timing, ABM adverse result, and withdrawn paradigm claim.
- [ ] Confirm current organization/budget failure while all legacy evidence gates remain green.
- [ ] Build a compact main decomposition table and one consolidated sensitivity/validation exhibit without mixing accounting bases.
- [ ] Rewrite results around the marginal; immediately pair any aggregate recovery with the null and its lack of holdout validation.
- [ ] Compress the ABM to supporting evidence; move mechanics, extensions, seeds, null-feasibility, and cross-design details to the online appendix.
- [ ] Relocate full grids and secondary diagnostics before removing duplicate prose.
- [ ] Run all hazard, floor, form, Fannie, Ginnie, composition, ABM, paradigm, timing, printed-value, TeX, and liveness checks; commit with `Consolidate the decisive lock-in evidence`.

### Task 7: Rewrite policy implications and conclusion

**Files:**
- Modify: both manuscript editions, manifest, ledger, redesign test, and affected gates

**Interfaces:**
- Consumes: current discussion, cap-design, Danish, conclusion, and limitations sections.
- Produces: three-to-four-page policy section and one-to-two-page conclusion.

- [ ] Add failing tests requiring cap nonbindingness, projection-to-cap arithmetic, cap-design recommendation, compact Danish extension, incidence/sign limitation, unpriced TBA cost, and the three approved concluding claims.
- [ ] Confirm the current policy/conclusion spans exceed the approved scope.
- [ ] Rewrite policy around decision-relevant cap arithmetic; move Danish recalibration, grids, and alternative anchors to the online appendix while retaining their governing qualification.
- [ ] Integrate binding limitations where they govern results and remove the repeated limitations catalog from the close.
- [ ] Run cap, Danish, buyback, headline-posture, printed-value, TeX, and liveness checks; commit with `Focus the policy implications on MBS runoff caps`.

### Task 8: Reorganize the online appendix

**Files:**
- Modify: appendix portions of both manuscript editions, manifest, ledger, and redesign test

**Interfaces:**
- Consumes: blocks assigned `appendix` by Tasks 2--7.
- Produces: substantial referee-facing appendix with stable labels and explicit main-text reachability.

- [ ] Add failing tests requiring every appendix section to support a main-text citation or protected adverse finding and every relocated block to have a resolvable destination.
- [ ] Confirm current organization fails the new reachability/disposition checks.
- [ ] Assemble benchmark/accounting derivations, full hazard/inference material, Path A, ABM details and cross-designs, composition/timing diagnostics, and Danish derivations under clear appendix headings.
- [ ] Verify every former main and appendix label's destination; preserve repository-only audit history outside the submitted prose.
- [ ] Run redesign, reference, edition-sync, full test, and liveness checks; commit with `Reorganize the referee-facing online appendix`.

### Task 9: Integrate, build, render, and measure

**Files:**
- Modify as needed: both manuscript editions, manifest, ledger, roadmap, and build documentation
- Generate under `paper/final/build_compressed/`: combined, main, online-appendix, and long-abstract PDFs

**Interfaces:**
- Consumes: all revised sections and dispositions.
- Produces: verified journal-facing artifacts and exact measurements.

- [ ] Run `python3 -m pytest tests/ -q`, `python3 tools/liveness_gates.py`, and both `tools/tex_validate.py` commands.
- [ ] Build both editions with the repository's working Tectonic binary into `paper/final/build_compressed/` without overwriting the pre-redesign PDFs.
- [ ] Split the canonical build using `tools/split_pdf.py` and the detected Online Appendix banner.
- [ ] Record exact main/appendix/combined page counts, section word counts, and relocated/consolidated/deleted quantities in the ledger.
- [ ] Run `tools/render_gate.py` against the new deliverables.
- [ ] Render and visually inspect the title page, abstract, every section opening, every changed table and figure, references transition, appendix boundary, and representative appendix pages.
- [ ] Re-read every design acceptance criterion, fix any gap, repeat the applicable verification, and commit with `Deliver the redesigned mortgage lock-in manuscript`.

### Task 10: Final branch review and handoff

**Files:**
- Review: full branch diff, commit history, final PDFs, manifest, and ledger

**Interfaces:**
- Consumes: the completed redesign branch.
- Produces: a verified handoff without push or PR creation.

- [ ] Run a fresh final full test suite, liveness gates, TeX validation, builds, split check, render gate, and page-count measurement.
- [ ] Confirm the current checkout outside the worktree remains untouched except for pre-existing temporary review files.
- [ ] Report exact output paths, page counts, validation evidence, commit list, and any residual author decisions.
