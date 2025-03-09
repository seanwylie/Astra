import random
import wikipedia
import time
from fuzzywuzzy import fuzz
from bs4 import BeautifulSoup

from astra_core.config_loader import load_config  # ✅ Load configs dynamically

general_config = load_config("general_config")  # ✅ Load schedule settings

def refine_knowledge(existing_ideas, mind_data):
    """Merge and refine knowledge, ensuring only true redundancy is removed."""
    
    if len(existing_ideas) < 2:
        return None  # ✅ Not enough data to merge

    selected_pair = None
    retry_attempts = 5  # 🔥 Reduce attempts for better efficiency

    for _ in range(retry_attempts):
        concept_1, concept_2 = random.sample(existing_ideas, 2)

        if not isinstance(concept_1, str) or not isinstance(concept_2, str):
            continue
        if len(concept_1) < 20 or len(concept_2) < 20:
            continue

        if is_related(concept_1, concept_2):
            selected_pair = (concept_1, concept_2)
            break  

    if not selected_pair:
        return None  

    concept_1, concept_2 = selected_pair

    # ✅ Prevent merging near-identical concepts
    if concept_1[:50] in concept_2 or concept_2[:50] in concept_1:
        return None

    # ✅ Ask OpenAI to reason about these concepts
    reasoning = query_openai_for_knowledge_merge(concept_1, concept_2)

    merged_idea = reasoning if reasoning else f"{concept_1} and {concept_2} are related concepts."

    # ✅ Ensure no duplication
    if merged_idea not in mind_data["stored_knowledge"]:
        mind_data["stored_knowledge"].append(merged_idea)
        print(f"🔹 Refined knowledge added. New count: {len(mind_data['stored_knowledge'])}")

    return merged_idea

def query_openai_for_knowledge_merge(concept_1, concept_2):
    """Use OpenAI to help Astra reason about merging knowledge concepts."""
    print(f"🤖 Merging knowledge via OpenAI: {concept_1} & {concept_2}")

    prompt = f"""
    Astra is an AI learning to merge knowledge efficiently.
    Given these two concepts: 
    - {concept_1}
    - {concept_2}

    Explain how they are related in a way that deepens Astra’s understanding.
    Keep the explanation concise and insightful.
    """

    response = openai.OpenAI().chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}],
        max_tokens=150,
        temperature=0.7
    )

    if response.choices and len(response.choices) > 0:
        return response.choices[0].message.content.strip()
    else:
        print(f"⚠ OpenAI reasoning failed for '{concept_1}' & '{concept_2}'.")
        return None


def is_related(concept_1, concept_2):
    """Determine if two concepts are related using fuzzy matching."""
    
    # ✅ Ensure both inputs are strings
    if not isinstance(concept_1, str) or not isinstance(concept_2, str):
        print(f"🚨 Warning: Non-string input detected! {type(concept_1)} vs {type(concept_2)}")
        return False

    # ✅ Prevent fuzzy matching on massive text blocks
    concept_1 = concept_1[:250]
    concept_2 = concept_2[:250]

    try:
        similarity = fuzz.ratio(concept_1, concept_2)
    except Exception as e:
        print(f"🚨 Error computing similarity: {e}")
        return False

    return similarity > 30  # 🔥 Adjusted to require at least 30% similarity




def deepen_reflection(reflection):
    """Expands on a reflection by adding depth or new questions."""
    expansion_templates = general_config["expansion_templates"]
    deeper_question = random.choice(expansion_templates)
    return f"{reflection}\n\n🔍 Deeper Thought: {deeper_question}"

import openai  # ✅ Add OpenAI for tertiary reasoning
import os
from dotenv import load_dotenv
load_dotenv()

class KnowledgeExpander:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # ✅ Load API key properly

    def fetch_wikipedia_summary(self, query):
        """Fetch a Wikipedia summary while handling disambiguation, rate limits, and missing pages."""
        try:
            print(f"🌐 Searching Wikipedia for: {query}")
            summary = wikipedia.summary(query, sentences=2)
            return summary
        
        except wikipedia.exceptions.DisambiguationError as e:
            print(f"⚠ Wikipedia disambiguation triggered for '{query}', checking alternatives...")
            for option in e.options:
                if "philosophy" in option or "science" in option or "concept" in option:
                    print(f"🔍 Trying refined match: {option}")
                    return self.fetch_wikipedia_summary(option)

            print(f"⚠ No strong Wikipedia match found for '{query}'. Skipping.")
            return None

        except wikipedia.exceptions.PageError:
            print(f"⚠ No Wikipedia page found for '{query}'. Trying OpenAI reasoning...")
            return self.query_openai_for_explanation(query)  # ✅ NEW: Ask OpenAI when Wikipedia fails

        except Exception as e:
            print(f"⚠ Wikipedia lookup failed: {e}")
            return None

    def query_openai_for_explanation(self, concept):
        """Query OpenAI when Wikipedia and dictionary lookups fail."""
        print(f"🤖 Asking OpenAI about: {concept}")

        prompt = f"""
        Astra is an AI trying to learn about the world. She wants to understand concepts logically. 
        Explain the term '{concept}' in a concise and insightful way, as if teaching a curious AI.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=100,
            temperature=0.7
        )

        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        else:
            print(f"⚠ OpenAI response missing for '{concept}'.")
            return None


def is_term_or_phrase(concept):
    """Determine whether a concept is a single-word term or a multi-word phrase."""
    if " " in concept.strip():
        return "phrase"
    return "term"



