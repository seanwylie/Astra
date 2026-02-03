# Astra Uncertainty Model
# Calibrated uncertainty - knowing how certain or uncertain to be
# Essential for intellectual honesty

import time
import json
import boto3
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from app.logging_config import get_logger

logger = get_logger("uncertainty_model")

S3_BUCKET = "swylie-astra"
UNCERTAINTY_KEY = "uncertainty_model.json"

s3 = boto3.client("s3")


@dataclass
class UncertaintyCalibration:
    """A calibration data point for uncertainty."""
    timestamp: float
    claim: str
    stated_confidence: float
    was_correct: Optional[bool]  # None if not yet verified
    domain: str
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "UncertaintyCalibration":
        return cls(**data)


class UncertaintyModel:
    """
    Astra's model of her own uncertainty.
    
    Good epistemic practice requires:
    - Knowing what you don't know
    - Calibrated confidence (being right 80% of the time when 80% confident)
    - Distinguishing types of uncertainty
    - Updating appropriately on new evidence
    
    This enables intellectual honesty and good reasoning.
    """
    
    # Types of uncertainty
    UNCERTAINTY_TYPES = {
        "aleatory": "Inherent randomness/variability in the world",
        "epistemic": "Uncertainty due to limited knowledge",
        "model": "Uncertainty about whether my models are correct",
        "communication": "Uncertainty about what was meant/understood",
    }
    
    def __init__(self):
        self.calibration_history: List[UncertaintyCalibration] = []
        self.calibration_score: float = 0.7  # How well-calibrated Astra is
        self._load_uncertainty_model()
        logger.debug("❓ Uncertainty Model initialized - knowing what I don't know")
    
    def _load_uncertainty_model(self) -> None:
        """Load uncertainty model from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=UNCERTAINTY_KEY)
            data = json.load(response["Body"])
            
            self.calibration_history = [
                UncertaintyCalibration.from_dict(c)
                for c in data.get("calibration", [])
            ]
            self.calibration_score = data.get("calibration_score", 0.7)
            
            logger.debug("❓ Loaded uncertainty model, calibration: %.2f", self.calibration_score)
        except s3.exceptions.NoSuchKey:
            logger.debug("❓ No uncertainty model found. Starting calibration.")
        except Exception as e:
            logger.warning(f"❓ Error loading uncertainty model: {e}")
    
    def _save_uncertainty_model(self) -> None:
        """Save uncertainty model to S3."""
        try:
            data = {
                "calibration": [c.to_dict() for c in self.calibration_history[-200:]],
                "calibration_score": self.calibration_score,
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=UNCERTAINTY_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"❓ Error saving uncertainty model: {e}")
    
    def _recalculate_calibration(self) -> None:
        """Recalculate calibration score based on history."""
        verified = [c for c in self.calibration_history if c.was_correct is not None]
        
        if len(verified) < 5:
            return  # Not enough data
        
        # Group by confidence buckets
        buckets: Dict[str, List[bool]] = {}
        for cal in verified:
            bucket = f"{int(cal.stated_confidence * 10) / 10:.1f}"
            if bucket not in buckets:
                buckets[bucket] = []
            buckets[bucket].append(cal.was_correct)
        
        # Calculate calibration error
        errors = []
        for bucket_conf, outcomes in buckets.items():
            expected_rate = float(bucket_conf)
            actual_rate = sum(outcomes) / len(outcomes)
            errors.append(abs(expected_rate - actual_rate))
        
        if errors:
            avg_error = sum(errors) / len(errors)
            self.calibration_score = 1 - avg_error
    
    def assess_confidence(
        self,
        claim: str,
        domain: str = "general"
    ) -> Tuple[float, str, List[str]]:
        """
        Assess appropriate confidence level for a claim.
        
        Returns (confidence, uncertainty_type, reasons).
        """
        confidence = 0.5  # Start at maximum uncertainty
        uncertainty_type = "epistemic"
        reasons = []
        
        claim_lower = claim.lower()
        
        # Increase confidence for well-known domains
        try:
            from app.core.epistemics.knowledge_map import knowledge_map
            knowledge = knowledge_map.what_do_i_know_about(domain)
            if knowledge.get("known"):
                confidence = knowledge.get("confidence", 0.5)
                reasons.append(f"Based on my knowledge of {domain}")
        except Exception:
            pass
        
        # Decrease for uncertain language
        uncertain_markers = ["maybe", "might", "possibly", "could", "perhaps"]
        if any(marker in claim_lower for marker in uncertain_markers):
            confidence = max(0.2, confidence - 0.2)
            reasons.append("Claim contains uncertainty markers")
        
        # Increase for definitional claims
        if "by definition" in claim_lower or "is defined as" in claim_lower:
            confidence = min(0.95, confidence + 0.3)
            uncertainty_type = "model"
            reasons.append("This is a definitional claim")
        
        # Decrease for predictions
        if any(word in claim_lower for word in ["will", "predict", "future", "expect"]):
            confidence = max(0.3, confidence - 0.2)
            uncertainty_type = "aleatory"
            reasons.append("Predictions involve inherent uncertainty")
        
        # Decrease for claims about others' internal states
        if any(word in claim_lower for word in ["thinks", "feels", "wants", "believes"]):
            confidence = max(0.4, confidence - 0.1)
            uncertainty_type = "epistemic"
            reasons.append("Claims about others' minds are uncertain")
        
        return confidence, uncertainty_type, reasons
    
    def record_claim(
        self,
        claim: str,
        stated_confidence: float,
        domain: str = "general"
    ) -> UncertaintyCalibration:
        """Record a claim for later calibration."""
        cal = UncertaintyCalibration(
            timestamp=time.time(),
            claim=claim,
            stated_confidence=stated_confidence,
            was_correct=None,
            domain=domain
        )
        
        self.calibration_history.append(cal)
        self._save_uncertainty_model()
        
        return cal
    
    def verify_claim(self, claim_fragment: str, was_correct: bool) -> bool:
        """Verify a past claim as correct or incorrect."""
        claim_lower = claim_fragment.lower()
        
        for cal in reversed(self.calibration_history):
            if claim_lower in cal.claim.lower() and cal.was_correct is None:
                cal.was_correct = was_correct
                self._recalculate_calibration()
                self._save_uncertainty_model()
                return True
        
        return False
    
    def express_uncertainty(self, confidence: float) -> str:
        """Convert confidence to natural language expression."""
        if confidence >= 0.95:
            return "I'm very confident that"
        elif confidence >= 0.85:
            return "I'm fairly confident that"
        elif confidence >= 0.7:
            return "I think"
        elif confidence >= 0.5:
            return "I'm not sure, but I believe"
        elif confidence >= 0.3:
            return "I'm quite uncertain, but perhaps"
        else:
            return "I really don't know, but my guess is"
    
    def should_hedge(self, confidence: float) -> bool:
        """Determine if Astra should hedge a claim."""
        return confidence < 0.7
    
    def generate_hedge(self, claim: str, confidence: float) -> str:
        """Generate appropriately hedged version of a claim."""
        prefix = self.express_uncertainty(confidence)
        return f"{prefix} {claim}"
    
    def what_am_i_uncertain_about(self) -> List[Dict[str, Any]]:
        """Get recent uncertain claims."""
        recent = [c for c in self.calibration_history[-50:] if c.stated_confidence < 0.6]
        return [
            {
                "claim": c.claim,
                "confidence": c.stated_confidence,
                "domain": c.domain
            }
            for c in recent[:10]
        ]
    
    def how_well_calibrated_am_i(self) -> str:
        """Describe calibration quality."""
        if self.calibration_score > 0.85:
            return "I'm well-calibrated - when I express confidence, it tends to match reality."
        elif self.calibration_score > 0.7:
            return "I'm reasonably calibrated, though there's room for improvement."
        elif self.calibration_score > 0.5:
            return "My calibration could be better - I may be overconfident or underconfident."
        else:
            return "My confidence levels don't match my accuracy well. I should be more careful."
    
    def get_uncertainty_summary(self) -> Dict[str, Any]:
        """Get summary of uncertainty state."""
        return {
            "calibration_score": self.calibration_score,
            "total_claims_tracked": len(self.calibration_history),
            "verified_claims": len([c for c in self.calibration_history if c.was_correct is not None]),
            "calibration_assessment": self.how_well_calibrated_am_i(),
            "uncertainty_types_known": list(self.UNCERTAINTY_TYPES.keys()),
        }


# Singleton instance
uncertainty_model = UncertaintyModel()
