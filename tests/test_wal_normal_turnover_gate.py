"""Battery for gate #108 (round-30 D2: the normal-turnover WAL row).

Same convention as the #105-#107 batteries: every mutation is verified
non-vacuous before it is applied. The artifact-perturbation tests exercise the
anti-drift direction (a moved artifact fails against the unmoved tex) and the
live cross-artifact anchor tie.
"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import wal_normal_turnover_check  # noqa: E402

TEX = (ROOT / "paper" / "final" / "paper_final_v1.tex").read_text()
VARIANT = (ROOT / "paper" / "final"
           / "paper_final_v1_long_abstract.tex").read_text()
WNT = json.loads((ROOT / "hazard" / "data"
                  / "wal_normal_turnover_results.json").read_text())
OOS = json.loads((ROOT / "hazard" / "data"
                  / "oos_identification_results.json").read_text())
ROW = ("Baseline turnover floor, off-window headline read (4.99\\%) "
       "& 9.5 & 8.6 \\\\")
STALE = "No row is printed at a normal-turnover speed."


def test_gate_passes_on_the_manuscript():
    ok, info = wal_normal_turnover_check(TEX, WNT, OOS)
    assert ok, f"gate #108 fails on the shipped manuscript: {info}"


def test_variant_carries_the_row():
    ok, info = wal_normal_turnover_check(VARIANT, WNT, OOS)
    assert ok, f"gate #108 fails on the long-abstract variant: {info}"


def test_row_removal_fails():
    assert ROW in TEX, "row not in the manuscript (vacuous mutation)"
    ok, _ = wal_normal_turnover_check(TEX.replace(ROW, ""), WNT, OOS)
    assert not ok


def test_stale_sentence_restored_fails():
    assert STALE not in TEX
    restored = TEX.replace(
        "The turnover-floor row is the normal-turnover counterpart.", STALE)
    ok, _ = wal_normal_turnover_check(restored, WNT, OOS)
    assert not ok


def test_perturbed_artifact_fails():
    w = copy.deepcopy(WNT)
    w["rows"]["turnover_floor_oow_mid"]["wal_june_2022"] += 0.1
    ok, _ = wal_normal_turnover_check(TEX, w, OOS)
    assert not ok, "a drifted artifact must fail against the unmoved tex"


def test_anchor_drift_fails():
    w = copy.deepcopy(WNT)
    w["spec"]["anchor_full_precision_pct"] = (
        OOS["instrument1_oow_floor"]["defensible_clean_floor"]["clean_lo_pct"])
    ok, _ = wal_normal_turnover_check(TEX, w, OOS)
    assert not ok, "the cross-artifact anchor tie must be live"


def test_parity_false_fails():
    w = copy.deepcopy(WNT)
    w["parity"]["nine_rows_bit_identical"] = False
    ok, _ = wal_normal_turnover_check(TEX, w, OOS)
    assert not ok, "a landing may not survive its own parity failure"


def test_run_tag_indexed():
    assert TEX.count("\\texttt{wal\\_normal\\_turnover}") >= 1
    assert VARIANT.count("\\texttt{wal\\_normal\\_turnover}") >= 1
