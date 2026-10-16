"""Current publication checks complement preserved historical manuscript gates."""
from pathlib import Path
import json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def load(n):return json.loads((ROOT/'hazard/data'/n).read_text())

def test_reported_and_closed_results_are_distinct_and_reconciled():
    r=load('stock_flow_accounting_2026-10-07_results.json')
    assert r['production_parity_pass']
    assert abs(r['production_parity_difference_b'])<1e-6
    p=r['paths'];assert p['closed']['marginal_b']<p['production']['marginal_b']
    for row in p.values():
        assert abs(row['marginal_b']-(row['off_principal_b']-row['on_principal_b']))<1e-9
        assert abs(row['marginal_pp']-100*row['marginal_b']/r['benchmark_b'])<1e-10
    assert r['off_max_active_identity_error_b']<1e-10
    assert r['on_max_active_identity_error_b']<1e-10

def test_bridge_has_fixed_ids_exact_targets_and_paired_parity():
    r=load('coupon_bridge_2026-10-07_results.json');assert r['unique_ids']==75000
    assert abs(r['bridge80_parity_difference_b'])<1e-6
    assert len({b['weights_sha256'] for b in r['bridges'].values()})==3
    for b in r['bridges'].values():
        assert b['status']=='supported' and len(b['cell_counts'])==12
        assert b['missing_target_share']==0 and b['max_share_error']<1e-8
        assert b['candidate_loans']==r['unique_ids']
        assert b['positive_weight_loans']==sum(b['cell_counts'].values())

def test_retrospective_scores_reconcile_and_retain_adverse_result():
    r=load('pathb_validation_2026-10-07_results.json')
    assert r['training_end']<r['evaluation_start']<r['evaluation_end']
    assert r['months']==21
    for name,total in r['aggregate'].items():
        for group in ['coupon_vintage','subperiods']:
            for key in ['observed_b','predicted_b','exposure_b_months']:
                assert np.isclose(sum(x[name][key] for x in r[group].values()),total[key])
    assert r['aggregate']['on']['weighted_rmse_monthly_pp']>r['aggregate']['base']['weighted_rmse_monthly_pp']

def test_figure_precise_points_match_artifacts():
    from figures.make_specification_sensitivity import load_rows
    rows,hashes=load_rows();assert len(rows)==9
    assert abs(rows[-2]['value']-load('psa_level_sweep_results.json')['cells']['4.991|150|6.5']['marginal_pp'])<1e-12
    for name,h in hashes.items():assert h==hashlib.sha256((ROOT/'hazard/data'/name).read_bytes()).hexdigest()
