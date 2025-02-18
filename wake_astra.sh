#!/bin/bash

# Function to find and kill existing Astra processes
kill_astra() {
    echo "$(date): Checking for running Astra processes..."
    DISCORD_PIDS=$(pgrep -f astra_discord.py)
    PROCESSING_PIDS=$(pgrep -f astra_processing.py)
    if [ -n "$DISCORD_PIDS" ]; then
        echo "$(date): Killing existing astra_discord.py processes: $DISCORD_PIDS"
        kill -9 $DISCORD_PIDS
    else
        echo "$(date): No existing astra_discord.py processes found."
    fi
    if [ -n "$PROCESSING_PIDS" ]; then
        echo "$(date): Killing existing astra_processing.py processes: $PROCESSING_PIDS"
        kill -9 $PROCESSING_PIDS
    else
        echo "$(date): No existing astra_processing.py processes found."
    fi
}

# Function to start Astra processes
start_astra() {
    echo "$(date): Starting Astra processes..."
    cd /home/ubuntu/astra_reflections || exit  # Navigate to Astra's directory
    source venv/bin/activate  # Activate the virtual environment
    nohup python3 astra_discord.py >> astra_discord.log 2>&1 &
    echo "$(date): astra_discord.py started with PID $!"
    nohup python3 astra_processing.py >> astra_processing.log 2>&1 &
    echo "$(date): astra_processing.py started with PID $!"
}

# Main script execution
kill_astra  # Kill existing Astra processes before starting new ones
start_astra  # Start Astra processes

# Monitor Astra processes and restart if they crash
while true; do
    sleep 5  # Wait before checking
    if ! pgrep -f astra_discord.py > /dev/null; then
        echo "$(date): astra_discord.py crashed! Restarting..."
        nohup python3 astra_discord.py >> astra_discord.log 2>&1 &
        echo "$(date): astra_discord.py restarted with PID $!"
    fi
    if ! pgrep -f astra_processing.py > /dev/null; then
        echo "$(date): astra_processing.py crashed! Restarting..."
        nohup python3 astra_processing.py >> astra_processing.log 2>&1 &
        echo "$(date): astra_processing.py restarted with PID $!"
    fi
    sleep 5  # Additional wait time before the next check
done
