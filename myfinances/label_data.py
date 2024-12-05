# from typing import Literal
import sys
from pathlib import Path

import pandas as pd
from loguru import logger as log
from pandera.typing import DataFrame, Series

from myfinances.config_utils import TransactionLabels
from myfinances.parse_data import Transaction
from myfinances.utils import get_rows_by_string


class TransactionLabeled(Transaction):
    Label: Series[pd.CategoricalDtype]
    Sublabel: Series[str]


# @pa.check_types
def set_all_labels(
    df: DataFrame[Transaction], label_configs: list[Path]
) -> DataFrame[TransactionLabeled]:
    df_with_labels: DataFrame[TransactionLabeled] = prepare_labels(df)
    df_all_labels_set: DataFrame[TransactionLabeled] = set_labels_by_config(
        df_with_labels, label_configs
    )
    if df_all_labels_set[TransactionLabeled.Label].isna().sum() > 0:
        log.error('Found unlabled transactions:')
        log.error(df_all_labels_set[df_all_labels_set[TransactionLabeled.Label].isna()])
        sys.exit()

    return df_all_labels_set


def prepare_labels(df: DataFrame[Transaction]) -> DataFrame[TransactionLabeled]:
    df = df.assign(Label=None)  # type: ignore
    df = df.assign(Sublabel=None)  # type: ignore
    return df  # type: ignore


def set_labels_by_config(
    df: DataFrame[TransactionLabeled], label_config_files: list[Path]
) -> DataFrame[TransactionLabeled]:
    for config_file in label_config_files:
        transaction_labels = TransactionLabels(config_file)
        for label in transaction_labels.transactions:
            df = set_string_label(df, label.Identifier, label.Label, label.Sublabel)

    return df


def set_string_label(df, string, label, sublabel) -> DataFrame[TransactionLabeled]:
    to_label = get_rows_by_string(df, string)
    if any(df[to_label][TransactionLabeled.Label].notna()):
        log.error('Error: Found duplicated labels!')
        log.error(label, sublabel)
        log.error(df[to_label].to_string())
        raise KeyError
    df.loc[to_label, TransactionLabeled.Label] = label
    df.loc[to_label, TransactionLabeled.Sublabel] = sublabel
    log.debug(df[to_label])
    log.debug('Labled ' + str(to_label.sum()) + ' entries with ' + label + '/' + sublabel)

    return df
