import time
import json
import random
import asyncio
import pytz
import signal
from datetime import datetime
from app.config.loader import load_config
from app.core.processing import process_reflection
from app.core.astra_schedule.dream import start_dreaming
from app.core.astra_schedule.school import start_learning
from app.core.astra_schedule.play import start_playtime
from app.core.astra_schedule.dinner import start_dinner_time
from app.core.astra_schedule.sleep import start_sleeping
from app.core.mood.mood_manager import mood_manager
from app.logging_config import get_logger

schedule_logger = get_logger("schedule")

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

def get_current_hour():
    tz_name = schedule_config.get("timezone", "UTC")
    tz = pytz.timezone(tz_name)
    return datetime.now(tz).hour

def get_current_mode():
    current_hour = get_current_hour()
    if is_dream_time(current_hour): 
        return "dream"
    elif is_learning_time(current_hour): 
        return "school"
    elif is_playtime(current_hour): 
        return "play"
    elif is_dinner_time(current_hour): 
        return "dinner"
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

async def astra_schedule(bot=None, channel_id=None):
    global last_state

    print("🟢 Astra Schedule Loop Initialized")

    while True:
        current_mode = get_current_mode()
        curiosity_level = set_curiosity_level(current_mode)

        print(f"🔄 Processing {current_mode} Mode | Curiosity: {curiosity_level}")

        if current_mode != last_state:
            notification = get_random_notification(current_mode)
            print(f"🔔 {notification}")  # Replaces SMS
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
            if schedule_config.get("sleep_mood_decay_enabled", True):
                try:
                    mood_manager.influence_mood("idle")
                except Exception as e:
                    print(f"[schedule] influence_mood idle failed: {e}")

        print(f"🔍 Astra Curiosity Level: {curiosity_level} in {current_mode} mode")

        if current_mode != "dream":
            def _on_reflection_done(task):
                exc = task.exception()
                if exc is not None:
                    schedule_logger.exception("process_reflection failed: %s", exc)

            task = asyncio.create_task(process_reflection())
            task.add_done_callback(_on_reflection_done)

        if asyncio.current_task().cancelled():
            print("🛑 Task was cancelled. Exiting schedule loop.")
            break

        print(f"🔁 Sleeping for {schedule_config['reflection_interval']} seconds before next loop...")
        await asyncio.sleep(schedule_config["reflection_interval"])

# --- Graceful Shutdown Entrypoint ---
if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, loop.stop)
        loop.run_until_complete(astra_schedule())
    except KeyboardInterrupt:
        print("👋 Gracefully shutting down Astra...")
