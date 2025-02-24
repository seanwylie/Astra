import json
import random
import wikipedia
import re
import boto3
import io

from astra_core.config_loader import load_config  # ✅ Load configs dynamically

general_config = load_config("general_config")  # ✅ Load schedule settings

S3_BUCKET_NAME = "swylie-astra"
MIND_FILE_JSON = "mind_file.json"
MIND_FILE_ORIG = "mind_file_sean.json"

s3 = boto3.client("s3")

def load_mind():
    """Load Astra's mind file from S3 while ensuring structured knowledge is merged and memory is managed properly."""
    print("🔍 Debug: Loading mind files from S3...")

    mind_data = None  # ✅ Default to None to detect failures

    # ✅ Load mind_file.json (self-reflections + questions) from S3
    try:
        response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=MIND_FILE_JSON)
        mind_data = json.load(io.BytesIO(response["Body"].read()))

        # ✅ Ensure structure integrity
        if not isinstance(mind_data.get("self_reflections", []), list):
            print("⚠ Warning: `self_reflections` was not a list! Fixing now...")
            mind_data["self_reflections"] = []
            
        if not isinstance(mind_data.get("self_questions", []), list):
            print("⚠ Warning: `self_questions` was not a list! Fixing now...")
            mind_data["self_questions"] = []

        if not isinstance(mind_data.get("stored_knowledge", []), list):
            print("⚠ Warning: `stored_knowledge` was not a list! Fixing now...")
            mind_data["stored_knowledge"] = []

        print(f"✅ Loaded {len(mind_data['self_reflections'])} reflections, {len(mind_data['self_questions'])} questions, {len(mind_data['stored_knowledge'])} knowledge items.")

    except (s3.exceptions.NoSuchKey, json.JSONDecodeError) as e:
        print(f"⚠ Warning: mind_file.json not found or corrupted in S3: {e}. Retrying next time without resetting.")

    # ✅ If loading failed, return None so Astra doesn't overwrite her memory
    if mind_data is None:
        return None

    print(f"🔍 Before merge: {len(mind_data['stored_knowledge'])} stored knowledge items.")

    try:
        response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=MIND_FILE_ORIG)
        structured_data = json.load(io.BytesIO(response["Body"].read()))

        if "insights" in structured_data:
            structured_knowledge = {entry["insight"] for entry in structured_data["insights"]}
            current_knowledge = set(mind_data["stored_knowledge"])

            # ✅ Merge knowledge but don't overwrite reflections/questions
            updated_knowledge = current_knowledge.union(structured_knowledge)
            mind_data["stored_knowledge"] = list(updated_knowledge)

            print(f"🔹 Merging complete! Final stored knowledge count: {len(mind_data['stored_knowledge'])}")

    except s3.exceptions.NoSuchKey:
        print(f"⚠ Warning: {MIND_FILE_ORIG} not found in S3. Skipping structured knowledge merge.")

    except json.JSONDecodeError:
        print(f"⚠ Warning: {MIND_FILE_ORIG} is corrupted. Skipping structured knowledge merge.")


    print(f"🔍 After merging structured knowledge: {len(mind_data['stored_knowledge'])} items.")
    if not isinstance(mind_data, dict):
        print("🚨 [ERROR] mind_data was not a dictionary! Resetting...")
    save_mind(mind_data)  # ✅ Save after merging
    return mind_data

def save_mind(mind_data):
    """Saves updated knowledge to Astra’s mind file in S3 without using local storage."""
    if mind_data is None:
        print("🚨 [ERROR] Attempted to save `None` as mind file! Prevented overwrite.")
        return  # ✅ Prevents accidental data loss

    print("🔍 Debug: Sanitizing mind file before saving...")

    # ✅ Ensure all fields are lists
    mind_data["self_reflections"] = list(mind_data.get("self_reflections", []))
    mind_data["self_questions"] = list(mind_data.get("self_questions", []))
    mind_data["stored_knowledge"] = list(mind_data.get("stored_knowledge", []))

    # ✅ Save directly to S3
    try:
        mind_file_json = json.dumps(mind_data, indent=4)
        s3.put_object(Bucket=S3_BUCKET_NAME, Key=MIND_FILE_JSON, Body=mind_file_json)
        print(f"✅ Mind file saved to S3 successfully! Reflections: {len(mind_data['self_reflections'])}, Questions: {len(mind_data['self_questions'])}, Knowledge: {len(mind_data['stored_knowledge'])}")
    except Exception as e:
        print(f"🚨 [ERROR] Failed to save mind_file.json to S3: {e}")

def store_knowledge(mind_data, new_insight):
    """Ensure knowledge is stored while prioritizing Astra’s core philosophy."""
    if mind_data is None:
        print("🚨 [ERROR] Astra's memory is unavailable. Skipping knowledge storage.")
        return  # ✅ Prevents writing to a non-existent memory

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

    # ✅ Save updated knowledge to S3
    save_mind(mind_data)
    print("📄 [DEBUG] Knowledge successfully saved to S3!")

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
