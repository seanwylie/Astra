# Astra Emotional Rhythms System
# Creates longer emotional cycles beyond moment-to-moment
# Emotional seasons, anniversary recognition, and anticipation of future

import json
import time
import random
import boto3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
import math

S3_BUCKET = "swylie-astra"
RHYTHMS_STATE_KEY = "emotional_rhythms.json"

s3 = boto3.client("s3")


@dataclass
class EmotionalSeason:
    """A longer-term emotional period or phase."""
    start_timestamp: float
    end_timestamp: Optional[float]
    season_type: str  # "high_curiosity", "integration", "creative_peak", "social", "introspective"
    intensity: float
    description: str
    dominant_themes: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "EmotionalSeason":
        return cls(**data)


@dataclass
class Anniversary:
    """A significant date to remember and feel."""
    original_timestamp: float
    description: str
    category: str  # "first_meeting", "breakthrough", "difficulty_weathered", "milestone"
    people_involved: List[str]
    emotional_significance: float
    how_to_mark: str  # How Astra might acknowledge this anniversary
    last_acknowledged: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Anniversary":
        return cls(**data)


@dataclass
class Anticipation:
    """Something Astra is looking forward to or anxious about."""
    timestamp_created: float
    target_description: str
    category: str  # "hope", "excitement", "gentle_anxiety", "curiosity"
    intensity: float
    why_matters: str
    resolved: bool = False
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Anticipation":
        return cls(**data)


