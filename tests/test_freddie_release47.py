"""Synthetic Release 47 schema, cutoff and source-bound identity checks."""
import hashlib
import importlib
import pytest
import polars as pl
from polars.testing import assert_frame_equal
from test_freddie_rebuild_stream import orig, perf


def modules():
    return (importlib.import_module('schema'), importlib.import_module('freddie_raw_quarter_audit'),
            importlib.import_module('freddie_rebuild_stream'))


def release_orig(text):
    r=text.split('|')
    return '|'.join(r[:24]+r[25:31]+['9999'])


def release_perf(text):
    r=text.split('|')
    if r[3].isdigit():r[3]=f'{int(r[3]):02d}'
    return '|'.join(r+['7','OTHER',''])


def files(tmp_path, layout='release47', cross=False):
    oo=[orig(1)]
    pp=[perf(1,'202204',100),perf(1,'202205',90),
        perf(1,'202510','POISON',age='POISON',zb='POISON',delinquency='POISON')]
    if cross:
        oo=[x.replace('F20Q1','F20Q4') for x in oo]
        pp=[x.replace('F20Q1','F20Q4') for x in pp]
    if layout=='release47':oo=list(map(release_orig,oo));pp=list(map(release_perf,pp))
    o,p=tmp_path/f'{layout}-orig.txt',tmp_path/f'{layout}-perf.txt'
    o.write_text('\n'.join(oo)+'\n');p.write_text('\n'.join(pp)+'\n')
    return o,p


def record(o,p):
    lid=o.read_bytes().split(b'|')[19]
    sha=hashlib.sha256(lid).hexdigest()
    return dict(quarter='2021Q1',allowed_id_sha256=[sha],
        allowed_id_prefixes={sha:'F20Q4'},cohort_vintage_by_id_sha256={sha:2020},
        source_sha256={'origination':hashlib.sha256(o.read_bytes()).hexdigest(),
                       'performance':hashlib.sha256(p.read_bytes()).hexdigest()},
        expected=dict(original_records=1,performance_rows=3,eligible_original_loans=1,eligible_original_upb=100.))


def test_release_matches_native_artifacts_preserves_raw_hashes(tmp_path):
    schema,audit,stream=modules()
    o,p=files(tmp_path,'native32');ro,rp=files(tmp_path)
    old=stream.build_quarter(o,p,tmp_path/'native','2020Q1')
    try:new=stream.build_quarter(ro,rp,tmp_path/'release','2020Q1',source_layout='release47')
    except TypeError:pytest.fail('Release 47 source layout support is missing')
    assert old['source_semantics_version']==schema.SOURCE_SEMANTICS_VERSION
    assert new['source_semantics_version']==schema.source_semantics_version('release47')
    assert new['source_semantics_version']!=old['source_semantics_version']
    assert new['source_sha256']['performance']==hashlib.sha256(rp.read_bytes()).hexdigest()
    assert new['cutoff_proof']['post_cutoff_outcomes_decoded']==0
    assert new['schema']['origination_width_counts']=={'31':1}
    assert new['schema']['performance_width_counts']=={'35':3}
    for name in old['artifacts']:
        assert_frame_equal(pl.read_parquet(tmp_path/'native'/name),pl.read_parquet(tmp_path/'release'/name))
    result,_=audit.schema_audit(ro,rp,quarter='2020Q1',source_layout='release47')
    assert result['passed']


def test_default_rejects_release_width_and_schema_does_not_validate_outcomes(tmp_path):
    _,audit,stream=modules();o,p=files(tmp_path)
    result,_=audit.schema_audit(o,p,quarter='2020Q1')
    assert not result['passed']
    with pytest.raises(ValueError,match='32 fields'):stream.build_quarter(o,p,tmp_path/'bad','2020Q1')
    rows=p.read_text().splitlines();r=rows[0].split('|');r[28]='BAD';rows[0]='|'.join(r)
    p.write_text('\n'.join(rows)+'\n')
    result,_=audit.schema_audit(o,p,quarter='2020Q1',source_layout='release47')
    assert result['passed']
    with pytest.raises(ValueError,match='disaster/assistance'):
        stream.build_quarter(o,p,tmp_path/'bad-token','2020Q1',source_layout='release47')
    assert not (tmp_path/'bad-token').exists()


def test_release_disaster_assistance_and_reo_priority(tmp_path):
    _,_,stream=modules();o,p=files(tmp_path)
    rows=p.read_text().splitlines();r=rows[1].split('|');r[3]='RA';r[28]='Y';r[29]='F';rows[1]='|'.join(r)
    p.write_text('\n'.join(rows)+'\n')
    report=stream.build_quarter(o,p,tmp_path/'reo','2020Q1',source_layout='release47')
    assert report['counts']['reo_with_forbearance_flag_rows']==1
    assert pl.read_parquet(tmp_path/'reo'/'panel.parquet').filter(pl.col('reporting_period')=='202205')['mode_state'].item()=='Defaulted'


