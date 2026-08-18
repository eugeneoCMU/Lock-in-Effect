I have verified every engine detail and literal against the code, artifacts, and manuscript. Here is the deliverable.

---

# Round-28 run specs — WP-B2, WP-C4, WP-C5

**Status:** drafts for coordinator+Eugene sign-off. Nothing here has been executed; no manuscript, gate, test, or letter line was touched. Every number cited below carries its source location. Items that change what the paper *claims* are flagged ⚖.

**Verification basis (read before signing off).** All three specs were written against the actual scripts, not against their manuscript descriptions: `hazard/floor_sweep.py`, `hazard/moving_share_bracket.py`, `hazard/bootstrap_pathb_cluster.py`, `hazard/covariate_priors_estimation.py`, `hazard/burnout_ablation.py`, `hazard/literature_hazard.py`, `hazard/competing_risks.py` (`prepay_hazard`), `hazard/microsim_engine.py` (`run_qt_microsim`), `tools/liveness_gates.py`.

**Three findings that change the shape of these specs and were not in the plan:**

1. **The `floor_sweep._ORIG_PREPAY` gotcha applies to B2 only.** `fs._run_scored` (floor_sweep.py:120–147) installs `_tallying_prepay(tally)` over `competing_risks.prepay_hazard`, and that wrapper delegates to the *module global* `floor_sweep._ORIG_PREPAY` resolved at call time — so a variant hazard must be installed at `fs._ORIG_PREPAY`, and `_run_scored`'s own `finally` then writes that same (variant) object back into `competing_risks.prepay_hazard`, which is why **both** names must be restored by the caller (as `moving_share_bracket.py:169–177` already does). C4 (`bootstrap_pathb_cluster`) never touches `prepay_hazard` — it calls `run_qt_microsim` directly and mutates only `literature_hazard.INVOLUNTARY_CPR_ANNUAL`; C5 mutates only `LITERATURE_COEFS` in place. **The seam gotcha does not apply to C4 or C5.**
2. **C4 as currently written will destroy a committed artifact and break a green gate.** `bootstrap_pathb_cluster.py` writes `RESULTS_JSON` unconditionally (line 318) and *appends* to `DRAWS_CSV` (line 251–253, `mode="a"`), both floor-independent paths; and gate #84 (`tools/liveness_gates.py:4159–4177`) reads `bootstrap_pathb_cluster_results.json` and asserts `n_reps == 200`, `p2_5 == 4.630919609903703`, `p97_5 == 6.924433300615744`, `verdict == "T1"`, `effective_n_clusters == 25.77710660741266`. Its G1 parity anchors (lines 140–142) are hard-coded to the *off-window* legs and would SystemExit at floor 4.0. C4 therefore requires a small, pre-committed parameterization patch, specified below.
3. **The "seven tex sites" in REVIEW2 #6 is a miscount.** `$[+9.17, +9.23]$` occurs **6** times — tex **45, 78, 272, 301, 359, 1391**. The 7th `9.17` (tex **1360**, tab:seasonalfloor, `Convexity-matched flat 4.0090\%… $+9.17$`) is a *different object* (the convexity-matched flat-floor marginal) and must not be touched. Two further sites carry the hierarchy claim **without** the literal — tex **65** (tab:headline caption) and tex **343** (tab:uncertainty lead-in) — and must be dispositioned with the six. **Eight disposition sites, not seven.**

---

## B2 — `moving_share_bracket_offwindow`: the construct-mismatch bracket at the headline floor

### B2.1 Run name and tag

- **Run tag:** `moving_share_bracket_offwindow` (manuscript form `\texttt{moving\_share\_bracket\_offwindow}`).
- **New script:** `hazard/moving_share_bracket_offwindow.py`, following the repo's established off-window convention (`floor_form_offwindow.py`, `ginnie_overlay_offwindow.py`, `danish_offwindow_floor.py`): a separate file with its own pre-committed header spec, its own artifact, and machinery imported **unmodified** from the in-sample script.
- **Artifact:** `hazard/data/moving_share_bracket_offwindow_results.json` (new path — the committed `moving_share_bracket_results.json` is **not** overwritten).

### B2.2 Engine entry point and exact parameterization

```
from moving_share_bracket import mixture_prepay, probe_identity, _ORIG_PREPAY   # imported unmodified
import floor_sweep as fs, competing_risks, literature_hazard as lh
```

