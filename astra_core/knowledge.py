import requests
import re
import time
import random
import openai
from fuzzywuzzy import fuzz
from astra_core.config_loader import load_config
from astra_interfaces.influence import load_mind, save_mind  
from astra_core.config_loader import debug_log

class KnowledgeManager:
    COMMON_WORDS = {
        "the", "a", "and", "is", "in", "with", "to", "from", "for", "on", "as", "it",
        "by", "this", "of", "that", "which", "at", "does", "relate", "how", "what"
    }
    IGNORE_TERMS = {"deeper thought", "🔍 reflection", "🔍 deeper thought"}

    def __init__(self):
        """Initialize Astra's knowledge system with memory and external lookup sources."""
        print("🔍 Debug: Loading knowledge settings...")
        self.config = load_config("lookup_config")
        debug_log("Loading")  
        self.mind_data = load_mind()  
        self.mind_data.setdefault("past_conversations", [])  

        # ✅ Deduplicate stored knowledge
        seen = set()
        self.mind_data["stored_knowledge"] = [
            x for x in self.mind_data["stored_knowledge"] if not (x in seen or seen.add(x))
        ]

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
        self.mind_data["past_conversations"] = self.mind_data["past_conversations"][-100:]  # Keep last 100
        save_mind(self.mind_data)

    def should_lookup_concept(self, concept, force=False):
        """Determine if Astra should look up a concept based on meaningful stored knowledge."""
        concept_lower = concept.lower().strip()

        if force:
            print(f"⚠ Force lookup enabled for '{concept}', overriding existing checks.")
            return True  

        if concept_lower in self.COMMON_WORDS or len(concept_lower) < 3:
            print(f"⚠ Ignoring '{concept}', too generic.")
            return False  

        # ✅ Check existing definitions
        for entry in self.mind_data["stored_knowledge"]:
            if concept_lower in entry.lower() and len(entry.split()) > 5:
                return False  

        # ✅ Fuzzy Matching (last resort, avoid false positives)
        for entry in self.mind_data["stored_knowledge"]:
            similarity = fuzz.partial_ratio(concept_lower, entry.lower())
            if similarity > 92:
                return False  

        print(f"🔍 Concept '{concept}' not found in a meaningful form, proceeding with lookup.")
        return True  

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
            else:
                print(f"🌐 Searching deeper for: {concept}")
                new_knowledge.append(self.query_openai_for_reasoning(concept))

        # ✅ If no new knowledge was retrieved, exit early
        if not new_knowledge:
            print("❌ No new knowledge retrieved. Skipping save.")
            return False  

        # ✅ Store new knowledge
        pre_save_count = len(self.mind_data["stored_knowledge"])
        for entry in new_knowledge:
            if entry and entry not in self.mind_data["stored_knowledge"]:  
                self.mind_data["stored_knowledge"].append(entry)

        print(f"🔍 Debug: Before saving, knowledge count: {pre_save_count} -> {len(self.mind_data['stored_knowledge'])}")

        # ✅ Save and verify
        save_mind(self.mind_data)
        time.sleep(0.5)  

        reloaded_mind = load_mind()
        self.mind_data["stored_knowledge"] = reloaded_mind["stored_knowledge"]

        return True  

    def query_openai_for_reasoning(self, concept):
        """Use OpenAI to generate a deeper understanding of a concept."""
        past_references = [entry for entry in self.mind_data["stored_knowledge"] if concept in entry.lower()]
        past_references_text = "\n".join(past_references[-3:]) if past_references else "None"

        prompt = f"""
        Astra is an AI who expands on knowledge by reasoning from prior conversations.
        She does NOT introduce external sources, only **thinks about what she knows**.

        **Concept:** {concept}
        **What Astra already knows:**
        {past_references_text}

        **How should Astra explain this concept in a way that deepens her understanding?**
        """

        response = openai.OpenAI().chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=200,
            temperature=0.8  
        )

        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        else:
            return f"🤔 I need more data to form a strong understanding of '{concept}'."

    def extract_unknown_terms(self, reflection):
        """Extract meaningful unknown concepts while filtering out noise."""
        print(f"🔍 Debug: Reflection Type: {type(reflection)}, Length: {len(reflection) if isinstance(reflection, str) else 'N/A'}")

        if isinstance(reflection, list):
            reflection = " ".join(reflection[-5:])  

        if not isinstance(reflection, str):
            return []

        if len(reflection) > 5000:
            print(f"⚠ WARNING: Reflection is too long ({len(reflection)} chars)! Trimming...")
            reflection = reflection[:5000]

        phrase_pattern = r'\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        found_phrases = set(re.findall(phrase_pattern, reflection))

        words = set(re.findall(r'\b\w+\b', reflection))
        filtered_words = {word.lower() for word in words if len(word) > 2 and word.lower() not in self.COMMON_WORDS}

        final_terms = (found_phrases | filtered_words) - self.IGNORE_TERMS
        unknown_terms = [term for term in final_terms if term not in self.mind_data["stored_knowledge"]]

        print(f"🔍 Debug: Final unknown concepts after filtering: {unknown_terms}")

        if unknown_terms:
            print("🔍 Debug: Attempting external knowledge lookup...")
            self.retrieve_external_knowledge(unknown_terms)

        return unknown_terms

knowledge_manager = KnowledgeManager()
