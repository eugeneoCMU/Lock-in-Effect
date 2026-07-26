# Handoff — round 22 + standing review — 2026-07-26

**Read this first in a fresh session.** It supersedes `HANDOFF_round21_referee.md` and
`HANDOFF_concision_round.md` (both marked superseded; the concision one's *hard constraints*
still bind). Companion documents: `PLAN_remaining_work.md` (the open-items ledger),
`revision_roadmap_round22.md` (what round 22 was), `TECHNICAL.md` §§29–30 (the new runs).

---

## 1. Where everything is

| | |
|---|---|
| Repo | `/Users/eugene/somthing/Lock In effect/Lock-in-Effect` (**public** on GitHub, `eugeneoCMU/Lock-in-Effect`) |
| Branch | `panel-revision-2026-07-18`, **pushed** through round 22. `main` untouched at `e1592f3`. |
| Manuscript | `paper/v18/revised_paper_v18.tex` — **113pp**, ~52k words, one paragraph per line (lines are LONG) |
| Archived variant | `paper/v18/revised_paper_v18_long_abstract.tex` — identical body, the old 574-word abstract |
| Build | `~/Downloads/texbuild/tectonic -X compile revised_paper_v18.tex --outdir build_r22 --keep-logs` (no `tectonic`/`pdflatex` on PATH) |
| Gates | `python3 tools/liveness_gates.py` → **93 ALL PASS** |
| Tests | `python3 -m pytest tests/` → **297 pass** |
| Response letter | `paper/v18/response_to_referees_round22.tex` (5pp, drafted, **not sent**) |

---

## 2. What the paper argues

Agency MBS runoff fell **\$764.7B** short of the QT redemption caps (June 2022 – Nov 2025).
**Most of that shortfall is mechanical, not behavioural.**

| Quantity | Value |
|---|---|
| Cap-relative benchmark | \$764.7B |
| Expectations-based complement | \$87.8B |
| **Mechanical null (β₁ = 0)** | **85.7%** of benchmark |
| **Lock-in marginal (headline)** | **+5.6pp = +\$42.6B** |
| — sampling interval (binding) | +3.0 to +8.0pp, open below +4.3 |
| — form-conditional hull (wider) | +3.9 to +13.1pp |
| Path B level | 91.3% headline / 97.9% in-sample |
| ABM | 13.6% seed mean |
| Cross-design ABM | 60.2% fifty-seed mean (76.3% at book composition) |
| Danish rule-only | +\$28.2B off-window / +\$61.2B in-sample |

The load-bearing result is **the null at 85.7%**, not the marginal. Three estimators with
unequal standing: **Path B** carries the result; the **ABM** is a falsification device;
**Path A** is excluded from every headline range.

---

## 3. HARD CONSTRAINTS — read before editing anything

- **Fix the `.tex`, not the gate.** Exception: a justified revision that changes pinned
  content moves tex + gates + tests in **ONE** commit.
- **Spec before run.** A specification commit must precede every result commit, with parity
  gates replaying committed values bit-exactly. This is the paper's central methodological
  claim; violating it is worse than not doing the run. Round-22 C1 exists because a
  precondition was articulated *after* a result was seen.
- **Run gates after EVERY section, never batched** — failures print only the dict key.
- **Hedges are load-bearing and stay.** Eugene's prose style: plain, direct, simple words,
  no flourish — but *never* weaken a qualifier. The concision handoff records that ~40% of
  that round's rewrites strengthened a claim past its evidence **while passing all gates**.
- **Zero-slack gate counts** (check before deleting any literal):
  `positive at every` ≥7 (exactly 7) · `$+3.0$ to $+8.0$` ≥2 · `11.06` ≥3 · `76.3\%` ≥4 ·
  `$+3.9$ to $+13.1$` ≥3 · `60.2\%` ≥3
