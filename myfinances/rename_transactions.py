from pathlib import Path

import pandas as pd
from pandera.typing import DataFrame

from myfinances.config_utils import RenameConfigs, to_config
from myfinances.parse_data import Transaction
from myfinances.utils import get_rows_by_exact_string


def rename_transactions(
    df: DataFrame[Transaction], rename_transaction_config: Path
) -> DataFrame[Transaction]:
    rename_transactions_class: RenameConfigs = to_config(rename_transaction_config, RenameConfigs)
    for transaction in rename_transactions_class.transactions:
        rename_transaction(df, transaction.old_text, transaction.new_text)
    return df


def rename_transaction(
    df: DataFrame[Transaction], old_text: str, new_text: str
) -> DataFrame[Transaction]:
    rows_to_rename: pd.Series = get_rows_by_exact_string(df, old_text)
    df.loc[rows_to_rename, Transaction.Text] = new_text
    return df
