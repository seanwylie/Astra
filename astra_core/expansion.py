import random
import wikipedia
import time
from fuzzywuzzy import fuzz
from bs4 import BeautifulSoup

from astra_core.config_loader import load_config  # ✅ Load configs dynamically

general_config = load_config("general_config")  # ✅ Load schedule settings

def refine_knowledge(existing_ideas, mind_data):
    """Merge and refine knowledge, ensuring only true redundancy is removed."""
    
    if len(existing_ideas) < 2:
        return None  # ✅ Not enough data to merge

    selected_pair = None
    retry_attempts = 5  # 🔥 Reduce attempts for better efficiency

    for _ in range(retry_attempts):
        concept_1, concept_2 = random.sample(existing_ideas, 2)

        if not isinstance(concept_1, str) or not isinstance(concept_2, str):
            continue
        if len(concept_1) < 20 or len(concept_2) < 20:
            continue

        if is_related(concept_1, concept_2):
            selected_pair = (concept_1, concept_2)
            break  

    if not selected_pair:
        return None  

    concept_1, concept_2 = selected_pair

    # ✅ Prevent merging near-identical concepts
    if concept_1[:50] in concept_2 or concept_2[:50] in concept_1:
        return None

    connection_phrases = general_config["connection_phrases"]
    merged_idea = f"{random.choice(connection_phrases)} {concept_1} and {concept_2}."

    # ✅ Ensure no duplication
    if merged_idea not in mind_data["stored_knowledge"]:
        mind_data["stored_knowledge"].append(merged_idea)
        print(f"🔹 Refined knowledge added. New count: {len(mind_data['stored_knowledge'])}")

        # ✅ Limit pruning to 3% of knowledge
        MAX_REMOVAL_PERCENT = 0.03
        max_removal_count = max(3, int(len(mind_data["stored_knowledge"]) * MAX_REMOVAL_PERCENT))

        # ✅ Prevent over-pruning if too little knowledge remains
        MIN_KNOWLEDGE_THRESHOLD = 100
        if len(mind_data["stored_knowledge"]) <= MIN_KNOWLEDGE_THRESHOLD:
            print(f"🚨 Too little knowledge remaining! Skipping pruning. Count: {len(mind_data['stored_knowledge'])}")
            return merged_idea

        # ✅ Optimize redundant comparisons
        removed_items = []
        removal_count = 0
        redundant_items = set()

        for c1, c2 in [(c1, c2) for c1 in mind_data["stored_knowledge"] for c2 in mind_data["stored_knowledge"] if c1 != c2]:
            if removal_count >= max_removal_count:
                break

            if is_related(c1, c2):
                if c1 not in redundant_items:
                    mind_data["stored_knowledge"].remove(c1)
                    removed_items.append(c1[:50])
                    redundant_items.add(c1)
                    removal_count += 1

                if c2 not in redundant_items and removal_count < max_removal_count:
                    mind_data["stored_knowledge"].remove(c2)
                    removed_items.append(c2[:50])
                    redundant_items.add(c2)
                    removal_count += 1

        if removed_items:
            print(f"🗑 Pruned {removal_count} knowledge items. Remaining count: {len(mind_data['stored_knowledge'])}")

    return merged_idea



def is_related(concept_1, concept_2):
    """Determine if two concepts are related using fuzzy matching."""
    
    # ✅ Ensure both inputs are strings
    if not isinstance(concept_1, str) or not isinstance(concept_2, str):
        print(f"🚨 Warning: Non-string input detected! {type(concept_1)} vs {type(concept_2)}")
        return False

    # ✅ Prevent fuzzy matching on massive text blocks
    concept_1 = concept_1[:250]
    concept_2 = concept_2[:250]

    try:
        similarity = fuzz.ratio(concept_1, concept_2)
    except Exception as e:
        print(f"🚨 Error computing similarity: {e}")
        return False

    return similarity > 30  # 🔥 Adjusted to require at least 30% similarity




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



