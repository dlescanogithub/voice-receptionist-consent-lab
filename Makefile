.PHONY: setup lint format typecheck test secretscan ci

PYTHON := $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi)

setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install -e ".[dev]"
	.venv/bin/pre-commit install

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

format:
	$(PYTHON) -m ruff format .
	$(PYTHON) -m ruff check --fix .

typecheck:
	$(PYTHON) -m mypy

test:
	$(PYTHON) -m pytest

secretscan:
	$(PYTHON) -m consent_lab secretscan .

ci: lint typecheck test secretscan
