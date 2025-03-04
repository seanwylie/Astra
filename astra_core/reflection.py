import random
import numpy as np
from astra_interfaces.influence import load_mind, save_mind
from astra_core.config_loader import load_config
from astra_core.mood.mood_manager import mood_manager
from fuzzywuzzy import fuzz
from astra_core.config_loader import debug_log

# Load configurations
question_config = load_config("question_config")
general_config = load_config("general_config")

# Constants for self-healing
MAX_REFLECTION_HISTORY = 20  # Number of past reflections to compare for loops
SIMILARITY_THRESHOLD = 85  # Percentage similarity to detect reflection loops
KNOWLEDGE_WEIGHT_LIMIT = 3  # How many times knowledge can appear before deprioritization

def generate_reflection(knowledge=None, recent_reflections=None, *args, **kwargs):
    """Generate a reflection dynamically while preventing loops and enforcing novelty."""

    # ✅ Load mind data if not provided explicitly
    debug_log("Loading")  
    mind_data = load_mind()
    knowledge = knowledge or mind_data.get("stored_knowledge", [])
    recent_reflections = recent_reflections or mind_data.get("self_reflections", [])

    if not knowledge:
        return "Astra is still learning and has no stored knowledge yet."

    mood = mood_manager.current_mood
    reflection_style = general_config["reflection_templates"]
    deeper_thought_templates = general_config["deeper_thought_templates"]

    # ✅ Track knowledge usage
    knowledge_usage = mind_data.setdefault("knowledge_usage", {})
    for entry in knowledge:
        knowledge_usage[entry] = knowledge_usage.get(entry, 0) + 1

    # ✅ Filter knowledge that is overused
    filtered_knowledge = [
        entry for entry in knowledge 
        if knowledge_usage.get(entry, 0) < KNOWLEDGE_WEIGHT_LIMIT
    ]

    if not filtered_knowledge:
        filtered_knowledge = knowledge  # Fall back to full knowledge set if all are overused

    # ✅ Select less-used knowledge
    base_idea = random.choice(filtered_knowledge)

    # ✅ Select a reflection template
    selected_template = random.choice(reflection_style)
    new_reflection = selected_template.format(base_idea)

    # ✅ Detect reflection loops
    for past_reflection in recent_reflections[-MAX_REFLECTION_HISTORY:]:
        similarity = fuzz.ratio(new_reflection, past_reflection)
        if similarity >= SIMILARITY_THRESHOLD:
            print(f"🚨 Reflection loop detected! Similarity: {similarity}%. Forcing novelty.")
            new_reflection = enforce_novelty(new_reflection, recent_reflections)
            break

    # ✅ Apply deeper thought expansion
    deeper_thought = random.choice(deeper_thought_templates)
    new_reflection += f"\n\n🔍 {deeper_thought}"

    # ✅ Save reflection and update memory
    mind_data["self_reflections"].append(new_reflection)
    save_mind(mind_data)
    print(f"📝 [DEBUG] Added new reflection: {new_reflection[:100]}...")

    return new_reflection

def enforce_novelty(reflection, past_reflections):
    """Modify a reflection to introduce novelty if it is too similar to past ones."""
    modifiers = general_config["reflection_style_modifiers"].values()
    for _ in range(3):  # Try a few times to ensure uniqueness
        new_reflection = f"{reflection} {random.choice(modifiers)}"
        if all(fuzz.ratio(new_reflection, past) < SIMILARITY_THRESHOLD for past in past_reflections):
            return new_reflection
    return new_reflection  # If no novelty can be enforced, return original

# ✅ Debugging: Track mind data changes
def track_mind_data():
    debug_log("Loading")  
    mind_data = load_mind()
    print(f"🔍 Debug: Stored Knowledge Count: {len(mind_data['stored_knowledge'])}")
    print(f"🔍 Debug: Reflection History Count: {len(mind_data['self_reflections'])}")
    print(f"🔍 Debug: Most Used Knowledge: {sorted(mind_data['knowledge_usage'].items(), key=lambda x: x[1], reverse=True)[:5]}")

if __name__ == "__main__":
    track_mind_data()
    print(generate_reflection())
