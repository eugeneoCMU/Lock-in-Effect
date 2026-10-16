"""Freddie Mac SF Loan-Level Dataset column layouts (pipe-delimited, no header)."""

import re

SOURCE_SEMANTICS_VERSION = 'freddie-native32-reo-priority-v2'
# Recognized archived receipts remain verifiable, but consumption gates require
# SOURCE_SEMANTICS_VERSION. This does not relabel earlier source outputs.
ARCHIVE_SOURCE_SEMANTICS_VERSIONS = frozenset({
    'freddie-native32-ddlpi-states-v1', SOURCE_SEMANTICS_VERSION})
_PERF_DATE = re.compile(rb'(19|20)\d{2}(0[1-9]|1[0-2])')
_TERMINAL_CODES = {b'01', b'02', b'03', b'09', b'15', b'16', b'96'}


def validate_performance_semantics(row, source_layout="native32"):
    """Validate native tokens only after the caller's outcome/date boundary."""
    source_semantics_version(source_layout)
    if (source_layout == 'release47' and row[8] not in _TERMINAL_CODES
            and row[3] != b'RA' and not re.fullmatch(rb'\d{2}', row[3])):
        raise ValueError('Release 47 performance semantic mismatch: unresolved nonterminal delinquency')
    if (row[12] and not _PERF_DATE.fullmatch(row[12])):
        raise ValueError('Native performance semantic mismatch: last-paid date')
    if row[28] not in {b'', b'Y'} or row[29] not in {b'', b'F', b'R', b'T'}:
        raise ValueError('Native performance semantic mismatch: disaster/assistance position')
    if row[8] not in _TERMINAL_CODES | {b''}:
        raise ValueError('Native performance semantic mismatch: unknown termination code')
    if row[8] not in _TERMINAL_CODES and not (
            row[3] == b'RA' or (row[3].isdigit() and len(row[3]) <= 3)):
        raise ValueError('Native performance semantic mismatch: unresolved nonterminal delinquency')

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
    "loan_purpose",           # 20
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

# January-2026 native performance layout: 32 columns, including DDLPI at 12.
# A missing DDLPI name shifts every later field without changing row width.
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
    "due_date_last_paid_installment", # 12 YYYYMM
    "mi_recoveries",              # 13
    "net_sales_proceeds",         # 14
    "non_mi_recoveries",          # 15
    "expenses",                   # 16
    "legal_costs",                # 17
    "maintenance_costs",          # 18
    "taxes_insurance",            # 19
    "misc_expenses",              # 20
    "actual_loss",                # 21
    "modification_cost",          # 22
    "step_mod_indicator",         # 23
    "deferred_payment_flag",      # 24
    "eltv",                       # 25
    "zero_balance_removal_upb",    # 26
    "delinquent_accrued_interest", # 27
    "delinq_disaster",            # 28
    "borrower_assistance",        # 29 F=Forbearance
    "current_month_mod_cost",     # 30
    "interest_bearing_upb",       # 31
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

# Release 47 provenance is explicit; native32 receipts keep their v2 identity.
RELEASE47_SOURCE_SEMANTICS_VERSION = 'freddie-release47-reo-priority-v3'
RELEASE47_LAYOUT_URL = 'https://www.freddiemac.com/fmac-resources/research/pdf/file_layout_july_2026.xlsx'
RELEASE47_DISCLOSURE_URL = 'https://www.freddiemac.com/fmac-resources/research/pdf/disclosure-changes-summary.pdf'
RELEASE47_ORIG_COLS = ORIG_COLS[:24] + ORIG_COLS[25:31] + ['vantage_score_4']
RELEASE47_PERF_COLS = PERF_COLS + ['mi_cancel', 'servicer_name', 'bankruptcy_cramdown_costs']


def source_semantics_version(source_layout='native32'):
    if source_layout == 'native32':
        return SOURCE_SEMANTICS_VERSION
    if source_layout == 'release47':
        return RELEASE47_SOURCE_SEMANTICS_VERSION
    raise ValueError('Unknown Freddie source layout')


def source_layout_metadata(source_layout='native32'):
    """Record physical widths, used canonical positions and publisher provenance."""
    version = source_semantics_version(source_layout)
    orig = ORIG_COLS if source_layout == 'native32' else RELEASE47_ORIG_COLS
    perf = PERF_COLS if source_layout == 'native32' else RELEASE47_PERF_COLS
    orig_used = [0, 1, 10, 11, 12, 15, 16, 19, 21]
    perf_used = [0, 1, 2, 3, 4, 5, 7, 8, 10, 11, 12, 24, 28, 29, 31]
    return dict(source_layout=source_layout, source_semantics_version=version,
        origination_width=len(orig), performance_width=len(perf),
        canonical_layout='native32', position_convention='zero-based',
        used_origination_positions={ORIG_COLS[i]: dict(source=i, canonical=i) for i in orig_used},
        used_performance_positions={PERF_COLS[i]: dict(source=i, canonical=i) for i in perf_used},
        performance_normalization=('Two-digit delinquency to canonical integer token after cutoff; all flags retained as reported'
            if source_layout == 'release47' else 'Native tokens unchanged'),
        unused_release47_fields=(['vantage_score_4', 'mi_cancel', 'servicer_name', 'bankruptcy_cramdown_costs']
            if source_layout == 'release47' else []),
        layout_url=RELEASE47_LAYOUT_URL if source_layout == 'release47' else None,
        disclosure_changes_url=RELEASE47_DISCLOSURE_URL if source_layout == 'release47' else None)


def normalize_origination(row, source_layout='native32'):
    source_semantics_version(source_layout)
    width = 32 if source_layout == 'native32' else 31
    if len(row) != width:
        raise ValueError(f"Origination source requires exactly {width} fields")
    if source_layout == 'native32':
        return row
    # Servicer and MI-cancellation moved to performance; VS4 is unused.
    return row[:24] + [b''] + row[24:30] + [b'']


def normalize_performance(row, source_layout='native32'):
    """Call only after the outcome cutoff boundary; preserve as-reported flags."""
    source_semantics_version(source_layout)
    width = 32 if source_layout == 'native32' else 35
    if len(row) != width:
        raise ValueError(f"Performance source requires exactly {width} fields")
    if source_layout == 'native32':
        return row
    canonical = row[:32]
    if canonical[3].isdigit():
        canonical[3] = str(int(canonical[3])).encode()
    return canonical
