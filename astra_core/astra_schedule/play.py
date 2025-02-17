import time
import random

def start_playtime(duration=600):
    """Astra’s Playtime (10 minutes)."""
    print("🎮 Astra is playing...")
    start_time = time.time()
    while time.time() - start_time < duration:
        creative_thinking()
        time.sleep(random.randint(20, 40))

def creative_thinking():
    """Astra experiments with creativity and fun thoughts."""
    fun_questions = [
        "What if Astra were a fictional character?",
        "If Astra could redesign herself, what new abilities would she want?",
        "What’s the strangest philosophical question Astra can generate?"
    ]
    thought = random.choice(fun_questions)
    print(f"🤔 Astra wonders: {thought}")
