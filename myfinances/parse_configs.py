import sys
from pathlib import Path

from loguru import logger as log
from pydantic import BaseModel

from myfinances.config_utils import load_yaml


class Configs(BaseModel):
    inputs_config: str
    label_config_root: str
    rename_transactions_config: str = ''
    drop_transactions_config: str = ''
    drop_configs: list[str] = []
    add_configs: list[str] = []


class ConfigPaths:
    def __init__(self, configs: Configs) -> None:
        self.inputs_config: Path = Path().cwd() / 'config' / configs.inputs_config
        self.label_configs: list[Path] = get_all_label_configs(
            Path().cwd() / 'config' / configs.label_config_root
        )
        self.rename_config: Path = Path().cwd() / 'config' / configs.rename_transactions_config
        self.drop_transactions_config: Path = (
            Path().cwd() / 'config' / configs.drop_transactions_config
        )
        self.drop_configs: list[Path] = [
            Path().cwd() / 'config' / drop_config for drop_config in configs.drop_configs
        ]
        self.add_configs: list[Path] = [
            Path().cwd() / 'config' / add_config for add_config in configs.add_configs
        ]


def get_all_label_configs(labels_dir) -> list[Path]:
    label_configs: list[Path] = list(labels_dir.rglob('*.yaml'))
    if label_configs == []:
        log.error(f'Found no label config files in {labels_dir}')
        sys.exit()
    return list(labels_dir.rglob('*.yaml'))


def parse_all_configs(config_file: str) -> ConfigPaths:
    configs: dict = load_yaml(Path().cwd() / config_file)
    configs_checked: Configs = Configs(**configs)
    config_paths: ConfigPaths = ConfigPaths(configs_checked)
    return config_paths
