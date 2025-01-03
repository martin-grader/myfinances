![CI passing](https://github.com/martin-grader/myfinances/actions/workflows/ci.yaml/badge.svg)
# MyFinances
A tool to analyze personal finances by categorizing and manipulating csv file based transactions. Specifically:
- Categorize transactions (by hand).
- Group the transactions by month.
- Estimate monthly expenses by category.
- Manipulate transactions by removing or adding or renaming.

# Installation
Requires python 3.12 and [poetry](https://python-poetry.org/docs/#installation).
Install required dependencies with `poetry install` and you are good to go.

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

<details>
<summary>Rename transactions</summary>
<br>
This configuration allows to change the text of transactions. This might help categorization.
<br>
See the example <a href='https://github.com/martin-grader/myfinances/blob/main/config/public/rename_transactions.yaml'>configuration</a> (`config/public/rename_transactions.yaml`) on how to rename a wrongly named transaction.
</details>

<details>
<summary>Drop transactions</summary>
This configuration allows to drop transactions before labeling happens. This avoids unnecessary work on transactions that are not of interest.
<br>
See the example <a href='https://github.com/martin-grader/myfinances/blob/main/config/public/drop_transactions.yaml'>configuration</a> (`config/public/drop_transactions.yaml`) on how to drop unwanted transaction.
</details>

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
