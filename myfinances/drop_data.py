from pathlib import Path

import pandas as pd
from loguru import logger as log
from pandera.typing import DataFrame

from myfinances.config_utils import load_yaml
from myfinances.parse_data import Transaction
from myfinances.utils import get_rows_by_string


def drop_data(df: DataFrame[Transaction], drop_transaction_config: Path) -> DataFrame[Transaction]:
    df = df.drop_duplicates()  # type:ignore
    if drop_transaction_config.is_file():
        df = drop_transaction_by_config(df, drop_transaction_config)
    return df


def drop_transaction_by_config(
    df: DataFrame[Transaction], drop_transaction_config: Path
) -> DataFrame[Transaction]:
    drop_transactions: dict = load_yaml(drop_transaction_config)
    for reason, transactions in drop_transactions.items():
        for transaction in transactions:
            df = drop_transaction_by_key_and_reason(df, transaction, reason)
    return df


def drop_transaction_by_key_and_reason(
    df: DataFrame[Transaction], transaction: str, reason: str
) -> DataFrame[Transaction]:
    rows_to_drop: pd.Series = get_rows_by_string(df, transaction)
    df = drop_by_bool(df, rows_to_drop, reason, transaction)
    return df


def drop_by_bool(
    df: DataFrame[Transaction], to_drop: pd.Series, reason: str, transaction: str
) -> DataFrame[Transaction]:
    entries_before: int = df.shape[0]
    df = df.loc[~to_drop]
    entries_dropped: int = entries_before - df.shape[0]

    check_dropped(entries_dropped, reason, transaction)
    log.debug(f'Dropped {entries_dropped} with reason {reason}')
    return df


def check_dropped(entries_dropped: int, reason: str, transaction: str) -> None:
    if entries_dropped == 0:
        log.error(f'Found no transactions tor drop with reason {reason} and key {transaction}!')
        raise KeyError
