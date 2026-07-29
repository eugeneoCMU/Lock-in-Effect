Worktree root: `/Users/eugene/somthing/Lock In effect/Lock-in-Effect/.claude/worktrees/paper-v18-review-plan-5b7b5e`

---

# Round-28 run specs — WP-C1, C2, C3, C6

**Status:** drafts only. Nothing in this document changes a file. All four are executed by the coordinator under the spec-before-run rule (PLAN §0.1).

## 0. Corrections to the pointers in the tasking, verified against the tex

| Tasking said | Verified location |
|---|---|
| tab:uncertainty ~tex 345–369 | correct: `\begin{table}[!t]` at 345, `\end{table}` 368; label 348 |
| its note ~tex 399, "No single cluster dominates" | **tex 364**. tex 399 is tab:estimators' correlation-convention note (different table) |
| tex 660-area inference ladder parenthetical (grep CR2) | **tex 592** (§V.C, `sec:robustness-floor`) is the ladder; the only other `CR2` is tex 364. tex **677** is the `tab:crosswalk` row "Binding layer on the headline marginal, $[+2.8, +8.7]$pp" — that is the tex-660-area object |
| "zero-slack ×7" | **×7 is the `to`-form only.** Full literal census below |

**Binding-interval literal census (re-derived this session; per PLAN §0.2 it must be re-derived again immediately before any edit):**

| Form | Count | Lines |
|---|---|---|
| `$+2.8$ to $+8.7$` | 7 | 45, 76, 301, 312, 592, 605, 611 |
| `$+2.8$ and $+8.7$` (and-form, **uncounted by any gate**) | 2 | 30 (abstract), 106 |
| `$[+2.8, +8.7]$` (bracket-form, **uncounted by any gate**) | 3 | 76, 357, 677 |
| **total occurrences / distinct lines** | **12 / 11** | |

Gate coverage, verified in `/Users/eugene/.../tools/liveness_gates.py`: line 4342 asserts `tex.count("$+2.8$ to $+8.7$") >= 4` (a `>=`, not exact — the round-27 lesson holds); line 402 pins the to-form inside gate #98's `posture_binding_layer` span; line 460 + 503 pin the **and**-form inside gate #99's `ABSTRACT_POSTURE["interval"]` **and its ordering assert**; line 584 pins the to-form in the letter literal list. The bracket-form ×3 is pinned nowhere. `tests/test_headline_posture_gate.py:79` hard-codes the abstract and-form sentence; `:151` hard-codes `"$+2.8$ to $+8.7$ points" in ve[0]`.

---

# SPEC C1 — `floor_inference_correction_v2` (floor-read inference rerun)

## C1.0 Recovery step 0 — what was actually used (RECOVERED, no run needed)

Everything the review says is "unreported" is recoverable from the committed script header and artifact. Recorded here so the spec does not re-litigate it:

| Quantity | Value | Source |
|---|---|---|
| Weights | **Rademacher** (2-point ±1) | `/Users/eugene/somthing/Lock In effect/Lock-in-Effect/.claude/worktrees/paper-v18-review-plan-5b7b5e/hazard/floor_inference_correction.py:181` `rng.choice([-1.0, 1.0], …)`; echoed in artifact `.reads.*.wild_t.weights = "rademacher"` |
| B | **9,999** | script `B_WILD = 9999` (line 120); artifact `.reads.*.wild_t.B` |
| Seed | fresh `default_rng(42)` **per read** | script line 303 |
| Null imposition | **NOT imposed — unrestricted (WCU-t)**. DGP is `A*_g = W_g·R̂ + s_g(A_g − R̂ W_g)` (lines 180–184): the point estimate is imposed as the DGP truth and the *unrestricted* residuals are sign-flipped. The interval is a percentile-t inversion of that distribution | script lines 33–41, 174–188 |
| Studentization scale | **floor (SMM) scale.** `t* = (R*−R)/SE*` with `SE*` = CR1 on SMM; the interval `[R − q₉₇.₅·SE_CR1, R − q₂.₅·SE_CR1]` is formed on SMM, then SMM→CPR%, then the *endpoints* are mapped through the PCHIP. **Not** post-PCHIP | script lines 186–188, 298–311 |
| Studentizing SE | **CR1** in both numerator and bootstrap denominator (matched, correct) | lines 174, 185 |
| df | **fixed at G−1**; `t_crit_G_minus_1 = 2.0422724563012373` (df=30) for R1/R2, used only for the CR1/CR2/CR3 *t*-intervals | line 292; artifact `.reads.*.t_crit_G_minus_1` |
| Leverages | only `max_leverage` is persisted (R1 0.27808, **R2 0.33233**, R3 0.38157, R4 0.16607). **The full h vector is NOT in the artifact** | artifact `.reads.*.max_leverage` |

**The one genuine recovery task:** the full leverage vector `h_g = W_g/ΣW` per read, and the 9,999 `t*` draws, are computed and discarded. Both are needed (h for G\*, t\* for C2). They are deterministic and cheap to regenerate — total committed runtime `.runtime_s = 9.1`. Step 0 of the run is therefore *recompute and persist them*, under the bit-exact parity gates below.

## C1.1 Run name and engine entry

- **Run name:** `floor_inference_correction_v2`
- **New file:** `/Users/eugene/somthing/Lock In effect/Lock-in-Effect/hazard/floor_inference_correction_v2.py` (new script; the committed `floor_inference_correction.py` and its artifact are **frozen and must not be edited or overwritten**).
- **Imports, not reimplements** (same discipline as the v1 script):
  - `floor_uncertainty as fu` → `fu._select`, `fu.LEG_2018`, `fu.CALIB_WINDOW`, `fu.cluster_bootstrap_cpr`, `fu._map_draws`
  - `matched_depth_reconciliation as mdr` → `mdr.build_panel`, `mdr.cpr_of`, `mdr.FloorMapping`
  - `stratum.build_stratum_id`
  - copies verbatim from v1: `cpr_pct_of_smm`, `cluster_sums`, `cr_ses`, `map_endpoint`, `map_floor_ci`, and the four `READ_SELECTIONS`
- **No engine run anywhere.** One FRED `MORTGAGE30US` fetch via `mdr.build_panel`. Does not touch `config.py`. Does not edit any `.tex`.

## C1.2 Parameterization

Reads R1–R4 exactly as v1 (R5 excluded ex ante, as in v1). Primary object stays **R2** (`R2_2018_gap<=-0.0025_age>=12`, G=31, point 4.990624060575566% → +5.5716pp).

**(1) Webb six-point weights (primary change).** Replace the 2-point draw with
`s ∈ {−√(3/2), −1, −√(1/2), +√(1/2), +1, +√(3/2)}`, each with probability 1/6 (Webb 2014). E[s]=0, E[s²]=1 (verify numerically as a self-test), E[s⁴]=7/6. B=9,999, fresh `default_rng(42)` per read, everything else identical. **Report the Rademacher interval alongside** — recomputed in the same run under the same rng-42 convention, and gated to reproduce the committed artifact bit-exactly (gate P4 below). Both weight schemes, both reported; the Webb line is the primary.

**(2) Bell–McCaffrey / Imbens–Kolesár data-driven df** for the CR2 and CR3 *t*-intervals (secondary objects; no rule attached, matching v1). Do **not** use a closed-form recollection. Compute it from the construction:
- Working model: the estimator `R = ΣA/ΣW` is the GLS/WLS estimator of `A_g = R·W_g + ε_g` under `Var(ε_g) ∝ W_g`; the corresponding WLS leverage is `h_g = W_g/ΣW`, which is exactly the `h` the committed script already computes (line 169). The CR2 adjustment `u_g/√(1−h_g)` is therefore the correct BM adjustment for that working model.
- Write `V̂_CR2 = Σ_g (g_g′ε)²`; form the G×G matrix `G` whose rows are `g_g′Ω^{1/2}` under the working `Ω = diag(W_g)/ΣW`; set `df = (tr(GG′))² / tr((GG′)²) = (Σλ_i)²/(Σλ_i²)` over the eigenvalues of `GG′`.
- **Mandatory self-test (blocking):** with `h_g ≡ 1/G` (equal clusters) the construction must return `df = G−1` to 1e-8. If it does not, the implementation is wrong; **STOP**, do not report a df.
- Report `df_BM` beside `G−1` per read, and the resulting `t_{0.975, df_BM}` beside `t_{0.975, G−1}`.

**(3) Carter–Schnepel–Steigerwald effective cluster count G\*.** CSS: `G* = G/(1+Γ)`, `Γ = (1/G)Σ_g((γ_g−γ̄)/γ̄)²` with `γ_g` the cluster's variance share. For this intercept-only estimator `γ_g ∝ h_g` and `Σh_g = 1`, so it reduces exactly to `G* = 1/Σ_g h_g²` — the Herfindahl-inverse convention **already used for the loan/stratum scheme** (`bootstrap_pathb_cluster.py:44–48`, "effective count 1/sum(p^2) = 25.8", committed at `.cluster_structure.effective_n_clusters = 25.77710660741266`). Using the same convention in both places is a hard requirement: otherwise tab:uncertainty's tablenote compares two different objects.
- Report `G*` for **all four reads** and both `Σh²` and `h_max`.
- **Ex-ante bound, derivable now with no run:** `Σh² ≥ h_max²`, so for R2 `G* ≤ 1/0.33233² = 9.05`. R1's "bounded near 9" is arithmetically correct. R3: `G* ≤ 1/0.38157² = 6.87` on G=25. R4: `G* ≤ 1/0.16607² = 36.3` on G=226.

