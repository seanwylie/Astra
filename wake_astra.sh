#!/bin/bash

echo "🔄 Restarting Astra..."
pkill -f astra_discord.py
pkill -f astra_reflection.py
pkill -f astra_vision.py
sleep 2  # Allow processes to fully terminate

echo "🚀 Starting Astra..."
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "⚠ Virtual environment not found! Run 'python3 -m venv venv' to create one."
    exit 1
fi


python3 astra_discord.py &  # Run Discord bot in background
python3 astra_reflection.py &  # Run reflection loop in background
python3 astra_vision.py &  # Run reflection loop in background
disown  # Keep processes running after closing the terminal

echo "✅ Astra is now running!"
