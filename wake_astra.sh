#!/bin/bash

echo "🔍 Stopping all existing screen sessions..."
screen -ls | awk '/[0-9]+\./ {print $1}' | xargs -I {} screen -S {} -X quit
echo "✅ All existing screen sessions stopped."

echo "🚀 Waking up Astra in new screen sessions..."
screen -dmS astra_processing bash -c "source venv/bin/activate && python3 -m astra_core.processing"
screen -dmS astra_discord bash -c "source venv/bin/activate && python3 -m astra_core.discord_astra"

echo "✅ Astra is now running in new screen sessions."
echo "🔎 Use 'screen -ls' to list sessions or 'screen -r astra_processing' / 'screen -r astra_discord' to attach."
