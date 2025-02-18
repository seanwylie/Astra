#!/bin/bash

echo "🔹 Stopping all existing Astra processes..."
pkill -f "python3 astra"  # Kill all running Astra-related processes

echo "🔄 Restarting Astra..."

mkdir -p logs  # Ensure logs folder exists

# Activate virtual environment
source /home/ubuntu/astra_reflections/venv/bin/activate

# Define Astra’s main directory
ASTRA_DIR="/home/ubuntu/astra_reflections"

# Auto-detect and start all Python scripts in core, interfaces, and growth folders
for script in $(find $ASTRA_DIR -type f -name "*.py" | grep -E 'astra_core|astra_interfaces|astra_growth'); do
    script_name=$(basename $script .py)
    echo "🚀 Launching $script_name..."
    nohup python3 "$script" > "$ASTRA_DIR/logs/${script_name}.log" 2>&1 & disown
done

echo "✅ Astra has been fully restarted!"
