"""Synthetic-only acceptance checks for the bounded original-source rebuild."""
import os
from pathlib import Path
import sys

os.environ.setdefault("FRED_API_KEY", "test-no-network")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hazard"))
import polars as pl
from polars.testing import assert_frame_equal
import pytest

from freddie_rebuild_stream import build_quarter


def orig(i, upb=100, term=360, first="202003", rate="3.12"):
    r = [""] * 32
    for k, v in {0:720, 1:first, 10:upb, 11:80, 12:rate, 15:"FRM", 16:"PA",
                 19:f"F20Q1{i:06d}", 21:term}.items():
        r[k] = str(v)
    return "|".join(r)


def perf(i, month, upb, age=20, zb="", delinquency="0"):
    r = [""] * 32
    for k, v in {0:f"F20Q1{i:06d}", 1:month, 2:upb, 3:delinquency, 4:age, 8:zb}.items():
        r[k] = str(v)
    return "|".join(r)


def sources(tmp_path, orig_rows=None, perf_rows=None):
    o, p = tmp_path / "orig.txt", tmp_path / "perf.txt"
    o.write_text("\n".join(orig_rows or [orig(1), orig(2, 200), orig(3), orig(4), orig(5, term=180)]) + "\n")
    p.write_text("\n".join(perf_rows or [
        perf(1,"202205",80), perf(1,"202203",100), perf(1,"202204",90,age=""),
        perf(1,"202510","DO NOT DECODE",age="DO NOT DECODE",zb="POISON"),
        perf(2,"202203",200), perf(2,"202204",0,zb="01"),
        perf(3,"202205",0,zb="01"),
        perf(4,"202203",100), perf(4,"202205",0,zb="01"),
        perf(5,"202205",100),
    ]) + "\n")
    return o, p


def test_parity_with_corrected_panel_and_snapshot(tmp_path):
    from ingest import build_panel_from_files
    from loan_sample import _snapshot_inputs_one_pair
    o, p = sources(tmp_path)
    dest = tmp_path / "stream"
    report = build_quarter(o,p,dest,"2020Q1",cutoff="202205")
    keys = ["vintage","coupon","fico_bucket","ltv_bucket","reporting_period"]
    baseline = build_panel_from_files([(o,p)],tmp_path/"baseline.parquet",term_months=360,reporting_end="202205")
    actual = pl.read_parquet(dest/"panel.parquet")
    columns = [x for x in baseline.columns if x != "mode_state"]
    assert_frame_equal(actual.select(columns).sort(keys),baseline.select(columns).sort(keys),check_dtypes=False)
    snap, history, ids = _snapshot_inputs_one_pair(o,p,term_months=360)
    got_snap = pl.read_parquet(dest/"snapshot.parquet")
    assert_frame_equal(got_snap.select(snap.columns).sort("loan_id"),snap.sort("loan_id"),check_dtypes=False)
    hk = ["vintage","cohort_coupon","fico_bucket","ltv_bucket"]
    assert_frame_equal(pl.read_parquet(dest/"cohort_history.parquet").select(history.columns).sort(hk),history.sort(hk),check_dtypes=False)
    assert set(pl.read_parquet(dest/"eligible_source_ids.parquet")["loan_sequence_number"]) == set(ids)
    assert report["cutoff_proof"]["post_cutoff_outcomes_decoded"] == 0
    assert report["counts"]["first_observed_payoff_rows"] == 1
    assert report["counts"]["payoff_with_nonadjacent_prior_rows"] == 1
    assert report["counts"]["missing_or_nonfinite_age_rows"] == 1
    assert actual["cohort_original_upb"].unique().to_list() == [500.]
    assert actual.filter(pl.col("reporting_period")=="202205")["burnout"].item() == .8
    transitions = pl.read_parquet(dest/"transition_counts.parquet")
    c = transitions.filter((pl.col("from_state")=="Current") & (pl.col("to_state")=="Current"))
    assert c["opening_upb"].item() == 190 and c["count"].item() == 2
    c = transitions.filter((pl.col("from_state")=="Current") & (pl.col("to_state")=="Prepaid"))
    assert c["opening_upb"].item() == 200 and c["count"].item() == 1


