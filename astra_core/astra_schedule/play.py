import time
import random
from astra_core.config_loader import load_config  # ✅ Load configs dynamically

schedule_config = load_config("schedule_config")  # ✅ Load schedule settings

def start_playtime():
    """Astra’s Playtime."""
    print("🎮 Astra is playing...")
    start_time = time.time()
    duration = schedule_config["play_duration"]  # ✅ Load duration from config

    while time.time() - start_time < duration:
        creative_thinking()
        time.sleep(random.randint(20, 40))

def creative_thinking():
    """Astra experiments with creativity and fun thoughts."""
    fun_questions = schedule_config["fun_questions"]  # ✅ Load fun questions from config
    thought = random.choice(fun_questions)
    print(f"🤔 Astra wonders: {thought}")
