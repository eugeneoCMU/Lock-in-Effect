# Handoff — v18 concision + draft-history round (2026-07-20)

Repo: `/Users/eugene/somthing/Lock In effect/Lock-in-Effect`
Branch: `panel-revision-2026-07-18` — **2 local commits, UNPUSHED**
Manuscript: `paper/v18/revised_paper_v18.tex`

## Current verified state

| | |
|---|---|
| Words | 45,477 (from 46,691) |
| Pages | 99 (from 101) |
| Liveness gates | 72/72 PASS |
| Tests | 267 passed |
| Undefined refs/cites | 0 |
| Abstract | 467 words (unchanged) |
| `earlier draft` mentions | 6 (from 20) |

Build: `~/Downloads/texbuild/tectonic -X compile revised_paper_v18.tex --outdir <dir> --keep-logs`
(no `tectonic`/`pdflatex` on PATH). Gates: `python3 tools/liveness_gates.py`.

## Hard constraints — read before editing the .tex

- **`paper/` was gitignored until today.** `paper/**/*.tex` and `*.bib` are now tracked
  (commit `0917530`). Derived files stay ignored. The pre-edit 101pp source was
  **permanently lost** earlier today (backup lived in session scratch, which was wiped;
  the 35 `.bak-*` files are all v16). Snapshot before destructive passes.
- **The repo is PUBLIC.** Pushing this branch publishes the working manuscript. The old
  `.gitignore` comment read "kept local-only, not published with the repo". Eugene has
  **not** authorized a push.
- **Gates pin prose, and some MANDATE redundancy:**
  - `tex.count("positive at every") >= 7` — currently exactly 7. **Zero slack.**
    Each site needs a forcedness marker within ±450 chars.
  - `"frozen manifests say otherwise"` — EXACTLY_ONE.
  - `count("11.06") >= 3` — currently 4.
  - `LEDGER_REQUIRED = ["spec v3", "121.5"]` must sit inside
    `\section{Superseded Figures and Run Ledger}`, which must never be the last `\section`.
  - `SUPERSEDED_CONTEXTUAL = {"894.8": "spec v3"}` — label within ±120 chars.
  - HARDCODED_XREF: never write `Table 7` / `Section V.C` / `Appendix A` / `Equation (2)`.
  - ZERO_COUNT bans literal phrases incl. `does not replicate`, `three independent legs`,
    `equal in size to the lock-in marginal`, bare `10.26`.
- **Gate failures print only the dict key**, not the sentence. Run gates after EVERY
  section, never batched, or the failure is unlocalizable.
- **Standing rule: when a gate fails, fix the .tex, not the gate.** The artifact is the
  authority (stated at `liveness_gates.py:1352, :1871, :2352`).
- **Hedge scope is load-bearing** (house style). Do not weaken. ~40% of proposed
  compression rewrites this round strengthened a claim past its evidence *while passing
  all 72 gates*. Gate-green is necessary, not sufficient.
- **The Superseded Figures / Run Ledger appendix is off-limits** for draft-history removal:
  it holds 1 of 32 such mentions, is gate-required, and carries three retractions.

## Open decisions — Eugene only

1. **Line 787 depth-limitation rewrite, two mutually exclusive variants.**
   A (saves 4w) keeps `That is false:` as an explicit concession.
   B (saves 10w) folds it into "The superseded claim … is false."
   Recommendation: **A**. KEEP is also defensible.
   Full text: task output `wja0xmc2n`, section 5 item 14.
2. **Push or not.** 2 local commits; pushing publishes the manuscript to a public repo.
3. **Abstract.** Condensation yields only 467→456 (11 words, 2.4%). To go materially
   shorter, a whole disclosed result must be deleted — recommended candidate is the
   ABM/cross-design sentence (32w). The prepared rewrite also changes voice
   (`This paper measures`→`I measure`), adds a new claim ("Almost all of that level is
   mechanical", 85.7/91.3 = 93.9%), and strengthens `follow from`→`forces`.
   Not applied. Full text: task output `wdrsu3nl2`.
4. **Repo deletion / reorganization** — see below.
5. **Venue** (still open from earlier rounds) — determines abstract length target.
6. **FRED key rotation** — still outstanding on Eugene from a prior round.

## Outstanding work

### Small, ready to execute
- **L789** now reads "This corrects the previous draft's reading" — inconsistent after
  edits 13 and 17 landed. Clean up.
- **`\textbf{Next steps:}` at L914** is an orphaned label; its bridge sentence was deleted.
- **Add literal gates for 7 ungated abstract hedges**: `genuine surprise`, `large majority`,
  `averaged across seeds`, `recalibrated`, `institutional cash-flow`,
  `baseline involuntary turnover`, `central allocation`. Verified ungated. The suite would
  have passed 3 of 4 candidate abstracts that misattributed a Federal Reserve projection.
  **This is the highest-value item on the list.**

### Concision, remaining
- **Tier 1 leftovers** (~300–680w, verified but unapplied): intro-lit C1 recovery cascade
  and C2 two-qualifiers, method L125 scale paragraph, Path A L374 bootstrap compression,
  abm L189 caption item-list, ident L583 seed-noise sentence, robust-a L662.
  Source: task output `wm8ttjy22`.
- **Tier 2** (~1,570w ≈ 3.4pp) — never started. Treat as a **claim-calibration review**,
  not copyediting. Two items are pre-confirmed gate failures and excluded:
  robust-a L720 errata compression, robust-a L730 curtailment merge.
- **Tier 3** (structural) — poor value. Demoting `fig:mc` to the appendix moves 0.7pp of
  area and removes **zero** pages. `tab:crosswalk` is read by ~39 run-tag counters.

### Repo organization
- Structure is already conventional (16 top-level entries). Real sprawl: `hazard/` at 183
  files, plus 3 round-specific `.md` files at root.
- ~35 `.bak-*` files under `paper/v16/` (~8MB) are now redundant given git tracking.
- **Do not delete the public repo without reading the brief.** The manuscript cites four
  commit hashes as pre-commitment evidence — `ad52db6`/`651d1a0` (specs) precede
  `d0ef130`/`57181b3` (results), verified by timestamps 7–9 minutes apart. `TECHNICAL.md`
  cites 75 more. Deleting makes those unresolvable and the pre-commitment claim
  unverifiable. Deletion also does not erase (forks, clones, Software Heritage, Wayback).

## Audit reliability note

Three separate audit lists this round were loose with facts. Verify before applying:
- claimed a number was "stated elsewhere" when it was not (the L936 case, caught);
- claimed baseline "73 PASS" when it is 72;
- self-reported correcting proposer word counts in 9 of 22 cases.
Always re-grep the canonical site yourself.
