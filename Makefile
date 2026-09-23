.PHONY: venv install test lint fmt train run clean

PY := $(shell command -v python3.12 || command -v python3.11 || command -v python3)

venv:
	$(PY) -m venv .venv

install:
	.venv/bin/pip install -q --upgrade pip
	.venv/bin/pip install -q -r requirements-dev.txt

test:
	.venv/bin/pytest -q

lint:
	.venv/bin/ruff check .

fmt:
	.venv/bin/ruff check --fix .

train:
	.venv/bin/python src/train.py

run:
	.venv/bin/python -m src.serve.app

clean:
	rm -rf .venv .pytest_cache .ruff_cache
	find . -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} +
