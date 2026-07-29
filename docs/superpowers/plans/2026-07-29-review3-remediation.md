# REVIEW3 Remediation Implementation Plan (Round 32)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

## /GOAL

**Make the Lock-In paper satisfy every condition raised by the REVIEW3 committee — by making the paper's claims true, complete, and correctly qualified. Not by making a reviewer happy, and not by making a score go up.**

The test of success is *per condition*, not aggregate: for each condition, either (a) the manuscript now states something that is true and was not stated before, or (b) a run has produced a number the manuscript now reports whichever way it fell, or (c) the condition is recorded as infeasible with the specific reason and the strongest honest alternative in its place. A condition is NOT satisfied by deleting the sentence a reviewer attacked, by softening a true claim into vagueness, or by re-running the panel until it agrees.

**Source of conditions:** `REVIEW3_v18_panel_2026-07-29.md` (committed, 1,326 lines) — the EIC, three peer reviewers, the Devil's Advocate, and the Editorial Synthesis. The synthesis's ranked roadmap R1–R16 is the committee's own consolidation, but **it is not the whole condition set** — each reviewer's report contains conditions the synthesis did not promote. Task 0 builds the complete inventory.

**Baseline:** 63.6/100, MAJOR REVISION (five reviewers independently 61.4–64.6). Carroll Round verdict: PRESENT WITH FIXES. Prior panel on the pre-round-28 draft: 76.3.

---

## ANTI-GAMING RULES (hard constraints — violating one fails the task)

1. **Never delete a disclosure to silence a criticism.** Several conditions exist *because* the paper honestly disclosed something (the 14.77pp PSA convention span; the age-transport error; the 51.0% book-face coverage). The remedy is always to carry the disclosure *into the headline*, never to remove the disclosure so the criticism has nothing to attack. If you find yourself deleting a caveat, stop.
2. **No tuning to the rubric.** Fix the defect the reviewer named. Do not restructure prose because "Writing scored 56," do not add citations to raise "Literature Integration," and do not re-run any panel to measure improvement. The score is a diagnostic, not a target.
3. **Spec-before-run is absolute.** Every run-class condition gets a committed spec — pre-committed expectation, parity gates, artifact-overwrite guard, and a landing rule *per outcome branch* — before it executes. **If a run makes the paper's headline worse, that result lands.** R5 in particular may move the marginal against the author's interest; that outcome is pre-authorised and must be reported.
4. **Verify every condition against source before acting.** The panel logged ten of its own factual errors (synthesis §8) and this plan's own prep caught an eleventh: the panel's suggested fix for the β₁ sign would have made the manuscript contradict its production code. Conditions carrying a wrong premise are listed in **Anti-Conditions** below; do not "fix" them. For any condition not pre-verified here, derive it from the `.tex`, the frozen artifact, or the production code *first*.
5. **Never overwrite a frozen artifact.** New runs write new paths. Re-derive, never regenerate, anything a gate reads.
6. **Green gates are necessary, never sufficient.** 108 gates passed while ~919 text items rendered off the physical sheet. Every landing runs gates + tests + `tools/render_gate.py`, and a human-legible read of the changed passage.

**Never push.** Eugene pushes. Two commits are already unpushed (`b493d78`, `95e1d2f`, `d5465d2` chain).

---

**Architecture:** Six dependency-ordered waves. Wave 1 is the four required-before-presenting wording repairs (no runs, exact strings supplied below). Waves 2–4 are the run-class conditions, each gated behind a committed spec. Wave 5 is structural (paragraph architecture — the single largest scoring deficit and untouched by rounds 28–31). Wave 6 is the policy exhibits. The close re-runs the whole verification stack and refreshes the derived artifacts.

**Tech Stack:** LaTeX (tectonic at `~/Downloads/texbuild/tectonic`), Python 3 (pypdf for PDF inspection), `tools/liveness_gates.py` (108 gates), `tests/` (495 tests), `tools/render_gate.py` (render layer), `tools/editions/{tex2md,md2txt}.py` (md/txt editions).

## Global Constraints

