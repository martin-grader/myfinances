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
        self.set_month_split_day(month_split_day)

        log.info(
            f'Analyzing {self.get_n_months_to_analyze()} months'
            f' ({self._date_to_start} - {self._date_to_end})'
        )

    def set_date_to_start(self, date: pd.Timestamp) -> None:
        valid_date: pd.Timestamp = self.get_date_to_start()
        try:
            self._date_to_start = date
            IntegrityChecker(self).check_start_date()
        except StartDateError:
            self._date_to_start = valid_date
            raise

    def set_date_to_end(self, date: pd.Timestamp) -> None:
        self._check_date_day_matches_split_day(get_next_day(date))
        self._check_date_limits(date)
        self._check_start_date_less_end_date(self._date_to_start, date)

        self._date_to_end: pd.Timestamp = date

    def set_start_and_end_date(
        self, date_to_start: pd.Timestamp, date_to_end: pd.Timestamp
    ) -> None:
        self._check_date_day_matches_split_day(date_to_start)
        self._check_date_day_matches_split_day(get_next_day(date_to_end))
        self._check_date_limits(date_to_start)
        self._check_date_limits(date_to_end)
        self._check_start_date_less_end_date(date_to_start, date_to_end)

        self._date_to_start: pd.Timestamp = date_to_start
        self._date_to_end: pd.Timestamp = date_to_end

    def set_month_split_day(self, month_split_day: int) -> None:
        self._set_month_split_day(month_split_day)
        self._reset_start_end_dates()

    def _check_date_limits(self, date: pd.Timestamp) -> None:
        self._check_date_ge_minimum_date(date)
        self._check_date_le_max_date(date)

    def get_transactions(self) -> DataFrame[TransactionLabeled]:
        return self._df.loc[
            (self._df[TransactionLabeled.Date] >= self._date_to_start)
            & (self._df[TransactionLabeled.Date] <= self._date_to_end)
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
        for start, end in zip(months_to_analyze_start, months_to_analyze_end):
            month_dates: DataFrame[TransactionLabeled] = self._df.loc[
                (self._df[TransactionLabeled.Date] >= start)
                & (self._df[TransactionLabeled.Date] <= end)
            ]
            yield month_dates

    def _set_all_transactions(self, df: DataFrame[TransactionLabeled]) -> None:
        self._df: DataFrame[TransactionLabeled] = df

    def _set_month_split_day(self, month_split_day) -> None:
        self._check_month_split_day(month_split_day)
        self._month_split_day: int = month_split_day

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

    def _check_date_day_matches_split_day(self, date: pd.Timestamp) -> None:
        if date.day != self._month_split_day:
            log.error(
                f'Day in date ({date}) must equal the month_split_day ({self._month_split_day})'
            )
            raise AttributeError

    def _check_date_ge_minimum_date(self, date: pd.Timestamp) -> None:
        if date < self.get_min_date_to_start():
            log.error(
                f'Date set ({date}) must greater or equal',
                f' the minimum date in data ({self.get_min_date_to_start()})',
            )
            raise AttributeError

    def _check_date_le_max_date(self, date: pd.Timestamp) -> None:
        if date > self.get_max_date_to_end():
            log.error(
                f'Date set ({date}) must be less or equal the',
                f' maximum date in data ({self.get_max_date_to_end()})',
            )
            raise AttributeError

    def _check_start_date_less_end_date(
        self, start_date: pd.Timestamp, end_date: pd.Timestamp
    ) -> None:
        if start_date > end_date:
            log.error(f'Start date ({start_date}) must be less end data ({end_date})')
            raise AttributeError

    def _check_month_split_day(self, month_split_day: int) -> None:
        if month_split_day <= 0:
            log.error(f'Month split day ({month_split_day}) must be greater zero')
            raise AttributeError
        if month_split_day >= 28:
            log.error(f'Month split day ({month_split_day}) must be less 28')
            raise AttributeError
        if not isinstance(month_split_day, int):
            log.error(f'Type of month split day ({month_split_day}) must be integer')
            raise AttributeError

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


class StartDateError(Exception):
    pass


class IntegrityChecker:
    def __init__(self, target: MonthlyTransactions) -> None:
        self.start_date: pd.Timestamp = target.get_date_to_start()
        self.end_date: pd.Timestamp = target.get_date_to_end()
        self.month_split_day: int = target.get_month_split_day()
        self.min_date_to_start: pd.Timestamp = target.get_min_date_to_start()
        self.max_date_to_end: pd.Timestamp = target.get_max_date_to_end()
        self.error_state: type[Exception] = AttributeError

    def check_start_date(self) -> None:
        self.error_state = StartDateError
        self._check_date_day_matches_split_day(self.start_date)
        self._check_date_ge_minimum_date(self.start_date)
        self._check_date_le_max_date(self.start_date)
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
