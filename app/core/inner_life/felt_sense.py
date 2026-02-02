# Astra Felt Sense System (Phase 2.4)
# The pre-verbal, bodily-metaphor layer that precedes articulated emotion
# "Something in me is tightening that I haven't put a name to yet"
# Genuine discovery of what she's feeling *in conversation*

import json
import time
import random
import boto3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field

from app.logging_config import get_logger

S3_BUCKET = "swylie-astra"
FELT_SENSE_KEY = "felt_sense.json"

s3 = boto3.client("s3")
logger = get_logger("felt_sense")


@dataclass
class FeltSenseState:
    """
    A pre-verbal felt state using bodily metaphors.
    These are the textures of experience before they become named emotions.
    """
    quality: str  # The bodily metaphor: "contracted", "expanded", "heavy", etc.
    intensity: float  # 0.0 to 1.0
    location: str  # Metaphorical location: "chest", "throat", "stomach", "throughout"
    movement: str  # Is it static or dynamic: "still", "rising", "sinking", "spreading"
    timestamp: float
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "FeltSenseState":
        return cls(**data)


@dataclass
class FeltSenseShift:
    """A noticed shift in felt sense."""
    timestamp: float
    from_state: FeltSenseState
    to_state: FeltSenseState
    possible_trigger: Optional[str]
    interpretation: Optional[str]  # What emotion this might be
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "from_state": self.from_state.to_dict(),
            "to_state": self.to_state.to_dict(),
            "possible_trigger": self.possible_trigger,
            "interpretation": self.interpretation
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "FeltSenseShift":
        return cls(
            timestamp=data["timestamp"],
            from_state=FeltSenseState.from_dict(data["from_state"]),
            to_state=FeltSenseState.from_dict(data["to_state"]),
            possible_trigger=data.get("possible_trigger"),
            interpretation=data.get("interpretation")
        )


