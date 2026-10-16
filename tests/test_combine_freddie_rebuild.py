import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import polars as pl
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'hazard'))
from combine_freddie_rebuild import combine_panel,combine_transitions,combine,SUMS
from config import MARKOV_STATES


def frame(months,denominator,paid):
    n=len(months)
    d={k:[0.]*n for k in SUMS}
    d.update(vintage=[2020]*n,coupon=[.03]*n,fico_bucket=['high']*n,ltv_bucket=['low']*n,
        reporting_period=months,cohort_original_upb=[denominator]*n,mode_state=['Current']*n,
        prepaid_upb=paid,exposure_upb=[80.]*n,finite_age_sum=[20.]*n,finite_age_count=[1]*n,loan_count=[1]*n)
    return pl.DataFrame(d)


def test_disappeared_quarter_keeps_fixed_denominator_in_later_months():
    d=combine_panel([frame(['202201'],100.,[100.]),frame(['202201','202202'],300.,[0.,60.])])
    assert d['cohort_original_upb'].to_list()==[400.,400.]
    assert d['burnout'].to_list()==[.25,.4]
    assert d['mean_loan_age'].to_list()==[20.,20.]


def test_transitions_pool_opening_weights_before_normalization():
    rows=[{'from_state':a,'to_state':b,'opening_upb':0.,'count':0} for a in MARKOV_STATES for b in MARKOV_STATES]
    a=pl.DataFrame(rows).with_columns(pl.when((pl.col('from_state')=='Current')&(pl.col('to_state')=='D30')).then(100.).otherwise(0.).alias('opening_upb'))
    b=pl.DataFrame(rows).with_columns(pl.when((pl.col('from_state')=='Current')&(pl.col('to_state')=='Current')).then(300.).otherwise(0.).alias('opening_upb'))
    matrix,diag=combine_transitions([a,b])
    assert matrix.loc['Current','D30']==.25
    assert matrix.loc['D30','D30']==1.
    np.testing.assert_allclose(matrix.sum(axis=1),1.)
    assert matrix.attrs['estimation_end']=='202205'


def test_missing_quarter_blocks_combination_before_output(tmp_path):
    with pytest.raises(FileNotFoundError,match='Missing verified'):
        combine(tmp_path)
    assert not (tmp_path/'combined').exists()


def _source_row(values):
    fields = [''] * 32
    for position, value in values.items():
        fields[position] = str(value)
    return '|'.join(fields)


@pytest.fixture
def rebuilt_two_quarters(tmp_path, monkeypatch):
    """Exercise the real streamer and combiner without any mounted sources."""
    from freddie_rebuild_stream import build_quarter
    import combine_freddie_rebuild as combined

    root = tmp_path / 'synthetic-rebuild'
    quarters = ['2020Q1', '2020Q2']
    # (original UPB, coupon percent, chronological performance observations)
    # The 5-percent cohort is wholly extinct. The 3-percent cohort spans both
    # quarters, and its Q1 survivor pays off after the snapshot cutoff.
    loans = {
        '2020Q1': [
            (100, 3., [('202204', 90, '0', ''), ('202205', 80, '0', ''),
                      ('202206', 0, '0', '01')]),
            (200, 3., [('202204', 200, '0', ''), ('202205', 0, '0', '01')]),
            (400, 5., [('202204', 400, '0', ''), ('202205', 0, '0', '01')]),
        ],
        '2020Q2': [
            (300, 3., [('202204', 300, '0', ''), ('202205', 270, '1', '')]),
            (500, 3., [('202204', 500, '1', ''), ('202205', 0, '0', '01')]),
            (600, 4., [('202204', 600, '0', ''), ('202205', 550, '0', '')]),
        ],
    }
    for quarter in quarters:
        source = tmp_path / 'synthetic-inputs' / quarter
        source.mkdir(parents=True)
        originals, performance = [], []
        for number, (upb, coupon, observations) in enumerate(loans[quarter], 1):
            loan_id = f'F{quarter[2:]}{number:06d}'
            originals.append(_source_row({0:720, 1:'202003' if quarter.endswith('1') else '202006',
                10:upb, 11:80, 12:coupon, 15:'FRM', 16:'PA', 19:loan_id, 21:360}))
            for age, (month, balance, delinquency, zero_balance) in enumerate(observations, 10):
                performance.append(_source_row({0:loan_id, 1:month, 2:balance,
                    3:delinquency, 4:age, 8:zero_balance}))
        orig, perf = source / 'orig.txt', source / 'perf.txt'
        orig.write_text('\n'.join(originals) + '\n')
        perf.write_text('\n'.join(performance) + '\n')
        destination = root / 'quarters' / quarter
        build_quarter(orig, perf, destination / 'rebuilt', quarter)
        (destination / 'completed.json').write_text('{}\n')

    validated = []
    def validate_synthetic_completion(destination, *args, **kwargs):
        validated.append(destination.name)
        return {'quarter': destination.name, 'status': 'completed'}
    # The cloud receipt API is the only mocked production behavior. Its own
    # tests cover provider receipts; every data artifact here is built for real.
    monkeypatch.setattr(combined, 'validate_completed', validate_synthetic_completion)
    return root, quarters, validated


