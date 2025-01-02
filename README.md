![CI passing](https://github.com/martin-grader/myfinances/actions/workflows/ci.yaml/badge.svg)
# MyFinances
A tool to get an overview of the own finances by categorizing and manipulating transactions

# Installation
[Install poetry](https://python-poetry.org/docs/#installation)
`poetry install`

# Usage
- Save the transactions to analyze with this tool as `.csv` file.
- Adjust all configurations as intended
- Use `make` to categorize and adjust your finances according to the configurations.

## Data
- put your csv transactions in e.g. data
## Configuration
- modify `config/public/inputs.yaml` to comply with your dataset.
- use `make` to iteratively set all labels and sublabels by:
    - modifying existing label configurations e.g. `config/public/labels/income.yaml`
    - add more configurations according to your needs

# Testing
`make test`

# Licences
The project is licensed under the MIT License - see the LICENSE file for details.