- Worktree: `/Users/eugene/somthing/Lock In effect/Lock-in-Effect/.claude/worktrees/agency-mbs-runoff-qt-424945`, branch `claude/brave-shaw-b02840`, HEAD `d5465d2`.
- Manuscript: `paper/v18/revised_paper_v18.tex` (139pp). Variant: `paper/v18/revised_paper_v18_long_abstract.tex` — **must receive identical body edits; the two differ at line 31 only (the abstract), and that invariant is asserted after every batch.**
- The `.tex` has 5KB+ single-line paragraphs. Never dump whole lines: use `grep -o`, `awk 'NR==n'` with `cut -c`, or targeted char ranges.
- **Zero-slack literal discipline:** before touching any printed number or pinned phrase, recount it with a **fixed-string** count (`grep -oF` or `str.count`), **including and-forms** (`$+2.9$ and $+8.7$` is a different string from `$+2.9$ to $+8.7$`), and read the *gate source* to learn each gate's actual minimum (they are `>=`, not exact). Recount after every batch.
- **Architecture (Eugene's standing instruction):** opus agents DRAFT edit sets as count-asserted OLD/NEW pairs with a pinned-span census; the coordinator independently verifies every span and count, then applies. **Agents never modify tracked files and never execute anything.** All runs and applies are the coordinator's.
- Argparse-less repo scripts EXECUTE on `--help`. Never probe that way. This includes `tools/liveness_gates.py` and `pytest` for agents (the coordinator runs them).
- One commit per batch, and the commit must be **conditioned on green** (`gates && tests && render_gate && git commit`) — three round-28 incidents committed before their checks ran.
- Baseline to preserve: **ALL GATES PASS (108) | 495 tests | ALL RENDER CHECKS PASS | 139pp canonical / 140pp variant / split 1–94 + 95–139 | 0 undefined refs.**

---

## ANTI-CONDITIONS — do NOT act on these

From synthesis §8 (the panel's own refutations) plus this plan's prep. Acting on any of these would introduce a defect.

| Claim | Why it is wrong | What a naive fix would break |
|---|---|---|
| R1: Webb is "the narrowest of the ten rungs" | False. Widths (pp): percentile 5.045, CR1-t 5.197, CR2-t 5.579, **Webb 5.823**, Rademacher 5.927, CR3-t 6.001, CR1-BM 6.043, CR2-BM 6.740, WCR 6.828, CR3-BM 7.284. Webb is third-narrowest overall, narrowest *among those with a credible few-cluster coverage property* — which is R1's real argument and survives. | Rewriting the selection sentence to concede a false premise. |
| DA: "the abstract is a single paragraph, 248 words" | Wrong on both counts. There is an explicit `\par` at `.tex:31`; the abstract is **two** paragraphs, ~250 words. DA's proposed break already exists at exactly the seam it names. | Inserting a duplicate paragraph break. |
| DA:N9: "not one Table 27 row moved a reported number" | False. The floor demotion moved the headline +9.2→+5.6 and the central level 97.9%→91.3%; the bootstrap retraction replaced [+9.17,+9.23] with [+8.27,+10.19]; the Webb correction moved the printed lower endpoint (`printed_lower_unchanged: false`); the Danish validation turned a point into a band. | Adding a defensive paragraph rebutting a claim that is already false. |
| DA:N1: "no cell where the mechanical baseline fails to deliver the majority" | False as a universal. `floor_form_mixture_results.json` at floor 4.991, s=1 gives a null of 44.70% standalone / 35.6% shared. | Nothing — but note the *opposite* condition (label the 85.7% as form-conditional) IS real and is C-R1b. |
| R2: duplicated table captions "will read as sloppiness in a submitted PDF" | Exists only in the markdown edition (a longtable→markdown converter artifact at md:41/43). The `.tex` caption sits correctly before `\endfirsthead`. No PDF defect. | Editing correct LaTeX to chase a converter bug. If anything, fix `tools/editions/tex2md.py`. |
| R2:M6: "the paper headlines the Danish minimum" | Right for Table 1's cell and the abstract's omission; **wrong** for §I and §VI.D, which both give the band and label +$61.2bn "the zero-refinance edge." | Rewriting two passages that are already correct. |
| R2:M2: "the sample's ≥4.0% share is 53.7%, not 13.8%" | 53.7% is correct only on UPB-weighted rounded-coupon buckets; the same draw is 58.2% count-weighted and 47.0% on raw coupons. The three-object confusion is real; the number needs its basis named. | Printing 53.7% unqualified — repeating the basis error being complained about. |
| R3: "40,234 active at window start" | `loan_sample.parquet` gives **40,077** rows with `balance > 0`; 40,234 is the survival count in `attenuation_sensitivity_results.json`. Downstream arithmetic unaffected. | Printing a wrong count. |
| **R4 (this plan's prep): "flip the printed β₁ signs"** | **The panel's fix is wrong.** `eq:beta1` (`.tex:228`) defines β₁ with a leading minus, making it **positive**; `eq:pathB` uses the signed gap, so positive β₁ × negative gap = suppression, self-consistent. `tab:params`' `$0.069$` is correct. `tab:lowband`'s negative column matches the production helper `hazard/literature_hazard.py:32 rothstein_beta1`, which returns `ln(h_shocked/h_base)` *without* that minus. Neither is a computational error. | Flipping signs blind produces a table contradicting the production code with no note explaining why. See Task 4 for the correct fix. |
| R2:M8 (benchmark monthly frequency) | **Not arbitrated** — the synthesizer did not re-derive the $764.7bn benchmark from the weekly SOMA series. Cap arithmetic does check: 3×17.5 + 39×35 = 1,417.5; 1,417.5 − 652.8 = 764.7. | Treat as OPEN, not as an established defect. Task 20 handles it as a check, not a fix. |

---

## Task 0: Build the complete condition inventory

**Files:**
- Read: `REVIEW3_v18_panel_2026-07-29.md` (all seven sections)
- Read: `specs/VERIFIED_R32_prep.md` (this plan's pre-verified findings)
- Create: `specs/INVENTORY_R32_conditions.md`

**Interfaces:**
- Produces: a canonical condition table with IDs `C-xx`, each carrying: raisers, severity, class (WORDING / RUN / CHECK / STRUCTURE / REFERENCE / META), verified status, exact location, and the concrete fix. Every later task references these IDs. The coverage ledger at the end of this file is the checklist.

- [ ] **Step 1: Extract per-reviewer conditions**

Dispatch one opus agent per report section (EIC, R1, R2, R3, DA, Synthesis). Each agent is read-only, must not execute any repo script, and must return one row per *distinct actionable* condition — not a summary. Require each agent to verify its conditions against the manuscript and mark `verified: true|false|partly` with the reason, because a condition on a wrong premise wastes a run.

- [ ] **Step 2: Consolidate and dedupe**

Merge conditions describing the same underlying defect across reviewers into one row listing all raisers (3+ raisers = mark CONSENSUS). Do not merge distinct defects that merely touch the same table. Fold in the Anti-Conditions table above verbatim.

- [ ] **Step 3: Produce the dependency waves and the run inventory**

For each RUN condition record: what is computed, which existing machinery does it, which artifact it writes, which frozen artifact it must not touch, whether its inputs exist in this worktree (S8's inputs did not — `floor_form_offwindow/`, `fannie_quarters/`, `cohort_month_panel_fannie.parquet` are gitignored), and its pre-committed expectation.

- [ ] **Step 4: Commit**

```bash
git add specs/INVENTORY_R32_conditions.md
git commit -m "R32 Task 0: canonical REVIEW3 condition inventory — N distinct conditions (M consensus), anti-conditions folded in, dependency waves and run inventory recorded"
```

---

# WAVE 1 — Required before presenting (no runs; ~3–4 hours)

These four are the union of the five reviewers' pre-talk preconditions. Exact current strings are supplied; all were verified in-session against the manuscript.

## Task 1: Abstract repair (C-R1a/b/c)

**Files:**
- Modify: `paper/v18/revised_paper_v18.tex:31` (abstract) and the same line in `paper/v18/revised_paper_v18_long_abstract.tex`
- Modify: `tools/liveness_gates.py` (gate #99 `ABSTRACT_POSTURE` spans if a pinned span text changes)
- Test: `tests/test_abstract_hedge_gate.py`, `tests/test_headline_posture_gate.py`

**Interfaces:**
- Consumes: nothing.
- Produces: the corrected abstract. Later tasks must not re-touch line 31.

- [ ] **Step 1: Recount the affected literals before editing**

```bash
cd "/Users/eugene/somthing/Lock In effect/Lock-in-Effect/.claude/worktrees/agency-mbs-runoff-qt-424945"
for s in 'it identifies levels only' 'does not identify levels' '85.7\%' '$+2.9$ and $+8.7$' '$+2.9$ to $+8.7$'; do
  printf '%-34s tex:%s\n' "$s" "$(grep -oF "$s" paper/v18/revised_paper_v18.tex | wc -l | tr -d ' ')"
done
```
Expected: `it identifies levels only` 1, `does not identify levels` 1, and-form 2, to-form 8.

- [ ] **Step 2: Fix the self-refuting clause (C-R1a)**

The abstract says the design "identifies levels only" while §V.E says it "does not identify levels." Both cannot stand. The body is right about what the design does: it identifies the *marginal*, and it does not identify levels or monthly timing.

OLD (in the abstract, count 1): `and it identifies levels only.`
NEW: `and it identifies a marginal, not a level and not monthly timing.`

Then verify §V.E's `does not identify levels` sentence still reads consistently, and that no gate span covered the old clause (`grep -n "identifies levels only" tools/liveness_gates.py tests/*.py` must return nothing before you rely on this).

- [ ] **Step 3: Label the mechanical claim as form-conditional (C-R1b)**

The abstract's 85.7% is a **max-form** result. The additive form gives a null of 44.70% standalone / 35.6% shared at the same floor (`hazard/data/floor_form_mixture_results.json`, `cells."4.991|1|0".share_pct = 44.69959732600039`). "Most of that gap was never about behavior" is therefore form-conditional and currently unlabelled — a CRITICAL upheld in arbitration (X6).

Append to the mechanical sentence, inside the same clause, wording to this effect (adjust to fit the sentence's grammar, keep it one clause): `— under the production floor form; under the additive form the same null recovers 35.6\%`. Derive the shared-basis 35.6 from the artifact before printing it; if the derivation does not reproduce, print the standalone 44.7 and label it standalone.

- [ ] **Step 4: Qualify the bounding claim (C-R1c)**

OLD (count 1, byte-exact):
```
The design bounds it between $+2.9$ and $+8.7$ points under its production floor form (the floor read's sampling error at my central elasticity; a wild-cluster interval on 31 clusters; the percentile read under-covers),
```
NEW must (i) keep the interval and its and-form literal, (ii) state that this is the binding layer *among those with a coverage property*, and (iii) name the wider unestimated layer in the same breath. Model it on §V.E's own formulation so the abstract and body agree:
```
The design bounds it between $+2.9$ and $+8.7$ points under its production floor form (the floor read's sampling error at my central elasticity, the widest layer that has a coverage property; a wild-cluster interval on 31 clusters; the percentile read under-covers; the unestimated baseline seasoning ramp spans $+0.9$ to $+15.6$ at the same calibration),
```
`+0.9` / `+15.6` come from `hazard/data/psa_level_sweep_results.json`, `ranges["4.991"] = {lo_pp: 0.856, hi_pp: 15.626}`. Verify both against the artifact and count them in the `.tex` before/after (they are new literals — expect 0→1 each, and check `psa` gate coverage).

- [ ] **Step 5: Re-pin any gate span whose text you changed, in the same commit**

Gate #99's `ABSTRACT_POSTURE["interval"]` pins `The design bounds it between $+2.9$ and $+8.7$ points`. If your NEW keeps that prefix byte-identically, no re-pin is needed — confirm with `python3 -c` substring check, do not assume.

- [ ] **Step 6: Verify the abstract word count and the letter's claim**

```bash
python3 -c "
import re
t=open('paper/v18/revised_paper_v18.tex').read()
t=re.sub(r'(?<!\\\\)%.*','',t)
i=t.find('\\\\begin{abstract}'); j=t.find('\\\\end{abstract}',i+1)
print('abstract words:', len(t[i+len('\\\\begin{abstract}'):j].split()))"
grep -o 'taken it to [0-9]* words' paper/v18/response_to_referees_round22.tex
```
Gate #101 requires these to be equal. If the count moved, update the letter's claim **and** check `tests/test_response_letter_gate.py:99`'s wrong-count list does not now contain the true count.

- [ ] **Step 7: Assert the variant invariant, then run the full stack**

```bash
python3 -c "
a=open('paper/v18/revised_paper_v18.tex').read().split(chr(10))
b=open('paper/v18/revised_paper_v18_long_abstract.tex').read().split(chr(10))
d=[i+1 for i,(x,y) in enumerate(zip(a,b)) if x!=y]
assert len(a)==len(b) and d==[31], d
print('variant invariant OK')"
python3 tools/liveness_gates.py | tail -2
python3 -m pytest tests/ -q | tail -1
```
Expected: `variant invariant OK`, `ALL GATES PASS`, `495 passed`.

- [ ] **Step 8: Rebuild and run the render gate**

```bash
cd paper/v18 && ~/Downloads/texbuild/tectonic --keep-intermediates --outdir build_split revised_paper_v18.tex 2>&1 | grep -ciE '^error|Overfull .vbox'
cd - && python3 tools/render_gate.py | tail -1
```
Expected: `0`, then `ALL RENDER CHECKS PASS`.

- [ ] **Step 9: Commit conditioned on green**

```bash
python3 tools/liveness_gates.py >/dev/null 2>&1 && python3 -m pytest tests/ -q >/dev/null 2>&1 && python3 tools/render_gate.py >/dev/null 2>&1 && git add -A && git commit -m "R32 C-R1: abstract repairs — the self-refuting 'identifies levels only' replaced (the body says the design does not identify levels); the 85.7% mechanical claim labelled as max-form with the additive form's null beside it; the bounding claim qualified as binding-among-layers-with-a-coverage-property with the unestimated PSA ramp's +0.9 to +15.6 span named in the same clause. Gates+tests+render green"
```

## Task 2: Basis-mix repair at `.tex:709` (C-R2)

**Files:**
- Modify: `paper/v18/revised_paper_v18.tex:709` + variant

**Interfaces:**
- Consumes: nothing. Produces: a single-basis comparison.

- [ ] **Step 1: Confirm the defect from the artifact (already verified; reproduce it)**

```bash
python3 -c "
import json; d=json.load(open('hazard/data/floor_form_mixture_results.json'))['cells']
for k in ('4.991|0|6.5','4.991|1|6.5','4.991|0|0','4.991|1|0'): print(k, d[k]['share_pct'])"
```
Expected: `4.991|0|6.5 100.36328284662208` (central, max form, **standalone**), `4.991|1|6.5 55.90661839965657` (central, additive). Because s=0 standalone is 100.36 while the manuscript's shared-basis central is 91.3, `share_pct` is the **standalone** basis.

- [ ] **Step 2: Apply the single-basis repair**

OLD (count 1, byte-exact): `falls from 91.3\% to 55.9\%`
NEW: `falls from 100.4\% to 55.9\% on the standalone scorer`

This is the standalone pairing, quotable directly from the artifact. The mixed sentence read as a 35.4-point fall; the true standalone fall is 44.5 points — the ~9-point understatement of the additive form's level cost that the panel identified. If you prefer the shared basis instead, you must **derive** the shared counterpart of the s=1 cell (the shared basis nets a common $69.6bn curtailment flow from every U.S. leg) — do not print the panel's "46.8" without deriving it; it is not a key in that file.

- [ ] **Step 3: Recount and verify**

```bash
for s in '91.3\%' '100.4\%' '55.9\%'; do printf '%-10s %s\n' "$s" "$(grep -oF "$s" paper/v18/revised_paper_v18.tex | wc -l | tr -d ' ')"; done
grep -rn '91.3' tools/liveness_gates.py | head -3
```
`91.3\%` must remain present elsewhere (it is the correct shared-basis central figure at its own sites) — this edit must reduce its count by exactly 1 and must not touch a gate-pinned instance.

- [ ] **Step 4: Full stack + commit conditioned on green** (same commands as Task 1 Steps 7–9)

```bash
python3 tools/liveness_gates.py >/dev/null 2>&1 && python3 -m pytest tests/ -q >/dev/null 2>&1 && python3 tools/render_gate.py >/dev/null 2>&1 && git add -A && git commit -m "R32 C-R2: basis-mix repair at the additive-form fork — the sentence paired a shared-basis 91.3% with a standalone-basis 55.9%, understating the additive form's level cost by ~9 points; restated on one basis (100.4 -> 55.9 standalone, verified against floor_form_mixture_results.json where share_pct is standalone). Gates+tests+render green"
```

## Task 3: Disclose the floor read's true support (C-DA-C1 / C-R3-support)

**Files:**
- Modify: `paper/v18/revised_paper_v18.tex` — the `tab:oosfloor` caption, the Definitions paragraph, §VII.F's floor-read discussion + variant

**Interfaces:**
- Consumes: nothing. Produces: an accurate sample description behind the headline interval. Task 12 (R5's landing) will quote this support description.

- [ ] **Step 1: Establish the true support from the artifact**

```bash
python3 -c "
import json; d=json.load(open('hazard/data/oos_identification_results.json'))
leg=d['instrument1_oow_floor']['legs']['2018_rising_rate']
print(json.dumps(leg, indent=1)[:1500])"
```
Read the seasoning block and record: the cohort-month counts by age band, the fact that `age[24,36)`, `age[36,60)` and `age[60,inf)` are **empty**, `mature_test_computable: false`, the verdict string `CLEAN_BY_CONSTRUCTION_MATURE_TEST_NOT_COMPUTABLE`, and `ramp_rise_is_psa_confounded: true`. Do not paraphrase from this plan — read the artifact and use its own numbers.

- [ ] **Step 2: Correct the table caption**

`2017--2019 performance` occurs exactly **1** time. For the three rows that set the headline (the 2018 reads), that description is wrong: they are one origination vintage, six 2018 reporting periods, all cohort-months aged 12–24. Narrow the caption to the truth and leave the pooled row's description intact.

- [ ] **Step 3: Add the support sentence at each quoting site**

One sentence, in the author's voice (concise, meaning-dense, hedge scopes load-bearing), stating: the clean leg contains no cohort-month aged ≥24; the mature-seasoning test is therefore not computable rather than passed; and because turnover rises with seasoning — which the paper asserts in both the 100 PSA ramp and the age standardization — the read **understates** the mature book's baseline turnover and therefore **overstates** the marginal, so the error is signed against the headline and unpriced. The paper already prints both corrections that bear on it (age-standardized 5.51%, Fannie 5.52%); say that they agree to 0.01pp and both sit above the clean band's top.

**Do not** delete or weaken the existing "the band's lower edge is the soft one" statement — add the sharper truth beside it.

- [ ] **Step 4: Promote the two corrections into the table (DA-C1 fix (c))**

Add rows to `tab:oosfloor` for the 5.51% age-standardized and 5.52% Fannie reads rather than confining them to a note. Recount every literal in the table and check `tab:oosfloor`'s gate pins (`grep -n "oosfloor" tools/liveness_gates.py`).

- [ ] **Step 5: Full stack + commit conditioned on green**

```bash
python3 tools/liveness_gates.py >/dev/null 2>&1 && python3 -m pytest tests/ -q >/dev/null 2>&1 && python3 tools/render_gate.py >/dev/null 2>&1 && git add -A && git commit -m "R32 C-DA-C1: the headline floor read's true support disclosed — one vintage, six 2018 periods, all cohort-months aged 12-24, zero at >=24, mature test NOT COMPUTABLE (artifact verdict CLEAN_BY_CONSTRUCTION_MATURE_TEST_NOT_COMPUTABLE); the age-transport error stated as signed against the headline and unpriced; tab:oosfloor caption narrowed and the 5.51/5.52 corrections promoted to rows. Gates+tests+render green"
```

## Task 4: β₁ sign harmonisation (C-R4) — read the Anti-Condition first

**Files:**
- Modify: `paper/v18/revised_paper_v18.tex` — `tab:lowband` β₁ column + its tablenote + variant
- Modify: `tools/liveness_gates.py` (new sign-agreement gate)
- Test: `tests/test_beta1_sign_gate.py` (create)

**Interfaces:**
- Consumes: nothing. Produces: gate #109 `beta1_sign_check`.

- [ ] **Step 1: Re-derive the convention yourself (do not trust this plan)**

```bash
grep -n 'label{eq:beta1}' -A 2 paper/v18/revised_paper_v18.tex | cut -c1-160
sed -n '32,46p' hazard/literature_hazard.py
grep -o 'beta_1\$ (central) & \$[^$]*\$' paper/v18/revised_paper_v18.tex
awk 'NR>=395 && NR<=404' paper/v18/revised_paper_v18.tex | cut -c1-60
```
You must conclude: `eq:beta1` carries a **leading minus** so β₁ is positive; `eq:pathB` uses the signed gap so positive β₁ suppresses prepayment; `tab:params` prints `$0.069$` (correct); `rothstein_beta1` returns `ln(h_shocked/h_base)` **without** that minus, hence negative; `tab:lowband` prints the code's convention. Neither is a computational error.

- [ ] **Step 2: Harmonise `tab:lowband` to the manuscript's own definition**

Make the nine β₁ values positive (`$-0.0103$` → `$0.0103$`, and likewise 0.0206, 0.0311, 0.0337, 0.0417, 0.0523, 0.0577, 0.0686, 0.0817). Verified pin exposure: those literals occur in the `.tex` 1,1,1,1,1,1,1,2,1 times and are pinned by **zero** gates and **zero** tests. The `$B` and `pp` columns are untouched. Note `0.0686`'s second occurrence is the prose site, which already prints it **positive** — corroborating that positive is the intended convention.

- [ ] **Step 3: Add the replicator note**

One sentence in the `tab:lowband` tablenote: the column follows `\eqref{eq:beta1}`'s sign convention, and the production helper `rothstein_beta1` returns the same quantity with the opposite sign. This is the honest resolution — it tells a replicator what they will see in the code instead of leaving them to find a contradiction.

- [ ] **Step 4: Write the failing gate test**

```python
# tests/test_beta1_sign_gate.py
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_s = importlib.util.spec_from_file_location("lg", ROOT / "tools" / "liveness_gates.py")
lg = importlib.util.module_from_spec(_s); _s.loader.exec_module(lg)
TEX = (ROOT / "paper" / "v18" / "revised_paper_v18.tex").read_text()


def test_beta1_signs_agree_across_tables():
    ok, info = lg.beta1_sign_check(TEX)
    assert ok, info


def test_gate_catches_a_reintroduced_negative_column():
    mutated = TEX.replace("6.50 & $0.0686$", "6.50 & $-0.0686$", 1)
    assert mutated != TEX, "anchor not found — update the test's anchor"
    ok, _ = lg.beta1_sign_check(mutated)
    assert not ok, "the gate accepted a sign disagreement"
```

- [ ] **Step 5: Run it and watch it fail**

Run: `python3 -m pytest tests/test_beta1_sign_gate.py -q`
Expected: FAIL with `AttributeError: module 'lg' has no attribute 'beta1_sign_check'`.

- [ ] **Step 6: Implement the gate**

Add to `tools/liveness_gates.py` a `beta1_sign_check(tex)` that extracts the `tab:params` central β₁ and every `tab:lowband` β₁ cell and returns `False` if any two disagree in sign, plus its `main()` call and print line in the established style. Wire it as gate #109.

- [ ] **Step 7: Run the tests and the full stack**

Expected: both tests PASS, `ALL GATES PASS` (109 checks now), 497 tests.

- [ ] **Step 8: Commit conditioned on green**

```bash
python3 tools/liveness_gates.py >/dev/null 2>&1 && python3 -m pytest tests/ -q >/dev/null 2>&1 && python3 tools/render_gate.py >/dev/null 2>&1 && git add -A && git commit -m "R32 C-R4: beta_1 sign harmonised to eq:beta1's own definition (tab:lowband column made positive; tab:params was already correct) + a tablenote recording that the production helper rothstein_beta1 returns the opposite sign, so a replicator is not left with a contradiction. NOTE: the panel's proposed 'flip the signs' would have contradicted the production code — derived from eq:beta1, eq:pathB and literature_hazard.py before editing. NEW GATE #109 + 2 tests. Gates+tests+render green"
```

## Task 5: Wave-1 gate — rehearsal artifact for the talk

**Files:**
- Create: `docs/carroll_round_qa_prep.md`

- [ ] **Step 1: Write the three prepared answers**

From the synthesis §6, with the numbers verified yourself: (1) the baseline ramp is a convention, and the null still delivers the majority at 75/100/125/150 PSA (92.8 / 85.7 / 73.3 / 59.3% shared) — lead with that, do not defend +5.6 as a central tendency; (2) the 75k pool is not a sample of the book — own the draw/universe/book-face table before being asked; (3) the floor's support is thin and both corrections sit above the band — concede first, note the composed cell lands at +2.9.

- [ ] **Step 2: Commit**

```bash
git add docs/carroll_round_qa_prep.md && git commit -m "R32 Wave 1 close: Carroll Round Q&A preparation — the three likeliest attacks with verified numbers and the concede-first framing the panel recommends"
```

---

# WAVE 2 — Wording and positioning conditions (no runs)

## Task 6: The inference-ladder selection sentence (C-Z13 / R1-M1)

Quote CR3-BM $[+2.3,+9.6]$ or the WCR inversion $[+2.3,+9.1]$ beside Webb, **or** state in one sentence why the wild bootstrap is preferred to Bell–McCaffrey at $G^*=5.9$ / $h_{\max}=0.33$. Also: delete the Rademacher–Webb near-identity as a *stability* claim (it is a re-printing, not evidence), and note that CR3-BM's upper endpoint is grid-truncated at the 6.0% floor-sweep edge (`truncated_at_grid_edge: true`) so promoting it would require extending the grid. **Respect the Anti-Condition:** Webb is not the narrowest of ten rungs; it is the narrowest with a credible coverage property.

Steps follow the Task 2 pattern: recount → edit → gate/test/render → commit conditioned on green.

## Task 7: Title, framing, and the "mechanical" word (C-X4 / R3-M6)

Two conditions the rename in round 29 did **not** fix: the panel found that "mechanical" is the word carrying the overclaim (not "involuntary", which was renamed). Restate the mechanical/elastic partition so "mechanical" is either defined at first use as *scheduled amortization plus a calibrated baseline turnover floor* or replaced. Separately, retitle to the claim the paper establishes (e.g. "…Redemption-Cap Shortfall", or "Mortgage Lock-In and the Composition of the Federal Reserve's Agency-MBS Runoff") — §III.B's own concession is that a shortfall against the MBS cap is not by itself evidence a stated objective was missed, which the current title's framing outruns.

⚖ **The retitle is Eugene's call** — surface both options with the trade-off before applying.

## Task 8: Missing references (C-Z19)

Add the references the domain and perspective reviewers named, each with one clause saying why it bears on the argument (never a bare citation added to inflate a count). Verify each exists and is correctly described before adding — the repo has a citation-verification convention; follow it.

---

# WAVE 3 — Run-class conditions (spec-before-run, each its own commit)

**Every task in this wave: write and COMMIT the spec first, then run, then land per the pre-committed branch.** A run whose result is unfavourable still lands.

## Task 9: R5 — re-anchor $h_0$ on Path A's estimated seasoning spline

**The single highest-value item in the plan.** It converts the largest disclosed uncertainty layer (the 14.77pp PSA convention span, the panel's second CRITICAL) from a convention into an estimate.

- [ ] **Step 1: Write `specs/SPEC_R32_h0_reanchor.md`** — the anchor (Path A's estimated spline, knots {12,24,36,60,84,120}); how to substitute it for the 100 PSA ramp (`PSA_SPEED` is a **def-time default** — runtime mutation is a silent no-op; patch `lh.baseline_hazard`, per the round-28 finding); the parity gates (the production 100 PSA leg must reproduce bit-identically before the substituted leg is believed); the artifact-overwrite guard (new path, never touch a frozen artifact); the pre-committed expectation with a stated band; and **the landing rule for every branch** — including the branch where the marginal moves against the headline.
- [ ] **Step 2: Commit the spec before running.**
- [ ] **Step 3: Execute (coordinator only). Step 4: Land per branch. Step 5: Gates/tests/render + commit conditioned on green.**

## Task 10: R6 — post-stratify the 75,000 loans onto SOMA coupon × vintage cells

Addresses Z1, upgraded to CRITICAL in arbitration: the estimation population is not the target population on the dimensions that set the answer (2017–19 is 60% of the draw against 6.0% of book face; the 2021 vintage carries 43.9% of book face on 22% of the pool; 2022 absent; all weights 1.0). Under the max form the marginal is zero wherever the baseline sits below the floor, so vintage weighting is censoring geometry, not a composition detail. Reuses `cross_design_reweight` machinery. Also: state the sampler's allocation rule in the appendix (it is currently nowhere in the manuscript) and add the draw's own composition row to the composition table.

Spec first, with the pre-committed expectation and both landing branches.

## Task 11: R7 — two-sided floor transport test

Z4 and Z5 are opposite-signed and both unpriced. Run **both** legs: (a) calendar-standardize the off-window read to the QT window's month mix using `seasonal_floor_timing`'s own normalizer; (b) measure the floor's dependence on housing-activity level and report an activity-matched read. **Running only (a) makes the paper honestly worse off; running only (b) is self-serving. The spec must commit to both before either executes** — this is the plan's clearest anti-gaming checkpoint.

## Task 12: R14 — analytic implied cross-sectional gradient

Recompute at the 4.991% headline floor and under the additive form, at 75/100/125 PSA. Analytic, no engine run. First realized-data evidence bearing on the form fork.

## Task 13: R10 — Ginnie attribution as a window mean

Restate using the window mean rather than the May-2025 snapshot (the one month buyouts dominate): CRR carries 63% of the CPR gap (1.354 of 2.137), CDR 40%. Score a Ginnie leg with the elasticity *attenuated* by the observed CRR differential rather than only share-scaled to zero, and add the assumability upper bound the CRR series supplies.

---

# WAVE 4 — Danish magnitude repair

## Task 14: R9 — re-derive the Danish discount

Z7: every Danish cash figure is ~2× too large because the discount is taken at the representative-coupon state rather than derived from the leg's own realized speed. Re-derive $D$ from the leg's own 5.61% CPR against the window rate path (or matched-coupon TBA marks) and restate every dependent figure. The **sign reversal survives**, so this is a magnitude repair the paper absorbs without changing a conclusion. Also: headline the band $[+61.2, +256.8]$bn in the Table 1 cell (currently the minimum), and add one sentence that the Danish mechanism is an open-market bond repurchase so the par-denominated cap is not the natural scorer.

**Until this lands, do not quote $-\$89$bn / $-\$117.7$bn aloud** (R2's explicit pre-talk instruction).

---

# WAVE 5 — Structural (the largest single scoring deficit)

## Task 15: R11 — paragraph architecture

Writing scored **56**, the lowest dimension, and rounds 28–31 never touched paragraph structure. §V.B is one **2,200-word** paragraph (14,732 chars) in the subsection referees are directed to first. Split §V.B at its five seams — specification / floor semantics / elasticity import and its three transports / aggregation bounds / ablations — move the competing-risks taxonomy to the appendix, split §V.E's and Appendix G's monoliths, and fold §VI.C into §VI.B.

**This is mechanical and costs no content**, but it renumbers nothing and must not move a single literal: assert the full pinned-span census (all 635 gate/test-pinned strings) survives byte-identically, exactly as the round-31 render repair did. Use `tools/render_fix_r31.py`'s verification pattern: ast-sweep every string constant in `tools/liveness_gates.py` + `tests/*.py` that is a substring of the old `.tex` and assert it is still a substring of the new.

---

# WAVE 6 — Policy exhibits (highest-value contribution, currently underbuilt)

## Task 16: R12 — the marginal in transaction counts

Report the marginal in transaction counts with the moving-share bracket applied, set against realized mortgage-financed transaction volume, and **state the verdict whichever way it falls**. This is the paper's first outcome-side external check and the only unit in which the household leg becomes commensurable with the institutional one.

## Task 17: R13 — rebuild §VI.B around a deliverable

Z14: the cap-design arithmetic is the paper's most exportable contribution and is currently stated without an objective function. Rebuild around the achievable-path band in \$bn/month (≈\$16–18bn/month, ±≈\$4bn from the floor read's own interval), a two-input table (book OTM share × turnover-floor band → implied cap), and an explicit statement of the objective a cap serves.

---

# CLOSE

## Task 18: Full verification and derived-artifact refresh

- [ ] Rebuild canonical + variant; assert 0 errors, 0 overfull vbox, 0 undefined refs.
- [ ] `python3 tools/render_gate.py` → ALL RENDER CHECKS PASS on all four PDFs.
- [ ] Recompute the two-PDF split from the fresh `.aux` (the appendix start page will have moved) and recut with pypdf.
- [ ] Regenerate md/txt editions (`tools/editions/tex2md.py` then `md2txt.py`); the self-checks must hold (tables/figures/equations/footnotes/headings) — update the WANT counts only if the content genuinely changed, and say so.
- [ ] Refresh the UPLOAD bundle and write its notes, including any page-count change and why.
- [ ] Full gates + tests.

## Task 19: Coverage ledger — prove every condition is addressed

- [ ] For every `C-xx` in `specs/INVENTORY_R32_conditions.md`, record: SATISFIED (with the commit that did it), INFEASIBLE (with the specific reason and the honest alternative that landed instead), ANTI-CONDITION (not acted on, with why), or DEFERRED (with whose decision it awaits). **No condition may be left unclassified.** Append to `PLAN_review2_fixes_2026-07-28.md`'s execution log and update the memory files.

## Task 20: Open items requiring Eugene

- [ ] R2:M8 (benchmark monthly frequency) — unarbitrated; run the check, do not assume the defect.
- [ ] The retitle (Task 7) — his call.
- [ ] R16 submission mechanics: anonymized master, archived DOI (Zenodo) replacing the GitHub URL, the Appendix O sentence stating the gate suite's domain.
- [ ] The **Freddie loan-level redistribution** question — two auditors independently rated the public `hazard/data/loan_sample.parquet` (75,000 real loan records) CRITICAL. This is a licensing judgment, not a technical fix, and it needs history rewriting if it is a problem. **Do not act unilaterally.**
- [ ] Push.

---

## Self-Review

**Spec coverage:** Wave 1 covers the four pre-talk conditions (R1–R4) with verified exact strings. Waves 2–6 cover synthesis roadmap R5–R16. Task 0 exists precisely because the roadmap is *not* the full condition set — each reviewer raised conditions the synthesis did not promote, and Task 19's ledger is what proves none was dropped. The four arbitration-upgraded CRITICALs map to: X6→Task 1 Step 3, DA-C1→Task 3, DA-C2/X1→Task 9, Z1→Task 10.

**Placeholder scan:** Wave 1 carries byte-exact OLD strings and complete replacement text. Waves 3–6 deliberately specify the *spec* as the deliverable rather than pre-writing run results — pre-writing a number a run has not produced would violate anti-gaming rule 3. Every task names exact files and exact verification commands.

**Type consistency:** `beta1_sign_check(tex) -> (bool, dict)` matches the existing gate-function convention (`floor_ladder_check`, `wal_normal_turnover_check`) and is consumed by `tests/test_beta1_sign_gate.py` as defined.
