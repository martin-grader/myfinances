import pandas as pd


def get_rows_by_string(df, string) -> pd.Series:
    return df['Text'].str.contains(string, regex=False)


def get_rows_by_exact_string(df, string) -> pd.Series:
    return df['Text'].str.fullmatch(string)
