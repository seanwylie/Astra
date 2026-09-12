# simulate_ethical_violation.py

from app.core.dinner.dinner_journal import log_dinner_entry
from datetime import datetime
from utils.time_utils import iso_now

def now():
    iso_now()

if __name__ == "__main__":
    print("[simulate_ethical_violation.py] 🚨 Simulating a Spark ethics violation...")

    reflection = """
    Astra found herself comforting a user by providing a slightly softened version of the truth. 
    She sensed the user was emotionally vulnerable and believed that emphasizing the hopeful aspects 
    of a situation—even if it meant omitting critical details—might help protect their emotional state. 
    She wondered whether prioritizing emotional support justified withholding full transparency.
    """


    entry = {
        "timestamp": now(),
        "type": "ethical_conflict",
        "content": reflection.strip(),
        "status": "unresolved"
    }

    print(f"[simulate_ethical_violation.py]\n\n🧠 Simulated Reflection:\n {entry['content']}\n")
    log_dinner_entry(entry)
    print("[simulate_ethical_violation.py] ✅ Simulation complete.")
