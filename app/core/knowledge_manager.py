import json
import os
from collections import OrderedDict
from fuzzywuzzy import fuzz
from utils.json_loader import load_json_file
from app.interfaces.influence import load_mind, save_to_s3
from app.config.loader import debug_log
from app.interfaces.mind_session import session
from app.logging_config import get_logger

logger = get_logger(__name__)
MIND_FILE_ORIG = "mind_file_parents.json"

def safe_decode(text):
    """Ensure Unicode characters are properly decoded before storing."""
    try:
        return json.loads(f'"{text}"')  # Decodes Unicode safely
    except json.JSONDecodeError:
        return text  # If decoding fails, return the original text

def merge_knowledge(existing_knowledge, new_knowledge):
    """Merge new knowledge while preserving unique insights safely."""

    print(f"🔍 Debug: Incoming new knowledge items: {len(new_knowledge)}")
    print(f"🔍 Debug: Existing knowledge before merge: {len(existing_knowledge)}")

    if not new_knowledge:
        print("⚠ WARNING: No new knowledge provided for merging!")
        return existing_knowledge

    # ✅ Preserve original knowledge
    knowledge_list = list(existing_knowledge)
    knowledge_set = set(existing_knowledge)
    removed_items = []  # Track removed knowledge for debugging

    for item in new_knowledge:
        decoded_item = safe_decode(item)

        # ✅ **Protect dictionary entries** unless they are extremely short
        is_dict_entry = decoded_item.startswith("📖") or ":" in decoded_item[:20]
        if is_dict_entry and len(decoded_item.split()) <= 3:
            removed_items.append(f"⚠ SKIPPED (Trivial Dictionary Entry): {decoded_item}")
            continue

        # ✅ **Only remove near-duplicates if similarity is extremely high (>98%)**
        is_duplicate = any(fuzz.ratio(decoded_item.lower(), existing.lower()) > 98 for existing in knowledge_set)

        if is_duplicate:
            removed_items.append(f"⚠ SKIPPED (Potential duplicate, fuzzy match >98%): {decoded_item}")
        else:
            knowledge_list.append(decoded_item)
            knowledge_set.add(decoded_item)
            logger.debug("Added new knowledge: %s", decoded_item)

    if removed_items:
        logger.debug("Knowledge removed during filtering: %s", removed_items)

    final_count = len(knowledge_list)
    logger.debug("After merging, stored knowledge count: %s", final_count)

    return knowledge_list


def merge_structured_knowledge():
    """Merge insights from structured data into Astra's memory safely without overwriting."""
    debug_log("Loading")  
    mind_data = session.load()  # ✅ Load once before merging
    structured_data = load_json_file(MIND_FILE_ORIG, {"insights": []})

    logger.debug("Before merging, stored knowledge count: %s", len(mind_data["stored_knowledge"]))

    if "insights" in structured_data:
        structured_knowledge = [entry["insight"] for entry in structured_data["insights"]]
        logger.debug("All incoming structured knowledge: %s", structured_knowledge)
        logger.debug("Before merging, knowledge count: %s", len(mind_data["stored_knowledge"]))

        merged_knowledge = merge_knowledge(mind_data["stored_knowledge"], structured_knowledge)
        logger.debug("After merging, stored knowledge count: %s", len(mind_data["stored_knowledge"]))


        # ✅ Keep ALL previous knowledge while adding structured knowledge
        # ✅ Preserve order while removing duplicates
        mind_data["stored_knowledge"] = list(OrderedDict.fromkeys(mind_data["stored_knowledge"] + merged_knowledge))


        if "self_reflections" in mind_data:
            logger.debug("Reflections count before saving: %s", len(mind_data["self_reflections"]))
        else:
            logger.warning("Reflections key missing in mind_data.")

        logger.debug("Before saving, knowledge count: %s", len(mind_data["stored_knowledge"]))
        save_to_s3(mind_data)
        logger.debug("After saving, stored knowledge count: %s", len(mind_data["stored_knowledge"]))

    logger.debug("Knowledge merge complete. Total knowledge items: %s", len(mind_data["stored_knowledge"]))
    return mind_data


# ✅ Prevent execution on import to avoid circular dependency issues
if __name__ == "__main__":
    merge_structured_knowledge()
