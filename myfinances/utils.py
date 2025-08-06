import pandas as pd
from dateutil.relativedelta import relativedelta

from myfinances.parse_data import Transaction


def get_rows_by_string(df, string) -> pd.Series:
    return df[Transaction.Text].str.contains(string, regex=False)


def get_rows_by_exact_string(df, string) -> pd.Series:
    return df[Transaction.Text].str.fullmatch(string)


def get_previous_day(date: pd.Timestamp) -> pd.Timestamp:
    previous_day: pd.Timestamp = date - relativedelta(days=1)  # type: ignore
    return previous_day


def get_previous_month(date: pd.Timestamp) -> pd.Timestamp:
    previous_month: pd.Timestamp = date - relativedelta(months=1)  # type: ignore
    return previous_month


def get_next_month(date: pd.Timestamp) -> pd.Timestamp:
    next_month: pd.Timestamp = date + relativedelta(months=1)  # type: ignore
    return next_month
