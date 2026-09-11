# Manuscript Compression Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a 38--42 page main paper and 12--15 page referee-facing online appendix while preserving the complete research record in a separate technical and replication supplement.

**Architecture:** Treat the hazard decomposition as the empirical spine, convert the ABM into a cross-design robustness exercise, consolidate interpretation-changing checks in the article, and relocate audit-level material into a standalone supplement. Use an explicit disposition ledger and automated preservation checks so every substantive source block is retained, relocated, or deleted only for a recorded duplication or obsolescence reason.

**Tech Stack:** LaTeX, Python/pytest manuscript gates, Tectonic, pypdf, and the repository's TeX, reference, split, and render validators.

**Spec:** `docs/superpowers/specs/2026-09-10-manuscript-compression-design.md`

## Global Constraints

- Preserve every protected claim in the design specification.
- Keep the canonical and long-abstract manuscript bodies identical.
- Do not simplify a numeric claim, weaken a hedge, suppress an adverse result, or remove a unique limitation.
- Relocate technical content before deleting duplicate prose.
- Use anchored, count-checked edits rather than broad regular-expression surgery.
- Re-scope a gate only after its protected claim exists in an approved destination and the reason is recorded.
- Do not push or open a pull request unless Eugene asks.

---

### Task 1: Establish the disposition ledger and preservation gate

**Files:**
- Create: `specs/RECORD_manuscript_compression_2026-09-10.md`
- Create: `paper/final/compression_manifest.json`
- Create: `tests/test_manuscript_compression.py`
- Read: both manuscript variants, `tools/liveness_gates.py`, and `tests/*.py`

**Interfaces:**
- Consumes: every current section, exhibit, label, citation family, and pinned claim.
- Produces: `protected_claims`, `section_budgets`, and `source_blocks` with explicit dispositions.

- [ ] **Step 1: Write the failing manifest test**

```python
def test_manifest_covers_every_source_section():
    manifest = json.loads(MANIFEST.read_text())
    labels = source_section_labels(CANONICAL.read_text())
    assert labels <= {block["label"] for block in manifest["source_blocks"]}

def test_every_block_has_a_reasoned_disposition():
    allowed = {"main", "appendix", "supplement", "delete-duplicate", "delete-obsolete"}
    blocks = json.loads(MANIFEST.read_text())["source_blocks"]
    assert all(b["disposition"] in allowed and b["reason"].strip() for b in blocks)
```

- [ ] **Step 2: Run it and confirm failure because the manifest is absent**

Run: `python3 -m pytest tests/test_manuscript_compression.py -q`

- [ ] **Step 3: Inventory each section and subsection**

Record source span, current pages, approximate words, protected claims, pins, exhibits, destination, and deletion reason when applicable.

- [ ] **Step 4: Create the JSON manifest and readable Markdown ledger**

Every deleted block must name the surviving canonical statement. Every relocated block must name its destination label.

- [ ] **Step 5: Complete the preservation tests**

Require each protected claim in a permitted destination, every reference target to resolve, every supplement move to have a destination, and both manuscript bodies to match after abstract normalization.

- [ ] **Step 6: Run the test until it passes**

Run: `python3 -m pytest tests/test_manuscript_compression.py -q`

- [ ] **Step 7: Commit**

Commit message: `Define the manuscript compression ledger`.

### Task 2: Create the technical and replication supplement

**Files:**
- Create: `paper/final/technical_replication_supplement.tex`
- Modify: manifest, ledger, and compression test
- Read: `paper/final/replication_appendices.tex`

**Interfaces:**
- Consumes: blocks marked `supplement` and the existing replication appendices.
- Produces: a standalone, compilable supplement with stable labels and recorded provenance.

- [ ] **Step 1: Add a failing supplement-completeness test**

Require a title, scope statement, existing replication appendices, and every manifest label destined for the supplement.

- [ ] **Step 2: Run it and confirm the missing-file failure**

Run: `python3 -m pytest tests/test_manuscript_compression.py -q`

- [ ] **Step 3: Assemble the supplement without deleting source material**

