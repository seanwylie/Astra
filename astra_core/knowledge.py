import requests
import re
import time
import random
from fuzzywuzzy import fuzz
from astra_core.config_loader import load_config
from astra_interfaces.influence import load_mind, save_mind  # ✅ Handles memory storage
from astra_core.config_loader import debug_log

class KnowledgeManager:
    COMMON_WORDS = {
        "the", "a", "and", "is", "in", "with", "to", "from", "for", "on", "as", "it",
        "by", "this", "of", "that", "which", "at", "does", "relate", "how", "what"
    }
    IGNORE_TERMS = {"deeper thought", "🔍 reflection", "🔍 deeper thought"}

    def __init__(self):
        """Initialize Astra's knowledge system with configurable lookup sources."""
        print("🔍 Debug: Loading knowledge settings...")
        self.config = load_config("lookup_config")
        debug_log("Loading")  
        self.mind_data = load_mind()  # ✅ Load Astra's memory
        self.mind_data.setdefault("past_conversations", [])  # ✅ Ensure past conversations are stored

        # ✅ Remove duplicates while keeping order
        seen = set()
        self.mind_data["stored_knowledge"] = [x for x in self.mind_data["stored_knowledge"] if not (x in seen or seen.add(x))]

        # ✅ Ensure proper memory structure
        if not isinstance(self.mind_data, dict):
            print("🚨 Warning: mind_data was corrupted! Resetting...")
            self.mind_data = {"self_reflections": [], "self_questions": [], "stored_knowledge": []}
        if "stored_knowledge" not in self.mind_data or not isinstance(self.mind_data["stored_knowledge"], list):
            print("🚨 Fixing `stored_knowledge`, ensuring it's a list!")
            self.mind_data["stored_knowledge"] = []
    def store_conversation(self, message):
        """Stores past conversations so Astra can reference them later."""
        self.mind_data["past_conversations"].append(message)

        # ✅ Keep only the last 100 interactions to prevent memory bloat
        self.mind_data["past_conversations"] = self.mind_data["past_conversations"][-100:]

        save_mind(self.mind_data)

    def should_lookup_concept(self, concept, force=False):
        """Determine if Astra should look up a concept based on meaningful stored knowledge."""
        concept_lower = concept.lower().strip()

        if force:
            print(f"⚠ Force lookup enabled for '{concept}', overriding existing checks.")
            return True  # ✅ Force lookup even if known

        if concept_lower in self.COMMON_WORDS or len(concept_lower) < 3:
            print(f"⚠ Ignoring '{concept}', too generic.")
            return False  # ✅ Skip looking up vague words

        # ✅ Check for existing definitions
        for entry in self.mind_data["stored_knowledge"]:
            if concept_lower in entry.lower() and len(entry.split()) > 5:
                return False  # ✅ Found meaningful knowledge, skip lookup

        # ✅ Fuzzy Matching (last resort, avoid false positives)
        for entry in self.mind_data["stored_knowledge"]:
            similarity = fuzz.partial_ratio(concept_lower, entry.lower())
            if similarity > 92:
                return False  # ✅ Found close match, skip lookup

        print(f"🔍 Concept '{concept}' not found in a meaningful form, proceeding with lookup.")
        return True  # 🔍 No explanation found, look it up

    def lookup_dictionary_definition(self, word):
        """Fetch definitions using the dictionary API."""
        clean_word = re.sub(r'[^\w\s]', '', word).strip()
        try:
            response = requests.get(f"{self.config['lookup_api']['dictionary']}{clean_word}")
            if response.status_code == 200:
                data = response.json()
                return f"🔹 {clean_word}: {data[0]['meanings'][0]['definitions'][0]['definition']}"
        except Exception as e:
            print(f"⚠ Dictionary lookup failed for '{clean_word}': {e}")
        return None

    def retrieve_external_knowledge(self, search_terms, force=False):
        """Fetch knowledge from external sources and update stored knowledge."""
        new_knowledge = []

        print(f"🔍 Debug: Attempting to retrieve knowledge for {search_terms}")

        for concept in search_terms:
            if not self.should_lookup_concept(concept, force=force):
                print(f"⚠ Skipping lookup for '{concept}', already known.")
                continue

            print(f"🔍 Looking up: {concept}")
            dictionary_info = self.lookup_dictionary_definition(concept)

            if dictionary_info:
                new_knowledge.append(f"📖 {concept}: {dictionary_info}")
                print(f"✅ Dictionary found: {dictionary_info}")

        # ✅ If no new knowledge was retrieved, exit early
        if not new_knowledge:
            print("❌ No new knowledge retrieved. Skipping save.")
            return False  

        # ✅ Step 1: Append new knowledge properly
        # ✅ Step 1: Avoid duplicates before appending
        pre_save_count = len(self.mind_data["stored_knowledge"])

        for entry in new_knowledge:
            if entry not in self.mind_data["stored_knowledge"]:  # ✅ Ensure it's unique
                self.mind_data["stored_knowledge"].append(entry)

        print(f"🔍 Debug: Before saving, knowledge count: {pre_save_count} -> {len(self.mind_data['stored_knowledge'])}")

        # ✅ Step 2: Save and immediately reload to verify
        save_mind(self.mind_data)
        time.sleep(0.5)  # ✅ Allow time for save to complete

        reloaded_mind = load_mind()
        self.mind_data["stored_knowledge"] = reloaded_mind["stored_knowledge"]

        return True  # ✅ Success

    def extract_unknown_terms(self, reflection):
        """Extract meaningful unknown concepts while filtering out noise."""
        
        print(f"🔍 Debug: Reflection Type: {type(reflection)}, Length: {len(reflection) if isinstance(reflection, str) else 'N/A'}")

        if isinstance(reflection, list):
            reflection = " ".join(reflection[-5:])  # ✅ Convert list to string

        if not isinstance(reflection, str):
            return []

        if len(reflection) > 5000:
            print(f"⚠ WARNING: Reflection is too long ({len(reflection)} chars)! Trimming...")
            reflection = reflection[:5000]

        # ✅ Extract potential unknown phrases (Proper Names, Key Concepts)
        phrase_pattern = r'\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        found_phrases = set(re.findall(phrase_pattern, reflection))
        
        # ✅ Extract individual words & filter common ones
        words = set(re.findall(r'\b\w+\b', reflection))
        filtered_words = {word.lower() for word in words if len(word) > 2 and word.lower() not in self.COMMON_WORDS}

        # ✅ Remove words that are already part of a larger phrase
        final_terms = (found_phrases | filtered_words) - self.IGNORE_TERMS
        unknown_terms = [term for term in final_terms if term not in self.mind_data["stored_knowledge"]]

        print(f"🔍 Debug: Final unknown concepts after filtering: {unknown_terms}")

        # ✅ External Lookup if unknowns exist
        if unknown_terms:
            print("🔍 Debug: Attempting external knowledge lookup...")
            if random.random() < 0.2:  # ✅ 20% chance to force lookup
                self.retrieve_external_knowledge(unknown_terms, force=True)
            else:
                self.retrieve_external_knowledge(unknown_terms)

            return []

        return unknown_terms

# ✅ Initialize knowledge manager instance
knowledge_manager = KnowledgeManager()
