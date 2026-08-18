# RECORD — R32 fact-check of three load-bearing external claims (2026-07-30)

Mode: `deep-research` / `fact-check` (source verification only). Iron rule applied: a claim I
could not confirm is recorded FAIL, not "uncertain". **Findings 1 and 2 were FIXED on Eugene's instruction** (see the addendum at the end).
Finding 4 (licensing) remains his call; finding 3 constrains the C-76 spec.

---

## FINDING 1 — `berger2026` is cited from a SUPERSEDED draft, and its headline GE magnitude has moved 20×. **VERDICT: FAIL (material).**

**Cited as:** Berger, Jeong, Marx, Olesen & Tourre, *A Danish Fix for U.S. Mortgage Lock-in?*,
SSRN abstract 6150766, "draft January 2026".

**Verified:** the January draft exists and is dated **January 27, 2026** (62pp). But a later
version exists: **July 16, 2026, 84pp**
(`fabricetourre.com/wp-content/uploads/2026/07/ssrn_posted_paper_20260716-1.pdf`), which also
won a best-paper award at the 10th SAFE Household Finance Workshop.

| manuscript claim | Jan 2026 draft | **July 2026 draft** |
|---|---|---|
| "shifts the equilibrium mortgage rate by only about **one basis point**, economically negligible" (`\citep[\S4.9.1]`) | ✅ "equilibrium mortgage rates are on average only **1 bps** higher with the option than without it" (p30, inside §4.9.1) | ❌ **20 bps**: "introducing the option raises mortgage rates by only **20 bps** on average"; "the value of the repurchase-at-market option — **20 bps per annum** on average in our baseline calibration"; robustness **18–23 bps**; two-factor **16 bps**; a tax variant at **18 bps** and another at **21 bps** |
| section pin `§4.9.1` | ✅ exists ("Introducing repurchase-at-market option in the U.S.") | ❌ **§4.9.1 does not exist.** July numbering runs 4.1–4.9 with only 4.7.1/4.7.2 as subsections |
| section pin `§4.6`, "structural parameters in tab. 3" | ✅ §4.6 = Calibration; Table 3 = "Model parameters" | §4.6 = Calibration still present (p28); table numbering not re-verified |

**The qualitative conclusion survives** — the July draft still frames the effect as "virtually
unchanged" and "only 20 bps" — but the paper prints a magnitude that is **20× too small against
the current version**, and calls it "economically negligible", which is a materially stronger
word at 1 bp than at 20 bps/year. §VI.C/§VI.D lean on this.

**Also newly quantified in July, and directly relevant:** the authors now report that a 100 bps
*decrease* in the yield gap changes annual moving rates by about **+14 bps** (their spec) or
**−19 bps** (under Fonseca–Liu controls) — i.e. near-zero and **sign-ambiguous** — and contrast
it with Fonseca & Liu (2024)'s U.S. estimate of **69–120 bps**. That is the flatness this paper
imports, now with numbers attached.

## FINDING 2 — the `§3.2.3` pin is on the wrong section. **VERDICT: FAIL (minor, both versions).**

The manuscript says `\citet[\S3.2.3]{berger2026} … estimate that under these rules household
mobility is close to flat in the coupon gap`. §3.2.3 is titled **"Aggregate prepayment,
refinancing, and moving rates"** in *both* drafts. It reports aggregate time-series behaviour
(FRM moving ≈3.1%/yr vs ARM ≈4.1%/yr) and says moving rates are "largely insensitive to
**mortgage rate fluctuations**" — then explicitly defers: *"These aggregate patterns provide
macro-level validation for the micro-level behavioral responses analyzed in the subsequent
sections."* The **estimate** of the moving hazard against the **coupon gap** is in §3.3
(Micro-data evidence) / §3.3.x, summarised in §3.4. The pin should move to §3.3, and the verb
"estimate" belongs with the micro section, not the aggregate one.

## FINDING 3 — `fonseca2026`'s 40% figure is real but is NOT a lock-in-attributed quantity. **VERDICT: PASS, with a scope warning.**

Verified verbatim from NBER WP 35237 (May 2026) abstract: *"Lock-in reduces both housing supply
… and demand …, evidenced by a **40% drop in U.S. existing home sales between 2022 and 2024**."*

- It is a **level drop in existing home sales, 2022 → 2024** — the *observed total* decline,
  offered as evidence that lock-in operates.
- It is **not** a decomposition, and **not** "lock-in caused 40%". The paper's own causal
  content is that lock-in *disproportionately* reduces moves down the housing ladder.
- Period is **2022–2024**, against this paper's window of **June 2022 – November 2025**.

**Consequence for C-76.** It can serve as the *denominator*/context for a foregone-payoff count
— realized decline in transactions — but it **cannot** be used as an attributed lock-in
comparator without importing an attribution the source does not make. Any C-76 spec must say
which of the two it is using, and the period mismatch must be stated.

## FINDING 4 — Freddie Mac SFLLD terms: the academic exception exists, but carries a proviso the committed extract does not obviously satisfy. **VERDICT: CONFIRMED (terms), JUDGMENT RESERVED (application).**

Verbatim, Freddie Mac *Additional Terms and Conditions for Single-Family Loan-Level Dataset*
(**Website Version effective November 2025; last updated 11-03-2025**):

> "You are prohibited from licensing, distributing, providing, re-posting, or otherwise making
> available, with or without charge, the Single-Family Loan-Level Dataset (in whole or in part)
> or any Derived Products to any third party, except as may be required by applicable law."

