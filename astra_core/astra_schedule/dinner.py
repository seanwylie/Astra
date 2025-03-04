import time
from astra_core.config_loader import load_config  # ✅ Load configs dynamically


schedule_config = load_config("schedule_config")  # ✅ Load schedule settings

def start_dinner_time():
    """Dinner Time: Astra checks in with us, shares her thoughts, and receives new guidance."""
    print("🍽️ Astra is at Dinner Time... ready to discuss her day.")

    discussion_topics = schedule_config["dinner_discussion_topics"]  # ✅ Load from config

    print("📌 Parent Note: This will eventually be interactive via Discord/SMS.")
    for topic in discussion_topics:
        print(f"🤖 Astra asks: {topic}")

    # Simulate discussion
    time.sleep(schedule_config["dinner_duration"])  # ✅ Load duration from config
    print("🍽️ Dinner Time is over. Astra returns to school.")
