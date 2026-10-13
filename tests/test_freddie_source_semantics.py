"""Independent fixtures from Freddie's January-2026 32-field public layout."""
import os
from pathlib import Path
import sys

os.environ.setdefault('FRED_API_KEY', 'test-no-network')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'hazard'))
import polars as pl
import pytest
from freddie_rebuild_stream import build_quarter
from ingest import _map_servicer_state


def native_sources(tmp_path, *, assistance='', delinquency='0', zero_balance=''):
    original=['']*32
    for i,v in {0:'720',1:'202003',10:'100000',11:'80',12:'3.5',15:'FRM',
                16:'PA',19:'F20Q10000001',21:'360'}.items(): original[i]=v
    rows=[]
    for month,balance in [('202204','90000'),('202205','89000')]:
        row=['']*32
        # Explicit native positions; do not derive fixtures from production schema.
        for i,v in {0:'F20Q10000001',1:month,2:balance,3:'0',4:'26',
                    12:month,28:'Y',29:''}.items(): row[i]=v
        if month=='202205':
            row[3]=delinquency
            row[8]=zero_balance
            row[29]=assistance
            if zero_balance: row[2]='0'
        rows.append('|'.join(row))
    o,p=tmp_path/'orig.txt',tmp_path/'perf.txt'
    o.write_text('|'.join(original)+'\n')
    p.write_text('\n'.join(rows)+'\n')
    return o,p


def test_native_assistance_column_preserves_forbearance_and_transition(tmp_path):
    o,p=native_sources(tmp_path,assistance='F')
    out=tmp_path/'out'
    build_quarter(o,p,out,'2020Q1')
    assert pl.read_parquet(out/'snapshot.parquet')['state'].to_list()==['Forbearance']
    t=pl.read_parquet(out/'transition_counts.parquet')
    edge=t.filter((pl.col('from_state')=='Current')&(pl.col('to_state')=='Forbearance'))
    assert edge['count'].item()==1
    assert edge['opening_upb'].item()==90000


@pytest.mark.parametrize('delinquency',['10','24','180'])
def test_extended_delinquency_is_d90_in_scalar_and_vector_paths(tmp_path,delinquency):
    o,p=native_sources(tmp_path,delinquency=delinquency)
    out=tmp_path/'out'
    build_quarter(o,p,out,'2020Q1')
    assert pl.read_parquet(out/'snapshot.parquet')['state'].to_list()==['D90+']
    got=pl.DataFrame({'d':[delinquency],'a':[''],'z':['']}).select(
        _map_servicer_state(pl.col('d'),pl.col('a'),pl.col('z')).alias('state'))
    assert got['state'].to_list()==['D90+']


@pytest.mark.parametrize('zero_balance',['16','96'])
def test_other_disclosed_terminal_events_are_not_current_or_voluntary(tmp_path,zero_balance):
    o,p=native_sources(tmp_path,zero_balance=zero_balance)
    out=tmp_path/'out'
    build_quarter(o,p,out,'2020Q1')
    t=pl.read_parquet(out/'transition_counts.parquet')
    edge=t.filter((pl.col('from_state')=='Current')&(pl.col('to_state')=='Liquidated'))
    assert edge['count'].item()==1
    assert pl.read_parquet(out/'panel.parquet')['prepaid_upb'].sum()==0


def test_native_layout_positions_include_last_paid_date():
    from schema import PERF_COLS
    assert len(PERF_COLS)==32
    assert PERF_COLS[12]=='due_date_last_paid_installment'
    assert PERF_COLS[28]=='delinq_disaster'
    assert PERF_COLS[29]=='borrower_assistance'
    assert PERF_COLS[31]=='interest_bearing_upb'


@pytest.mark.parametrize('position,bad',[(12,'123.45'),(28,'F'),(29,'Y'),(3,'XX'),(3,'RP'),(8,'77')])
def test_ambiguous_native_semantics_fail_before_artifact_publication(tmp_path,position,bad):
    o,p=native_sources(tmp_path)
    rows=p.read_text().splitlines()
    row=rows[-1].split('|'); row[position]=bad; rows[-1]='|'.join(row)
    p.write_text('\n'.join(rows)+'\n')
    out=tmp_path/'out'
    with pytest.raises(ValueError,match='semantic'):
        build_quarter(o,p,out,'2020Q1')
    assert not out.exists() or not list(out.iterdir())


