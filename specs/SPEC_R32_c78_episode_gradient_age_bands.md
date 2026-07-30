# SPEC — R32 / C-78: the episode gradient within narrow age bands

**Status: PRE-COMMITTED. Committed BEFORE the runner, and both before the run.**
Run tag: `episode_gradient_age_bands`. Runner: `hazard/episode_confrontation_age_bands.py`
(not yet written; this spec lands first and stands on its own).
New artifact: `hazard/data/episode_gradient_age_bands_results.json`.

---

## 1. The condition

C-78 (DA:A2, MAJOR, RUN). `.tex:331` carries the paper's **only realized-data exhibit that moves
in the lock-in direction**: a $+4.20$ CPR-point gap gradient, stratum-cluster 95% interval
$[+3.59, +4.66]$, one-sided permutation $p = 0.005$, against a model-implied $+0.94$. The
composition limb has been tested (`episode_confrontation_within`, standardized $+3.44$), but the
standardization holds **vintage $\times$ FICO $\times$ LTV and not age**, and the same sentence
lists "residual seasoning past the age cut" among the confounds still open. The condition: the
exhibit must be shown not to be a seasoning artifact, with loan age in the standardization cells
as **12-month strata**.

The manuscript's own hedge is the target. It currently reads "the excess is **not composition in
the dimensions the panel can hold fixed**". Age is a dimension the panel *can* hold fixed, so
either that clause tightens or the exhibit weakens.

**Note on line numbers.** The inventory cites `.tex:315`; the live site is **`.tex:331`** in the
153pp manuscript. The inventory's number is stale, and this spec uses the live one.

## 2. What is already known — DECLARED, NOT PREDICTED

Read from the committed `episode_confrontation_within_results.json` during scoping, *before this
spec existed*. These are the reference points E4 and E5 are stated against; they are measurements,
not predictions:

| object | committed value |
|---|---|
| FG branch actually taken | **FG-1**, axis `vintage_fico_ltv` |
| common cells / shallow coverage | **18** cells, **99.72%** shallow exposure, 100.00% deep |
| Limb B total (identity) | `total_pp = 4.198179219676357` |
| Limb B `between_composition_pp` (full cell) | **+0.7679069252018227** |
| Limb B `within_composition_pp` (full cell) | **+3.430272294474534**, `identity_residual = 0.0` |
| `between_by_axis.vintage_only` | between **+0.3504588404194209**, 4 cells |
| `between_by_axis.fico_ltv_only` | between **+0.37292703507091396**, 6 cells |
| primary selection | 290 strata total, 276 bucketed, **159 primary** (age0 $\ge$ 24), 6346 rows |
| endpoints | shallow `[-1,0)`, deep `<=-3` |

So on the committed axis **composition of any kind accounts for +0.77 of +4.20 (18.3%)**, and the
vintage axis alone for +0.35 (8.3%). Nothing in scoping computed anything on an age axis.

## 3. The structural fact this spec must confront first

`age0` is **already a stratum-level attribute** in the committed machinery:
`episode_confrontation.py:674` computes it as
`first["mean_loan_age"] - _months_since_window_start(first["rp"])` — the stratum's loan age at the
window's first observed month. It is therefore eligible as a standardization axis in exactly the
way vintage, FICO and LTV are, and no new data is needed. That is what makes C-78 computable at
all.

**But `age0` and `vintage` are near-collinear by construction.** `vintage` is an origination
*year* and `age0` is age at one common date (2022-06), so within a vintage the age spread is
about twelve months — roughly the width of one band. A 12-month age band is therefore close to a
relabelling of vintage, and adding it to a cell that already contains vintage mostly *fragments*
cells rather than adding orthogonal information. This spec does not assume that; it makes it
**E3**, a falsifiable prediction, and it builds the axis both ways so the run is informative
whichever way E3 falls.

**One thing this run cannot do, stated up front.** The literal "within-stratum gradient" remains
NOT COMPUTABLE for the reason `episode_confrontation_within.py`'s header establishes: the stratum
id contains coupon and gap = coupon − market rate, so every stratum lives in exactly one bucket.
Adding age changes nothing about that. This run is composition control on an age axis, not a
within-stratum estimator, and the artifact must say so.

## 4. Construction

**Age axis.** `age_band(stratum) = floor(age0 / 12)`, labelled by its month range
(`[24,36)`, `[36,48)`, …). Built on `age0` — the stratum-constant object — and **not** on the
time-varying `mean_loan_age`, because the standardization template weights cells by exposure share
and a time-varying cell would not be a cell. The primary selection's `age0 >= AGE0_MIN = 24` cut
is held at production, so the lowest band starts at 24 months.

**Two axes, evaluated in this fixed order:**

- **`AXIS_AGE_FULL = (vintage, fico_bucket, ltv_bucket, age_band)`** — the condition read
  literally: age *added* to the committed cell.
- **`AXIS_AGE_ONLY = (age_band, fico_bucket, ltv_bucket)`** — age *replacing* vintage. This is the
  more informative test if E3 holds, and it is the direct analogue of the committed run's FG-2
  fallback.

