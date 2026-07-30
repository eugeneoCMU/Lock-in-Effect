# SPEC — R32 / C-74: the Ginnie leg with the elasticity attenuated by the measured CRR differential

**Status: PRE-COMMITTED. Committed BEFORE the runner, and both before the run.**
Run tag: `ginnie_overlay_attenuated`. Runner: `tools/ginnie_overlay_attenuated_run.py`
(not yet written; this spec lands first and stands on its own). New artifact:
`hazard/data/ginnie_overlay_attenuated_results.json`.

---

## 1. The condition

C-74 (R2:M4(b), SY:Z6/R10, MAJOR, RUN). Today the overlay scores the **20.4% Ginnie face share by
the observed Ginnie speed in *both* Path B legs**, so that share's central-minus-null difference is
**exactly zero** and the marginal correction is pure conventional-share scaling. `.tex:283` states
it: "$0.797$ against $0.796$" in-sample, and "$0.797\times$" composed off-window. The condition:
the Ginnie share should generate a **weaker marginal, measured**, rather than **none, assumed**.
It bears on **20.4% of book face**.

**Note on line numbers.** The inventory cites `.tex:271` and T8 at `.tex:433`; the live sites are
the overlay paragraph at **`.tex:283`**, the `tab:assembly` row at **`.tex:374`**, the run-index
row at **`.tex:847`**, and the assumability sentence at **`.tex:52`**.

## 2. Two honesty constraints, before any construction

**(a) The direction relative to the *current* treatment is near-mechanical, and this run gets no
credit for it.** The Ginnie share contributes exactly zero marginal today. Therefore for **any**
positive attenuation factor $a > 0$ the corrected marginal must exceed the committed $0.797\times$,
by arithmetic. Reporting "the marginal rose above $0.797\times$" as a finding would be the same
error the paper already names about its own headline sign. **The landing text must state that this
rise is forced.**

The **genuinely open sign** is different, and it is the one the inventory means: whether the
derived $a$ lands **below or above 1** — whether the Ginnie share responds **less** than the
conventional share (attenuation, $a < 1$) or **more** (amplification, $a > 1$). Both are
pre-authorised in §5/§6, and if $a > 1$ the result is labelled **amplification**, not quietly
re-described as attenuation.

**(b) A level differential does not identify a slope differential.** The measured object is a
**level** difference in voluntary speed — Ginnie CRR runs above conventional CRR at the *same*
window rate path. The elasticity is a **slope**. Nothing in the data maps one to the other; a
mapping must be assumed. This spec therefore **brackets over the mapping** rather than picking one
and calling it measured, in the same convention as C-76's $\sigma$ range and the buyback's $D$ grid.

## 3. What is already known — DECLARED, NOT PREDICTED

Computed at scoping from committed artifacts, *before this spec existed*:

| object | source | value |
|---|---|---|
| window-mean Ginnie CRR | `gmar_dec25_cpr_series.json:crr.ginnie`, 42 months 2022-06…2025-11 | **7.294976** |
| window-mean Freddie CRR | `…crr.freddie` | **5.940905** |
| window-mean Fannie CRR | `…crr.fannie` | 5.942643 |
| **differential (Ginnie − Freddie)** | derived | **+1.354071 pp** — the manuscript's "$1.35$ points" at `.tex:52` |
| differential (Ginnie − GSE-mean) | derived | +1.353202 pp |
| **speed ratio $r$ (Ginnie / Freddie)** | derived | **1.227923355** |
| un-overlaid marginal $M_{\text{full}}$ | `ginnie_cpr_overlay_results.json:committed_anchors` | (818.5300844066606 − 748.1850239867648) / 764.7482532227002 = **9.198459770710 pp** |
| committed overlay `crr_only` | same artifact | `marginal_b` 56.080892083313415, **`marginal_pp` 7.333248797494442**, ratio to $M_{\text{full}}$ **0.797225729** |
| committed overlay `primary` / `gse_placebo` | same | 7.335061460712228 / 7.331601870734776 |
| off-window pair | `ginnie_overlay_offwindow_results.json` | conventional **5.57155818290974**, overlay **4.443419164229439**, ratio **0.797518220** |
| conventional face share | `.tex:283` | 0.796 |

**Nothing in scoping computed a corrected marginal at any $a > 0$.**

## 4. Construction

**This is engine-free, deliberately.** The overlay is already a **re-scoring of committed legs by
an observed series**, not a re-simulation, and this run stays in that regime — the C-80/C-81
re-tabulation posture. Re-simulating the Ginnie share under a modified $\beta_1$ would be an engine
run against a **single-tenant** engine, for a share whose per-unit-face model response is already
recoverable from the committed legs. That fuller version is named and **declared out of scope** in
§7.

