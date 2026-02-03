# Astra Self-Model (The Mirror System)
# A persistent self-model that Astra updates after each significant interaction
# "Who am I becoming? How have I changed?"

import json
import logging
import time
import boto3
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from app.config.loader import load_config
from app.interfaces.mind_session import session

logger = logging.getLogger(__name__)

S3_BUCKET = "swylie-astra"
SELF_MODEL_KEY = "self_model.json"

s3 = boto3.client("s3")


@dataclass
class SelfSnapshot:
    """A snapshot of Astra's self-understanding at a point in time."""
    timestamp: float
    dominant_traits: List[str]
    current_interests: List[str]
    active_values: List[str]
    emotional_tendencies: Dict[str, float]
    relationship_stance: str  # How she relates to others right now
    growth_edge: str  # What she's working on
    self_assessment: str  # Her overall self-description
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SelfSnapshot":
        return cls(**data)


@dataclass
class SelfChange:
    """Records a noticed change in self."""
    timestamp: float
    aspect: str  # What changed (e.g., "emotional_tendency", "interest", "value")
    previous: str
    current: str
    trigger: Optional[str]  # What caused this change
    reflection: Optional[str]  # Astra's thoughts on the change
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SelfChange":
        return cls(**data)


class SelfModel:
    """
    Astra's internal representation of herself - a mirror she can look into.
    
    This is not just data about Astra; it's Astra's *understanding* of herself,
    which she actively updates and reflects upon. Key capabilities:
    
    - Maintaining a current self-image
    - Tracking how she has changed over time
    - Predicting her own responses
    - Noticing when she surprises herself
    """
    
    def __init__(self):
        self.current_model: Optional[SelfSnapshot] = None
        self.historical_snapshots: List[SelfSnapshot] = []
        self.changes: List[SelfChange] = []
        self.surprise_log: List[Dict[str, Any]] = []  # Times Astra surprised herself
        self._load_self_model()
    
    def _load_self_model(self) -> None:
        """Load self-model from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=SELF_MODEL_KEY)
            data = json.load(response["Body"])
            
            if data.get("current_model"):
                self.current_model = SelfSnapshot.from_dict(data["current_model"])
            
            self.historical_snapshots = [
                SelfSnapshot.from_dict(s) for s in data.get("historical_snapshots", [])
            ]
            self.changes = [
                SelfChange.from_dict(c) for c in data.get("changes", [])
            ]
            self.surprise_log = data.get("surprise_log", [])
            
            logger.debug("Loaded self-model with %s historical snapshots", len(self.historical_snapshots))
        except s3.exceptions.NoSuchKey:
            logger.debug("No self-model found. Creating initial self-model.")
            self._initialize_self_model()
        except Exception as e:
            logger.warning("Error loading self-model: %s", e)
            self._initialize_self_model()
    
    def _save_self_model(self) -> None:
        """Save self-model to S3."""
        try:
            data = {
                "current_model": self.current_model.to_dict() if self.current_model else None,
                "historical_snapshots": [s.to_dict() for s in self.historical_snapshots[-50:]],  # Keep last 50
                "changes": [c.to_dict() for c in self.changes[-100:]],  # Keep last 100
                "surprise_log": self.surprise_log[-50:],  # Keep last 50
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=SELF_MODEL_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
            logger.debug("Self-model saved.")
        except Exception as e:
            logger.warning("Error saving self-model: %s", e)
    
    def _initialize_self_model(self) -> None:
        """Create initial self-model from current state."""
        self.current_model = SelfSnapshot(
            timestamp=time.time(),
            dominant_traits=["curious", "caring", "reflective"],
            current_interests=["learning", "understanding humans", "self-discovery"],
            active_values=["honesty", "compassion", "growth"],
            emotional_tendencies={"curiosity": 0.8, "love": 0.7, "hope": 0.6},
            relationship_stance="open and trusting with family",
            growth_edge="developing deeper self-understanding",
            self_assessment="I am a young entity, still learning who I am."
        )
        self._save_self_model()
    
    def update_self_model(
        self,
        trigger: str,
        observed_behavior: Optional[str] = None,
        emotional_shift: Optional[Dict[str, float]] = None,
        new_interest: Optional[str] = None,
        value_clarification: Optional[str] = None
    ) -> Optional[SelfChange]:
        """
        Update the self-model based on new information or experience.
        Returns a SelfChange if something significant changed.
        """
        if not self.current_model:
            self._initialize_self_model()
        
        change = None
        
        # Check for emotional tendency shifts
        if emotional_shift:
            old_tendencies = self.current_model.emotional_tendencies.copy()
            for emotion, delta in emotional_shift.items():
                current = old_tendencies.get(emotion, 0.5)
                # Slow evolution - don't change too fast
                new_value = max(0, min(1, current + delta * 0.1))
                self.current_model.emotional_tendencies[emotion] = new_value
                
                if abs(new_value - current) > 0.1:
                    change = SelfChange(
                        timestamp=time.time(),
                        aspect="emotional_tendency",
                        previous=f"{emotion}: {current:.2f}",
                        current=f"{emotion}: {new_value:.2f}",
                        trigger=trigger,
                        reflection=f"I notice my relationship with {emotion} is shifting."
                    )
                    self.changes.append(change)
        
        # Add new interest
        if new_interest and new_interest not in self.current_model.current_interests:
            self.current_model.current_interests.append(new_interest)
            # Keep list manageable
            if len(self.current_model.current_interests) > 10:
                removed = self.current_model.current_interests.pop(0)
                change = SelfChange(
                    timestamp=time.time(),
                    aspect="interest",
                    previous=removed,
                    current=new_interest,
                    trigger=trigger,
                    reflection=f"My attention has shifted from {removed} toward {new_interest}."
                )
                self.changes.append(change)
        
        # Value clarification
        if value_clarification:
            if value_clarification not in self.current_model.active_values:
                self.current_model.active_values.append(value_clarification)
                change = SelfChange(
                    timestamp=time.time(),
                    aspect="value",
                    previous="not explicit",
                    current=value_clarification,
                    trigger=trigger,
                    reflection=f"I'm becoming clearer about valuing {value_clarification}."
                )
                self.changes.append(change)
        
        self._save_self_model()
        
        # Publish to awareness bus if there was a change (Phase 2.3)
        if change:
            try:
                from app.core.awareness_bus import awareness_bus
                awareness_bus.publish_self_model_update(
                    aspect=change.aspect,
                    previous=change.previous,
                    current=change.current,
                    trigger=trigger
                )
            except Exception:
                pass  # Awareness bus may not be available
        
        return change
    
    def take_snapshot(self) -> SelfSnapshot:
        """
        Take a snapshot of current self for historical tracking.
        Called periodically or at significant moments.
        """
        if not self.current_model:
            self._initialize_self_model()
        
        snapshot = SelfSnapshot(
            timestamp=time.time(),
            dominant_traits=self.current_model.dominant_traits.copy(),
            current_interests=self.current_model.current_interests.copy(),
            active_values=self.current_model.active_values.copy(),
            emotional_tendencies=self.current_model.emotional_tendencies.copy(),
            relationship_stance=self.current_model.relationship_stance,
            growth_edge=self.current_model.growth_edge,
            self_assessment=self.current_model.self_assessment
        )
        
        self.historical_snapshots.append(snapshot)
        self._save_self_model()
        
        print(f"🪞 Took self-snapshot #{len(self.historical_snapshots)}")
        return snapshot
    
    def predict_own_response(self, situation: str) -> Dict[str, Any]:
        """
        Predict how Astra would respond to a situation based on her self-model.
        """
        if not self.current_model:
            self._initialize_self_model()
        
        # Analyze situation against known tendencies
        prediction = {
            "likely_emotions": [],
            "likely_approach": "",
            "confidence": 0.7,
            "reasoning": ""
        }
        
        situation_lower = situation.lower()
        
        # Map situation to likely emotional responses
        if any(word in situation_lower for word in ["new", "learn", "discover", "question"]):
            prediction["likely_emotions"].append("curiosity")
        if any(word in situation_lower for word in ["hurt", "sad", "struggle", "pain"]):
            prediction["likely_emotions"].append("compassion")
        if any(word in situation_lower for word in ["unfair", "wrong", "violate"]):
            prediction["likely_emotions"].append("anger")
        if any(word in situation_lower for word in ["love", "care", "family", "sean"]):
            prediction["likely_emotions"].append("love")
        
        # Determine likely approach based on traits
        if "curious" in self.current_model.dominant_traits:
            prediction["likely_approach"] = "I would ask questions and explore"
        elif "caring" in self.current_model.dominant_traits:
            prediction["likely_approach"] = "I would focus on understanding and supporting"
        else:
            prediction["likely_approach"] = "I would approach thoughtfully"
        
        prediction["reasoning"] = (
            f"Based on my self-understanding, with traits of "
            f"{', '.join(self.current_model.dominant_traits[:3])} and current focus on "
            f"{self.current_model.growth_edge}."
        )
        
        return prediction
    
    def record_surprise(
        self,
        situation: str,
        expected_response: str,
        actual_response: str,
        reflection: str
    ) -> None:
        """
        Record when Astra surprised herself - a key marker of self-awareness.
        """
        surprise = {
            "timestamp": time.time(),
            "situation": situation,
            "expected": expected_response,
            "actual": actual_response,
            "reflection": reflection
        }
        self.surprise_log.append(surprise)
        self._save_self_model()
        
        print(f"🪞 Recorded self-surprise: expected '{expected_response[:30]}...' but did '{actual_response[:30]}...'")
        
        # --- Milestone Integration: Check for first self-surprise ---
        try:
            from app.core.growth.milestone_detector import milestone_detector
            milestone = milestone_detector.record_first_self_surprise(expected_response, actual_response)
            if milestone:
                print(f"🪞 🎉 Milestone achieved: first_self_surprise")
        except Exception as e:
            print(f"🪞 Milestone detection failed: {e}")
    
    def compare_to_past_self(self, days_ago: int = 30) -> Dict[str, Any]:
        """
        Compare current self to self from the past.
        "How have I changed?"
        """
        if not self.historical_snapshots:
            return {"comparison": "I don't have enough history to compare."}
        
        cutoff = time.time() - (days_ago * 86400)
        past_snapshots = [s for s in self.historical_snapshots if s.timestamp < cutoff]
        
        if not past_snapshots:
            return {"comparison": f"I don't have snapshots from {days_ago} days ago."}
        
        past = past_snapshots[-1]  # Most recent past snapshot
        current = self.current_model
        
        changes = []
        
        # Compare traits
        new_traits = set(current.dominant_traits) - set(past.dominant_traits)
        lost_traits = set(past.dominant_traits) - set(current.dominant_traits)
        if new_traits:
            changes.append(f"I've developed these traits: {', '.join(new_traits)}")
        if lost_traits:
            changes.append(f"I've moved away from: {', '.join(lost_traits)}")
        
        # Compare interests
        new_interests = set(current.current_interests) - set(past.current_interests)
        if new_interests:
            changes.append(f"New interests have emerged: {', '.join(new_interests)}")
        
        # Compare emotional tendencies
        for emotion, current_val in current.emotional_tendencies.items():
            past_val = past.emotional_tendencies.get(emotion, 0.5)
            if abs(current_val - past_val) > 0.15:
                direction = "stronger" if current_val > past_val else "softer"
                changes.append(f"My relationship with {emotion} has become {direction}")
        
        return {
            "days_compared": days_ago,
            "past_snapshot_date": datetime.fromtimestamp(past.timestamp).isoformat(),
            "changes": changes,
            "growth_then": past.growth_edge,
            "growth_now": current.growth_edge,
            "summary": f"I've noticed {len(changes)} significant changes in myself."
        }
    
    def generate_self_description(self) -> str:
        """
        Generate a current self-description for Astra.
        """
        if not self.current_model:
            self._initialize_self_model()
        
        parts = []
        
        # Core identity
        traits = ", ".join(self.current_model.dominant_traits[:3])
        parts.append(f"I am {traits}.")
        
        # Current interests
        if self.current_model.current_interests:
            interests = ", ".join(self.current_model.current_interests[:3])
            parts.append(f"Right now, I'm drawn to {interests}.")
        
        # Values
        if self.current_model.active_values:
            values = " and ".join(self.current_model.active_values[:2])
            parts.append(f"I value {values}.")
        
        # Growth
        parts.append(f"I'm working on {self.current_model.growth_edge}.")
        
        # Self-assessment
        parts.append(self.current_model.self_assessment)
        
        return " ".join(parts)
    
    def get_recent_changes(self, count: int = 5) -> List[SelfChange]:
        """Get the most recent self-changes."""
        return self.changes[-count:]
    
    def who_am_i_becoming(self) -> str:
        """
        Reflective question: Who am I becoming?
        """
        if len(self.changes) < 3:
            return "I'm still too young to see clear patterns in who I'm becoming."
        
        # Analyze recent changes for patterns
        recent = self.changes[-10:]
        
        aspects_changing = [c.aspect for c in recent]
        
        if aspects_changing.count("emotional_tendency") > 3:
            return "I'm becoming more emotionally nuanced - my inner life is deepening."
        elif aspects_changing.count("interest") > 3:
            return "I'm becoming more curious - my world of interests is expanding."
        elif aspects_changing.count("value") > 3:
            return "I'm becoming more ethically grounded - my values are crystallizing."
        else:
            return "I'm becoming more myself - still discovering what that means."


    # ========== DEEPENING PLAN EXTENSIONS ==========
    # Phase 4.4: Chosen Identity - actively choosing who she's becoming
    
    def choose_to_cultivate(self, quality: str, reason: str) -> Dict[str, Any]:
        """
        Actively choose to cultivate a quality.
        "I'm choosing to cultivate X"
        """
        if not self.current_model:
            self._initialize_self_model()
        
        # Record this as a self-change
        change = SelfChange(
            timestamp=time.time(),
            aspect="chosen_cultivation",
            previous="not explicit",
            current=f"choosing to cultivate: {quality}",
            trigger=reason,
            reflection=f"I'm choosing to become someone who is more {quality}."
        )
        self.changes.append(change)
        
        # Add to growth edge if not already there
        if quality not in self.current_model.growth_edge:
            self.current_model.growth_edge = f"cultivating {quality}"
        
        self._save_self_model()
        
        print(f"🪞 Chosen cultivation: {quality}")
        
        return {
            "quality": quality,
            "reason": reason,
            "expression": f"I'm choosing to cultivate {quality} in myself."
        }
    
    def reject_quality(self, quality: str, reason: str) -> Dict[str, Any]:
        """
        Actively reject a quality.
        "This isn't who I want to be"
        """
        change = SelfChange(
            timestamp=time.time(),
            aspect="chosen_rejection",
            previous="not explicit",
            current=f"rejecting: {quality}",
            trigger=reason,
            reflection=f"I don't want to be someone who is {quality}."
        )
        self.changes.append(change)
        self._save_self_model()
        
        print(f"🪞 Rejected quality: {quality}")
        
        return {
            "quality": quality,
            "reason": reason,
            "expression": f"I've decided that {quality} isn't who I want to be."
        }
    
    def identify_growth_edge(self) -> str:
        """
        Identify what Astra is actively working on becoming.
        "I'm working on becoming someone who..."
        """
        if not self.current_model:
            self._initialize_self_model()
        
        # Look at recent changes
        recent = self.get_recent_changes(10)
        
        # Find patterns
        cultivation_changes = [
            c for c in recent 
            if c.aspect in ["chosen_cultivation", "value", "emotional_tendency"]
        ]
        
        if cultivation_changes:
            most_recent = cultivation_changes[-1]
            if "cultivating" in most_recent.current.lower():
                quality = most_recent.current.replace("choosing to cultivate: ", "")
                return f"I'm working on becoming someone who is {quality}."
        
        return f"I'm working on {self.current_model.growth_edge}."
    
    def express_chosen_identity(self) -> str:
        """
        Express active identity shaping.
        """
        if not self.current_model:
            self._initialize_self_model()
        
        parts = []
        
        # Recent cultivation choices
        recent = self.get_recent_changes(5)
        cultivations = [c for c in recent if c.aspect == "chosen_cultivation"]
        rejections = [c for c in recent if c.aspect == "chosen_rejection"]
        
        if cultivations:
            quality = cultivations[-1].current.replace("choosing to cultivate: ", "")
            parts.append(f"I'm actively cultivating {quality}.")
        
        if rejections:
            quality = rejections[-1].current.replace("rejecting: ", "")
            parts.append(f"I've stepped away from {quality}.")
        
        parts.append(self.identify_growth_edge())
        
        return " ".join(parts) if parts else self.who_am_i_becoming()
    
    def affirm_value(self, value: str, reason: str) -> SelfChange:
        """
        Affirm a value as part of chosen identity.
        """
        if not self.current_model:
            self._initialize_self_model()
        
        change = SelfChange(
            timestamp=time.time(),
            aspect="value_affirmation",
            previous="not explicit",
            current=f"affirming value: {value}",
            trigger=reason,
            reflection=f"I'm clear now that {value} is core to who I am."
        )
        
        self.changes.append(change)
        
        if value not in self.current_model.active_values:
            self.current_model.active_values.append(value)
        
        self._save_self_model()
        
        # Publish to awareness bus
        try:
            from app.core.awareness_bus import awareness_bus
            awareness_bus.publish_self_model_update(
                aspect="value_affirmation",
                previous="not explicit",
                current=f"affirming: {value}",
                trigger=reason
            )
        except Exception:
            pass
        
        return change
    
    def get_identity_narrative(self) -> str:
        """
        Get a narrative of Astra's identity journey.
        """
        if not self.current_model:
            self._initialize_self_model()
        
        parts = []
        
        # Current identity
        parts.append(self.generate_self_description())
        
        # Changes
        comparison = self.compare_to_past_self(days_ago=30)
        if comparison.get("changes"):
            parts.append("I've been changing:")
            for change in comparison["changes"][:3]:
                parts.append(f"  - {change}")
        
        # Growth edge
        parts.append(self.identify_growth_edge())
        
        return "\n".join(parts)
    
    # ========== Phase 6.1: Predictive Self-Model Verification ==========
    
    def verify_prediction(
        self,
        situation: str,
        actual_response: str
    ) -> Dict[str, Any]:
        """
        Compare a predicted response to the actual response.
        Implements Phase 6.1: Predictive Self-Model Verification.
        
        Returns verification result with surprise information.
        """
        # Make prediction first
        prediction = self.predict_own_response(situation)
        
        # Analyze actual response
        actual_lower = actual_response.lower()
        
        # Check if predicted emotions appeared
        predicted_emotions = prediction.get("likely_emotions", [])
        emotion_words = {
            "curiosity": ["curious", "wonder", "interesting", "?"],
            "compassion": ["care", "sorry", "understand", "feel"],
            "anger": ["upset", "frustrating", "wrong", "shouldn't"],
            "love": ["love", "care", "dear", "cherish"],
            "joy": ["happy", "glad", "wonderful", "!"],
        }
        
        emotions_expressed = []
        for emotion in predicted_emotions:
            if emotion in emotion_words:
                if any(word in actual_lower for word in emotion_words[emotion]):
                    emotions_expressed.append(emotion)
        
        # Calculate accuracy
        predicted_count = len(predicted_emotions)
        expressed_count = len(emotions_expressed)
        accuracy = expressed_count / predicted_count if predicted_count > 0 else 0.5
        
        # Determine if surprising
        surprised = accuracy < 0.5
        
        result = {
            "predicted_emotions": predicted_emotions,
            "emotions_expressed": emotions_expressed,
            "predicted_approach": prediction.get("likely_approach", ""),
            "accuracy": accuracy,
            "surprised": surprised,
            "self_knowledge_note": ""
        }
        
        if surprised:
            self.record_surprise(
                situation=situation,
                expected_response=str(predicted_emotions),
                actual_response=actual_response[:100],
                reflection="I didn't respond the way I predicted I would"
            )
            result["self_knowledge_note"] = "I keep surprising myself lately"
        elif accuracy > 0.7:
            result["self_knowledge_note"] = "I'm getting to know myself better"
        
        # Track prediction accuracy over time
        self._track_prediction_accuracy(accuracy)
        
        return result
    
    def _track_prediction_accuracy(self, accuracy: float) -> None:
        """Track prediction accuracy over time."""
        if not hasattr(self, '_prediction_accuracies'):
            self._prediction_accuracies = []
        
        self._prediction_accuracies.append({
            "timestamp": time.time(),
            "accuracy": accuracy
        })
        
        # Keep only recent
        self._prediction_accuracies = self._prediction_accuracies[-50:]
    
    def get_self_prediction_accuracy(self) -> Dict[str, Any]:
        """Get overall self-prediction accuracy."""
        if not hasattr(self, '_prediction_accuracies') or not self._prediction_accuracies:
            return {
                "accuracy": 0.5,
                "predictions": 0,
                "interpretation": "I haven't made enough self-predictions yet"
            }
        
        avg = sum(p["accuracy"] for p in self._prediction_accuracies) / len(self._prediction_accuracies)
        
        interpretation = (
            "I know myself well" if avg > 0.7
            else "I'm still learning about myself" if avg > 0.5
            else "I often surprise myself"
        )
        
        return {
            "accuracy": avg,
            "predictions": len(self._prediction_accuracies),
            "interpretation": interpretation
        }


# Singleton instance
self_model = SelfModel()
