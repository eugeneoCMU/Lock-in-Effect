# Plan — remaining work after round 22 — 2026-07-26

State: `panel-revision-2026-07-18`, 37 local commits unpushed. **90 gates PASS, 297 tests, 113pp, 0 undefined refs.**

> **STATUS 2026-07-26 (final): EVERYTHING EXECUTED EXCEPT THE PUSH.**
> §1 the gap — closed (`bootstrap_pathb_cluster`, T1, [+4.63,+6.92]pp; the committed
> within-stratum scheme had understated loan sampling ~37×). §2 four free wins — landed.
> §3a B4 — executed under a **second** pre-commitment (T1, production spec, 12.66% vs 12.18%);
> the failed tolerance was never widened. §3b venue — resolved, short abstract now canonical
> at 424 words. §3e Berger locators — **verified against the source; one was wrong and is fixed**.
> §6 bookkeeping — done, both PDFs rebuilt. §6e response letter — drafted, 5pp.
> **§3c the push — DONE** (2026-07-26, 46 commits to `origin/panel-revision-2026-07-18`; `main` untouched).
> **Nothing outstanding.** 91 gates, 297 tests, 113pp, clean tree.

**DECISION RECORDED: page compression is abandoned.** The 55–65pp target from
`HANDOFF_round21_referee.md:65` is withdrawn at Eugene's instruction. Nothing below
optimises for length. Three previously-listed items die with it: the V.B section
split, the Path A footprint reduction (its *honesty* half is already done — the sign
claims are retracted), and the `tab:headline` row trim. The hedge-repetition item
survives only where a hedge is *wrong*, not where it is repetitive.

---

## 1. THE GAP — stratum-cluster bootstrap on Path B (item B5)

The one remaining analytical hole. Everything else below is disclosure or bookkeeping.

### What is actually wrong

`hazard/bootstrap_pathb.py:63` resamples loans **within** each stratum and preserves
each stratum's size, so between-stratum sampling variance is **never drawn**. That is
why the interval is degenerate — marginal sd **0.0164pp**, CI [9.1664, 9.2286] — and
why the paper can say the loan draw "contributes essentially no uncertainty." The
claim is true of the scheme that was run and says nothing about the scheme that
matters. The repo already has cluster resampling (`hazard/bootstrap_se.py`), applied
to Path A and never to Path B.

### The design question that has to be settled BEFORE writing the script

The 130 strata are **violently unequal**: min 1 loan, median 136, **max 6,076** — one
cluster is 8.1% of the 75,000-loan sample. Two consequences:

1. **A textbook cluster bootstrap resamples 130 clusters with replacement, so total
   loan count varies run to run.** Before committing a spec I must establish whether
   that breaks the scorer. `microsim_engine.py:56-62` recomputes
   `scale = WSHOMCB_t / pool_exposure_t` every month, so the loan sample may be a
   *shape* input whose level is normalised away. **If it is, a naive cluster
   bootstrap would absorb exactly the variance it is meant to measure and produce a
   second falsely-tight interval.** This is the single thing most likely to make the
   run worthless, and it is checkable offline in minutes.
2. **Effective cluster count is far below 130.** With one 8.1% cluster, the interval
   should be reported alongside an effective-cluster count and the leverage of the
   largest stratum, or a referee will read "130 clusters" as more information than it is.

### Pre-committed threshold (fix before running, not after)

The consequential outcome is whether the cluster interval **exceeds the floor-read
cluster bootstrap's [+2.97, +8.02]pp**. `tab:uncertainty` (L509) currently labels that
floor-read layer **"the binding layer."** If loan/stratum sampling is wider, that label
is wrong and moves — a headline-adjacent change. Branches to declare ex ante:
- **T1** cluster interval materially narrower than [+2.97, +8.02] → floor read stays binding; L509 unchanged; the degenerate within-stratum claim is replaced by a real one.
- **T2** comparable (overlapping, neither dominating) → both layers reported, "the binding layer" retired for a two-layer statement.
- **T3** cluster interval wider → the binding layer is loan/stratum sampling, L509 and `tab:uncertainty`'s caption move, and the abstract's uncertainty sentence must be re-checked.

### Steps

