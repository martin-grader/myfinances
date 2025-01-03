import pandas as pd
import pytest

import myfinances.utils as u
from myfinances.parse_data import Transaction


@pytest.fixture
def df() -> pd.DataFrame:
    df: pd.DataFrame = pd.DataFrame({Transaction.Text: ['abba', 'acdc', 'abab']})
    return df


def test_get_rows_by_string(df) -> None:
    ser_expected: pd.Series = pd.Series([True, False, True], name=Transaction.Text)
    ser: pd.Series = u.get_rows_by_string(df, 'ab')
    pd.testing.assert_series_equal(ser, ser_expected)


def test_get_rows_by_exact_string(df) -> None:
    ser_expected: pd.Series = pd.Series([False, True, False], name=Transaction.Text)
    ser: pd.Series = u.get_rows_by_exact_string(df, 'acdc')
    pd.testing.assert_series_equal(ser, ser_expected)
