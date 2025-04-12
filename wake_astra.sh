#!/bin/bash

LOG_DIR="logs"
mkdir -p "$LOG_DIR"  # Ensure the logs directory exists

echo "🔍 Stopping all existing screen sessions..."
screen -ls | awk '/[0-9]+\./ {print $1}' | xargs -I {} screen -S {} -X quit
echo "✅ All existing screen sessions stopped."

echo "🚀 Launching Astra's components..."

# ✅ Launch schedule manager
screen -dmS astra_schedule bash -c "source venv/bin/activate && python3 -u astra_core/astra_schedule/schedule.py 2>&1 | tee $LOG_DIR/astra_schedule.log"

# ✅ Launch Discord interface
screen -dmS astra_discord bash -c "source venv/bin/activate && python3 -u -m astra_core.discord_astra 2>&1 | tee $LOG_DIR/astra_discord.log"

echo "✅ Astra is fully online!"
echo "🔎 Use 'screen -ls' to list sessions."
echo "💬 Attach with 'screen -r astra_schedule' or 'screen -r astra_discord'."
echo "📜 Logs: '$LOG_DIR/astra_schedule.log' and '$LOG_DIR/astra_discord.log'"
