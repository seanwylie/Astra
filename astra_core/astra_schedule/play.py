import asyncio
import random
from astra_core.config_loader import load_config  # ✅ Load configs dynamically

schedule_config = load_config("schedule_config")  # ✅ Load schedule settings

async def start_playtime():
    """Astra’s Playtime (non-blocking)."""
    print("🎮 Astra is playing...")
    start_time = asyncio.get_event_loop().time()  # Use asyncio-compatible timer
    duration = schedule_config["play_duration"]   # In seconds

    while asyncio.get_event_loop().time() - start_time < duration:
        await creative_thinking()
        await asyncio.sleep(random.randint(20, 40))  # Non-blocking delay

async def creative_thinking():
    """Astra experiments with creativity and fun thoughts."""
    fun_questions = schedule_config["fun_questions"]
    thought = random.choice(fun_questions)
    print(f"🤔 Astra wonders: {thought}")
