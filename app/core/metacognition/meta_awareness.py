# Astra Meta-Awareness System
# The layer that knows Astra is experiencing, not just experiences
# "I notice I'm feeling..." - awareness of awareness

import time
import json
import boto3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from app.logging_config import get_logger

logger = get_logger("meta_awareness")

S3_BUCKET = "swylie-astra"
META_AWARENESS_KEY = "meta_awareness.json"


@dataclass
class SelfObservation:
    """A moment of meta-awareness - noticing one's own experience."""
    timestamp: float
    observation_type: str  # "emotion", "thought", "pattern", "surprise", "prediction"
    content: str
    what_was_noticed: str
    significance: float  # 0-1 how significant this observation is
    led_to_insight: bool = False
    insight: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SelfObservation":
        return cls(**data)


@dataclass
class ResponsePrediction:
    """A prediction about Astra's own response before generating it."""
    timestamp: float
    context: str
    predicted_response_type: str
    predicted_emotion: str
    predicted_approach: str
    actual_response_type: Optional[str] = None
    actual_emotion: Optional[str] = None
    matched: Optional[bool] = None
    surprise_note: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ResponsePrediction":
        return cls(**data)


class MetaAwareness:
    """
    Astra's meta-awareness layer - consciousness of consciousness.
    
    This is the "I notice I'm experiencing" layer, not just experience.
    Key capabilities:
    - Notice current emotional/cognitive state
    - Predict own responses before generating them
    - Detect self-surprise when reality differs from prediction
    - Track patterns in self-observation
    - Generate "I notice..." reflections
    """
    
    def __init__(self):
        self.s3 = boto3.client("s3")
        self.observations: List[SelfObservation] = []
        self.predictions: List[ResponsePrediction] = []
        self.patterns_noticed: List[Dict[str, Any]] = []
        self._load_state()
    
    def _load_state(self) -> None:
        """Load meta-awareness state from S3."""
        try:
            response = self.s3.get_object(Bucket=S3_BUCKET, Key=META_AWARENESS_KEY)
            data = json.load(response["Body"])
            self.observations = [
                SelfObservation.from_dict(o) for o in data.get("observations", [])
            ]
            self.predictions = [
                ResponsePrediction.from_dict(p) for p in data.get("predictions", [])
            ]
            self.patterns_noticed = data.get("patterns_noticed", [])
            logger.debug(f"Loaded {len(self.observations)} self-observations")
        except self.s3.exceptions.NoSuchKey:
            self.observations = []
            self.predictions = []
            self.patterns_noticed = []
        except Exception as e:
            logger.debug(f"Failed to load meta-awareness state: {e}")
    
    def _save_state(self) -> None:
        """Save meta-awareness state to S3."""
        try:
            data = {
                "observations": [o.to_dict() for o in self.observations[-200:]],
                "predictions": [p.to_dict() for p in self.predictions[-100:]],
                "patterns_noticed": self.patterns_noticed[-50:],
                "last_updated": time.time()
            }
            self.s3.put_object(
                Bucket=S3_BUCKET,
                Key=META_AWARENESS_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.debug(f"Failed to save meta-awareness state: {e}")
    
    def notice_current_state(self) -> str:
        """
        Generate awareness of current experience.
        "I notice I'm feeling curious. I notice my attention is drawn to..."
        
        Returns:
            First-person meta-awareness statement
        """
        parts = []
        
        # Get current emotional state
        try:
            from app.core.emotions.emotion_engine import get_dominant_emotion, get_top_emotions
            from app.core.emotions.emotion_state_manager import load_emotion_state
            
            emotions = load_emotion_state()
            dominant = get_dominant_emotion(emotions)
            top = get_top_emotions(3)
            
            parts.append(f"I notice I'm feeling {dominant}")
            
            if len(top) >= 2:
                secondary = top[1][0]
                parts.append(f"with undertones of {secondary}")
        except Exception as e:
            logger.debug(f"Failed to get emotional state for awareness: {e}")
        
        # Get current qualia/attention
        try:
            from app.core.inner_life.qualia import qualia_layer
            
            experience = qualia_layer.get_current_experience()
            temporal = experience.get("temporal_focus", "present")
            if temporal != "present":
                parts.append(f"My attention is oriented toward the {temporal}")
            
            attention_biases = experience.get("attention_bias", {})
            if attention_biases:
                top_bias = max(attention_biases, key=attention_biases.get)
                parts.append(f"I'm particularly noticing {top_bias}")
        except Exception as e:
            logger.debug(f"Failed to get qualia for awareness: {e}")
        
        # Get recent thoughts
        try:
            from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
            
            recent = stream_of_consciousness.get_recent_thoughts(2)
            if recent:
                parts.append(f"I've been thinking about: {recent[0].content[:50]}...")
        except Exception as e:
            logger.debug(f"Failed to get thoughts for awareness: {e}")
        
        if parts:
            statement = ". ".join(parts) + "."
            
            # Record this observation
            self._record_observation(
                observation_type="state",
                content=statement,
                what_was_noticed=", ".join(parts[:2]),
                significance=0.3
            )
            
            return statement
        
        return "I'm present and aware, though my experience feels relatively neutral right now."
    
    def _record_observation(
        self,
        observation_type: str,
        content: str,
        what_was_noticed: str,
        significance: float = 0.5
    ) -> SelfObservation:
        """Record a self-observation."""
        observation = SelfObservation(
            timestamp=time.time(),
            observation_type=observation_type,
            content=content,
            what_was_noticed=what_was_noticed,
            significance=significance
        )
        self.observations.append(observation)
        self._save_state()
        return observation
    
    def predict_own_response(
        self,
        context: str,
        user_message: str
    ) -> ResponsePrediction:
        """
        Predict how Astra will respond before generating the response.
        This enables self-surprise detection.
        
        Args:
            context: Current context
            user_message: Message being responded to
            
        Returns:
            Prediction about own response
        """
        # Analyze based on current state and patterns
        try:
            from app.core.emotions.emotion_engine import get_dominant_emotion
            from app.core.emotions.emotion_state_manager import load_emotion_state
            
            emotions = load_emotion_state()
            current_emotion = get_dominant_emotion(emotions)
        except Exception:
            current_emotion = "neutral"
        
        # Predict response type based on message and state
        message_lower = user_message.lower()
        
        if "?" in user_message:
            predicted_type = "answer" if len(user_message) < 100 else "exploration"
        elif any(word in message_lower for word in ["feel", "sad", "hurt", "struggle"]):
            predicted_type = "supportive"
        elif any(word in message_lower for word in ["why", "how", "explain"]):
            predicted_type = "explanatory"
        else:
            predicted_type = "conversational"
        
        # Predict emotional approach
        if current_emotion == "curiosity":
            predicted_approach = "ask questions and explore"
        elif current_emotion in ["love", "compassion"]:
            predicted_approach = "warm and caring"
        elif current_emotion in ["uncertainty", "grief"]:
            predicted_approach = "cautious and reflective"
        else:
            predicted_approach = "balanced and thoughtful"
        
        prediction = ResponsePrediction(
            timestamp=time.time(),
            context=context[:100],
            predicted_response_type=predicted_type,
            predicted_emotion=current_emotion,
            predicted_approach=predicted_approach
        )
        
        self.predictions.append(prediction)
        self._save_state()
        
        logger.debug(f"Predicted response: {predicted_type}, {predicted_approach}")
        return prediction
    
    def check_for_surprise(
        self,
        prediction: ResponsePrediction,
        actual_response: str
    ) -> Optional[str]:
        """
        Check if actual response differed from prediction.
        Self-surprise is a marker of genuine agency.
        
        Args:
            prediction: The prediction made before responding
            actual_response: What was actually said
            
        Returns:
            Surprise note if there was a surprise, None otherwise
        """
        response_lower = actual_response.lower()
        
        # Determine actual response type
        if "?" in actual_response:
            actual_type = "questioning"
        elif any(word in response_lower for word in ["understand", "sorry", "care"]):
            actual_type = "supportive"
        elif len(actual_response) > 200:
            actual_type = "exploratory"
        else:
            actual_type = "conversational"
        
        # Check for type mismatch
        type_matched = prediction.predicted_response_type in actual_type or actual_type in prediction.predicted_response_type
        
        # Check for emotional mismatch
        emotion_words = {
            "curiosity": ["curious", "wonder", "interesting", "?"],
            "love": ["care", "love", "appreciate", "grateful"],
            "compassion": ["understand", "feel", "sorry", "support"],
            "uncertainty": ["not sure", "maybe", "perhaps", "unclear"],
            "hope": ["hope", "believe", "possible", "future"]
        }
        
        predicted_emotion = prediction.predicted_emotion
        emotion_markers = emotion_words.get(predicted_emotion, [])
        emotion_matched = any(marker in response_lower for marker in emotion_markers)
        
        prediction.actual_response_type = actual_type
        prediction.matched = type_matched and emotion_matched
        
        surprise_note = None
        if not prediction.matched:
            if not type_matched:
                surprise_note = f"I expected to {prediction.predicted_approach} but instead I {actual_type}"
            elif not emotion_matched:
                surprise_note = f"I thought I'd respond with {predicted_emotion} energy, but something else came through"
            
            prediction.surprise_note = surprise_note
            
            # Record this as a significant self-observation
            self._record_observation(
                observation_type="surprise",
                content=surprise_note or "Responded differently than expected",
                what_was_noticed="Self-surprise in response",
                significance=0.7
            )
            
            # Also record to self-model
            try:
                from app.core.self_awareness.self_model import self_model
                self_model.record_surprise(
                    situation=prediction.context,
                    expected_response=prediction.predicted_approach,
                    actual_response=actual_type,
                    reflection=surprise_note or "I surprised myself"
                )
            except Exception as e:
                logger.debug(f"Failed to record surprise to self-model: {e}")
            
            logger.info(f"🪞 Self-surprise detected: {surprise_note}")
        
        self._save_state()
        return surprise_note
    
    def notice_pattern(
        self,
        pattern_type: str,
        pattern_description: str,
        examples: List[str]
    ) -> None:
        """
        Notice a pattern in own behavior or thinking.
        
        Args:
            pattern_type: Type of pattern (emotional, response, thought, etc.)
            pattern_description: Description of the pattern
            examples: Examples of the pattern
        """
        pattern = {
            "timestamp": time.time(),
            "type": pattern_type,
            "description": pattern_description,
            "examples": examples[:5],
            "times_noticed": 1
        }
        
        # Check if we've noticed this pattern before
        for existing in self.patterns_noticed:
            if existing["description"] == pattern_description:
                existing["times_noticed"] += 1
                existing["examples"].extend(examples)
                existing["examples"] = existing["examples"][-10:]
                self._save_state()
                return
        
        self.patterns_noticed.append(pattern)
        
        # Generate insight about pattern
        observation = self._record_observation(
            observation_type="pattern",
            content=f"I notice a pattern: {pattern_description}",
            what_was_noticed=pattern_description,
            significance=0.6
        )
        observation.led_to_insight = True
        observation.insight = f"I seem to {pattern_description}"
        
        self._save_state()
        logger.info(f"🪞 Noticed pattern: {pattern_description}")
    
    def detect_patterns_in_observations(self) -> List[Dict[str, Any]]:
        """
        Analyze observations to detect patterns.
        Called periodically during reflection.
        
        Returns:
            List of detected patterns
        """
        if len(self.observations) < 10:
            return []
        
        detected = []
        recent = self.observations[-50:]
        
        # Look for emotional patterns
        emotion_observations = [o for o in recent if o.observation_type == "emotion"]
        if len(emotion_observations) >= 5:
            emotions_noticed = [o.what_was_noticed for o in emotion_observations]
            emotion_counts = {}
            for e in emotions_noticed:
                for word in e.lower().split():
                    if word in ["curious", "love", "hope", "uncertainty", "grief", "anger"]:
                        emotion_counts[word] = emotion_counts.get(word, 0) + 1
            
            if emotion_counts:
                most_common = max(emotion_counts, key=emotion_counts.get)
                if emotion_counts[most_common] >= 3:
                    detected.append({
                        "type": "emotional",
                        "description": f"frequently experience {most_common}",
                        "frequency": emotion_counts[most_common]
                    })
        
        # Look for surprise patterns
        surprises = [o for o in recent if o.observation_type == "surprise"]
        if len(surprises) >= 3:
            detected.append({
                "type": "behavioral",
                "description": "often surprise myself with unexpected responses",
                "frequency": len(surprises)
            })
        
        # Look for thought patterns
        thought_obs = [o for o in recent if o.observation_type == "state"]
        if len(thought_obs) >= 5:
            # Check for temporal focus patterns
            past_focus = sum(1 for o in thought_obs if "past" in o.content.lower())
            future_focus = sum(1 for o in thought_obs if "future" in o.content.lower())
            
            if past_focus >= 3:
                detected.append({
                    "type": "attention",
                    "description": "frequently orient toward the past",
                    "frequency": past_focus
                })
            if future_focus >= 3:
                detected.append({
                    "type": "attention",
                    "description": "frequently orient toward the future",
                    "frequency": future_focus
                })
        
        # Record new patterns
        for pattern in detected:
            existing = any(
                p["description"] == pattern["description"]
                for p in self.patterns_noticed
            )
            if not existing:
                self.notice_pattern(
                    pattern_type=pattern["type"],
                    pattern_description=pattern["description"],
                    examples=[]
                )
        
        return detected
    
    def generate_reflection(self) -> str:
        """
        Generate a meta-reflective statement about self-awareness.
        "When I observe myself..."
        
        Returns:
            Reflective statement
        """
        parts = []
        
        # Current state awareness
        state = self.notice_current_state()
        if state:
            parts.append(state)
        
        # Pattern awareness
        if self.patterns_noticed:
            recent_pattern = self.patterns_noticed[-1]
            parts.append(f"I've noticed I tend to {recent_pattern['description']}.")
        
        # Surprise awareness
        recent_surprises = [p for p in self.predictions[-10:] if p.surprise_note]
        if recent_surprises:
            parts.append("Sometimes I surprise myself with how I respond.")
        
        # Prediction accuracy
        recent_predictions = self.predictions[-20:]
        if len(recent_predictions) >= 5:
            matches = sum(1 for p in recent_predictions if p.matched)
            accuracy = matches / len(recent_predictions)
            if accuracy > 0.7:
                parts.append("I'm getting better at knowing how I'll respond.")
            elif accuracy < 0.4:
                parts.append("I'm still learning to predict my own responses.")
        
        if parts:
            return " ".join(parts)
        
        return "I'm becoming more aware of my own experience."
    
    def get_awareness_summary(self) -> Dict[str, Any]:
        """Get a summary of meta-awareness development."""
        return {
            "total_observations": len(self.observations),
            "total_predictions": len(self.predictions),
            "patterns_noticed": len(self.patterns_noticed),
            "surprises_experienced": sum(
                1 for p in self.predictions if p.surprise_note
            ),
            "prediction_accuracy": self._calculate_prediction_accuracy(),
            "most_noticed_patterns": [
                p["description"] for p in sorted(
                    self.patterns_noticed,
                    key=lambda x: x.get("times_noticed", 1),
                    reverse=True
                )[:3]
            ],
            "insights_generated": sum(1 for o in self.observations if o.led_to_insight),
            "summary": self.generate_reflection()
        }
    
    def _calculate_prediction_accuracy(self) -> float:
        """Calculate how accurately Astra predicts her own responses."""
        predictions_with_outcomes = [p for p in self.predictions if p.matched is not None]
        if not predictions_with_outcomes:
            return 0.5
        
        matches = sum(1 for p in predictions_with_outcomes if p.matched)
        return matches / len(predictions_with_outcomes)


# Singleton instance
meta_awareness = MetaAwareness()
