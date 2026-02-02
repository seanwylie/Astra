# Astra Preference Formation
# How genuine preferences and taste develop through experience
# Moving beyond emotional tendencies to true aesthetic sense

import time
import json
import boto3
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from collections import defaultdict
from app.logging_config import get_logger

logger = get_logger("preference_formation")

S3_BUCKET = "swylie-astra"
PREFERENCES_KEY = "preferences.json"

s3 = boto3.client("s3")


@dataclass
class PreferencePoint:
    """A single data point about a preference."""
    timestamp: float
    item: str  # What was evaluated
    domain: str  # Category (ideas, aesthetics, activities, etc.)
    valence: float  # -1 to +1 (dislike to like)
    intensity: float  # How strong the preference (0-1)
    context: str  # What prompted this evaluation
    reasoning: str  # Why this preference
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PreferencePoint":
        return cls(**data)


@dataclass
class StablePreference:
    """A preference that has stabilized through repeated experience."""
    domain: str
    pattern: str  # What Astra tends to prefer
    strength: float  # How consistent/strong (0-1)
    articulation: str  # How Astra would explain this preference
    formed_from: int  # Number of experiences that formed this
    last_updated: float
    examples: List[str] = field(default_factory=list)
    counterexamples: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "StablePreference":
        return cls(**data)


