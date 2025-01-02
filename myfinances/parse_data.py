import locale
from pathlib import Path

import pandas as pd
import pandera as pa
from loguru import logger as log
from pandera.typing import DataFrame, Series

from myfinances.config_utils import InputConfig, to_input_config


class Transaction(pa.DataFrameModel):
    Date: Series[pd.Timestamp]
    Text: Series[str]
    Amount: Series[float]
    Account: Series[pd.CategoricalDtype]


@pa.check_types
def load_data(inputs_config: Path) -> DataFrame[Transaction]:
    inputs: list[InputConfig] = to_input_config(inputs_config)
    dfs: list[DataFrame[Transaction]] = []
    for input_config in inputs:
        data_files: list[Path] = get_all_data_files(input_config)
        for file in data_files:
            df_raw: pd.DataFrame = load_generic(file, input_config.Delimiter, input_config.Decimal)
            date: pd.Series = parse_dates(df_raw, input_config.DateKey, input_config.DateFormat)
            text: pd.Series = parse_text(df_raw, input_config.TextKeys)
            amount: pd.Series = parse_amount(df_raw, input_config.AmountKey)
            df: DataFrame[Transaction] = pd.DataFrame(
                {
                    Transaction.Date: date,
                    Transaction.Text: text,
                    Transaction.Amount: amount,
                    Transaction.Account: input_config.Account,
                }
            )  # type: ignore
            dfs.append(df)

    df: DataFrame[Transaction] = pd.concat(dfs)  # type: ignore

    df[Transaction.Account] = pd.Categorical(df['Account'])

    return df


def get_all_data_files(input_config: InputConfig) -> list[Path]:
    all_data_files: list[Path] = []
    for files in input_config.Files:
        for file in Path().cwd().rglob(files):
            all_data_files.append(file)

    return all_data_files


def load_generic(file_name: Path, delimiter: str, decimal: str) -> pd.DataFrame:
    log.info(f'Loading {file_name.name}')
    df: pd.DataFrame = pd.read_csv(
        file_name, delimiter=delimiter, decimal=decimal, encoding='iso-8859-1'
    )
    df.dropna(axis=1, how='all', inplace=True)
    return df


def parse_amount(df: pd.DataFrame, amount_key: str) -> pd.Series:
    amount: pd.Series = df.loc[:, amount_key]
    if amount.dtype != float:
        locale.setlocale(locale.LC_NUMERIC, '')
        amount: pd.Series = amount.apply(lambda v: locale.atof(v))  # type:ignore
    return amount


def parse_dates(df: pd.DataFrame, date_key: str, date_model: str) -> pd.Series:
    date: pd.Series = pd.to_datetime(df[date_key], format=date_model)
    return date


def parse_text(df: pd.DataFrame, text_keys: list[str]) -> pd.Series:
    df.fillna('-', inplace=True)
    text: pd.Series = df.loc[:, text_keys].agg(';'.join, axis=1)
    return text
