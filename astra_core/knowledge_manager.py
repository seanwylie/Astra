import json
import sys
import os
from fuzzywuzzy import fuzz
from utils.json_loader import load_json_file
from astra_interfaces.influence import load_mind, save_mind

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

MIND_FILE_ORIG = "mind_file_parents.json"
print(f"\U0001F50D Debug: MIND_FILE_ORIG Path → {MIND_FILE_ORIG}")  # ✅ Debug print

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

    # 🚨 Save backup BEFORE merging
    with open("debug_before_merge.json", "w") as debug_file:
        json.dump(existing_knowledge, debug_file, indent=4)
        print(f"🔍 [DEBUG] Backup of knowledge BEFORE merging saved.")

    knowledge_list = list(existing_knowledge)
    knowledge_set = set(existing_knowledge)  

    initial_count = len(knowledge_list)

    for item in new_knowledge:
        decoded_item = safe_decode(item)

        # ✅ Reduce threshold to avoid aggressive filtering
        is_duplicate = any(fuzz.ratio(decoded_item.lower(), existing.lower()) > 98 for existing in knowledge_set)

        if is_duplicate:
            print(f"⚠ SKIPPED (potential false duplicate, fuzzy match >98%): {decoded_item}")
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

    if final_count < initial_count:
        print(f"⚠ WARNING: Knowledge count **decreased**, investigate merge logic!")

    return knowledge_list


def merge_structured_knowledge():
    """Merge insights from structured data into Astra's memory safely without overwriting stored knowledge."""

    mind_data = load_mind()
    structured_data = load_json_file(MIND_FILE_ORIG, {"insights": []})

    if not mind_data:
        print("🚨 [ERROR] Mind data is empty or failed to load! Aborting merge.")
        return None

    if "insights" in structured_data:
        structured_knowledge = set(entry["insight"] for entry in structured_data["insights"])
        existing_knowledge = set(mind_data.get("stored_knowledge", []))

        # ✅ Fix: Merge structured knowledge without replacing stored knowledge
        merged_knowledge = existing_knowledge.union(structured_knowledge)
        mind_data["stored_knowledge"] = list(merged_knowledge)

        print(f"🔍 Debug: Structured merge completed. Final stored knowledge count: {len(mind_data['stored_knowledge'])}")

        # ✅ Save merged data to prevent knowledge loss
        save_mind(mind_data)

        # 🚨 Verify that saved knowledge count matches expectations
        reloaded_data = load_mind()
        reloaded_count = len(reloaded_data.get("stored_knowledge", []))

        if reloaded_count < len(merged_knowledge):
            print(f"⚠ WARNING: Knowledge loss detected! Expected: {len(merged_knowledge)}, Reloaded: {reloaded_count}")

            # ✅ Restore lost knowledge
            save_mind(mind_data)
            print("✅ Restored lost knowledge after structured merge.")

            # 🔍 Double-check if the restoration was successful
            final_reloaded_data = load_mind()
            final_count = len(final_reloaded_data.get("stored_knowledge", []))
            print(f"🔍 Final stored knowledge count after restoration: {final_count}")

    return mind_data


# ✅ Prevent execution on import to avoid circular dependency issues
if __name__ == "__main__":
    merge_structured_knowledge()
