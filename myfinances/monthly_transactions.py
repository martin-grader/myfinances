import datetime
from pathlib import Path
from typing import Generator

import pandas as pd
from loguru import logger as log
from pandera.typing import DataFrame

from myfinances.config_utils import AddLabels, DropLabels
from myfinances.label_data import TransactionLabeled
from myfinances.utils import get_next_month, get_previous_day, get_previous_month


class MonthlyTransactions:
    def __init__(self, df: DataFrame[TransactionLabeled], month_split_day: int = 1) -> None:
        assert month_split_day < 28
        assert month_split_day > 0
        self.month_split_day: int = month_split_day
        self._set_all_transactions(df)
        self._date_to_start: pd.Timestamp = self._day_to_start(df)
        self._date_to_end: pd.Timestamp = self._day_to_end(df)
        self._min_date_to_start: pd.Timestamp = self._day_to_start(df)
        self._max_date_to_end: pd.Timestamp = self._day_to_end(df)

        log.info(
            f'Analyzing {self.get_n_months_to_analyze()} months'
            f' ({self._date_to_start} - {self._date_to_end})'
        )

    def get_transactions(self) -> DataFrame[TransactionLabeled]:
        return self._df.loc[
            (self._df[TransactionLabeled.Date] >= self._date_to_start)
            & (self._df[TransactionLabeled.Date] <= self._date_to_end)
        ]

    def get_date_to_start(self) -> pd.Timestamp:
        return self._date_to_start

    def get_date_to_end(self) -> pd.Timestamp:
        return self._date_to_end

    def set_date_to_start(self, date: pd.Timestamp) -> None:
        assert date.day == self.month_split_day
        self._date_to_start: pd.Timestamp = date

    def set_date_to_end(self, date: pd.Timestamp) -> None:
        # assert date.day == self.month_split_day - 1
        self._date_to_end: pd.Timestamp = date

    def get_min_date_to_start(self) -> pd.Timestamp:
        return self._min_date_to_start

    def get_max_date_to_end(self) -> pd.Timestamp:
        return self._max_date_to_end

    def _set_all_transactions(self, df: DataFrame[TransactionLabeled]) -> None:
        self._df: DataFrame[TransactionLabeled] = df

    def _day_to_start(self, df) -> pd.Timestamp:
        first_date: pd.Timestamp = (
            df.groupby(TransactionLabeled.Account, observed=True)[TransactionLabeled.Date]
            .min()
            .max()
        )

        if first_date.day > self.month_split_day:
            first_date: pd.Timestamp = get_next_month(first_date)

        return pd.Timestamp(first_date.year, first_date.month, self.month_split_day)  # type: ignore

    def _day_to_end(self, df) -> pd.Timestamp:
        last_date: pd.Timestamp = (
            df.groupby(TransactionLabeled.Account, observed=True)[TransactionLabeled.Date]
            .max()
            .min()
        )
        day_to_end: pd.Timestamp = pd.Timestamp(
            datetime.date(last_date.year, last_date.month, self.month_split_day)
        )  # type: ignore
        if self.month_split_day == 1:
            if get_previous_day(get_next_month(day_to_end)) == last_date:
                return get_previous_day(get_next_month(day_to_end))
            else:
                return get_previous_day(day_to_end)
        else:
            if get_previous_day(day_to_end) <= last_date:
                return get_previous_day(day_to_end)
            else:
                return get_previous_day(get_previous_month(day_to_end))

    def get_months_to_analyze_start(self) -> list[pd.Timestamp]:
        months_to_analyze_start: list[pd.Timestamp] = []
        month: pd.Timestamp = self._date_to_start
        while month <= self._date_to_end:
            months_to_analyze_start.append(month)
            month: pd.Timestamp = get_next_month(month)
        return months_to_analyze_start

    def get_months_to_analyze_end(self) -> list[pd.Timestamp]:
        months: list[pd.Timestamp] = self.get_months_to_analyze_start()
        months.append(get_next_month(months[-1]))
        months: list[pd.Timestamp] = [get_previous_day(month) for month in months]
        return months[1:]

    def get_n_months_to_analyze(self) -> int:
        return len(self.get_months_to_analyze_start())

    def iterate_months(self) -> Generator:
        months_to_analyze_start: list[pd.Timestamp] = self.get_months_to_analyze_start()
        months_to_analyze_end: list[pd.Timestamp] = self.get_months_to_analyze_end()
        for start, end in zip(months_to_analyze_start, months_to_analyze_end):
            month_dates: DataFrame[TransactionLabeled] = self._df.loc[
                (self._df[TransactionLabeled.Date] >= start)
                & (self._df[TransactionLabeled.Date] <= end)
            ]
            yield month_dates

    def drop_costs(self, label: str, sublabel: str) -> None:
        to_drop: pd.Series = (self._df[TransactionLabeled.Label] == label) & (
            self._df[TransactionLabeled.Sublabel] == sublabel
        )
        if to_drop.sum() == 0:
            log.error(
                f'Transaction not found in monthly costs! Label: {label}, Sublabel: {sublabel}'
            )
            raise KeyError
        else:
            self._df: DataFrame[TransactionLabeled] = self._df.loc[~to_drop]

    def drop_costs_by_config(self, file_name: Path) -> None:
        drop_labels = DropLabels(file_name)
        for transaction in drop_labels.transactions:
            self.drop_costs(transaction.Label, transaction.Sublabel)

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
        self._df = pd.concat([self._df, df_to_add_all_configs])  # type: ignore
