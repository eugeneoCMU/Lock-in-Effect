# SPEC — R32 / C-72: month-clustered and two-way (stratum × month) ladder rungs

**Status: PRE-COMMITTED. Committed BEFORE the runner, and both before the run.**
Run tag: `floor_inference_correction_v3`. Runner:
`hazard/floor_inference_correction_v3.py` (not yet written; this spec lands first and stands on
its own). New artifact: `hazard/data/floor_inference_correction_v3_results.json`.

---

## 1. The condition

C-72 (R1:M3, MAJOR, RUN). **No "month-clustered" and no "two-way" string exists anywhere in the
manuscript**, and the committed cluster unit is cross-sectional only:
`floor_uncertainty_results.json:part_a_sampling_uncertainty.cluster_unit` =
`"4-way stratum (vintage x coupon-bps x fico_bucket x ltv_bucket; stratum.build_stratum_id)"`.
The condition: the **month-level common shock the current scheme cannot see must be priced, or
shown not to matter**. Site: T9 `tab:ladder`, `\label{tab:ladder}` at **`.tex:479`**.

## 2. Two corrections to the condition's own framing, recorded before the construction

**(a) The cluster unit is NOT a function parameter.**
`hazard/floor_uncertainty.py:206` hard-codes `sel.groupby("stratum", sort=True)`. The inventory's
"cluster unit is a read parameter" is loose: it is a **column**, not an argument. Month-clustering
is therefore done by handing `cluster_bootstrap_cpr` a selection whose `stratum` column carries the
month id — a data substitution, which the runner must perform **explicitly and visibly** rather
than by a silent rename. The committed function is imported unmodified.

**(b) Two-way *fixed effects* and two-way *clustering* are different objects, and the inventory
conflates them.** `episode_confrontation_within_results.json:limb_c.confounds_note` records that a
two-way **(stratum + month) FE** variant of the neighbouring within-*estimator* is "EXACTLY
unidentified". That is a statement about a regression's identification, and it does **not** carry
over to a two-way **cluster-robust variance** on this read. Two-way clustering
(Cameron–Gelbach–Miller) is computable in principle; its failure modes are different and specific:
a **non-positive-definite variance estimate** and a **tiny effective df**. This spec expects
infeasibility for *those* reasons and states them, rather than importing an argument that does not
apply.

## 3. What is already known — DECLARED, NOT PREDICTED

Read from committed artifacts at scoping, *before this spec existed*:

| object | source | value |
|---|---|---|
| the read | `FLOOR_LADDER_READ` | `R2_2018_gap<=-0.0025_age>=12` — `rp 201801..201812, gap<=-0.0025, age>=12` |
| point | `floor_uncertainty_results.json` | `point_cpr_pct = 4.990624060575566` |
| support | same | **`n_cohort_months = 137`**, **`n_clusters = 31`** (strata) |
| committed percentile CI | same | floor `[4.368576777908708, 6.003552252675821]`% |
| **already truncating** | same | `mapped_marginal_at_6.5.truncated_at_grid_edge = true`, `n_draws_outside_grid = 26` |
| mapped marginal CI | same | `[2.974329560125351, 8.01850965353176]` pp |
| CR1 $t(30)$ rung | `tab:ladder` / v2 artifact | $+3.2$ to $+8.3$ |
| CR1 Bell–McCaffrey rung | same | $+2.8$ to $+8.8$ at $t(6.2)$ |
| Webb designer units | gate #107 | floor interval **4.177% to 5.800%** |
| PCHIP grid | `floor_inference_correction.py:36–50` | **[2.0, 6.0]% CPR, NEVER extrapolated** |

**$G_{\text{month}}$ is NOT known and this spec does not compute it.** The selection is calendar
2018, so $G_{\text{month}} \le 12$; 137 cohort-months across 31 strata averages ~4.4 months per
stratum, so the panel is unbalanced and the distinct-month count could be anything from a handful
to twelve. The inventory asserts "5–6 month clusters"; **that is asserted, not verified here**, and
obtaining it requires `mdr.build_panel()` — a panel build plus a live FRED fetch — which this
spec deliberately does not perform. $G_{\text{month}}$ is a **measured input reported before any
interval is computed** (E2).

## 4. Construction

Every endpoint is mapped through the committed `FloorMapping` PCHIP using **v1's grid-edge
truncation convention** (`floor_inference_correction.py:36–50`): an endpoint outside [2.0, 6.0]% is
mapped **at the nearest grid edge** and flagged `truncated_at_grid_edge`, with the direction stated
(the marginal decreases in the floor, so a floor endpoint above 6.0% yields a marginal edge that is
an **upper bound** on the truncated true edge). **Never extrapolated.** v2's convention is reused
unchanged, not re-derived.

