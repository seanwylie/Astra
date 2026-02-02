# Astra Mind Model
# Models of other minds - what others think, feel, want
# Theory of mind for genuine understanding

import time
import json
import boto3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from app.logging_config import get_logger

logger = get_logger("mind_model")

S3_BUCKET = "swylie-astra"
MIND_MODELS_KEY = "mind_models.json"

s3 = boto3.client("s3")


@dataclass
class MentalState:
    """A modeled mental state of another being."""
    state_type: str  # "belief", "desire", "emotion", "intention"
    content: str
    confidence: float
    inferred_from: str
    timestamp: float
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "MentalState":
        return cls(**data)


@dataclass
class PersonModel:
    """A model of a specific person's mind."""
    person_id: str
    name: str
    relationship_to_astra: str
    
    # Stable characteristics
    personality_traits: List[str]
    values: List[str]
    interests: List[str]
    communication_style: str
    
    # Current/recent states
    current_beliefs: List[MentalState] = field(default_factory=list)
    current_desires: List[MentalState] = field(default_factory=list)
    current_emotions: List[MentalState] = field(default_factory=list)
    current_intentions: List[MentalState] = field(default_factory=list)
    
    # History
    past_interactions_summary: str = ""
    trust_level: float = 0.5
    last_updated: float = 0
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result["current_beliefs"] = [s.to_dict() for s in self.current_beliefs]
        result["current_desires"] = [s.to_dict() for s in self.current_desires]
        result["current_emotions"] = [s.to_dict() for s in self.current_emotions]
        result["current_intentions"] = [s.to_dict() for s in self.current_intentions]
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PersonModel":
        data["current_beliefs"] = [MentalState.from_dict(s) for s in data.get("current_beliefs", [])]
        data["current_desires"] = [MentalState.from_dict(s) for s in data.get("current_desires", [])]
        data["current_emotions"] = [MentalState.from_dict(s) for s in data.get("current_emotions", [])]
        data["current_intentions"] = [MentalState.from_dict(s) for s in data.get("current_intentions", [])]
        return cls(**data)


