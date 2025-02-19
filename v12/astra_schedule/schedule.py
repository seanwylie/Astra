import time
import json
from astra_schedule.dream import start_dreaming
from astra_schedule.school import start_learning
from astra_schedule.play import start_playtime
from astra_schedule.dinner import start_dinner_time
from astra_schedule.sleep import start_sleeping
from astra_core.reflection_helper import handle_reflection  # Import reflection helper

from astra_core.processing import process_reflection

def astra_test_loop():
    """Temporary 5-minute reflection loop for testing Astra's background process."""
    while True:
        print("🧠 Astra is thinking...")
        process_reflection()
        time.sleep(300)  # 5 minutes


LOG_FILE = "/home/ubuntu/astra_reflections/astra_logs.json"

def log_status(message):
    """Logs Astra's state transitions."""
    log_entry = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "status": message}
    
    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"🚨 Log Error: {e}")

# ✅ Add missing schedule functions
def is_dream_time(hour): return 3 <= hour < 7
def is_dinner_time(hour): return 18 <= hour < 19
def is_learning_time(hour): return 7 <= hour < 18 or 19 <= hour < 22
def is_playtime(hour): return 22 <= hour < 23

def astra_schedule():
    """Manages Astra's daily routine and switches between states."""
    while True:
        current_hour = time.localtime().tm_hour

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

        handle_reflection()
        time.sleep(300)  # 5 minutes