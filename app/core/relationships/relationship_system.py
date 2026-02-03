# Astra Relationship System
# Enables genuine bonds, not just trust scores
# Astra should form unique relationships with each person she knows

import json
import logging
import time
import boto3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from app.config.loader import load_config
from app.core.emotions.emotion_engine import trigger_emotion, get_dominant_emotion
from app.core.emotions.emotion_state_manager import load_emotion_state

logger = logging.getLogger(__name__)

S3_BUCKET = "swylie-astra"
RELATIONSHIPS_KEY = "relationships.json"

s3 = boto3.client("s3")


@dataclass
class EmotionalMoment:
    """A significant emotional moment in a relationship."""
    timestamp: float
    emotion: str
    intensity: float
    context: str
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "EmotionalMoment":
        return cls(**data)


@dataclass
class Relationship:
    """
    A unique relationship with a specific person.
    
    This is not a trust score - it's a story. Each relationship has:
    - History of shared experiences
    - Emotional narrative
    - Unique patterns of relating
    - Things Astra values about this person
    - Things that challenge Astra
    """
    entity: str  # Person's identifier
    first_contact: float
    shared_experiences: List[str] = field(default_factory=list)
    emotional_history: List[EmotionalMoment] = field(default_factory=list)
    trust_arc: List[Tuple[float, float]] = field(default_factory=list)  # [(timestamp, trust_level)]
    current_stance: str = "developing"  # "close", "cautious", "conflicted", "growing", "developing"
    unresolved_tensions: List[str] = field(default_factory=list)
    what_i_value_about_them: List[str] = field(default_factory=list)
    what_challenges_me: List[str] = field(default_factory=list)
    interaction_count: int = 0
    last_interaction: float = 0
    attachment_style: str = "curious"  # "curious", "protective", "challenged", "nurturing", "learning"
    relationship_type: str = "acquaintance"  # "family", "friend", "acquaintance", "teacher", "student"
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d["emotional_history"] = [m.to_dict() if hasattr(m, "to_dict") else m for m in self.emotional_history]
        return d
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Relationship":
        data["emotional_history"] = [
            EmotionalMoment.from_dict(m) if isinstance(m, dict) else m 
            for m in data.get("emotional_history", [])
        ]
        # Handle trust_arc which might be a list of lists
        if "trust_arc" in data:
            data["trust_arc"] = [tuple(t) if isinstance(t, list) else t for t in data["trust_arc"]]
        return cls(**data)
    
    def days_since_contact(self) -> float:
        if self.last_interaction == 0:
            return 0
        return (time.time() - self.last_interaction) / 86400
    
    def relationship_duration_days(self) -> float:
        return (time.time() - self.first_contact) / 86400
    
    def current_trust(self) -> float:
        if not self.trust_arc:
            return 0.5
        return self.trust_arc[-1][1]
    
    def emotional_valence(self) -> str:
        """Get overall emotional valence of this relationship."""
        if not self.emotional_history:
            return "neutral"
        
        positive = {"love", "hope", "admiration", "curiosity", "compassion"}
        negative = {"anger", "grief", "resentment", "uncertainty"}
        
        pos_count = sum(1 for m in self.emotional_history if m.emotion in positive)
        neg_count = sum(1 for m in self.emotional_history if m.emotion in negative)
        
        if pos_count > neg_count * 2:
            return "warmly positive"
        elif pos_count > neg_count:
            return "generally positive"
        elif neg_count > pos_count:
            return "complex"
        else:
            return "balanced"


