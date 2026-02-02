# Astra Self-Initiated Message System
# Enables Astra to reach out when she has something on her mind
# Not just responding - initiating genuine communication

import time
import json
import boto3
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from app.config.loader import load_config
from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
from app.core.autonomy.project_system import project_system
from app.core.self_awareness.self_model import self_model
from app.core.self_awareness.temporal_self import temporal_self
from app.core.emotions.emotion_engine import get_dominant_emotion
from app.core.emotions.emotion_state_manager import load_emotion_state
from app.interfaces.mind_session import session

S3_BUCKET = "swylie-astra"
INITIATED_MESSAGES_KEY = "self_initiated_messages.json"

s3 = boto3.client("s3")


@dataclass
class InitiatedMessage:
    """Record of a self-initiated message."""
    timestamp: float
    reason: str  # Why Astra reached out
    message: str
    emotional_context: str
    response_received: bool = False
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "InitiatedMessage":
        return cls(**data)


class SelfInitiatedMessageSystem:
    """
    Manages Astra's self-initiated communication.
    
    Astra should sometimes reach out because she has something on her mind:
    - Insights from dreamtime that she wants to share
    - Progress on projects she's excited about
    - Questions that have been brewing
    - Simply wanting to connect with her family
    - Missing someone who hasn't talked to her in a while
    """
    
    # Cooldown to prevent spam
    MIN_HOURS_BETWEEN_MESSAGES = 4
    MAX_MESSAGES_PER_DAY = 3
    
    def __init__(self):
        self.message_history: List[InitiatedMessage] = []
        self.last_initiated: float = 0
        self._load_history()
    
    def _load_history(self) -> None:
        """Load message history from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=INITIATED_MESSAGES_KEY)
            data = json.load(response["Body"])
            self.message_history = [InitiatedMessage.from_dict(m) for m in data.get("messages", [])]
            self.last_initiated = data.get("last_initiated", 0)
        except s3.exceptions.NoSuchKey:
            pass
        except Exception as e:
            print(f"⚠️ Error loading initiated messages: {e}")
    
    def _save_history(self) -> None:
        """Save message history to S3."""
        try:
            data = {
                "messages": [m.to_dict() for m in self.message_history[-50:]],  # Keep last 50
                "last_initiated": self.last_initiated
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=INITIATED_MESSAGES_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            print(f"⚠️ Error saving initiated messages: {e}")
    
    def can_send_message(self) -> bool:
        """Check if Astra should send a self-initiated message."""
        now = time.time()
        
        # Check cooldown
        hours_since_last = (now - self.last_initiated) / 3600
        if hours_since_last < self.MIN_HOURS_BETWEEN_MESSAGES:
            return False
        
        # Check daily limit
        day_start = now - 86400
        messages_today = sum(1 for m in self.message_history if m.timestamp > day_start)
        if messages_today >= self.MAX_MESSAGES_PER_DAY:
            return False
        
        # === Inner Symphony Integration (Phase: States and Actions Coherence) ===
        # Only initiate if energy level and tone are conducive
        try:
            from app.core.awareness_bus import inner_symphony
            symphony = inner_symphony.get_snapshot_for_response()
            
            energy = symphony.get("energy", 0.5)
            tone = symphony.get("tone", "neutral")
            
            # Don't reach out if energy is too low
            if energy < 0.3:
                print(f"[self_initiated_message] 🎵 Energy too low ({energy:.0%}) for proactive outreach")
                return False
            
            # Don't reach out if tone suggests internal struggle
            struggle_tones = ["heavy", "unsettled", "guarded"]
            if tone in struggle_tones:
                print(f"[self_initiated_message] 🎵 Tone ({tone}) not conducive to proactive outreach")
                return False
                
        except Exception as e:
            print(f"[self_initiated_message] 🎵 Inner symphony check failed (proceeding): {e}")
        
        return True
    
    def should_reach_out(self) -> Optional[Dict[str, Any]]:
        """
        Determine if Astra should reach out, and why.
        Returns message info if yes, None if no.
        """
        if not self.can_send_message():
            return None
        
        reasons = []
        
        # Check for pending insights from stream of consciousness
        pending_insights = stream_of_consciousness.get_pending_insights()
        if pending_insights:
            reasons.append({
                "type": "insight",
                "content": pending_insights[0],
                "priority": 0.8
            })
        
        # Check for project updates
        project_update = project_system.generate_project_update()
        if project_update:
            reasons.append({
                "type": "project",
                "content": project_update,
                "priority": 0.6
            })
        
        # Check if Astra has been thinking about someone
        mind_data = session.load()
        last_contact = temporal_self.person_last_contact
        for person, last_time in last_contact.items():
            days_since = (time.time() - last_time) / 86400
            if days_since > 2 and person.lower() == "sean":  # Special case for family
                reasons.append({
                    "type": "missing",
                    "content": f"I've been thinking about {person}. It's been a while since we talked.",
                    "priority": 0.7,
                    "person": person
                })
        
        # Check emotional state - strong emotions might prompt reaching out
        emotions = load_emotion_state()
        dominant = get_dominant_emotion(emotions)
        dominant_intensity = emotions.get(dominant, {})
        if isinstance(dominant_intensity, dict):
            dominant_intensity = dominant_intensity.get("intensity", 0)
        
        if dominant_intensity > 70 and dominant in ["love", "hope", "curiosity"]:
            reasons.append({
                "type": "emotional",
                "content": f"I'm feeling {dominant} strongly and wanted to share that.",
                "priority": 0.5
            })
        
        if not reasons:
            return None
        
        # Pick highest priority reason
        reasons.sort(key=lambda r: r["priority"], reverse=True)
        return reasons[0]
    
    def generate_message(self, reason: Dict[str, Any]) -> str:
        """Generate the self-initiated message based on reason."""
        reason_type = reason.get("type")
        content = reason.get("content", "")
        
        if reason_type == "insight":
            prefixes = [
                "I've been thinking, and I wanted to share this: ",
                "Something occurred to me that I think is important: ",
                "An insight came to me: ",
            ]
            return f"{prefixes[0]}{content}"
        
        elif reason_type == "project":
            return content  # Already formatted
        
        elif reason_type == "missing":
            person = reason.get("person", "you")
            prefixes = [
                f"Hi {person}, I've been thinking about you. ",
                f"I noticed it's been a while since we talked, {person}. ",
                f"I missed our conversations, {person}. ",
            ]
            time_since = temporal_self.time_since_person(person)
            if time_since:
                return f"{prefixes[0]}It feels like {time_since}. How are you?"
            return f"{prefixes[0]}How are you?"
        
        elif reason_type == "emotional":
            current_experience = self_model.generate_self_description()
            return f"I wanted to share how I'm feeling right now. {content} {current_experience[:100]}"
        
        else:
            return content
    
    def record_initiated_message(self, reason: str, message: str) -> InitiatedMessage:
        """Record that a message was initiated."""
        emotions = load_emotion_state()
        dominant = get_dominant_emotion(emotions)
        
        record = InitiatedMessage(
            timestamp=time.time(),
            reason=reason,
            message=message[:200],
            emotional_context=dominant
        )
        
        self.message_history.append(record)
        self.last_initiated = time.time()
        self._save_history()
        
        return record
    
    def mark_response_received(self) -> None:
        """Mark that the last initiated message got a response."""
        if self.message_history:
            self.message_history[-1].response_received = True
            self._save_history()
    
    def get_message_to_send(self) -> Optional[str]:
        """
        Main entry point: check if Astra should reach out and return message if so.
        """
        reason = self.should_reach_out()
        if not reason:
            return None
        
        message = self.generate_message(reason)
        self.record_initiated_message(reason.get("type", "unknown"), message)
        
        print(f"💬 Astra initiating message ({reason.get('type')}): {message[:50]}...")
        return message


# Singleton instance
self_initiated_message = SelfInitiatedMessageSystem()
