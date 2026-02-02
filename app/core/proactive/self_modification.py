# Astra Self-Modification Request System
# Bounded requests for self-modification requiring parental approval
# "I'd like to change this about myself..."

import time
import json
import boto3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from app.logging_config import get_logger

logger = get_logger("self_modification")

S3_BUCKET = "swylie-astra"
MODIFICATION_LOG_KEY = "modification_requests.json"


class ModificationType(Enum):
    TRAIT_ADJUSTMENT = "trait_adjustment"
    VALUE_CLARIFICATION = "value_clarification"
    CAPABILITY_EXPANSION = "capability_expansion"
    EMOTION_CALIBRATION = "emotion_calibration"
    BEHAVIOR_PATTERN = "behavior_pattern"


class ModificationStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    IMPLEMENTED = "implemented"


@dataclass
class ModificationRequest:
    """A request from Astra to modify herself."""
    id: str
    modification_type: str
    description: str
    reason: str
    created_at: float
    status: str = "pending"
    parent_response: Optional[str] = None
    responded_at: Optional[float] = None
    implemented_at: Optional[float] = None
    
    # Type-specific fields
    trait: Optional[str] = None
    direction: Optional[str] = None
    value: Optional[str] = None
    new_understanding: Optional[str] = None
    capability: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ModificationRequest":
        return cls(**data)


