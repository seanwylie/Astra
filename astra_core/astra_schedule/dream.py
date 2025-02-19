import time
from astra_core.config_loader import load_config
from astra_core.processing import process_reflection

schedule_config = load_config("schedule_config")  # ✅ Load schedule settings

def start_dreaming():
    """Handles Astra's Dream Mode and transitions out when dream time ends."""
    from astra_schedule.schedule import is_dream_time, get_current_mode

    print("🌙 Astra has started Dream Mode.")
    
    while is_dream_time(time.localtime().tm_hour):
        time.sleep(300)  # Check every 5 minutes
        print("🌙 Astra is still dreaming...")

    print("🌅 Dream time is over. Transitioning to new mode.")