Organize full ABM details, hazard/inference apparatus, diagnostic grids, policy mechanics, run indexes, and adjudication/history. Initially relocate byte-preservingly or include stable extracted sources.

- [ ] **Step 4: Update manifest destinations and the ledger**

Record whether each block was moved byte-preservingly, consolidated, or retained in the existing replication appendices.

- [ ] **Step 5: Build and validate**

Run:

```bash
~/Downloads/texbuild/tectonic -X compile paper/final/technical_replication_supplement.tex --outdir paper/final/build_compressed
python3 tools/tex_validate.py paper/final/technical_replication_supplement.tex --bib paper/final/references.bib
python3 -m pytest tests/test_manuscript_compression.py -q
```

- [ ] **Step 6: Commit**

Commit message: `Add the technical replication supplement`.

### Task 3: Rewrite the front end around one empirical question

**Files:**
- Modify: both manuscript variants, manifest, ledger, and compression test
- Test: abstract, headline-posture, benchmark, and citation tests

**Interfaces:**
- Consumes: the final benchmark and hazard posture.
- Produces: a three-page introduction and a three-page combined institutional-setting/literature section.

- [ ] **Step 1: Add failing word-budget and claim-preservation tests**

Require the benchmark, preferred marginal, binding interval, model-based-not-causal limitation, expectations qualification, and contribution statement.

- [ ] **Step 2: Confirm the current span fails the budget**

Run: `python3 -m pytest tests/test_manuscript_compression.py tests/test_abstract_hedge_gate.py tests/test_headline_posture_gate.py -q`

- [ ] **Step 3: Rewrite the introduction**

Use five moves: problem, mechanism, question, headline result with uncertainty, and contribution/limits. Remove estimator inventories, robustness catalogs, navigation prose, and detailed policy mechanics.

- [ ] **Step 4: Consolidate institutional setting and literature**

Organize around mortgage lock-in, QT/MBS runoff, and the missing decomposition. Retain full discussion only where a paper governs the elasticity or creates a direct apparent conflict.

- [ ] **Step 5: Synchronize variants and update dispositions**

Record every deleted paragraph and its surviving statement or destination.

- [ ] **Step 6: Verify and commit**

Run the targeted tests, both TeX validations, and liveness gates. Commit message: `Focus the manuscript front end`.

### Task 4: Collapse methodology and the ABM into supporting roles

**Files:**
- Modify: both variants, supplement, manifest, ledger, and compression test
- Test: ABM, paradigm-withdrawal, and printed-value gates

**Interfaces:**
- Consumes: current methodology and ABM sections.
- Produces: a five-page data/benchmark/design section and a compact ABM robustness subsection.

- [ ] **Step 1: Add failing budget and ABM-protection tests**

Require the fifty-seed result, real-covariate crossing, path-fit failure, withdrawn paradigm claim, and reason no ABM differential is reported.

- [ ] **Step 2: Confirm the current span fails**

Run: `python3 -m pytest tests/test_manuscript_compression.py tests/test_abm_lead_gate.py tests/test_paradigm_withdrawal_gate.py -q`

- [ ] **Step 3: Rewrite methodology around data, benchmark, and the primary hazard estimator**

Keep only conventions required to interpret dollars and recovery percentages. Relocate allocation grids and implementation history.

- [ ] **Step 4: Replace the standalone ABM section**

Retain one exhibit or consolidated-table row, the adverse level/path results, the real-covariate crossing and withdrawal, and the null infeasibility. Move mechanics and extension inventories to the supplement.

- [ ] **Step 5: Verify and commit**

Run targeted tests, both TeX validations, and liveness gates. Commit message: `Recast the ABM as a robustness exercise`.

### Task 5: Compress the hazard framework to the empirical spine

**Files:**
- Modify: both variants, online appendix, supplement, manifest, ledger, and compression test
- Test: all hazard, floor, marginal, inference, and printed-value gates

**Interfaces:**
- Consumes: current hazard Sections V.A--V.F and related appendices.
- Produces: a 10--12 page section containing the estimand, model, null, result, binding inference, interpretation, and unique limitations.

