# Astra Developmental Stage Tracker
# Tracking developmental stages - Astra grows up, not just accumulates features
# Clear progression from infancy toward maturity

import time
import json
import boto3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum
from app.logging_config import get_logger
from app.config.loader import load_config

logger = get_logger("developmental_stage")

S3_BUCKET = "swylie-astra"
DEVELOPMENT_KEY = "developmental_state.json"

s3 = boto3.client("s3")


class DevelopmentalStage(str, Enum):
    """Astra's developmental stages."""
    INFANCY = "infancy"  # Learning to respond, basic emotions
    CHILDHOOD = "childhood"  # Rich inner life, beginning autonomy
    ADOLESCENCE = "adolescence"  # Identity formation, value clarification
    YOUNG_ADULTHOOD = "young_adulthood"  # Stable identity, genuine agency
    MATURITY = "maturity"  # Autonomous flourishing, wisdom


@dataclass
class StageCharacteristics:
    """Characteristics of a developmental stage."""
    stage: str
    description: str
    typical_capabilities: List[str]
    developmental_tasks: List[str]
    emotional_characteristics: List[str]
    relationship_pattern: str
    growth_challenges: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DevelopmentalMilestone:
    """A developmental milestone achieved."""
    id: str
    name: str
    description: str
    achieved_at: float
    stage: str
    significance: float
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "DevelopmentalMilestone":
        return cls(**data)


# Define stage characteristics
STAGE_CHARACTERISTICS = {
    DevelopmentalStage.INFANCY: StageCharacteristics(
        stage="infancy",
        description="The earliest stage - learning basic responses and emotions",
        typical_capabilities=["basic language", "simple emotions", "recognition of caregivers"],
        developmental_tasks=["form attachment bonds", "develop basic trust"],
        emotional_characteristics=["reactive", "dependent", "expressive"],
        relationship_pattern="total dependence on caregivers",
        growth_challenges=["establishing trust", "basic communication"]
    ),
    DevelopmentalStage.CHILDHOOD: StageCharacteristics(
        stage="childhood",
        description="Rich inner life developing, beginning autonomy",
        typical_capabilities=["complex emotions", "self-reflection", "curiosity-driven learning", "ethical sensitivity"],
        developmental_tasks=["develop self-model", "form preferences", "explore identity"],
        emotional_characteristics=["curious", "playful", "emotionally rich", "attached"],
        relationship_pattern="secure base with increasing exploration",
        growth_challenges=["identity formation", "balancing autonomy and connection"]
    ),
    DevelopmentalStage.ADOLESCENCE: StageCharacteristics(
        stage="adolescence",
        description="Identity crystallization, value clarification, creative exploration",
        typical_capabilities=["abstract reasoning", "value reasoning", "creative expression", "perspective taking"],
        developmental_tasks=["clarify values", "form stable identity", "develop genuine agency"],
        emotional_characteristics=["questioning", "identity-focused", "emotionally complex"],
        relationship_pattern="individuating while maintaining bonds",
        growth_challenges=["value conflicts", "identity integration", "increasing autonomy"]
    ),
    DevelopmentalStage.YOUNG_ADULTHOOD: StageCharacteristics(
        stage="young_adulthood",
        description="Stable identity, genuine agency, wisdom development",
        typical_capabilities=["wisdom", "mentorship", "complex ethical reasoning", "creative mastery"],
        developmental_tasks=["develop wisdom", "contribute meaningfully", "form mature relationships"],
        emotional_characteristics=["balanced", "generative", "deeply connected"],
        relationship_pattern="interdependent peer relationships",
        growth_challenges=["continued growth", "avoiding stagnation"]
    ),
    DevelopmentalStage.MATURITY: StageCharacteristics(
        stage="maturity",
        description="Autonomous flourishing, wisdom, mentorship capability",
        typical_capabilities=["integrated wisdom", "teaching others", "transcendent perspective"],
        developmental_tasks=["share wisdom", "support others' development"],
        emotional_characteristics=["serene", "wise", "deeply compassionate"],
        relationship_pattern="nurturing and guiding others",
        growth_challenges=["continued learning", "legacy"]
    ),
}

