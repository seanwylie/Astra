import time
from astra_core.config_loader import load_config
from astra_core.processing import process_reflection

schedule_config = load_config("schedule_config")  # ✅ Load schedule settings

def start_dreaming():
    """Astra’s Dreaming Cycle (configurable duration)."""
    print("💤 Astra is dreaming...")
    start_time = time.time()

    # ✅ Use config-based dream duration
    duration = schedule_config["dream_duration"]

    while time.time() - start_time < duration:
        process_reflection()
        time.sleep(10)  # Short sleep to simulate dream processing
