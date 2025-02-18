import json
from astra_core.expansion import retrieve_external_knowledge

# ✅ Mock mind file data
mind_data = {
    "stored_knowledge": [
        "Astra is designed to be self-reflective, continuously evolving based on knowledge, experience, and ethical considerations."
    ]
}

# ✅ Define test search terms (one known, one unknown)
search_terms = ["Artificial Intelligence", "Quantum Computing"]

# ✅ Run Wikipedia lookup
new_knowledge = retrieve_external_knowledge(search_terms, mind_data)

# ✅ Store results
if new_knowledge:
    mind_data["stored_knowledge"].extend(new_knowledge)

# ✅ Print results
print("\n🔍 Wikipedia Lookup Test Results:")
print(json.dumps(mind_data, indent=4))