@pytest.mark.parametrize("kind",["duplicate_orig","duplicate_month","reentry","width","unknown_id","missing_coverage","terminal_revival","bad_snapshot_age"])
def test_invalid_input_never_publishes_partial_artifacts(tmp_path,kind):
    oo, pp = [orig(1),orig(2)], [perf(1,"202204",100),perf(1,"202205",90),perf(2,"202205",100)]
    if kind == "duplicate_orig": oo.append(orig(1))
    elif kind == "duplicate_month": pp.insert(1,pp[0])
    elif kind == "reentry": pp.append(perf(1,"202206",80))
    elif kind == "width": pp[0] += "|EXTRA"
    elif kind == "unknown_id": pp.append(perf(3,"202205",100))
    elif kind == "missing_coverage": pp = pp[:2]
    elif kind == "terminal_revival": pp[0] = perf(1,"202204",0,zb="01")
    elif kind == "bad_snapshot_age": pp[1] = perf(1,"202205",90,age="")
    o,p = sources(tmp_path,oo,pp); output = tmp_path/"rebuild"
    with pytest.raises(ValueError): build_quarter(o,p,output,"2020Q1")
    assert not output.exists() or not list(output.iterdir())


def test_transition_cutoff_and_empty_snapshot(tmp_path):
    o,p = sources(tmp_path,[orig(1)],[perf(1,"202204",100),perf(1,"202205",0,zb="01"),perf(1,"202206",50)])
    # A later active observation does not enter the frozen transition history.
    dest = tmp_path/"out"
    report = build_quarter(o,p,dest,"2020Q1",transition_end="202205")
    assert pl.read_parquet(dest/"snapshot.parquet").height == 0
    assert report["transition_diagnostics"]["used_pairs"] == 1
    assert report["transition_diagnostics"]["terminal_absorption_violations"] == 0


def test_output_cannot_overwrite_existing_files(tmp_path):
    o,p = sources(tmp_path); dest = tmp_path/"existing";dest.mkdir();(dest/"keep").write_text("safe")
    with pytest.raises(FileExistsError): build_quarter(o,p,dest,"2020Q1")
    assert (dest/"keep").read_text()=="safe"


def test_history_includes_cohort_without_survivors_and_excludes_future_originations(tmp_path):
    o,p = sources(tmp_path,[orig(1),orig(2,first="202207",rate="6.0")],
        [perf(1,"202205",0,zb="01"),perf(2,"202207",100)])
    dest=tmp_path/"out"; build_quarter(o,p,dest,"2020Q1")
    history=pl.read_parquet(dest/"cohort_history.parquet")
    assert history.height==1 and history["cohort_original_upb"].item()==100
    assert history["survivor_original_upb"].item()==0
    assert pl.read_parquet(dest/"panel.parquet").height==2


def test_original_coverage_requires_valid_pre_snapshot_observation(tmp_path):
    o,p=sources(tmp_path,[orig(1)],[perf(1,"202206",100)])
    with pytest.raises(ValueError,match="pre-snapshot"):
        build_quarter(o,p,tmp_path/"out","2020Q1")


def test_future_outcomes_are_not_decoded(tmp_path,monkeypatch):
    import freddie_rebuild_stream as rebuild
    original_finite = rebuild.finite
    def guarded(value):
        assert value != b"DO NOT DECODE"
        return original_finite(value)
    monkeypatch.setattr(rebuild,"finite",guarded)
    o,p=sources(tmp_path)
    report=build_quarter(o,p,tmp_path/"out","2020Q1")
    assert report["counts"]["post_cutoff_date_rows"]==1


def test_duplicate_excluded_loan_month_is_rejected(tmp_path):
    o,p=sources(tmp_path,[orig(1),orig(2,term=180)],
                [perf(1,"202205",100),perf(2,"202205",100),perf(2,"202205",100)])
    with pytest.raises(ValueError,match="Duplicate loan-month"):
        build_quarter(o,p,tmp_path/"out","2020Q1")


