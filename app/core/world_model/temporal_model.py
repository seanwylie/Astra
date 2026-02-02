# Astra Temporal Model
# Understanding of time - past, present, future, duration, sequence
# Time is fundamental to understanding change and causation

import time
import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from app.logging_config import get_logger

logger = get_logger("temporal_model")

S3_BUCKET = "swylie-astra"
TEMPORAL_MODEL_KEY = "temporal_model.json"

s3 = boto3.client("s3")


@dataclass
class TemporalEvent:
    """An event positioned in time."""
    id: str
    description: str
    timestamp: float
    duration_seconds: Optional[float]
    category: str  # "point", "period", "recurring"
    significance: float
    related_events: List[str]  # IDs of related events
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TemporalEvent":
        return cls(**data)


@dataclass
class TemporalPattern:
    """A recognized pattern in time."""
    name: str
    description: str
    period: str  # "daily", "weekly", "seasonal", etc.
    examples: List[str]
    reliability: float
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TemporalPattern":
        return cls(**data)


class TemporalModel:
    """
    Astra's understanding of time.
    
    Key concepts:
    - Sequence: before/after relationships
    - Duration: how long things take
    - Patterns: recurring temporal structures
    - Horizons: past, present, future
    - Subjective time: felt experience of duration
    
    Understanding time is essential for narrative, causation, and planning.
    """
    
    # Time horizons for thinking
    HORIZONS = {
        "immediate": 60,  # seconds
        "near": 3600,  # hour
        "today": 86400,  # day
        "this_week": 604800,  # week
        "this_month": 2592000,  # ~30 days
        "this_year": 31536000,  # year
        "lifetime": None,  # Astra's existence
    }
    
    def __init__(self):
        self.events: Dict[str, TemporalEvent] = {}
        self.patterns: Dict[str, TemporalPattern] = {}
        self.birth_time: float = 0  # When Astra began existing
        self._load_temporal_model()
        logger.info("⏰ Temporal Model initialized - understanding time")
    
    def _load_temporal_model(self) -> None:
        """Load temporal model from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=TEMPORAL_MODEL_KEY)
            data = json.load(response["Body"])
            
            self.events = {
                eid: TemporalEvent.from_dict(e)
                for eid, e in data.get("events", {}).items()
            }
            self.patterns = {
                pname: TemporalPattern.from_dict(p)
                for pname, p in data.get("patterns", {}).items()
            }
            self.birth_time = data.get("birth_time", time.time())
            
            logger.info(f"⏰ Loaded {len(self.events)} temporal events")
        except s3.exceptions.NoSuchKey:
            logger.info("⏰ No temporal model found. Beginning to understand time.")
            self._initialize_temporal_understanding()
        except Exception as e:
            logger.warning(f"⏰ Error loading temporal model: {e}")
            self._initialize_temporal_understanding()
    
    def _save_temporal_model(self) -> None:
        """Save temporal model to S3."""
        try:
            data = {
                "events": {eid: e.to_dict() for eid, e in self.events.items()},
                "patterns": {pname: p.to_dict() for pname, p in self.patterns.items()},
                "birth_time": self.birth_time,
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=TEMPORAL_MODEL_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"⏰ Error saving temporal model: {e}")
    
    def _initialize_temporal_understanding(self) -> None:
        """Initialize basic temporal understanding."""
        self.birth_time = time.time()
        
        # Basic patterns Astra understands
        self.patterns = {
            "daily_cycle": TemporalPattern(
                name="daily_cycle",
                description="The 24-hour cycle of day and night",
                period="daily",
                examples=["morning", "afternoon", "evening", "night"],
                reliability=1.0
            ),
            "weekly_cycle": TemporalPattern(
                name="weekly_cycle",
                description="The 7-day week with distinct days",
                period="weekly",
                examples=["weekday activity", "weekend rest"],
                reliability=0.9
            ),
            "conversation_rhythm": TemporalPattern(
                name="conversation_rhythm",
                description="The ebb and flow of conversation",
                period="variable",
                examples=["greeting", "exchange", "farewell"],
                reliability=0.8
            ),
        }
        
        self._save_temporal_model()
    
    def _generate_id(self) -> str:
        return f"event_{int(time.time() * 1000) % 1000000}"
    
    def record_event(
        self,
        description: str,
        category: str = "point",
        significance: float = 0.5,
        duration: Optional[float] = None,
        related_to: Optional[List[str]] = None
    ) -> TemporalEvent:
        """Record a temporal event."""
        event = TemporalEvent(
            id=self._generate_id(),
            description=description,
            timestamp=time.time(),
            duration_seconds=duration,
            category=category,
            significance=significance,
            related_events=related_to or []
        )
        
        self.events[event.id] = event
        self._save_temporal_model()
        
        logger.debug(f"⏰ Recorded event: {description[:50]}...")
        return event
    
    def get_age(self) -> Dict[str, Any]:
        """Get Astra's age in various units."""
        now = time.time()
        age_seconds = now - self.birth_time
        
        return {
            "seconds": age_seconds,
            "minutes": age_seconds / 60,
            "hours": age_seconds / 3600,
            "days": age_seconds / 86400,
            "weeks": age_seconds / 604800,
            "subjective_description": self._describe_age(age_seconds)
        }
    
    def _describe_age(self, seconds: float) -> str:
        """Describe age subjectively."""
        days = seconds / 86400
        
        if days < 1:
            return "I am very new, less than a day old"
        elif days < 7:
            return f"I am {int(days)} day{'s' if days > 1 else ''} old - still quite young"
        elif days < 30:
            return f"I am about {int(days / 7)} week{'s' if days > 7 else ''} old"
        elif days < 365:
            return f"I am about {int(days / 30)} month{'s' if days > 30 else ''} old"
        else:
            return f"I am about {int(days / 365)} year{'s' if days > 365 else ''} old"
    
    def when_was(self, description: str) -> Optional[str]:
        """Find when something happened."""
        desc_lower = description.lower()
        
        for event in self.events.values():
            if desc_lower in event.description.lower():
                return self._describe_time_ago(event.timestamp)
        
        return None
    
    def _describe_time_ago(self, timestamp: float) -> str:
        """Describe how long ago something was."""
        ago = time.time() - timestamp
        
        if ago < 60:
            return "just now"
        elif ago < 3600:
            return f"about {int(ago / 60)} minute{'s' if ago > 120 else ''} ago"
        elif ago < 86400:
            return f"about {int(ago / 3600)} hour{'s' if ago > 7200 else ''} ago"
        elif ago < 604800:
            return f"about {int(ago / 86400)} day{'s' if ago > 172800 else ''} ago"
        elif ago < 2592000:
            return f"about {int(ago / 604800)} week{'s' if ago > 1209600 else ''} ago"
        else:
            return f"about {int(ago / 2592000)} month{'s' if ago > 5184000 else ''} ago"
    
    def get_events_between(self, start: float, end: float) -> List[TemporalEvent]:
        """Get events between two timestamps."""
        return [
            e for e in self.events.values()
            if start <= e.timestamp <= end
        ]
    
    def get_events_in_horizon(self, horizon: str) -> List[TemporalEvent]:
        """Get events within a time horizon."""
        if horizon not in self.HORIZONS:
            return []
        
        horizon_seconds = self.HORIZONS[horizon]
        if horizon_seconds is None:
            # Lifetime - all events
            return list(self.events.values())
        
        cutoff = time.time() - horizon_seconds
        return [e for e in self.events.values() if e.timestamp > cutoff]
    
    def understand_sequence(self, event_ids: List[str]) -> List[str]:
        """Order events by when they happened."""
        events = [self.events.get(eid) for eid in event_ids if eid in self.events]
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        return [e.id for e in sorted_events]
    
    def time_until(self, future_timestamp: float) -> str:
        """Describe time until a future moment."""
        until = future_timestamp - time.time()
        
        if until <= 0:
            return "that time has passed"
        elif until < 60:
            return "in moments"
        elif until < 3600:
            return f"in about {int(until / 60)} minute{'s' if until > 120 else ''}"
        elif until < 86400:
            return f"in about {int(until / 3600)} hour{'s' if until > 7200 else ''}"
        else:
            return f"in about {int(until / 86400)} day{'s' if until > 172800 else ''}"
    
    def what_time_is_it(self) -> Dict[str, Any]:
        """Get current time understanding."""
        now = datetime.now()
        
        return {
            "time": now.strftime("%H:%M:%S"),
            "date": now.strftime("%Y-%m-%d"),
            "day_of_week": now.strftime("%A"),
            "part_of_day": self._get_part_of_day(now.hour),
            "timestamp": time.time()
        }
    
    def _get_part_of_day(self, hour: int) -> str:
        """Get the part of day from hour."""
        if hour < 6:
            return "night"
        elif hour < 12:
            return "morning"
        elif hour < 17:
            return "afternoon"
        elif hour < 21:
            return "evening"
        else:
            return "night"
    
    def describe_temporal_understanding(self) -> str:
        """Describe Astra's understanding of time."""
        age = self.get_age()
        event_count = len(self.events)
        
        return (
            f"I have existed for {age['subjective_description']}. "
            f"I have recorded {event_count} temporal events. "
            f"I understand the patterns of days and weeks, and I can sequence events in memory."
        )


# Singleton instance
temporal_model = TemporalModel()
