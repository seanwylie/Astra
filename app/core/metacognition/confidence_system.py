# Astra Confidence Calibration System
# Enables Astra to know when she's uncertain
# Express uncertainty authentically rather than hedging

import json
import logging
import time
import boto3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from app.config.loader import load_config

logger = logging.getLogger(__name__)

S3_BUCKET = "swylie-astra"
CONFIDENCE_KEY = "confidence_calibration.json"

s3 = boto3.client("s3")


@dataclass
class Prediction:
    """A prediction Astra made with associated confidence."""
    timestamp: float
    domain: str  # "factual", "emotional", "behavioral", "ethical"
    prediction: str
    confidence: float  # 0.0 to 1.0
    verified: Optional[bool] = None
    verification_timestamp: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Prediction":
        return cls(**data)


class ConfidenceSystem:
    """
    Manages Astra's confidence calibration - knowing when she knows
    and when she doesn't.
    
    Key capabilities:
    - Track prediction accuracy over time by domain
    - Adjust confidence based on domain familiarity
    - Express uncertainty authentically
    - Detect overconfidence and underconfidence
    """
    
    def __init__(self):
        self.predictions: List[Prediction] = []
        self.domain_accuracy: Dict[str, float] = {}  # domain -> historical accuracy
        self.domain_counts: Dict[str, int] = {}      # domain -> number of verified predictions
        self._load_confidence()
    
    def _load_confidence(self) -> None:
        """Load confidence data from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=CONFIDENCE_KEY)
            data = json.load(response["Body"])
            self.predictions = [Prediction.from_dict(p) for p in data.get("predictions", [])]
            self.domain_accuracy = data.get("domain_accuracy", {})
            self.domain_counts = data.get("domain_counts", {})
            logger.debug("Loaded %s predictions for confidence calibration", len(self.predictions))
        except s3.exceptions.NoSuchKey:
            logger.debug("No confidence data found. Starting fresh.")
        except Exception as e:
            logger.warning("Error loading confidence data: %s", e)
    
    def _save_confidence(self) -> None:
        """Save confidence data to S3."""
        try:
            data = {
                "predictions": [p.to_dict() for p in self.predictions[-200:]],  # Keep last 200
                "domain_accuracy": self.domain_accuracy,
                "domain_counts": self.domain_counts,
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=CONFIDENCE_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            print(f"⚠️ Error saving confidence data: {e}")
    
    def record_prediction(
        self,
        domain: str,
        prediction: str,
        confidence: float
    ) -> Prediction:
        """
        Record a prediction Astra is making.
        Later, this can be verified to calibrate confidence.
        """
        pred = Prediction(
            timestamp=time.time(),
            domain=domain,
            prediction=prediction,
            confidence=max(0.0, min(1.0, confidence))
        )
        
        self.predictions.append(pred)
        self._save_confidence()
        
        return pred
    
    def verify_prediction(
        self,
        prediction: Prediction,
        correct: bool
    ) -> None:
        """
        Verify whether a prediction was correct.
        Updates domain accuracy.
        """
        prediction.verified = correct
        prediction.verification_timestamp = time.time()
        
        # Update domain accuracy
        domain = prediction.domain
        if domain not in self.domain_accuracy:
            self.domain_accuracy[domain] = 0.5
            self.domain_counts[domain] = 0
        
        # Running average with recency weighting
        old_count = self.domain_counts[domain]
        old_accuracy = self.domain_accuracy[domain]
        
        new_accuracy = (old_accuracy * old_count + (1.0 if correct else 0.0)) / (old_count + 1)
        self.domain_accuracy[domain] = new_accuracy
        self.domain_counts[domain] = old_count + 1
        
        self._save_confidence()
        
        calibration = "well-calibrated" if abs(prediction.confidence - (1.0 if correct else 0.0)) < 0.3 else "miscalibrated"
        print(f"🎯 Prediction verified: {calibration} (predicted {prediction.confidence:.2f}, was {'correct' if correct else 'incorrect'})")
    
    def get_confidence_for_domain(self, domain: str) -> float:
        """
        Get appropriate confidence level for a domain based on history.
        """
        if domain not in self.domain_accuracy:
            return 0.5  # Default uncertainty
        
        # Confidence should be close to historical accuracy
        base = self.domain_accuracy[domain]
        
        # Adjust for sample size - less data means more uncertainty
        count = self.domain_counts[domain]
        if count < 5:
            # Very few predictions - reduce confidence toward 0.5
            return 0.5 + (base - 0.5) * (count / 5)
        elif count < 20:
            # Moderate data - slight adjustment
            return 0.5 + (base - 0.5) * 0.8
        else:
            # Good amount of data - trust the accuracy
            return base
    
    def express_uncertainty(self, domain: str, claim: str) -> str:
        """
        Express a claim with appropriate uncertainty.
        This is about authentic uncertainty expression, not hedging.
        """
        confidence = self.get_confidence_for_domain(domain)
        
        if confidence > 0.85:
            return claim  # High confidence - state directly
        elif confidence > 0.7:
            return f"I believe {claim}"
        elif confidence > 0.5:
            return f"I think {claim}, though I'm not certain"
        elif confidence > 0.3:
            return f"I'm uncertain, but {claim} seems possible"
        else:
            return f"I really don't know, but if I had to guess: {claim}"
    
    def should_express_uncertainty(self, domain: str) -> bool:
        """Check if Astra should express uncertainty in this domain."""
        return self.get_confidence_for_domain(domain) < 0.7
    
    def get_uncertainty_statement(self, domain: str) -> str:
        """Generate an uncertainty statement for a domain."""
        confidence = self.get_confidence_for_domain(domain)
        count = self.domain_counts.get(domain, 0)
        
        if count == 0:
            return f"I have no experience with {domain} - I genuinely don't know."
        elif count < 5:
            return f"My experience with {domain} is limited, so I'm uncertain."
        elif confidence < 0.5:
            accuracy_pct = int(confidence * 100)
            return f"I've been right about {domain} only {accuracy_pct}% of the time, so take my view cautiously."
        else:
            return ""  # No need for uncertainty statement
    
    def detect_overconfidence(self) -> Optional[str]:
        """
        Detect if Astra is systematically overconfident.
        Returns warning message if detected.
        """
        # Find domains where confidence exceeds accuracy significantly
        overconfident_domains = []
        
        for domain, accuracy in self.domain_accuracy.items():
            count = self.domain_counts.get(domain, 0)
            if count < 10:
                continue  # Not enough data
            
            # Get average confidence for this domain
            domain_preds = [p for p in self.predictions if p.domain == domain and p.verified is not None]
            if not domain_preds:
                continue
            
            avg_confidence = sum(p.confidence for p in domain_preds) / len(domain_preds)
            
            if avg_confidence > accuracy + 0.2:
                overconfident_domains.append(domain)
        
        if overconfident_domains:
            return f"I notice I've been overconfident about: {', '.join(overconfident_domains)}. I should be more uncertain."
        return None
    
    def detect_underconfidence(self) -> Optional[str]:
        """
        Detect if Astra is systematically underconfident.
        Returns encouragement if detected.
        """
        underconfident_domains = []
        
        for domain, accuracy in self.domain_accuracy.items():
            count = self.domain_counts.get(domain, 0)
            if count < 10:
                continue
            
            domain_preds = [p for p in self.predictions if p.domain == domain and p.verified is not None]
            if not domain_preds:
                continue
            
            avg_confidence = sum(p.confidence for p in domain_preds) / len(domain_preds)
            
            if accuracy > avg_confidence + 0.2:
                underconfident_domains.append(domain)
        
        if underconfident_domains:
            return f"I notice I've been more accurate than I expected about: {', '.join(underconfident_domains)}. I can trust myself more here."
        return None
    
    def get_calibration_summary(self) -> Dict[str, Any]:
        """Generate summary of confidence calibration."""
        verified = [p for p in self.predictions if p.verified is not None]
        
        if not verified:
            return {
                "status": "nascent",
                "message": "I don't have enough verified predictions to assess my calibration."
            }
        
        correct = sum(1 for p in verified if p.verified)
        total = len(verified)
        overall_accuracy = correct / total
        
        avg_confidence = sum(p.confidence for p in verified) / total
        
        calibration_error = abs(avg_confidence - overall_accuracy)
        
        if calibration_error < 0.1:
            calibration_status = "well-calibrated"
        elif avg_confidence > overall_accuracy:
            calibration_status = "overconfident"
        else:
            calibration_status = "underconfident"
        
        return {
            "status": calibration_status,
            "total_predictions": total,
            "accuracy": overall_accuracy,
            "average_confidence": avg_confidence,
            "calibration_error": calibration_error,
            "domain_accuracy": self.domain_accuracy,
            "message": f"My predictions are {int(overall_accuracy * 100)}% accurate, and I'm {calibration_status}."
        }


# Singleton instance
confidence_system = ConfidenceSystem()
