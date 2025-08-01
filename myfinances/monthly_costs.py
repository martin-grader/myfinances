import pandas as pd
from pandera.typing import DataFrame

from myfinances.label_data import TransactionLabeled
from myfinances.monthly_transactions import MonthlyTransactions


class MonthlyCosts(MonthlyTransactions):
    def __init__(self, df: DataFrame[TransactionLabeled], month_split_day: int = 2) -> None:
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

    def get_monthly_expenses(self):
        df_monthly_expenses = pd.DataFrame()
        for df in self.iterate_months():
            date_income: pd.Timestamp = df[TransactionLabeled.Date].min()
            date_income = date_income.replace(day=1)
            expenses: float = df[TransactionLabeled.Amount].sum()
            expenses_this_month: pd.DataFrame = pd.DataFrame(
                {
                    TransactionLabeled.Date: [date_income],
                    TransactionLabeled.Amount: [expenses],
                }
            )
            df_monthly_expenses = pd.concat([df_monthly_expenses, expenses_this_month])
        return df_monthly_expenses
