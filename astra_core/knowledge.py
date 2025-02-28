import requests
import re
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
        """Determine if Astra should look up a concept based on existing knowledge."""
        concept_count = sum(1 for insight in self.mind_data["stored_knowledge"] if concept.lower() in insight.lower())
        return concept_count < self.config["knowledge_storage_threshold"]

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

    def retrieve_external_knowledge(self, search_terms, mind_data):
        """Fetch knowledge from external sources and update stored knowledge."""
        new_knowledge = []
        for concept in search_terms:
            if not self.should_lookup_concept(concept):
                continue
            dictionary_info = self.lookup_dictionary_definition(concept)
            wiki_info = self.fetch_wikipedia_summary(concept)
            if dictionary_info:
                new_knowledge.append(f"📖 {concept}: {dictionary_info}")
            elif wiki_info:
                new_knowledge.append(f"📄 {concept}: {wiki_info}")
        if new_knowledge:
            mind_data["stored_knowledge"].extend(new_knowledge)
            save_mind(mind_data)
        
        return mind_data  # ✅ Ensures the function always returns the full mind_data dictionary


    def extract_unknown_terms(self, reflection, mind_data):
        """Extract potential unknown concepts from a reflection dynamically."""
        known_terms = set(mind_data.get("stored_knowledge", []))  # ✅ Use a set for fast lookup
    
        # ✅ Detect Multi-Word Phrases (Proper Nouns, Scientific Terms, etc.)
        phrase_pattern = r'\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        found_phrases = re.findall(phrase_pattern, reflection)

        # ✅ Detect Individual Words
        words = re.findall(r'\b\w+\b', reflection)
        found_words = [word.lower() for word in words if len(word) > 2]

        # ✅ Filter out individual words that are part of a known phrase
        filtered_words = [word for word in found_words if not any(phrase.lower().startswith(word) for phrase in found_phrases)]

        # ✅ Combine phrases and words into a single set
        all_terms = set(found_phrases + filtered_words)

        # ✅ Only consider terms that Astra doesn't fully understand
        unknown_terms = [term for term in all_terms if term not in known_terms]

        print(f"🔍 Final unknown concepts after filtering: {unknown_terms}")
        return unknown_terms

# ✅ Initialize knowledge manager instance
knowledge_manager = KnowledgeManager()
