.PHONY: setup test cov run lint docs clean wheel

PYTHON ?= python3
VENV ?= .venv
VENV_BIN := $(VENV)/bin

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -e .[dev]

test:
	$(PYTHON) -m pytest

cov:
	$(PYTHON) -m pytest --cov=code_crawler --cov-report=term-missing

run:
	$(PYTHON) -m code_crawler --input code_crawler --no-diagrams --no-graph --no-explain-cards --no-badges --no-metrics --no-bundles --no-summary

lint:
	$(PYTHON) -m ruff check code_crawler tests
	$(PYTHON) -m mypy code_crawler

docs:
	mkdir -p build
	$(PYTHON) -m code_crawler --help > build/cli_help.txt

clean:
	rm -rf $(VENV) build code_crawler_runs

wheel:
	$(PYTHON) -m build
