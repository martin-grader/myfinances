# from typing import Literal
from pathlib import Path

import pandas as pd
import pandera as pa
from loguru import logger as log
from pandera.typing import DataFrame, Series

from myfinances.config_utils import TransactionLabels
from myfinances.parse_data import Transaction
from myfinances.utils import get_rows_by_string


class TransactionLabeled(Transaction):
    Label: Series[str]
    Sublabel: Series[str]


@pa.check_types
def set_all_labels(
    df: DataFrame[Transaction], label_configs: list[Path]
) -> DataFrame[TransactionLabeled]:
    df_with_labels: DataFrame[TransactionLabeled] = add_empty_labels_columns(df)
    df_all_labels_set: DataFrame[TransactionLabeled] = set_labels_by_config(
        df_with_labels, label_configs
    )
    check_for_unlabeled_transactions(df_all_labels_set)

    return df_all_labels_set


def add_empty_labels_columns(df: DataFrame[Transaction]) -> DataFrame[TransactionLabeled]:
    df = df.assign(Label=None)  # type: ignore
    df = df.assign(Sublabel=None)  # type: ignore
    return df  # type: ignore


def set_labels_by_config(
    df: DataFrame[TransactionLabeled], label_config_files: list[Path]
) -> DataFrame[TransactionLabeled]:
    for config_file in label_config_files:
        transaction_labels = TransactionLabels(config_file)
        for label in transaction_labels.transactions:
            set_label(df, label.Identifier, label.Label, label.Sublabel)

    return df


def set_label(
    df: DataFrame[TransactionLabeled], identifier: str, label: str, sublabel: str
) -> None:
    to_label: pd.Series = get_rows_by_string(df, identifier)
    check_for_duplicated_labels(df, to_label, label, sublabel)
    df.loc[to_label, TransactionLabeled.Label] = label
    df.loc[to_label, TransactionLabeled.Sublabel] = sublabel
    log.debug(df[to_label])
    log.debug('Labled ' + str(to_label.sum()) + ' entries with ' + label + '/' + sublabel)


def check_for_duplicated_labels(
    df: DataFrame[TransactionLabeled], to_label: pd.Series, label: str, sublabel: str
) -> None:
    if any(df.loc[to_label, TransactionLabeled.Label].notna()):
        log.error('Error: Found duplicated labels!')
        log.error(label, sublabel)
        log.error(df[to_label].to_string())
        raise KeyError


def check_for_unlabeled_transactions(df) -> None:
    if df[TransactionLabeled.Label].isna().sum() > 0:
        log.error('Found unlabled transactions:')
        log.error(df[df[TransactionLabeled.Label].isna()])
        raise KeyError
