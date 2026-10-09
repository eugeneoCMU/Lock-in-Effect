# External data access and SOMA pool pilot — October 9, 2026

## What was actually checked

The official New York Fed holdings API returned the June 29, 2022 agency file.
The local frozen copy contains 29,692 MBS rows and $2,700,563,694,147.7837 of
current face. SHA256: `7e17a803e799e80ce13c5e107fbe82b56edaf8d52f65c8a1093003f53e756e34`.
The raw response and deterministic selection manifest are in
`output/research-limits/2026-10-09/pool/`.

Selection was fixed before retrieving collateral attributes: the five largest
30-year UMBS positions by current face, breaking ties by ascending CUSIP.
These positions represent 5.2562492258% of all MBS current face in that snapshot.
This is a deliberately concentrated feasibility sample, not a probability sample.

| CUSIP | June 29, 2022 face, USD | Security coupon | Maturity in description |
|---|---:|---:|---|
| 3132DWAW3 | 31,258,169,932.77 | 2% | January 2051 |
| 31418DV74 | 29,142,178,234.45 | 2% | January 2051 |
| 3132DWCB7 | 28,702,352,240.66 | 2% | September 2051 |
| 3132DWBP7 | 26,685,829,122.50 | 2% | May 2051 |
| 3132DWCH4 | 26,159,828,735.64 | 2% | October 2051 |

The first PoolTalk search redirected to a Terms & Conditions page, dated
September 12, 2026. No agreement was accepted. No collateral attribute was
retrieved, so **no match-rate, borrower-rate bridge or underlying agency mix is
estimated by this pilot**. An empty aggregation flag in the Fed response is not
evidence that a security has no underlying resecuritization.

The next authorized lookup must verify each identifier in the appropriate issuing
agency's disclosure system, record the disclosure date and whether it is a pool
or resecuritization, and retrieve historical collateral WAC and remaining balance
at the corresponding opening date. A current WAC cannot stand in for June 2022.
If a security is a resecuritization, preserve the underlying-pool mapping and
ownership weights; do not count collateral twice. Keep unmatched face visible.
Only then compare borrower WAC with the security coupon and the assumed 80-bp
bridge. The selected positions alone do not justify a book-wide bridge.

## Earlier Freddie vintages and later outcomes

The official dataset page reports originations from 1999 and performance through
March 2026, with academic use free subject to terms. The existing Chrome session
was redirected from the download page to an empty Clarity sign-in form. No
credentials were requested or entered, no account was created, and no download
occurred. Earlier Freddie quarters are not in the local/known Drive locations
inspected during the prior feasibility check.

After access is available, the first useful extension is one 2015 or 2016 quarter
at a time, retaining the 2018 risk set and all terminations needed to calculate
voluntary payoff rates. Selecting only loans still outstanding in May 2022 would
condition on future survival and is unsuitable for this baseline. Preserve the
new July 2026 file-layout version separately from older source snapshots.

Do not read post-September-2025 Freddie loan outcomes until the future evaluation
protocol, candidate choice and source-exposure audit are frozen. Later aggregate
SOMA outcomes and some Fannie outcomes have already been examined: this cannot be
described as a wholly unseen economic period.

## Moving-share access

Cotality advertises sale, refinance and other payoff classifications, but this
does not establish that a usable historical academic extract is available. Public
CMU pages confirm research-data consultation services; they do not establish a
CMU Cotality or LLMA subscription. The earlier under-$25 budget remains binding.
No purchase, outreach, form submission, or personal-data transmission occurred.

The smallest useful access request is a de-identified aggregate extract with:

- A fixed eligible loan population, agency/product coverage and reporting period.
- Month, coupon/rate-gap bucket, loan-age bucket and available region strata.
- Sale-related voluntary terminations and all comparable voluntary terminations,
  both counts and pre-payoff balances, with maturity distinguished if possible.
- Outstanding beginning-of-month loans and balances in exactly the same population.
- Unknown/unmatched outcomes, coverage and linkage rates, classification validation,
  and rules for cash sales, repeat borrowers, refinancing and partial repayments.
- Allowed academic/publication uses and explicit zero-cost or under-$25 access.

Counts alone estimate a count share; a dollar simulation requires a defensible
balance-weighted translation. A national transaction share is not a replacement
for the study population's payoff share. Measuring this input would not separately
identify financing effects from housing inventory and affordability.

## Primary sources checked

- [NY Fed June 29, 2022 holdings API](https://markets.newyorkfed.org/api/soma/agency/get/all/asof/2022-06-29.json)
- [NY Fed CUSIP aggregation description](https://www.newyorkfed.org/markets/agency_mbs_cusip_aggregation_faqs_201116)
- [Fannie pool information and fields](https://capitalmarkets.fanniemae.com/mortgage-backed-securities/mbs-contact-information)
- [PoolTalk](https://fanniemae.mbs-securities.com/fannie)
- [Fannie dataset application terms](https://www.fanniemae.com/media/37961/display)
- [Freddie dataset coverage and access](https://www.freddiemac.com/research/datasets/sf-loanlevel-dataset)
- [Freddie Clarity download entry](https://claritydownload.fmapps.freddiemac.com/CRT/#/sflld)
- [Cotality Payoff Analysis](https://www.cotality.com/products/payoff-analysis)
- [CMU Data and Code Support](https://www.library.cmu.edu/services/data-code-support)
