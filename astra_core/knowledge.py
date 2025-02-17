from astra_core.expansion import is_term_or_phrase, fetch_wikipedia_summary

disambiguation_keywords = ["disambiguation", "may refer to", "multiple meanings"]

def should_lookup_concept(concept, mind_data):
    """Determine if Astra should look up a concept based on her existing knowledge."""
    
    mind_data.setdefault("self_questions", [])
    mind_data.setdefault("self_reflections", [])

    print(f"\n🔍 Checking lookup need for: '{concept}'")
    # print(f"📚 Current Stored Knowledge: {mind_data['stored_knowledge']}")

    # ✅ Check if Astra already knows the concept
    if any(concept.lower() in insight.lower() for insight in mind_data["stored_knowledge"]):
        print(f"🔹 SKIPPING: Astra already knows '{concept}'")
        return False

    # ✅ Check if Astra has questioned this concept before
    if any(concept.lower() in question.lower() for question in mind_data["self_questions"]):
        print(f"🔍 Astra lacks context for '{concept}'—lookup triggered")
        return True

    print(f"✅ LOOKUP NEEDED: '{concept}' is unknown!")
    return True




def detect_conflict(concept, new_definitions, mind_data):
    """Detect contradictions between new definitions and stored knowledge."""
    conflicting = []
    
    for definition in new_definitions:
        for existing_knowledge in mind_data["stored_knowledge"]:
            if concept.lower() in existing_knowledge.lower():
                if definition.lower() not in existing_knowledge.lower():
                    conflicting.append((definition, existing_knowledge))

    return conflicting

def retrieve_external_knowledge(search_terms, mind_data):
    """Fetch knowledge from external sources and update stored knowledge."""
    print(f"🔍 Debug: Type of `mind_data` BEFORE lookup: {type(mind_data)}")

    # ✅ Ensure `mind_data` is always a dictionary
    if not isinstance(mind_data, dict):
        print("🚨 ERROR: `mind_data` is not a dictionary! Resetting...")
        mind_data = {"self_reflections": [], "self_questions": [], "stored_knowledge": []}

    # ✅ Ensure `stored_knowledge` exists and is a list
    if "stored_knowledge" not in mind_data or not isinstance(mind_data["stored_knowledge"], list):
        print("🚨 ERROR: `stored_knowledge` is missing or not a list! Resetting...")
        mind_data["stored_knowledge"] = []

    new_knowledge = []

    for concept in search_terms:
        lookup_type = is_term_or_phrase(concept)

        # ✅ Ensure Astra doesn't re-fetch known knowledge
        if any(concept.lower() in insight.lower() for insight in mind_data["stored_knowledge"]):
            print(f"🔹 {concept} already known. Skipping lookup.")
            continue

        print(f"🌐 Determining best lookup method for: {concept} → {lookup_type.upper()}")

        if lookup_type == "term":
            wiki_info = fetch_wikipedia_summary(concept)

            # 🚨 DEBUG: Show what Wikipedia is returning
            print(f"🔍 Wikipedia lookup result type: {type(wiki_info)}")
            print(f"📄 Wikipedia lookup content preview: {wiki_info[:100]}..." if wiki_info else "⚠ Wikipedia lookup returned NOTHING!")

            if wiki_info:
                if isinstance(wiki_info, list):  # 🚨 Flatten lists just in case
                    wiki_info = " ".join(wiki_info)

                if wiki_info not in mind_data["stored_knowledge"]:
                    new_knowledge.append(wiki_info)
                    print(f"✅ New Wikipedia knowledge added: {wiki_info[:100]}...")

        elif lookup_type == "phrase":
            print(f"🔍 (Placeholder) Would search Google for: {concept}")

    # ✅ Merge new knowledge into `stored_knowledge`
    if new_knowledge:
        mind_data["stored_knowledge"].extend(new_knowledge)

    print(f"🔍 Debug: Type of `mind_data` AFTER lookup: {type(mind_data)}")
    return mind_data  # ✅ Always return a dictionary



def seek_external_knowledge(unknown_concepts, mind_data):
    """Determine which unknown concepts need lookup and retrieve knowledge."""
    
    print(f"\n🌐 Astra detected unknown concepts: {unknown_concepts}")

    # ✅ Filter out concepts that don't actually need lookup
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

