import time
import json
import random
import asyncio
from astra_schedule.dream import start_dreaming
from astra_schedule.school import start_learning
from astra_schedule.play import start_playtime
from astra_schedule.dinner import start_dinner_time
from astra_schedule.sleep import start_sleeping
from astra_core.config_loader import load_config
from astra_core.mood.mood_manager import mood_manager
from astra_core.astra_helpers.sms_helper import send_sms  # ✅ Import SMS helper

# ✅ Load configurations
general_config = load_config("general_config")
schedule_config = load_config("schedule_config")
curiosity_config = load_config("curiosity_config")

LOG_FILE = general_config['log_file']
last_state = None  # ✅ Track Astra’s last known state to avoid repeat notifications


def log_status(message):
    """Logs Astra's state transitions."""
    log_entry = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "status": message}
    
    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"🚨 Log Error: {e}")


# ✅ Dynamic Schedule Functions
def is_dream_time(hour): return schedule_config["dream_time"][0] <= hour < schedule_config["dream_time"][1]
def is_dinner_time(hour): return schedule_config["dinner_time"][0] <= hour < schedule_config["dinner_time"][1]
def is_learning_time(hour): return any(start <= hour < end for start, end in schedule_config["learning_time"])
def is_playtime(hour): return schedule_config["play_time"][0] <= hour < schedule_config["play_time"][1]


def get_current_mode():
    """Returns the current mode based on the time of day."""
    current_hour = time.localtime().tm_hour

    if is_dream_time(current_hour):
        return "dream"
    elif is_learning_time(current_hour):
        return "school"
    elif is_playtime(current_hour):
        return "play"
    elif is_dinner_time(current_hour):
        return "dinner"
    else:
        return "sleep"


def set_curiosity_level(mode):
    """Set Astra's curiosity level based on both mode and mood."""
    base_curiosity = curiosity_config.get(mode, 1.0)  # Default to 1.0 if mode not found
    mood_factor = mood_manager.curiosity_level  # Get mood-adjusted curiosity factor

    # Adjust curiosity dynamically
    adjusted_curiosity = base_curiosity * mood_factor
    return round(adjusted_curiosity, 2)  # Keep values readable


def get_random_notification(mode):
    """Selects a random notification message from `schedule_config.json`."""
    messages = schedule_config.get("state_change_messages", {}).get(mode, [])
    return random.choice(messages) if messages else f"Astra is now in {mode} mode!"


async def astra_schedule():
    """Manages Astra's daily routine and switches between states asynchronously."""
    
    # 🔥 Lazy import to break circular dependency
    from astra_core.processing import process_reflection

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
            await start_dinner_time()

        elif current_mode == "school":
            print("📚 Astra is in School Mode.")
            await start_learning()  # ✅ Ensure this is awaited

        elif current_mode == "play":
            print("🎮 Astra is in Playtime Mode.")
            await start_playtime()

        else:
            print("😴 Astra is in Sleep Mode. No active schedule detected.")
            await start_sleeping()

        # ✅ Ensure curiosity level updates based on actual mode
        curiosity_level = set_curiosity_level(get_current_mode())
        print(f"🔍 Astra Curiosity Level: {curiosity_level} in {current_mode} mode")

        if current_mode != "dream":
            print(f"🔍 Debug: Calling handle_reflection({curiosity_level})")
            await process_reflection()  # ✅ Now correctly imported

        print(f"🔁 Sleeping for {schedule_config['reflection_interval']} seconds before next loop...")
        await asyncio.sleep(schedule_config["reflection_interval"])  # ✅ Ensure async behavior
