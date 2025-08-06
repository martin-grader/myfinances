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


@pytest.mark.parametrize(
    'this_day, previous_day_expected',
    [
        (pd.Timestamp(year=2025, month=4, day=4), pd.Timestamp(year=2025, month=4, day=3)),
        (pd.Timestamp(year=2025, month=4, day=1), pd.Timestamp(year=2025, month=3, day=31)),
        (pd.Timestamp(year=2025, month=3, day=1), pd.Timestamp(year=2025, month=2, day=28)),
        (pd.Timestamp(year=2024, month=3, day=1), pd.Timestamp(year=2024, month=2, day=29)),
        (pd.Timestamp(year=2025, month=7, day=1), pd.Timestamp(year=2025, month=6, day=30)),
        (pd.Timestamp(year=2025, month=1, day=1), pd.Timestamp(year=2024, month=12, day=31)),
    ],
)
def test_get_previous_day(this_day, previous_day_expected) -> None:
    assert u.get_previous_day(this_day) == previous_day_expected


@pytest.mark.parametrize(
    'this_month, previous_month_expected',
    [
        (pd.Timestamp(year=2025, month=4, day=4), pd.Timestamp(year=2025, month=3, day=4)),
        (pd.Timestamp(year=2025, month=4, day=1), pd.Timestamp(year=2025, month=3, day=1)),
        (pd.Timestamp(year=2025, month=7, day=31), pd.Timestamp(year=2025, month=6, day=30)),
        (pd.Timestamp(year=2025, month=1, day=31), pd.Timestamp(year=2024, month=12, day=31)),
    ],
)
def test_get_previous_month(this_month, previous_month_expected) -> None:
    assert u.get_previous_month(this_month) == previous_month_expected


@pytest.mark.parametrize(
    'this_month, next_month_expected',
    [
        (pd.Timestamp(year=2025, month=4, day=4), pd.Timestamp(year=2025, month=5, day=4)),
        (pd.Timestamp(year=2025, month=3, day=1), pd.Timestamp(year=2025, month=4, day=1)),
        (pd.Timestamp(year=2024, month=12, day=10), pd.Timestamp(year=2025, month=1, day=10)),
        (pd.Timestamp(year=2025, month=1, day=31), pd.Timestamp(year=2025, month=2, day=28)),
    ],
)
def test_get_next_month(this_month, next_month_expected) -> None:
    assert u.get_next_month(this_month) == next_month_expected
