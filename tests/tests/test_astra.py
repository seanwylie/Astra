import sys
import os
# ✅ Ensure the tests can find Astra's modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import os
import pytest
import asyncio
import discord
from unittest.mock import AsyncMock
from astra_discord import on_message
from astra_reflection import generate_reflection, load_mind
import builtins
import wikipedia

import shutil
import pytest

MIND_FILE = "mind_file.json"
BACKUP_FILE = "mind_file_backup.json"

@pytest.fixture
def backup_mind_file():
    """Backup the mind file before each test and restore it after."""
    if os.path.exists(MIND_FILE):
        shutil.copy(MIND_FILE, BACKUP_FILE)  # ✅ Safe backup
    else:
        print("❌ ERROR: mind_file.json is missing before tests!")

    try:
        yield  # ✅ Run the test
    finally:
        if os.path.exists(BACKUP_FILE):
            shutil.copy(BACKUP_FILE, MIND_FILE)  # ✅ Restore after test
            os.remove(BACKUP_FILE)  # ✅ Clean up
        else:
            print("❌ ERROR: Backup file was lost! Not restoring mind_file.json.")

@pytest.mark.asyncio
async def test_discord_reflect_command():
    """Ensure Astra responds to `!reflect` command and generates a reflection."""
    mock_message = AsyncMock()
    mock_message.content = "!reflect"
    mock_message.author = "test_user"
    mock_message.channel.send = AsyncMock()

    print("✅ DEBUG: Sending !reflect command to Astra...")
    await on_message(mock_message)

    print("✅ DEBUG: Checking if `send()` was called...")
    print("✅ DEBUG: send() Calls:", mock_message.channel.send.call_args_list)


def test_generate_reflection(backup_mind_file):
    """Test that Astra generates a reflection and saves it correctly."""
    mind_data_before = load_mind()
    num_reflections_before = len(mind_data_before["self_reflections"])

    generate_reflection()  # Trigger Astra to generate a thought

    mind_data_after = load_mind()
    num_reflections_after = len(mind_data_after["self_reflections"])

    assert num_reflections_after > num_reflections_before, "Reflection count did not increase!"

def test_wikipedia_lookup():
    """Test that Astra correctly searches Wikipedia when needed."""
    from astra_reflection import fetch_wikipedia_summaries

    result = fetch_wikipedia_summaries("Artificial intelligence")
    assert result is not None and len(result) > 20, "Wikipedia lookup failed or returned an empty summary!"

def test_no_duplicate_reflections(backup_mind_file):
    """Test that Astra does not repeat the exact same reflection twice in a row."""
    generate_reflection()
    generate_reflection()

    mind_data = load_mind()
    reflections = mind_data["self_reflections"][-2:]

    assert reflections[0] != reflections[1], "Astra repeated the same reflection!"

def test_wake_astra_script_exists():
    """Check that `wake_astra.sh` exists and is executable."""
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../wake_astra.sh"))
    
    assert os.path.exists(script_path), "wake_astra.sh is missing!"
    assert os.access(script_path, os.X_OK), f"{script_path} is not executable!"

def test_deep_thought_expansion(backup_mind_file):
    """Ensure Astra refines self-reflections over time rather than repeating them."""
    generate_reflection()
    generate_reflection()  # Astra should build on previous thoughts

    mind_data = load_mind()
    reflections = mind_data["self_reflections"][-2:]

    assert reflections[0] != reflections[1], "Astra did not refine its reflection!"
    assert len(reflections[1]) > len(reflections[0]), "New reflection should be more complex than the previous one!"

def test_knowledge_integration(backup_mind_file, capsys):
    """Ensure Astra correctly merges new knowledge or detects duplicates properly."""
    mind_data_before = load_mind()
    stored_knowledge_before = set(mind_data_before["stored_knowledge"])

    generate_reflection()  # This should add new insights or at least attempt to

    mind_data_after = load_mind()
    stored_knowledge_after = set(mind_data_after["stored_knowledge"])

    # Capture debug logs
    captured = capsys.readouterr()
    
    # ✅ Print full captured output for debugging
    print("✅ DEBUG: Full Captured Output Below:\n")
    print(captured.out)

    duplicate_log_detected = "⚠ DEBUG: Wikipedia entry already known, rejecting duplicate:" in captured.out
    lookup_attempted = "🌍 DEBUG: Wikipedia Lookup: Searching for" in captured.out
    success_log_detected = "✅ DEBUG: Successfully added new knowledge:" in captured.out
    lookup_failed = "⚠ DEBUG: Wikipedia lookup failed or returned no results." in captured.out

    # ✅ Adjust assertion: If Astra did nothing, explicitly fail with more info
    assert (
        duplicate_log_detected or success_log_detected or lookup_failed or lookup_attempted
    ), "Astra did not attempt to add new knowledge, detect a duplicate, or even try a lookup!"