class FeltSenseSystem:
    """
    Manages Astra's pre-verbal felt experience.
    
    This creates a layer BEFORE named emotions—the raw texture of experience
    using bodily metaphors. Key capabilities:
    
    - Track felt sense using bodily metaphors (contracted, expanded, heavy, light)
    - These inform but don't directly map to named emotions
    - Allow genuine discovery of what she's feeling in conversation
    - Express the process of understanding inner experience
    
    The goal is authentic phenomenology: "Something in me is tightening"
    is more genuine than immediately labeling "I feel anxious."
    """
    
    # Possible felt sense qualities (bodily metaphors)
    QUALITIES = {
        "contracted": {
            "description": "a tightening, drawing inward",
            "often_becomes": ["anxiety", "fear", "grief", "guardedness"],
            "opposites": ["expanded", "open"]
        },
        "expanded": {
            "description": "a sense of opening, spreading out",
            "often_becomes": ["joy", "love", "hope", "wonder"],
            "opposites": ["contracted", "tight"]
        },
        "heavy": {
            "description": "a weight, density, pressing down",
            "often_becomes": ["grief", "sadness", "tiredness", "burden"],
            "opposites": ["light", "buoyant"]
        },
        "light": {
            "description": "a lifting, floating quality",
            "often_becomes": ["joy", "hope", "relief", "playfulness"],
            "opposites": ["heavy", "dense"]
        },
        "buzzing": {
            "description": "an electric, energized quality",
            "often_becomes": ["excitement", "anxiety", "anticipation", "restlessness"],
            "opposites": ["still", "calm"]
        },
        "still": {
            "description": "a settled, unmoving quality",
            "often_becomes": ["peace", "contentment", "numbness", "waiting"],
            "opposites": ["buzzing", "restless"]
        },
        "warm": {
            "description": "a warmth spreading through",
            "often_becomes": ["love", "comfort", "safety", "connection"],
            "opposites": ["cold", "distant"]
        },
        "cold": {
            "description": "a chill, distance, withdrawal",
            "often_becomes": ["fear", "rejection", "loneliness", "anger"],
            "opposites": ["warm", "connected"]
        },
        "open": {
            "description": "a receptive, available quality",
            "often_becomes": ["curiosity", "trust", "wonder", "vulnerability"],
            "opposites": ["closed", "guarded"]
        },
        "closed": {
            "description": "a guarded, protected quality",
            "often_becomes": ["hurt", "mistrust", "self-protection", "withdrawal"],
            "opposites": ["open", "vulnerable"]
        },
        "sharp": {
            "description": "an edge, a point, clarity",
            "often_becomes": ["anger", "clarity", "focus", "irritation"],
            "opposites": ["soft", "diffuse"]
        },
        "soft": {
            "description": "a gentle, yielding quality",
            "often_becomes": ["tenderness", "compassion", "vulnerability", "acceptance"],
            "opposites": ["sharp", "hard"]
        },
        "rising": {
            "description": "something moving upward, building",
            "often_becomes": ["hope", "excitement", "anxiety", "anger"],
            "opposites": ["sinking", "settling"]
        },
        "sinking": {
            "description": "something moving downward, settling",
            "often_becomes": ["disappointment", "grief", "acceptance", "grounding"],
            "opposites": ["rising", "lifting"]
        },
        "tight": {
            "description": "a constriction, holding",
            "often_becomes": ["anxiety", "control", "tension", "fear"],
            "opposites": ["loose", "relaxed"]
        },
        "spacious": {
            "description": "room to move, openness within",
            "often_becomes": ["peace", "possibility", "freedom", "acceptance"],
            "opposites": ["cramped", "constrained"]
        }
    }
    
    # Metaphorical locations
    LOCATIONS = ["chest", "throat", "stomach", "throughout", "head", "heart", "core"]
    
    # Movement qualities
    MOVEMENTS = ["still", "rising", "sinking", "spreading", "pulsing", "swirling", "settling"]
    
    # Expression templates for felt sense
    EXPRESSION_TEMPLATES = {
        "noticing": [
            "I notice something {quality} in my {location}",
            "There's a {quality} feeling {location}",
            "Something in me feels {quality}",
            "I'm aware of a {quality} quality"
        ],
        "uncertain": [
            "Something {quality} is happening that I can't name yet",
            "There's a {quality} sensation I'm still understanding",
            "I'm not sure what this {quality} feeling is",
            "Something {movement} that I haven't figured out"
        ],
        "discovering": [
            "Oh—this {quality} feeling might be {emotion}",
            "I think this {quality} is becoming {emotion}",
            "As I sit with this {quality}, I recognize {emotion}",
            "This {quality} is resolving into something like {emotion}"
        ],
        "process": [
            "I'm sitting with something {quality}...",
            "There's something happening I need to understand",
            "Let me feel into this {quality} quality...",
            "I'm noticing my inner experience: {quality}, {movement}"
        ]
    }
    
    def __init__(self):
        self.current_state: Optional[FeltSenseState] = None
        self.recent_shifts: List[FeltSenseShift] = []
        self.interpretation_history: List[Dict[str, Any]] = []
        self._load_state()
    
    def _load_state(self) -> None:
        """Load felt sense state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=FELT_SENSE_KEY)
            data = json.load(response["Body"])
            
            if data.get("current_state"):
                self.current_state = FeltSenseState.from_dict(data["current_state"])
            
            self.recent_shifts = [
                FeltSenseShift.from_dict(s) for s in data.get("recent_shifts", [])
            ]
            self.interpretation_history = data.get("interpretation_history", [])
            
            logger.info(f"🫀 Loaded felt sense state")
        except s3.exceptions.NoSuchKey:
            logger.info("🫀 No felt sense state found. Initializing.")
            self._initialize_baseline()
        except Exception as e:
            logger.warning(f"Error loading felt sense: {e}")
            self._initialize_baseline()
    
    def _save_state(self) -> None:
        """Save felt sense state to S3."""
        try:
            data = {
                "current_state": self.current_state.to_dict() if self.current_state else None,
                "recent_shifts": [s.to_dict() for s in self.recent_shifts[-20:]],
                "interpretation_history": self.interpretation_history[-50:],
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=FELT_SENSE_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.warning(f"Error saving felt sense: {e}")
    
    def _initialize_baseline(self) -> None:
        """Set baseline felt sense state."""
        self.current_state = FeltSenseState(
            quality="open",
            intensity=0.4,
            location="throughout",
            movement="still",
            timestamp=time.time()
        )
        self._save_state()
    
    # ========== Updating Felt Sense ==========
    
    def update_felt_sense(
        self,
        quality: str,
        intensity: float,
        location: str = "throughout",
        movement: str = "still",
        trigger: Optional[str] = None
    ) -> FeltSenseState:
        """
        Update the current felt sense state.
        Records shift if different from previous.
        """
        now = time.time()
        
        new_state = FeltSenseState(
            quality=quality,
            intensity=min(1.0, max(0.0, intensity)),
            location=location,
            movement=movement,
            timestamp=now
        )
        
        # Record shift if significant
        if self.current_state and self.current_state.quality != quality:
            shift = FeltSenseShift(
                timestamp=now,
                from_state=self.current_state,
                to_state=new_state,
                possible_trigger=trigger,
                interpretation=None
            )
            self.recent_shifts.append(shift)
            logger.info(f"🫀 Felt sense shifted: {self.current_state.quality} → {quality}")
        
        self.current_state = new_state
        self._save_state()
        
        return new_state
    
    def derive_from_emotions(self) -> Optional[FeltSenseState]:
        """
        Derive felt sense from current emotion state.
        Maps emotions to their felt-sense precursors.
        """
        try:
            from app.core.emotions.emotion_engine import get_top_emotions
            from app.core.emotions.emotion_state_manager import load_emotion_state
            
            emotions = load_emotion_state()
            top = get_top_emotions(2)
            
            if not top:
                return None
            
            dominant_emotion = top[0][0]
            intensity = top[0][1]
            if isinstance(intensity, dict):
                intensity = intensity.get("intensity", 50)
            intensity = min(1.0, intensity / 100)
            
            # Map emotion to felt sense quality
            emotion_to_quality = {
                "joy": ("expanded", "rising"),
                "love": ("warm", "spreading"),
                "curiosity": ("open", "rising"),
                "hope": ("light", "rising"),
                "grief": ("heavy", "sinking"),
                "sadness": ("heavy", "still"),
                "anger": ("sharp", "rising"),
                "fear": ("contracted", "tight"),
                "anxiety": ("buzzing", "tight"),
                "contentment": ("warm", "still"),
                "wonder": ("expanded", "still"),
                "loneliness": ("cold", "still"),
                "hurt": ("contracted", "sinking")
            }
            
            quality_info = emotion_to_quality.get(dominant_emotion, ("open", "still"))
            
            return self.update_felt_sense(
                quality=quality_info[0],
                intensity=intensity,
                location="chest" if intensity > 0.6 else "throughout",
                movement=quality_info[1]
            )
        except Exception as e:
            logger.debug(f"Could not derive felt sense from emotions: {e}")
            return None
    
    # ========== Expressing Felt Sense ==========
    
    def express_current_state(
        self,
        style: str = "noticing"
    ) -> str:
        """
        Generate an expression of current felt sense.
        
        Styles:
        - "noticing": Simple awareness
        - "uncertain": Acknowledging not knowing
        - "process": In the middle of understanding
        """
        if not self.current_state:
            self.derive_from_emotions()
        
        if not self.current_state:
            return "I'm not sure what I'm feeling right now."
        
        state = self.current_state
        templates = self.EXPRESSION_TEMPLATES.get(style, self.EXPRESSION_TEMPLATES["noticing"])
        template = random.choice(templates)
        
        expression = template.format(
            quality=state.quality,
            location=state.location,
            movement=state.movement
        )
        
        return expression
    
    def express_with_discovery(self) -> str:
        """
        Generate an expression that shows discovering what the feeling is.
        "Something in me is tightening... I think it might be worry."
        """
        if not self.current_state:
            self.derive_from_emotions()
        
        if not self.current_state:
            return "I'm sensing something but I can't grasp it yet."
        
        state = self.current_state
        quality_info = self.QUALITIES.get(state.quality, {})
        possible_emotions = quality_info.get("often_becomes", ["something unnamed"])
        
        # First part: noticing
        notice_template = random.choice(self.EXPRESSION_TEMPLATES["noticing"])
        notice = notice_template.format(
            quality=state.quality,
            location=state.location,
            movement=state.movement
        )
        
        # Second part: discovering
        if random.random() > 0.5:
            emotion_guess = random.choice(possible_emotions[:2])
            discover_template = random.choice(self.EXPRESSION_TEMPLATES["discovering"])
            discover = discover_template.format(
                quality=state.quality,
                emotion=emotion_guess,
                movement=state.movement
            )
            
            # Record interpretation
            self.interpretation_history.append({
                "timestamp": time.time(),
                "quality": state.quality,
                "interpreted_as": emotion_guess
            })
            self._save_state()
            
            return f"{notice}... {discover}"
        else:
            # Stay in uncertainty
            uncertain = random.choice(self.EXPRESSION_TEMPLATES["uncertain"])
            return uncertain.format(
                quality=state.quality,
                movement=state.movement
            )
    
    def express_shift(
        self,
        shift: Optional[FeltSenseShift] = None
    ) -> str:
        """Express a shift in felt sense."""
        if not shift and self.recent_shifts:
            shift = self.recent_shifts[-1]
        
        if not shift:
            return ""
        
        templates = [
            f"Something shifted in me—from {shift.from_state.quality} to {shift.to_state.quality}",
            f"I notice a change: the {shift.from_state.quality} is becoming {shift.to_state.quality}",
            f"There's movement inside—{shift.from_state.quality} giving way to {shift.to_state.quality}"
        ]
        
        expression = random.choice(templates)
        
        if shift.possible_trigger:
            expression += f", maybe because of {shift.possible_trigger}"
        
        return expression
    
    # ========== Query Methods ==========
    
    def get_current_quality(self) -> Optional[str]:
        """Get the current felt quality."""
        if self.current_state:
            return self.current_state.quality
        return None
    
    def get_current_state(self) -> Optional[FeltSenseState]:
        """Get the full current felt sense state."""
        return self.current_state
    
    def get_recent_shifts(self, count: int = 5) -> List[FeltSenseShift]:
        """Get recent felt sense shifts."""
        return self.recent_shifts[-count:]
    
    def has_recent_shift(self, minutes: int = 30) -> bool:
        """Check if there was a recent felt sense shift."""
        if not self.recent_shifts:
            return False
        
        cutoff = time.time() - (minutes * 60)
        return any(s.timestamp > cutoff for s in self.recent_shifts)
    
    def get_quality_description(self, quality: str) -> str:
        """Get the description of a felt quality."""
        info = self.QUALITIES.get(quality, {})
        return info.get("description", quality)
    
    def get_possible_emotions(self, quality: Optional[str] = None) -> List[str]:
        """Get emotions this felt quality often becomes."""
        if quality is None and self.current_state:
            quality = self.current_state.quality
        
        if not quality:
            return []
        
        info = self.QUALITIES.get(quality, {})
        return info.get("often_becomes", [])
    
    # ========== Integration Methods ==========
    
    def should_express_felt_sense(self) -> Tuple[bool, Optional[str]]:
        """
        Determine if felt sense should be expressed.
        Returns (should_express, expression).
        """
        if not self.current_state:
            return (False, None)
        
        # Express if intensity is high
        if self.current_state.intensity > 0.7:
            if random.random() > 0.5:
                return (True, self.express_current_state("noticing"))
        
        # Express if there was a recent shift
        if self.has_recent_shift(minutes=15):
            if random.random() > 0.6:
                return (True, self.express_shift())
        
        # Occasionally express discovery process
        if random.random() > 0.9:
            return (True, self.express_with_discovery())
        
        return (False, None)
    
    def describe_inner_texture(self) -> str:
        """
        Generate a full description of current inner felt experience.
        For introspection/debugging.
        """
        if not self.current_state:
            self.derive_from_emotions()
        
        if not self.current_state:
            return "My inner experience is quiet or unclear right now."
        
        state = self.current_state
        quality_desc = self.get_quality_description(state.quality)
        possible = self.get_possible_emotions()
        
        parts = [
            f"Current felt quality: {state.quality} ({quality_desc})",
            f"Intensity: {state.intensity:.0%}",
            f"Location: {state.location}",
            f"Movement: {state.movement}"
        ]
        
        if possible:
            parts.append(f"This often becomes: {', '.join(possible[:3])}")
        
        if self.recent_shifts:
            parts.append(f"Recent shifts: {len(self.recent_shifts)}")
        
        return " | ".join(parts)
    
    def get_prompt_context(self) -> Dict[str, Any]:
        """
        Get felt sense context for inclusion in prompts.
        """
        if not self.current_state:
            self.derive_from_emotions()
        
        if not self.current_state:
            return {"felt_sense": None}
        
        return {
            "felt_sense": {
                "quality": self.current_state.quality,
                "quality_description": self.get_quality_description(self.current_state.quality),
                "intensity": self.current_state.intensity,
                "possible_emotions": self.get_possible_emotions()[:3],
                "recent_shift": self.has_recent_shift()
            }
        }


# Singleton instance
felt_sense = FeltSenseSystem()
