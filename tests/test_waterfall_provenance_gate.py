"""Battery for gate #110 (finding 5: waterfall stage provenance)."""
import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import waterfall_provenance_check  # noqa: E402

TEX = (ROOT / "paper" / "v18" / "revised_paper_v18.tex").read_text()
VARIANT = (ROOT / "paper" / "v18"
           / "revised_paper_v18_long_abstract.tex").read_text()
STAGES = json.loads((ROOT / "figures" / "fig3_stage_levels.json").read_text())
PREFOLDIN = json.loads((ROOT / "abm" / "data" / "runs" / "run-2026-07-04"
                        / "manifest.json").read_text())
FOLDIN = json.loads((ROOT / "abm" / "data" / "runs"
                     / "run-2026-07-04-15yr-foldin" / "manifest.json").read_text())
BERGER = json.loads((ROOT / "abm" / "data" / "runs" / "run-2026-07-05-berger"
                     / "manifest.json").read_text())

RETIRED = (
    "Stage levels from the frozen run manifests catalogued in the "
    "run ledger"
)


def test_gate_passes_on_the_manuscript():
    ok, info = waterfall_provenance_check(
        TEX, STAGES, PREFOLDIN, FOLDIN, BERGER)
    assert ok, f"gate #110 fails on the shipped manuscript: {info}"


def test_variant_carries_the_landing():
    ok, info = waterfall_provenance_check(
        VARIANT, STAGES, PREFOLDIN, FOLDIN, BERGER)
    assert ok, f"gate #110 fails on the long-abstract variant: {info}"


def test_disclosure_removal_fails():
    span = ("committed diagnostic sequence in "
            "\\texttt{figures/fig3\\_stage\\_levels.json}")
    assert span in TEX
    ok, _ = waterfall_provenance_check(
        TEX.replace(span, ""), STAGES, PREFOLDIN, FOLDIN, BERGER)
    assert not ok


def test_retired_caption_restored_fails():
    assert RETIRED not in TEX
    restored = TEX.replace(
        "The first four stages are the committed diagnostic sequence",
        RETIRED + ". The first four stages are the committed diagnostic "
        "sequence",
    )
    ok, info = waterfall_provenance_check(
        restored, STAGES, PREFOLDIN, FOLDIN, BERGER)
    assert not ok
    assert RETIRED in info["present_retired"]


def test_early_stage_literal_removal_fails():
    lit = "71.1\\%"
    assert lit in TEX  # appears in caption and body; both must stay consistent
    ok, _ = waterfall_provenance_check(
        TEX.replace(lit, "XX\\%"), STAGES, PREFOLDIN, FOLDIN, BERGER)
    assert not ok


def test_manifest_tag_removal_fails():
    tag = "\\texttt{run-2026-07-04-15yr-foldin}"
    assert tag in TEX
    ok, _ = waterfall_provenance_check(
        TEX.replace(tag, "\\texttt{run-MISSING}"),
        STAGES, PREFOLDIN, FOLDIN, BERGER)
    assert not ok


def test_stage_json_nondistinct_fails():
    s = copy.deepcopy(STAGES)
    s["stages"][1]["share_pct"] = s["stages"][0]["share_pct"]
    ok, info = waterfall_provenance_check(
        TEX, s, PREFOLDIN, FOLDIN, BERGER)
    assert not ok
    assert info["distinct_ok"] is False


def test_manifest_drift_fails():
    f = copy.deepcopy(FOLDIN)
    f["metrics"]["dollars_b"]["share_explained_pct"] = 99.9
    ok, _ = waterfall_provenance_check(
        TEX, STAGES, PREFOLDIN, f, BERGER)
    assert not ok
