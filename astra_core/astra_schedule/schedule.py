import time
import json
import shutil
import subprocess
import random
import os
import asyncio
from astra_core.config_loader import load_config, debug_log
from astra_interfaces.influence import load_mind, save_mind
from astra_core.knowledge import knowledge_manager
from astra_core.processing import process_reflection
from astra_schedule.dream import start_dreaming
from astra_schedule.school import start_learning
from astra_schedule.play import start_playtime
from astra_schedule.sleep import start_sleeping
from astra_core.mood.mood_manager import mood_manager
from astra_core.astra_helpers.sms_helper import send_sms

# ✅ Load configurations
schedule_config = load_config("schedule_config")
general_config = load_config("general_config")
curiosity_config = load_config("curiosity_config")

LOG_FILE = general_config['log_file']
last_state = None

# Schedule Check Functions
def is_dream_time(hour): return schedule_config["dream_time"][0] <= hour < schedule_config["dream_time"][1]
def is_dinner_time(hour): return schedule_config["dinner_time"][0] <= hour < schedule_config["dinner_time"][1]
def is_learning_time(hour): return any(start <= hour < end for start, end in schedule_config["learning_time"])
def is_playtime(hour): return schedule_config["play_time"][0] <= hour < schedule_config["play_time"][1]

def get_current_mode():
    current_hour = time.localtime().tm_hour
    if is_dream_time(current_hour): return "dream"
    elif is_learning_time(current_hour): return "school"
    elif is_playtime(current_hour): return "play"
    elif is_dinner_time(current_hour): return "dinner"
    return "sleep"

def set_curiosity_level(mode):
    base = curiosity_config.get(mode, 1.0)
    return round(base * mood_manager.curiosity_level, 2)

def get_random_notification(mode):
    messages = schedule_config.get("state_change_messages", {}).get(mode, [])
    return random.choice(messages) if messages else f"Astra is now in {mode} mode!"

def log_status(message):
    log_entry = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "status": message}
    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"🚨 Log Error: {e}")

async def astra_schedule(bot, channel_id):
    from astra_schedule.dinner import start_dinner_time  # Lazy import to avoid circular issues
    global last_state

    while True:
        current_mode = get_current_mode()
        curiosity_level = set_curiosity_level(current_mode)

        print(f"🔄 Processing {current_mode} Mode | Curiosity: {curiosity_level}")

        if current_mode != last_state:
            notification = get_random_notification(current_mode)
            send_sms(notification)
            print(f"📨 SMS Sent: {notification}")
            log_status(f"Astra is transitioning into {current_mode} mode.")
            last_state = current_mode

        if current_mode == "dream":
            print("🌙 Astra is in Dream Mode.")
            await start_dreaming()

        elif current_mode == "dinner":
            print("🍽️ Astra is in Dinner Time.")
            await start_dinner_time(bot, channel_id)

        elif current_mode == "school":
            print("📚 Astra is in School Mode.")
            await start_learning()

        elif current_mode == "play":
            print("🎮 Astra is in Playtime Mode.")
            await start_playtime()

        else:
            print("😴 Astra is in Sleep Mode. No active schedule detected.")
            await start_sleeping()

        print(f"🔍 Astra Curiosity Level: {curiosity_level} in {current_mode} mode")

        if current_mode != "dream":
            print(f"🔍 Debug: Calling handle_reflection({curiosity_level})")
            await process_reflection()

        print(f"🔁 Sleeping for {schedule_config['reflection_interval']} seconds before next loop...")
        await asyncio.sleep(schedule_config["reflection_interval"])

# NOTE: Do not use asyncio.run() here to avoid runtime loop conflicts from Discord
