import random
import wikipedia
import time
from bs4 import BeautifulSoup

from astra_core.config_loader import load_config  # ✅ Load configs dynamically

general_config = load_config("general_config")  # ✅ Load schedule settings

def refine_knowledge(existing_ideas, mind_data):
    """Merge and refine knowledge, ensuring only true redundancy is removed."""
    if len(existing_ideas) < 2:
        return None  # Not enough data to merge

    selected_pair = None

    # ✅ Select two related insights that aren't trivial
    for _ in range(5):  # Try up to 5 times to find a relevant match
        concept_1, concept_2 = random.sample(existing_ideas, 2)

        # ✅ Ensure they are not completely unrelated topics
        if is_related(concept_1, concept_2) and len(concept_1) > 50 and len(concept_2) > 50:
            selected_pair = (concept_1, concept_2)
            break  # ✅ Found a suitable pair

    if not selected_pair:
        return None  # No valid pair found

    concept_1, concept_2 = selected_pair

    # ✅ Prevent merging concepts that are too similar
    if concept_1[:50] in concept_2 or concept_2[:50] in concept_1:
        return None

    # 🔹 Generate a natural knowledge integration phrase
    connection_phrases = general_config["connection_phrases"]
    new_concept = f"{random.choice(connection_phrases)} {concept_1} and {concept_2}."

    # ✅ Ensure no duplication
    if new_concept not in mind_data["stored_knowledge"]:
        mind_data["stored_knowledge"].append(new_concept)

        # ✅ Debug: Show refined knowledge added
        print(f"🔹 Refined knowledge added. New count: {len(mind_data['stored_knowledge'])}")

        # 🔥 PRUNING LOGIC: Ensure we are only removing redundant knowledge
        MAX_REMOVAL_PERCENT = 0.05  # ⬇ Lower from 10% → 5%
        max_removal_count = max(3, int(len(mind_data["stored_knowledge"]) * MAX_REMOVAL_PERCENT))

        # 🚨 SAFEGUARD: If knowledge drops below 80, stop pruning
        MIN_KNOWLEDGE_THRESHOLD = 80
        if len(mind_data["stored_knowledge"]) <= MIN_KNOWLEDGE_THRESHOLD:
            print(f"🚨 Too little knowledge remaining! Skipping pruning. Count: {len(mind_data['stored_knowledge'])}")
            return new_concept

        redundant_pairs = [
            (c1, c2) for c1 in mind_data["stored_knowledge"] for c2 in mind_data["stored_knowledge"]
            if c1 != c2 and is_related(c1, c2) and len(c1) < len(new_concept) and len(c2) < len(new_concept)
        ]

        removed_items = []
        removal_count = 0

        for c1, c2 in redundant_pairs:
            if c1 in mind_data["stored_knowledge"] and c2 in mind_data["stored_knowledge"]:
                if removal_count < max_removal_count:
                    mind_data["stored_knowledge"].remove(c1)
                    removal_count += 1
                if removal_count < max_removal_count:
                    mind_data["stored_knowledge"].remove(c2)
                    removal_count += 1
                removed_items.append(c1[:50])
                removed_items.append(c2[:50])

        # ✅ Debug: Show what was removed
        if removed_items:
            print(f"🗑 Pruned {removal_count} knowledge items. Remaining count: {len(mind_data['stored_knowledge'])}")

    return new_concept


def is_related(concept_1, concept_2):
    """Determines if two concepts are related based on shared keywords."""
    keywords_1 = set(concept_1.lower().split()[:8])  # ⬆ Use only the first 8 words (down from 10)
    keywords_2 = set(concept_2.lower().split()[:8])

    common_words = keywords_1.intersection(keywords_2)

    return len(common_words) > 3  # ⬆ Increase threshold (was 2)

def deepen_reflection(reflection):
    """Expands on a reflection by adding depth or new questions."""
    expansion_templates = general_config["expansion_templates"]
    deeper_question = random.choice(expansion_templates)
    return f"{reflection}\n\n🔍 Deeper Thought: {deeper_question}"

def fetch_wikipedia_summary(query):
    """Fetch a Wikipedia summary while handling disambiguation, rate limits, and missing pages."""
    try:
        print(f"🌐 Searching Wikipedia for: {query}")
        summary = wikipedia.summary(query, sentences=2)
        
        # ✅ Ensure response is always a string
        soup = BeautifulSoup(summary, "html.parser")
        summary = soup.get_text()

        return summary
    
    except wikipedia.exceptions.DisambiguationError as e:
        print(f"⚠ Wikipedia disambiguation triggered for '{query}', checking alternatives...")
        # ✅ Look for the best match instead of picking the first option blindly
        for option in e.options:
            if "philosophy" in option or "science" in option or "concept" in option:
                print(f"🔍 Trying refined match: {option}")
                return fetch_wikipedia_summary(option)
        
        print(f"⚠ No strong Wikipedia match found for '{query}'. Skipping.")
        return None

    except wikipedia.exceptions.PageError:
        print(f"⚠ No Wikipedia page found for '{query}'. Skipping.")
        return None

    except wikipedia.exceptions.HTTPTimeoutError:
        print("⚠ Wikipedia request timed out. Retrying...")
        time.sleep(2)
        return fetch_wikipedia_summary(query)

    except wikipedia.exceptions.WikipediaException as e:
        print(f"⚠ Wikipedia lookup failed: {e}")
        return None



def is_term_or_phrase(concept):
    """Determine whether a concept is a single-word term or a multi-word phrase."""
    if " " in concept.strip():
        return "phrase"
    return "term"



