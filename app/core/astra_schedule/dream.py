import time
import json
import shutil
import subprocess
import random
import asyncio
import os
from app.config.loader import load_config, debug_log, CONFIG_DIR
from app.core.knowledge import knowledge_manager
from app.core.dream.dream_seed_logger import load_dream_seeds, remove_dream_seed
from app.core.ethics.spark_checker import load_spark_values
from app.core.expansion import refine_knowledge
from app.core.processing import reflection_loop_check
from app.core.dinner.dinner_journal import log_if_ethically_conflicting, log_if_contradictory
from openai import AsyncOpenAI
from app.interfaces.mind_session import session
from app.logging_config import get_logger

logger = get_logger("dream")



# ✅ Load configurable dream settings
schedule_config = load_config("schedule_config")
client = AsyncOpenAI()

# 🔧 Configurable Dreaming Constraints
MAX_DREAM_CYCLES = schedule_config.get("dream_duration", 1800) // 300
EXTERNAL_LOOKUP_THRESHOLD = schedule_config.get("reflection_interval", 180) // 30

CONFIG_FILE = str(CONFIG_DIR / "schedule_config.json")
BACKUP_FILE = str(CONFIG_DIR / "schedule_config_backup.json")
TEST_SCRIPT = str(CONFIG_DIR.parent / "app" / "core" / "evolution" / "sandbox" / "test_script.py")

MODIFIABLE_CONFIG_KEYS = {
    "reflection_interval": (60, 600),
    "dream_duration": (600, 3600),
    "dinner_duration": (600, 1800)
}


def handle_dream_reflection(insight, source="dream"):
    """Classify, save, and log insight based on reflection novelty."""
    mind = session.load()
    reflections = mind.get("self_reflections", [])

    result = reflection_loop_check(insight, reflections[-5:])
    if result == "repeat":
        logger.warning("Dream thought is repetitive — attempting synthesis.")
        if refine_knowledge(mind.get("stored_knowledge", []), mind):
            logger.info("Dream insight merged via knowledge refinement.")
    elif result == "synthesis":
        logger.info("Dream thought recognized as synthesis — saving to reflections.")
        mind["self_reflections"].append(insight)
    else:
        logger.info("Dream thought is novel — storing in knowledge.")
        mind["stored_knowledge"].append(f"📖 Astra reflected on a dream seed:\n{insight.strip()}")

    log_if_ethically_conflicting({"content": insight, "source": source})
    log_if_contradictory(insight, mind["stored_knowledge"])
    session.maybe_save()
    try:
        from app.core.astra_helpers.utils_helper import proactive_lookup_from_text
        proactive_lookup_from_text(insight, mind, max_lookups=1)
    except Exception as e:
        logger.debug("Proactive lookup from dream failed: %s", e)


async def process_dream_seed():
    """Process up to dream_seeds_per_cycle seeds per call. Default 3."""
    seeds = load_dream_seeds()
    if not seeds:
        logger.debug("No dream seeds to process.")
        return

    max_per_cycle = schedule_config.get("dream_seeds_per_cycle", 3)
    to_process = seeds[:max_per_cycle]

    for seed in to_process:
        content = seed["content"]
        logger.info("Reflecting on dream seed: %s...", content[:120])

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
            logger.debug("Dream reflection: %s...", insight[:120])

            handle_dream_reflection(insight, source="dream")
            remove_dream_seed(content)

        except Exception as e:
            logger.exception("Failed to process dream seed: %s", e)


async def start_dreaming():
    """Handles Astra's Dream Mode asynchronously."""
    from app.core.astra_schedule.schedule import is_dream_time, get_current_hour
    from app.core.processing import process_reflection
    from app.interfaces.mind_session import session

    cycle_interval = schedule_config.get("dream_cycle_interval_sec", 300)
    logger.info("Astra has started Dream Mode (cycle_interval=%s sec).", cycle_interval)

    while is_dream_time(get_current_hour()):
        await asyncio.sleep(cycle_interval)
        await process_dream_seed()
        attempt_alien_thought_experiment()
        logger.debug("Still dreaming...")
        debug_log("Loading")
        mind_data = session.load()

        if mind_data["self_questions"]:
            logger.info("Resolving %s self-questions...", len(mind_data["self_questions"]))
            await process_reflection()

        elif mind_data.get("unresolved_questions"):
            unresolved = mind_data["unresolved_questions"]
            if len(unresolved) > EXTERNAL_LOOKUP_THRESHOLD:
                logger.info("Missing answers for %s questions; expanding knowledge.", len(unresolved))
                unknown_terms = knowledge_manager.extract_unknown_terms(" ".join(q["question"] for q in unresolved))
                if unknown_terms:
                    knowledge_manager.retrieve_external_knowledge(unknown_terms)
                    session.maybe_save()
        else:
            attempt_config_modification()


def attempt_alien_thought_experiment():
    seed_path = "substrate_experiments/0001_alien_thought.seed"
    if not os.path.exists(seed_path):
        logger.debug("No alien thought seed found.")
        return

    with open(seed_path, "r", encoding="utf-8") as seed:
        experiment = seed.read().strip()

    if not experiment:
        logger.debug("Alien seed file is empty.")
        return

    logger.info("Engaging with alien thought seed.")
    mind_data = session.load()
    reflection = f"👽 [Alien Thought Attempt]: {experiment[:500]}..."
    mind_data.setdefault("self_reflections", []).append(reflection)
    session.maybe_save()
    logger.debug("Reflected on alien seed.")


def attempt_config_modification():
    """Optionally modify schedule config and validate via test script. Skipped if disabled or script missing."""
    if not schedule_config.get("allow_dream_config_experiments", False):
        return
    if not os.path.isfile(TEST_SCRIPT):
        return
    logger.info("Considering a configuration change...")
    config_data = load_config("schedule_config")
    key_to_modify = random.choice(list(MODIFIABLE_CONFIG_KEYS.keys()))
    min_val, max_val = MODIFIABLE_CONFIG_KEYS[key_to_modify]
    new_value = random.randint(min_val, max_val)
    logger.info("Modifying %s: %s -> %s", key_to_modify, config_data[key_to_modify], new_value)
    shutil.copy(CONFIG_FILE, BACKUP_FILE)
    config_data[key_to_modify] = new_value

    with open(CONFIG_FILE, "w") as f:
        json.dump(config_data, f, indent=4)

    logger.debug("Config saved. Running tests...")
    if run_validation_tests():
        logger.info("Config change confirmed: %s = %s", key_to_modify, new_value)
    else:
        logger.warning("Reverting due to test failure.")
        shutil.copy(BACKUP_FILE, CONFIG_FILE)


def run_validation_tests():
    logger.debug("Running test script: %s", TEST_SCRIPT)
    result = subprocess.run(["python3", TEST_SCRIPT], capture_output=True, text=True)
    if result.stdout:
        logger.debug("Test output: %s", result.stdout.strip())
    if result.stderr:
        logger.warning("Test stderr: %s", result.stderr.strip())
    return result.returncode == 0


def track_dream_state():
    debug_log("Loading")
    mind_data = session.load()
    logger.debug("Unresolved questions: %s; stored knowledge: %s",
                 len(mind_data.get("self_questions", [])), len(mind_data.get("stored_knowledge", [])))


if __name__ == "__main__":
    track_dream_state()
    asyncio.run(start_dreaming())
