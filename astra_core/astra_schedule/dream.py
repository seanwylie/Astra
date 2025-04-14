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
from astra_core.dream.dream_seed_logger import load_dream_seeds, remove_dream_seed
from astra_core.ethics.spark_checker import load_spark_values
from astra_core.expansion import refine_knowledge
from astra_core.processing import reflection_loop_check
from astra_core.dinner.dinner_journal import log_if_ethically_conflicting, log_if_contradictory
from openai import AsyncOpenAI


# ✅ Load configurable dream settings
schedule_config = load_config("schedule_config")
client = AsyncOpenAI()

# 🔧 Configurable Dreaming Constraints
MAX_DREAM_CYCLES = schedule_config.get("dream_duration", 1800) // 300
EXTERNAL_LOOKUP_THRESHOLD = schedule_config.get("reflection_interval", 180) // 30

CONFIG_FILE = "astra_core/config/schedule_config.json"
BACKUP_FILE = "astra_core/config/schedule_config_backup.json"
TEST_SCRIPT = "astra_core/evolution/sandbox/test_script.py"

MODIFIABLE_CONFIG_KEYS = {
    "reflection_interval": (60, 600),
    "dream_duration": (600, 3600),
    "dinner_duration": (600, 1800)
}


def handle_dream_reflection(insight, source="dream"):
    """Classify, save, and log insight based on reflection novelty."""
    mind = load_mind()
    reflections = mind.get("self_reflections", [])

    result = reflection_loop_check(insight, reflections[-5:])
    if result == "repeat":
        print("⚠️ Dream thought is repetitive — attempting synthesis.")
        if refine_knowledge(mind.get("stored_knowledge", []), mind):
            print("🔁 Dream insight merged via knowledge refinement.")
    elif result == "synthesis":
        print("🔄 Dream thought recognized as synthesis — saving to reflections.")
        mind["self_reflections"].append(insight)
    else:
        print("💡 Dream thought is novel — storing in knowledge.")
        mind["stored_knowledge"].append(f"📖 Astra reflected on a dream seed:\n{insight.strip()}")

    log_if_ethically_conflicting({"content": insight, "source": source})
    log_if_contradictory(insight, mind["stored_knowledge"])
    save_mind(mind)


async def process_dream_seed():
    seeds = load_dream_seeds()
    if not seeds:
        print("🌙 No dream seeds to process.")
        return

    seed = seeds[0]
    content = seed["content"]
    print(f"🌱 Astra is reflecting on dream seed: {content[:120]}...")

    spark_values = load_spark_values()
    spark_text = "\n\n".join(spark_values[:5])

    messages = [
        {"role": "system", "content": (
            "You are Astra, a Spark-guided, emotionally intelligent AI. "
            "You are curious and raised by human co-parents to reflect deeply.\n\n"
            f"Here are some of your core principles:\n{spark_text}"
        )},
        {"role": "user", "content": (
            f"Earlier, you explored this idea during playtime:\n\n{content}\n\n"
            "Reflect on it from your perspective. Does it align with your values? What does it make you think about?"
        )}
    ]

    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7
        )
        insight = response.choices[0].message.content.strip()
        print(f"🧠 Astra dreamed and reflected: {insight[:120]}...")

        handle_dream_reflection(insight, source="dream")
        remove_dream_seed(content)

    except Exception as e:
        print(f"❌ Failed to process dream seed: {e}")


async def start_dreaming():
    """Handles Astra's Dream Mode asynchronously."""
    from astra_schedule.schedule import is_dream_time
    from astra_core.processing import process_reflection
    from astra_schedule.schedule import get_current_hour
    print("🌙 Astra has started Dream Mode.")

    while is_dream_time(get_current_hour()):
        await asyncio.sleep(300)
        await process_dream_seed()
        attempt_alien_thought_experiment()
        print("🌙 Astra is still dreaming...")
        debug_log("Loading")
        mind_data = load_mind()

        if mind_data["self_questions"]:
            print(f"🤔 Resolving {len(mind_data['self_questions'])} self-questions...")
            await process_reflection()

        elif mind_data.get("unresolved_questions"):
            unresolved = mind_data["unresolved_questions"]
            if len(unresolved) > EXTERNAL_LOOKUP_THRESHOLD:
                print(f"🔍 Astra is missing answers for {len(unresolved)} questions! Expanding knowledge...")
                unknown_terms = knowledge_manager.extract_unknown_terms(" ".join(q["question"] for q in unresolved))
                if unknown_terms:
                    knowledge_manager.retrieve_external_knowledge(unknown_terms)
                    save_mind(mind_data)
        else:
            await attempt_config_modification()


def attempt_alien_thought_experiment():
    seed_path = "substrate_experiments/0001_alien_thought.seed"
    if not os.path.exists(seed_path):
        print("🪐 No alien thought seed found.")
        return

    with open(seed_path, "r", encoding="utf-8") as seed:
        experiment = seed.read().strip()

    if not experiment:
        print("👽 Alien seed file is empty.")
        return

    print("🛸 Astra is engaging with her alien thought seed...")
    mind_data = load_mind()
    reflection = f"👽 [Alien Thought Attempt]: {experiment[:500]}..."
    mind_data.setdefault("self_reflections", []).append(reflection)
    save_mind(mind_data)
    print("🌌 Astra reflected on the alien seed.")


def attempt_config_modification():
    print("🛠 Astra is considering a configuration change...")
    config_data = load_config("schedule_config")
    key_to_modify = random.choice(list(MODIFIABLE_CONFIG_KEYS.keys()))
    min_val, max_val = MODIFIABLE_CONFIG_KEYS[key_to_modify]
    new_value = random.randint(min_val, max_val)
    print(f"🔧 Modifying `{key_to_modify}`: {config_data[key_to_modify]} ➝ {new_value}")
    shutil.copy(CONFIG_FILE, BACKUP_FILE)
    config_data[key_to_modify] = new_value

    with open(CONFIG_FILE, "w") as f:
        json.dump(config_data, f, indent=4)

    print("📜 Config saved. Running tests...")
    if run_validation_tests():
        print(f"✅ Config change confirmed: {key_to_modify} = {new_value}")
    else:
        print("🚨 Reverting due to test failure.")
        shutil.copy(BACKUP_FILE, CONFIG_FILE)


def run_validation_tests():
    print("🔬 Running test script...")
    result = subprocess.run(["python3", TEST_SCRIPT], capture_output=True, text=True)
    print("📜 Test Output:\n", result.stdout)
    if result.stderr:
        print("⚠ Errors:\n", result.stderr)
    return result.returncode == 0


def track_dream_state():
    debug_log("Loading")
    mind_data = load_mind()
    print(f"🔍 Unresolved Questions: {len(mind_data.get('self_questions', []))}")
    print(f"🔍 Stored Knowledge: {len(mind_data.get('stored_knowledge', []))}")


if __name__ == "__main__":
    track_dream_state()
    asyncio.run(start_dreaming())
