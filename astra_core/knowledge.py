import requests
import re
import time
from fuzzywuzzy import fuzz
from astra_core.config_loader import load_config
from astra_interfaces.influence import load_mind, save_mind  # ✅ Handles memory storage
from astra_core.config_loader import debug_log

class KnowledgeManager:
    def __init__(self):
        """Initialize Astra's knowledge system with configurable lookup sources."""
        print("🔍 Debug: Loading knowledge settings...")
        self.config = load_config("lookup_config")
        debug_log("Loading")  
        self.mind_data = load_mind()  # ✅ Load Astra's memory
        if not isinstance(self.mind_data, dict):
            print("🚨 Warning: mind_data was corrupted! Resetting...")
            self.mind_data = {"self_reflections": [], "self_questions": [], "stored_knowledge": []}
        if "stored_knowledge" not in self.mind_data or not isinstance(self.mind_data["stored_knowledge"], list):
            print("🚨 Fixing `stored_knowledge`, ensuring it's a list!")
            self.mind_data["stored_knowledge"] = []

    def should_lookup_concept(self, concept, force=False):
        """Determine if Astra should look up a concept based on meaningful stored knowledge."""
        if force:
            print(f"⚠ Force lookup enabled for '{concept}', overriding existing checks.")
            return True  # ✅ Force lookup even if known

        concept_lower = concept.lower()

        # ✅ Check for formal definitions first (📖 or 📄)
        existing_definitions = [
            entry for entry in self.mind_data["stored_knowledge"]
            if entry.lower().startswith(f"📖 {concept_lower}:") or entry.lower().startswith(f"📄 {concept_lower}:")
        ]
        
        if existing_definitions:
            print(f"✅ Skipping lookup: Found structured definition for '{concept}'")
            return False  # ✅ Proper definition exists, no need to look it up

        # ✅ Check if the concept is mentioned in stored knowledge in an *explanatory* way
        for entry in self.mind_data["stored_knowledge"]:
            if concept_lower in entry.lower():
                if ":" in entry[:40] or len(entry.split()) > 10:
                    print(f"✅ Skipping lookup: '{concept}' appears in a meaningful knowledge entry.")
                    return False  # ✅ Found an explanation, so skip lookup

        # ✅ Use fuzzy matching as a last check for similar explanations
        for entry in self.mind_data["stored_knowledge"]:
            similarity = fuzz.partial_ratio(concept_lower, entry.lower())
            if similarity > 90:
                print(f"✅ Skipping lookup: Found related explanation '{entry}' (similarity: {similarity}%)")
                return False  # ✅ A related concept is well explained

        print(f"🔍 Concept '{concept}' not found in an explained form, proceeding with lookup")
        return True  # 🔍 No explanation found, look it up

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

    def retrieve_external_knowledge(self, search_terms, force=False):
        """Fetch knowledge from external sources and update stored knowledge."""
        new_knowledge = []
        retrieved_anything = False

        print(f"🔍 Debug: Attempting to retrieve knowledge for {search_terms}")

        for concept in search_terms:
            if not self.should_lookup_concept(concept, force=force):
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
            pre_save_count = len(self.mind_data["stored_knowledge"])
            self.mind_data["stored_knowledge"].extend(new_knowledge)

            print(f"🔍 Debug: Before saving, knowledge count: {pre_save_count} -> {len(self.mind_data['stored_knowledge'])}")

            save_mind(self.mind_data)
            time.sleep(0.5)

            debug_log("Loading")  
            reloaded_mind = load_mind()

            print(f"🔍 After reloading, stored knowledge count: {len(reloaded_mind['stored_knowledge'])}")

            post_save_count = len(reloaded_mind["stored_knowledge"])

            print(f"🔍 Debug: After first reload, knowledge count: {post_save_count}")

            if post_save_count < len(self.mind_data["stored_knowledge"]):
                print("🚨 WARNING: Knowledge count mismatch! Reloading again to verify data integrity.")
                time.sleep(0.5)
                reloaded_mind = load_mind()
                post_save_count = len(reloaded_mind["stored_knowledge"])
                print(f"🔍 Debug: After second reload, knowledge count: {post_save_count}")

            self.mind_data["stored_knowledge"] = reloaded_mind["stored_knowledge"]
            print(f"new knowledge {new_knowledge}")

        return retrieved_anything

    def extract_unknown_terms(self, reflection):
        """Extract potential unknown concepts and force an external lookup *before* generating more self-questions."""
        known_terms = set(self.mind_data.get("stored_knowledge", []))  # ✅ Use a set for fast lookup

        # ✅ Ensure reflection is a string before regex processing
        if isinstance(reflection, list):
            reflection = " ".join(reflection)  # Convert list to a single string
        elif not isinstance(reflection, str):
            print(f"🚨 Error: Expected `reflection` to be str, got {type(reflection)}")
            return []

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
                print("✅ External knowledge retrieved, skipping question generation.")
                return []

        return unknown_terms  # ✅ If nothing was found, allow question generation


# ✅ Initialize knowledge manager instance
knowledge_manager = KnowledgeManager()
