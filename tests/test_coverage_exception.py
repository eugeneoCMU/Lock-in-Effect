import hashlib
import polars as pl
import pytest
from test_freddie_rebuild_stream import orig, perf, sources
from freddie_rebuild_stream import build_quarter


def record(o,p,**changes):
    value=dict(policy='known_pre_snapshot_history_v1',quarter='2020Q1',
        source_sha256={'origination':hashlib.sha256(o.read_bytes()).hexdigest(),
                       'performance':hashlib.sha256(p.read_bytes()).hexdigest()},
        expected_missing_loans=1,expected_missing_original_upb=200.,
        expected_original_first_payment={'202003':1},expected_first_valid_performance={'202207':1})
    value.update(changes);return value


def fixture(tmp_path):
    return sources(tmp_path,[orig(1),orig(2,200),orig(3)],
        [perf(1,'202204',0,zb='01'),perf(2,'202207',200),perf(2,'202208',0,zb='01'),perf(3,'202205',80)])


def test_strict_default_still_stops(tmp_path):
    o,p=fixture(tmp_path)
    with pytest.raises(ValueError,match='pre-snapshot'):build_quarter(o,p,tmp_path/'strict','2020Q1')


def test_exception_uses_known_history_denominator_and_audits_unknown_bounds(tmp_path):
    o,p=fixture(tmp_path);out=tmp_path/'exception'
    result=build_quarter(o,p,out,'2020Q1',coverage_exception=record(o,p))
    audit=result['pre_snapshot_coverage']
    assert audit['missing_loans']==1 and audit['unknown_original_upb']==200
    cohort=audit['affected_cohorts'][0]
    assert cohort['known_history_original_upb']==200
    assert cohort['known_history_burnout']==.5
    assert cohort['full_cohort_burnout_lower']==.25
    assert cohort['full_cohort_burnout_upper']==.75
    history=pl.read_parquet(out/'cohort_history.parquet')
    assert history['cohort_original_upb'].item()==200
    assert history['historical_prepaid_upb'].item()==100
    snap=pl.read_parquet(out/'snapshot.parquet')
    assert snap.height==1 and snap['loan_id'].item().endswith('000003')
    panel=pl.read_parquet(out/'panel.parquet')
    assert panel['cohort_original_upb'].unique().to_list()==[400.]
    assert panel['prepaid_upb'].sum()==300


@pytest.mark.parametrize('change',[{'expected_missing_loans':2},{'expected_missing_original_upb':201},
    {'quarter':'2020Q2'},{'source_sha256':{}},{'expected_first_valid_performance':{'202208':1}}])
def test_exception_cannot_waive_different_missing_pattern(tmp_path,change):
    o,p=fixture(tmp_path)
    with pytest.raises(ValueError):build_quarter(o,p,tmp_path/'out','2020Q1',coverage_exception=record(o,p,**change))
    assert not (tmp_path/'out').exists()


def test_receipt_checks_saved_history_and_snapshot(tmp_path):
    from coverage_exception import validate_audit
    o,p=fixture(tmp_path);dest=tmp_path/'2020Q1';out=dest/'rebuilt'
    r=record(o,p);report=build_quarter(o,p,out,'2020Q1',coverage_exception=r)
    validate_audit(r,report,dest)
    history=pl.read_parquet(out/'cohort_history.parquet').with_columns(pl.lit(400.).alias('cohort_original_upb'))
    history.write_parquet(out/'cohort_history.parquet')
    with pytest.raises(ValueError,match='denominator'):validate_audit(r,report,dest)


def test_frozen_authorization_is_required_before_source_access(tmp_path):
    from coverage_exception import frozen_record
    from run_freddie_rebuild import freeze_coverage_record,digest
    import json
    root=tmp_path/'root';root.mkdir();dest=root/'quarters/2020Q1';dest.mkdir(parents=True)
    note=root/'authorization.md';note.write_text('Approved known-history exception')
    r=dict(policy='known_pre_snapshot_history_v1',quarter='2020Q1',evidence_sha256={'authorization.md':digest(note)})
    (root/'coverage_exceptions_frozen.json').write_text(json.dumps({'2020Q1':r}))
    freeze=freeze_coverage_record(root,dest,'2020Q1')
    assert frozen_record(dest,freeze,digest)==r
    (dest/'authorization.md').write_text('changed')
    with pytest.raises(ValueError,match='evidence'):frozen_record(dest,freeze,digest)
