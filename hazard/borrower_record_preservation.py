"""Verify a nested sample retains the original monthly values."""
import pandas as pd


def assert_preserved_records(original,expanded):
    order=['loan_id','reporting_period']
    if original.duplicated(order).any() or expanded.duplicated(order).any():
        raise ValueError('Duplicate loan-month in preservation comparison')
    ids=set(original.loan_id)
    if not ids<=set(expanded.loan_id):raise ValueError('Original loan missing')
    retained=expanded[expanded.loan_id.isin(ids)]
    pd.testing.assert_frame_equal(original.sort_values(order).reset_index(drop=True),
        retained.sort_values(order).reset_index(drop=True),check_dtype=False,check_exact=True)
