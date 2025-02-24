import sys
import os

# Add the project root to the Python path to resolve imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from astra_core.expansion import lookup_dictionary_definition

test_words = ["philosophy", "quantum", "automation", "deeper", "nonexistentword"]

print("\n🔍 Dictionary Lookup Test Results:")
for word in test_words:
    definition = lookup_dictionary_definition(word)
    if definition:
        print(f"✅ Found in dictionary: {definition}")
    else:
        print(f"⚠ '{word}' not found in dictionary.")
