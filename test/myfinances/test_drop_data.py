from pathlib import Path

import pandas as pd
import pytest
from pandera.typing import DataFrame

import myfinances.drop_data as dt
from myfinances.parse_data import Transaction


@pytest.fixture
def df_before() -> DataFrame[Transaction]:
    df_before: DataFrame[Transaction] = pd.DataFrame(
        {Transaction.Text: ['-1', '1', '2', '3', '2'], 'b': ['-2', '4', '2', '6', '2']}
    )  # type:ignore
    return df_before


@pytest.fixture
def ser_bool() -> pd.Series:
    ser_bool: pd.Series = pd.Series([False, False, True, False, True])
    return ser_bool


def mock_get_rows_by_string(*args, **kwargs) -> pd.Series:
    ser_bool: pd.Series = pd.Series([False, False, True, False, True])
    return ser_bool


def mock_load_yaml(*args, **kwargs) -> dict:
    config: dict = {'reason_1': ['3', '2'], 'reason_2': ['-1']}
    return config


def test_drop_data_no_config(df_before) -> None:
    df_expected: pd.DataFrame = df_before.iloc[:-1, :]
    df: DataFrame[Transaction] = dt.drop_data(df_before, Path())
    pd.testing.assert_frame_equal(df, df_expected)


def test_drop_data(df_before, monkeypatch) -> None:
    monkeypatch.setattr(dt, 'load_yaml', mock_load_yaml)
    df_expected: pd.DataFrame = df_before.iloc[1:2, :]
    df: DataFrame[Transaction] = dt.drop_data(df_before, Path(__file__))
    pd.testing.assert_frame_equal(df, df_expected)


def test_drop_transaction_by_key_and_reason(df_before, monkeypatch, ser_bool) -> None:
    monkeypatch.setattr(dt, 'get_rows_by_string', mock_get_rows_by_string)
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
