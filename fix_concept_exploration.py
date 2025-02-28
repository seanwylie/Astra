from astra_core.knowledge import knowledge_manager  # ✅ Correct import
from astra_interfaces.influence import load_mind, save_mind
from astra_core.knowledge_manager import merge_knowledge
from utils.json_loader import load_json_file


MIND_FILE_ORIG = "mind_file_parents.json"

def merge_structured_knowledge():
    """Merge insights from structured data into Astra's memory safely while exploring unknown concepts."""
    
    mind_data = load_mind()
    structured_data = load_json_file(MIND_FILE_ORIG, {"insights": []})

    if "insights" in structured_data:
        structured_knowledge = [entry["insight"] for entry in structured_data["insights"]]

        # ✅ Identify unknown concepts BEFORE merging knowledge
        unknown_concepts = knowledge_manager.extract_unknown_terms(" ".join(structured_knowledge), mind_data)
        print(f"🔍 Unknown concepts detected: {unknown_concepts}")

        # ✅ Retrieve external knowledge ONLY for truly unknown terms
        if unknown_concepts:
            mind_data = knowledge_manager.retrieve_external_knowledge(unknown_concepts, mind_data)

        # ✅ Merge structured knowledge **carefully**
        mind_data["stored_knowledge"] = merge_knowledge(mind_data["stored_knowledge"], structured_knowledge)

    print(f"🔹 Knowledge merge complete! Total knowledge items: {len(mind_data['stored_knowledge'])}")
    save_mind(mind_data)
    return mind_data

# ✅ Run the function
merge_structured_knowledge()


# ✅ Run the function
merge_structured_knowledge()
