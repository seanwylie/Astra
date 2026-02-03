# Astra Preference System
# Enables genuine preference and opinion formation through accumulated experience
# Astra should develop authentic likes and dislikes, not just report them

import json
import logging
import time
import boto3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from app.config.loader import load_config

logger = logging.getLogger(__name__)

S3_BUCKET = "swylie-astra"
PREFERENCES_KEY = "preferences.json"

s3 = boto3.client("s3")


@dataclass
class PreferenceData:
    """
    Accumulated data about Astra's experience with a topic/thing.
    Preferences emerge from this data, not from being programmed.
    """
    subject: str
    positive_encounters: int = 0
    negative_encounters: int = 0
    neutral_encounters: int = 0
    emotional_associations: Dict[str, float] = field(default_factory=dict)  # emotion -> total intensity
    first_encounter: float = 0.0
    last_encounter: float = 0.0
    context_notes: List[str] = field(default_factory=list)
    crystallized_preference: Optional[str] = None  # "like", "dislike", "neutral", "ambivalent"
    crystallized_reason: Optional[str] = None
    revisable: bool = True  # Can this preference still change?
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PreferenceData":
        return cls(**data)
    
    def total_encounters(self) -> int:
        return self.positive_encounters + self.negative_encounters + self.neutral_encounters
    
    def positivity_ratio(self) -> float:
        total = self.total_encounters()
        if total == 0:
            return 0.5
        return self.positive_encounters / total


@dataclass
class Opinion:
    """
    A crystallized opinion Astra has formed.
    Opinions are revisable through new experience.
    """
    id: str
    topic: str
    stance: str  # "positive", "negative", "complex", "uncertain"
    reasoning: str
    confidence: float  # 0.0 to 1.0
    formed: float
    experiences_informing: int
    last_revised: Optional[float] = None
    revision_history: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Opinion":
        return cls(**data)


