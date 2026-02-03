import json
import re
import boto3
import aioboto3
import io
import wikipedia
import os
from app.config.loader import load_config
from fuzzywuzzy import fuzz
from app.logging_config import get_logger


# ✅ Load general configurations
general_config = load_config("general_config")
S3_BUCKET_NAME = general_config.get("s3_bucket", "swylie-astra")
MIND_FILE_JSON = general_config.get("mind_file", "mind_file.json")
MIND_FILE_ORIG = general_config.get("structured_mind_file", "mind_file_parents.json")

# Legacy sync client
s3 = boto3.client("s3")

logger = get_logger("interfaces.influence")


# === NEW: Async Mind Load ===
async def load_mind_async():
    """Asynchronously load the mind file from S3."""
    logger.debug("🔍 [async] Loading mind file from S3...")
    async with aioboto3.client("s3") as s3_async:
        response = await s3_async.get_object(Bucket=S3_BUCKET_NAME, Key=MIND_FILE_JSON)
        body = await response["Body"].read()
        mind_data = json.loads(body)
        logger.debug("📝 [async] Post-Load Knowledge Count: %s", len(mind_data.get("stored_knowledge", [])))
        return mind_data


# === NEW: Async Save ===
async def save_mind_async(data):
    """Asynchronously save the mind file to S3."""
    logger.debug("💾 [async] Saving mind to S3. Reflections: %s", len(data.get("self_reflections", [])))
    async with aioboto3.client("s3") as s3_async:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        await s3_async.put_object(Bucket=S3_BUCKET_NAME, Key=MIND_FILE_JSON, Body=payload)
    logger.debug("✅ [async] Mind saved to S3.")


def save_to_s3(mind_data):
    """Save mind file to S3 using proper encoding and error handling."""
    try:
        logger.debug("📝 [save_to_s3] Pre-Save Knowledge Count: %s", len(mind_data.get("stored_knowledge", [])))
        local_mind_file = "/home/sean/dev/systems/Astra/mind_file.json"
        if os.path.exists(local_mind_file):
            logger.debug("⚠ Deleting local mind_file.json to prevent accidental overwrites.")
            os.remove(local_mind_file)

        mind_file_json = json.dumps(mind_data, indent=4, ensure_ascii=False)
        logger.debug("[save_to_s3] Writing to S3 Bucket: %s, Key: %s", S3_BUCKET_NAME, MIND_FILE_JSON)
        s3.put_object(Bucket=S3_BUCKET_NAME, Key=MIND_FILE_JSON, Body=mind_file_json.encode("utf-8"))

        logger.info(
            "✅ Mind file saved to S3 successfully! Reflections: %s, Questions: %s, Knowledge: %s",
            len(mind_data.get("self_reflections", [])),
            len(mind_data.get("self_questions", [])),
            len(mind_data.get("stored_knowledge", [])),
        )
    except Exception:
        logger.exception("🚨 [save_to_s3] Failed to save mind file to S3.")


def clean_text_entries(entries, label="entry", min_length=25, dedupe_threshold=90):
    logger.debug("🧹 [clean_text_entries] Cleaning %s entries...", label)
    seen = []
    cleaned = []
    too_short, malformed = [], []
    duplicates_skipped = 0

    for entry in entries:
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

    logger.debug(
        "✅ [clean_text_entries] %s: %s → Kept: %s | Duplicates: %s | Too Short: %s | Malformed: %s",
        label.title(),
        len(entries),
        len(cleaned),
        duplicates_skipped,
        len(too_short),
        len(malformed),
    )
    return cleaned


def clean_question_entries(entries, min_length=10, dedupe_threshold=85):
    """Normalize question dictionaries without discarding metadata."""
    logger.debug("🧹 [clean_question_entries] Cleaning %s question entries...", len(entries))
    cleaned = []
    seen = []
    duplicates_skipped = 0

    for entry in entries:
        if isinstance(entry, dict):
            text = entry.get("question", "")
            meta = entry
        elif isinstance(entry, str):
            text = entry
            meta = {"question": text}
        else:
            logger.debug("⚠️ [clean_question_entries] Skipping malformed question entry: %s", entry)
            continue

        normalized = (text or "").strip()
        if len(normalized) < min_length:
            continue

        is_duplicate = any(fuzz.ratio(normalized.lower(), existing.lower()) > dedupe_threshold for existing in seen)
        if is_duplicate:
            duplicates_skipped += 1
            continue

        new_entry = dict(meta)
        new_entry["question"] = normalized
        cleaned.append(new_entry)
        seen.append(normalized)

    logger.debug(
        "✅ [clean_question_entries] Questions: %s → Kept: %s | Duplicates: %s",
        len(entries),
        len(cleaned),
        duplicates_skipped,
    )
    return cleaned