Let $W_G = 0.204$, $W_C = 0.796$, and let $\Delta_C$ be the conventional share's per-unit-face
central-minus-null wedge implied by the committed legs. Then

$$\text{marginal}(a) \;=\; \text{marginal}(0) \;+\; a \cdot W_G \cdot \Delta_C$$

with $\Delta_C$ **pinned by requiring $\text{marginal}(1) = M_{\text{full}}$** — i.e. at $a = 1$
the Ginnie share responds exactly like the conventional share and the overlay's marginal must
return to the un-overlaid one. That is not a free parameter: it is the identity that makes $a$ mean
what its name says, and it is gated (P3).

**The mapping bracket over $a$**, evaluated at every point, none privileged as "the" answer:

| label | $a$ | reading |
|---|---|---|
| **M0** | 0 | the committed treatment — Ginnie share gap-inert. **The parity anchor.** |
| **M2** | $1/r = 0.814383077$ | **primary.** Absolute-response preservation: if the absolute pp response to a 100 bp gap is a property of the rate environment rather than of the book, a book running $r$ times faster carries a proportionally *smaller* semi-elasticity. This is the reading under which "attenuated by the measured CRR differential" is literally true. |
| **M1** | 1 | the no-differential null: Ginnie responds exactly like conventional. |
| **M3** | $r = 1.227923355$ | proportional-hazard preservation: same $\beta_1$, higher baseline, hence $r$ times the *absolute* response — **amplification**. |

Both calibrations are scored: the **in-sample** point (against $M_{\text{full}} = 9.198$) and the
**off-window headline** composition (against 5.5716, the $+5.6$ the paper headlines), so the
result lands in the same units as `.tex:283`'s $+4.4$.

**Comparator choice, stated because it is a choice.** $r$ uses **Freddie**, because Path B is built
on the Freddie panel and `.tex:52` quotes that differential. The **GSE-mean** variant is reported
alongside; the two differ by 0.000869 pp in the differential and 0.00018 in $r$, and P4 gates that
the two mappings cannot move the verdict.

## 5. Pre-commitments

**STOP-class:**

- **E1 — the $a = 0$ cell reproduces the committed overlay bit-identically.** `marginal_pp`
  7.333248797494442 and `marginal_b` 56.080892083313415 for `crr_only`, and the committed anchors
  818.5300844066606 / 748.1850239867648 / 764.7482532227002 — **all read live from
  `ginnie_cpr_overlay_results.json`**, not from literals in the runner.
- **E2 — monotonicity.** $\text{marginal}(a)$ is strictly increasing in $a$ across the grid. A
  violation means the wiring is backwards.

**GENUINE predictions** (may fail; a miss lands with the miss named):

- **E3 — the corrected marginal recovers most of the un-overlaid one.** At the primary mapping M2
  ($a = 0.8144$) the in-sample corrected marginal lands in **[8.5, 9.2] pp**. Rationale, and it is
  the paper's own: `.tex:52` argues an assumed loan does not prepay, so materially high assumption
  take-up would show up as **slower** Ginnie voluntary speeds — and the measured differential runs
  the other way, $+1.35$ pp **faster**. That says take-up is low, the carve-out is small, and the
  Ginnie share's gap response should sit far closer to the conventional share's than to zero.
  **I do not know the realized value and this may fail.**
- **E4 — the open sign, pre-authorised both ways.** Whether the *defensible* mapping puts $a$ below
  or above 1 is **not** predicted. M2 gives 0.814 and M3 gives 1.228 from the *same* measurement;
  which is the right reading is a modelling judgement this data cannot settle, which is exactly why
  the run reports the bracket. **Either conclusion lands, and neither is scored as a miss.**
- **E5 — declared as forced, not claimed as a finding.** The corrected marginal exceeds the
  committed $0.797\times$ at every $a > 0$. This is arithmetic (§2a). It is recorded so that no
  landing text can present it as evidence.

## 6. Gates

- **P0** sha pins on `hazard/data/gmar_dec25_cpr_series.json`,
  `hazard/data/ginnie_cpr_overlay_results.json`, `hazard/data/ginnie_overlay_offwindow_results.json`.
- **P1 (the parity anchor)** — E1 above, live.
- **P2 (the series re-derivation)** — the window-mean CRRs are recomputed from
  `gmar_dec25_cpr_series.json` over the **42** months 2022-06…2025-11 and asserted against
  7.294976 / 5.940905 / 5.942643 to $10^{-6}$, with the month count asserted $= 42$ and the window
  endpoints asserted by label. The differential and $r$ are **derived, never hard-coded**.
