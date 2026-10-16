"""Source-cohort history and corrected-run input contracts."""
import os
import sys
from pathlib import Path
os.environ.setdefault('FRED_API_KEY', 'test-no-network')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'hazard'))
import numpy as np
import polars as pl
import pytest
import loan_sample as ls


def sources(monkeypatch):
    orig = pl.DataFrame({
        'loan_sequence_number': ['a', 'b', 'c', 'd'], 'vintage': [2020]*4,
        'coupon': [.03]*4, 'fico_bucket': ['high']*4, 'ltv_bucket': ['low']*4,
        'original_upb': [100.]*4, 'original_loan_term': [180., 360., 360., 360.],
        'original_interest_rate': [3.]*4, 'credit_score': [750.]*4,
        'original_ltv': [70.]*4, 'property_state': ['PA']*4,
        'first_payment_date': ['202001']*4,
    })
    perf = pl.DataFrame({
        'loan_sequence_number': ['a','a','b','b','c','d','d','b'],
        'reporting_period': ['202204','202205','202204','202205','202204','202204','202205','202206'],
        'current_upb': [90.,80.,90.,0.,70.,90.,80.,9999.],
        'loan_age': [27.,28.,27.,28.,27.,27.,28.,29.],
        'servicer_state': ['Current','Current','Current','Prepaid','Current','Current','D30','INVALID FUTURE'],
        'is_prepay': [False,False,False,True,False,False,False,True],
    })
    monkeypatch.setattr(ls, '_scan_orig', lambda _:orig.lazy())
    monkeypatch.setattr(ls, '_scan_perf', lambda _, reporting_end=None:
        perf.lazy().filter(pl.col('reporting_period') <= reporting_end))
    return orig, perf


def test_snapshot_uses_exact_month_known_terms_and_historical_denominator(monkeypatch, tmp_path):
    sources(monkeypatch)
    d=ls._loan_snapshot_one_pair(tmp_path/'o', tmp_path/'p').sort('loan_id')
    assert d['loan_id'].to_list() == ['a','d']  # stale c and paid b cannot enter
    assert d['original_loan_term'].to_list() == [180.,360.]
    assert d['reporting_period'].unique().to_list() == ['202205']
    assert d['initial_burnout'].to_list() == pytest.approx([90/400]*2)
    assert d['burnout_denominator_multiplier'].to_list() == [2.,2.]
    assert d['stratum_id'].n_unique() == 1
    assert d['history_first_observed_payoff_count'].sum() == 0


def test_snapshot_term_filter_changes_history_population_together(monkeypatch,tmp_path):
    sources(monkeypatch)
    d=ls._loan_snapshot_one_pair(tmp_path/'o',tmp_path/'p',term_months=360)
    assert d['loan_id'].to_list() == ['d']
    assert d['initial_burnout'].item() == .3
    assert d['burnout_denominator_multiplier'].item() == 3.


def test_corrected_runner_rejects_legacy_before_macro_or_matrix_access(monkeypatch,tmp_path):
    import microsim_engine as engine
    def unexpected(*a,**k): raise AssertionError('No macro/matrix access before input checks')
    monkeypatch.setattr(engine,'fetch_data',unexpected)
    monkeypatch.setattr(engine,'load_transition_matrix',unexpected)
    with pytest.raises(ValueError,match='terms|history|historical'):
        engine.run_qt_microsim(loan_sample=pl.DataFrame({'loan_id':['a']}),output=tmp_path/'out.parquet')
    assert not (tmp_path/'out.parquet').exists()


def test_fixed_history_combines_partitions_before_sampling(monkeypatch,tmp_path):
    sources(monkeypatch)
    # Disjoint loans, with another fully paid source cohort still represented
    # in the denominator even though its quarter has no surviving snapshot.
    base_orig=ls._scan_orig(None).collect(); base_perf=ls._scan_perf(None,'202205').collect()
    other_orig=base_orig.head(1).with_columns(pl.lit('e').alias('loan_sequence_number'))
    other_perf=base_perf.filter(pl.col('loan_sequence_number')=='b').with_columns(pl.lit('e').alias('loan_sequence_number'))
    monkeypatch.setattr(ls,'_scan_orig',lambda p:(base_orig if p.name=='o1' else other_orig).lazy())
    monkeypatch.setattr(ls,'_scan_perf',lambda p,reporting_end=None:(base_perf if p.name=='p1' else other_perf).lazy())
    d=ls._build_loan_universe([(tmp_path/'o1',tmp_path/'p1'),(tmp_path/'o2',tmp_path/'p2')])
    assert d['initial_burnout'].to_list() == pytest.approx([180/500]*2)
    assert d['burnout_denominator_multiplier'].to_list() == [2.5,2.5]


