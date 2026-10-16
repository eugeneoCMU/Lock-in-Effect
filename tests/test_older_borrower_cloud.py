from pathlib import Path
import pytest
from older_borrower_cloud import Native32Decoder

FROZEN=Path(__file__).resolve().parents[1]/'output/research-rerun/2026-10-14-archive/quarters/2018Q1/executed_code'


def row(**values):
    r=[b'']*32
    for k,v in values.items():r[int(k[1:])]=v.encode()
    return b'|'.join(r)


def test_native32_keeps_correct_termination_and_assistance_precedence():
    d=Native32Decoder(FROZEN)
    r=row(c0='F18Q10000001',c1='202205',c2='0',c3='RA',c4='50',c8='01',c10='4.5',c12='202204',c29='F')
    p=d.performance(r)
    assert p['state']=='Prepaid' and p['current_note_rate']==.045
    r=row(c0='F18Q10000001',c1='202205',c2='100',c3='RA',c4='50',c10='4.5',c29='F')
    assert d.performance(r)['state']=='Defaulted'


def test_native32_rejects_wrong_width_and_semantic_shift():
    d=Native32Decoder(FROZEN)
    with pytest.raises(ValueError):d.performance(b'|'.join([b'']*35))
    with pytest.raises(ValueError):d.performance(row(c0='F18Q10000001',c1='202205',c2='100',c3='0',c12='F'))


def test_origination_native32_matches_expected_eligibility_and_units():
    d=Native32Decoder(FROZEN)
    p=d.origination(row(c0='750',c10='100000',c11='80',c12='4.5',c15='FRM',c16='PA',c19='F18Q10000001',c21='360'))
    assert p['vintage']==2018 and p['coupon']==.045 and p['orig_upb']==100000
    assert p['fico_bucket']=='740+' and p['ltv_bucket']=='≤80'


def test_nested_expansion_preserves_initial_hash_sample():
    from borrower_origination_reference import select_origination_ids
    ids=[f'F18Q1{i:08}' for i in range(100)]
    small=select_origination_ids(ids,n=5,seed='20261016-2018Q1-origination-support')
    large=select_origination_ids(ids,n=20,seed='20261016-2018Q1-origination-support')
    assert set(small)<set(large)


def test_invalid_cloud_sample_size_rejected_before_source_reads(tmp_path):
    from older_borrower_cloud import run
    for n in [0,True,50001,1.5]:
        with pytest.raises(ValueError,match='sample size'):
            run(tmp_path,tmp_path,sample_size=n)
