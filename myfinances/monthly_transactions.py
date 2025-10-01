import datetime
from pathlib import Path
from typing import Generator

import pandas as pd
from loguru import logger as log
from pandera.typing import DataFrame

from myfinances.config_utils import AddLabels, DropLabels
from myfinances.label_data import TransactionLabeled
from myfinances.utils import get_next_day, get_next_month, get_previous_day, get_previous_month


class MonthlyTransactions:
    def __init__(self, df: DataFrame[TransactionLabeled], month_split_day: int = 1) -> None:
        self._set_all_transactions(df)
        self._mask: pd.Series = pd.Series([True] * df.shape[0])
        self.set_month_split_day(month_split_day)

        log.info(
            f'Analyzing {self.get_n_months_to_analyze()} months'
            f' ({self._date_to_start} - {self._date_to_end})'
        )

    def set_date_to_start(self, date: pd.Timestamp) -> None:
        self.set_start_and_end_date(date, self.get_date_to_end())

    def set_date_to_end(self, date: pd.Timestamp) -> None:
        self.set_start_and_end_date(self.get_date_to_start(), date)

    def set_start_and_end_date(
        self, date_to_start: pd.Timestamp, date_to_end: pd.Timestamp
    ) -> None:
        valid_start_date: pd.Timestamp = self.get_date_to_start()
        valid_end_date: pd.Timestamp = self.get_date_to_end()
        try:
            self._date_to_start = date_to_start
            self._date_to_end = date_to_end
            DateValidityChecker(self).execute()
        except DateError:
            self._date_to_start = valid_start_date
            self._date_to_end = valid_end_date
            raise

    def set_month_split_day(self, month_split_day: int) -> None:
        MonthSplitDateValidityChecker().execute(month_split_day)
        self._month_split_day: int = month_split_day
        self._reset_start_end_dates()
        DateValidityChecker(self).execute()

    def get_transactions(self) -> DataFrame[TransactionLabeled]:
        return self._df.loc[
            (
                (self._df[TransactionLabeled.Date] >= self._date_to_start)
                & (self._df[TransactionLabeled.Date] <= self._date_to_end)
                & self._mask
            )
        ]

    def get_date_to_start(self) -> pd.Timestamp:
        return self._date_to_start

    def get_date_to_end(self) -> pd.Timestamp:
        return self._date_to_end

    def get_month_split_day(self) -> int:
        return self._month_split_day

    def get_min_date_to_start(self) -> pd.Timestamp:
        return self._min_date_to_start

    def get_max_date_to_end(self) -> pd.Timestamp:
        return self._max_date_to_end

    def get_all_months_to_analyze_start(self) -> list[pd.Timestamp]:
        return self._calculate_months_to_analyze_start(
            self._min_date_to_start, self._max_date_to_end
        )

    def get_months_to_analyze_start(self) -> list[pd.Timestamp]:
        return self._calculate_months_to_analyze_start(self._date_to_start, self._date_to_end)

    def _calculate_months_to_analyze_start(
        self, date_to_start: pd.Timestamp, date_to_end: pd.Timestamp
    ) -> list[pd.Timestamp]:
        months_to_analyze_start: list[pd.Timestamp] = []
        month: pd.Timestamp = date_to_start
        while month <= date_to_end:
            months_to_analyze_start.append(month)
            month: pd.Timestamp = get_next_month(month)
        return months_to_analyze_start

    def get_all_months_to_analyze_end(self) -> list[pd.Timestamp]:
        return self._get_months_to_analyze_end(self.get_all_months_to_analyze_start())

    def get_months_to_analyze_end(self) -> list[pd.Timestamp]:
        return self._get_months_to_analyze_end(self.get_months_to_analyze_start())

    def _get_months_to_analyze_end(
        self, months_to_analyze_start: list[pd.Timestamp]
    ) -> list[pd.Timestamp]:
        months: list[pd.Timestamp] = [
            get_previous_day(month) for month in months_to_analyze_start[1:]
        ]
        months.append(get_previous_day(get_next_month(months_to_analyze_start[-1])))
        return months

    def get_n_months_to_analyze(self) -> int:
        return len(self.get_months_to_analyze_start())

    def iterate_months(self) -> Generator:
        months_to_analyze_start: list[pd.Timestamp] = self.get_months_to_analyze_start()
        months_to_analyze_end: list[pd.Timestamp] = self.get_months_to_analyze_end()
        df: DataFrame[TransactionLabeled] = self.get_transactions()
        for start, end in zip(months_to_analyze_start, months_to_analyze_end):
            month_dates: DataFrame[TransactionLabeled] = df.loc[
                (df[TransactionLabeled.Date] >= start) & (df[TransactionLabeled.Date] <= end)
            ]
            yield month_dates

    def _set_all_transactions(self, df: DataFrame[TransactionLabeled]) -> None:
        self._df: DataFrame[TransactionLabeled] = df
        self._df = self._df.reset_index(drop=True)  # pyright: ignore

    def _reset_start_end_dates(self) -> None:
        self._date_to_start: pd.Timestamp = self._min_day_to_start()
        self._date_to_end: pd.Timestamp = self._max_day_to_end()
        self._min_date_to_start: pd.Timestamp = self._min_day_to_start()
        self._max_date_to_end: pd.Timestamp = self._max_day_to_end()

    def _min_day_to_start(self) -> pd.Timestamp:
        first_date: pd.Timestamp = (
            self._df.groupby(TransactionLabeled.Account, observed=True)[TransactionLabeled.Date]
            .min()
            .max()
        )  # type:ignore

        if first_date.day > self._month_split_day:
            first_date: pd.Timestamp = get_next_month(first_date)

        return pd.Timestamp(first_date.year, first_date.month, self._month_split_day)  # type: ignore

    def _max_day_to_end(self) -> pd.Timestamp:
        last_date: pd.Timestamp = (
            self._df.groupby(TransactionLabeled.Account, observed=True)[TransactionLabeled.Date]
            .max()
            .min()
        )  # type: ignore
        day_to_end: pd.Timestamp = pd.Timestamp(
            datetime.date(last_date.year, last_date.month, self._month_split_day)
        )  # type: ignore
        if self._month_split_day == 1:
            if get_previous_day(get_next_month(day_to_end)) == last_date:
                return get_previous_day(get_next_month(day_to_end))
            else:
                return get_previous_day(day_to_end)
        else:
            if get_previous_day(day_to_end) <= last_date:
                return get_previous_day(day_to_end)
            else:
                return get_previous_day(get_previous_month(day_to_end))

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
            self._mask: pd.Series = self._mask & ~to_drop

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
        _df: DataFrame[TransactionLabeled] = pd.concat([self._df, df_to_add_all_configs])  # type: ignore
        self._set_all_transactions(_df)
        self._mask: pd.Series = pd.concat(
            [
                self._mask,
                pd.Series([True] * df_to_add_all_configs.shape[0]),
            ]
        )
        self._mask.reset_index(drop=True, inplace=True)
        self._reset_start_end_dates()

    def get_all_labels(self):
        return self._df[TransactionLabeled.Label].unique()

    def get_active_labels(self):
        return self.get_transactions()[TransactionLabeled.Label].unique()

    def set_active_labels(self, values: list[str]) -> None:
        self._mask: pd.Series = self._df.loc[:, TransactionLabeled.Label].isin(values)

    def get_all_sublabels(self) -> dict:
        all_labels = self.get_all_labels()
        all_sublabels: dict = {}
        for label in all_labels:
            sublabels = self._df.loc[
                self._df[TransactionLabeled.Label] == label, TransactionLabeled.Sublabel
            ].unique()
            all_sublabels[label] = sublabels
        return all_sublabels

    def get_active_sublabels(self, label: str) -> list[str]:
        df: DataFrame[TransactionLabeled] = self.get_transactions()
        sublabels = df.loc[
            df[TransactionLabeled.Label] == label, TransactionLabeled.Sublabel
        ].unique()
        return sublabels

    def set_active_sublabels(self, sublabels: dict) -> None:
        mask: pd.Series = pd.Series([False] * self._df.shape[0])
        for active_label, active_sublabels in sublabels.items():
            mask += (self._df.loc[:, TransactionLabeled.Label] == active_label) & (
                self._df.loc[:, TransactionLabeled.Sublabel].isin(active_sublabels)
            )

        self._mask = mask