**Three new rungs, on the same R2 read:**

1. **Month-clustered.** `cluster_bootstrap_cpr` with the cluster column set to the reporting month.
   Plus the CR1/CR2/CR3 sandwich family and the Webb six-point wild-cluster bootstrap-$t$
   (B = 9999, fresh `default_rng(42)` per read per procedure) from
   `floor_inference_correction_v2.py`, all at $G = G_{\text{month}}$, with **both** the
   conventional $t(G-1)$ and the Bell–McCaffrey/Imbens–Kolesár data-driven df, and the
   Carter–Schnepel–Steigerwald effective-cluster count $G^{*} = 1/\sum h^2$.
2. **Two-way (stratum × month), Cameron–Gelbach–Miller.**
   $\hat V_{\text{2way}} = \hat V_{\text{stratum}} + \hat V_{\text{month}} - \hat V_{\cap}$, with
   the intersection clusters being the stratum-month cells (there are 137 of them). df taken as
   $\min(G_{\text{stratum}}, G_{\text{month}}) - 1$.
3. **The committed stratum rung, replayed** — the parity anchor (E1).

## 5. Pre-commitments

**STOP-class:**

- **E1 — the stratum rungs replay bit-identically.** Under stratum clustering this runner must
  reproduce `floor_inference_correction_v2_results.json`'s R2 rungs exactly: `cr1_t_interval`,
  `cr1_t_interval_df_bm`, `cr3_t_interval`, `wild_t_webb.floor_ci95_pct`, and
  `df_bm_by_estimator` — **all read live from that artifact**, never from literals in the runner.
  A miss is an environment alarm and a STOP. v2 and v1 and their artifacts are **FROZEN: read,
  never written.**
- **E2 — feasibility before outcome.** $G_{\text{month}}$, the distinct-month list, the
  cohort-month count per month, and the CSS effective-cluster count are computed and written
  **before** any interval is read, in the committed runs' ex-ante-inspection convention. No
  threshold below may be resolved after seeing an interval.

**GENUINE predictions** (may fail; a miss lands with the miss named):

- **E3 — month clustering widens the interval.** The month-clustered mapped-marginal width exceeds
  the committed CR1 $t(30)$ width ($+3.2$ to $+8.3$, i.e. 5.1 pp). Rationale: 31 clusters drop to
  at most 12. **It can fail** — if the month-level common shock is small relative to the
  cross-sectional variance, the month-clustered SE can come in *narrower*, and that would be the
  condition's "shown not to matter" answer, which is a perfectly good landing.
- **E4 — the upper endpoint truncates at the grid edge.** The month-clustered floor interval's
  upper endpoint exceeds **6.0%** and is flagged `truncated_at_grid_edge`. Declared basis: the
  committed *stratum*-clustered percentile CI already reaches 6.0036% with 26 draws outside the
  grid and the flag already set; a wider interval truncates harder. **Consequence, pre-committed:**
  the mapped upper marginal is then a **bound, not an estimate**, and any landed row must say so in
  the same words the committed table already uses.
- **E5 — the two-way rung's computability is NOT predicted.** It is a **first-class branch**
  (§6, NC-2), not a failure. Predicting it either way would be a guess.

## 6. NOT_COMPUTABLE branches — first-class landings, each with its own trigger

- **NC-1 — too few month clusters.** $G_{\text{month}} < 5$. The month rung is reported
  NOT_COMPUTABLE with the count, and the reason lands in the tablenote. (Bell–McCaffrey df would
  then be below 4 and the $t$ critical value is not usable as an inference statement.)
- **NC-2 — the two-way variance is not positive.** $\hat V_{\text{2way}} \le 0$. Reported
  NOT_COMPUTABLE **with the negative estimate printed**. **The run REFUSES the standard
  zero-truncation fix** and says why: truncating a negative variance to zero manufactures a usable
  standard error out of an unusable estimate, and a rung built that way would look like inference
  and not be. The eigenvalue-correction variant is likewise not substituted.
- **NC-3 — both endpoints leave the grid.** If the mapped interval truncates at *both* edges it
  carries no information about either bound and is reported NOT_COMPUTABLE rather than printed as
  [2.0-edge, 6.0-edge].
