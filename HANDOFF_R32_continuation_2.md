# HANDOFF — R32 continuation #2. Read this file first, in full, before touching anything.

This supersedes `HANDOFF_R32_continuation.md`, which described the state before the
previous session. Everything in §5 of that file is now done. This file is self-contained:
everything you need is either here or in a repo path named here.

---

## 0. THE GOAL — unchanged, and it governs every judgment call

Make the paper satisfy every condition the REVIEW3 committee raised **by making its claims
true, complete and correctly qualified.** Not by making a reviewer happy, and not by raising
a score.

Per condition, success is one of: (a) the manuscript now states something true it did not
state before, (b) a run produced a number the manuscript reports **whichever way it fell**,
or (c) the condition is recorded infeasible/declined/moot with the specific reason and the
strongest honest alternative in its place.

**Eugene has explicitly ruled out score-chasing** — *"i don't think that we should hit the
80, but just make the best paper while being honest about what we are."* Do **not** re-run
any review panel. Do not delete a disclosure to silence a criticism. Several conditions
exist *because* the paper disclosed something honestly; the remedy is always to carry the
disclosure into the headline.

## 1. HOUSE RULES THAT BIND

- **NEVER push.** Eugene pushes. **58 commits are unpushed and that is intended.**
- **Spec-before-run is absolute.** Any run-class condition gets a committed spec —
  pre-committed expectation, parity gates, artifact-overwrite guard, landing rule per
  outcome branch — **before** it executes, and the runner is committed before it runs too.
  An unfavourable result still lands.
- **One commit per batch, conditioned on green.** Literally
  `gates && tests && build && recut && render_gate && git commit`.
- **Argparse-less repo scripts EXECUTE on `--help`.** Never probe that way.
- **Never overwrite a frozen artifact.** New runs write new paths and refuse to overwrite.
- **The variant invariant.** `revised_paper_v18_long_abstract.tex` must differ from the
  canonical file at **line 31 only**. Body edits are mirrored; **line-31 edits are NOT** —
  the variant abstract is an archive. Assert it after every batch.
- **Assert DELTAS, not before/after pairs.** See §8.1 — this changed mid-session and it
  matters.

## 2. STATE, AND THE INVARIANT TO PRESERVE

Worktree: `/Users/eugene/somthing/Lock In effect/Lock-in-Effect/.claude/worktrees/agency-mbs-runoff-qt-424945`
Branch `claude/brave-shaw-b02840`, **58 commits on top of `a785f3d`**, tree clean.

**ALL GATES PASS (109) | 504 tests | ALL RENDER CHECKS PASS | 148pp canonical (main 1–102,
online appendix 103–148) | 148pp variant | abstract 427 words | 0 undefined refs |
0 errors | 0 overfull vbox | 0 off-page items.**

Verify before your first edit:
```bash
python3 tools/liveness_gates.py | tail -1
python3 -m pytest tests/ -q | tail -1
python3 tools/render_gate.py | tail -1
```

Build + split + render, the loop after every `.tex` batch:
```bash
cd paper/v18
for f in revised_paper_v18 revised_paper_v18_long_abstract; do
  ~/Downloads/texbuild/tectonic --keep-intermediates --outdir build_split $f.tex 2>&1 \
    | grep -ciE '^error|Overfull .vbox'; done      # both must print 0
cd - && python3 - <<'PY'
from pypdf import PdfReader, PdfWriter
import re
B='paper/v18/build_split/'
a=open(B+'revised_paper_v18.aux').read()
start=min(int(m.group(3)) for m in re.finditer(r'\\newlabel\{(app:[^}]*)\}\{\{([^}]*)\}\{(\d+)\}', a))
r=PdfReader(B+'revised_paper_v18.pdf'); n=len(r.pages); split=start-1
for name,rng in (('main',range(0,split)),('online_appendix',range(split,n))):
    w=PdfWriter()
    for i in rng: w.add_page(r.pages[i])
    with open(B+'revised_paper_v18_%s.pdf'%name,'wb') as f: w.write(f)
print(n,'pp; appendix starts',start)
PY
python3 tools/render_gate.py | tail -1
```

## 3. WHERE EVERYTHING IS

| what | path |
|---|---|
| **coverage ledger — every condition classified** | `specs/LEDGER_R32_coverage.md` |
| **133 canonical conditions** | `specs/INVENTORY_R32_conditions.md` |
| committed run specs | `specs/SPEC_R32_h0_reanchor.md`, `specs/SPEC_R32_floor_transport_two_sided.md`, `specs/SPEC_R32_c07_post_stratification.md`, `specs/SPEC_R32_c73_gradient_recompute.md` |
| the G2 adjudication record | `specs/RECORD_R32_h0_reanchor_G2_adjudication.md` |
| the panel's own reports | `REVIEW3_v18_panel_2026-07-29.md` |
| previous handoff (now historical) | `HANDOFF_R32_continuation.md` |

