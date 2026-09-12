#!/usr/bin/env bash
# Install Astra as a systemd user service (background + survive reboot).
# Run from project root or from scripts/.
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
USER_SYSTEMD="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
SERVICE_FILE="$USER_SYSTEMD/astra.service"

if [[ ! -d "$ROOT/.venv" ]]; then
  echo "No .venv found at $ROOT/.venv. Run ./scripts/setup_venv.sh first."
  exit 1
fi
if [[ ! -f "$ROOT/.env" ]]; then
  echo "No .env at $ROOT/.env. Create it with TOKEN, OPENAI_API_KEY, AWS keys, etc."
  exit 1
fi

mkdir -p "$USER_SYSTEMD"
sed "s|__ASTRA_PROJECT_ROOT__|$ROOT|g" "$SCRIPT_DIR/astra.service" > "$SERVICE_FILE"
echo "Installed $SERVICE_FILE"

systemctl --user daemon-reload
systemctl --user enable astra
systemctl --user start astra
echo "Astra service enabled and started."

echo ""
echo "To start Astra automatically after reboot (without logging in), run once:"
echo "  loginctl enable-linger $USER"
echo ""
read -p "Enable linger now? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  loginctl enable-linger "$USER"
  echo "Linger enabled. Astra will start at boot."
fi
echo ""
echo "Useful commands:"
echo "  systemctl --user status astra"
echo "  journalctl --user -u astra -f"
echo "  ./scripts/update_and_restart.sh"
