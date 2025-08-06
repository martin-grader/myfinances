import pandas as pd
from dateutil.relativedelta import relativedelta

from myfinances.parse_data import Transaction


def get_rows_by_string(df, string) -> pd.Series:
    return df[Transaction.Text].str.contains(string, regex=False)


def get_rows_by_exact_string(df, string) -> pd.Series:
    return df[Transaction.Text].str.fullmatch(string)


def get_previous_day(date: pd.Timestamp) -> pd.Timestamp:
    return date - relativedelta(days=1)


def get_previous_month(date: pd.Timestamp) -> pd.Timestamp:
    return date - relativedelta(months=1)


def get_next_month(date: pd.Timestamp) -> pd.Timestamp:
    return date + relativedelta(months=1)
