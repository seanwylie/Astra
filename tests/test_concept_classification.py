import sys
import os

# Add the project root to the Python path to resolve imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from astra_core.expansion import is_term_or_phrase

# ✅ Test cases for known terms and phrases
test_concepts = [
    "Singularity",                 # Should be TERM
    "Quantum computing",           # Should be TERM
    "The ethics of AI development", # Should be PHRASE
    "Deep learning",               # Should be TERM
    "The impact of automation on employment", # Should be PHRASE
    "Neural networks",             # Should be TERM
]

# ✅ Run classification for each concept
print("\n🔍 Concept Classification Test Results:")
for concept in test_concepts:
    classification = is_term_or_phrase(concept)
    print(f"🔹 {concept} → {classification.upper()}")
