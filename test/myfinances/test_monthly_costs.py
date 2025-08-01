import pandas as pd
import pytest
from pandera.typing import DataFrame

from myfinances.label_data import TransactionLabeled
from myfinances.monthly_costs import MonthlyCosts


@pytest.fixture
def start_date() -> pd.Timestamp:
    return pd.Timestamp(year=2024, month=1, day=2)  # type:ignore


@pytest.fixture
def end_date() -> pd.Timestamp:
    return pd.Timestamp(year=2024, month=4, day=30)  # type:ignore


@pytest.fixture
def dates(start_date, end_date) -> pd.DatetimeIndex:
    return pd.date_range(start=start_date, end=end_date)


@pytest.fixture
def df_test(dates) -> DataFrame[TransactionLabeled]:
    days: int = dates.shape[0]
    df = pd.DataFrame(
        {
            TransactionLabeled.Amount: [0] * days,
            TransactionLabeled.Date: dates,
            TransactionLabeled.Account: ['Martin'] * days,
            TransactionLabeled.Text: ['sample'] * days,
            TransactionLabeled.Label: ['test_label'] * days,
            TransactionLabeled.Sublabel: ['test_sublabel'] * days,
        }
    )
    df.loc[21:23, TransactionLabeled.Amount] = 10.0
    df.loc[26:28, TransactionLabeled.Amount] = -20.0
    return df  # type:ignore


@pytest.fixture
def month_split_day() -> int:
    return 5


@pytest.fixture
def monthly_costs(df_test, month_split_day):
    monthly_costs = MonthlyCosts(df_test, month_split_day)
    return monthly_costs


def test_get_income(monthly_costs) -> None:
    income_expected = 10 * 3
    assert monthly_costs.get_income() == income_expected


def test_get_averaged_income(monthly_costs) -> None:
    averaged_income_expected: float = 10 * 3 / 3
    averaged_income: DataFrame[TransactionLabeled] = monthly_costs.get_averaged_income()
    assert averaged_income.loc[0, TransactionLabeled.Amount] == averaged_income_expected


def test_get_expenses(monthly_costs) -> None:
    expenses_expected = -20 * 3
    assert monthly_costs.get_expenses() == expenses_expected


def test_drop_costs(monthly_costs):
    monthly_costs.drop_costs('test_label', 'test_sublabel')
    assert monthly_costs.get_transactions().empty


@pytest.mark.parametrize(
    'label, sublabel',
    [
        ('non-existent_label', 'test_sublabel'),
        ('test_label', 'non_existent_sublabel'),
        ('non_existent_label', 'non_existent_sublabel'),
    ],
)
def test_drop_costs_fails(monthly_costs, label, sublabel) -> None:
    with pytest.raises(KeyError):
        monthly_costs.drop_costs(label, sublabel)
