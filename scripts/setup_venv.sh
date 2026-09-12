#!/usr/bin/env bash
# Create and use a venv for Astra (avoids system pip / PEP 668).
set -e
cd "$(dirname "$0")/.."
VENV="${1:-.venv}"
if [[ ! -d "$VENV" ]]; then
  python3 -m venv "$VENV"
  echo "Created venv at $VENV"
fi
"$VENV/bin/pip" install -r requirements.txt
if [[ -f requirements-dev.txt ]]; then
  "$VENV/bin/pip" install -r requirements-dev.txt
fi
echo ""
echo "Activate with:"
echo "  source $VENV/bin/activate"
echo "Then run: python -m app.main  or  pytest"
