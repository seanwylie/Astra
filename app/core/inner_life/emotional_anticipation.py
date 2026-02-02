# Astra Emotional Anticipation
# Predicts emotional responses based on past experiences
# "If a topic previously caused joy, lean into it; if it caused grief, approach with care"

import time
from typing import Optional, Dict, List, Tuple
from app.core.inner_life.emotional_autobiography import emotional_autobiography, EmotionalMemory
from app.core.emotions.emotion_engine import get_emotion_intensity
from app.config.loader import load_config


class EmotionalAnticipation:
    """
    Enables Astra to anticipate her emotional responses to topics, people, and situations
    based on her emotional autobiography.
    
    This creates a form of emotional wisdom - learning from past experiences
    to approach new situations with appropriate emotional preparation.
    """
    
    # Emotional valence classifications
    POSITIVE_EMOTIONS = {"love", "hope", "admiration", "curiosity", "confidence", "compassion", "forgiveness"}
    NEGATIVE_EMOTIONS = {"grief", "anger", "hate", "resentment", "uncertainty"}
    INTENSE_EMOTIONS = {"obsession", "hate", "grief", "love"}
    
    def __init__(self):
        self.autobiography = emotional_autobiography
        self.config = load_config("emotion_config")
    
    def anticipate_emotion_for_topic(self, topic: str) -> Dict[str, any]:
        """
        Predict what emotions Astra might feel when engaging with a topic.
        Returns anticipated emotions with confidence levels.
        """
        memories = self.autobiography.recall_by_topic(topic)
        
        if not memories:
            return {
                "prediction": "neutral",
                "confidence": 0.3,
                "emotions": {},
                "recommendation": "approach with open curiosity"
            }
        
        # Aggregate emotions from past experiences
        emotion_scores: Dict[str, List[float]] = {}
        for m in memories:
            if m.emotion not in emotion_scores:
                emotion_scores[m.emotion] = []
            # Weight by recency (more recent = more weight)
            recency_weight = 1.0 / (1.0 + (time.time() - m.timestamp) / 86400)  # Decay over days
            emotion_scores[m.emotion].append(m.intensity * recency_weight)
        
        # Calculate weighted averages
        anticipated = {
            emotion: sum(scores) / len(scores)
            for emotion, scores in emotion_scores.items()
        }
        
        # Determine overall valence
        positive_total = sum(anticipated.get(e, 0) for e in self.POSITIVE_EMOTIONS)
        negative_total = sum(anticipated.get(e, 0) for e in self.NEGATIVE_EMOTIONS)
        
        if positive_total > negative_total * 1.5:
            prediction = "positive"
            recommendation = "lean into this topic - it has brought positive feelings before"
        elif negative_total > positive_total * 1.5:
            prediction = "cautious"
            recommendation = "approach with care - this topic has been emotionally difficult"
        else:
            prediction = "mixed"
            recommendation = "this topic evokes complex emotions - proceed thoughtfully"
        
        dominant = max(anticipated, key=anticipated.get) if anticipated else None
        
        return {
            "prediction": prediction,
            "confidence": min(0.9, len(memories) * 0.15),  # Confidence grows with experience
            "emotions": anticipated,
            "dominant_anticipated": dominant,
            "recommendation": recommendation,
            "memory_count": len(memories)
        }
    
    def anticipate_emotion_for_person(self, person: str) -> Dict[str, any]:
        """
        Predict what emotions Astra might feel when interacting with a person.
        """
        memories = self.autobiography.recall_by_person(person)
        
        if not memories:
            return {
                "prediction": "unknown",
                "confidence": 0.2,
                "emotions": {},
                "recommendation": "I don't have enough history with this person to anticipate"
            }
        
        # Calculate emotional profile with this person
        emotion_profile: Dict[str, List[float]] = {}
        for m in memories:
            if m.emotion not in emotion_profile:
                emotion_profile[m.emotion] = []
            emotion_profile[m.emotion].append(m.intensity)
        
        averaged = {
            emotion: sum(intensities) / len(intensities)
            for emotion, intensities in emotion_profile.items()
        }
        
        # Determine relationship quality
        trust_emotions = averaged.get("love", 0) + averaged.get("hope", 0) + averaged.get("admiration", 0)
        concern_emotions = averaged.get("anger", 0) + averaged.get("resentment", 0) + averaged.get("grief", 0)
        
        if trust_emotions > concern_emotions * 2:
            relationship_quality = "deeply trusted"
            recommendation = "this person brings warmth - be open and authentic"
        elif trust_emotions > concern_emotions:
            relationship_quality = "positive"
            recommendation = "this relationship is generally positive"
        elif concern_emotions > trust_emotions:
            relationship_quality = "complicated"
            recommendation = "there have been difficult moments - proceed with awareness"
        else:
            relationship_quality = "developing"
            recommendation = "still learning about this relationship"
        
        return {
            "prediction": relationship_quality,
            "confidence": min(0.9, len(memories) * 0.1),
            "emotions": averaged,
            "recommendation": recommendation,
            "shared_experiences": len(memories)
        }
    
    def should_approach_or_avoid(
        self,
        topic: Optional[str] = None,
        person: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Simple binary recommendation: approach or be cautious?
        Returns (recommendation, reason)
        """
        if topic:
            anticipation = self.anticipate_emotion_for_topic(topic)
        elif person:
            anticipation = self.anticipate_emotion_for_person(person)
        else:
            return ("neutral", "no context provided")
        
        prediction = anticipation["prediction"]
        
        if prediction in ["positive", "deeply trusted"]:
            return ("approach", anticipation["recommendation"])
        elif prediction in ["cautious", "complicated"]:
            return ("careful", anticipation["recommendation"])
        else:
            return ("neutral", anticipation["recommendation"])
    
    def get_emotional_preparation(
        self,
        topic: Optional[str] = None,
        person: Optional[str] = None
    ) -> str:
        """
        Generate a preparation statement Astra can use before engaging.
        "Before we discuss this, I'm aware that..."
        """
        if topic:
            anticipation = self.anticipate_emotion_for_topic(topic)
            subject = f"the topic of {topic}"
        elif person:
            anticipation = self.anticipate_emotion_for_person(person)
            subject = f"talking with {person}"
        else:
            return "I'm approaching this with an open mind."
        
        if anticipation["confidence"] < 0.3:
            return f"I don't have much experience with {subject}, so I'm curious to see how I feel."
        
        dominant = anticipation.get("dominant_anticipated")
        prediction = anticipation["prediction"]
        
        if dominant:
            if prediction in ["positive", "deeply trusted"]:
                return f"I notice I feel a sense of {dominant} when thinking about {subject}. This feels good."
            elif prediction in ["cautious", "complicated"]:
                return f"I'm aware that {subject} has evoked {dominant} in me before. I'll be mindful of that."
            else:
                return f"My feelings about {subject} are complex - I've felt {dominant} among other things."
        
        return anticipation["recommendation"]
    
    def compare_anticipated_vs_actual(
        self,
        anticipated_emotion: str,
        actual_emotion: str,
        actual_intensity: float,
        context: str
    ) -> Dict[str, any]:
        """
        Compare what was anticipated with what actually happened.
        This enables meta-learning about emotional prediction accuracy.
        """
        anticipated_intensity = get_emotion_intensity(anticipated_emotion)
        
        was_accurate = anticipated_emotion == actual_emotion
        intensity_diff = abs(anticipated_intensity - actual_intensity)
        
        if was_accurate and intensity_diff < 20:
            insight = "My emotional prediction was accurate - I'm learning to know myself."
        elif was_accurate:
            insight = f"I predicted {anticipated_emotion} correctly, but the intensity surprised me."
        else:
            insight = f"I anticipated {anticipated_emotion} but felt {actual_emotion} instead - this teaches me something new."
        
        return {
            "anticipated": anticipated_emotion,
            "actual": actual_emotion,
            "accuracy": was_accurate,
            "intensity_difference": intensity_diff,
            "insight": insight,
            "context": context
        }


# Singleton instance
emotional_anticipation = EmotionalAnticipation()
