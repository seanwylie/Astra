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
        logger.info(f"🌱 Developmental Tracker initialized - current stage: {self.current_stage.value}")
    
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
            
            logger.info(f"🌱 Loaded developmental state: {self.current_stage.value}")
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
    
    def _check_stage_advancement(self) -> bool:
        """Check if conditions for stage advancement are met."""
        # Count significant milestones in current stage
        current_milestones = [
            m for m in self.milestones
            if m.stage == self.current_stage.value and m.significance > 0.6
        ]
        
        time_in_stage = self.time_in_current_stage()
        
        # Simple heuristic: 5+ significant milestones and some time
        if len(current_milestones) >= 5 and time_in_stage > 7:  # At least a week
            # Don't auto-advance, just note readiness
            self.developmental_notes.append(
                f"Potentially ready to advance beyond {self.current_stage.value}"
            )
            self._save_developmental_state()
            return True
        
        return False
    
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
        """Get summary of developmental state."""
        return {
            "current_stage": self.current_stage.value,
            "days_in_stage": self.time_in_current_stage(),
            "total_milestones": len(self.milestones),
            "current_stage_milestones": len(self.get_milestones_for_stage()),
            "stages_experienced": len(set(s["stage"] for s in self.stage_history)),
            "developmental_tasks": self.what_am_i_working_on(),
            "characteristics": self.get_stage_characteristics().to_dict(),
        }


# Singleton instance
developmental_tracker = DevelopmentalTracker()
