from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from manuscript_reference_audit import expand_source, semantic_errors

def test_reject_equation_label_attached_to_section():
    assert semantic_errors(r'\section{Model}\label{eq:beta1} See \eqref{eq:beta1}.')

def test_reject_table_label_on_wrong_object():
    assert semantic_errors(r'\section{Discussion}\label{tab:wal} Table~\ref{tab:wal}')

def test_actual_equation_and_table_pass():
    s=r'\begin{equation}x=1\label{eq:x}\end{equation}\begin{table}\caption{Life}\label{tab:wal}\end{table} Equation~\eqref{eq:x} Table~\ref{tab:wal}'
    assert not semantic_errors(s)

def test_current_destinations_and_shared_editions():
    s=expand_source(ROOT/'paper/final/paper_final_v1.tex')
    assert not semantic_errors(s)
    for key in ['eq:beta1','eq:pathB','eq:default','tab:wal']:
        assert ('\\label{'+key+'}') in s
    long=expand_source(ROOT/'paper/final/paper_final_v1_long_abstract.tex')
    assert s.split('\\end{abstract}',1)[1]==long.split('\\end{abstract}',1)[1]