- **Scoring entry point:** `fs._run_scored(loans, empirical, FLOOR, pq)` — identical to the committed in-sample run. This carries the production convention: committed 75k `LOAN_SAMPLE_PATH`, `RNG_SEED = 42`, the default `("US","Danish")` regime tuple with per-regime seed offsets (`run_qt_microsim` is called at floor_sweep.py:129 with no `regimes=` argument), one shared macro frame fetched once, raw-basis scoring via `extension_risk.score_extension_risk`, and the value-preserving bind tally.
- **`FLOOR = 0.04991`** (the committed off-window point floor; consumed at runtime from `oos_identification_results.json → headline_oos_marginal.clean_floor_point_pct` and asserted `== 4.991` to 1e-9, per `floor_form_offwindow`'s convention — not hard-coded).
- **`CENTRAL_PQ = 6.5`**, `SHARES = [0.25, 0.50, 1.00]`, plus a null cell at `pq = 0.0` run through the **unpatched** production path.
- **Variant installation (the seam gotcha — applies here):** for each `s`, set `moving_share_bracket._share = s`, then `fs._ORIG_PREPAY = mixture_prepay`; in a `finally`, restore **both** `fs._ORIG_PREPAY = _ORIG_PREPAY` **and** `competing_risks.prepay_hazard = _ORIG_PREPAY`, and reset `_share = 1.0`. This is exactly `moving_share_bracket.py:169–178` and must be reproduced verbatim, not paraphrased.
- **Floor propagation is already correct and needs no code change:** `mixture_prepay` reads `lh.INVOLUNTARY_CPR_ANNUAL` at call time (moving_share_bracket.py:108–109), and `fs._run_scored` sets that module global to `floor` on entry (floor_sweep.py:124). Verified by reading both.
- **One required deviation from the in-sample script:** `probe_identity()` must be called **with `lh.INVOLUNTARY_CPR_ANNUAL` already set to 0.04991**, so the algebraic identity is exercised in the censoring region that actually obtains at the headline floor. In the committed run it executes at the production 4.0% floor (moving_share_bracket.py:147, before any `_run_scored`). Set the floor, probe, restore.
- **Runtime:** 4 engine runs (null + three `s` cells) at ~25 s each; the committed in-sample run reports `runtime_s = 93.3`.

### B2.3 Held at production (must not vary)

Loan sample, engine seed, regime tuple, macro frame, `FLOOR_MODE = "max"` (hard maximum — the mixture reproduces the production combination unchanged, moving_share_bracket.py:110–114), the elasticity `β₁ = -0.06857052676484808` at `p_q = 6.5`, the involuntary floor **unscaled by `s`**, `LITERATURE_COEFS`, scorer basis. `config.py` production defaults are not edited.

### B2.4 Pre-committed expectation, with derivation

**Committed inputs.**

| source | value |
|---|---|
| `moving_share_bracket_results.json → cells` (floor 4.0%) | s=1: `marginal_b 70.34506041989584` / `marginal_pp 9.198459770709789`; s=0.5: `37.664390601629066` / `4.925070497763002`; s=0.25: `19.23440215838832` / `2.5151286161600552` |
| `oos_identification_results.json → instrument1_marginal_table` (floor 4.991, band 6.5) | `marginal_b 42.60839388108866` / `marginal_pp 5.571558182909726`; null `724.9180585654117`; central `767.5264524465003` |

**In-sample ratios** (identical in dollars and points to 15 digits, confirming basis-invariance):
`r(0.5) = 0.5354233883204735`, `r(0.25) = 0.27342932174024`. Both are *super*-proportional in `s` by 7.1% and 9.4%.

**Central pre-committed projection** (proportional scaling of the off-window s=1 marginal by the in-sample ratios):

- **s = 0.50 → +$22.81B, +2.983 pp**
- **s = 0.25 → +$11.65B, +1.523 pp**

(Strict linear-in-`s` scaling would give +$21.30B/+2.786pp and +$10.65B/+1.393pp; the proportional-ratio figures are the committed projection, the linear figures are recorded as the lower reference.)

**Signed ex-ante prediction of the deviation (falsifiable, and the interesting part).** Under the hard maximum, a loan-month's contribution to the marginal is `min(h_null − f, h_null(1 − m_s))` where `m_s = (1−s) + s·m` and `f` is the floor hazard. Raising `f` from 4.0% to 4.991% raises the central leg's bind share from **36.3%** to **68.8%** (`floor_bind_share` 0.36269282595934704 → 0.6881875607501289, both over 1,683,124 US loan-months), which enlarges the region where the first term binds. Wherever it binds, the contribution is *independent of `s`*. Therefore **the realized off-window ratios `r_ow(s)` should land at or above the in-sample ratios**, i.e. the projections above are **lower bounds**. Signed at the hazard level; the dollar aggregate inherits it only approximately (renormalization and amortization intervene), so this is a prediction, not an identity.

**Materiality band:** ±1.0 pp on the marginal (the house `floor_form_test` convention). A landing outside the band is reported as a deviation with its size stated; it is **not** reinterpreted.

**Why the branch is genuinely open.** The projection for s = 0.5 (**+2.983 pp**) sits **0.017 pp below** the percentile read's lower edge (+3.0) and **0.183 pp above** the wild-t lower edge (+2.8). The signed prediction pushes it up. The landing branch is therefore not pre-determined by the projection — which is what makes the landing rule a test rather than a formality.

### B2.5 Parity and identity checks (BLOCKING — any FAIL voids the run)

- **P1 (s=1 dollar parity, bit-exact):** the mixture code path at `s = 1.00`, floor 4.991%, `p_q 6.5` must return `trapped_b == 767.5264524465003` and `share_pct == 100.36328284662208` to **< 1e-9** (`oos_identification_results.json`). *This is the parity the task names: s=1 must reproduce the committed +5.57pp bit-exactly.* Bit-exactness (not the house ±$0.01B) is the correct tolerance — `oos_identification`, `burnout_ablation` G6, and `bootstrap_pathb_cluster` G1 all record `got == want` to 16 digits at this floor.
- **P1b (algebraic identity probe at the headline floor):** `max |h_mixture(s=1) − h_production| < 1e-12` on the fixed 10,000-point grid (`PROBE_SEED = 42`, `loan_age 1..360`, `rate_gap −0.05..+0.01`, `burnout 0..3`, `fico_z/ltv_z −3..3`), evaluated **with `INVOLUNTARY_CPR_ANNUAL = 0.04991`**.
- **P2 (null parity, bit-exact):** the unpatched null at floor 4.991%, `p_q 0` must return `trapped_b == 724.9180585654117` and `share_pct == 94.79172466371236` to < 1e-9; and `max |h_mixture(s=0) − h_production(β₁=0)| < 1e-12` on the same probe grid.
- **P3 (bind anchor):** the `s = 1` cell's `floor_bind_share == 0.6881875607501289` over `1683124` loan-months, to < 1e-9. This is the run's cross-check that the floor actually moved.
- **P4 (restoration):** after every cell, assert `fs._ORIG_PREPAY is _ORIG_PREPAY`, `competing_risks.prepay_hazard is _ORIG_PREPAY`, `moving_share_bracket._share == 1.0`, and `lh.INVOLUNTARY_CPR_ANNUAL == 0.04`.
- **C1 (ex-ante ordering check, non-parity):** `0 < marginal(0.25) < marginal(0.50) < marginal(1.00) + 1e-9` on $B. A violation is a wiring alarm: artifact written with `status = CHECK_FAILURE`, nothing lands.
- **C2 (ex-ante monotonicity of the ratio, reported, obliging only itself):** `r_ow(s) ≥ r_in(s)` for both `s`. Reported in every branch; a violation is disclosed, not reinterpreted.

Status ladder mirrors the in-sample script: `OK` / `GATE_FAILURE` / `CHECK_FAILURE`; non-OK raises `SystemExit` and nothing lands.

### B2.6 Artifact path and fields

`hazard/data/moving_share_bracket_offwindow_results.json`

```
mode, status, spec (verbatim header),
floor_annual_cpr_pct (4.991), floor_provenance (oos artifact key consumed),
parity_gates: {P1_s1_offwindow{got,want,identity_probe{max_abs_diff_s1,max_abs_diff_s0,pass}},
               P2_null{got,want}, P3_bind{got,want}, P4_restoration}, parity_gates_all_pass,
c1_bracket_ordering_pass, c2_ratio_monotone{r_ow_0.5, r_in_0.5, r_ow_0.25, r_in_0.25, pass},
null{...}, cells{"0.25","0.5","1"}: each with floor_annual_cpr_pct, p_q_shock_pct, beta1,
  trapped_b, share_pct (standalone), share_pct_shared (= standalone − 9.096091632702699),
  cpr_r_lag0, best_lag, peak_lag_r, mean_us_cpr_pct, floor_bind_share, floor_bind_loan_months,
  share_s, marginal_b, marginal_pp, ratio_vs_s1,
projection{committed_ratio_0.5, committed_ratio_0.25, projected_marginal_pp, projected_marginal_b,
           deviation_pp, within_materiality_band_1pp},
landing_branch (A|B|C, computed by a pure function fixed in the header), runtime_s
```

The shared-basis offset `9.096091632702699` is read at runtime from `calibration_reconciliation_results.json → basis_map.offset_pp` and asserted, per `burnout_ablation`'s G0f/G0g convention. Point deltas are basis-invariant; only levels carry the basis label.

### B2.7 Landing rule (pre-committed; branch on the **s = 0.50** marginal in pp)

The classifier is a pure function fixed in the script header so it is testable without a run.

> **Branch A — `m(0.5) > +3.0 pp`** (above both the wild-t lower edge +2.8 and the percentile read's +3.0).
> The bracket lands inside the binding interval. Disposition: **two rows added to tab:assembly** (WP-B1's rebuild) and **one clause added to tab:uncertainty's headline row**; the off-window pair added beside the in-sample pair at tex 255. **No range-conditionality statement is forced.**

> **Branch B — `+2.8 ≤ m(0.5) ≤ +3.0 pp`** (inside the wild-t interval, at or below the percentile read's lower edge). **The projection's branch.**
> Same table dispositions as A, **plus** a range-conditionality statement is forced: the moving-share bracket's central stress lands at the *floor* of the layer the paper calls binding, so the binding interval's lower edge is no longer a floor on the measured corrections — it is reached by one of them. ⚖

> **Branch C — `m(0.5) < +2.8 pp`** (below the binding interval entirely).
> Same table dispositions, plus the strongest form of the same statement: a measured, disclosed specification variation puts the marginal **outside** the binding interval, so the interval cannot be quoted as if it encompassed the disclosed corrections. ⚖

**Pre-committed and NOT a new finding in any branch:** `m(0.25)` is projected at **+1.52 pp**, i.e. Branch-C territory by construction. The s = 0.25 cell is the *deep stress* of a bracketing parameter, already labeled as such at tex 255 (`$s$ is a bracketing parameter rather than an estimate`, gate #102 span `bracket_posture`). It is reported, it enters tab:assembly as the bracket's low member, and **it does not on its own trigger the Branch B/C statement** — only `m(0.5)` does. This is fixed here so that a large s=0.25 excursion cannot be read after the fact as licensing a stronger claim.

**Disposition sites, with current text quoted (anchors for the later edit; this spec changes none of them).**

- **tex 255** (§V.C, moving-share paragraph — the primary site):
  > `at the production calibration the marginal is $+\$37.7$ billion ($+4.9$ points) at $s = 0.5$ and $+\$19.2$ billion ($+2.5$ points) at $s = 0.25$, against the production $+\$70.3$ billion at $s = 1$, close to proportional in $s$.`

  **⚖ GATE COLLISION — must be handled in the same commit.** That clause is pinned verbatim as gate #102's `bracket_values` span (`tools/liveness_gates.py:617–618`). The off-window pair is **added beside it**, and the in-sample clause must survive verbatim, **or** `ELASTICITY_DISCIPLINE_SPANS["bracket_values"]` is re-anchored in the same commit. Sentence-level substitution silently breaks gate #102. Also in the paragraph and unaffected: `For this book's rate configuration the convention is therefore signed`.
- **tex 312** (§V.E, seventh qualification):
  > `The two specification choices that are not floor corrections both run the other way: the additive form returns $+11.2$ points at the same off-window anchors, nearly floor-invariantly, and it is what sets the hull's upper end, while \citepos{fonseca2024} anchor would put the marginal at $+11.5$ points at the production floor…`

  This is DA-C2's false completeness claim. B2's rows are two of the three counterexamples. **Correction of this sentence is WP-B1's, not B2's** — B2 supplies the number, B1 rewrites the sentence. Noted here so the two commits are sequenced correctly.
- **tab:assembly, tex 314–334** (`\label{tab:assembly}` at 317; nine rows, columns `Reading & Marginal (pp) & vs.\ $+5.6$ & Status`). Rows added: `Moving-share bracket, $s = 0.5$` and `Moving-share bracket, $s = 0.25$`, Status column reading `bracket, not an estimate (run \texttt{moving\_share\_bracket\_offwindow})`. Gate #98's `ASSEMBLY_TABLE_SPANS` (liveness_gates.py:426–431) pins four spans by presence, not row count — **adding rows is gate-safe**; WP-B1 may add pins.
- **tab:uncertainty headline row, tex 357** — one clause appended to the Calibration-range cell, beside the existing `concave transform $+5.1$` and `Ginnie overlay $+4.4$` entries.
- **tab:runindex, tex 707** — current row:
  > `\texttt{moving\_share\_bracket} & Gap response confined to a share of the voluntary hazard; construct-mismatch bracket (Section~\ref{sec:pathb}) \\`

  One new row for the off-window tag.
- **tab:verdicts, tex 1378–1400** — `moving_share_bracket` currently has **no** verdict row (verified). WP-B1 adds one; B2's landing rule supplies its Outcome and Adjudication cells (direction: *against the headline* under Branches B/C, *neutral* under A).

### B2.8 What this run must NOT change

The headline `+5.6` pp / `+$42.6` billion; the in-sample `+9.2` pp; the in-sample moving-share literals at tex 255 (gate-#102-pinned); the binding interval `$+2.8$ to $+8.7$` (currently **7** occurrences, tex 45, 76, 301, 312, 592, 605, 611, **plus the and-form `$+2.8$ and $+8.7$` ×2** at tex 30 and 96 — grep and-forms, per the round-26 lesson); the percentile read `$+3.0$ to $+8.0$` (**4**: tex 301, 312, 592, 605); the hull `$+3.5$ to $+13.1$` (**7**); `config.py` production defaults; the committed `moving_share_bracket_results.json`; and any `.tex` file (the run writes only its artifact).

---

## C4 — `bootstrap_pathb_cluster` at the in-sample 4.0% floor

### C4.1 Run name and tag

- **Run tag:** `bootstrap_pathb_cluster` (in-sample cell). Manuscript reference: `\texttt{bootstrap\_pathb\_cluster}` at the 4.0% floor — the same run tag as the committed off-window cell, distinguished by its floor label, following how `floor_form_offwindow` reports parity and off-window cells under one tag.
- **Command:** `cd hazard && python3 bootstrap_pathb_cluster.py --reps 200 --floor 4.0`
- **Artifact:** `hazard/data/bootstrap_pathb_cluster_results_floor4.0.json` + `..._draws_floor4.0.csv`.

### C4.2 Required pre-committed script patch (minimal, four changes)

The run **cannot** be executed against the script as it stands. The patch is part of this spec and is committed *before* the run.

1. **Floor-tagged output paths.** `RESULTS_JSON` / `DRAWS_CSV` (bootstrap_pathb_cluster.py:130–131) become functions of `args.floor`, with the existing filenames preserved exactly when `floor == DEFAULT_FLOOR_PCT` (4.991) so the committed off-window artifact and **gate #84** (`tools/liveness_gates.py:4159–4177`) are byte-identical and still PASS. `DRAWS_CSV` is opened `mode="a"` (line 252) — without this, the in-sample draws would be appended to the committed off-window draws file.
2. **Floor-conditional parity anchors.** `COMMITTED_CENTRAL_B` / `COMMITTED_NULL_B` / `COMMITTED_MARGINAL_PP` (lines 140–142) become a floor→anchor map. At 4.0%: `central 818.5300844066606`, `null 748.1850239867648`, `marginal_pp 9.198459770709789` (`no_lockin_null_results.json`). As written, G1 at floor 4.0 fails and `SystemExit`s at line 231.
3. **Comparison baseline made floor-correct.** `WITHIN_STRATUM_WIDTH_PP` (line 148) is the 4.0% within-stratum width — at the in-sample floor it becomes the *same-floor* comparison, which is what the R1 ratio is for. Record explicitly in the artifact that the in-sample R1 ratio is a like-for-like comparison, where the off-window one was not.
4. **`classify()` neutered at this floor.** `classify()` (lines 188–196) partitions against `FLOOR_READ_CI_PP`, the **off-window** floor read's percentile interval `[2.974329560125351, 8.01850965353176]`. Comparing an in-sample marginal's cluster width to an off-window floor-read width is a category error. The patch keeps `classify()` unchanged and **records its output as `verdict_offwindow_reference_only`**, with the operative comparison at this floor being the in-sample **calibration box** (`$+2.1$ to $+13.2$`, width 11.1 pp) and the within-stratum width. This is a pre-commitment against a post-run reading of a T-tier that does not apply.

Everything else — the cluster resample (`cluster_resample`, lines 151–163: 130 stratum_ids drawn with replacement, every loan of each drawn stratum, resample `rng = default_rng(rep)`), engine seed 42 fixed, `regimes=("US",)`, paired central/null per replicate, raw-basis scoring — is **unchanged**.

### C4.3 Held at production

`LOAN_SAMPLE_PATH`, `RNG_SEED = 42`, US-only regime, one shared macro frame, `LITERATURE_COEFS`, `FLOOR_MODE = "max"`, `p_q ∈ {6.5, 0}`, scorer basis. `literature_hazard.INVOLUNTARY_CPR_ANNUAL` is restored to `PRODUCTION_FLOOR` in the `finally` with a post-restore assertion (lines 263–265) — at floor 4.0 that restore is a no-op, and the assertion still holds.

**Regime-tuple invariance is established, not assumed.** `bootstrap_pathb_cluster`'s G1 reproduced `oos_identification`'s 4.991% legs (produced under the `("US","Danish")` tuple) **bit-exactly under `regimes=("US",)`** — recorded in the committed artifact as `got == want` to 16 digits. The US leg is regime-tuple invariant. G1 at 4.0% re-verifies this against the two-regime `no_lockin_null` anchors.

### C4.4 Replicate count and its own noise

- **`--reps 200`.** The script default **is** 200 (line 201) and the off-window run used 200 (`n_reps: 200`). No divergence to flag; 200 is mandated for comparability and because gate #84 asserts it for the off-window cell.
- **Monte Carlo noise of the percentile endpoints at B = 200**, computed from the off-window replicate sd (0.6044572173024999) under a normal approximation, `se(q_p) = σ√(p(1−p)/B)/φ(z_p)`: **≈ 0.114 pp per endpoint**, so **≤ ≈0.16 pp on the width**. The 0.5 pp materiality threshold below is therefore **>3× the MC noise** — that is its justification, and it is stated ex ante rather than chosen after seeing the number.
- **The design's own limit is not fixable by more replicates.** `effective_n_clusters = 25.77710660741266` on 130 strata (largest 9.77% of balance, top five 35.3%). A percentile interval on ~26 effective clusters is itself noisy, and no correction (Webb/wild-t) is run for this scheme — the committed tablenote at tex 364 already says so: `No such correction is run for the loan/stratum scheme, whose interval is still better read as a lower bound on sampling uncertainty than as calibrated 95\% coverage.` This carries to the in-sample cell verbatim.

### C4.5 Pre-committed expectation, with derivation

**Committed inputs:** within-stratum at 4.0% (`bootstrap_pathb_results.json`): `marginal_pp p2_5 9.166412038908136`, `p97_5 9.228594662666818`, `sd 0.016399089265543645`, width **0.0622 pp**. Cluster at 4.991% (`bootstrap_pathb_cluster_results.json`): `[4.630919609903703, 6.924433300615744]`, `sd 0.6044572173024999`, width **2.2935136907120413**, `R1_width_ratio_vs_within_stratum 36.87321046160797`.

**Projection (coefficient-of-variation preservation).** The cluster scheme perturbs *composition*; the marginal's composition sensitivity scales with the marginal's own magnitude. Off-window CV = 0.6045/5.683 = 0.1064. Scaling by `9.198459770709789 / 5.571558182909726 = 1.651`:

- **expected sd ≈ 1.00 pp, expected width ≈ 3.79 pp, expected interval ≈ [+7.3, +11.1] pp**
- implied `R1` ratio vs within-stratum ≈ **61×** (against 37× off-window)
- vs the in-sample **calibration box** width (11.1 pp): ratio ≈ 0.34 — the box would remain the wider layer.

**Counteracting consideration, stated ex ante:** censoring is *lower* at 4.0% (36.3% vs 68.8% bind), so composition perturbations pass through less truncated — which argues for the sd scaling at least proportionally, i.e. the projection is if anything conservative. **Materiality band on the width: ±1.0 pp** around 3.79.

**Honest statement of what is and is not open.** The 0.5 pp materiality threshold below is very likely to be crossed — the projection exceeds it by 7×, and even the absolute-sd-preservation floor (2.29 pp) exceeds it by 4.6×. Branch (b) is kept live because it is the *only* outcome under which the seven-site claim survives, and pre-committing it is what makes branch (a) a finding rather than an assumption. If (b) fires it is a strong finding about the design (composition variance is floor-dependent to a degree nothing predicts) and must be reported as such.

### C4.6 Parity and identity checks (BLOCKING)

- **G0 (free, no engine):** `score_extension_risk` empirical benchmark `== 764.7482532227002` to < 1e-9 (input-drift detector; distinguishes FRED/SOMA revision from engine drift, per `burnout_ablation` G0a).
- **G1 (unresampled parity, bit-exact, `TOL_PARITY = 1e-9`):** the unresampled 75k sample at floor 4.0% must reproduce `central 818.5300844066606` and `null 748.1850239867648`. On FAIL the run is **void, not unfavourable** — the existing `SystemExit` text (lines 231–235) is retained verbatim.
- **G1b (derived marginal):** `marginal_b == 70.34506041989584` and `marginal_pp == 9.198459770709789` to < 1e-9.
- **G2 (cluster-structure invariance):** `effective_n_clusters == 25.77710660741266`, `n_clusters == 130`, `largest_cluster_balance_share == 0.09769928846876974` to < 1e-9. The cluster structure is a property of the loan sample, not the floor, so these must be **identical** to the off-window run. A mismatch means the sample changed and everything downstream is incomparable.
- **G3 (committed-artifact integrity, run after):** re-read `bootstrap_pathb_cluster_results.json` and `..._draws.csv`; assert byte-identical to their pre-run hashes, and that **gate #84 still PASSes**. This is the guard against finding (2) above.
- **R1 (reported, obliging only itself):** width ratio vs the same-floor within-stratum width 0.0622 pp.
- **R2 (reported):** whether `+9.198459770709789` lies inside the cluster interval. Outside would mean the point estimate is not central to its own resampling distribution.
- **R3 (reported):** `verdict_offwindow_reference_only` = `classify()`'s output, explicitly labeled non-operative at this floor (see patch item 4).

### C4.7 Artifact path and fields

`hazard/data/bootstrap_pathb_cluster_results_floor4.0.json` — same schema as the committed off-window artifact (`mode`, `spec`, `floor_annual_cpr_pct`, `n_reps`, `cluster_structure`, `parity_gates`, `parity_gates_all_pass`, `central_share_pct`, `null_share_pct`, `marginal_pp`, `marginal_b`, `n_loans`, `comparison`, `verdict`, `runtime_s`), with three additions: `comparison.within_stratum_same_floor` (true), `comparison.vs_calibration_box_width_pp`, `verdict_offwindow_reference_only`, and `materiality{threshold_pp: 0.5, mc_se_width_pp, branch}`. Draws to `..._draws_floor4.0.csv`. Expected runtime ~35 min (off-window: 2110 s).

### C4.8 Landing rule (pre-committed; branch on the cluster interval **width** at 4.0%)

**Materiality threshold, fixed ex ante: width > 0.5 pp.** Justification recorded above: >3× the B=200 Monte Carlo noise on the width (≈0.16 pp), and 8× the committed within-stratum width (0.0622 pp), so it is a threshold on a real difference rather than on resampling noise.

> **Branch (a) — width > 0.5 pp** ("materially wider"). The 37× understatement carries to the in-sample floor. **Disposition, all eight sites:**
>
> 1. **tex 45** (§I): `(sampling 95\% confidence interval $[+9.17, +9.23]$ points from a 200-replicate paired loan-level bootstrap; sampling and seed noise are negligible at reporting precision, so the operative uncertainty is calibration, Table~\ref{tab:uncertainty})` → the interval is **requalified** as the within-stratum scheme's and the measured cluster interval quoted beside it; **the "negligible at reporting precision" clause is STRUCK.** ⚖ (this clause is the hierarchy claim the panel names).
> 2. **tex 65** (tab:headline caption): `The uncertainty hierarchy is established in Table~\ref{tab:uncertainty}: sampling and simulation-seed noise are negligible at reporting precision; the calibration box is the operative uncertainty` → **strike** "sampling and"; the seed claim survives independently (`under \$0.01 billion across ten paired reruns`, tex 343). ⚖
> 3. **tex 78** (tab:headline row): `sampling CI $[+9.17, +9.23]$; calibration box $+2.1$ to $+13.2$; Fannie replication $+8.68$` → the cell carries both schemes' intervals, within-stratum labeled as such.
> 4. **tex 272** (§V.C): `…and the paired lock-in marginal's at $[+9.17, +9.23]$ points (standard deviation 0.016). Those intervals are narrow because the scheme holds the design fixed…` → the in-sample cluster interval joins the off-window one in the sentence that already performs the retraction; `$[+4.63, +6.92]$` (2 occurrences, tex 272 and 357) and `factor of $37$` (gate-#84-pinned, tex 272) **must survive verbatim**.
> 5. **tex 301** (§V.E, third qualification): `Third, the marginal's sampling precision is not the operative uncertainty: the stratified loan-level bootstrap puts the paired marginal at $[+9.17, +9.23]$ points (Section~\ref{sec:pathb}), so the calibration box, not simulation noise, governs the interval.` → the *conclusion* may survive (the box at 11.1 pp is expected to remain wider than ~3.8 pp) but the *premise* is replaced: the cluster interval, not the retracted one, is what the box is ranked against. ⚖
> 6. **tex 343** (tab:uncertainty lead-in): `The hierarchy it displays is the one argued above: sampling error is negligible at the paper's reporting precision, the draw-seed contribution is smaller still…` → same strike as (2). ⚖
> 7. **tex 359** (tab:uncertainty, in-sample row): `$[+9.17, +9.23]$pp (sd $0.016$)` → gains the cluster interval, symmetric with the headline row at tex 357.
> 8. **tex 1391** (tab:verdicts): `Ex-ante stratified loan bootstrap, strata held fixed (Section~\ref{sec:pathb}) & CI $[+9.17, +9.23]$ & Superseded: the cluster scheme showed a $\sim$37$\times$ understatement of loan-sampling uncertainty; the committed claim retracted (against the headline)` → the Adjudication cell gains "at both floors" and the in-sample ratio.
>
> **NOT a site: tex 1360** — `Convexity-matched flat 4.0090\%\tnote{c} & --- & --- & $+70.156$ & $+9.17$ & 1.0029 & $-0.204$` in tab:seasonalfloor is a marginal *value*, not the bootstrap interval. Do not touch. (This is the miscount in REVIEW2 #6.)

> **Branch (b) — width ≤ 0.5 pp** ("not materially wider"). The eight sites are **kept as written** and each gains the clause *"verified under the stratum-cluster scheme"* with the measured in-sample cluster interval in the tablenote at tex 364. The finding is then reported affirmatively: composition variance at the in-sample floor is negligible where it is not at the headline floor, and tex 272's retraction sentence gains "at the headline floor" as a scope qualifier.

Both branches additionally: one row added to **tab:runindex** (tex 693–740) and one row to **tab:verdicts**, and the tablenote at **tex 364** (`Both cluster bootstraps above rest on few clusters: 31 carry the floor read, and the loan/stratum scheme's 130 strata are unequal enough to be worth 25.8 effective ones… No such correction is run for the loan/stratum scheme…`) gains the in-sample cell — the sentence needs no change, only extension.

### C4.9 What this run must NOT change

`bootstrap_pathb_cluster_results.json` and `..._draws.csv` (committed off-window; **G3 enforces byte-identity**); gate #84's PASS state; the off-window cluster interval `$[+4.63, +6.92]$` (2 occurrences) and `factor of $37$` and `25.8` (3 occurrences) — all gate-#84-pinned tex literals; the point marginals `+9.2` pp and `+5.6` pp; the calibration box `$+2.1$ to $+13.2$`; the binding-layer designation on the *headline* row (which is about the floor read, not the loan sample); tex 1360.

---

## C5 — `covariate_ablation_offwindow`: the covariate block at the headline floor

### C5.1 Run name and tag

- **Run tag:** `covariate_ablation_offwindow`.
- **New script:** `hazard/covariate_ablation_offwindow.py`, modeled **directly on `burnout_ablation.py`**, which is the correct template and not merely a convenient one: `burnout_ablation.py`'s own header (lines 63–95) names this exact run as the follow-up, and states why it must not be a fourth scenario inside `covariate_priors_estimation.py`:

  > *"covariate_priors_estimation.py's 'production' comparator should either be replaced by a fresh replay gated against no_lockin_null_results.json, or cross-gated against this script's G1, so the FICO/LTV 1.3-point literal acquires the parity the burnout literal was missing."*

  The four reasons given there apply verbatim: (a) `covariate_priors_estimation` reads its production comparator out of the cached `microsim_results.parquet` and **never replays it** — zero parity discipline; (b) it drags in `PANEL_PATH`, `HAZARD_COEF_PATH`, `statsmodels` and a 60-rep bootstrap before it touches the microsim; (c) it runs **one floor and no β₁ = 0 null**, so it cannot state the sensitivity at the headline floor and cannot state it as a marginal; (d) the missing artifact/gate/TECHNICAL record attaches to a run.
- **Artifact:** `hazard/data/covariate_ablation_offwindow_results.json` (the committed `covariate_priors_results.json` is not overwritten).

### C5.2 Engine entry point and exact parameterization

- **Coefficients are PINNED, not re-estimated.** The Poisson PML on the Freddie stratum-month panel is **floor-independent** — the floor enters nowhere in `hazard_fit` — so the committed estimates are re-used as *inputs*: `beta_fico = -0.393082485292068`, `beta_ltv = 0.20848086275975533` (`covariate_priors_results.json → estimated.*.point`), consumed at runtime and asserted equal to 1e-12. This guarantees the only moving part is the floor.
  - **Optional cheap identity gate (recommended, ~seconds):** one un-bootstrapped re-fit via `covariate_priors_estimation.fit_credit_betas` must reproduce both to < 1e-9. The 60-replicate bootstrap (`N_BOOT = 60`) is **skipped** — its CIs `[-1.5060737810435332, 0.6526556714566496]` / `[-0.5895575436619275, 1.0030619130400864]` are committed and unchanged.
- **Coefficient installation:** `literature_hazard.LITERATURE_COEFS` mutated **in place** (`clear` + `update` in a `finally`, with a post-restore assertion), exactly as `burnout_ablation.py` does and for the reason its header records: `prepay_hazard` takes a `coefs` argument but `competing_risks.monthly_step` never forwards it, so the parameter is unreachable from the engine and in-place mutation is the only route. **Verified against `competing_risks.py` and `literature_hazard.py:98` (`c = coefs or LITERATURE_COEFS`).**
- **Floor:** `literature_hazard.INVOLUNTARY_CPR_ANNUAL` set per leg, restored to `0.04` with assertion.
- **Engine:** `run_qt_microsim(loan_sample=loans, macro=macro, regimes=("US",), seed=42, output=<own parquet>, p_q_shock_pct=pq)`. Note `run_qt_microsim` applies `calculate_dynamic_friction(fetch_data())` internally when `macro is None` (microsim_engine.py:104–105), so `covariate_priors_estimation`'s explicit `calculate_dynamic_friction(fetch_data())` and `floor_sweep`'s implicit path are equivalent — **verified, and it is why parity is achievable across the two scripts.**
- **Bind instrumentation:** the value-preserving tally wrapper of `floor_sweep`/`oos_identification`/`burnout_ablation`. Since this run does **not** install a variant hazard function, the `_ORIG_PREPAY` seam gotcha does not arise; the wrapper is used in its standard form.
- **Leg set — 12 US-regime microsim runs** (`{production priors, β_F=β_L=0, re-estimated} × {p_q 6.5, p_q 0} × {floor 4.0%, floor 4.991%}`). "Both legs" is read in both senses deliberately: both **covariate variants** and both **central/null legs**, at both floors. The null legs are required for the same reason `burnout_ablation` requires them — β_F/β_L are not the elasticity, they enter both legs, so the covariate sensitivity *of the marginal* must be re-differenced rather than assumed invariant. The 4.0% legs double as parity and give the first committed measurement of the covariate block's effect on the **marginal**, which does not currently exist anywhere.
- **Runtime:** ~12 × 25–45 s ≈ 6–9 min plus one benchmark fetch (`burnout_ablation` ran 8 legs in 45.8 s including the fetch).

### C5.3 Held at production

Loan sample, `RNG_SEED = 42` passed explicitly, US-only regime (regime-tuple invariance established — see C4.3), one shared macro frame, `FLOOR_MODE = "max"`, `beta_burnout = -0.5`, `beta1` from `p_q ∈ {6.5, 0}`, scorer basis, `config.py` untouched.

### C5.4 Pre-committed expectation, with derivation and direction logic

**Committed inputs.**

| quantity | value | source |
|---|---|---|
| production central, 4.0% | `818.5300844066606` / `107.0326190295068` | `covariate_priors_results.json → production`; `no_lockin_null_results.json` |
| β_F=β_L=0, 4.0% | `828.2105611766495` / `108.29845739254911` | `covariate_priors_results.json → zeroed` |
| re-estimated, 4.0% | `774.5297606295118` / `101.27904932970971` | `covariate_priors_results.json → reestimated` |
| in-sample swing | **+1.266 pp up, −5.754 pp down; total 7.019 pp = $53.68B** | derived |
| shared-basis image | `92.18`–`99.20` (standalone − 9.096091632702699) | derived; matches the printed `92.2--99.2` |
| central bind share | 4.0%: `0.36269282595934704`; 4.991%: `0.6881875607501289` | `oos_identification_results.json` |

**Direction logic (the censoring argument).** Under the hard maximum `h = max(f, h_vol)`, a perturbation to `β_F`/`β_L` moves `h_vol` multiplicatively and is **absorbed wherever the floor binds**. Raising `f` from 4.0% to 4.991% raises the central leg's bind share from 36.3% to 68.8%, i.e. cuts the uncensored loan-month share from **0.6373 to 0.3118**, a first-order compression factor of **0.489**. These are unweighted loan-month counts, not balance-weighted shares — the manuscript flags this itself at tex 301 (`these are unweighted loan-month counts, not balance-weighted shares, so nothing follows from them about what fraction of the dollar marginal the uncensored months carry`) — so the proxy is an ordering expectation, not a point.

**Empirical calibration of the proxy (the reason this expectation is trustworthy).** The β_B = 0 ablation has *already* been run at both floors under exactly this design (`burnout_ablation_results.json`, tex 263), and it calibrates the compression directly:

- **level:** `delta_pp` **−0.8607272887573743** @4.0% → **−0.4547025015657056** @4.991% ⇒ factor **0.528**
- **marginal:** `marginal_delta_pp` **+0.7432337069787138** @4.0% → **+0.9427230127140547** @4.991% ⇒ factor **1.269**

The measured level compression (0.528) sits within 8% of the uncensored-share proxy (0.489). The manuscript already states the mechanism at tex 263: `because the floor's bind share rises from 36.3\% to 68.8\% of evaluated loan-months and the hard maximum makes burnout inert wherever it binds.`

**Pre-committed expectations.**

- **LEVEL swing: compresses.** Central projection **factor 0.52** (band **[0.45, 0.60]**, spanning the burnout precedent and the uncensored-share proxy). Projected off-window total swing **≈ 3.7 pp (≈ $28B)**, range 3.2–4.2 pp; standalone endpoints ≈ `97.3%` to `101.0%`, shared ≈ **88.2%–91.9%** against the in-sample `92.2–99.2%`.
- **Asymmetry, signed:** the **downward-hazard** leg (β_F=β_L=0, which *raises* trapped liquidity) should compress **at least as much as** the upward-hazard leg (re-estimated, which lowers it), because a downward push on `h_vol` is fully absorbed once it falls below the floor whereas an upward push is only partially absorbed. The burnout precedent is an upward-hazard perturbation, so 0.528 is the *less*-compressed reference.
- **MARGINAL sensitivity: direction NOT signed.** The burnout precedent went the **other way** (amplified 1.27×): raising the floor compresses the level swing while *amplifying* the marginal swing, because the null leg's floor-pinning (35.8% vs 14.3%) shifts too. No signed pre-commitment is made for the marginal. It is reported with the **±1.0 pp** materiality convention and nothing is read into its direction after the fact.
- **Materiality band on the level projection: ±1.0 pp** on the total swing.

### C5.5 Parity and identity checks (BLOCKING; bit-exact `< 1e-9`, per `burnout_ablation`)

**Free gates (no engine; run first so input drift is caught in seconds):**
- **G0a** benchmark: `score_extension_risk` empirical `== 764.7482532227002`.
- **G0b** committed production cache `microsim_results.parquet` rescored `== 818.5300844066606`.
- **G0c** committed null cache `microsim_results_pq0.0.parquet` rescored `== 748.1850239867648`.
- **G0d WIRING, analytic:** with `fico_z = 1, ltv_z = 0`, floor asserted non-binding, `h(β_F=0)/h(β_F=−0.15) == exp(0.15)` to 1e-12; symmetric probe for `β_L`. A FAIL means the override does not reach the hazard and every number below is meaningless.
- **G0e LEAK, analytic:** with `fico_z = ltv_z = 0`, the three coefficient settings must give **identical** hazards (diff exactly 0.0), because β_F/β_L multiply those covariates. A FAIL means the override leaks into a non-covariate channel and BLOCKS interpretation.
- **G0f COEFFICIENT PROVENANCE:** the pinned estimates equal `covariate_priors_results.json → estimated.beta_fico.point / beta_ltv.point` to 1e-12.
- **G0g BASIS:** `calibration_reconciliation_results.json → basis_map` internally consistent (`offset_pp == 69.56220187263008 / 764.7482532227002 × 100 == 9.096091632702699`) and reproduces shared `97.93652739680411` from standalone `107.0326190295068`.

**Engine gates (fresh runs, production coefficients):**
- **G1** production central @4.0% `== 818.5300844066606`; **G2** production null @4.0% `== 748.1850239867648`; **G3** marginal @4.0% `== 70.34506041989584` / `+9.198459770709789` pp; **G4** shares @4.0% `== 107.0326190295068` / `97.83415925879702`.
- **G5** production central @4.991% `== 767.5264524465003` **and** null @4.991% `== 724.9180585654117` (`oos_identification_results.json`). *This is the parity `covariate_priors_estimation` never had, and the reason the new script exists.*
- **G6** bind anchors: central @4.0% `0.36269282595934704`, central @4.991% `0.6881875607501289`, null @4.0% `0.14340654639824515`, all over `1683124` loan-months.
- **G7 CROSS-ARTIFACT REPLAY:** the fresh `β_F=β_L=0` and re-estimated legs **at 4.0%** must reproduce `covariate_priors_results.json → zeroed.trapped_b == 828.2105611766495` and `reestimated.trapped_b == 774.5297606295118` to < 1e-9. **This is the run's most important gate**: it retro-fits parity to the currently unparried 108.3/101.3 literals, and a FAIL means the committed covariate literals were produced under a different convention and the in-sample sites need repair before anything off-window can be reported.
- **G8 RESTORATION:** after every leg, `LITERATURE_COEFS == {beta_fico: -0.15, beta_ltv: 0.10, beta_burnout: -0.5, …}` and `INVOLUNTARY_CPR_ANNUAL == 0.04`, asserted inside the leg runner.

### C5.6 Artifact path and fields

`hazard/data/covariate_ablation_offwindow_results.json`

```
mode, spec (verbatim header), parity_tolerance (1e-9),
pinned_coefficients{beta_fico, beta_ltv, source, refit_identity_pp},
basis_map{curtailment_netted_b, cap_benchmark_b, offset_pp, note},
legs{prod|zeroed|reest × central|null × floor4|floor4991}: tag, coefs, floor_annual_cpr_pct,
  p_q_shock_pct, beta1, trapped_b, share_pct_standalone, share_pct_shared, r_lag0, peak_lag,
  mean_us_cpr_pct, floor_bind_share, floor_bind_loan_months,
parity_gates{G0a..G8}, parity_gates_all_pass,
block_at_production_floor{zeroed_delta_pp, reest_delta_pp, total_swing_pp, total_swing_b,
                          marginal_prod_pp, marginal_zeroed_pp, marginal_reest_pp,
                          marginal_swing_pp},
block_at_offwindow_floor{ same fields },
compression{level_zeroed, level_reest, level_total, marginal_total,
            burnout_precedent_level 0.5283, burnout_precedent_marginal 1.2685,
            uncensored_share_proxy 0.4893, within_band_045_060, asymmetry_ok},
comparison_vs_marginal{swing_pp_offwindow, marginal_pp_offwindow 5.571558182909726,
                       ratio, insample_ratio 0.7631, exceeds_marginal},
landing_branch, runtime_s
```

### C5.7 Landing rule (pre-committed)

**Unconditional in every branch:**

- **tab:uncertainty gains the off-window covariate row/clause.** Currently the covariate entry lives only in the *in-sample level* row, tex **355**: `Path B central level (in-sample calibration) & 97.9\%; 107.0\% & … & covariate priors 92.2--99.2\%; elasticity band 96.8--99.1\% (shared basis); off-window floor 91.3\% shared (88.2--93.7\% across its range)`. The measured off-window covariate range is added, labeled with its floor, **and** the newly-measured covariate sensitivity *of the marginal* enters the headline row's Calibration-range cell at tex **357**, beside `concave transform $+5.1$` and `Ginnie overlay $+4.4$`.
- **tex 263** (§V.C, the primary site) gains the off-window pair. Current text:
  > `The FICO and LTV covariates receive the same treatment: a $\beta_F = \beta_L = 0$ rerun moves the recovery to 108.3\% ($+1.3$pp), and a rerun under coefficients estimated Path-A-style from the panel moves it to 101.3\% ($-5.7$pp); Appendix~\ref{app:params} reports the estimation…`

  The in-sample figures are retained with an explicit `at the in-window 4.0\% floor` label — the same construction the adjacent burnout sentence already uses in this very paragraph (`It is measured at the in-window 4.0\% floor; at the 4.991\% off-window floor the paper headlines the same ablation is worth only \$3.48 billion ($-0.45$pp), because the floor's bind share rises from 36.3\% to 68.8\% of evaluated loan-months and the hard maximum makes burnout inert wherever it binds.`). **This sentence is the model for the covariate landing** — same paragraph, same mechanism, already accepted.
- **tex 911** (App. D, tab:params notes): `The sensitivity brackets are correspondingly modest: a $\beta_F = \beta_L = 0$ rerun moves the recovery from 107.0\% to 108.3\%, and the panel-estimated pair moves it to 101.3\%` → gains the off-window pair; **"correspondingly modest" must be re-checked against the measured off-window numbers rather than carried forward.**
- **tex 79** (tab:headline): `covariate priors 92.2--99.2\% (in-sample)` — already carries the `(in-sample)` label; extended, not corrected.
- **tab:runindex** (tex 693–740) gains one row; **tab:verdicts** gains one row (the covariate block currently has none).

**Branch on the "largest single sensitivity" sentence — tex 301:**

> `The covariate-prior swing of Section~\ref{sec:pathb} is also comparable in size to the marginal itself.`

The comparison is the covariate **level swing** (points of benchmark) against the **marginal** (points of benchmark). In-sample: `7.019 / 9.198 = 0.763`. Projected off-window: `3.7 / 5.572 ≈ 0.66`.

> **Branch (i) — off-window swing ≥ the off-window marginal (`swing_pp ≥ 5.572`).** The sentence **is strengthened and restated at the headline floor**: the covariate block is the paper's largest single sensitivity *where the headline lives*, and it exceeds the quantity it perturbs. ⚖ This is the only branch that changes what the sentence claims, and it moves it against the headline. Requires the DA-M1 disclosure to be promoted from §V.E's qualification list to the headline-adjacent sites.

> **Branch (ii) — `0.5 × marginal ≤ swing_pp < marginal`** (**the projection's branch**, ratio ≈ 0.66). The sentence **stands**, gains the floor label and the measured off-window figure: `comparable in size to the marginal itself at both calibrations`. No claim changes. This is the expected outcome and is *not* a null result — it establishes that the largest disclosed sensitivity does not shrink relative to its target when the floor is corrected, which is what DA-M1 asks and what no committed run currently answers.

> **Branch (iii) — `swing_pp < 0.5 × marginal`.** The sentence is **requalified to in-sample only**: `comparable in size to the marginal itself at the in-sample calibration; at the headline floor the hard maximum censors most of the covariate channel and the swing falls to <X> points.` ⚖

**Independently reported in every branch, obliging only itself:** the covariate sensitivity **of the marginal** at both floors (the object that does not currently exist). If it exceeds the ±1.0 pp materiality convention at the off-window floor, it enters tab:uncertainty's headline row **and** the tab:assembly rebuild as a two-sided entry — the re-estimated leg's direction is not pre-signed and may enter as an **upward** counterweight, which is symmetric with WP-B1's whole point.

### C5.8 What this run must NOT change

The headline `+5.6` pp / `+$42.6` billion (the covariate block is a sensitivity, never a headline input); the in-sample literals `108.3\%` and `101.3\%` at tex 263 and 911 and `92.2--99.2` at tex 79 and 355 (retained, floor-labeled — unless G7 FAILs, in which case the run halts and the in-sample literals are the finding); the committed `covariate_priors_results.json`; the committed coefficient estimates and their CIs; `config.py` `LITERATURE_COEFS` (mutated in place, restored, asserted); `beta_burnout = -0.5` (burnout is `burnout_ablation`'s remit); the floor form (the form dimension is `floor_form_offwindow`'s remit); any `.tex` file.

---

## Cross-cutting notes for the coordinator

**Sequencing.** C4 and C5 are independent of everything. **B2 must land before WP-B1's tab:assembly rebuild** — B1 needs B2's rows, and B2's tex 255 edit collides with gate #102 (see B2.7). All three specs are committed *before* execution, per the B5/TECHNICAL §43 protocol.

**Zero-slack recon at execution start (re-derived by me now, 2026-07-28, against `paper/v18/revised_paper_v18.tex`; the plan's Decision-record snapshot agrees except where noted):**

| literal | count | lines |
|---|---|---|
| `$+2.8$ to $+8.7$` | 7 | 45, 76, 301, 312, 592, 605, 611 |
| `$+2.8$ and $+8.7$` (and-form, **not** a counted literal) | 2 | 30, 96 |
| `$+3.0$ to $+8.0$` | 4 | 301, 312, 592, 605 |
| `$+3.5$ to $+13.1$` | 7 | — |
| `$[+9.17, +9.23]$` | **6** | 45, 78, 272, 301, 359, 1391 |
| `9.17` (raw; includes the tex-1360 false positive) | 7 | + 1360 |
| `$[+4.63, +6.92]$` (gate #84) | 2 | 272, 357 |
| `92.2--99.2` | 2 | 79, 355 |
| `108.3\%` | 2 | 263, 911 |
| `68.8\%` / `36.3\%` | 3 / 5 | 263, 301, 312 / 263, 301, 312, 1234, 1328 |

The plan's snapshot records "9.17 ×7" — that count includes tex 1360, a different object. **Six sites carry the interval; eight carry the disposition** (adding tex 65 and 343, which carry the hierarchy claim without the literal).

**Gate collisions, consolidated:** gate **#102** `ELASTICITY_DISCIPLINE_SPANS["bracket_values"]` pins tex 255's in-sample moving-share clause verbatim (B2). Gate **#84** pins the off-window cluster artifact *and* three tex literals (C4 — must survive the run byte-identical). Gate **#98** `ASSEMBLY_SPANS` / `ASSEMBLY_TABLE_SPANS` pin the assembly paragraph and four table spans, including `posture_middle_member` and `posture_lower_half` — which the Decision record has already resolved (**posture RETIRED**), so B2's Branch B/C wording and B1's rebuild land against a posture that is being removed, not defended. **No test or gate references `9.17`, `covariate_priors_results.json`, `moving_share_bracket_results.json`, or `bootstrap_pathb_cluster.classify` (verified by grep over `tests/` and `tools/`)** — so C4's and C5's landings are tex-only plus the artifact cross-check gates the coordinator chooses to add.

**Posture-adjacent (⚖) elements, collected:** B2 Branches B and C (range-conditionality statement); C4 Branch (a) strikes of the "negligible at reporting precision" hierarchy claim at tex 45, 65, 343 and the premise replacement at tex 301; C5 Branches (i) and (iii) on the "comparable in size to the marginal itself" sentence. Everything else in these three specs is measurement.
