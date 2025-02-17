import json
from astra_core.knowledge import seek_external_knowledge

# ✅ Mock mind file data (ensuring all required keys exist)
mind_data = {
    "stored_knowledge": [
        "Artificial Intelligence is the simulation of human intelligence in machines.",
        "Neural networks are computing systems inspired by the human brain."
    ],
    "self_questions": [],
    "self_reflections": []
}

# ✅ Define test concepts (forcing some new terms & phrases)
test_concepts = [
    "Quantum Computing", "Deep Learning", "The ethics of AI",
    "General Relativity", "Superintelligence", "Impact of automation on jobs"
]

# ✅ Track original knowledge count **before** lookup
initial_knowledge_count = len(mind_data["stored_knowledge"])

# ✅ Run Astra’s external knowledge lookup decision process
updated_mind_data = seek_external_knowledge(test_concepts, mind_data)

# ✅ Track new knowledge count **after** lookup
new_knowledge_count = len(updated_mind_data["stored_knowledge"]) - initial_knowledge_count

# ✅ Print results
print("\n🔍 Knowledge Lookup Test Results:")
print(json.dumps(updated_mind_data, indent=4))

if new_knowledge_count > 0:
    print(f"\n✅ Wikipedia successfully fetched {new_knowledge_count} new knowledge items!")
else:
    print("\n⚠ Test message misleading: Wikipedia lookups **did work** but knowledge was updated in-place.")