## 4. WHAT IS DONE — do not redo

**86 of 133 SATISFIED. All 12 actionable CRITICALs are SATISFIED**; the 13th (C-132,
Freddie parquet licensing) is Eugene's. Ledger: 86 SATISFIED / 35 OPEN / 7 DEFERRED-EUGENE
/ 3 DECLINED / 1 CLOSED-REFUTED / 1 MOOT, **zero unclassified**.

**All four Wave-2 clusters landed** (`287e266` G, `8e94534` B, `09bfad2` F, `80a109f` C),
plus C-40's inclusion-rule limb (`dcd6fc4`) and C-04's completion (`3defb90`).

**Four runs executed and landed, each reported whichever way it fell:**

| run | result | pre-commitment |
|---|---|---|
| **C-08** h₀ re-anchor (`bf7cbdc`/`0fbab7e`) | Branch B, u=0.5350; median **+9.44** (p05 +8.99, p95 +9.81); all 107 replicates above the headline, 106 above the +8.7 binding edge | predicted a FALL — **PREDICTION FAILED**, stated in the manuscript |
| **Task 11** two-sided transport (`41bf991`/`c3f37a7`) | leg (a) floor 5.2156% → **+4.70** (−0.87); leg (b1) floor 3.1533% → **+10.69** (+5.11); (b2) NOT_COMPUTABLE | both signs **HELD**; (a) in band [+4.60,+4.90] |
| **C-07** post-stratification (`00bb203`) | Branch A, all 6 gates; **+5.11** (−0.47); vintage-only +4.67 | direction **HELD**, band [+2.5,+5.0] **MISSED**, both reported |
| **C-73** gradient recompute (`e69be7a`) | ratios **5.5 / 4.7** vs the committed 4.5; all finite ratios 3.6–12.7; one **degenerate** cell | max-form sign HELD, **additive-form sign FAILED** |

**The consequential edit:** Task 11 leg (b) is a *measured floor correction that moves the
headline UP*, which falsified the abstract's and §I's claim that "every correction I can
measure … moves it down within the range rather than up". Both sites are **restated, not
deleted** (`c3f37a7`), and the gate literal, two test anchors, the response letter's word
count and the wrong-count list all moved with it.

## 5. WHAT IS LEFT — 35 conditions, in the order I would take them

### 5.1 Wave-4 table/structure edits — START HERE (7, mostly MINOR, all self-contained)
`C-93` Table 8's oversized calibration cell → its tablenote · `C-94` tab:wal note-rate-basis
row · `C-95` make tab:pathadiag single-spec · `C-96` promote the distributional-incidence
result out of the homogeneity check · `C-97` give the transportable methodological lesson
its own named paragraph · `C-82` household-side row in Table 1 · `C-83` duration row in
Table 1.
**Check gate pins on every table span first** — `tests/test_floor_ladder_gate.py` and
`tests/test_assembled_corrections_gate.py` carry hard `count(...) == 1` asserts.

### 5.2 The remaining wording (6)
`C-66` scope the "Two Structurally Distinct Estimators" framing (**heading is NOT
gate-pinned — verified**; the decomposition is a Path B object only) · `C-99` print the
measured +3.7 at the age-standardized floor with the grid-read beside it (`b5_joint_cell`
`conventional_agestd`: marginal 3.67132, ladder_implied 3.8, wedge −0.12868) · `C-109`
label the comparator basis at eight 5.14% sites (the fix suggests ONE definitions entry
plus pointers) · `C-106` spec-before-run ordering checkable, or say it is git-only ·
`C-121` de-nest 4+-parenthetical sentences · `C-117` prefer "cap shortfall" — **35 sites,
several inside gate-quoted spans; lowest value, highest risk, do it last or not at all**.

### 5.3 The two citation conditions (2) — need external verification, not memory
`C-85` add ~8 missing references (Deng–Quigley–Van Order 2000; Hanson 2014;
**Frankel–Gyntelberg–Kjeldsen–Persson 2004**; Svenstrup–Willemann 2006;
López-Salido–Vissing-Jørgensen 2023 and/or Acharya et al. 2024; Aiello 2022;
Fuster–Lucca–Vickery; Diep–Eisfeldt–Richardson 2021) and cite each at the argument it
bears on. **Verify every entry against a source before adding it — do not write
bibliographic details from memory.** Note the inventory's own correction: `fonseca2024` is
already in the bib, so only a *Fonseca–Liu–Mabille* extension would be new, and it must be
checked as distinct first.
`C-86` give §VI.C's assumability claims a cited basis (FHFA proposal, HUD Handbook 4000.1,
a VA circular, an assumption-volume basis). Sources are not named by the panel and must be
selected and verified.
**`C-51` is BLOCKED on C-85's Frankel entry** — do C-85 first, then C-51 lands as one
sentence.

