import json
import random
import wikipedia
import re

from astra_core.config_loader import load_config  # ✅ Load configs dynamically

general_config = load_config("general_config")  # ✅ Load schedule settings



MIND_FILE_JSON = "mind_file.json"
MIND_FILE_ORIG = "mind_file_sean.json"

def load_mind():
    """Load Astra's mind file while ensuring structured knowledge is merged and memory is managed properly."""
    print("🔍 Debug: Loading mind files...")



    # ✅ Default structure
    mind_data = {
        "self_reflections": [],
        "self_questions": [],
        "stored_knowledge": [],
    }

    # ✅ Load mind_file.json (self-reflections + questions)
    try:
        with open(MIND_FILE_JSON, "r", encoding="utf-8") as f:
            mind_data = json.load(f)


            # ✅ Force `self_reflections` to be a list
            if not isinstance(mind_data["self_reflections"], list):
                print("⚠ Warning: `self_reflections` was not a list! Fixing now...")
                mind_data["self_reflections"] = []
                
            # ✅ Force `self_reflections` to be a list
            if not isinstance(mind_data["self_questions"], list):
                print("⚠ Warning: `self_questions` was not a list! Fixing now...")
                mind_data["self_questions"] = []

            print(f"✅ Loaded {len(mind_data['self_reflections'])} reflections, {len(mind_data['self_questions'])} questions.")
    except (FileNotFoundError, json.JSONDecodeError):
        print("⚠ Warning: mind_file.json not found or corrupted. Starting with an empty mind.")
    
    print(f"🔍 Before merge: {len(mind_data['stored_knowledge'])} stored knowledge items.")

    # ✅ Merge structured knowledge from mind_file_sean.json
    try:
        with open(MIND_FILE_ORIG, "r", encoding="utf-8") as f:
            structured_data = json.load(f)

            if "insights" in structured_data:
                structured_knowledge = {entry["insight"] for entry in structured_data["insights"]}
                current_knowledge = set(mind_data["stored_knowledge"])

                # ✅ Merge knowledge but don't overwrite reflections/questions
                updated_knowledge = current_knowledge.union(structured_knowledge)
                mind_data["stored_knowledge"] = list(updated_knowledge)

                print(f"🔹 Merging complete! Final stored knowledge count: {len(mind_data['stored_knowledge'])}")

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"⚠ Error loading structured mind file: {e}")

    print(f"🔍 After merging structured knowledge: {len(mind_data['stored_knowledge'])} items.")
    # print(f"🔍 Debug: Type of `mind_data`: {type(mind_data)}")
    # print(f"🔍 Debug: Raw `mind_data`: {mind_data}")
    save_mind(mind_data)
    return mind_data



def save_mind(mind_data):
    """Saves updated knowledge to Astra’s mind file while ensuring no nested structures exist."""
    print("🔍 Debug: Sanitizing mind file before saving...")

    # ✅ Ensure all fields are lists
    mind_data["self_reflections"] = list(mind_data.get("self_reflections", []))
    mind_data["self_questions"] = list(mind_data.get("self_questions", []))
    mind_data["stored_knowledge"] = list(mind_data.get("stored_knowledge", []))

    # ✅ Save back to mind_file.json
    with open(MIND_FILE_JSON, "w", encoding="utf-8") as f:
        json.dump(mind_data, f, indent=4)

    print(f"✅ Mind file saved successfully! Reflections: {len(mind_data['self_reflections'])}, Questions: {len(mind_data['self_questions'])}, Knowledge: {len(mind_data['stored_knowledge'])}")


def store_knowledge(mind_data, new_insight):
    """Ensure knowledge is stored while prioritizing Astra’s core philosophy."""
    import json
    mind_file_path = "/home/ubuntu/astra_reflections/mind_file.json"

    print(f"🧠 [DEBUG] Attempting to store knowledge: {new_insight[:100]}...")

    # ✅ Prevent duplicate storage
    if any(new_insight[:50] in insight for insight in mind_data["stored_knowledge"]):
        print("⚠ [DEBUG] Insight already exists. Skipping.")
        return

    # 🔹 Define core themes Astra values
    core_themes = ["self-reflection", "collaboration", "ethical AI", "curiosity", "growth"]
    score = sum(1 for theme in core_themes if theme in new_insight.lower())

    # ✅ Loosen filtering: Store all high-scoring insights
    if score > 0 or random.random() < 0.8:  # ✅ Increase general knowledge storage to 80%
        mind_data["stored_knowledge"].append(new_insight)
        print(f"✅ [DEBUG] Stored new insight: {new_insight[:100]}... (Score: {score})")

    # ✅ Save updated knowledge
    with open(mind_file_path, "w") as f:
        json.dump(mind_data, f, indent=4)
    print("📄 [DEBUG] Knowledge successfully saved!")




def is_term_or_phrase(concept):
    """Determine if a concept is a single term (Wikipedia) or a phrase (Google Search)."""

    # 🔹 Strip punctuation to avoid lookup errors
    clean_concept = re.sub(r"[^\w\s]", "", concept).strip()

    # 🔹 If the cleaned concept is empty after stripping, ignore it
    if not clean_concept:
        print(f"⚠ Ignoring malformed concept: '{concept}'")
        return None  

    # 🔹 If the concept is one or two words, treat it as a term
    if len(clean_concept.split()) <= 2:
        return "term"

    # 🔹 Check if Wikipedia recognizes it as a title
    try:
        wiki_search_results = wikipedia.search(clean_concept, results=1)
        if wiki_search_results and clean_concept.lower() in [result.lower() for result in wiki_search_results]:
            return "term"
    except Exception:
        pass  # Ignore errors, fallback to phrase

    # 🔹 If it's longer than two words and doesn't match a Wikipedia entry, it's a phrase
    return "phrase"

