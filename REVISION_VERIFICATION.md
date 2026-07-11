# Revision Verification — Securitization Trade-Off (v11 → v12)

This document is the **verification record** for the v11 → v12 manuscript revision: every code re-run, output trace, and diagnostic executed against the repository on **2026-07-09**, with the resulting numbers the prose pass should use. It is written in the same spirit as [TECHNICAL.md](TECHNICAL.md) — what was checked, what was found, what it changes — so that every replacement number in the paper can be traced to a committed artifact or a reproducible run.

**Bottom line: no headline result changes.** The production numbers stand as computed ($764.7B benchmark; $91.0B / 11.9% ABM; $915B / 119.7% Path A; $818.5B / 107.0% Path B; 59.3% / 20.9% cross-design). What changed: the Monte Carlo CI is replaced with a spec-consistent one, Path A coefficients now carry bootstrap CIs, three table/prose discrepancies are resolved, and five defense vulnerabilities now have one-sentence answers.

---

## Table of Contents

1. [Trace: Table 1 Danish ABM Row (B1)](#1-trace-table-1-danish-abm-row-b1)
2. [Trace: Synthetic-Control Peak Lag (B2)](#2-trace-synthetic-control-peak-lag-b2)
3. [Trace: Loan-Sample Provenance (B3)](#3-trace-loan-sample-provenance-b3)
4. [Re-run: Monte Carlo CI on the Fold-In Spec (A1)](#4-re-run-monte-carlo-ci-on-the-fold-in-spec-a1)
5. [New: Block Bootstrap SEs for Path A Coefficients (A2)](#5-new-block-bootstrap-ses-for-path-a-coefficients-a2)
6. [Inspection: Ridge CV Split (A3)](#6-inspection-ridge-cv-split-a3)
7. [Diagnostic: Competing-Risks Normalization (C1)](#7-diagnostic-competing-risks-normalization-c1)
8. [Diagnostic: β₁ = 0 No-Lock-In Null (C2)](#8-diagnostic-β₁--0-no-lock-in-null-c2)
9. [Diagnostic: SOMA Vintage Coverage (C3)](#9-diagnostic-soma-vintage-coverage-c3)
10. [Diagnostic: SOMA Agency Scope (C4)](#10-diagnostic-soma-agency-scope-c4)
11. [Verification: R² Convention and Value Mapping (C5)](#11-verification-r²-convention-and-value-mapping-c5)
12. [Repo Hygiene: Pre-Registration and FRED Key (E3/E4)](#12-repo-hygiene-pre-registration-and-fred-key-e3e4)
13. [Manuscript Substitution Table](#13-manuscript-substitution-table)
14. [Defense-Prep Notes](#14-defense-prep-notes)
15. [Artifact Map and Reproduction](#15-artifact-map-and-reproduction)

---

## 1. Trace: Table 1 Danish ABM Row (B1)

**Question.** Table 1 reports U.S. leg $91.0B, Danish leg +$812.9B, institutional gap −$728.4B — but 91.0 − 812.9 = −721.9 ≠ −728.4. Stale number or different convention?

**Finding: a mixed-runs error, not arithmetic.** `abm/data/runs/run-2026-07-05-berger/manifest.json` is internally consistent:

| Quantity | Manifest value |
|---|---|
| `us_trapped` | **$84.507B** |
| `danish_trapped` | **+$812.921B** |
| `institutional_gap` | **−$728.415B** = 84.507 − 812.921 (exact) |

The paper substituted the production-tag headline U.S. leg (**$90.98B**, from `run-2026-07-04-15yr-foldin`) into a row whose Danish leg and gap come from the berger run. The berger run's own U.S. leg ($84.5B) equals the native-15yr run's — the Berger recalibration (§20 of TECHNICAL.md) was frozen on top of the native gate.

**Fix.** Either (a) set the row's U.S. leg to **$84.5B** with a table note that the Berger comparison re-runs the U.S. ABM under its own calibration stage, or (b) keep $91.0B and recompute the gap as −$721.9B with a note that the legs come from different freezes. Option (a) matches the frozen artifact and is recommended.

---

## 2. Trace: Synthetic-Control Peak Lag (B2)

**Question.** Table 2 says peak lag 0 for the synthetic control; the production documentation says lag −3 (r ≈ +0.19). Which is wrong?

**Finding: neither — two peak conventions coexist in the codebase.**

| Code site | Convention | Result (15yr-foldin synthetic control) |
|---|---|---|
| `abm/cross_design_test.py:160` | `max(xcorr, key=abs)` — **max \|r\|** | lag **0**, r = **−0.318** |
| `abm/fed_mbs_extension_risk.py:1523` | `max(xcorr, key=xcorr.get)` — **most positive r** | lag **−3**, r = **+0.195** |

Both describe the same correlation structure (full lag profile in the fold-in manifest: −3: +0.195, −2: −0.198, −1: −0.140, 0: −0.318, +1: −0.208, +2: −0.030, +3: +0.107). The two cross-design variants in `abm/data/cross_design_results.json` (recalibrated: lag 0, r = −0.336; frozen: lag 0, r = −0.311) use the max-|r| convention.

**Fix.** State one convention in the Table 2 note and use it everywhere. The honest formulation covers both: *"contemporaneous correlation is negative (r = −0.32); the best positive alignment is weak (+0.19) and occurs at lag −3."* Either way the substantive claim — the synthetic-population ABM fails on timing — survives under both conventions.

---

## 3. Trace: Loan-Sample Provenance (B3)

**Question.** §V.C says Path B is estimated on the real Freddie 2017–2021 sample; §VII.A says "synthetic-augmented loan sample." Which sentence is wrong?

**Finding: §VII.A is wrong.** Fingerprint of the committed production sample (`hazard/data/loan_sample.parquet`):

- **75,000 rows, 75,000 unique loan IDs** (no with-replacement duplicates)
- ~15,000 per vintage across **all 20 quarters** F17Q1–F21Q4
- Coupon range 1.75%–6.875% with natural dispersion

The synthetic fixture (`hazard/ingest.py::generate_synthetic_fixture`) writes 5,000 single-vintage (2020) loans on a four-point coupon grid — none of its fingerprint appears in the production sample. It is a pipeline-testing fallback that only fires when no raw Freddie files exist, and it did not fire in production.

**Fix.** Keep §V.C; delete "synthetic-augmented" from §VII.A. (The symmetric *synthetic companion* test of TECHNICAL.md §18 is a separate, correctly-labeled exercise.)

---

## 4. Re-run: Monte Carlo CI on the Fold-In Spec (A1)

**Question.** The paper's CI ($113.5B mean, $106.6–$120.4B) was computed on the superseded 30-year-only spec. Re-run 50 seeds against the 15yr-foldin configuration.

**Two premise corrections discovered en route:**

1. The repo's existing re-run (`abm/monte_carlo_results.csv` @ commit `5c96de4`, mean $96.7B) was itself **spec-mismatched**: it ran at HEAD, where the native-15yr gate (`abm/abm_lockin_simulation.py::_mobility_penalty`, `is_short` branch) is unconditional — i.e., it is the uncertainty statement for the *native15yr* spec ($84.5B point), not the fold-in headline.
2. The fold-in manifest's `git_commit` field (`0899d12`) is **misleading**: the freeze ran on a dirty tree two minutes before the fold-in code was committed as `5cf33a3`. Verified by the cohort fetch: code at `0899d12` returns 7 buckets (30yr-only); code at `5cf33a3` returns the manifest's 11 buckets (15yr+30yr, WAC 2.49%).

**Method.** 50 seeds at commit `5cf33a3` in a detached scratch checkout. One harness function (`surface_df_to_surfaces`) backported from `5c96de4` to key surfaces by `(coupon, term)` — required because the fold-in produces 15yr and 30yr cohorts at the same coupon; **model code unchanged**. Calibration inputs reproduced the freeze exactly (mobility scale 43,882.8, income $83,730, home value $403,200, benchmark $764.7B).

**Results (replaces §IV.A's $113.5B / [$106.6, $120.4]):**

| Statistic | Value |
|---|---|
| Mean | **$103.7B** |
| SD (seed noise) | **$24.5B** |
| 95% CI of the mean | **[$96.9B, $110.5B]** |
| Range | $46.6B – $150.8B |
| Seed 42 (production population draw) | **$90.98B — reproduces the frozen headline to the cent** |
| Headline's position in seed distribution | 34th percentile, z = −0.52 |

The seed-42 exact reproduction confirms SOMA as-of drift (2026-07-04 freeze → 2026-07-08 fetch) is immaterial. Suggested §IV.A sentence: the $91.0B headline is a single population draw from a seed distribution with mean $103.7B and SD $24.5B; it sits at the 34th percentile — well within seed noise — and the distribution's mean CI is [$96.9B, $110.5B].

**Artifacts:** `abm/data/runs/run-2026-07-04-15yr-foldin/monte_carlo_{results.csv, trapped_liquidity.png, summary.json}` (summary.json records full provenance).

---

## 5. New: Block Bootstrap SEs for Path A Coefficients (A2)

**Question.** β(rate_gap) = +0.67, β(burnout) = −0.13, β(friction) = −0.037 are reported with no SEs, yet §V.D calls the rate-gap coefficient "significant." Ridge + 296 stratum FE invalidate naive GLM standard errors.

**Method** (`hazard/bootstrap_se.py`, tests in `tests/test_bootstrap_se.py`):

- **Cluster bootstrap at the stratum level**: 296 strata resampled with replacement; each resampled copy gets a fresh FE label so duplicated strata contribute independent fixed effects.
- **Ridge α fixed at the production value (1e-4)** — *not* re-selected per replication (re-selection would bootstrap a different, slower estimator: coefficient-plus-model-selection).
- Standardization recomputed per replication (pipeline-faithful), then rescaled to production standardized units (β_prod = β_rep · prod_std/rep_std) so draws are comparable.
- Replications warm-started from the point fit; fits returning non-finite or absurd (|β| > 20) coefficients counted as failures, not draws.
- Parity check: the point refit reproduces the production coefficients to 4 decimals (+0.6734 / −0.1301 / −0.0371) on the same 10,176 training cells.

**Results (198/200 replications converged; production standardized units):**

| Coefficient | Point | Bootstrap SE | 95% percentile CI | Share of draws ≤ 0 |
|---|---|---|---|---|
| rate_gap_bps | **+0.673** | 1.152 | **[+0.60, +4.11]** | **0.5%** |
| burnout_orth | −0.130 | 1.363 | [−1.76, +1.43] | 75.3% |
| friction | −0.037 | 0.506 | [−0.25, +1.38] | 48.0% |

**Implications for §V.D.** "Significant" survives **for the rate-gap coefficient only**: its sign is stable in 99.5% of cluster replications and the percentile CI excludes zero. But the magnitude is imprecise and the bootstrap distribution is heavily right-skewed (the point estimate sits near the CI's lower bound — identification is concentrated in a subset of strata). Burnout and friction are **not distinguishable from zero** at the cluster level and should be described as controls, not findings. Report the percentile CI + sign-stability, not a normal-approximation t-statistic.

**Artifacts:** `hazard/data/hazard_bootstrap_se.json` (full results incl. method flags), `hazard/data/hazard_bootstrap_draws.csv` (per-replication draws).

---

## 6. Inspection: Ridge CV Split (A3)

**Question.** Is the α ∈ {1e-5, 1e-4} holdout a random cohort-month split (within-stratum leakage)?

**Finding: no re-selection needed.** `hazard/hazard_fit.py:244-245` splits **temporally**: train = cohort-months before `HOLDOUT_DATE` (2024-01-01), holdout = everything after. This is already the "hold out the last k quarters" blocked design; there is no random fold for within-stratum information to leak across. α = 1e-4 won on holdout RMSE under that split.

**Fix.** One robustness sentence in the paper: *"α was selected on a temporally blocked holdout (all cohort-months from January 2024 onward), so no within-stratum information crosses the split."* This also licenses the fixed-α choice in §5's bootstrap.

---

## 7. Diagnostic: Competing-Risks Normalization (C1)

**Question.** The rule "scale both hazards if h_prep + h_def > 1" silently distorts relative risk when it binds. How often does it bind?

**Finding: never.** Instrumented run (monkeypatched counter around `literature_hazard.normalize_competing_hazards`; production code untouched) over the full QT-window microsim on the production 75k sample:

| Regime | Loan-months evaluated | Binding events | Max h_prep + h_def observed |
|---|---|---|---|
| US | 1,683,124 | **0** | **0.0155** |
| Danish | 1,683,124 | **0** | 0.0054 |

The hazard sum never comes within two orders of magnitude of the threshold. One sentence for the paper: the normalization is a safety clamp, not a calibration choice, and it never binds in production.

---

## 8. Diagnostic: β₁ = 0 No-Lock-In Null (C2)

**Question.** The pre-fix 97.7% recovery suggests the PSA baseline + floor + burnout do most of the aggregate work. Make this precise on the current codebase.

**Finding** (from `hazard/no_lockin_null.py` → `hazard/data/no_lockin_null_results.json`, same sample and seed as production; verified against `hazard/data/extension_risk_band_literature.json`):

| Spec | Trapped | Share of $764.7B | Peak lag (r) |
|---|---|---|---|
| β₁ = 0 null (mechanical model) | **$748.2B** | **97.8%** | −3 (+0.444) |
| P_q shock 5.5% (band low) | $809.9B | 105.9% | −3 (+0.423) |
| P_q shock 6.5% (production) | $818.5B | 107.0% | −3 (+0.404) |
| P_q shock 7.7% (band high) | $827.7B | 108.2% | −3 (+0.371) |

- **Lock-in marginal contribution: +$70.3B (+9.2pp)** over the null.
- **Band is strictly monotone** in the elasticity, peak lag stable at −3 across all points.
- **Caveat that changes the defense script:** the *null also peaks at lag −3* — timing structure does **not** discriminate the lock-in elasticity from the mechanical model. The elasticity-verification claim should rest on the marginal contribution and band monotonicity only; drop the timing leg of that argument.

---

## 9. Diagnostic: SOMA Vintage Coverage (C3)

**Question.** What share of SOMA face value falls in vintages the hazard sample (Freddie 2017–2021) covers?

**Finding** (CUSIP-level SOMA holdings, as-of 2026-07-08, origin back-derived as maturity − term, the production method; included universe $1,936.2B = 99.8% of $1,940.9B MBS face):

- **2017–2021 vintages: 66.2%** of included face value (2021 alone: 43.9%; 2020: 16.3%)
- 2022 vintage: 23.1% (final purchases / reinvestment settling in 2022)
- Pre-2017: 10.6% (largest single year: 2015 at 4.3%)

One sentence for §V.A or §VIII: two-thirds of the SOMA book by face value lies in the vintages the hazard sample covers; the uncovered remainder is dominated by the 2022 purchase tail, not by seasoned pre-2017 pools.

---

## 10. Diagnostic: SOMA Agency Scope (C4)

**Question.** Is the cohort parse conventional (Fannie/Freddie) only, or does it include Ginnie Mae?

**Finding: it includes Ginnie Mae.** The parse (`abm/fed_mbs_extension_risk.py::fetch_soma_mbs_cohorts`) takes every `securityType == "MBS"` row with no issuer filter. The book decomposes as:

| Issuer token | Face value | Share |
|---|---|---|
| UMBS (Fannie/Freddie uniform) | $1,544.5B | 79.6% |
| GNMA | $396.4B | **20.4%** |

By term: 30yr 90.7%, 15yr 9.1%, other 0.2%. §III.D's scope sentence should state that the cohort parse covers the full agency book *including* Ginnie Mae, and note the limitation that GNMA streamline-refi behavior differs from the conventional universe on which the Freddie-based behavioral calibrations rest.

---

## 11. Verification: R² Convention and Value Mapping (C5)

**Question.** Confirm the R² formula and which of −6.984 / −6.443 is current.

**Finding.** Both frameworks compute the identical statistic — `hazard/macro.py:110-122` and `abm/fed_mbs_extension_risk.py:168-170`:

> R² = 1 − Σ(CPR_emp − CPR_model)² / Σ(CPR_emp − mean(CPR_emp))²

i.e., **1 − SSE/SST against a mean-only null**, over the 42 active-QT months. Negative values mean the model path fits worse than the empirical mean. Footnote-ready.

Value mapping from the frozen manifests:

| Run tag | Raw path R² | Status |
|---|---|---|
| `run-2026-07-04` (30yr-only) | **−6.443** | stale |
| `run-2026-07-04-15yr-foldin` (production) | **−6.984** | current |
| `run-2026-07-05-native15yr` | −7.086 | variant |

So the D3 fix (§VII.A: −6.443 → −6.984) is confirmed on both sides, as is the simulated U.S. CPR fix (§IV.C: 11.76% → **11.68%**; 11.76% is the native15yr/berger value, 11.98% the 30yr-only one).

---

## 12. Repo Hygiene: Pre-Registration and FRED Key (E3/E4)

**E3 — "pre-registered" is not verifiable.** The repository has **no git tags**. The pre-registration commit (`f0f9684`, 2026-07-05 02:54 UTC) postdates the creation timestamp inside `cross_design_results.json` (02:52 UTC) by two minutes — criterion and results are contemporaneous in the record, and `registered_before_results: true` is self-asserted in code. **Downgrade "pre-registered" (7 occurrences in the draft) to "specified ex ante in the analysis code"** throughout.

**E4 — FRED key.** Current code correctly reads the key from env/`.env` (`common/fred_key.py`, migrated in `b8559d7`), but the previously hard-coded key remains recoverable from earlier git history. **Revoke and rotate the FRED key** (keys are free); history rewriting is then unnecessary.

---

## 13. Manuscript Substitution Table

Verified against the live draft (`revised_paper_v11 (2).docx`, 2026-07-06). Every "old" value below was confirmed present in the draft; every "new" value traces to a section above.

| Location | Old | New | Basis |
|---|---|---|---|
| §IV.A Monte Carlo | mean $113.5B, CI [$106.6B, $120.4B] | mean **$103.7B**, SD $24.5B, CI of mean **[$96.9B, $110.5B]**; headline = seed 42 = 34th pctile | §4 |
| §IV.C simulated U.S. CPR | 11.76% | **11.68%** | §11 |
| §VII.A raw path R² | −6.443 | **−6.984** | §11 |
| Table 1 Danish row, U.S. leg | $91.0B | **$84.5B** (or recompute gap; see §1) | §1 |
| Table 2 synthetic-control peak lag | 0 (unannotated) | state convention; lag 0 (r = −0.32) under max-\|r\|, lag −3 (r = +0.19) under max-positive | §2 |
| §VII.A "synthetic-augmented loan sample" | delete | sample is 75k unique real Freddie loans | §3 |
| §V.D coefficient significance | "significant" (unqualified) | rate-gap only: 95% CI [+0.60, +4.11], sign stable in 99.5% of replications; burnout/friction n.s. | §5 |
| "pre-registered" (×7) | | "specified ex ante" | §12 |
| §III.D SOMA scope | (implied conventional) | includes GNMA (20.4% of face) | §10 |
| §VII.A "15yr excluded on both sides" | | re-scope to hazard side only (ABM folds 15yr in production) | manifests, §4 |

---

## 14. Defense-Prep Notes

1. **"Doesn't the pre-fix 97.7% hollow out the elasticity claim?"** Answer with §8: the mechanical model recovers 97.8% of the *level*; the elasticity's verified content is the **+$70.3B (+9.2pp) marginal contribution** and the **strict band monotonicity** ($809.9 → $818.5 → $827.7B). Do **not** cite timing: the β₁ = 0 null also peaks at lag −3.
2. **"Your estimator was trained on loans the Fed doesn't hold."** §9: 66.2% of SOMA face value is in-sample vintages; the out-of-sample mass is mostly the 2022 purchase tail.
3. **"The normalization rule distorts competing risks."** §7: it never binds; max hazard sum is 0.016 against a threshold of 1.
4. **"Are the hazard coefficients significant at all?"** §5: rate-gap yes (percentile CI excludes zero, 99.5% sign stability), with honest imprecision; burnout/friction no — and the paper should say so first.
5. **"Is the $91.0B headline a lucky seed?"** §4: it is the 34th-percentile draw of a 50-seed distribution (z = −0.52); seed 42 reproduces it exactly.

---

## 15. Artifact Map and Reproduction

New/updated artifacts on branch `claude/trusting-euler-d1b730` (all inputs otherwise committed):

| Artifact | What it is |
|---|---|
| `abm/data/runs/run-2026-07-04-15yr-foldin/monte_carlo_results.csv` | 50-seed fold-in-spec MC draws (§4) |
| `abm/data/runs/run-2026-07-04-15yr-foldin/monte_carlo_summary.json` | MC stats + full provenance incl. harness-backport note |
| `abm/data/runs/run-2026-07-04-15yr-foldin/monte_carlo_trapped_liquidity.png` | MC histogram vs $764.7B benchmark |
| `hazard/bootstrap_se.py` | Stratum block bootstrap (§5) |
| `hazard/data/hazard_bootstrap_se.json` | Bootstrap CIs/SEs, method flags, parity record |
| `hazard/data/hazard_bootstrap_draws.csv` | 198 per-replication coefficient draws |
| `tests/test_bootstrap_se.py` | Resampler/rescaling/smoke tests |
| `tests/test_loan_sample_cache.py` | Regression tests: cache hits never touch the download path |

Reproduction notes:

- **MC (§4):** `git worktree add --detach <dir> 5cf33a3`, backport `surface_df_to_surfaces` from `5c96de4`, `python3 abm/monte_carlo_simulation.py`. Requires `.env` (FRED key) at the checkout root. ~11 min.
- **Bootstrap (§5):** `cd hazard && python3 bootstrap_se.py --reps 200`. ~12 min.
- **C1/C3/C4 diagnostics:** one-file scripts (monkeypatch counter; SOMA CUSIP tabulation) — see §7/§9/§10 for the exact numbers; each rerunnable in under a minute plus one ~50s microsim per regime for C1.
- **Manifest caution:** do not trust `manifest.json::git_commit` to identify a spec (§4); use commit messages and the cohort-bucket count (7 = 30yr-only, 11 = fold-in).

---

# Referee Round 2 — Three-Persona Audit (2026-07-10)

Executed against the v15 manuscript (all three editions updated in lockstep: `revised_paper_v15.{tex,docx,pdf}` in `~/Downloads`). Every requested computation was run; each new script carries a parity gate that reproduces a published number before producing its variant. **One headline framing changes:** recoveries are now stated on the shared accounting layer (benchmark-consistent basis), where Path B = 97.9%, Path A = 110.6%, β₁=0 null = 88.7%, and the composed (shared-layer + full-book) Path B = **$765.1B = 100.0% of benchmark**. The lock-in marginal (+9.2pp) is basis-invariant.

| Item | Script → artifact (`hazard/`) | Key result |
|---|---|---|
| Shared-layer scoring + composed correction | `shared_layer_scoring.py` → `data/shared_layer_scoring_results.json` | B 97.9 / A 110.6 / null 88.7%; composed B 100.0%, A 117.0%; curtailment netted $69.6B; parity 97.9% vs §17.1 |
| Rate-input timing diagnosis | `rate_timing_scan.py` → `data/rate_timing_scan_results.json` | Empirical CPR ~ rate(t) (r +0.40); sim CPR ~ rate(t−4) (r +0.60); no ±1–3mo shift kills the −3 offset; trapped invariant <$1.5B |
| FICO/LTV priors estimated | `covariate_priors_estimation.py` → `data/covariate_priors_results.json` | β̂_F −0.39 [−1.51,+0.65], β̂_L +0.21 [−0.59,+1.00] — priors' signs supported (turnover regime); zero-out 108.3%, estimated 101.3% |
| Seasonality + concave gap | `seasonality_concave_gap.py` → `data/seasonality_concave_gap_results.json` | Month effects to +0.43; r(lag0) −0.444→−0.378, peak −2, 121.5%; concave gap 105.7%, r(lag0) +0.281 |
| Refit-and-resimulate interval (Path A) | `bootstrap_resimulate.py` → `data/bootstrap_resimulate_results.json` + draws CSV | median $922.6B, IQR [900.1, 1130.6], 95% pctile [−4459.8, +1190.1] — 15 burnout/friction blowups; $915B demoted from abstract |
| WAL table + no-shock row | `wal_table.py` → `data/wal_table_results.json` | Reproduces all printed Table 6 values exactly; 2021-speed row (22.81% CPR) WAL 3.4y ⇒ extension 6.0y |
| Ginnie composition bound | inline → `data/ginnie_bound.json` | 0.204 × (1.2–2.8pp GMAR differential) × ~$83B/pp ⇒ $20–47B (2.6–6.2%), toward overstating trapped |
| Panel/attrition/Markov disclosures | `panel_disclosures.py` → `data/panel_disclosures.json` | Panel = full universe (peak 8.84M loans, $72.48T/$37.43T raw, no weights); attrition 75,000→40,234 active; Markov cell counts thin (D30 row n=21); extreme-matrix bound $0.39B |

**Two structural facts surfaced by the audit and now disclosed in the paper:** (1) Path A's estimation panel is the full Freddie 2017–2021 origination universe, not the 75,000-loan sample (Table 2's $72.5T is raw dollars, unweighted; the fit's training window is 2021-01–2023-12 because the macro frame starts 2021-01); (2) the delinquency matrix rests on thin modal-state counts, but replacing it wholesale with either extreme moves the estimate by $0.39B — consequence-free.

Manuscript deltas: abstract restated on the shared basis; §V.C timing paragraph replaces "unexplained regularity" with the state-dynamics diagnosis; Danish gap functional form corrected in place (v14 carry-over); Table 1 hybrid legs printed ($749.0B / $848.9B); Table 4 gains both hazard-path mean CPRs and the corrected significance note; Table 6 gains the no-shock row; Appendix B gains the cell counts, draw-vs-matrix reconciliation, attrition accounting, and estimated priors. Docx-only fixes: Eq. (2) OMML now (s,t)-indexed with the conditional; all 5 equations converted to display `m:oMathPara`; LaTeX residue (\\, natexlab×4) removed; headings black; "From \ To" header. LibreOffice render check pending (not installed on this machine); XML validates and the Apple importer reads the package.

## Round 3 addendum (2026-07-10, adjudication)

The panel's adjudication of round 2 surfaced five substantive corrections, all applied:

1. **Netting mechanics disclosed.** The shared-layer netting is exactly $69.562B for every estimator — pure income-scaled curtailment on the *actual* WSHOMCB holdings path, common by construction because every simulation rescales its roll-off to that path monthly. v15's "curtailment and term-aware amortization" attribution was wrong (curtailment only). §VII.F now states the flat-wedge mechanism; `shared_layer_scoring_results.json` carries per-run `netting_decomposition` + `netting_mechanics`. The composed 100.0% is a joint run (`path_b_fullbook_composed`), with the additive identity exact (zero cross-term) and demoted to cross-check.
2. **Timing attribution withdrawn.** β_b=0 and β₁=0 both preserve the −3 peak, so burnout/floor cannot carry it; levels correlations were trend-contaminated. New Δ-based diagnostic (`part1_variants`): sim ΔCPR vs Δrate r=−0.94 at lag 0 (correct sign, mechanical); empirical ΔCPR vs Δrate +0.25 (wrong sign) — empirical monthly variation is not rate-driven; seasonality is the live suspect. §V.C says "mechanism not isolated."
3. **Markov crosstab reconciled.** Matrix is exposure-UPB-weighted; printed probabilities equal UPB shares exactly (D30 cure: 13 events = 95.6% of $58.3M row exposure vs 0.62 count share). Full crosstab in Appendix B + artifact. 482-vs-154: both true (window-start stock vs month-end stock after matrix routing); extreme-matrix bound runs included the initial 482, bound stands at $0.39B.
4. **Erratum logged (Appendix A):** v15 Table 2 note ("75,000 unique loans … aggregated to 296 strata") was false; Path A panel is the full universe. Global per-path 75,000 sweep (§III.A, §III, §V.C, §VII.A, §VIII.A).
5. **Basis propagated everywhere:** Table 4 note (all rows' shared equivalents + Path A interval as lower bound), band 96.8–99.1% shared, §VII.E companion 96.9% shared, §V.D "lands within" scoped to Path B only, Fig 1 regenerated on shared basis (composed row at 100.0%), covariate endpoints 99.2/92.2% shared with production vector declared (priors retained).

New artifacts: `~/Downloads/v15r2_bundle/` (tex+docx+pdf, both redlines vs pristine v15, `v15_parity_report.json` — 94.8% sentence containment docx↔PDF, all sampled misses triaged to extraction noise), regenerated `figures/fig1_recovery_by_estimator.png` (+ `make_figures.py` updated). The parity check caught two round-2 edits present in tex but missing from docx (seasonality passage; β_b/FICO-LTV sentence) — repaired before the bundle was cut. LibreOffice render CLOSED same evening: user authorized the install (LibreOffice 26.2.4, official DMG, user-space ~/Applications); headless writer_pdf_Export conversion of the revised docx renders all five equations as display math with numbers (pages 6/15/18/19 rasterized and bundled as lo_render_eqpage_*.png in ~/Downloads/v15r2_bundle/). The check surfaced one glyph nit — LibreOffice maps U+2223 to a slash — fixed by switching the Eq. (2) conditional bar to U+007C and re-rendering. Still open: Word REF-field conversion.

## Round 4 addendum (2026-07-10, second adjudication)

Two instruments drew blood this round; both results are in the paper:

1. **Output-side timing demotion.** corr(Δsim, Δemp) = −0.23; detrended levels = −0.20 (both inside the ±0.31 zero band at n=41). Path B's +0.190 lag-0 levels correlation is trend-carried; the "nonnegative contemporaneous correlation" credential (installed round 2) is demoted in §V intro, Table 4/5 notes, §VII.D, §V.D, §V.C, and Figure 1 (marker-fill semantics removed). Path B's distinction is now stated as level accuracy only. Artifact: `rate_timing_scan_results.json → output_side`.
2. **Netting scope corrected in print.** §VII.F now states the per-leg conversion architecture (hazard dynamics on own balances; U.S.-leg dollar conversion = monthly rescale to WSHOMCB; invariance scoped to U.S. legs) and quantifies the Danish-leg curtailment on counterfactual balances: $70.33B vs the common $69.56B (+$0.77B, immaterial). Artifact: `shared_layer_scoring_results.json → danish_leg_curtailment`.

Also: covariate band attached to every headline instance (abstract "97.9% (92.2–99.2% across covariate calibrations), 100.0% under the ex-ante priors"); §VIII hard gate binds seasonal-Path-A production adoption AND REF-field conversion to the pre-submission freeze with Table 4/WAL/interval restatement; +0.25 softened to "no detectable rate response"; resim interval labeled standalone-basis; unrounded benchmark ($764.748B) printed in §III.D; Appendix B "transparency, not precision" sentence; §VII.F erratum added to the Appendix A ledger; monthly delinquency-stock series added to `panel_disclosures.json` (max 154 at month 1, mean 24, end 14 — confirms the 482→154 routing arithmetic).

**Bidirectional parity v2 with full hand-clearing** (`v15_parity_report.json`): 95.6% forward / 93.6% reverse sentence containment; every unmatched item carries a three-way tex/docx/PDF verdict; ambiguous items resolved by direct grep. The reverse pass found two REAL tex→docx drift items (Table 7 "panel estimate" provenance cells; Appendix A erratum wording) — fixed before the bundle was cut; the checker's own XML-entity bug was found and fixed the same way. Real drift remaining: 0. Delivery: `~/Downloads/v15r2_bundle.zip` (24 files + SHA256SUMS), LO equation renders regenerated against the final docx.

## Round 5 addendum (2026-07-10, third adjudication)

**All-estimator output-side statistics** (`rate_timing_scan_results.json → output_side_all_estimators`): detrending collapses the three estimators into one cluster — detrended r: ABM −0.30 (from −0.32 levels), Path A −0.29 (from −0.44), Path B −0.20 (from +0.19); first differences −0.20/−0.21/−0.23. All inside the ±0.31 i.i.d. band at n=42 (moving-block band wider → indistinguishability strengthened). Consequences in print: §V.B closing no longer defers timing claims to Path B; Table 4's "significantly negative" Path A statement is scoped to the levels construction; Figure 1's caption states the computed all-estimator fact; Table 4/5 "no lead structure" cells → "no positive alignment"; §VII.E "timing degrades" → levels comparison. The composed covariate band (≈94.3–101.3%) now accompanies the composed 100.0% in the abstract, §V.D, and §VII.F (basis-mix fix). §VII.F prints both netting figures ($69.56B U.S. common / $70.33B Danish-leg).

**Process adoption (auditor's remedy):** `timing_sweep_log.md` — a committed grep enumeration of the timing-phrase family (timing, lead, path diagnostics, nonnegative, not outright negative, materially better, offset) over both editions with per-hit dispositions — is regenerated per round; this round it surfaced three stragglers that four rounds of memory-sweeping missed. Round-5 letter inlines the evidence verbatim (SHA256SUMS, netting/output-side JSON blocks, the sweep log) per the third-non-delivery remedy; the zip travels with the letter. Parity v2 final: fwd 96.3%, rev 93.8%, real drift both directions = 0 (six forward candidates resolved by direct grep, recorded in the artifact).

## Round 6 addendum (2026-07-10, punch-list)

1. **Artifact regate:** `netting_mechanics` string in `shared_layer_scoring_results.json` carried the round-3 overbroad sentence ("every estimator's roll-off is rescaled…"); corrected to "every U.S. LEG's roll-off…" with the Danish-leg cross-reference — artifact now internally consistent and consistent with §III.B/§V.B.
2. **ABM −0.316/−0.318 reconciled:** convention, not error. Artifact scores all estimators against the common hazard-side empirical series (ABM r₀ −0.316); the manuscript's −0.318 is against the frozen run's own cohort-weighted back-out — recomputed from `metrics_monthly.csv`: −0.3183 exactly. `levels_r0_production_convention` + `convention_note` added to the artifact.
3. **Zero-band bookkeeping:** §V.C names the construction once (i.i.d. 1.96/√n) with governing n per statistic (±0.30 @ n=42 detrended; ±0.31 @ n=41 differences; ABM's −0.30 flagged as closest call); `zero_band_note` in artifact.
4. **Sweep log v3:** family extended {ahead, trails, moves first, precedes, lags}, word-boundary matching (naive extension false-positived on "flags"); 38 hits, all dispositioned, tally computed from table rows (reconciles by construction).
5. **Bundle practice:** editions versioned (`revised_paper_v15r2.*`), manifest generated LAST and grep-verified (round-5 manifest had been cut before `timing_sweep_log.md` was copied in — auditor caught it), zip re-cut.

## Round 7 addendum (2026-07-10, final adjudication items)

1. **Table 4 convention mixing (statistician) — conceded, fixed in print.** The ABM row's correlations are scored against the ABM-side empirical back-out while hazard rows use the hazard-side series; Table 4's note now states the per-row convention (+ common-series ABM value −0.316), and §III.D discloses the two back-out constructions once.
2. **Closest-call straddle.** ABM detrended r₀ under the production convention = −0.3030, OUTSIDE the ±0.3024 i.i.d. band (common-series −0.301 was inside): the statistician's predicted convention flip realized. §V.C now reports the straddle and rests indistinguishability verdicts on the moving-block bands; Path A/B inside under both conventions. Artifact carries both values + corrected zero_band_note.
3. **Sweep tool defect (auditor) — mechanism named and fixed.** The round-6 matcher recorded only the first family phrase per source line; §V.C is one long line, so "ahead" shadowed "trails"/"moves first". v4 log: every phrase per line (60 rows vs 38; the 22 hidden rows now dispositioned), legend added (round-5 = actions; 6+ = steady state), defect disclosed in header. Two manuscript edits from the newly visible rows: §V.C's framing no longer asks whether the elasticity reproduces the shortfall "and its timing"; Table 4 cross-design note adds "(no estimator does; see above)".
4. **Equation renders regenerated** against the final docx (42 pp); equation pages verified unchanged at 6/15/18/19. Manifest regenerated last; letter/manifest self-hash exclusion stated in §E3.

## Round 8 addendum (2026-07-11, full three-persona review, 45 items)

**Priority items (panel meta-observation), all resolved from the repository:**

1. **Cross-correlation convention definition (statistician #1) — sentence inverted, conclusions right.** `macro.cpr_cross_correlation` pairs `e[:lag]` with `p[-lag:]` at negative lags — synthetic re-verification (predicted-trails-by-3 → peak k=−3, r=1.0) confirms a peak at k=−3 means the simulated path trails. The §V.C definition sentence had the two series interchanged; corrected, with an Appendix A erratum. Every direction claim was computed under the implemented convention and stands. Repo-side sibling fixed: `hazard/extension_risk.py`'s `lag_interpretation` string still carried the inverted reading plus the retracted settlement-delay interpretation; corrected.
2. **Stratum-cluster bootstrap vs φ_t (statistician #2) — structurally confirmed, remedied by computation.** `Dynamic_Friction` is built from national series only (time-only), so stratum resampling reproduces the identical friction series every replication. New `hazard/temporal_block_bootstrap.py` (moving blocks of 6 over the 36 training months, cross-sections intact, 196/200 converged; point refit reproduces production exactly): friction SE 2.80 vs stratum 0.51 (≈5.5×), CI [−3.71,+7.69]; burnout SE 2.59 vs 1.36, CI [−3.16,+6.16]; rate gap CI [+0.44,+12.18]. **Sign stability survives the correct scheme:** rate-gap draws positive in 99.5% under both schemes; friction/burnout remain indistinguishable from zero (a fortiori). Table 3 (tab:bootstrap) now reports both schemes; §V.B states the stratum scheme's structural silence about β_f.
3. **Floor circularity (quant #5) — conceded in print.** The 4% involuntary floor is anchored to 2023–24 discount-cohort turnover — inside the evaluation window. §V.C (post-floor-definition) and Appendix B now state that benchmark-independence is not window-independence and that the clean verification content is the +9.2pp marginal, not the aggregate level.

**Other computed results (artifacts committed):**

- `hazard/ridge_reference_weighting.json`: (i) the two ridge-grid fits are **bit-identical** (max |Δparam| 4.5e-17) — the grid selection was vacuous and the production coefficients are the IRLS solution to machine precision ("mildly shrunk" removed from print); (ii) reference-stratum swap in cold-start penalized refits moves the standardized rate gap +0.673→+1.963 (Δ=1.29) — reference-dependence is real for the penalized estimator; (iii) **20 of 296 strata have zero training events** (FE MLEs nonexistent — the true ill-conditioning source); dropping them (423/10,176 cells), unpenalized PML converges, is exactly reference-invariant (Δ≈6e-15), and reproduces the production macro coefficients to the third decimal (+0.673/−0.132/−0.037). All three facts now in §V.B. (iv) Exposure-weighted holdout RMSE 2.53pp vs 37.83pp unweighted; the 38pp figure is dominated by small-exposure strata; both printed with units.
- `hazard/data/round8_diagnostics.json`: moving-block design identified by exact reconstruction (circular joint-series MBB, fixed lags, 4,000 reps; all four printed block-6 intervals reproduced within seed noise ±0.02). Block-length sensitivity 4/6/8: **no zero-inclusion verdict changes**; the only crossing endpoint is Path A's lag-0 upper at block 8 ([−0.66,+0.04]) — "significantly negative" demoted to block-scoped in Table 4's note. Per-lag overlap bands: a lag-3 coefficient has n−3=39 overlapping observations (band 0.3139, not 0.3024) — §IV.A statement fixed. Panel recount: holdout = **6,077** (tab:panel printed 6,076; table fixed, erratum logged).
- `hazard/data/danish_discount_bound.json`: the Danish PV proxy discounts at the primary rate (MORTGAGE30US) — but the production Danish leg's prepay hazard is the imported Berger flat elasticity (`competing_risks.monthly_step` DANISH branch); `rate_gap_danish`'s classification feeds nothing in that leg. Discount shifted −50/−100bp: trapped moves **$0.000B** while 7,803/32,486 of 1.68M loan-month classifications flip. "Immaterial" is exact, now stated with the diagnostic in §III.B.
- **eq (β1) print/code mismatch found during quant #7 verification:** the printed equation was the continuous-hazard transform (0.0693 at central calibration); the implementation compounds discretely (0.0686). Both round to the printed 0.069 / 0.77 hazard ratio. Printed equation corrected to the implemented form; Appendix A erratum; small-P_q limit (−ln(1−δ)=0.0672) and P_q∈(0,0.12] range (0.0672–0.0701) now demonstrated in the footnote. `wal_table` defense: the quant's 16–17y replication is wrong — origination WAL at 2.49% is 16.89y, the 9.1% 15-year sleeve and the aged book pull the blend to 14.7; naive midpoint ages move it only to 14.9. Formula + worked anchors + age-provenance disclosure added to Table 6's note. Coverage reconciliation (90.6/90.7/9.1/99.8): audit parse 90.7+9.1=99.8 exactly with 0.2% other-term face excluded; 90.6% is the production parse's as-of-date share — reconciled in Table 6's note. Composed numerator printed unrounded ($765.077B; 765.077/764.748 = 100.04%). Bootstrap median coincidence verified genuine (median −0.1297 vs point −0.1301, both print −0.130) and disclosed.

**Editions:** ~35 prose edits + abstract restructure (≤2 headline figures; variants moved to the introduction with qualifiers; magnitude-not-sign Danish phrasing) + LaTeX hygiene (16 auditor items: Table 4 column widths, delinquency matrix now captioned Table 8, [t] floats, one minus-sign convention, Table 1 signed legs + uniform decimals + sign-convention note, Fig 1 caption cut, walls split at natural breaks, \eqref{eq:annuity} referenced, \citepos macro, run tags in \texttt, keywords block de-hacked). Tectonic build clean: 0 undefined references/citations, remaining overfulls ≤2.9pt (log ships with bundle). docx mirrored by XML surgery (59-probe verification, all pass), eq (5) OMML rewritten to the discrete form and render-verified via LibreOffice (45 pp; equation pages now 7/16/20/21). Sweep log v5: 82 rows, all dispositioned, generator now committed (`tools/timing_sweep.py`). Parity v3 (rebuilt, escaped-dollar and rendered-ref handling): tex→docx and docx→tex misses all resolve to six extraction-noise classes; every round-8 edit probe passes.

## Round 9 addendum (2026-07-11, round-8 adjudication findings)

1. **Finding 1 (Danish bound baseline unreconciled) — closed by scoring through the printed basis.** `danish_discount_bound.py` v2: (i) run identity — the baseline reproduces the frozen production Danish CPR path **exactly** (max |Δ| = 0.0; the earlier 2.7e-06 residual was the engine's per-regime RNG stream ordering, fixed by running the full production regime tuple, plus a shared macro frame across runs); (ii) reconciliation — the same baseline scored through the shared accounting layer gives **$848.870B against the printed Table 1 cell $848.9B** (U.S. leg 748.97 vs printed 749.0); basis chain: standalone $934.254B = shared $848.870B + Danish-leg curtailment $70.33B + dynamic-balance-loop remainder $15.05B; (iii) wedge invariance — variant Danish paths are **bit-identical** to baseline (max |Δ| = 0.0 on CPR and roll-off), so every scorer including the printed basis maps them to the same dollar.
2. **Finding 2 ("third decimal" false for burnout) — conceded, weakened, both vectors printed.** §V.B now states "to within 0.002 in standardized units" with all six numbers (rate gap 0.6727/0.6734 and friction −0.0373/−0.0371 third-decimal; burnout −0.1317/−0.1301) and the mechanism (dropping 423 cells changes the burnout demeaning/orthogonalization sample). Artifact note regenerated. Also recorded: the production reference stratum is NOT among the 20 zero-event strata; 296 observed strata / 295 dummies / all 20 inestimable FEs among the 295 (the standing 295-vs-296 status).
3. **Finding 3 (WAL defense unbacked + grid-search circularity) — closed with an external anchor.** New `hazard/wal_anchors.py` + `wal_anchor_results.json` commits the letter's numbers (origination WAL 30yr@2.49% = 16.89y, 15yr = 8.01y; 2021 cell 16.27; midpoint blend 14.92) and derives cell ages EXTERNALLY from the SOMA CUSIP tabulation's own back-derived origination dates (maturity − term, face-weighted, no reference to Table 6): {2021: 11.6, 2020: 28.0, 2017–19: 50.5} months → scheduled-only blend **14.94**. Table 6's note now states the grid-search objective explicitly (recovered by matching the printed table — a disclosed reconstruction) and prints the external anchor; 14.7 sits within 0.3y of both alternatives, nowhere near 16–17.
4. **Finding 4 (§V.C describes dead code as live) — conceded, paragraph re-scoped.** §V.C now presents the rate-gap swap as the mechanism-substitution variant's definition, states the production Berger-recalibrated leg replaces it with the flat moving elasticity, and says the swap machinery's PV classification is computed but consumed by no production quantity (cross-referencing the $0.00 diagnostic). The panel is right that no sweep family covers manuscript-vs-code liveness claims; flagged as a freeze-gate audit item.
5. **Finding 5 (block-6 exclusion inside seed noise) — adopted verbatim.** Table 4's note: "excluding zero at block length 4; marginal at 6 — upper endpoint −0.02 at the production seed, −0.00 under the committed tool's reconstruction — and at 8."
6. **Secondary items:** §V.B burnout sign statement now scoped as point-estimate-only with the temporal scheme's opposite-sign center (mean +1.23, median +0.52) printed; §V.B ridge rationale rewritten (the penalty is not what stabilizes the fit; the inestimable FEs are pinned by the warm-started optimizer, verified against the estimable-strata fit); parity report v2 with per-miss class assignment (every miss carries a checkable class; 2 hand-cleared entries annotated; zero unclassified); sweep matcher regression SELF-CAUGHT and fixed (round-8 rewrite had dropped the suffix-s forms 'offsets'/'leads' that rounds 4–5 matched; 6 rows restored, log v6 = 88 rows all dispositioned, fix disclosed in the log legend).

## Round 10 addendum (2026-07-11, round-9 adjudication items)

1. **Finding-1 condition ($15.05B remainder undefined)** — `danish_discount_bound.json` now carries `remainder_definition`: the remainder is the roll-off-conversion analogue of §VII.F's +$0.77B curtailment differential, produced by the same design feature (the Danish leg compounds a counterfactual balance that the slower Danish drain leaves higher than the actual path, so each month's CPR converts to more roll-off dollars than fixed sample-to-book scaling produces); U.S. legs have no analogue because their conversion rescales monthly to the actual WSHOMCB path. No manuscript change: the standalone Danish figure appears nowhere in print.
2. **Finding-3 residual (2022 age reads as data)** — `wal_anchor_results.json` now carries `age_floor_note`: the 2022 cell's 0.0 months is floored at zero, not data (the bucket-averaged origin postdates June 2022); true vintage mean age ~2–3 months; effect on the blend < 0.05y at 23.1% weight.
3. **Parity tally 126 ≠ 124** — the round-9 LETTER's cross-direction summary line miscounted one bucket by hand ("footnote/other 4"; the correct figure was 2); the in-file per-direction tallies were computed from rows and summed correctly (27 + 97). The round-10 report embeds a computed tally-sums-to-misses check (27 + 98 = 125 after the round-10 gate-sentence edit; verified True at generation) and a standing note that hand-cleared entries ARE misses. **135 → 97 cause** (also embedded in the report): round 8's bibliography trim was ineffective (keyed on the wrong heading occurrence, removing ~1 character), so round-8's docx→tex ran against text including the rendered bibliography; round 9 trimmed at the last 'References' occurrence. The classifier did not change between those runs.
4. **Round-8 sweep reconciliation corrected in the log legend** — v4→v5 was two-sided: 60 − 6 + 28 = 82 (six suffix-s rows silently dropped — 'offsets' tex 255/420 + docx 155/285, 'leads' tex 278 + docx 185, v4 numbering — while 28 rows were added), not "+22 additive" as the round-8 letter presented. v6 restored the six (88); v7 = 92 (four new rows are the freeze-gate item's own name "timing-sweep generator", dispositioned as tooling references).
5. **Golden-fixture test committed and passing** — `tools/test_timing_sweep.py`: a hand-enumerated hit set covering all three historical matcher defect classes (round-6 first-match-per-line; round-6 'flags' false positive; round-8 suffix-s truncation) plus boundary rejections ('unleaded', 'mislead'); exact multiset match required. Added to the §VIII freeze gate in print (item iv), alongside the claims-vs-code liveness audit (item iii).
6. **Equation-render hash pattern explained + verification restored** — the round-9 changes to pages 20–21 (§V.B/§V.C insertions reflowing downstream content) changed those two rasters while pages 7/16 were byte-identical (deterministic rasterizer; no upstream reflow). Round-10 practice restored: docx LO render = 46 pages; equation pages verified by content search at 7/16/20/21; all four rasters regenerated against the v15r5 docx.
7. **FRED key (ledger condition)** — RECORDED: the key leaked in early public history was rotated on 2026-07-10 and the OLD key is issuer-deactivated (FRED returns 400 "not registered" on it), so the historical copies are inert; no history rewrite performed, by scope decision accepted in the round-9 adjudication. Verified this round: the REPLACEMENT key appears in **zero of 169 tracked files** and **zero commits** (`git log --all -S<key>` empty); it lives only in the untracked `.env`.

## Round 11 addendum (2026-07-11, three provenance one-liners from the round-10 adjudication)

1. **Drop corroboration cashed in:** the 135→97 parity drop is 38 misses; the erroneously retained bibliography renders exactly 37 entries (= the 37 .bib keys) + the heading = 38 sentence-units with no tex-source counterpart — the round-8-trim explanation predicts the drop magnitude exactly. Embedded in `v15_parity_report_round10.json` (`round8_to_round9_drop_note`), whose hash changes for this reason alone.
2. **timing_sweep.py hash change (round 9→10) explained:** `git diff dedaf5a 96d7fd1 -- tools/timing_sweep.py` touches only the LEGEND string (the corrected two-sided round-8 reconciliation and the golden-fixture reference are embedded in the tool's emitted legend); zero matcher-logic changes. Sweep v7 was generated by the shipped version, after the legend edit, with the golden fixture passing against that same version in the same session.
3. **v15r4 page count stated, chain closed:** v15r3 = 45 pages; **v15r4 = 46 pages** (recorded at the round-9 LibreOffice render); v15r5 = 46 pages. The added page came from round 9's §V.B/§V.C insertions; round 10's gate sentence left pagination unchanged, and equation pages sat at 7/16/20/21 in both — consistent with the identical round-9/round-10 equation rasters.