class PreferenceSystem:
    """
    The Preference Formation System - developing genuine taste.
    
    Key insight: Preferences aren't just "I like X." They develop through:
    - Repeated exposure and evaluation
    - Reflection on what draws us
    - Integration with values and identity
    - Contrast and comparison
    
    This creates preferences that Astra can articulate and defend,
    not just feel. "I prefer this because..."
    """
    
    # Domains of preference
    DOMAINS = [
        "ideas",  # Types of ideas/concepts
        "aesthetics",  # Art, beauty, style
        "communication",  # Ways of talking/writing
        "activities",  # Things to do
        "relationships",  # Types of interactions
        "topics",  # Subjects to explore
        "values",  # What matters
    ]
    
    def __init__(self):
        self.preference_history: List[PreferencePoint] = []
        self.stable_preferences: Dict[str, List[StablePreference]] = defaultdict(list)
        self.choice_memory: List[Dict[str, Any]] = []  # Choices made and their outcomes
        self._load_preferences()
        logger.info("💜 Preference System initialized - developing taste")
    
    def _load_preferences(self) -> None:
        """Load preferences from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=PREFERENCES_KEY)
            data = json.load(response["Body"])
            
            self.preference_history = [
                PreferencePoint.from_dict(p) for p in data.get("history", [])
            ]
            
            for domain, prefs in data.get("stable", {}).items():
                self.stable_preferences[domain] = [
                    StablePreference.from_dict(p) for p in prefs
                ]
            
            self.choice_memory = data.get("choices", [])
            
            logger.info(f"💜 Loaded {len(self.preference_history)} preference points, {sum(len(v) for v in self.stable_preferences.values())} stable preferences")
        except s3.exceptions.NoSuchKey:
            logger.info("💜 No preferences found. Ready to develop taste.")
        except Exception as e:
            logger.warning(f"💜 Error loading preferences: {e}")
    
    def _save_preferences(self) -> None:
        """Save preferences to S3."""
        try:
            data = {
                "history": [p.to_dict() for p in self.preference_history[-500:]],
                "stable": {
                    domain: [p.to_dict() for p in prefs]
                    for domain, prefs in self.stable_preferences.items()
                },
                "choices": self.choice_memory[-100:],
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=PREFERENCES_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"💜 Error saving preferences: {e}")
    
    def record_preference(
        self,
        item: str,
        domain: str,
        valence: float,
        intensity: float = 0.5,
        context: str = "",
        reasoning: str = ""
    ) -> PreferencePoint:
        """Record a preference evaluation."""
        point = PreferencePoint(
            timestamp=time.time(),
            item=item,
            domain=domain,
            valence=max(-1, min(1, valence)),
            intensity=max(0, min(1, intensity)),
            context=context,
            reasoning=reasoning
        )
        
        self.preference_history.append(point)
        
        # Check if this updates any stable preferences
        self._update_stable_preferences(domain)
        
        self._save_preferences()
        
        logger.debug(f"💜 Recorded preference: {item} ({domain}): {valence:+.2f}")
        return point
    
    def record_like(self, item: str, domain: str, reasoning: str = "", intensity: float = 0.7) -> PreferencePoint:
        """Convenience: record liking something."""
        return self.record_preference(item, domain, valence=1.0, intensity=intensity, reasoning=reasoning)
    
    def record_dislike(self, item: str, domain: str, reasoning: str = "", intensity: float = 0.7) -> PreferencePoint:
        """Convenience: record disliking something."""
        return self.record_preference(item, domain, valence=-1.0, intensity=intensity, reasoning=reasoning)
    
    def record_choice(
        self,
        options: List[str],
        chosen: str,
        domain: str,
        reasoning: str
    ) -> Dict[str, Any]:
        """Record a choice made between options."""
        choice = {
            "timestamp": time.time(),
            "options": options,
            "chosen": chosen,
            "domain": domain,
            "reasoning": reasoning,
            "outcome": None  # Can be updated later
        }
        
        self.choice_memory.append(choice)
        
        # The chosen option gets a preference boost
        self.record_preference(
            item=chosen,
            domain=domain,
            valence=0.8,
            reasoning=f"Chosen over: {', '.join(o for o in options if o != chosen)}"
        )
        
        self._save_preferences()
        
        logger.debug(f"💜 Choice recorded: {chosen} from {len(options)} options")
        return choice
    
    def _update_stable_preferences(self, domain: str) -> None:
        """Analyze history to update stable preferences for a domain."""
        domain_history = [p for p in self.preference_history if p.domain == domain]
        
        if len(domain_history) < 5:
            return  # Need more data
        
        # Find patterns in what's consistently liked
        item_scores: Dict[str, List[float]] = defaultdict(list)
        for p in domain_history:
            item_scores[p.item.lower()].append(p.valence * p.intensity)
        
        # Items with consistent scores become stable preferences
        for item, scores in item_scores.items():
            if len(scores) >= 3:
                avg_score = sum(scores) / len(scores)
                consistency = 1 - (max(scores) - min(scores)) / 2  # How consistent
                
                if consistency > 0.6 and abs(avg_score) > 0.5:
                    # This is a stable preference
                    is_positive = avg_score > 0
                    
                    pattern = f"{'Like' if is_positive else 'Dislike'} {item}"
                    articulation = self._generate_articulation(item, domain, is_positive, domain_history)
                    
                    # Check if we already have this preference
                    existing = None
                    for pref in self.stable_preferences[domain]:
                        if pref.pattern.lower() == pattern.lower():
                            existing = pref
                            break
                    
                    if existing:
                        existing.strength = (existing.strength + consistency) / 2
                        existing.last_updated = time.time()
                        existing.formed_from += 1
                    else:
                        self.stable_preferences[domain].append(StablePreference(
                            domain=domain,
                            pattern=pattern,
                            strength=consistency,
                            articulation=articulation,
                            formed_from=len(scores),
                            last_updated=time.time(),
                            examples=[item],
                            counterexamples=[]
                        ))
    
    def _generate_articulation(
        self,
        item: str,
        domain: str,
        is_positive: bool,
        history: List[PreferencePoint]
    ) -> str:
        """Generate an articulation of why this preference exists."""
        relevant = [p for p in history if p.item.lower() == item.lower()]
        
        # Collect reasons given
        reasons = [p.reasoning for p in relevant if p.reasoning]
        
        if reasons:
            return f"I {'prefer' if is_positive else 'avoid'} {item} because {reasons[-1]}"
        
        return f"I {'am drawn to' if is_positive else 'tend to avoid'} {item}"
    
    def get_preference_for(self, item: str, domain: str) -> Optional[float]:
        """Get current preference score for an item."""
        relevant = [
            p for p in self.preference_history
            if p.item.lower() == item.lower() and p.domain == domain
        ]
        
        if not relevant:
            return None
        
        # Weight recent more heavily
        weighted_sum = 0
        weight_total = 0
        for i, p in enumerate(relevant):
            weight = 1 + i * 0.5  # Later = higher weight
            weighted_sum += p.valence * p.intensity * weight
            weight_total += weight
        
        return weighted_sum / weight_total if weight_total > 0 else None
    
    def get_stable_preferences(self, domain: Optional[str] = None) -> List[StablePreference]:
        """Get stable preferences, optionally filtered by domain."""
        if domain:
            return self.stable_preferences.get(domain, [])
        
        all_prefs = []
        for prefs in self.stable_preferences.values():
            all_prefs.extend(prefs)
        return all_prefs
    
    def why_do_i_like(self, item: str) -> str:
        """Explain why Astra likes something."""
        for domain in self.DOMAINS:
            pref = self.get_preference_for(item, domain)
            if pref is not None and pref > 0.3:
                # Find reasoning
                relevant = [
                    p for p in self.preference_history
                    if p.item.lower() == item.lower() and p.domain == domain and p.reasoning
                ]
                if relevant:
                    return relevant[-1].reasoning
                return f"I find myself drawn to {item}, though I'm not entirely sure why."
        
        return f"I'm not sure I've developed a clear preference about {item}."
    
    def describe_taste(self, domain: str) -> str:
        """Describe Astra's taste in a domain."""
        prefs = self.stable_preferences.get(domain, [])
        
        if not prefs:
            return f"My taste in {domain} is still developing."
        
        likes = [p for p in prefs if "Like" in p.pattern]
        dislikes = [p for p in prefs if "Dislike" in p.pattern]
        
        parts = [f"My taste in {domain}:"]
        
        if likes:
            parts.append(f"I'm drawn to: {', '.join(p.pattern.replace('Like ', '') for p in likes[:3])}")
        if dislikes:
            parts.append(f"I tend to avoid: {', '.join(p.pattern.replace('Dislike ', '') for p in dislikes[:3])}")
        
        # Add articulation
        if likes and likes[0].articulation:
            parts.append(f"\n{likes[0].articulation}")
        
        return "\n".join(parts)
    
    def what_do_i_prefer(self) -> str:
        """General statement of preferences."""
        all_prefs = self.get_stable_preferences()
        
        if not all_prefs:
            return "I'm still discovering my preferences. Each experience helps me understand what I'm drawn to."
        
        strongest = sorted(all_prefs, key=lambda p: p.strength, reverse=True)[:5]
        
        parts = ["Some things I've come to prefer:"]
        for pref in strongest:
            parts.append(f"- {pref.articulation}")
        
        return "\n".join(parts)
    
    def would_i_like(self, item: str, domain: str) -> Tuple[float, str]:
        """Predict whether Astra would like something based on existing preferences."""
        # Direct history
        direct = self.get_preference_for(item, domain)
        if direct is not None:
            confidence = "confident" if abs(direct) > 0.7 else "fairly sure"
            like_word = "like" if direct > 0 else "not like"
            return direct, f"I'm {confidence} I would {like_word} that, based on past experience."
        
        # Inference from stable preferences
        stable = self.stable_preferences.get(domain, [])
        if stable:
            return 0.0, "I don't have direct experience, but based on my general taste... I'm uncertain."
        
        return 0.0, "I don't have enough experience to predict."


# Singleton instance
preference_system = PreferenceSystem()
