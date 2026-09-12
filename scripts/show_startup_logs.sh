#!/bin/bash
# Show Astra startup logs clearly

echo "=== ASTRA STARTUP LOGS (Last Restart) ==="
echo ""

# Get the most recent restart time
RESTART_TIME=$(journalctl --user -u astra.service --no-pager | grep "Started astra.service" | tail -1 | awk '{print $1" "$2" "$3}')

if [ -z "$RESTART_TIME" ]; then
    echo "No restart found in logs. Showing last 5 minutes:"
    journalctl --user -u astra.service --since "5 minutes ago" --no-pager | grep -E "(Starting|Bot is ready|on_ready|on_connect|EVENT HANDLER|FINAL VERIFICATION|Astra initialized|Discord gateway)" | tail -20
else
    echo "Restart detected at: $RESTART_TIME"
    echo ""
    echo "=== STARTUP SEQUENCE ==="
    journalctl --user -u astra.service --since "$RESTART_TIME" --no-pager | grep -E "(Starting|Bot is ready|on_ready|on_connect|EVENT HANDLER|FINAL VERIFICATION|Astra initialized|Discord gateway|📨📨📨)" | head -30
fi

echo ""
echo "=== RECENT MESSAGE EVENTS ==="
journalctl --user -u astra.service --since "10 minutes ago" --no-pager | grep "📨📨📨" | tail -10

echo ""
echo "=== CURRENT STATUS ==="
systemctl --user status astra.service --no-pager -l | head -15
