# Handoff — round 25 — two scope calls, and nothing else open

**Read this first.** It supersedes `HANDOFF_round24.md`, whose items **1, 3, 4 and 6 are
closed**. `HANDOFF_round22.md` **§3 hard constraints and §4 gotchas still bind** — read them
before editing anything. Companions: `TECHNICAL.md` §35 (this round), §§31–34 (round 23).

---

## 0. State

| | |
|---|---|
| Repo | `/Users/eugene/somthing/Lock In effect/Lock-in-Effect` (**public**, `eugeneoCMU/Lock-in-Effect`) |
| Branch | `claude/handoff-rounds-22-24-59c228`, **local, unpushed**, four commits on top of `00d938d`. `claude/handoff-round22-edits-701fb2` fast-forwards onto it. `panel-revision-2026-07-18` and `main` untouched. |
| Manuscript | `paper/v18/revised_paper_v18.tex` — **116pp**, abstract **307 words**, one paragraph per line |
| Gates | `python3 tools/liveness_gates.py` → **98 ALL PASS** |
| Tests | `python3 -m pytest tests/` → **337 pass** |
| Build | `~/Downloads/texbuild/tectonic -X compile revised_paper_v18.tex --outdir build_r24 --keep-logs` → 116pp, **0 undefined refs** |

Round 24 ran **no runs at all**. Every number it landed was read out of a committed artifact.

---

## 1. What round 24 closed

Detail in `TECHNICAL.md` §35. In one line each:

- **§1 + §4 — the assembly.** A seventh qualification in `sec:identification` lines up the
  downward corrections ($+9.2 \to +5.6 \to +4.4 \to +3.8$, Fannie's 5.52% bracketing below
  $+4.3$, the uncomposed pair near $+3.0$), states the frame (corrections to the **floor or
  the accounting basis**, production form and imported elasticity held fixed), and **commits
  to a posture**: within the production form the binding layer is $[+3.0, +8.0]$, the headline
  sits just above its midpoint, every correction falls in the lower half, so $+5.6$ is an
  **upper-middle member rather than the centre**. Counterweight in the same paragraph (the
  additive form, the Fonseca anchor, the sixth qualification's three readings). Censoring
  folded in with round-22 §8.2's framing intact. Pinned by **gate #98**.
- **§3 — Path A's prominence.** `tab:panel` and `tab:bootstrap` moved verbatim to `app:ridge`.
  Path A now holds **one** of the first seven tables, not three. No result touched.
- **§6 — the orphaned Section IV.** Two sentences returned the ABM to the abstract, with both
  the 13.6% seed mean and the cross-design counterweight, and four new abstract-scoped hedge
  spans travelling with them.

---

## 2. WHAT IS OPEN: two scope calls, both Eugene's

Neither is a defect. Both are judgement calls about what the paper is, and a session should
not make them. My recommendation is recorded so it can be argued with, not so it can be
executed on sight.

### 2.1 `HANDOFF_round24.md` §2 — the ABM

The production ABM recovers **13.6%**; its own cross-design variant reaches **76.3%** at book
composition, and round 23 established (`abm_null_feasibility`, NOT_FEASIBLE, TECHNICAL §31)
that it cannot be compared with Path B on a differential at all.

**My recommendation: option 1 — lead §IV with the cross-design result**, framing the production
ABM as the synthetic-population special case. Reasons, in order:

1. It changes emphasis and not one number, so it cannot introduce an accuracy defect. Option 2
   (cut §IV to a diagnostic) moves ~15–20pp of specification detail and would be the largest
   destructive pass since the v18 source was lost.
2. It is what the evidence already says. The paper's own sixth qualification lists the
   cross-design result among three readings pointing to a *larger* channel; §IV currently leads
   with the reading that points the other way.
3. It survives either later decision. If §IV is cut afterwards, a cross-design-led §IV is the
   part you keep.

**Cost of being wrong:** gate exposure is heavy (`76.3\%` ×7, `60.2\%` ×8, `13.6\%` ×10, and
the ABM spans now live in **both** `RELOCATED_TO_BODY` and `ABSTRACT_HEDGES`). Any restructure
moves tex + gates + tests in ONE commit. Budget a full session; do not start it in the last
hour of one.

**Against my own recommendation, honestly:** option 3 (leave it) is defensible. A falsification
device that fails when handed real covariates is a finding about the device, and the paper says
so. The reason I do not recommend it is that §IV is a third of the paper and currently reads as
if the 13.6% were the result.

### 2.2 `HANDOFF_round24.md` §5 — 116pp, and the methods note

Page compression was abandoned by Eugene on 2026-07-26 and **that decision stands**. Round 24
added a page rather than removing one, which is the right trade for the paper's biggest
exposure but is worth stating plainly.

**My recommendation: do nothing about length, and split the methods note only if you want to
publish it.** The apparatus (spec-before-run, 98 gates, parity replay, the perturbation
batteries) is a genuine contribution and it is crowding the finding — but "crowding" is an
argument for a *second paper*, not for deleting the apparatus from this one. A conference
venue does not force the issue. If §2.1 is taken, ~15–20pp leave as a byproduct and the
question may answer itself.

**What I would not do:** reopen compression as an exercise. The concision handoff records that
~40% of that round's rewrites strengthened a claim past its evidence while passing every gate.

---

## 3. Constraints — the ones that bit this round

All of `HANDOFF_round22.md` §3 still binds. Specifically:

- **Every body edit must be mirrored into `paper/v18/revised_paper_v18_long_abstract.tex`.**
  The variant gate requires an **identical line count** and difference on the abstract line
  **only**. The reliable move is to regenerate it: canonical with line 30 swapped for the
  archived abstract line. Doing this by hand will drift.
- **Zero-slack literals, recounted at 116pp:** `positive at every` **6** · `$+3.0$ to $+8.0$`
  **4** · `11.06` **4** · `76.3\%` **7** · `$+3.5$ to $+13.1$` **6** ·
  `$+3.9$ to $+13.1$` **0 (must stay 0)** · `60.2\%` **8** · `13.6\%` **10**.
  Gate minima are lower than these counts; check the gate, not this table, before deleting.
- **Gate #98 is paragraph-scoped.** Splitting the seventh qualification into two paragraphs
  fails it even though every literal survives in the file. That is intentional.
- **The figure PNGs and `.env` are gitignored**, so a fresh worktree build needs both symlinked
  in from the main checkout before `tectonic` will run.

---

## 4. What round 24 got wrong, and how it was caught

Same shape as round 23's four, and the same lesson: **the check was wrong, the artifact was
right, and the thing that found it was a test written against intent rather than
implementation.**

1. **Gate #98 did not pin its own headline number.** The first cut pinned the censoring
   *framing* and not the 68.8% *share* — the whole of item §4 — so the number could have been
   deleted while the gate stayed green. Found by the battery's coverage test on its first run,
   not by review.
2. **"Every correction points down" is too strong as written.** The handoff's ladder lists only
   the downward ones; the additive form ($+11.2$) and the Fonseca anchor ($+11.5$) run the
   other way. The paragraph states the frame explicitly (**floor or accounting basis**, form
   and elasticity held fixed) for that reason. Anyone restating the assembly without the frame
   is overclaiming.
3. **The `0.797` is a ratio, not a parameter.** It is the overlay marginal over the
   conventional one (4.44342 / 5.57156), computed from the artifact. It reads like an input
   scale and is not one.
