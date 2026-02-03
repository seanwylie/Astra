# astra_core/astra_helpers/utils_helper.py

import re
import requests
import wikipedia
from app.interfaces.influence import load_mind
from app.interfaces.mind_session import session
from app.logging_config import get_logger

logger = get_logger(__name__)


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
            logger.debug("Dictionary definition found for '%s'", clean_term)
            return definition
    except Exception as e:
        logger.debug("Dictionary lookup failed for '%s': %s", clean_term, e)

    try:
        summary = wikipedia.summary(clean_term, sentences=1)
        logger.debug("Wikipedia summary found for '%s'", clean_term)
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        logger.debug("Wikipedia disambiguation for '%s': %s", clean_term, e.options[:3])
    except wikipedia.exceptions.PageError:
        logger.debug("Wikipedia page not found for '%s'", clean_term)
    except Exception as e:
        logger.debug("Wikipedia lookup failed for '%s': %s", clean_term, e)

    return None





def extract_unknown_terms(user_message):
    """Extract candidate terms from a message that Astra doesn't already understand."""
    # Match Title-Cased single or multi-word terms
    words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', user_message)

    stored_knowledge = session.load().get("stored_knowledge", [])
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


def extract_candidate_terms_from_text(text, known_text_lower):
    """Extract candidate terms (Title-Case or notable words) from text that are not in known_text_lower."""
    words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text or "")
    candidates = []
    for term in words:
        term_clean = term.strip().lower()
        if term_clean in BLOCKED_TERMS or len(term_clean) < 3:
            continue
        if term_clean in known_text_lower:
            continue
        candidates.append(term)
    return candidates


def proactive_lookup_from_text(text, mind_data, max_lookups=2):
    """
    From text (e.g. reflection or question), extract candidate terms not in stored_knowledge,
    run lookup_definition for up to max_lookups, and append new entries to mind.
    """
    if not text or not mind_data:
        return 0
    stored = mind_data.get("stored_knowledge", [])
    known_parts = []
    for e in stored:
        if isinstance(e, dict):
            known_parts.append((e.get("insight") or str(e)).lower())
        else:
            known_parts.append((e or "").lower())
    known_text_lower = " ".join(known_parts)
    candidates = extract_candidate_terms_from_text(text, known_text_lower)
    if not candidates:
        return 0
    added = 0
    for term in candidates[:max_lookups]:
        definition = lookup_definition(term)
        if definition:
            entry = f"📖 **{term}**: {definition}"
            if entry not in stored:
                mind_data.setdefault("stored_knowledge", []).append(entry)
                added += 1
                session.maybe_save()
                print(f"[proactive_lookup] Learned from text: {term}")
    return added
