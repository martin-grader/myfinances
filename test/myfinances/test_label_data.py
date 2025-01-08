import pandas as pd
import pytest
from pandera.typing import DataFrame

import myfinances.label_data as ld
from myfinances.label_data import TransactionLabeled
from myfinances.parse_data import Transaction


@pytest.fixture
def df() -> DataFrame[TransactionLabeled]:
    df: DataFrame[TransactionLabeled] = TransactionLabeled.example(size=4)  # type: ignore
    return df


@pytest.fixture
def df_no_labels(df: DataFrame[TransactionLabeled]) -> DataFrame[TransactionLabeled]:
    df_no_labels: DataFrame[TransactionLabeled] = df.copy()
    df_no_labels.loc[:, TransactionLabeled.Label] = None
    df_no_labels.loc[:, TransactionLabeled.Sublabel] = None
    return df_no_labels


@pytest.fixture
def rows_to_label(df: DataFrame[TransactionLabeled]) -> pd.Series:
    ser: pd.Series = pd.Series([True] + [False] * (df.shape[0] - 2) + [True])
    return ser


def test_add_empty_labels_columns() -> None:
    df_no_labels: DataFrame[Transaction] = Transaction.example(size=0)  # type:ignore
    df: DataFrame[TransactionLabeled] = ld.add_empty_labels_columns(df_no_labels)
    assert all(df.columns == TransactionLabeled.example(size=0).columns)  # type:ignore


def test_set_label(df_no_labels: DataFrame[TransactionLabeled], rows_to_label: pd.Series) -> None:
    label: str = 'test_label'
    sublabel: str = 'test_sublabel'
    ld.set_label(df_no_labels, rows_to_label, label, sublabel)
    pd.testing.assert_frame_equal(
        df_no_labels.loc[~rows_to_label, :], df_no_labels.loc[~rows_to_label, :]
    )
    assert all(df_no_labels.loc[rows_to_label, TransactionLabeled.Label] == label)
    assert all(df_no_labels.loc[rows_to_label, TransactionLabeled.Sublabel] == sublabel)


def test_check_for_duplicated_labels(df_no_labels: DataFrame[TransactionLabeled]) -> None:
    ser: pd.Series = pd.Series([True] * df_no_labels.shape[0])
    df_with_labels: DataFrame[TransactionLabeled] = df_no_labels.copy()
    df_with_labels.loc[0, TransactionLabeled.Label] = 'label already specified'
    with pytest.raises(KeyError):
        ld.check_for_duplicated_labels(df_with_labels, ser, '', '')


def test_check_for_duplicated_labels_no_raise(df_no_labels: DataFrame[TransactionLabeled]) -> None:
    ser: pd.Series = pd.Series([True] * df_no_labels.shape[0])
    ld.check_for_duplicated_labels(df_no_labels, ser, '', '')


def test_check_for_unlabeled_transactions(df_no_labels: DataFrame[TransactionLabeled]) -> None:
    with pytest.raises(KeyError):
        ld.check_for_unlabeled_transactions(df_no_labels)


def test_check_for_unlabeled_transactions_no_raise(df: DataFrame[TransactionLabeled]) -> None:
    ld.check_for_unlabeled_transactions(df)
