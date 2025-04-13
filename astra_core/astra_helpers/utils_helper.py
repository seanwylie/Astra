# astra_core/astra_helpers/utils_helper.py

import re
import requests
import wikipedia
from astra_interfaces.influence import load_mind

def extract_unknown_terms(user_message):
    """Extract potential complex terms from a message."""
    words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', user_message)
    stored_knowledge = load_mind().get("stored_knowledge", [])
    return [term for term in words if term.lower() not in stored_knowledge]

def lookup_definition(term):
    """Fetch definitions from dictionary API, fallback to Wikipedia."""
    clean_term = re.sub(r'[^\w\s]', '', term).strip()

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
