import random
import os
import sys
import asyncio
import time
from fuzzywuzzy import fuzz

# ✅ Ensure Python knows where to find Astra’s core modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from astra_core.knowledge import knowledge_manager
from astra_core.reflection import generate_reflection
from astra_core.questions.question_manager import generate_questions
from astra_core.expansion import refine_knowledge
from astra_interfaces.influence import load_mind, save_mind
from astra_core.config_loader import load_config
from astra_core.config_loader import debug_log


general_config = load_config("general_config")


# ✅ Function: Ensure Mind Structure
def validate_mind_structure(mind_data):
    """Ensure `mind_data` has the correct structure."""
    mind_data.setdefault("self_reflections", [])
    mind_data.setdefault("self_questions", [])
    mind_data.setdefault("stored_knowledge", [])


async def process_reflection():
    """Generate, refine, and deepen Astra's reflections while ensuring responsiveness."""
    debug_log("Loading")  
    mind_data = load_mind()
    validate_mind_structure(mind_data)

    # ✅ Limit reflection processing
    recent_reflections = " ".join(mind_data["self_reflections"][-3:]) if mind_data["self_reflections"] else ""
    if len(recent_reflections) > 2500:
        recent_reflections = recent_reflections[:2500]

    # ✅ Extract unknown terms
    unknown_terms = knowledge_manager.extract_unknown_terms(recent_reflections)
    if unknown_terms:
        found_new_knowledge = await asyncio.to_thread(knowledge_manager.retrieve_external_knowledge, unknown_terms)  # ✅ Ensures non-blocking call
        if found_new_knowledge:
            for knowledge in found_new_knowledge:
                if knowledge not in mind_data["stored_knowledge"]:
                    mind_data["stored_knowledge"].append(knowledge)

            await asyncio.to_thread(save_mind, mind_data)  # ✅ Ensure this runs asynchronously

            # ✅ Reload mind
            reloaded_mind_data = load_mind()
            missing_knowledge = set(found_new_knowledge) - set(reloaded_mind_data["stored_knowledge"])
            if missing_knowledge:
                mind_data["stored_knowledge"].extend(missing_knowledge)
                await asyncio.to_thread(save_mind, mind_data)  # ✅ Ensure async

    new_reflection = await asyncio.to_thread(generate_reflection, mind_data["stored_knowledge"], mind_data["self_reflections"])

    # ✅ Ensure return is **always** a string
    if not new_reflection or not isinstance(new_reflection, str) or len(new_reflection.strip()) < 20:
        print("⚠ Skipping reflection - too short!")
        return None

    expanded_reflection = await asyncio.to_thread(expand_reflection, new_reflection)

    if not any(fuzz.ratio(expanded_reflection.lower(), r.lower()) > 95 for r in mind_data["self_reflections"]):
        mind_data["self_reflections"].append(expanded_reflection)

    latest_mind = load_mind()
    if len(mind_data["stored_knowledge"]) > len(latest_mind.get("stored_knowledge", [])):
        await asyncio.to_thread(save_mind, mind_data)
    else:
        print("⚠ Prevented overwriting mind file with less data!")

    print(f"🔍 Debug: process_reflection() final return type: {type(expanded_reflection)}")
    return str(expanded_reflection)  # ✅ Ensure we **always** return a string


def expand_reflection(reflection):
    """Deepens thoughts and ensures unique reflections."""
    expanded_reflection = reflection

    # ✅ Remove existing "Deeper Thought" before adding a new one
    expanded_reflection = "\n\n".join(
        line for line in expanded_reflection.split("\n\n") if not line.startswith("🔍 Deeper Thought:")
    )

    deeper_thought_templates = general_config["deeper_thought_templates"]
    deeper_thought = f"\n\n🔍 Deeper Thought: {random.choice(deeper_thought_templates)}"
    expanded_reflection += deeper_thought

    return expanded_reflection


def filter_knowledge(knowledge_list):
    """Ensure Astra keeps valuable knowledge while avoiding excessive duplicates."""
    filtered_knowledge = []
    seen = set()

    for entry in knowledge_list:
        if len(entry) < 10:
            continue  # ✅ Ignore very short junk entries

        key = entry.lower().strip()

        is_duplicate = False
        for existing in seen:
            similarity = fuzz.ratio(key, existing)

            if similarity >= 99:  # 🔥 Adjusted from 100% → 98% to allow slight variations
                is_duplicate = True
                break

        if not is_duplicate:
            seen.add(key)
            filtered_knowledge.append(entry)

    lost_percentage = (1 - (len(filtered_knowledge) / len(knowledge_list))) * 100

    if lost_percentage > 5:  # 🔥 Adjusted from 3% → 5% tolerance
        print(f"🚨 WARNING: Excessive filtering detected! Restoring original knowledge. Lost: {lost_percentage:.2f}%")
        return knowledge_list  # 🚀 Restore original knowledge if too much was removed

    return filtered_knowledge


# ✅ Debugging Function
def track_mind_data_changes(operation, mind_data):
    """Debugging function to track when `mind_data` changes."""
    if isinstance(mind_data, list):
        print(f"🚨 Error: `mind_data` has turned into a list! Contents: {mind_data}")
    elif isinstance(mind_data, dict):
        print(f"✅ `mind_data` is a dictionary. Keys: {list(mind_data.keys())}")


if __name__ == "__main__":
    print("🧠 Astra is thinking...")

    from astra_core.astra_schedule.schedule import astra_schedule
    from astra_core.config_loader import load_config

    schedule_config = load_config("schedule_config")  # ✅ Load schedule configuration

    def main():
        """Check Astra’s schedule, adjust state, then process reflections."""
        from astra_core.astra_schedule.schedule import astra_schedule, get_current_mode

        astra_schedule()  # ✅ Ensure Astra transitions properly
        current_mode = get_current_mode()  # ✅ Fetch the current mode
        print(f"🕒 Current Mode: {current_mode}")

        asyncio.run(process_reflection())  # ✅ Reflect after state execution


    while True:
        main()
        sleep_time = schedule_config.get("reflection_interval", 600)  # ✅ Default to 10 minutes if missing
        print(f"⏳ Sleeping for {sleep_time} seconds before the next cycle...")
        time.sleep(sleep_time)

