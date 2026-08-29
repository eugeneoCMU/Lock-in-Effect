"""The manuscript states how many standalone pre-committed specifications ship in specs/.

That sentence was written when the count was eleven and silently went stale as the round added
nine more; no gate pinned it, so the suite stayed green over a false claim in a paper that
publishes the very directory refuting it. This test ties the printed number to the directory.

It counts FILES, deliberately. The earlier sentence said "Eleven runs" while counting files, which
was true only while each spec covered exactly one run -- the round-28 specs cover several apiece
and three R32 specs cover none. Counting files is the claim that can actually be checked.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPECS = ROOT / "specs"
_REPLAPPX = (ROOT / "paper" / "final" / "replication_appendices.tex").read_text()
TEX = [ROOT / "paper" / "final" / "paper_final_v1.tex",
       ROOT / "paper" / "final" / "paper_final_v1_long_abstract.tex"]

NUMBER_WORDS = {
    10: "Ten", 11: "Eleven", 12: "Twelve", 13: "Thirteen", 14: "Fourteen", 15: "Fifteen",
    16: "Sixteen", 17: "Seventeen", 18: "Eighteen", 19: "Nineteen", 20: "Twenty",
    21: "Twenty-one", 22: "Twenty-two", 23: "Twenty-three", 24: "Twenty-four",
    25: "Twenty-five", 26: "Twenty-six", 27: "Twenty-seven", 28: "Twenty-eight",
    29: "Twenty-nine", 30: "Thirty",
}

CLAIM = re.compile(
    r"(\w[\w-]*) standalone pre-committed specifications in the replication package's")


def spec_file_count() -> int:
    return len(list(SPECS.glob("SPEC_*.md")))


@pytest.mark.parametrize("tex_path", TEX, ids=lambda p: p.name)
def test_printed_spec_count_matches_the_directory(tex_path: Path) -> None:
    n = spec_file_count()
    assert n in NUMBER_WORDS, (
        f"specs/ holds {n} SPEC files, outside this test's number-word table; extend "
        f"NUMBER_WORDS and update the manuscript sentence together")
    # V20 closing-session rescope: the claim sentence lives in app:verdicts,
    # migrated to replication_appendices.tex; each variant ships with it.
    hits = CLAIM.findall(tex_path.read_text() + _REPLAPPX)
    assert len(hits) == 1, (
        f"{tex_path.name}: expected exactly one spec-count claim, found {len(hits)}: {hits}")
    assert hits[0] == NUMBER_WORDS[n], (
        f"{tex_path.name} prints '{hits[0]} standalone pre-committed specifications' but "
        f"specs/ holds {n} SPEC files ('{NUMBER_WORDS[n]}'). Update the sentence in BOTH .tex "
        f"variants whenever a spec is added or removed.")


def test_both_variants_agree_on_the_count() -> None:
    words = [CLAIM.findall(p.read_text() + _REPLAPPX)[0] for p in TEX]
    assert len(set(words)) == 1, (
        f"the two manuscript variants disagree on the spec count: {words}")
