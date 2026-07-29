# Handoff — round 27 — re-review Minor Revision; posture set AND survivor set landed; letter + PR + two runs remain

**STATE SUPERSEDED BY THE SECOND HALF (same day): the full survivor set is now EXECUTED** — ten further commits `c68ff9f..ce5fc6e`, per-item log in `PLAN_score_improvements_2026-07-28.md` (second execution log) and `TECHNICAL.md` §41. Current state: **ALL GATES PASS · 440 tests · 1407 lines · 126pp (main text ends ~p.82 WITH references; Online Appendix pp.83–126; new `app:patha-detail` p.100) · abstract 367 words · zero-slack counts exact (7/5/7/5/6/8/10/11/0) · letter UNTOUCHED by the second half (367-word claim still current).** New pinned machinery: gate #98 gained whole-file `ASSEMBLY_TABLE_SPANS` (tab:assembly); gate #99's `interval_qualifier`/`hull_in_abstract` spans re-anchored to the unstacked abstract. Two-PDF packaging: one compilation splits at the p.82/83 boundary (`qpdf --pages`; recompute pages after any reflow). **Open: send the letter (Eugene) · push/PR (Eugene) · B5 run with pre-committed landing rule (Eugene sign-off). #21 is DISPOSITIONED NOT_FEASIBLE (TECHNICAL §42: sampler pre-QT censoring + deleted staging + absent credentials; the netting fact and infeasibility disclosure landed run-free, `828b28e`).** The §0–§4 below describe the round's FIRST half and remain accurate as history.

**Read this first.** It supersedes `HANDOFF_round26.md` §§0–2; round-26 §3's constraints still bind **with the deltas in §3 below**, and `HANDOFF_round22.md` §3–4 still bind underneath everything. Companions: `TECHNICAL.md` §40 (this round), `REREVIEW_v18_panel_2026-07-28.md` (verification review, Minor Revision), `PLAN_score_improvements_2026-07-28.md` (35 verified proposals + 4 kills + execution log).

## 0. State

| | |
|---|---|
| Branch | `claude/paper-v18-review-plan-5b7b5e`, continues round 26; ~35 commits since `89ba2e4`, **UNPUSHED**. A PR from this branch is still the way in and carries everything since round 24b. |
| Manuscript | `paper/v18/revised_paper_v18.tex` — **1356 lines, 123pp: main text ends ~p.84, Online Appendix pp.85–123** (`app:floormech` p.105). Abstract **367 words, TWO paragraphs** (inline `\par` at the "accounts for 91.3%." seam; line 30 is still one source line). |
| Gates | `python3 tools/liveness_gates.py` → **ALL PASS** (104) |
| Tests | `python3 -m pytest tests/` → **436 pass** (the letter battery gained the 366 wrong-count case) |
| Build | tectonic (`/Users/eugene/Downloads/texbuild/tectonic`), 0 undefined refs; figures + `.env` present in this worktree. |
| Letter | `response_to_referees_round22.tex` — **current: 8 §7 items ("Four of the eight move against"), claims 367 words**, gate #101 green. **STILL UNSENT — Eugene's.** |

## 1. What round 27 did (details: TECHNICAL §40, plan-file execution log)

- **Re-review (verification mode): Minor Revision.** All Critical/Major roadmap items verified addressed except B1 (partial by choice), B2 (two variant-phrased stale lines — both now fixed), B5 (unrun, disclosed). Six new issues found; **all six repaired this round** (NEW-1..NEW-6a, commits `5e5dee6..95d9f6c`).
- **Score-improvement plan:** 35 adversarially-verified proposals across the six panel dimensions + 4 kills (do not resurrect the "outcome holdout" — it is circular; see the K1 kill).
- **Posture decisions (Eugene: 1 yes, 2 yes, 3 no, 4 yes), all executed:** abstract `\par` (366→367, letter + tests re-anchored); the paired design-crossing claimed as a validation design at L102-tail with indirect inference named as nearest relative (external lit check on record); Calibration Box split → `app:floormech` (three tables + mechanics prose moved verbatim, two deixis repairs); **submission-variant short abstract DECLINED**.

