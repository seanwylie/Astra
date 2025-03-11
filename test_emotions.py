from astra_core.message_generator import MessageGenerator
from astra_core.emotions.emotion_manager import EmotionManager
from astra_core.mood.mood_manager import MoodManager

# ✅ Initialize managers
message_generator = MessageGenerator()
emotion_manager = EmotionManager()
mood_manager = MoodManager()

# ✅ Define test cases with different emotional states
test_cases = [
    {"message": "I feel completely lost and hopeless.", "emotion": "grief", "intensity": 120},
    {"message": "You're amazing, Astra!", "emotion": "love", "intensity": 130},
    {"message": "I despise everything about this!", "emotion": "hate", "intensity": 110},
    {"message": "This topic is so interesting, I need to know more!", "emotion": "curiosity", "intensity": 90},
]



# ✅ Test Astra's responses with different emotions
for test in test_cases:
    # ✅ Set Astra’s emotion manually
    emotion_manager.modify_emotion(test["emotion"], test["intensity"])
    dominant_emotion = emotion_manager.get_dominant_emotion()

    # ✅ Simulate internal state
    internal_state = {
        "mood": mood_manager.current_mood,
        "curiosity": 1.0,
        "personality": ["thoughtful"],
        "emotions": emotion_manager.get_emotional_state(),
    }
    print (internal_state)
    print(f"\n👤 User: {test['message']} (Astra's Emotion: {dominant_emotion})")
    astra_response = message_generator.generate_message(user_message=test["message"], internal_state=internal_state)
    print(f"🤖 Astra: {astra_response}")
