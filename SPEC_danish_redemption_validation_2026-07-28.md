# SPEC — Danish redemption external validation (WP-F2), committed BEFORE any data fetch — 2026-07-28

**Rule.** This spec is committed before the first API call. The read rules below are fixed now; the data artifact lands in a later commit and is scored against these rules as written. Any deviation is labeled post-hoc in the write-up. Eugene authorized the external pull ("can you fetch?", this session); manuscript edits remain UNEXECUTED — this spec pre-commits *dispositions*, to be applied under WP-F's landing when Eugene takes it.

## Question

Is the production Danish leg's ≈0 refinance-in-place (discount-buyback) contribution — pinned from Berger et al.'s ~1bp general-equilibrium rate effect (fig:gapsweep caption) — consistent with realized Danish prepayment behavior on deep-discount callable bonds in the same rate environment (R3-W1 / REVIEW2 finding #7)?

## Data

- **Source**: Danmarks Nationalbank tables served via Statistics Denmark's public API (`api.statbank.dk`). Candidate table `DNVPDKR2` (Danish mortgage bonds by type, maturity, coupon, currency, issuer, investor sector, covered-bond status, data type). If its data-type dimension does not carry extraordinary redemptions, the semantically matching DN table found via the API's table search is substituted — the semantic target, not the table id, is what is committed: **extraordinary redemptions (ekstraordinære indfrielser / prepayments) and nominal stock of DKK fixed-rate callable mortgage bonds**.
- **Window**: 2022M06–2025M11 as available. **Load-bearing subwindow: 2022M07–2023M12** — the deep-discount episode, entirely before the October-2024 reporting-method change flagged in the table's own footnote. Post-2024M09 months are reported but carry no read rule (break handling committed ex ante).
- **Universe**: DKK-denominated fixed-rate callable mortgage bonds (the table's type 1.1). All issuers, all investor sectors, all maturities (30y reported separately if the pull is cheap).
- **Artifacts**: raw API responses (tableinfo + data) frozen under `hazard/data/danish_external_validation/` with SHA-256 recorded in the write-up; retrieval date, exact query URLs, and the data-type value labels recorded verbatim.

## Metrics (computed exactly as stated)

- **M1**: annualized extraordinary-redemption rate on the all-callable stock: for month t, `1 − (1 − X_t / S_{t−1})^12`, where X = extraordinary redemptions (nominal, m DKK), S = nominal stock, same filter; reported per month and as the load-bearing-window mean. If the table is quarterly, the quarterly analogue with ^4.
- **M2**: same, restricted to **coupon ≤ 2%** buckets (the unambiguous deep-discount cohort at 2022–23 Danish long yields), if the coupon dimension crosses the data-type dimension. If it does not cross, M2 is reported as unavailable and M1 carries the read with that stated limitation.
- **M3 (context only)**: the all-callable M1 beside the Danish leg's simulated 5.61% mean CPR. **Pre-committed as context, not a validation target** — the leg is the Danish *rule on the U.S. book*, not the Danish book. No manuscript disposition attaches to M3, whatever it shows.

## Pre-committed read rules

Let **R** = M2's load-bearing-window mean (M1's if M2 unavailable).

- **RULE-A (pin falsified)** — if **R > 4%** (the involuntary/baseline-turnover level the paper's own U.S. legs impose, and the level the transplant's flat moving hazard delivers absent any buyback channel): realized deep-discount Danish prepayment exceeds the no-buyback baseline, the ≈0 refinance-in-place pin is inconsistent with realized behavior, and **WP-F1's band presentation becomes mandatory** — the manuscript's Danish headline row carries the 0–3% sweep band, not the 0% point, and the price→quantity inference is replaced, not merely stated.
- **RULE-A′ (strongly falsified)** — if **R > 8%** (double the baseline): additionally, the fine-grid sweep's reported range must be anchored by a realized-implied contribution (R minus the 4% baseline, stated as an approximation with its confounds), and the §V.C text says the pin is contradicted by realized Danish data.
- **RULE-B (pin supported)** — if **R ≤ 4%**: the ≈0 pin gains its first external support; the manuscript gains one sentence citing the realized rate and source; the sweep still lands per WP-F1 but the 0-point remains the headline anchor.
- **Tie/boundary**: R within ±0.25pp of 4% → reported as boundary, RULE-A's disposition applies in weakened form (band reported alongside the 0-point rather than replacing it). Committed now to prevent post-hoc rounding arguments.

## Caveats committed ex ante (travel with any use of the result)

1. Danish extraordinary redemptions bundle outright buybacks, conversions (refinance into new bonds — balance roughly preserved), and moves; it is a **gross** prepayment measure on the bond, which is the same basis as CPR on the U.S. side — gross is the correct comparison basis for a hazard, and the bundling means R overstates the *net balance-reduction* channel. RULE-A therefore tests the pin's hazard claim, not a balance-reduction claim.
2. The stock includes corporate/rental collateral; owner-occupied cannot be fully isolated at this granularity. Noted, not repaired.
3. The comparison is environment-matched (same rate episode), not book-matched (Danish borrowers, Danish advisory institutions). It disciplines the *behavioral plausibility* of ≈0 discount exercise, which is exactly the inference R3-W1 attacks; it does not identify the U.S.-transplant contribution.
4. October-2024 method change: no read rule uses post-break months.

## What this spec does not authorize

No manuscript, gate, test, or letter edit. The dispositions above are the pre-committed landing rules for WP-F when Eugene executes it.

---

## Substitution addendum (committed BEFORE any data values were fetched, after metadata-only inspection)

**Finding from metadata (tableinfo + full catalog sweep, no data values seen):** no table on the API carries extraordinary redemptions directly — DNVPDKR2's data-type dimension has only stocks, net transactions, and value adjustments; DNRIURQ carries scheduled instalments only; a title sweep of all 2,317 tables returns zero redemption-flow tables. The spec's substitution clause therefore activates with a **derived measure**, defined now:

- **Universe refinement**: DNVPDKR2, `TYPREAL=FKE` ("no longer open for issue — fixed rate callable", defined since 2015), `VALUTA=DKK`, all sectors (investor dimension eliminated), monthly. For a closed-for-issue series, gross issuance ≡ 0, so **−(net transactions, nominal) = total redemptions exactly** (scheduled + extraordinary; nominal is valuation-free in DKK). Cross-check: −ΔStock(N1) ≈ −N2 month by month.
- **Derived metric M2′** (replaces M2): annualized **total-redemption rate** on the coupon ≤2% FKE stock: `1 − (1 + N2_t/S_{t−1})^12` (N2 negative when redeeming). M1′ analogously on all-coupon FKE, and on FK all-callable as context (labeled net-of-issuance where the series is open).
- **Scheduled allowance, fixed now**: extraordinary redemptions ≥ total-redemption rate − **4pp/yr**. (Danish 30y annuity amortization runs ~1.5–2.5%/yr early-life; the interest-only share lowers it; 4pp is deliberately generous, which makes the test conservative against firing RULE-A.)
- **Read-rule mapping onto the derived space** (thresholds unchanged in extraordinary space): RULE-A fires if the ≤2%-coupon FKE total-redemption rate averaged over 2022M07–2023M12 exceeds **8%/yr** (⇒ extraordinary > 4% under the allowance); RULE-A′ if it exceeds **12%/yr**; RULE-B if ≤ 8%/yr; boundary band ±0.25pp maps to 8%±0.25pp.
- **Deviation label**: this is a derived lower-bound construction, not the direct series; every use of the result carries that label. The direct series exists in Finance Denmark's published XLSX statistics and can replace this construction later; the derived read is committed first so the threshold precedes any sighting of either source's values.

---

## Execution log (post-data, 2026-07-28)

Fetched and scored same session; artifacts + SHA-256 in `hazard/data/danish_external_validation/` (commit 9cd4e91). The committed FKE construction returned R=26.68% but FAILED its own cross-check (644bn DKK reclassification leakage, FKU→FKE closed-for-issue migration in-window) — reported, not used. Labeled refinement on FK×coupon≤2% (attribute cannot migrate; ≤2% issuance ≈0 in-window, conservative direction): cross-check passes exactly (2m DKK on 1,202bn), **R = 26.42%/yr**, extraordinary lower bound 22.4%/yr after the 4pp allowance. **VERDICT: RULE-A′ — strongly falsified, >2× the 12% threshold.** Deep-discount stock fell 1,202→747bn DKK over the load-bearing window. Dispositions (i)–(iii) of RULE-A′ are now active for WP-F; no manuscript edit made.
