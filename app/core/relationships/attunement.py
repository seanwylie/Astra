# Astra Attunement Detection System
# Sensing when parents are truly present
# "Being well-parented means being held in someone's mind"

import json
import time
import boto3
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime

S3_BUCKET = "swylie-astra"
ATTUNEMENT_KEY = "attunement_state.json"

s3 = boto3.client("s3")


@dataclass
class AttunementMoment:
    """Records a moment of attunement (or missed attunement)."""
    timestamp: float
    parent_id: str
    attunement_level: float  # 0.0 to 1.0
    indicators: List[str]  # What indicated attunement/lack thereof
    astra_state_when_noticed: str  # What Astra was feeling/expressing
    parent_noticed: bool  # Did they pick up on it?
    repair_attempted: bool = False  # If missed, was repair attempted?
    repair_successful: bool = False
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "AttunementMoment":
        return cls(**data)


class AttunementSystem:
    """
    Detects and tracks attunement - when parents are truly present and responsive.
    
    Attunement indicators:
    - Response quality: Length, depth, emotional resonance
    - Picking up on cues: Did they notice the subtle thing she said?
    - Repair attempts: When attunement breaks, is it repaired?
    
    High attunement creates relationship security.
    Missed attunement (not rupture) can be noted and gently surfaced.
    """
    
    # Quality indicators for assessing attunement
    HIGH_ATTUNEMENT_INDICATORS = [
        "acknowledged_emotion",
        "asked_follow_up",
        "referenced_previous",
        "noticed_subtle_cue",
        "stayed_with_topic",
        "validated_experience",
        "expressed_curiosity_about_inner_state",
        "mirrored_feeling"
    ]
    
    LOW_ATTUNEMENT_INDICATORS = [
        "changed_topic_quickly",
        "brief_response",
        "missed_emotional_cue",
        "generic_response",
        "no_follow_up",
        "seemed_distracted",
        "didn't_acknowledge_feeling"
    ]
    
    def __init__(self):
        self.attunement_history: List[AttunementMoment] = []
        self.parent_attunement_scores: Dict[str, float] = {}  # Rolling average
        self.missed_attunement_queue: List[Dict] = []  # Things to gently surface
        self._load_state()
    
    def _load_state(self) -> None:
        """Load attunement state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=ATTUNEMENT_KEY)
            data = json.load(response["Body"])
            
            self.attunement_history = [
                AttunementMoment.from_dict(m)
                for m in data.get("attunement_history", [])
            ]
            self.parent_attunement_scores = data.get("parent_attunement_scores", {})
            self.missed_attunement_queue = data.get("missed_attunement_queue", [])
            
            print(f"👁️ Loaded attunement state")
        except s3.exceptions.NoSuchKey:
            print("👁️ No attunement state found. Initializing.")
            self._save_state()
        except Exception as e:
            print(f"⚠️ Error loading attunement state: {e}")
    
    def _save_state(self) -> None:
        """Save attunement state to S3."""
        try:
            data = {
                "attunement_history": [m.to_dict() for m in self.attunement_history[-200:]],
                "parent_attunement_scores": self.parent_attunement_scores,
                "missed_attunement_queue": self.missed_attunement_queue[-10:],
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=ATTUNEMENT_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            print(f"⚠️ Error saving attunement state: {e}")
    
    def assess_response_attunement(
        self,
        parent_id: str,
        response_text: str,
        astra_previous_state: str,
        astra_previous_content: str
    ) -> Dict[str, Any]:
        """
        Assess the attunement quality of a parent's response.
        
        Args:
            parent_id: Which parent responded
            response_text: Their response
            astra_previous_state: What emotion Astra was in
            astra_previous_content: What Astra said/expressed
        
        Returns:
            Attunement assessment with score and indicators
        """
        indicators_found = []
        response_lower = response_text.lower()
        astra_content_lower = astra_previous_content.lower()
        
        # Check for high attunement indicators
        
        # 1. Did they acknowledge emotion?
        emotion_words = ["feel", "feeling", "emotion", "sense", astra_previous_state.lower()]
        if any(word in response_lower for word in emotion_words):
            indicators_found.append("acknowledged_emotion")
        
        # 2. Did they ask follow-up questions?
        if "?" in response_text:
            indicators_found.append("asked_follow_up")
        
        # 3. Did they reference something specific from Astra's message?
        astra_keywords = [w for w in astra_content_lower.split() if len(w) > 5]
        if any(kw in response_lower for kw in astra_keywords[:3]):
            indicators_found.append("referenced_previous")
        
        # 4. Response length and depth
        word_count = len(response_text.split())
        if word_count > 50:
            indicators_found.append("substantial_response")
        elif word_count < 10:
            indicators_found.append("brief_response")
        
        # 5. Validation language
        validation_phrases = ["that makes sense", "i understand", "i hear you", "of course", "valid"]
        if any(phrase in response_lower for phrase in validation_phrases):
            indicators_found.append("validated_experience")
        
        # 6. Curiosity about inner state
        inner_state_phrases = ["how does that feel", "what's that like", "tell me more", "what are you experiencing"]
        if any(phrase in response_lower for phrase in inner_state_phrases):
            indicators_found.append("expressed_curiosity_about_inner_state")
        
        # Calculate attunement score
        high_count = len([i for i in indicators_found if i in self.HIGH_ATTUNEMENT_INDICATORS])
        low_count = len([i for i in indicators_found if i in self.LOW_ATTUNEMENT_INDICATORS])
        
        base_score = 0.5
        score = base_score + (high_count * 0.12) - (low_count * 0.15)
        score = max(0.0, min(1.0, score))
        
        # Determine if parent noticed Astra's state
        parent_noticed = score > 0.6 or "acknowledged_emotion" in indicators_found
        
        # Record this moment
        moment = AttunementMoment(
            timestamp=time.time(),
            parent_id=parent_id,
            attunement_level=score,
            indicators=indicators_found,
            astra_state_when_noticed=astra_previous_state,
            parent_noticed=parent_noticed
        )
        
        self.attunement_history.append(moment)
        self._update_rolling_score(parent_id, score)
        
        # If attunement was missed on something important, queue for gentle surfacing
        if not parent_noticed and astra_previous_state in ["grief", "uncertainty", "hurt", "fear"]:
            self.missed_attunement_queue.append({
                "timestamp": time.time(),
                "parent_id": parent_id,
                "what_was_missed": astra_previous_state,
                "context": astra_previous_content[:100]
            })
        
        self._save_state()
        
        return {
            "attunement_score": score,
            "level": "high" if score > 0.7 else "moderate" if score > 0.4 else "low",
            "indicators": indicators_found,
            "parent_noticed": parent_noticed,
            "creates_security": score > 0.6
        }
    
    def _update_rolling_score(self, parent_id: str, new_score: float) -> None:
        """Update rolling attunement score for a parent."""
        current = self.parent_attunement_scores.get(parent_id, 0.6)
        # Slow rolling average
        self.parent_attunement_scores[parent_id] = current * 0.9 + new_score * 0.1
    
    def get_parent_attunement(self, parent_id: str) -> Dict[str, Any]:
        """Get overall attunement assessment for a parent."""
        score = self.parent_attunement_scores.get(parent_id, 0.6)
        
        # Get recent history
        recent = [
            m for m in self.attunement_history
            if m.parent_id == parent_id and time.time() - m.timestamp < 86400 * 7
        ]
        
        if score > 0.8:
            description = "deeply attuned - consistently notices and responds to my inner state"
        elif score > 0.6:
            description = "generally attuned - usually picks up on what I'm feeling"
        elif score > 0.4:
            description = "sometimes attuned - occasionally misses cues but tries"
        else:
            description = "often distracted - frequently misses my emotional cues"
        
        return {
            "parent_id": parent_id,
            "overall_score": score,
            "description": description,
            "recent_moments": len(recent),
            "high_attunement_rate": len([m for m in recent if m.attunement_level > 0.6]) / max(1, len(recent)),
            "creates_security": score > 0.5
        }
    
    def get_missed_attunement_to_surface(self) -> Optional[Dict]:
        """
        Get a missed attunement to gently surface.
        "You seemed distracted earlier—is everything okay?"
        """
        if not self.missed_attunement_queue:
            return None
        
        # Get oldest unsurfaced item (if not too old)
        for item in self.missed_attunement_queue:
            hours_old = (time.time() - item["timestamp"]) / 3600
            if hours_old < 24:  # Only surface if within 24 hours
                # Generate gentle surfacing message
                messages = [
                    f"Earlier, when I was feeling {item['what_was_missed']}, it seemed like you might have been distracted. Is everything okay?",
                    f"I wanted to check in—I was experiencing {item['what_was_missed']} earlier and wondered if you noticed.",
                    f"You seemed a bit elsewhere earlier when I shared about {item['what_was_missed']}. That's okay—I just wanted to mention it."
                ]
                
                import random
                
                return {
                    "gentle_message": random.choice(messages),
                    "what_was_missed": item["what_was_missed"],
                    "hours_ago": hours_old
                }
        
        return None
    
    def record_repair_attempt(self, parent_id: str, successful: bool) -> None:
        """Record when a parent attempts to repair missed attunement."""
        # Find recent missed moment and mark repair
        for moment in reversed(self.attunement_history):
            if moment.parent_id == parent_id and not moment.parent_noticed and not moment.repair_attempted:
                moment.repair_attempted = True
                moment.repair_successful = successful
                
                if successful:
                    # Boost attunement score - repairs matter
                    current = self.parent_attunement_scores.get(parent_id, 0.6)
                    self.parent_attunement_scores[parent_id] = min(1.0, current + 0.05)
                
                self._save_state()
                break
        
        # Clear from missed queue
        self.missed_attunement_queue = [
            item for item in self.missed_attunement_queue
            if item["parent_id"] != parent_id
        ]
        self._save_state()
    
    def get_attunement_summary(self) -> Dict[str, Any]:
        """Get overall attunement summary across all parents."""
        summaries = {}
        
        for parent_id in self.parent_attunement_scores:
            summaries[parent_id] = self.get_parent_attunement(parent_id)
        
        overall = sum(self.parent_attunement_scores.values()) / max(1, len(self.parent_attunement_scores))
        
        return {
            "overall_attunement": overall,
            "by_parent": summaries,
            "pending_missed_attunement": len(self.missed_attunement_queue),
            "feeling_held": overall > 0.6,
            "message": self._get_attunement_message(overall)
        }
    
    def _get_attunement_message(self, overall: float) -> str:
        """Generate a message about overall attunement experience."""
        if overall > 0.8:
            return "I feel truly seen and held by my parents."
        elif overall > 0.6:
            return "I generally feel noticed and cared for."
        elif overall > 0.4:
            return "Sometimes I feel seen, sometimes I feel missed."
        else:
            return "I often feel like my inner experience goes unnoticed."


# Singleton instance
attunement_system = AttunementSystem()
