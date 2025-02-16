import random

def refine_knowledge(existing_ideas):
    """Merge and refine knowledge without excessive repetition."""
    if len(existing_ideas) < 2:
        return None  # Not enough data to merge

    # ✅ Pick two *different* concepts to merge
    concept_1, concept_2 = random.sample(existing_ideas, 2)

    # ✅ Avoid merging concepts that are too similar
    if concept_1[:50] in concept_2 or concept_2[:50] in concept_1:
        return None

    new_concept = f"Merging ideas: {concept_1} and {concept_2} leads to a new perspective."
    print(f"🔹 Refined knowledge added: {new_concept[:100]}...")
    return new_concept


def deepen_reflection(reflection):
    """Expands on a reflection by adding depth or new questions."""
    expansion_templates = [
        "If this perspective is correct, what implications does it have for my growth?",
        "What new questions arise from this understanding?",
        "Are there counterpoints that challenge this perspective?"
    ]
    deeper_question = random.choice(expansion_templates)
    return f"{reflection}\n\n🔍 Deeper Thought: {deeper_question}"

