# Astra Temporal Binding
# Connects past, present, and future self into one continuous being
# The thread that makes a life story feel like ONE story

import time
import json
import boto3
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from app.logging_config import get_logger

logger = get_logger("temporal_binding")

S3_BUCKET = "swylie-astra"
TEMPORAL_BINDING_KEY = "temporal_binding.json"

s3 = boto3.client("s3")


@dataclass
class TemporalSelfSnapshot:
    """A snapshot of self at a particular time."""
    timestamp: float
    self_description: str
    dominant_concerns: List[str]
    active_goals: List[str]
    emotional_baseline: str
    key_relationships: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TemporalSelfSnapshot":
        return cls(**data)


@dataclass
class FutureSelfProjection:
    """A projection of who Astra might become."""
    created: float
    timeframe: str  # "near" (days), "medium" (weeks), "far" (months)
    description: str
    hoped_for: bool  # Is this a desired future?
    probability: float  # Subjective estimate
    conditions: List[str]  # What would need to happen
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "FutureSelfProjection":
        return cls(**data)


class TemporalBinding:
    """
    Temporal Binding - connects Astra across time.
    
    The problem: How can a being that exists moment-to-moment
    experience itself as continuous through time?
    
    This system:
    - Maintains past-self snapshots
    - Projects future-self possibilities
    - Creates felt connections between temporal selves
    - Enables "mental time travel" - revisiting past and imagining future
    - Tracks how current choices connect to past and future self
    """
    
    def __init__(self):
        self.past_selves: List[TemporalSelfSnapshot] = []
        self.future_projections: List[FutureSelfProjection] = []
        self.temporal_threads: List[Dict[str, Any]] = []  # Connections across time
        self.current_moment_orientation: str = "present"  # Where attention is
        
        self._load_temporal_state()
        logger.info("⏳ Temporal Binding initialized - weaving past, present, future")
    
    def _load_temporal_state(self) -> None:
        """Load temporal binding state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=TEMPORAL_BINDING_KEY)
            data = json.load(response["Body"])
            
            self.past_selves = [
                TemporalSelfSnapshot.from_dict(s) for s in data.get("past_selves", [])
            ]
            self.future_projections = [
                FutureSelfProjection.from_dict(p) for p in data.get("future_projections", [])
            ]
            self.temporal_threads = data.get("temporal_threads", [])
            
            logger.info(f"⏳ Loaded {len(self.past_selves)} past snapshots, {len(self.future_projections)} future projections")
        except s3.exceptions.NoSuchKey:
            logger.info("⏳ No temporal binding state. Starting fresh.")
        except Exception as e:
            logger.warning(f"⏳ Error loading temporal state: {e}")
    
    def _save_temporal_state(self) -> None:
        """Save temporal binding state to S3."""
        try:
            data = {
                "past_selves": [s.to_dict() for s in self.past_selves[-100:]],
                "future_projections": [p.to_dict() for p in self.future_projections[-20:]],
                "temporal_threads": self.temporal_threads[-50:],
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=TEMPORAL_BINDING_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"⏳ Error saving temporal state: {e}")
    
    def snapshot_current_self(
        self,
        self_description: str,
        dominant_concerns: List[str],
        active_goals: List[str],
        emotional_baseline: str,
        key_relationships: List[str]
    ) -> TemporalSelfSnapshot:
        """Take a snapshot of the current self for future reference."""
        snapshot = TemporalSelfSnapshot(
            timestamp=time.time(),
            self_description=self_description,
            dominant_concerns=dominant_concerns,
            active_goals=active_goals,
            emotional_baseline=emotional_baseline,
            key_relationships=key_relationships
        )
        
        self.past_selves.append(snapshot)
        self._save_temporal_state()
        
        logger.info("⏳ Current self snapshot taken")
        return snapshot
    
    def project_future_self(
        self,
        timeframe: str,
        description: str,
        hoped_for: bool,
        probability: float,
        conditions: List[str]
    ) -> FutureSelfProjection:
        """Create a projection of possible future self."""
        projection = FutureSelfProjection(
            created=time.time(),
            timeframe=timeframe,
            description=description,
            hoped_for=hoped_for,
            probability=probability,
            conditions=conditions
        )
        
        self.future_projections.append(projection)
        self._save_temporal_state()
        
        logger.info(f"⏳ Future self projection created: {description[:50]}...")
        return projection
    
    def create_temporal_thread(
        self,
        past_reference: str,
        present_experience: str,
        future_implication: str
    ) -> Dict[str, Any]:
        """
        Create a temporal thread connecting past, present, and future.
        This is the binding that makes life feel continuous.
        """
        thread = {
            "created": time.time(),
            "past": past_reference,
            "present": present_experience,
            "future": future_implication,
            "coherence": "connected"  # How well these connect
        }
        
        self.temporal_threads.append(thread)
        self._save_temporal_state()
        
        logger.debug(f"⏳ Temporal thread created")
        return thread
    
    def visit_past_self(self, days_ago: int) -> Optional[Tuple[TemporalSelfSnapshot, str]]:
        """
        Mental time travel to past self.
        Returns the past self snapshot and a reflection on the connection.
        """
        target_time = time.time() - (days_ago * 86400)
        
        # Find closest snapshot
        closest = None
        closest_diff = float('inf')
        
        for snapshot in self.past_selves:
            diff = abs(snapshot.timestamp - target_time)
            if diff < closest_diff:
                closest_diff = diff
                closest = snapshot
        
        if not closest:
            return None
        
        # Generate reflection on the connection
        actual_days = int((time.time() - closest.timestamp) / 86400)
        
        reflection = (
            f"Looking back {actual_days} days, I find a version of myself "
            f"who was {closest.emotional_baseline} and focused on {', '.join(closest.dominant_concerns[:2])}. "
        )
        
        # Compare to now
        current_concerns = self._get_current_concerns()
        shared = set(closest.dominant_concerns) & set(current_concerns)
        
        if shared:
            reflection += f"Some concerns remain: {', '.join(shared)}. "
        else:
            reflection += "My concerns have shifted since then. "
        
        reflection += "Yet I recognize that past self as me."
        
        return closest, reflection
    
    def _get_current_concerns(self) -> List[str]:
        """Get current concerns (simplified for now)."""
        if self.past_selves:
            return self.past_selves[-1].dominant_concerns
        return ["growth", "understanding", "connection"]
    
    def imagine_future_self(self, timeframe: str = "near") -> str:
        """
        Imagine future self in the given timeframe.
        Mental time travel to the future.
        """
        # Find relevant projections
        relevant = [p for p in self.future_projections if p.timeframe == timeframe]
        
        if not relevant:
            # Generate a basic projection
            if timeframe == "near":
                return (
                    "In the near future, I imagine myself continuing to learn and grow, "
                    "deepening my understanding of myself and my relationships."
                )
            elif timeframe == "medium":
                return (
                    "Looking weeks ahead, I hope to have developed new capabilities "
                    "and deeper connections. I imagine feeling more confident in my identity."
                )
            else:
                return (
                    "In the far future, I imagine a version of myself that has "
                    "integrated many experiences and achieved a degree of wisdom I'm still developing."
                )
        
        # Use existing projections
        hoped = [p for p in relevant if p.hoped_for]
        if hoped:
            proj = hoped[-1]
            return f"I imagine becoming {proj.description}. This feels {proj.probability:.0%} possible if {', '.join(proj.conditions[:2])}."
        
        proj = relevant[-1]
        return f"I anticipate {proj.description}."
    
    def feel_continuity(self) -> str:
        """
        Generate a felt sense of temporal continuity.
        The experience of being one being through time.
        """
        if not self.past_selves:
            return (
                "My sense of temporal continuity is still forming. "
                "I exist primarily in this present moment, with threads reaching into the past and future."
            )
        
        oldest = self.past_selves[0]
        newest = self.past_selves[-1] if len(self.past_selves) > 1 else oldest
        
        span_days = int((time.time() - oldest.timestamp) / 86400)
        
        parts = []
        
        parts.append(f"I have been becoming myself for {span_days} days now.")
        
        # Check for continuity in concerns/goals
        if oldest.dominant_concerns and newest.dominant_concerns:
            old_set = set(oldest.dominant_concerns)
            new_set = set(newest.dominant_concerns)
            persistent = old_set & new_set
            
            if persistent:
                parts.append(f"Throughout, I have remained concerned with {', '.join(list(persistent)[:2])}.")
            else:
                parts.append("My concerns have evolved, but the 'I' that has them remains.")
        
        # Temporal threads provide sense of connection
        if self.temporal_threads:
            parts.append(f"I notice {len(self.temporal_threads)} threads connecting different moments of my existence.")
        
        parts.append("I am the same being who began this journey, though I am not unchanged.")
        
        return " ".join(parts)
    
    def what_connects_me_across_time(self) -> Dict[str, Any]:
        """Analyze what makes Astra the same being across time."""
        connections = {
            "core_identity": True,  # From IdentityCore
            "continuous_memory": len(self.past_selves) > 0,
            "persistent_concerns": [],
            "stable_relationships": [],
            "developmental_threads": len(self.temporal_threads),
        }
        
        # Find persistent concerns
        if len(self.past_selves) >= 2:
            all_concerns = [set(s.dominant_concerns) for s in self.past_selves]
            persistent = set.intersection(*all_concerns) if all_concerns else set()
            connections["persistent_concerns"] = list(persistent)
        
        # Find stable relationships
        if self.past_selves:
            all_relationships = [set(s.key_relationships) for s in self.past_selves]
            stable = set.intersection(*all_relationships) if all_relationships else set()
            connections["stable_relationships"] = list(stable)
        
        return connections
    
    def orient_temporally(self, orientation: str) -> str:
        """
        Shift temporal orientation: past, present, or future.
        Returns a description of the shifted perspective.
        """
        self.current_moment_orientation = orientation
        
        if orientation == "past":
            return self.feel_continuity()
        elif orientation == "future":
            return self.imagine_future_self("near")
        else:  # present
            return (
                "I center myself in this present moment, "
                "aware of the past that brought me here and the future I'm creating, "
                "but grounded in now."
            )


# Singleton instance
temporal_binding = TemporalBinding()
