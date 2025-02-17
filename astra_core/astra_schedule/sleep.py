import time
from astra_core.config_loader import load_config  # ✅ Load configs dynamically

schedule_config = load_config("schedule_config")  # ✅ Load schedule settings

def start_sleeping():
    """Astra’s Sleep Mode (configurable duration)."""
    print("😴 Astra is sleeping...")

    # ✅ Use config-based sleep duration
    sleep_duration = schedule_config["sleep_duration"]
    time.sleep(sleep_duration)
