import requests
import re
from fuzzywuzzy import fuzz
from astra_core.config_loader import load_config
from astra_interfaces.influence import load_mind, save_mind  # ✅ Handles memory storage

class KnowledgeManager:
    def __init__(self):
        """Initialize Astra's knowledge system with configurable lookup sources."""
        print("🔍 Debug: Loading knowledge settings...")
        self.config = load_config("lookup_config")

        self.mind_data = load_mind()  # ✅ Load Astra's memory
        if not isinstance(self.mind_data, dict):
            print("🚨 Warning: mind_data was corrupted! Resetting...")
            self.mind_data = {"self_reflections": [], "self_questions": [], "stored_knowledge": []}
        if "stored_knowledge" not in self.mind_data or not isinstance(self.mind_data["stored_knowledge"], list):
            print("🚨 Fixing `stored_knowledge`, ensuring it's a list!")
            self.mind_data["stored_knowledge"] = []

    def should_lookup_concept(self, concept):
        """Determine if Astra should look up a concept based on meaningful stored knowledge."""
        concept_lower = concept.lower()

        # ✅ Ensure we only check *actual definitions*, not just any mention
        existing_definitions = [
            entry for entry in self.mind_data["stored_knowledge"]
            if entry.lower().startswith(f"📖 {concept_lower}:") or entry.lower().startswith(f"📄 {concept_lower}:")
        ]

        return len(existing_definitions) == 0  # ✅ Only skip lookup if a proper definition exists




    def lookup_dictionary_definition(self, word):
        """Fetch definitions using the dictionary API."""
        clean_word = re.sub(r'[^\w\s]', '', word).strip()
        try:
            response = requests.get(f"{self.config['lookup_api']['dictionary']}{clean_word}")
            if response.status_code == 200:
                data = response.json()
                definitions = [entry["meanings"][0]["definitions"][0]["definition"] for entry in data]
                return f"🔹 {clean_word}: {definitions[0]}"
        except Exception as e:
            print(f"⚠ Dictionary lookup failed for '{clean_word}': {e}")
        return None

    def fetch_wikipedia_summary(self, concept):
        """Fetch a summary from Wikipedia's REST API."""
        try:
            response = requests.get(f"{self.config['lookup_api']['wikipedia_rest']}{concept}")
            if response.status_code == 200:
                data = response.json()
                return data.get("extract", "No summary available.")
        except Exception as e:
            print(f"⚠ Wikipedia lookup failed for '{concept}': {e}")
        return None

    def retrieve_external_knowledge(self, search_terms):
        """Fetch knowledge from external sources and update stored knowledge *before* generating new questions."""
        new_knowledge = []
        retrieved_anything = False  # ✅ Track whether anything was found

        print(f"🔍 Debug: Attempting to retrieve knowledge for {search_terms}")

        for concept in search_terms:
            if not self.should_lookup_concept(concept):
                print(f"⚠ Skipping lookup for '{concept}', already known.")
                continue
            
            print(f"🔍 Looking up: {concept}")
            dictionary_info = self.lookup_dictionary_definition(concept)
            wiki_info = self.fetch_wikipedia_summary(concept)

            if dictionary_info:
                new_knowledge.append(f"📖 {concept}: {dictionary_info}")
                print(f"✅ Dictionary found: {dictionary_info}")
            elif wiki_info:
                new_knowledge.append(f"📄 {concept}: {wiki_info}")
                print(f"✅ Wikipedia found: {wiki_info}")
            else:
                print(f"⚠ No external info found for '{concept}'.")

        print(f"🔍 Debug: Retrieved new knowledge: {new_knowledge}")

        if new_knowledge:
            retrieved_anything = True

            # ✅ Ensure knowledge is added BEFORE saving
            pre_save_count = len(self.mind_data["stored_knowledge"])
            self.mind_data["stored_knowledge"].extend(new_knowledge)

            print(f"🔍 Debug: Before saving, knowledge count: {pre_save_count} -> {len(self.mind_data['stored_knowledge'])}")

            save_mind(self.mind_data)

            # ✅ Immediately reload to check if it was actually saved
            reloaded_mind = load_mind()
            post_save_count = len(reloaded_mind["stored_knowledge"])

            print(f"🔍 Debug: After reloading, knowledge count: {post_save_count}")

            if post_save_count < len(self.mind_data["stored_knowledge"]):
                print("🚨 WARNING: Knowledge lost between saving and reloading!")

        return retrieved_anything


    def extract_unknown_terms(self, reflection):
        """Extract potential unknown concepts and force an external lookup *before* generating more self-questions."""
        known_terms = set(self.mind_data.get("stored_knowledge", []))  # ✅ Use a set for fast lookup

        phrase_pattern = r'\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        found_phrases = re.findall(phrase_pattern, reflection)

        words = re.findall(r'\b\w+\b', reflection)
        found_words = [word.lower() for word in words if len(word) > 2]

        filtered_words = [word for word in found_words if not any(phrase.lower().startswith(word) for phrase in found_phrases)]

        all_terms = set(found_phrases + filtered_words)
        unknown_terms = [term for term in all_terms if term not in known_terms]

        print(f"🔍 Final unknown concepts after filtering: {unknown_terms}")

        if unknown_terms:
            found_new_knowledge = self.retrieve_external_knowledge(unknown_terms)

            # ✅ If new knowledge was found, return empty (no need for self-questions)
            if found_new_knowledge:
                print(f"✅ External knowledge retrieved, skipping question generation.")
                return []

        return unknown_terms  # ✅ If nothing was found, allow question generation




# ✅ Initialize knowledge manager instance
knowledge_manager = KnowledgeManager()
