import pandas as pd
import pytest
from pandas._libs import NaTType
from pandera.typing import DataFrame

from myfinances.label_data import TransactionLabeled
from myfinances.monthly_transactions import (
    DateError,
    DateValidityChecker,
    MonthlyTransactions,
    MonthSplitDateValidityChecker,
)
from myfinances.utils import get_next_day, get_previous_day, get_previous_month


@pytest.fixture()
def start_date() -> pd.Timestamp | NaTType:
    return pd.Timestamp(year=2024, month=1, day=3)


@pytest.fixture()
def end_date() -> pd.Timestamp | NaTType:
    return pd.Timestamp(year=2024, month=4, day=20)


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
def month_split_day() -> int:
    return 1


@pytest.fixture
def monthly_transactions(df_test, month_split_day) -> MonthlyTransactions:
    return MonthlyTransactions(df_test, month_split_day)


@pytest.fixture
def monthly_transactions_two_accounts(df_test_two_accounts, month_split_day) -> MonthlyTransactions:
    return MonthlyTransactions(df_test_two_accounts, month_split_day)


@pytest.fixture
def date_to_start_expected() -> pd.Timestamp | NaTType | None:
    return pd.Timestamp(year=2024, month=2, day=1)


@pytest.fixture
def date_to_end_expected() -> pd.Timestamp | NaTType | None:
    return pd.Timestamp(year=2024, month=3, day=31)


def test_set_date_to_start_below_data(monthly_transactions, date_to_start_expected) -> None:
    date_to_start_valid: pd.Timestamp = monthly_transactions.get_date_to_start()
    with pytest.raises(DateError):
        monthly_transactions.set_date_to_start(get_previous_month(date_to_start_expected))
    assert monthly_transactions.get_date_to_start() == date_to_start_valid


def test_set_date_to_start_above_data(monthly_transactions, date_to_end_expected) -> None:
    date_to_start_valid: pd.Timestamp = monthly_transactions.get_date_to_start()
    with pytest.raises(DateError):
        monthly_transactions.set_date_to_start(get_next_day(date_to_end_expected))
    assert monthly_transactions.get_date_to_start() == date_to_start_valid


def test_set_date_to_start_wrong_day(monthly_transactions, date_to_start_expected) -> None:
    date_to_start_valid: pd.Timestamp = monthly_transactions.get_date_to_start()
    with pytest.raises(DateError):
        monthly_transactions.set_date_to_start(get_next_day(date_to_start_expected))
    assert monthly_transactions.get_date_to_start() == date_to_start_valid


def test_set_date_to_start_ge_date_to_end(monthly_transactions) -> None:
    date_to_start_valid: pd.Timestamp = monthly_transactions.get_date_to_start()
    monthly_transactions.set_date_to_end(pd.Timestamp(year=2024, month=2, day=29))
    with pytest.raises(DateError):
        monthly_transactions.set_date_to_start(pd.Timestamp(year=2024, month=3, day=1))
    assert monthly_transactions.get_date_to_start() == date_to_start_valid


def test_set_end_to_start_below_data(monthly_transactions, date_to_start_expected) -> None:
    date_to_end_valid: pd.Timestamp = monthly_transactions.get_date_to_end()
    with pytest.raises(DateError):
        monthly_transactions.set_date_to_end(get_previous_month(date_to_start_expected))
    assert monthly_transactions.get_date_to_end() == date_to_end_valid


def test_set_date_to_end_above_data(monthly_transactions, date_to_end_expected) -> None:
    date_to_end_valid: pd.Timestamp = monthly_transactions.get_date_to_end()
    with pytest.raises(DateError):
        monthly_transactions.set_date_to_end(get_next_day(date_to_end_expected))
    assert monthly_transactions.get_date_to_end() == date_to_end_valid


def test_set_date_to_end_wrong_day(monthly_transactions, date_to_end_expected) -> None:
    date_to_end_valid: pd.Timestamp = monthly_transactions.get_date_to_end()
    with pytest.raises(DateError):
        monthly_transactions.set_date_to_end(get_previous_day(date_to_end_expected))
    assert monthly_transactions.get_date_to_end() == date_to_end_valid


def test_set_date_to_end_le_date_to_start(monthly_transactions) -> None:
    date_to_end_valid: pd.Timestamp = monthly_transactions.get_date_to_end()
    monthly_transactions.set_date_to_start(pd.Timestamp(year=2024, month=3, day=1))
    with pytest.raises(DateError):
        monthly_transactions.set_date_to_end(pd.Timestamp(year=2024, month=2, day=29))
    assert monthly_transactions.get_date_to_end() == date_to_end_valid


class MonthlyTransactionsMock:
    def get_date_to_start(self) -> pd.Timestamp | NaTType | None:
        return pd.Timestamp(year=2024, month=2, day=1)

    def get_date_to_end(self) -> pd.Timestamp | NaTType | None:
        return pd.Timestamp(year=2024, month=3, day=31)

    def get_month_split_day(self) -> int:
        return 2

    def get_min_date_to_start(self) -> pd.Timestamp | NaTType | None:
        return pd.Timestamp(year=2024, month=2, day=1)

    def get_max_date_to_end(self) -> pd.Timestamp | NaTType | None:
        return pd.Timestamp(year=2024, month=3, day=31)


def test_date_validity_checker() -> None:
    target = MonthlyTransactionsMock()
    with pytest.raises(DateError):
        DateValidityChecker(target).execute()  # type: ignore


@pytest.mark.parametrize('month_split_day', [0, 29, 2.3])
def test_split_day_wrong(month_split_day) -> None:
    with pytest.raises(DateError):
        MonthSplitDateValidityChecker().execute(month_split_day)
