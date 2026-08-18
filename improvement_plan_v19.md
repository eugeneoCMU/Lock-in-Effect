# Improvement Plan — `revised_paper_v19.pdf` → v20

**Input:** the five-reviewer panel package (`~/Downloads/revised_paper_v19_PANELREV.md`, 2026-08-04). Decision: Major Revision, panel mean ≈ 68.1/100.
**Coverage rule:** every panel item is accounted for below — 5 must-fix (R1–R5), 10 should-fix (S1–S10), the Priority-3 list, DA C1–C5 (required responses), DA M1–M6, DA m1–m6, the DA's 6 alternative paths, and all 29 Questions for Authors. Nothing is silently dropped; the traceability table at the end maps every ID to a plan item or an explicit no-action disposition.
**Overall effort:** Substantial — ~2.5–4 calendar weeks. The load is dominated by the restructure (Phase 3); only three items need new runs, all small.
**Character of the revision:** subtraction and relocation, not re-analysis. No reviewer found an error requiring the core pipeline to be re-run. The paper's numbers survive; the claims-layer and the document form are what change.

---

## Phase 0 — Decision gates (½ day; blocks everything downstream)

Four decisions only the author can make. Each has a recommendation; deciding them first prevents rewriting the same text twice.

**D1 — Headline convention posture.** The panel's minimum ask (R1 W2, R2 W1, DA M1/C3) is not that you abandon the max-form/s=1 headline, but that the abstract and results box carry its conditioning and the convention envelope (+0.9 to +13.2, named variants) alongside it.
*Options:* (a) keep the +5.6 anchor inside a fully-conditioned single results box; (b) drop any privileged anchor and headline the form-conditional range itself.
*Recommendation:* **(a)** — smallest diff that satisfies all four reviewers; (b) only if you conclude the s=0 semantics argument cannot bear the weight (the paper already concedes at p. 42 that your floor semantics point at the hull's upper region — decide whether that concession is compatible with keeping the conservative anchor as "the" number).

**D2 — Title and framing.** EIC suggests the title signals the mechanism (established) rather than the contribution (the decomposition + cap arithmetic); the trade-off/trilemma narrative is the paper's least-supported element (EIC W4, DA M5).
*Options:* (a) keep title, rewrite abstract decomposition-first, demote the trade-off to discussion; (b) retitle (e.g., "How Much of the Fed's QT Shortfall Was Lock-In? A Decomposition").
*Recommendation:* **(a)** unless a venue change (D3) argues otherwise; either way the mobility leg gets explicitly attributed to the literature (EIC W4) *and* bounded in-paper (R3 W1 — the two remedies are compatible; the editor's arbitration was "do both").

**D3 — Target venue → length budget.** EIC's realistic list: JME (heaviest compression), **JMCB / IJCB (natural fits)**, J. Financial Stability, RE Economics / J. Housing Economics.
*Recommendation:* pick JMCB/IJCB-class norms as the working target → main text ≤ 45–50 pp., abstract ≤ 150 words. This decision sets Phase 3's scope; a conference (Carroll Round) version can be cut from the same restructured source.

**D4 — Contest-vs-concede posture per DA CRITICAL** (feeds the response letter):
| Finding | Posture | One-line rationale |
|---|---|---|
| C1 (denominator-conditional headline) | **Concede & fix** | You compute both denominators yourself; present them symmetrically (Phase 2). |
| C2 (null embeds behavior / calibration echo) | **Concede components, contest the label** | Rename + run the compounding-consistent null + surface the floor-depression alternative; contest "tautology" with Table 6's floor-sensitivity (recovery moves materially with floor level, so the decomposition has content conditional on the floor). |
| C3 (single-layer interval) | **Concede & fix** | Conditioning statement + envelope in the results box; note the sign claim rests on rate-configuration, not the interval (p. 46). |
| C4 (ABM verdict doesn't follow) | **Concede** | Condition the conclusion's "two central findings" framing; compress the ABM (Phase 3). |
| C5 (Danish "small" is the band edge) | **Partially contest** | Defend the rule-only zero-refinance anchor's semantics (R2 corroborates it as the correct production choice); concede the abstract must carry the band + incidence conditioning. |

---

## Phase 1 — Runs and data checks (2–3 days; start early — outputs feed Phase 2 text)

**All runs are author-only under repo discipline (spec-before-run, frozen grids, gates).** Do these first: their outputs change sentences in the abstract and V.E.

| ID | Item | Source | Notes |
|---|---|---|---|
| RUN-1 | **Compounding-consistent β1=0 null** (counterfactual balance path, as the Danish legs already implement) to size the marginal's upper-bound bias now disclosed only in Table 11's note | R5 / R1 W4, Q3; EIC Q7; DA C2 | The single most important new number: it converts "an admitted, unquantified upward bias" into a priced one. Write the spec (grid + interpretation rule) before running. |
| RUN-2 | **Propagate the floor read's sampling error to the null's 85.7%** (marginal-side machinery exists) | S2 / R1 Q8 | Small; gives the mechanical-majority claim the same interval discipline as the marginal. |
| RUN-3 | **Few-cluster coverage simulation** calibrated to the leverage profile (5.9 effective clusters, 0.33 max leverage) to defend Webb wild-t as the binding layer — *or* the no-run fallback: adopt the widest bias-respecting read (CR3/BM [+2.3, +9.6]) as binding | S2 / R1 W3, Q1 | Recommendation: attempt the simulation (a designed DGP-based coverage check is a referee-proof answer); the fallback costs only width. |
| CHK-1 | **Batzer et al. (2024) estimand**: quote their construct exactly; fix the "$2.4T foregone capital gains" characterization if it misstates | S5 / R2 Q1; R3 minor | Document check, no run. |
| CHK-2 | **Ginnie 20.4% share**: add as-of date + source; reconcile the $1,940.9B parsed book vs the benchmark's implied holdings path | S5 / R2 Q2 | Provenance sentences. |
| CHK-3 | **"Joint-and-several"** for modern Danish series: verify against Berg et al. (2018); likely delete the phrase | S5 / R2 Q7 | One phrase. |
| CHK-4 | **Ginnie GMAR assumption counts** 2023–25: attempt to turn the 20.4% assumability carve-out upper bound into a take-up estimate | S5 / R2 Q8; R3 Q6 | Data acquisition; if unavailable, state that it was attempted. |
| OPT-1 | *(Optional)* Later OMO-vintage expectations complement (2023/2024 reports) to date the surprise year-by-year | R2 Q5; DA alt-path 6 | Nice-to-have; directly probes the "projection embeds lock-in" confound you currently label untestable. Decide scope before Phase 2. |
| OPT-2 | *(Optional / future-work note)* Joint discipline of s via Graybill–Mangum's deed-record moving hazard | R1 Q2; R2 Q6 | Likely a research task, not a revision task. Recommendation: add as named future work + response-letter answer, not a v20 run. |

---

## Phase 2 — Claim surgery (2–3 days; after Phase 1 numbers land)

The wording/framing pass. Every item touches the claims layer, not the analysis.

| ID | Item | Source | Acceptance criterion |
|---|---|---|---|
| P2-1 | **Renaming pass**: "mechanical" → "rate-inelastic baseline" globally; "never about behavior" → "never about the rate-responsive margin"; retire or define "trapped liquidity"; fix "I measure what it cost the Federal Reserve" against the p. 18 standing paragraph; "as homeowners relocated naturally" → "as principal was repaid" | Must-fix R2; consensus 2; R2 W3; P3 list | No instance of the old vocabulary survives unqualified; abstract parenthetical no longer has to carry the entire correction. |
| P2-2 | **Consolidated results box** (the new single source of truth): object; conditioning (production floor form, s=1, 100 PSA, δ=6.5%); binding interval [+2.9,+8.7] *inside* the convention envelope (+0.9 to +13.2 with named variants); both denominators side by side — cap-relative (rate-inelastic majority 85.7%, with RUN-2's interval) and projection-relative (≈ half the surprise; 23–49% / 38–80% with the allocation sensitivity attached, per DA m4); RUN-1's compounding-consistent marginal. Everything else in the paper points here. | Must-fix R1; DA C1/C3; consensus 3 | A reader of the box alone can state the paper's claim without error; +5.6 is labeled "anchor," not "headline" (R3 minor). |
| P2-3 | **Abstract rewrite ≤ 150 words**, decomposition-first: shortfall → rate-inelastic majority → bounded margin (one interval + envelope clause) → cap-design implication → Danish result with band/incidence clause | EIC W1/Title & Abstract; R2 W3; DA C1/C5 | One number per object; no orphaned qualifications. |
| P2-4 | **Form symmetry**: max-vs-additive and the mixture curve get weight-proportionate treatment in abstract + V.E (not one clause); state plainly that the s=0 endpoint is a convention your own semantics do not privilege | Must-fix R3; DA M1; EIC Q5 | The additive +11.2 appears wherever +5.6 does. |
| P2-5 | **Danish "small" conditioning**: abstract sentence carries the +$61.2→$256.8B band, the incidence bracket, and the anchor's status; keep the rule-only anchor (D4/C5 posture) | S1; DA C5 | "Small" never appears without its conditions. |
| P2-6 | **Pre-commitment credential calibration**: temper front-matter "pre-committed" claims to what Table 27 records, or attach the Olken-style caveat where the credential is claimed | S8; DA M6 | The credential and the adjudication record can be read together without tension. |
| P2-7 | **Overlay estimand statement**: one passage stating why Ginnie/vintage overlay values (+2.9–4.4 book-consistent) are a change of estimand, and what the book-wide headline conditions on | S9; DA M2 | A referee can locate the estimand boundary in one place. |
| P2-8 | **Monthly magnitude sentence**: "~$1B/month against a $35B/month cap" stated once | S10; DA m6 | Present. |
| P2-9 | **Floor-depression alternative surfaced in main text**: the 2019 leg's 6.91% read, its exclusion's "unadjudicable below gap ≤ 0, not refuted" status (p. 80), and what it would imply — currently Appendix J material | Must-fix R5; DA C2, alt-path 2 | The strongest standing challenge is confronted where the headline is stated. |
| P2-10 | **Episode-specificity scope sentence** for the sign-forcing configuration (breaks in mixed-moneyness windows) in the limitations | DA m1 | Present. |
| P2-11 | **"Replication" label qualified** at first use (certifies pipeline determinism + cross-agency compositional stability, not external validity) | DA m3 | Present. |
| P2-12 | **Elasticity's evidential basis** ("external literature alone," p. 36) stated abstract-adjacent, not only in V.E | DA M3 | Present near the headline. |

---

## Phase 3 — Restructure + additions (1–1.5 weeks; the bulk of the work)

**Structure (must-fix R4; consensus 1, 5; DA C4/M4):**
- Main text ≤ 45–50 pp. (per D3). The EIC's preservation list is the skeleton: Table 1, III.B, V.B/V.E compressed, VI.B, VI.D, VII.F — everything else online.
- **ABM → one short subsection + appendix** (stress-test verdict + cross-design hedge only); strip residual "structurally distinct estimators agree" phrasing; conclusion's "two central empirical findings" framing conditioned per C4.
- Move Appendices A, G, H, J–O (provenance/adjudication apparatus) to the replication package; Appendix O and the superseded-figures ledger live in the repo README, not the journal file.
- Tables 5 (assembly) and 9 (inference ladder) relocate adjacent to V.E — they are the real headline exhibits.
- Run tags out of main-text prose (→ table notes/appendix); the demotion narrative (+9.2 → +5.6) told once, as design, where the floor program is introduced; delete the "How to read this paper" shortcut once the structure makes it redundant.
- Path A out of headline-adjacent exhibits or clearly fenced as excluded-from-headlines, stated once prominently (DA m2; R1 minor on spec v3/v4).

**Additions (integrate during the restructure so sections are touched once):**
| ID | Item | Source |
|---|---|---|
| P3-A1 | Household-side subsection: constrained-moves band implied by the marginal at book-average balance × per-move welfare estimates (Gerardi et al. 2024); one renters/first-time-buyers sentence | S3; R3 W1; EIC W4 arbitration |
| P3-A2 | Distributional tilt promoted to conclusion as an equity statement (1.23–1.26× below-740-FICO, 1.23× above-80-LTV, with its placebo discipline) | S3; R3 W3 |
| P3-A3 | Taxpayer/remittances carry paragraph: trapped balance × funding spread × WAL extension | S4; R3 W2, Q1 |
| P3-A4 | Policy box (one page): what a QT2 designer takes (floor band in CPR units, scheduled-amortization path, elasticity band), what they must not take (+5.6 as a point; cap-shortfall as failure), which accounting basis answers which question | S7; R3 W5, Q5 |
| P3-A5 | Deliberate-non-bindingness paragraph in VI.B: the cap as a communication device; test the design lesson against the FOMC's stated primarily-Treasuries composition objective; state the partial-equilibrium boundary (incl. sales-spread feedback) where the recommendations are made | R3 W4, Q3/Q4; DA alt-path 3 |
| P3-A6 | Institutional note: $35B MBS cap retained in the June 2024 / March 2025 runoff-slowing decisions; confirm no above-cap month | S5; R2 institutional #1, Q4 |
| P3-A7 | One sentence on why current-face differencing rather than CUSIP factor paydowns (or adopt factor series as future work) | R2 institutional #2, Q3 |

**Priority-3 text pass (fold into the same sweep):** sentence-length/nesting reduction; accounting-basis map surfaced early; peak-lag convention standardized; ±1-point materiality convention stated once; Table 12 re-derived natively (also DA m5) and cross-referenced from the intro (R3); Fig. 7 trimmed to its informative range; Berger et al. draft-history commentary → footnote; SSRN entries get IDs; Fonseca–Liu restatements consolidated (p. 27/p. 36); "no loan-purpose field" → "no termination-reason field"; re-tag the two uncommitted-tree runs so manifests name reproduction checkouts.

**References to add (S6; verify before citing):** Fuster, Goodman, Lucca, Madar, Molloy & Willen (2013, FRBNY EPR); Hancock & Passmore (2011, JME); Amromin, Bhutta & Keys (2020, ARFE); Song & Zhu ("Mortgage Dollar Roll," RFS — verify vol/year); optionally McPhail–Schnabl–Tuckman (verify). R3's cross-disciplinary list (Porter; Power; Tucker; Mian–Sufi; Campbell 2006) is optional — cherry-pick Campbell (2006) for P3-A1's welfare vocabulary; the rest are context, not obligations.

---

## Phase 4 — Repo mechanics (1–2 days; specific to this project's discipline)

1. **Gate re-sync is a deliberate step, not a casualty.** The liveness-gate suite asserts manuscript phrasing and ordering; the renaming pass (P2-1) and abstract rewrite (P2-3) will break gates *by design*. Re-sync gates to the new text (gates follow the manuscript — same direction as the 2026-07-19 re-sync), then re-run the full suite + tests to green.
2. New runs (RUN-1/2/3) follow spec-before-run: write and commit the spec (grid, interpretation rule, gate number) before executing; add gates + tests per the established pattern.
3. Rebuild both PDF variants; verify 0-undefined; recut the split; regenerate md/txt editions (tools/editions/) and the bundle.
4. Work on a fresh round branch off the current paper branch; do not touch main. Push remains author-only.

---

## Phase 5 — Response letter + re-review (2–3 days)

1. Fill the response-letter skeleton (below) — every panel concern gets a Response + Changes-made entry; DA CRITICALs get explicit acknowledge-and-respond entries even where contested (C5).
2. Self-check against the panel's own re-review standard: each concern independently verified against the revised manuscript, not just claimed addressed.
3. Optional: run the reviewer panel in **re-review mode** (original roadmap + revised manuscript + response letter → verification matrix + residual issues + new decision) before circulating v20.

---

## Suggested calendar

| Week | Work |
|---|---|
| Wk 1, days 1–2 | Phase 0 decisions; Phase 1 specs written and committed; RUN-1/2/3 executed; CHK-1..4 |
| Wk 1, days 3–5 | Phase 2 claim surgery (all 12 items) |
| Wk 2 – mid Wk 3 | Phase 3 restructure + additions + P3 text pass + references |
| mid Wk 3 | Phase 4 gate re-sync, rebuilds, editions |
| end Wk 3 / Wk 4 | Phase 5 response letter, optional re-review, buffer |

---

## Full traceability table

| Panel ID | Disposition | Plan item |
|---|---|---|
| Must-fix R1 | Planned | P2-2 (+ P2-3) |
| Must-fix R2 | Planned | P2-1 |
| Must-fix R3 | Planned | P2-4 (+ D1) |
| Must-fix R4 | Planned | Phase 3 structure |
| Must-fix R5 | Planned | RUN-1 + P2-9 (+ Table-11-note promotion into V.E) |
| S1 | Planned | P2-5 |
| S2 | Planned | RUN-2, RUN-3 |
| S3 | Planned | P3-A1, P3-A2 |
| S4 | Planned | P3-A3 |
| S5 | Planned | CHK-1..4, P3-A6, P3-A7 |
| S6 | Planned | Phase 3 references |
| S7 | Planned | P3-A4 |
| S8 | Planned | P2-6 |
| S9 | Planned | P2-7 |
| S10 | Planned | P2-8 |
| Priority-3 list (all) | Planned | Phase 3 text pass |
| DA C1 | Concede & fix | P2-2, P2-3 (+ response letter) |
| DA C2 | Concede components | P2-1, P2-9, RUN-1 (+ response letter contests "tautology" via Table 6 floor-sensitivity) |
| DA C3 | Concede & fix | P2-2 (+ response notes sign rests on rate configuration) |
| DA C4 | Concede | Phase 3 ABM compression + conclusion conditioning |
| DA C5 | Partially contest | P2-5 (+ response defends rule-only anchor with R2's domain read) |
| DA M1 | Planned | P2-4 |
| DA M2 | Planned | P2-7 |
| DA M3 | Planned | P2-12 (+ OPT-2 as future work) |
| DA M4 | Planned | Phase 3 structure |
| DA M5 | Planned | D2 + P3-A1 (attribute + bound) |
| DA M6 | Planned | P2-6 |
| DA m1 | Planned | P2-10 |
| DA m2 | Planned | Phase 3 (Path A fencing) |
| DA m3 | Planned | P2-11 |
| DA m4 | Planned | P2-2 (allocation sensitivity travels with the number) |
| DA m5 | Planned | Phase 3 text pass (Table 12) |
| DA m6 | Planned | P2-8 |
| DA alt-path 1 | Response letter | Label-symmetry fix for the Aladangady entry (with R1 Q5) |
| DA alt-path 2 | Planned | P2-9 (+ named future work) |
| DA alt-path 3 | Planned | P3-A5 |
| DA alt-path 4 | Response letter / future work | Note observed-speed whole-book accounting as a design alternative; the overlays already implement its informative cells |
| DA alt-path 5 | Response letter | Realized-Danish anchor's four confounds; sentence added with P2-5 |
| DA alt-path 6 | Optional | OPT-1 |
| EIC Q1–Q7 | Response letter | Q1→P2-2; Q2→Phase 3 ABM; Q3→P2-3/intro contribution list; Q4→D3/Phase 3; Q5→P2-4 (answer directly: state whether policy conclusions change at +11); Q6→D2; Q7→RUN-1 |
| R1 Q1–Q8 | Response letter | Q1→RUN-3; Q2→OPT-2; Q3→RUN-1; Q4→response (PSA convention span; observed age-profile discussion); Q5→label-symmetry fix (alt-path 1); Q6→P2-2 anchor framing (address the 5.51/5.52 asymmetry explicitly); Q7→P2-1; Q8→RUN-2 |
| R2 Q1–Q8 | Response letter | Q1→CHK-1; Q2→CHK-2; Q3→P3-A7; Q4→P3-A6; Q5→OPT-1; Q6→OPT-2; Q7→CHK-3; Q8→CHK-4 |
| R3 Q1–Q6 | Response letter | Q1→P3-A3; Q2→P3-A2; Q3→P3-A5; Q4→P3-A5 (partial-equilibrium boundary); Q5→P3-A4; Q6→CHK-4 |
| Positive findings (all reviewers' Strengths) | Acknowledge | Response letter opening; no manuscript action |

---

## Response Letter Skeleton

```
Dear Editors and Reviewers,

Thank you for the unusually thorough five-perspective review. We were encouraged that
the panel unanimously credited [cap arithmetic / transparency apparatus / Danish
repricing / Fannie replication], and we recognize the equally unanimous diagnosis:
the measurement discipline outran the presentation discipline. The revision
accordingly changes the claims layer and the document form, not the analysis.

Summary of major changes:
1. Renamed the β1=0 construction "rate-inelastic baseline" throughout; rewrote the
   abstract (≤150 words) decomposition-first.  [R2-consensus, DA C2]
2. Added a consolidated results box stating the claim once, with conditioning,
   the convention envelope, and both denominators.  [R1-consensus, DA C1/C3]
3. Ran the compounding-consistent null: [RESULT].  [R1 W4, EIC Q7, DA C2]
4. Restructured to [N] pp. main text; ABM compressed to §[X] + appendix.  [EIC W1/W2]
5. [Form-symmetry / Danish conditioning / household bound / carry / policy box ...]

## Response to the Editor-in-Chief
### EIC-Q1 (single sentence the paper stands behind)
Response: [The results box states: ... — the wild-cluster interval is the
coverage-bearing statement; the envelope is the convention statement.]
Changes made: [box location]
### EIC-Q2 … EIC-Q7, EIC-W1 … W5
[one entry each; PLACEHOLDER]

## Response to Reviewer 1 (Methodology)
### R1-W1 (naming) / R1-W2 (interval scope) / R1-W3 (clusters) / R1-W4
(renormalization) / R1-W5 (two-estimator) / R1-Q1 … Q8 / minors
[one entry each; PLACEHOLDER]

## Response to Reviewer 2 (Domain)
### R2-W1 … W5 / R2-Q1 … Q8 / institutional notes / references / minors
[one entry each; PLACEHOLDER]

## Response to Reviewer 3 (Perspective)
### R3-W1 … W5 / R3-Q1 … Q6 / minors
[one entry each; PLACEHOLDER]

## Response to the Devil's Advocate
### DA-C1 [concede & fix — symmetric denominators; changes: …]
### DA-C2 [concede components; contest "tautology": Table 6 shows recovery moves
one-for-one with floor level, so the decomposition is not a restatement; the
floor-depression alternative is now confronted in §V.E and priced as far as the
design permits (RUN-1: [RESULT]); its full estimation is named future work]
### DA-C3 [concede & fix — conditioning; sign rests on rate configuration, not
the interval]
### DA-C4 [concede — ABM verdict conditioned; section compressed]
### DA-C5 [partially contest — the rule-only zero-refinance anchor is the
semantics-consistent production choice (cf. R2's assessment); abstract now
carries the band and incidence conditions]
### DA-M1 … M6, m1 … m6, alternative paths 1–6
[one entry each; PLACEHOLDER]
```

---

## What is explicitly NOT in this plan

- **No re-analysis of the core pipeline** — no reviewer required it.
- **OPT-2 (estimating s from deed records)** and **DA alt-path 4 (whole-book observed-speed accounting)** are named as future work, not v20 scope — both are research projects, and the panel's asks are satisfiable without them.
- **R3's cross-disciplinary reading list** beyond Campbell (2006) — context, not obligations.
- Any change to the committed artifact record: superseded figures stay in the ledger; the ledger moves to the replication package.