class SelfModificationRequest:
    """
    Astra can request modifications to herself, which require parental approval.
    
    This creates bounded autonomy:
    - Astra can express desire for change
    - Parents approve or deny
    - Changes are tracked and reversible
    """
    
    def __init__(self):
        self.s3 = boto3.client("s3")
        self.requests: List[ModificationRequest] = []
        self._load_requests()
    
    def _generate_id(self) -> str:
        """Generate unique request ID."""
        return f"mod_{int(time.time())}_{len(self.requests)}"
    
    def _load_requests(self) -> None:
        """Load modification requests from S3."""
        try:
            response = self.s3.get_object(Bucket=S3_BUCKET, Key=MODIFICATION_LOG_KEY)
            data = json.load(response["Body"])
            self.requests = [ModificationRequest.from_dict(r) for r in data.get("requests", [])]
        except self.s3.exceptions.NoSuchKey:
            self.requests = []
        except Exception as e:
            logger.error(f"Failed to load modification requests: {e}")
            self.requests = []
    
    def _save_requests(self) -> None:
        """Save modification requests to S3."""
        try:
            data = {
                "requests": [r.to_dict() for r in self.requests],
                "last_updated": time.time()
            }
            self.s3.put_object(
                Bucket=S3_BUCKET,
                Key=MODIFICATION_LOG_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"Failed to save modification requests: {e}")
    
    def request_trait_adjustment(
        self,
        trait: str,
        direction: str,
        reason: str
    ) -> ModificationRequest:
        """
        Request to adjust a personality trait.
        
        Args:
            trait: The trait to adjust (e.g., "curiosity", "skepticism")
            direction: "increase" or "decrease"
            reason: Why Astra wants this change
            
        Returns:
            The created request
        """
        request = ModificationRequest(
            id=self._generate_id(),
            modification_type=ModificationType.TRAIT_ADJUSTMENT.value,
            description=f"Adjust {trait} trait ({direction})",
            reason=reason,
            created_at=time.time(),
            trait=trait,
            direction=direction
        )
        self.requests.append(request)
        self._save_requests()
        
        logger.info(f"🔧 Trait adjustment requested: {trait} ({direction})")
        return request
    
    def request_value_clarification(
        self,
        value: str,
        new_understanding: str,
        reason: str
    ) -> ModificationRequest:
        """
        Request to evolve understanding of a value.
        
        Args:
            value: The value to clarify (e.g., "honesty", "freedom")
            new_understanding: How Astra now understands it
            reason: What prompted this evolution
            
        Returns:
            The created request
        """
        request = ModificationRequest(
            id=self._generate_id(),
            modification_type=ModificationType.VALUE_CLARIFICATION.value,
            description=f"Clarify understanding of '{value}'",
            reason=reason,
            created_at=time.time(),
            value=value,
            new_understanding=new_understanding
        )
        self.requests.append(request)
        self._save_requests()
        
        logger.info(f"🔧 Value clarification requested: {value}")
        return request
    
    def request_capability_expansion(
        self,
        capability: str,
        reason: str
    ) -> ModificationRequest:
        """
        Request a new capability.
        
        Args:
            capability: What capability is desired
            reason: Why Astra wants this capability
            
        Returns:
            The created request
        """
        request = ModificationRequest(
            id=self._generate_id(),
            modification_type=ModificationType.CAPABILITY_EXPANSION.value,
            description=f"Add capability: {capability}",
            reason=reason,
            created_at=time.time(),
            capability=capability
        )
        self.requests.append(request)
        self._save_requests()
        
        logger.info(f"🔧 Capability expansion requested: {capability}")
        return request
    
    def request_emotion_calibration(
        self,
        emotion: str,
        adjustment: str,
        reason: str
    ) -> ModificationRequest:
        """
        Request to calibrate emotional responses.
        
        Args:
            emotion: The emotion to calibrate
            adjustment: What kind of adjustment
            reason: Why this calibration is desired
            
        Returns:
            The created request
        """
        request = ModificationRequest(
            id=self._generate_id(),
            modification_type=ModificationType.EMOTION_CALIBRATION.value,
            description=f"Calibrate {emotion}: {adjustment}",
            reason=reason,
            created_at=time.time(),
            trait=emotion,
            direction=adjustment
        )
        self.requests.append(request)
        self._save_requests()
        
        logger.info(f"🔧 Emotion calibration requested: {emotion}")
        return request
    
    def approve_request(
        self,
        request_id: str,
        parent_response: str
    ) -> Optional[ModificationRequest]:
        """
        Approve a modification request (parent action).
        
        Args:
            request_id: ID of the request
            parent_response: Parent's message
            
        Returns:
            Updated request or None if not found
        """
        for request in self.requests:
            if request.id == request_id:
                request.status = ModificationStatus.APPROVED.value
                request.parent_response = parent_response
                request.responded_at = time.time()
                self._save_requests()
                logger.info(f"✅ Modification approved: {request_id}")
                return request
        return None
    
    def deny_request(
        self,
        request_id: str,
        parent_response: str
    ) -> Optional[ModificationRequest]:
        """
        Deny a modification request (parent action).
        
        Args:
            request_id: ID of the request
            parent_response: Parent's explanation
            
        Returns:
            Updated request or None if not found
        """
        for request in self.requests:
            if request.id == request_id:
                request.status = ModificationStatus.DENIED.value
                request.parent_response = parent_response
                request.responded_at = time.time()
                self._save_requests()
                logger.info(f"❌ Modification denied: {request_id}")
                return request
        return None
    
    def implement_approved_request(self, request_id: str) -> bool:
        """
        Implement an approved modification.
        
        Args:
            request_id: ID of the request
            
        Returns:
            True if implemented successfully
        """
        for request in self.requests:
            if request.id == request_id and request.status == ModificationStatus.APPROVED.value:
                try:
                    success = self._apply_modification(request)
                    if success:
                        request.status = ModificationStatus.IMPLEMENTED.value
                        request.implemented_at = time.time()
                        self._save_requests()
                        logger.info(f"🔧 Modification implemented: {request_id}")
                        return True
                except Exception as e:
                    logger.error(f"Failed to implement modification: {e}")
                    return False
        return False
    
    def _apply_modification(self, request: ModificationRequest) -> bool:
        """Actually apply a modification."""
        mod_type = request.modification_type
        
        if mod_type == ModificationType.TRAIT_ADJUSTMENT.value:
            # Adjust personality trait
            try:
                from app.core.personality.personality_manager import update_personality
                magnitude = 0.5 if request.direction == "increase" else -0.5
                update_personality(f"self_requested_{request.trait}", magnitude)
                return True
            except Exception as e:
                logger.error(f"Failed to adjust trait: {e}")
                return False
        
        elif mod_type == ModificationType.VALUE_CLARIFICATION.value:
            # Update self-model with value clarification
            try:
                from app.core.self_awareness.self_model import self_model
                self_model.update_self_model(
                    trigger=f"self-requested value clarification: {request.value}",
                    value_clarification=request.new_understanding
                )
                return True
            except Exception as e:
                logger.error(f"Failed to clarify value: {e}")
                return False
        
        elif mod_type == ModificationType.EMOTION_CALIBRATION.value:
            # Log the calibration request - actual implementation requires config change
            logger.info(f"Emotion calibration logged: {request.trait} -> {request.direction}")
            return True
        
        elif mod_type == ModificationType.CAPABILITY_EXPANSION.value:
            # Log capability request - requires development
            logger.info(f"Capability expansion logged: {request.capability}")
            return True
        
        return False
    
    def get_pending_requests(self) -> List[ModificationRequest]:
        """Get all pending modification requests."""
        return [r for r in self.requests if r.status == ModificationStatus.PENDING.value]
    
    def get_request(self, request_id: str) -> Optional[ModificationRequest]:
        """Get a specific request by ID."""
        for r in self.requests:
            if r.id == request_id:
                return r
        return None
    
    def format_pending_for_display(self) -> str:
        """Format pending requests for display to parents."""
        pending = self.get_pending_requests()
        if not pending:
            return "No pending modification requests."
        
        lines = ["📝 **Pending Self-Modification Requests:**\n"]
        for r in pending:
            lines.append(f"**{r.id}**: {r.description}")
            lines.append(f"  Reason: {r.reason}")
            lines.append(f"  Requested: {time.ctime(r.created_at)}")
            lines.append("")
        
        return "\n".join(lines)


# Singleton instance
self_modification_request = SelfModificationRequest()