- **`HARDCODED_XREF` bans** literal `Table~N`, `Figure~N`, `Section~V.C`, `Appendix~A`,
  `Equation~(N)`. Always `\ref`/`\eqref`. (For an *external* paper's table, write `tab.~3`.)
- **PAGE COMPRESSION IS ABANDONED** (Eugene, 2026-07-26). Do not reopen. No journal
  submission planned; the target venue is a conference, so length is not the constraint.
- **Never push Fannie data** — license prohibits redistribution and the repo is public.
  Scan before any push: no `.env`, no secrets, no `fannie` paths.
- **Snapshot before destructive passes.** The 101pp pre-edit v18 source was permanently lost
  once. Current snapshot: `paper/v18/snapshots/revised_paper_v18_pre-round22.tex`.

---

## 4. Gotchas that actually bit me this session

Each of these cost real time or produced a wrong answer. They are not hypothetical.

1. **Check which Danish leg a script ran.** `common/berger_calibration.py:_DANISH_MOVING_ANCHOR`
   defaults to `dk_level` (the **bracketing** leg). Only 2 of 18 scripts touching a Danish leg
   call `set_danish_moving_anchor`. Two committed artifacts were built on the wrong leg —
   `danish_discount_bound` (round-22 A2) and `curtailment_danish_scaling` (item 7b). **Always
   grep the caller list before trusting a Danish number.**
2. **A green suite proves nothing about an unpinned claim.** The gates pin numeric literals
   and phrases. They are structurally blind to captions, omitted summary statistics, claims
   about *magnitudes*, and anything stated in prose. Four round-22 defects lived behind 80
   passing gates.
3. **Mutation-test every gate you add**, and **revert the mutation in the file you applied it
   to**, then re-verify. A mutation left in the short-abstract variant rode into the canonical
   abstract and inserted an unintended strengthening ("substantial" for "real") that stayed
   green because the BENIGN fixture matched the *other* sentence.
4. **Beware numeric collisions when sweeping literals.** A `59.3%` in the floor section is the
   **additive central share**, not the cross-design variant. A `33.7%` is both the ABM
   waterfall stage and the out-of-window vintage share.
5. **Verify your own filters.** A vintage filter on year strings returned 46.5% where the field
   holds *group* labels (`2017-19`) and the right answer was 51.0%. The artifact was right; my
   check was wrong. This happened three times in one session — **when a check disagrees with an
   artifact, suspect the check first.**
6. **Scope a claim before attempting the run that would strengthen it.** Item 16 was scoped
   honestly first, so when B4 halted on data drift the manuscript was still correct, and when
   it later landed the sentence could be upgraded rather than rescued.
7. **`sleep` is blocked in the foreground.** Use `run_in_background: true` for long runs.
8. **SSRN 403s `WebFetch`**, but author sites often host the PDF; `pypdf` on the fetched file
   works. I wrongly told Eugene a citation check was his to do — it was not.

---

## 5. What round 22 did (all landed, all pushed)

Full detail in `revision_roadmap_round22.md` and `TECHNICAL.md` §§29–30.

- **14 accuracy defects (Tier A).** Four were invisible to every gate: a caption asserting the
  opposite of the body text; a sensitivity table run on the wrong leg; a bootstrap reporting
  every favourable summary and omitting the mean (78.3%, below the paper's own null); an
  ablation whose figures came from the *minimum* of an unrelated permutation experiment.
- **Claims retracted:** loan-draw uncertainty ("essentially no uncertainty" — understated 37×);
  form/transform additivity (interaction −1.47pp); Path A corroboration; curtailment
  immateriality (sign flips to −\$1.68B on the production leg); a post-hoc admissibility
  exclusion in VII.D.
- **Seven runs**, each spec-committed first: `concave_additive_marginal`, `burnout_ablation`,
  `cross_design_seeds`, `production_scale_test` (halted, then a **second** pre-commitment),
  `bootstrap_pathb_cluster`, `fannie_floor_read`, `curtailment_danish_scaling --anchor`.
- **Gates 80 → 93**, tests 295 → 297, pages 106 → 113.

---

## 6. OPEN ITEMS

`PLAN_remaining_work.md` §7 (7a–7f) is **closed**. What follows is the un-worked remainder of
the post-round-22 standing review, plus older leftovers. Ordered by how a hostile discussant
would raise them.

### 6.1 Substantive — likely to change what the paper says

| # | Item |
|---|---|
| **A** | **No ABM counterpart to the β₁ = 0 null.** The paper insists throughout that levels do not identify and only the central-minus-null differential does — then conducts the entire ABM comparison on levels. Every null in the source is Path B or Path A. A behavioural-gate-off ABM null would make the ABM contrast an apples-to-apples differential. Needs a run. |
| **B** | **"Structurally independent" overstates, and it is in the Section V title.** Path B's floor is "anchored to the same empirical observation as the ABM's mobility calibration" (L312) — 2023–24 deep-discount turnover, inside the evaluation window. The two estimators share their dominant level-setter. Prose, but it touches a section title and four other sites. |
| **C** | **68.8% censoring at the headline calibration.** At the off-window floor the hazard is censored at the constant floor in more than two-thirds of evaluated loan-months (36.3% in-sample). Disclosed only as an aside inside the burnout qualification. The implication — that the elasticity is inert in most of the sample *at the calibration the paper headlines* — is never drawn. |
| **D** | **Expectations-basis circularity.** The "quarter to half of the genuine surprise" rests on \$87.8B being a lock-in-free residual. Nothing asks what prepayment model underlies the NY Fed's May 2022 baseline; if it already priced lock-in, the attribution double-counts. L173 invokes this exact circularity to justify keeping the cap as headline, then the projection-basis ratio goes in the abstract without it. |
| **E** | **Two same-signed corrections never composed.** The age-standardised floor (→ ~+3.8) and the Ginnie overlay (0.797× → +4.4) both point down and are only ever reported in isolation. Composing them gives roughly **+3.0**, which roughly halves the headline. |
| **F** | **Small-G inference.** 31 clusters on the floor read, 25.8 effective on the loan/stratum bootstrap. Percentile cluster bootstraps under-cover badly at that G. No wild-cluster bootstrap, no t(G−1) critical values, no acknowledgement. |
| **G** | **Estimand transport untested.** β₁ is a quarterly ZIP-code *mobility* semi-elasticity applied multiplicatively to a *total prepayment* hazard whose floor the paper concedes "includes discretionary life-cycle moves and cash-out refinancings". |
| **H** | **Three independent readings suggest the imported elasticity is several-fold too small** for this book (Path A's own coefficient, the episode gap gradient at 4.5× the implied, and the cross-design result). The paper declines each individually and never confronts them together. |
| **I** | **The hull's upper end is disqualified and retained.** +13.1pp comes from a cell recovering 61.2% of the benchmark, which the paper says "should not be read as an equally credentialed member" — then publishes the range anyway. |

### 6.2 Presentational

- **"Cash-flow" is the wrong noun**, used four times (L30, L606, L901, L905). The computed
  quantity is balance retirement, not cash flow.
- **The ABM's headline sits outside its own stated uncertainty**: `tab:headline` gives 13.6%
  with operative range "20.9–59.3%", which does not contain the point.
- **`tab:oosfloor`'s "defensible range" is a depth-cut convention**, not an uncertainty: all
  three rows are the same 2018 leg at different gap thresholds.
- **Two uncited load-bearing claims** at L173 (market participants' early understanding; the
  cap-as-authorised-maximum characterisation, which mischaracterises a reinvestment *ceiling*).

### 6.3 Older leftovers (round-21 R10, never started)

- settlement-months benchmark variant · DTI non-monotonicity decomposition
- concave × additive **band ends** unrun, so the hull is "not contradicted" rather than "complete"

### 6.4 Eugene-only

- **Send the response letter** (drafted, 5pp).
- **Confirm nothing else needs pushing** — everything through this session is on
  `origin/panel-revision-2026-07-18`.
- ~~FRED key rotation~~ **CLOSED 2026-07-10** (TECHNICAL.md:1562-6). Verified: `.env` never
  committed, gitignored.
- ~~Berger locators~~ **VERIFIED 2026-07-26** against the January 27 2026 draft. `§4.9.1` and
  `tab. 3` correct; `~1 bps` verbatim; 3.2%/yr confirmed a Danish *descriptive* calibration
  target. `§3.3.1` was **wrong** (it is the buyback subsection) and is fixed → `§4.6` / `§3.2.3`.

---

## 7. Last actions in this session

Two regressions of my own, found by the standing review and fixed:

1. The abstract had dropped **both** the 60.2% fifty-seed mean and the 76.3% book-composition
   value for the cross-design variant, reporting only the single-seed 59.3% — undoing what
   round 21 and this round's seed sweep established. Restored.
2. **"corroborates"** survived for Path A at L51 and L899 while L441 and L582 said the sign does
   *not* corroborate. Both retracted.

Neither was caught by the gates: the required literals existed elsewhere in the file.
