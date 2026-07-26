# Revision roadmap — round 22 (referee critique triage) — 2026-07-25
## STATUS 2026-07-26: EXECUTED. 23 commits. 89 gates PASS, 297 tests, 112pp, 0 undefined refs.

**Done:** all 14 Tier-A items; B1 (run, gate #81), B2, B3 (run, gate #83), B6;
C1 (gate-hardened + mutation-tested), C2, C4 (gate); A9 (run, gate #82); item 13;
item 15 confirmed already fixed; item 16 scoped at five sites; 6a; 12a; 12d;
5b/5d/5e residuals; the four mis-pointed Fannie refs.

**Blocked, recorded not worked around:** B4 (`production_scale_test`) halted at
its pre-committed $0.05B parity tier — a uniform $0.136B offset across all fifty
seeds from FRED revision, diagnosed in TECHNICAL.md §29. The manuscript's scale
claim was scoped *before* the run precisely so it is correct either way. Re-anchoring
arm A to a fresh baseline is defensible but is a post-hoc change to a pre-committed
rule, so it is left as an explicit amendment for Eugene.

**Not started:** B5 (stratum-cluster bootstrap on Path B, ~2.5h, no script yet) —
the last genuine analytical gap. Editorial: 3d hedge compression, 5g Path A
footprint, Tier-E relocations, 9c abstract length (venue decision).

**Note the page count moved 106 → 112.** Every added page is disclosure
(un-priced Danish channel, additive level cost, seed bands, spec labels,
provenance). If the 55–65pp target is live, the compression pass now has more to
do, and `HANDOFF_concision_round.md:46-48` still applies: ~40% of last round's
compression rewrites strengthened claims past their evidence while passing gates.

---


Manuscript: `paper/v18/revised_paper_v18.tex` (1,243 lines, 48,675 words, **106pp** per `paper/v18/build_r21/revised_paper_v18.log`).
Baseline verified this session: **80/80 liveness gates PASS**, **295 tests pass**. One uncommitted change (the abstract, line 30).

## Headline: the critique is substantially stale — but the audit found worse

The 16-item critique was written against a pre-round-21 draft. Round 21 already discharged much of it,
including the item it called fatal. What the verification pass found instead is a **fourteen-item
accuracy batch (Tier A below), most of which the critique never raised, and much of which no gate can
catch** — because the gates pin numeric literals and pinned phrases, while these defects live in
captions, in omitted artifact summaries, and in claims about *magnitudes* rather than values.

Two defects and the baseline were verified directly, not via subagent:

| # | Defect | Verified |
|---|---|---|
| A1 | `fig:gapsweep` caption (L619) asserts both anchors stay "an order of magnitude below the superseded \$925.5 billion extrapolation across the entire sweep". L614, five lines earlier, says the sweep rises "to $+\$1{,}038.9$ billion at the ceiling". Artifact `danish_us_intercept_results.json` `sweep[6] = 1038.918`. The caption is false and self-contradicted by the body. No gate references `925.5`, `order of magnitude`, or `entire sweep`. | **direct** |
| A2 | `tab:discount` caption (L332) and L328 call the tested leg "The production (Berger-recalibrated) Danish leg". `hazard/danish_discount_bound.py` contains **zero** calls to `set_danish_moving_anchor`, so it ran at the module default `dk_level` (`common/berger_calibration.py:76`). Its artifact records `mean_danish_cpr_pct = 3.3856` and `danish_trapped_standalone_b = 934.25` — the *bracketing* leg. The paper asserts a verified sensitivity on a leg the run did not execute, then extends it to "the production $+\$61.2$ billion gap". | **direct** |
| A3 | Baseline green state (80 gates / 295 tests / 106pp) — so every defect below coexists with a fully green suite. | **direct** |

### What the critique got right, wrong, and stale

- **Already addressed (do not spend time):** items 1a, 1b, 1d, 5a, 5c, 5f, 7, 8, 9a, 9b, 10, 11, 12c, 15, and Tier-3 (c) and (f). Item 10's welfare sentence is gone and *replaced by the critique's own argument* at L598: "I do not translate the \$764.7 billion shortfall into welfare terms: it is an accounting gap against a cap schedule, mostly mechanical by the decomposition above, and neither a lower nor an upper bound on the welfare cost of the par-payoff rule." Item 12c's "within 2.1\%" survives only inside the named-retractions list at L936.
- **Premise false:** 12b (97.9→89.3 is the *demoted* in-sample pair; the live pair is off-window 84.0/79.5), 15 (`tab:specbox`'s Path B cell already names the in-window floor), Tier-3 (a)'s Fannie half (`sec:pathb-fannie` has been its own subsection since v17).
- **Item 1 (the "fatal" Danish item): the constructive fix already landed.** `hazard/danish_us_intercept.py` runs exactly the transplant the critique prescribes — `prepay_hazard(..., np.zeros_like(rate_gap), ...)` with the floor retained — and lands at 5.6136% mean Danish CPR, hitting the critique's own predicted "~6% CPR" target, flipping the gap to $+\$61.2$B in-sample and $+\$28.2$B at the headline floor. It is production. The floor violation is disclosed at four sites.
- **Item 1b's numbers are right but its inference is wrong.** The rule-only Danish leg *is* numerically the β₁=0 null (null $748.185$B vs us_intercept $748.181$B; max monthly CPR difference 0.000107pp). That is not a missing mechanism — it is forced arithmetic, and it is precisely what item 1a's fix demands. The paper already says so at L614 ("one object measured on two accounting legs").
- **Item 5d's premise is wrong in the way that matters least.** The abstract's 97.9% is *Path B's* in-sample recovery, not Path A's. But 112.4% (Path A) does still sit in **Section I at L51**, and L51 carries both endpoints in adjacent sentences on the same basis, so a Section I reader reconstitutes the banned range without the paper printing a dash. The live fix is the verb, not the number: strike "corroborates".

---

## Tier A — accuracy and honesty defects. All prose. No runs. Do these first.

Ordered by how badly a discussant could use them.

| id | Site | Defect | Fix | Gate cost |
|---|---|---|---|---|
| **A1** | L619 caption | False magnitude claim (above). Both sweep endpoints exceed \$925.5B: us_intercept $+\$1{,}038.9$B, dk_level $+\$972.0$B. Only the refi=0 points support it. | Delete the clause or restate: positivity holds across the sweep; the magnitude claim holds only at low refinance contributions, and the ceiling *exceeds* the superseded extrapolation. | none |
| **A2** | L328, L332 | Discount table ran the bracketing leg, labelled production (above). | Relabel to "The Danish-level Berger-recalibrated leg on which the diagnostic executed (mean CPR 3.39\%)", and state that the production U.S.-intercept leg's PV-independence is *structural* (it zeroes the gap before the hazard is evaluated, `competing_risks.py:150`) rather than run-verified. | none — gates #47/#51 pin only flip-count literals and `25--150 bp` |
| **A3** | L399/L424 | **Selective reporting.** `bootstrap_resimulate_results.json` gives `trapped_b.mean = 598.85` = **78.3% of benchmark** — below the paper's own β₁=0 null (85.7%) and below Path B's headline (91.3%). The tex prints the median (922.6 = 120.6%), the IQR, the CI, and "83.8\% of draws land above the benchmark" — every favourable summary — and omits the one that reverses the reading. Share-basis CI $[-583.2\%, +155.6\%]$ also unreported. Inconsistent with the paper's own stated standard 40 lines earlier at L424, where mean/median/bias are reported *because* the distributions are right-skewed. | Report the mean and the share-basis interval alongside the median. | none; add one |
| **A4** | L582 | Stale spec-v3 literal: "nearly \$150 billion" is the v3 Path A error (+\$150.3B). Under production spec v4 the same paper prints \$928.9B and +\$164.1B. Understates its own committed figure by \$14B and contradicts L1193 and `tab:estimators`. Survives v16→v17→v18, ungated. | Replace with \$164.1 billion (or \$94.6B if the sentence is meant to be shared-basis). | none; gate it off `theil_data.json` so it cannot rot again |
| **A5** | L473 | Stale and now false: says the concave-gap variant "was run only in window". Round 21's `concave_marginal` ran a concave central *and* null at the 4.991% off-window floor, and `tab:uncertainty` (L509) already quotes it as "concave transform $+5.1$". L473 contradicts L509 on the same manuscript. | Repair the floor clause before appending anything to this sentence. | none |
| **A6** | L473 | Logical defect: "only the form-conditional range $+3.9$ to $+13.1$ points is defensible" states a lower bound **0.9pp above** the layer the paper itself calls binding — `floor_uncertainty`'s $[+2.97, +8.02]$pp, labelled "the binding layer" at L509. The stated identified range is not a superset of the paper's own disclosed uncertainty. | Re-state the hull so its lower end is not narrower than the binding sampling layer, or say explicitly that the hull is conditional on the floor read being taken at its point estimate. | gate #69 pins the hull to 1e-9 and needs `$+3.9$ to $+13.1$` at ≥3 of 5 sites — moving the hull is a tex+gates+tests commit |
| **A7** | L316 | Internal contradiction. `concave_marginal`'s G3 shows the concave null is bit-identical to the production null, so the level delta and the marginal delta **are the same number**: $-1.3243$pp. L316 calls that immaterial for the level and, forty words later, material for the marginal, invoking "the same $\pm 1$-point materiality threshold". Defensible only on a relative reading (1.2% of recovery vs 14% of the marginal) that the tex never states. Gate #70 now pins the inconsistent claim. | State the relative convention explicitly, or drop the shared-threshold appeal. | gate #70 pins `$+7.87$`/`$+5.06$`/`not load-bearing for the level` |
| **A8** | L441–444 | `tab:pathadiag` — the table the prose designates as the collection point ("collects Path A's diagnostics in one place", L429) — silently interleaves **spec v4 / v3 / v3 / v4** with no label in caption, rows, or note. Row 442's spec-v3 point (\$915.067B) is never shown, so a reader reads median 922.6 as centred on the 928.9 printed one row above. `tab:bootstrap` *does* carry the label (L406). | Add the spec label per row. | none |
| **A9** | L584, L588, L899 | **The burnout ablation has no provenance.** \$6.6B / $-0.9$pp / 106.2% has no committed artifact, no `TECHNICAL.md` run record, no script, and no gate. `hazard/config.py:55` sets `beta_burnout=-0.5` and nothing overrides it to 0. The only file in the repo containing the implied values (811.9116, 106.1672) is **one replicate row of `permutation_test_ablate_orig`** — an unrelated experiment. Either the number was read off the wrong object or it came from an uncommitted run. It is one of three magnitudes the mechanism-scoping rests on. | Re-run it properly: ~40-line `hazard/burnout_ablation.py` calling `run_qt_microsim` with `beta_burnout=0.0`, or a fourth scenario in `covariate_priors_estimation.py` (scaffold at PRIORS L57, `coef_override` L116). **~2 minutes.** Then restate the literals from the artifact. | additive gate; nothing currently pins 6.6/0.9/106.2 |
| **A10** | L45, L74, L614, L619, L635, L643, L725, L901 | The Danish-level $-\$99.9$B/$-\$100$B number appears at 8 sites, including the **Introduction** and the **Conclusion**, without the floor-violation caveat. Only L942 (ledger) and L649 (no number) carry it. | Attach a short caveat clause at the intro and conclusion sites at minimum. | `abstract_leads_with_flip` compares `find()` positions of two substrings and survives insertion between them |
| **A11** | L140 | **The Danish leg credits retired balance at par.** Every Danish dynamic-balance loop books `rolloff = bal * monthly_drain` with no buyback-price term (`abm/fed_mbs_extension_risk.py:912, 996, 1072, 1104, 1135`), so a Danish borrower extinguishing below-par debt still returns 100 cents of Fed cash. Using the paper's *own* pricing proxy at its own representative state the discount is 33.2% at a 3.0% coupon against 6.8% market; committed Danish roll-off is \$669.3B. Even at a conservative quarter-discount on half the roll-off, market-price crediting removes **~\$84B — larger than the entire $+\$61.2$B gap, and signed against it.** `TECHNICAL.md:114` documents the mechanism as "debt retired at discount", so the code contradicts the project's own documentation. Nothing in the tex discloses it. | Minimum honest fix, prose only: add a third qualification at L140 stating the par-crediting, its direction, and the one-sided magnitude. Full fix is a pre-committed `danish_market_price_credit` variant — that is what would make `tab:discount` real, and it is **large** (trips gates #66, #71, #44). | prose fix: none |
| **A12** | L30 | **Regression in the uncommitted edit.** `git diff` shows it deletes "an input-stability check rather than an outcome holdout". The abstract now has zero occurrences of holdout / nineteen / input-stability. Round 21's "all 4 sites incl. abstract" is now 3. `ABSTRACT_HEDGES` has no holdout entry, so no gate catches it. | Restore the clause, or drop the 4th site knowingly. Add an `ABSTRACT_HEDGES` entry. | none currently — that is the problem |
| **A13** | L582 | The bare 59.3% at the paper's own concession paragraph lacks the 76.3% book-composition companion that every other headline site carries. It *understates* the concession: at book composition the variant lands within 24% of the benchmark, not 45%, so the "within 45\%" framing is stale. | Add the companion. | gate #76 needs `76.3\%` ≥4; currently 5 |
| **A14** | L98 | Citation trail. `berger2026` is credited at L98 with having "demonstrated" that Danish mobility "remains insulated from rising rates" — the slope fact the whole exercise rests on — asserted in the literature review with no page, section, table, or figure. Six `berger2026` sites, zero locators. Worse: the entire provenance layer (`common/berger_calibration.py:2`, `tests/test_berger_calibration.py:35`, `TECHNICAL.md:1340`) attributes the transcribed literals to "Berger, Milbradt, Tourre & Vavra" — the **berger2021** AER author list — while the manuscript cites **berger2026** (Berger, Jeong, Marx, Olesen, Tourre). One attribution is wrong and a reader has no locator to tell which. | Add `\citealp[\S3.3.1]{berger2026}`-style locators (natbib is loaded `[authoryear,round]`, so this compiles). Resolve the attribution before editing. | none |

---

## Tier B — genuinely open analytical work

| id | Item | Status | Cost |
|---|---|---|---|
| **B1** | **Concave × additive cell** (critique item 3). The level sweep and the form test both landed — the hull $[+3.89, +13.10]$pp is in the abstract. But `concave_marginal.py` ran `FLOOR_MODE='max'` **only**; its own header disclaims the form dimension. So the concave check is still executed *inside* the censoring regime the critique asked it to escape, and the hull's completeness over {form × transform} is asserted, not established. `tab:uncertainty` L509 lists "additive $+11.2$" and "concave $+5.1$" as parallel un-interacted entries, silently asserting a separability nothing has measured. | **New `hazard/concave_additive_marginal.py`** (do not edit the committed script). Both mechanisms compose with no new plumbing: `concave_marginal.py:102-113` monkeypatches `prepay_hazard`; `FLOOR_MODE` is read at call time in `literature_hazard.py:110`. Set both. Parity legs must replay 7.8741354244354085 and 11.248471889121141. **~2–3 min runtime.** Genuinely the cheapest consequential item on the page, exactly as the critique said. |
| **B2** | **Off-window additive levels are undisclosed.** At the anchors that underwrite the hull, the additive central leg recovers **55.9%** (null 44.7%) at the 4.991% headline anchor, and the $+13.098$pp hull *maximum* comes from a cell whose central leg recovers **61.2%**. None of 55.9 / 44.7 / 61.2 / 50.4 appears anywhere in the manuscript. The paper's identified-range upper end is produced by a specification that explains barely half the benchmark it is scored against, and no table shows it. This cuts *against* the additive form, and a referee who opens the artifact will find it. | Prose only, no run — all in `floor_form_offwindow_results.json`. Extend L784 past the production floor; add one clause at L797/L473 pricing the form-robustness at a 43–45 point undershoot. |
| **B3** | **Cross-design is N=1.** Every cross-design number — 59.3, 20.9, 76.3, 12.6, 70.6, 36.0, and the 150.6 external-gate variant — is a single seed-42 draw. No seed loop exists in `cross_design_test.py`, `cross_design_reweight.py`, or `abm_external_gates.py`. Both randomization layers are pinned (behavioral draws `RNG_SEED=42`; the 10,000-of-75,000 covariate subsample). Meanwhile `tab:headline` L72 asserts "the operative uncertainty is calibration, not seed noise" on the strength of a 50-seed run **that never varied the calibration**. And \$24.5B is a *lower* bound for the recalibrated variant, because the MC holds the mobility scale fixed while the recalibrated variant re-searches it per population. | `--seeds` loop threading seed into *both* layers. **Keep seed 42 as the bit-exact parity draw** (gate pins 59.30299434493775 to 1e-9). **~5–15 min for 50 seeds**, not hours — the cross-design surface is single-cohort. ~11 tex sites to requote as mean ± band. |
| **B4** | **The scale test does not test the production estimator** (critique item 16 — substantively right). Production mean CPR is **11.761%** (`abm/data/latest_run_manifest.json:67`), not the critique's 11.68% (that is the superseded fold-in run). Against the live spec the isolated mechanic runs 3.855pp / 32.8% hot. Omitted features confirmed in code: DTI wall 0.43, the discrete 20% freeze trait, income-scaled curtailment, 11-cohort weighting, 15yr/30yr split, settlement-lag kernel. **Worse than alleged: the scale test has no committed script, no artifact, and no gate.** `15.616` appears nowhere in the repo outside the v15r5/v16/v17/v18 tex. It is absent from `tab:runindex` and `tab:crosswalk`. Five downstream assertion sites: L51, L110, L125, L219, L911. | **Option A (preferred):** `abm/monte_carlo_simulation.py` already *is* the production-spec 50-seed harness; the only change is a `--n` flag into the engine constructor. **~15–25 min** both arms. Re-run both arms on the *fold-in* spec or the comparison is apples-to-oranges. **Option B:** soften all five sites, ~15 min, zero gate exposure. |
| **B5** | **Stratum-cluster bootstrap on Path B.** The critique's "single 75,000-loan draw" premise is false — `bootstrap_pathb.py` ran 200 replicates. But it holds the **strata fixed** (resamples loans within each stratum, preserves counts), so between-stratum variance is never drawn; that is exactly why the interval is degenerate (sd 0.03pp) and why the tex can say the draw "contributes essentially no uncertainty". There are 130 strata — few enough that between-stratum variance is not negligible a priori. The repo *already has* cluster resampling in `hazard/bootstrap_se.py`, applied to Path A but never to Path B. Also: the loan-level CIs exist only at the **demoted in-sample** point; the headline off-window row carries no loan-level CI at all. `floor_uncertainty` is a distinct layer (sampling error in a calibrated *input*), not a substitute. | New script or `--scheme cluster` flag, mirroring `bootstrap_se.py`. **~73 min per 200-rep leg-pair, ~2.5h at both floors.** If the cluster interval is wider, the "binding layer" label at L509 is wrong and must move. |
| **B6** | **Cumulative runoff error as the primary statistic** (critique item 2). The affine identity *is* already conceded (L1197 note, L731). What is absent: no error is ever expressed as a percentage of realized runoff, and **the headline calibration has no committed cumulative-error figure at all** — the only error row (L1193) is the demoted in-sample standalone leg. At the headline floor the shared-basis error is $-\$66.8$B (a 10.2% *over*-prediction of realized runoff); standalone is $+\$2.8$B (0.43%). Neither appears. The critique's arithmetic checks exactly (realized runoff = 1417.5 − 764.748 = \$652.75B; 53.78/652.75 = 8.24%, 164.14 = 25.15%, 673.77 = 103.22%). One correction: nothing "flips sign" — recovery = 1 + error/764.748 is monotone; what changes is the referent and the denominator. | **Zero re-runs.** Every value is in committed JSON. Minimal version: add a "Terminal cumulative runoff error (\$B)" column to `tab:bases` and `tab:estimators`, plus one sentence in the L80 definitions block. Full version (abstract leads with dollar error) trips all four gate-#63 abstract keys → one tex+gates+tests commit. |

---

## Tier C — pre-commitment integrity. Highest reputational risk per unit of effort.

**C1 — the VII.D admissibility exclusion (critique item 14c). This is the single most damaging finding in the audit, and the evidence is harder than the critique claimed: the exclusion contradicts the run's own frozen artifact.**

Timeline, from commits, blobs and mtimes:

- `2026-07-16 10:18:59` — spec commit `335797a`. `git show 335797a:abm/abm_external_gates.py` contains **no admissibility precondition**; it says the external variant "is evaluated against the SAME pre-registered bands" and the floor diagnostic "is reported alongside whatever the recovery number is, whichever direction it moves".
- `2026-07-16 10:23:08` — run commit `aa65eee`. The diff touches only a JSON dict path; the spec header is **byte-identical**. No precondition was added even at run time.
- Artifact records `preregistration.registered_before_results: true` and `classification_external: "undercuts_paradigm"`.
- `2026-07-16 13:06` — the earliest file on disk containing both `150.6` and "that band presupposed an empirically admissible turnover level". **The precondition entered the manuscript ~2h43m after the run** and survived into v17 and v18 (L713).
- `TECHNICAL.md` §25.3, written the same round, records "same pre-registered bands" and **no exclusion**.

So L675's ex-ante threshold and the artifact's own pre-committed classification both say 150.6% is an undercutting result; L713 says it "is not scored against" that band. Both cannot be true. **Aggravating:** the SMD near-fit at L715 *is* scored against the same bands ("107.1\%, far above the pre-committed cross-design bands"). One 100%+ variant is scored and the other is not, in adjacent paragraphs. That asymmetry makes it read as motivated independently of the timeline. No gate protects the sentence and none would catch its removal.

*Fix (small, no re-run):* rewrite L713 to state the pre-committed classification **first**, then label the qualification as post hoc and explain why it is still reported. Optionally align L715. Same commit: extend the round-15 Q4 gate (`tools/liveness_gates.py:439-452`) to assert `classification_external == 'undercuts_paradigm'` and `registered_before_results is True`, plus a required tex phrase marking the qualification post hoc; add "is not scored against the 50\% undercutting band" to `ZERO_COUNT`. The current gate stays green through the rewrite either way — **which is exactly why it must be extended.**

**C2 — the two dirty-tree freezes** (item 14b) are disclosed at L948 but **never named**, only one of the two is documented in the repo, and the sentence's final clause is unsupported. Name them.

**C3 — item 14a is closed.** The git audit confirms the spec-before-run convention held for the round-21 runs, and L950 already discloses the exception for the two objects the critique names.

**C4 — `revised_paper_v18_simple_abstract.tex` is untracked and entirely ungated.** `liveness_gates.py:34` hard-codes the canonical path. Run against the short variant, `abstract_hedge_check` fails with **5 of 8 spans missing** and 8 further pinned literals absent; 10 of 17 mutation fixtures in `tests/test_abstract_hedge_gate.py` become no-ops. It silently reverses the round-20 calibration-label discipline (no 97.9/88.7 pair, no 88.2–93.7 band) and the round-21 Danish dual label. **It is not a drop-in.** Either mark it `% CANDIDATE ONLY` or — better — make `liveness_gates.py:34` glob `revised_paper_v18*.tex` so any variant on disk is checked.

---

## Tier D — presentation, and one claim to sharpen

- **Item 13 (trilemma).** The critique's reduction is correct and verified in code. Step 1 is already explicit (L614, L905). Step 2 is not stated anywhere: with $h_{null} = \max(h_{floor}, h_{vol,0})$ and the hazard monotone in the gap, the marginal is bounded by $h_{null} - h_{floor}$ and is **exactly zero in the 36% of loan-months where the floor binds**. Two precision corrections to the critique: the ceiling is $h_{null} - h_{floor}$ where $h_{null}$ includes the covariate terms, not $h_0$ alone; and the ceiling is a property of the **max form only** — under the additive form the marginal roughly doubles, so the reduction bounds the magnitude, not the sign. *One sentence at L905. No run.*
- **Item 9c — abstract overload is worse, not better.** Current working-tree abstract: **26 numeric quantities in 542 words** (critique-era v16: 12 in 277; v17: 16 in 467; committed v18: 590 words). Round 21 more than doubled the numeric load in exchange for honesty. No excluded-estimator figure is in it, so the critique's "three from estimators you exclude" no longer maps onto anything. A gate-free ~75-word Tier-1 trim exists (→ ~467 words, ~21 quantities). **Two zero-slack traps:** `positive at every` needs ≥7 and there are exactly 7; `$+3.0$ to $+8.0$` needs ≥2 and there are exactly 2, one of them the abstract's. This is a venue decision, not a mechanical edit.
- **Item 12a/12d — Ginnie.** The overlay reaches `tab:headline` only as the **superseded in-sample** level (89.3%) and `tab:uncertainty` only as a marginal entry. The off-window pair (84.0%/79.5%) that composes with the actual headline appears **only** in V.B prose at L326, and the run's own pre-committed frame says to carry it "wherever the off-window level/marginal is quoted as a headline". The abstract quotes both 91.3% and $+5.6$pp and carries neither. Separately, the representation arithmetic: the caption's "about two-thirds" is the **vintage-only marginal**. Netting the cross-cutting Ginnie slice on the book's own agency × vintage joint cells gives UMBS ∧ 2017–21 = **50.97%** (independence approximation 52.65%), so the directly represented fraction is **~51%, barely over half**. The critique's "well under two-thirds" is arithmetically right. *Prose only, no run.* One counter-argument to engage: \$27.8B of the \$66.3B raw adjustment is a GSE-mean placebo component common to any observed-series overlay, so 84.0% mixes a model-vs-observed recalibration into the Ginnie correction — that argues for promoting it as a *labelled accounting-correction variant*, not as the headline level.
- **Item 5g / 5e — Path A footprint.** `sec:patha` is 3,506 words (7.2%) with **three of the paper's first seven tables** plus a dedicated appendix, for a non-headline exhibit whose propagated interval spans zero and whose sign claim was withdrawn. Residual sign language survives unretracted in `tab:specbox`'s Path A column (L294, "sign-only claims") where L424's parallel phrasing *is* retracted in-sentence. Path A is also still the **top row** of the recovery ladder. *(Correction to the audit: that figure is the paper's fourth, not first — `fig1_` is legacy naming.)* Minimal demotion: move the ML/landmark comparator digressions into `app:ridge`, merge `tab:panel` into `tab:pathadiag`, strike the "sign … agree" parentheticals at L441/L582, drop the numeral at L51. **Do not rewrite the seasonality paragraph at L429** — gate #62 pins it verbatim.
- **Item 3b/3d — hedge and relocation.** The paradigm hedge is at **14 sites, not 8** (L30, 43, 51, 110, 548, 582, 608, 657, 665, 671, 709, 721, 899, 919). Two are hard-pinned and cannot be cut (L721 by gate #61; L711's neighbour by gate #76), and gate #76's `76.3\%` ≥4 constraint means **at most one** of L30/L51/L899 may lose it. The achievable floor is **three** surviving sites, not two. Do not delete hedge content — compress the nine pointer-only sites to a bare `\ref`, ~350–400 words. Before touching L30, *add* it to `ABSTRACT_HEDGES` (the concision handoff already calls gating the ungated abstract hedges "the highest-value item on the list").

---

## Tier E — compression: reframe it

Tier 3 as specified **does not move the page count.** (a) removes zero words and *adds* subsection headers; (b) is a relocation; (e) yields ~0.8–1.0pp. The concision round already measured that demoting `fig:mc` "moves 0.7pp of area and removes zero pages". Calibration is **495 words/page** from two committed build points. The handoff's 55–65pp target from 106pp is a 41–51 page cut — 34–44% of the paper — and Tier 3 cannot deliver it.

So treat Tier 3 as a **readability and defect-repair batch**, not compression. It requires **zero re-runs**. Sequence: (i) the two genuine defects first — the four mis-pointed Fannie `\ref`s at L295/515/926/997, and the V.B↔VII.F circular composition reference at L324/L733 that prints the same 107.0→109.1 coupon effect twice; (ii) the relocations (Danish inventory belongs in **VI.C**, not VII — `tab:danish` and `fig:gapsweep` already live there); (iii) the L80/L169 merge; (iv) the hedge compression as a *gated* claim-calibration commit; (v) the `tab:headline` four-row trim. **Defer the V.B section split to last** — 74 `\ref{sec:pathb}` occurrences of silent-failure surface for zero pages.

If 55–65pp is the real objective, spend the weekend on the handoff's item 6 list instead — and read `HANDOFF_concision_round.md:46-48` first, because ~40% of last round's compression rewrites strengthened a claim past its evidence **while passing all gates**.

---

## Suggested execution order

1. **Tier A, all 14.** Prose only, one run (A9's burnout ablation, ~2 min). Re-run gates after *each* section, never batched — gate failures print only the dict key.
2. **C1 + C4.** The pre-commitment items. C1 is the one a referee reads as motivated.
3. **B1 (2–3 min) + B2 (prose).** Closes the critique's cheapest and most consequential ask properly.
4. **B3 (5–15 min) + B4 (15–25 min).** Retires the two N=1 claims.
5. **B6.** Zero runs; changes the paper's fit vocabulary.
6. **B5 (~2.5h unattended).** The last identification layer.
7. **Tier D**, then **Tier E** only if the venue demands the page count.

## Standing constraints (from the round-21 and concision handoffs)

- **Fix the .tex, not the gate** — unless a justified revision changes pinned content; then tex + gates + tests move in **one** commit.
- **Green ≠ correct.** Every Tier A defect above coexists with 80/80 PASS. Six of them are ungated by construction.
- Hedge scope is load-bearing. Do not weaken.
- `HARDCODED_XREF` bans literal `Table 7` / `Section V.C` / `Appendix A` / `Equation (2)` — always `\ref`/`\eqref`.
- The repo is **public** and unpushed. Snapshot before destructive passes: the 101pp pre-edit v18 source was permanently lost once.

## Carroll Round note

Leading with the Danish leg is now defensible in a way it was not when the critique was written — the U.S.-intercept transplant *is* the fix the critique demanded, and it is production. But **three live defects sit inside the Danish section** (A1's false caption, A2's mislabelled discount table, A11's par-crediting), and A11 is the one a discussant could actually kill the leg with, because the omitted buyback price is larger than the whole $+\$61.2$B gap and signed against it. Fix A1, A2 and A11 before the Danish leg leads anything.
