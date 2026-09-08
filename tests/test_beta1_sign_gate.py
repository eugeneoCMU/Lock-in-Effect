"""Gate #109: the manuscript must print beta_1 under ONE sign convention.

Round 32 (C-R4). The panel found $0.069$ in tab:params and $-0.0686$ in
tab:lowband for the same parameter at the same delta, and proposed "flip the
printed signs". Reading the source first showed the fix had to be narrower than
that: eq:beta1 defines beta_1 WITH a leading minus, so it is positive under the
manuscript's own definition, and eq:pathB uses the signed gap, so a positive
beta_1 suppresses prepayment -- self-consistent. tab:params was already right.
The production helper hazard/literature_hazard.py:rothstein_beta1 returns
ln(h_shocked/h_base) WITHOUT that minus, hence negative, which is what
tab:lowband was printing. Neither is a computational error; the manuscript was
printing one symbol under two conventions, and tab:lowband was the outlier.

So this gate does not assert a sign. It asserts AGREEMENT: whatever convention
tab:params states, every tab:lowband cell follows it. That is the property a
referee's objection was actually about, and it is the property that stays true
if a later round decides to restate eq:beta1 the other way.
"""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_s = importlib.util.spec_from_file_location("lg", ROOT / "tools" / "liveness_gates.py")
lg = importlib.util.module_from_spec(_s)
_s.loader.exec_module(lg)
TEX = (ROOT / "paper" / "final" / "paper_final_v1.tex").read_text()


def test_beta1_signs_agree_across_tables():
    ok, info = lg.beta1_sign_check(TEX)
    assert ok, info


def test_gate_catches_a_reintroduced_negative_column():
    mutated = TEX.replace("6.50 & $0.0686$", "6.50 & $-0.0686$", 1)
    assert mutated != TEX, "anchor not found — update the test's anchor"
    ok, _ = lg.beta1_sign_check(mutated)
    assert not ok, "the gate accepted a sign disagreement"


def test_gate_catches_a_flipped_tab_params_cell():
    """The disagreement is symmetric: flipping the reference cell must fail too,
    or the gate is only checking one table against a hardcoded expectation."""
    mutated = TEX.replace(r"$\beta_1$ (central) & $0.069$", r"$\beta_1$ (central) & $-0.069$", 1)
    assert mutated != TEX, "anchor not found — update the test's anchor"
    ok, _ = lg.beta1_sign_check(mutated)
    assert not ok, "the gate accepted a flipped reference cell"


def test_gate_reports_what_it_found():
    """A gate that cannot say which cells it read cannot be debugged when it
    fails, and this table's rows move between rounds."""
    _, info = lg.beta1_sign_check(TEX)
    assert info["params_sign"] == 1
    assert len(info["lowband"]) == 9, info
    assert all(v > 0 for v in info["lowband"]), info


def test_replicator_note_records_the_opposite_code_convention():
    """The honest half of the fix: harmonising the table without telling a
    replicator that the code returns the other sign just moves the surprise."""
    assert "rothstein" in TEX
    i = TEX.find(r"\label{tab:lowband}")
    assert i != -1
    j = TEX.find(r"\end{threeparttable}", i)
    assert "rothstein" in TEX[i:j], "the note is not inside tab:lowband's float"
