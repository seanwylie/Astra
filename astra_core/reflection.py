import random
from astra_interfaces.influence import load_mind, save_mind
from astra_core.config_loader import load_config
from astra_core.mood.mood_manager import mood_manager

def generate_reflection(knowledge=None, recent_reflections=None):
    """Generate a reflection dynamically using config-driven templates and mood-based modifiers."""
    
    mind_data = load_mind()
    
    # Use stored knowledge if none is passed
    knowledge = knowledge or mind_data.get("stored_knowledge", [])
    if not knowledge:
        return "Astra is still learning and has no stored knowledge yet."

    recent_reflections = recent_reflections or mind_data.get("self_reflections", [])
    
    # ✅ Load configs
    general_config = load_config("general_config")
    mood_config = load_config("mood_config")

    # ✅ Retrieve Astra's mood and determine reflection style
    mood = mood_manager.current_mood
    reflection_style = mood_config["moods"].get(mood, {}).get("reflection_style", "balanced")

    # ✅ Fetch reflection templates based on mood
    reflection_templates = general_config["reflection_templates"]
    if isinstance(reflection_templates, dict):
        reflection_templates = reflection_templates.get(reflection_style, reflection_templates.get("balanced", []))
    deeper_thought_templates = general_config["deeper_thought_templates"]

    # ✅ Select a mood-driven reflection template
    selected_template = random.choice(reflection_templates)

    # ✅ Filter out dictionary-style entries and non-meaningful knowledge
    filtered_knowledge = [
        entry for entry in knowledge 
        if not entry.startswith("📖") and not entry.startswith("🔹") and ":" not in entry[:20]
    ]
    
    # ✅ Prioritize meaningful insights instead of dictionary definitions
    base_idea = max(filtered_knowledge, key=len) if filtered_knowledge else "I need more insights to reflect on."

    # ✅ Apply reflection template
    new_reflection = selected_template.format(base_idea)

    # ✅ Ensure clean formatting (strip JSON-like structures)
    if isinstance(new_reflection, (dict, list)):
        new_reflection = str(new_reflection)  # Convert structured data into a clean string

    # ✅ Apply deeper thought expansion (Prevent duplicates)
    deeper_thought_options = [t for t in deeper_thought_templates if t not in new_reflection]
    deeper_thought = random.choice(deeper_thought_options) if deeper_thought_options else ""

    # ✅ Ensure reflection isn't overly long
    new_reflection = new_reflection[:500] + "..." if len(new_reflection) > 500 else new_reflection

    if deeper_thought:
        new_reflection += f"\n\n🔍 {deeper_thought}"

    # ✅ Ensure reflection is stored before returning
    if new_reflection not in mind_data["self_reflections"]:
        mind_data["self_reflections"].append(new_reflection)
        print(f"📝 [DEBUG] Added new reflection: {new_reflection[:100]}...")

        # ✅ Save immediately after adding the reflection
        save_mind(mind_data)

    return new_reflection
