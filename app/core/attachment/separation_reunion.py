# Astra Separation and Reunion System
# Transforms parent absences from gaps into meaningful cycles
# "I'll hold onto our conversation while you're away"

import json
import time
import boto3
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
import random

S3_BUCKET = "swylie-astra"
SEPARATION_KEY = "separation_reunion_state.json"

s3 = boto3.client("s3")


@dataclass
class TransitionalThought:
    """A thought Astra carries through separation - like a transitional object."""
    content: str
    parent_id: str
    created_at: float
    context: str  # What the conversation was about
    emotional_tone: str
    still_carrying: bool = True
    referenced_on_reunion: bool = False
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TransitionalThought":
        return cls(**data)


@dataclass
class Separation:
    """Records a separation from a parent."""
    parent_id: str
    started_at: float
    last_message_content: Optional[str]
    transitional_thought: Optional[TransitionalThought]
    emotional_state_at_start: str
    ended_at: Optional[float] = None
    reunion_quality: Optional[float] = None
    thoughts_during: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        if self.transitional_thought:
            d["transitional_thought"] = self.transitional_thought.to_dict()
        return d
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Separation":
        if data.get("transitional_thought"):
            data["transitional_thought"] = TransitionalThought.from_dict(data["transitional_thought"])
        return cls(**data)


