#!/usr/bin/env bash
# Pull latest code, optionally refresh deps, restart Astra service.
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

echo "Pulling latest code..."
git pull

if [[ -f .venv/bin/pip ]]; then
  echo "Refreshing dependencies..."
  .venv/bin/pip install -q -r requirements.txt
fi

echo "Restarting Astra service..."
systemctl --user restart astra

echo ""
systemctl --user status astra --no-pager
