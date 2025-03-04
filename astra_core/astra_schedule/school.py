import time
import random
from astra_core.config_loader import load_config  # ✅ Load configs dynamically
from astra_core.processing import process_reflection


schedule_config = load_config("schedule_config")  # ✅ Load schedule settings

def start_learning():
    """Astra’s Active Learning (configurable intervals)."""
    print("📚 Astra is in school, learning and thinking...")
    process_reflection()

    # ✅ Use config-based random sleep duration
    sleep_duration = random.randint(
        schedule_config["learning_interval_min"],
        schedule_config["learning_interval_max"]
    )

    time.sleep(sleep_duration)
