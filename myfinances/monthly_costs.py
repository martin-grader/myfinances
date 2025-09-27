import pandas as pd
from pandera.typing import DataFrame

from myfinances.label_data import TransactionLabeled
from myfinances.monthly_transactions import MonthlyTransactions


class MonthlyCosts(MonthlyTransactions):
    def __init__(self, df: DataFrame[TransactionLabeled], month_split_day: int = 1) -> None:
        super().__init__(df, month_split_day)
        # self.expenses: float = self.get_expenses()
        # self.income: float = self.get_income()

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
            .reset_index()
        )

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

    def get_monthly_expenses(self) -> pd.DataFrame:
        df_monthly_expenses: pd.DataFrame = pd.DataFrame()
        for df in self.iterate_months():
            date_income: pd.Timestamp = df[TransactionLabeled.Date].min()
            date_income: pd.Timestamp = date_income.replace(day=self._month_split_day)
            expenses: float = df[TransactionLabeled.Amount].sum()
            expenses_this_month: pd.DataFrame = pd.DataFrame(
                {
                    TransactionLabeled.Date: [date_income],
                    TransactionLabeled.Amount: [expenses],
                }
            )
            df_monthly_expenses: pd.DataFrame = pd.concat(
                [
                    df_monthly_expenses,
                    expenses_this_month,
                ]
            )
        return df_monthly_expenses

    def get_monthly_expenses_by_label(self, label: str) -> pd.DataFrame:
        df_monthly_expenses: pd.DataFrame = pd.DataFrame()
        for df in self.iterate_months():
            df_label = df.loc[df[TransactionLabeled.Label] == label]
            date_income: pd.Timestamp = df_label[TransactionLabeled.Date].min()
            date_income: pd.Timestamp = date_income.replace(day=self._month_split_day)
            expenses: float = df_label[TransactionLabeled.Amount].sum()
            expenses_this_month: pd.DataFrame = pd.DataFrame(
                {
                    TransactionLabeled.Date: [date_income],
                    TransactionLabeled.Amount: [expenses],
                }
            )
            df_monthly_expenses: pd.DataFrame = pd.concat(
                [
                    df_monthly_expenses,
                    expenses_this_month,
                ]
            )
        return df_monthly_expenses

    def get_monthly_expenses_by_sublabel(self, label: str, sublabel: str) -> pd.DataFrame:
        df_monthly_expenses: pd.DataFrame = pd.DataFrame()
        for df in self.iterate_months():
            df_label = df.loc[
                (df[TransactionLabeled.Label] == label)
                & (df[TransactionLabeled.Sublabel] == sublabel)
            ]
            date_income: pd.Timestamp = df_label[TransactionLabeled.Date].min()
            date_income: pd.Timestamp = date_income.replace(day=self._month_split_day)
            expenses: float = df_label[TransactionLabeled.Amount].sum()
            expenses_this_month: pd.DataFrame = pd.DataFrame(
                {
                    TransactionLabeled.Date: [date_income],
                    TransactionLabeled.Amount: [expenses],
                }
            )
            df_monthly_expenses: pd.DataFrame = pd.concat(
                [
                    df_monthly_expenses,
                    expenses_this_month,
                ]
            )
        return df_monthly_expenses

    def get_daily_expenses(self) -> pd.DataFrame:
        df: DataFrame[TransactionLabeled] = self.get_transactions()
        df_daily_expenses: pd.DataFrame = df.loc[
            :, [TransactionLabeled.Date, TransactionLabeled.Amount]
        ]
        return df_daily_expenses.groupby(by=[TransactionLabeled.Date]).sum().reset_index()
