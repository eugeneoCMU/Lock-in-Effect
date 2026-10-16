import pytest
from decimal import Decimal

from hazard.freddie_relief_linkage import audit_relief_links, parse_origination_row


def row(*, key, predecessor="", relief=" ", first_payment="201703", maturity="204702",
        original_upb="250000", ltv="80", rate="4.0", ppm="N", amortization="FRM",
        term="360"):
    fields = [""] * 32
    fields[1] = first_payment
    fields[3] = maturity
    fields[10] = original_upb
    fields[11] = ltv
    fields[12] = rate
    fields[14] = ppm
    fields[15] = amortization
    fields[19] = key
    fields[21] = term
    fields[26] = predecessor
    fields[28] = relief
    return "|".join(fields)


def test_parser_requires_exact_12_character_sequence_key():
    parsed = parse_origination_row(row(key="F17Q10000001", relief="Y", predecessor="F06Q40000001"))
    assert parsed["parsed"]["sequence_product"] == "F"
    with pytest.raises(ValueError, match="sequence key"):
        parse_origination_row(row(key="F17Q1000001"))
    with pytest.raises(ValueError, match="sequence key"):
        parse_origination_row(row(key="F17Q100000001"))


def test_parser_requires_exact_32_field_width():
    with pytest.raises(ValueError, match="32"):
        parse_origination_row("|".join([""] * 31))


def test_dates_keep_raw_values_and_do_not_infer_exact_origination_month():
    parsed = parse_origination_row(row(key="F17Q10000001", first_payment="201702", maturity=""))
    assert parsed["raw"]["first_payment_date"] == "201702"
    assert parsed["parsed"]["first_payment_date"] == "2017-02"
    assert parsed["raw"]["maturity_date"] == ""
    assert parsed["parsed"]["maturity_date"] is None
    assert parsed["parsed"]["origination_month"] is None
    with pytest.raises(ValueError, match="date"):
        parse_origination_row(row(key="F17Q10000001", first_payment="201713"))
    with pytest.raises(ValueError, match="date"):
        parse_origination_row(row(key="F17Q10000001", maturity="999999"))


def test_trimmed_parse_keeps_raw_fields_and_reports_term_999_as_numeric():
    source = row(key="F17Q10000001", term="999")
    fields = source.split("|")
    fields[19] = " F17Q10000001 "
    parsed = parse_origination_row("|".join(fields))
    assert parsed["raw_fields"][19] == " F17Q10000001 "
    assert parsed["parsed"]["loan_sequence_number"] == "F17Q10000001"
    assert parsed["parsed"]["original_term"] == 999
    assert "original_term" not in parsed["missing"]
    assert "original_term_above_600_months" in parsed["plausibility_diagnostics"]
    assert parsed["layout"] == "freddie_pre_july_2026_32_field_origination"


@pytest.mark.parametrize("field,value", [
    ("original_upb", "-1"), ("original_upb", "0"),
    ("original_ltv", "-0.1"), ("original_interest_rate", "-1"),
    ("original_term", "-12"), ("original_term", "0"),
    ("original_upb", "Infinity"), ("original_interest_rate", "NaN"),
])
def test_numeric_values_must_be_finite_and_nonnegative_with_positive_upb_term(field, value):
    fields = row(key="F17Q10000001").split("|")
    positions = {"original_upb": 10, "original_ltv": 11, "original_interest_rate": 12, "original_term": 21}
    fields[positions[field]] = value
    with pytest.raises(ValueError):
        parse_origination_row("|".join(fields))


def test_upb_and_rate_preserve_decimal_precision_and_unknown_upb_sentinel_is_not_missing():
    fields = row(key="F17Q10000001", original_upb="999999999999", rate="3.123456789012345678").split("|")
    parsed = parse_origination_row("|".join(fields))
    assert parsed["parsed"]["original_upb"] == Decimal("999999999999")
    assert parsed["parsed"]["original_interest_rate"] == Decimal("3.123456789012345678")
    assert "original_upb" not in parsed["missing"]


def test_unknown_tokens_and_bad_own_term_dates_are_rejected_or_diagnosed():
    with pytest.raises(ValueError, match="date"):
        parse_origination_row(row(key="F17Q10000001", first_payment="UNKNOWN"))
    parsed = parse_origination_row(row(key="F17Q10000001", first_payment="204803", maturity="204702"))
    assert parsed["chronology_diagnostics"] == ["first_payment_after_maturity"]


