# HANDOFF — R32 continuation #3. Read this file first, in full, before touching anything.

Supersedes `HANDOFF_R32_continuation_2.md`. Everything in that file's §5.1–§5.4 is now done.
§0 (the goal), §1 (house rules), §6 (reserved for Eugene), §7 (verified facts) and §9
(anti-conditions) of that file **still bind** and are not restated here except where this
session added to them.

---

## 0. READ THIS FIRST — the branch moved

The R32 work was on `claude/brave-shaw-b02840` in worktree `agency-mbs-runoff-qt-424945`.
**This session ran in a different worktree** (`frosty-maxwell-de1f9a`, branch
`claude/round-32-continuation-248428`) because it was launched there and a sibling worktree
(`jolly-dhawan-1c5829`) sat on an identically-shaped branch at the identical starting commit —
the R30 parallel-session collision, about to repeat. Two sessions editing one worktree is
unrecoverable; two branches is untidy. So:

- `claude/round-32-continuation-248428` was **fast-forwarded** onto `508349a` (lossless: the old
  head was a strict ancestor) and all this session's work sits on top of it.
- **`claude/brave-shaw-b02840` is a strict ancestor of this branch.** Pushing this branch
  pushes everything; there is nothing to merge and nothing stranded.
- Eugene should push **`claude/round-32-continuation-248428`**, not the old branch.

## 1. STATE

Worktree: `.../.claude/worktrees/frosty-maxwell-de1f9a`, branch
`claude/round-32-continuation-248428`, tree clean.

**ALL GATES PASS (111) | 532 tests | ALL RENDER CHECKS PASS | 152pp canonical (main 1–106,
online appendix 107–152) | 152pp variant | 0 undefined refs | 0 errors | 0 overfull vbox |
0 off-page items | variant differs at line 31 only.**

Verify before your first edit (and note the two footguns after it):
```bash
python3 tools/liveness_gates.py | tail -1
python3 -m pytest tests/ -q | tail -1
python3 tools/render_gate.py | tail -1
```

**Footgun A — `tectonic` does not create its own `--outdir`.** In a fresh worktree
`mkdir -p paper/v18/build_split` first, or every build "fails" with
`error: output directory "build_split" does not exist` and the `grep -c` loop prints 1.

**Footgun B — the test count is build-dependent.** `tests/` collects **530** until the split
PDFs exist and **532** afterwards: `test_render_gate.py` parametrizes over
`revised_paper_v18_main.pdf` / `_online_appendix.pdf`. A "missing" 2 tests means you have not
run the split yet, not that tests vanished.

## 2. LEDGER

`specs/LEDGER_R32_coverage.md` — **103 SATISFIED / 18 OPEN / 7 DEFERRED-EUGENE / 3 DECLINED /
1 CLOSED-REFUTED / 1 MOOT = 133, zero unclassified.**

## 3. TWO DEFECTS IN HANDOFF #2 — fixed here, do not re-inherit

1. **`C-115` was missing from its §5 ordering.** §5.1–§5.6 enumerated 34 conditions and called
   them 35. `C-115` appeared in no group. It was genuinely OPEN; it is now SATISFIED (`8036fd3`)
   and the ledger records the discrepancy.
2. **The `§8.4` cross-reference in its §5.5 (C-76) is dangling.** Neither handoff has an §8.4 —
   handoff #1's §8 has six items, handoff #2's has seven. The substantive warning survives in
   #2's own §5.5 prose ("that FRED series has no usable history on this account") and is
   restated in §5 below.

## 4. WHAT THIS SESSION DID

| condition | commit | note |
|---|---|---|
| C-93, C-95, C-96, C-97, C-83 | `8255e0d` | Wave-4 presentation + T1 duration row |
| C-94 (**RUN**) | `ee7c5fb` | note-rate-basis WAL row, GATE #110, 16 tests |
| C-66, C-99, C-106, C-109 | `fbf7b33` | wording; C-121 partial |
| C-85, C-86, C-51 | `38db980` | 10 source-verified references |
| C-48, C-49, C-54, C-115 | `8036fd3` | Danish group + cap in $bn/month, GATE #111, 11 tests |
| TECHNICAL 47 correction | `23c35a6` | see §6 |

**The one run.** `wal_note_rate_basis`, Branch A, spec (`dd769f8`) → runner (`057b336`) → run.
Both pre-commitments **held**: E1 wanted June-2022 ∈ [8.8, 9.2] and Nov-2025 ∈ [7.9, 8.3] and
got **8.9 / 8.1**; E2 wanted the basis effect in [0.2, 0.6] and pre-committed it as "the same
order as" the 0.6-year Danish rule-only effect, and it landed at **0.5 years**. E3 (strict
monotonicity in CPR) held.

## 5. WHAT IS LEFT — 18 conditions

### 5.1 The ten wave-3 RUN conditions — START HERE, none started
`C-72` month-clustered + two-way (stratum × month) rungs · `C-74` Ginnie leg with the
elasticity attenuated by the measured CRR differential · `C-75` re-derive the Danish buyback
discount D from the leg's own prepay path · `C-76` marginal in transaction counts · `C-77`
re-solve the Aladangady reconciliation under the additive form · `C-78` episode gradient within
narrow age bands · `C-79` Danish leg with an interest-only share · `C-80` read the 2018 depth
ladder's shape · `C-81` state-contingent cap two-input table (**re-tabulation, no new
estimation**) · `C-92` sweep or flag the floor's flatness in loan age (**spec it so it cannot
repeat the `floor_cyclical` mislabel**).

