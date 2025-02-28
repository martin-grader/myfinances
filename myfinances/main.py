import sys
from argparse import Namespace

import pandas as pd
from loguru import logger as log
from pandera.typing import DataFrame

from myfinances.dashboard import Dashboard
from myfinances.drop_data import drop_data
from myfinances.label_data import TransactionLabeled, set_all_labels
from myfinances.monthly_costs import MonthlyCosts
from myfinances.parse_arguments import get_parsed_arguments
from myfinances.parse_configs import ConfigPaths, parse_all_configs
from myfinances.parse_data import Transaction, load_data
from myfinances.rename_transactions import rename_transactions

pd.set_option('display.max_colwidth', None)
log.remove(0)
log.add(sys.stderr, level='INFO')


def main() -> None:
    args: Namespace = get_parsed_arguments()
    configs_paths: ConfigPaths = parse_all_configs(args.config)

    transactions_labled: DataFrame[TransactionLabeled] = get_labled_data(configs_paths)

    monthly_costs: MonthlyCosts = MonthlyCosts(transactions_labled)
    for drop_config in configs_paths.drop_configs:
        monthly_costs.drop_costs_by_config(drop_config)
    for add_config in configs_paths.add_configs:
        monthly_costs.add_costs_by_config(add_config)
    log.info(monthly_costs.get_averaged_expenses_by_label())
    log.info(monthly_costs.get_averaged_expenses_by_label().sum())
    log.info(monthly_costs.get_monthly_expenses())

    if args.dashboard:
        dashboard: Dashboard = Dashboard(monthly_costs)
        dashboard.run()


def get_labled_data(configs_paths) -> DataFrame[TransactionLabeled]:
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
    return transactions_labled


if __name__ == '__main__':
    main()
