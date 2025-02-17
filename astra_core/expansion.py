import random
import wikipedia
from bs4 import BeautifulSoup

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

    # ✅ Ensure merging does not modify reflections
    if "Considering" in concept_1 or "Considering" in concept_2:
        return None

    # ✅ Prevent merging concepts that are too similar
    if concept_1[:50] in concept_2 or concept_2[:50] in concept_1:
        return None

    # ✅ Prevent recursive phrasing by checking for self-referential phrases
    if concept_1 in concept_2 or concept_2 in concept_1:
        print(f"⚠ Recursive phrase detected! Skipping merge of: \n - {concept_1[:100]}... \n - {concept_2[:100]}...")
        return None  

    # 🔹 Generate a natural knowledge integration phrase
    connection_phrases = [
        "By integrating these insights, a new understanding emerges:",
        "This suggests a deeper relationship between",
        "These ideas together point to an important realization:",
        "By combining these concepts, Astra gains a refined perspective on"
    ]
    new_concept = f"{random.choice(connection_phrases)} {concept_1} and {concept_2}."

    # ✅ Ensure no duplication
    if new_concept not in mind_data["stored_knowledge"]:
        mind_data["stored_knowledge"].append(new_concept)
        print(f"🔹 Refined knowledge added: {new_concept[:100]}...")

        # 🔥 PRUNING LOGIC: Ensure we are only removing redundant knowledge
        redundant_pairs = [
            (c1, c2) for c1 in mind_data["stored_knowledge"] for c2 in mind_data["stored_knowledge"]
            if c1 != c2 and is_related(c1, c2) and len(c1) < len(new_concept) and len(c2) < len(new_concept)
        ]

        # ✅ Only remove if both old concepts are redundant compared to the new one
        removed_items = []
        for c1, c2 in redundant_pairs:
            if c1 in mind_data["stored_knowledge"] and c2 in mind_data["stored_knowledge"]:
                if len(mind_data["stored_knowledge"]) > 25:  # ✅ Never drop below 25 knowledge items
                    mind_data["stored_knowledge"].remove(c1)
                    mind_data["stored_knowledge"].remove(c2)
                    removed_items.extend([c1[:50], c2[:50]])

        if removed_items:
            print(f"🗑 Removed redundant knowledge: {', '.join(removed_items)}")

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


def fetch_wikipedia_summary(query):
    """Fetch a Wikipedia summary for a given term, ensuring it always returns a string."""
    try:
        print(f"🌐 Fetching Wikipedia summary for: {query}")
        summary = wikipedia.summary(query, sentences=2)

        # ✅ Ensure response is always a string
        if isinstance(summary, list):
            summary = " ".join(summary)  # Convert list to a single string

        # ✅ Use BeautifulSoup with explicit parser to avoid list parsing issues
        soup = BeautifulSoup(summary, "html.parser")
        summary = soup.get_text()

        # print(f"✅ Wikipedia returned: {type(summary)}")
        print(f"📄 Wikipedia content preview: {summary[:100]}..." if summary else "⚠ Wikipedia returned NOTHING!")

        return summary

    except wikipedia.exceptions.DisambiguationError as e:
        print(f"⚠ Wikipedia disambiguation for '{query}', selecting best match...")
        best_guess = e.options[0] if e.options else None

        if best_guess:
            print(f"🔍 Trying best match: {best_guess}")
            try:
                summary = wikipedia.summary(best_guess, sentences=2)

                # ✅ Ensure response is a string
                if isinstance(summary, list):
                    summary = " ".join(summary)

                soup = BeautifulSoup(summary, "html.parser")
                summary = soup.get_text()

                return summary
            except Exception as retry_error:
                print(f"⚠ Failed retrying with best match: {retry_error}")
                return None
        else:
            return None

    except wikipedia.exceptions.PageError:
        print(f"⚠ No Wikipedia page found for '{query}', skipping.")
        return None

    except Exception as e:
        print(f"🚨 Unexpected Wikipedia error: {e}")
        return None


def is_term_or_phrase(concept):
    """Determine whether a concept is a single-word term or a multi-word phrase."""
    if " " in concept.strip():
        return "phrase"
    return "term"


def is_related(concept_1, concept_2):
    """Determines if two concepts are related based on shared keywords."""
    keywords_1 = set(concept_1.lower().split()[:10])  # Use first 10 words as keywords
    keywords_2 = set(concept_2.lower().split()[:10])

    common_words = keywords_1.intersection(keywords_2)

    return len(common_words) > 2  # ✅ Consider related if at least 2 words overlap


