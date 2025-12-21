from abc import ABC, abstractmethod

from pandera.typing import DataFrame

from myfinances.drop_data import drop_data
from myfinances.label_data import TransactionLabeled, set_all_labels
from myfinances.parse_data import Transaction, load_data
from myfinances.rename_transactions import rename_transactions


class TransactionsInterface(ABC):
    @property
    @abstractmethod
    def df(self) -> DataFrame[TransactionLabeled]:
        pass


class TransactionLoader(TransactionsInterface):
    def __init__(self) -> None:
        self._df: DataFrame[TransactionLabeled]

    def load_labled_data(self, configs_paths) -> None:
        transactions_all: DataFrame[Transaction] = load_data(configs_paths.inputs_config)
        transactions_renamed: DataFrame[Transaction] = rename_transactions(
            transactions_all, configs_paths.rename_config
        )
        transactions_relevant: DataFrame[Transaction] = drop_data(
            transactions_renamed, configs_paths.drop_transactions_config
        )
        transactions_labled: DataFrame[TransactionLabeled] = set_all_labels(
            transactions_relevant, configs_paths.label_configs
        )
        self._df = transactions_labled

    @property
    def df(self) -> DataFrame[TransactionLabeled]:
        return self._df

    @df.setter
    def df(self, df: DataFrame[TransactionLabeled]) -> None:
        self._df = df
