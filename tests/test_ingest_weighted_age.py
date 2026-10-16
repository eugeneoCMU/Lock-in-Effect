"""A cohort's mean age must be invariant to partitioning into quarterly files."""
import os
import sys
from pathlib import Path
import polars as pl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'hazard'))
os.environ.setdefault('FRED_API_KEY', 'test-dummy-key')
from hazard import ingest
from hazard.fannie_replication import combine_quarter_cells


def test_unequal_quarter_sizes_recover_the_loan_mean(monkeypatch, tmp_path):
    # One 12-month-old loan and nine 32-month-old loans: pooled mean is 30.
    # An unweighted mean of the two file means instead gives 22.
    origins, histories, pairs = {}, {}, []
    for quarter, count, age in [('small', 1, 12.), ('large', 9, 32.)]:
        op, pp = tmp_path/f'{quarter}_orig', tmp_path/f'{quarter}_perf'
        ids = [f'{quarter}{i}' for i in range(count)]
        origins[op] = pl.DataFrame({
            'loan_sequence_number': ids, 'vintage': [2015]*count,
            'coupon': [.04]*count, 'fico_bucket': ['high']*count,
            'ltv_bucket': ['low']*count, 'original_upb': [120.]*count,
        })
        histories[pp] = pl.DataFrame({
            'loan_sequence_number': ids, 'reporting_period': ['201801']*count,
            'current_upb': [100.]*count, 'is_prepay': [False]*count,
            'loan_age': [age]*count, 'servicer_state': ['Current']*count,
        })
        pairs.append((op, pp))
    monkeypatch.setattr(ingest, '_scan_orig', lambda p: origins[p].lazy())
    monkeypatch.setattr(ingest, '_scan_perf', lambda p: histories[p].lazy())
    single = ingest.build_panel_from_files(pairs, tmp_path/'single.parquet')
    cells = []
    for i, pair in enumerate(pairs):
        dest = tmp_path/f'cells_{i}.parquet'
        ingest.build_panel_from_files([pair], dest)
        cells.append(dest)
    combined = combine_quarter_cells(cells, tmp_path/'combined.parquet', vintage_years=None)
    for panel in [single, combined]:
        assert panel['mean_loan_age'].item() == pytest.approx(30.)
        assert panel['loan_count'].item() == 10
        assert panel['exposure_upb'].item() == 1000.


def test_recombine_weights_unequal_existing_quarter_cells(tmp_path):
    paths = []
    for i, (count, age) in enumerate([(1,12.),(9,32.)]):
        frame = pl.DataFrame({
            'vintage':[2015], 'coupon':[.04], 'fico_bucket':['high'],
            'ltv_bucket':['low'], 'reporting_period':['201801'],
            'exposure_upb':[100.*count], 'orig_upb_sum':[120.*count],
            'prepaid_upb':[0.], 'mean_loan_age':[age], 'mode_state':['Current'],
            'loan_count':[count], 'monthly_prepay_rate':[0.],
            'period':['2018-01-01'], 'burnout':[0.],
        })
        p=tmp_path/f'{i}.parquet'; frame.write_parquet(p); paths.append(p)
    combined=combine_quarter_cells(paths,tmp_path/'pooled.parquet',vintage_years=None,allow_legacy_cells=True)
    assert combined['mean_loan_age'].item() == pytest.approx(30.)


@pytest.mark.parametrize('missing', [None, float('nan')])
def test_missing_quarter_age_does_not_turn_known_age_into_zero_or_nan(tmp_path, missing):
    paths=[]
    for i,age in enumerate([missing, 30.]):
        p=tmp_path/f'age_{i}.parquet'
        pl.DataFrame({
            'vintage':[2015], 'coupon':[.04], 'fico_bucket':['high'],
            'ltv_bucket':['low'], 'reporting_period':['201801'],
            'exposure_upb':[100.], 'orig_upb_sum':[120.], 'prepaid_upb':[0.],
            'mean_loan_age':pl.Series([age],dtype=pl.Float64), 'mode_state':['Current'],
            'loan_count':[1], 'monthly_prepay_rate':[0.], 'period':['2018-01-01'],
            'burnout':[0.],
        }).write_parquet(p)
        paths.append(p)
    result=combine_quarter_cells(paths,tmp_path/'known_age.parquet',vintage_years=None,allow_legacy_cells=True)
    assert result['mean_loan_age'].item() == pytest.approx(30.)
    assert result['loan_count'].item() == 2
