import numpy as np
import pandas as pd
import pytest
from pandera.typing import DataFrame

import myfinances.label_data as ld
from myfinances.label_data import TransactionLabeled
from myfinances.parse_data import Transaction


@pytest.fixture(scope='module')
def df() -> DataFrame[TransactionLabeled]:
    df: DataFrame[TransactionLabeled] = TransactionLabeled.example(size=4)  # type: ignore
    return df


@pytest.fixture(scope='module')
def df_no_labels(df: DataFrame[TransactionLabeled]) -> DataFrame[TransactionLabeled]:
    df_no_labels: DataFrame[TransactionLabeled] = df.copy()
    df_no_labels.loc[:, TransactionLabeled.Label] = np.nan
    return df_no_labels


def test_add_empty_labels_columns() -> None:
    df_no_labels: DataFrame[Transaction] = Transaction.example(size=0)  # type:ignore
    df: DataFrame[TransactionLabeled] = ld.add_empty_labels_columns(df_no_labels)
    assert all(df.columns == TransactionLabeled.example(size=0).columns)  # type:ignore


def test_check_for_duplicated_labels(df_no_labels) -> None:
    ser: pd.Series = pd.Series([True] * df_no_labels.shape[0])
    df_with_labels: DataFrame[TransactionLabeled] = df_no_labels.copy()
    df_with_labels.loc[0, TransactionLabeled.Label] = 'label already specified'
    with pytest.raises(KeyError):
        ld.check_for_duplicated_labels(df_with_labels, ser, '', '')


def test_check_for_duplicated_labels_no_raise(df_no_labels) -> None:
    ser: pd.Series = pd.Series([True] * df_no_labels.shape[0])
    ld.check_for_duplicated_labels(df_no_labels, ser, '', '')


def test_check_for_unlabeled_transactions(df_no_labels) -> None:
    with pytest.raises(KeyError):
        ld.check_for_unlabeled_transactions(df_no_labels)


def test_check_for_unlabeled_transactions_no_raise(df) -> None:
    ld.check_for_unlabeled_transactions(df)
