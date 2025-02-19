from utils.json_loader import load_json_file
from astra_core.mind_manager import load_mind, save_mind

MIND_FILE_ORIG = "mind_file_sean.json"

print(f"🔍 Debug: MIND_FILE_ORIG Path → {MIND_FILE_ORIG}")  # ✅ Debug print

def merge_knowledge(existing_knowledge, new_knowledge):
    """Merge Astra's structured knowledge dynamically."""
    return list(set(existing_knowledge).union(set(new_knowledge)))

def merge_structured_knowledge():
    """Merge insights from structured data into Astra's memory."""
    mind_data = load_mind()
    structured_data = load_json_file(MIND_FILE_ORIG, {"insights": []})
    
    if "insights" in structured_data:
        structured_knowledge = [entry["insight"] for entry in structured_data["insights"]]
        mind_data["stored_knowledge"] = merge_knowledge(mind_data["stored_knowledge"], structured_knowledge)

    print(f"🔹 Knowledge merge complete! Total knowledge items: {len(mind_data['stored_knowledge'])}")
    save_mind(mind_data)
    return mind_data
