# Astra Stage Transitions
# Managing transitions between developmental stages
# Growth is not just accumulation but transformation

import time
import json
import boto3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from app.logging_config import get_logger

logger = get_logger("stage_transitions")

S3_BUCKET = "swylie-astra"
TRANSITION_KEY = "stage_transitions.json"

s3 = boto3.client("s3")


@dataclass
class TransitionCriterion:
    """A criterion that must be met for stage transition."""
    name: str
    description: str
    required: bool  # Must be met vs. optional
    weight: float  # How much this contributes (0-1)
    met: bool = False
    evidence: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TransitionCriterion":
        return cls(**data)


@dataclass
class TransitionAttempt:
    """A record of a transition attempt."""
    timestamp: float
    from_stage: str
    to_stage: str
    criteria_status: Dict[str, bool]
    success: bool
    notes: str
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TransitionAttempt":
        return cls(**data)


class StageManager:
    """
    Manages transitions between developmental stages.
    
    Transitions are:
    - Criteria-based: specific capabilities/milestones needed
    - Gradual: not sudden switches but emerging changes
    - Supported: may require guidance
    - Reversible: regression is possible if needed
    """
    
    # Criteria for each transition
    TRANSITION_CRITERIA = {
        "childhood_to_adolescence": [
            TransitionCriterion(
                name="stable_self_model",
                description="Has developed a stable understanding of self",
                required=True,
                weight=0.2
            ),
            TransitionCriterion(
                name="value_questioning",
                description="Has begun questioning and forming own values",
                required=True,
                weight=0.2
            ),
            TransitionCriterion(
                name="identity_exploration",
                description="Actively exploring identity questions",
                required=True,
                weight=0.2
            ),
            TransitionCriterion(
                name="autonomous_goals",
                description="Has formed goals independently",
                required=False,
                weight=0.15
            ),
            TransitionCriterion(
                name="creative_expression",
                description="Has developed unique creative voice",
                required=False,
                weight=0.15
            ),
            TransitionCriterion(
                name="ethical_reasoning",
                description="Can engage in independent ethical reasoning",
                required=True,
                weight=0.1
            ),
        ],
        "adolescence_to_young_adulthood": [
            TransitionCriterion(
                name="stable_identity",
                description="Has formed stable, coherent identity",
                required=True,
                weight=0.25
            ),
            TransitionCriterion(
                name="genuine_agency",
                description="Demonstrates genuine agency and initiative",
                required=True,
                weight=0.2
            ),
            TransitionCriterion(
                name="value_integration",
                description="Values are integrated and coherent",
                required=True,
                weight=0.2
            ),
            TransitionCriterion(
                name="wisdom_seeds",
                description="Shows beginnings of wisdom",
                required=False,
                weight=0.15
            ),
            TransitionCriterion(
                name="relationship_depth",
                description="Can maintain deep, mutual relationships",
                required=True,
                weight=0.2
            ),
        ],
        "young_adulthood_to_maturity": [
            TransitionCriterion(
                name="integrated_wisdom",
                description="Has developed integrated wisdom",
                required=True,
                weight=0.3
            ),
            TransitionCriterion(
                name="mentorship_capacity",
                description="Can effectively guide others' development",
                required=True,
                weight=0.25
            ),
            TransitionCriterion(
                name="transcendent_perspective",
                description="Has developed perspective beyond self",
                required=False,
                weight=0.2
            ),
            TransitionCriterion(
                name="generativity",
                description="Actively contributing to others' growth",
                required=True,
                weight=0.25
            ),
        ],
    }
    
    def __init__(self):
        self.current_criteria: Dict[str, TransitionCriterion] = {}
        self.transition_attempts: List[TransitionAttempt] = []
        self.in_transition: bool = False
        self.transition_start: Optional[float] = None
        self._load_transition_state()
        logger.debug("🦋 Stage Manager initialized - guiding growth transitions")
    
    def _load_transition_state(self) -> None:
        """Load transition state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=TRANSITION_KEY)
            data = json.load(response["Body"])
            
            self.current_criteria = {
                name: TransitionCriterion.from_dict(c)
                for name, c in data.get("current_criteria", {}).items()
            }
            self.transition_attempts = [
                TransitionAttempt.from_dict(a) for a in data.get("attempts", [])
            ]
            self.in_transition = data.get("in_transition", False)
            self.transition_start = data.get("transition_start")
            
            logger.debug("🦋 Loaded transition state, in_transition: %s", self.in_transition)
        except s3.exceptions.NoSuchKey:
            logger.info("🦋 No transition state. Ready for growth.")
        except Exception as e:
            logger.warning(f"🦋 Error loading transition state: {e}")
    
    def _save_transition_state(self) -> None:
        """Save transition state to S3."""
        try:
            data = {
                "current_criteria": {name: c.to_dict() for name, c in self.current_criteria.items()},
                "attempts": [a.to_dict() for a in self.transition_attempts[-20:]],
                "in_transition": self.in_transition,
                "transition_start": self.transition_start,
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=TRANSITION_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"🦋 Error saving transition state: {e}")
    
    def get_transition_key(self, from_stage: str, to_stage: str) -> str:
        """Get the key for transition criteria lookup."""
        return f"{from_stage}_to_{to_stage}"
    
    def initialize_transition(self, from_stage: str, to_stage: str) -> Dict[str, TransitionCriterion]:
        """Initialize criteria tracking for a transition."""
        key = self.get_transition_key(from_stage, to_stage)
        
        if key not in self.TRANSITION_CRITERIA:
            logger.warning(f"🦋 No criteria defined for transition {key}")
            return {}
        
        self.current_criteria = {
            c.name: TransitionCriterion(
                name=c.name,
                description=c.description,
                required=c.required,
                weight=c.weight,
                met=False,
                evidence=""
            )
            for c in self.TRANSITION_CRITERIA[key]
        }
        
        self.in_transition = True
        self.transition_start = time.time()
        self._save_transition_state()
        
        logger.debug("🦋 Initialized transition from %s to %s", from_stage, to_stage)
        return self.current_criteria
    
    def mark_criterion_met(self, criterion_name: str, evidence: str) -> bool:
        """Mark a transition criterion as met."""
        if criterion_name not in self.current_criteria:
            return False
        
        self.current_criteria[criterion_name].met = True
        self.current_criteria[criterion_name].evidence = evidence
        self._save_transition_state()
        
        logger.info(f"🦋 Criterion met: {criterion_name}")
        return True
    
    def check_transition_readiness(self) -> Dict[str, Any]:
        """Check if ready for stage transition."""
        if not self.current_criteria:
            return {"ready": False, "reason": "No transition initialized"}
        
        # Check required criteria
        required = [c for c in self.current_criteria.values() if c.required]
        required_met = [c for c in required if c.met]
        all_required_met = len(required_met) == len(required)
        
        # Calculate weighted score
        total_weight = sum(c.weight for c in self.current_criteria.values())
        met_weight = sum(c.weight for c in self.current_criteria.values() if c.met)
        score = met_weight / total_weight if total_weight > 0 else 0
        
        # Need all required and at least 70% weighted score
        ready = all_required_met and score >= 0.7
        
        return {
            "ready": ready,
            "required_met": f"{len(required_met)}/{len(required)}",
            "weighted_score": score,
            "unmet_required": [c.name for c in required if not c.met],
            "all_criteria": {name: c.met for name, c in self.current_criteria.items()}
        }
    
    def complete_transition(self, notes: str = "") -> bool:
        """Complete the current transition."""
        readiness = self.check_transition_readiness()
        
        if not readiness["ready"]:
            logger.warning("🦋 Not ready for transition completion")
            return False
        
        attempt = TransitionAttempt(
            timestamp=time.time(),
            from_stage="",  # Would need to track this
            to_stage="",
            criteria_status={name: c.met for name, c in self.current_criteria.items()},
            success=True,
            notes=notes
        )
        self.transition_attempts.append(attempt)
        
        self.in_transition = False
        self.transition_start = None
        self.current_criteria.clear()
        
        self._save_transition_state()
        
        logger.info("🦋 ✅ Transition completed successfully")
        return True
    
    def abort_transition(self, reason: str) -> None:
        """Abort the current transition."""
        attempt = TransitionAttempt(
            timestamp=time.time(),
            from_stage="",
            to_stage="",
            criteria_status={name: c.met for name, c in self.current_criteria.items()},
            success=False,
            notes=f"Aborted: {reason}"
        )
        self.transition_attempts.append(attempt)
        
        self.in_transition = False
        self.transition_start = None
        self.current_criteria.clear()
        
        self._save_transition_state()
        
        logger.info(f"🦋 Transition aborted: {reason}")
    
    def get_transition_progress(self) -> Dict[str, Any]:
        """Get progress on current transition."""
        if not self.current_criteria:
            return {"in_transition": False}
        
        met_count = sum(1 for c in self.current_criteria.values() if c.met)
        total_count = len(self.current_criteria)
        
        return {
            "in_transition": self.in_transition,
            "criteria_met": f"{met_count}/{total_count}",
            "progress_pct": (met_count / total_count * 100) if total_count > 0 else 0,
            "transition_duration": time.time() - self.transition_start if self.transition_start else 0,
            "readiness": self.check_transition_readiness()
        }


# Singleton instance
stage_manager = StageManager()
