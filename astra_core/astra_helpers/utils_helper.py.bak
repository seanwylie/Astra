# astra_core/astra_helpers/utils_helper.py

import re
import requests
import wikipedia
from astra_interfaces.influence import load_mind

BLOCKED_TERMS = {
    "the", "a", "an", "and", "or", "in", "on", "with", "to", "from", "at", "by", 
    "for", "of", "this", "that", "these", "those", "english", "however", 
    "nevertheless", "historically", "history", "spinning", "it", "one", "moreover",
    "furthermore", "deeper", "consideration", "fallback", "building"
}



lookup_attempts = {}  # Add this at the module level if needed

def lookup_definition(term):
    """Fetch definitions from dictionary API, fallback to Wikipedia."""
    clean_term = re.sub(r'[^\w\s]', '', term).strip().lower()

    # 🛡 Block stopwords immediately
    if clean_term in BLOCKED_TERMS:
        print(f"🛑 Skipping blocked term: {clean_term}")
        return None

    # 🛡 Prevent excessive re-lookup
    lookup_attempts.setdefault(clean_term, 0)
    if lookup_attempts[clean_term] > 3:
        print(f"🧯 Aborting excessive retries for: {clean_term}")
        return None
    lookup_attempts[clean_term] += 1

    # ✅ Try Dictionary API
    try:
        response = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{clean_term}")
        if response.status_code == 200:
            definition = response.json()[0]['meanings'][0]['definitions'][0]['definition']
            print(f"📖 Dictionary definition found for '{clean_term}'")
            return definition
    except Exception as e:
        print(f"⚠️ Dictionary lookup failed for '{clean_term}': {e}")

    # ✅ Fallback to Wikipedia
    try:
        summary = wikipedia.summary(clean_term, sentences=1)
        print(f"🌐 Wikipedia summary found for '{clean_term}'")
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        print(f"⚠️ Wikipedia disambiguation for '{clean_term}': {e.options[:3]}")
    except wikipedia.exceptions.PageError:
        print(f"⚠️ Wikipedia page not found for '{clean_term}'")
    except Exception as e:
        print(f"⚠️ Wikipedia lookup failed for '{clean_term}': {e}")

    return None





def extract_unknown_terms(user_message):
    """Extract candidate terms from a message that Astra doesn't already understand."""
    # Match Title-Cased single or multi-word terms
    words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', user_message)

    stored_knowledge = load_mind().get("stored_knowledge", [])
    known_text = " ".join(stored_knowledge).lower()

    unknowns = []
    for term in words:
        term_clean = term.strip().lower()

        # 🧹 Skip blocked/stopwords and overly short terms
        if term_clean in BLOCKED_TERMS or len(term_clean) < 3:
            continue

        # 🔍 Skip if it's already in stored knowledge somewhere
        if term_clean in known_text:
            continue

        unknowns.append(term)

    return unknowns
