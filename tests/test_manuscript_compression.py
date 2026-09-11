"""Structural safeguards for the shortened manuscript package."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "paper" / "final" / "paper_final_v1.tex"
VARIANT = ROOT / "paper" / "final" / "paper_final_v1_long_abstract.tex"
MANIFEST = ROOT / "paper" / "final" / "compression_manifest.json"

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