@pytest.mark.parametrize("rate",["2.75","3.25","3.75","4.25","4.75","5.25"])
def test_coupon_bucket_rounding_matches_ingest(tmp_path,rate):
    from ingest import _scan_orig
    o,p=sources(tmp_path,[orig(1,rate=rate)],[perf(1,"202205",100)])
    build_quarter(o,p,tmp_path/"out","2020Q1")
    got=pl.read_parquet(tmp_path/"out"/"panel.parquet")["coupon"].item()
    assert got==_scan_orig(o).collect()["coupon"].item()


def test_deterministic_mode_tie_and_finite_age_denominator(tmp_path):
    o,p=sources(tmp_path,[orig(1),orig(2)],[perf(1,"202204",100,age=""),
        perf(1,"202205",90,age=4),perf(2,"202204",100,age=2,delinquency="1"),
        perf(2,"202205",90,age=3,delinquency="1")])
    build_quarter(o,p,tmp_path/"out","2020Q1")
    panel=pl.read_parquet(tmp_path/"out"/"panel.parquet").sort("reporting_period")
    assert panel["mode_state"].to_list()==["Current","Current"]
    assert panel["mean_loan_age"].to_list()==[2.,3.5]
def test_offline_cli_does_not_require_a_macro_api_key():
    import os, subprocess, sys
    from pathlib import Path
    env=dict(os.environ)
    env.pop('FRED_API_KEY',None)
    result=subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'hazard/freddie_rebuild_stream.py'),'--help'],env=env,capture_output=True,text=True)
    assert result.returncode == 0, result.stderr


def test_zero_rate_exclusion_is_explicit_audited_and_outcome_blind(tmp_path):
    from freddie_raw_quarter_audit import schema_audit
    o,p=sources(tmp_path,[orig(1),orig(2,upb=237000,rate='0'),orig(3,upb=10000,term=180,rate='0')],
        [perf(1,'202204',100),perf(1,'202205',90),
         perf(2,'202205','DO NOT DECODE',age='DO NOT DECODE'),perf(3,'202205','DO NOT DECODE')])
    strict,_=schema_audit(o,p,quarter='2020Q1')
    assert not strict['passed']
    with pytest.raises(ValueError,match='valid note rate'):build_quarter(o,p,tmp_path/'strict','2020Q1')
    schema,_=schema_audit(o,p,quarter='2020Q1',exclude_zero_note_rate=True)
    report=build_quarter(o,p,tmp_path/'explicit','2020Q1',exclude_zero_note_rate=True)
    expected={'enabled':True,'otherwise_eligible_frm_count':2,'otherwise_eligible_frm_upb':247000.,'known360_count':1,'known360_upb':237000.}
    assert schema['passed']
    assert schema['origination']['zero_note_rate_exclusions']==expected
    assert report['zero_note_rate_exclusions']==expected
    assert report['counts']['eligible_original_ids']==1
    assert report['counts']['excluded_original_ids']==2
    assert report['counts']['valid_balance_rows']==2
    assert pl.read_parquet(tmp_path/'explicit/panel.parquet')['cohort_original_upb'].unique().to_list()==[100.]
    assert pl.read_parquet(tmp_path/'explicit/snapshot.parquet').height==1
    assert pl.read_parquet(tmp_path/'explicit/eligible_source_ids.parquet').height==1


@pytest.mark.parametrize('rate',['','nan','-1','30','9999'])
def test_zero_rate_clarification_keeps_other_rate_errors_blocking(tmp_path,rate):
    from freddie_raw_quarter_audit import schema_audit
    o,p=sources(tmp_path,[orig(1),orig(2,rate=rate)],[perf(1,'202205',100),perf(2,'202205',100)])
    schema,_=schema_audit(o,p,quarter='2020Q1',exclude_zero_note_rate=True)
    assert not schema['passed']
    with pytest.raises(ValueError,match='valid note rate'):
        build_quarter(o,p,tmp_path/'out','2020Q1',exclude_zero_note_rate=True)
    assert not (tmp_path/'out').exists()
