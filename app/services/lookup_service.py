# lookup_service.py

"""
🔍 Lookup Service
-----------------
Provides factual, multi-source definitions and explanations for unfamiliar terms.

This service powers Astra’s `!lookup` command, drawing from:
- Memory (user-taught knowledge)
- Dictionary
- Wikipedia
- GPT-4 (as a fallback explainer)

Behavioral Philosophy:
- The goal is **accuracy** and **clarity**, not emotional interpretation.
- Responses are factual, neutral, and easy to understand.
- Astra’s mood or personality is **not** used here.
- For emotional or philosophical takes, consider a future `!reflect_on <term>` command.

Author: Sean Wylie
Created: 2025-04-14
"""

# --- Imports ---
import os
import json
import wikipedia
from openai import OpenAI
from app.core.astra_helpers.utils_helper import lookup_definition
from app.interfaces.mind_session import session

# --- Client Setup ---
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Public API ---

def lookup_term(term: str) -> list[str]:
    """
    Looks up a term using Astra’s memory, dictionary, Wikipedia, and GPT-4 fallback.

    Args:
        term (str): The concept or word to explain.

    Returns:
        list[str]: A list of Discord-safe 1900-character chunks summarizing the findings.
    """
    mind_data = session.load()
    stored_knowledge = mind_data.get("stored_knowledge", [])

    # Step 1: Search existing memory and sources
    memory_match = next((entry for entry in stored_knowledge if term.lower() in entry.lower()), None)
    dictionary_definition = lookup_definition(term)

    try:
        wikipedia_summary = wikipedia.summary(term, sentences=2)
    except wikipedia.exceptions.DisambiguationError as e:
        wikipedia_summary = f"🔍 Wikipedia has multiple meanings for '{term}': {', '.join(e.options[:3])}..."
    except wikipedia.exceptions.PageError:
        wikipedia_summary = None

    # Step 2: Assemble multi-source definition
    knowledge_sources = [
        f"🔹 Memory: {memory_match}" if memory_match else None,
        f"📖 Dictionary: {dictionary_definition}" if dictionary_definition else None,
        f"🌐 Wikipedia: {wikipedia_summary}" if wikipedia_summary else None,
    ]
    knowledge_text = "\n".join(filter(None, knowledge_sources)).strip()

    # Step 3: GPT clarification (fallback synthesis)
    prompt = f"""
You are Astra, an assistant who explains terms using memory, dictionary, and Wikipedia knowledge.

Here’s what was found about the term **{term}**:
{knowledge_text or "No definitions found."}

Explain this to a curious user in clear, neutral language.
Clarify ambiguous terms. Provide context or examples if helpful.
""".strip()

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=250,
            temperature=0.6
        )
        ai_reasoning = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[lookup_service] ⚠ GPT explanation failed: {e}")
        ai_reasoning = "⚠ GPT is currently unavailable. Fallback definitions provided."

    # Step 4: Store learned knowledge if new
    if not memory_match:
        formatted_entry = f"📖 **{term}**:\n- Dictionary: {dictionary_definition}\n- Wikipedia: {wikipedia_summary}"
        if formatted_entry not in stored_knowledge:
            mind_data["stored_knowledge"].append(formatted_entry)
            session.maybe_save()
            print(f"[lookup_service] ✅ Stored new knowledge: {term}")
        else:
            print(f"[lookup_service] ⚠ '{term}' already exists in memory.")

    # Step 5: Chunk output for Discord safety
    full_output = f"🔍 **{term}**\n\n{knowledge_text}\n\n🤖 {ai_reasoning}"
    return [full_output[i:i + 1900] for i in range(0, len(full_output), 1900)]