### 5.4 The Danish/§VI.B remainder (3)
`C-48` report the Danish counterfactual in duration units at its own sites (tab:wal already
has the rows: Danish rule-only 9.1/8.2, Danish-level 10.8/9.6) · `C-54` restate §VI.B's
result in \$bn/month with a band · `C-49` T1's Danish cell must lead with the band
[+\$61.2, +\$256.8]bn. **C-49 is gate-delicate**: gate #71 requires the *first* paragraph
containing `$+\$61.2$ billion` to also carry `forced rather than found` and
`$-\$99.9$ billion`; the band must be added **around** those spans byte-preserving and the
first-mention ordering re-checked (my apply scripts already do this check — reuse it).

### 5.5 The ten wave-3 RUN conditions (10)
`C-72` month-clustered + two-way (stratum × month) rungs · `C-74` Ginnie leg with the
elasticity attenuated by the measured CRR differential · `C-75` re-derive the Danish
buyback discount D from the leg's own prepay path · `C-76` express the marginal in
transaction counts (**note: its comparator is realized existing-home-sale volume, and that
FRED series has no usable history on this account — see §8.4**) · `C-77` re-solve the
Aladangady reconciliation under the additive form · `C-78` episode gradient within narrow
age bands · `C-79` Danish leg with an interest-only share · `C-80` read the 2018 depth
ladder's shape · `C-81` state-contingent cap two-input table (a **re-tabulation**, no new
estimation) · `C-92` sweep or flag the floor's flatness in loan age (**spec it so it cannot
repeat the `floor_cyclical` mislabel**).

**`hazard/episode_gradient_recompute.py` + `specs/SPEC_R32_c73_gradient_recompute.md` are
the template.** That one took about an hour end to end. The pattern that works: reproduce a
committed number as a parity gate first, *then* vary one thing.

### 5.6 Wave-6 length — LAST, and check with Eugene first (4)
`C-88`–`C-91` (bring §IV/§VII.A/C/D to ~2pp, §V.B and §V.E to ~2,500 words, §VI.D to ~3pp)
and `C-122` (fold §VI.C into §VI.B). **These ask for cuts, and this round has ADDED roughly
2,400 words and taken the paper 142 → 148pp.** They are entangled with `C-130` (length and
venue), which is Eugene's. Do not start cutting without his call, and do not cut any
disclosure this round deliberately added.

## 6. RESERVED FOR EUGENE — do not act

`C-127`–`C-133`: the **public Freddie loan-level parquet licensing question** (`C-132`,
CRITICAL), **length and venue scope** (`C-130`, MAJOR — now 148pp and a 427-word abstract),
the unarbitrated benchmark monthly frequency and window-boundary allocation
(`C-127`/`C-128`), the anonymized master and archived DOI (`C-129`), the adverse-findings
register as a standalone methods note (`C-131`), and **the push** (`C-133`).

Also his, and newly sharpened by this round: **the abstract is 427 words** (was 323).
`C-123`/`C-124` were DECLINED because they collide with upheld conditions (see the ledger's
Dispositions section) — if he wants the abstract shorter, that is a scope decision, not a
defect to fix.

## 7. VERIFIED FACTS — use these, do not re-derive them

Everything in the previous handoff's §7 still holds. Added this session:

- **Ginnie−Freddie over the 42 QT months** (`gmar_dec25_cpr_series.json`): CPR gap
  **+2.1365**, CRR (voluntary) **+1.3541 = 63.4%**, CDR (buyout) **+0.8475 = 39.7%**. The
  CPR gap cross-checks bit-exactly against `ginnie_cpr_overlay_results.json`
  `G3_static_bound.window_mean_ginnie_minus_freddie_pp = 2.1365238095238093`. May-2025 is
  the buyout-dominated month (Ginnie CDR 2.10 vs Freddie 0.39), **not** representative.
- **Freddie realized CDR window mean 0.3139%/yr**, against the 3e-4 monthly prior's
  0.36%/yr — corroboration the calibration did not use.
- **Task 11 leg (a) arithmetic reproduces exactly**: 2018-leg support = periods
  201807–201812, counts 2/48/48/49/49/49, exposure shares 0.00009/20.2875/20.1487/19.9925/
  19.8530/19.7182%. "The QT window's mix" is `b1_profile.exposure_weight_by_month` **alone**
  (ratio 1.04500 → floor 5.2156%). Two rival readings were tested and rejected:
  calendar-count gives 1.04647, count×exposure gives 1.05987.
- **`vintage_overlay`'s `shares.retained = 0.663` is 1 − 0.337, the in-support share of book
  FACE.** The renormalised 2021 share is **also** 0.6631, by coincidence. Two different
  objects, same literal — never quote one for the other.