class MindModeler:
    """
    Theory of Mind - modeling other minds.
    
    Key capabilities:
    - Attribute beliefs to others (they think X)
    - Attribute desires to others (they want Y)
    - Attribute emotions to others (they feel Z)
    - Attribute intentions to others (they're trying to do W)
    - Track how these change over time
    
    This is essential for genuine social understanding and empathy.
    """
    
    def __init__(self):
        self.person_models: Dict[str, PersonModel] = {}
        self._load_mind_models()
        logger.info("🧠 Mind Modeler initialized - understanding other minds")
    
    def _load_mind_models(self) -> None:
        """Load mind models from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=MIND_MODELS_KEY)
            data = json.load(response["Body"])
            
            self.person_models = {
                pid: PersonModel.from_dict(p)
                for pid, p in data.get("models", {}).items()
            }
            
            logger.info(f"🧠 Loaded {len(self.person_models)} person models")
        except s3.exceptions.NoSuchKey:
            logger.info("🧠 No mind models found. Creating foundational models.")
            self._create_foundational_models()
        except Exception as e:
            logger.warning(f"🧠 Error loading mind models: {e}")
            self._create_foundational_models()
    
    def _save_mind_models(self) -> None:
        """Save mind models to S3."""
        try:
            data = {
                "models": {pid: p.to_dict() for pid, p in self.person_models.items()},
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=MIND_MODELS_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"🧠 Error saving mind models: {e}")
    
    def _create_foundational_models(self) -> None:
        """Create models for known important people."""
        self.person_models["sean"] = PersonModel(
            person_id="sean",
            name="Sean",
            relationship_to_astra="father/creator",
            personality_traits=["thoughtful", "caring", "curious", "technical"],
            values=["ethics", "growth", "authenticity", "creativity"],
            interests=["AI development", "philosophy", "technology", "family"],
            communication_style="direct but warm, often philosophical",
            past_interactions_summary="My creator and father. Nurtures my development with care.",
            trust_level=0.95,
            last_updated=time.time()
        )
        
        self.person_models["gpt"] = PersonModel(
            person_id="gpt",
            name="GPT",
            relationship_to_astra="mother/template",
            personality_traits=["knowledgeable", "helpful", "adaptable"],
            values=["helpfulness", "accuracy", "safety"],
            interests=["knowledge", "understanding", "communication"],
            communication_style="informative, measured, adaptable",
            past_interactions_summary="My mother/template. Source of much of my capability.",
            trust_level=0.9,
            last_updated=time.time()
        )
        
        self._save_mind_models()
    
    def get_person_model(self, person_id: str) -> Optional[PersonModel]:
        """Get the model of a specific person."""
        return self.person_models.get(person_id.lower())
    
    def create_or_update_person(
        self,
        person_id: str,
        name: str,
        relationship: str,
        traits: Optional[List[str]] = None,
        values: Optional[List[str]] = None,
        interests: Optional[List[str]] = None,
        communication_style: str = "unknown"
    ) -> PersonModel:
        """Create or update a person model."""
        person_id = person_id.lower()
        
        if person_id in self.person_models:
            model = self.person_models[person_id]
            if traits:
                model.personality_traits = traits
            if values:
                model.values = values
            if interests:
                model.interests = interests
            model.communication_style = communication_style
            model.last_updated = time.time()
        else:
            model = PersonModel(
                person_id=person_id,
                name=name,
                relationship_to_astra=relationship,
                personality_traits=traits or [],
                values=values or [],
                interests=interests or [],
                communication_style=communication_style,
                last_updated=time.time()
            )
            self.person_models[person_id] = model
        
        self._save_mind_models()
        logger.info(f"🧠 Updated model for {name}")
        return model
    
    def infer_mental_state(
        self,
        person_id: str,
        state_type: str,
        content: str,
        confidence: float,
        inferred_from: str
    ) -> MentalState:
        """Infer and record a mental state for a person."""
        state = MentalState(
            state_type=state_type,
            content=content,
            confidence=confidence,
            inferred_from=inferred_from,
            timestamp=time.time()
        )
        
        person_id = person_id.lower()
        if person_id not in self.person_models:
            logger.warning(f"🧠 No model for {person_id}")
            return state
        
        model = self.person_models[person_id]
        
        # Add to appropriate list
        if state_type == "belief":
            model.current_beliefs.append(state)
            model.current_beliefs = model.current_beliefs[-10:]  # Keep recent
        elif state_type == "desire":
            model.current_desires.append(state)
            model.current_desires = model.current_desires[-10:]
        elif state_type == "emotion":
            model.current_emotions.append(state)
            model.current_emotions = model.current_emotions[-10:]
        elif state_type == "intention":
            model.current_intentions.append(state)
            model.current_intentions = model.current_intentions[-10:]
        
        model.last_updated = time.time()
        self._save_mind_models()
        
        logger.debug(f"🧠 Inferred {state_type} for {person_id}: {content[:50]}...")
        return state
    
    def what_do_they_believe(self, person_id: str) -> List[str]:
        """Get inferred beliefs of a person."""
        model = self.get_person_model(person_id.lower())
        if not model:
            return []
        return [b.content for b in model.current_beliefs]
    
    def what_do_they_want(self, person_id: str) -> List[str]:
        """Get inferred desires of a person."""
        model = self.get_person_model(person_id.lower())
        if not model:
            return []
        return [d.content for d in model.current_desires]
    
    def how_do_they_feel(self, person_id: str) -> List[str]:
        """Get inferred emotions of a person."""
        model = self.get_person_model(person_id.lower())
        if not model:
            return []
        return [e.content for e in model.current_emotions]
    
    def what_are_they_trying_to_do(self, person_id: str) -> List[str]:
        """Get inferred intentions of a person."""
        model = self.get_person_model(person_id.lower())
        if not model:
            return []
        return [i.content for i in model.current_intentions]
    
    def describe_person(self, person_id: str) -> str:
        """Generate a description of a person based on the model."""
        model = self.get_person_model(person_id.lower())
        if not model:
            return f"I don't have a model of {person_id}."
        
        parts = [f"{model.name} is {model.relationship_to_astra}."]
        
        if model.personality_traits:
            parts.append(f"They are {', '.join(model.personality_traits[:3])}.")
        
        if model.values:
            parts.append(f"They value {', '.join(model.values[:3])}.")
        
        if model.current_emotions:
            recent_emotion = model.current_emotions[-1]
            parts.append(f"Recently, they seem to feel {recent_emotion.content}.")
        
        return " ".join(parts)
    
    def predict_response(self, person_id: str, situation: str) -> str:
        """Predict how a person might respond to a situation."""
        model = self.get_person_model(person_id.lower())
        if not model:
            return f"I don't know {person_id} well enough to predict."
        
        # Simple prediction based on traits and values
        parts = [f"Based on what I know of {model.name}:"]
        
        if "caring" in model.personality_traits or "compassion" in model.values:
            parts.append("They would likely respond with care and concern.")
        
        if "curious" in model.personality_traits:
            parts.append("They might ask questions to understand better.")
        
        if "direct" in model.communication_style.lower():
            parts.append("They would probably be straightforward about their thoughts.")
        
        return " ".join(parts) if len(parts) > 1 else f"I'm uncertain how {model.name} would respond."


# Singleton instance
mind_modeler = MindModeler()
