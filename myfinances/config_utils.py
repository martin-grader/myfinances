from pathlib import Path
from typing import Annotated

import yaml
from loguru import logger as log
from pydantic import BaseModel, BeforeValidator, TypeAdapter, ValidationError
from pydantic.dataclasses import dataclass


@dataclass
class LabelMinimal:
    Label: str
    Sublabel: str
    Amount: float = 0.0
    IsIncome: bool = False


@dataclass
class Label:
    Label: str
    Sublabel: str
    Identifier: str = ''
    Amount: float = 0.0
    IsIncome: bool = False


def load_yaml(file_to_load: Path) -> dict:
    with open(file_to_load, 'r') as file:
        raw: dict = yaml.safe_load(file)
    return raw


def ensure_path(value: str, info) -> list[Path] | Path:
    base_dir: str = info.context['base']
    return _resolve(value, base_dir)


def _resolve(value: list[str] | str, base: str) -> list[Path] | Path:
    if isinstance(value, list):
        return [_resolve(x, base) for x in value]  # type: ignore
    p = Path(value)
    abs_path: Path = p if p.is_absolute() else base / p
    if not abs_path.exists():
        raise FileExistsError(abs_path)
    return abs_path.resolve()


class TransactionLabelsPrototype:
    def __init__(self, config_file) -> None:
        self.config: dict = load_yaml(config_file)
        self.transactions: list[Label] = []


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
    IsIncome: bool = False


class AddLabels(TransactionLabelsPrototype):
    def __init__(self, config_file) -> None:
        super().__init__(config_file)
        add_configs: list[AddConfig] = [
            to_add_config(add_candidate) for add_candidate in self.config.values()
        ]
        self.transactions: list[Label] = [
            Label(add_config.Label, add_config.Sublabel, '', add_config.Amount, add_config.IsIncome)
            for add_config in add_configs
        ]
        self.transactions_clean: list[LabelMinimal] = [
            LabelMinimal(
                add_config.Label, add_config.Sublabel, add_config.Amount, add_config.IsIncome
            )
            for add_config in add_configs
        ]


class LabelConfig(BaseModel):
    label: str
    sublabels: dict[str, list[str]]
    is_income: bool = False


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
    Files: Annotated[list[Path], BeforeValidator(ensure_path)]
    Delimiter: str
    Decimal: str
    DateKey: str
    DateFormat: str
    AmountKey: str
    TextKeys: list[str]


class Configs(BaseModel):
    inputs_config: Annotated[Path, BeforeValidator(ensure_path)]
    label_configs: Annotated[list[Path], BeforeValidator(ensure_path)]

    rename_transactions_config: Annotated[Path, BeforeValidator(ensure_path)] = Path()
    drop_transactions_config: Annotated[Path, BeforeValidator(ensure_path)] = Path()
    drop_configs: Annotated[list[Path], BeforeValidator(ensure_path)] = []
    add_configs: Annotated[list[Path], BeforeValidator(ensure_path)] = []


def to_config(config_file: Path, config_definition):
    config: dict = load_yaml(config_file)
    ta = TypeAdapter(config_definition)
    try:
        rename_config = ta.validate_python(config, context={'base': config_file.parent})
    except ValidationError as e:
        log.error(e.errors())
        raise
    return rename_config