**(4) Restricted (WCR) CI by inversion** — reported, no rule attached. For a grid of 401 candidate `R₀` spanning ±5 CR1-SEs around `R̂`: residuals `A_g − R₀W_g`, `t(R₀) = (R̂−R₀)/SE_CR1`, bootstrap `t*(R₀)` under Webb weights; retain `R₀` iff `t(R₀) ∈ [q₂.₅, q₉₇.₅](t*(R₀))`. Map the retained set's endpoints through the PCHIP. This is the object MacKinnon–Webb recommend and it discharges "state the bootstrap DGP" completely: the paper then reports both the unrestricted and restricted constructions.

**(5) Truncation convention.** Keep v1's convention (map at the nearest grid edge, flag `truncated_at_grid_edge`, state the direction) — do **not** switch to `_map_draws`'s exclusion convention. Report the flags. Grid `[2.0, 6.0]`% CPR, never extrapolated.

## C1.3 Pre-committed expectation + derivation

**Structural point, fixed before the run:** the BM/IK df change **cannot move the primary interval** — the wild bootstrap-*t* reads its critical values off the `t*` quantiles, not a *t* table. df enters only CR2/CR3 (secondary, no rule). G\* is a diagnostic with no interval. **The only channel that can move the binding literal is the Webb weight change.**

**Expected direction and size.** Webb's E[s⁴]=7/6 vs Rademacher's 1 ⇒ the `t*` distribution is slightly more dispersed ⇒ a small **widening**. The classic Webb motivation (too few distinct sign patterns) does *not* bind here: 2³¹ ≈ 2.1×10⁹ ≫ B=9,999. The relevant leading-order term scales as `(E[s⁴]−1)/G_eff`. With `G=31` that is 0.167/31 ≈ 0.5% (≈ 0.03pp on the 5.9268pp width); with the *effective* `G* ≲ 9` it is 0.167/9 ≈ 1.9% (≈ 0.11pp). **Pre-committed expectation: a widening of 0.03–0.15pp, concentrated at the upper edge** (the committed correction already "widens it mostly at the top", tex 592).

**Printing slack — the reason this matters, computed ex ante.** Committed `[+2.796265669289897, +8.723086701307457]`:
- lower literal `+2.8` survives while `L ∈ [2.75, 2.85)` → **0.0463pp of downward slack**
- upper literal `+8.7` survives while `U ∈ [8.65, 8.75)` → **0.0269pp of upward slack**

The expected widening (0.03–0.15pp) **straddles the 0.027pp upper slack.** The modal outcome is therefore *not* the tasking's branch (a) or (b) but a third case the tasking does not name, specified below as (a′).

**Expected CR2/CR3 movement (secondary).** `t_{0.975,30} = 2.0423`; at `df_BM` near G\* ≈ 8–9 the critical value rises to ≈ 2.26–2.31, inflating the CR2/CR3 *t*-intervals by ~11–13%. CR2 `[+2.974, +8.553]` → roughly `[+2.7, +8.9]`; CR3 `[+2.773, +8.774]` → roughly `[+2.5, +9.1]`. The tablenote's "The secondary corrected reads agree with the wild-$t$ layer: CR2 $+3.0$ to $+8.6$, CR3 $+2.8$ to $+8.8$" (tex 364) **will need restating** under any branch — the numbers change even when the primary does not. This is not optional and is not covered by the tasking's (a)/(b).

## C1.4 Ex-ante landing rule

Let `[L*, U*]` = the Webb wild-*t* R2 interval mapped to pp at δ=6.5; `[Lc, Uc] = [2.796265669289897, 8.723086701307457]`.

**Branch (a) — CONFIRM, no printed change.** `|L*−Lc| ≤ 0.10` **and** `|U*−Uc| ≤ 0.10` **and** `L* ∈ [2.75, 2.85)` **and** `U* ∈ [8.65, 8.75)`.
*Equivalent width threshold:* the interval's width stays within `[5.727, 6.127]`pp **and** neither endpoint crosses a rounding boundary.
→ **Land:** one clause in tab:uncertainty's tablenote (tex 364) reporting the Webb interval, the BM/IK df, and G\*; plus the **mandatory** replacement of the tablenote's final sentence (see A7 collision below). **All 12 interval literals untouched.** Gates: only the tablenote-content gate needs its literal added; #98/#99/#101 untouched. Effort: tex-only + one gate.

**Branch (a′) — CONFIRM in substance, printed literal moves.** Both endpoints within 0.10pp, but at least one crosses a rounding boundary.
→ **Land:** the new printed pair replaces the old at **all 12 occurrences on 11 lines** (45, 76×2, 301, 312, 592, 605, 611, 30, 106, 357, 677) in **ONE commit** with: gate #98 span `posture_binding_layer` (`liveness_gates.py:401–402`), gate #99 `ABSTRACT_POSTURE["interval"]` (line 460) **and the ordering assert's search string** (line 503), the count gate (line 4342), the letter literal list (line 584), `tests/test_headline_posture_gate.py:79` and `:151`, and the letter recount (claim currently 226). Prose must say the interval is *materially unchanged and re-printed*, **not** "widened" — a 0.03pp move is a printing artifact and describing it as a widening would misstate the result.

