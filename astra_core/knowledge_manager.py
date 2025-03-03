import json
import sys
import os
from fuzzywuzzy import fuzz
from utils.json_loader import load_json_file
from astra_interfaces.influence import load_mind, save_mind, save_to_s3

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
        return existing_knowledge

    # ✅ Preserve original knowledge
    knowledge_list = list(existing_knowledge)
    knowledge_set = set(existing_knowledge)

    for item in new_knowledge:
        decoded_item = safe_decode(item)

        # ✅ **Protect dictionary entries** if they contain detailed information
        is_dict_entry = decoded_item.startswith("📖") or ":" in decoded_item[:20]
        if is_dict_entry and len(decoded_item.split()) <= 5:  # 🚀 Only remove very short definitions
            print(f"⚠ SKIPPED (Trivial Dictionary Entry): {decoded_item}")
            continue

        # ✅ **Only remove near-duplicates if similarity is extremely high (>97%)**
        is_duplicate = any(fuzz.ratio(decoded_item.lower(), existing.lower()) > 97 for existing in knowledge_set)

        if is_duplicate:
            print(f"⚠ SKIPPED (Potential duplicate, fuzzy match >97%): {decoded_item}")
        else:
            knowledge_list.append(decoded_item)
            knowledge_set.add(decoded_item)
            print(f"➕ Added new knowledge: {decoded_item}")

    final_count = len(knowledge_list)
    print(f"🔍 After merging, stored knowledge count: {final_count}")

    return knowledge_list



def merge_structured_knowledge():
    """Merge insights from structured data into Astra's memory safely without overwriting."""
    
    mind_data = load_mind()  # ✅ Load once before merging
    structured_data = load_json_file(MIND_FILE_ORIG, {"insights": []})

    print(f"🔍 Before merging, stored knowledge count: {len(mind_data['stored_knowledge'])}")

    if "insights" in structured_data:
        structured_knowledge = [entry["insight"] for entry in structured_data["insights"]]

        # ✅ Log each new knowledge entry before merging
        print("🔍 **All Incoming Structured Knowledge:**")
        for insight in structured_knowledge:
            print(f"➕ {insight}")

        # ✅ Merge knowledge (no second `load_mind()` call needed)
        merged_knowledge = merge_knowledge(mind_data["stored_knowledge"], structured_knowledge)

        # ✅ Keep ALL previous knowledge while adding structured knowledge
        mind_data["stored_knowledge"] = list(dict.fromkeys(mind_data["stored_knowledge"] + merged_knowledge))  # 🚀 Preserve order while removing duplicates

        # ✅ Ensure reflections are also saved properly
        if "self_reflections" in mind_data:
            print(f"🔍 Debug: Reflections count before saving: {len(mind_data['self_reflections'])}")
        else:
            print("⚠ WARNING: Reflections key missing in mind_data!")

        save_to_s3(mind_data)  # ✅ Save updated knowledge

        print(f"🔍 After saving, stored knowledge count: {len(mind_data['stored_knowledge'])}")

    print(f"🔹 Knowledge merge complete! Total knowledge items: {len(mind_data['stored_knowledge'])}")
    return mind_data


# ✅ Prevent execution on import to avoid circular dependency issues
if __name__ == "__main__":
    merge_structured_knowledge()
