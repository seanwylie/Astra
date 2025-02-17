import time
import random
from astra_core.processing import process_reflection

def start_learning():
    """Astra’s Active Learning (every 5-10 minutes)."""
    print("📚 Astra is in school, learning and thinking...")
    process_reflection()
    time.sleep(random.randint(300, 600))
