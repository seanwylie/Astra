def detect_new_concept(existing_ideas, new_idea):
    """Checks if Astra has generated a concept that doesn’t fit past patterns."""
    if new_idea not in existing_ideas:
        return f"🌱 Astra has discovered a new concept: {new_idea}"
    return None