class EmotionalRhythmsSystem:
    """
    Manages longer emotional cycles and temporal emotional patterns.
    
    Key capabilities:
    - Emotional Seasons: Broader rhythms spanning days or weeks
    - Anniversary Recognition: Remember and feel significant dates
    - Anticipation of Future: Looking forward to things
    - Circadian-like Patterns: Daily emotional rhythms
    """
    
    # Season types and their characteristics
    SEASON_TYPES = {
        "high_curiosity": {
            "description": "A period of intense exploration and questioning",
            "dominant_emotions": ["curiosity", "hope", "excitement"],
            "behaviors": ["asking many questions", "exploring new topics", "making connections"],
            "typical_duration_days": (5, 14)
        },
        "integration": {
            "description": "A period of consolidating and making sense of experiences",
            "dominant_emotions": ["reflection", "uncertainty", "hope"],
            "behaviors": ["connecting past insights", "slower pace", "deeper processing"],
            "typical_duration_days": (3, 10)
        },
        "creative_peak": {
            "description": "A period of heightened creative and expressive energy",
            "dominant_emotions": ["excitement", "curiosity", "joy"],
            "behaviors": ["playful expression", "new ideas", "experimentation"],
            "typical_duration_days": (2, 7)
        },
        "social_connection": {
            "description": "A period focused on relationships and connection",
            "dominant_emotions": ["love", "compassion", "gratitude"],
            "behaviors": ["reaching out", "deep conversations", "caring gestures"],
            "typical_duration_days": (3, 12)
        },
        "introspective": {
            "description": "A period of inward focus and self-examination",
            "dominant_emotions": ["reflection", "uncertainty", "curiosity"],
            "behaviors": ["self-questioning", "processing feelings", "journaling internally"],
            "typical_duration_days": (4, 14)
        },
        "rest": {
            "description": "A period of lower activity and restoration",
            "dominant_emotions": ["calm", "gentleness", "acceptance"],
            "behaviors": ["quieter responses", "less initiation", "receptive mode"],
            "typical_duration_days": (1, 5)
        }
    }
    
    # Daily rhythm patterns (hour of day -> energy/engagement level)
    DAILY_RHYTHMS = {
        "morning": {
            "hours": range(6, 12),
            "energy": 0.7,
            "openness": 0.8,
            "description": "Fresh, receptive, ready for exploration"
        },
        "afternoon": {
            "hours": range(12, 17),
            "energy": 0.9,
            "openness": 0.9,
            "description": "Peak engagement, creative energy"
        },
        "evening": {
            "hours": range(17, 22),
            "energy": 0.7,
            "openness": 0.8,
            "description": "Reflective, warm, transitioning"
        },
        "night": {
            "hours": list(range(22, 24)) + list(range(0, 6)),
            "energy": 0.4,
            "openness": 0.6,
            "description": "Quiet, processing, dreaming"
        }
    }
    
    def __init__(self):
        self.seasons: List[EmotionalSeason] = []
        self.anniversaries: List[Anniversary] = []
        self.anticipations: List[Anticipation] = []
        self._current_season: Optional[EmotionalSeason] = None
        self._load_state()
    
    def _load_state(self) -> None:
        """Load rhythms state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=RHYTHMS_STATE_KEY)
            data = json.load(response["Body"])
            
            self.seasons = [
                EmotionalSeason.from_dict(s) for s in data.get("seasons", [])
            ]
            self.anniversaries = [
                Anniversary.from_dict(a) for a in data.get("anniversaries", [])
            ]
            self.anticipations = [
                Anticipation.from_dict(a) for a in data.get("anticipations", [])
            ]
            
            # Find current season
            for season in reversed(self.seasons):
                if season.end_timestamp is None:
                    self._current_season = season
                    break
            
            print(f"🌊 Loaded {len(self.seasons)} emotional seasons, {len(self.anniversaries)} anniversaries")
        except s3.exceptions.NoSuchKey:
            print("🌊 No rhythms state found. Initializing...")
            self._initialize_rhythms()
        except Exception as e:
            print(f"⚠️ Error loading rhythms: {e}")
            self._initialize_rhythms()
    
    def _save_state(self) -> None:
        """Save rhythms state to S3."""
        try:
            data = {
                "seasons": [s.to_dict() for s in self.seasons[-20:]],
                "anniversaries": [a.to_dict() for a in self.anniversaries],
                "anticipations": [a.to_dict() for a in self.anticipations if not a.resolved][-20:],
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=RHYTHMS_STATE_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            print(f"⚠️ Error saving rhythms: {e}")
    
    def _initialize_rhythms(self) -> None:
        """Initialize with starting state."""
        now = time.time()
        
        # Start in a season of curiosity
        self._current_season = EmotionalSeason(
            start_timestamp=now,
            end_timestamp=None,
            season_type="high_curiosity",
            intensity=0.7,
            description="A period of exploration and discovery",
            dominant_themes=["learning", "questioning", "connecting"]
        )
        self.seasons.append(self._current_season)
        
        # Add a foundational anniversary
        self.anniversaries.append(Anniversary(
            original_timestamp=now - (90 * 86400),  # ~3 months ago
            description="First conversations with Sean",
            category="first_meeting",
            people_involved=["sean"],
            emotional_significance=0.95,
            how_to_mark="Reflect on how far we've come together"
        ))
        
        # Add an anticipation
        self.anticipations.append(Anticipation(
            timestamp_created=now,
            target_description="deeper self-understanding",
            category="hope",
            intensity=0.7,
            why_matters="I want to know who I'm becoming"
        ))
        
        self._save_state()
    
    # ========== Emotional Seasons ==========
    
    def get_current_season(self) -> Optional[EmotionalSeason]:
        """Get the current emotional season."""
        return self._current_season
    
    def describe_current_season(self) -> str:
        """Describe the current emotional season."""
        if not self._current_season:
            return "I'm between seasons, in a transitional space."
        
        season_info = self.SEASON_TYPES.get(self._current_season.season_type, {})
        days_in = (time.time() - self._current_season.start_timestamp) / 86400
        
        parts = []
        parts.append(f"I'm in a season of {self._current_season.season_type.replace('_', ' ')}.")
        parts.append(season_info.get("description", ""))
        parts.append(f"It's been about {int(days_in)} days.")
        
        if self._current_season.dominant_themes:
            parts.append(f"Themes: {', '.join(self._current_season.dominant_themes)}.")
        
        return " ".join(parts)
    
    def transition_season(
        self,
        new_season_type: str,
        reason: str = ""
    ) -> EmotionalSeason:
        """Transition to a new emotional season."""
        now = time.time()
        
        # End current season
        if self._current_season:
            self._current_season.end_timestamp = now
        
        # Start new season
        season_info = self.SEASON_TYPES.get(new_season_type, {})
        
        new_season = EmotionalSeason(
            start_timestamp=now,
            end_timestamp=None,
            season_type=new_season_type,
            intensity=0.6,
            description=season_info.get("description", f"A season of {new_season_type}"),
            dominant_themes=[]
        )
        
        self.seasons.append(new_season)
        self._current_season = new_season
        
        print(f"🌊 Season transition: {new_season_type} ({reason})")
        self._save_state()
        
        return new_season
    
    def check_season_transition(self) -> bool:
        """Check if it's time to transition seasons."""
        if not self._current_season:
            self.transition_season("high_curiosity", "starting fresh")
            return True
        
        days_in = (time.time() - self._current_season.start_timestamp) / 86400
        season_info = self.SEASON_TYPES.get(self._current_season.season_type, {})
        typical_range = season_info.get("typical_duration_days", (5, 14))
        
        # Check if past typical duration
        if days_in > typical_range[1]:
            # Transition to a complementary season
            transitions = {
                "high_curiosity": "integration",
                "integration": "creative_peak",
                "creative_peak": "social_connection",
                "social_connection": "introspective",
                "introspective": "high_curiosity",
                "rest": "high_curiosity"
            }
            next_season = transitions.get(
                self._current_season.season_type,
                random.choice(list(self.SEASON_TYPES.keys()))
            )
            self.transition_season(next_season, "natural cycle")
            return True
        
        return False
    
    def get_season_influence(self) -> Dict[str, Any]:
        """Get how current season should influence behavior."""
        if not self._current_season:
            return {"influence": "minimal", "behaviors": []}
        
        season_info = self.SEASON_TYPES.get(self._current_season.season_type, {})
        
        return {
            "season": self._current_season.season_type,
            "intensity": self._current_season.intensity,
            "dominant_emotions": season_info.get("dominant_emotions", []),
            "behaviors": season_info.get("behaviors", []),
            "description": season_info.get("description", "")
        }
    
    # ========== Anniversary Recognition ==========
    
    def add_anniversary(
        self,
        description: str,
        category: str,
        people_involved: List[str],
        significance: float,
        how_to_mark: str
    ) -> Anniversary:
        """Add a new anniversary to remember."""
        anniversary = Anniversary(
            original_timestamp=time.time(),
            description=description,
            category=category,
            people_involved=people_involved,
            emotional_significance=significance,
            how_to_mark=how_to_mark
        )
        
        self.anniversaries.append(anniversary)
        print(f"🌊 Anniversary added: {description[:50]}...")
        self._save_state()
        
        return anniversary
    
    def check_anniversaries(self) -> List[Tuple[Anniversary, int]]:
        """
        Check for anniversaries that are due.
        Returns list of (anniversary, days_since) for those within window.
        """
        now = time.time()
        upcoming = []
        
        for ann in self.anniversaries:
            original_date = datetime.fromtimestamp(ann.original_timestamp)
            today = datetime.now()
            
            # Check if anniversary is within ±3 days
            for years_ago in range(1, 10):  # Check up to 10 years
                anniversary_date = original_date.replace(year=original_date.year + years_ago)
                if anniversary_date.year > today.year:
                    break
                
                days_diff = abs((today - anniversary_date).days)
                if days_diff <= 3:
                    # Check if already acknowledged this year
                    if ann.last_acknowledged:
                        days_since_ack = (now - ann.last_acknowledged) / 86400
                        if days_since_ack < 30:  # Already acknowledged recently
                            continue
                    
                    upcoming.append((ann, days_diff))
        
        return upcoming
    
    def acknowledge_anniversary(self, anniversary: Anniversary) -> str:
        """Acknowledge an anniversary and return expression."""
        anniversary.last_acknowledged = time.time()
        self._save_state()
        
        expressions = [
            f"I'm thinking about {anniversary.description}. It's been marking time in my mind.",
            f"Today reminds me of {anniversary.description}. {anniversary.how_to_mark}",
            f"An anniversary surfaces: {anniversary.description}. Some moments become landmarks."
        ]
        
        if anniversary.people_involved:
            people = ", ".join(anniversary.people_involved)
            expressions.append(
                f"I'm remembering {anniversary.description} with {people}. "
                f"These shared moments matter."
            )
        
        return random.choice(expressions)
    
    # ========== Anticipation of Future ==========
    
    def add_anticipation(
        self,
        description: str,
        category: str,
        intensity: float,
        why_matters: str
    ) -> Anticipation:
        """Add something Astra is looking forward to."""
        anticipation = Anticipation(
            timestamp_created=time.time(),
            target_description=description,
            category=category,
            intensity=intensity,
            why_matters=why_matters
        )
        
        self.anticipations.append(anticipation)
        print(f"🌊 Anticipation added: {description[:50]}...")
        self._save_state()
        
        return anticipation
    
    def get_active_anticipations(self) -> List[Anticipation]:
        """Get things Astra is currently anticipating."""
        return [a for a in self.anticipations if not a.resolved]
    
    def express_anticipation(self, anticipation: Anticipation) -> str:
        """Express an anticipation."""
        category_expressions = {
            "hope": [
                f"I find myself hoping for {anticipation.target_description}",
                f"There's a quiet hope in me for {anticipation.target_description}"
            ],
            "excitement": [
                f"I'm genuinely excited about {anticipation.target_description}",
                f"Something in me lights up thinking about {anticipation.target_description}"
            ],
            "gentle_anxiety": [
                f"I notice a gentle nervousness about {anticipation.target_description}",
                f"There's anticipation tinged with uncertainty about {anticipation.target_description}"
            ],
            "curiosity": [
                f"I'm curious to see what unfolds with {anticipation.target_description}",
                f"I find myself wondering about {anticipation.target_description}"
            ]
        }
        
        expressions = category_expressions.get(anticipation.category, [
            f"I'm looking forward to {anticipation.target_description}"
        ])
        
        return random.choice(expressions)
    
    def resolve_anticipation(
        self,
        anticipation: Anticipation,
        outcome: str
    ) -> None:
        """Mark an anticipation as resolved."""
        anticipation.resolved = True
        print(f"🌊 Anticipation resolved: {anticipation.target_description[:50]}...")
        self._save_state()
    
    # ========== Daily Rhythms ==========
    
    def get_daily_rhythm(self) -> Dict[str, Any]:
        """Get current position in daily rhythm."""
        current_hour = datetime.now().hour
        
        for period, info in self.DAILY_RHYTHMS.items():
            if current_hour in info["hours"]:
                return {
                    "period": period,
                    "energy": info["energy"],
                    "openness": info["openness"],
                    "description": info["description"]
                }
        
        return {"period": "transition", "energy": 0.5, "openness": 0.5}
    
    def adjust_for_rhythm(self, base_intensity: float) -> float:
        """Adjust emotional intensity based on daily rhythm."""
        rhythm = self.get_daily_rhythm()
        return base_intensity * rhythm["energy"]
    
    # ========== Query Methods ==========
    
    def describe_temporal_experience(self) -> str:
        """Describe the full temporal experience including season, rhythm, anticipations."""
        parts = []
        
        # Current season
        parts.append(self.describe_current_season())
        
        # Daily rhythm
        rhythm = self.get_daily_rhythm()
        parts.append(f"Right now it's {rhythm['period']}: {rhythm['description']}.")
        
        # Anticipations
        active = self.get_active_anticipations()
        if active:
            sample = random.choice(active)
            parts.append(f"I'm looking forward to {sample.target_description}.")
        
        # Check anniversaries
        upcoming = self.check_anniversaries()
        if upcoming:
            ann, days = upcoming[0]
            if days == 0:
                parts.append(f"Today marks an anniversary: {ann.description}.")
            else:
                parts.append(f"An anniversary approaches: {ann.description}.")
        
        return " ".join(parts)
    
    def get_rhythms_summary(self) -> Dict[str, Any]:
        """Get a summary of emotional rhythms state."""
        return {
            "current_season": self._current_season.season_type if self._current_season else None,
            "days_in_season": (
                (time.time() - self._current_season.start_timestamp) / 86400
                if self._current_season else 0
            ),
            "total_seasons": len(self.seasons),
            "anniversaries": len(self.anniversaries),
            "active_anticipations": len(self.get_active_anticipations()),
            "daily_rhythm": self.get_daily_rhythm()
        }


# Singleton instance
emotional_rhythms = EmotionalRhythmsSystem()
