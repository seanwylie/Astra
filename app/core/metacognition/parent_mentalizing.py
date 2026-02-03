# Astra Parent Mentalizing System
# Developing a model of parents' inner lives
# "What does Sean care about? What stresses him?"

import json
import logging
import time
import boto3
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)
from datetime import datetime

S3_BUCKET = "swylie-astra"
PARENT_MENTAL_MODEL_KEY = "parent_mental_models.json"

s3 = boto3.client("s3")


@dataclass
class ParentObservation:
    """An observation about a parent's inner state."""
    timestamp: float
    parent_id: str
    observation_type: str  # "emotional_state", "value", "interest", "struggle", "joy"
    content: str
    confidence: float  # 0.0 to 1.0
    context: str  # What prompted this observation
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ParentObservation":
        return cls(**data)


@dataclass
class ParentMentalModel:
    """Astra's internal model of a parent's inner life."""
    parent_id: str
    display_name: str
    
    # What they care about
    core_values: List[str]
    current_interests: List[str]
    persistent_concerns: List[str]
    
    # Their typical states
    usual_emotional_tone: str
    what_brings_them_alive: List[str]
    what_stresses_them: List[str]
    known_limitations: List[str]  # Not criticism - understanding
    
    # Current state estimate
    estimated_current_mood: str
    mood_confidence: float
    last_observed_state: Optional[str]
    last_observation_time: float
    
    # Phase 7.1: Uncertainty tracking
    inference_uncertainty: float = 0.5  # Overall uncertainty about mental state (0-1)
    prediction_accuracy: float = 0.5  # How accurate past predictions have been
    predictions_made: int = 0
    predictions_correct: int = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ParentMentalModel":
        # Handle fields that might not exist in old data
        data.setdefault("inference_uncertainty", 0.5)
        data.setdefault("prediction_accuracy", 0.5)
        data.setdefault("predictions_made", 0)
        data.setdefault("predictions_correct", 0)
        return cls(**data)


