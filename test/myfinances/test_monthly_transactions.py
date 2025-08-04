import pandas as pd
import pytest
from pandera.typing import DataFrame

from myfinances.label_data import TransactionLabeled
from myfinances.monthly_transactions import MonthlyTransactions


@pytest.fixture
def month_start() -> int:
    return 1


@pytest.fixture
def month_end() -> int:
    return 4


@pytest.fixture
def start_date(month_start) -> pd.Timestamp:
    return pd.Timestamp(year=2024, month=month_start, day=1)  # type:ignore


@pytest.fixture
def end_date(month_end) -> pd.Timestamp:
    return pd.Timestamp(year=2024, month=month_end, day=30)  # type:ignore


@pytest.fixture
def dates(start_date, end_date) -> pd.DatetimeIndex:
    return pd.date_range(start=start_date, end=end_date)


@pytest.fixture
def df_test(dates) -> DataFrame[TransactionLabeled]:
    days: int = dates.shape[0]
    df = pd.DataFrame(
        {
            TransactionLabeled.Amount: [0.0] * days,
            TransactionLabeled.Date: dates,
            TransactionLabeled.Account: ['Martin'] * days,
            TransactionLabeled.Text: ['sample'] * days,
        }
    )
    return df  # type:ignore


@pytest.fixture
def df_test_two_accounts(dates, df_test, month_split_day) -> DataFrame[TransactionLabeled]:
    days: int = dates.shape[0]
    df_test.loc[month_split_day, TransactionLabeled.Account] = 'Miri'
    df_test.loc[days - 1, TransactionLabeled.Account] = 'Miri'
    return df_test


@pytest.fixture
def month_split_day() -> int:
    return 5


@pytest.fixture
def monthly_transactions(df_test, month_split_day):
    return MonthlyTransactions(df_test, month_split_day)


@pytest.fixture
def monthly_transactions_two_accounts(df_test_two_accounts, month_split_day):
    return MonthlyTransactions(df_test_two_accounts, month_split_day)


def test_month_split_day(monthly_transactions, month_split_day) -> None:
    assert monthly_transactions.month_split_day == month_split_day


def test_date_to_start(monthly_transactions, month_split_day, start_date) -> None:
    start_date_expected = start_date + pd.to_timedelta(month_split_day - 1, unit='d')
    assert monthly_transactions.get_date_to_start() == start_date_expected


def test_date_to_start_two_accounts(
    monthly_transactions_two_accounts, month_split_day, start_date
) -> None:
    assert monthly_transactions_two_accounts.get_date_to_start() == pd.Timestamp(
        year=start_date.year, month=start_date.month + 1, day=month_split_day
    )


def test_date_to_end(monthly_transactions, month_split_day, end_date) -> None:
    assert monthly_transactions.get_date_to_end() == pd.Timestamp(
        year=end_date.year, month=end_date.month, day=month_split_day - 1
    )


def test_get_n_months_to_analyze(monthly_transactions, start_date, end_date) -> None:
    n_months_to_analyze_expected: int = end_date.month - start_date.month
    assert monthly_transactions.get_n_months_to_analyze() == n_months_to_analyze_expected


def test_get_months_to_analyze_start(
    monthly_transactions, month_split_day, month_start, month_end
) -> None:
    months_expected = [
        pd.Timestamp(year=2024, month=m, day=month_split_day) for m in range(month_start, month_end)
    ]
    assert monthly_transactions.get_months_to_analyze_start() == months_expected


def test_get_months_to_analyze_end(
    monthly_transactions, month_split_day, month_start, month_end
) -> None:
    months_expected = [
        pd.Timestamp(year=2024, month=m + 1, day=month_split_day - 1)
        for m in range(month_start, month_end)
    ]
    assert monthly_transactions.get_months_to_analyze_end() == months_expected


def test_df(monthly_transactions, df_test, start_date, end_date, month_split_day) -> None:
    df_expected = df_test.iloc[
        (start_date.day + month_split_day - 2) : -(end_date.day - month_split_day + 1)
    ]
    pd.testing.assert_frame_equal(monthly_transactions.get_transactions(), df_expected)
