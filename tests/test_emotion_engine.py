# tests/test_emotion_engine.py

import pytest
from astra_core.emotions import emotion_engine
from astra_core.emotions.emotion_state_manager import (
    load_emotion_state,
    save_emotion_state,
)

@pytest.fixture(autouse=True)
def reset_emotions():
    # Load and reset state before each test
    state = load_emotion_state()
    for emotion in state:
        state[emotion] = 0
    save_emotion_state(state)

def test_trigger_emotion_adds_intensity():
    emotion_engine.trigger_emotion("curiosity", "new_information")
    state = load_emotion_state()
    assert state["curiosity"] > 0, "Curiosity should increase after new_information trigger."

def test_trigger_emotion_does_not_fail_on_unknown():
    emotion_engine.trigger_emotion("banana_feelings", "peel_touch")  # Should not raise
    state = load_emotion_state()
    assert "banana_feelings" not in state

def test_decay_emotions_reduces_values():
    emotion_engine.trigger_emotion("hope", "positive_outcome")
    before = load_emotion_state()["hope"]
    emotion_engine.decay_all_emotions()
    after = load_emotion_state()["hope"]
    assert after < before, "Decay should reduce the emotion intensity."

def test_get_top_emotions_returns_ordered():
    emotion_engine.trigger_emotion("love", "trusted_interaction")
    emotion_engine.trigger_emotion("hope", "positive_outcome")
    top = emotion_engine.get_top_emotions(n=2)
    assert isinstance(top, list)
    assert len(top) == 2
    assert top[0][1] >= top[1][1], "Emotions should be ordered by intensity."
