from astra_core.knowledge import knowledge_manager  # ✅ Correct import
from astra_interfaces.influence import load_mind, save_mind
from astra_core.knowledge_manager import merge_knowledge
from utils.json_loader import load_json_file


MIND_FILE_ORIG = "mind_file_parents.json"

def merge_structured_knowledge():
    """Merge insights from structured data into Astra's memory safely without overwriting."""
    
    mind_data = load_mind()
    structured_data = load_json_file(MIND_FILE_ORIG, {"insights": []})

    print(f"🔍 Before merging, stored knowledge count: {len(mind_data['stored_knowledge'])}")

    if "insights" in structured_data:
        structured_knowledge = [entry["insight"] for entry in structured_data["insights"]]

        # ✅ Reload mind data before merging to prevent overwriting
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
        saved_mind_data = load_mind()
        print(f"🔍 After saving & reloading, stored knowledge count: {len(saved_mind_data['stored_knowledge'])}")

        if len(saved_mind_data['stored_knowledge']) < len(reloaded_mind_data['stored_knowledge']):
            print(f"⚠ WARNING: Knowledge loss detected after saving! Before: {len(reloaded_mind_data['stored_knowledge'])}, After: {len(saved_mind_data['stored_knowledge'])}")

    print(f"🔹 Knowledge merge complete! Total knowledge items: {len(saved_mind_data['stored_knowledge'])}")
    return saved_mind_data


# ✅ Run the function
merge_structured_knowledge()
