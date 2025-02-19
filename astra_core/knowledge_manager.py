from utils.json_loader import load_json_file
from astra_core.mind_manager import load_mind, save_mind

MIND_FILE_ORIG = "mind_file_sean.json"

print(f"🔍 Debug: MIND_FILE_ORIG Path → {MIND_FILE_ORIG}")  # ✅ Debug print

def merge_knowledge(existing_knowledge, new_knowledge):
    """Merge new knowledge into existing knowledge without duplication."""
    print(f"🔍 Before merge: {len(existing_knowledge)} stored knowledge items.")
    knowledge_set = set(existing_knowledge)
    initial_count = len(knowledge_set)

    for item in new_knowledge:
        if item not in knowledge_set:
            knowledge_set.add(item)
            print(f"➕ Added new knowledge: {item}")
        else:
            print(f"⚠️ Duplicate knowledge not added: {item}")

    final_count = len(knowledge_set)
    print(f"🔹 Merging complete! {final_count - initial_count} new items added. Final stored knowledge count: {final_count}")
    return list(knowledge_set)


def merge_structured_knowledge():
    """Merge insights from structured data into Astra's memory."""
    mind_data = load_mind()
    structured_data = load_json_file(MIND_FILE_ORIG, {"insights": []})
    
    if "insights" in structured_data:
        structured_knowledge = [entry["insight"] for entry in structured_data["insights"]]
        mind_data["stored_knowledge"].extend([entry for entry in structured_knowledge if entry not in mind_data["stored_knowledge"]])

    print(f"🔹 Knowledge merge complete! Total knowledge items: {len(mind_data['stored_knowledge'])}")
 
    save_mind(mind_data)
    return mind_data

