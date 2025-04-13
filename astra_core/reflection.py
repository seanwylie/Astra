import random
from astra_interfaces.influence import load_mind, save_mind
from astra_core.config_loader import load_config
from fuzzywuzzy import fuzz
from astra_core.config_loader import debug_log
from astra_core.dinner.dinner_journal import log_if_ethically_conflicting

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

    reflection_style = general_config["reflection_templates"]
    deeper_thought_templates = general_config["deeper_thought_templates"]

    # ✅ Select less-used knowledge
    base_idea = random.choice(knowledge)

    # ✅ Select a reflection template
    selected_template = random.choice(reflection_style)
    new_reflection = selected_template.format(base_idea)

    # ✅ Detect reflection loops
    for past_reflection in recent_reflections[-MAX_REFLECTION_HISTORY:]:
        similarity = fuzz.ratio(new_reflection, past_reflection)
        print(f"🔍 Debug: Comparing reflection similarity -> {similarity}%")

        if similarity >= SIMILARITY_THRESHOLD:
            print(f"🚨 Reflection loop detected! Similarity: {similarity}%. Forcing novelty.")
            new_reflection = enforce_novelty(new_reflection, recent_reflections)
            break

    # ✅ Remove existing "Deeper Thought" before adding a new one
    new_reflection = clean_deeper_thoughts(new_reflection)
    deeper_thought = random.choice(deeper_thought_templates)

    if deeper_thought not in new_reflection:
        new_reflection += f"\n\n🔍 {deeper_thought}"

    # ✅ Save key insights in `stored_knowledge`
    if base_idea not in mind_data["stored_knowledge"]:
        mind_data["stored_knowledge"].append(base_idea)
        print(f"📝 [DEBUG] Stored new knowledge: {base_idea[:100]}...")

    save_mind(mind_data)

    # See if the reflection violates her spark
    log_if_ethically_conflicting(new_reflection)

    return new_reflection

def enforce_novelty(reflection, past_reflections):
    """Modify a reflection to introduce novelty if it is too similar to past ones."""
    return f"💡 A fresh take: {reflection}"

def clean_deeper_thoughts(reflection):
    """Ensure only one unique 'Deeper Thought' section per reflection."""
    return "\n\n".join(line for line in reflection.split("\n\n") if not line.startswith("🔍 Deeper Thought:"))

if __name__ == "__main__":
    print(generate_reflection())