| # | Step | Cost |
|---|---|---|
| 1 | Offline: determine whether WSHOMCB rescaling neutralises variable loan count. Decide fixed-N vs variable-N resampling on the answer. | 20 min, no run |
| 2 | Report effective cluster count and max-stratum leverage from `loan_sample.parquet`. | 10 min, no run |
| 3 | Write `hazard/bootstrap_pathb_cluster.py`, mirroring `bootstrap_se.py`'s documented design. Parity gate G1 must replay the committed within-stratum percentiles bit-exactly before anything new is reported. | 1–2 h |
| 4 | **Commit the spec** (spec-before-run; non-negotiable given round-22 C1). | — |
| 5 | Run at the **4.991% headline floor first** (~73 min for 200 reps × 2 legs, from the committed `runtime_s 4368.2`). Add the 4.0% in-sample floor only if step 5 lands. | 73 min / +73 min |
| 6 | Land in tex: L351, `tab:uncertainty` rows 507/509/511 and its caption at L499 ("Sampling intervals are the stratified loan-level bootstrap's…"), plus whichever branch fired. | 1 h |
| 7 | New gate pinning artifact + parity + the branch verdict, mutation-tested. | 30 min |

**Risk:** unlike B4 this run is loan-sample-driven, not FRED-driven, so it is not
exposed to the upstream-revision drift that halted the scale test. The real risk is
step 1's answer.

---

## 2. FREE WINS — measured in round 22, not yet in the paper

These need **no runs**. The numbers already sit in committed artifacts.

| Item | What | Where |
|---|---|---|
| **2a** | The **frozen cross-design variant's floor lands at 7.0–7.3% on every one of 50 seeds** — outside the observed 4–5% involuntary band. The paper's own admissibility logic (VII.D) is what makes this matter, and it currently appears in no table. | `cross_design_seeds_results.json` → VII.D |
| **2b** | The **"frozen" mobility scale is itself seed-variable** when re-derived: mean 43,493, sd 1,181, min 39,984 against the committed 43,882.8, which sits at the *top* of its own range. "Frozen" is doing less work than the label implies. | same artifact → VII.D |
| **2c** | **The Danish refi sweep produces negative trapped balances** at contributions ≥12% CPR: −\$14.4B, −\$158.0B, −\$290.0B. A negative trapped balance is not economically meaningful, and this is the same sweep whose ceiling I corrected in Figure 5's caption. The upper half of that x-axis should be marked as non-interpretable, which further weakens any reading of the ceiling. | `danish_us_intercept_results.json` → `fig:gapsweep` caption + IV.C |
| **2d** | **Per-seed floor CPR disclosure** — round-21 R10 item, now available for free from the 50-seed sweep (recalibrated floors 4.77–4.90%, all inside [4,5]). | → VII.D |

**2c is the one I would not leave out.** It is visible in a committed artifact, it is
in the section a Carroll Round discussant would open first, and it is adjacent to a
caption that was already wrong once.

---

## 3. EUGENE-ONLY DECISIONS — blocked on you, not on me

| # | Decision | Context |
|---|---|---|
| **3a** | **B4 re-anchoring.** `production_scale_test` halted at its pre-committed \$0.05B parity tier: uniform \$0.136B offset across all 50 seeds from FRED revision (median home value 403,200→410,700). The scale test compares two *arms* on the same fresh frame, so arm A could be re-anchored to a fresh baseline with the offset disclosed. Defensible — but it is a post-hoc change to a pre-committed acceptance rule, which is exactly what round-22 C1 retracts elsewhere. **I will not make this call.** Diagnosed in TECHNICAL.md §29. | If yes: ~30 min run |
| **3b** | **Venue.** Still open from round 17. It determines whether the 573-word abstract is acceptable. A gate-clean 324-word variant now exists and passes all nine hedge spans (`revised_paper_v18_simple_abstract.tex`). Not a compression question — a submission-requirement question. | — |
| **3c** | **Push.** 24 commits sit local on a public repo. Nothing has been pushed. | — |
| ~~3d~~ | ~~FRED key rotation~~ **CLOSED 2026-07-10**, not open — TECHNICAL.md:1562-1566 records the rotation: the key hard-coded in early public history was rotated and the old one is issuer-deactivated (FRED returns 400), so historical copies are inert; the replacement appears in zero tracked files and zero commits and lives only in the untracked, gitignored `.env`. Verified this session: `.env` was never committed. | none |
| **3e** | **Confirm the Berger section locators.** Round 22 promoted `\S3.3.1`, `\S4.9.1` and `tab.~3` into the manuscript from the replication package's own code comments (`common/berger_calibration.py:9-10`, `TECHNICAL.md:1340`). I cannot open the SSRN draft, so if those numbers are wrong they are now wrong in the paper. Not a decision — a two-minute check only you can do. | 2 min |

