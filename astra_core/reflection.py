import random

def generate_reflection(knowledge, recent_reflections):
    """Generate a reflection while keeping it clear, concise, and novel."""

    if not knowledge:
        return "Astra is still learning, but she has no stored knowledge yet."

    base_idea = random.choice(knowledge)

    reflection_templates = [
        "Exploring a new perspective, I consider that {}",
        "A challenging idea emerges: {}",
        "By looking deeper, I see that {}",
        "A thought-provoking realization: {}"
    ]

    # ✅ Ensure reflection is unique
    for _ in range(5):  # Try multiple times for a unique reflection
        new_reflection = random.choice(reflection_templates).format(base_idea)

        # ✅ Prevent reflections from repeating too often
        if new_reflection not in recent_reflections:
            break

    # ✅ Ensure reflection isn't overly long
    if len(new_reflection) > 500:
        new_reflection = new_reflection[:497] + "..."

    return new_reflection

