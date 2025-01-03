import pandas as pd

from myfinances.parse_data import Transaction


def get_rows_by_string(df, string) -> pd.Series:
    return df[Transaction.Text].str.contains(string, regex=False)


def get_rows_by_exact_string(df, string) -> pd.Series:
    return df[Transaction.Text].str.fullmatch(string)
