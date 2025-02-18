import random
from astra_interfaces.influence import load_mind, save_mind
from astra_core.config_loader import load_config  # ✅ Load reflection templates dynamically


def generate_reflection(knowledge, recent_reflections):
    """Generate a reflection dynamically, allowing Astra to evolve her phrasing."""
    
    mind_data = load_mind()
    
    if not knowledge:
        return "Astra is still learning and has no stored knowledge yet."

    # Retrieve or initialize reflection templates
    if "reflection_templates" not in mind_data:
    
        # ✅ Load reflection templates from general_config.json
        general_config = load_config("general_config")
        reflection_templates = general_config.get("reflection_templates", [])

        # ✅ Debugging: Ensure templates are loading correctly
        if not reflection_templates:
            print("🚨 Warning: No reflection templates found in general_config.json!")

        print(f"🔍 Debug: Reflection Templates Loaded: {reflection_templates}")


        save_mind(mind_data)  # Save default templates initially


    # Prioritize deeper insights by weighting longer knowledge entries higher
    prioritized_knowledge = sorted(knowledge, key=lambda x: len(x), reverse=True)
    base_idea = random.choice(prioritized_knowledge[:max(1, len(prioritized_knowledge) // 3)])

    # ✅ Pick one reflection template to ensure no multiple applications
    selected_template = random.choice(reflection_templates)

    # ✅ Strip old template patterns from base_idea before applying a new one
    for template in reflection_templates:
        if "{}" in template:
            base_idea = base_idea.replace(template.format(""), "").strip()

    # ✅ Apply only ONE template
    new_reflection = selected_template.format(base_idea)
    print(f"Selected Template: {selected_template}")
    print(f"Base Idea After Cleanup: {base_idea}")
    print(f"Final Reflection: {new_reflection}")


    # Ensure reflection isn't overly long
    if len(new_reflection) > 500:
        new_reflection = new_reflection[:497] + "..."

    # Ensure it doesn’t match the last two reflections
    if any(new_reflection in past for past in recent_reflections):
        return generate_reflection(knowledge, recent_reflections)  # Retry with a different idea

    return new_reflection


