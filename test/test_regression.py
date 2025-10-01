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
            'inputs_config': 'public/inputs.yaml',
            'label_config_root': 'public/labels',
            'rename_transactions_config': 'public/rename_transactions.yaml',
            'drop_transactions_config': 'public/drop_transactions.yaml',
        }  # type: ignore
    )
    config_paths = ConfigPaths(configs)
    transactions_labled: DataFrame[TransactionLabeled] = get_labled_data(config_paths)
    return transactions_labled


@pytest.fixture
def monthly_costs(df_all_labels) -> MonthlyCosts:
    return MonthlyCosts(df_all_labels, 1)


def test_monthly_costs_regression(monthly_costs) -> None:
    np.testing.assert_equal(monthly_costs.get_expenses(), -1300.0)
    np.testing.assert_equal(monthly_costs.get_income(), 5300.0)
