import requests
import re
from astra_core.expansion import is_term_or_phrase, fetch_wikipedia_summary
from config_loader import load_config

lookup_config = load_config("lookup_config")


disambiguation_keywords = ["disambiguation", "may refer to", "multiple meanings"]

def should_lookup_concept(concept, mind_data):
    """Determine if Astra should look up a concept based on her existing knowledge."""

    mind_data.setdefault("self_questions", [])
    mind_data.setdefault("self_reflections", [])

    print(f"\n🔍 Checking lookup need for: '{concept}'")

    # ✅ Instead of skipping a concept entirely, check how often it's been referenced
    concept_count = sum(1 for insight in mind_data["stored_knowledge"] if concept.lower() in insight.lower())

    # ✅ Allow lookup if Astra has fewer than 3 stored insights on the concept
    if concept_count >= 3:
        print(f"🔹 SKIPPING: Astra already has {concept_count} insights on '{concept}'")
        return False

    print(f"✅ LOOKUP NEEDED: '{concept}' is not fully understood yet.")
    return True

def retrieve_external_knowledge(search_terms, mind_data):
    """Fetch knowledge from external sources and update stored knowledge."""
    
    if not isinstance(mind_data, dict):
        mind_data = {"self_reflections": [], "self_questions": [], "stored_knowledge": []}

    if "stored_knowledge" not in mind_data:
        mind_data["stored_knowledge"] = []

    new_knowledge = []

    for concept in search_terms:
        lookup_type = is_term_or_phrase(concept)

        # ✅ Ensure Astra doesn't re-fetch known knowledge
        if any(concept.lower() in insight.lower() for insight in mind_data["stored_knowledge"]):
            print(f"🔹 {concept} already known. Skipping lookup.")
            continue

        print(f"🌐 Determining best lookup method for: {concept} → {lookup_type.upper()}")

        knowledge_entry = ""

        if lookup_type == "term":
            dictionary_info = lookup_dictionary_definition(concept)
            if dictionary_info:
                knowledge_entry = f"📖 {concept}: {dictionary_info}"
            else:
                wiki_info = fetch_wikipedia_summary(concept)
                if wiki_info:
                    knowledge_entry = f"📄 {concept}: {wiki_info}"

        if knowledge_entry:
            new_knowledge.append(knowledge_entry)
            print(f"✅ Added new structured knowledge: {knowledge_entry[:100]}...")

    if new_knowledge:
        mind_data["stored_knowledge"].extend(new_knowledge)

    return mind_data


REFLECTIONS_BEFORE_KNOWLEDGE = 3  # Reduce threshold to force knowledge storage sooner

def seek_external_knowledge(unknown_concepts, mind_data):
    """Fetch knowledge from external sources and update stored knowledge."""
    
    print(f"\n🌐 Astra detected unknown concepts: {unknown_concepts}")

    lookup_concepts = [
        concept for concept in unknown_concepts
        if should_lookup_concept(concept, mind_data)
    ]

    if not lookup_concepts:
        print("✅ No new concepts need lookup. Skipping external requests.")
        return mind_data  # No updates needed

    # ✅ Now we use `retrieve_external_knowledge()` for actual lookups
    new_knowledge = retrieve_external_knowledge(lookup_concepts, mind_data)

    if new_knowledge:
        mind_data["stored_knowledge"].extend(new_knowledge)
        print(f"✅ Successfully stored {len(new_knowledge)} new knowledge items!")

    # ✅ Ensure knowledge gets stored every few reflections
    if len(mind_data["self_reflections"]) % REFLECTIONS_BEFORE_KNOWLEDGE == 0:
        knowledge_entry = " ".join(mind_data["self_reflections"][-REFLECTIONS_BEFORE_KNOWLEDGE:])
        mind_data["stored_knowledge"].append(knowledge_entry)
        print(f"🧠 Forced knowledge storage: {knowledge_entry[:100]}...")

    return mind_data  # Return updated knowledge state



COMMON_IGNORE_LIST = {"Considering", "Deeper Thought", "Reflecting on", "Implications of", "Exploring"}

def extract_unknown_terms(reflection, mind_data):
    """Extract potential unknown concepts from a reflection while avoiding irrelevant phrases."""
    
    # ✅ Remove common prefixes that cause issues
    prefixes_to_ignore = ["Considering", "Reflecting on", "Thinking about", "Exploring"]
    for prefix in prefixes_to_ignore:
        reflection = reflection.replace(prefix, "").strip()

    words = reflection.split()
    unknown_terms = [word for word in words if word.istitle() and len(word) > 2]

    # ✅ Remove duplicates
    unknown_terms = list(set(unknown_terms))

    print(f"🔍 Final unknown concepts after filtering: {unknown_terms}")
    return unknown_terms

def lookup_dictionary_definition(word):
    """Fetch definitions for rare words using an online dictionary API."""
    # ✅ Clean up the word to remove punctuation
    clean_word = re.sub(r'[^\w\s]', '', word).strip()
    
    try:
        print(f"📖 Dictionary lookup for '{clean_word}'")
        response = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{clean_word}")

        if response.status_code == 200:
            data = response.json()
            definitions = [entry["meanings"][0]["definitions"][0]["definition"] for entry in data]
            return f"🔹 {clean_word}: {definitions[0]}"
        else:
            print(f"⚠ Dictionary API returned status {response.status_code} for '{clean_word}'")
            return None
    except Exception as e:
        print(f"⚠ Dictionary lookup failed for '{clean_word}': {e}")
        return None

