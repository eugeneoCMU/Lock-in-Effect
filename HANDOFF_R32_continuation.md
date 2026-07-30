# HANDOFF — R32 continuation. Read this file first, in full, before touching anything.

You are continuing Round 32 (REVIEW3 remediation) on the Lock-In paper. A prior session
landed 21 commits. This file is self-contained: everything you need is either here or in
a repo path named here. **Nothing lives in a scratchpad** — the prior session's scratchpad
is gone, and its contents that matter were copied into `specs/r32_wave2/`.

---

## 0. THE GOAL — it governs every judgment call

Make the paper satisfy every condition the REVIEW3 committee raised **by making its claims
true, complete and correctly qualified.** Not by making a reviewer happy, and not by raising
a score.

Per condition, success is one of: (a) the manuscript now states something true it did not
state before, (b) a run produced a number the manuscript reports **whichever way it fell**,
or (c) the condition is recorded infeasible with the specific reason and the strongest
honest alternative in its place.

**Eugene has explicitly ruled out score-chasing.** He asked at one point for the panel to
grade ≥80 and then withdrew it himself: *"i don't think that we should hit the 80, but just
make the best paper while being honest about what we are."* Do **not** re-run any review
panel to measure improvement. Do not delete a disclosure to silence a criticism, and do not
soften a true claim into vagueness. Several conditions exist *because* the paper disclosed
something honestly; the remedy is always to carry the disclosure into the headline.

## 1. HOUSE RULES THAT BIND

- **NEVER push.** Eugene pushes. 21 commits are unpushed and that is intended.
- **Agents DRAFT only.** Opus agents produce count-asserted OLD/NEW pairs with a pinned-span
  census. The coordinator independently re-verifies every span and count, then applies.
  Agents never modify tracked files and never execute anything. All runs and applies are
  the coordinator's.
- **Spec-before-run is absolute.** Any run-class condition gets a committed spec — pre-committed
  expectation, parity gates, artifact-overwrite guard, landing rule per outcome branch —
  **before** it executes. An unfavourable result still lands.
- **One commit per batch, conditioned on green.** Literally:
  `gates && tests && render_gate && git commit`. Three round-28 incidents committed before
  their checks ran.
- **Argparse-less repo scripts EXECUTE on `--help`.** Never probe that way. Includes
  `tools/liveness_gates.py`.
- **Never overwrite a frozen artifact.** New runs write new paths.
- **Zero-slack literal discipline.** Recount printed numbers with fixed-string counts
  (`grep -oF` / `str.count`), including and-forms, and read the *gate source* for each
  gate's actual minimum — they are `>=`, not exact. Recount after every batch.
- **The variant invariant.** `revised_paper_v18_long_abstract.tex` must differ from the
  canonical file at **line 31 only**. Assert it after every batch. Body edits are mirrored;
  **line-31 edits are NOT** — `liveness_gates.py` records that the variant abstract "is an
  archive that must not be rewritten to suit a new pin".

## 2. STATE, AND THE INVARIANT TO PRESERVE

Worktree: `/Users/eugene/somthing/Lock In effect/Lock-in-Effect/.claude/worktrees/agency-mbs-runoff-qt-424945`
Branch `claude/brave-shaw-b02840`, 21 commits on top of `a785f3d`, tree clean.

**ALL GATES PASS (109) | 503 tests | ALL RENDER CHECKS PASS | 142pp canonical / 143pp
variant | split main 1–96, online appendix 97–142 | 0 undefined refs | 0 errors |
0 overfull vbox.**

Verify before your first edit:
```bash
python3 tools/liveness_gates.py | tail -1
python3 -m pytest tests/ -q | tail -1
python3 tools/render_gate.py | tail -1
```

Build + split + render, the loop to run after every `.tex` batch:
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
| the plan | `docs/superpowers/plans/2026-07-29-review3-remediation.md` |
| **133 canonical conditions** | `specs/INVENTORY_R32_conditions.md` |
| **coverage ledger, every condition classified** | `specs/LEDGER_R32_coverage.md` |
| execution log with all findings | `PLAN_R32_execution_log.md` |
| Wave-2 drafts, verdicts, corrected sets | `specs/r32_wave2/` |
| committed run specs | `specs/SPEC_R32_h0_reanchor.md`, `specs/SPEC_R32_floor_transport_two_sided.md` |
| the panel's own reports | `REVIEW3_v18_panel_2026-07-29.md` |
| talk prep | `docs/carroll_round_qa_prep.md` |

## 4. WHAT IS ALREADY DONE — do not redo

20 of 133 conditions SATISFIED, including **8 of the 13 CRITICALs**. See
`specs/LEDGER_R32_coverage.md` for the per-condition mapping. Headlines:

