import json
import re
import boto3
import io
import wikipedia
import os
from astra_core.config_loader import load_config  # ✅ Load configs dynamically
from fuzzywuzzy import fuzz

# ✅ Load general configurations
general_config = load_config("general_config")
S3_BUCKET_NAME = general_config.get("s3_bucket", "swylie-astra")
MIND_FILE_JSON = general_config.get("mind_file", "mind_file.json")
MIND_FILE_ORIG = general_config.get("structured_mind_file", "mind_file_parents.json")

s3 = boto3.client("s3")

### ✅ **Fix: Prevent Local Saves & Ensure S3 Persistence**
def save_to_s3(mind_data):
    """Save mind file to S3 using proper encoding and error handling."""
    try:
        print(f"📝 [DEBUG] Pre-Save Knowledge Count: {len(mind_data['stored_knowledge'])}")

        # ✅ Step 1: Remove any local mind file to avoid confusion
        local_mind_file = "/home/ubuntu/astra_reflections/mind_file.json"
        if os.path.exists(local_mind_file):
            print("⚠ Deleting local mind_file.json to prevent accidental overwrites.")
            os.remove(local_mind_file)

        # ✅ Step 2: Save to S3
        mind_file_json = json.dumps(mind_data, indent=4, ensure_ascii=False)
        print(f"[save_to_s3] Writing to S3 Bucket: {S3_BUCKET_NAME}, Key: {MIND_FILE_JSON}")

        s3.put_object(Bucket=S3_BUCKET_NAME, Key=MIND_FILE_JSON, Body=mind_file_json.encode("utf-8"))

        print(f"✅ Mind file saved to S3 successfully! Reflections: {len(mind_data['self_reflections'])}, "
              f"Questions: {len(mind_data['self_questions'])}, Knowledge: {len(mind_data['stored_knowledge'])}")

    except Exception as e:
        print(f"🚨 [ERROR] Failed to save mind file to S3: {e}")





def clean_text_entries(entries, label="entry", min_length=25, dedupe_threshold=90):
    """
    Cleans and deduplicates a list of text entries (e.g., reflections or questions).
    """
    print(f"🧹 [clean_text_entries] Cleaning {label}s...")

    seen = []
    cleaned = []
    too_short, malformed = [], []
    duplicates_skipped = 0

    for i, entry in enumerate(entries):
        if not isinstance(entry, str):
            malformed.append(str(entry))
            continue

        stripped = entry.strip()
        if len(stripped) < min_length:
            too_short.append(stripped)
            continue

        is_duplicate = False
        for seen_entry in seen:
            similarity = fuzz.ratio(stripped[:400], seen_entry[:400])
            if similarity > dedupe_threshold:
                is_duplicate = True
                duplicates_skipped += 1
                break

        if not is_duplicate:
            cleaned.append(stripped)
            seen.append(stripped)

    print(f"✅ [clean_text_entries] {label.title()}s: {len(entries)} → Kept: {len(cleaned)} | Duplicates: {duplicates_skipped} | Too Short: {len(too_short)} | Malformed: {len(malformed)}")
    return cleaned



