import random
from astra_interfaces.influence import load_mind
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

    # ✅ Prioritize deeper insights by weighting longer knowledge entries higher
    base_idea = max(knowledge, key=len)

    # ✅ Apply reflection template
    new_reflection = selected_template.format(base_idea)

    # ✅ Apply deeper thought expansion (Prevent duplicates)
    deeper_thought_options = [t for t in deeper_thought_templates if t not in new_reflection]
    deeper_thought = random.choice(deeper_thought_options) if deeper_thought_options else ""
    
    # ✅ Ensure reflection isn't overly long
    new_reflection = new_reflection[:500] + "..." if len(new_reflection) > 500 else new_reflection
    
    # ✅ Ensure clean question formatting (no raw JSON dumps)
    if deeper_thought:
        new_reflection += f"\n\n🔍 {deeper_thought}"
    
    # ✅ Ensure unique reflection and format final output properly
    if new_reflection in recent_reflections:
        return generate_reflection(knowledge, recent_reflections)  # Retry with a different idea
    
    # ✅ Properly extract and clean up reflection output
    if "{'question':" in new_reflection:
        new_reflection = new_reflection.split("{'question':", 1)[0].strip()
    
    return new_reflection