---

## 4. ROUND-21 R10 LEFTOVERS — never executed

From `HANDOFF_round21_referee.md:62-64`. Status after round 22:

- ~~production-spec scale rerun~~ → attempted, halted (3a above).
- ~~β_B interaction bound~~ → **superseded**: round-22 A9 ran the real β_B=0 ablation at both floors and reported the marginal's burnout-sensitivity (+0.74/+0.94pp).
- ~~per-seed floor CPR disclosure~~ → **now free** (2d above).
- **settlement-months benchmark variant** — still open. Not started, no script.
- **DTI non-monotonicity decomposition** — still open. Not started, no script.

Both survivors are genuine but second-order: neither touches a headline quantity.
I would do them only after §1 and §2.

---

## 5. KNOWN INCOMPLETENESS I AM CHOOSING TO LEAVE — stated, not hidden

- **The concave × additive hull is not shown complete.** Round-22 B1 ran the joint cell at the *central* elasticity only; its {5.5, 7.7} band ends are unrun. The tex says so. Closing it is ~3 min of runtime and would let "not contradicted" become "complete." Cheap; low value; listed for honesty.
- **Path A still occupies three of the first seven tables** for a non-headline exhibit whose interval spans zero. With compression abandoned this is no longer a page question, and the honesty half is done. Leaving it.

---

## 6. BOOKKEEPING GAPS FOUND ON A SECOND PASS — none of this is analysis, all of it is visible to a referee

| # | Gap | Why it matters |
|---|---|---|
| **6a** | **`tab:runindex` is missing 12 runs.** It lists 23 and omits every round-21 run (`floor_form_offwindow`, `concave_marginal`, `danish_offwindow_floor`, `ginnie_overlay_offwindow`, `floor_uncertainty`, `patha_sign_test`, `episode_confrontation`, `cross_design_reweight`) and every round-22 run (`concave_additive_marginal`, `burnout_ablation`, `cross_design_seeds`, `production_scale_test`). Its caption claims completeness: "Each row names a committed run cited in the main text by its result; tags are collected here rather than in the narrative." | This is the reproducibility ledger a referee opens to check the pre-commitment architecture. Four of the twelve are mine. **Largest item in this section.** |
| **6b** | **`TECHNICAL.md` has no record for 3 of the 4 round-22 runs** (only `production_scale_test`, via §29 on the halt). The convention is one record per run, and TECHNICAL.md carries the 75 commit-hash citations that make the pre-commitment claim checkable. | Same architecture, same referee. |
| **6c** | **The canonical PDF is stale.** `paper/v18/revised_paper_v18.pdf` is dated Jul 20 at 106pp; round 22 built to `build_r22/` at 112pp. `revised_paper_v18_simple_abstract.pdf` is staler still — I rewrote that abstract and never rebuilt it. | Anyone opening the repo reads the pre-round-22 paper. |
| **6d** | **Stale counts in the handoffs.** `HANDOFF_round21_referee.md` still says 80 gates / 106pp. `HANDOFF_concision_round.md` says 72 gates, is untracked, and is now moot. | Cheap; misleads the next session. |
| **6e** | **No response-to-referees letter.** Rounds 18 and 19 each produced one (`paper/v16/response_to_referees_roundNN.tex`). None exists for this round. | Much easier to write now than later — especially the awkward parts, where the critique's premises were **stale or wrong** (items 1a/1b, 5d, 10, 12b/12c, 15) and need answering without sounding dismissive. |
| **6f** | **Eleven untracked paths** need a deliberate track-or-ignore call: eight run subdirectories of intermediate parquets, three `patha_sign_test_*.csv`, and `HANDOFF_concision_round.md`. The standing rule is that derived files stay ignored, but they are currently just dangling rather than ignored. | Low risk, but "paper/ was gitignored until today" is how the 101pp source was lost once. |

**Also, not a gap but a likely blocker:** the canonical abstract is **573 words**. Most
journals cap at 100–250. That is a submission requirement rather than a style question,
so it survives the decision to abandon compression — the gate-clean 324-word variant
exists precisely for this, and it is still short of a 250-word cap.

## Suggested order

