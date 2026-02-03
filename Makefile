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
	PYTHONPATH=. python -m pytest tests/ -v

test-unit:
	PYTHONPATH=. python -m pytest tests/ -v -m "not integration"

# Install dev dependencies (black, isort, flake8, mypy) - use pip or uv
install-dev:
	pip install -r requirements-dev.txt
	pip install black isort flake8 mypy