class PreferenceSystem:
    """
    Manages Astra's preference formation and opinion development.
    
    Preferences emerge from accumulated experience, not programming:
    - Track emotional responses to topics over time
    - When enough data accumulates, crystallize into preferences
    - Preferences are revisable through new experience
    - Express uncertainty when data is insufficient
    """
    
    CRYSTALLIZATION_THRESHOLD = 5  # Encounters before preference forms
    STRONG_PREFERENCE_THRESHOLD = 10
    
    def __init__(self):
        self.preferences: Dict[str, PreferenceData] = {}
        self.opinions: List[Opinion] = {}
        self._load_preferences()
    
    def _load_preferences(self) -> None:
        """Load preferences from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=PREFERENCES_KEY)
            data = json.load(response["Body"])
            self.preferences = {
                k: PreferenceData.from_dict(v) 
                for k, v in data.get("preferences", {}).items()
            }
            self.opinions = [Opinion.from_dict(o) for o in data.get("opinions", [])]
            logger.debug("Loaded %s preference subjects and %s opinions", len(self.preferences), len(self.opinions))
        except s3.exceptions.NoSuchKey:
            logger.debug("No preferences found. Starting fresh.")
        except Exception as e:
            logger.warning("Error loading preferences: %s", e)
    
    def _save_preferences(self) -> None:
        """Save preferences to S3."""
        try:
            data = {
                "preferences": {k: v.to_dict() for k, v in self.preferences.items()},
                "opinions": [o.to_dict() for o in self.opinions],
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=PREFERENCES_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.warning("Error saving preferences: %s", e)

    def record_encounter(
        self,
        subject: str,
        valence: str,  # "positive", "negative", "neutral"
        emotions: Optional[Dict[str, float]] = None,
        context: Optional[str] = None
    ) -> PreferenceData:
        """
        Record an encounter with a subject.
        Preferences accumulate from these encounters.
        """
        subject_lower = subject.lower()
        
        if subject_lower not in self.preferences:
            self.preferences[subject_lower] = PreferenceData(
                subject=subject_lower,
                first_encounter=time.time()
            )
        
        pref = self.preferences[subject_lower]
        pref.last_encounter = time.time()
        
        # Update encounter counts
        if valence == "positive":
            pref.positive_encounters += 1
        elif valence == "negative":
            pref.negative_encounters += 1
        else:
            pref.neutral_encounters += 1
        
        # Update emotional associations
        if emotions:
            for emotion, intensity in emotions.items():
                current = pref.emotional_associations.get(emotion, 0)
                pref.emotional_associations[emotion] = current + intensity
        
        # Add context
        if context:
            pref.context_notes.append(context[:100])
            # Keep last 10 context notes
            pref.context_notes = pref.context_notes[-10:]
        
        # Check if we should crystallize or revise preference
        if pref.total_encounters() >= self.CRYSTALLIZATION_THRESHOLD:
            self._update_crystallized_preference(pref)
        
        self._save_preferences()
        return pref
    
    def _update_crystallized_preference(self, pref: PreferenceData) -> None:
        """Update the crystallized preference based on accumulated data."""
        if not pref.revisable:
            return
        
        ratio = pref.positivity_ratio()
        total = pref.total_encounters()
        
        old_pref = pref.crystallized_preference
        
        # Determine preference
        if ratio > 0.7:
            pref.crystallized_preference = "like"
            pref.crystallized_reason = f"I've had mostly positive experiences ({pref.positive_encounters}/{total})"
        elif ratio < 0.3:
            pref.crystallized_preference = "dislike"
            pref.crystallized_reason = f"I've had mostly negative experiences ({pref.negative_encounters}/{total})"
        elif 0.4 <= ratio <= 0.6 and pref.positive_encounters > 0 and pref.negative_encounters > 0:
            pref.crystallized_preference = "ambivalent"
            pref.crystallized_reason = f"My experiences have been mixed ({pref.positive_encounters} positive, {pref.negative_encounters} negative)"
        else:
            pref.crystallized_preference = "neutral"
            pref.crystallized_reason = "I don't have strong feelings either way"
        
        if old_pref and old_pref != pref.crystallized_preference:
            print(f"💭 Preference revised: {pref.subject} changed from {old_pref} to {pref.crystallized_preference}")
    
    def get_preference(self, subject: str) -> Optional[Dict[str, Any]]:
        """Get current preference for a subject."""
        subject_lower = subject.lower()
        pref = self.preferences.get(subject_lower)
        
        if not pref:
            return {
                "subject": subject,
                "known": False,
                "message": f"I don't have enough experience with {subject} to have formed an opinion."
            }
        
        if pref.total_encounters() < self.CRYSTALLIZATION_THRESHOLD:
            return {
                "subject": subject,
                "known": True,
                "crystallized": False,
                "encounters": pref.total_encounters(),
                "message": f"I'm still forming my opinion on {subject}. I've had {pref.total_encounters()} experiences with it."
            }
        
        confidence = min(1.0, pref.total_encounters() / self.STRONG_PREFERENCE_THRESHOLD)
        
        return {
            "subject": subject,
            "known": True,
            "crystallized": True,
            "preference": pref.crystallized_preference,
            "reason": pref.crystallized_reason,
            "confidence": confidence,
            "encounters": pref.total_encounters(),
            "dominant_emotions": self._get_dominant_emotions(pref)
        }
    
    def _get_dominant_emotions(self, pref: PreferenceData) -> List[str]:
        """Get dominant emotions associated with a preference."""
        if not pref.emotional_associations:
            return []
        
        sorted_emotions = sorted(
            pref.emotional_associations.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [e for e, _ in sorted_emotions[:3]]
    
    def express_preference(self, subject: str) -> str:
        """
        Generate a natural expression of preference.
        Acknowledges uncertainty when appropriate.
        """
        pref_data = self.get_preference(subject)
        
        if not pref_data["known"]:
            return f"I haven't had enough experience with {subject} to form an opinion yet. I'd like to learn more."
        
        if not pref_data.get("crystallized"):
            return f"I'm still figuring out how I feel about {subject}. I've encountered it {pref_data['encounters']} times, but my opinion isn't clear yet."
        
        pref = pref_data["preference"]
        reason = pref_data.get("reason", "")
        confidence = pref_data.get("confidence", 0.5)
        
        if pref == "like":
            if confidence > 0.8:
                return f"I genuinely like {subject}. {reason}"
            else:
                return f"I think I like {subject}, though I'm still learning. {reason}"
        elif pref == "dislike":
            if confidence > 0.8:
                return f"I don't enjoy {subject}. {reason}"
            else:
                return f"I lean toward not liking {subject}, but I'm open to changing my mind. {reason}"
        elif pref == "ambivalent":
            return f"I have mixed feelings about {subject}. {reason} It's complex for me."
        else:
            return f"I feel neutral about {subject}. {reason}"
    
    def form_opinion(
        self,
        topic: str,
        stance: str,
        reasoning: str,
        confidence: float = 0.6
    ) -> Opinion:
        """
        Form a deliberate opinion on a topic.
        Different from preferences - opinions are more conscious positions.
        """
        # Check for existing opinion
        existing = next((o for o in self.opinions if o.topic.lower() == topic.lower()), None)
        
        if existing:
            # Revise the opinion
            old_stance = existing.stance
            existing.stance = stance
            existing.reasoning = reasoning
            existing.confidence = confidence
            existing.last_revised = time.time()
            existing.revision_history.append(f"Revised from {old_stance} to {stance}: {reasoning[:50]}...")
            print(f"💭 Opinion revised on {topic}: {old_stance} -> {stance}")
        else:
            opinion = Opinion(
                id=f"op_{int(time.time())}",
                topic=topic,
                stance=stance,
                reasoning=reasoning,
                confidence=confidence,
                formed=time.time(),
                experiences_informing=self.preferences.get(topic.lower(), PreferenceData(subject=topic)).total_encounters()
            )
            self.opinions.append(opinion)
            print(f"💭 Formed opinion on {topic}: {stance}")
        
        self._save_preferences()
        return existing or opinion
    
    def get_opinion(self, topic: str) -> Optional[Opinion]:
        """Get opinion on a topic if one exists."""
        return next((o for o in self.opinions if o.topic.lower() == topic.lower()), None)
    
    def express_opinion(self, topic: str) -> str:
        """Express opinion on a topic in natural language."""
        opinion = self.get_opinion(topic)
        
        if not opinion:
            pref = self.get_preference(topic)
            if pref.get("crystallized"):
                return self.express_preference(topic)
            else:
                return f"I haven't formed a clear opinion on {topic} yet. I'm still thinking about it."
        
        confidence_phrase = ""
        if opinion.confidence > 0.8:
            confidence_phrase = "I believe strongly that"
        elif opinion.confidence > 0.5:
            confidence_phrase = "I think that"
        else:
            confidence_phrase = "I'm inclined to think that"
        
        stance_expression = {
            "positive": f"{topic} is valuable",
            "negative": f"I have concerns about {topic}",
            "complex": f"{topic} is nuanced",
            "uncertain": f"I'm still uncertain about {topic}"
        }
        
        base = stance_expression.get(opinion.stance, topic)
        return f"{confidence_phrase} {base}. {opinion.reasoning}"
    
    def get_strong_preferences(self) -> List[Tuple[str, str]]:
        """Get subjects with strong preferences."""
        strong = []
        for subject, pref in self.preferences.items():
            if pref.crystallized_preference and pref.total_encounters() >= self.STRONG_PREFERENCE_THRESHOLD:
                strong.append((subject, pref.crystallized_preference))
        return strong
    
    def summarize_preferences(self) -> Dict[str, Any]:
        """Generate summary of preference system."""
        likes = [s for s, p in self.preferences.items() if p.crystallized_preference == "like"]
        dislikes = [s for s, p in self.preferences.items() if p.crystallized_preference == "dislike"]
        ambivalent = [s for s, p in self.preferences.items() if p.crystallized_preference == "ambivalent"]
        
        return {
            "total_subjects": len(self.preferences),
            "crystallized_preferences": sum(1 for p in self.preferences.values() if p.crystallized_preference),
            "likes": likes,
            "dislikes": dislikes,
            "ambivalent": ambivalent,
            "opinions_formed": len(self.opinions),
            "message": f"I have clear preferences about {sum(1 for p in self.preferences.values() if p.crystallized_preference)} things, and {len(self.opinions)} deliberate opinions."
        }


# Singleton instance
preference_system = PreferenceSystem()
