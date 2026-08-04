# Response to the v19 Review Panel — DRAFT (v20 revision in progress)

**Status:** working draft, 2026-08-04. Phase 2 (claim surgery) is landed and green
(ALL GATES PASS; 1093 tests). Items marked **[PENDING-RUN]** await the author-only
runs specced in `specs/DRAFT_V20_A/B/C`; items marked **[PHASE-3]** land with the
restructure. Panel reports: `panel_review_v19.md`; plan: `improvement_plan_v19.md`.

---

Dear Editors and Reviewers,

Thank you for the five-perspective review. We were encouraged that the panel
unanimously credited the ex-ante cap arithmetic, the disclosure apparatus, the
Danish repricing, and the Fannie Mae reproduction — and we accept the equally
unanimous diagnosis: the measurement discipline outran the presentation
discipline. The revision changes the claims layer and the document form, not the
analysis. A note on versions: the reviewed PDF predated the round-32 audit
remediation, which had independently landed several of the panel's asks (the
ex-ante-projection denominator in the abstract, the additive-form null share, the
seasoning-ramp span, the two-way corrections statement); this response reports
against the post-R32 manuscript.

## Summary of changes landed (Phase 2)

1. **Renaming pass.** The β1 = 0 construction is now the "rate-inelastic
   null/baseline" throughout both variants (28 context-anchored renames; the 14
   surviving "mechanical" instances are the genuinely mechanical uses —
   scheduled-amortization arithmetic, collinearity, adjudication language).
   "Never about behavior" → "never about the rate-responsive margin." Rhetorical
   uses of "trapped liquidity" → "cap shortfall"; the term survives only as the
   defined simulation object (definition sentence retained). "As homeowners
   relocated naturally" → "as principal was repaid."  *(R1-W1; R2-W3; R3-minor;
   DA-C2 naming component; EIC abstract comments.)*
