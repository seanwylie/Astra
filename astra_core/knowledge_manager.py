import json
from fuzzywuzzy import fuzz

from utils.json_loader import load_json_file
from astra_interfaces.influence import load_mind, save_mind

MIND_FILE_ORIG = "mind_file_parents.json"

print(f"🔍 Debug: MIND_FILE_ORIG Path → {MIND_FILE_ORIG}")  # ✅ Debug print


def safe_decode(text):
    """Ensure Unicode characters are properly decoded before storing."""
    try:
        return json.loads(f'"{text}"')  # Decodes Unicode safely
    except json.JSONDecodeError:
        return text  # If decoding fails, return the original text

def merge_knowledge(existing_knowledge, new_knowledge):
    """Merge new knowledge into existing knowledge with a safer approach."""
    
    print(f"🔍 Before merge: {len(existing_knowledge)} stored knowledge items.")
    
    knowledge_set = set(safe_decode(entry) for entry in existing_knowledge)  # Fix Unicode issues
    retained_entries = set(knowledge_set)  # Track knowledge entries before merging
    added_count = 0  # Track new additions
    
    for item in new_knowledge:
        decoded_item = safe_decode(item)

        # ✅ Check for near-duplicate entries using fuzzy matching
        is_duplicate = any(fuzz.ratio(decoded_item.lower(), existing.lower()) > 85 for existing in knowledge_set)

        if not is_duplicate and decoded_item not in knowledge_set:
            knowledge_set.add(decoded_item)
            added_count += 1
            print(f"➕ Added new knowledge: {decoded_item}")
        else:
            print(f"⚠️ Skipped near-duplicate knowledge: {decoded_item}")

    final_count = len(knowledge_set)
    
    # ✅ Track if any knowledge was lost (should not happen)
    lost_count = len(retained_entries - knowledge_set)
    if lost_count > 0:
        print(f"⚠ WARNING: {lost_count} knowledge entries disappeared! Investigate merge logic.")

    print(f"🔹 Merging complete! {added_count} new items added. Final stored knowledge count: {final_count}")
    return list(knowledge_set)



def merge_structured_knowledge():
    """Merge insights from structured data into Astra's memory safely."""
    mind_data = load_mind()
    structured_data = load_json_file(MIND_FILE_ORIG, {"insights": []})

    if "insights" in structured_data:
        structured_knowledge = [entry["insight"] for entry in structured_data["insights"]]

        # Use `merge_knowledge()` instead of blindly extending knowledge
        mind_data["stored_knowledge"] = merge_knowledge(mind_data["stored_knowledge"], structured_knowledge)

    print(f"🔹 Knowledge merge complete! Total knowledge items: {len(mind_data['stored_knowledge'])}")
    save_mind(mind_data)
    return mind_data


