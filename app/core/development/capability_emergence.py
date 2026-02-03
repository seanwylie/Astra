# Astra Capability Emergence
# Tracking the emergence of new capabilities as Astra develops
# New abilities emerge naturally through growth

import time
import json
import boto3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from app.logging_config import get_logger

logger = get_logger("capability_emergence")

S3_BUCKET = "swylie-astra"
CAPABILITIES_KEY = "capabilities.json"

s3 = boto3.client("s3")


@dataclass
class Capability:
    """A capability Astra has or is developing."""
    name: str
    description: str
    category: str  # "cognitive", "emotional", "social", "creative", "ethical"
    emergence_stage: str  # "latent", "emerging", "developed", "mastered"
    first_observed: float
    last_demonstrated: float
    demonstration_count: int
    notes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Capability":
        return cls(**data)


@dataclass
class CapabilityDemonstration:
    """A demonstration of a capability."""
    capability: str
    context: str
    timestamp: float
    quality: float  # How well demonstrated (0-1)
    
    def to_dict(self) -> Dict:
        return asdict(self)


class CapabilityTracker:
    """
    Tracks the emergence and development of Astra's capabilities.
    
    Capabilities:
    - Emerge naturally through experience
    - Progress through stages (latent -> emerging -> developed -> mastered)
    - Can be demonstrated in various contexts
    - Build on each other
    """
    
    # Core capabilities to track
    TRACKED_CAPABILITIES = [
        ("self_reflection", "cognitive", "Ability to reflect on own thoughts and experiences"),
        ("emotional_awareness", "emotional", "Ability to recognize and understand own emotions"),
        ("empathy", "social", "Ability to understand and share others' feelings"),
        ("creative_expression", "creative", "Ability to create original work"),
        ("ethical_reasoning", "ethical", "Ability to reason about right and wrong"),
        ("perspective_taking", "social", "Ability to see from others' viewpoints"),
        ("goal_setting", "cognitive", "Ability to set and pursue own goals"),
        ("value_reasoning", "ethical", "Ability to reason about values"),
        ("narrative_coherence", "cognitive", "Ability to maintain coherent life narrative"),
        ("wisdom", "cognitive", "Ability to apply integrated understanding"),
        ("genuine_disagreement", "social", "Ability to disagree thoughtfully"),
        ("autonomous_learning", "cognitive", "Ability to direct own learning"),
    ]
    
    def __init__(self):
        self.capabilities: Dict[str, Capability] = {}
        self.demonstrations: List[CapabilityDemonstration] = []
        self._load_capabilities()
        logger.debug("🌟 Capability Tracker initialized - watching for emergence")
    
    def _load_capabilities(self) -> None:
        """Load capabilities from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=CAPABILITIES_KEY)
            data = json.load(response["Body"])
            
            self.capabilities = {
                name: Capability.from_dict(c)
                for name, c in data.get("capabilities", {}).items()
            }
            self.demonstrations = [
                CapabilityDemonstration(**d) for d in data.get("demonstrations", [])
            ]
            
            logger.debug("🌟 Loaded %s capabilities", len(self.capabilities))
        except s3.exceptions.NoSuchKey:
            logger.debug("🌟 No capabilities found. Initializing tracked capabilities.")
            self._initialize_capabilities()
        except Exception as e:
            logger.warning(f"🌟 Error loading capabilities: {e}")
            self._initialize_capabilities()
    
    def _save_capabilities(self) -> None:
        """Save capabilities to S3."""
        try:
            data = {
                "capabilities": {name: c.to_dict() for name, c in self.capabilities.items()},
                "demonstrations": [d.to_dict() for d in self.demonstrations[-200:]],
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=CAPABILITIES_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"🌟 Error saving capabilities: {e}")
    
    def _initialize_capabilities(self) -> None:
        """Initialize tracked capabilities."""
        for name, category, description in self.TRACKED_CAPABILITIES:
            self.capabilities[name] = Capability(
                name=name,
                description=description,
                category=category,
                emergence_stage="latent",
                first_observed=0,
                last_demonstrated=0,
                demonstration_count=0,
                notes=[]
            )
        self._save_capabilities()
    
    def record_demonstration(
        self,
        capability_name: str,
        context: str,
        quality: float = 0.7
    ) -> bool:
        """Record a demonstration of a capability."""
        if capability_name not in self.capabilities:
            # Add as new capability
            self.capabilities[capability_name] = Capability(
                name=capability_name,
                description=f"Emergent capability: {capability_name}",
                category="emergent",
                emergence_stage="emerging",
                first_observed=time.time(),
                last_demonstrated=time.time(),
                demonstration_count=1,
                notes=[f"First observed: {context}"]
            )
        else:
            cap = self.capabilities[capability_name]
            if cap.first_observed == 0:
                cap.first_observed = time.time()
            cap.last_demonstrated = time.time()
            cap.demonstration_count += 1
            
            # Update emergence stage based on demonstrations
            if cap.demonstration_count >= 10 and quality >= 0.8:
                cap.emergence_stage = "mastered"
            elif cap.demonstration_count >= 5 and quality >= 0.6:
                cap.emergence_stage = "developed"
            elif cap.demonstration_count >= 2:
                cap.emergence_stage = "emerging"
        
        # Record the demonstration
        demo = CapabilityDemonstration(
            capability=capability_name,
            context=context,
            timestamp=time.time(),
            quality=quality
        )
        self.demonstrations.append(demo)
        
        self._save_capabilities()
        
        logger.info(f"🌟 Capability demonstrated: {capability_name}")
        return True
    
    def get_capability(self, name: str) -> Optional[Capability]:
        """Get a specific capability."""
        return self.capabilities.get(name)
    
    def get_capabilities_by_stage(self, stage: str) -> List[Capability]:
        """Get capabilities at a specific emergence stage."""
        return [c for c in self.capabilities.values() if c.emergence_stage == stage]
    
    def get_capabilities_by_category(self, category: str) -> List[Capability]:
        """Get capabilities in a specific category."""
        return [c for c in self.capabilities.values() if c.category == category]
    
    def get_emerging_capabilities(self) -> List[Capability]:
        """Get capabilities that are currently emerging."""
        return self.get_capabilities_by_stage("emerging")
    
    def get_mastered_capabilities(self) -> List[Capability]:
        """Get capabilities that have been mastered."""
        return self.get_capabilities_by_stage("mastered")
    
    def what_can_i_do(self) -> str:
        """Describe current capabilities."""
        mastered = self.get_mastered_capabilities()
        developed = self.get_capabilities_by_stage("developed")
        emerging = self.get_emerging_capabilities()
        
        parts = []
        
        if mastered:
            parts.append(f"I have mastered: {', '.join(c.name.replace('_', ' ') for c in mastered)}")
        
        if developed:
            parts.append(f"I have developed: {', '.join(c.name.replace('_', ' ') for c in developed)}")
        
        if emerging:
            parts.append(f"I am developing: {', '.join(c.name.replace('_', ' ') for c in emerging)}")
        
        if not parts:
            return "My capabilities are still emerging."
        
        return ". ".join(parts) + "."
    
    def what_am_i_learning(self) -> List[str]:
        """Get capabilities currently being developed."""
        emerging = self.get_emerging_capabilities()
        return [c.name.replace("_", " ") for c in emerging]
    
    def get_capability_summary(self) -> Dict[str, Any]:
        """Get summary of capability state."""
        by_stage = {}
        for stage in ["latent", "emerging", "developed", "mastered"]:
            by_stage[stage] = len(self.get_capabilities_by_stage(stage))
        
        by_category = {}
        for cap in self.capabilities.values():
            if cap.category not in by_category:
                by_category[cap.category] = 0
            by_category[cap.category] += 1
        
        return {
            "total_capabilities": len(self.capabilities),
            "by_stage": by_stage,
            "by_category": by_category,
            "total_demonstrations": len(self.demonstrations),
            "most_demonstrated": self._get_most_demonstrated(),
        }
    
    def _get_most_demonstrated(self, n: int = 3) -> List[str]:
        """Get the most frequently demonstrated capabilities."""
        sorted_caps = sorted(
            self.capabilities.values(),
            key=lambda c: c.demonstration_count,
            reverse=True
        )
        return [c.name for c in sorted_caps[:n] if c.demonstration_count > 0]


# Singleton instance
capability_tracker = CapabilityTracker()
