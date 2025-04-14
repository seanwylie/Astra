# beta/services/concept_service.py

"""
📚 Concept Service
------------------
Utility functions for storing new concepts into Astra’s knowledge base.

These are typically called after unknown terms are discovered in user messages.
"""

from astra_interfaces.mind_session import session

def store_concept(term: str, definition: str) -> str:
    """
    Saves a new concept-definition pair into Astra's `stored_knowledge`.

    Args:
        term (str): The unknown word or phrase Astra just learned.
        definition (str): The definition to store.

    Returns:
        str: Status message indicating result.
    """
    mind_data = session.load()
    mind_data.setdefault("stored_knowledge", [])

    formatted_entry = f"📖 **{term}**: {definition}"

    if formatted_entry not in mind_data["stored_knowledge"]:
        mind_data["stored_knowledge"].append(formatted_entry)
        session.maybe_save()
        return f"✅ Stored new concept: {formatted_entry}"
    else:
        return f"⚠ Concept '{term}' already exists in memory."
