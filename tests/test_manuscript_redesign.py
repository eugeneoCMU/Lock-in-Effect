"""Publication-facing invariants for the mortgage-lock-in redesign."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / "paper/final/paper_final_v1.tex"
LONG = ROOT / "paper/final/paper_final_v1_long_abstract.tex"
MAIN = ROOT / "paper/final/journal_main_v2.tex"
MANIFEST = ROOT / "paper/final/manuscript_redesign_manifest.json"


def _section(text: str, heading: str, next_heading: str) -> str:
    """Return one manuscript section without coupling tests to full paragraphs."""
    start = text.index(heading)
    end = text.index(next_heading, start)
    return text[start:end]


def _abstract(path: Path) -> str:
    text = path.read_text()
    start = text.index(r"\begin{abstract}")
    end = text.index(r"\end{abstract}", start)
    return text[start:end]


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


def test_main_exposes_referee_critical_model_inputs_and_construct_bracket():
    text = MAIN.read_text()
    for phrase in (
        r"5.5--7.7\% quarterly decline per 100 basis points",
        "$\\beta=0.0686$",
        "$\\mu=0.25/0.50/1.00$",
        "$+1.8/+3.4/+5.6$ points",
        "No termination-reason field",
    ):
        assert phrase in text


def test_main_separates_sampling_inference_from_assumption_sensitivity():
    text = MAIN.read_text()
    assert "Sampling layer with a coverage interpretation" in text
    assert "Assumption or calibration sensitivity without a coverage interpretation" in text


def test_main_quantifies_floor_provenance_and_portfolio_transport():
    text = MAIN.read_text()
    for phrase in (
        r"4.70--5.33\%",
        r"4.991\%",
        "Quantitative consequence",
        "Behavioral coverage gap",
        r"approximately 9\%",
    ):
        assert phrase in text


def test_main_states_public_soma_data_boundary_directly():
    text = MAIN.read_text()
    assert "do not separately report monthly gross principal receipts" in text
    assert "reproduces the holdings change rather than independently identifying gross remittances" in text


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
        "\\section{Institutional Background and Related Literature}",
        "\\section{Data and Benchmark Construction}",
        "\\section{Empirical Methodology}",
        "\\section{Results}",
        "\\section{Robustness and External Validation}",
        "\\section{Discussion and Policy Implications}",
        "\\section{Conclusion}",
    ]
    positions = [text.index(h) for h in headings]
    assert positions == sorted(positions)


def test_main_uses_descriptive_subsections_under_conventional_sections():
    text = MAIN.read_text()
    for heading in (
        "\\subsection{Contribution Relative to the Existing Literature}",
        "\\subsection{The expectations-relative benchmark}",
        "\\subsection{Loan-level prepayment model}",
        "\\subsection{Calibration and simulation}",
        "\\subsection{Baseline-turnover specifications}",
        "\\subsection{Validation boundaries}",
        "\\subsection{Hard-maximum baseline result}",
        "\\subsection{Functional-form comparison}",
        "\\subsection{Uncertainty and sensitivity}",
        "\\subsection{Distribution across borrowers and loan cohorts}",
        "\\subsection{Turnover-floor measurement and transport}",
        "\\subsection{Alternative model comparison}",
        "\\subsection{Monthly validation failure}",
    ):
        assert heading in text


def test_introduction_orders_claims_by_evidence_status():
    intro = _section(
        MAIN.read_text(),
        r"\section{Introduction}",
        r"\section{Institutional Background and Related Literature}",
    )
    markers = (
        r"\$764.748 billion",
        r"\$87.8 billion",
        "imported rate response",
        "$+1.9$ to $+9.1$",
        "$+2.1$ to $+13.2$",
        "additive",
        "plausible portfolio cash flows",
    )
    positions = [intro.index(marker) for marker in markers]
    assert positions == sorted(positions)
    assert "allocation-dependent" in intro
    assert "may already incorporate some lock-in" in intro
    assert "spring-2022 rate path below the realized path" in intro


def test_results_lead_with_interval_then_anchor_then_assumption_sensitivity():
    results = _section(
        MAIN.read_text(),
        r"\section{Results}",
        r"\section{Robustness and External Validation}",
    )
    markers = (
        "$+1.9$ to $+9.1$",
        "5.6-point lock-in marginal",
        "$+2.1$ to $+13.2$",
        "additive",
    )
    positions = [results.index(marker) for marker in markers]
    assert positions == sorted(positions)


def test_main_labels_each_evidence_layer_and_monthly_boundary():
    text = MAIN.read_text()
    for marker in (
        "cap-relative accounting gap",
        "allocation-dependent",
        "imported rate response",
        "calibrated turnover floor",
        "model-based marginal",
        "model-based within-sample decompositions",
        "sampling uncertainty",
        "without a coverage interpretation",
        "not an estimate of monthly timing",
    ):
        assert marker in text


def test_main_rejects_unqualified_overclaims():
    text = MAIN.read_text()
    forbidden = (
        r"lock-in caused (?:the )?\$764\.748 billion",
        r"\$\+1\.9\$ to \$\+9\.1\$[^.]{0,100}total uncertainty",
        r"Fannie[^.]{0,120}independent causal validation",
        r"subgroup[^.]{0,120}(?:measures|estimates) welfare",
        r"model predicts monthly runoff",
    )
    for pattern in forbidden:
        assert re.search(pattern, text, flags=re.IGNORECASE) is None

    for match in re.finditer(r"91\.3\\%", text):
        local = text[max(0, match.start() - 240):match.end() + 240]
        assert "85.7\\%" in local


def test_both_abstracts_lead_with_sampling_then_anchor_then_assumptions():
    for path in (CANON, LONG):
        abstract = _abstract(path)
        markers = (
            "$+1.9$ to $+9.1$",
            "$+5.6$",
            "$+2.1$ to $+13.2$",
            "$+11.2$",
        )
        positions = [abstract.index(marker) for marker in markers]
        assert positions == sorted(positions), path
        assert "sampling uncertainty" in abstract
        assert "interior anchor" in abstract
        assert "without a coverage interpretation" in abstract
        assert "allocation-dependent" in abstract


def test_coverage_table_reserves_space_for_approximate_share():
    text = MAIN.read_text()
    assert r"\begin{tabular}{@{}p{3.1cm}p{2.3cm}p{9.3cm}@{}}" in text
