#!/bin/bash
echo "Starting Astra Core..."
nohup python3 -m astra_core.processing > astra_core.log 2>&1 &

echo "Starting Astra Discord Interface..."
nohup python3 -m astra_core.discord_astra > discord_astra.log 2>&1 &

echo "Astra is running!"
