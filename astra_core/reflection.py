import random
from astra_interfaces.influence import load_mind
from astra_core.config_loader import load_config
from astra_core.mood.mood_manager import mood_manager

def generate_reflection(knowledge, recent_reflections):
    """Generate a reflection dynamically using config-driven templates and mood-based modifiers."""

    if not knowledge:
        return "Astra is still learning and has no stored knowledge yet."

    mind_data = load_mind()
    
    # ✅ Load configs
    general_config = load_config("general_config")
    mood_config = load_config("mood_config")

    # ✅ Retrieve Astra's mood and determine reflection style
    mood = mood_manager.current_mood
    reflection_style = mood_config["moods"].get(mood, {}).get("reflection_style", "balanced")

    # ✅ Fetch reflection templates
    reflection_templates = general_config["reflection_templates"]
    expansion_templates = general_config["expansion_templates"]
    deeper_thought_templates = general_config["deeper_thought_templates"]

    # ✅ Select a mood-driven reflection template
    selected_template = random.choice(reflection_templates)

    # ✅ Prioritize deeper insights by weighting longer knowledge entries higher
    prioritized_knowledge = sorted(knowledge, key=len, reverse=True)
    base_idea = random.choice(prioritized_knowledge[: max(1, len(prioritized_knowledge) // 3)])

    # ✅ Apply reflection template
    new_reflection = selected_template.format(base_idea)

    # ✅ Apply deeper thought expansion
    # ✅ Prevent duplicate deeper thoughts
    deeper_thought = random.choice([t for t in deeper_thought_templates if t not in new_reflection])

    new_reflection = f"{new_reflection}\n\n🔍 {deeper_thought}"

    # ✅ Ensure reflection isn't overly long
    if len(new_reflection) > 500:
        new_reflection = new_reflection[:497] + "..."

    # ✅ Ensure the new reflection is unique
    if any(new_reflection in past for past in recent_reflections):
        return generate_reflection(knowledge, recent_reflections)  # Retry with a different idea

    return new_reflection
