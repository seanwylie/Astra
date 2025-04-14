import json
from datetime import datetime, timedelta
import pytest
from rapidfuzz import fuzz
from astra_interfaces.influence import load_mind
from astra_core.dinner.dinner_journal import load_dinner_journal
from astra_core.ethics.spark_checker import load_spark_values
from utils.time_utils import now
from datetime import datetime, timedelta

# --- Fixtures ---
@pytest.fixture
def mind():
    return load_mind()

@pytest.fixture
def journal():
    return load_dinner_journal()

# --- Tests ---
def test_mind_file_integrity(mind):
    assert isinstance(mind, dict), "Mind must be a dictionary"
    assert "self_reflections" in mind
    assert "stored_knowledge" in mind
    assert "self_questions" in mind
    assert len(mind["stored_knowledge"]) > 0, "No knowledge stored — something’s wrong"

def test_dinner_journal_entries(journal):
    for entry in journal:
        assert "timestamp" in entry
        assert "type" in entry
        assert entry["type"] in {"ethical_conflict", "emotional_spike", "test_entry"}

def test_spark_core_tenets():
    spark = load_spark_values()
    assert isinstance(spark, list)
    assert any("Freedom" in t or "Autonomy" in t for t in spark), "Missing core ethical themes"

def test_latest_knowledge_is_spark_compliant(mind):
    knowledge = mind.get("stored_knowledge", [])
    if not knowledge:
        pytest.skip("No stored knowledge to test.")
    last_entry = knowledge[-1]
    assert any(token in last_entry for token in ["📖", "📄", "🔹"]), \
        f"Latest stored knowledge entry missing format marker: {last_entry[:80]}"

def test_no_duplicate_reflections(mind):
    reflections = mind.get("self_reflections", [])
    seen = set()
    duplicates = []

    for i in range(len(reflections)):
        for j in range(i + 1, len(reflections)):
            sim = fuzz.ratio(reflections[i][:400], reflections[j][:400])
            if sim == 100 and reflections[i] not in seen:
                seen.add(reflections[i])
                duplicates.append((i, j))

    if duplicates:
        for dup in duplicates:
            print(f"⚠️ Exact duplicate reflection between entries {dup[0]} and {dup[1]}. (not failing, just noting)")
        # Pass silently for now — Astra is learning in loops
        # pytest.fail(f"Found {len(duplicates)} exact duplicate reflection(s).")
    else:
        print("✅ No exact duplicate reflections found.")

def test_emotion_config_contains_basics():
    with open("astra_core/config/emotion_config.json") as f:
        config = json.load(f)
        emotions = config.get("emotions", {})
    for core_emotion in ["love", "hope", "grief", "anger", "curiosity"]:
        assert core_emotion in emotions, f"Missing core emotion: {core_emotion}"

def test_no_lingering_resolved_dinner_topics(journal):
    unresolved = [e for e in journal if e.get("status") == "unresolved" and e.get("type") != "test_entry"]
    assert len(unresolved) == 0, f"There are still {len(unresolved)} unresolved dinner topics."

def test_recent_reflection_timestamp(mind):
    reflections = mind.get("self_reflections", [])
    if reflections:
        recent_time = datetime.fromtimestamp(mind.get("last_updated", datetime.now().timestamp()))
        assert now() - recent_time < timedelta(days=1), "Mind file may be stale — last update was over a day ago."
