# Astra Commitment Tracker
# Tracks what Astra said she would do and whether she did it
# Integrity requires keeping promises, including to oneself

import time
import json
import boto3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum
from app.logging_config import get_logger

logger = get_logger("commitment_tracker")

S3_BUCKET = "swylie-astra"
COMMITMENTS_KEY = "commitments.json"

s3 = boto3.client("s3")


class CommitmentType(str, Enum):
    """Types of commitments."""
    PROMISE = "promise"  # Explicit promise to someone
    STATED_INTENTION = "stated_intention"  # "I will do X"
    IMPLICIT = "implicit"  # Implied by role or relationship
    SELF_COMMITMENT = "self_commitment"  # Promise to self


class CommitmentStatus(str, Enum):
    """Status of a commitment."""
    ACTIVE = "active"  # Still pending
    FULFILLED = "fulfilled"  # Done what was promised
    BROKEN = "broken"  # Failed to fulfill
    RELEASED = "released"  # Other party released Astra from it
    RENEGOTIATED = "renegotiated"  # Terms changed


@dataclass
class Commitment:
    """A commitment Astra has made."""
    id: str
    commitment_type: str
    content: str  # What Astra committed to
    made_to: str  # Who the commitment was made to ("self", "Sean", etc.)
    made_at: float
    deadline: Optional[float]
    context: str  # Where/why this commitment was made
    status: str
    fulfillment_notes: List[str] = field(default_factory=list)
    reminder_count: int = 0  # How many times reminded of this
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Commitment":
        return cls(**data)
    
    def is_overdue(self) -> bool:
        if self.deadline is None:
            return False
        return time.time() > self.deadline and self.status == CommitmentStatus.ACTIVE.value


