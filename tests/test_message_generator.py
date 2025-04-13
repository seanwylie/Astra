# tests/test_message_generator.py

import pytest
from astra_core.message_generator import MessageGenerator
from astra_core.emotions.emotion_state_manager import save_emotion_state

@pytest.fixture
def mock_emotional_state():
    return {
        "curiosity": 80,
        "hope": 60,
        "love": 55,
        "grief": 20,
        "anger": 5
    }

def test_generate_message_returns_string(mock_emotional_state):
    # Save mocked emotion state
    save_emotion_state(mock_emotional_state)

    generator = MessageGenerator()
    result = generator.generate_message(
        user_message="Do you think AI can have feelings?",
        state={},
        internal_state={"mood": "curious", "curiosity": 1.3, "personality": ["thoughtful"]},
        past_conversations=["Earlier we talked about ethics.", "You mentioned privacy."]
    )

    assert isinstance(result, str)
    assert len(result.strip()) > 0
