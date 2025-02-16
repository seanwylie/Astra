def deprioritize_knowledge(knowledge_list):
    """Gradually deprioritizes older knowledge that Astra no longer references."""
    if len(knowledge_list) > 50:  # Example threshold
        faded_idea = knowledge_list.pop(0)  # Remove the oldest idea
        return f"🕰️ Astra has deprioritized: {faded_idea}"
    return None
