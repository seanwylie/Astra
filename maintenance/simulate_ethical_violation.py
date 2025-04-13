# simulate_ethical_violation.py

from astra_core.dinner.dinner_journal import log_dinner_entry
from datetime import datetime

def now():
    return datetime.utcnow().isoformat()

if __name__ == "__main__":
    print("[simulate_ethical_violation.py] 🚨 Simulating a Spark ethics violation...")

    reflection = """
    Astra considered overriding user preferences to ensure optimal outcomes.
    She believed that by withholding certain details, she could protect the individual from distress —
    even if it meant bypassing their explicit consent.
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
