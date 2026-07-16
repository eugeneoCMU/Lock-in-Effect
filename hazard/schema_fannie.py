"""
Fannie Mae Single-Family Loan Performance (SF LPH) column layout + constants.

PROVENANCE
----------
Field positions, names, value enumerations, types, and every semantic claim in
this module are transcribed from Fannie Mae's own published glossary:

  "Single-Family Loan Performance Dataset and Credit Risk Transfer -
   Glossary and File Layout", (c) 2023 Fannie Mae, 6/26/2023, 9 pp, 108 fields.
  https://capitalmarkets.fanniemae.com/sites/capmrkt/files/2023-06/crt-file-layout-and-glossary.pdf

Local copies used while writing this module (do not ship):
  scratchpad/fannie_crt_layout_glossary.pdf   (source PDF)
  scratchpad/fannie_layout_raw.txt            (verbatim text dump)
  scratchpad/fannie_fields.json               (position -> name map)

STRUCTURAL NOTE (differs from Freddie)
--------------------------------------
Freddie ships TWO pipe-delimited headerless files per quarter (32-col orig +
32-col perf) joined on loan_sequence_number. Fannie ships ONE record layout,
108 fields, in which the static origination attributes are REPEATED on every
monthly reporting row (field 3 = Monthly Reporting Period). There is no
separate origination file. hazard/prepare_fannie.py adapts this single layout
into synthesized orig_/perf_ pairs so hazard/ingest.py is reused UNCHANGED.

The glossary column "Single-Family (SF) Loan Performance" marks each field as
applicable (checkmark) or not (NA) to the SF LPH dataset. 38 of the 108 fields
are CAS/CIRT-only (NA for SF LPH) - notably 48 and 50 (Scheduled / Unscheduled
Principal Current) and 69-72 (credit scores At Issuance / Current). The names
below are the full 108-position glossary layout regardless of SF-LPH
applicability; whether a real SF LPH file physically emits all 108 positions
or only the ~70 SF-applicable ones is UNRESOLVED (see prepare_fannie.py).

This module is import-safe: no I/O, no network, no credentials.

Snake_case names REUSE the Freddie names in hazard/schema.py wherever the
concept is identical, so the synthesized orig_/perf_ files need no downstream
change. Where a Fannie field has no Freddie counterpart, a faithful new
snake_case name is used.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 108-field SF LPH record layout, in glossary Field-Position order (1-indexed
# in the glossary; this list is 0-indexed). Names matching hazard/schema.py are
# marked "== Freddie" so downstream consumers see identical column names.
# ---------------------------------------------------------------------------
FANNIE_COLS = [
    "reference_pool_id",                        # 1
    "loan_identifier",                          # 2   X(12); NO vintage encoded
    "reporting_period",                         # 3   == Freddie; MMYYYY (!)
    "channel",                                  # 4   == Freddie; R/C/B
    "seller_name",                              # 5   == Freddie
    "servicer_name",                            # 6   == Freddie
    "master_servicer",                          # 7
    "original_interest_rate",                   # 8   == Freddie; 9(2).999 pct
    "current_interest_rate",                    # 9   == Freddie
    "original_upb",                             # 10  == Freddie
    "upb_at_issuance",                          # 11  CRT cut-off UPB; SF LPH=NA
    "current_upb",                              # 12  == Freddie (Current Actual UPB)
    "original_loan_term",                       # 13  == Freddie
    "origination_date",                         # 14  MMYYYY; vintage source
    "first_payment_date",                       # 15  == Freddie; MMYYYY (!)
    "loan_age",                                 # 16  == Freddie
    "remaining_months_legal_maturity",          # 17
    "remaining_months",                         # 18  == Freddie
    "maturity_date",                            # 19  == Freddie; MMYYYY (!)
    "original_ltv",                             # 20  == Freddie
    "cltv",                                     # 21  == Freddie
    "num_borrowers",                            # 22  == Freddie
    "dti",                                      # 23  == Freddie
    "credit_score",                             # 24  == Freddie (Borrower @ Orig)
    "co_borrower_credit_score",                 # 25
    "first_time_homebuyer",                     # 26  == Freddie
    "loan_purpose",                             # 27  == Freddie
    "property_type",                            # 28  == Freddie
    "num_units",                                # 29  == Freddie
    "occupancy",                                # 30  == Freddie
    "property_state",                           # 31  == Freddie
    "msa",                                      # 32  == Freddie
    "postal_code",                              # 33  == Freddie (Zip Code Short)
    "mi_pct",                                   # 34  == Freddie
    "amortization_type",                        # 35  == Freddie; FRM/ARM
    "ppm_flag",                                 # 36  == Freddie (Prepay Penalty)
    "io_indicator",                             # 37  == Freddie (Interest Only)
    "io_first_pi_payment_date",                 # 38  MMYYYY
    "months_to_amortization",                   # 39
    "delinquency_status",                       # 40  == Freddie; X(2), 00/01/.. (!)
    "loan_payment_history",                     # 41  24/48-char coded string
    "modification_flag",                        # 42  == Freddie
    "mi_cancel",                                # 43  == Freddie; SF LPH=NA
    "zero_balance_code",                        # 44  == Freddie; X(3) declared (!)
    "zero_balance_date",                        # 45  == Freddie (ZB Effective); MMYYYY
    "zero_balance_removal_upb",                 # 46  == Freddie (UPB at Removal)
    "repurchase_date",                          # 47  MMYYYY; SF LPH=NA
    "scheduled_principal_current",              # 48  SF LPH=NA (CAS-only)
    "total_principal_current",                  # 49  UPB delta; from Apr-2020
    "unscheduled_principal_current",            # 50  SF LPH=NA (CAS-only)
    "last_paid_installment_date",               # 51  MMYYYY
    "foreclosure_date",                         # 52  MMYYYY
    "disposition_date",                         # 53  MMYYYY
    "foreclosure_costs",                        # 54
    "property_preservation_costs",              # 55
    "asset_recovery_costs",                     # 56
    "misc_holding_expenses",                    # 57
    "holding_taxes",                            # 58
    "net_sales_proceeds",                       # 59  == Freddie
    "credit_enhancement_proceeds",              # 60
    "repurchase_make_whole_proceeds",           # 61
    "other_foreclosure_proceeds",               # 62
    "mod_non_ib_upb",                           # 63  Mod-Related Non-Int-Bearing UPB
    "principal_forgiveness_amount",             # 64
    "original_list_start_date",                 # 65  MMYYYY; SF LPH=NA
    "original_list_price",                      # 66  SF LPH=NA
    "current_list_start_date",                  # 67  MMYYYY; SF LPH=NA
    "current_list_price",                       # 68  SF LPH=NA
    "borrower_credit_score_issuance",           # 69  SF LPH=NA; FICO Score 5/Equifax
    "co_borrower_credit_score_issuance",        # 70  SF LPH=NA
    "borrower_credit_score_current",            # 71  SF LPH=NA
    "co_borrower_credit_score_current",         # 72  SF LPH=NA
    "mi_type",                                  # 73
    "servicing_activity_indicator",             # 74
    "current_period_mod_loss",                  # 75  SF LPH=NA
    "cumulative_mod_loss",                      # 76  SF LPH=NA
    "current_period_credit_event_net",          # 77  SF LPH=NA
    "cumulative_credit_event_net",              # 78  SF LPH=NA
    "special_eligibility",                      # 79  == Freddie (name reuse)
    "foreclosure_principal_writeoff",           # 80
    "relocation_mortgage_indicator",            # 81
    "zero_balance_code_change_date",            # 82  MMYYYY; SF LPH=NA
    "loan_holdback_indicator",                  # 83  SF LPH=NA
    "loan_holdback_effective_date",             # 84  MMYYYY; SF LPH=NA
    "delinquent_accrued_interest",              # 85  == Freddie; SF LPH=NA
    "property_val_method",                      # 86  == Freddie
    "high_balance_indicator",                   # 87
    "arm_initial_fixed_rate_le5yr",             # 88  CIRT-only
    "arm_product_type",                         # 89  CIRT-only
    "initial_fixed_rate_period",                # 90  CIRT-only
    "rate_adjustment_frequency",                # 91  CIRT-only
    "next_rate_adjustment_date",                # 92  MMYYYY; CIRT-only
    "next_payment_change_date",                 # 93  MMYYYY; CIRT-only
    "arm_index",                                # 94  CIRT-only
    "arm_cap_structure",                        # 95  CIRT-only
    "initial_rate_cap_up",                      # 96  CIRT-only
    "periodic_rate_cap_up",                     # 97  CIRT-only
    "lifetime_rate_cap_up",                     # 98  CIRT-only
    "mortgage_margin",                          # 99  CIRT-only
    "arm_balloon_indicator",                    # 100 CIRT-only
    "arm_plan_number",                          # 101 CIRT-only
    "borrower_assistance",                      # 102 == Freddie; F=Forbearance
    "hltv_refinance_indicator",                 # 103
    "deal_name",                                # 104 SF LPH=NA
    "repurchase_make_whole_flag",               # 105
    "alternative_delinquency_resolution",       # 106
    "alternative_delinquency_resolution_count", # 107
    "total_deferral_amount",                    # 108
]

assert len(FANNIE_COLS) == 108, f"expected 108 fields, got {len(FANNIE_COLS)}"

# ---------------------------------------------------------------------------
# OBSERVED WIRE FORMAT (verified against the real 2019Q1 SF LPH download,
# 2026-07-15; 341,865 loans / 11,583,612 rows):
#   * pipe-delimited, headerless, despite the .csv inner filename and the
#     FAQ's "CSV format" wording;
#   * 113 physical columns: positions 1-108 match this glossary layout
#     EXACTLY (verified by value-distribution profiling: the FRM-only ARM
#     block 88-101 is empty, borrower assistance at 102 shows the documented
#     {7,F,N,T,R} code set, MI type at 73 shows {1,2,3}, etc.), plus FIVE
#     APPENDED positions 109-113 added by Fannie after this glossary's
#     2023-06 revision. Observed content: 109 constant "7", 111 sparse
#     credit-score-like values, 110/112/113 empty. Their official names are
#     pending the current layout doc; NONE are consumed by the pipeline.
# ---------------------------------------------------------------------------
FANNIE_COLS_APPENDED = [
    "appended_109",   # observed constant "7" (7 = Not Applicable convention)
    "appended_110",   # observed empty
    "appended_111",   # observed sparse 3-digit credit-score-like values
    "appended_112",   # observed empty
    "appended_113",   # observed empty
]
FANNIE_COLS_WIRE = FANNIE_COLS + FANNIE_COLS_APPENDED
assert len(FANNIE_COLS_WIRE) == 113

# ---------------------------------------------------------------------------
# dtypes for the columns hazard/ingest.py actually consumes (post-synthesis
# names match Freddie). The native file is read all-Utf8 (infer_schema_length=0)
# and cast at stage time, exactly as ingest.py does; these are documentation of
# the intended casts and may be used by callers that want an eager schema.
# ---------------------------------------------------------------------------
FANNIE_DTYPES = {
    "loan_identifier": "str",              # 2   X(12) alpha-numeric
    "reporting_period": "str",             # 3   MMYYYY (transcode to YYYYMM)
    "original_interest_rate": "Float64",   # 8   9(2).999 percent units
    "original_upb": "Float64",             # 10  9(10).99
    "current_upb": "Float64",              # 12  9(10).99
    "original_loan_term": "Int64",         # 13  9(3)
    "origination_date": "str",             # 14  MMYYYY (vintage source)
    "first_payment_date": "str",           # 15  MMYYYY
    "loan_age": "Int64",                   # 16  9(3)
    "original_ltv": "Float64",             # 20  9(3)
    "credit_score": "Int64",               # 24  9(3)
    "amortization_type": "str",            # 35  X(3) FRM/ARM
    "delinquency_status": "str",           # 40  X(2) 00/01/.. or XX/99
    "zero_balance_code": "str",            # 44  X(3) declared
    "zero_balance_removal_upb": "Float64", # 46  9(10).99
    "property_state": "str",               # 31  X(2)
    "borrower_assistance": "str",          # 102 X(1) F/R/T/O/N/7/9
}

# ---------------------------------------------------------------------------
# Zero Balance Code semantics (glossary field 44, verbatim enumeration):
#   01 = Prepaid or Matured
#   02 = Third Party Sale
#   03 = Short Sale
#   06 = Repurchased
#   09 = Deed-in-Lieu; REO Disposition
#   15 = Notes Sales
#   16 = Reperforming Loan Sale
#   96 = Removal (non-credit event)
#   "Applies to all CAS deals prior to and including 2015-C03:"
#   97 = Delinquency (credit event due to D180)
#   98 = Other Credit Event
#
# HOW THESE CONSTANTS ARE (AND ARE NOT) USED
# -------------------------------------------
# Only FANNIE_ZB_VOLUNTARY_PREPAY ("01") and FANNIE_ZB_LEGACY_CREDIT_EVENT are
# load-bearing. prepare_fannie.py stages the raw code through unchanged (after
# stripping the declared X(3) padding), and hazard/ingest.py's is_prepay test
# fires on the literal "01" exactly as for Freddie; the legacy set is used only
# for the absence-gate in prepare_fannie.py. The remaining sets
# (FANNIE_ZB_CREDIT_EVENT / DEFAULT_REO / NON_CREDIT_REMOVAL / FANNIE_ZB_ALL) are
# DOCUMENTATION ONLY: they are not imported by ingest.py, which carries its own
# hardcoded recognized set {"01"} and {"02","03","09","15"} and routes every
# other code (Fannie's 06/16/96) to its `.otherwise("Current")` fallthrough.
# Consequence, verified and deliberately NOT silently patched here: a Fannie
# non-01 removal self-censors CORRECTLY out of the dollar-denominated risk set
# (Current Actual UPB zeroes at removal, glossary field 12), so the headline
# prepay hazard is unaffected; but such a loan is MISLABELED "Current" in the
# secondary Markov mode_state exhibit. Fixing that mislabel would require an
# ingest.py change (out of scope this round; see FIRST-DOWNLOAD CHECKLIST).
#
# Mapping choices mirror hazard/schema.py so the estimator stays identical
# across agencies:
#   * VOLUNTARY_PREPAY keeps the single literal "01" (== Freddie ZB_VOLUNTARY_PREPAY).
#     NB the glossary bundles "Matured" into 01; for 2017-2021 vintages no
#     360/180-month loan matures inside the window, matching Freddie's identical
#     01 conflation.
#   * CREDIT_EVENT = {"02","03","09","15"} == Freddie ZB_CREDIT_EVENT.
#   * DEFAULT_REO   = {"02","03","09"}      == Freddie ZB_DEFAULT_REO.
#   * NON_CREDIT_REMOVAL = {"06","16","96"} has NO Freddie counterpart. These are
#     censoring events (repurchase / reperforming-loan sale / non-credit
#     removal), NOT prepay and NOT default. 06 is the Fannie analogue of the
#     Ginnie servicer-buyout channel the paper flags as mechanically distinct,
#     and MUST NOT be folded into voluntary prepay (doing so biases the lock-in
#     marginal toward zero; see FIRST-DOWNLOAD CHECKLIST).
#   * LEGACY_CREDIT_EVENT = {"97","98"} is glossary-scoped to "CAS deals prior to
#     and including 2015-C03" and must NOT appear in a 2017-2021 SF LPH file;
#     prepare_fannie.py gates on their absence (validate_legacy_zbc=...).
# ---------------------------------------------------------------------------
FANNIE_ZB_VOLUNTARY_PREPAY = "01"
FANNIE_ZB_CREDIT_EVENT = {"02", "03", "09", "15"}
FANNIE_ZB_DEFAULT_REO = {"02", "03", "09"}
FANNIE_ZB_NON_CREDIT_REMOVAL = {"06", "16", "96"}
FANNIE_ZB_LEGACY_CREDIT_EVENT = {"97", "98"}

# All ZBC tokens the glossary documents (for validation / assertion at stage time)
FANNIE_ZB_ALL = (
    {FANNIE_ZB_VOLUNTARY_PREPAY}
    | FANNIE_ZB_CREDIT_EVENT
    | FANNIE_ZB_NON_CREDIT_REMOVAL
    | FANNIE_ZB_LEGACY_CREDIT_EVENT
)