2. **Abstract rewritten 427 → 229 words**, decomposition-first: cap shortfall
   with the 1.7–1.9× ex-ante multiple in the same sentence; rate-inelastic
   baseline with its behavior-containing floor named inside the sentence; both
   denominators (cap-relative 85.7%/35.6% by form; projection-relative $87.8B
   with lock-in ≈ half, 23–80% across floors and allocations); the range stated
   before the point per the round-24 posture (gate #99), with the wild-cluster
   status and form-conditional hull kept inside the interval sentence; the
   institutional-cost sentence now carries its two conditions ("small only under
   the production floor form and face-value accounting").  *(EIC-W1/W5; R1-W2;
   R2-W3; R3-W5; DA-C1/C3/C5.)*
3. **Convention-envelope row added to Table 1** (+0.9 to +15.6 across named
   convention variants; calibration box +2.1 to +13.2; labeled as ranges without
   coverage properties).  *(R1-W2; DA-C3.)*
4. **Pre-commitment credential calibrated** where it is claimed: "Pre-commitment
   here is a disclosure device rather than a proof," pointing at the Appendix O
   adjudication record, citing Olken (2015).  *(DA-M6; R1 results-integrity.)*
5. **Floor-depression alternative surfaced in the main text** beside the
   "unadjudicable below gap ≤ 0, not refuted" adjudication: if the floor's level
   is itself an equilibrium outcome of the episode, part of what the baseline
   absorbs belongs to the lock-in channel; named as future work with the reason
   it is not folded into the headline.  *(DA-C2; R1-W1 fix; DA alt-path 2.)*
6. **Monthly magnitude stated once**: the anchor marginal ≈ $1B/month against a
   $35B/month cap.  *(DA-m6.)*
7. **Episode-specificity scope extended**: the recurrence sentence now says the
   accounting machinery is episode-shaped (sign forced, refinancing margin
   inert) and a mixed-moneyness window would require re-deriving both.  *(DA-m1.)*
8. **Verified factual corrections** (independent web verification, 2026-08-04):
   - Batzer et al. (2024) recharacterized at all three citation sites: **$2.4T is
     below-market financing value retained by staying and forfeited on
     relocation** — not "foregone capital gains"; prevented-sales counts added
     (1.33M 2022Q2–2023Q4; 1.72M through 2024Q2 in their revision). *(R2-Q1.)*
   - "Joint-and-several" removed from the Danish series description — that
     liability belonged to the historical associations, not modern SDO/capital-
     centre series. *(R2-Q7.)*
   - Cap-history note added: the June 2024 and April 2025 runoff slowings cut
     only the Treasury cap and retained the $35B MBS cap (above-cap MBS
     reinvestment provision never triggered), so the constant post-phase-in $35B
     schedule is the policy-committed one. *(R2-Q4 / institutional #1.)*
   - Provenance clauses added: the $1,940.9B audit parse is the 2026-07-15 as-of
     of the book whose committed June-2022 as-of is $2,700.6B (difference =
     interval runoff); the 20.4% Ginnie share is from the paper's CUSIP-level
     cohort parse. *(R2-Q2.)*
9. **Gates and tests follow the manuscript**: 9 gate pins re-synced with
   documented V20 comments (ordering assert #99 retained and enforced — the
   abstract still states the range before the point); perturbation battery
   re-synced; ALL GATES PASS, 1093 tests green; both variants rebuild clean.

## Pending author-only runs (specs committed before any run)

- **DRAFT_V20_A `compounding_consistent_null`** — prices the renormalization
  upper-bound bias Table 11 discloses. Landing rules fixed ex ante, including
  the uncomfortable branch. *(R1-W4/Q3; EIC-Q7; DA-C2.)*  **[PENDING-RUN]**
- **DRAFT_V20_B `null_floor_interval`** — the floor read's sampling interval on
  the null's 85.7%, same draws as the marginal layer. *(R1-Q8.)* **[PENDING-RUN]**
- **DRAFT_V20_C `fewcluster_coverage`** — coverage simulation at the design's
  5.9 effective clusters / 0.33 leverage; pre-committed rule can replace the
  quoted binding interval with CR3+BM [+2.3, +9.6]. *(R1-W3/Q1; DA-C3.)*
  **[PENDING-RUN]**

## Phase-3 additions landed (2026-08-04, second commit)

- **Household-side treatment** (R3-W1): the existing constrained-move counts
  (per-year counts; 5.7–6.3% of the 4.08M annual sale run rate) now carry the
  welfare attribution sentence (magnitude attributed to Gerardi et al. 2024
  rather than measured), and the conclusion states the distributional tilt
  (below-740-FICO 1.23–1.26×, above-80-LTV 1.23×) with the assumability
  carve-out's bounded status (R3-W3).
- **Taxpayer-carry back-of-envelope** (R3-W2/Q1): ~250–300bp funding spread
  over the 2.49% WAC → order-of-$1B/year negative carry on the $42.6B of
  trapped roll-off, stated as a remittances-denominated restatement of the WAL
  extension with the face-versus-cash incidence caveat.
- **Policy take-away paragraph** (R3-W5/Q5): what transfers (floor band in CPR
  units, scheduled-amortization path, elasticity band), what must not travel
  alone (+5.6 anchor; $764.7B), which accounting basis answers which question.
- **Deliberate-non-bindingness + partial-equilibrium boundary in VI.B**
  (R3-W4/Q3/Q4; DA alt-path 3): non-bindingness as a possible choice; the
  FOMC's primarily-Treasuries composition objective as the standing that
  survives it; spread-feedback boundary stated where the recommendations are.
- **Factor-paydown note** (R2 institutional #2/Q3): the CUSIP factor-series
  construction named as the superior path and why it was not taken.
- **References added and cited**: Fuster et al. (2013) at the primary–secondary
  spread decomposition; Hancock & Passmore (2011) at the QE rate-transmission
  sentence; Amromin, Bhutta & Keys (2020) at the moving/refi-mix bracket (with
  the "loan-purpose" → "termination-reason" wording fix); Song & Zhu (2019,
  RFS 32(8), 2955–2996) at the TBA financing discussion.

## Deferred to the dedicated compression session **[PHASE-3b]**

Main text ≤ 50 pp. (global prose compression); ABM section + VII.C tightening
and the conclusion's "two central findings" framing conditioned (EIC-W2; R1-W5;
DA-C4); audit apparatus migrated to the replication package with gate #104
rescoped to the migrated file (EIC-W1; R2-W5); Tables 5/9 relocated adjacent to
§V.E; run tags out of prose; editions + split recut after pagination settles.
Optional additional reference: McPhail–Schnabl–Tuckman — **correct title: "Do
Banks Hedge Using Interest Rate Swaps?", NBER WP 31166**.

## Responses to the Devil's Advocate CRITICALs

- **DA-C1 (denominator-conditional headline): concede and fix — landed.** The
  abstract now carries both denominators with their bands; the cap-relative and
  projection-relative readings travel together everywhere the headline is
  stated.
- **DA-C2 (null embeds behavior / calibration echo): concede components,
  contest the label.** Landed: renaming; floor-depression alternative in main
  text; renormalization disclosure promoted via spec V20-A. Contested:
  "near-tautology" — Table 6 shows recovery moves materially with the floor
  level (+0.7 at the contaminated 6.91% read vs +9.2 at 4.00%), so the
  decomposition has content conditional on the floor; what is conceded is that
  the floor's own level is a convention boundary, now stated in the text.
- **DA-C3 (single-layer interval): concede and fix — landed** (envelope row +
  abstract conditioning; the sign claim's independence from the interval was
  already stated at the zero-exclusion sentence and remains).
- **DA-C4 (ABM verdict): concede — [PHASE-3]** for the compression; the
  contrast's disclaimers are already in place at HEAD ("not clean evidence
  about modeling paradigm alone").
- **DA-C5 (Danish "small"): partially contest.** The rule-only zero-refinance
  anchor stands as the semantics-consistent production choice (per the domain
  reviewer's assessment); conceded and landed: the abstract's cost sentence now
  carries its two conditions, and the band/incidence bracket remain in
  Table 13/§VI.D/conclusion.

## Answers to selected questions (drafted)

- **EIC-Q1 (the single sentence):** "Lock-in adds +2.9 to +8.7 points of the
  cap shortfall under the production floor form (+3.5 to +13.1 across forms),
  $42.6B at the anchor calibration; a policymaker should quote the range, not
  the anchor." This is now the abstract's own construction.
- **EIC-Q5 (+11 policy relevance):** drafted answer — no Section VIII policy
  conclusion reverses at +11.2: the cap-design lesson and the mobility-vs-cash
  ranking survive; the "small institutional cost" sentence is now explicitly
  form-conditional. To be confirmed by the author.
- **R1-Q5 (asymmetric labels for Aladangady vs Fonseca anchors):** to be
  addressed in Phase 3 (label symmetry in Table 5) or contested with a stated
  ranking criterion — author's call.
- **R2-Q8/R3-Q6 (Ginnie assumption counts):** attempted 2026-08-04 — Ginnie Mae
  publishes no assumption counts in GMAR or MBS disclosures; public volumes are
  press analyses of FHA/VA data (≈4,052 FHA assumptions 2023; ≈6,400 combined
  2023). The 20.4% therefore remains an upper bound; a sentence citing the FHA
  counts as scale context is drafted for Phase 3, source-flagged as press
  analysis of agency data.
- **R3-Q1 (carry cost):** accepted in principle — Phase 3 adds the
  back-of-envelope (trapped balance × funding spread × WAL extension) with the
  incidence caveats the cash-haircut bracket already establishes.

*(All remaining per-reviewer minor items are tracked in
`improvement_plan_v19.md`'s traceability table; none is dropped.)*
