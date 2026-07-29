# Danish redemption external validation — frozen artifact (WP-F2)

Retrieved 2026-07-28 (Europe: 2026-07-29 API date) from Statistics Denmark's public API (api.statbank.dk) serving
Danmarks Nationalbank table DNVPDKR2 ("Danish mortgage bonds", monthly, m DKK, updated 2026-07-28).
Spec committed BEFORE fetch: SPEC_danish_redemption_validation_2026-07-28.md (54b8992 + pre-data addendum 7959969).

Files: query_dnvpdkr2.json (exact POST body) · dnvpdkr2_data.csv (raw CSV response) · dnvpdkr2_tableinfo.json
(metadata; data-type labels verbatim) · score_against_spec.py + results.json (committed FKE construction) ·
score_refinement_fk_le2.py + results_refinement.json (labeled refinement, see below).

SHA-256:
c9584d1496e6833b5839d8eb8b8e88708ee9d8c0cab04dcf0882c6220d70d415  dnvpdkr2_data.csv
f4b3bbb498498082e0e6533934694bc0818e88ec02fb149548baaef5aad36e9f  dnvpdkr2_tableinfo.json
e4a8e8b9efd4b44891035daa1b0d93dc7648aebabe43ee847d259bc26f1536f6  query_dnvpdkr2.json
badc7bcd2fc11584c34362b10cefce43d58b19b022e26eb2215550e399152e9a  results.json
6daf55357927e225249319949ad2f9a9909c0ef3364c91db691699c2b92324e7  results_refinement.json

## Result (scored against the pre-committed rules)

- Committed FKE construction: R = 26.68%/yr (2022M07–2023M12 mean, coupons <=2%) — but its own committed
  cross-check FAILED (max |dStock − NetTxn| = 644bn DKK: FKU->FKE closed-for-issue reclassification migrates
  stock between subcategories in exactly this window). Reported, not used for the verdict.
- LABELED REFINEMENT (verification-driven, same semantic target): FK x coupon<=2% — the coupon attribute cannot
  migrate and <=2%-coupon callable issuance was ~0 in-window (residual issuance biases the rate DOWN, conservative).
  Cross-check passes exactly (max |dStock − NetTxn| = 2m DKK on a 1,202bn DKK opening stock).
  **R = 26.42%/yr; extraordinary lower bound after the pre-committed 4pp scheduled allowance = 22.4%/yr.**
  Stock 2022M06 1,202.3bn -> 2023M12 747.2bn DKK (−38% in 18 months); peak months 2022M07 49.4%, 2022M11 41.0%.
- **VERDICT: RULE-A′ (strongly falsified) — more than double the 12% threshold.** Realized deep-discount Danish
  prepayment ran ~5–6x the 4–5% baseline while the production Danish leg pins the discount-exercise contribution at ~0.
- Context (M3, no disposition attaches): FK all-callable net-of-issuance rate 8.7%/yr vs the Danish leg's simulated
  5.61% mean CPR. 30y-only variant of the headline read: 28.2%/yr (committed construction).
- Post-break months (>=2024M10) carry no read rule per spec; reported in results JSONs only.

Ex-ante caveats travel (spec §Caveats): gross bond-level measure (conversions bundle in — on the hazard question
conversion IS the delivery-option exercise); stock includes non-household collateral; environment-matched, not
book-matched; this validates against the ~0 PIN's behavioral plausibility, it does not identify the U.S.-transplant
contribution.

## Pre-committed dispositions now active (to be applied under WP-F, manuscript untouched this session)

Per RULE-A′: (i) the Danish headline row carries the WP-F1 sweep band, not the 0% point; (ii) the sweep range is
anchored by a realized-implied contribution (R − 4pp, stated as an approximation with its confounds); (iii) §V.C
states the ~0 pin is contradicted by realized Danish redemption data (this source, this window).