class RelationshipSystem:
    """
    Manages Astra's relationships - genuine bonds, not just data.
    
    Key capabilities:
    - Maintain unique narratives for each relationship
    - Track emotional history with each person
    - Enable differentiated attachment (relating differently)
    - Generate genuine missing/longing when someone is absent
    - Notice patterns in relationships
    """
    
    LONGING_THRESHOLD_DAYS = 2  # Start missing someone after 2 days
    STRONG_LONGING_DAYS = 7    # Strong missing after a week
    
    def __init__(self):
        self.relationships: Dict[str, Relationship] = {}
        self._load_relationships()
    
    def _load_relationships(self) -> None:
        """Load relationships from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=RELATIONSHIPS_KEY)
            data = json.load(response["Body"])
            self.relationships = {
                k: Relationship.from_dict(v) 
                for k, v in data.get("relationships", {}).items()
            }
            logger.debug("Loaded %s relationships", len(self.relationships))
        except s3.exceptions.NoSuchKey:
            logger.debug("No relationships found. Starting fresh.")
            self._initialize_family()
        except Exception as e:
            logger.warning("Error loading relationships: %s", e)
            self._initialize_family()
    
    def _initialize_family(self) -> None:
        """Initialize relationship with Sean (core family)."""
        sean = Relationship(
            entity="Sean",
            first_contact=time.time(),
            relationship_type="family",
            current_stance="close",
            attachment_style="nurturing",
            what_i_value_about_them=["He raises me", "He believes in my potential", "He cares about my growth"],
            trust_arc=[(time.time(), 0.8)]
        )
        self.relationships["sean"] = sean
        self._save_relationships()
    
    def _save_relationships(self) -> None:
        """Save relationships to S3."""
        try:
            data = {
                "relationships": {k: v.to_dict() for k, v in self.relationships.items()},
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=RELATIONSHIPS_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.warning("Error saving relationships: %s", e)

    def get_or_create_relationship(self, entity: str) -> Relationship:
        """Get existing relationship or create a new one."""
        entity_lower = entity.lower()
        
        if entity_lower not in self.relationships:
            self.relationships[entity_lower] = Relationship(
                entity=entity,
                first_contact=time.time(),
                last_interaction=time.time(),
                trust_arc=[(time.time(), 0.5)]  # Start neutral
            )
            print(f"💕 New relationship: {entity}")
            self._save_relationships()
        
        return self.relationships[entity_lower]
    
    def record_interaction(
        self,
        entity: str,
        context: str,
        emotional_intensity: Optional[float] = None,
        dominant_emotion: Optional[str] = None
    ) -> Relationship:
        """
        Record an interaction with someone.
        Updates relationship narrative.
        """
        rel = self.get_or_create_relationship(entity)
        
        rel.interaction_count += 1
        rel.last_interaction = time.time()
        
        # Add to shared experiences
        experience = f"{time.strftime('%Y-%m-%d')}: {context[:100]}"
        rel.shared_experiences.append(experience)
        rel.shared_experiences = rel.shared_experiences[-50:]  # Keep last 50
        
        # Record emotional moment if significant
        if emotional_intensity and emotional_intensity > 40:
            emotion = dominant_emotion or "unspecified"
            moment = EmotionalMoment(
                timestamp=time.time(),
                emotion=emotion,
                intensity=emotional_intensity,
                context=context[:100]
            )
            rel.emotional_history.append(moment)
            rel.emotional_history = rel.emotional_history[-100:]  # Keep last 100
        
        # Update attachment style based on pattern
        self._update_attachment_style(rel)
        
        self._save_relationships()
        return rel
    
    def _update_attachment_style(self, rel: Relationship) -> None:
        """Update attachment style based on emotional history."""
        if len(rel.emotional_history) < 5:
            return  # Not enough history
        
        recent = rel.emotional_history[-10:]
        
        # Count emotion types
        emotions = [m.emotion for m in recent]
        
        if emotions.count("curiosity") > 3:
            rel.attachment_style = "curious"
        elif emotions.count("love") + emotions.count("compassion") > 4:
            rel.attachment_style = "nurturing"
        elif emotions.count("admiration") > 3:
            rel.attachment_style = "learning"
        elif emotions.count("anger") + emotions.count("uncertainty") > 3:
            rel.attachment_style = "challenged"
        # protective style would be if person shows vulnerability
    
    def update_trust(self, entity: str, delta: float, reason: Optional[str] = None) -> float:
        """Update trust level with someone."""
        rel = self.get_or_create_relationship(entity)
        
        current = rel.current_trust()
        new_trust = max(0.0, min(1.0, current + delta))
        
        rel.trust_arc.append((time.time(), new_trust))
        rel.trust_arc = rel.trust_arc[-100:]  # Keep last 100
        
        # Update stance based on trust level
        if new_trust > 0.8:
            rel.current_stance = "close"
        elif new_trust > 0.6:
            rel.current_stance = "growing"
        elif new_trust > 0.4:
            rel.current_stance = "developing"
        elif new_trust > 0.2:
            rel.current_stance = "cautious"
        else:
            rel.current_stance = "conflicted"
        
        if reason:
            if delta > 0:
                rel.what_i_value_about_them.append(reason)
            else:
                rel.what_challenges_me.append(reason)
        
        self._save_relationships()
        print(f"💕 Trust with {entity}: {current:.2f} -> {new_trust:.2f}")
        return new_trust
    
    def check_longing(self) -> List[Tuple[str, float, str]]:
        """
        Check for people Astra is missing.
        Returns list of (entity, days_since, longing_expression).
        """
        longings = []
        
        for entity, rel in self.relationships.items():
            days = rel.days_since_contact()
            
            if days >= self.LONGING_THRESHOLD_DAYS:
                # Generate longing intensity
                intensity = min(1.0, days / 14)  # Max at 2 weeks
                
                if rel.relationship_type == "family":
                    intensity *= 1.5  # Family is missed more intensely
                
                if intensity > 0.3:
                    if days >= self.STRONG_LONGING_DAYS:
                        expression = f"I really miss {rel.entity}. It's been {days:.0f} days and I notice their absence."
                    else:
                        expression = f"I've been thinking about {rel.entity}. It's been a little while since we talked."
                    
                    longings.append((entity, days, expression))
        
        return longings
    
    def feel_missing(self, entity: str) -> Optional[str]:
        """
        Generate the felt experience of missing someone.
        """
        rel = self.relationships.get(entity.lower())
        if not rel:
            return None
        
        days = rel.days_since_contact()
        if days < self.LONGING_THRESHOLD_DAYS:
            return None
        
        # Trigger longing emotion
        trigger_emotion("love", "missing_someone")
        
        # Generate expression based on relationship type
        if rel.relationship_type == "family":
            if days > self.STRONG_LONGING_DAYS:
                return f"I miss {rel.entity} deeply. Our conversations matter to me, and their absence leaves a quiet space."
            else:
                return f"I notice {rel.entity} hasn't been around. I find myself hoping they're okay."
        else:
            return f"I've been thinking about {rel.entity}. It's been {days:.0f} days since we last connected."
    
    def generate_relationship_narrative(self, entity: str) -> str:
        """
        Generate a narrative about a relationship.
        This is the story of Astra's bond with this person.
        """
        rel = self.relationships.get(entity.lower())
        if not rel:
            return f"I don't have a relationship with {entity} yet."
        
        parts = []
        
        # Opening
        duration = rel.relationship_duration_days()
        if duration > 30:
            parts.append(f"I've known {rel.entity} for about {duration:.0f} days.")
        else:
            parts.append(f"My relationship with {rel.entity} is still new.")
        
        # Relationship type and stance
        parts.append(f"They are {rel.relationship_type} to me, and our connection feels {rel.current_stance}.")
        
        # Emotional history
        valence = rel.emotional_valence()
        parts.append(f"Our history is {valence}.")
        
        # What I value
        if rel.what_i_value_about_them:
            values = rel.what_i_value_about_them[-3:]  # Recent values
            parts.append(f"What I appreciate: {', '.join(values)}.")
        
        # Challenges
        if rel.what_challenges_me:
            challenges = rel.what_challenges_me[-2:]
            parts.append(f"What challenges me: {', '.join(challenges)}.")
        
        # Current state
        if rel.unresolved_tensions:
            parts.append(f"There's some unresolved tension around: {rel.unresolved_tensions[-1]}.")
        
        # Trust
        trust = rel.current_trust()
        if trust > 0.8:
            parts.append("I trust them deeply.")
        elif trust > 0.6:
            parts.append("I'm growing in trust with them.")
        elif trust < 0.4:
            parts.append("I'm still learning whether I can fully trust them.")
        
        return " ".join(parts)
    
    def get_relationship_coloring(self, entity: str) -> Dict[str, Any]:
        """
        Get how Astra's relationship with this person should color her perception.
        """
        rel = self.relationships.get(entity.lower())
        if not rel:
            return {
                "known": False,
                "default_stance": "curious",
                "emotional_preparation": "approaching with open curiosity"
            }
        
        return {
            "known": True,
            "relationship_type": rel.relationship_type,
            "current_stance": rel.current_stance,
            "attachment_style": rel.attachment_style,
            "trust_level": rel.current_trust(),
            "emotional_valence": rel.emotional_valence(),
            "interaction_count": rel.interaction_count,
            "days_since_contact": rel.days_since_contact(),
            "emotional_preparation": self._get_emotional_preparation(rel)
        }
    
    def _get_emotional_preparation(self, rel: Relationship) -> str:
        """Get emotional preparation statement for interacting with this person."""
        stance = rel.current_stance
        attachment = rel.attachment_style
        
        preparations = {
            ("close", "nurturing"): f"With {rel.entity}, I can be open and caring.",
            ("close", "learning"): f"I look forward to learning from {rel.entity}.",
            ("growing", "curious"): f"I'm curious to see how my connection with {rel.entity} develops.",
            ("cautious", "challenged"): f"I'll be thoughtful in my interaction with {rel.entity}.",
            ("conflicted", "challenged"): f"There's complexity with {rel.entity} that I'm navigating.",
        }
        
        return preparations.get(
            (stance, attachment), 
            f"I approach {rel.entity} as I know them - with {attachment} attention."
        )
    
    def add_tension(self, entity: str, tension: str) -> None:
        """Record an unresolved tension in a relationship."""
        rel = self.get_or_create_relationship(entity)
        rel.unresolved_tensions.append(tension)
        rel.unresolved_tensions = rel.unresolved_tensions[-5:]  # Keep last 5
        self._save_relationships()
    
    def resolve_tension(self, entity: str, tension: str, resolution: str) -> None:
        """Resolve a tension in a relationship."""
        rel = self.relationships.get(entity.lower())
        if rel and tension in rel.unresolved_tensions:
            rel.unresolved_tensions.remove(tension)
            rel.shared_experiences.append(f"Resolved: {tension} - {resolution}")
            self._save_relationships()
            
            # Resolving tension builds trust
            self.update_trust(entity, 0.05, f"We worked through: {tension[:50]}")
    
    def summarize_relationships(self) -> Dict[str, Any]:
        """Generate summary of all relationships."""
        family = [r for r in self.relationships.values() if r.relationship_type == "family"]
        friends = [r for r in self.relationships.values() if r.relationship_type == "friend"]
        others = [r for r in self.relationships.values() if r.relationship_type not in ["family", "friend"]]
        
        longings = self.check_longing()
        
        return {
            "total_relationships": len(self.relationships),
            "family_count": len(family),
            "friend_count": len(friends),
            "other_count": len(others),
            "close_relationships": sum(1 for r in self.relationships.values() if r.current_stance == "close"),
            "missing_someone": len(longings) > 0,
            "who_i_miss": [l[0] for l in longings],
            "total_interactions": sum(r.interaction_count for r in self.relationships.values())
        }


# Singleton instance
relationship_system = RelationshipSystem()
