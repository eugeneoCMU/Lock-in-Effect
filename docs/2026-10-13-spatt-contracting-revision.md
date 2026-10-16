# Dunn–Spatt contracting revision

The user authorized implementation of the prior readiness work and the pasted
proposal. Work is isolated from the active source pipeline in the managed
spatt-contracting-revision worktree, based on commit 56986a0.

## Implemented

- Added a narrow contracting-theory paragraph after the introduction's mobility
  discussion, with a Dunn–Spatt citation.
- Added the fixed-contract interpretation and current agency-institution
  qualifications after the paired simulation description.
- Documented the separately implemented mixture specification as pending the
  corrected source run. No new estimate is inserted into the paper.
- Added an appendix specifying the future contracting/sale/refinancing extension
  and an uncalibrated Python prototype. Sale-to-termination incidence and cash
  accounting are explicitly separate; no lender optimum is estimated.
- Applied the calibration coverage-disclosure patch in this isolated checkout,
  including the unknown-history qualification. Tests cover key presence and
  exact serialization of a populated synthetic audit.
- Saved the comparison acceptance checklist as a tracked document.

Existing main-text blocks are byte-identical after removing the three targeted
insertions. Both abstracts are byte-identical to the base. Publication dates are
updated to October 13. Prior numerical findings and their conditional labels are
preserved. The live f586 run does not consume this revision until a later safe
integration; none of its frozen files is modified by this work.

## Source verification

Primary publisher abstract and metadata:
https://afajof.org/issue/volume-40-issue-1/
Dunn and Spatt, Journal of Finance40(1),293–308. Publisher DOI:
10.1111/j.1540-6261.1985.tb04950.x; JSTOR stable2328061 (user's DOI alias
10.2307/2328061). The abstract supports the face-minus-market-value financing
loss, asymmetric-information game and conditional lower penalty inducing more
prepayments. Full article text was not retrieved, so detailed equations in the
new appendix are labeled as a proposed extension rather than a verified
replication of the 1985 optimum.

Primary agency rules checked October13,2026:
- Fannie Mae B2-1.4-01, fixed-rate eligibility, dated December14,2022:
  https://guide-selling.fanniemae.com/sel/b2-1.4-01/fixed-rate-loans
- Fannie Mae D1-4.1-05, due-on-sale enforcement and exceptions, dated November8,2017:
  https://servicing-guide.fanniemae.com/svc/d1-4.1-05/enforcing-due-sale-or-due-transfer-provision
- Freddie Mac8406.1, effective September10,2025:
  https://guide.freddiemac.com/app/servicing/section/8406.1
These are institutional qualifications, not a historical loan-by-loan rule audit.

## Verification boundary

Targeted insertion preservation, citation/reference validation, compiler output,
render inspection and software regression are recorded under output/spatt-revision.
These checks do not validate the imported response, identify the gains/opportunity
process, estimate concession behavior or establish causal/full-SOMA transport.
The abstracts were not regenerated. No formal ARS integrity certification is
claimed; the LaTeX edits use bounded insertions and exact inverse preservation.
