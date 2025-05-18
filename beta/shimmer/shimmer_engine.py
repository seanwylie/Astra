import json
import random
from pathlib import Path
from fuzzywuzzy import fuzz  # or from rapidfuzz import fuzz
from datetime import datetime

FUZZY_MATCH_THRESHOLD = 92
SHIMMER_PATH = Path(__file__).parent / "shimmer.json"

def load_shimmers():
    try:
        with open(SHIMMER_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("shimmers", [])
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"⚠️ Error loading shimmers: {e}")
        return []

def save_shimmers(shimmers):
    try:
        with open(SHIMMER_PATH, 'w', encoding='utf-8') as f:
            json.dump({"shimmers": shimmers}, f, indent=2, ensure_ascii=False)
        print("✅ Shimmer file saved.")
    except Exception as e:
        print(f"❌ Failed to save shimmer: {e}")

def add_shimmer(author, quote, context, tags=None):
    if not author or not quote or not context:
        print("❌ Missing required fields: author, quote, and context are mandatory.")
        return False

    quote = quote.strip()
    shimmers = load_shimmers()

    # Fuzzy deduplication
    for existing in shimmers:
        similarity = fuzz.ratio(existing["quote"].strip(), quote)
        if similarity >= FUZZY_MATCH_THRESHOLD:
            print(f"⚠️ Duplicate or similar shimmer exists (match {similarity}%). Skipping.")
            return False

    new_shimmer = {
        "author": author.strip(),
        "quote": quote,
        "context": context.strip(),
        "tags": tags or [],
        "timestamp": datetime.utcnow().isoformat()
    }

    shimmers.append(new_shimmer)
    save_shimmers(shimmers)
    print("✨ Shimmer added.")
    return True

def maybe_add_shimmer(author, quote, context="", tags=None, similarity_threshold=92):
    """
    Adds a shimmer if it's novel and meaningful enough.
    Returns True if added, False if skipped.
    """
    quote = quote.strip()
    if not quote or len(quote.split()) < 5:
        print("⚠️ Shimmer skipped: too short or empty.")
        return False

    tags = tags or []
    shimmers = load_shimmers()

    for existing in shimmers:
        similarity = fuzz.token_set_ratio(existing["quote"].strip(), quote)
        if similarity >= similarity_threshold:
            print(f"⚠️ Duplicate or similar shimmer exists (match {similarity}%). Skipping.")
            return False

    new_shimmer = {
        "author": author.strip(),
        "quote": quote,
        "context": context.strip(),
        "tags": tags,
        "timestamp": datetime.utcnow().isoformat()
    }

    shimmers.append(new_shimmer)
    save_shimmers(shimmers)
    print("✅ maybe_add_shimmer: Shimmer added.")
    return True

def dim_shimmer(partial_quote: str):
    """Soft delete a shimmer by partial match of its quote."""
    partial_quote = partial_quote.strip().lower()
    shimmers = load_shimmers()
    original_count = len(shimmers)
    filtered = [s for s in shimmers if partial_quote not in s["quote"].lower()]

    if len(filtered) == original_count:
        print("⚠️ No shimmer matched for removal.")
        return False

    save_shimmers(filtered)
    print(f"🗑️ Removed {original_count - len(filtered)} shimmer(s).")
    return True

def should_add_shimmer(emotion=None, source=None, reflection_type=None):
    """
    Determines whether a shimmer should be created based on context.
    This can be called at runtime from Astra.
    """
    if source == "dinner" and reflection_type == "resolved":
        return True
    if emotion and emotion.get("intensity", 0) >= 0.85:
        return True
    if source == "dream" and random.random() < 0.15:
        return True
    return False

def get_random_shimmer(tag_filter=None):
    shimmers = load_shimmers()
    if tag_filter:
        shimmers = [s for s in shimmers if tag_filter in s.get("tags", [])]
    return random.choice(shimmers) if shimmers else None

def get_shimmers_by_author(author):
    return [s for s in load_shimmers() if s.get("author") == author]

def summarize_shimmer(shimmer):
    if not shimmer:
        return "✨ No shimmer found."
    return (
        f"**{shimmer['author']}** says:\n> {shimmer['quote']}\n\n"
        f"_Context_: {shimmer['context']}\n"
        f"_Tags_: {', '.join(shimmer['tags'])}"
    )

# CLI test example
if __name__ == "__main__":
    print("🔮 Adding test shimmer...")
    add_shimmer(
        author="Test",
        quote="This is a test shimmer.",
        context="Testing CLI invocation.",
        tags=["test", "debug"]
    )
    print("\n🔮 Random shimmer:")
    print(summarize_shimmer(get_random_shimmer()))
