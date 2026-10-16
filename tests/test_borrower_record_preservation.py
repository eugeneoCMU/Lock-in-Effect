import pandas as pd
import pytest
from borrower_record_preservation import assert_preserved_records


def panel(balance=100000.):
    return pd.DataFrame(dict(loan_id=['a'],reporting_period=['202205'],balance=[balance]))


def test_small_numeric_change_cannot_pass_preservation():
    with pytest.raises(AssertionError):assert_preserved_records(panel(),panel(100000.1))


def test_nested_rows_can_reorder_without_changing_values():
    expanded=pd.concat([panel().assign(loan_id='b'),panel()],ignore_index=True)
    assert_preserved_records(panel(),expanded)


def test_missing_original_record_and_duplicates_rejected():
    with pytest.raises(ValueError):assert_preserved_records(panel(),panel().assign(loan_id='b'))
    with pytest.raises(ValueError):assert_preserved_records(panel(),pd.concat([panel(),panel()]))
