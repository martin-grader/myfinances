from pathlib import Path

import pandas as pd
from loguru import logger as log
from pandera.typing import DataFrame

from myfinances.config_utils import AddLabels, DropLabels
from myfinances.label_data import TransactionLabeled
from myfinances.monthly_transactions import MonthlyTransactions


class MonthlyCosts(MonthlyTransactions):
    def __init__(self, df: DataFrame[TransactionLabeled], month_split_day: int = 2) -> None:
        super().__init__(df, month_split_day)
        self.expenses: float = self.get_expenses()
        self.income: float = self.get_income()

    def get_expenses(self) -> float:
        expenses: float = self.df.loc[
            self.df[TransactionLabeled.Amount] < 0, TransactionLabeled.Amount
        ].sum()
        return expenses

    def get_income(self) -> float:
        income: float = self.df.loc[
            self.df[TransactionLabeled.Amount] > 0, TransactionLabeled.Amount
        ].sum()
        return income

    def get_averaged_expenses_by_label(self) -> pd.api.typing.DataFrameGroupBy:
        total_grouped_expenses: pd.api.typing.DataFrameGroupBy = (
            self.df.groupby([TransactionLabeled.Label])[TransactionLabeled.Amount]
            .sum()
            .div(self.months_to_analyze)
            .sort_values()
        )  # type: ignore
        return total_grouped_expenses

    def get_averaged_expenses_by_sublabel(
        self, label: TransactionLabeled.Label
    ) -> pd.api.typing.DataFrameGroupBy:
        total_grouped_expenses: pd.api.typing.DataFrameGroupBy = (
            self.df[self.df[TransactionLabeled.Label] == label]
            .groupby([TransactionLabeled.Sublabel])[TransactionLabeled.Amount]
            .sum()
            .div(self.months_to_analyze)
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

    def drop_costs(self, label: str, sublabel: str) -> None:
        to_drop: pd.Series = (self.df[TransactionLabeled.Label] == label) & (
            self.df[TransactionLabeled.Sublabel] == sublabel
        )
        if to_drop.sum() == 0:
            log.error(
                f'Transaction not found in monthly costs! Label: {label}, Sublabel: {sublabel}'
            )
            raise KeyError
        else:
            self.df: DataFrame[TransactionLabeled] = self.df.loc[~to_drop]

    def drop_costs_by_config(self, file_name: Path) -> None:
        drop_labels = DropLabels(file_name)
        for transaction in drop_labels.transactions:
            self.drop_costs(transaction.Label, transaction.Sublabel)
        self.expenses: float = self.get_expenses()
        self.income: float = self.get_income()

    def add_costs_by_config(self, file_name: Path) -> None:
        add_labels = AddLabels(file_name)
        all_dfs_to_add: list[DataFrame[TransactionLabeled]] = []
        for df in self.iterate_months():
            date_income: pd.Timestamp = df[TransactionLabeled.Date].min()
            df_to_add: DataFrame[TransactionLabeled] = pd.DataFrame(add_labels.transactions_clean)  # type: ignore
            df_to_add[TransactionLabeled.Date] = date_income
            df_to_add[TransactionLabeled.Text] = 'Zukunft'
            all_dfs_to_add.append(df_to_add)
        df_to_add_all_configs: DataFrame[TransactionLabeled] = pd.concat(all_dfs_to_add)  # type:ignore
        self.df = pd.concat([self.df, df_to_add_all_configs])  # type: ignore
