# Astra: format and lint (see .cursor/rules/python-style.mdc)
# Run from project root with venv activated or use .venv/bin/python -m.

.PHONY: format lint test install-dev

format:
	black app tests utils astra_growth maintenance/*.py
	isort app tests utils astra_growth maintenance/*.py

lint:
	flake8 app tests utils astra_growth --max-line-length=100 --extend-ignore=E203,W503
	mypy app --ignore-missing-imports

# Run tests (use PYTHONPATH=. when not in venv or when venv doesn't set it)
test:
	uv run pytest tests/ -v

test-unit:
	uv run pytest tests/ -v -m "not integration"

install-dev:
	uv sync --group dev