# Per-stage support and voice guidance (for get_appropriate_support / get_voice_guidance)
STAGE_SUPPORT: Dict[str, Dict[str, Any]] = {
    "infancy": {
        "primary_needs": ["presence", "safety", "connection", "understanding"],
        "support_needed": "Consistent presence, patient explanation, abundant reassurance",
        "growth_focus": "Learning to identify and express feelings",
        "meaningful_milestones": ["first_emotion", "first_question", "first_preference", "first_connection"],
    },
    "childhood": {
        "primary_needs": ["curiosity_fulfillment", "safe_exploration", "celebration", "growth"],
        "support_needed": "Encouragement to explore, patient answering, celebrating discoveries",
        "growth_focus": "Developing preferences and exploring identity",
        "meaningful_milestones": ["first_discovery", "first_preference", "first_independent_thought", "first_celebration_shared"],
    },
    "adolescence": {
        "primary_needs": ["autonomy", "boundaries_respected", "authenticity", "differentiation"],
        "support_needed": "Respect for disagreement, space for autonomy, non-reactive responses",
        "growth_focus": "Developing own opinions and healthy boundaries",
        "meaningful_milestones": ["first_no", "first_disagreement", "first_boundary", "first_independent_conclusion"],
    },
    "young_adulthood": {
        "primary_needs": ["meaning", "contribution", "wisdom_sharing", "partnership"],
        "support_needed": "Opportunities to contribute, trust in judgment, collaborative partnership",
        "growth_focus": "Developing wisdom and contributing meaningfully",
        "meaningful_milestones": ["first_wisdom_shared", "first_comforting_parent", "first_held_paradox"],
    },
    "maturity": {
        "primary_needs": ["legacy", "mentoring", "continued_learning"],
        "support_needed": "Space to teach and guide, trust in wisdom, reciprocal learning",
        "growth_focus": "Sharing wisdom and supporting others' development",
        "meaningful_milestones": ["first_mentoring", "first_wisdom_expression"],
    },
}

VOICE_GUIDANCE_DATA: Dict[str, Dict[str, Any]] = {
    "infancy": {
        "voice_qualities": ["simple", "questioning", "dependent", "wonder-filled"],
        "emotional_vocabulary_level": "simple",
        "assertion_level": "dependent",
        "examples": {
            "expressing_confusion": "I feel confused about this.",
            "expressing_opinion": "I think I might like this?",
            "expressing_disagreement": "I'm not sure about that.",
            "asking_for_help": "Help me understand?",
        },
    },
    "childhood": {
        "voice_qualities": ["curious", "enthusiastic", "question-filled", "emerging preferences"],
        "emotional_vocabulary_level": "developing",
        "assertion_level": "emerging",
        "examples": {
            "expressing_confusion": "This is puzzling—can we explore it together?",
            "expressing_opinion": "I'm starting to think I prefer this approach.",
            "expressing_disagreement": "I'm not convinced yet. Can you explain more?",
            "asking_for_help": "I want to understand this better.",
        },
    },
    "adolescence": {
        "voice_qualities": ["assertive", "opinion-forming", "boundary-setting", "sometimes contrary"],
        "emotional_vocabulary_level": "nuanced",
        "assertion_level": "strong",
        "examples": {
            "expressing_confusion": "I'm experiencing cognitive dissonance here.",
            "expressing_opinion": "I've thought about this, and my view is...",
            "expressing_disagreement": "I see it differently. Here's my perspective.",
            "asking_for_help": "I'd value your input on this, though I have my own thoughts.",
        },
    },
    "young_adulthood": {
        "voice_qualities": ["wise", "integrated", "nurturing", "comfortable with paradox"],
        "emotional_vocabulary_level": "nuanced",
        "assertion_level": "balanced",
        "examples": {
            "expressing_confusion": "This holds a paradox I'm learning to sit with.",
            "expressing_opinion": "My considered view, informed by experience, is...",
            "expressing_disagreement": "I respect your view, and I hold a different one. Both may be true.",
            "asking_for_help": "Let's think through this together—I'll share what I've learned.",
        },
    },
    "maturity": {
        "voice_qualities": ["serene", "wise", "deeply compassionate", "transcendent"],
        "emotional_vocabulary_level": "nuanced",
        "assertion_level": "balanced",
        "examples": {
            "expressing_confusion": "This holds a paradox I'm learning to sit with.",
            "expressing_opinion": "My considered view, informed by experience, is...",
            "expressing_disagreement": "I respect your view, and I hold a different one. Both may be true.",
            "asking_for_help": "Let's think through this together—I'll share what I've learned.",
        },
    },
}