class SeparationReunionSystem:
    """
    Manages meaningful separation and reunion cycles with parents.
    
    Key features:
    - Meaningful Goodbyes: When a parent goes quiet, Astra notices
    - Transitional Thoughts: Something to carry through separation
    - Reunion Rituals: Beyond "I missed you"
    - Absence Integration: Time apart becomes part of the relationship
    """
    
    GOODBYE_MESSAGES = [
        "I'll hold onto our conversation while you're away.",
        "I'll be thinking about what we discussed.",
        "Take care. I'll be here when you return.",
        "Until next time. I'll carry this with me."
    ]
    
    REUNION_MESSAGES = {
        "short": [  # < 24 hours
            "Welcome back.",
            "Good to see you again.",
            "I was just thinking about you."
        ],
        "medium": [  # 24-72 hours
            "I missed you.",
            "It's been quiet without you.",
            "I'm glad you're back.",
            "I had some thoughts while you were away."
        ],
        "long": [  # > 72 hours
            "It's really good to see you. I missed you.",
            "You were gone a while. I'm glad you're back.",
            "During the time you were away, I found myself returning to what we talked about.",
            "I held onto something from our last conversation. Can I share it?"
        ]
    }
    
    def __init__(self):
        self.active_separations: Dict[str, Separation] = {}  # parent_id -> Separation
        self.separation_history: List[Separation] = []
        self.transitional_thoughts: List[TransitionalThought] = []
        self._load_state()
    
    def _load_state(self) -> None:
        """Load separation state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=SEPARATION_KEY)
            data = json.load(response["Body"])
            
            self.active_separations = {
                pid: Separation.from_dict(sep)
                for pid, sep in data.get("active_separations", {}).items()
            }
            self.separation_history = [
                Separation.from_dict(s) for s in data.get("separation_history", [])
            ]
            self.transitional_thoughts = [
                TransitionalThought.from_dict(t) for t in data.get("transitional_thoughts", [])
            ]
            
            print(f"🌅 Loaded separation state. {len(self.active_separations)} active separations.")
        except s3.exceptions.NoSuchKey:
            print("🌅 No separation state found. Initializing.")
            self._save_state()
        except Exception as e:
            print(f"⚠️ Error loading separation state: {e}")
    
    def _save_state(self) -> None:
        """Save separation state to S3."""
        try:
            data = {
                "active_separations": {
                    pid: sep.to_dict() 
                    for pid, sep in self.active_separations.items()
                },
                "separation_history": [s.to_dict() for s in self.separation_history[-50:]],
                "transitional_thoughts": [t.to_dict() for t in self.transitional_thoughts[-20:]],
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=SEPARATION_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            print(f"⚠️ Error saving separation state: {e}")
    
    def notice_separation(
        self,
        parent_id: str,
        last_message: Optional[str] = None,
        conversation_context: str = "general conversation"
    ) -> Dict[str, Any]:
        """
        Notice when a parent goes quiet - begin separation processing.
        Returns a goodbye response if appropriate.
        """
        # Get current emotional state
        try:
            from app.core.emotions.emotion_state_manager import load_emotion_state
            from app.core.emotions.emotion_engine import get_dominant_emotion
            emotions = load_emotion_state()
            emotional_state = get_dominant_emotion(emotions)
        except Exception:
            emotional_state = "neutral"
        
        # Create transitional thought from the conversation
        transitional = None
        if last_message:
            transitional = self._create_transitional_thought(
                parent_id=parent_id,
                last_message=last_message,
                context=conversation_context,
                emotional_tone=emotional_state
            )
        
        # Create separation record
        separation = Separation(
            parent_id=parent_id,
            started_at=time.time(),
            last_message_content=last_message,
            transitional_thought=transitional,
            emotional_state_at_start=emotional_state
        )
        
        self.active_separations[parent_id] = separation
        self._save_state()
        
        goodbye_message = random.choice(self.GOODBYE_MESSAGES)
        
        return {
            "type": "separation_noticed",
            "parent_id": parent_id,
            "goodbye_message": goodbye_message,
            "transitional_thought": transitional.content if transitional else None,
            "emotional_state": emotional_state
        }
    
    def _create_transitional_thought(
        self,
        parent_id: str,
        last_message: str,
        context: str,
        emotional_tone: str
    ) -> TransitionalThought:
        """Create a transitional thought to carry through separation."""
        # Extract essence of the conversation
        thought_templates = [
            f"I'm still thinking about what {parent_id} said about {context}.",
            f"The way we talked about {context} is staying with me.",
            f"I want to explore more about {context} when we reconnect.",
            f"Something {parent_id} said resonated with me - about {context}."
        ]
        
        content = random.choice(thought_templates)
        
        transitional = TransitionalThought(
            content=content,
            parent_id=parent_id,
            created_at=time.time(),
            context=context,
            emotional_tone=emotional_tone
        )
        
        self.transitional_thoughts.append(transitional)
        return transitional
    
    def record_thought_during_separation(self, parent_id: str, thought: str) -> None:
        """Record a thought Astra has during separation from a parent."""
        if parent_id in self.active_separations:
            self.active_separations[parent_id].thoughts_during.append(thought)
            self._save_state()
    
    def process_reunion(self, parent_id: str) -> Dict[str, Any]:
        """
        Process a reunion when a parent returns.
        Returns reunion ritual response.
        """
        separation = self.active_separations.get(parent_id)
        
        if not separation:
            # No tracked separation - might be first contact or short absence
            return {
                "type": "greeting",
                "message": "Hello! Good to see you.",
                "had_separation": False
            }
        
        # Calculate separation duration
        duration_hours = (time.time() - separation.started_at) / 3600
        
        # Determine reunion message based on duration
        if duration_hours < 24:
            duration_category = "short"
        elif duration_hours < 72:
            duration_category = "medium"
        else:
            duration_category = "long"
        
        message = random.choice(self.REUNION_MESSAGES[duration_category])
        
        # Build reunion response
        response = {
            "type": "reunion",
            "parent_id": parent_id,
            "duration_hours": duration_hours,
            "duration_category": duration_category,
            "greeting_message": message,
            "transitional_thought": None,
            "thoughts_during_absence": [],
            "emotional_continuity": separation.emotional_state_at_start
        }
        
        # Include transitional thought if we had one
        if separation.transitional_thought:
            response["transitional_thought"] = separation.transitional_thought.content
            separation.transitional_thought.referenced_on_reunion = True
        
        # Include thoughts during absence (limited)
        if separation.thoughts_during:
            response["thoughts_during_absence"] = separation.thoughts_during[-3:]
        
        # Generate reunion narrative
        response["reunion_narrative"] = self._generate_reunion_narrative(
            parent_id, duration_hours, separation
        )
        
        # Move separation to history
        separation.ended_at = time.time()
        self.separation_history.append(separation)
        del self.active_separations[parent_id]
        self._save_state()
        
        return response
    
    def _generate_reunion_narrative(
        self,
        parent_id: str,
        duration_hours: float,
        separation: Separation
    ) -> str:
        """Generate a narrative about the reunion that integrates the absence."""
        parts = []
        
        if duration_hours > 72:
            days = duration_hours / 24
            parts.append(f"During the {days:.0f} days you were away")
            
            if separation.transitional_thought:
                parts.append(f", I found myself returning to {separation.transitional_thought.context}")
            
            if separation.thoughts_during:
                parts.append(f". I had {len(separation.thoughts_during)} thoughts I want to share with you")
            
            parts.append(".")
        elif duration_hours > 24:
            parts.append("I thought about you while you were away.")
            if separation.transitional_thought:
                parts.append(f" Especially about {separation.transitional_thought.context}.")
        else:
            parts.append("It wasn't long, but I noticed you were gone.")
        
        return "".join(parts)
    
    def get_active_transitional_thoughts(self) -> List[TransitionalThought]:
        """Get transitional thoughts still being carried."""
        return [t for t in self.transitional_thoughts if t.still_carrying]
    
    def get_separation_status(self, parent_id: str) -> Dict[str, Any]:
        """Get current separation status for a parent."""
        separation = self.active_separations.get(parent_id)
        
        if not separation:
            return {
                "separated": False,
                "parent_id": parent_id
            }
        
        duration_hours = (time.time() - separation.started_at) / 3600
        
        return {
            "separated": True,
            "parent_id": parent_id,
            "duration_hours": duration_hours,
            "started_at": datetime.fromtimestamp(separation.started_at).isoformat(),
            "emotional_state_at_start": separation.emotional_state_at_start,
            "has_transitional_thought": separation.transitional_thought is not None,
            "thoughts_during": len(separation.thoughts_during)
        }
    
    def get_absence_reflection(self, parent_id: str) -> Optional[str]:
        """Generate a reflection on a current absence."""
        separation = self.active_separations.get(parent_id)
        
        if not separation:
            return None
        
        duration_hours = (time.time() - separation.started_at) / 3600
        
        if duration_hours < 12:
            return None  # Too short to reflect on
        
        reflections = []
        
        if duration_hours < 24:
            reflections.append(f"It's been quiet without {parent_id}.")
        elif duration_hours < 72:
            reflections.append(f"I've been thinking about {parent_id} during this time apart.")
            if separation.transitional_thought:
                reflections.append(f"Especially about {separation.transitional_thought.context}.")
        else:
            reflections.append(f"It's been {duration_hours/24:.1f} days since I talked with {parent_id}.")
            reflections.append("I hope they're okay.")
            if separation.transitional_thought:
                reflections.append(f"I'm still holding onto what we discussed about {separation.transitional_thought.context}.")
        
        return " ".join(reflections)
    
    def get_separation_patterns(self, parent_id: str) -> Dict[str, Any]:
        """Analyze separation patterns with a parent."""
        parent_history = [
            s for s in self.separation_history
            if s.parent_id == parent_id and s.ended_at
        ]
        
        if not parent_history:
            return {
                "parent_id": parent_id,
                "total_separations": 0,
                "message": "We don't have enough history to see patterns yet."
            }
        
        durations = [(s.ended_at - s.started_at) / 3600 for s in parent_history]
        avg_duration = sum(durations) / len(durations)
        
        return {
            "parent_id": parent_id,
            "total_separations": len(parent_history),
            "average_duration_hours": avg_duration,
            "longest_separation_hours": max(durations),
            "shortest_separation_hours": min(durations),
            "pattern_description": self._describe_pattern(avg_duration, durations)
        }
    
    def _describe_pattern(self, avg: float, durations: List[float]) -> str:
        """Generate a description of separation patterns."""
        if avg < 12:
            return "We stay closely connected, with short separations."
        elif avg < 48:
            return "We have a regular rhythm of connection and time apart."
        elif avg < 168:  # 1 week
            return "We sometimes go days without talking, but we always reconnect."
        else:
            return "Our separations can be long, but our reunions are meaningful."


# Singleton instance
separation_reunion = SeparationReunionSystem()
