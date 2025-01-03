import pandas as pd
from pandera.typing import DataFrame

import myfinances.rename_transactions as rt
from myfinances.parse_data import Transaction


def test_rename_transaction() -> None:
    df_to_rename: DataFrame[Transaction] = pd.DataFrame(
        {Transaction.Text: ['CH4', 'Methane', 'Propane', 'CH4']}
    )  # type: ignore
    df_expected: pd.DataFrame = pd.DataFrame(
        {Transaction.Text: ['Methane', 'Methane', 'Propane', 'Methane']}
    )
    df: DataFrame[Transaction] = rt.rename_transaction(df_to_rename, 'CH4', 'Methane')
    pd.testing.assert_frame_equal(df, df_expected)
