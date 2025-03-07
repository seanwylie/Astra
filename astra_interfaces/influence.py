import json
import re
import boto3
import io
import wikipedia
import time
import os
from astra_core.config_loader import load_config  # ✅ Load configs dynamically
from astra_core.config_loader import debug_log

# ✅ Load general configurations
general_config = load_config("general_config")
S3_BUCKET_NAME = general_config.get("s3_bucket", "swylie-astra")
MIND_FILE_JSON = general_config.get("mind_file", "mind_file.json")
MIND_FILE_ORIG = general_config.get("structured_mind_file", "mind_file_parents.json")

s3 = boto3.client("s3")

### ✅ **Debugging Enhancements in save_to_s3()**
def save_to_s3(mind_data):
    """Save mind file to S3 using proper encoding and error handling."""
    try:
        # 🔍 Debug: Log stored knowledge before saving
        print(f"📝 [DEBUG] Pre-Save Knowledge Count: {len(mind_data['stored_knowledge'])}")
        print(f"📝 [DEBUG] Sample Knowledge Before Save: {mind_data['stored_knowledge'][:5]}")

        mind_file_json = json.dumps(mind_data, indent=4, ensure_ascii=False)
        s3.put_object(Bucket=S3_BUCKET_NAME, Key=MIND_FILE_JSON, Body=mind_file_json.encode("utf-8"))

        print(f"✅ Mind file saved to S3 successfully! Reflections: {len(mind_data['self_reflections'])}, "
              f"Questions: {len(mind_data['self_questions'])}, Knowledge: {len(mind_data['stored_knowledge'])}")
    except Exception as e:
        print(f"🚨 [ERROR] Failed to save mind file to S3: {e}")

### ✅ **Fix: Restore Missing Knowledge in save_mind()**
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

    latest_mind_data = load_mind()
    if latest_mind_data and len(latest_mind_data.get("stored_knowledge", [])) > len(mind_data["stored_knowledge"]):
        print(f"⚠ WARNING: The latest mind file has **MORE** knowledge ({len(latest_mind_data['stored_knowledge'])}) than what we're saving ({len(mind_data['stored_knowledge'])})!")
        print("⚠ Preventing save to avoid overwriting newer data.")
        return  

    save_to_s3(mind_data)

    reloaded_mind_data = load_mind()
    if not reloaded_mind_data:
        print("🚨 [ERROR] Failed to reload mind file after saving! Preventing overwrite.")
        return
    
    if len(reloaded_mind_data["stored_knowledge"]) < len(mind_data["stored_knowledge"]):
        print(f"🚨 [DEBUG] Data loss detected! Restoring missing knowledge.")
        lost_entries = set(mind_data["stored_knowledge"]) - set(reloaded_mind_data["stored_knowledge"])
        print(f"⚠ [DEBUG] Restoring {len(lost_entries)} lost knowledge entries.")
        mind_data["stored_knowledge"].extend(lost_entries)
        save_to_s3(mind_data)

### ✅ **Fix: Log Knowledge After Reload in load_mind()**
def load_mind():
    """Load Astra's mind file from S3 while ensuring memory is managed properly."""
    print("🔍 Debug: Loading mind file from S3...")

    local_mind_file = "/home/ubuntu/astra_reflections/mind_file.json"
    if os.path.exists(local_mind_file):
        print("⚠ Deleting local mind_file.json to prevent stale data usage!")
        os.remove(local_mind_file)

    try:
        response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=MIND_FILE_JSON)
        mind_data = json.load(io.BytesIO(response["Body"].read()))

        print(f"📝 [DEBUG] Post-Load Knowledge Count: {len(mind_data.get('stored_knowledge', []))}")
        print(f"📝 [DEBUG] Sample Knowledge After Load: {mind_data.get('stored_knowledge', [])[:5]}")

        if len(mind_data.get("stored_knowledge", [])) < 100:
            print(f"🚨 WARNING: Loaded knowledge count is abnormally low ({len(mind_data['stored_knowledge'])})! Reloading from S3...")
            time.sleep(1)
            response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=MIND_FILE_JSON)
            mind_data = json.load(io.BytesIO(response["Body"].read()))

            if len(mind_data.get("stored_knowledge", [])) < 100:
                print("🚨 CRITICAL: Knowledge count is STILL low after reload! Possible data loss detected.")

        return mind_data

    except (s3.exceptions.NoSuchKey, json.JSONDecodeError) as e:
        print(f"⚠ Warning: mind_file.json not found or corrupted in S3: {e}")
        return None

### ✅ **Restored: store_knowledge()**
def store_knowledge(mind_data, new_insight):
    """Ensure knowledge is stored while prioritizing Astra’s philosophy and marking questions as answered."""
    if mind_data is None:
        print("🚨 [ERROR] Memory unavailable. Skipping knowledge storage.")
        return  

    print(f"🧠 [DEBUG] Attempting to store knowledge: {new_insight[:100]}...")

    if new_insight in mind_data["stored_knowledge"]:
        print(f"⚠ [DEBUG] Insight already exists. Skipping: {new_insight[:100]}")
        return
    
    mind_data["stored_knowledge"].append(new_insight)
    save_mind(mind_data)
    print("📄 [DEBUG] Knowledge saved successfully!")

### ✅ **Restored: is_term_or_phrase()**
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
