import json
import boto3
import io
from astra_interfaces.influence import load_mind, save_mind, store_knowledge


# ✅ **Configuration**
S3_BUCKET_NAME = "swylie-astra"
MIND_FILE_JSON = "mind_file.json"
s3 = boto3.client("s3")


def test_mind_file_integrity():
    """✅ Test 1: Verify the structure of the mind file in S3."""
    print("\n🔍 Running Test 1: Mind File Integrity...")

    mind_data = load_mind()
    
    assert isinstance(mind_data, dict), "❌ ERROR: Mind data is not a dictionary!"
    assert "stored_knowledge" in mind_data, "❌ ERROR: `stored_knowledge` key missing!"
    assert isinstance(mind_data["stored_knowledge"], dict), "❌ ERROR: `stored_knowledge` is not a dictionary!"

    print("✅ PASSED: Mind file structure is correct.")


def test_knowledge_retrieval():
    """✅ Test 2: Verify knowledge retrieval from `stored_knowledge`."""
    print("\n🔍 Running Test 2: Knowledge Retrieval...")

    mind_data = load_mind()
    stored_knowledge = mind_data.get("stored_knowledge", {})

    if not stored_knowledge:
        print("⚠ WARNING: No knowledge stored yet! Skipping test.")
        return
    
    sample_key = list(stored_knowledge.keys())[0]
    retrieved_knowledge = stored_knowledge.get(sample_key, None)

    assert retrieved_knowledge, f"❌ ERROR: Could not retrieve knowledge for `{sample_key}`!"
    print(f"✅ PASSED: Successfully retrieved `{sample_key}`: {retrieved_knowledge}")


def test_knowledge_storage():
    """✅ Test 3: Store a new knowledge entry and verify persistence."""
    print("\n🔍 Running Test 3: Knowledge Storage...")

    mind_data = load_mind()
    test_term = "quantum_fluctuation"
    test_definition = "Temporary changes in the amount of energy in a point in space."

    # Store knowledge
    store_knowledge(mind_data, f"{test_term}: {test_definition}")  # ✅ Correct

    save_mind(mind_data)

    # Reload and verify
    reloaded_mind_data = load_mind()
    assert test_term in reloaded_mind_data["stored_knowledge"], "❌ ERROR: Knowledge did not persist!"
    print(f"✅ PASSED: Successfully stored `{test_term}`!")


def test_data_persistence():
    """✅ Test 4: Ensure knowledge is not lost after saving & loading."""
    print("\n🔍 Running Test 4: Data Persistence...")

    mind_data = load_mind()
    pre_save_count = len(mind_data["stored_knowledge"])

    # Save and reload
    save_mind(mind_data)
    reloaded_mind_data = load_mind()

    assert len(reloaded_mind_data["stored_knowledge"]) >= pre_save_count, "❌ ERROR: Data loss detected!"
    print("✅ PASSED: No data loss after save/load cycle.")


if __name__ == "__main__":
    test_mind_file_integrity()
    test_knowledge_retrieval()
    test_knowledge_storage()
    test_data_persistence()

    print("\n🎉 ALL TESTS COMPLETED! 🎉")
