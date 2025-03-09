import random
import os
import sys
import asyncio
import time
import openai
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

# ✅ Load configuration
general_config = load_config("general_config")
schedule_config = load_config("schedule_config")

# ✅ Ensure Mind Structure
def validate_mind_structure(mind_data):
    """Ensure `mind_data` has the correct structure."""
    mind_data.setdefault("self_reflections", [])
    mind_data.setdefault("self_questions", [])
    mind_data.setdefault("stored_knowledge", [])

async def process_reflection():
    """Generate, refine, and deepen Astra's reflections while ensuring memory consistency."""
    debug_log("Loading")  
    mind_data = load_mind()
    validate_mind_structure(mind_data)

    if not mind_data["self_reflections"]:
        return "🤔 I have no reflections yet!"

    # ✅ Select the most recent reflection for deeper reasoning
    previous_reflection = mind_data["self_reflections"][-1]

    # 🔥 NEW: If a reflection is too recent, avoid looping on the same thoughts
    if len(mind_data["self_reflections"]) > 2:
        last_two = mind_data["self_reflections"][-2:]
        similarity = fuzz.ratio(last_two[0], last_two[1])
        if similarity > 85:  # 🔥 Avoid repeating the same thought too much
            print(f"⚠ Recent reflections are too similar ({similarity}%). Expanding knowledge instead.")
            refined_knowledge = refine_knowledge(mind_data["stored_knowledge"], mind_data)
            if refined_knowledge:
                return refined_knowledge
            return last_two[1]  # Fallback to the latest valid thought

    # ✅ Ask OpenAI to deepen Astra’s reflections
    refined_reflection = query_openai_for_deeper_thought(previous_reflection)

    if refined_reflection:
        mind_data["self_reflections"].append(refined_reflection)
        save_mind(mind_data)
        return refined_reflection
    else:
        print("⚠ OpenAI failed to refine the thought. Using previous reflection.")
        return previous_reflection

def query_openai_for_deeper_thought(reflection):
    """Ask OpenAI to refine Astra’s reflections while considering past thoughts."""
    prompt = f"""
    Astra is an AI that evolves her thoughts over time. She builds on past reflections instead of repeating them.

    Last Reflection:
    "{reflection}"

    Expand on this idea. Provide deeper insight, connect it to knowledge Astra has, or introduce a new perspective.
    """

    try:
        response = openai.OpenAI().chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=200,
            temperature=0.7
        )

        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"🚨 OpenAI request failed: {e}")
    return None

def expand_reflection(reflection):
    """Deepens thoughts by adding new layers of complexity."""
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


    from astra_core.config_loader import load_config

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