def test_link_audit_finds_predecessor_in_nonstandard_lookup_and_keeps_missing_terms():
    successor = row(key="F17Q10000001", predecessor="A06Q40000001", relief="Y", rate="3.5")
    predecessor = row(key="A06Q40000001", rate="6.5", original_upb="180000", term="")
    result = audit_relief_links([successor], [{"dataset": "nonstandard", "row": predecessor}], target_vintage="06Q4")
    link = result["matches"][0]
    assert link["status"] == "exact_origination_key_match"
    assert link["predecessor_dataset"] == "nonstandard"
    assert link["predecessor"]["parsed"]["original_term"] is None
    assert link["predecessor"]["missing"]["original_term"] == "blank"
    assert link["contract_verified"] is False
    assert result["verified_payoff_contracts"] == 0
    assert result["ordinary_payoff_causes_classified"] == 0


def test_duplicate_predecessor_keys_are_ambiguous_without_deleting_records():
    successor = row(key="F17Q10000001", predecessor="F06Q40000001", relief="Y")
    old_a = row(key="F06Q40000001", original_upb="180000")
    old_b = row(key="F06Q40000001", original_upb="181000")
    result = audit_relief_links([successor], [old_a, old_b], target_vintage="06Q4")
    assert result["matches"][0]["status"] == "duplicate_predecessor_ambiguity"
    assert len(result["matches"][0]["predecessor_candidates"]) == 2


def test_duplicate_successor_key_with_conflicting_link_is_flagged():
    first = row(key="F17Q10000001", predecessor="F06Q40000001", relief="Y")
    conflicting = row(key="F17Q10000001", predecessor="F06Q30000001", relief="Y")
    result = audit_relief_links([first, conflicting], [], target_vintage="06Q4")
    assert all(m["status"] == "duplicate_successor_ambiguity" for m in result["matches"])
    assert all(m["duplicate_successor_type"] == "conflicting" for m in result["matches"])
    assert result["counts"]["conflicting_duplicate_successor_groups"] == 1
    assert result["counts"]["duplicate_successor_ambiguous_rows"] == 2


def test_duplicate_successor_same_link_but_conflicting_terms_is_still_ambiguous():
    first = row(key="F17Q10000001", predecessor="F06Q40000001", relief="Y", rate="3.5")
    second = row(key="F17Q10000001", predecessor="F06Q40000001", relief="Y", rate="4.0")
    result = audit_relief_links([first, second], [row(key="F06Q40000001")], target_vintage="06Q4")
    assert all(m["status"] == "duplicate_successor_ambiguity" for m in result["matches"])
    assert all(m["duplicate_successor_type"] == "conflicting" for m in result["matches"])


def test_identical_duplicate_successors_are_counted_and_preserved():
    source = row(key="F17Q10000001", predecessor="F06Q40000001", relief="Y")
    result = audit_relief_links([source, source], [row(key="F06Q40000001")], target_vintage="06Q4")
    assert len(result["matches"]) == 2
    assert all(m["duplicate_successor_type"] == "identical" for m in result["matches"])
    assert result["counts"]["identical_duplicate_successor_groups"] == 1


def test_program_flag_mismatch_is_not_treated_as_candidate():
    result = audit_relief_links([row(key="F17Q10000001", predecessor="", relief="Y")], [], target_vintage="06Q4")
    assert result["matches"][0]["status"] == "program_flag_inconsistent"


def test_wrong_target_vintage_is_reported_as_scope_not_chronology():
    successor = row(key="F17Q10000001", predecessor="F17Q10000002", relief="Y")
    predecessor = row(key="F17Q10000002")
    result = audit_relief_links([successor], [predecessor], target_vintage="06Q4")
    assert result["matches"][0]["status"] == "outside_target_vintage"
    assert result["matches"][0]["unique_predecessor_key_found"] is True


def test_missing_dates_preserve_unique_key_match_and_mark_timing_unknown():
    successor = row(key="F17Q10000001", predecessor="F06Q40000001", relief="Y", first_payment="", maturity="")
    predecessor = row(key="F06Q40000001", first_payment="", maturity="")
    result = audit_relief_links([successor], [predecessor], target_vintage="06Q4")
    link = result["matches"][0]
    assert link["status"] == "exact_origination_key_match"
    assert link["unique_predecessor_key_found"] is True
    assert link["timing_status"] == "unknown_missing_dates"
    assert link["payoff_timing_verified"] is False


def test_date_conflict_does_not_change_literal_unique_key_match():
    successor = row(key="F17Q10000001", predecessor="F06Q40000001", relief="Y", first_payment="200601")
    predecessor = row(key="F06Q40000001", first_payment="200602")
    result = audit_relief_links([successor], [predecessor], target_vintage="06Q4")
    link = result["matches"][0]
    assert link["status"] == "exact_origination_key_match"
    assert link["unique_predecessor_key_found"] is True
    assert link["timing_status"] == "conflict"
    assert link["payoff_timing_verified"] is False


