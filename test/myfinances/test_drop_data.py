from pathlib import Path

import pandas as pd
import pytest
from pandera.typing import DataFrame

import myfinances.drop_data as dt
from myfinances.parse_data import Transaction


@pytest.fixture
def df_before() -> DataFrame[Transaction]:
    df_before: DataFrame[Transaction] = pd.DataFrame({'a': [1, 2, 3, 2], 'b': [4, 2, 6, 2]})  # type:ignore
    return df_before


@pytest.fixture
def ser_bool() -> pd.Series:
    ser_bool: pd.Series = pd.Series([False, True, False, True])
    return ser_bool


def mockreturn(*args, **kwargs) -> pd.Series:
    ser_bool: pd.Series = pd.Series([False, True, False, True])
    return ser_bool


def test_drop_data_no_config(df_before) -> None:
    df_expected: pd.DataFrame = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 2, 6]})
    df: DataFrame[Transaction] = dt.drop_data(df_before, Path())
    pd.testing.assert_frame_equal(df, df_expected)


def test_drop_transaction_by_key_and_reason(df_before, monkeypatch, ser_bool) -> None:
    monkeypatch.setattr(dt, 'get_rows_by_string', mockreturn)
    df_expected: pd.DataFrame = df_before.iloc[ser_bool[~ser_bool].index.values, :]  # type:ignore
    df: DataFrame[Transaction] = dt.drop_transaction_by_key_and_reason(df_before, '', '')
    pd.testing.assert_frame_equal(df, df_expected)


def test_drop_by_bool(df_before, ser_bool) -> None:
    df_expected: pd.DataFrame = df_before.iloc[ser_bool[~ser_bool].index.values, :]  # type:ignore
    df: DataFrame[Transaction] = dt.drop_by_bool(df_before, ser_bool, '', '')
    pd.testing.assert_frame_equal(df, df_expected)


def test_check_dropped() -> None:
    with pytest.raises(KeyError):
        dt.check_dropped(0, '', '')
    dt.check_dropped(1, '', '')
