import time
import random
import asyncio
from astra_core.config_loader import load_config  # ✅ Load configs dynamically
from astra_core.processing import process_reflection

schedule_config = load_config("schedule_config")  # ✅ Load schedule settings

async def start_learning():
    print("📚 Astra is in school, learning and thinking...")

    await process_reflection()  # ✅ Properly await reflection processing

    # ✅ Use config-based random sleep duration
    sleep_duration = random.randint(
        schedule_config["learning_interval_min"],
        schedule_config["learning_interval_max"]
    )

    print(f"⏳ Sleeping for {sleep_duration} seconds before continuing learning...")
    await asyncio.sleep(sleep_duration)  # ✅ Ensure non-blocking behavior

