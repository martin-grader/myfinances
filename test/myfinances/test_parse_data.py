from pathlib import Path

import pandas as pd
import pytest

import myfinances.parse_data as prsd


@pytest.fixture
def transaction_file(tmp_path_factory, request) -> dict:
    d: str = request.param['delimiter']
    c: str = request.param['decimal']
    transactions: str = f"""
a{d}b{d}c{d}d
1{c}41{d}2{c}0{d}{d}3{c}1
    """
    fn: Path = tmp_path_factory.mktemp('data') / 'transaction.csv'
    with open(fn, 'w') as f:
        f.write(transactions)
    metadata: dict = {'file_name': fn, 'delimiter': d, 'decimal': c}
    return metadata


@pytest.mark.parametrize(
    'transaction_file',
    [
        {'delimiter': ',', 'decimal': '.'},
        {'delimiter': ';', 'decimal': ','},
    ],
    indirect=True,
)
def test_load_generic(transaction_file) -> None:
    df: pd.DataFrame = prsd.load_generic(
        transaction_file['file_name'], transaction_file['delimiter'], transaction_file['decimal']
    )
    df_expected: pd.DataFrame = pd.DataFrame({'a': [1.41], 'b': [2.0], 'd': [3.1]})
    pd.testing.assert_frame_equal(df, df_expected)


@pytest.fixture
def df_amount() -> pd.DataFrame:
    df: pd.DataFrame = pd.DataFrame({'a': [1.0, 2.0], 'b': ['1,0', '2,0']})
    return df


@pytest.mark.parametrize('key', ['a', 'b'])
def test_parse_amount(df_amount, key) -> None:
    df: pd.Series = prsd.parse_amount(df_amount, key, ',')
    df_expected: pd.Series = pd.Series([1.0, 2.0], name=key)
    pd.testing.assert_series_equal(df, df_expected)


@pytest.fixture
def df_dates() -> pd.DataFrame:
    df: pd.DataFrame = pd.DataFrame({'a': ['04-10-2023'], 'b': ['04-10-23']})
    return df


@pytest.mark.parametrize(('key', 'model'), [('a', '%d-%m-%Y'), ('b', '%d-%m-%y')])
def test_parse_dates(df_dates, key, model) -> None:
    df: pd.Series = prsd.parse_dates(df_dates, key, model)
    df_expected: pd.Series = pd.Series([pd.Timestamp(year=2023, month=10, day=4)], name=key)
    pd.testing.assert_series_equal(df, df_expected)


def test_parse_text() -> None:
    df_unprocessed: pd.DataFrame = pd.DataFrame({'a': ['a', pd.NaT], 'b': ['b', 'c']})
    df: pd.Series = prsd.parse_text(df_unprocessed, ['a', 'b'])
    df_expected: pd.Series = pd.Series(['a;b', '-;c'])
    pd.testing.assert_series_equal(df, df_expected)
