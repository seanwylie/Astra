import random

def generate_reflection(stored_knowledge, past_reflections):
    """Generate a structured self-reflection that avoids excessive self-referencing."""
    print("🔍 Debug: Generating a new reflection...")

    if not stored_knowledge:
        return "I need more knowledge to reflect on."

    # ✅ Sample a subset of knowledge
    sampled_knowledge = random.sample(stored_knowledge, min(5, len(stored_knowledge)))

    # ✅ Choose a primary thought
    thought = random.choice(sampled_knowledge)

    # ✅ Find a related past reflection *only if it's unique*
    related_reflections = [r for r in past_reflections if thought[:50] not in r and len(r) < 500]
    related_reflection = random.choice(related_reflections) if related_reflections else "a previous thought I had"

    # ✅ Ensure function always returns a string, never a list
    reflection = f"Considering {thought}, and reflecting on {related_reflection}"
    
    print(f"✅ Generated reflection: {reflection[:100]}...")
    print(f"🔍 Debug: Type of `reflection`: {type(reflection)}")  # ✅ Ensure it's a string

    return str(reflection)  # ✅ Explicitly return a string