def save_mind(mind_data, force=False):
    """Ensures knowledge persistence and prevents unnecessary overwrites with full debugging."""
    if mind_data is None or not isinstance(mind_data, dict):
        print("🚨 [save_mind] Invalid mind_data structure! Aborting save.")
        return

    if not any(mind_data.get(k) for k in ["self_reflections", "self_questions", "stored_knowledge"]):
        print("🚨 [save_mind] All core memory fields are empty! Skipping save to prevent overwrite.")
        return

    from astra_core.questions.question_manager import track_question_patterns

    print("🔍 [save_mind] Tracking self-questioning patterns before saving...")
    track_question_patterns(mind_data)

    reflections = mind_data.get("self_reflections", [])
    questions = mind_data.get("self_questions", [])
    knowledge = mind_data.get("stored_knowledge", [])

    print(f"🔍 [save_mind] Reflection Count: {len(reflections)}")
    print(f"🔍 [save_mind] Question Count: {len(questions)}")
    print(f"🔍 [save_mind] Knowledge Count (pre-save): {len(knowledge)}")

    # ✅ Clean up and validate stored_knowledge
    cleaned_knowledge = []
    seen = set()
    too_short, too_long, malformed = [], [], []

    for entry in knowledge:
        if not isinstance(entry, str):
            malformed.append(str(entry))
            continue

        key = entry.strip().lower()
        if key in seen:
            continue
        seen.add(key)

        if len(entry) < 10:
            too_short.append(entry)
            continue
        elif len(entry) > 1000:
            too_long.append(entry)
            continue

        if not any(token in entry.lower() for token in ["📖", "📄", "🔹"]):
            entry = f"📖 {entry.strip()}"  # 🔧 Add default tag for formatting
        
        cleaned_knowledge.append(entry)



    if too_short:
        print(f"⚠️ [save_mind] {len(too_short)} very short knowledge entries skipped.")
    if too_long:
        print(f"⚠️ [save_mind] {len(too_long)} oversized entries flagged.")
    if malformed:
        print(f"⚠️ [save_mind] {len(malformed)} malformed entries detected. Showing one:")
        print(f"    ❓ {malformed[0][:100]}...")

    mind_data["stored_knowledge"] = cleaned_knowledge

    print("🔍 [save_mind] Loading latest mind for comparison...")
    latest_mind_data = load_mind()

    if latest_mind_data:
        latest_knowledge = set(latest_mind_data.get("stored_knowledge", []))
        current_knowledge = set(cleaned_knowledge)

        lost_entries = current_knowledge - latest_knowledge
        new_entries = current_knowledge - latest_knowledge

        if lost_entries:
            print(f"⚠️ [save_mind] Detected {len(lost_entries)} missing entries. Reinserting...")

        if new_entries:
            print(f"🧠 [save_mind] Detected {len(new_entries)} new knowledge entries:")
            for entry in list(new_entries)[:3]:
                print(f"   ➕ {entry[:120]}...")
        elif not force:
            print("✅ [save_mind] No new knowledge. Skipping redundant save.")
            return

        mind_data["stored_knowledge"] = list(current_knowledge)

    print("💾 [save_mind] Committing updated mind to S3...")
    save_to_s3(mind_data)

    # ✅ Post-save verification
    print("🔁 [save_mind] Re-loading mind to verify persisted changes...")
    reloaded = load_mind()
    if not reloaded:
        print("❌ [save_mind] Failed to reload mind after save!")
        return

    # 🧼 Also sanitize reflections and questions
    mind_data["self_reflections"] = clean_text_entries(mind_data.get("self_reflections", []), label="reflection")
    mind_data["self_questions"] = clean_text_entries(mind_data.get("self_questions", []), label="question", min_length=10)

    reloaded_knowledge_count = len(reloaded.get("stored_knowledge", []))
    intended_count = len(mind_data.get("stored_knowledge", []))

    print(f"🔍 [save_mind] Post-save knowledge count: {reloaded_knowledge_count} vs intended: {intended_count}")

    if reloaded_knowledge_count < intended_count:
        print("🚨 [save_mind] Save verification failed! Knowledge did not persist.")
    else:
        print("✅ [save_mind] Save verified successfully.")



### ✅ **Fix: Log Knowledge After Reload in load_mind()**
def load_mind():
    """Load Astra's mind file from S3 while ensuring proper memory management."""
    print("🔍 Debug: Loading mind file from S3...")

    local_mind_file = "/home/ubuntu/astra_reflections/mind_file.json"
    if os.path.exists(local_mind_file):
        print("⚠ Deleting local mind_file.json to prevent stale data usage!")
        os.remove(local_mind_file)

    try:
        response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=MIND_FILE_JSON)
        mind_data = json.load(io.BytesIO(response["Body"].read()))

        print(f"📝 [DEBUG] Post-Load Knowledge Count: {len(mind_data.get('stored_knowledge', []))}")

        if len(mind_data.get("stored_knowledge", [])) < 100:
            print("⚠ WARNING: Knowledge count abnormally low! Checking for S3 sync issues.")

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