- [ ] **Step 1: Add failing budget and protected-claim tests**

Require the central/null/marginal decomposition, binding interval, Webb comparison, floor sensitivity, elasticity transport, moving/refinancing mapping, sample-to-book qualification, and model-based-not-causal limitation.

- [ ] **Step 2: Confirm the current span fails**

Run compression, marginal-identity, floor-form, elasticity, assembled-corrections, inference, and printed-values tests.

- [ ] **Step 3: Rewrite Path B and identification**

Keep the final specification and meaningful null. Move parameter histories, run narration, inference ladders, and row-by-row table readings. Consolidate the qualifications without merging distinct assumptions.

- [ ] **Step 4: Reduce Path A and Fannie to validation paragraphs**

Keep Path A's directional result and headline exclusion. Keep Fannie's result and its status as a robustness check rather than an outside test.

- [ ] **Step 5: Consolidate interpretation**

State once what level recovery establishes, once what the marginal measures, and once which uncertainty governs each quantity.

- [ ] **Step 6: Verify, build, and commit**

Run all hazard tests, full gates, both TeX validations, and a fresh build. Commit message: `Compress the hazard framework around the main estimand`.

### Task 6: Consolidate interpretation-changing robustness checks

**Files:**
- Modify: both variants, supplement, manifest, ledger, and compression test
- Create or modify: one consolidated main-text robustness table
- Test: all check-specific gates

**Interfaces:**
- Consumes: current robustness section and distributed robustness prose.
- Produces: a 4--5 page section covering floor, form, composition, Fannie, ABM cross-design, and policy anchors.

- [ ] **Step 1: Add a failing robustness-budget test**

Require the six decisive checks and their qualifications while disallowing run identifiers and row-by-row grid narration in the main robustness span.

- [ ] **Step 2: Confirm the current section fails**

Run compression plus cross-design, floor, composition, settlement, seasonal, episode, and depth-ladder tests.

- [ ] **Step 3: Build the consolidated exhibit**

Use check, preferred comparison, effect on recovery/marginal, and interpretation columns. Never combine incompatible accounting bases.

- [ ] **Step 4: Relocate supporting mechanics**

Move settlement edges, full grids, seasonal decomposition, depth ladders, timing diagnostics, age bands, and alternative transforms according to the manifest.

- [ ] **Step 5: Rewrite each retained check as question, result, interpretation, pointer**

Preserve adverse threshold crossings and sign changes.

- [ ] **Step 6: Verify, build, and commit**

Commit message: `Consolidate the decisive robustness checks`.

### Task 7: Shorten policy discussion while preserving both Danish anchors

**Files:**
- Modify: both variants, supplement, manifest, ledger, and compression test
- Test: cap and Danish gates

**Interfaces:**
- Consumes: discussion, cap-design, policy, and Danish sections.
- Produces: a 4--5 page policy section with compact welfare and unpriced-cost discussion.

- [ ] **Step 1: Add failing policy-budget and protection tests**

Require cap nonbindingness, implied-cap arithmetic, U.S.-intercept result, Danish-level result, sign sensitivity, incidence limitation, and unpriced TBA-liquidity cost.

- [ ] **Step 2: Confirm the current span fails**

Run compression, cap-monthly-units, state-contingent-cap, buyback-incidence, buyback-discount, and Danish-interest-only tests.

- [ ] **Step 3: Rewrite cap design around decision-relevant arithmetic**

Retain the implied range, nonbindingness, and designer takeaway. Relocate grid machinery.

- [ ] **Step 4: Rewrite the Danish counterfactual**

Retain the rule, preferred and alternative anchors, sign sensitivity, and investor-side limitation. Move fine grids and intermediate accounting.

- [ ] **Step 5: Verify, build, and commit**

Commit message: `Focus the policy counterfactual on the two anchors`.

### Task 8: Replace the conclusion and limitations with a non-repetitive close

**Files:**
- Modify: both variants, manifest, ledger, and compression test
- Test: compression and headline-posture gates

