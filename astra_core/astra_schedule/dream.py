import time
from astra_core.processing import process_reflection

def start_dreaming(duration=1800):
    """Astra’s Dreaming Cycle (30 minutes)."""
    print("💤 Astra is dreaming...")
    start_time = time.time()
    while time.time() - start_time < duration:
        process_reflection()
        time.sleep(10)