class DateError(Exception):
    pass


class DateValidityChecker:
    def __init__(self, target: MonthlyTransactions) -> None:
        self.start_date: pd.Timestamp = target.get_date_to_start()
        self.end_date: pd.Timestamp = target.get_date_to_end()
        self.month_split_day: int = target.get_month_split_day()
        self.min_date_to_start: pd.Timestamp = target.get_min_date_to_start()
        self.max_date_to_end: pd.Timestamp = target.get_max_date_to_end()
        self.error_state: type[Exception] = DateError

    def execute(self) -> None:
        self._check_date_day_matches_split_day(self.start_date)
        self._check_date_day_matches_split_day(get_next_day(self.end_date))
        self._check_date_ge_minimum_date(self.start_date)
        self._check_date_ge_minimum_date(self.end_date)
        self._check_date_le_max_date(self.start_date)
        self._check_date_le_max_date(self.end_date)
        self._check_start_date_less_end_date(self.start_date, self.end_date)

    def _check_date_day_matches_split_day(self, start_date: pd.Timestamp) -> None:
        if start_date.day != self.month_split_day:
            log.error(
                f'Day in date ({start_date}) not equal month_split_day ({self.month_split_day})'
            )
            raise self.error_state

    def _check_date_ge_minimum_date(self, date: pd.Timestamp) -> None:
        if date < self.min_date_to_start:
            log.error(
                f'Date ({date}) must greater or equal',
                f' the minimum date in data ({self.min_date_to_start})',
            )
            raise self.error_state

    def _check_date_le_max_date(self, date: pd.Timestamp) -> None:
        if date > self.max_date_to_end:
            log.error(
                f'Date set ({date}) must be less or equal the',
                f' maximum date in data ({self.max_date_to_end})',
            )
            raise self.error_state

    def _check_start_date_less_end_date(
        self, start_date: pd.Timestamp, end_date: pd.Timestamp
    ) -> None:
        if start_date > end_date:
            log.error(f'Start date ({start_date}) must be less end data ({end_date})')
            raise self.error_state


class MonthSplitDateValidityChecker:
    min_split_day: int = 1
    max_split_day: int = 27

    def execute(self, month_split_day: int) -> None:
        if month_split_day < self.min_split_day:
            log.error(f'Month split day ({month_split_day}) must be greater zero')
            raise DateError
        if month_split_day > self.max_split_day:
            log.error(f'Month split day ({month_split_day}) must be less 28')
            raise DateError
        if not isinstance(month_split_day, int):
            log.error(f'Type of month split day ({month_split_day}) must be integer')
            raise DateError
