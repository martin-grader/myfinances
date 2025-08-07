import pandas as pd
import pytest
from pandas._libs import NaTType
from pandera.typing import DataFrame

from myfinances.label_data import TransactionLabeled
from myfinances.monthly_transactions import MonthlyTransactions
from myfinances.utils import get_next_month, get_previous_day


@pytest.fixture(
    params=[
        pd.Timestamp(year=2022, month=1, day=30),
        pd.Timestamp(year=2024, month=1, day=1),
        pd.Timestamp(year=2024, month=1, day=5),
    ],
    ids=['start_30_01_2022', 'start_01_01_2024', 'start_05_01_2024'],
)
def start_date(request) -> pd.Timestamp:
    return request.param


@pytest.fixture(
    params=[
        pd.Timestamp(year=2024, month=4, day=30),
        pd.Timestamp(year=2024, month=4, day=3),
    ],
    ids=['end_30_04_2024', 'end_03_04_2024'],
)
def end_date(request) -> pd.Timestamp:
    return request.param


@pytest.fixture
def dates(start_date, end_date) -> pd.DatetimeIndex:
    return pd.date_range(start=start_date, end=end_date)


@pytest.fixture
def df_test(dates) -> DataFrame[TransactionLabeled]:
    days: int = dates.shape[0]
    df: DataFrame[TransactionLabeled] = pd.DataFrame(
        {
            TransactionLabeled.Amount: [0.0] * days,
            TransactionLabeled.Date: dates,
            TransactionLabeled.Account: ['Martin'] * days,
            TransactionLabeled.Text: ['sample'] * days,
        }
    )  # type: ignore
    return df


@pytest.fixture
def df_test_two_accounts(dates, df_test, month_split_day) -> DataFrame[TransactionLabeled]:
    days: int = dates.shape[0]
    df_test.loc[month_split_day, TransactionLabeled.Account] = 'Miri'
    df_test.loc[days - 1, TransactionLabeled.Account] = 'Miri'
    return df_test


@pytest.fixture(
    params=[1, 2, 15, 27], ids=['split_day_1', 'split_day_2', 'split_day_15', 'split_day_27']
)
def month_split_day(request) -> int:
    return request.param


@pytest.fixture
def monthly_transactions(df_test, month_split_day) -> MonthlyTransactions:
    return MonthlyTransactions(df_test, month_split_day)


@pytest.fixture
def monthly_transactions_two_accounts(df_test_two_accounts, month_split_day) -> MonthlyTransactions:
    return MonthlyTransactions(df_test_two_accounts, month_split_day)


@pytest.fixture
def date_to_start_expected(start_date, month_split_day) -> pd.Timestamp | NaTType | None:
    if start_date == pd.Timestamp(year=2022, month=1, day=30):
        if month_split_day == 1:
            return pd.Timestamp(year=2022, month=2, day=1)
        elif month_split_day == 2:
            return pd.Timestamp(year=2022, month=2, day=2)
        elif month_split_day == 15:
            return pd.Timestamp(year=2022, month=2, day=15)
        elif month_split_day == 27:
            return pd.Timestamp(year=2022, month=2, day=27)
        else:
            assert False
    elif start_date == pd.Timestamp(year=2024, month=1, day=1):
        if month_split_day == 1:
            return pd.Timestamp(year=2024, month=1, day=1)
        elif month_split_day == 2:
            return pd.Timestamp(year=2024, month=1, day=2)
        elif month_split_day == 15:
            return pd.Timestamp(year=2024, month=1, day=15)
        elif month_split_day == 27:
            return pd.Timestamp(year=2024, month=1, day=27)
        else:
            assert False
    if start_date == pd.Timestamp(year=2024, month=1, day=5):
        if month_split_day == 1:
            return pd.Timestamp(year=2024, month=2, day=1)
        elif month_split_day == 2:
            return pd.Timestamp(year=2024, month=2, day=2)
        elif month_split_day == 15:
            return pd.Timestamp(year=2024, month=1, day=15)
        elif month_split_day == 27:
            return pd.Timestamp(year=2024, month=1, day=27)
        else:
            assert False


