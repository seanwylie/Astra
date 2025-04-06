#!/bin/bash

LOG_DIR="logs"
mkdir -p "$LOG_DIR"  # Ensure the logs directory exists

echo "🔍 Stopping all existing screen sessions..."
screen -ls | awk '/[0-9]+\./ {print $1}' | xargs -I {} screen -S {} -X quit
echo "✅ All existing screen sessions stopped."

echo "🚀 Waking up Astra in new screen sessions..."

# ✅ Improved: Force output capture & flush stdout/stderr
screen -dmS astra_processing bash -c "source venv/bin/activate && python3 -u -m astra_core.processing 2>&1 | tee $LOG_DIR/astra_processing.log"
screen -dmS astra_discord bash -c "source venv/bin/activate && python3 -u -m astra_core.discord_astra 2>&1 | tee $LOG_DIR/astra_discord.log"

echo "✅ Astra is now running in new screen sessions."
echo "🔎 Use 'screen -ls' to list sessions or 'screen -r astra_processing' / 'screen -r astra_discord' to attach."
echo "📜 Logs are saved in '$LOG_DIR/astra_processing.log' and '$LOG_DIR/astra_discord.log'."
#!/bin/bash

LOG_DIR="logs"
mkdir -p "$LOG_DIR"  # Ensure the logs directory exists

echo "🔍 Stopping all existing screen sessions..."
screen -ls | awk '/[0-9]+\./ {print $1}' | xargs -I {} screen -S {} -X quit
echo "✅ All existing screen sessions stopped."

echo "🚀 Launching Astra's Discord interface..."

# ✅ Launch only Discord logic with stdout/stderr piped into log file
screen -dmS astra_discord bash -c "source venv/bin/activate && python3 -u -m astra_core.discord_astra 2>&1 | tee $LOG_DIR/astra_discord.log"

echo "✅ Astra Discord session launched."
echo "🔎 Use 'screen -ls' to list sessions or 'screen -r astra_discord' to attach."
echo "📜 Logs are saved in '$LOG_DIR/astra_discord.log'."
