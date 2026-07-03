"""Freddie Mac SF Loan-Level Dataset column layouts (pipe-delimited, no header)."""

# Origination file — 32 columns (0-indexed positions)
ORIG_COLS = [
    "credit_score",           # 0
    "first_payment_date",     # 1  YYYYMM
    "first_time_homebuyer",   # 2
    "maturity_date",          # 3
    "msa",                    # 4
    "mi_pct",                 # 5
    "num_units",              # 6
    "occupancy",              # 7
    "cltv",                   # 8
    "dti",                    # 9
    "original_upb",           # 10
    "original_ltv",           # 11
    "original_interest_rate", # 12
    "channel",                # 13
    "ppm_flag",               # 14
    "amortization_type",      # 15  FRM / ARM
    "property_state",         # 16
    "property_type",          # 17
    "postal_code",            # 18
    "loan_sequence_number",   # 19
    "loan_purpose",           # 18 -> actually 20 in 1-indexed = index 19
    "original_loan_term",     # 21
    "num_borrowers",          # 22
    "seller_name",            # 23
    "servicer_name",           # 24
    "super_conforming",       # 25
    "pre_relief_seq",         # 26
    "special_eligibility",    # 27
    "relief_refi",            # 28
    "property_val_method",    # 29
    "io_indicator",           # 30
    "mi_cancel",              # 31
]

# Performance file — 32 columns
PERF_COLS = [
    "loan_sequence_number",       # 0
    "reporting_period",           # 1  YYYYMM
    "current_upb",                # 2
    "delinquency_status",         # 3
    "loan_age",                   # 4
    "remaining_months",           # 5
    "defect_settlement_date",     # 6
    "modification_flag",          # 7
    "zero_balance_code",          # 8
    "zero_balance_date",          # 9
    "current_interest_rate",      # 10
    "current_non_ib_upb",         # 11
    "mi_recoveries",              # 12
    "net_sales_proceeds",         # 13
    "non_mi_recoveries",          # 14
    "expenses",                   # 15
    "legal_costs",                # 16
    "maintenance_costs",          # 17
    "taxes_insurance",            # 18
    "misc_expenses",              # 19
    "actual_loss",                # 20
    "modification_cost",          # 21
    "step_mod_indicator",         # 22
    "deferred_payment_flag",      # 23
    "eltv",                       # 24
    "zero_balance_removal_upb",   # 25
    "delinquent_accrued_interest",# 26
    "delinq_disaster",            # 27
    "borrower_assistance",        # 28  F=Forbearance
    "current_month_mod_cost",     # 29
    "interest_bearing_upb",       # 30
    "deferred_upb",               # 31
]

ORIG_DTYPES = {
    "credit_score": "Int64",
    "first_payment_date": "str",
    "original_upb": "Float64",
    "original_ltv": "Float64",
    "original_interest_rate": "Float64",
    "loan_sequence_number": "str",
    "amortization_type": "str",
    "property_state": "str",
}

PERF_DTYPES = {
    "loan_sequence_number": "str",
    "reporting_period": "str",
    "current_upb": "Float64",
    "delinquency_status": "str",
    "loan_age": "Int64",
    "zero_balance_code": "str",
    "borrower_assistance": "str",
}

# Zero balance codes (termination events)
ZB_VOLUNTARY_PREPAY = "01"
ZB_CREDIT_EVENT = {"02", "03", "09", "15"}
ZB_DEFAULT_REO = {"02", "03", "09"}