**Feasibility gate, thresholds carried across UNCHANGED from the committed run** (they are not
re-tuned for this axis; re-tuning them here would be exactly the gaming this round forbids):

- **FG-1′** `coverage_shallow >= 0.30` **and** `>= 10` common cells on `AXIS_AGE_FULL`
  $\rightarrow$ Limb A′ on that axis. Attainable: 5 vintages $\times$ 3 FICO $\times$ 2 LTV
  $\times$ $n$ bands $\ge 30$ possible cells.
- **FG-2′** else `coverage_shallow >= 0.30` and `>= 2` common cells on `AXIS_AGE_ONLY`
  $\rightarrow$ Limb A′ there. The cell bar is **2**, not 10, for the committed run's own
  documented reason: that axis carries at most $n \times 3 \times 2$ cells and a literal 10 would
  make the branch unreachable and delete it. The adaptation is inherited verbatim, and the
  artifact must record what a literal 10 would have returned.
- **FG-3′** else Limb A′ is **NOT_COMPUTABLE**. This is a **landing**, not a failure — and it is
  not a dead end here, because Limb B′ below is an identity and always reports.

FG is computed from `exposure_upb` and cell/stratum counts **only**, before any outcome on this
selection is read, exactly as the committed run does.

**Limbs.**

- **Limb A′ (primary, may degenerate).** Composition-standardized gradient on the chosen axis:
  the committed `_standardize` template unchanged — shallow-bucket cell exposure shares as
  weights, ratio imputation from the nearest populated common cell by L1 ordinal distance with the
  flat fallback, **imputed weight share reported**. Uncertainty from the imported
  `joint_gradient_bootstrap` convention, 1000 reps, seed 42, imputation re-applied inside every
  replicate. The age axis gets an ordinal encoding by band index; ties broken as in the committed
  rule (larger deep exposure, then lower cell id).
- **Limb B′ (identity, ALWAYS computable — the guaranteed landing).** The exact telescoping
  within/between decomposition, with `between_by_axis` **extended by two entries**:
  `age_only` and `vintage_x_age`, alongside the committed `full_cell`, `vintage_only` and
  `fico_ltv_only`. `age_only`'s between-component is the direct numerical answer to DA:A2 — how
  much of $+4.20$ is seasoning composition — and it exists **even under FG-3′**.
- **Limb C — NOT re-run, deliberately.** The committed run's `limb_c.confounds_note` already
  records that the two-way (stratum + month) FE variant is "EXACTLY unidentified and is not run".
  Age adds nothing to that estimator, since age within a stratum is a deterministic function of
  calendar time. Re-running it would be an empty run. (This is the same structural wall C-72
  meets; the two conditions should cite one another rather than each re-deriving it.)

## 5. Pre-commitments

**STOP-class** (failure means the environment or the construction is wrong; land nothing):

- **E1 — parity.** G0–G6 all pass (§6). A G5 miss is an **environment alarm**, not a finding.
- **E2 — the decomposition telescopes.** `identity_residual < 1e-12` on **every** axis reported,
  computed and asserted rather than assumed.

**GENUINE predictions** (may fail; a miss lands with the miss named):

- **E3 — age is near-collinear with vintage.** At least **80%** of primary-selection shallow
  exposure sits in (vintage) groups whose strata fall entirely within a **single** age band.
  Rationale in §3. **If E3 fails, age carries real variation orthogonal to vintage and the test is
  substantially stronger than expected** — a good outcome, and one that makes FG-1′ more likely to
  clear.
- **E4 — seasoning composition is not the story.** Limb B′'s `age_only` between-composition
  component is **below +2.099pp** (half the raw $+4.198$, the committed run's own
  "materially closed" bar). Declared reference: the committed `vintage_only` between is $+0.3505$
  and `fico_ltv_only` is $+0.3729$ — both small — so if E3 holds the age component should be the
  same order. **I do not know this and it may fail.**
- **E5 — the standardized gradient survives the age axis.** If Limb A′ is computable, its
  standardized gradient stays **above +2.099pp**. **I do not know this and it may fail.**

**The failure that would matter most, named in advance.** If E4 or E5 fails — the gradient
collapses once age is held fixed — then the paper's only realized-data lock-in exhibit is
substantially a seasoning artifact, the `.tex:331` clause "not composition in the dimensions the
panel can hold fixed" becomes **false as written**, and `tab:assembly`'s upward entry has to come
out or be re-signed. **That result lands.** It is pre-authorised here in full, in writing, before
the run, precisely because it is the outcome that costs the paper most.

## 6. Gates

- **G0–G5** — replicated from `episode_confrontation_within.py` line for line, with constants and
  tolerances **read from the imported module** (`ec.E3_POOLED_FREDDIE`, `ec.TOL_*`, …) so there is
  one source of truth. `episode_confrontation.py` is **imported, never modified, and its `main()`
  is never called** — calling it would rewrite its frozen artifact. Order is unchanged:
  G0–G4 $\rightarrow$ selection + FG (exposure and counts only) $\rightarrow$ G5 (first outcome
  read) $\rightarrow$ limbs. FG sits before G5 so no threshold can be tuned on an outcome.
