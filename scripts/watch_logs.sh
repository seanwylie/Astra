#!/bin/bash
# Watch Astra log files efficiently
# This script uses tail -F (follow by name) which handles log rotation better
# and is more efficient than tail -f on multiple files

LOG_DIR="${ASTRA_LOG_DIR:-$HOME/astra_logs}"

if [ ! -d "$LOG_DIR" ]; then
    echo "Log directory not found: $LOG_DIR"
    echo "Using journalctl instead..."
    journalctl --user -u astra -f
    exit 0
fi

# Use tail -F (capital F) which follows by name and handles rotation
# This is more efficient than tail -f and works better with log rotation
tail -F "$LOG_DIR"/*.log 2>/dev/null || {
    echo "Warning: Could not watch log files directly."
    echo "Falling back to journalctl..."
    journalctl --user -u astra -f
}
