# test_shimmer_engine.py

from shimmer_engine import add_shimmer, get_random_shimmer, summarize_shimmer

# Test adding a shimmer
added = add_shimmer(
    author="UnitTest",
    quote="Even the brightest mind needs a quiet night to dream.",
    context="Testing shimmer addition logic.",
    tags=["test", "dream"]
)
print("✅ Shimmer added:", added)

# Test retrieving and summarizing a random shimmer
shimmer = get_random_shimmer()
print("🔮 Random shimmer summary:")
print(summarize_shimmer(shimmer))