def test_two_quarter_combination_preserves_source_history_and_balances(rebuilt_two_quarters):
    from run_freddie_rebuild import digest

    root, quarters, validated = rebuilt_two_quarters
    result = combine(root, quarters=quarters, n_loans=3, seed=42)
    output = root / 'combined'
    panel = pl.read_parquet(output / 'cohort_month_panel.parquet')
    sample = pl.read_parquet(output / 'loan_sample.parquet')
    matrix = pd.read_parquet(output / 'markov_transition_matrix.parquet')
    diagnostics = json.loads((output / 'transition_diagnostics.json').read_text())

    assert validated == quarters
    assert result['quarters'] == quarters and result['complete_freddie_manifest'] is False
    assert result['original_loans'] == 6
    assert result['observed_source_survivors'] == result['sample_n'] == result['sample_unique_ids'] == 3
    assert panel.height == 7

    shared = panel.filter(pl.col('coupon') == .03).sort('reporting_period')
    assert shared['reporting_period'].to_list() == ['202204', '202205', '202206']
    assert shared['cohort_original_upb'].to_list() == [1100.] * 3
    assert shared['prepaid_upb'].to_list() == [0., 700., 80.]
    np.testing.assert_allclose(shared['burnout'], [0., 700 / 1100, 780 / 1100])
    extinct = panel.filter((pl.col('coupon') == .05) & (pl.col('reporting_period') == '202205'))
    assert extinct['cohort_original_upb'].item() == 400.
    assert extinct['burnout'].item() == 1.

    # All survivors fit in this sample, so their observed balance and original
    # principal must be conserved exactly. Terminated loans are never sampled.
    assert set(sample['loan_id']) == {'F20Q1000001', 'F20Q2000001', 'F20Q2000003'}
    assert sample['reporting_period'].unique().to_list() == ['202205']
    assert sample['original_loan_term'].unique().to_list() == [360.]
    assert sample['weight'].unique().to_list() == [1.]
    assert sample['balance'].sum() == 900.
    assert sample['orig_upb'].sum() == 1000.
    shared_sample = sample.filter(pl.col('cohort_coupon') == .03)
    for name, expected in [('cohort_original_upb', 1100.), ('historical_prepaid_upb', 700.),
                           ('survivor_original_upb', 400.), ('initial_burnout', 700 / 1100),
                           ('burnout_denominator_multiplier', 1100 / 400)]:
        np.testing.assert_allclose(shared_sample[name], expected)
    # May history excludes the additional June payoff, while the panel includes it.
    assert panel['prepaid_upb'].sum() == 1180.
    assert panel['exposure_upb'].sum() == 2990.
    assert panel['orig_upb_sum'].sum() == 4300.
    for name in SUMS:
        expected = sum(pl.read_parquet(root / 'quarters' / q / 'rebuilt/panel.parquet')[name].sum()
                       for q in quarters)
        assert panel[name].sum() == pytest.approx(expected)

    # Pool opening balances, then normalize; the June payoff must not contribute.
    assert diagnostics['used_pairs'] == 6
    assert diagnostics['opening_weight_by_state']['Current'] == 1590.
    assert diagnostics['opening_weight_by_state']['D30'] == 500.
    assert sum(diagnostics['opening_weight_by_state'].values()) == 2090.
    assert matrix.loc['Current', 'Current'] == pytest.approx(690 / 1590)
    assert matrix.loc['Current', 'Prepaid'] == pytest.approx(600 / 1590)
    assert matrix.loc['Current', 'D30'] == pytest.approx(300 / 1590)
    assert matrix.loc['D30', 'Prepaid'] == 1.
    assert matrix.loc['Prepaid', 'Prepaid'] == 1.
    np.testing.assert_allclose(matrix.sum(axis=1), 1.)
    for name, expected in result['output_sha256'].items():
        assert digest(output / name) == expected
    assert json.loads((output / 'report.json').read_text()) == result