**Templates, in order of closeness.** `tools/wal_note_rate_basis_run.py` +
`specs/SPEC_R32_c94_wal_note_rate_basis.md` (this session) is the closest working example of the
guarded shape: sha-pin every input, AST-check the imported module's body binds names only,
re-hash artifacts after import and at exit, re-derive the committed rows bit-identically as a
parity gate, precision-insensitivity gate, write guard. `hazard/episode_gradient_recompute.py` +
`specs/SPEC_R32_c73_gradient_recompute.md` is the other.

**Two of these are cheapest and were probed this session:**
- **`C-81`.** Every input is present and committed. `composition_shift_results.json` carries
  `soma_book.asof_june_2022` (`total_mbs_face_b = 2700.5637`, `coupon_shares` in 11 buckets,
  `wac_face_weighted_pct = 2.4710`) and `soma_book.latest` (`1940.8033`, WAC `2.4954`). The
  OTM cuts at 200/300/400 bp are constructible from `coupon_shares` against the window rate
  path; the floor band and its wild-cluster interval (4.177–5.800%) are already printed in the
  same §VI.B paragraph C-54 just rewrote, so this **lands beside C-54's $bn/month units**.
- **`C-76`.** The internal arithmetic reproduces: `loan_sample.parquet` mean `balance` =
  **126,812.61** (verified this session, matches the inventory). Its **comparator** is the
  problem, not its count. There is **no existing-home-sales series anywhere in the repo**, so
  the comparator needs an external fetch, and handoff #2 warns that FRED series "has no usable
  history on this account". Decide the comparator question *in the spec*, before the run, and
  if it is not sourceable, land the count with the comparator recorded infeasible rather than
  quietly dropping the check. **`C-82` (T1's household row) is blocked on this** and the
  inventory forbids an unquantified placeholder.

### 5.2 Leftover wording (3)
`C-121` **OPEN (PARTIAL)** — the worst site is de-nested (10 parentheses → 1 in the lead
clause); ~30 sites remain, all dense legal/citation prose where each parenthetical is
load-bearing · `C-117` **not started** — 35 sites, several inside gate-quoted spans; handoff
#2's own instruction is "do it last or not at all" · `C-122` fold §VI.C into §VI.B (wave 6).

### 5.3 Wave-6 length (4) — Eugene's call, do not start
`C-88`–`C-91`. **The pressure is now worse, not better: this round took the paper 148 → 152pp**
(+1 Wave-4, +2 citations, +1 Danish/cap units). Entangled with `C-130`.

## 6. ADDED TO §7's VERIFIED FACTS

- **The SOMA book has two committed sizes and they are two AS-OF DATES of one object.**
  `$2,700.5637bn` is June-2022; `$1,940.8033bn` is the 2026-07-15 parse. I asserted in TECHNICAL
  47 that the $2.70trn figure "is not a committed quantity", **which was wrong**, and corrected
  it in `23c35a6`. Before quoting either, say which date.
- **`coupon_convention_amortization_results.json` owns the empirical-CPR bases.**
  `hazard_legs.committed_0250.mean_cpr_pct = 5.518089009047279` (the printed 5.52%),
  `delta_080.mean_cpr_pct = 5.785664704297843` (the printed 5.79%, the 0.80pp wedge leg that
  run's own spec names primary). The ABM-basis 5.14% is the default convention and is now fixed
  once in "Definitions used throughout".
- **`expectation_benchmark_results.json` carries the settlement-aware total directly** as
  `settlement_aware_allocation.projected_runoff_window_b = 839.5299`. The inventory said it was
  only *derivable* (652.752 + 186.778); it is not — read it, do not reconstruct it.
- **`b5_joint_cell_results.json` `conventional_agestd`** — `marginal_pp = 3.67131541392159`
  against `ladder_implied_pp = 3.8`. The measured value now leads at five narrative sites; the
  **grid table `tab:oosfloor` deliberately still prints $+3.8$**, because every sibling row in
  it is a grid read.
- **A same-literal collision that is now labelled, not silent:** `$+3.7$` denotes *both* the
  vintage overlay (3.702154) and the age-standardized floor (3.671315) in `tab:assembly`. The
  row says the printed tie is a rounding accident. Do not "fix" it into one number.

## 7. ADDED TO §9's ANTI-CONDITIONS

- **`tab:oosfloor`'s age-standardized `$+3.8$` is not a stale grid read left behind.** It is the
  grid column, kept deliberately. The measured `$+3.7$` lives in the narrative and in
  `tab:assembly`.
- **`tab:pathadiag` is single-spec on purpose.** Both spec-v3 rows and row 4's `(2.5 under spec
  v3)` parenthetical were demoted to its note. Do not restore them to the body.
- **The C-54 band is `$0.53`–`$1.58`bn/month and is NOT R3's `±$3.6`bn/month.** R3's number is
  arithmetically reproducible but bypasses the committed floor-to-marginal grid. The reason is
  the construction, not the denominator (see §6).
- **`\paragraph{Distributional incidence.}` is sequenced with `C-90`**, which is Eugene's and
  would relocate the containing subsection. It is not free-floating.

## 8. WHAT TO PRODUCE AT THE END

Unchanged from handoff #2 §10. **Do not push.**
