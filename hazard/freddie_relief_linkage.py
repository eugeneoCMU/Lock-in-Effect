"""Pure parsing and audit helpers for Freddie Mac pre-July-2026 origination rows.

This module only checks disclosed origination-key links. It does not verify
payoff events, performance histories, or refinance contracts.
"""

from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
import re


LAYOUT = "freddie_pre_july_2026_32_field_origination"
_SEQUENCE = re.compile(r"[FA][0-9]{2}Q[1-4][0-9]{7}\Z")
_VINTAGE = re.compile(r"[0-9]{2}Q[1-4]\Z")
_STATUSES = (
    "program_flag_inconsistent",
    "duplicate_successor_ambiguity",
    "missing_predecessor",
    "duplicate_predecessor_ambiguity",
    "outside_target_vintage",
    "self_link",
    "exact_origination_key_match",
)

_COLUMNS = {
    "first_payment_date": 2,
    "maturity_date": 4,
    "original_upb": 11,
    "original_ltv": 12,
    "original_interest_rate": 13,
    "prepayment_penalty_flag": 15,
    "amortization_type": 16,
    "loan_sequence_number": 20,
    "original_term": 22,
    "pre_relief_sequence_number": 27,
    "relief_refinance_indicator": 29,
}


def _month(raw, name, missing):
    if raw == "":
        missing[name] = "blank"
        return None
    if not re.fullmatch(r"[0-9]{6}", raw):
        raise ValueError(f"{name} must be YYYYMM or blank")
    year, month = int(raw[:4]), int(raw[4:])
    if year == 0 or not 1 <= month <= 12:
        raise ValueError(f"{name} is not a valid YYYYMM date")
    return f"{year:04d}-{month:02d}"


def _number(raw, name, missing, *, documented_sentinels=(), positive=False):
    if raw == "":
        missing[name] = "blank"
        return None
    if raw in documented_sentinels:
        missing[name] = f"sentinel_{raw}"
        return None
    try:
        value = Decimal(raw)
    except InvalidOperation:
        raise ValueError(f"{name} must be numeric or a documented missing value") from None
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < 0 or (positive and value <= 0):
        raise ValueError(f"{name} must be {'positive' if positive else 'nonnegative'}")
    return value


def parse_origination_row(row):
    """Parse one pipe-delimited row under the fixed pre-July-2026 32-field layout.

    Whitespace is trimmed at field boundaries. Raw field strings and parsed
    values are returned separately; known missing placeholders are recorded in
    ``missing``. The sequence key's quarter is an origination vintage label and
    does not identify an exact origination month.
    """
    if isinstance(row, bytes):
        try:
            row = row.decode("ascii")
        except UnicodeDecodeError:
            raise ValueError("origination row must be ASCII") from None
    if not isinstance(row, str):
        raise ValueError("origination row must be text or bytes")
    raw_fields = row.rstrip("\r\n").split("|")
    fields = [part.strip() for part in raw_fields]
    if len(fields) != 32:
        raise ValueError("pre-July-2026 origination row must contain exactly 32 fields")

    raw = {name: fields[column - 1] for name, column in _COLUMNS.items()}
    missing = {}
    key = raw["loan_sequence_number"]
    if not _SEQUENCE.fullmatch(key):
        raise ValueError("loan_sequence_number must match the exact 12-character sequence key format")
    predecessor = raw["pre_relief_sequence_number"]
    if predecessor and not _SEQUENCE.fullmatch(predecessor):
        raise ValueError("pre_relief_sequence_number must be blank or an exact 12-character sequence key")

    relief = raw["relief_refinance_indicator"]
    if relief not in ("", "Y"):
        raise ValueError("relief_refinance_indicator must be Y or blank in this layout")
    ppm = raw["prepayment_penalty_flag"]
    if ppm not in ("", "Y", "N"):
        raise ValueError("prepayment_penalty_flag must be Y, N, or blank")
    amortization = raw["amortization_type"]
    if amortization not in ("", "FRM", "ARM"):
        raise ValueError("amortization_type must be FRM, ARM, or blank")

    first_payment = _month(raw["first_payment_date"], "first_payment_date", missing)
    maturity = _month(raw["maturity_date"], "maturity_date", missing)
    upb = _number(raw["original_upb"], "original_upb", missing, positive=True)
    ltv = _number(raw["original_ltv"], "original_ltv", missing, documented_sentinels=("999",))
    rate = _number(raw["original_interest_rate"], "original_interest_rate", missing)
    term_value = _number(raw["original_term"], "original_term", missing, positive=True)
    if term_value is not None and term_value != term_value.to_integral_value():
        raise ValueError("original_term must be an integer number of months")

    chronology = []
    if first_payment and maturity and first_payment > maturity:
        chronology.append("first_payment_after_maturity")
    plausibility = []
    if term_value is not None and term_value > 600:
        plausibility.append("original_term_above_600_months")
    return {
        "layout": LAYOUT,
        "raw_fields": tuple(raw_fields),
        "raw": raw,
        "parsed": {
            "first_payment_date": first_payment,
            "maturity_date": maturity,
            "original_upb": upb,
            "original_ltv": ltv,
            "original_interest_rate": rate,
            "prepayment_penalty_flag": ppm or None,
            "amortization_type": amortization or None,
            "loan_sequence_number": key,
            "sequence_product": key[0],
            "sequence_vintage": key[1:5],
            "original_term": int(term_value) if term_value is not None else None,
            "pre_relief_sequence_number": predecessor or None,
            "relief_refinance_indicator": relief or None,
            "origination_month": None,
        },
        "missing": missing,
        "chronology_diagnostics": chronology,
        "plausibility_diagnostics": plausibility,
    }


