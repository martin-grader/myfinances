
.PHONY: finanzen
.PHONY: test

finanzen:
	poetry run python myfinances/main.py -o results -c config/default_public.yaml

test:
	poetry run pytest