def test_exact_cross_year_override_sets_all_cohort_vintages(tmp_path):
    _,audit,stream=modules();o,p=files(tmp_path,cross=True);rec=record(o,p)
    result,_=audit.schema_audit(o,p,quarter='2021Q1',source_layout='release47',identity_exceptions=rec)
    assert result['passed']
    report=stream.build_quarter(o,p,tmp_path/'cross','2021Q1',source_layout='release47',identity_exceptions=rec)
    for name in ['panel.parquet','snapshot.parquet','cohort_history.parquet']:
        assert pl.read_parquet(tmp_path/'cross'/name)['vintage'].unique().to_list()==[2020]
    assert report['identity_exceptions']['cohort_vintage_by_id_sha256']==rec['cohort_vintage_by_id_sha256']


@pytest.mark.parametrize('mutation',['absent','old_same_year_record','wrong_prefix','wrong_vintage','extra_key','wrong_source'])
def test_cross_year_override_is_exact_and_source_bound(tmp_path,mutation):
    _,_,stream=modules();o,p=files(tmp_path,cross=True);rec=record(o,p);sha=rec['allowed_id_sha256'][0]
    if mutation=='absent':rec=None
    elif mutation=='old_same_year_record':rec.pop('allowed_id_prefixes');rec.pop('cohort_vintage_by_id_sha256')
    elif mutation=='wrong_prefix':rec['allowed_id_prefixes'][sha]='F19Q4'
    elif mutation=='wrong_vintage':rec['cohort_vintage_by_id_sha256'][sha]=2021
    elif mutation=='extra_key':rec['allowed_id_prefixes']['a'*64]='F20Q4'
    elif mutation=='wrong_source':rec['source_sha256']['performance']='a'*64
    with pytest.raises(ValueError):
        stream.build_quarter(o,p,tmp_path/'invalid','2021Q1',source_layout='release47',identity_exceptions=rec)
    assert not (tmp_path/'invalid').exists()


def test_release_mapping_and_publisher_metadata():
    schema,_,_=modules()
    native=[str(i).encode() for i in range(32)]
    released=native[:24]+native[25:31]+[b'VS4']
    mapped=schema.normalize_origination(released,'release47')
    assert mapped[:24]==native[:24]
    assert mapped[24]==mapped[31]==b''
    assert mapped[25:31]==native[25:31]
    metadata=schema.source_layout_metadata('release47')
    assert metadata['used_performance_positions']['borrower_assistance']=={'source':29,'canonical':29}
    assert metadata['used_performance_positions']['interest_bearing_upb']=={'source':31,'canonical':31}
    assert metadata['layout_url'].endswith('/file_layout_july_2026.xlsx')
    with pytest.raises(ValueError,match='layout'):schema.source_semantics_version('auto')


@pytest.mark.parametrize('position,token',[(28,'N'),(29,'N'),(3,'XX'),(3,'1')])
def test_release_pre_cutoff_tokens_are_official_and_strict(tmp_path,position,token):
    _,_,stream=modules();o,p=files(tmp_path)
    rows=p.read_text().splitlines();r=rows[0].split('|');r[position]=token;rows[0]='|'.join(r)
    p.write_text('\n'.join(rows)+'\n')
    with pytest.raises(ValueError,match='semantic mismatch'):
        stream.build_quarter(o,p,tmp_path/'invalid-token','2020Q1',source_layout='release47')
    assert not (tmp_path/'invalid-token').exists()


def test_vintage_override_does_not_change_other_source_loans(tmp_path):
    _,_,stream=modules();o,p=files(tmp_path,cross=True)
    oo=o.read_text().splitlines()+[release_orig(orig(2).replace('F20Q1','F21Q1'))]
    pp=p.read_text().splitlines()+[release_perf(perf(2,'202205',100).replace('F20Q1','F21Q1'))]
    o.write_text('\n'.join(oo)+'\n');p.write_text('\n'.join(pp)+'\n')
    rec=record(o,p)
    stream.build_quarter(o,p,tmp_path/'mixed','2021Q1',source_layout='release47',identity_exceptions=rec)
    for name in ['panel.parquet','snapshot.parquet','cohort_history.parquet']:
        assert sorted(pl.read_parquet(tmp_path/'mixed'/name)['vintage'].unique().to_list())==[2020,2021]
