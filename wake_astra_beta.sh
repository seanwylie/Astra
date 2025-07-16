#!/bin/bash

# wake_astra_beta.sh - Launch script for Astra Beta System

LOG_DIR="logs"
mkdir -p "$LOG_DIR"

echo "🔍 Stopping any existing Astra processes..."
# Stop any existing screen sessions
screen -ls | awk '/[0-9]+\.astra/ {print $1}' | xargs -I {} screen -S {} -X quit 2>/dev/null || true
echo "✅ Existing processes stopped."

echo "🚀 Launching Astra Beta System..."

# Launch the beta Discord bot
screen -dmS astra_beta bash -c "
    echo '🤖 Starting Astra Beta Discord Bot...'
    python3 -u beta/main.py 2>&1 | tee $LOG_DIR/astra_beta.log
"

# Wait a moment for startup
sleep 3

echo "✅ Astra Beta is launching!"
echo ""
echo "📊 Status Check:"
screen -ls | grep astra || echo "⚠️ No screen sessions found"
echo ""
echo "🔎 Usage:"
echo "  - View logs: tail -f $LOG_DIR/astra_beta.log"
echo "  - Attach to session: screen -r astra_beta"
echo "  - Stop bot: screen -S astra_beta -X quit"
echo ""
echo "🎉 Astra Beta deployment complete!"