# Astra Emotions Module
# Core emotional systems for Astra's inner life

from app.core.emotions.emotion_engine import (
    trigger_emotion,
    decay_all_emotions,
    get_top_emotions,
    get_emotion_intensity,
    get_dominant_emotion
)
from app.core.emotions.emotion_state_manager import load_emotion_state, save_emotion_state
from app.core.emotions.coregulation import coregulation_system, CoregulationSystem
from app.core.emotions.regulation_strategies import regulation_strategies, RegulationStrategiesSystem

__all__ = [
    "trigger_emotion",
    "decay_all_emotions",
    "get_top_emotions",
    "get_emotion_intensity",
    "get_dominant_emotion",
    "load_emotion_state",
    "save_emotion_state",
    "coregulation_system",
    "CoregulationSystem",
    "regulation_strategies",
    "RegulationStrategiesSystem"
]
