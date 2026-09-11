"""Publication-facing invariants for the mortgage-lock-in redesign."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / "paper/final/paper_final_v1.tex"
LONG = ROOT / "paper/final/paper_final_v1_long_abstract.tex"
MAIN = ROOT / "paper/final/journal_main_v2.tex"
MANIFEST = ROOT / "paper/final/manuscript_redesign_manifest.json"


def test_manifest_has_reasoned_dispositions():
    data = json.loads(MANIFEST.read_text())
    allowed = {"main", "appendix", "records", "delete-duplicate", "delete-obsolete"}
    blocks = data["source_blocks"]
    assert blocks
    assert all(b["disposition"] in allowed for b in blocks)
    assert all(b["destination"].strip() and b["reason"].strip() for b in blocks)
    for block in blocks:
        if block["disposition"].startswith("delete-"):
            assert block["destination"], block


def test_title_is_unchanged_in_both_editions():
    title = "Mortgage Lock-In and the Federal Reserve's Quantitative Tightening Shortfall"
    assert f"\\title{{{title}}}" in CANON.read_text()
    assert f"\\title{{{title}}}" in LONG.read_text()


def test_both_editions_use_the_shared_journal_body():
    pin = "\\input{journal_main_v2}"
    assert pin in CANON.read_text()
    assert pin in LONG.read_text()


def test_main_distinguishes_the_three_empirical_objects():
    text = MAIN.read_text()
    for phrase in (
        "Cap-relative MBS runoff shortfall",
        "Expectations-relative shortfall",
        "Lock-in marginal",
        "\\$764.748 billion",
        "\\$87.8 billion",
    ):
        assert phrase in text


def test_main_states_scope_and_identification_boundary():
    canon = CANON.read_text()
    main = MAIN.read_text()
    assert "not the performance of the Federal Reserve's overall balance-sheet reduction program" in canon
    assert "model-based portfolio decomposition" in canon
    assert "does not claim to identify a new causal elasticity" in main
    assert "No estimator explains the empirical month-to-month path" in main


def test_both_floor_forms_are_first_order_main_assumptions():
    text = MAIN.read_text()
    assert "h^{\\max}_{it}=\\max" in text
    assert "h^{\\mathrm{add}}_{it}=f_t+h^{R}_{it}" in text
    assert "The paper therefore reports the production result and the cross-form implication together" in text


def test_adverse_and_policy_limits_survive_in_main():
    text = MAIN.read_text()
    for phrase in (
        "$R^2=-6.984$",
        "does not isolate a clean ABM-versus-hazard paradigm effect",
        "$-\\$51.0$ billion",
        "does not estimate the cost of migrating the U.S. issuance architecture",
    ):
        assert phrase in text


def test_main_has_approved_section_order():
    text = MAIN.read_text()
    headings = [
        "\\section{Introduction}",
        "\\section{Mortgage Lock-In and Federal Reserve MBS Runoff}",
        "\\section{Data and Empirical Benchmarks}",
        "\\section{Loan-Level Decomposition}",
        "\\section{Results: The Lock-In Marginal}",
        "\\section{Functional Form, Calibration, and External Validation}",
        "\\section{Policy Implications}",
        "\\section{Conclusion}",
    ]
    positions = [text.index(h) for h in headings]
    assert positions == sorted(positions)
