"""Frozen development costs and held-out distribution transport, never behavior."""

from collections import Counter
from copy import deepcopy
from decimal import Decimal
import csv
import hashlib
import importlib
import json

import pytest

from hazard.hmda_cost_profiles import profile_csv


PROTOCOL_HASH = "a" * 64


def api():
    return importlib.import_module("hazard.refinancing_cost_calibration")


def row(year="2024", **changes):
    result = dict(
        activity_year=year, state_code="PA", county_code="42003", loan_type="1",
        lien_status="1", reverse_mortgage="2", conforming_loan_limit="C",
        construction_method="1", total_units="1", occupancy_type="1",
        action_taken="1", loan_purpose="31", loan_amount="1000",
        total_loan_costs="10", interest_rate="6", discount_points="",
        lender_credits="", lei="L1", **{"open-end_line_of_credit": "2"},
    )
    result.update(changes)
    return result


@pytest.fixture
def development(tmp_path):
    profiles = {}
    hashes = {}
    for year, scale in (("2022", 1), ("2023", 2)):
        rows = [
            row(year, loan_purpose=purpose, total_loan_costs=str(cost * scale * purpose_scale))
            for purpose, purpose_scale in (("31", 1), ("32", 3))
            for cost in (0, 10, 20, 30, 40)
        ]
        rows.extend([
            row(year, total_loan_costs="NA"),
            row(year, loan_amount="0", total_loan_costs="10"),
        ])
        source = tmp_path / (year + ".csv")
        with source.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        counts = Counter((r["action_taken"], r["loan_purpose"]) for r in rows)
        amounts = Counter()
        for r in rows:
            amounts[r["action_taken"], r["loan_purpose"]] += Decimal(r["loan_amount"])
        aggregation = {"aggregations": [
            {"actions_taken": a, "loan_purposes": p, "count": n,
             "sum": str(amounts[a, p])}
            for (a, p), n in counts.items()
        ]}
        profiles[year] = profile_csv(
            source, expected_year=int(year), expected_state="PA",
            aggregation=aggregation, expected_header=list(rows[0]),
        )
        hashes[year] = hashlib.sha256(
            json.dumps(profiles[year], sort_keys=True).encode()
        ).hexdigest()
    return profiles, hashes


def freeze(development):
    profiles, hashes = development
    return api().freeze_cost_scenarios(
        profiles, protocol_sha256=PROTOCOL_HASH, profile_sha256=hashes,
    )


def held_out_rows():
    rows = [row(total_loan_costs=str(cost)) for cost in (0, 10, 10, 20, 30)]
    rows.extend([
        row(total_loan_costs="NA"), row(loan_amount="0"), row(loan_amount="NA"),
    ])
    rows.extend(row(loan_purpose="32", total_loan_costs=str(cost))
                for cost in (0, 20, 60, 90, 120))
    return rows


def test_freeze_exports_exact_purpose_and_mode_counts_without_pooling(development):
    result = freeze(development)
    assert result["scenario_count"] == len(result["scenarios"]) == 84
    assert Counter((s["development_year"], s["purpose_code"]) for s in result["scenarios"]) == {
        (2022, 31): 24, (2022, 32): 18, (2023, 31): 24, (2023, 32): 18,
    }
    assert Counter(s["balance_rule"] for s in result["scenarios"]) == {
        "supplied_balance_ratio": 72, "unchanged_balance": 6,
        "all_fees_financed_no_other_balance_change": 6,
    }
    assert result["frozen_cutoffs"]["2022"]["31"] == {"p25": .01, "p50": .02, "p75": .03}
    assert result["frozen_cutoffs"]["2023"]["31"] == {"p25": .02, "p50": .04, "p75": .06}
    assert result["frozen_cutoffs"]["2022"]["32"] == {"p25": .03, "p50": .06, "p75": .09}
    for scenario in result["scenarios"]:
        if scenario["purpose_code"] == 32:
            assert scenario["balance_rule"] == "supplied_balance_ratio"
        if scenario["balance_rule"] == "supplied_balance_ratio":
            assert scenario["new_to_existing_ratio"] in (.9, 1., 1.1)


def test_percentage_units_and_financed_identity_use_bridge_conversion(development):
    result = freeze(development)
    selected = [s for s in result["scenarios"] if s["development_year"] == 2022
                and s["purpose_code"] == 31 and s["quantile"] == "p50"]
    supplied = next(s for s in selected if s["balance_rule"] == "supplied_balance_ratio"
                    and s["new_to_existing_ratio"] == 1.1 and s["financing"] == "cash")
    financed = next(s for s in selected if s["balance_rule"] == "all_fees_financed_no_other_balance_change")
    assert supplied["reported_cost_to_new_loan_ratio"] == .02
    assert supplied["cost_fraction"] == pytest.approx(.022)
    assert financed["cost_fraction"] == pytest.approx(.02040816326530612)
    assert financed["new_to_existing_ratio"] == pytest.approx(1.0204081632653061)


