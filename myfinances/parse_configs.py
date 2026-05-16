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
    def __init__(self, configs: Configs, config_file: Path) -> None:
        self._config_directory: Path = config_file.parent
        self.inputs_config: Path = self.absolute_path(configs.inputs_config)
        self.label_configs: list[Path] = get_all_label_configs(
            self.absolute_path(configs.label_config_root)
        )
        self.rename_config: Path = self.absolute_path(configs.rename_transactions_config)
        self.drop_transactions_config: Path = self.absolute_path(configs.drop_transactions_config)
        self.drop_configs: list[Path] = [
            self.absolute_path(drop_config) for drop_config in configs.drop_configs
        ]
        self.add_configs: list[Path] = [
            self.absolute_path(add_config) for add_config in configs.add_configs
        ]

    def absolute_path(self, candidate: str) -> Path:
        path: Path = Path(candidate)
        if path.is_absolute():
            return path
        else:
            return Path(self._config_directory / candidate).absolute()


def get_all_label_configs(labels_dir) -> list[Path]:
    label_configs: list[Path] = list(labels_dir.rglob('*.yaml'))
    if label_configs == []:
        log.error(f'Found no label config files in {labels_dir}')
        sys.exit()
    return list(labels_dir.rglob('*.yaml'))


def parse_all_configs(config_file: str) -> ConfigPaths:
    configs: dict = load_yaml(Path(config_file))
    configs_checked: Configs = Configs(**configs)
    config_paths: ConfigPaths = ConfigPaths(configs_checked, Path(config_file))
    return config_paths
