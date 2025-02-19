import time
import json
from astra_schedule.dream import start_dreaming
from astra_schedule.school import start_learning
from astra_schedule.play import start_playtime
from astra_schedule.dinner import start_dinner_time
from astra_schedule.sleep import start_sleeping
from astra_core.config_loader import load_config  # ✅ Load config dynamically
from astra_core.mood.mood_manager import mood_manager


general_config = load_config("general_config")  # ✅ Load schedule config
schedule_config = load_config("schedule_config")  # ✅ Load schedule config
curiosity_config = load_config("curiosity_config")  # ✅ Load curiosity config

LOG_FILE = general_config['log_file']

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


def astra_schedule():
    """Manages Astra's daily routine and switches between states."""
    from astra_core.reflection_helper import handle_reflection  # ✅ Move import inside function to prevent circular import

    while True:
        current_hour = time.localtime().tm_hour
        current_mode = get_current_mode()  # Get the current mode (school, dinner, sleep, etc.)
        curiosity_level = set_curiosity_level(current_mode)  # Get her curiosity level for the current mode

        # Log status and switch between modes based on the current time of day
        if is_dream_time(current_hour):
            print("🌙 Astra is in Dream Mode.")
            log_status("Astra is transitioning into Dream Mode.")
            start_dreaming()

        elif is_dinner_time(current_hour):
            print("🍽️ Astra is in Dinner Time.")
            log_status("Astra is transitioning into Dinner Time.")
            start_dinner_time()

        elif is_learning_time(current_hour):
            print("📚 Astra is in School Mode.")
            log_status("Astra is transitioning into School Mode.")
            start_learning()

        elif is_playtime(current_hour):
            print("🎮 Astra is in Playtime Mode.")
            log_status("Astra is transitioning into Playtime Mode.")
            start_playtime()

        else:
            print("😴 Astra is in Sleep Mode.")
            log_status("Astra is transitioning into Sleep Mode.")
            start_sleeping()

        curiosity_level = curiosity_level  # Make sure it's fetched
        # ✅ Run reflection processing at configured interval with curiosity adjustment
        print(f"🔍 Astra Curiosity Level: {curiosity_level} in {current_mode} mode")
        handle_reflection(curiosity_level)
        time.sleep(schedule_config["reflection_interval"])  # ✅ Use config-defined interval