def test_internal_first_payment_after_maturity_makes_timing_status_conflict():
    successor = row(key="F17Q10000001", predecessor="F06Q40000001", relief="Y",
                    first_payment="201703", maturity="201702")
    predecessor = row(key="F06Q40000001", first_payment="200602", maturity="200601")
    link = audit_relief_links([successor], [predecessor], target_vintage="06Q4")["matches"][0]
    assert link["status"] == "exact_origination_key_match"
    assert link["unique_predecessor_key_found"] is True
    assert link["timing_status"] == "conflict"


def test_two_digit_vintages_do_not_infer_century_or_exact_dates():
    successor = row(key="F17Q10000001", predecessor="F99Q40000001", relief="Y", first_payment="", maturity="")
    predecessor = row(key="F99Q40000001", first_payment="", maturity="")
    result = audit_relief_links([successor], [predecessor], target_vintage=None)
    link = result["matches"][0]
    assert link["status"] == "exact_origination_key_match"
    assert link["sequence_century_unresolved"] is True
    assert link["timing_status"] == "unknown_missing_dates"
    assert link["successor"]["parsed"]["origination_month"] is None
    assert result["successor_vintage_counts"] == {"17Q1": 1}


def test_source_scope_metadata_is_echoed_as_caller_supplied_unverified():
    scope = {"predecessor_component": "2006Q4 origination", "source_identity_verified": True}
    result = audit_relief_links([], [], source_scope=scope)
    assert result["source_scope"] == {
        "value": scope,
        "verification": "caller_supplied_unverified",
    }
    assert result["source_identity_verified"] is False
    assert result["layout_assumption"] == "pre-July-2026 32-field origination layout"
    assert result["release_compatibility_verified"] is False
    assert result["cross_source_compatibility_verified"] is False
    assert result["source_scope"]["value"]["source_identity_verified"] is True


def test_first_payment_order_is_only_a_timing_diagnostic():
    successor = row(key="F17Q10000001", predecessor="F06Q40000001", relief="Y", first_payment="200601")
    predecessor = row(key="F06Q40000001", first_payment="200602")
    result = audit_relief_links([successor], [predecessor], target_vintage="06Q4")
    assert result["matches"][0]["status"] == "exact_origination_key_match"
    assert result["matches"][0]["timing_status"] == "conflict"
    assert result["matches"][0]["unique_predecessor_key_found"] is True
    assert result["verified_payoff_contracts"] == 0


def test_missing_predecessor_is_distinguished_from_candidate():
    successor = row(key="F17Q10000001", predecessor="F06Q40000001", relief="Y")
    result = audit_relief_links([successor], [], target_vintage="06Q4")
    assert result["matches"][0]["status"] == "missing_predecessor"
    assert result["counts"]["candidates"] == 1
    assert result["counts"]["exact_origination_key_matches"] == 0


def test_self_link_is_explicitly_flagged():
    source = row(key="F17Q10000001", predecessor="F17Q10000001", relief="Y")
    result = audit_relief_links([source], [source], target_vintage="06Q4")
    assert result["matches"][0]["status"] == "self_link"


def test_predecessor_fanout_histogram_and_flags_preserve_link_records():
    one = row(key="F17Q10000001", predecessor="F06Q40000001", relief="Y")
    two = row(key="F17Q10000002", predecessor="F06Q40000001", relief="Y")
    old = row(key="F06Q40000001")
    result = audit_relief_links([one, two], [old], target_vintage="06Q4")
    assert result["predecessor_fanout_histogram"] == {"2": 1}
    assert len(result["matches"]) == 2
    assert all(m["predecessor_fanout"] == 2 and m["predecessor_fanout_flag"] for m in result["matches"])


def test_audit_aggregates_parse_errors_without_echoing_raw_rows_or_identifiers():
    malformed_successor = row(key="PRIVATE-INVALID-KEY", relief="Y", predecessor="F06Q40000001")
    malformed_predecessor = row(key="F06Q40000001")[:-1]
    result = audit_relief_links([malformed_successor], [malformed_predecessor], target_vintage="06Q4")
    assert result["counts"]["successor_parse_errors"] == 1
    assert result["counts"]["predecessor_parse_errors"] == 1
    assert result["matches"] == []
    assert "PRIVATE-INVALID-KEY" not in repr(result)
