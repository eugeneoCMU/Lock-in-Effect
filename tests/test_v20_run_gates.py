"""Perturbation battery for gates #123/#124/#125 (the V20 spec-run companions).

The three gates are live cross-artifact ties: each formats the printed sentence
from the artifact's own values and checks the artifact's landing branch and
runner parity gates. The battery exercises both failure directions per gate —
the sentence leaving the manuscript, and the artifact moving under a frozen
sentence — plus the branch consistency case, so a re-run that lands on a
different branch cannot leave stale prose standing.

Follows the standing rules: imports the shipped rule rather than redefining it;
perturbs copies, never the real artifacts.
"""
from __future__ import annotations

import copy
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import (  # noqa: E402
    CN_RESULTS,
    FCC_RESULTS,
    NFI_RESULTS,
    TEX,
    compounding_null_check,
    fewcluster_coverage_check,
    null_floor_interval_gate_check,
)


@pytest.fixture(scope="module")
def tex() -> str:
    return TEX.read_text()


@pytest.fixture(scope="module")
def cn() -> dict:
    return json.loads(CN_RESULTS.read_text())


@pytest.fixture(scope="module")
def nfi() -> dict:
    return json.loads(NFI_RESULTS.read_text())


@pytest.fixture(scope="module")
def fcc() -> dict:
    return json.loads(FCC_RESULTS.read_text())


# ---------------------------------------------------------------- gate #123
def test_cn_passes_on_real_tree(tex, cn):
    ok, info = compounding_null_check(tex, cn)
    assert ok, info


def test_cn_fails_when_sentence_removed(tex, cn):
    mutated = tex.replace("the marginal is $+", "the marginal is $-")
    ok, info = compounding_null_check(mutated, cn)
    assert not ok and not info["marginal_span"], info


def test_cn_fails_when_artifact_moves(tex, cn):
    art = copy.deepcopy(cn)
    art["compounding_consistent"]["marginal_cc_pp"] += 0.25
    ok, info = compounding_null_check(tex, art)
    assert not ok and not info["marginal_span"], info


def test_cn_fails_on_non_L1_branch(tex, cn):
    art = copy.deepcopy(cn)
    art["landing_branch"] = "L2_companion_figure"
    ok, info = compounding_null_check(tex, art)
    assert not ok and not info["branch_L1"], info


def test_cn_fails_if_signing_violated(tex, cn):
    art = copy.deepcopy(cn)
    art["committed_anchors"]["marginal_pp"] = (
        art["compounding_consistent"]["marginal_cc_pp"] - 0.5
    )
    ok, info = compounding_null_check(tex, art)
    assert not ok and not info["signing_held"], info


# ---------------------------------------------------------------- gate #124
def test_nfi_passes_on_real_tree(tex, nfi):
    ok, info = null_floor_interval_gate_check(tex, nfi)
    assert ok, info


def test_nfi_fails_when_one_of_two_spans_removed(tex, nfi):
    lo, hi = nfi["binding_interval_pct"]
    span = f"$[{lo:.1f}, {hi:.1f}]$\\%"
    assert tex.count(span) >= 2
    mutated = tex.replace(span, "$[0.0, 0.0]$\\%", 1)
    ok, info = null_floor_interval_gate_check(mutated, nfi)
    assert not ok and not info["span_count_ge_2"], info


def test_nfi_fails_when_interval_moves(tex, nfi):
    art = copy.deepcopy(nfi)
    art["binding_interval_pct"] = [art["binding_interval_pct"][0] - 1.0,
                                   art["binding_interval_pct"][1]]
    ok, info = null_floor_interval_gate_check(tex, art)
    assert not ok, info


def test_nfi_fails_when_offnode_tolerance_breached(tex, nfi):
    art = copy.deepcopy(nfi)
    art["gates"]["G_B1b_offnode"]["max_err_pp"] = (
        art["gates"]["G_B1b_offnode"]["tol_pp"] * 2
    )
    ok, info = null_floor_interval_gate_check(tex, art)
    assert not ok and not info["offnode_within_tol"], info


# ---------------------------------------------------------------- gate #125
def test_fcc_passes_on_real_tree(tex, fcc):
    ok, info = fewcluster_coverage_check(tex, fcc)
    assert ok, info


def test_fcc_fails_when_coverage_sentence_removed(tex, fcc):
    g = fcc["cells"]["gaussian"]["coverage_pct"]
    t5 = fcc["cells"]["t5"]["coverage_pct"]
    span = (f"covers {g['restricted_webb']:.1f}\\% under Gaussian and "
            f"{t5['restricted_webb']:.1f}\\% under $t_5$")
    assert span in tex
    ok, info = fewcluster_coverage_check(tex.replace(span, ""), fcc)
    assert not ok and not info["spans_present"], info


def test_fcc_fails_when_coverage_moves(tex, fcc):
    art = copy.deepcopy(fcc)
    art["cells"]["gaussian"]["coverage_pct"]["restricted_webb"] -= 1.0
    ok, info = fewcluster_coverage_check(tex, art)
    assert not ok and not info["spans_present"], info


def test_fcc_fails_on_non_L1_branch(tex, fcc):
    art = copy.deepcopy(fcc)
    art["landing_branch"] = "L2_bm_sandwich_binding"
    ok, info = fewcluster_coverage_check(tex, art)
    assert not ok and not info["branch_L1"], info


def test_fcc_fails_when_oracle_out_of_bounds(tex, fcc):
    art = copy.deepcopy(fcc)
    first = next(iter(art["gates"]["G_C1_oracle"]))
    art["gates"]["G_C1_oracle"][first] = 90.0
    ok, info = fewcluster_coverage_check(tex, art)
    assert not ok and not info["oracle_bounds"], info