@pytest.mark.parametrize('old_version',[None,'freddie-native32-ddlpi-states-v1'])
def test_pre_semantic_repair_receipts_cannot_feed_combination(rebuilt_two_quarters,old_version):
    root, quarters, _ = rebuilt_two_quarters
    p=root/'quarters'/quarters[0]/'rebuilt/report.json'
    report=json.loads(p.read_text()); report.pop('source_semantics_version',None)
    if old_version is not None: report['source_semantics_version']=old_version
    p.write_text(json.dumps(report))
    with pytest.raises(ValueError,match='semantic'):
        combine(root,quarters=quarters,n_loans=3)
    assert not (root/'combined').exists()


def test_cross_quarter_overlap_rejects_a_paid_off_source_id_before_output(rebuilt_two_quarters):
    root, quarters, validated = rebuilt_two_quarters
    source_ids = root / 'quarters' / quarters[1] / 'rebuilt/eligible_source_ids.parquet'
    original_ids = pl.read_parquet(source_ids)
    # Duplicate an extinct Q1 loan that is absent from both survivor snapshots.
    pl.concat([original_ids, pl.DataFrame({'loan_sequence_number': ['F20Q1000003']})]).write_parquet(source_ids)
    with pytest.raises(ValueError, match='Cross-quarter original loan ID overlap'):
        combine(root, quarters=quarters, n_loans=3)
    assert validated == quarters
    assert not (root / 'combined').exists()


def test_stratified_sampling_is_reproducible_for_a_fixed_pool_and_seed():
    from loan_sample import _stratified_sample

    pool = pl.DataFrame({'loan_id':['A1', 'A2', 'A3', 'B1', 'B2', 'B3'],
                         'stratum_id':['A'] * 3 + ['B'] * 3})
    samples = {tuple(sorted(_stratified_sample(ordered_pool, 2, 42)['loan_id'].to_list()))
               for ordered_pool in (pool, pool.reverse()) for _ in range(12)}
    assert len(samples) == 1, f'The same fixed pool and seed produced different loans: {samples}'


def test_mixed_layout_combination_binds_exact_source_provenance(rebuilt_two_quarters, monkeypatch):
    from schema import RELEASE47_SOURCE_SEMANTICS_VERSION, source_layout_metadata, SOURCE_SEMANTICS_VERSION
    import combine_freddie_rebuild as stage
    root, quarters, _ = rebuilt_two_quarters
    path = root / 'quarters' / quarters[1] / 'rebuilt/report.json'
    report = json.loads(path.read_text())
    report.update(source_semantics_version=RELEASE47_SOURCE_SEMANTICS_VERSION,
                  source_layout=source_layout_metadata('release47'))
    path.write_text(json.dumps(report))
    monkeypatch.setattr(stage, 'validate_completed', lambda p: {
        'storage_policy': 'local_archive_retained'} if p.name == quarters[1] else {})
    result = combine(root, quarters=quarters, n_loans=3)
    assert result['source_semantics_version'] == 'freddie-mixed-layout-reo-priority-v4'
    assert result['source_semantics_by_quarter'] == dict(zip(quarters, [SOURCE_SEMANTICS_VERSION, RELEASE47_SOURCE_SEMANTICS_VERSION]))
    assert result['source_layouts_by_quarter'] == dict(zip(quarters, [source_layout_metadata('native32'), source_layout_metadata('release47')]))
    assert result['source_receipt_types_by_quarter'] == dict(zip(quarters, ['native_cloud', 'local_archive_retained']))


def test_release47_report_requires_canonical_layout(rebuilt_two_quarters):
    from schema import RELEASE47_SOURCE_SEMANTICS_VERSION
    root, quarters, _ = rebuilt_two_quarters
    path = root / 'quarters' / quarters[1] / 'rebuilt/report.json'
    report = json.loads(path.read_text())
    report['source_semantics_version'] = RELEASE47_SOURCE_SEMANTICS_VERSION
    report.pop('source_layout', None)
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match='layout'):
        combine(root, quarters=quarters, n_loans=3)
    assert not (root / 'combined').exists()