- **NC-4 — bootstrap resolution floor (a disclosure, not a stop).** With $G_{\text{month}} \le 8$,
  Rademacher weights admit fewer than $2^8 = 256$ distinct sign vectors and the wild-$t$ p-value
  has a hard resolution floor. **Webb six-point is therefore primary** (as it already is in v2),
  the Rademacher variant is reported alongside, and its resolution floor $2^{-G_{\text{month}}}$ is
  written into the artifact so no p-value is read past its own granularity.

**NOT_COMPUTABLE is the expected outcome and it is a landing.** The condition is discharged by
"shown not to matter" or by "shown not to be estimable here, with the count", not only by a new
interval.

## 7. Gates

- **P0** sha pins on `hazard/floor_uncertainty.py`, `hazard/floor_inference_correction.py`,
  `hazard/floor_inference_correction_v2.py`, `hazard/matched_depth_reconciliation.py` and both
  committed artifacts; **P0a** AST import-safety on each; **P0b** all artifacts byte-identical
  after import and at exit.
- **P1** — E1, live.
- **P2** — the R2 selection reproduces `n_cohort_months = 137` and `n_clusters = 31` and
  `point_cpr_pct = 4.990624060575566` to $10^{-9}$ before any new cluster unit is applied.
- **P3** — the cluster substitution is **visible**: the artifact records, for each rung, the column
  actually grouped on and the resulting cluster count, so a reader can see that the month rung
  really clustered on months.
- **P4** — the PCHIP mapping is v1's truncation convention and **not** `_map_draws`'s exclusion
  convention; asserted by re-mapping a known out-of-grid endpoint and checking it lands **at** the
  edge with the flag set, rather than being dropped.
- **P5** — the BM df self-test: with equal cluster weights the data-driven df returns $G-1$
  (v2's blocking P6, replayed at the new $G$).
- **W1** — writes **only** `hazard/data/floor_inference_correction_v3_results.json` plus its own
  `t^*` CSVs under a `v3_` prefix; refuses to overwrite a differing file; **never writes v1's or
  v2's artifacts**; edits no `.tex`.
- **No engine.** PCHIP mapping and bootstrap only; nothing under `hazard/data/floor_sweep/`.

## 8. Landing rules, per branch

- **Branch A — gates pass, both new rungs computable.** Add **two rows** to `tab:ladder` plus a
  note clause naming the cluster unit of each. **Gate #107's ordering assert must survive**: it
  requires `cr1_conventional` to precede `"CR2 $t$ & $+3.0$ to $+8.6$"` and `cr1_bell_mccaffrey` to
  precede `"CR2 $t$, Bell--McCaffrey"`, so **the new rows are appended after the existing CR2 rows**
  and no existing row is moved or re-worded. `FLOOR_LADDER_SPANS` is **extended, never replaced**.
  New gate + test battery; `tab:runindex` row. The manuscript gains its first "month-clustered" and
  "two-way" strings.
- **Branch B — gates pass, month rung computable, two-way NOT_COMPUTABLE (NC-2).** Land **one**
  row plus a note sentence recording that the two-way estimator returns a non-positive variance at
  this cluster configuration and that the zero-truncation fix was **refused, not overlooked**.
  This discharges the condition: the month shock is priced, and the two-way limb is shown not to be
  estimable here.
- **Branch C — E3 fails: month clustering *narrows* the interval.** **Land it.** That is the
  condition's own alternative — "or shown not to matter" — and it is the outcome most favourable to
  the paper, so it must be reported with the pre-committed direction quoted beside it and
  explicitly flagged as having gone against my prediction.
- **Branch D — NC-1 or NC-3: neither rung is computable.** Land the negative result at
  `tab:ladder`'s note with $G_{\text{month}}$, the truncation flags and the grid edges. No new
  rows, no gate change beyond the artifact reference. **This is a landing, and on the evidence
  above it is the most likely one.**
- **Branch E — P0–P5 or E1/E2 fails.** Land nothing; commit the runner output and a failure record.

## 9. Scope limits this spec commits to stating

1. **This prices sampling uncertainty, not the floor's level.** The ladder is an interval exercise
   on one read; it does not move the point estimate and no branch may be written as if it did.
2. **The truncation convention is a bound, not a measurement.** Wherever E4 fires, the mapped
   endpoint is a bound on the truncated true edge and stays labelled as one — the same discipline
   the committed table already applies.
3. **One read only.** The primary object is R2, as in v2. R1/R3/R4 may be reported for context;
   R5 stays excluded ex ante, as v2 excluded it.
4. **$G_{\text{month}} \le 12$ is a ceiling from the selection's calendar year**, not a
   measurement. If the realized count is at the low end, every interval on the month axis is a
   small-$G$ object and the artifact must present it as such rather than as a routine
   cluster-robust interval.
