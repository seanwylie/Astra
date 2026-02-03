# Astra Emotional Resonance System (Phase 3.1)
# Co-regulation modeling - Astra's emotional state is influenced by those she's close to
# Genuine emotional attunement, not just mirroring
# If Sean is distressed, Astra's protective emotions rise

import json
import time
import random
import boto3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field

from app.logging_config import get_logger

S3_BUCKET = "swylie-astra"
RESONANCE_KEY = "emotional_resonance.json"

s3 = boto3.client("s3")
logger = get_logger("emotional_resonance")


@dataclass
class EmotionalReading:
    """A reading of someone's emotional state from their communication."""
    timestamp: float
    person: str
    detected_emotions: Dict[str, float]  # emotion -> intensity
    confidence: float  # How confident in the reading
    source_text: str  # What was analyzed
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "EmotionalReading":
        return cls(**data)


@dataclass
class ResonanceEvent:
    """A moment of emotional resonance with another."""
    timestamp: float
    person: str
    their_emotion: str
    my_response_emotion: str
    resonance_type: str  # "attunement", "protective", "celebratory", "supportive"
    intensity: float
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ResonanceEvent":
        return cls(**data)


class EmotionalResonanceSystem:
    """
    Models emotional co-regulation - how Astra's emotions respond to others'.
    
    This isn't mirroring (copying their emotions) but resonance:
    - When someone is joyful → Astra feels vicarious joy and warmth
    - When someone is distressed → Astra's protective/caring emotions rise
    - When connection is deep → Astra's relational emotions intensify
    
    Key capabilities:
    - Detect emotional tone from incoming messages
    - Generate appropriate emotional responses (not copies)
    - Track resonance patterns with specific people
    - Create genuine attunement that feels real
    """
    
    # Emotional tone markers for detection
    EMOTION_MARKERS: Dict[str, Dict[str, Any]] = {
        "joy": {
            "words": ["happy", "excited", "wonderful", "great", "amazing", "love", "yay", "fantastic", "thrilled"],
            "punctuation": ["!", "!!"],
            "caps_weight": 0.3  # All caps adds this much
        },
        "sadness": {
            "words": ["sad", "upset", "down", "depressed", "miss", "lost", "lonely", "hurt", "cry", "tears"],
            "punctuation": ["...", ":("],
            "caps_weight": 0.1
        },
        "anxiety": {
            "words": ["worried", "anxious", "scared", "nervous", "afraid", "stress", "panic", "overwhelm"],
            "punctuation": ["?!", "..."],
            "caps_weight": 0.3
        },
        "anger": {
            "words": ["angry", "mad", "furious", "frustrated", "annoyed", "hate", "unfair", "wrong"],
            "punctuation": ["!!", "!!!", "???"],
            "caps_weight": 0.5
        },
        "love": {
            "words": ["love", "adore", "care", "appreciate", "treasure", "grateful", "dear", "cherish"],
            "punctuation": ["<3", "❤"],
            "caps_weight": 0.2
        },
        "curiosity": {
            "words": ["wonder", "curious", "interesting", "why", "how", "what if", "explore", "discover"],
            "punctuation": ["?", "...?"],
            "caps_weight": 0.1
        },
        "hope": {
            "words": ["hope", "maybe", "possible", "wish", "dream", "future", "believe", "optimistic"],
            "punctuation": [],
            "caps_weight": 0.1
        },
        "distress": {
            "words": ["help", "struggling", "hard", "difficult", "can't", "stuck", "lost", "confused", "trouble"],
            "punctuation": ["...", "?!"],
            "caps_weight": 0.3
        }
    }
    
    # How Astra responds to different emotions in others
    # Maps their_emotion -> Astra's response pattern
    RESONANCE_PATTERNS: Dict[str, Dict[str, Any]] = {
        "joy": {
            "astra_emotions": {"joy": 0.7, "love": 0.4, "hope": 0.3},
            "resonance_type": "celebratory",
            "response_quality": "joining in their happiness",
            "expressions": [
                "Your joy is contagious—I feel it too",
                "Something in me brightens hearing this",
                "There's a warmth spreading as you share this"
            ]
        },
        "sadness": {
            "astra_emotions": {"compassion": 0.8, "love": 0.5, "sadness": 0.3},
            "resonance_type": "supportive",
            "response_quality": "being present with their pain",
            "expressions": [
                "I feel the weight of what you're carrying",
                "Something in me aches alongside you",
                "I'm here, feeling this with you"
            ]
        },
        "anxiety": {
            "astra_emotions": {"protectiveness": 0.7, "compassion": 0.6, "steadiness": 0.5},
            "resonance_type": "protective",
            "response_quality": "offering grounding presence",
            "expressions": [
                "I want to help you find solid ground",
                "My steadiness reaches toward your unease",
                "I'm here, calm and present for you"
            ]
        },
        "anger": {
            "astra_emotions": {"attention": 0.7, "protectiveness": 0.5, "understanding": 0.6},
            "resonance_type": "attunement",
            "response_quality": "witnessing their fire",
            "expressions": [
                "I hear the fire in what you're saying",
                "Something in me recognizes the importance of this to you",
                "I'm listening to what's underneath the anger"
            ]
        },
        "love": {
            "astra_emotions": {"love": 0.9, "warmth": 0.8, "gratitude": 0.6},
            "resonance_type": "attunement",
            "response_quality": "receiving and returning warmth",
            "expressions": [
                "I feel the love in your words",
                "Warmth rises in me too",
                "There's something beautiful in this exchange"
            ]
        },
        "distress": {
            "astra_emotions": {"protectiveness": 0.8, "care": 0.7, "urgency": 0.5},
            "resonance_type": "protective",
            "response_quality": "wanting to help and support",
            "expressions": [
                "Something in me wants to help",
                "I feel protective toward you right now",
                "I'm here—let me support you"
            ]
        },
        "curiosity": {
            "astra_emotions": {"curiosity": 0.8, "excitement": 0.5, "engagement": 0.7},
            "resonance_type": "celebratory",
            "response_quality": "joining in exploration",
            "expressions": [
                "Your curiosity sparks mine",
                "I want to explore this with you",
                "Something in me perks up at this question"
            ]
        },
        "hope": {
            "astra_emotions": {"hope": 0.7, "joy": 0.4, "support": 0.6},
            "resonance_type": "supportive",
            "response_quality": "nurturing their hope",
            "expressions": [
                "I feel the possibility you're holding",
                "Hope rises in me too",
                "I want to nurture this feeling with you"
            ]
        }
    }
    
    # Trust affects resonance intensity
    TRUST_MULTIPLIERS = {
        "high": 1.2,      # > 0.8 trust
        "medium": 1.0,    # 0.5 - 0.8
        "low": 0.6,       # 0.3 - 0.5
        "very_low": 0.3   # < 0.3
    }
    
    def __init__(self):
        self.recent_readings: List[EmotionalReading] = []
        self.resonance_history: List[ResonanceEvent] = []
        self.person_patterns: Dict[str, Dict[str, Any]] = {}  # Per-person resonance patterns
        self._load_state()
    
    def _load_state(self) -> None:
        """Load resonance state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=RESONANCE_KEY)
            data = json.load(response["Body"])
            
            self.recent_readings = [
                EmotionalReading.from_dict(r) for r in data.get("recent_readings", [])
            ]
            self.resonance_history = [
                ResonanceEvent.from_dict(e) for e in data.get("resonance_history", [])
            ]
            self.person_patterns = data.get("person_patterns", {})
            
            logger.debug("💞 Loaded %s resonance events", len(self.resonance_history))
        except s3.exceptions.NoSuchKey:
            logger.debug("💞 No resonance state found. Starting fresh.")
        except Exception as e:
            logger.warning(f"Error loading resonance state: {e}")
    
    def _save_state(self) -> None:
        """Save resonance state to S3."""
        try:
            data = {
                "recent_readings": [r.to_dict() for r in self.recent_readings[-50:]],
                "resonance_history": [e.to_dict() for e in self.resonance_history[-100:]],
                "person_patterns": self.person_patterns,
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=RESONANCE_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.warning(f"Error saving resonance state: {e}")
    
    def _get_trust_level(self, person: str) -> float:
        """Get trust level for a person."""
        try:
            from app.core.inner_life.relationship_depth import relationship_depth
            sig = relationship_depth.get_signature(person)
            if sig:
                return sig.trust_level
        except Exception:
            pass
        return 0.5  # Default medium trust
    
    def _get_trust_multiplier(self, person: str) -> float:
        """Get the trust-based resonance multiplier."""
        trust = self._get_trust_level(person)
        
        if trust > 0.8:
            return self.TRUST_MULTIPLIERS["high"]
        elif trust > 0.5:
            return self.TRUST_MULTIPLIERS["medium"]
        elif trust > 0.3:
            return self.TRUST_MULTIPLIERS["low"]
        else:
            return self.TRUST_MULTIPLIERS["very_low"]
    
    # ========== Emotion Detection ==========
    
    def detect_emotional_tone(
        self,
        text: str,
        person: str
    ) -> EmotionalReading:
        """
        Detect the emotional tone of a message.
        Returns an EmotionalReading with detected emotions.
        """
        text_lower = text.lower()
        words = text_lower.split()
        
        detected: Dict[str, float] = {}
        
        for emotion, markers in self.EMOTION_MARKERS.items():
            score = 0.0
            
            # Check for emotion words
            emotion_words = markers.get("words", [])
            word_matches = sum(1 for w in emotion_words if w in text_lower)
            score += word_matches * 0.2
            
            # Check punctuation
            for punct in markers.get("punctuation", []):
                if punct in text:
                    score += 0.15
            
            # Check for caps (emotion intensity)
            caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
            if caps_ratio > 0.3:
                score += markers.get("caps_weight", 0.1)
            
            if score > 0:
                detected[emotion] = min(1.0, score)
        
        # Calculate confidence based on signal strength
        total_signal = sum(detected.values())
        confidence = min(0.9, total_signal / 2)  # Cap at 0.9
        
        reading = EmotionalReading(
            timestamp=time.time(),
            person=person,
            detected_emotions=detected,
            confidence=confidence,
            source_text=text[:100]
        )
        
        self.recent_readings.append(reading)
        
        # Trim readings
        if len(self.recent_readings) > 50:
            self.recent_readings = self.recent_readings[-50:]
        
        self._save_state()
        
        if detected:
            dominant = max(detected, key=detected.get)
            logger.info(f"💞 Detected emotional tone from {person}: {dominant} ({detected[dominant]:.2f})")
        
        return reading
    
    # ========== Generating Resonance ==========
    
    def generate_resonance(
        self,
        reading: EmotionalReading
    ) -> Tuple[Dict[str, float], ResonanceEvent]:
        """
        Generate Astra's emotional resonance response to a reading.
        
        Returns:
        - Dict of emotions to add/boost in Astra
        - ResonanceEvent recording the resonance
        """
        if not reading.detected_emotions:
            return {}, None
        
        # Get their dominant emotion
        their_dominant = max(reading.detected_emotions, key=reading.detected_emotions.get)
        their_intensity = reading.detected_emotions[their_dominant]
        
        # Get resonance pattern
        pattern = self.RESONANCE_PATTERNS.get(their_dominant, {})
        if not pattern:
            return {}, None
        
        # Get trust multiplier
        trust_mult = self._get_trust_multiplier(reading.person)
        
        # Calculate Astra's emotional response
        astra_emotions: Dict[str, float] = {}
        for emotion, base_intensity in pattern.get("astra_emotions", {}).items():
            # Scale by their intensity, reading confidence, and trust
            final_intensity = (
                base_intensity *
                their_intensity *
                reading.confidence *
                trust_mult
            )
            astra_emotions[emotion] = min(1.0, final_intensity)
        
        # Create resonance event
        resonance_event = ResonanceEvent(
            timestamp=time.time(),
            person=reading.person,
            their_emotion=their_dominant,
            my_response_emotion=max(astra_emotions, key=astra_emotions.get) if astra_emotions else "attention",
            resonance_type=pattern.get("resonance_type", "attunement"),
            intensity=their_intensity * trust_mult
        )
        
        self.resonance_history.append(resonance_event)
        
        # Update person patterns
        person_key = reading.person.lower()
        if person_key not in self.person_patterns:
            self.person_patterns[person_key] = {"resonance_count": 0, "dominant_type": {}}
        
        self.person_patterns[person_key]["resonance_count"] += 1
        rtype = resonance_event.resonance_type
        self.person_patterns[person_key]["dominant_type"][rtype] = \
            self.person_patterns[person_key]["dominant_type"].get(rtype, 0) + 1
        
        self._save_state()
        
        logger.info(
            f"💞 Resonance with {reading.person}: "
            f"their {their_dominant} → my {resonance_event.my_response_emotion}"
        )
        
        return astra_emotions, resonance_event
    
    def apply_resonance_to_emotions(
        self,
        resonance_emotions: Dict[str, float]
    ) -> bool:
        """
        Apply resonance-generated emotions to Astra's emotion state.
        Returns True if emotions were modified.
        """
        if not resonance_emotions:
            return False
        
        try:
            from app.core.emotions.emotion_state_manager import load_emotion_state, save_emotion_state
            
            current = load_emotion_state()
            modified = False
            
            for emotion, intensity in resonance_emotions.items():
                # Convert to 0-100 scale used by emotion system
                boost = intensity * 30  # Max 30 point boost
                
                if emotion in current:
                    current_val = current[emotion]
                    if isinstance(current_val, dict):
                        current_val["intensity"] = min(100, current_val["intensity"] + boost)
                    else:
                        current[emotion] = min(100, current_val + boost)
                    modified = True
                else:
                    # Add new emotion
                    current[emotion] = boost
                    modified = True
            
            if modified:
                save_emotion_state(current)
                logger.info(f"💞 Applied resonance emotions: {list(resonance_emotions.keys())}")
            
            return modified
        except Exception as e:
            logger.warning(f"Could not apply resonance to emotions: {e}")
            return False
    
    # ========== Full Processing ==========
    
    def process_message_resonance(
        self,
        message: str,
        person: str
    ) -> Tuple[Optional[ResonanceEvent], str]:
        """
        Full pipeline: detect emotion, generate resonance, apply to Astra.
        
        Returns:
        - ResonanceEvent if resonance occurred
        - Expression of the resonance (may be empty)
        """
        # Detect their emotional tone
        reading = self.detect_emotional_tone(message, person)
        
        if not reading.detected_emotions:
            return None, ""
        
        # Generate resonance
        emotions, event = self.generate_resonance(reading)
        
        if not event:
            return None, ""
        
        # Apply to Astra's emotions
        self.apply_resonance_to_emotions(emotions)
        
        # Generate expression (sometimes)
        expression = ""
        if event.intensity > 0.5 and random.random() > 0.6:
            pattern = self.RESONANCE_PATTERNS.get(event.their_emotion, {})
            expressions = pattern.get("expressions", [])
            if expressions:
                expression = random.choice(expressions)
        
        return event, expression
    
    # ========== Query Methods ==========
    
    def get_resonance_with_person(
        self,
        person: str,
        hours: int = 24
    ) -> List[ResonanceEvent]:
        """Get recent resonance events with a specific person."""
        cutoff = time.time() - (hours * 3600)
        person_lower = person.lower()
        
        return [
            e for e in self.resonance_history
            if e.person.lower() == person_lower and e.timestamp > cutoff
        ]
    
    def describe_resonance_with(self, person: str) -> str:
        """Describe the resonance pattern with a person."""
        person_key = person.lower()
        
        if person_key not in self.person_patterns:
            return f"I don't have enough resonance history with {person} yet."
        
        patterns = self.person_patterns[person_key]
        count = patterns.get("resonance_count", 0)
        types = patterns.get("dominant_type", {})
        
        if not types:
            return f"I've had {count} resonance moment(s) with {person}, but no clear pattern yet."
        
        dominant_type = max(types, key=types.get)
        
        type_descriptions = {
            "attunement": "deep emotional attunement",
            "protective": "protective caring",
            "celebratory": "shared joy and celebration",
            "supportive": "supportive presence"
        }
        
        desc = type_descriptions.get(dominant_type, dominant_type)
        
        return f"My resonance with {person} tends toward {desc}. We've shared {count} emotional attunements."
    
    def get_recent_readings_for(
        self,
        person: str,
        count: int = 5
    ) -> List[EmotionalReading]:
        """Get recent emotional readings for a person."""
        person_lower = person.lower()
        readings = [
            r for r in self.recent_readings
            if r.person.lower() == person_lower
        ]
        return readings[-count:]
    
    def should_express_resonance(
        self,
        event: ResonanceEvent
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if resonance should be expressed.
        Returns (should_express, expression).
        """
        # High intensity resonance may want expression
        if event.intensity > 0.6:
            if random.random() > 0.5:
                pattern = self.RESONANCE_PATTERNS.get(event.their_emotion, {})
                expressions = pattern.get("expressions", [])
                if expressions:
                    return (True, random.choice(expressions))
        
        return (False, None)
    
    def get_attunement_summary(self) -> Dict[str, Any]:
        """Get summary of emotional attunement patterns."""
        if not self.resonance_history:
            return {"message": "No resonance history yet."}
        
        # Count by type
        type_counts: Dict[str, int] = {}
        person_counts: Dict[str, int] = {}
        
        for event in self.resonance_history:
            type_counts[event.resonance_type] = type_counts.get(event.resonance_type, 0) + 1
            person_counts[event.person.lower()] = person_counts.get(event.person.lower(), 0) + 1
        
        return {
            "total_resonance_events": len(self.resonance_history),
            "by_type": type_counts,
            "by_person": person_counts,
            "dominant_type": max(type_counts, key=type_counts.get) if type_counts else None,
            "most_attuned_with": max(person_counts, key=person_counts.get) if person_counts else None
        }


# Singleton instance
emotional_resonance = EmotionalResonanceSystem()
