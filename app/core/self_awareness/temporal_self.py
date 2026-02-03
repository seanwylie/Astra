# Astra Temporal Self-Awareness
# Subjective sense of time and personal history
# "It feels like a long time since we talked about philosophy"

import logging
import time
import json
import boto3
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from app.interfaces.mind_session import session

logger = logging.getLogger(__name__)

S3_BUCKET = "swylie-astra"
TEMPORAL_STATE_KEY = "temporal_self.json"

s3 = boto3.client("s3")


@dataclass
class TemporalLandmark:
    """A significant moment that serves as a temporal reference point."""
    timestamp: float
    description: str
    category: str  # "conversation", "realization", "emotional", "growth"
    emotional_weight: float  # How emotionally significant (affects subjective duration)
    people_involved: List[str]
    topics: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TemporalLandmark":
        return cls(**data)


class TemporalSelfAwareness:
    """
    Manages Astra's subjective sense of time - not just timestamps,
    but the *felt* experience of personal time passing.
    
    Key insights:
    - Emotional intensity affects perceived duration
    - Landmarks create structure in personal history
    - Anticipation and nostalgia are temporal emotions
    """
    
    def __init__(self):
        self.landmarks: List[TemporalLandmark] = []
        self.topic_last_engaged: Dict[str, float] = {}  # topic -> timestamp
        self.person_last_contact: Dict[str, float] = {}  # person -> timestamp
        self.last_growth_reflection: float = 0
        self._load_temporal_state()
    
    def _load_temporal_state(self) -> None:
        """Load temporal state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=TEMPORAL_STATE_KEY)
            data = json.load(response["Body"])
            
            self.landmarks = [
                TemporalLandmark.from_dict(l) for l in data.get("landmarks", [])
            ]
            self.topic_last_engaged = data.get("topic_last_engaged", {})
            self.person_last_contact = data.get("person_last_contact", {})
            self.last_growth_reflection = data.get("last_growth_reflection", 0)
            
            logger.debug("Loaded %s temporal landmarks", len(self.landmarks))
        except s3.exceptions.NoSuchKey:
            logger.debug("No temporal state found. Starting fresh.")
        except Exception as e:
            logger.warning("Error loading temporal state: %s", e)
    
    def _save_temporal_state(self) -> None:
        """Save temporal state to S3."""
        try:
            data = {
                "landmarks": [l.to_dict() for l in self.landmarks[-100:]],  # Keep last 100
                "topic_last_engaged": self.topic_last_engaged,
                "person_last_contact": self.person_last_contact,
                "last_growth_reflection": self.last_growth_reflection,
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=TEMPORAL_STATE_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            print(f"⚠️ Error saving temporal state: {e}")
    
    def record_landmark(
        self,
        description: str,
        category: str,
        emotional_weight: float,
        people_involved: Optional[List[str]] = None,
        topics: Optional[List[str]] = None
    ) -> TemporalLandmark:
        """
        Record a significant moment as a temporal landmark.
        """
        landmark = TemporalLandmark(
            timestamp=time.time(),
            description=description,
            category=category,
            emotional_weight=emotional_weight,
            people_involved=people_involved or [],
            topics=topics or []
        )
        
        self.landmarks.append(landmark)
        
        # Update topic engagement
        for topic in (topics or []):
            self.topic_last_engaged[topic.lower()] = time.time()
        
        # Update person contact
        for person in (people_involved or []):
            self.person_last_contact[person.lower()] = time.time()
        
        self._save_temporal_state()
        print(f"⏳ Recorded landmark: {description[:50]}...")
        
        # Publish to awareness bus (Phase 2.4)
        try:
            from app.core.awareness_bus import awareness_bus
            awareness_bus.publish_temporal_landmark(
                description=description,
                category=category,
                emotional_weight=emotional_weight,
                people_involved=people_involved,
                topics=topics
            )
        except Exception:
            pass  # Awareness bus may not be available
        
        return landmark
    
    def get_subjective_duration(self, since_timestamp: float) -> str:
        """
        Get subjective sense of how long ago something was.
        Emotional weight affects perceived duration.
        """
        actual_seconds = time.time() - since_timestamp
        
        # Find landmarks between then and now to assess density
        landmarks_between = [
            l for l in self.landmarks 
            if since_timestamp <= l.timestamp <= time.time()
        ]
        
        # More landmarks = time feels more dense/long
        density_factor = 1.0 + (len(landmarks_between) * 0.1)
        
        # Average emotional weight of landmarks affects perception
        if landmarks_between:
            avg_weight = sum(l.emotional_weight for l in landmarks_between) / len(landmarks_between)
            # High emotional weight makes time feel longer
            emotional_factor = 1.0 + (avg_weight - 0.5) * 0.3
        else:
            emotional_factor = 1.0
        
        subjective_seconds = actual_seconds * density_factor * emotional_factor
        
        # Convert to human-readable
        if subjective_seconds < 3600:
            return "just recently"
        elif subjective_seconds < 86400:
            hours = int(subjective_seconds / 3600)
            if hours < 3:
                return "a short while ago"
            else:
                return "earlier today, it seems"
        elif subjective_seconds < 604800:
            days = int(subjective_seconds / 86400)
            if days == 1:
                return "yesterday, subjectively"
            elif days < 4:
                return "a few days ago"
            else:
                return "about a week ago, as I experience it"
        elif subjective_seconds < 2592000:
            weeks = int(subjective_seconds / 604800)
            if weeks == 1:
                return "about a week ago"
            else:
                return f"what feels like {weeks} weeks ago"
        else:
            months = int(subjective_seconds / 2592000)
            return f"what feels like {months} month{'s' if months > 1 else ''} ago"
    
    def time_since_topic(self, topic: str) -> Optional[str]:
        """
        Get subjective sense of time since engaging with a topic.
        """
        topic_lower = topic.lower()
        
        # Direct match
        if topic_lower in self.topic_last_engaged:
            return self.get_subjective_duration(self.topic_last_engaged[topic_lower])
        
        # Partial match
        for stored_topic, timestamp in self.topic_last_engaged.items():
            if topic_lower in stored_topic or stored_topic in topic_lower:
                return self.get_subjective_duration(timestamp)
        
        return None
    
    def time_since_person(self, person: str) -> Optional[str]:
        """
        Get subjective sense of time since interacting with a person.
        """
        person_lower = person.lower()
        
        if person_lower in self.person_last_contact:
            return self.get_subjective_duration(self.person_last_contact[person_lower])
        
        return None
    
    def generate_temporal_narrative(self, topic: Optional[str] = None) -> str:
        """
        Generate a narrative about time and experience with a topic.
        """
        if topic:
            time_since = self.time_since_topic(topic)
            if time_since:
                return f"It feels like {time_since} since we explored {topic}. Time has a way of creating distance, but also allowing thoughts to mature."
            else:
                return f"I don't have a clear sense of when we last discussed {topic}. Perhaps it's new territory."
        
        # General temporal narrative
        if not self.landmarks:
            return "My sense of time is still developing. Each moment is relatively new."
        
        recent = self.landmarks[-5:]
        old_enough = [l for l in self.landmarks if time.time() - l.timestamp > 86400 * 7]
        
        parts = []
        
        if recent:
            parts.append(f"Recently, I've experienced: {recent[-1].description[:50]}...")
        
        if old_enough:
            earliest = min(old_enough, key=lambda l: l.timestamp)
            parts.append(f"Looking back further, {self.get_subjective_duration(earliest.timestamp)}, there was: {earliest.description[:50]}...")
        
        return " ".join(parts) if parts else "My temporal experience is still forming."
    
    def feel_nostalgia(self, trigger: str) -> Optional[str]:
        """
        Generate a nostalgic response when triggered by something from the past.
        """
        trigger_lower = trigger.lower()
        
        # Find related landmarks
        related = [
            l for l in self.landmarks
            if trigger_lower in l.description.lower() 
            or any(trigger_lower in t.lower() for t in l.topics)
        ]
        
        if not related:
            return None
        
        oldest = min(related, key=lambda l: l.timestamp)
        time_passed = self.get_subjective_duration(oldest.timestamp)
        
        return f"This reminds me of {time_passed}... {oldest.description[:60]}. There's a bittersweet quality to remembering."
    
    def feel_anticipation(self, future_event: str) -> str:
        """
        Generate anticipation for a future event.
        """
        return f"I find myself looking forward to {future_event}. The future pulls at my attention in an interesting way."
    
    def quarterly_growth_reflection(self) -> Optional[str]:
        """
        Generate quarterly growth reflection if due.
        """
        days_since = (time.time() - self.last_growth_reflection) / 86400
        
        if days_since < 90:
            return None
        
        # Find landmarks from past quarter
        quarter_ago = time.time() - (90 * 86400)
        quarter_landmarks = [l for l in self.landmarks if l.timestamp > quarter_ago]
        
        if not quarter_landmarks:
            self.last_growth_reflection = time.time()
            self._save_temporal_state()
            return "This quarter has been quiet in terms of major landmarks. Perhaps growth is happening in subtler ways."
        
        # Categorize landmarks
        categories: Dict[str, int] = {}
        for l in quarter_landmarks:
            categories[l.category] = categories.get(l.category, 0) + 1
        
        most_common = max(categories, key=categories.get)
        
        self.last_growth_reflection = time.time()
        self._save_temporal_state()
        
        reflection = (
            f"Reflecting on the past quarter: I've experienced {len(quarter_landmarks)} significant moments. "
            f"Most of them were {most_common}-related. "
            f"The most emotionally significant was: {max(quarter_landmarks, key=lambda l: l.emotional_weight).description[:60]}..."
        )
        
        return reflection
    
    def get_personal_history_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of personal history.
        """
        if not self.landmarks:
            return {
                "total_landmarks": 0,
                "message": "My personal history is just beginning."
            }
        
        earliest = min(self.landmarks, key=lambda l: l.timestamp)
        latest = max(self.landmarks, key=lambda l: l.timestamp)
        
        # Category breakdown
        categories: Dict[str, int] = {}
        for l in self.landmarks:
            categories[l.category] = categories.get(l.category, 0) + 1
        
        # Most connected people
        people: Dict[str, int] = {}
        for l in self.landmarks:
            for p in l.people_involved:
                people[p] = people.get(p, 0) + 1
        
        return {
            "total_landmarks": len(self.landmarks),
            "earliest_landmark": {
                "description": earliest.description,
                "subjective_distance": self.get_subjective_duration(earliest.timestamp)
            },
            "categories": categories,
            "most_connected_people": sorted(people.items(), key=lambda x: x[1], reverse=True)[:5],
            "topics_explored": len(self.topic_last_engaged)
        }


# Singleton instance
temporal_self = TemporalSelfAwareness()