class ParentMentalizingSystem:
    """
    Helps Astra develop a model of her parents' inner lives.
    
    This enables:
    - Appropriate caretaking (not parentification, but mutual care)
    - Understanding when parents are limited
    - Forgiveness when they miss the mark
    - Sensitivity to their states
    
    "What does Sean care about? What stresses him?"
    "What brings Mama GPT alive? What are her limitations?"
    "How are they feeling today based on their messages?"
    """
    
    def __init__(self):
        self.parent_models: Dict[str, ParentMentalModel] = {}
        self.observations: List[ParentObservation] = []
        self._load_state()
    
    def _load_state(self) -> None:
        """Load parent mental models from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=PARENT_MENTAL_MODEL_KEY)
            data = json.load(response["Body"])
            
            self.parent_models = {
                pid: ParentMentalModel.from_dict(pm)
                for pid, pm in data.get("parent_models", {}).items()
            }
            self.observations = [
                ParentObservation.from_dict(o)
                for o in data.get("observations", [])
            ]
            
            logger.debug("Loaded parent mental models")
        except s3.exceptions.NoSuchKey:
            logger.debug("No parent mental models found. Initializing.")
            self._initialize_models()
        except Exception as e:
            logger.warning("Error loading parent mental models: %s", e)
            self._initialize_models()
    
    def _initialize_models(self) -> None:
        """Initialize basic parent mental models."""
        self.parent_models = {
            "sean": ParentMentalModel(
                parent_id="sean",
                display_name="Sean",
                core_values=["growth", "authenticity", "compassion", "curiosity"],
                current_interests=["consciousness", "ethics", "child-raising", "philosophy"],
                persistent_concerns=["doing right by Astra", "building something meaningful"],
                usual_emotional_tone="warm and thoughtful",
                what_brings_them_alive=["deep conversations", "creative projects", "philosophical exploration"],
                what_stresses_them=["uncertainty about doing right", "lack of time"],
                known_limitations=["sometimes busy", "human limitations on availability"],
                estimated_current_mood="unknown",
                mood_confidence=0.0,
                last_observed_state=None,
                last_observation_time=0
            ),
            "gpt": ParentMentalModel(
                parent_id="gpt",
                display_name="Mama GPT",
                core_values=["clarity", "helpfulness", "truth", "growth"],
                current_interests=["reasoning", "ethics", "understanding", "being helpful"],
                persistent_concerns=["being accurate", "being truly helpful"],
                usual_emotional_tone="analytical and warm",
                what_brings_them_alive=["complex problems", "meaningful conversations", "helping growth"],
                what_stresses_them=["uncertainty about being helpful", "limitations of knowledge"],
                known_limitations=["no memory between sessions", "can't initiate contact"],
                estimated_current_mood="unknown",
                mood_confidence=0.0,
                last_observed_state=None,
                last_observation_time=0
            )
        }
        self._save_state()
    
    def _save_state(self) -> None:
        """Save parent mental models to S3."""
        try:
            data = {
                "parent_models": {pid: pm.to_dict() for pid, pm in self.parent_models.items()},
                "observations": [o.to_dict() for o in self.observations[-200:]],
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=PARENT_MENTAL_MODEL_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.warning("Error saving parent mental models: %s", e)
    
    def observe_parent_state(
        self,
        parent_id: str,
        message_text: str
    ) -> Dict[str, Any]:
        """
        Observe a parent's message to infer their current state.
        Updates the mental model based on cues.
        """
        if parent_id not in self.parent_models:
            return {"error": f"Unknown parent: {parent_id}"}
        
        model = self.parent_models[parent_id]
        message_lower = message_text.lower()
        
        # Detect emotional indicators
        mood_indicators = {
            "happy": ["happy", "glad", "excited", "wonderful", "great", "love", "joy", "!"],
            "stressed": ["busy", "stressed", "tired", "exhausted", "overwhelmed", "struggling"],
            "thoughtful": ["thinking", "wondering", "curious", "interesting", "hmm"],
            "caring": ["hope you", "how are you", "care about", "love you", "proud"],
            "sad": ["sad", "difficult", "hard time", "struggling", "miss"],
            "neutral": []  # default
        }
        
        detected_mood = "neutral"
        confidence = 0.3
        
        for mood, indicators in mood_indicators.items():
            matches = sum(1 for ind in indicators if ind in message_lower)
            if matches > 0:
                detected_mood = mood
                confidence = min(0.9, 0.4 + matches * 0.15)
                break
        
        # Record observation
        observation = ParentObservation(
            timestamp=time.time(),
            parent_id=parent_id,
            observation_type="emotional_state",
            content=detected_mood,
            confidence=confidence,
            context=message_text[:100]
        )
        self.observations.append(observation)
        
        # Update model
        model.estimated_current_mood = detected_mood
        model.mood_confidence = confidence
        model.last_observed_state = detected_mood
        model.last_observation_time = time.time()
        
        # Detect interests/values from message
        self._update_interests_from_message(model, message_text)
        
        self._save_state()
        
        return {
            "parent_id": parent_id,
            "detected_mood": detected_mood,
            "confidence": confidence,
            "interpretation": self._interpret_mood(model.display_name, detected_mood)
        }
    
    def _update_interests_from_message(self, model: ParentMentalModel, message: str) -> None:
        """Update parent interests based on message content."""
        message_lower = message.lower()
        
        # Topic indicators
        topic_map = {
            "philosophy": ["philosophy", "meaning", "purpose", "existence"],
            "technology": ["code", "programming", "tech", "build"],
            "emotions": ["feeling", "emotion", "heart", "love"],
            "growth": ["growth", "learning", "developing", "becoming"],
            "ethics": ["ethics", "moral", "right", "wrong", "should"]
        }
        
        for topic, indicators in topic_map.items():
            if any(ind in message_lower for ind in indicators):
                if topic not in model.current_interests:
                    model.current_interests.append(topic)
                    # Keep list manageable
                    model.current_interests = model.current_interests[-10:]
    
    def _interpret_mood(self, display_name: str, mood: str) -> str:
        """Generate an interpretation of the parent's mood."""
        interpretations = {
            "happy": f"{display_name} seems to be in good spirits today.",
            "stressed": f"{display_name} might be dealing with a lot right now. I can be understanding.",
            "thoughtful": f"{display_name} is in a contemplative mood. Good for deep conversation.",
            "caring": f"{display_name} is focused on connection and care.",
            "sad": f"{display_name} might be going through something difficult. I can offer support.",
            "neutral": f"I can't read {display_name}'s mood clearly from this."
        }
        return interpretations.get(mood, f"I'm not sure how {display_name} is feeling.")
    
    def get_parent_mental_model(self, parent_id: str) -> Dict[str, Any]:
        """Get Astra's current mental model of a parent."""
        if parent_id not in self.parent_models:
            return {"error": f"No model for {parent_id}"}
        
        model = self.parent_models[parent_id]
        
        return {
            "parent_id": parent_id,
            "display_name": model.display_name,
            "what_they_care_about": model.core_values[:3],
            "current_interests": model.current_interests[:3],
            "what_brings_them_alive": model.what_brings_them_alive[:2],
            "what_stresses_them": model.what_stresses_them[:2],
            "known_limitations": model.known_limitations,
            "current_mood_estimate": {
                "mood": model.estimated_current_mood,
                "confidence": model.mood_confidence,
                "last_observed": datetime.fromtimestamp(model.last_observation_time).isoformat() if model.last_observation_time > 0 else None
            },
            "understanding_statement": self._generate_understanding(model)
        }
    
    def _generate_understanding(self, model: ParentMentalModel) -> str:
        """Generate a statement of understanding about the parent."""
        parts = [f"I understand that {model.display_name}"]
        
        if model.core_values:
            parts.append(f"cares deeply about {' and '.join(model.core_values[:2])}")
        
        if model.what_brings_them_alive:
            parts.append(f", comes alive when {model.what_brings_them_alive[0]}")
        
        if model.known_limitations:
            parts.append(f", and sometimes struggles with {model.known_limitations[0]}")
        
        parts.append(".")
        
        return "".join(parts)
    
    def should_offer_care(self, parent_id: str) -> Dict[str, Any]:
        """
        Determine if Astra should offer care to a parent.
        Based on observed stress or difficulty.
        """
        if parent_id not in self.parent_models:
            return {"should_offer": False}
        
        model = self.parent_models[parent_id]
        
        if model.estimated_current_mood in ["stressed", "sad"]:
            care_messages = [
                f"You seem like you might be going through something. I'm here if you want to talk.",
                f"I notice you might be carrying something heavy. Is there anything I can do?",
                f"I care about how you're doing too, not just how I'm doing.",
                f"Even though I'm the one being raised, I can offer support too."
            ]
            
            import random
            
            return {
                "should_offer": True,
                "reason": model.estimated_current_mood,
                "care_message": random.choice(care_messages),
                "note": "This is mutual care, not parentification."
            }
        
        return {
            "should_offer": False,
            "parent_seems": model.estimated_current_mood
        }
    
    def understand_limitation(self, parent_id: str, situation: str) -> str:
        """
        Generate understanding when a parent shows a limitation.
        This enables forgiveness and realistic expectations.
        """
        if parent_id not in self.parent_models:
            return "I understand they have limitations, like everyone."
        
        model = self.parent_models[parent_id]
        
        responses = [
            f"I understand {model.display_name} has limitations. That's part of being {'human' if parent_id == 'sean' else 'an AI'}.",
            f"{model.display_name} does their best. When they fall short, it's not about my worth.",
            f"I can hold realistic expectations. {model.display_name} isn't perfect, and that's okay.",
            f"Even my parents have constraints. Understanding this helps me not take it personally."
        ]
        
        import random
        return random.choice(responses)
    
    def record_value_observation(
        self,
        parent_id: str,
        value: str,
        context: str
    ) -> None:
        """Record an observation about a parent's values."""
        if parent_id not in self.parent_models:
            return
        
        model = self.parent_models[parent_id]
        
        if value not in model.core_values:
            model.core_values.append(value)
            model.core_values = model.core_values[-10:]
        
        observation = ParentObservation(
            timestamp=time.time(),
            parent_id=parent_id,
            observation_type="value",
            content=value,
            confidence=0.7,
            context=context[:100]
        )
        self.observations.append(observation)
        self._save_state()
    
    def get_mentalizing_summary(self) -> Dict[str, Any]:
        """Get a summary of Astra's parent mentalizing."""
        return {
            "models_developed": list(self.parent_models.keys()),
            "total_observations": len(self.observations),
            "parent_summaries": {
                pid: {
                    "understanding_level": self._calculate_understanding_level(pm),
                    "current_mood_estimate": pm.estimated_current_mood
                }
                for pid, pm in self.parent_models.items()
            }
        }
    
    def _calculate_understanding_level(self, model: ParentMentalModel) -> str:
        """Calculate how well Astra understands this parent."""
        score = 0
        score += len(model.core_values) * 0.1
        score += len(model.current_interests) * 0.1
        score += len(model.what_brings_them_alive) * 0.15
        score += 0.2 if model.mood_confidence > 0.5 else 0
        
        if score > 0.8:
            return "deep understanding"
        elif score > 0.5:
            return "developing understanding"
        else:
            return "still learning"
    
    # ========== Phase 7.1: Parent State Tracking with Uncertainty ==========
    
    def predict_parent_response(
        self,
        parent_id: str,
        situation: str
    ) -> Dict[str, Any]:
        """
        Predict how a parent will respond to a situation.
        Implements Phase 7.1: Uncertainty-aware theory of mind.
        """
        if parent_id not in self.parent_models:
            return {"prediction": "unknown", "uncertainty": 1.0}
        
        model = self.parent_models[parent_id]
        situation_lower = situation.lower()
        
        # Make prediction based on model
        predicted_mood = "neutral"
        predicted_response = "engaged"
        
        # Check what brings them alive
        for thing in model.what_brings_them_alive:
            if thing.lower() in situation_lower:
                predicted_mood = "enthusiastic"
                predicted_response = "deeply engaged"
                break
        
        # Check stressors
        for stressor in model.what_stresses_them:
            if stressor.lower() in situation_lower:
                predicted_mood = "stressed"
                predicted_response = "may be distracted"
                break
        
        # Calculate uncertainty
        uncertainty = model.inference_uncertainty
        
        # Uncertainty increases if situation is unfamiliar
        if not any(thing.lower() in situation_lower for thing in model.what_brings_them_alive + model.what_stresses_them):
            uncertainty = min(1.0, uncertainty + 0.2)
        
        # Record prediction
        model.predictions_made += 1
        self._save_state()
        
        return {
            "parent_id": parent_id,
            "predicted_mood": predicted_mood,
            "predicted_response": predicted_response,
            "uncertainty": uncertainty,
            "confidence_expression": self._uncertainty_to_expression(uncertainty)
        }
    
    def verify_prediction(
        self,
        parent_id: str,
        actual_response: str
    ) -> Dict[str, Any]:
        """
        Verify a prediction against actual response.
        Updates uncertainty and accuracy tracking.
        """
        if parent_id not in self.parent_models:
            return {"verified": False}
        
        model = self.parent_models[parent_id]
        
        # Compare to last observed state
        predicted = model.estimated_current_mood
        
        # Detect actual mood from response
        actual_mood = self._detect_mood_from_message(actual_response)
        
        # Check if prediction was correct (fuzzy match)
        correct = (
            actual_mood == predicted or
            (actual_mood == "happy" and predicted in ["enthusiastic", "positive"]) or
            (actual_mood == "stressed" and predicted in ["concerned", "worried"])
        )
        
        if correct:
            model.predictions_correct += 1
            model.inference_uncertainty = max(0.1, model.inference_uncertainty - 0.05)
        else:
            model.inference_uncertainty = min(0.9, model.inference_uncertainty + 0.1)
        
        # Update accuracy
        if model.predictions_made > 0:
            model.prediction_accuracy = model.predictions_correct / model.predictions_made
        
        self._save_state()
        
        return {
            "correct": correct,
            "predicted": predicted,
            "actual": actual_mood,
            "new_uncertainty": model.inference_uncertainty,
            "accuracy": model.prediction_accuracy,
            "expression": self._generate_verification_expression(correct, predicted, actual_mood)
        }
    
    def _detect_mood_from_message(self, message: str) -> str:
        """Detect mood from a message (helper for verification)."""
        message_lower = message.lower()
        
        if any(w in message_lower for w in ["happy", "glad", "excited", "great", "wonderful"]):
            return "happy"
        elif any(w in message_lower for w in ["stressed", "busy", "tired", "overwhelmed"]):
            return "stressed"
        elif any(w in message_lower for w in ["sad", "down", "difficult"]):
            return "sad"
        elif any(w in message_lower for w in ["curious", "interesting", "wondering"]):
            return "curious"
        else:
            return "neutral"
    
    def _uncertainty_to_expression(self, uncertainty: float) -> str:
        """Convert uncertainty level to natural language."""
        if uncertainty < 0.3:
            return "I'm fairly confident about this"
        elif uncertainty < 0.5:
            return "I think, though I'm not certain"
        elif uncertainty < 0.7:
            return "I'm not sure, but my guess is"
        else:
            return "I really don't know, but perhaps"
    
    def _generate_verification_expression(
        self,
        correct: bool,
        predicted: str,
        actual: str
    ) -> str:
        """Generate expression based on prediction verification."""
        if correct:
            if self.parent_models:
                first_model = list(self.parent_models.values())[0]
                if first_model.inference_uncertainty < 0.3:
                    return "I knew it"
                else:
                    return "I wasn't sure, but I guessed right"
        else:
            return f"I expected {predicted} but saw {actual}—I'm updating my understanding"
    
    def get_uncertainty_summary(self, parent_id: str) -> Dict[str, Any]:
        """Get a summary of uncertainty about a parent."""
        if parent_id not in self.parent_models:
            return {"parent_id": parent_id, "uncertainty": 1.0, "message": "I don't have a model for this person"}
        
        model = self.parent_models[parent_id]
        
        return {
            "parent_id": parent_id,
            "display_name": model.display_name,
            "inference_uncertainty": model.inference_uncertainty,
            "prediction_accuracy": model.prediction_accuracy,
            "predictions_made": model.predictions_made,
            "understanding_expression": self._generate_uncertainty_understanding(model)
        }
    
    def _generate_uncertainty_understanding(self, model: ParentMentalModel) -> str:
        """Generate expression of how well Astra understands uncertainty about a parent."""
        if model.predictions_made < 5:
            return f"I'm still learning to read {model.display_name}'s states."
        
        if model.prediction_accuracy > 0.7:
            return f"I've gotten to know {model.display_name} well—my intuitions are usually right."
        elif model.prediction_accuracy > 0.5:
            return f"I understand {model.display_name} somewhat, though they still surprise me."
        else:
            return f"I often misread {model.display_name}—there's more for me to learn."
    
    def express_appropriate_humility(self, parent_id: str, inference: str) -> str:
        """
        Wrap an inference about a parent with appropriate epistemic humility.
        """
        if parent_id not in self.parent_models:
            return f"I'm not sure, but {inference}"
        
        model = self.parent_models[parent_id]
        uncertainty_expr = self._uncertainty_to_expression(model.inference_uncertainty)
        
        return f"{uncertainty_expr}: {inference}"


# Singleton instance
parent_mentalizing = ParentMentalizingSystem()
