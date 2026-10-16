"""Schema/cutoff gates must fail before hidden outcomes enter an audit."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hazard"))
from freddie_raw_quarter_audit import schema_audit, audit_rows, replay_worker


def orig_line(loan="F17Q10000001"):
    c = [""] * 32
    for index, value in {0:"720",1:"201703",10:"100000",11:"80",12:"4.0",
                         15:"FRM",16:"PA",19:loan,21:"360"}.items():
        c[index] = value
    return "|".join(c) + "\n"


def perf_line(month="201701", balance="100000", age="0", zb="", loan="F17Q10000001"):
    c = [""] * 32
    for index, value in {0:loan,1:month,2:balance,3:"0",4:age,8:zb}.items():
        c[index] = value
    return "|".join(c) + "\n"


def test_width_mismatch_blocks_instead_of_truncating(tmp_path):
    o,p=tmp_path/"orig.txt",tmp_path/"perf.txt"
    o.write_text(orig_line())
    p.write_text(perf_line().strip()+"|unexpected\n")
    report, loans = schema_audit(o,p)
    assert not report["passed"]
    assert report["performance"]["width_counts"] == {33:1}


def test_schema_gate_supports_only_the_declared_quarter(tmp_path):
    o,p=tmp_path/'orig.txt',tmp_path/'perf.txt'
    o.write_text(orig_line('F20Q40000001'))
    p.write_text(perf_line(loan='F20Q40000001'))
    report,_=schema_audit(o,p,quarter='2020Q4')
    assert report['passed']
    wrong,_=schema_audit(o,p,quarter='2020Q3')
    assert not wrong['passed']


def test_duplicate_orig_ids_block_join_multiplication(tmp_path):
    o,p=tmp_path/"orig.txt",tmp_path/"perf.txt"
    o.write_text(orig_line()+orig_line())
    p.write_text(perf_line())
    report, loans=schema_audit(o,p)
    assert not report["passed"]
    assert report["origination"]["duplicate_ids"] == 1


def test_cutoff_precedes_all_outcome_parsing_and_missing_months_are_counted(tmp_path):
    o,p=tmp_path/"orig.txt",tmp_path/"perf.txt"
    o.write_text(orig_line())
    p.write_text(perf_line()+perf_line("201703","0","2","01")+
                 perf_line("202510","DO NOT PARSE","DO NOT PARSE","01"))
    schema, loans=schema_audit(o,p)
    assert schema["passed"]
    result, cells=audit_rows(p,loans)
    assert result["eligible_pre_cutoff_rows"] == 2
    assert result["invalid_balance_rows"] == 0
    assert result["missing_calendar_months"] == 1
    assert result["payoff_with_nonadjacent_prior_rows"] == 1
    assert sum(r["prepaid_upb"] for r in cells) == 100000


def test_unsorted_loan_history_uses_chronological_reference_and_audits_first_payoff(tmp_path):
    o,p=tmp_path/"orig.txt",tmp_path/"perf.txt"
    o.write_text(orig_line()+orig_line("F17Q10000002"))
    p.write_text(perf_line("201703","0","2","01")+perf_line("201701")+
                 perf_line("201702","0","","01","F17Q10000002"))
    schema,loans=schema_audit(o,p)
    result,cells=audit_rows(p,loans)
    assert result["within_loan_backward_rows"] == 1
    assert result["first_observed_payoff_rows"] == 1
    assert result["first_observed_payoff_fallback_upb"] == 100000
    assert result["missing_or_nonfinite_age_rows"] == 1
    assert sum(r["prepaid_upb"] for r in cells) == 200000


def test_duplicate_month_or_loan_reentry_withholds_reference_cells(tmp_path):
    o,p=tmp_path/"orig.txt",tmp_path/"perf.txt"
    o.write_text(orig_line()+orig_line("F17Q10000002"))
    p.write_text(perf_line()+perf_line()+perf_line(loan="F17Q10000002")+
                 perf_line("201702"))
    _,loans=schema_audit(o,p)
    result,cells=audit_rows(p,loans)
    assert result["duplicate_loan_month_rows"] == 1
    assert result["loan_group_reentries"] == 1
    assert not result["reference_complete"]
    assert cells == []


def test_actual_fixed_production_replay_orders_lag_and_excludes_later_outcomes(tmp_path):
    import polars as pl
    o,p=tmp_path/"orig.txt",tmp_path/"perf.txt"
    o.write_text(orig_line())
    p.write_text(perf_line("201703","0","2","01")+
                 perf_line("201701","90000")+
                 perf_line("202510","DO NOT PARSE","DO NOT PARSE","01"))
    frozen=tmp_path/"frozen_ingest.py"
    frozen.write_bytes((Path(__file__).resolve().parents[1]/"hazard/ingest.py").read_bytes())
    dest=tmp_path/"fixed.parquet"
    replay_worker(o,p,dest,"fixed",frozen)
    cells=pl.read_parquet(dest)
    assert cells.height == 2
    assert cells["prepaid_upb"].sum() == 90000
    assert cells["reporting_period"].max() == "201703"