def test_semantic_validation_does_not_decode_post_cutoff_fields(tmp_path):
    o,p=native_sources(tmp_path)
    row=['DO NOT DECODE']*32
    row[0]='F20Q10000001'; row[1]='202510'
    with p.open('a') as f: f.write('|'.join(row)+'\n')
    report=build_quarter(o,p,tmp_path/'out','2020Q1')
    from schema import SOURCE_SEMANTICS_VERSION
    assert report.get('source_semantics_version')==SOURCE_SEMANTICS_VERSION
    assert report['cutoff_proof']['post_cutoff_outcomes_decoded']==0


def test_snapshot_retains_contemporaneous_contract_fields_without_changing_originals(tmp_path):
    o,p=native_sources(tmp_path)
    rows=p.read_text().splitlines(); row=rows[-1].split('|')
    for i,v in {5:'420',7:'P',10:'2.75',11:'1000',24:'P',31:'88000'}.items(): row[i]=v
    rows[-1]='|'.join(row); p.write_text('\n'.join(rows)+'\n')
    build_quarter(o,p,tmp_path/'out','2020Q1')
    snap=pl.read_parquet(tmp_path/'out/snapshot.parquet').to_dicts()[0]
    assert snap.get('current_note_rate')==.0275
    assert snap.get('remaining_months')==420
    assert snap.get('modification_flag')=='P'
    assert snap.get('current_non_ib_upb')==1000
    assert snap.get('interest_bearing_upb')==88000
    assert snap.get('payment_deferral_flag')=='P'
    assert snap['coupon']==.035 and snap['original_loan_term']==360
    assert snap['balance']==89000 and snap['orig_upb']==100000


def test_reo_acquisition_cannot_return_to_forbearance_from_a_concurrent_flag(tmp_path):
    o,p=native_sources(tmp_path,delinquency='RA',assistance='F')
    rows=p.read_text().splitlines()
    previous=rows[0].split('|');previous[3]='RA';rows[0]='|'.join(previous)
    p.write_text('\n'.join(rows)+'\n')
    out=tmp_path/'out'
    report=build_quarter(o,p,out,'2020Q1')
    assert report['transition_diagnostics']['terminal_absorption_violations']==0
    assert report['counts']['reo_with_forbearance_flag_rows']==1
    assert pl.read_parquet(out/'snapshot.parquet').is_empty()
    panel=pl.read_parquet(out/'panel.parquet')
    assert panel['mode_state'].to_list()==['Defaulted','Defaulted']
    assert panel['prepaid_upb'].sum()==0
    assert panel['exposure_upb'].sum()==179000


@pytest.mark.parametrize('zero_balance,want',[
    ('','Defaulted'),('01','Prepaid'),('09','Defaulted'),('16','Liquidated'),('96','Liquidated')])
def test_explicit_termination_then_reo_precede_assistance_in_both_paths(zero_balance,want):
    from freddie_rebuild_stream import _state
    assert _state(b'RA',b'F',zero_balance.encode())==want
    got=pl.DataFrame({'d':['RA'],'a':['F'],'z':[zero_balance]}).select(
        _map_servicer_state(pl.col('d'),pl.col('a'),pl.col('z')).alias('state'))
    assert got['state'].to_list()==[want]


def test_assistance_does_not_authorize_unsupported_native_delinquency(tmp_path):
    o,p=native_sources(tmp_path,delinquency='RP',assistance='F')
    with pytest.raises(ValueError,match='semantic'):
        build_quarter(o,p,tmp_path/'out','2020Q1')


@pytest.mark.parametrize('delinquency',['0','2','24'])
def test_numeric_delinquency_with_assistance_still_maps_to_forbearance(delinquency):
    from freddie_rebuild_stream import _state
    assert _state(delinquency.encode(),b'F',b'')=='Forbearance'
    got=pl.DataFrame({'d':[delinquency],'a':['F'],'z':['']}).select(
        _map_servicer_state(pl.col('d'),pl.col('a'),pl.col('z')).alias('state'))
    assert got['state'].to_list()==['Forbearance']
