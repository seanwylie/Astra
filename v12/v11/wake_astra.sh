#!/bin/bash

echo "🔄 Restarting Astra..."
pkill -f astra_discord.py
pkill -f astra_reflection.py
sleep 2  # Allow processes to fully terminate

echo "🚀 Starting Astra..."
source venv/bin/activate  # Activate virtual environment
python3 astra_discord.py &  # Run Discord bot in background
python3 astra_reflection.py &  # Run reflection loop in background
disown  # Keep processes running after closing the terminal

echo "✅ Astra is now running!"
