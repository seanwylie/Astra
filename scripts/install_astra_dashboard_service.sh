#!/usr/bin/env bash
# Install Astra Dashboard as a systemd user service (Streamlit on 8502, survive reboot).
# Run from project root or from scripts/.
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
USER_SYSTEMD="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
SERVICE_FILE="$USER_SYSTEMD/astra-dashboard.service"

if [[ ! -d "$ROOT/.venv" ]]; then
  echo "No .venv found at $ROOT/.venv. Run ./scripts/setup_venv.sh first."
  exit 1
fi

mkdir -p "$USER_SYSTEMD"
sed "s|__ASTRA_PROJECT_ROOT__|$ROOT|g" "$SCRIPT_DIR/astra-dashboard.service" > "$SERVICE_FILE"
echo "Installed $SERVICE_FILE"

systemctl --user daemon-reload
systemctl --user enable astra-dashboard
systemctl --user start astra-dashboard
echo "Astra Dashboard service enabled and started (port 8502)."

echo ""
echo "If Astra main service uses linger, the dashboard will also start at boot."
echo "Useful commands:"
echo "  systemctl --user status astra-dashboard"
echo "  journalctl --user -u astra-dashboard -f"
echo "  systemctl --user stop astra-dashboard"
echo "  systemctl --user restart astra-dashboard"
