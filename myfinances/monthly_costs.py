import pandas as pd
from pandera.typing import DataFrame

from myfinances.label_data import TransactionLabeled
from myfinances.monthly_transactions import MonthlyTransactions


class MonthlyCosts(MonthlyTransactions):
    def __init__(self, df: DataFrame[TransactionLabeled], month_split_day: int = 1) -> None:
        super().__init__(df, month_split_day)

    def get_expenses(self) -> float:
        df: DataFrame[TransactionLabeled] = self.get_transactions()
        expenses: float = df.loc[df[TransactionLabeled.Amount] < 0, TransactionLabeled.Amount].sum()
        return expenses

    def get_income(self) -> float:
        positive_transactions: DataFrame[TransactionLabeled] = self._get_positive_transactions()
        income: float = positive_transactions[TransactionLabeled.Amount].sum()
        return income

    def get_averaged_income(self) -> pd.DataFrame:
        positive_transactions: DataFrame[TransactionLabeled] = self._get_positive_transactions()
        total_grouped_income: pd.DataFrame = (
            positive_transactions.groupby([TransactionLabeled.Sublabel])[TransactionLabeled.Amount]
            .sum()
            .div(self.get_n_months_to_analyze())
            .sort_values()
        )  # type: ignore

        return total_grouped_income

    def _get_positive_transactions(self) -> DataFrame[TransactionLabeled]:
        df: DataFrame[TransactionLabeled] = self.get_transactions()
        positive_transactions: DataFrame[TransactionLabeled] = df.loc[
            df[TransactionLabeled.Amount] > 0, :
        ]
        return positive_transactions

    def get_averaged_expenses_by_label(self) -> pd.api.typing.DataFrameGroupBy:
        df: DataFrame[TransactionLabeled] = self.get_transactions()
        total_grouped_expenses: pd.api.typing.DataFrameGroupBy = (
            df.groupby([TransactionLabeled.Label])[TransactionLabeled.Amount]
            .sum()
            .div(self.get_n_months_to_analyze())
            .sort_values()
        )  # type: ignore
        return total_grouped_expenses

    def get_averaged_expenses_by_sublabel(self, label: str) -> pd.api.typing.DataFrameGroupBy:
        df: DataFrame[TransactionLabeled] = self.get_transactions()
        total_grouped_expenses: pd.api.typing.DataFrameGroupBy = (
            df[df[TransactionLabeled.Label] == label]
            .groupby([TransactionLabeled.Sublabel])[TransactionLabeled.Amount]
            .sum()
            .div(self.get_n_months_to_analyze())
            .sort_values()
        )  # type: ignore
        return total_grouped_expenses

    def get_monthly_expenses(self, additional_labels=[]) -> pd.DataFrame:
        monthly_expenses: list = []
        groupby_labels: list = [TransactionLabeled.Date] + additional_labels
        for df in self.iterate_months():
            date_income: pd.Timestamp = df[TransactionLabeled.Date].min()
            df.loc[:, TransactionLabeled.Date] = date_income.replace(day=self._month_split_day)
            monthly_expenses.append(df.groupby(groupby_labels).sum().reset_index())
        return pd.concat(monthly_expenses).reset_index(drop=True)

    def get_monthly_expenses_by_label(self, label: str) -> pd.DataFrame:
        expenses = self.get_monthly_expenses([TransactionLabeled.Label])
        return expenses.loc[expenses[TransactionLabeled.Label] == label]

    def get_monthly_expenses_by_sublabel(self, label: str, sublabel: str) -> pd.DataFrame:
        expenses = self.get_monthly_expenses(
            [
                TransactionLabeled.Label,
                TransactionLabeled.Sublabel,
            ]
        )
        return expenses.loc[
            (expenses[TransactionLabeled.Label] == label)
            & (expenses[TransactionLabeled.Sublabel] == sublabel)
        ]

    def get_relative_monthly_expenses_by_sublabel(self, label: str, sublabel: str) -> pd.DataFrame:
        df_label = self.get_monthly_expenses_by_label(label)
        df_sublabel = self.get_monthly_expenses_by_sublabel(label, sublabel)
        df_relative = pd.merge(
            df_sublabel,
            df_label[[TransactionLabeled.Date, TransactionLabeled.Amount]],
            how='left',
            on=TransactionLabeled.Date,
            suffixes=('', '_label'),
        )
        df_relative.loc[:, TransactionLabeled.Amount] = (
            df_relative[TransactionLabeled.Amount]
            / df_relative[f'{TransactionLabeled.Amount}_label']
            * 100
        )
        df_relative.drop(columns=[f'{TransactionLabeled.Amount}_label'], inplace=True)
        return df_relative

    def get_daily_expenses(self) -> pd.DataFrame:
        df: DataFrame[TransactionLabeled] = self.get_transactions()
        df_daily_expenses: pd.DataFrame = df.loc[
            :, [TransactionLabeled.Date, TransactionLabeled.Amount]
        ]
        return df_daily_expenses.groupby(by=[TransactionLabeled.Date]).sum().reset_index()
