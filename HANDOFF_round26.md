# Handoff — round 26 — roadmap executed; wave 2, the letter, and the merge are what remain

**Read this first.** It supersedes `HANDOFF_round25.md`, whose one open scope call (length/methods note) was
decided by Eugene on 2026-07-28: **B1 relocation authorized and executed, wave 1**. `HANDOFF_round22.md`
§3 hard constraints and §4 gotchas still bind. Companions: `TECHNICAL.md` §39 (this round), §§35–38
(round 24), `REVIEW_v18_panel_2026-07-28.md` (the panel), `PLAN_v18_fixes_2026-07-28.md` (item-by-item
disposition of all 12 roadmap items).

---

## 0. State

| | |
|---|---|
| Branch | `claude/paper-v18-review-plan-5b7b5e` (worktree), ~25 commits `89ba2e4..`, **UNPUSHED**. Cut from the round-24d state. `main` still lacks rounds 24b–24d AND all of round 26; `main` has a merge commit the branches lack (HANDOFF_round25 §0) — **a PR from this branch is the way in and carries everything**. |
| Manuscript | `paper/v18/revised_paper_v18.tex` — **122pp total: main text ends p.87, Online Appendix pp.88–122** (wave 2a done) (designated in-document). Abstract **366 words**, one paragraph per line, 1342 lines. |
| Gates | `python3 tools/liveness_gates.py` → **104 ALL PASS** (#103 now 8 spans: denomination resolution) (new: #102 elasticity exhibits, #103 buyback incidence, #104 verdict audit) |
| Tests | `python3 -m pytest tests/` → **435 pass** |
| Build | tectonic, 0 undefined refs. Worktree needs figure PNGs + `.env` symlinked from the main checkout. |
| Letter | `response_to_referees_round22.tex` — current (§7 lists FOUR against-the-paper developments), gate #101 green, **STILL UNSENT — Eugene's** |

## 1. What round 26 did (one line each; detail in TECHNICAL §39)

- **Five-reviewer panel** (Major Revision, 68/100), every Critical/Major adversarially re-verified before use.
- **81 wording-only edits** under a mechanical frozen-content validator.
- **`floor_inference_correction` → MOVES → full restatement:** the binding layer is now the wild-cluster
  **$[+2.8, +8.7]$**; percentile $[+3.0, +8.0]$ demoted ×5; **posture re-derived** ("a middle member of an
  interval whose measured corrections concentrate below it" — +5.57 sits just BELOW the corrected midpoint 5.76).
- **`band_low_extension` + `moving_share_bracket`:** the marginal as a curve in the elasticity
  (`tab:lowband`; +5.1/+3.5pp at half-central) and the moving-share bracket (+4.9pp at s=0.5) — gate #102.
- **`buyback_credit_bracket` → REVERSES:** Danish gap is **incidence-conditional** (+$61.2B face /
  −$89.4..−$117.7B cash); the signed "modestly improved (3)" is GONE; dissolution scoped to face
  accounting; the off-window +$28.2B carries the same scope — gate #103.
- **Abstract now carries:** the corrected interval + demoted percentile, the form hull, and the
  null-floor-behavioral clause (ABSTRACT_POSTURE = 7 canonical-scoped spans).
- **Online Appendix** (wave 1, moves-only): extension mechanics, WAL, fold-in/units, seasonal floor moved
  verbatim; 23 callers re-pointed `Section~`→`Appendix~`; VII.I stayed (forensics share lines with
  binding-layer machinery).
- **`app:verdicts`** (gate #104): 16-row census of every non-mechanical adjudication, both directions pinned.
- **Four web-verified references:** du2024, agarwal2013, chernov2018, graybill2026 (bib 66→70).

## 2. WHAT IS OPEN

1. **B1 wave 2b (optional, submission-time):** wave 2a moved III.B+III.C (spec) and the notation
   glossary — main text is 87pp. **The Danish gap is no longer sign-open:** the incidence bracket is
   resolved by denomination (face = benchmark-consistent, +$61.2B stands; cash reversal = the foregone
   par-windfall transfer), gate #103 pins both halves. The remaining ~25pp to the EIC's 55–60 is
   results-and-qualifications prose: getting it out requires paragraph splits with deixis repairs
   (VII.I class) or condensing results — the rewrite class the concision round proved dangerous.
   Budget a full session with fresh eyes; consider a separate Online Appendix PDF in the same pass.
2. **Send the letter** — Eugene only. It is current as of this round; anything further that changes a §7
   figure must update it in the same commit (gate #101 recomputes).
3. **Push / PR** — Eugene only. Everything since round 24b is only on branches.
4. **Panel re-review** (recommended next session): the panel prescribed re-review; the ARS skill has a
   re-review mode that takes the roadmap + revised manuscript + letter and produces a traceability matrix.
   All 12 items are dispositioned, so this is a verification pass, not new work.

## 3. Constraints — new or changed this round (round-22 §3 still binds)

- **Zero-slack recount:** `$+2.8$ to $+8.7$` **7** · `$+3.0$ to $+8.0$` **5** (demoted mentions — do not
  delete, do not grow) · `$+3.5$ to $+13.1$` **7** · `11.06` **5** (the verdict table added one) ·
  `positive at every` 6 · `76.3\%` 8 · `60.2\%` 10 · `13.6\%` 11 · `$+3.9$ to $+13.1$` **0 (must stay 0)**.
- **Abstract word count 366** is what the letter claims; gate #101 recomputes it. Any abstract edit updates
  the letter in the same commit.
- **Gate #99 ordering literal is now `$+2.8$ and $+8.7$`.** Gate #98's posture span is
  `posture_middle_member`; the binding-layer span reads "…$+2.8$ to $+8.7$ points after wild-cluster
  correction". Restating the interval again means tex+gates+tests+letter in ONE commit, same as this round.
- **Gates #102/#103/#104 batteries mutate ALL occurrences** (presence-gate power). Known limit, recorded in
  the tests: a span that appears twice (the run tags) is not protected per-site.
- **`fs._ORIG_PREPAY` is the variant-hazard seam.** Patching `competing_risks.prepay_hazard` around
  `floor_sweep._run_scored` is silently bypassed by the bind-tally wrapper. Install variants at
  `fs._ORIG_PREPAY`, restore BOTH names after (TECHNICAL §39.3).
- **The buyback identities are accounting, not model:** they rest on trapped liquidity being a NET monthly
  sum (targets cancel from differences). If the benchmark construction ever changes to a capped monthly
  form, `buyback_credit_bracket` must be re-derived, not re-run.
- The long-abstract variant regeneration rule is unchanged (canonical with line 30 swapped; identical line
  count; difference on line 30 only).

## 4. What this round got wrong, and how it was caught

1. **A battery caught its own gate's hole on first run** (gate #102: run tag occurs twice, single-site
   deletion invisible). Fourth consecutive round in which a test written against intent caught what the
   implementation missed. The limit is now documented in the test rather than papered over.
2. **The letter's word-count battery went vacuous twice in one day** (328→352→359→366): the mutation
   literal must be re-anchored every time the count changes, and the wrong-count parametrization now
   carries every count that was ever true.
3. **The wording-pass validator's pin extraction flagged two spurious single-token "pins"**
   (`estimators`, `comparison`) — identifier strings, not prose spans. The fix (no-decrease for
   single-token pins, exact-count for prose spans) is in the scratchpad applier, not the repo.
4. **An 80-char preview truncated a line and sent an exact-match edit hunting for text that wasn't there**
   (`This section collects…` intro line). Prefix-match against the file, not against a preview.