@pytest.fixture
def date_to_end_expected(end_date, month_split_day) -> pd.Timestamp | NaTType | None:
    if end_date == pd.Timestamp(year=2024, month=4, day=30):
        if month_split_day == 1:
            return pd.Timestamp(year=2024, month=4, day=30)
        elif month_split_day == 2:
            return pd.Timestamp(year=2024, month=4, day=1)
        elif month_split_day == 15:
            return pd.Timestamp(year=2024, month=4, day=14)
        elif month_split_day == 27:
            return pd.Timestamp(year=2024, month=4, day=26)
        else:
            assert False
    if end_date == pd.Timestamp(year=2024, month=4, day=3):
        if month_split_day == 1:
            return pd.Timestamp(year=2024, month=3, day=31)
        elif month_split_day == 2:
            return pd.Timestamp(year=2024, month=4, day=1)
        elif month_split_day == 15:
            return pd.Timestamp(year=2024, month=3, day=14)
        elif month_split_day == 27:
            return pd.Timestamp(year=2024, month=3, day=26)
        else:
            assert False


def test_month_split_day(monthly_transactions, month_split_day) -> None:
    assert monthly_transactions.month_split_day == month_split_day


def test_date_to_start(monthly_transactions, date_to_start_expected) -> None:
    assert monthly_transactions.get_date_to_start() == date_to_start_expected


def test_date_to_start_two_accounts(
    monthly_transactions_two_accounts, month_split_day, start_date
) -> None:
    assert monthly_transactions_two_accounts.get_date_to_start() == pd.Timestamp(
        year=start_date.year, month=start_date.month + 1, day=month_split_day
    )


def test_date_to_end(monthly_transactions, date_to_end_expected) -> None:
    assert monthly_transactions.get_date_to_end() == date_to_end_expected


def test_get_n_months_to_analyze(
    monthly_transactions, date_to_start_expected, date_to_end_expected
) -> None:
    n_months_to_analyze_expected: int = date_to_end_expected.month - date_to_start_expected.month
    n_months_to_analyze_expected += 12 * (date_to_end_expected.year - date_to_start_expected.year)
    if monthly_transactions.month_split_day == 1:
        n_months_to_analyze_expected += 1
    assert monthly_transactions.get_n_months_to_analyze() == n_months_to_analyze_expected


def test_get_months_to_analyze_start(
    monthly_transactions, date_to_start_expected, date_to_end_expected
) -> None:
    months_expected: list[pd.Timestamp] = []
    month_start_date: pd.Timestamp = date_to_start_expected
    while month_start_date < date_to_end_expected:
        months_expected.append(month_start_date)
        month_start_date: pd.Timestamp = get_next_month(month_start_date)
    assert monthly_transactions.get_months_to_analyze_start() == months_expected


def test_get_months_to_analyze_end(
    monthly_transactions, date_to_start_expected, date_to_end_expected
) -> None:
    months_expected: list[pd.Timestamp] = []
    month_start_date: pd.Timestamp = date_to_start_expected
    while month_start_date < date_to_end_expected:
        month_end_date: pd.Timestamp = get_previous_day(get_next_month(month_start_date))
        months_expected.append(month_end_date)
        month_start_date: pd.Timestamp = get_next_month(month_start_date)
    assert monthly_transactions.get_months_to_analyze_end() == months_expected


def test_df(monthly_transactions, df_test, date_to_start_expected, date_to_end_expected) -> None:
    df_expected: DataFrame[TransactionLabeled] = df_test.loc[
        (df_test[TransactionLabeled.Date] >= date_to_start_expected)
        & (df_test[TransactionLabeled.Date] <= date_to_end_expected)
    ]
    pd.testing.assert_frame_equal(monthly_transactions.get_transactions(), df_expected)
