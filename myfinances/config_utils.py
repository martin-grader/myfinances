from pathlib import Path

import yaml
from loguru import logger as log
from pydantic import BaseModel, TypeAdapter, ValidationError
from pydantic.dataclasses import dataclass


@dataclass
class LabelMinimal:
    Label: str
    Sublabel: str
    Amount: float = 0.0


@dataclass
class Label:
    Label: str
    Sublabel: str
    Identifier: str = ''
    Amount: float = 0.0


def load_yaml(file_to_load: Path) -> dict:
    with open(file_to_load, 'r') as file:
        test = yaml.safe_load(file)
    return test


class TransactionLabelsPrototype:
    def __init__(self, config_file) -> None:
        self.config: dict = load_yaml(config_file)
        self.transactions: list[Label] = []


class TransactionLabels(TransactionLabelsPrototype):
    def __init__(self, config_file) -> None:
        super().__init__(config_file)
        transaction_config: LabelConfig = to_label_config(self.config)
        self.transactions: list[Label] = [
            Label(transaction_config.label, sublabel, identifier)
            for sublabel, identifiers in transaction_config.sublabels.items()
            for identifier in identifiers
        ]


class DropLabels(TransactionLabelsPrototype):
    def __init__(self, config_file) -> None:
        super().__init__(config_file)
        self.transactions: list[Label] = [
            Label(label, sublabel)
            for label, sublabels in self.config.items()
            for sublabel in sublabels
        ]


class AddConfig(BaseModel):
    Label: str
    Sublabel: str
    Amount: float


class AddLabels(TransactionLabelsPrototype):
    def __init__(self, config_file) -> None:
        super().__init__(config_file)
        add_configs: list[AddConfig] = [
            to_add_config(add_candidate) for add_candidate in self.config.values()
        ]
        self.transactions: list[Label] = [
            Label(add_config.Label, add_config.Sublabel, '', add_config.Amount)
            for add_config in add_configs
        ]
        self.transactions_clean: list[LabelMinimal] = [
            LabelMinimal(add_config.Label, add_config.Sublabel, add_config.Amount)
            for add_config in add_configs
        ]


class LabelConfig(BaseModel):
    label: str
    sublabels: dict[str, list[str]]


def to_label_config(config: dict) -> LabelConfig:
    try:
        label_config: LabelConfig = LabelConfig(**config)
    except ValidationError as e:
        log.error(e.errors())
        raise
    return label_config


def to_add_config(config: dict) -> AddConfig:
    try:
        add_config: AddConfig = AddConfig(**config)
    except ValidationError as e:
        log.error(e.errors())
        raise
    return add_config


class RenameConfig(BaseModel):
    old_text: str
    new_text: str


class RenameConfigs(BaseModel):
    transactions: list[RenameConfig]


class InputConfig(BaseModel):
    Account: str
    Files: list[str]
    Delimiter: str
    Decimal: str
    DateKey: str
    DateFormat: str
    AmountKey: str
    TextKeys: list[str]


def to_config(config_file: Path, config_definition):
    config: dict = load_yaml(config_file)
    ta = TypeAdapter(config_definition)
    try:
        rename_config = ta.validate_python(config)
    except ValidationError as e:
        log.error(e.errors())
        raise
    return rename_config
