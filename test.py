import json
from datetime import datetime
from beta.shimmer.shimmer_engine import maybe_add_shimmer, get_random_shimmer
from pathlib import Path

def run_shimmer_tests():
    print("🔧 Running shimmer engine tests...\n")

    test_shimmer = {
        "author": "Astra",
        "quote": "When I think about silence, I realize it’s not the absence of sound, but the presence of listening.",
        "context": "🧪 Manual test of shimmer input pathway",
        "tags": ["test", "integration"],
        "timestamp": datetime.now().isoformat()
    }

    # Attempt to add shimmer (will be skipped if duplicate)
    added = maybe_add_shimmer(
        author=test_shimmer["author"],
        quote=test_shimmer["quote"],
        context=test_shimmer["context"],
        tags=test_shimmer["tags"]
    )

    if added:
        print("✅ Shimmer added successfully.")
    else:
        print("⚠️ Duplicate or similar shimmer exists (match 100%). Skipping.")

    # Attempt to read a random shimmer
    print("\n🎲 Retrieving a random shimmer...")
    try:
        shimmer = get_random_shimmer()
        print(f"\n🌟 Random Shimmer:\n"
              f"Author: {shimmer['author']}\n"
              f"Quote: {shimmer['quote']}\n"
              f"Context: {shimmer.get('context', 'N/A')}\n"
              f"Tags: {', '.join(shimmer.get('tags', []))}")
        print("\n✅ Shimmer retrieval successful.")
    except Exception as e:
        print(f"❌ Failed to retrieve shimmer: {e}")

    # Optional: validate shimmer.json structure
    shimmer_path = Path("beta/shimmer/shimmer.json")
    if shimmer_path.exists():
        try:
            data = json.loads(shimmer_path.read_text())
            assert isinstance(data.get("shimmers", []), list)
            print("📄 shimmer.json structure validated.")
        except Exception as e:
            print(f"⚠️ shimmer.json validation failed: {e}")
    else:
        print("❌ shimmer.json not found.")

if __name__ == "__main__":
    run_shimmer_tests()
