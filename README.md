![CI passing](https://github.com/martin-grader/myfinances/actions/workflows/ci.yaml/badge.svg)
# MyFinances
A tool to get an overview of the own finances by categorizing and manipulating csv file based transactions.

# Installation
[Install poetry](https://python-poetry.org/docs/#installation)
`poetry install`

# Usage
- Save the transactions to analyze with this tool as `.csv` file.
- Adjust all configurations as intended.
- Use `make` to categorize and adjust your finances according to the configurations.

## Data
Put your .csv transactions in e.g. `data/`. Fields for a date, and amount are required, yet naming may be different. Moreover, a fiel containing text for transaction idetification is required.

## Configurations (required)
Configurations are distributed accross several yaml files. One file with links to all relevant configuration files is required (e.g. `/config/default.public.yaml`). Necessary configurations are:

Input handling (here:`config/public/inputs.yaml`):
- Specifies keys for all relevant columns, float and date handling.
- Allows to pass several data files per wildcard.
- Different data file formats can be specified.

Labeling (here: all yaml files in `config/public/labels`):
- use `make` to iteratively set all labels and sublabels by:
- modifying existing label configurations e.g. `config/public/labels/income.yaml`


## Configurations (optional)

Renaming transactions (here: `config/public/rename_transactions.yaml`)
Dropping transactions from the analysis (here: `config/public/drop_transactions.yaml`)


## Analysis (optional)
Provides an overview of monthly expenses by label.

May be adjusted to:
Exclude transactions (here: `config/public/drop_candidates_future.yaml`)
Redefine amount of the transactions (here: `config/public/reset_candidates_future.yaml`)
Add user defined transactions (here: `config/public/add_candidates_future.yaml`)

# Testing
`make test`

# Licences
The project is licensed under the MIT License - see the LICENSE file for details.
