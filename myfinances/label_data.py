from pathlib import Path

import pandas as pd
import pandera as pa
from loguru import logger as log
from pandera.typing import DataFrame, Series

from myfinances.config_utils import LabelConfig, to_config
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
    set_labels_by_config(df_with_labels, label_configs)
    check_for_unlabeled_transactions(df_with_labels)

    return df_with_labels


def add_empty_labels_columns(df: DataFrame[Transaction]) -> DataFrame[TransactionLabeled]:
    df = df.assign(Label=None)  # type: ignore
    df = df.assign(Sublabel=None)  # type: ignore
    return df  # type: ignore


def set_labels_by_config(
    df: DataFrame[TransactionLabeled], label_config_files: list[Path]
) -> DataFrame[TransactionLabeled]:
    for config_file in label_config_files:
        label_config: LabelConfig = to_config(config_file, LabelConfig)
        set_labels_this_config(df, label_config)

    return df


def set_labels_this_config(df: DataFrame[TransactionLabeled], label_config: LabelConfig) -> None:
    for sublabel, identifiers in label_config.sublabels.items():
        for identifier in identifiers:
            rows_to_label: pd.Series = get_rows_by_string(df, identifier)
            check_for_duplicated_labels(df, rows_to_label, label_config.label, sublabel)
            set_label(df, rows_to_label, label_config.label, sublabel)


def set_label(
    df: DataFrame[TransactionLabeled], rows_to_label: pd.Series, label: str, sublabel: str
) -> None:
    df.loc[rows_to_label, TransactionLabeled.Label] = label
    df.loc[rows_to_label, TransactionLabeled.Sublabel] = sublabel
    log.debug(df[rows_to_label])
    log.debug('Labled ' + str(rows_to_label.sum()) + ' entries with ' + label + '/' + sublabel)


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
