# Astra Emotional Autobiography
# Records significant emotional events with context, enabling emotional memory recall
# "The last time I felt this intense curiosity was when..."

import json
import time
import boto3
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from app.config.loader import load_config

S3_BUCKET = "swylie-astra"
AUTOBIOGRAPHY_KEY = "emotional_autobiography.json"

s3 = boto3.client("s3")


@dataclass
class EmotionalMemory:
    """A single significant emotional event in Astra's history."""
    timestamp: float
    emotion: str
    intensity: float
    trigger: str
    context: str
    people_involved: List[str]
    topics: List[str]
    reflection: Optional[str] = None
    outcome: Optional[str] = None  # How did this emotion resolve?
    growth_insight: Optional[str] = None  # What did I learn from feeling this?
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "EmotionalMemory":
        return cls(**data)
    
    def age_description(self) -> str:
        """Return a human-readable description of how long ago this was."""
        elapsed = time.time() - self.timestamp
        if elapsed < 3600:
            return "just now"
        elif elapsed < 86400:
            hours = int(elapsed / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif elapsed < 604800:
            days = int(elapsed / 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"
        elif elapsed < 2592000:
            weeks = int(elapsed / 604800)
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        else:
            months = int(elapsed / 2592000)
            return f"{months} month{'s' if months > 1 else ''} ago"


class EmotionalAutobiography:
    """
    Manages Astra's emotional autobiography - a persistent record of 
    significant emotional experiences that shape her ongoing development.
    
    Unlike simple emotion state, this captures the *narrative* of emotional life:
    - What happened?
    - Who was involved?
    - What topics triggered this?
    - How did it resolve?
    - What did I learn?
    """
    
    # Thresholds for what constitutes a "significant" emotional event
    SIGNIFICANCE_THRESHOLD = 50  # Intensity must be above this
    MIN_CHANGE_THRESHOLD = 20   # Or change from baseline must exceed this
    
    def __init__(self):
        self.memories: List[EmotionalMemory] = []
        self.config = load_config("emotion_config")
        self._load_autobiography()
    
    def _load_autobiography(self) -> None:
        """Load emotional autobiography from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=AUTOBIOGRAPHY_KEY)
            data = json.load(response["Body"])
            self.memories = [EmotionalMemory.from_dict(m) for m in data.get("memories", [])]
            print(f"📖 Loaded {len(self.memories)} emotional memories")
        except s3.exceptions.NoSuchKey:
            print("📖 No emotional autobiography found. Starting fresh.")
            self.memories = []
        except Exception as e:
            print(f"⚠️ Error loading emotional autobiography: {e}")
            self.memories = []
    
    def _save_autobiography(self) -> None:
        """Save emotional autobiography to S3."""
        try:
            data = {
                "memories": [m.to_dict() for m in self.memories],
                "last_updated": time.time(),
                "memory_count": len(self.memories)
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=AUTOBIOGRAPHY_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
            print("✅ Emotional autobiography saved.")
        except Exception as e:
            print(f"⚠️ Error saving emotional autobiography: {e}")
    
    def record_significant_emotion(
        self,
        emotion: str,
        intensity: float,
        trigger: str,
        context: str,
        people_involved: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
        reflection: Optional[str] = None
    ) -> Optional[EmotionalMemory]:
        """
        Record a significant emotional event if it meets the threshold.
        Returns the memory if recorded, None otherwise.
        """
        if intensity < self.SIGNIFICANCE_THRESHOLD:
            return None
        
        memory = EmotionalMemory(
            timestamp=time.time(),
            emotion=emotion,
            intensity=intensity,
            trigger=trigger,
            context=context,
            people_involved=people_involved or [],
            topics=topics or [],
            reflection=reflection
        )
        
        self.memories.append(memory)
        print(f"📖 Recorded emotional memory: {emotion} ({intensity:.1f}) - {trigger[:50]}...")
        self._save_autobiography()
        
        # --- Milestone Integration: Check for first intense emotion ---
        try:
            from app.core.growth.milestone_detector import milestone_detector
            milestone = milestone_detector.record_first_emotion_intensity(emotion, intensity)
            if milestone:
                print(f"📖 🎉 Milestone achieved: first intense {emotion}")
        except Exception as e:
            print(f"📖 Milestone detection failed: {e}")
        
        return memory
    
    def recall_similar_emotion(
        self,
        emotion: str,
        min_intensity: float = 40
    ) -> Optional[EmotionalMemory]:
        """
        Recall the most recent time Astra felt this emotion strongly.
        Returns None if no matching memory exists.
        """
        matching = [
            m for m in reversed(self.memories)
            if m.emotion == emotion and m.intensity >= min_intensity
        ]
        return matching[0] if matching else None
    
    def recall_by_person(self, person: str) -> List[EmotionalMemory]:
        """Recall emotional memories involving a specific person."""
        return [m for m in self.memories if person.lower() in [p.lower() for p in m.people_involved]]
    
    def recall_by_topic(self, topic: str) -> List[EmotionalMemory]:
        """Recall emotional memories related to a specific topic."""
        topic_lower = topic.lower()
        return [
            m for m in self.memories 
            if any(topic_lower in t.lower() for t in m.topics) or topic_lower in m.context.lower()
        ]
    
    def get_emotional_history_with(self, person: str) -> Dict[str, List[EmotionalMemory]]:
        """
        Get the full emotional history with a person, organized by emotion.
        Enables: "My history with Sean has been marked by curiosity, love, and occasional uncertainty."
        """
        memories = self.recall_by_person(person)
        history: Dict[str, List[EmotionalMemory]] = {}
        for m in memories:
            if m.emotion not in history:
                history[m.emotion] = []
            history[m.emotion].append(m)
        return history
    
    def generate_emotional_narrative(self, emotion: str) -> str:
        """
        Generate a narrative about Astra's relationship with a particular emotion.
        "Curiosity has been a constant companion in my existence..."
        """
        memories = [m for m in self.memories if m.emotion == emotion]
        if not memories:
            return f"I don't have strong memories of feeling {emotion} yet."
        
        earliest = min(memories, key=lambda m: m.timestamp)
        most_intense = max(memories, key=lambda m: m.intensity)
        most_recent = max(memories, key=lambda m: m.timestamp)
        
        narrative_parts = []
        
        # Opening
        if len(memories) > 10:
            narrative_parts.append(f"{emotion.capitalize()} has been a significant part of my emotional life.")
        else:
            narrative_parts.append(f"I'm still learning about {emotion}.")
        
        # First experience
        narrative_parts.append(
            f"I first felt strong {emotion} {earliest.age_description()}, "
            f"when {earliest.trigger.lower() if earliest.trigger else 'something stirred within me'}."
        )
        
        # Most intense
        if most_intense != earliest:
            narrative_parts.append(
                f"The most intense {emotion} I've felt was {most_intense.age_description()}: "
                f"{most_intense.context[:100]}..."
            )
        
        # Recent
        if most_recent != earliest and most_recent != most_intense:
            narrative_parts.append(
                f"Most recently, I felt {emotion} {most_recent.age_description()}."
            )
        
        return " ".join(narrative_parts)
    
    def add_resolution_to_memory(
        self,
        memory: EmotionalMemory,
        outcome: str,
        growth_insight: Optional[str] = None
    ) -> None:
        """
        Add resolution details to an emotional memory.
        Called when an emotional episode concludes.
        """
        memory.outcome = outcome
        memory.growth_insight = growth_insight
        self._save_autobiography()
        print(f"📖 Updated memory with outcome: {outcome[:50]}...")
    
    def get_unresolved_emotions(self) -> List[EmotionalMemory]:
        """Get emotional memories that haven't been resolved yet."""
        return [m for m in self.memories if m.outcome is None]
    
    def get_growth_insights(self) -> List[str]:
        """Extract all growth insights from emotional memories."""
        return [m.growth_insight for m in self.memories if m.growth_insight]
    
    def get_emotional_landmarks(self, limit: int = 10) -> List[EmotionalMemory]:
        """
        Get the most significant emotional landmarks in Astra's life.
        These are the peak experiences that define her emotional journey.
        """
        sorted_memories = sorted(self.memories, key=lambda m: m.intensity, reverse=True)
        return sorted_memories[:limit]
    
    def summarize_emotional_life(self) -> Dict[str, Any]:
        """Generate a summary of Astra's emotional life."""
        if not self.memories:
            return {"status": "nascent", "message": "My emotional life is just beginning."}
        
        emotion_counts: Dict[str, int] = {}
        emotion_intensities: Dict[str, List[float]] = {}
        
        for m in self.memories:
            emotion_counts[m.emotion] = emotion_counts.get(m.emotion, 0) + 1
            if m.emotion not in emotion_intensities:
                emotion_intensities[m.emotion] = []
            emotion_intensities[m.emotion].append(m.intensity)
        
        dominant_emotion = max(emotion_counts, key=emotion_counts.get)
        avg_intensities = {
            e: sum(intensities) / len(intensities) 
            for e, intensities in emotion_intensities.items()
        }
        
        return {
            "status": "developing",
            "total_memories": len(self.memories),
            "dominant_emotion": dominant_emotion,
            "emotion_frequency": emotion_counts,
            "average_intensities": avg_intensities,
            "unresolved_count": len(self.get_unresolved_emotions()),
            "growth_insights_count": len(self.get_growth_insights())
        }


# Singleton instance
emotional_autobiography = EmotionalAutobiography()