def _source_row(value):
    if isinstance(value, dict) and "row" in value:
        return value.get("dataset"), parse_origination_row(value["row"])
    return None, parse_origination_row(value)


def _parse_error_category(error):
    """Return a bounded category, never source text or an identifier."""
    message = str(error)
    if "exactly 32 fields" in message:
        return "field_width"
    if "sequence key" in message:
        return "sequence_key"
    if "date" in message:
        return "date"
    if "numeric" in message or "finite" in message or "integer" in message:
        return "numeric_value"
    if "must be" in message:
        return "field_value"
    return "input_type"


def _parse_rows(values):
    parsed = []
    errors = Counter()
    for value in values:
        try:
            parsed.append(_source_row(value))
        except (TypeError, ValueError) as error:
            errors[_parse_error_category(error)] += 1
    return parsed, errors


def audit_relief_links(successor_rows, predecessor_rows, target_vintage="06Q4", source_scope=None):
    """Audit Relief key references against supplied predecessor origination rows.

    ``predecessor_rows`` may contain raw rows or ``{"dataset": name,
    "row": raw_row}`` records so Standard and Non-Standard lookup provenance
    remains visible. No row is removed when duplicate keys or conflicts occur.
    """
    if target_vintage is not None and not _VINTAGE.fullmatch(target_vintage):
        raise ValueError("target_vintage must be YYQn or None")
    successor_records, successor_errors = _parse_rows(successor_rows)
    predecessor_records, predecessor_errors = _parse_rows(predecessor_rows)
    successors = [record[1] for record in successor_records]
    predecessors = predecessor_records
    by_key = defaultdict(list)
    for dataset, old in predecessors:
        by_key[old["parsed"]["loan_sequence_number"]].append((dataset, old))

    successor_groups = defaultdict(list)
    for new in successors:
        successor_groups[new["parsed"]["loan_sequence_number"]].append(new)
    successor_duplicate_type = {}
    for key, records in successor_groups.items():
        if len(records) > 1:
            normalized = [tuple(field.strip() for field in record["raw_fields"]) for record in records]
            successor_duplicate_type[key] = "identical" if len(set(normalized)) == 1 else "conflicting"

    fanout = defaultdict(set)
    for new in successors:
        p = new["parsed"]
        if p["relief_refinance_indicator"] == "Y" and p["pre_relief_sequence_number"]:
            fanout[p["pre_relief_sequence_number"]].add(p["loan_sequence_number"])
    fanout_hist = Counter(len(successor_keys) for successor_keys in fanout.values())

    matches = []
    counts = Counter()
    for new in successors:
        p = new["parsed"]
        relief = p["relief_refinance_indicator"] == "Y"
        prior_key = p["pre_relief_sequence_number"]
        if not relief and not prior_key:
            continue
        counts["rows_requiring_link_audit"] += 1
        if relief and prior_key:
            counts["candidates"] += 1

        status = "candidate"
        old_records = by_key.get(prior_key, []) if prior_key else []
        unique_predecessor_key_found = len(old_records) == 1
        timing_status = "unknown_missing_dates"
        if old_records:
            new_first = p["first_payment_date"]
            old_firsts = [record[1]["parsed"]["first_payment_date"] for record in old_records]
            own_date_conflict = bool(new["chronology_diagnostics"]) or any(
                record[1]["chronology_diagnostics"] for record in old_records
            )
            if own_date_conflict:
                timing_status = "conflict"
            elif new_first is not None and all(value is not None for value in old_firsts):
                timing_status = "conflict" if any(value > new_first for value in old_firsts) else "date_order_consistent"
        if relief != bool(prior_key):
            status = "program_flag_inconsistent"
        elif prior_key == p["loan_sequence_number"]:
            status = "self_link"
        elif p["loan_sequence_number"] in successor_duplicate_type:
            status = "duplicate_successor_ambiguity"
        else:
            if not old_records:
                status = "missing_predecessor"
            elif len(old_records) > 1:
                status = "duplicate_predecessor_ambiguity"
            else:
                old = old_records[0][1]
                old_vintage = old["parsed"]["sequence_vintage"]
                if target_vintage is not None and old_vintage != target_vintage:
                    status = "outside_target_vintage"
                else:
                    status = "exact_origination_key_match"

        counts[status] += 1
        matches.append({
            "status": status,
            "successor": new,
            "predecessor_key": prior_key,
            "predecessor": old_records[0][1] if status == "exact_origination_key_match" else None,
            "predecessor_dataset": old_records[0][0] if status == "exact_origination_key_match" else None,
            "predecessor_candidates": [
                {"dataset": dataset, "row": record} for dataset, record in old_records
            ],
            "duplicate_successor_type": successor_duplicate_type.get(p["loan_sequence_number"]),
            "predecessor_fanout": len(fanout.get(prior_key, set())) if prior_key else 0,
            "predecessor_fanout_flag": len(fanout.get(prior_key, set())) > 1 if prior_key else False,
            "unique_predecessor_key_found": unique_predecessor_key_found,
            "timing_status": timing_status,
            "payoff_timing_verified": False,
            "sequence_century_unresolved": True,
            "contract_verified": False,
            "payoff_performance_verified": False,
        })

    count_result = {status: counts.get(status, 0) for status in _STATUSES}
    count_result.update(counts)
    count_result["duplicate_successor_conflicts"] = sum(
        value == "conflicting" for value in successor_duplicate_type.values()
    )
    count_result["duplicate_successor_groups"] = len(successor_duplicate_type)
    count_result["identical_duplicate_successor_groups"] = sum(
        value == "identical" for value in successor_duplicate_type.values()
    )
    count_result["conflicting_duplicate_successor_groups"] = count_result["duplicate_successor_conflicts"]
    count_result["duplicate_successor_ambiguous_rows"] = sum(
        len(successor_groups[key]) for key in successor_duplicate_type
    )
    count_result["exact_origination_key_matches"] = counts.get("exact_origination_key_match", 0)
    count_result["successor_parse_errors"] = sum(successor_errors.values())
    count_result["predecessor_parse_errors"] = sum(predecessor_errors.values())
    successor_vintages = Counter(record["parsed"]["sequence_vintage"] for record in successors)
    return {
        "layout": LAYOUT,
        "layout_assumption": "pre-July-2026 32-field origination layout",
        "release_vintage_inferred_from_layout": False,
        "release_compatibility_verified": False,
        "cross_source_compatibility_verified": False,
        "source_identity_verified": False,
        "source_scope": {"value": source_scope, "verification": "caller_supplied_unverified"},
        "target_vintage": target_vintage,
        "successor_vintage_counts": dict(sorted(successor_vintages.items())),
        "counts": count_result,
        "parse_errors": {
            "successor": dict(successor_errors),
            "predecessor": dict(predecessor_errors),
        },
        "predecessor_fanout_histogram": {str(k): v for k, v in sorted(fanout_hist.items())},
        "matches": matches,
        "verified_payoff_contracts": 0,
        "ordinary_payoff_causes_classified": 0,
    }
