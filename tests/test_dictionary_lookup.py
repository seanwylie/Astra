from astra_core.expansion import lookup_dictionary_definition

test_words = ["philosophy", "quantum", "automation", "deeper", "nonexistentword"]

print("\n🔍 Dictionary Lookup Test Results:")
for word in test_words:
    definition = lookup_dictionary_definition(word)
    if definition:
        print(f"✅ Found in dictionary: {definition}")
    else:
        print(f"⚠ '{word}' not found in dictionary.")