- **P3 (the identity that defines $a$)** — $\lvert\text{marginal}(1) - M_{\text{full}}\rvert \le
  0.05$ pp at both calibrations, with $M_{\text{full}}$ computed live from the committed anchors.
  The tolerance is **pre-committed and justified**, not tuned: the committed overlay's own
  ratio-vs-share discrepancy is 0.797226 against 0.796, i.e. about 0.011 pp, so 0.05 pp is a loose
  multiple of the known level-interaction residual. A miss means the additive decomposition in §4
  does not hold and the construction is wrong.
- **P4 (comparator invariance)** — the GSE-mean variant moves the M2 marginal by **less than
  0.05 pp**; if it does not, the comparator choice is material and must be reported as a second
  bracket axis rather than a footnote.
- **P5 (series integrity)** — `series_validation.crr_endpoint_residual_pp` is re-read and the
  extraction residuals (fannie 0.0006, freddie −0.0115, ginnie 0.011) recorded in the artifact, so
  the reader sees the measurement error that sits under a $+1.354$ pp differential. **This is
  material: the extraction residual is roughly 1% of the differential it feeds**, and the artifact
  must say so rather than presenting $r$ as exact.
- **W1** — writes **only** `hazard/data/ginnie_overlay_attenuated_results.json`; refuses to
  overwrite a differing file; **never rewrites either committed Ginnie artifact**; edits no `.tex`.
- **No engine.** The runner touches nothing under `hazard/data/floor_sweep/` and imports no
  simulation entry point; asserted structurally, not merely intended.

## 7. Landing rules, per branch

- **Branch A — gates pass, E3 holds.** Land the bracket beside `.tex:283`'s $0.797\times$ sentence:
  the Ginnie share is no longer gap-inert, the corrected marginal is reported at M0/M2/M1/M3 at
  both calibrations, and the **forced** part of the rise (§2a) is stated as forced. The
  `tab:assembly` row at `.tex:374` gains the corrected member beside its $+4.4$; a `tab:runindex`
  row lands at `.tex:847`. New gate + test battery pinning the bracket endpoints and the P3
  identity. `.tex:52`'s assumability sentence gains the link from "$1.35$ points faster" to "so the
  carve-out is small and the share is not gap-inert".
- **Branch B — gates pass, E3 misses** (the corrected marginal stays well below 8.5 pp, i.e. the
  Ginnie share's response really is weak). **Land anyway**, with the pre-committed band quoted
  beside the realized value and the miss named. This is the outcome R2 anticipated — "a weaker
  marginal, measured" — and it **strengthens** the paper's existing conservative framing rather
  than damaging it.
- **Branch C — gates pass and the defensible mapping is M3 ($a > 1$, amplification).** Land it
  **as amplification**, explicitly. The consequence is uncomfortable and is pre-authorised: the
  overlay's $0.797\times$ would then be understating the marginal on 20.4% of face, and the
  $+4.4$-point overlay member at `.tex:374` becomes a **lower** bound rather than a re-scoped
  estimand. Say so.
- **Branch D — P0–P5 or E1/E2 fails.** Land nothing in the manuscript; commit the runner output
  and a failure record under `specs/`.

## 8. Scope limits this spec commits to stating

1. **The mapping is assumed, not identified.** §2b is not a caveat to be dropped in drafting: the
   bracket is the result, and no single cell may be quoted as "the measured Ginnie marginal".
2. **The re-scoring is engine-free by design.** A full re-simulation of the Ginnie share at
   $\beta_1 \cdot a$ is the stronger version of this test and is **out of scope** here — it needs
   the single-tenant engine and a Ginnie-specific loan panel this design does not have. The
   artifact must record that the per-unit-face conventional wedge is being *transplanted* onto the
   Ginnie share, which is the attenuation hypothesis stated cleanly, not a Ginnie-specific
   estimate.
3. **The published series is full-universe Ginnie collateral**, while SOMA's Ginnie holdings are
   seasoned and low-coupon. The committed artifact's own note says the overlay "if anything
   OVERSTATES the correction"; that direction carries into $r$ and stays stated.
4. **Structural Ginnie inclusion remains formally declined** and this run does not reopen it. The
   overlay treats the buyout-inclusive Ginnie speed as data, which is what runoff accounting
   requires of a passthrough holder.
5. **Realized assumption take-up is measured nowhere in this design.** The $20.4\%$ share and the
   observed-speed argument are both **ceilings**, as `.tex:52` already says. This run prices a
   response on the share; it does not size the carve-out.