def test_snapshot_rejects_overlapping_origination_files(monkeypatch,tmp_path):
    sources(monkeypatch)
    with pytest.raises(ValueError,match='[Oo]verlap|Duplicate'):
        ls._build_loan_universe([(tmp_path/'o1',tmp_path/'p1'),(tmp_path/'o2',tmp_path/'p2')])


def test_partial_unknown_payoff_history_is_not_zero(monkeypatch,tmp_path):
    _, perf = sources(monkeypatch)
    monkeypatch.setattr(ls,'_scan_perf',lambda _,reporting_end=None:
        perf.lazy().filter((pl.col('reporting_period') <= reporting_end)
                           & (pl.col('loan_sequence_number') != 'b')))
    with pytest.raises(ValueError,match='lack pre-QT performance'):
        ls._loan_snapshot_one_pair(tmp_path/'o',tmp_path/'p')


@pytest.mark.parametrize('bad_snapshot,bad_cutoff',[(True,False),(False,True)])
def test_corrected_runner_rejects_later_inputs_before_macro_access(monkeypatch,tmp_path,bad_snapshot,bad_cutoff):
    import microsim_engine as engine
    from markov import estimate_transitions_from_loans
    sources(monkeypatch)
    sample=ls._loan_snapshot_one_pair(tmp_path/'o',tmp_path/'p')
    if bad_snapshot:
        sample=sample.with_columns(pl.lit('202505').alias('reporting_period'))
    matrix,_=estimate_transitions_from_loans(pl.DataFrame({
        'loan_sequence_number':['a'], 'reporting_period':['202205'],
        'current_upb':[100.], 'servicer_state':['Current']}),
        estimation_end='202509' if bad_cutoff else '202205')
    def unexpected(*a,**k): raise AssertionError('No macro access before cutoff checks')
    monkeypatch.setattr(engine,'fetch_data',unexpected)
    with pytest.raises(ValueError,match='pre-QT|cutoff'):
        engine.run_qt_microsim(loan_sample=sample,transition_matrix=matrix,output=tmp_path/'out.parquet')


def test_frozen_sample_cannot_be_deleted_by_force_rebuild(monkeypatch,tmp_path):
    old=tmp_path/'old.parquet';old.write_bytes(b'frozen sample')
    monkeypatch.setattr(ls,'LOAN_SAMPLE_PATH',old)
    with pytest.raises(FileExistsError,match='Preserve'):
        ls.load_or_build_loan_sample(force_rebuild=True)
    assert old.read_bytes() == b'frozen sample'


def test_corrected_run_uses_rebuilt_history_and_preserves_existing_outputs(monkeypatch,tmp_path):
    import pandas as pd
    import microsim_engine as engine
    from markov import estimate_transitions_from_loans
    sources(monkeypatch)
    sample=ls._loan_snapshot_one_pair(tmp_path/'o',tmp_path/'p')
    histories=pl.DataFrame({'loan_sequence_number':['a','a'],
        'reporting_period':['202204','202205'], 'current_upb':[90.,80.],
        'servicer_state':['Current','Current']})
    trans,_=estimate_transitions_from_loans(histories,estimation_end='202205',output=tmp_path/'matrix.parquet')
    # Cutoff provenance survives the actual matrix storage path.
    stored=pd.read_parquet(tmp_path/'matrix.parquet')
    assert stored.attrs == trans.attrs
    macro=pd.DataFrame({'MORTGAGE30US':[6.,6.5], 'WSHOMCB':[1000.,999.]},
        index=pd.to_datetime(['2022-06-30','2022-07-31']))
    output=tmp_path/'simulation.parquet'
    result=engine.run_qt_microsim(loan_sample=sample,macro=macro,transition_matrix=stored,
        output=output,regimes=('US',))
    assert len(result['US']) == 2
    assert np.isfinite(result['US'].select_dtypes('number').to_numpy()).all()
    assert (result['US']['weighted_sched_b'] > 0).all()
    before=output.read_bytes()
    with pytest.raises(FileExistsError,match='Preserve'):
        engine.run_qt_microsim(loan_sample=sample,macro=macro,transition_matrix=stored,
            output=output,regimes=('US',))
    assert output.read_bytes() == before
