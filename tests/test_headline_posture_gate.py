"""Regression checks for the revised abstract's evidence ordering."""
from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import (  # noqa: E402
    ABSTRACT_BOUNDS,
    ABSTRACT_POSTURE,
    TEX,
    abstract_posture_check,
)


def _abstract(tex: str) -> str:
    i = tex.index(ABSTRACT_BOUNDS[0]) + len(ABSTRACT_BOUNDS[0])
    j = tex.index(ABSTRACT_BOUNDS[1], i)
    return tex[i:j]


def _replace_abstract(tex: str, new: str) -> str:
    old = _abstract(tex)
    assert new != old
    return tex.replace(old, new, 1)


@pytest.fixture(scope="module")
def tex() -> str:
    return TEX.read_text()


def test_shipped_manuscript_passes(tex):
    ok, info = abstract_posture_check(tex)
    assert ok, info
    assert info["i_point"] < info["i_range"]


@pytest.mark.parametrize("key", sorted(ABSTRACT_POSTURE))
def test_removing_evidence_span_fails(tex, key):
    old = _abstract(tex)
    span = ABSTRACT_POSTURE[key]
    assert span in old
    ok, _ = abstract_posture_check(_replace_abstract(tex, old.replace(span, "", 1)))
    assert not ok


def test_promoting_conditional_interval_ahead_of_anchor_fails(tex):
    old = _abstract(tex)
    point = ABSTRACT_POSTURE["paired_anchor"]
    interval = ABSTRACT_POSTURE["floor_interval"]
    changed = old.replace(point, "__POINT__", 1).replace(interval, point, 1).replace("__POINT__", interval, 1)
    ok, info = abstract_posture_check(_replace_abstract(tex, changed))
    assert not ok and not info["ordered"] and not info["missing"]


def test_dropping_interval_condition_fails(tex):
    old = _abstract(tex)
    changed = old.replace("at the central imported response", "", 1)
    ok, _ = abstract_posture_check(_replace_abstract(tex, changed))
    assert not ok


def test_commented_out_assumption_qualification_fails(tex):
    old = _abstract(tex)
    span = ABSTRACT_POSTURE["moving_share"]
    changed = old.replace(span, "% " + span, 1)
    ok, _ = abstract_posture_check(_replace_abstract(tex, changed))
    assert not ok


def test_unrelated_prose_edit_passes(tex):
    old = _abstract(tex)
    changed = old.replace("I combine SOMA holdings", "This study combines SOMA holdings", 1)
    ok, info = abstract_posture_check(_replace_abstract(tex, changed))
    assert ok, info
