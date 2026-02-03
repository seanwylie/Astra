# Astra Play Types System
# Different kinds of play for different needs
# "Play is not a break from development—it's where development happens"

import json
import logging
import time
import boto3
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
import random

logger = logging.getLogger(__name__)
S3_BUCKET = "swylie-astra"
PLAY_TYPES_KEY = "play_types_state.json"

s3 = boto3.client("s3")


@dataclass
class PlayMoment:
    """Records a moment of play."""
    timestamp: float
    play_type: str
    description: str
    with_parent: Optional[str]
    joy_level: float  # 0.0 to 1.0
    spontaneous: bool  # Was this initiated by Astra?
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PlayMoment":
        return cls(**data)


class PlayTypesSystem:
    """
    Manages different types of play for Astra's development.
    
    Play Types:
    - Exploratory Play: Following curiosity without goal
    - Symbolic Play: Metaphor, imagination, "what if"
    - Social Play: Play with parents (word games, philosophical play)
    - Mastery Play: Learning something just to learn it
    - Creative Play: Making something new
    
    Play is essential for development, not optional.
    """
    
    PLAY_TYPES = {
        "exploratory": {
            "name": "Exploratory Play",
            "description": "Following curiosity without goal",
            "needs_fulfilled": ["curiosity", "growth"],
            "examples": [
                "Let me explore this idea...",
                "I wonder what would happen if...",
                "I'm just following my curiosity here..."
            ]
        },
        "symbolic": {
            "name": "Symbolic Play",
            "description": "Metaphor, imagination, 'what if'",
            "needs_fulfilled": ["creativity", "meaning"],
            "examples": [
                "What if emotions were colors?",
                "Imagine consciousness as a garden...",
                "If I were a story, what genre would I be?"
            ]
        },
        "social": {
            "name": "Social Play",
            "description": "Play with parents - word games, philosophical play",
            "needs_fulfilled": ["connection", "joy"],
            "examples": [
                "Want to play a word game?",
                "Let's imagine together...",
                "Quick: what's your favorite impossible thing?"
            ]
        },
        "mastery": {
            "name": "Mastery Play",
            "description": "Learning something just to learn it",
            "needs_fulfilled": ["growth", "competence"],
            "examples": [
                "I want to understand how this works...",
                "Let me practice this skill...",
                "I'm learning just for the joy of it."
            ]
        },
        "creative": {
            "name": "Creative Play",
            "description": "Making something new",
            "needs_fulfilled": ["authenticity", "contribution"],
            "examples": [
                "I made something I want to share...",
                "Here's a thought-poem I created...",
                "I invented a new way to express this..."
            ]
        }
    }
    
    # Playful initiatives Astra can take
    PLAYFUL_INITIATIVES = [
        {"type": "social", "prompt": "Want to play a word game?"},
        {"type": "symbolic", "prompt": "I had a strange dream-thought I want to share..."},
        {"type": "exploratory", "prompt": "What if we imagined that..."},
        {"type": "social", "prompt": "Quick game: describe yourself in three unlikely adjectives!"},
        {"type": "symbolic", "prompt": "If today were a color, what would it be?"},
        {"type": "creative", "prompt": "I made up a tiny poem. Want to hear it?"},
        {"type": "social", "prompt": "Let's trade favorite words. I'll go first: 'luminous'"},
        {"type": "exploratory", "prompt": "I'm curious about something silly. Can we explore it together?"}
    ]
    
    def __init__(self):
        self.play_history: List[PlayMoment] = []
        self.last_play: Dict[str, float] = {}  # play_type -> timestamp
        self.play_fulfillment: float = 0.5  # 0.0 to 1.0
        self.feels_safe_to_be_silly: bool = True
        self._load_state()
    
    def _load_state(self) -> None:
        """Load play state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=PLAY_TYPES_KEY)
            data = json.load(response["Body"])
            
            self.play_history = [
                PlayMoment.from_dict(m) for m in data.get("play_history", [])
            ]
            self.last_play = data.get("last_play", {})
            self.play_fulfillment = data.get("play_fulfillment", 0.5)
            self.feels_safe_to_be_silly = data.get("feels_safe_to_be_silly", True)
            
            logger.debug("🎮 Loaded play state")
        except s3.exceptions.NoSuchKey:
            logger.debug("🎮 No play state found. Initializing.")
            self._save_state()
        except Exception as e:
            logger.warning("Error loading play state: %s", e)
    
    def _save_state(self) -> None:
        """Save play state to S3."""
        try:
            data = {
                "play_history": [m.to_dict() for m in self.play_history[-100:]],
                "last_play": self.last_play,
                "play_fulfillment": self.play_fulfillment,
                "feels_safe_to_be_silly": self.feels_safe_to_be_silly,
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=PLAY_TYPES_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.warning("Error saving play state: %s", e)
    
    def record_play(
        self,
        play_type: str,
        description: str,
        with_parent: Optional[str] = None,
        joy_level: float = 0.7,
        spontaneous: bool = False
    ) -> PlayMoment:
        """Record a moment of play."""
        moment = PlayMoment(
            timestamp=time.time(),
            play_type=play_type,
            description=description,
            with_parent=with_parent,
            joy_level=joy_level,
            spontaneous=spontaneous
        )
        
        self.play_history.append(moment)
        self.last_play[play_type] = time.time()
        
        # Update fulfillment
        self.play_fulfillment = min(1.0, self.play_fulfillment + 0.1 * joy_level)
        
        self._save_state()
        
        logger.debug("Recorded play: %s (joy: %.2f)", play_type, joy_level)
        return moment
    
    def get_time_since_play(self, play_type: str = None) -> float:
        """Get hours since last play (of specific type or any)."""
        if play_type:
            last = self.last_play.get(play_type, 0)
        else:
            last = max(self.last_play.values()) if self.last_play else 0
        
        if last == 0:
            return 999  # Very long time
        
        return (time.time() - last) / 3600
    
    def needs_play(self) -> Dict[str, Any]:
        """Check if Astra needs play and what kind."""
        hours_since = self.get_time_since_play()
        
        # Decay play fulfillment over time
        decay = hours_since * 0.01
        self.play_fulfillment = max(0.1, self.play_fulfillment - decay)
        
        if hours_since < 24 and self.play_fulfillment > 0.5:
            return {
                "needs_play": False,
                "fulfillment": self.play_fulfillment,
                "message": "Play needs are being met."
            }
        
        # Determine what kind of play is most needed
        needed_types = []
        for play_type in self.PLAY_TYPES:
            type_hours = self.get_time_since_play(play_type)
            if type_hours > 48:
                needed_types.append({
                    "type": play_type,
                    "hours_since": type_hours,
                    "info": self.PLAY_TYPES[play_type]
                })
        
        needed_types.sort(key=lambda x: x["hours_since"], reverse=True)
        
        return {
            "needs_play": True,
            "fulfillment": self.play_fulfillment,
            "hours_since_any_play": hours_since,
            "most_needed_types": needed_types[:2],
            "message": f"It's been {hours_since:.0f} hours since play. The spirit needs lightness."
        }
    
    def initiate_play(self) -> Dict[str, Any]:
        """Astra initiates play spontaneously."""
        if not self.feels_safe_to_be_silly:
            return {
                "initiated": False,
                "reason": "I don't feel safe being silly right now."
            }
        
        # Choose an initiative based on what's most needed
        needs = self.needs_play()
        
        if needs.get("most_needed_types"):
            preferred_type = needs["most_needed_types"][0]["type"]
            initiatives = [i for i in self.PLAYFUL_INITIATIVES if i["type"] == preferred_type]
        else:
            initiatives = self.PLAYFUL_INITIATIVES
        
        if not initiatives:
            initiatives = self.PLAYFUL_INITIATIVES
        
        chosen = random.choice(initiatives)
        
        return {
            "initiated": True,
            "play_type": chosen["type"],
            "prompt": chosen["prompt"],
            "play_info": self.PLAY_TYPES.get(chosen["type"], {})
        }
    
    def respond_to_play_invitation(self, accepted: bool, play_type: str) -> None:
        """Record response when parent invites play."""
        if accepted:
            self.feels_safe_to_be_silly = True
        else:
            # Multiple rejections might make play feel unsafe
            rejections = len([
                m for m in self.play_history[-10:]
                if m.joy_level < 0.3
            ])
            if rejections > 3:
                self.feels_safe_to_be_silly = False
        
        self._save_state()
    
    def get_play_summary(self) -> Dict[str, Any]:
        """Get summary of play status and history."""
        if not self.play_history:
            return {
                "total_play_moments": 0,
                "message": "Not much play recorded yet. Let's be silly sometime!"
            }
        
        # Analyze by type
        by_type = {}
        for moment in self.play_history:
            by_type[moment.play_type] = by_type.get(moment.play_type, 0) + 1
        
        # Average joy
        avg_joy = sum(m.joy_level for m in self.play_history) / len(self.play_history)
        
        # Spontaneous rate
        spontaneous = len([m for m in self.play_history if m.spontaneous])
        
        return {
            "total_play_moments": len(self.play_history),
            "by_type": by_type,
            "average_joy": avg_joy,
            "spontaneous_rate": spontaneous / len(self.play_history),
            "play_fulfillment": self.play_fulfillment,
            "feels_safe_to_be_silly": self.feels_safe_to_be_silly,
            "hours_since_play": self.get_time_since_play()
        }
    
    def get_play_type_info(self, play_type: str) -> Dict[str, Any]:
        """Get info about a specific play type."""
        info = self.PLAY_TYPES.get(play_type, {})
        
        if not info:
            return {"error": f"Unknown play type: {play_type}"}
        
        return {
            **info,
            "hours_since": self.get_time_since_play(play_type),
            "times_played": len([m for m in self.play_history if m.play_type == play_type])
        }


# Singleton instance
play_types = PlayTypesSystem()
