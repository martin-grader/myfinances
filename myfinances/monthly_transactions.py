import datetime
from typing import Generator

import pandas as pd
from dateutil.relativedelta import relativedelta
from loguru import logger as log
from pandera.typing import DataFrame

from myfinances.label_data import TransactionLabeled


class MonthlyTransactions:
    def __init__(self, df: DataFrame[TransactionLabeled], month_split_day: int = 2) -> None:
        self.month_split_day: int = month_split_day
        self.date_to_start: pd.Timestamp = self._day_to_start(df)
        self.date_to_end: pd.Timestamp = self._day_to_end(df)

        print(self.date_to_start)
        print(self.date_to_end)
        self.months_to_analyze: int = self._get_months_to_analyze()
        self.df: DataFrame[TransactionLabeled] = df.loc[
            (df[TransactionLabeled.Date] >= self.date_to_start)
            & (df[TransactionLabeled.Date] <= self.date_to_end)
        ]
        log.info(
            f'Analyzing {self.months_to_analyze} months'
            f' ({self.date_to_start} - {self.date_to_end})'
        )

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

    def _get_months_to_analyze(self) -> int:
        time_period: pd.tseries.offsets.BaseOffset = self.date_to_end.to_period(  # type:ignore
            'M'
        ) - self.date_to_start.to_period('M')
        return time_period.n

    def iterate_months(self) -> Generator:
        delta = relativedelta(months=1)
        month_to_analyze_start = self.date_to_start
        month_to_analyze_end = self.date_to_start + delta - relativedelta(days=1)
        while month_to_analyze_end <= self.date_to_end:
            month_dates = self.df[
                (self.df[TransactionLabeled.Date] >= pd.Timestamp(month_to_analyze_start))
                & (self.df[TransactionLabeled.Date] <= pd.Timestamp(month_to_analyze_end))
            ]
            yield month_dates
            month_to_analyze_start = month_to_analyze_start + delta
            month_to_analyze_end = month_to_analyze_end + delta