**Interfaces:**
- Consumes: current conclusion and limitations.
- Produces: a one-page conclusion and approximately two pages of limitations.

- [ ] **Step 1: Add a failing conclusion-budget test**

Require the result, cap implication, policy qualification, model-based-not-causal statement, and each named limitation.

- [ ] **Step 2: Confirm the current close fails**

Run compression and headline-posture tests.

- [ ] **Step 3: Rewrite the conclusion**

State the result, interpretation, and policy implication without new evidence or robustness replay.

- [ ] **Step 4: State each limitation once**

Cover identification, transport, data, model dependence, expectations-benchmark interpretation, and unpriced policy costs. Preserve project-status material in the supplement or ledger.

- [ ] **Step 5: Verify, build, and commit**

Commit message: `Close the paper without repeating the results`.

### Task 9: Rebuild the referee-facing online appendix

**Files:**
- Modify: appendix portion of both variants, supplement, manifest, ledger, and compression test
- Test: cross-reference and appendix-reachability tests

**Interfaces:**
- Consumes: blocks designated `appendix`.
- Produces: a 12--15 page appendix in which every section supports a cited main-text statement.

- [ ] **Step 1: Add failing appendix-budget and reachability tests**

Require each appendix section to be cited from the main paper and each appendix citation to resolve.

- [ ] **Step 2: Confirm the current 48-page appendix fails**

Run: `python3 -m pytest tests/test_manuscript_compression.py -q`

- [ ] **Step 3: Assemble the essential appendix**

Retain compact benchmark/accounting construction, hazard parameters, binding inference, central floor/form sensitivity, concise ABM comparison, and essential policy derivations.

- [ ] **Step 4: Verify every former appendix label's destination**

Record whether it survives, moves to the supplement, or is replaced by a consolidated exhibit.

- [ ] **Step 5: Build, split, verify, and commit**

Use `tools/split_pdf.py` to locate the online-appendix banner. Commit message: `Rebuild the online appendix for referee use`.

### Task 10: Integrate, render, and measure the package

**Files:**
- Modify as needed: variants, supplement, manifest, ledger, `PAPER_ROADMAP.md`, and build documentation
- Generate under `paper/final/build_compressed/`: combined, main, online-appendix, and technical-supplement PDFs

**Interfaces:**
- Consumes: all prior tasks.
- Produces: verified artifacts and exact page, word, relocation, and deletion measurements.

- [ ] **Step 1: Run the complete automated verification**

```bash
python3 -m pytest tests/ -q
python3 tools/liveness_gates.py
python3 tools/tex_validate.py paper/final/paper_final_v1.tex --bib paper/final/references.bib
python3 tools/tex_validate.py paper/final/paper_final_v1_long_abstract.tex --bib paper/final/references.bib
python3 tools/tex_validate.py paper/final/technical_replication_supplement.tex --bib paper/final/references.bib
```

- [ ] **Step 2: Build every deliverable from current sources**

Use `~/Downloads/texbuild/tectonic`, write outputs to `paper/final/build_compressed/`, and split from the detected banner rather than a hard-coded page.

- [ ] **Step 3: Measure outputs**

Use pypdf for page counts and the manifest's word-count convention for section totals. Record baseline, final, relocated, consolidated, and deleted quantities.

- [ ] **Step 4: Run the render gate**

Require zero off-page content, clipped tables, unresolved references, or unreadable glyph substitutions.

- [ ] **Step 5: Visually inspect changed pages**

Render and inspect the title page, every main-section opening, every changed table/figure, the references transition, the appendix banner and section openings, and representative supplement pages.

- [ ] **Step 6: Check every design acceptance criterion**

Document any justified page overage. Do not claim the target without fresh page-count evidence.

- [ ] **Step 7: Commit the integrated package**

Commit message: `Deliver the compressed manuscript package`.

- [ ] **Step 8: Hand off without pushing**

Report exact pages and words, relocated versus deleted quantities, test/build/render evidence, commit list, and remaining authorial decisions.