**Branch (b) — MATERIAL WIDENING.** Either endpoint moves outward by >0.10pp.
→ **Land:** the wider interval becomes binding at all 12 occurrences (same one-commit list as (a′)), **plus** the characterizing prose is re-derived at each of the three sites that describe it, not just re-numbered:
- tex 592: "the wild-$t$ interval is $+2.8$ to $+8.7$ points (CR2 $+3.0$ to $+8.6$, CR3 $+2.8$ to $+8.8$), and it is the wild-$t$ interval this paper quotes as the binding layer, with the lower edge above zero on every corrected read" — the "widens it mostly at the top" clause immediately before it must be re-checked against the new asymmetry.
- tex 312: "Within the production form the binding layer is the floor reads' own sampling error, $+2.8$ to $+8.7$ points after wild-cluster correction…" — **this is gate #98's pinned span**; changing it changes the gate.
- tex 30 (abstract): "The design pins it between $+2.8$ and $+8.7$ points under its production floor form (a wild-cluster interval on 31 clusters; the percentile read under-covers)" — the parenthetical must gain "31 clusters, an effective 9" or the abstract keeps asserting a cluster count the run has just qualified. **⚖ abstract posture span.**
- tab:assembly's caption (tex 316) and the "headline sits just below that interval's midpoint" clause (tex 312) both depend on the midpoint; re-derive.
**⚖ posture-adjacent** (moves the paper's headline interval).

**Branch (c) — NARROWING by >0.10pp** (not expected; specify anyway). **Do not adopt the narrower interval.** Keep the committed pair as the quoted binding layer, report the Webb interval in the tablenote as narrower, and state that the wider construction is retained. Narrowing a disclosed uncertainty on a rerun of one's own machinery is adjudication in one's own favor, which this paper's own convention forbids. **⚖ flag to Eugene either way.**

**Unconditional in every branch** (these do not depend on the verdict):
1. `G*` and `Σh²` land in the tablenote for the floor read, in the same convention as the loan/stratum scheme's 25.8.
2. tex 364's final sentence — "**No single cluster dominates the primary read: the run's recorded maximum single-cluster leverage is 0.33.**" — is **deleted or inverted**. It asserts the opposite of its own number (h_max = 0.33 with G\* ≤ 9.05). This is PLAN item A7's honest replacement; **C1 and A7 collide on this exact sentence and must not both edit it** — assign it to whichever lands first and have the other verify.
3. The CR2/CR3 numbers in tex 364 are restated at `df_BM`.
4. The bootstrap DGP (unrestricted, point-imposed), B=9,999, and the SMM-scale studentization are stated in the tablenote — R1 asked for exactly these three and they are currently nowhere in the tex.

## C1.5 Parity checks (BLOCKING; on failure write `status: GATE_FAILURE` and stop)

- **P1** R1–R4 point reads reproduce `5.334239649398553 / 4.990624060575566 / 4.695495330057254 / 3.9719264231555695`%, n = `155/137/125/2838`, G = `31/31/25/226`, to 1e-9. (v1's P1, unchanged.)
- **P2** Percentile bootstrap reproduced bit-exactly at R2 via `fu.cluster_bootstrap_cpr` (rng 42): `se_pp = 0.3933971547430653`, `ci95_pct = [4.368576777908708, 6.003552252675821]`, mapped `ci95_pp = [2.974329560125351, 8.01850965353176]`.
- **P3** `FloorMapping` reproduces the committed `floor_sweep` grid exactly and `max|mapped−engine| ≤ 0.69` ($B). Assert from `floor_uncertainty_results.json .mapping_fidelity` (committed `0.6867374936622994`).
- **P4 (new, load-bearing)** With `weights="rademacher"` the v2 code reproduces the committed v1 artifact **bit-exactly on all four reads**: `.reads.*.wild_t.marginal_ci95_pp`, `.t_star_q`, `.cr1/cr2/cr3_t_interval.*` to 1e-12. This is what licenses reading any Webb-vs-Rademacher difference as the weight change rather than a refactor.
- **P5 (new)** `Σ_g h_g = 1` to 1e-12 per read; `h_max` reproduces the committed `.reads.*.max_leverage` to 1e-12.
- **P6 (new)** BM/IK equal-cluster self-test returns `df = G−1` to 1e-8.
- **P7 (new)** Webb weight moments over the realized draw matrix: `|mean| < 0.01`, `|E[s²]−1| < 0.01`, `|E[s⁴]−7/6| < 0.02`.

## C1.6 Artifact

`/Users/eugene/somthing/Lock In effect/Lock-in-Effect/hazard/data/floor_inference_correction_v2_results.json`

Required fields (superset of v1's schema so gates can be written against either):
```
mode, status, spec, parity_gates{P1..P7}, parity_gates_all_pass
reads.<R>.{ n_clusters, n_cohort_months, point_cpr_pct,
            leverages_h[]            <- NEW, full vector, ordered by sorted stratum
            sum_h_sq, h_max, G_star_css,
            df_bm, t_crit_df_bm, t_crit_G_minus_1,
            cr1|cr2|cr3_t_interval{ …, df_used },      <- both df variants
            wild_t_rademacher{ B, seed, weights, t_star_q, t_star_draws_path, floor_ci95_pct, marginal_ci95_pp, marginal_ci95_b, lower_pp_edge, upper_pp_edge },
            wild_t_webb{ …same… },
            wcr_inverted{ grid_lo, grid_hi, n_grid, floor_ci95_pct, marginal_ci95_pp } }
verdict.{ primary:"R2 Webb wild-t", corrected_pp, committed_pp, delta_lower_pp,
          delta_upper_pp, printed_lower_unchanged, printed_upper_unchanged,
          code: CONFIRM_NO_PRINT | CONFIRM_PRINT_MOVE | WIDENS | NARROWS,
          manuscript_action }
runtime_s
```
Plus `/Users/eugene/.../hazard/data/floor_inference_v2_tstar_R2_webb.csv` and `…_rademacher.csv` (9,999 rows each) — **required by C2**, which cannot run without them.

## C1.7 What must NOT change

`hazard/floor_inference_correction.py` and `hazard/data/floor_inference_correction_results.json` (frozen; v1 is the committed provenance for tex 592/677). `hazard/floor_uncertainty.py` and its artifact. `hazard/config.py`. The percentile layer `[+3.0, +8.0]` and its 4 tex sites. The PCHIP grid and the `$0.69B` fidelity tolerance. `tab:oosfloor`'s floor→marginal grid. The point estimate `+5.5716pp / +$42.6B`.

---

# SPEC C2 — `layer_convolution` (floor-read × loan-sample)

Decision taken (PLAN Decision record item 4): **labeled second line, not a replacement.**

## C2.0 Recovery step 0 — do both replicate sets exist?

| Layer | Exists? | Where |
|---|---|---|
| Loan-sample cluster replicates | **YES** | `/Users/eugene/somthing/Lock In effect/Lock-in-Effect/hazard/data/bootstrap_pathb_cluster_draws.csv` — 200 rows, columns `rep, n_loans, central_trapped_b, central_share_pct, null_trapped_b, null_share_pct, marginal_b, marginal_pp`. Field used: **`marginal_pp`**. Summary in `bootstrap_pathb_cluster_results.json .marginal_pp` = `{p2_5: 4.630919609903703, median: 5.640716853146607, p97_5: 6.924433300615744, mean: 5.682988123686434, sd: 0.6044572173024999}` |
| Floor-read replicates | **NO — not persisted.** `floor_uncertainty.cluster_bootstrap_cpr` builds 1,000 draws and returns only summaries (`floor_uncertainty.py:201–214, 376–399`); the 9,999 `t*` draws in `floor_inference_correction.py` are likewise discarded (line 304, `tstar` never written) | must be regenerated |

**Step 0:** both floor-read replicate sets are regenerated, bit-exactly, as a by-product of **C1** (parity gates P2 and P4 pin them). **C2 is blocked on C1 landing its two `t*` CSVs.** If C1 is deferred, C2's step 0 is a standalone rerun of `fu.cluster_bootstrap_cpr(selections[R2])` under rng 42 with the draws dumped, gated on reproducing `se_pp = 0.3933971547430653` and `ci95_pct = [4.368576777908708, 6.003552252675821]`.

## C2.1 Run name and engine entry

- **Run name:** `layer_convolution`
- **New file:** `/Users/eugene/somthing/Lock In effect/Lock-in-Effect/hazard/layer_convolution.py`
- Imports `matched_depth_reconciliation.FloorMapping`, `floor_uncertainty as fu`; reads the two C1 `t*` CSVs and `bootstrap_pathb_cluster_draws.csv`. **No engine run. No refit. Pure post-processing** — runtime seconds.

## C2.2 The convolution, defined exactly

**Choice: independent sum on the marginal (pp) scale. Not re-simulation.** Justification from what the artifacts support:

1. The two layers are measured on **disjoint data and disjoint time**: the floor read is a cluster-ratio on 2018 reporting-month cohort-months of the Freddie disclosure panel (`rp ∈ [201801, 201812]`, gap ≤ −0.0025, age ≥ 12; 137 cohort-months, 31 strata); the loan-sample layer resamples the 130 strata of the **75,000-loan simulation sample** over the 2022-06–2025-11 window. No cohort-month enters both.
2. Their dependence is **not estimable from any committed artifact** — they share the underlying Freddie book but nothing links a 2018 stratum-ratio replicate to a window-period composition replicate. Independence is therefore an assumption, and it is stated as one.
3. **Re-simulation is possible but buys the wrong thing at a real price.** A joint re-simulation (draw a floor replicate, re-run the paired legs on a cluster-resampled sample at that floor) costs ≈ 10.6 s/replicate — read off `bootstrap_pathb_cluster_results.json .runtime_s = 2110.55` for 200 replicates × 2 legs — so 1,000 joint replicates ≈ 3 hours. What it would add is the *floor × composition interaction*, which the independent sum assumes away. But the committed PCHIP already substitutes for engine runs at arbitrary floors to within `$0.687B` (P3), so re-simulation adds interaction, not accuracy. Interaction is priced instead by parity check **P4** below at a fraction of the cost.

**Construction (primary line).**
- Floor layer as a *confidence distribution on the marginal*: for each of the 9,999 Webb `t*` draws, the implied floor is `R_b = R̂ − t*_b · SE_CR1` on the SMM scale; convert `SMM → CPR%`; map through the committed PCHIP under C1's edge-truncation convention (map at the nearest grid edge, flag, count) → `M_b` (pp at δ=6.5). By construction the 2.5/97.5 percentiles of `{M_b}` reproduce C1's Webb wild-*t* interval **exactly** — that is parity check P2 below, and it is what makes this line the correct companion to the wild-*t* referent the decision record preserved.
- Loan layer as *deviations*: `d_j = m_j − m̄`, `j = 1…200`, `m_j` = `marginal_pp` from `bootstrap_pathb_cluster_draws.csv`. **Centering convention, fixed ex ante: `m̄` = the committed point marginal at this floor, `+5.5715581829` pp** (the value `bootstrap_pathb_cluster_results.json .comparison.committed_point_marginal_pp` is compared against, verified inside the interval, `.R2_committed_point_inside = true`). Using the replicate median (5.6407) or mean (5.6830) instead would smuggle a +0.07/+0.11pp recentering into the headline layer; the point is the right center and its use is stated.
- Convolved sample: the full outer sum `{M_b + d_j}` over 9,999 × 200 = 1,999,800 pairs; report the 2.5/97.5 percentiles, the sd, and the median. (Exact enumeration, not a Monte-Carlo sub-sample — it is 2M float ops.)
- **Secondary line, also reported:** the same construction with the 1,000 *percentile* floor replicates in place of the Webb `t*`-implied set, which yields the convolved companion to `[+3.0, +8.0]`. Report both truncation conventions' counts (the committed percentile map **excluded 26 of 1,000 draws** as out-of-grid — `floor_uncertainty_results.json .part_a_sampling_uncertainty.reads.R2…mapped_marginal_at_6.5.n_draws_outside_grid = 26`, all above 6.0% floor, i.e. all on the *low-marginal* side, which is the side the lower edge is read from. This must be disclosed; it is why the edge-truncation convention is preferred).

## C2.3 Pre-committed expectation + derivation

Widths: floor-read Webb ≈ Rademacher `8.723086701307457 − 2.796265669289897 = 5.9268`pp; loan/stratum `6.924433300615744 − 4.630919609903703 = 2.2935`pp. Ratio `w₂/w₁ = 0.3870` (the committed `.comparison.width_ratio_vs_floor_read = 0.4546851318235146` is the ratio against the *percentile* width 5.0442, not the wild-*t* width — do not confuse the two).

**Root-sum-of-squares, ex ante:** independent half-widths add in quadrature, so
`w_conv / w₁ = √(1 + 0.3870²) = √1.1498 = 1.0723` → **+7.2% wider**.

Applied asymmetrically about the point `+5.5716`: lower half-width `√(2.7753² + 1.0098²) = 2.9533`; upper `√(3.1515² + 1.2837²) = 3.4029`.

> **Pre-committed point prediction: convolved ≈ `[+2.62, +8.97]`pp, width ≈ 6.36pp, +0.43pp (+7.2%) wider than `[+2.8, +8.7]`.**

**Bracket, also pre-committed.** Independence is a lower bound on the convolved width; perfect positive dependence is the upper bound: `5.9268 + 2.2935 = 8.220`pp (+38.7%). The reported line is the independent one; the comonotone width is stated in the tablenote as the bound under maximal dependence, so no reader mistakes independence for a measured fact.

**Verdict rule (ex ante, no discretion):** the convolved interval must be **wider than `[+2.8, +8.7]`**. If it is not — i.e. `w_conv < w₁` — the construction is wrong (a sum of independent variates cannot narrow); **STOP** and debug rather than report.

## C2.4 Landing rule

**Single branch** (the decision record fixed the presentation form; the only free content is the numbers).

1. **tab:uncertainty (tex 357), headline row, `Sampling 95% CI` cell** — a labeled second line appended after the existing loan/stratum clause. Draft:
   > `…; loan/stratum cluster bootstrap $[+4.63, +6.92]$pp (width $0.39\times$ the corrected floor read; 25.8 effective clusters); the two layers convolved as independent, $[+X.XX, +Y.YY]$pp (run \texttt{layer\_convolution}; independence is assumed, not measured — under maximal positive dependence the width is $Z.ZZ$pp)`

   ⚠ **Zero-slack collision:** this cell contains the bracket-form `$[+2.8, +8.7]$` literal (occurrence 2 of 3) and the gate-pinned `$[+4.63, +6.92]$` (`liveness_gates.py:4175`) and `25.8` (`:4177`). Neither may be disturbed. The gate at `:4167` also asserts `width_ratio_vs_floor_read < 0.5` — that ratio is against the *percentile* width and is unaffected by adding a convolved line, but confirm before committing.

2. **tex 301, the interval-discussion sentence.** The existing text reads: *"…propagating the floor reads' own cluster-bootstrap sampling error puts the max-form member at $+2.8$ to $+8.7$ points after wild-cluster correction (the percentile read is $+3.0$ to $+8.0$; Section~\ref{sec:robustness-floor}) and leaves it open below $+4.3$ on an age-standardized read…"* Append one sentence, after that clause and before "The hull's lower edge is thus narrower…":
   > `Those two layers are reported side by side rather than maximized over: convolved as independent draws the pair spans $+X.X$ to $+Y.Y$ points, which is the interval a reader who wants one number for sampling error should use, and which I do not substitute for the floor read because independence between a 2018 cohort-month ratio and a window-period composition resample is an assumption rather than a measurement.`

3. **tex 364 tablenote** — the sentence *"No such correction is run for the loan/stratum scheme, whose interval is still better read as a lower bound on sampling uncertainty than as calibrated 95\% coverage"* stays and is **load-bearing for the convolution's honesty**: one input to the sum is itself a lower bound, so the convolved line is a lower bound too. Say so in one clause.

**⚖ flag:** the tex 301 sentence sits inside §V.C's identification argument and is adjacent to the `$+2.8$ to $+8.7$` to-form (occurrence 3 of 7). It does not change any committed number, but it changes how the paper *ranks* its uncertainty layers — that is posture-adjacent, and Eugene should see the drafted sentence before it lands.

**Not landing anywhere:** the abstract (tex 30), tab:headline (tex 76), tab:crosswalk (tex 677), the conclusion (tex 605/611). The convolved line is a body-and-table object per the "labeled second line, not a replacement" decision.

## C2.5 Parity checks

- **P1** `bootstrap_pathb_cluster_draws.csv` has exactly 200 rows; `np.percentile(marginal_pp, [2.5, 97.5])` reproduces `[4.630919609903703, 6.924433300615744]` to 1e-9 and `sd = 0.6044572173024999` to 1e-9.
- **P2** The `t*`-implied floor layer's own 2.5/97.5 percentiles reproduce C1's Webb wild-*t* `marginal_ci95_pp` to 1e-9 (self-consistency of the confidence-distribution construction).
- **P3** The percentile-replicate secondary line reproduces `[2.974329560125351, 8.01850965353176]` to 1e-9 when the loan deviations are set to zero.
- **P4 (the interaction probe — the substitute for re-simulation).** The independent sum assumes the loan-layer width does not depend on the floor. Test it: rerun `bootstrap_pathb_cluster` at the band ends **4.695%** and **5.334%** with `--reps 60` each (≈ 2 × 11 min at the measured 10.6 s/leg-pair). Pre-committed tolerance: the 5–95 percentile width at each end within **±25%** of the 4.991% width scaled by nothing (i.e. the loan-layer width is treated as floor-invariant). Inside tolerance → the additive convolution stands as specified. Outside → the convolved line is reported **only** at 4.991% with the floor-dependence disclosed in the tablenote, and the RSS is not claimed to hold across the floor range. *(Cost note: this is the only non-trivial cost in C2. If the coordinator declines it, the convolved line must carry "the loan-layer width is assumed floor-invariant; not tested" — do not omit the caveat.)*

## C2.6 Artifact

`/Users/eugene/somthing/Lock In effect/Lock-in-Effect/hazard/data/layer_convolution_results.json`
```
mode, status, spec, parity_gates{P1..P4}, parity_gates_all_pass
inputs.{ floor_tstar_csv, floor_percentile_source, loan_draws_csv,
         n_floor_reps, n_loan_reps, centering_convention, center_pp }
layers.floor_wild_t.{ ci95_pp, width_pp, n_truncated_at_edge }
layers.loan_cluster.{ ci95_pp, width_pp, effective_clusters }
convolved_primary.{ ci95_pp, ci95_b, width_pp, median_pp, sd_pp,
                    width_ratio_vs_floor_read, n_pairs }
convolved_percentile_secondary.{ … }
dependence_bracket.{ independent_width_pp, comonotone_width_pp }
expectation_check.{ predicted_ci95_pp:[2.62,8.97], predicted_width_pp:6.356,
                    realized_width_pp, abs_err_pp }
floor_invariance_probe.{ reps, floors, widths_pp, within_tolerance }
verdict.{ wider_than_committed: bool, manuscript_action }
runtime_s
```

## C2.7 What must NOT change

`[+2.8, +8.7]` at any of its 12 occurrences. `[+4.63, +6.92]`, `25.8`, `factor of $37$` (all gate-pinned, `liveness_gates.py:4175–4177`). `[+3.0, +8.0]` ×4. The point `+5.6pp / +$42.6B`. The label "the binding layer" (C3 may move it; C2 may not). Any committed artifact.

---

# SPEC C3 — `psa_level_sweep` (baseline seasoning-ramp level)

## C3.0 Two engine gotchas, both verified in code

**Gotcha 1 (the one that binds — and it is not the one named in the tasking).** `h0_psa`'s speed is a **default argument bound at definition time**:
```
hazard/literature_hazard.py:58   def h0_psa(age_months, psa_speed: float = PSA_SPEED) -> np.ndarray:
hazard/literature_hazard.py:73-76 def baseline_hazard(age_months, mode=BASELINE_MODE):
                                      … return h0_psa(age_months)          # no speed passed
```
Setting `config.PSA_SPEED = 75.0` or `literature_hazard.PSA_SPEED = 75.0` **at runtime is a silent no-op** — the default was captured at import. Contrast `INVOLUNTARY_CPR_ANNUAL`, which *is* read as a module global inside `prepay_hazard` (lines 107–109), which is why `floor_sweep._run_scored` can set it and it works. **If the run mutates `PSA_SPEED`, all four cells return the identical 100-PSA result and the sweep silently reports "no sensitivity."** No committed script mutates `PSA_SPEED` (only `episode_confrontation.py:157,545` *gates* on it `== 100.0`), so nothing existing is affected — this is a trap for the new run only.

**Gotcha 2 (`floor_sweep._ORIG_PREPAY`) — DOES NOT BIND HERE, and here is why.** The chain flagged in `moving_share_bracket.py:165–177` (floor_sweep's bind-tally wrapper delegates to `fs._ORIG_PREPAY`, and its `finally` writes `fs._ORIG_PREPAY` back into `competing_risks.prepay_hazard`, so a variant must be installed at `fs._ORIG_PREPAY`) binds **only if the run layers on `floor_sweep._run_scored`**. This spec does not: it follows the `regime_split_marginal.py` template, which patches `competing_risks.prepay_hazard` with a faithful local copy and never imports `floor_sweep`. The gotcha would bind if a later editor re-plumbed C3 through `floor_sweep`; it is recorded so that does not happen silently.

**Third fact, easy to get wrong.** PSA is multiplicative on the **annual CPR**, not on the monthly hazard: `cpr_ann = 0.06·(psa/100)·min(age,30)/30` then `h = 1−(1−cpr)^(1/12)`. So a PSA-125 cell is **not** `1.25 × h0`. The run must call `h0_psa(age, psa_speed=P)` with the speed passed explicitly. (The regime-split's `f × h0` device is a *different* perturbation and its numbers are not directly comparable cell-for-cell — say so in the artifact.)

## C3.1 Run name and engine entry

- **Run name:** `psa_level_sweep`
- **New file:** `/Users/eugene/somthing/Lock In effect/Lock-in-Effect/hazard/psa_level_sweep.py`
- **Template:** `/Users/eugene/somthing/Lock In effect/Lock-in-Effect/hazard/regime_split_marginal.py`, structure copied verbatim: committed `microsim_engine._simulate_regime` unchanged; in-process monkey-patch of `competing_risks.prepay_hazard` with a faithful copy of `literature_hazard.prepay_hazard` in which the single line `h0 = baseline_hazard(loan_age)` becomes `h0 = h0_psa(loan_age, psa_speed=_STATE["psa"])` and the floor annual CPR is taken from `_STATE["floor"]`; US regime only; committed 75k sample (`config.LOAN_SAMPLE_PATH`); `RNG_SEED = 42` fixed; one shared macro frame fetched once; `extension_risk.score_extension_risk` on the standalone scorer.
- **No `microsim_engine.monthly_step` wrapper** — unlike the regime split, the PSA level applies to every window month, so no calendar-month counter is needed. Delete that patch rather than carry it inert.
- **Bind tally, free:** the copied `prepay_hazard` already computes `h_vol` and `h_floor` separately before the `np.maximum`; tally `(h_vol < h_floor)` in place. Do **not** import `floor_sweep`'s double-evaluation wrapper (gotcha 2).

## C3.2 Parameterization

- PSA levels: **75, 100, 125, 150**
- Legs: **central (`p_q_shock_pct = 6.5`) and null (`p_q_shock_pct = 0.0`)**, paired, differenced within cell
- Floors: **both calibrations** — `0.04` (in-sample production) and `0.04991` (off-window headline). Use the paper's rounded off-window anchor `4.991%`, matching `bootstrap_pathb_cluster`'s `--floor 4.991` convention and its committed G1 anchors, **not** the unrounded `4.990624060575566`
- **16 engine legs total.** Cost, derived from `regime_split_marginal_results.json .runtime_s = 126.3` for 10 legs ⇒ ≈ 12.6 s/leg ⇒ **≈ 3.5 minutes plus setup**. This is the cheapest run in the plan.
- `FLOOR_MODE` stays `"max"` (production). `LITERATURE_COEFS`, `N_LOANS`, `RNG_SEED`, `P_Q_BASELINE`, `BASELINE_MODE` untouched. No `config.py` write.
- Report per cell: `central_trapped_b`, `null_trapped_b`, `marginal_b`, `marginal_pp`, `central_share_pct`, `null_share_pct`, **`floor_bind_share_central`**, **`floor_bind_share_null`**, `n_loan_months`.

## C3.3 Pre-committed expectation + derivation

**Direction, from the mechanism.** Under `FLOOR_MODE="max"`, the per-loan-month marginal is `max(f, v₀) − max(f, v_c)` with `v_c = v₀·exp(−|β₁|·100·|gap|) < v₀` and `f` the floor hazard. Scaling the ramp scales `v₀` and `v_c` together, so: below `f/v₀` the cell contributes zero (fully censored); above it the contribution rises to the uncensored `v₀(1−e^{−k})`. **The marginal is monotone increasing in the baseline level** — because the baseline multiplies the very rate-gap channel the null switches off (the paper's own sentence at tex 301). Confirmed empirically by the committed regime split: `h0_factor 0.8 → +4.966`, `1.0 → +9.198`, `1.2 → +12.124` (`regime_split_marginal_results.json .results.h0_marginal_pps`).

**Magnitude, derived ex ante from the regime-split slopes.** Chord slopes at the in-window 4.0% floor: down-arm `(9.198−4.966)/0.2 = 21.16` pp per unit factor; up-arm `(12.124−9.198)/0.2 = 14.63`. Down > up ⇒ **empirically concave** over this range (42-month pool depletion dominates the per-month convexity). Two corrections to carry over:
1. The regime split applies its factor from 2023-01, i.e. **35 of 42 window months** (`.spec.n_post_months = 35`). PSA applies to all 42. The 7 pre-break months (Jun–Dec 2022) are the first half of the window's first third, which carries 21.3% of the marginal (tex 1040), and the marginal ramps within the window, so those months carry ≈ 6–11%. Scale the *deviation from +9.198* by **×1.06–1.12**.
2. Extrapolate the concave arms: down-arm steepens, up-arm saturates.

> **Pre-committed expectations at the 4.0% in-sample floor:**
> PSA 75 → **+2.5 to +3.5** pp · PSA 100 → **+9.198** (parity anchor) · PSA 125 → **+12.5 to +13.5** pp · PSA 150 → **+15 to +17** pp
> Sweep range ≈ **+3 to +16.5 pp, width ≈ 13 pp.**
>
> **At the 4.991% off-window floor** (censoring 68.8% central / 35.8% null at PSA 100, tex 301): lowering the ramp pushes more loan-months onto the floor, so the low cell compresses hard toward zero; raising it de-censors fast.
> PSA 75 → **+1.5 to +2.5** · PSA 100 → **+5.5716** (parity anchor) · PSA 125 → **+8.5 to +10** · PSA 150 → **+11 to +14**
> Sweep range ≈ **+1.5 to +14 pp, width ≈ 10–12 pp.**
>
> **Both calibrations are expected to exceed the floor-read interval's 5.93 pp width by a factor of roughly 2.** R1's expectation ("it will") is the pre-committed expectation here too.

**Secondary pre-committed expectation (a check the run gets for free):** the central-leg bind share must fall monotonically in PSA at both floors, and at the 4.991% floor PSA 75 should push it well above 68.8%. If bind share and marginal do not move in opposite directions monotonically, the patch is not reaching the hazard (gotcha 1) — treat as a failure, not a finding.

## C3.4 Landing rule

Let `W_psa` = the PSA-sweep marginal range width **at the off-window 4.991% floor** (the headline calibration; the in-window range is reported beside it), and `W_floor = 5.9268` pp (the wild-*t* width; if C1 lands a new pair, use the new width).

**Branch (a) — `W_psa > W_floor` (expected).** The layer-ranking sentence is restated. It lives at **tex 312** and it is **gate #98's pinned span** `posture_binding_layer` (`liveness_gates.py:401–402`), currently:
> *"Within the production form the binding layer is the floor reads' own sampling error, $+2.8$ to $+8.7$ points after wild-cluster correction of the percentile read's under-coverage (run \texttt{floor\_inference\_correction}; the percentile read is $+3.0$ to $+8.0$); the headline sits just below that interval's midpoint…"*

**Pre-drafted replacement** (to be verified against the realized numbers before it lands):
> `Within the production form the widest disclosed layer is the baseline level. Sweeping the seasoning ramp over 75 to 150 PSA on both legs carries the marginal from $+A.A$ to $+B.B$ points at the off-window floor and from $+C.C$ to $+D.D$ at the in-sample calibration (run \texttt{psa\_level\_sweep}), a span wider than any sampling interval reported here. That layer has no coverage property: it is a range over a convention I did not estimate, and its endpoints are not draws from anything. The widest layer that does have a coverage property is the floor read's own sampling error, $+2.8$ to $+8.7$ points after wild-cluster correction of the percentile read's under-coverage (run \texttt{floor\_inference\_correction}; the percentile read is $+3.0$ to $+8.0$), and that is the interval this paper quotes as binding. The headline sits just below its midpoint…`

Same commit, mandatory: gate #98's `posture_binding_layer` span updated to the new string; **tex 343** ("the operative uncertainty on every headline quantity is calibration --- except the headline marginal, where the binding layer is the floor read's own propagated sampling error") gains the same qualification, or the table's lead-in contradicts its own tablenote; **tex 357** and **tex 76** and **tex 677**, which each print the phrase "the binding layer", gain the qualifier "with a coverage property" or the phrase is left as-is with the qualification carried once at tex 312 (⚖ Eugene's call — the cheap option is the single-site qualification, the honest-but-wide option is all four). The PSA range is added as a new row/clause in **tab:uncertainty**'s `Calibration range` cell for the headline row (tex 357) and the in-sample row (tex 359, beside the existing `regime-split baseline break $+5.0$ to $+12.1$`).

**⚖ posture-adjacent.** This restates the paper's uncertainty ranking, which is a claim about what the design delivers. Eugene sees the drafted sentence before it lands.

**Branch (b) — `W_psa ≤ W_floor`.** The tablenote (tex 364) gains one clause: `A 75--150 PSA sweep of the baseline seasoning ramp, run on both legs at both floor calibrations, moves the marginal over $+A.A$ to $+B.B$ points, inside the floor read's interval (run \texttt{psa\_level\_sweep}).` Nothing else moves. The layer-ranking sentence stands as written and R1-W1(i) is answered by disclosure rather than restatement.

**Branch (c) — surprise: the marginal is non-monotone in PSA, or PSA 75 returns a negative marginal.** Non-monotonicity would contradict the mechanism argument the paper makes at tex 301 ("because the baseline multiplies the very rate-gap channel the null switches off, a structural break in $h_0$ scales the marginal rather than cancelling from it"). **STOP, report, land nothing** — a mechanism sentence in §V.C would be at stake and that is not a tablenote edit. A negative marginal at any cell would also contradict the sign-forcing argument (tex 301, 97.40% of exposure at or below 4.79% against a window-minimum 5.2311%), which is a much larger problem than this run.

## C3.5 Parity checks (BLOCKING)

- **G1 (PSA 100, floor 4.0%)** central `818.5300844066606` B, null `748.1850239867648` B, marginal `70.34506041989584` B / `9.198459770709789` pp, all to 1e-6 (pp to 1e-9). Source: `regime_split_marginal_results.json .committed_anchors`. At PSA 100 the patched `h0_psa(age, psa_speed=100.0)` must be **IEEE-bit-identical** to `baseline_hazard(age)` — assert on the array, not just the aggregate.
- **G2 (PSA 100, floor 4.991%)** central `767.5264524465003` B, null `724.9180585654117` B (source: `bootstrap_pathb_cluster_results.json .parity_gates.G1_central_b/G1_null_b`, themselves replayed bit-exactly by `burnout_ablation`'s G6 under the same US-only convention), marginal `+5.5715581829` pp to 1e-6.
- **G3 (anti-gotcha-1, the load-bearing one)** the PSA 75 and PSA 150 cells must return `marginal_pp` **differing from the PSA 100 anchor by more than 0.5 pp**. If any off-anchor cell returns the anchor value to within 1e-9, the patch is not reaching the hazard — `status: GATE_FAILURE`, stop, do not report "no sensitivity".
- **G4 (bind-share instrumentation)** at PSA 100 / floor 4.0% the central-leg bind share reproduces `36%` of `1,683,124` loan-months (`floor_sweep.py:74–76` anchors `BIND_SHARE_ANCHOR = 0.36`, `BIND_N_ANCHOR = 1_683_124`); at PSA 100 / floor 4.991% it reproduces `68.8%` (tex 301) to ±0.5pp, and the null leg `35.8%`.
- **G5 (monotonicity)** `marginal_pp` strictly increasing in PSA at each floor; bind share strictly decreasing. Reported, not blocking — a violation routes to branch (c).

## C3.6 Artifact

`/Users/eugene/somthing/Lock In effect/Lock-in-Effect/hazard/data/psa_level_sweep_results.json`
```
mode, status, spec, spec.psa_levels:[75,100,125,150], spec.floors:[0.04,0.04991],
spec.patch_target:"competing_risks.prepay_hazard (faithful copy; h0_psa(age, psa_speed=P))",
spec.psa_is_multiplicative_on_annual_cpr_not_monthly_hazard: true,
spec.regime_split_not_directly_comparable_note,
parity_gates{G1..G5}, parity_gates_all_pass,
cells[]:{ psa, floor_annual_cpr_pct, central_trapped_b, null_trapped_b,
          central_share_pct, null_share_pct, marginal_b, marginal_pp,
          bind_share_central, bind_share_null, n_loan_months },
ranges.{ floor_4.0.{lo_pp,hi_pp,width_pp}, floor_4.991.{lo_pp,hi_pp,width_pp} },
comparison.{ floor_read_width_pp, psa_width_over_floor_read_ratio_at_headline,
             regime_split_h0_range_pp:[4.965583563905398,12.123711475343967] },
expectation_check.{ predicted_ranges, realized_ranges, inside_prediction: bool },
verdict.{ code: PSA_WIDER | PSA_NARROWER | NON_MONOTONE, manuscript_action },
runtime_s
```

## C3.7 What must NOT change

`hazard/config.py` (`PSA_SPEED = 100.0` stays; production is 100 PSA). `hazard/literature_hazard.py`. `hazard/floor_sweep.py`, `hazard/moving_share_bracket.py`, `hazard/regime_split_marginal.py` and every committed artifact. The headline `+5.6pp / +$42.6B` and `+9.2pp / +$70.3B`. The regime-split literals `$+5.0$ to $+12.1$` (tex 301, tex 359) — the PSA sweep is a **new, separate** layer and does not restate the break-run. `episode_confrontation`'s PSA gates. The 27-cell positivity claim.

---

# SPEC C6 — Path A repairs (three sub-runs)

## C6.0 A destructive-run hazard that must be read before anything else

`bootstrap_se.py:286` sets `seasonal = "month_effects" in prod`, and `prod` is `hazard/data/hazard_coefficients.json`, which is now **spec v4** (`.spec_version = 4`, 317 coefficients, `month_effects` present, verified). Line 298 passes `draws_csv=BOOTSTRAP_DRAWS_CSV` — **hard-coded**, and `--out` only redirects the JSON.

> **Running `python3 hazard/bootstrap_se.py` today would (a) run at spec v4, not v3, and (b) overwrite `/Users/eugene/…/hazard/data/hazard_bootstrap_draws.csv`, the committed spec v3 draw set that `tab:bootstrap` (tex 1088) and `bootstrap_resimulate_results.json` both rest on. There is no `--draws` flag to prevent it.**

Every C6 sub-run therefore writes to **new** artifact paths through **new** scripts. `bootstrap_se.py` is imported for its functions, never invoked as `__main__`.

## C6.0b Recovery step 0 — what exists

| Needed | Exists? | Where / what is missing |
|---|---|---|
| 198 converged replicates | **YES, but only the 3 macro coefficients** | `hazard/data/hazard_bootstrap_draws.csv` — 198 rows, columns exactly `rate_gap_bps, burnout_orth, friction` (asserted at `bootstrap_resimulate.py:59`). Spec **v3**, seed 42, α=1e-4 (`hazard_bootstrap_se.json .spec_version = 3, .seed = 42, .ridge_alpha = 0.0001, .n_reps = 200, .n_failed = 2`) |
| Full replicate coefficient vectors | **NO** | `fit_betas` computes `params_head` (const + 7 age + 3 macro [+ 11 months at v4] = 22 entries at v4) and returns it, but `run_bootstrap` (lines 210–225) stores only the 3 rescaled macro betas. The FE block is never returned at all |
| Per-replicate standardization constants | **NO** | `gap_std / burn_std / fric_std` are returned by `fit_betas` and discarded |
| Ridge-drop check at spec v4 | **NO** | `ridge_reference_weighting.fit_full` (lines 58–88) has **no seasonal path** — the design matrix is `[age_basis, gap, burnout, friction, FE]` with no month block. It is hard-coded spec v3 |

**A structural finding the tasking should know: R1's ask (ii) is not literally executable.** `resample_strata` (`bootstrap_se.py:113–130`) relabels every drawn stratum `f"{sid}__b{k:03d}"` so duplicated strata carry independent fixed effects — `bootstrap_resimulate.py`'s docstring states it: *"FE resampling relabels strata so replication FEs do not map back to production pools."* A replicate's 296 FEs are indexed by bootstrap labels with no canonical map to the 296 production strata. C6(ii) is therefore specified in two tiers, with the tier-1 object being the one that actually fixes the broken joint distribution.

---

## C6(i) — `pathA_ridge_v4`

**Run name / file:** `pathA_ridge_v4` → `/Users/eugene/somthing/Lock In effect/Lock-in-Effect/hazard/pathA_ridge_v4.py`

**Engine entry.** Reuse `ridge_reference_weighting.load_split` verbatim. Reimplement `fit_full`/`holdout_rmse` with a `seasonal: bool` flag, inserting the month block **between the macro block and the FE block** — the exact position `bootstrap_se.fit_betas` uses (lines 118–121), so the macro coefficients stay at `params[1+k : 4+k]`. **Use `hazard_fit._month_dummy_matrix`, not `pd.get_dummies(period.dt.month)`** — the former has fixed columns `m_2…m_12` "regardless of which months appear in the sample" (its docstring, `hazard_fit.py:36–43`), which matters because the zero-event-drop variant removes 423 cells. Warm-start every seasonal fit from `bootstrap_se.production_start_head(prod)` (the Gate-B lesson recorded in that function's docstring: *"cold IRLS on the seasonal design can land a different penalized optimum"*).

**Parameterization.** Reproduce all three committed spec-v3 facts at spec v4:
1. **Grid identity:** α ∈ {1e-5, 1e-4}, max |param diff| (committed v3: `4.5102810375396984e-17`)
2. **Reference-stratum swap:** production reference `2017_200_740+_≤80` vs `sorted(...)[-1]`, at α = 1e-4; report the three macro deltas (committed v3 max |Δ| = `1.2892293326075137`)
3. **Ridge-drop:** drop the zero-event strata, fit **unpenalized** Poisson PML, report macro coefficients under both references (committed v3: 20 strata / 423 cells; `rate_gap_bps 0.6727292125124604` vs production `0.6733519352905115`; reference-invariance `max_abs_delta = 5.717648576819556e-15`)

Also report the v4 holdout RMSEs at both α, both weightings, and the α ranking (committed v3 ranking is **not** weighting-invariant: `.alpha_ranking_invariant_to_weighting = false`).

**Note the zero-event set may differ at v4** — the month dummies do not change which strata have zero training events, so 20/423 should carry over exactly; assert it.

**Pre-committed expectation (R1's own).** *"survives ~unchanged."* Concretely: the drop-fit's spec-v4 macro coefficients reproduce the spec-v4 production values (`rate_gap_bps +0.65`, `burnout_orth −0.17`, `friction −0.007`, tex 981) to within **0.005** in standardized units — a looser tolerance than v3's 0.002, because the 11 month dummies absorb time variation the friction coefficient formerly carried (tex 981 says exactly that: *"The friction coefficient's shrinkage relative to the prior spec ($-0.037$) is expected under the seasonal design"*). Reference-invariance of the drop-fit is expected to hold to 1e-12 (it is an algebraic property of the unpenalized fit, not a numerical accident). Grid identity expected to hold to ~1e-16.

**Landing rule.**
- **(i-a) Survives** (all three facts reproduce within tolerance): the phrase **"not recomputed at adoption"** is deleted at its **4 occurrences — tex 980, 983, 1003, 1051** — and replaced with "recomputed under spec v4 (run `pathA_ridge_v4`); the device is unchanged." tex 1051's opening clause *"all under spec v3 (the device is unchanged under the spec v4 refit; these verification artifacts were not recomputed at adoption)"* becomes the affirmative statement. The v4 numbers are printed beside the v3 ones in App. `app:ridge`.
- **(i-b) Drop-fit macro coefficients move by >0.005, or reference-invariance fails at v4**: the concession *strengthens* rather than disappears — tex 980's sentence *"Nor is the production point an artifact of the device: dropping the 20 zero-event strata and fitting unpenalized Poisson PML reproduces the spec v3 macro coefficients to within $0.002$"* gains "…at spec v3; at spec v4 the same check moves the rate-gap coefficient by X.XXX, and the production point's independence of the device is established only at the prior specification." Path A is already excluded from every headline figure (tex 290, 978, 1053) so **nothing propagates**. ⚖ light: it is a disclosure widening, not a number move.
- **(i-c) Grid identity fails at v4** (the two α return materially different vectors): the "numerical no-op" claim (tex 980, 1051) is spec-v3-only and must be scoped. Report; land the scoped version.

**Parity checks.** P1: with `seasonal=False` the new script reproduces **every** field of `hazard/data/ridge_reference_weighting.json` to 1e-12 — this is what licenses reading any v4 difference as the seasonal design. P2: the v4 production refit reproduces `hazard_coefficients.json .coefficients.{rate_gap_bps, burnout_orth, friction}` to 1e-9 (warm-started). P3: v4 holdout RMSEs reproduce `pathA_v4_holdout_results.json .spec_v4.{rmse_unweighted_pp: 37.903228802264934, rmse_exposure_weighted_pp: 3.037942336998421}` to 1e-6. P4: n_zero_event_strata = 20, n_cells_dropped = 423.

**Artifact.** `/Users/eugene/…/hazard/data/pathA_ridge_v4_results.json` — same schema as `ridge_reference_weighting.json`, with every block duplicated under `spec_v3_replay` (parity) and `spec_v4` (new), plus `parity_gates{P1..P4}` and `verdict.code ∈ {SURVIVES, MOVES, GRID_IDENTITY_FAILS}`.

**Cost.** ~8 GLM fits on 10,176 cells × ~318 columns. A 4-replication bootstrap runs inside the unit-test suite (`tests/test_bootstrap_se.py:91`), so each fit is seconds; the battery is minutes.

---

## C6(ii) — `pathA_resimulate_joint`

**Run name / file:** `pathA_resimulate_joint` → `/Users/eugene/somthing/Lock In effect/Lock-in-Effect/hazard/pathA_resimulate_joint.py`

**Engine entry.** Two stages, both new scripts, neither invoking `bootstrap_se.main()`:
- **Stage A (`pathA_bootstrap_fullvec`)**: re-run the 200 stratum-cluster replications with `bootstrap_se.run_bootstrap`'s logic **copied and extended** to persist, per converged replicate: `params_head` (22 entries at v4 / 11 at v3), `gap_std`, `burn_std`, `fric_std`, `fit_method`, and — for tier 2 — the FE block together with the `stratum_id_src ↔ bootstrap-label` map that `resample_strata` already retains (line 122, `g["stratum_id_src"] = sid`). Writes to **new** paths.
- **Stage B**: `bootstrap_resimulate.py`'s loop, copied, with the coefficient dict built from the replicate's full head instead of the 3 macro betas. Reuse its `sim_mod.fetch_data` patch (single FRED fetch) and its every-10-reps checkpoint.

**Parameterization — units, and the trap in them.** `rescale_to_production_units` exists because the three macro regressors are standardized **per replicate**. The age spline and intercept are **not** standardized (`fit_betas:100`, `age_basis = _age_spline_basis(loan_age, AGE_SPLINE_KNOTS)`, raw) and the month dummies are raw 0/1. Therefore:
- const + 7 age-spline coefficients + 11 month coefficients transfer **directly, unrescaled**;
- the 3 macro coefficients are rescaled exactly as now.
This makes the joint head unit-consistent with what `simulate.simulate_qt_window` consumes. **Do not** rescale the age spline; **do not** simulate with a replicate's own standardization constants against production regressors.

**Tier 1 (primary).** Joint head = const + age spline + 3 macro (+ 11 months at v4). FE held at production. This is the minimal, fully defensible repair of the broken joint distribution — the current construction holds the age spline (the seasoning shape) at production while drawing the macro block, which is precisely the independence R1 objects to.

**Tier 2 (secondary, rule-dependent, reported as a robustness line only).** FE mapped back to production strata by **averaging the replicate's FE coefficients across the duplicate copies of each source stratum** (via `stratum_id_src`), with the absorbed reference re-inserted at 0 and **production FE as the fallback for source strata not drawn in that replicate** (~37% of strata are undrawn in a given replicate under sampling with replacement). The averaging rule and the fallback are arbitrary; they are pre-committed here and disclosed in the artifact as arbitrary. Tier 2 does **not** enter any manuscript number.

**Specification version: run at both.** Spec v3 first (parity — must reproduce the committed interval), then spec v4. Note that spec v4 replications are the ones the paper calls **branch-unstable** (tex 623, 981); expect a *higher* failure count than 2/200 at v4, and report it as a finding.

**Pre-committed expectation (R1's own).** *"Verdict survives, interval possibly widens — strengthening the exclusion."* Committed spec-v3 baseline: `bootstrap_resimulate_results.json` — point `915.067027857209` B / `119.65598142932075`%; median `922.6022056753297` B; mean `598.8526094183436` B (`78.307156230137`%); 95% percentile `[-4459.7936261770865, +1190.1355126947665]` B; `frac_above_benchmark = 0.8383838383838383`. Drawing the age spline jointly with the macro block adds baseline-shape variance to a 42-month forward compounding that is already destabilized by 15 replications (tex 981), so the interval is expected to **widen further**, the mean to fall, and the "no useful forward precision" verdict to hold a fortiori. Pre-committed direction: `|ci_95| width ≥` the committed width. A *narrowing* would be the surprise (see landing).

**Landing rule.**
- **(ii-a) Verdict survives, interval widens or is unchanged** (expected): tex 981's sentence *"Propagated coefficient uncertainty therefore leaves the forward simulation with no useful precision, an additional reason the aggregate dollar figure is held to the aggregate-level role assigned below and is not carried in the abstract"* gains one clause naming the joint construction and the wider interval; the numbers in the preceding sentences (median `$922.6`B, IQR `$900.1--$1{,}130.6`B, 95% `$[-4{,}459.8, +1{,}190.1]$`B, mean `$598.9`B / `78.3\%`, share interval `[-583.2\%, +155.6\%]`, SE `201.9`, `83.8\%` above benchmark) are restated at the joint values. **tex 400** (tab:estimators note, *"its refit-and-resimulate interval, and the spec v3 provenance of every Path A inferential object, are reported in Section~\ref{sec:patha}"*) is updated for provenance. Path A is excluded from every headline figure, so **nothing propagates to any headline number**.
- **(ii-b) Interval narrows materially** (>20% narrower): the joint construction is *more* favorable to Path A than the current one. **Do not adopt it as the headline Path A interval.** Report both, keep the wider committed interval as the quoted one, and state that the joint construction is narrower. Same logic as C1 branch (c). **⚖ flag to Eugene.**
- **(ii-c) Spec-v4 replications fail at a materially higher rate than 2/200**: this *is* the "branch-unstable" claim at tex 623/981 measured rather than asserted. Land the measured failure count in tex 981 in place of the qualitative claim. Good outcome; land it either way the interval goes.

**Parity checks.** P1 (blocking): stage A at spec v3, seed 42, α=1e-4 reproduces `hazard/data/hazard_bootstrap_draws.csv` **row-for-row to 1e-12** (198 rows) and `hazard_bootstrap_se.json .se/.ci_95/.frac_le_0` to 1e-9. Without P1 nothing downstream is interpretable. P2: stage B with the head **forced to production** except the 3 macro betas reproduces `bootstrap_resimulate_results.json` to 1e-6 on `trapped_b.{mean, median, ci_95}`. P3: the point head reproduces `hazard_coefficients_specv3.json` (v3) / `hazard_coefficients.json` (v4) macro coefficients to 1e-9.

**Artifact.** `/Users/eugene/…/hazard/data/pathA_bootstrap_fullvec_draws_specv3.csv`, `…_specv4.csv` (198±/200 rows × 22 head columns + 3 scales + `converged`), `…_fe_specv3.npz` / `…_specv4.npz` (tier 2), and `/Users/eugene/…/hazard/data/pathA_resimulate_joint_results.json`:
```
mode, status, spec, spec_versions:[3,4], parity_gates{P1..P3}, parity_gates_all_pass,
construction.tier1.{ head_swapped:[const,age_spline,macro,months], fe:"production" },
construction.tier2.{ fe_map_rule:"mean over stratum_id_src duplicates; production fallback for undrawn",
                     rule_is_arbitrary: true, mean_undrawn_share },
results.<spec>.<tier>.{ n_reps, n_failed, point_trapped_b, point_share_pct,
                        trapped_b{mean,se,median,iqr,ci_95}, share_pct{…},
                        frac_above_benchmark },
comparison_vs_committed.{ committed_ci_95_b, joint_ci_95_b, width_ratio },
verdict.{ code: SURVIVES_WIDER | SURVIVES_UNCHANGED | NARROWS | V4_UNSTABLE,
          manuscript_action },
runtime_s
```

---

## C6(iii) — `pathA_cold_starts`

**Run name / file:** `pathA_cold_starts` → `/Users/eugene/somthing/Lock In effect/Lock-in-Effect/hazard/pathA_cold_starts.py`

**Engine entry.** `bootstrap_se.fit_betas` on the **production training panel** (10,176 cells, no resampling — this is the multimodality probe on the *production* likelihood, which is what makes it decisive; the documented instability is on *resampled* panels), `seasonal=True` (spec v4), α = 1e-4, with `start_head` supplied per start. Panel via the same filters as `bootstrap_se.main()` lines 278–283 (`enrich_panel_with_macro`, dropna, `exposure > 0`, `period < HOLDOUT_DATE`).

**Parameterization — 50 starts, pre-committed composition:**
- **1** production warm start (`production_start_head(prod)`) → the anchor, must return the production coefficients (gate G1)
- **1** true cold start (`start_head=None` → `_fit_poisson_glm`'s own IRLS default). *This is the exact configuration `production_start_head`'s docstring warns about* ("cold IRLS on the seasonal design can land a different penalized optimum") and it is the single most informative draw in the run
- **48** dispersed starts: `head_s = head_prod + σ_s ⊙ z_s`, `z_s ~ N(0, I)` under `default_rng(1000 + s)`, with `σ_s` scaled from a fixed ladder `σ ∈ {0.25, 0.5, 1.0, 2.0}` × `|head_prod|` elementwise (floored at 0.05 absolute so zero-valued entries are still perturbed), **12 draws per ladder rung**. Seeds fixed and recorded per start
- FE coefficients start at zero in every case (`fit_betas` line 138 sets them so)
- Non-converged / `|β|>20` starts are counted as failures, not draws (`MAX_ABS_BETA = 20.0`, line 74)

**Branch classification, fixed ex ante.** A start "lands on the production branch" iff all three macro coefficients are within **0.02** (standardized units) of the spec-v4 production values `(+0.65, −0.17, −0.007)` **and** the penalized log-likelihood is within `1e-4` of the production fit's. Report the full triple and the objective value for every start; cluster the non-production landings by rounding the triple to 3 decimals and report the distinct optima with their objective values and multiplicities.

**Pre-committed expectation (R1's own).** *"Majority land on production branch."* Concretely: **≥ 26/50 on the production branch**, and — the sharper prediction — the production branch has the **best (lowest) penalized objective** among all distinct optima found. The documented instability is on *resampled* panels with 20 inestimable FEs (tex 1051, `ridge_reference_weighting.json .estimable_strata_mle.note`: *"the reference-swap sensitivity above is an optimizer-path artifact of penalized cold-start refits, not information in the production point"*); on the full production panel the reference stratum `2017_200_740+_≤80` is **not** among the 20 zero-event strata (same note), so the production panel is the better-conditioned case.

**Landing rule.**
- **(iii-a) Majority on production branch AND production has the best objective** (expected): tex 981's *"bootstrap replications under the spec v4 seasonal design are branch-unstable (the resampled penalized likelihood has a second optimum that attracts replications away from the production branch)"* gains its scope made explicit and measured: `…branch-unstable on resampled panels (the resampled penalized likelihood has a second optimum that attracts replications away from the production branch); on the production panel itself N of 50 dispersed starts land on the production branch and no start reaches a better penalized optimum (run \texttt{pathA\_cold\_starts})`. Same clause echoes at **tex 623**, the other `branch-unstable` site. The exclusion sentence (*"Path A is excluded from the paper's headline figures for this reason"*) **stays** — it rests on the *resampled* instability, which this run does not touch.
- **(iii-b) Minority on production branch, but production still has the best objective**: the production point is the global optimum and the basin is small. Report the count honestly; the exclusion is strengthened, not weakened. Land in the same two sentences with the unfavorable number.
- **(iii-c) SURPRISE — a start reaches a strictly better penalized objective than production** (objective lower by >1e-4 with a materially different macro triple): **STOP. Report to Eugene. Land nothing.** Path A is excluded from every headline figure, so **no headline number is at risk and nothing propagates** — but the *disclosure* sentences would all need re-derivation, and that is an author decision, not a spec branch. The sites that would be in scope, enumerated so the stop is actionable:

  | tex | content at risk |
  |---|---|
  | 290 | §V: *"Its aggregate recovery is \$928.9 billion, 121.5\% standalone --- reported as corroboration only and excluded from every headline figure"* |
  | 310 | sixth qualification: *"Path A's fitted rate-gap coefficient is $+0.29$ per 100 bp… I compare them on sign rather than magnitude"* |
  | 390 | tab:estimators row: *"Hazard Path A: stratum-month Poisson PML (spec v4, calendar-month) … \$928.9B … 121.5\%"* |
  | 400 | tab:estimators note: *"Path A's point estimate carries no useful forward precision and is excluded from headline figures"* |
  | 680 | tab:crosswalk: *"Path A 112.4\% (121.5\% standalone) … spec v4 (non-headline corroboration)"* |
  | 978, 980, 981, 983 | §`sec:patha`: the ridge-device paragraph, the coefficient/exclusion paragraph, the holdout paragraph |
  | 987 | *"excluded from the paper"* |
  | 995–998, 1003 | tab:panel / tab:bootstrap and the spec-provenance note |
  | 1051, 1053 | App. `app:ridge` opening and the exclusion restatement |
  | 1088 | tab:bootstrap *"198 of 200 replications converged"* |
  | — | `pathA_seasonal_adoption_results.json .gate_b_v4_target` (`trapped_b 928.892970289881`, `r_lag0 −0.37817286723880483`, `peak_lag −2`) and every gate asserting them |

  **⚖ posture.** A better optimum on the production panel would mean the adopted spec-v4 fit is not the fit its own gates think it is. That is Eugene's call, and it is the reason this branch stops rather than lands.
- **(iii-d) The true cold start alone diverges but all dispersed starts converge to production**: this is the *expected* signature of the documented Gate-B lesson. Report it as confirmation of the warm-start device; no tex change beyond (iii-a)'s clause.

**Parity checks.** G1 (blocking): the production warm start returns `hazard_coefficients.json .coefficients.{rate_gap_bps, burnout_orth, friction}` to 1e-9 and reproduces `.fit_method = "ridge(alpha=0.0001)"`. G2: n_train = 10,176 and n_strata = 296 (matching `hazard_coefficients.json .n_train / .n_strata`). G3: `_month_dummy_matrix` yields exactly 11 columns and the head length is 22.

**Artifact.** `/Users/eugene/…/hazard/data/pathA_cold_starts_results.json` + `…_draws.csv` (50 rows: `start_id, kind ∈ {warm_production, cold, dispersed}, sigma_rung, seed, converged, rate_gap_bps, burnout_orth, friction, penalized_objective, on_production_branch, l2_distance_to_production`), with
```
verdict.{ n_on_production_branch, n_failed, distinct_optima[]:{triple, objective, count},
          production_is_best_objective: bool,
          code: MAJORITY_PRODUCTION | MINORITY_PRODUCTION | BETTER_OPTIMUM_FOUND,
          manuscript_action }
```

---

## C6.7 What must NOT change (all three sub-runs)

`hazard/bootstrap_se.py`, `hazard/bootstrap_resimulate.py`, `hazard/ridge_reference_weighting.py`, `hazard/pathA_seasonal_adoption.py`, `hazard/pathA_v4_holdout.py` — imported, never edited, never run as `__main__`. **`hazard/data/hazard_bootstrap_draws.csv` and `hazard_bootstrap_se.json` must not be overwritten** (see C6.0). `hazard/data/hazard_coefficients.json`, `hazard_coefficients_specv3.json`, `ridge_reference_weighting.json`, `bootstrap_resimulate_results.json`, `pathA_v4_holdout_results.json`, `pathA_seasonal_adoption_results.json` — all frozen. `hazard/config.py` (`RIDGE_ALPHA`, `RIDGE_ALPHA_GRID`, `AGE_SPLINE_KNOTS`, `HOLDOUT_DATE`). Path A's `$928.9B / 121.5\%` and its exclusion from every headline figure. And — the whole point of the exclusion — **no Path A result may enter any headline number under any branch of any of the three sub-runs.**

---

# Cross-spec dependencies and sequencing

1. **C1 → C2.** C2 cannot run until C1 persists the R2 `t*` draws (both weight schemes). If C1 is deferred, C2 gains a standalone step-0 rerun of `fu.cluster_bootstrap_cpr` with draws dumped.
2. **C1 and C3 collide on tex 312 and tex 364.** C1 branch (b) rewrites gate #98's `posture_binding_layer` span; C3 branch (a) rewrites the *same span*. If both fire, they land in **one** commit with **one** re-derivation of the span, not two.
3. **C1 and PLAN item A7 collide on tex 364's final sentence** ("No single cluster dominates the primary read"). Assign once.
4. **C3 is independent of C1/C2** and is the cheapest run in the plan (~3.5 min, 16 legs). It can go first and its result is what determines whether the layer-ranking sentence needs re-derivation at all.
5. **C6 is independent of C1/C2/C3** and touches no headline number under any branch.
6. **Before any tex edit in any of these specs:** re-derive the 12-occurrence census in §0 (PLAN §0.2 — the and-form and bracket-form are gate-invisible, which is exactly the blindness that let a defect survive round 26), read the gate SOURCE (all counts are `>=`), and recount after every batch.
