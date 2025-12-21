from pathlib import Path
from typing import cast

import pandas as pd
import pytest
from pandera.typing import DataFrame

from myfinances.label_data import TransactionLabeled

# from myfinances.parse_configs import ConfigPaths
# from myfinances.parse_configs import ConfigPaths
from myfinances.transaction_loader import TransactionLoader


@pytest.fixture()
def test_df() -> DataFrame[TransactionLabeled]:
    df = TransactionLabeled.example(size=1)
    return cast(DataFrame[TransactionLabeled], df)


class ConfigPathsMock:
    def __init__(self) -> None:
        self.inputs_config: Path = Path()
        self.label_configs: list[Path] = [Path()]
        self.rename_config: Path = Path()
        self.drop_transactions_config: Path = Path()
        self.drop_configs: list[Path] = [Path()]
        self.add_configs: list[Path] = [Path()]


# @pytest.fixture()
# def configs_paths_mock() -> ConfigPaths:
#    return ConfigPathsMock()


class TestTransactionLoader:
    def test_init(self) -> None:
        assert TransactionLoader()

    def test_df(self, test_df) -> None:
        loader = TransactionLoader()
        loader.df = test_df
        pd.testing.assert_frame_equal(loader.df, test_df)