## 2. WHAT IS OPEN

1. **Send the letter** — Eugene only. It is current as of this round (8 items, 367-word claim). Anything that changes a §7 figure or the abstract count updates the letter in the same commit (gate #101 recomputes; the wrong-count list now carries 263/328/341/352/359/366/424).
2. **Push / PR** — Eugene only.
3. **The unexecuted survivor set** in `PLAN_score_improvements_2026-07-28.md` (~28 wording/structural proposals: §II differentiation enumeration, §I contributions paragraph, Fannie exhibit, Graybill point-of-use, coverage-bound caption, hierarchy-summary exception clauses, L43 paragraph split, abstract interval-sentence unstack, appendix wording pass, two-PDF packaging, reading guide, wave-2b move #1…). Observe the file's **dedup note** (Graybill ×2, SMD ×2 at the same insertion point). The L43 split renumbers everything below it — land line-anchored work first.
4. **B5 run** (overlay × age-standardized floor) under its committed spec, **with the landing rule pre-committed first** (the plan's top rigor item; Eugene sign-off required).

## 3. Constraint deltas vs. round-26 §3 (everything not listed is unchanged)

- **Zero-slack counts UNCHANGED:** `$+2.8$ to $+8.7$` 7 · `$+3.0$ to $+8.0$` 5 · `$+3.5$ to $+13.1$` 7 · `11.06` 5 · `positive at every` 6 (threshold-exact; one occurrence moved verbatim into `app:floormech` with its forced-marker) · `76.3\%` 8 · `60.2\%` 10 · `13.6\%` 11 · `$+3.9$ to $+13.1$` 0. **NEW-1 was executed literal-neutral** via the and-form: `$+2.8$ and $+8.7$` now appears ×2 (abstract, §II L96) and is NOT a counted literal — future sweeps must grep and-forms too; that blindness is what let the L96 defect survive round 26.
- **Abstract count is 367** (letter claims it; tests re-anchored). The `\par` is inline — do not convert it to a blank line (gate C4 line parity).
- **Manuscript is 1356 lines.** Variant rule unchanged: regenerate (canonical with line 30 swapped); C4 allows differences only on canonical `\noindent` lines.
- **New label `app:floormech`** (p.105) — landed after the nocite block, deliberately OUTSIDE the ledger's find-window (a new `\section{}` between L741's ledger and its `spec v3`/`121.5` content truncates gate `ledger-contains`). Keep it that way.
- **Letter §7 now has EIGHT items + Verification;** L335 says "Four of the eight". The Two/Three enumeration is reconciled — the letter now mirrors the manuscript's three-item list with `$+11.2$`/`$+11.5$` inside the §7 window (gate #101 current-literals).
- **Verdict table taxonomy:** the seasonal-timing row reads `Pass weakened: rule met as written; the timing claim withheld…`. "Enforced" rows are now exclusively rule-applied-as-written.
- **VII.F's kept lines cite `Appendix~\ref{app:floormech}` twice** (stability threshold; 2019-leg rejection) — those are reference re-wordings, not moves; do not "restore" them.

## 4. What this round got wrong or nearly wrong, and how it was caught

1. **My own re-review's L96 remedy assumed the ×7 count had to move; the and-form made it free.** The recon agent's threshold map (all counts are `>=`, none exact) plus the abstract's own and-form precedent turned a tex+gates+tests+letter commit into a tex-only one. Read the gate SOURCE before pricing an edit.
2. **The letter battery would have gone silently vacuous at 367** — both mutation tests `.replace()` a hard-coded "366" string. Caught by the recon map before the edit, not after. Same class as round 26's word-count lesson; the wrong-count list now carries every historical count including 366.
3. **The Calibration Box split's first draft (per the plan) moved the intro paragraph too** — leaving kept text with a dangling "The box" antecedent. Caught by reading the region line-by-line before surgery; the intro stayed.
4. **A pytest invocation that "ran the full suite" ran 32 tests** (arg dedup illusion — 0.27s for what should be 6s). Re-ran properly. Check the runtime, not just the green.
