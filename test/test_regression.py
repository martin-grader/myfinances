from pathlib import Path

import numpy as np
import pytest
from pandera.typing import DataFrame

from myfinances.config_utils import Configs, to_config
from myfinances.label_data import TransactionLabeled
from myfinances.main import get_labled_data
from myfinances.monthly_costs import MonthlyCosts


@pytest.fixture
def df_all_labels() -> DataFrame[TransactionLabeled]:
    config_paths: Configs = to_config(
        Path(__file__).parent / 'data/config/default_public.yaml', Configs
    )
    transactions_labled: DataFrame[TransactionLabeled] = get_labled_data(config_paths)
    return transactions_labled


@pytest.fixture
def monthly_costs(df_all_labels) -> MonthlyCosts:
    return MonthlyCosts(df_all_labels, 1)


def test_monthly_costs_negative_transactions_regression(monthly_costs) -> None:
    np.testing.assert_equal(monthly_costs.calculate_sum_negative_transactions(), -182965.09)


def test_monthly_costs_positive_transactions_regression(monthly_costs) -> None:
    np.testing.assert_equal(monthly_costs.calculate_sum_positive_transactions(), 193220.49)