1. **§1 step 1** — the WSHOMCB question. It decides whether the gap is closable at all, costs 20 minutes, and needs no run.
2. **§2** — all four free wins, one commit, no runs. Highest value per minute in this plan.
3. **§6a + §6b + §6c** — run index, TECHNICAL records, rebuild both PDFs. Mechanical, ~1h total, and 6a is the one a referee actually opens.
4. **§1 steps 3–7** — the cluster bootstrap.
5. **§6e** — the response letter, while the reasoning is still fresh.
6. **§4 survivors** and **§6d/§6f**, if you want them.

§2 and §6 do not depend on §1, so if the WSHOMCB answer is bad, both still land.

---

## 7. FINDINGS FROM THE POST-ROUND-22 STANDING REVIEW (2026-07-26)

A fresh adversarial read of the whole manuscript, run after round 22 closed. One
item was fixed immediately; the rest are open and are listed in the order a
hostile discussant would raise them.

| # | Finding | Status |
|---|---|---|
| **7a** | **Abstract dropped the binding sampling layer.** L473 requires the hull and the `[+3.0, +8.0]` sampling interval be quoted together; the short-abstract swap kept only the hull. My regression, introduced the same day. | **FIXED** (commit `0eef701`) |
| ~~7b~~ **DONE** | **The anchor defect generalises.** Only 2 of 18 scripts touching a Danish leg call `set_danish_moving_anchor`; the rest run at the `dk_level` default. Most are engine modules where the caller sets it — correct design. But `curtailment_danish_scaling.py` produces a committed artifact behind the manuscript's "+\$0.77 billion, immaterial" curtailment-differential claim (L727, L731), and it ran the **bracketing** leg. Direction almost certainly flips: under `dk_level` the Danish leg is *slower* (3.39% vs 4.76%) so retains higher balances and higher curtailment; under production `us_intercept` it is *faster* (5.61%), so the differential should be negative. **This is the same defect class as round-22 A2 (`tab:discount`) — I found one instance and did not generalise.** | **OPEN — needs a re-run under `us_intercept`** |
| ~~7c~~ **DONE** | **The par-crediting disclosure sits in one section only.** Round 22 established that the Danish leg credits ~\$470B of retired balance at par against a 32–34% discount, an un-priced channel larger than the gap and signed against it. It appears in V.B. It does **not** appear in VII.D, `tab:danish`, `fig:gapsweep`, `tab:headline`, the limitations, or the conclusion — and the abstract still says the institutional cash-flow cost is "small" without it. | **OPEN — prose propagation, no run** |
| ~~7d~~ **DONE** | **The floor was never re-read on Fannie data.** The binding parameter rests on 31 Freddie clusters of 2018 turnover, with the mature-age seasoning test not computable and an age-standardised read above the clean band (84% imputed weight). 826M Fannie loan-months spanning 2017Q1–2022Q4 are already staged in the identical layout, and the replication holds the floor **fixed**. The manuscript never raises re-reading it there. The reviewer's likely opener, and there is no feasibility defence. | **OPEN — one run on staged data** |
| ~~7e~~ **DONE** | **Recovery percentages cannot compound error.** The engine renormalises the pool to actual WSHOMCB holdings monthly, so every recovery figure is effectively a window-mean-CPR statement, not a balance-path fit. Disclosed only as a parenthetical at L351. Round-22 B6 made the affine relation explicit; this is the sharper version of the same point and belongs beside it. | **OPEN — one sentence** |
| ~~7f~~ **DONE** | **The calibration box carries no statistical content.** The 5.5–7.7% band is Liebersohn–Rothstein's *specification* range and 6.5% is an adopted midpoint, not a published point estimate; their standard error is propagated nowhere. The box is nonetheless set against the bootstrap CI and called "the operative uncertainty", which invites reading it as an interval. Disclosed in a footnote, over-read in the tables. | **OPEN — framing** |

**ALL OF 7a-7f ARE NOW DONE** (2026-07-26). 7d returned T2 — the Fannie read at 5.522% sits above the clean band and
corroborates the age-standardised hedge from an independent book. 7b reversed the curtailment differential's sign to
-$1.68B and the "immaterial" claim is withdrawn. 7c/7e/7f landed as prose. Gates #86 and #87 added.

One defect found while doing them and worth recording: a mutation test earlier the same day left the string
"The mobility cost is substantial." in the canonical abstract (commit `1b17deb` carried it in from the mutated
variant), an unintended strengthening of "real". Removed. Mutation tests must be reverted in the file they were
applied to, and the revert re-verified, not assumed.
