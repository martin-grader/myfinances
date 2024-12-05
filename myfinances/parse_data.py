import locale
from pathlib import Path

import pandas as pd
import pandera as pa
from pandera.typing import DataFrame, Series

from myfinances.config_utils import InputConfig, to_input_config


class TransactionRaw(pa.DataFrameModel):
    Date: Series[pd.Timestamp]
    Text: Series[str]
    Amount: Series[float]


class Transaction(TransactionRaw):
    Account: Series[pd.CategoricalDtype]


@pa.check_types
def load_data(inputs_config: Path) -> DataFrame[Transaction]:
    inputs: list[InputConfig] = to_input_config(inputs_config)
    dfs: list[DataFrame[Transaction]] = []
    for input_config in inputs:
        for files in input_config.Files:
            for file in Path().cwd().rglob(files):
                df_raw: pd.DataFrame = load_generic(
                    file, input_config.Delimiter, input_config.Decimal
                )
                amount: pd.Series = parse_amount(df_raw, input_config.AmountKey)
                date: pd.Series = parse_dates(df_raw, input_config.DateKey, input_config.DateFormat)
                text: pd.Series = parse_text(df_raw, input_config.TextKeys)
                df: DataFrame[TransactionRaw] = pd.DataFrame(
                    {
                        TransactionRaw.Date: date,
                        TransactionRaw.Text: text,
                        TransactionRaw.Amount: amount,
                    }
                )
                df[Transaction.Account] = input_config.Account
                df_with_account = transform(df, input_config.Account)
                dfs.append(df_with_account)

    df: DataFrame[Transaction] = pd.concat(dfs)  # type: ignore

    df[Transaction.Account] = pd.Categorical(df['Account'])

    return df


# @pa.check_types
def transform(df: DataFrame[TransactionRaw], account: str) -> DataFrame[Transaction]:
    return df.assign(Account=account)


def load_generic(file_name: Path, delimiter: str, decimal: str) -> pd.DataFrame:
    df: pd.DataFrame = pd.read_csv(
        file_name, delimiter=delimiter, decimal=decimal, encoding='iso-8859-1'
    )
    df.dropna(axis=1, how='all', inplace=True)
    return df


def parse_amount(df: pd.DataFrame, amount_key: str) -> pd.Series:
    amount: pd.Series = df[amount_key]
    if amount.dtype != float:
        locale.setlocale(locale.LC_NUMERIC, '')
        amount = amount.apply(lambda v: locale.atof(v))
    return amount


def parse_dates(df: pd.DataFrame, date_key: str, date_model: str) -> pd.Series:
    date: pd.Series = pd.to_datetime(df[date_key], format=date_model)
    return date


def parse_text(df: pd.DataFrame, text_keys: list[str]) -> pd.Series:
    df.fillna('-', inplace=True)
    text: pd.Series = df[text_keys].agg(';'.join, axis=1)
    return text