- Abstract repaired (three CRITICALs) — `66df169`; the layer/read ambiguity — `b26c1f6`
- Form-fork basis mix, one basis named — `c2e505e`
- β₁ signs harmonised + **new gate #109** — `d22b265`
- Floor read's true support; "two independent lines" argument **retired**; `tab:oosfloor`
  caption narrowed and the 5.51/5.52 reads promoted to rows — `6a34d5c`
- Composition: sampler's allocation rule disclosed, `tab:composition` restructured — `2ec6a8e`
- **Paragraph architecture**: the four worst paragraphs split, zero words moved — `59d81c1`
- **Appendix O states the gate suite's domain** + the 919-off-page disclosure — `a978da7`
- **The partition defined**, with the behavioral concession inside it — `1fe5bb6`
- **Retitle + the +5.6 posture** (both Eugene's calls, both taken) — `d1bf578`
- Carroll Round prep, later corrected for a basis error — `7189c8e`, `3757e03`

## 5. WHAT IS LEFT, IN ORDER

### 5.1 Apply the four Wave-2 clusters — START HERE

`specs/r32_wave2/` holds, per cluster: `DRAFT_w2_<k>.md` (the original edit set),
`VERDICT_w2_<k>.md` (an adversarial verifier's findings), and where the fix pass finished,
`CORRECTED_w2_<k>.md` (the draft with those findings folded in and re-anchored).

**Every one of the seven verdicts came back `APPLY_WITH_LISTED_FIXES` — none was clean.**
65 refuted claims across the wave. Apply the CORRECTED set where it exists; where it does
not, fold the verdict into the draft yourself before applying.

| cluster | conditions | corrected set present? |
|---|---|---|
| `G-denominators` | C-31, C-36, C-42, C-43, C-44, C-45, C-46, C-62 | yes |
| `B-ladder` | C-05, C-20, C-21, C-24, C-25, C-27, C-38, C-69 | yes |
| `F-assembly` | C-18, C-26, C-39, C-40, C-41 | check; else fold the verdict |
| `C-formfork` | C-04 (CRITICAL, partial), C-22, C-23, C-28, C-32 | check; else fold the verdict |

Apply **one cluster per commit**, and for each: re-measure every `OLD` count against the
*current* file (the drafts predate several landings — see §7), assert every pinned span
survives, build, recut, render-gate, then commit.

**Collision warning.** These clusters overlap. The line that starts `A seventh qualification`
is contested by `B-ladder` and `F-assembly`, and it carries all 15 `ASSEMBLY_SPANS`. Apply
sequentially and re-measure between clusters; an apply script that asserts `count == 1` turns
a collision into a clean abort rather than silent corruption.

### 5.2 `D-mechanical`'s residual — probably DROP

`specs/r32_wave2/DRAFT_w2_D-mechanical.md` has 33 edits renaming the partition-carrying uses
of "mechanical". Five of them landed as the definition (`1fe5bb6`). **With the term now
defined, the remaining 28 are uses of a defined term, not defects.** The draft itself adds
+164 front-matter words. Recommend dropping it and recording that in the ledger. If you
disagree, note that the verifier found the draft shipped four surface names for one object.

### 5.3 The two specced runs

Both specs are committed. Read the spec, do not re-derive it, and land whatever comes.

- **C-08 / Task 9 — h₀ re-anchor.** `specs/SPEC_R32_h0_reanchor.md`. Seam is
  `literature_hazard.baseline_hazard` (NOT `_ORIG_PREPAY` — the spec explains why, and
  `PSA_SPEED` binds at def time so mutating config is a silent no-op). Six parity gates
  including **a no-op patch is GATE_FAILURE** and a cross-route check whose expected value
  comes from outside the run (φ=0.75 and 75 PSA must both give `marginal_pp` 0.8560355409769471).
  **Pre-committed prediction: the marginal FALLS.** Measured before speccing: only 98 of 199
  converged Path A bootstrap replicates imply a usable hazard over ages 18–107, so Branch B
  or C is likely. Branch C (NOT_FEASIBLE) is a legitimate outcome — record it with the
  reason and land the honest alternative.
- **Task 11 — two-sided floor transport.** `specs/SPEC_R32_floor_transport_two_sided.md`.
  Two **opposite-signed** legs, both committed before either runs; **neither may be reported
  without the other.** Leg (a) is analytic and already derived in the spec (floor
  4.991 → 5.2156%, marginal ≈ +4.74pp, a −0.83pp move) but needs **one engine cell** for the
  exact value — `floor_sweep_results.json`'s grid is 2.0/3.0/3.5/4.0/4.5/5.0/6.0 with nothing
  at 5.2156. Pre-committed band [+4.60, +4.90].
  **If leg (b) lands, the paper's claim that "every correction I can measure … moves it down
  within the range rather than up" becomes FALSE as written — in the body AND the abstract —
  and must be restated, not deleted.** That is the single most likely way this round goes
  quietly wrong.

### 5.4 C-07 — the only CRITICAL with no spec

Post-stratify the 75,000-loan draw onto SOMA coupon × vintage cells. **Write and commit a
spec first.** The composition disclosure it builds on landed in `2ec6a8e`; the
surviving-balance shares it needs are in §7 below. Reuses `cross_design_reweight` machinery.

### 5.5 Remaining waves, then the close

77 conditions are still OPEN in the ledger — mostly Wave 5 (structural) and Wave 6 (policy
exhibits, incl. rebuilding §VI.B around a deliverable). Work them in ledger order, highest
severity first. Then the close: rebuild all four PDFs, recut the split from the fresh `.aux`,
regenerate the md/txt editions (`tools/editions/tex2md.py` then `md2txt.py`), refresh the
UPLOAD bundle **with a note on the page-count change and why**, and finalise
`specs/LEDGER_R32_coverage.md` so **no condition is left unclassified**.

## 6. RESERVED FOR EUGENE — do not act

`C-127`–`C-133` in the ledger. Named explicitly: the **public Freddie loan-level parquet
licensing question** (`C-132`, CRITICAL, two auditors independently; a licensing judgment
needing history rewriting if it is a problem), **length and venue scope** (`C-130`, MAJOR —
the paper is 142pp and this round added 3), the unarbitrated benchmark monthly frequency and
window-boundary allocation (`C-127`/`C-128`), the anonymized master and archived DOI
(`C-129`), the adverse-findings register as a standalone methods note (`C-131`), and **the
push** (`C-133`).

## 7. VERIFIED FACTS — use these, do not re-derive them

- **Basis conversion.** `shared_pct = standalone_pct − 9.0964`, from
  `shared_layer_scoring_results.json` `curtailment_netted_b = 69.56220187263008` over
  benchmark `764.7482532227`. Reproduces every printed figure from
  `floor_form_mixture_results.json`'s standalone `share_pct`: 100.363→91.3, 94.792→85.7,
  55.907→46.8, 44.700→35.6. **Marginals in pp are basis-INVARIANT** — never label one.
- **Inference ladder** at the headline read (`floor_inference_correction_v2_results.json`,
  `reads.R2_2018_gap<=-0.0025_age>=12`), widths in pp: percentile 5.044, CR1-t 5.197,
  CR2-t 5.579, **Webb 5.823**, Rademacher 5.927, CR3-t 6.001, CR1-BM 6.043, CR2-BM 6.740,
  WCR 6.828, CR3-BM 7.284. Webb is **third-narrowest**, and narrowest only among rungs with
  a credible few-cluster coverage property.
- **Grid truncation direction.** CR3-BM and WCR clip their **LOWER** endpoints to `+2.2809`
  at the 6.0% floor-grid edge (unclipped `floor_pct` 6.1160 / 6.1813). So their unclipped
  lower ends lie **below** +2.28 and the true spread is **wider** than printed. Corroborated
  independently: `floor_sweep_results.json`'s 6.0% cell marginal is 17.443 = exactly that
  clipped value.
- **The draw's composition, on four distinct bases.** The aggregation applies **surviving
  balance at the window open** (§V.B), computed over the 40,077 loans with `balance > 0`:

  | vintage | count | orig. balance | **surviving balance** | book face |
  |---|---|---|---|---|
  | 2017–19 | 60.0% | 55.5% | **27.0%** | 6.0% |
  | 2020 | 20.0% | 22.2% | **30.7%** | 16.3% |
  | 2021 | 20.0% | 22.3% | **42.3%** | 43.9% |

  So on the operative basis 2021 is **near parity (0.96×)** and 2017–19 is 4.5× over, not
  10×. Out-of-support mass is what binds: pre-2017 (10.6%) + 2022 (23.1%) = **33.7% of face**,
  and the paper's own caveat is that this nets against the 20.4% Ginnie share on joint cells
  rather than adding to it.
- **Coupon buckets.** The paper's `3.0–4.0%` bucket is rounded half-point keys 3.0+3.5, with
  the 4.0 key belonging to `≥4.0`. On that convention the committed shares are 7.1/34.7/58.2
  count-weighted and 7.9/38.4/53.7 UPB-weighted. `47.0%` is the count-weighted **raw**
  (unrounded) ≥4.0 share. The `coupon` column in `loan_sample.parquet` is **decimal-scaled**.
- **Clean floor leg support.** The 2018 rising-rate leg has cohort-months only in ages
  [0,12) (505) and [12,24) (155); **zero at ≥24**; `mature_test_computable: false`; verdict
  `CLEAN_BY_CONSTRUCTION_MATURE_TEST_NOT_COMPUTABLE`. Its own +1.558pp ramp is flagged
  `ramp_rise_is_psa_confounded: true` and is **not** evidence for the seasoning direction —
  the cross-agency mature cells are (12 of 12 measurable cells run the same way: +0.08/+0.19pp
  in window, +3.74/+4.61pp pooled-but-contaminated).
- **The 2018 leg's month support** (in no committed artifact until R32): reporting periods
  201807–201812, cohort-month counts 2/48/48/49/49/49, exposure shares
  0.00009/20.287/20.149/19.993/19.853/19.718% — **six periods by count, five by exposure
  weight.** Say which weighting you mean.

## 8. TRAPS THAT ALREADY BIT — all of these cost real time

1. **Table notes live AFTER the float, not inside it.** Round 31 moved `tab:bases`,
   `tab:estimators`, `tab:danish`, `tab:ladder`, `tab:oosfloor` (and now `tab:composition`)
   to post-float `\noindent{\footnotesize \emph{Notes to Table~\ref{...}.} … \quad b … \par}`
   paragraphs because in-float notes pushed floats off the page. A prior session "fixed" two
   non-existent dangling-`\tnote` defects by duplicating notes that already existed
   (`3a81e71`, reverted by `d2c0c67`). **Any structural audit must encode the repo's actual
   convention, not LaTeX's default.**
2. **Green gates are necessary and never sufficient.** 108 gates passed while ~919 items
   rendered off the page. In this round alone, green coexisted with duplicated notes and with
   a float 87.6pt over its page. **Always build and run `render_gate.py`.**
3. **The abstract word count is a three-way coupling.** Gate #101 ties
   `response_to_referees_round22.tex`'s "taken it to N words" to the measured abstract count,
   and `tests/test_response_letter_gate.py` hardcodes that string as a mutation anchor — if
   you change the count and not the anchor, three tests silently vacate. Add the retired count
   to that test's wrong-count parametrize list. It is currently **323**.
4. **Three gates read paragraphs, not the file.** Never split or merge: the line starting
   `A seventh qualification` (gate #98 needs all 15 `ASSEMBLY_SPANS` on that one line), the
   line starting `This section is a stress test` (gate #100), or any line containing
   `$+\$61.2$ billion` (gate #71 needs `forced rather than found` and `$-\$99.9$ billion`
   co-occurring in that same paragraph).
5. **Pinned-span assertions must fail on DROPS, not on changes.** Gates take `>=` minimums,
   so an increase is fine. Assert decreases, plus `ZERO_COUNT` still 0 and `EXACTLY_ONE`
   still 1.
6. **Do not trust an agent's arithmetic, and do not trust your own over the artifact.** A
   prior session doubted a draft's coupon cells, recomputed, and was itself wrong — the
   artifact settled it. Go to the artifact.

## 9. ANTI-CONDITIONS — do not "fix" any of these

Webb is not the narrowest of ten rungs. The abstract is **two** paragraphs (explicit `\par`
at line 31). Table 27 rows **did** move reported numbers. There **is** a cell where the
baseline fails to deliver the majority (floor 4.991, s=1: 44.70% standalone / 35.6% shared).
The duplicated table captions exist **only** in the markdown edition — a converter artifact;
fix `tools/editions/tex2md.py` if anything. The ≥4.0% share 53.7% is correct only on
UPB-weighted rounded-coupon buckets — name the basis, never swap the number. **40,234 is the
paper's own attrition figure** (75,000 − 34,734 − 32); `loan_sample.parquet`'s `balance > 0`
count is 40,077, so the *provenance* claim is wrong but the number is right. **Do not flip
β₁ signs** — `eq:beta1` carries a leading minus making β₁ positive, while
`hazard/literature_hazard.py:32 rothstein_beta1` omits it; gate #109 now asserts agreement.
R2:M8 (benchmark monthly frequency) is **unarbitrated** — treat as open, not as a defect.
The full list, with the corrections, is in `specs/INVENTORY_R32_conditions.md`.

## 10. WHAT TO PRODUCE AT THE END

A summary for Eugene covering: which conditions moved from OPEN to SATISFIED and by which
commit; every run's result **reported whichever way it fell**, with its pre-committed
expectation quoted beside it and whether the prediction held; anything recorded INFEASIBLE
with the specific reason and the honest alternative that landed instead; the final
verification line (gates / tests / render / page counts / split); the finalised coverage
ledger counts with **zero unclassified**; and a short, honest list of judgment calls he might
reverse. State plainly anything you could not finish and why. Do not push.
