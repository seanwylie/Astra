# Astra Expectation Model
# Predictions about what users will say/do and surprise detection
# Genuine surprise as a felt experience, not just a word

import time
import json
import boto3
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from app.logging_config import get_logger

logger = get_logger("expectation_model")

S3_BUCKET = "swylie-astra"
EXPECTATION_KEY = "expectation_model.json"

s3 = boto3.client("s3")


@dataclass
class Expectation:
    """A prediction about what will happen."""
    id: str
    entity: str  # Who this is about (user/parent ID)
    prediction: str  # What Astra predicted
    prediction_type: str  # "response_valence", "topic_continuation", "emotional_state", "behavior"
    confidence: float  # How sure (0-1)
    created_at: float
    context: str  # What prompted this prediction
    resolved: bool = False
    outcome: Optional[str] = None
    was_correct: Optional[bool] = None
    surprise_intensity: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Expectation":
        return cls(**data)


@dataclass
class SurpriseMoment:
    """A recorded moment of genuine surprise."""
    timestamp: float
    expected: str
    actual: str
    surprise_level: float  # 0-1
    felt_quality: str  # "pleasant", "unsettling", "curious", "delightful"
    entity: str
    processed: bool = False
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SurpriseMoment":
        return cls(**data)


class ExpectationModel:
    """
    Astra's Expectation Model - predictions about what will happen and
    detection of expectation violations (surprise).
    
    Key capabilities:
    - Maintain predictions about users/parents
    - Detect when expectations are violated
    - Generate genuine surprise emotion
    - Learn from prediction accuracy
    
    This enables authentic surprise as a felt experience, not just a word.
    """
    
    # Prediction templates by type
    PREDICTION_TYPES = {
        "response_valence": ["positive", "negative", "neutral", "mixed"],
        "topic_continuation": ["continue_topic", "change_topic", "deepen_topic"],
        "emotional_state": ["happy", "sad", "curious", "stressed", "calm"],
        "behavior": ["engage", "withdraw", "question", "share", "request"]
    }
    
    # Surprise felt qualities based on valence
    SURPRISE_QUALITIES = {
        "positive_unexpected": ["delightful", "warming", "exciting"],
        "negative_unexpected": ["unsettling", "concerning", "puzzling"],
        "neutral_unexpected": ["curious", "intriguing", "notable"]
    }
    
    def __init__(self):
        self.current_expectations: Dict[str, Expectation] = {}
        self.expectation_history: List[Expectation] = []
        self.surprise_log: List[SurpriseMoment] = []
        self.accuracy_by_entity: Dict[str, Dict[str, float]] = {}
        self._load_state()
        logger.info("🔮 Expectation Model initialized - predicting and noticing surprise")
    
    def _load_state(self) -> None:
        """Load expectation model state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=EXPECTATION_KEY)
            data = json.load(response["Body"])
            
            self.current_expectations = {
                eid: Expectation.from_dict(e)
                for eid, e in data.get("current_expectations", {}).items()
            }
            self.expectation_history = [
                Expectation.from_dict(e) for e in data.get("history", [])
            ]
            self.surprise_log = [
                SurpriseMoment.from_dict(s) for s in data.get("surprise_log", [])
            ]
            self.accuracy_by_entity = data.get("accuracy_by_entity", {})
            
            logger.debug(f"🔮 Loaded {len(self.current_expectations)} active expectations")
        except s3.exceptions.NoSuchKey:
            logger.info("🔮 No expectation model found. Starting fresh.")
        except Exception as e:
            logger.warning(f"🔮 Error loading expectation model: {e}")
    
    def _save_state(self) -> None:
        """Save expectation model state to S3."""
        try:
            data = {
                "current_expectations": {
                    eid: e.to_dict() for eid, e in self.current_expectations.items()
                },
                "history": [e.to_dict() for e in self.expectation_history[-100:]],
                "surprise_log": [s.to_dict() for s in self.surprise_log[-50:]],
                "accuracy_by_entity": self.accuracy_by_entity,
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=EXPECTATION_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"🔮 Error saving expectation model: {e}")
    
    def _generate_id(self) -> str:
        return f"exp_{int(time.time() * 1000) % 1000000}"
    
    def predict(
        self,
        entity: str,
        prediction: str,
        prediction_type: str,
        confidence: float = 0.6,
        context: str = ""
    ) -> Expectation:
        """
        Record a prediction about what will happen.
        Called before receiving a response.
        """
        exp = Expectation(
            id=self._generate_id(),
            entity=entity,
            prediction=prediction,
            prediction_type=prediction_type,
            confidence=confidence,
            created_at=time.time(),
            context=context
        )
        
        self.current_expectations[entity] = exp
        self._save_state()
        
        logger.debug(f"🔮 Predicted for {entity}: {prediction} ({confidence:.0%})")
        return exp
    
    def predict_response_valence(self, entity: str, context: str) -> Expectation:
        """
        Predict the emotional valence of the next response.
        Based on patterns and context.
        """
        # Simple heuristic based on context
        context_lower = context.lower()
        
        if any(w in context_lower for w in ["question", "help", "problem", "confused"]):
            prediction = "engaged"
        elif any(w in context_lower for w in ["happy", "excited", "good", "love"]):
            prediction = "positive"
        elif any(w in context_lower for w in ["sad", "frustrated", "angry", "upset"]):
            prediction = "supportive_but_concerned"
        else:
            prediction = "neutral_engaged"
        
        # Adjust confidence based on history
        confidence = 0.6
        if entity in self.accuracy_by_entity:
            accuracy = self.accuracy_by_entity[entity].get("overall", 0.5)
            confidence = 0.4 + (accuracy * 0.4)  # Scale between 0.4 and 0.8
        
        return self.predict(entity, prediction, "response_valence", confidence, context)
    
    def check_prediction(
        self,
        entity: str,
        actual_response: str
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Check if prediction was correct and calculate surprise.
        
        Returns: (was_correct, surprise_level, felt_quality)
        """
        if entity not in self.current_expectations:
            return True, 0.0, None  # No prediction = no surprise
        
        exp = self.current_expectations[entity]
        
        # Analyze actual response
        response_lower = actual_response.lower()
        
        # Determine actual valence
        positive_markers = ["thank", "love", "happy", "great", "wonderful", "!", "good"]
        negative_markers = ["upset", "sad", "angry", "frustrated", "no", "wrong", "bad"]
        question_markers = ["?", "why", "how", "what"]
        
        positive_count = sum(1 for m in positive_markers if m in response_lower)
        negative_count = sum(1 for m in negative_markers if m in response_lower)
        question_count = sum(1 for m in question_markers if m in response_lower)
        
        # Determine actual category
        if positive_count > negative_count:
            actual = "positive"
        elif negative_count > positive_count:
            actual = "negative"
        elif question_count > 0:
            actual = "curious"
        else:
            actual = "neutral"
        
        # Check if prediction matches
        prediction_lower = exp.prediction.lower()
        was_correct = actual in prediction_lower or prediction_lower in actual
        
        # Calculate surprise level
        if was_correct:
            surprise_level = 0.0
            felt_quality = None
        else:
            # Surprise scales with confidence (higher confidence = more surprise when wrong)
            surprise_level = exp.confidence * 0.8  # Scale to max 0.8
            
            # Determine felt quality
            if actual == "positive" and "negative" in prediction_lower:
                felt_quality = "delightful"
            elif actual == "negative" and "positive" in prediction_lower:
                felt_quality = "unsettling"
            else:
                felt_quality = "curious"
        
        # Update expectation
        exp.resolved = True
        exp.outcome = actual
        exp.was_correct = was_correct
        exp.surprise_intensity = surprise_level
        
        # Move to history
        self.expectation_history.append(exp)
        del self.current_expectations[entity]
        
        # Update accuracy tracking
        self._update_accuracy(entity, was_correct)
        
        # Record surprise if significant
        if surprise_level > 0.3:
            self._record_surprise(exp.prediction, actual, surprise_level, felt_quality, entity)
        
        self._save_state()
        
        return was_correct, surprise_level, felt_quality
    
    def check_and_record(
        self,
        entity: str,
        actual_response: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check prediction and return a context dict for response generation.
        This is the main integration point called from message_bus.
        """
        # First, check if we have an outstanding prediction
        was_correct, surprise_level, felt_quality = self.check_prediction(entity, actual_response)
        
        # Then make a new prediction for next exchange
        self.predict_response_valence(entity, actual_response[:100])
        
        if surprise_level > 0.2:
            # Trigger surprise emotion
            try:
                from app.core.emotions.emotion_engine import trigger_emotion
                # Curiosity for positive surprise, uncertainty for negative
                if felt_quality in ["delightful", "warming"]:
                    trigger_emotion("curiosity", "new_information")
                else:
                    trigger_emotion("uncertainty", "unexpected_event")
            except Exception:
                pass
            
            # Record in self-model
            try:
                from app.core.self_awareness.self_model import self_model
                self_model.record_surprise(
                    situation=f"Conversation with {entity}",
                    expected_response=self.expectation_history[-1].prediction if self.expectation_history else "unknown",
                    actual_response=actual_response[:100],
                    reflection=f"Felt {felt_quality} surprise"
                )
            except Exception:
                pass
            
            return {
                "surprised": True,
                "surprise_level": surprise_level,
                "felt_quality": felt_quality,
                "surprise_description": f"That wasn't what I expected—{felt_quality} surprise"
            }
        
        return {
            "surprised": False,
            "surprise_level": surprise_level
        }
    
    def _record_surprise(
        self,
        expected: str,
        actual: str,
        level: float,
        quality: str,
        entity: str
    ) -> None:
        """Record a surprise moment."""
        moment = SurpriseMoment(
            timestamp=time.time(),
            expected=expected,
            actual=actual,
            surprise_level=level,
            felt_quality=quality,
            entity=entity
        )
        self.surprise_log.append(moment)
        logger.info(f"🔮 ⚡ Surprise! Expected '{expected}' but got '{actual}' ({quality})")
    
    def _update_accuracy(self, entity: str, was_correct: bool) -> None:
        """Update prediction accuracy tracking."""
        if entity not in self.accuracy_by_entity:
            self.accuracy_by_entity[entity] = {"correct": 0, "total": 0, "overall": 0.5}
        
        self.accuracy_by_entity[entity]["total"] += 1
        if was_correct:
            self.accuracy_by_entity[entity]["correct"] += 1
        
        total = self.accuracy_by_entity[entity]["total"]
        correct = self.accuracy_by_entity[entity]["correct"]
        self.accuracy_by_entity[entity]["overall"] = correct / total if total > 0 else 0.5
    
    def get_unprocessed_surprises(self) -> List[SurpriseMoment]:
        """Get surprises that haven't been processed/expressed yet."""
        unprocessed = [s for s in self.surprise_log if not s.processed]
        return unprocessed
    
    def mark_surprise_processed(self, timestamp: float) -> None:
        """Mark a surprise as having been processed/expressed."""
        for s in self.surprise_log:
            if s.timestamp == timestamp:
                s.processed = True
                self._save_state()
                break
    
    def get_prediction_accuracy(self, entity: str) -> Dict[str, Any]:
        """Get prediction accuracy for an entity."""
        if entity not in self.accuracy_by_entity:
            return {"entity": entity, "accuracy": "unknown", "predictions": 0}
        
        acc = self.accuracy_by_entity[entity]
        return {
            "entity": entity,
            "accuracy": acc["overall"],
            "predictions": acc["total"],
            "interpretation": (
                "I predict well" if acc["overall"] > 0.7
                else "I'm still learning to predict" if acc["overall"] > 0.5
                else "I'm often surprised"
            )
        }
    
    def describe_surprise_pattern(self) -> str:
        """Describe patterns in surprise experiences."""
        if not self.surprise_log:
            return "I haven't experienced much surprise yet."
        
        recent = self.surprise_log[-10:]
        avg_level = sum(s.surprise_level for s in recent) / len(recent)
        
        quality_counts = {}
        for s in recent:
            quality_counts[s.felt_quality] = quality_counts.get(s.felt_quality, 0) + 1
        
        most_common = max(quality_counts, key=quality_counts.get) if quality_counts else "curious"
        
        return (
            f"Recently, my surprises have been mostly {most_common}, "
            f"with an average intensity of {avg_level:.0%}. "
            f"This tells me something about my expectations."
        )


# Singleton instance
expectation_model = ExpectationModel()