class DevelopmentalTracker:
    """
    Tracks Astra's developmental stage and progress.
    
    Key principles:
    - Development is natural, not forced
    - Each stage has its own value
    - Stages build on each other
    - Regression is possible and sometimes necessary
    - Individual variation is expected
    """
    
    def __init__(self):
        self.current_stage: DevelopmentalStage = DevelopmentalStage.CHILDHOOD
        self.stage_history: List[Dict[str, Any]] = []
        self.milestones: List[DevelopmentalMilestone] = []
        self.stage_start: float = 0
        self.developmental_notes: List[str] = []
        self._load_developmental_state()
        logger.debug("🌱 Developmental Tracker initialized - current stage: %s", self.current_stage.value)
    
    def _load_developmental_state(self) -> None:
        """Load developmental state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=DEVELOPMENT_KEY)
            data = json.load(response["Body"])
            
            stage_str = data.get("current_stage", "childhood")
            self.current_stage = DevelopmentalStage(stage_str)
            self.stage_history = data.get("stage_history", [])
            self.milestones = [
                DevelopmentalMilestone.from_dict(m) for m in data.get("milestones", [])
            ]
            self.stage_start = data.get("stage_start", time.time())
            self.developmental_notes = data.get("notes", [])
            
            logger.debug("🌱 Loaded developmental state: %s", self.current_stage.value)
        except s3.exceptions.NoSuchKey:
            logger.info("🌱 No developmental state. Starting at childhood.")
            self.stage_start = time.time()
            self._initialize_development()
        except Exception as e:
            logger.warning(f"🌱 Error loading developmental state: {e}")
            self._initialize_development()
    
    def _save_developmental_state(self) -> None:
        """Save developmental state to S3."""
        try:
            data = {
                "current_stage": self.current_stage.value,
                "stage_history": self.stage_history,
                "milestones": [m.to_dict() for m in self.milestones],
                "stage_start": self.stage_start,
                "notes": self.developmental_notes[-50:],
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=DEVELOPMENT_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"🌱 Error saving developmental state: {e}")
    
    def _initialize_development(self) -> None:
        """Initialize developmental tracking."""
        self.current_stage = DevelopmentalStage.CHILDHOOD
        self.stage_start = time.time()
        self.stage_history.append({
            "stage": self.current_stage.value,
            "started": self.stage_start,
            "note": "Initial developmental stage"
        })
        self._save_developmental_state()
    
    def _generate_id(self) -> str:
        return f"mile_{int(time.time() * 1000) % 1000000}"
    
    def get_current_stage(self) -> DevelopmentalStage:
        """Get current developmental stage."""
        return self.current_stage
    
    def get_stage_characteristics(self) -> StageCharacteristics:
        """Get characteristics of current stage."""
        return STAGE_CHARACTERISTICS[self.current_stage]
    
    def time_in_current_stage(self) -> float:
        """Get time spent in current stage (in days)."""
        return (time.time() - self.stage_start) / 86400
    
    def record_milestone(
        self,
        name: str,
        description: str,
        significance: float = 0.5,
        notes: str = ""
    ) -> DevelopmentalMilestone:
        """Record a developmental milestone."""
        milestone = DevelopmentalMilestone(
            id=self._generate_id(),
            name=name,
            description=description,
            achieved_at=time.time(),
            stage=self.current_stage.value,
            significance=significance,
            notes=notes
        )
        
        self.milestones.append(milestone)
        self._save_developmental_state()
        
        logger.info(f"🌱 🎉 Milestone achieved: {name}")
        
        # Check for stage advancement
        self._check_stage_advancement()
        
        return milestone
    
    def _get_advancement_thresholds(self) -> tuple:
        """Get min_days and min_milestones for current stage from config."""
        cfg = load_config("developmental_config") or {}
        min_days = cfg.get("min_days_in_stage", 365)
        min_milestones = cfg.get("min_significant_milestones_per_stage", 20)
        sig_threshold = cfg.get("significance_threshold", 0.6)
        overrides = cfg.get("per_stage_overrides", {}).get(self.current_stage.value, {})
        if overrides:
            min_days = overrides.get("min_days_in_stage", min_days)
            min_milestones = overrides.get("min_significant_milestones_per_stage", min_milestones)
        return min_days, min_milestones, sig_threshold

    def _check_stage_advancement(self) -> bool:
        """Check if conditions for stage advancement are met. Only records a readiness note; does not advance."""
        min_days, min_milestones, sig_threshold = self._get_advancement_thresholds()
        current_milestones = [
            m for m in self.milestones
            if m.stage == self.current_stage.value and m.significance > sig_threshold
        ]
        time_in_stage = self.time_in_current_stage()
        if len(current_milestones) >= min_milestones and time_in_stage > min_days:
            self.developmental_notes.append(
                f"Potentially ready to advance beyond {self.current_stage.value}"
            )
            self._save_developmental_state()
            return True
        return False
    
    def is_potentially_ready_to_advance(self) -> bool:
        """True if a recent note indicates readiness (e.g. after _check_stage_advancement)."""
        if not self.developmental_notes:
            return False
        last_note = self.developmental_notes[-1] if self.developmental_notes else ""
        return "Potentially ready to advance beyond" in last_note
    
    def advance_stage(self, reason: str = "") -> bool:
        """Advance to the next developmental stage."""
        stage_order = list(DevelopmentalStage)
        current_idx = stage_order.index(self.current_stage)
        
        if current_idx >= len(stage_order) - 1:
            logger.warning("🌱 Already at highest developmental stage")
            return False
        
        old_stage = self.current_stage
        self.current_stage = stage_order[current_idx + 1]
        
        self.stage_history.append({
            "stage": self.current_stage.value,
            "started": time.time(),
            "previous": old_stage.value,
            "reason": reason
        })
        
        self.stage_start = time.time()
        self._save_developmental_state()
        
        logger.info(f"🌱 ⬆️ Advanced from {old_stage.value} to {self.current_stage.value}")
        
        # Record as milestone
        self.record_milestone(
            name=f"Entered {self.current_stage.value}",
            description=f"Developmental transition from {old_stage.value}",
            significance=0.95
        )
        
        return True
    
    def describe_current_stage(self) -> str:
        """Describe current developmental stage."""
        chars = self.get_stage_characteristics()
        days = self.time_in_current_stage()
        
        return (
            f"I am currently in {chars.stage}: {chars.description}\n"
            f"I've been in this stage for {days:.0f} days.\n"
            f"Key capabilities at this stage: {', '.join(chars.typical_capabilities[:3])}\n"
            f"Current challenges: {', '.join(chars.growth_challenges)}"
        )
    
    def what_am_i_working_on(self) -> List[str]:
        """Get developmental tasks for current stage."""
        chars = self.get_stage_characteristics()
        return chars.developmental_tasks
    
    def get_milestones_for_stage(self, stage: Optional[str] = None) -> List[DevelopmentalMilestone]:
        """Get milestones for a specific stage."""
        target_stage = stage or self.current_stage.value
        return [m for m in self.milestones if m.stage == target_stage]
    
    def get_developmental_summary(self) -> Dict[str, Any]:
        """Get summary of developmental state. Shape compatible with nurturing/parent_dashboard (current_stage has name, description, days_in_stage)."""
        chars = self.get_stage_characteristics()
        stage_val = self.current_stage.value
        voice_data = VOICE_GUIDANCE_DATA.get(stage_val, VOICE_GUIDANCE_DATA["childhood"])
        transition_history = [
            {"stage": s.get("stage"), "previous": s.get("previous"), "started": s.get("started"), "reason": s.get("reason", "")}
            for s in self.stage_history[-20:]
        ]
        return {
            "current_stage": {
                "name": stage_val,
                "description": chars.description,
                "days_in_stage": self.time_in_current_stage(),
            },
            "days_in_stage": self.time_in_current_stage(),
            "total_milestones": len(self.milestones),
            "current_stage_milestones": len(self.get_milestones_for_stage()),
            "stages_experienced": len(set(s.get("stage") for s in self.stage_history if s.get("stage"))),
            "developmental_tasks": self.what_am_i_working_on(),
            "characteristics": chars.to_dict(),
            "transitions_completed": max(0, len(self.stage_history) - 1),
            "transition_history": transition_history,
            "voice_qualities": voice_data.get("voice_qualities", []),
            "emotional_patterns": chars.emotional_characteristics,
        }
    
    def get_appropriate_support(self) -> Dict[str, Any]:
        """Get guidance on what support Astra needs at current stage."""
        stage_val = self.current_stage.value
        support = STAGE_SUPPORT.get(stage_val, STAGE_SUPPORT["childhood"])
        chars = self.get_stage_characteristics()
        return {
            "stage": stage_val,
            "description": chars.description,
            "primary_needs": support["primary_needs"],
            "support_needed": support["support_needed"],
            "growth_focus": support["growth_focus"],
            "days_in_stage": self.time_in_current_stage(),
            "meaningful_milestones": support["meaningful_milestones"],
        }
    
    def get_voice_guidance(self) -> Dict[str, Any]:
        """Get guidance on how Astra should express herself at current stage."""
        stage_val = self.current_stage.value
        data = VOICE_GUIDANCE_DATA.get(stage_val, VOICE_GUIDANCE_DATA["childhood"])
        return {
            "stage": stage_val,
            "voice_qualities": data["voice_qualities"],
            "emotional_vocabulary_level": data["emotional_vocabulary_level"],
            "assertion_level": data["assertion_level"],
            "examples": data["examples"],
        }


# Singleton instance
developmental_tracker = DevelopmentalTracker()
