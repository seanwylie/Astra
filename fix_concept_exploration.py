import json
import sys
import os
from fuzzywuzzy import fuzz
from utils.json_loader import load_json_file
from astra_interfaces.influence import load_mind, save_mind

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

MIND_FILE_ORIG = "mind_file_parents.json"
print(f"🔍 Debug: MIND_FILE_ORIG Path → {MIND_FILE_ORIG}")  # ✅ Debug print

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
        return existing_knowledge  # Avoid overwriting with an empty set

    # 🚨 Save backup BEFORE merging
    with open("debug_before_merge.json", "w") as debug_file:
        json.dump(existing_knowledge, debug_file, indent=4)
        print(f"🔍 [DEBUG] Backup of knowledge BEFORE merging saved.")

    knowledge_list = list(existing_knowledge)  # ✅ Preserve original knowledge
    knowledge_set = set(existing_knowledge)

    for item in new_knowledge:
        decoded_item = safe_decode(item)

        # ✅ Reduce duplicate threshold from 95% → 90%
        is_duplicate = any(fuzz.ratio(decoded_item.lower(), existing.lower()) > 90 for existing in knowledge_set)

        if is_duplicate:
            print(f"⚠ SKIPPED (potential false duplicate, fuzzy match >90%): {decoded_item}")
        else:
            knowledge_list.append(decoded_item)
            knowledge_set.add(decoded_item)
            print(f"➕ Added new knowledge: {decoded_item}")

    final_count = len(knowledge_list)

    # 🚨 Save backup AFTER merging
    with open("debug_after_merge.json", "w") as debug_file:
        json.dump(knowledge_list, debug_file, indent=4)
        print(f"🔍 [DEBUG] Backup of knowledge AFTER merging saved.")

    print(f"🔍 After merging, stored knowledge count: {final_count}")

    return knowledge_list  # ✅ Ensure updated knowledge is returned

def merge_structured_knowledge():
    """Merge insights from structured data into Astra's memory safely without overwriting."""
    debug_log("Loading")  
    mind_data = load_mind()
    structured_data = load_json_file(MIND_FILE_ORIG, {"insights": []})

    print(f"🔍 Before merging, stored knowledge count: {len(mind_data['stored_knowledge'])}")

    if "insights" in structured_data:
        structured_knowledge = [entry["insight"] for entry in structured_data["insights"]]

        # ✅ Reload mind data before merging to prevent overwriting
        debug_log("Loading")  
        reloaded_mind_data = load_mind()
        print(f"🔍 Reloaded mind data before merge. Stored Knowledge: {len(reloaded_mind_data['stored_knowledge'])}")

        # ✅ Log what structured knowledge is merging
        with open("debug_structured_knowledge.json", "w") as debug_file:
            json.dump(structured_knowledge, debug_file, indent=4)
        print(f"🔍 [DEBUG] Saved structured knowledge before merging.")

        # ✅ Append new knowledge instead of overwriting
        merged_knowledge = merge_knowledge(reloaded_mind_data["stored_knowledge"], structured_knowledge)

        # 🚨 Compare what was lost (if anything)
        lost_knowledge = set(reloaded_mind_data["stored_knowledge"]) - set(merged_knowledge)
        if lost_knowledge:
            with open("debug_lost_knowledge.json", "w") as lost_file:
                json.dump(list(lost_knowledge), lost_file, indent=4)
            print(f"⚠ [WARNING] Knowledge loss detected! Lost items saved to debug_lost_knowledge.json")

        # ✅ Keep ALL previous knowledge while adding structured knowledge
        reloaded_mind_data["stored_knowledge"] = list(set(reloaded_mind_data["stored_knowledge"]).union(merged_knowledge))

        from astra_interfaces.influence import save_mind
        save_mind(reloaded_mind_data)

        # ✅ Reload after saving to verify persistence
        debug_log("Loading")  
        saved_mind_data = load_mind()
        print(f"🔍 After saving & reloading, stored knowledge count: {len(saved_mind_data['stored_knowledge'])}")

        if len(saved_mind_data['stored_knowledge']) < len(reloaded_mind_data['stored_knowledge']):
            print(f"⚠ WARNING: Knowledge loss detected after saving! Before: {len(reloaded_mind_data['stored_knowledge'])}, After: {len(saved_mind_data['stored_knowledge'])}")

    print(f"🔹 Knowledge merge complete! Total knowledge items: {len(saved_mind_data['stored_knowledge'])}")
    return saved_mind_data

# ✅ Prevent execution on import to avoid circular dependency issues
if __name__ == "__main__":
    merge_structured_knowledge()