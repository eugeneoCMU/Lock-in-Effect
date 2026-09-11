"""Structural safeguards for the shortened manuscript package."""

import json
import importlib.util
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "paper" / "final" / "paper_final_v1.tex"
VARIANT = ROOT / "paper" / "final" / "paper_final_v1_long_abstract.tex"
SUBMISSION = ROOT / "paper" / "final" / "paper_final_v1_submission.tex"
SUBMISSION_VARIANT = (
    ROOT / "paper" / "final" / "paper_final_v1_submission_long_abstract.tex"
)
MANIFEST = ROOT / "paper" / "final" / "compression_manifest.json"
SUPPLEMENT = ROOT / "paper" / "final" / "technical_replication_supplement.tex"
ARCHIVE = ROOT / "paper" / "final" / "technical_replication_archive.tex"

_VALIDATOR_SPEC = importlib.util.spec_from_file_location(
    "tex_validate", ROOT / "tools" / "tex_validate.py"
)
TEX_VALIDATE = importlib.util.module_from_spec(_VALIDATOR_SPEC)
_VALIDATOR_SPEC.loader.exec_module(TEX_VALIDATE)

ALLOWED_DISPOSITIONS = {
    "main",
    "appendix",
    "supplement",
    "delete-duplicate",
    "delete-obsolete",
}


def source_section_labels(text):
    return set(
        re.findall(
            r"\\(?:section|subsection|subsubsection)\{[^}]+\}\\label\{([^}]+)\}",
            text,
        )
    )


def section_span(text, start_label, end_label):
    start = text.index(r"\label{" + start_label + "}")
    end = text.index(r"\label{" + end_label + "}", start)
    return text[start:end]


def prose_word_count(text):
    text = re.sub(r"\\iffalse.*?\\fi", " ", text, flags=re.DOTALL)
    text = re.sub(r"%.*", " ", text)
    text = re.sub(r"\\(?:cite\w*|ref|eqref|label)\{[^}]*\}", " ", text)
    text = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^]]*\])?", " ", text)
    text = re.sub(r"[{}$&_^~\\]", " ", text)
    return len(re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*", text))


def load_manifest():
    return json.loads(MANIFEST.read_text())


def test_manifest_covers_every_source_section():
    labels = source_section_labels(CANONICAL.read_text())
    covered = {block["label"] for block in load_manifest()["source_blocks"]}
    assert labels <= covered


def test_every_source_block_has_a_reasoned_disposition():
    blocks = load_manifest()["source_blocks"]
    assert blocks
    assert all(block["disposition"] in ALLOWED_DISPOSITIONS for block in blocks)
    assert all(block["reason"].strip() for block in blocks)
    assert all(block["destination_label"].strip() for block in blocks)


def test_manifest_declares_approved_page_targets():
    targets = load_manifest()["targets"]
    assert targets == {"main_pages_max": 42, "appendix_pages_max": 15}


def test_manifest_declares_verified_source_page_counts():
    source = load_manifest()["source_pdf_pages"]
    assert source == {"combined": 147, "main": 99, "appendix": 48}


def test_protected_claims_have_patterns_and_allowed_destinations():
    claims = load_manifest()["protected_claims"]
    assert claims
    assert len({claim["id"] for claim in claims}) == len(claims)
    for claim in claims:
        assert claim["patterns"]
        assert set(claim["required_destination"]) <= {"main", "appendix"}


def test_current_manuscript_variants_have_the_same_structure():
    canonical_labels = source_section_labels(CANONICAL.read_text())
    variant_labels = source_section_labels(VARIANT.read_text())
    assert canonical_labels == variant_labels


def test_submission_sources_are_physically_compressed_and_synchronized():
    canonical = SUBMISSION.read_text()
    variant = SUBMISSION_VARIANT.read_text()
    assert r"\iffalse" not in canonical
    assert r"\iffalse" not in variant
    archive_lines = len(ARCHIVE.read_text().splitlines())
    assert len(canonical.splitlines()) < 0.65 * archive_lines
    assert len(variant.splitlines()) < 0.65 * archive_lines
    assert source_section_labels(canonical) == source_section_labels(variant)


def test_submission_sources_retain_core_destinations():
    labels = source_section_labels(SUBMISSION.read_text())
    assert {
        "sec:intro",
        "sec:method",
        "sec:abm",
        "sec:hazard",
        "sec:robustness",
        "sec:discussion",
        "sec:conclusion",
        "app:benchmark",
        "app:params",
    } <= labels


def test_submission_carries_reader_facing_evidence_tables():
    text = SUBMISSION.read_text()
    for label in (
        "tab:headline-compact",
        "tab:uncertainty-compact",
        "tab:danish-compact",
    ):
        assert rf"\label{{{label}}}" in text
    for row in (
        "Cap-relative benchmark",
        "Production ABM",
        "Path B central, off-window floor",
        r"Rate-inelastic null, $\beta_1=0$",
        "Lock-in marginal, off-window floor",
    ):
        assert row in text


def test_submission_keeps_uncertainty_dimensions_separate():
    text = SUBMISSION.read_text()
    assert "Floor-read sampling uncertainty" in text
    assert "Elasticity calibration range" in text
    assert "Functional-form range" in text
    assert "no coverage interpretation" in text
    assert "carries calibration, floor, and functional-form uncertainty" not in text


def test_submission_appendix_contains_evaluable_specification():
    text = SUBMISSION.read_text()
    required = (
        r"h^{\mathrm{prep}}_{i,t}",
        r"h^{\mathrm{def}}_{i,t}",
        "40{,}234",
        "1{,}683{,}124",
        "tab:floor-elasticity-grid",
        "tab:floor-form-compact",
        "Fannie Mae reproduction is a robustness check, not an outside test",
        "wrong-month rotations",
        "Path~A is excluded from every headline range",
        "10{,}000 heterogeneous households",
    )
    for item in required:
        assert item in text


def test_submission_variants_differ_only_in_abstract():
    def without_abstract(text):
        return re.sub(
            r"\\begin\{abstract\}.*?\\end\{abstract\}",
            "ABSTRACT",
            text,
            flags=re.DOTALL,
        )

    assert without_abstract(SUBMISSION.read_text()) == without_abstract(
        SUBMISSION_VARIANT.read_text()
    )


def test_technical_supplement_is_standalone_and_scoped():
    text = SUPPLEMENT.read_text()
    assert r"\title{Technical and Replication Supplement" in text
    assert r"\begin{document}" in text
    assert r"\end{document}" in text
    assert "does not add evidence to the publication-facing paper" in text


def test_supplement_declares_every_manifest_destination():
    text = SUPPLEMENT.read_text()
    destinations = {
        block["destination_label"]
        for block in load_manifest()["source_blocks"]
        if block["disposition"] == "supplement"
    }
    assert destinations
    assert destinations <= source_section_labels(text)


def test_introduction_meets_approved_word_budget():
    text = CANONICAL.read_text()
    introduction = section_span(text, "sec:intro", "sec:lit")
    assert prose_word_count(introduction) <= 1500


def test_literature_review_meets_approved_word_budget():
    text = CANONICAL.read_text()
    literature = section_span(text, "sec:lit", "sec:method")
    assert prose_word_count(literature) <= 1500


def test_validator_ignores_labels_inside_disabled_migration_blocks():
    source = r"\section{Live}\label{sec:x}\iffalse\label{sec:x}\fi"
    active = TEX_VALIDATE.strip_false_blocks(source)
    assert TEX_VALIDATE.ref_check(active) == []
