import datetime
from pathlib import Path
from typing import Generator

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta
from loguru import logger as log
from pandera.typing import DataFrame

from myfinances.config_utils import AddLabels, DropLabels
from myfinances.label_data import TransactionLabeled


class MonthlyTransactions:
    def __init__(self, df: DataFrame[TransactionLabeled], month_split_day: int = 1) -> None:
        self.month_split_day: int = month_split_day
        self.date_to_start: pd.Timestamp = self._day_to_start(df)
        self.date_to_end: pd.Timestamp = self._day_to_end(df)

        print(self.date_to_start)
        print(self.date_to_end)
        self.n_months_to_analyze: int = self._get_n_months_to_analyze()
        self._set_all_transactions(df)
        self.months_to_analyze: pd.Series = self._get_months_to_analyze()
        log.info(
            f'Analyzing {self.n_months_to_analyze} months'
            f' ({self.date_to_start} - {self.date_to_end})'
        )

    def get_transactions(self) -> DataFrame[TransactionLabeled]:
        return self._df.loc[
            (self._df[TransactionLabeled.Date] >= self.date_to_start)
            & (self._df[TransactionLabeled.Date] <= self.date_to_end)
        ]

    def _set_all_transactions(self, df) -> None:
        self._df = df

    def _day_to_start(self, df) -> pd.Timestamp:
        first_date: pd.Timestamp = (
            df.groupby(TransactionLabeled.Account, observed=True)[TransactionLabeled.Date]
            .min()
            .max()
        )

        if first_date.day >= self.month_split_day:
            first_date: pd.Timestamp = first_date + pd.DateOffset(months=1)

        return pd.Timestamp(datetime.date(first_date.year, first_date.month, self.month_split_day))  # type: ignore

    def _day_to_end(self, df) -> pd.Timestamp:
        last_date: pd.Timestamp = (
            df.groupby(TransactionLabeled.Account, observed=True)[TransactionLabeled.Date]
            .max()
            .min()
        )
        if last_date.day < self.month_split_day:
            last_date: pd.Timestamp = last_date - pd.DateOffset(months=1)

        return pd.Timestamp(
            datetime.date(last_date.year, last_date.month, self.month_split_day - 1)
        )  # type:ignore

    def _get_n_months_to_analyze(self) -> int:
        time_period: pd.tseries.offsets.BaseOffset = self.date_to_end.to_period(  # type:ignore
            'M'
        ) - self.date_to_start.to_period('M')
        return time_period.n

    def _get_months_to_analyze(self) -> np.ndarray:
        dates_sorted = self._df[TransactionLabeled.Date]
        time_period: pd.Series = dates_sorted.apply(lambda x: x.strftime('%B-%Y'))  # type: ignore
        time_period_unique: np.ndarray = time_period.sort_values().unique()
        ps = pd.to_datetime(time_period_unique, format='%B-%Y').sort_values()
        return ps

    def iterate_months(self) -> Generator:
        delta = relativedelta(months=1)
        month_to_analyze_start = self.date_to_start
        month_to_analyze_end = self.date_to_start + delta - relativedelta(days=1)
        while month_to_analyze_end <= self.date_to_end:
            month_dates = self._df[
                (self._df[TransactionLabeled.Date] >= pd.Timestamp(month_to_analyze_start))
                & (self._df[TransactionLabeled.Date] <= pd.Timestamp(month_to_analyze_end))
            ]
            yield month_dates
            month_to_analyze_start = month_to_analyze_start + delta
            month_to_analyze_end = month_to_analyze_end + delta

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