- **G6 (NEW — the axis-machinery identity gate).** Run this runner's own decomposition with its
  axis set to the **committed** `(vintage, fico_bucket, ltv_bucket)` and require it to reproduce
  `episode_confrontation_within_results.json` **bit-identically**: `total_pp`
  4.198179219676357, `between_composition_pp` 0.7679069252018227, `within_composition_pp`
  3.430272294474534, `n_cells` 22, `identity_residual` 0.0, `between_by_axis.vintage_only`
  0.3504588404194209, `between_by_axis.fico_ltv_only` 0.37292703507091396 — all to $10^{-12}$,
  **read live from the committed artifact rather than from literals in the runner**. This is what
  certifies the age axis is being cut by the committed machinery and not a re-implementation.
- **G7** — the FG selection reproduces the committed selection counts exactly (290 / 276 / 159
  strata, 6346 primary rows, endpoints `[-1,0)` and `<=-3`), read live from the committed
  artifact. A drift here means the panel or the FRED fetch moved and the comparison is void.
- **W1** — writes **only** `hazard/data/episode_gradient_age_bands_results.json`; refuses to
  overwrite a differing file; **never writes `episode_confrontation_results.json` or
  `episode_confrontation_within_results.json`**; edits no `.tex` file; never touches `config.py`.

**MUST NOT CHANGE:** `episode_confrontation.py`, `episode_confrontation_within.py` and both their
artifacts; `matched_depth_reconciliation.build_panel`; `floor_uncertainty.cluster_bootstrap_cpr`;
the bucket rule, the age cut and the support rule; and the pinned literals
$+4.20$ / $[+3.59, +4.66]$ / $+0.94$ / $0.68$ / $p = 0.005$ at `.tex:331` and in **gate #75**
(`tools/liveness_gates.py:4873–4890`), which pins `"$+4.20$ CPR points"`, `"$[+3.59, +4.66]$"`,
`"$+0.94$ points at the central"`, `"unusable as a measurement of its size"` and
`"monthly-timing nulls above stand unchanged"`. Those are the **raw** numbers and they stay raw
under every branch below.

## 7. Landing rules, per branch

Evaluated in this total, deterministic order:

- **Branch A — E4 and E5 both hold (or E4 holds and Limb A′ is NOT_COMPUTABLE).** The seasoning
  limb is tested and small. `.tex:331`'s clause is **tightened**: "not composition in the
  dimensions the panel can hold fixed" is replaced by a version naming age explicitly, with the
  `age_only` between-component quoted. Gate #75 is **extended, never replaced** — the raw $+4.20$
  stays. New gate + test battery on the age-axis numbers; `tab:runindex` row. No new
  `tab:assembly` row (the existing composition entry already carries this exhibit).
- **Branch B — E4 or E5 misses but the gradient stays signed and above the implied $+0.94$.**
  **Land anyway**, with the pre-committed +2.099 bar quoted beside the realized value and the miss
  named in the text. The `.tex:331` clause is re-scoped downward: composition in the panel's
  dimensions now explains a materially larger share, and the exhibit's weight drops accordingly.
- **Branch C — the gradient collapses to at or below the implied $+0.94$, or its CI covers zero.**
  **Land the collapse.** `.tex:331`'s composition sentence is rewritten to say the exhibit does
  not survive holding age fixed; `tab:assembly`'s upward entry is withdrawn or re-signed
  (**[posture] — Eugene signs the assembly change**); the abstract's and §V.D's reliance on this
  exhibit is re-scoped. Gate #75's raw literals still stand — they describe the raw gradient,
  which is unchanged — and the new gate pins the collapse.
- **Branch D — FG-3′ AND Limb B′'s `age_only` component is itself degenerate** (fewer than two
  populated age bands in an endpoint bucket). Land **NOT_COMPUTABLE** with the coverage numbers
  and the collinearity measurement from E3, reported at `.tex:331` as the answer DA:A2 gets: the
  age control this exhibit needs is not identified in a closed 2017–2021 book, because origination
  year and loan age are the same variable there. No gate change beyond the artifact reference.
- **Branch E — G0–G7 or E1/E2 fails.** Land **nothing** in the manuscript. Commit the runner
  output and a failure record under `specs/`.

## 8. Scope limits this spec commits to stating

1. **This closes the seasoning limb, not the refinancing limb.** `.tex:331`'s other named
   confound — within-window refinancing on the high-coupon shallow buckets — is separated by **no
   field in this design**, and stays open and stated under every branch above. Closing one of two
   confounds is not closing the confound.
2. **A cross-sectional level gradient is not a dollar marginal.** The committed exhibit's status
   line ("directional; not a marginal re-estimate") is preserved verbatim in every branch.
3. **The age cut is held, not swept.** `AGE0_MIN = 24` stays at production. This run stratifies
   *above* the cut; it does not test the cut's location. A run that moved the cut would change the
   selection and break G7's parity with the committed exhibit.
4. **Bands are cut on `age0`, one date.** Strata are not re-banded as the window advances. That is
   a modelling choice forced by the standardization template, and the artifact must name it rather
   than let a reader assume a time-varying age control.
