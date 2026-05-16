from pathlib import Path

import numpy as np
import pytest
from pandera.typing import DataFrame

from myfinances.label_data import TransactionLabeled
from myfinances.main import get_labled_data
from myfinances.monthly_costs import MonthlyCosts
from myfinances.parse_configs import ConfigPaths, Configs


@pytest.fixture
def df_all_labels() -> DataFrame[TransactionLabeled]:
    configs: Configs = Configs(
        **{
            'inputs_config': '../config/public/inputs.yaml',
            'label_config_root': '../config/public/labels',
            'rename_transactions_config': '../config/public/rename_transactions.yaml',
            'drop_transactions_config': '../config/public/drop_transactions.yaml',
        }  # type: ignore
    )
    config_paths = ConfigPaths(configs, Path(__file__))
    transactions_labled: DataFrame[TransactionLabeled] = get_labled_data(config_paths)
    return transactions_labled


@pytest.fixture
def monthly_costs(df_all_labels) -> MonthlyCosts:
    return MonthlyCosts(df_all_labels, 1)


def test_monthly_costs_negative_transactions_regression(monthly_costs) -> None:
    np.testing.assert_equal(monthly_costs.calculate_sum_negative_transactions(), -182965.09)


def test_monthly_costs_positive_transactions_regression(monthly_costs) -> None:
    np.testing.assert_equal(monthly_costs.calculate_sum_positive_transactions(), 193220.49)