def test_each_scenario_carries_provenance_and_all_group_denominators(development):
    profiles, hashes = development
    result = freeze(development)
    sample = next(s for s in result["scenarios"] if s["development_year"] == 2022
                  and s["purpose_code"] == 31)
    assert sample["protocol_sha256"] == PROTOCOL_HASH
    assert sample["profile_sha256"] == hashes["2022"]
    denominators = sample["group_denominators"]
    assert denominators["originated_records"] == 7
    assert denominators["numeric_loan_cost_records"] == 6
    assert denominators["fee_new_rounded_principal_pair_records"] == 5
    assert denominators["missing_or_nonpositive_new_principal_among_known_cost"] == 1
    assert denominators["cost_missing_by_code"] == {"not_applicable_or_unavailable": 1}
    for scenario in result["scenarios"]:
        assert scenario["evidence_class"] == "conditional_cost_scenario"
        assert scenario["cost_component"] == "reported_loan_costs"
        assert scenario["assumptions"]
        assert "production_ready" not in scenario
        for unsupported in ("rate_percent_quantiles_among_known_cost", "dollar_cost_quantiles"):
            assert unsupported not in scenario
    assert json.loads(json.dumps(result, allow_nan=False)) == result
    assert "production_ready" not in result


def test_observed_zero_quantile_stays_zero_for_every_transformation(development):
    profiles, hashes = development
    for p in profiles.values():
        for group in p["conforming_sitebuilt_principal_residence"]["by_purpose"]:
            group["new_principal_cost_ratio_percent_quantiles"] = {"p25": 0., "p50": 0., "p75": 0.}
    result = freeze(development)
    assert all(s["cost_fraction"] == 0. for s in result["scenarios"])


@pytest.mark.parametrize("extra", ["2024", "pooled", 2022])
def test_held_out_or_pooled_data_cannot_enter_freeze(development, extra):
    profiles, hashes = development
    profiles[extra] = deepcopy(profiles["2022"])
    hashes[extra] = "b" * 64
    with pytest.raises(ValueError):
        freeze(development)


@pytest.mark.parametrize("missing", ["2022", "2023"])
def test_both_development_years_are_mandatory(development, missing):
    profiles, _ = development
    profiles.pop(missing)
    with pytest.raises(ValueError):
        freeze(development)


@pytest.mark.parametrize("field,value", [
    ("year", 2024), ("year", "2022"), ("state", "OH"),
    ("status", "unvalidated"), ("evidence_class", "simulated"),
    ("behavioral_parameters_fitted", 1), ("model_parameters_changed", True),
])
def test_profile_scope_and_evidence_metadata_are_required(development, field, value):
    development[0]["2022"][field] = value
    with pytest.raises(ValueError):
        freeze(development)


@pytest.mark.parametrize("field", [
    "source_sha256", "source_bytes", "csv_columns", "frozen_source_schema_matched",
    "all_query_cells_match", "cells",
])
def test_missing_source_validation_receipts_fail_closed(development, field):
    development[0]["2022"]["source_validation"].pop(field)
    with pytest.raises(ValueError):
        freeze(development)


@pytest.mark.parametrize("field,value", [
    ("source_sha256", "not-a-sha"), ("source_bytes", 0),
    ("csv_columns", 1), ("frozen_source_schema_matched", False),
    ("all_query_cells_match", False),
])
def test_invalid_source_validation_receipts_fail_closed(development, field, value):
    development[0]["2022"]["source_validation"][field] = value
    with pytest.raises(ValueError):
        freeze(development)


def test_source_cell_and_cost_denominator_inconsistencies_are_rejected(development):
    profiles, _ = development
    profiles["2022"]["source_validation"]["cells"][0]["count"] += 1
    with pytest.raises(ValueError):
        freeze(development)


@pytest.mark.parametrize("quantiles", [
    None, {"p25": 1, "p50": 2}, {"p25": 3, "p50": 2, "p75": 1},
    {"p25": -1, "p50": 2, "p75": 3},
    {"p25": 1, "p50": float("nan"), "p75": 3},
])
def test_cost_cutoffs_must_be_present_finite_nonnegative_and_ordered(development, quantiles):
    group = development[0]["2022"]["conforming_sitebuilt_principal_residence"]["by_purpose"][0]
    group["new_principal_cost_ratio_percent_quantiles"] = quantiles
    with pytest.raises(ValueError):
        freeze(development)


@pytest.mark.parametrize("which", ["protocol", "profile", "profile_year"])
def test_provenance_hashes_are_mandatory(development, which):
    profiles, hashes = development
    protocol_hash = PROTOCOL_HASH
    if which == "protocol":
        protocol_hash = None
    elif which == "profile":
        hashes["2022"] = "bad"
    else:
        hashes.pop("2023")
    with pytest.raises(ValueError):
        api().freeze_cost_scenarios(profiles, protocol_sha256=protocol_hash, profile_sha256=hashes)