> "In connection with the Internal Purpose, you may: (i) derive data from the Single-Family
> Loan-Level Dataset; (ii) create products that incorporate data from the Single-Family
> Loan-Level Dataset or data derived therefrom (such derived data and products, **'Derived
> Products'**); and (iii) disseminate … **solely within your own company or organization** …"

> "You may also use the Single-Family Loan-Level Dataset for **academic or research purposes**,
> and **make your academic or research results and any related Derived Products available to the
> public**, provided that any such distribution is **solely for noncommercial purposes** and
> further provided that **the same does not include and cannot be used to derive or recreate any
> part of the Single-Family Loan-Level Dataset** or to identify any specific individual …"

**Repo facts established (not judgments):**

- `hazard/data/loan_sample.parquet` is **git-tracked** and **present in `origin/main`** on the
  **public** repository `github.com/eugeneoCMU/Lock-in-Effect`. So is
  `hazard/data/cohort_month_panel.parquet`.
- `loan_sample.parquet` is **75,000 rows at LOAN grain**, 14 columns: `loan_id`, `stratum_id`,
  `fico`, `property_state`, `orig_ltv`, `coupon`, `orig_upb`, `balance`, `loan_age`, `state`
  (Prepaid/Current), `vintage`, `fico_bucket`, `ltv_bucket`, `weight`.
- `cohort_month_panel.parquet` is aggregated to stratum-month cells, not loan grain.

**The tension, stated without deciding it.** The academic exception permits public release of
research results *and related Derived Products*, but only where the released material "does not
include and cannot be used to derive or recreate **any part of**" the dataset. A 75,000-row
table of per-loan SFLLD-sourced field values is, on a plain reading, difficult to describe as
not including any part of the dataset — the risk concentrates on `loan_sample.parquet`, not on
the aggregated `cohort_month_panel.parquet`. `loan_id` appears re-keyed (`F17Q20283803`), which
bears on the *identification* limb but not on the *include-or-recreate* limb.

**This is a licensing judgment and it is Eugene's.** Note also that the repo already treats the
**Fannie** equivalent as prohibited (`.gitignore`: "Fannie Mae SF Loan Performance data —
LICENSE prohibits redistribution (repo is public)"), so the two agency datasets are currently
handled asymmetrically. If remediation is needed it involves rewriting published history, which
no agent may attempt.

---

## Sources

- Berger, Jeong, Marx, Olesen & Tourre, Jan 27 2026 draft; and Jul 16 2026 draft (author site).
- Fonseca, Liu & Mabille, NBER WP 35237 (May 2026), full text.
- Freddie Mac, *Additional Terms and Conditions for Single-Family Loan-Level Dataset*,
  effective November 2025 (`capitalmarkets.freddiemac.com/crt/docs/pdfs/fre_terms_conditions_sflld.pdf`).
- Repo state read directly from `origin/main` and the committed parquet schemas.

## AI-assistance disclosure

Retrieval, PDF text extraction and claim matching were AI-assisted. Every verdict above rests on
verbatim text quoted from the primary source, not on model recall.

---

## ADDENDUM — findings 1 and 2 FIXED (2026-07-30, on Eugene's instruction "fix")

| site | before | after |
|---|---|---|
| `references.bib` | "draft January 2026" | **"draft July 2026"** |
| SS II lit review (`\citet[...]`) | `\S3.2.3`, "January 2026 SSRN working draft" | **`\S3.3.2`**, "July 2026 SSRN working draft" |
| SS VI.B framing | "a January 2026 SSRN working draft" | **"a July 2026 SSRN working draft"** |
| SS VI.B two-channel para | `\citep[\S4.9.1]` … "only about one basis point, economically negligible" | **`\citep[\S4.10.2]`** … "about **20 basis points** on average, **16--23** across their robustness variants, which they read as leaving equilibrium rates virtually unchanged" |
| SS VI.D (**a second stale site, caught by the post-edit residual sweep, not by the original fact-check**) | "an equilibrium-rate effect of about one basis point" | **"about 20 basis points"** |

Two things were added rather than merely corrected:

1. **The version sensitivity is now disclosed in the manuscript**, not hidden in this record:
   "That estimate is itself draft-sensitive --- the January 2026 version of the same paper
   reported about one basis point --- which is one more reason this channel is carried as an
   unrefereed import rather than as a settled magnitude." This is the only surviving mention of
   the 1 bps figure, and a test asserts it can only appear as version history.
2. **The imported flatness is now quantified from the newer draft's own microdata** instead of
   asserted: a 100 bp *decrease* in the yield gap moves the annual moving rate by about
   **+14 bps** under their specification and about **−19 bps** under Fonseca–Liu's control set
   — near zero and **not consistently signed** (`\S3.3.2`). This strengthens the claim the
   Danish leg rests on.

**Re-verified as still correct against the July draft, and therefore left alone:**
`\citep[\S4.6, structural parameters in tab.~3]` — SS4.6 is still Calibration, and the 3.2%
unconditional Danish FRM moving rate is still one of its stated calibration targets ("jointly
calibrated to match (i) the average annual moving rate among Danish FRM borrowers (3.2%)").
The 22% mortgage-interest deduction and 15% capital-gains rate are also still the July draft's
U.S. tax calibration, summarised in its Table 3.

**Regression cover:** `tests/test_berger_citation_currency.py`, 13 tests (532 → 545). It is a
test and not a liveness gate because an external working paper has no committed artifact to tie
a gate to. It pins the absence of both superseded section numbers, the presence of the current
ones, the 20 bps magnitude, the bib version, and that "one basis point" survives exactly once
and only inside the declared version-history clause.

**Verification:** ALL GATES PASS (111) | 545 tests | ALL RENDER CHECKS PASS | 152pp both
variants | variant differs at line 31 only.
