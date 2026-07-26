# Plan — remaining work after round 22 — 2026-07-26

State: `panel-revision-2026-07-18`, 24 local commits unpushed. **89 gates PASS, 297 tests, 112pp, 0 undefined refs.**

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
| **3d** | **FRED key rotation** — outstanding since round 14, and round 22 used the key in `.env`. | — |

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

## Suggested order

1. **§1 step 1** — the WSHOMCB question. It decides whether the gap is closable at all, costs 20 minutes, and needs no run.
2. **§2** — all four free wins, one commit, no runs. Highest value per minute in this plan.
3. **§1 steps 3–7** — the cluster bootstrap.
4. **§4 survivors**, if you want them.

§2 does not depend on §1, so if the WSHOMCB answer is bad, §2 still lands.
