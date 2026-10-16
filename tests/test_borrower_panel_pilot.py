import hashlib
from pathlib import Path
import zipfile

import pandas as pd
import pytest

from borrower_panel_pilot import FrozenDecoder, stream_selected, prepare_followup, reconcile_landmark, require_headroom

FROZEN = Path(__file__).resolve().parents[1]/'output/research-rerun/2026-10-14-archive/quarters/2021Q1/executed_code'


def orig(loan='F21Q10000001'):
    row=[b'']*31
    for i,v in {0:'750',1:'202103',10:'100000',11:'70',12:'3',15:'FRM',16:'PA',19:loan,21:'360'}.items():
        row[i]=v.encode()
    return b'|'.join(row)+b'\n'


def perf(month, *, loan='F21Q10000001', balance='90000', code='', dq='00', assistance='', rate='3'):
    row=[b'']*35
    for i,v in {0:loan,1:month,2:balance,3:dq,4:'14',5:'346',8:code,10:rate,11:'0',29:assistance,31:balance}.items():
        row[i]=v.encode()
    return b'|'.join(row)+b'\n'


def archive(tmp_path, performance):
    p=tmp_path/'source.zip'; original=orig()
    with zipfile.ZipFile(p,'w',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('orig_2021Q1.txt',original);z.writestr('perf_2021Q1.txt',performance)
    hashes={'origination':hashlib.sha256(original).hexdigest(),'performance':hashlib.sha256(performance).hexdigest()}
    return p,hashes


def test_stream_hashes_all_bytes_but_never_decodes_post_cutoff_outcomes(tmp_path):
    p,hashes=archive(tmp_path,perf('202205')+perf('202206')+perf('202510',dq='invalid_future_outcome'))
    rows,report=stream_selected(p,{'F21Q10000001'},FrozenDecoder(FROZEN),expected_hashes=hashes)
    assert rows.reporting_period.tolist()==['202205','202206']
    assert report['post_cutoff_selected_rows']==1
    assert report['source_hashes_verified'] is True
    assert rows.iloc[0].current_note_rate==.03


def test_wrong_source_hash_blocks_acceptance(tmp_path):
    p,hashes=archive(tmp_path,perf('202205'));hashes['performance']='bad'
    with pytest.raises(ValueError,match='hash'):
        stream_selected(p,{'F21Q10000001'},FrozenDecoder(FROZEN),expected_hashes=hashes)


def test_frozen_state_precedence_reused():
    decoder=FrozenDecoder(FROZEN)
    assert decoder.state(b'RA',b'F',b'')=='Defaulted'
    assert decoder.state(b'RA',b'F',b'01')=='Prepaid'


def records(months, states, balances):
    return pd.DataFrame(dict(loan_id=['one']*len(months),reporting_period=months,
        state=states,balance=balances,current_note_rate=[.03]*len(months),loan_age=list(range(14,14+len(months)))))


def test_adjacent_payoff_once_and_previous_observation_covariates():
    d=records(['202205','202206','202207'],['Current','Prepaid','Prepaid'],[100.,0.,0.])
    d.loc[1,'current_note_rate']=.09
    out,audit=prepare_followup(d)
    assert out.recorded_payoff_event.sum()==1
    assert out.adjacent_payoff_upb.sum()==100.
    assert out.iloc[1].lag_current_note_rate==.03
    assert not out.iloc[2].at_risk_adjacent


def test_reporting_gap_does_not_become_a_monthly_hazard():
    d=records(['202205','202207'],['Current','Prepaid'],[100.,0.])
    out,audit=prepare_followup(d)
    assert out.adjacent_payoff_upb.sum()==0.
    assert out.timing_unallocated_payoff_upb.sum()==100.
    assert pd.isna(out.iloc[1].lag_current_note_rate)
    assert audit['missing_calendar_months']==1


@pytest.mark.parametrize('months,states',[
    (['202205','202205'],['Current','Current']),
    (['202206','202205'],['Current','Current']),
    (['202205','202206','202207'],['Current','Prepaid','Current'])])
def test_duplicates_backward_dates_and_terminal_revival_rejected(months,states):
    with pytest.raises(ValueError):
        prepare_followup(records(months,states,[100.]*len(months)))


def test_snapshot_mismatch_is_reported_not_discarded():
    d=records(['202205'],['Current'],[100.]);saved=d.copy();saved['balance']=99.
    r=reconcile_landmark(d,saved)
    assert r['matched_loans']==0 and r['mismatch_rows']==1
    assert r['all_matched'] is False


def test_resource_gate_cannot_start_below_four_gib():
    with pytest.raises(RuntimeError,match='4 GiB'):
        require_headroom(4*1024**3-1)
    require_headroom(4*1024**3)


def test_local_only_reserve_is_explicit_and_cannot_fall_below_one_gib():
    require_headroom(2*1024**3,minimum=1024**3)
    with pytest.raises(ValueError):
        require_headroom(2*1024**3,minimum=1)
    with pytest.raises(RuntimeError):
        require_headroom(1024**3-1,minimum=1024**3)
