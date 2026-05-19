from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandera.typing import DataFrame

from myfinances.config_utils import Configs, to_config
from myfinances.label_data import TransactionLabeled
from myfinances.main import get_labled_data
from myfinances.monthly_costs import MonthlyCosts
from myfinances.parse_data import Transaction, load_data
from myfinances.rename_transactions import rename_transactions


@pytest.fixture
def config_paths() -> Configs:
    config_paths: Configs = to_config(
        Path(__file__).parent / 'data/config/default_public.yaml', Configs
    )
    return config_paths


@pytest.fixture
def df_all_labels(config_paths) -> DataFrame[TransactionLabeled]:
    transactions_labled: DataFrame[TransactionLabeled] = get_labled_data(config_paths)
    return transactions_labled


@pytest.fixture
def monthly_costs(df_all_labels) -> MonthlyCosts:
    return MonthlyCosts(df_all_labels, 1)


def test_monthly_costs_negative_transactions_regression(monthly_costs) -> None:
    np.testing.assert_equal(monthly_costs.calculate_sum_negative_transactions(), -182965.09)


def test_monthly_costs_positive_transactions_regression(monthly_costs) -> None:
    np.testing.assert_equal(monthly_costs.calculate_sum_positive_transactions(), 193220.49)


@pytest.mark.parametrize(
    'old_text, new_text', [('Fuel station', 'Diesel'), ('Fuel station refund', 'Diesel refund')]
)
def test_renamed_transactions(config_paths: Configs, old_text: str, new_text: str) -> None:
    transactions_all: DataFrame[Transaction] = load_data(config_paths.inputs_config)
    rename_candidates: pd.Series = transactions_all[Transaction.Text].str.fullmatch(old_text)
    assert rename_candidates.any()
    assert not transactions_all[Transaction.Text].str.contains(new_text).any()

    transactions_renamed: DataFrame[Transaction] = rename_transactions(
        transactions_all, config_paths.rename_transactions_config
    )
    assert (
        transactions_renamed.loc[rename_candidates, Transaction.Text].str.contains(new_text).all()
    )
    assert not (
        transactions_renamed.loc[~rename_candidates, Transaction.Text].str.fullmatch(new_text).any()
    )
