import numpy as np
import pytest
from pandera.typing import DataFrame

import myfinances.label_data as ld
from myfinances.label_data import TransactionLabeled
from myfinances.parse_data import Transaction


def test_add_empty_labels_columns() -> None:
    df_no_labels: DataFrame[Transaction] = Transaction.example(size=0)  # type:ignore
    df: DataFrame[TransactionLabeled] = ld.add_empty_labels_columns(df_no_labels)
    assert all(df.columns == TransactionLabeled.example(size=0).columns)  # type:ignore


def test_check_for_unlabeled_transactions() -> None:
    df: DataFrame[TransactionLabeled] = TransactionLabeled.example(size=1)  # type: ignore
    ld.check_for_unlabeled_transactions(df)
    df.loc[:, TransactionLabeled.Label] = np.nan
    with pytest.raises(KeyError):
        ld.check_for_unlabeled_transactions(df)
