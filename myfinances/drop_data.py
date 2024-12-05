from pathlib import Path

import pandas as pd
from loguru import logger as log
from pandera.typing import DataFrame

from myfinances.config_utils import load_yaml
from myfinances.parse_data import Transaction
from myfinances.utils import get_rows_by_string


def drop_data(df: DataFrame[Transaction], drop_transaction_config: Path) -> DataFrame[Transaction]:
    df = df.drop_duplicates()  # type:ignore
    df = drop_transaction_by_config(df, drop_transaction_config)
    return df


def drop_transaction_by_config(
    df: DataFrame[Transaction], drop_transaction_config: Path
) -> DataFrame[Transaction]:
    drop_transactions: dict = load_yaml(drop_transaction_config)
    reasons: list[tuple[str, str]] = []
    for reason, transactions in drop_transactions.items():
        for transaction in transactions:
            reasons.append((transaction, reason))
    return drop_transaction_by_key_and_reason(df, reasons)


def drop_transaction_by_key_and_reason(
    df: DataFrame[Transaction], reasons: list[tuple[str, str]]
) -> DataFrame[Transaction]:
    for key, reason in reasons:
        rows_to_drop: pd.Series = get_rows_by_string(df, key)
        df = drop_by_bool(df, rows_to_drop, reason)
    return df


def drop_by_bool(
    df: DataFrame[Transaction], to_drop: pd.Series, reason: str
) -> DataFrame[Transaction]:
    log.debug(df[to_drop])
    entries_before: int = df.shape[0]
    df = df.loc[~to_drop]
    entries_after: int = df.shape[0]
    log.debug(f'Dropped {entries_before - entries_after} with reason {reason}')
    return df