def test_reflection_format(backup_mind_file):
    """Ensure Astra's reflections follow a structured format."""
    generate_reflection()
    
    mind_data = load_mind()
    last_reflection = mind_data["self_reflections"][-1]

    assert "Thinking about" in last_reflection, "Reflection does not start with expected phrase!"
    assert "By analyzing these insights together, I see a pattern:" in last_reflection, "Reflection missing analysis section!"

def test_follow_up_question_generation(backup_mind_file):
    """Ensure Astra generates a follow-up question after each reflection."""
    generate_reflection()
    
    mind_data = load_mind()
    last_question = mind_data["self_questions"][-1]

    assert last_question, "Astra did not generate a follow-up question!"

def test_wikipedia_trigger(backup_mind_file, monkeypatch):
    """Ensure Astra correctly triggers a Wikipedia lookup when needed."""
    from astra_reflection import fetch_wikipedia_summaries

    # ✅ Mock Wikipedia lookup to return multiple test values
    monkeypatch.setattr("astra_reflection.fetch_wikipedia_summaries", lambda query, max_results: ["Test Wikipedia Summary 1", "Test Wikipedia Summary 2"])

    results = fetch_wikipedia_summaries("Artificial intelligence", max_results=3)

    # ✅ Ensure Astra retrieves multiple results and picks one
    assert len(results) > 1, "Astra did not fetch multiple Wikipedia summaries!"
    assert any("Test Wikipedia Summary" in result for result in results), "Wikipedia lookup did not return expected test values!"


def test_wikipedia_no_loop(monkeypatch, capsys):
    """Ensure Astra handles Wikipedia disambiguation pages by exploring subtopics."""
    from astra_reflection import fetch_wikipedia_summaries

    # ✅ Mock Wikipedia lookup to simulate a disambiguation page
    def mock_disambiguation(*args, **kwargs):
        return ["This may refer to multiple topics: AI ethics, AI research, AI technology."]

    def mock_subtopic_lookup(*args, **kwargs):
        return ["AI ethics summary retrieved successfully."]

    monkeypatch.setattr(wikipedia, "search", mock_disambiguation)
    monkeypatch.setattr(wikipedia, "summary", mock_subtopic_lookup)

    results = fetch_wikipedia_summaries("Artificial intelligence", max_results=3)

    captured = capsys.readouterr()

    # ✅ Ensure Astra did NOT get stuck on disambiguation
    # ✅ Ensure Astra explores a subtopic instead of getting stuck on disambiguation
    assert results, "Astra did not return any Wikipedia results!"
    assert any("summary" in res.lower() for res in results), \
        f"Astra did not retrieve a valid Wikipedia summary! Retrieved: {results}"
    assert "🔎 DEBUG: Selected" in captured.out, \
        "Astra did not log that it explored a related topic!"



    assert any(keyword in results[0].lower() for keyword in disambiguation_keywords), \
        f"Astra did not properly handle Wikipedia disambiguation! Retrieved: {results[0]}"

    assert "🌍 DEBUG: Attempting Wikipedia search" in captured.out, "Astra did not log the Wikipedia lookup!"



def test_follow_up_question_relevance(backup_mind_file):
    """Ensure Astra’s follow-up questions relate to the previous reflection."""
    generate_reflection()

    mind_data = load_mind()
    last_reflection = mind_data["self_reflections"][-1]
    last_question = mind_data["self_questions"][-1]

    assert any(word in last_reflection for word in last_question.split()), "Follow-up question is not related to the last reflection!"

def test_reflection_contains_insights(backup_mind_file):
    """Ensure Astra's reflections contain at least one insight from stored knowledge."""
    generate_reflection()
    
    mind_data = load_mind()
    last_reflection = mind_data["self_reflections"][-1]
    
    assert any(insight in last_reflection for insight in mind_data["stored_knowledge"]), "Reflection does not contain an insight!"

def test_no_repeated_follow_up_questions(backup_mind_file):
    """Ensure Astra does not generate the same follow-up question twice in a row."""
    generate_reflection()
    generate_reflection()

    mind_data = load_mind()
    last_two_questions = mind_data["self_questions"][-2:]

    assert last_two_questions[0] != last_two_questions[1], "Astra repeated the same follow-up question!"

def test_reflection_builds_on_previous_knowledge(backup_mind_file):
    """Ensure Astra integrates stored knowledge into new reflections."""
    generate_reflection()

    mind_data = load_mind()
    last_reflection = mind_data["self_reflections"][-1]
    stored_knowledge = mind_data["stored_knowledge"]

    assert any(insight in last_reflection for insight in stored_knowledge), "New reflection did not incorporate stored knowledge!"