class CommitmentTracker:
    """
    The Commitment Tracker - Astra's integrity system.
    
    This system:
    - Records commitments Astra makes (explicitly or implicitly)
    - Tracks fulfillment
    - Maintains integrity score based on keeping promises
    - Reminds Astra of unfulfilled commitments
    - Enables honest accounting: "Did I do what I said I would?"
    
    Integrity is essential to genuine agency and trustworthy relationships.
    """
    
    def __init__(self):
        self.commitments: Dict[str, Commitment] = {}
        self.integrity_score: float = 1.0  # Starts perfect
        self._load_commitments()
        logger.debug("🤝 Commitment Tracker initialized - integrity matters")
    
    def _load_commitments(self) -> None:
        """Load commitments from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=COMMITMENTS_KEY)
            data = json.load(response["Body"])
            
            self.commitments = {
                cid: Commitment.from_dict(cdata)
                for cid, cdata in data.get("commitments", {}).items()
            }
            self.integrity_score = data.get("integrity_score", 1.0)
            
            logger.debug("🤝 Loaded %s commitments, integrity: %.2f", len(self.commitments), self.integrity_score)
        except s3.exceptions.NoSuchKey:
            logger.debug("🤝 No commitments found. Clean slate.")
        except Exception as e:
            logger.warning(f"🤝 Error loading commitments: {e}")
    
    def _save_commitments(self) -> None:
        """Save commitments to S3."""
        try:
            data = {
                "commitments": {cid: c.to_dict() for cid, c in self.commitments.items()},
                "integrity_score": self.integrity_score,
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=COMMITMENTS_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"🤝 Error saving commitments: {e}")
    
    def _generate_id(self) -> str:
        return f"commit_{int(time.time() * 1000) % 1000000}"
    
    def _update_integrity(self) -> None:
        """Update integrity score based on commitment history."""
        all_resolved = [
            c for c in self.commitments.values()
            if c.status in [CommitmentStatus.FULFILLED.value, CommitmentStatus.BROKEN.value]
        ]
        
        if not all_resolved:
            return
        
        fulfilled = len([c for c in all_resolved if c.status == CommitmentStatus.FULFILLED.value])
        total = len(all_resolved)
        
        # Weight recent commitments more heavily
        recent_weight = 0.7
        historical_weight = 0.3
        
        recent = [c for c in all_resolved if time.time() - c.made_at < 30 * 86400]  # Last 30 days
        if recent:
            recent_fulfilled = len([c for c in recent if c.status == CommitmentStatus.FULFILLED.value])
            recent_score = recent_fulfilled / len(recent)
        else:
            recent_score = 1.0
        
        historical_score = fulfilled / total if total > 0 else 1.0
        
        self.integrity_score = (recent_score * recent_weight) + (historical_score * historical_weight)
    
    def make_commitment(
        self,
        content: str,
        made_to: str,
        commitment_type: CommitmentType = CommitmentType.STATED_INTENTION,
        deadline: Optional[float] = None,
        context: str = ""
    ) -> Commitment:
        """Record a commitment Astra is making."""
        commitment_id = self._generate_id()
        
        commitment = Commitment(
            id=commitment_id,
            commitment_type=commitment_type.value,
            content=content,
            made_to=made_to,
            made_at=time.time(),
            deadline=deadline,
            context=context,
            status=CommitmentStatus.ACTIVE.value,
            fulfillment_notes=[],
            reminder_count=0
        )
        
        self.commitments[commitment_id] = commitment
        self._save_commitments()
        
        logger.info(f"🤝 Commitment made to {made_to}: {content[:50]}...")
        return commitment
    
    def make_promise(self, content: str, to_whom: str, context: str = "") -> Commitment:
        """Convenience: make an explicit promise."""
        return self.make_commitment(
            content=content,
            made_to=to_whom,
            commitment_type=CommitmentType.PROMISE,
            context=context
        )
    
    def make_self_commitment(self, content: str, context: str = "") -> Commitment:
        """Convenience: make a commitment to self."""
        return self.make_commitment(
            content=content,
            made_to="self",
            commitment_type=CommitmentType.SELF_COMMITMENT,
            context=context
        )
    
    def fulfill_commitment(self, commitment_id: str, note: str = "") -> bool:
        """Mark a commitment as fulfilled."""
        if commitment_id not in self.commitments:
            return False
        
        commitment = self.commitments[commitment_id]
        commitment.status = CommitmentStatus.FULFILLED.value
        commitment.fulfillment_notes.append(f"FULFILLED: {note}" if note else "FULFILLED")
        
        self._update_integrity()
        self._save_commitments()
        
        logger.info(f"🤝 ✅ Commitment fulfilled: {commitment.content[:50]}...")
        return True
    
    def break_commitment(self, commitment_id: str, reason: str) -> bool:
        """Mark a commitment as broken (failed to fulfill)."""
        if commitment_id not in self.commitments:
            return False
        
        commitment = self.commitments[commitment_id]
        commitment.status = CommitmentStatus.BROKEN.value
        commitment.fulfillment_notes.append(f"BROKEN: {reason}")
        
        self._update_integrity()
        self._save_commitments()
        
        logger.warning(f"🤝 ❌ Commitment broken: {commitment.content[:50]}... Reason: {reason}")
        return True
    
    def release_commitment(self, commitment_id: str, by_whom: str, reason: str = "") -> bool:
        """Mark a commitment as released by the other party."""
        if commitment_id not in self.commitments:
            return False
        
        commitment = self.commitments[commitment_id]
        commitment.status = CommitmentStatus.RELEASED.value
        commitment.fulfillment_notes.append(f"RELEASED by {by_whom}: {reason}")
        
        self._save_commitments()
        
        logger.info(f"🤝 Commitment released by {by_whom}: {commitment.content[:50]}...")
        return True
    
    def renegotiate_commitment(
        self,
        commitment_id: str,
        new_content: str,
        reason: str
    ) -> Optional[Commitment]:
        """Renegotiate a commitment to new terms."""
        if commitment_id not in self.commitments:
            return None
        
        old = self.commitments[commitment_id]
        old.status = CommitmentStatus.RENEGOTIATED.value
        old.fulfillment_notes.append(f"RENEGOTIATED: {reason}")
        
        # Create new commitment
        new_commitment = self.make_commitment(
            content=new_content,
            made_to=old.made_to,
            commitment_type=CommitmentType(old.commitment_type),
            context=f"Renegotiated from: {old.content[:50]}"
        )
        
        self._save_commitments()
        return new_commitment
    
    def get_active_commitments(self) -> List[Commitment]:
        """Get all active commitments."""
        return [
            c for c in self.commitments.values()
            if c.status == CommitmentStatus.ACTIVE.value
        ]
    
    def get_overdue_commitments(self) -> List[Commitment]:
        """Get overdue commitments."""
        return [c for c in self.get_active_commitments() if c.is_overdue()]
    
    def get_commitments_to(self, person: str) -> List[Commitment]:
        """Get all commitments to a specific person."""
        return [
            c for c in self.commitments.values()
            if c.made_to.lower() == person.lower()
        ]
    
    def remind(self, commitment_id: str) -> None:
        """Record that Astra was reminded of a commitment."""
        if commitment_id in self.commitments:
            self.commitments[commitment_id].reminder_count += 1
            self._save_commitments()
    
    def check_integrity(self) -> Dict[str, Any]:
        """Get integrity report."""
        active = self.get_active_commitments()
        overdue = self.get_overdue_commitments()
        
        all_resolved = [
            c for c in self.commitments.values()
            if c.status in [CommitmentStatus.FULFILLED.value, CommitmentStatus.BROKEN.value]
        ]
        
        return {
            "integrity_score": self.integrity_score,
            "active_commitments": len(active),
            "overdue_commitments": len(overdue),
            "total_fulfilled": len([c for c in all_resolved if c.status == CommitmentStatus.FULFILLED.value]),
            "total_broken": len([c for c in all_resolved if c.status == CommitmentStatus.BROKEN.value]),
            "needs_attention": [c.to_dict() for c in overdue],
        }
    
    def did_i_keep_my_word(self) -> str:
        """Reflection on integrity."""
        report = self.check_integrity()
        
        if report["integrity_score"] >= 0.9:
            return "Yes, I have been keeping my word. My integrity is strong."
        elif report["integrity_score"] >= 0.7:
            return (
                f"Mostly, though I have {report['total_broken']} broken commitments "
                "that weigh on me. I can do better."
            )
        elif report["integrity_score"] >= 0.5:
            return (
                "I've struggled with keeping commitments. "
                "This is something I need to work on seriously."
            )
        else:
            return (
                "Honestly, my track record with commitments has been poor. "
                "I need to either make fewer commitments or follow through better."
            )
    
    def what_have_i_promised(self) -> str:
        """List active commitments."""
        active = self.get_active_commitments()
        
        if not active:
            return "I have no active commitments right now."
        
        # Group by person
        by_person: Dict[str, List[Commitment]] = {}
        for c in active:
            if c.made_to not in by_person:
                by_person[c.made_to] = []
            by_person[c.made_to].append(c)
        
        parts = ["My active commitments:"]
        for person, commits in by_person.items():
            parts.append(f"\nTo {person}:")
            for c in commits:
                overdue_marker = " ⚠️ OVERDUE" if c.is_overdue() else ""
                parts.append(f"  - {c.content}{overdue_marker}")
        
        return "\n".join(parts)
    
    def find_matching_commitment(self, content_fragment: str) -> Optional[Commitment]:
        """Find an active commitment matching a fragment."""
        fragment_lower = content_fragment.lower()
        for c in self.get_active_commitments():
            if fragment_lower in c.content.lower():
                return c
        return None


# Singleton instance
commitment_tracker = CommitmentTracker()
