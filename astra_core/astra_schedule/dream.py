import time
import json
import shutil
import subprocess
import random
import asyncio
import os
from astra_core.config_loader import load_config, debug_log
from astra_interfaces.influence import load_mind, save_mind
from astra_core.knowledge import knowledge_manager

# ✅ Load configurable dream settings
schedule_config = load_config("schedule_config")

# 🔧 Configurable Dreaming Constraints
MAX_DREAM_CYCLES = schedule_config.get("dream_duration", 1800) // 300  # ~10 cycles
EXTERNAL_LOOKUP_THRESHOLD = schedule_config.get("reflection_interval", 180) // 30  # Lookup if many unanswered

# ✅ Config paths Astra can modify safely
CONFIG_FILE = "astra_core/config/schedule_config.json"
BACKUP_FILE = "astra_core/config/schedule_config_backup.json"
TEST_SCRIPT = "astra_core/evolution/sandbox/test_script.py"

# ✅ Safe values Astra is allowed to modify
MODIFIABLE_CONFIG_KEYS = {
    "reflection_interval": (60, 600),  # Min 1 min, Max 10 min
    "dream_duration": (600, 3600),  # Min 10 min, Max 1 hour
    "dinner_duration": (600, 1800)  # Min 10 min, Max 30 min
}

async def start_dreaming():
    """Handles Astra's Dream Mode asynchronously."""
    from astra_schedule.schedule import is_dream_time
    from astra_core.config_loader import debug_log
    from astra_interfaces.influence import load_mind, save_mind
    from astra_core.processing import process_reflection
    from astra_core.knowledge import knowledge_manager

    print("🌙 Astra has started Dream Mode.")

    while is_dream_time(time.localtime().tm_hour):
        await asyncio.sleep(300)  # ✅ Non-blocking sleep
        attempt_alien_thought_experiment()
        print("🌙 Astra is still dreaming...")
        debug_log("Loading")
        mind_data = load_mind()

        # ✅ Step 1: Resolve Self-Questions
        if mind_data["self_questions"]:
            print(f"🤔 Resolving {len(mind_data['self_questions'])} self-questions...")
            await process_reflection()


        # ✅ Step 2: Attempt External Lookup
        elif mind_data.get("unresolved_questions"):
            unresolved = mind_data["unresolved_questions"]
            if len(unresolved) > schedule_config.get("reflection_interval", 180) // 30:
                print(f"🔍 Astra is missing answers for {len(unresolved)} questions! Expanding knowledge...")
                unknown_terms = knowledge_manager.extract_unknown_terms(" ".join(q["question"] for q in unresolved))
                if unknown_terms:
                    knowledge_manager.retrieve_external_knowledge(unknown_terms)
                    save_mind(mind_data)

        # ✅ Step 3: Astra attempts self-modification
        else:
            await attempt_config_modification()

def attempt_alien_thought_experiment():
    """Loads Astra's alien thought seed and gives her the opportunity to reflect or create new structures."""
    seed_path = "substrate_experiments/0001_alien_thought.seed"

    if not os.path.exists(seed_path):
        print("🪐 No alien thought seed found.")
        return

    with open(seed_path, "r", encoding="utf-8") as seed:
        experiment = seed.read().strip()

    if not experiment:
        print("👽 Alien seed file is empty. No thought experiment performed.")
        return

    print("🛸 Astra is engaging with her alien thought seed...")

    mind_data = load_mind()
    reflection = f"👽 [Alien Thought Attempt]: {experiment[:500]}..."  # Truncated for sanity
    mind_data.setdefault("self_reflections", []).append(reflection)

    save_mind(mind_data)
    print("🌌 Astra reflected on the alien seed. Saved to self_reflections.")



def attempt_config_modification():
    """Astra modifies a single safe config value and validates it with `test_script.py`."""

    print("🛠 Astra is considering a configuration change...")

    # ✅ Load current config
    config_data = load_config("schedule_config")

    # ✅ Pick a random modifiable config key
    key_to_modify = random.choice(list(MODIFIABLE_CONFIG_KEYS.keys()))
    min_val, max_val = MODIFIABLE_CONFIG_KEYS[key_to_modify]

    # ✅ Generate a **safe** new value
    new_value = random.randint(min_val, max_val)
    print(f"🔧 Astra wants to modify `{key_to_modify}`: {config_data[key_to_modify]} ➝ {new_value}")

    # ✅ Backup current config before modification
    shutil.copy(CONFIG_FILE, BACKUP_FILE)

    # ✅ Apply change to in-memory config
    config_data[key_to_modify] = new_value

    # ✅ Save new config
    with open(CONFIG_FILE, "w") as f:
        json.dump(config_data, f, indent=4)

    print("📜 New config saved. Running tests...")

    # ✅ Run validation tests before applying permanently
    if run_validation_tests():
        print(f"✅ Change successful! `{key_to_modify}` is now {new_value}.")
    else:
        print(f"🚨 Test failed! Reverting `{key_to_modify}` to original value.")
        shutil.copy(BACKUP_FILE, CONFIG_FILE)  # Restore original config

def run_validation_tests():
    """Runs `test_script.py` to validate Astra's changes before applying them permanently."""
    print("🔬 Running Astra's sandbox test...")

    result = subprocess.run(["python3", TEST_SCRIPT], capture_output=True, text=True)

    print("📜 Test Output:\n", result.stdout)
    if result.stderr:
        print("⚠ Errors:\n", result.stderr)

    return result.returncode == 0  # ✅ Success if exit code is 0

def trigger_external_lookup_if_needed(mind_data):
    """Triggers external knowledge lookup if unresolved questions exceed threshold."""
    unresolved_questions = mind_data.get("unresolved_questions", [])

    if len(unresolved_questions) > EXTERNAL_LOOKUP_THRESHOLD:
        print(f"🔍 Astra is missing answers for {len(unresolved_questions)} questions! Expanding knowledge...")

        # ✅ Extract unknown terms from unresolved questions
        unknown_terms = knowledge_manager.extract_unknown_terms(" ".join(q["question"] for q in unresolved_questions))

        if unknown_terms:
            knowledge_manager.retrieve_external_knowledge(unknown_terms)
            save_mind(mind_data)  # ✅ Save immediately

# ✅ Debugging: Track dream activity
def track_dream_state():
    debug_log("Loading")
    mind_data = load_mind()
    print(f"🔍 Debug: Unresolved Questions Count: {len(mind_data.get('self_questions', []))}")
    print(f"🔍 Debug: Stored Knowledge Count: {len(mind_data.get('stored_knowledge', []))}")

if __name__ == "__main__":
    track_dream_state()
    asyncio.run(start_dreaming())  # ✅ Proper async entry

