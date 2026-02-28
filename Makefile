# Midolli-AI — Makefile
# Uses pip (not uv). Windows Git Bash paths.

PYTHON = .venv/Scripts/python
PIP = .venv/Scripts/pip
PYTEST = .venv/Scripts/pytest
UVICORN = .venv/Scripts/uvicorn

.PHONY: setup ingest serve test lint clean

setup:
	python -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt

ingest:
	$(PYTHON) backend/ingest.py

serve:
	$(UVICORN) backend.main:app --reload --port 8000

test:
	$(PYTEST) tests/ -v --cov=backend

lint:
	.venv/Scripts/ruff check backend/ tests/
	.venv/Scripts/black --check backend/ tests/

clean:
	rm -rf backend/data/vectorstore/
	rm -rf __pycache__ backend/__pycache__ tests/__pycache__
	rm -rf .pytest_cache .coverage
