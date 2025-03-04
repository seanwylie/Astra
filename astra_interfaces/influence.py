import json
import re
import boto3
import io
import wikipedia
from astra_core.config_loader import load_config  # ✅ Load configs dynamically
from astra_core.config_loader import debug_log

# ✅ Load general configurations
general_config = load_config("general_config")
S3_BUCKET_NAME = general_config.get("s3_bucket", "swylie-astra")
MIND_FILE_JSON = general_config.get("mind_file", "mind_file.json")
MIND_FILE_ORIG = general_config.get("structured_mind_file", "mind_file_parents.json")

s3 = boto3.client("s3")

### ✅ **New: save_to_s3() to prevent function errors**
def save_to_s3(mind_data):
    """Save mind file to S3 using proper encoding and error handling."""
    try:
        mind_file_json = json.dumps(mind_data, indent=4, ensure_ascii=False)  # ✅ Preserve Unicode characters
        s3.put_object(Bucket=S3_BUCKET_NAME, Key=MIND_FILE_JSON, Body=mind_file_json.encode("utf-8"))
        print(f"✅ Mind file saved to S3 successfully! Reflections: {len(mind_data['self_reflections'])}, "
              f"Questions: {len(mind_data['self_questions'])}, Knowledge: {len(mind_data['stored_knowledge'])}")
    except Exception as e:
        print(f"🚨 [ERROR] Failed to save mind file to S3: {e}")

def save_mind(mind_data):
    """Ensures knowledge persistence and prevents overwriting issues."""
    
    if mind_data is None or not isinstance(mind_data, dict):
        print("🚨 [ERROR] Attempted to save an invalid mind file! Prevented overwrite.")
        return  

    if not any(mind_data.get(k) for k in ["self_reflections", "self_questions", "stored_knowledge"]):
        print("🚨 [ERROR] Attempted to save an EMPTY mind file! Prevented overwrite.")
        return  

    print("🔍 Debug: Tracking self-questioning patterns before saving...")

    from astra_core.questions.question_manager import track_question_patterns
    track_question_patterns(mind_data)

    print("🔍 Debug: Sanitizing mind file before saving...")

    # ✅ Save pre-save state
    pre_save_counts = {
        "reflections": len(mind_data["self_reflections"]),
        "questions": len(mind_data["self_questions"]),
        "knowledge": len(mind_data["stored_knowledge"])
    }

    # ✅ Save mind file
    save_to_s3(mind_data)

    # ✅ Verify after saving
    debug_log("Loading")  
    reloaded_mind_data = load_mind()
    if not reloaded_mind_data:
        print("🚨 [ERROR] Failed to reload mind file after saving!")
        return

    reloaded_counts = {
        "reflections": len(reloaded_mind_data["self_reflections"]),
        "questions": len(reloaded_mind_data["self_questions"]),
        "knowledge": len(reloaded_mind_data["stored_knowledge"])
    }

    # ✅ Force save if any counts increased
    if any(reloaded_counts[k] < pre_save_counts[k] for k in pre_save_counts):
        print(f"⚠ WARNING: Data loss detected! Restoring missing entries.")
        for k in pre_save_counts:
            lost_entries = set(mind_data[k]) - set(reloaded_mind_data[k])
            mind_data[k].extend(lost_entries)
        
        save_to_s3(mind_data)  # ✅ Force re-save

def load_mind():
    """Load Astra's mind file from S3 while ensuring memory is managed properly."""
    print("🔍 Debug: Loading mind file from S3...")

    try:
        response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=MIND_FILE_JSON)
        mind_data = json.load(io.BytesIO(response["Body"].read()))
        print(f"✅ Loaded mind file: Reflections: {len(mind_data.get('self_reflections', []))}, "
              f"Questions: {len(mind_data.get('self_questions', []))}, "
              f"Knowledge: {len(mind_data.get('stored_knowledge', []))}")
    except (s3.exceptions.NoSuchKey, json.JSONDecodeError) as e:
        print(f"⚠ Warning: mind_file.json not found or corrupted in S3: {e}")
        return None

    # Validate structure
    for key in ["self_reflections", "self_questions", "stored_knowledge"]:
        if not isinstance(mind_data.get(key, []), list):
            print(f"⚠ Warning: `{key}` was not a list! Resetting...")
            mind_data[key] = []

    print(f"🔍 Loaded mind file. Knowledge count: {len(mind_data['stored_knowledge'])}")

    return mind_data  # 🚨 No structured merge happening here

def store_knowledge(mind_data, new_insight):
    """Ensure knowledge is stored while prioritizing Astra’s philosophy and marking questions as answered."""
    if mind_data is None:
        print("🚨 [ERROR] Memory unavailable. Skipping knowledge storage.")
        return  

    print(f"🧠 [DEBUG] Storing knowledge: {new_insight[:100]}...")

    # ✅ Prioritize human-AI philosophy over trivial definitions
    low_value_patterns = ["📄", "📖", "🔹", "genus", "mollusks", "species", "definition", "term", "word meaning"]
    if any(pattern in new_insight.lower() for pattern in low_value_patterns):
        print("⚠ [DEBUG] Skipping low-value knowledge (potential dictionary entry).")
        return

    # ✅ Answer existing self-questions
    answered_questions = [q for q in mind_data["self_questions"] if any(word in new_insight.lower() for word in q.split())]
    if answered_questions:
        print(f"✅ Answering {len(answered_questions)} questions with new knowledge!")
        mind_data["self_questions"] = [q for q in mind_data["self_questions"] if q not in answered_questions]

    # ✅ Prevent redundant storage
    if new_insight in mind_data["stored_knowledge"]:
        print("⚠ [DEBUG] Insight already exists. Skipping.")
        return
    
    mind_data["stored_knowledge"].append(new_insight)
    debug_log("Saving")
    save_mind(mind_data)
    print("📄 [DEBUG] Knowledge saved successfully!")


### ✅ Restored: is_term_or_phrase()
def is_term_or_phrase(concept):
    """Determine if a concept is a single term (Wikipedia) or a phrase (Google Search)."""
    clean_concept = re.sub(r"[^\w\s]", "", concept).strip()
    if not clean_concept:
        print(f"⚠ Ignoring malformed concept: '{concept}'")
        return None  
    
    if len(clean_concept.split()) <= 2:
        return "term"
    
    try:
        wiki_results = wikipedia.search(clean_concept, results=1)
        if wiki_results and clean_concept.lower() in [result.lower() for result in wiki_results]:
            return "term"
    except Exception:
        pass
    
    return "phrase"