def save_mind(mind_data, force=False):
    """Ensures knowledge persistence and prevents unnecessary overwrites with full debugging."""
    if mind_data is None or not isinstance(mind_data, dict):
        logger.error("🚨 [save_mind] Invalid mind_data structure! Aborting save.")
        return

    if not any(mind_data.get(k) for k in ["self_reflections", "self_questions", "stored_knowledge"]):
        logger.error("🚨 [save_mind] All core memory fields are empty! Skipping save to prevent overwrite.")
        return

    # 💡 Try tracking self-questioning patterns only if dependencies are present
    try:
        from app.core.questions.question_manager import track_question_patterns

        logger.debug("🔍 [save_mind] Tracking self-questioning patterns before saving...")
        track_question_patterns(mind_data)
    except ModuleNotFoundError:
        logger.warning("⚠️ [save_mind] Torch not installed — skipping question tracking.")
    except Exception:
        logger.exception("⚠️ [save_mind] Error while tracking question patterns.")

    reflections = mind_data.get("self_reflections", [])
    questions = mind_data.get("self_questions", [])
    knowledge = mind_data.get("stored_knowledge", [])

    logger.debug("🔍 [save_mind] Reflection Count: %s", len(reflections))
    logger.debug("🔍 [save_mind] Question Count: %s", len(questions))
    logger.debug("🔍 [save_mind] Knowledge Count (pre-save): %s", len(knowledge))

    def normalize_knowledge_entry(entry):
        """Standardize stored_knowledge entry to string (dict with 'insight' or raw string)."""
        if isinstance(entry, dict):
            return (entry.get("insight") or str(entry)).strip()
        if isinstance(entry, str):
            return entry.strip()
        return str(entry).strip()

    cleaned_knowledge = []
    seen = set()
    too_short, too_long, malformed = [], [], []

    for entry in knowledge:
        text = normalize_knowledge_entry(entry)
        if not text:
            malformed.append(str(entry)[:50])
            continue

        key = text.lower()[:500]
        if key in seen:
            continue
        seen.add(key)

        if len(text) < 10:
            too_short.append(text)
            continue
        if len(text) > 1000:
            text = text[:1000] + "..."
            too_long.append(text)

        if not any(token in text.lower() for token in ["📖", "📄", "🔹"]):
            text = f"📖 {text}"
        cleaned_knowledge.append(text)

    if too_short:
        logger.warning("⚠️ [save_mind] %s very short knowledge entries skipped.", len(too_short))
    if too_long:
        logger.debug("⚠️ [save_mind] %s oversized entries flagged.", len(too_long))
    if malformed:
        logger.warning("⚠️ [save_mind] %s malformed entries detected. Example: %s", len(malformed), malformed[0][:100])

    mind_data["stored_knowledge"] = cleaned_knowledge

    logger.debug("🔍 [save_mind] Loading latest mind for comparison...")
    latest_mind_data = load_mind()

    if latest_mind_data:
        latest_raw = latest_mind_data.get("stored_knowledge", [])
        latest_normalized = []
        for entry in latest_raw:
            normalized = normalize_knowledge_entry(entry)
            if normalized:
                latest_normalized.append(normalized)

        current_set = set(cleaned_knowledge)
        latest_set = set(latest_normalized)

        missing_entries = [entry for entry in latest_normalized if entry not in current_set]
        new_entries = [entry for entry in cleaned_knowledge if entry not in latest_set]

        if missing_entries:
            logger.warning("⚠️ [save_mind] Detected %s missing entries. Reinserting...", len(missing_entries))
            cleaned_knowledge.extend(missing_entries)
            current_set.update(missing_entries)

        if new_entries:
            logger.info("🧠 [save_mind] Detected %s new knowledge entries.", len(new_entries))
            for entry in new_entries[:3]:
                logger.debug("   ➕ %s", entry[:120])
        elif not missing_entries and not force:
            logger.debug("✅ [save_mind] No knowledge changes detected. Skipping redundant save.")
            return

        mind_data["stored_knowledge"] = cleaned_knowledge

    logger.debug("💾 [save_mind] Committing updated mind to S3...")
    save_to_s3(mind_data)

    logger.debug("🔁 [save_mind] Re-loading mind to verify persisted changes...")
    reloaded = load_mind()
    if not reloaded:
        logger.error("❌ [save_mind] Failed to reload mind after save!")
        return

    mind_data["self_reflections"] = clean_text_entries(mind_data.get("self_reflections", []), label="reflection")
    # Questions are dicts; must use clean_question_entries (dict-safe), not clean_text_entries
    mind_data["self_questions"] = clean_question_entries(mind_data.get("self_questions", []), min_length=10)

    reloaded_knowledge_count = len(reloaded.get("stored_knowledge", []))
    intended_count = len(mind_data.get("stored_knowledge", []))

    logger.debug(
        "🔍 [save_mind] Post-save knowledge count: %s vs intended: %s",
        reloaded_knowledge_count,
        intended_count,
    )

    if reloaded_knowledge_count < intended_count:
        logger.error("🚨 [save_mind] Save verification failed! Knowledge did not persist.")
    else:
        logger.debug("✅ [save_mind] Save verified successfully.")


def load_mind():
    """Load Astra's mind file from S3 while ensuring proper memory management."""
    logger.debug("🔍 Debug: Loading mind file from S3...")
    local_mind_file = "/home/sean/dev/systems/Astra/mind_file.json"
    if os.path.exists(local_mind_file):
        logger.debug("⚠ Deleting local mind_file.json to prevent stale data usage!")
        os.remove(local_mind_file)

    try:
        response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=MIND_FILE_JSON)
        mind_data = json.load(io.BytesIO(response["Body"].read()))
        logger.debug("📝 [DEBUG] Post-Load Knowledge Count: %s", len(mind_data.get("stored_knowledge", [])))
        if len(mind_data.get("stored_knowledge", [])) < 100:
            logger.warning("⚠ WARNING: Knowledge count abnormally low! Checking for S3 sync issues.")
        return mind_data
    except (s3.exceptions.NoSuchKey, json.JSONDecodeError) as e:
        logger.warning("⚠ Warning: mind_file.json not found or corrupted in S3: %s", e)
        return None


def is_term_or_phrase(concept):
    """Determine if a concept is a single term (Wikipedia) or a phrase (Google Search)."""
    clean_concept = re.sub(r"[^\w\s]", "", concept).strip()
    if not clean_concept:
        logger.warning("⚠ Ignoring malformed concept: '%s'", concept)
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
