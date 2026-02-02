#!/bin/bash
# Wake Astra: start or restart the Astra systemd user service.
# Install once with: ./scripts/install_astra_service.sh

if ! systemctl --user restart astra 2>/dev/null; then
  echo "Astra service not installed. Run first:"
  echo "  ./scripts/install_astra_service.sh"
  exit 1
fi

echo "Astra service restarted."
echo ""
echo "  Status:  systemctl --user status astra"
echo "  Logs:    journalctl --user -u astra -f"
echo "  Update:  ./scripts/update_and_restart.sh"
