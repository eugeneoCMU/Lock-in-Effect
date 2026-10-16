# Selected HARP linkage pilot

The pilot audit is implemented in `hazard/harp_linkage_audit.py`. It is a local evidence check before any exercise-rate estimation. The user-downloaded `/Users/eugene/Downloads/HARP_Files.zip` is now hashed and its full mapping structure audited. Original-loan pilot ingestion still requires the fixed2008Q1 primary file.

The signed-in Data Dynamics page was verified at `https://datadynamics.fanniemae.com/data-dynamics/#/downloadLoanData/Single-Family`. Its HARP Dataset button is labeled **HARP Acquisitions, Performance and Mapping Files**. It provides a bundle rather than a visible separate mapping option. Browser download capture stalled twice and produced no verified file path. The user subsequently downloaded HARP_Files.zip manually. It contains HARPLPPub.csv (26,087,153,779 uncompressed bytes) and Loan_Mapping.txt (26,921,752 bytes). The mapping has1,035,452 unique comma-delimited headerless links, with12-character original/successor IDs in columns0/1. All500 streamed successor anchors matched only column1. Full original-loan pilot ingestion remains pending the2008Q1 primary archive.

Access history: local Fannie API credentials were unavailable. The user completed login/password recovery themselves, then confirmed the dashboard was visible. The earlier automatic-review restriction protecting a populated recovery form was resolved by that state change. Current download failure is a browser transfer/capture problem, not evidence about the data or model.

Source documentation: Fannie Mae's dataset page and FAQ describe a selected historical HARP population with original/successor mapping. Original-loan acquisition dates run January2000–September2015, and mapped HARP refis April2009–September2016. This does not establish representativeness for the corrected Freddie2017–2021 portfolio. See https://capitalmarkets.fanniemae.com/credit-risk-transfer/fannie-mae-single-family-loan-performance-data and https://capitalmarkets.fanniemae.com/media/8921/display.

Once the archive exists locally:

1. Record its byte size, hash, release date and member list before extraction. Identify the mapping member and its actual delimiter, header, field width and original/successor orientation. The parser requires these explicitly; it does not guess them.
2. Inspect original acquisition-quarter coverage, then choose one primary quarter and a pilot sample using a documented rule fixed before observing future refinance outcomes. Mapping positives alone cannot define the starting-loan population.
3. Normalize one summary per primary loan and one static record per relevant successor. Record original source removal code/effective month and adjacent pre-event balance/remaining term. Keep missing or masked balances explicit.
4. Run the audit in a new local directory. It detects duplicate/colliding mapping roles, cross-input orientation contradictions, duplicate loans, invalid dates, missing successors and conflicting event timing. A mapped original payoff is retained as a selected HARP positive. An unmapped code01 remains an unknown payoff/maturity and sale/refinance cause.
5. Compare successor balance and term with the documented pre-event original record using declared tolerances. Differences are descriptive. They are not measured transaction costs; matching values alone do not establish purpose, qualification or full consistency with the borrower objective.
6. Build a complete monthly outstanding-loan risk set and eligibility/coverage audit separately before considering estimation. This pilot never sets `ready_for_general_refinancing_fit` to true.

`select_opening_stock(rows)` implements the frozen March2009 stock/hash selector without consulting future payoffs or mapping membership; it keeps delinquency states and records missing/zero-balance exclusions. `read_mapping(stream, original_column=..., successor_column=..., field_count=..., header=...)` preserves 12-character provider IDs and leading zeros. `audit_linked_refinances(...)` returns local loan diagnostics and aggregate counts. `run_local_pilot(input_path, output_path)` accepts a compact normalized JSON object containing `primary`, `mapping`, `successors`, `selection_definition`, `balance_tolerance`, `term_tolerance_months`, `evidence_class`, and three source-provenance descriptions. CLI: `python3 -m hazard.harp_linkage_audit --input-json <normalized pilot> --output <fresh directory>`.

Outputs include a local loan audit, aggregate summary and input/output hashes. Existing output directories are rejected. The source file must remain unchanged during the run. The loan-level output and provider records remain local; any shareable package should include only code, tests, documentation and appropriate verification evidence.

This implements the import and linkage checks. It does not complete raw-source ingestion, establish HARP eligibility, label all refinancing/sale/maturity exits, estimate alpha, infer dollar closing costs, reproduce lender pricing or change the accepted runoff estimates.


## Completed source intake

The complete HARP history scan checked92,327,378 monthly records for1,035,452 successor loans. Both ZIP members passed CRC and independent SHA256 binding; every mapped successor has history and every observed successor has a mapping. The earlier source-hash references were independently verified before acceptance, without discarding historical receipts.

There are45,979 first-disclosed successor terms outside180/240/360months. Seventeen loans have changing repeated original attributes over719rows; they remain flagged in the local index. Original successor-note dates beginMarch2009 while first reporting beginsApril2009. The original-loan effective payoff date will determine the linked event month; the successor date is not silently substituted for it.

The implemented pilot and pre-outcome selector have25passing tests; the related targeted suite has118passes, and the full regression suite1761passes with1skip and29warnings. Original2008Q1 histories remain pending; no observed original-loan pilot, eligibility inference or exercise-rate estimate is claimed.