def test_held_out_ties_zeros_and_all_cost_denominators_are_preserved(development):
    frozen = freeze(development)
    result = api().compare_held_out_costs(held_out_rows(), frozen=frozen)
    assert result["test_scope"] == "cost_distribution_transport_only"
    purpose = result["held_out_by_purpose"]["31"]
    assert purpose["group_denominators"]["originated_records"] == 8
    assert purpose["group_denominators"]["numeric_loan_cost_records"] == 7
    assert purpose["group_denominators"]["fee_new_rounded_principal_pair_records"] == 5
    assert purpose["group_denominators"]["missing_or_nonpositive_new_principal_among_known_cost"] == 2
    assert purpose["group_denominators"]["cost_missing_by_code"] == {"not_applicable_or_unavailable": 1}
    assert purpose["q_distribution"] == {
        "records": 5, "zero_records": 1, "positive_records": 4,
        "minimum": 0., "maximum": .03,
        "quantiles": {"p25": .01, "p50": .01, "p75": .02},
    }
    comparison = next(c for c in result["comparisons"]
                      if c["development_year"] == 2022 and c["purpose_code"] == 31)
    assert comparison["counts"] == {
        "at_or_below_p25": 3, "at_or_below_p50": 4, "at_or_below_p75": 5,
        "central_p25_to_p75_inclusive": 4,
    }
    assert comparison["proportions"] == {
        "at_or_below_p25": .6, "at_or_below_p50": .8, "at_or_below_p75": 1.,
        "central_p25_to_p75_inclusive": .8,
    }
    assert len(result["comparisons"]) == 4
    assert "production_ready" not in result


def test_held_out_distributions_cannot_refit_frozen_development_cutoffs(development):
    frozen = freeze(development)
    original = deepcopy(frozen)
    ordinary = api().compare_held_out_costs(held_out_rows(), frozen=frozen)
    poison = [row(total_loan_costs="999999999"), row(loan_purpose="32", total_loan_costs="0")]
    changed = api().compare_held_out_costs(poison, frozen=frozen)
    assert frozen == original
    for result in (ordinary, changed):
        for comparison in result["comparisons"]:
            year, purpose = str(comparison["development_year"]), str(comparison["purpose_code"])
            assert comparison["frozen_q_cutoffs"] == original["frozen_cutoffs"][year][purpose]
    assert ordinary["comparisons"][0]["proportions"] != changed["comparisons"][0]["proportions"]


@pytest.mark.parametrize("change", [
    {"loan_type": "2"}, {"lien_status": "2"}, {"open-end_line_of_credit": "1"},
    {"reverse_mortgage": "1"}, {"conforming_loan_limit": "NC"},
    {"construction_method": "2"}, {"total_units": "5"}, {"occupancy_type": "2"},
])
def test_valid_scoped_rows_outside_narrower_loan_filters_are_excluded(development, change):
    rows = [row(), row(total_loan_costs="999999", **change)]
    result = api().compare_held_out_costs(rows, frozen=freeze(development))
    assert result["raw_originated_records"] == 2
    assert result["narrower_originated_records"] == 1
    assert result["excluded_by_loan_filters"] == 1
    assert result["held_out_by_purpose"]["31"]["q_distribution"]["maximum"] == .01


@pytest.mark.parametrize("change", [
    {"activity_year": "2023"}, {"state_code": "OH"},
    {"loan_purpose": "1"}, {"action_taken": "2"},
])
def test_wrong_held_out_query_scope_is_rejected(development, change):
    with pytest.raises(ValueError):
        api().compare_held_out_costs([row(**change)], frozen=freeze(development))


@pytest.mark.parametrize("key", [
    "protocol_sha256", "profile_sha256", "frozen_cutoffs", "freeze_integrity_sha256", "scenarios",
])
def test_missing_frozen_metadata_is_rejected_before_comparison(development, key):
    frozen = freeze(development)
    frozen.pop(key)
    with pytest.raises(ValueError):
        api().compare_held_out_costs(held_out_rows(), frozen=frozen)


def test_tampered_frozen_cutoffs_are_rejected_before_comparison(development):
    frozen = freeze(development)
    frozen["frozen_cutoffs"]["2022"]["31"]["p50"] = .99
    with pytest.raises(ValueError):
        api().compare_held_out_costs(held_out_rows(), frozen=frozen)


def test_empty_ratio_population_preserves_missingness_in_shares(development):
    result = api().compare_held_out_costs([row(total_loan_costs="Exempt")], frozen=freeze(development))
    assert result["held_out_by_purpose"]["31"]["q_distribution"]["records"] == 0
    assert result["held_out_by_purpose"]["31"]["q_distribution"]["quantiles"] is None
    for comparison in result["comparisons"]:
        assert all(value is None for value in comparison["proportions"].values())