- **`rothstein_beta1(x)`'s first argument is the quarterly DECLINE, not P_q.** The P_q sweep
  is the `p_q_base` keyword: |β₁| = 0.0675/0.0679/0.0686/0.0701 at P_q = 0.015/0.03/0.06/0.12.
- **The "six extension-years" is 9.4 − 3.4 against tab:wal's 2021 refi-boom row.** Against
  the normal-turnover row it is 9.4 vs **9.5** — essentially nothing.
- **The coupon×vintage JOINT is not observable**: `fetch_soma_mbs_cohorts` collapses vintage
  to one value-weighted `origin_date` per (term, coupon) bucket. C-07 rakes **two
  marginals**, and any restatement must say so.

## 8. TRAPS THAT BIT THIS SESSION — all of these cost real time

1. **Assert DELTAS, not before/after pairs.** I mis-guessed baseline counts in four
   consecutive batches; every delta was right and only my baseline guess was wrong, so the
   script kept aborting on my arithmetic instead of on the paper's. Switching the census to
   `(after − before) == expected_delta` made it baseline-independent and it has passed
   first-time since.
2. **Some gate pins are BUILT DYNAMICALLY and a literal grep will not find them.**
   `liveness_gates.py` constructs e.g. `f"accounts for {…:.1f}\\%."` from artifact values.
   I grepped the gate source for the phrase, saw nothing, changed the wording, and broke the
   gate (108/109). **AST-extract the string constants, or diff the gate output, before
   changing any abstract or headline phrasing.**
3. **The engine is SINGLE-TENANT.** `floor_sweep._run_scored` writes fixed microsim parquet
   paths under the gitignored `hazard/data/floor_sweep/`. Never run two engine jobs at once.
4. **`run_qt_microsim` calls `fetch_data()` on EVERY cell.** A 214-cell run makes 214 live
   FRED calls and the first attempt died on a transient 502 eleven minutes in. `fetch_data`
   is patchable in `microsim_engine`'s namespace; `h0_reanchor.install_macro_cache` shows
   the pattern, and gate G1a validates the cache by still reproducing committed values.
   **Also: `fetch_data()` returns a frame trimmed to 2021+**, so anything needing pre-2021
   history (the 2018 leg) must call FRED directly.
5. **Do not write a progress watcher that greps for its own command line.** Mine tested
   `ps aux | grep -q '[h]0_reanchor'`, which always matched the watcher itself, so it
   reported a dead run as alive for eleven minutes. Parquet mtimes settled it.
6. **A failed gate may be your own instrumentation.** Task 9's G2 failed with an *empty*
   changed-list — a self-contradiction that turned out to be a checkpoint file I had added
   to the sha scope after writing the exclusion list. Adjudicated with git as independent
   evidence in `specs/RECORD_R32_h0_reanchor_G2_adjudication.md`; the artifact was left
   exactly as the run wrote it. **Never rewrite a produced artifact to turn a gate green.**
7. **Same-literal/different-object collisions are everywhere in this paper.** Three hit this
   session: `0.663`, `\$2.4 trillion`, and `$+9.4$`. Before printing any new figure, grep it
   and read what the existing occurrences denote.

## 9. ANTI-CONDITIONS — do not "fix" any of these

All of the previous handoff's §9 still holds (Webb is not the narrowest of ten; the abstract
is **two** paragraphs; Table 27 rows did move reported numbers; the duplicated table captions
exist only in the markdown edition; 40,234 is the paper's own attrition figure; do not flip
β₁ signs; R2:M8 is unarbitrated). Added:

- **The "every correction moves it down" claim is GONE on purpose.** It was falsified by a
  measured floor correction and restated. Do not restore it.
- **C-65 is MOOT**, not open — it was the fallback for "absent C-07", and C-07 ran.
- **C-123/C-124 are DECLINED**, with reasons in the ledger. Do not act on them mechanically.
- **`extension_risk_results.json`'s `lag_interpretation` string is knowingly wrong** and is
  left in place because the artifact is sha-pinned; the manuscript now says so (C-114). Do
  not "fix" the artifact.
- **tab:ladder already overflows its text block by 35.77pt** — pre-existing, and
  `render_gate.py` does **not** catch horizontal in-table overflow. Recorded, not repaired.

## 10. WHAT TO PRODUCE AT THE END

A summary for Eugene covering: which conditions moved from OPEN to SATISFIED and by which
commit; every run's result **reported whichever way it fell**, with its pre-committed
expectation quoted beside it and whether the prediction held; anything recorded
INFEASIBLE/DECLINED/MOOT with the specific reason and the honest alternative that landed
instead; the final verification line (gates / tests / render / page counts / split /
abstract words); the finalised coverage-ledger counts with **zero unclassified**; and a
short, honest list of judgment calls he might reverse. State plainly anything you could not
finish and why. **Do not push.**
