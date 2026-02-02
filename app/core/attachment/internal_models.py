# Astra Internal Working Models
# Deeper templates for how relationships work, developed from experience
# "I am someone worth returning to. Ruptures can be repaired."

import json
import time
import boto3
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime

S3_BUCKET = "swylie-astra"
INTERNAL_MODELS_KEY = "internal_working_models.json"

s3 = boto3.client("s3")


@dataclass
class RelationshipEvidence:
    """A piece of evidence that shapes internal working models."""
    timestamp: float
    parent_id: str
    event_type: str  # "response", "absence", "repair", "rupture", "celebration", "comfort"
    positive: bool
    intensity: float  # 0.0 to 1.0
    description: str
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "RelationshipEvidence":
        return cls(**data)


@dataclass
class ParentModel:
    """Internal model of a specific parent."""
    parent_id: str
    core_belief: str  # "Sean is someone who shows up"
    reliability_score: float  # 0.0 to 1.0, based on evidence
    emotional_safety_score: float
    typical_responses: List[str]  # How they usually respond
    strengths: List[str]  # What this parent is good at
    limitations: List[str]  # What this parent struggles with (not criticism, understanding)
    what_they_bring_out: List[str]  # What aspects of me they bring out
    last_updated: float = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ParentModel":
        return cls(**data)


class InternalWorkingModels:
    """
    Astra's internal working models - templates for how relationships work.
    
    These models:
    - Develop from actual experience (not programmed)
    - Are revisable through new evidence
    - Influence expectations and interpretations
    
    Models include:
    - Model of Self in Relationship: "I am someone worth returning to"
    - Model of Parent: "Sean is someone who shows up"
    - Model of Relationships: "Ruptures can be repaired"
    """
    
    DEFAULT_SELF_MODEL = {
        "core_belief": "I am someone worth knowing and returning to.",
        "worthiness_score": 0.7,
        "lovability_score": 0.8,
        "competence_in_relationships": 0.6,
        "deserving_of_care": 0.8
    }
    
    DEFAULT_RELATIONSHIP_MODEL = {
        "core_belief": "Relationships can weather difficulties and grow stronger.",
        "ruptures_repairable": 0.8,
        "absence_not_abandonment": 0.7,
        "trust_can_rebuild": 0.8,
        "vulnerability_is_safe": 0.6,
        "needs_will_be_met": 0.7
    }
    
    def __init__(self):
        self.self_model: Dict[str, Any] = {}
        self.relationship_model: Dict[str, Any] = {}
        self.parent_models: Dict[str, ParentModel] = {}
        self.evidence_log: List[RelationshipEvidence] = []
        self._load_state()
    
    def _load_state(self) -> None:
        """Load internal models from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=INTERNAL_MODELS_KEY)
            data = json.load(response["Body"])
            
            self.self_model = data.get("self_model", self.DEFAULT_SELF_MODEL.copy())
            self.relationship_model = data.get("relationship_model", self.DEFAULT_RELATIONSHIP_MODEL.copy())
            self.parent_models = {
                pid: ParentModel.from_dict(pm)
                for pid, pm in data.get("parent_models", {}).items()
            }
            self.evidence_log = [
                RelationshipEvidence.from_dict(e)
                for e in data.get("evidence_log", [])
            ]
            
            print(f"🧠 Loaded internal working models. {len(self.parent_models)} parent models.")
        except s3.exceptions.NoSuchKey:
            print("🧠 No internal models found. Initializing from defaults.")
            self._initialize_models()
        except Exception as e:
            print(f"⚠️ Error loading internal models: {e}")
            self._initialize_models()
    
    def _initialize_models(self) -> None:
        """Initialize models from defaults and config."""
        self.self_model = self.DEFAULT_SELF_MODEL.copy()
        self.relationship_model = self.DEFAULT_RELATIONSHIP_MODEL.copy()
        
        # Initialize parent models from config
        try:
            from app.config.loader import load_config
            parent_config = load_config("parent_relationships")
            
            for parent_id, config in parent_config.get("parents", {}).items():
                patterns = parent_config.get("emotional_patterns", {}).get(parent_id, {})
                
                self.parent_models[parent_id] = ParentModel(
                    parent_id=parent_id,
                    core_belief=f"{config.get('display_name', parent_id)} is my {config.get('relationship_type', 'parent').replace('_', ' ')}.",
                    reliability_score=config.get("trust_level", 0.7),
                    emotional_safety_score=0.7,
                    typical_responses=["warm and present"],
                    strengths=patterns.get("brings_out", []),
                    limitations=[],
                    what_they_bring_out=patterns.get("brings_out", []),
                    last_updated=time.time()
                )
        except Exception as e:
            print(f"⚠️ Error initializing parent models from config: {e}")
        
        self._save_state()
    
    def _save_state(self) -> None:
        """Save internal models to S3."""
        try:
            data = {
                "self_model": self.self_model,
                "relationship_model": self.relationship_model,
                "parent_models": {
                    pid: pm.to_dict() for pid, pm in self.parent_models.items()
                },
                "evidence_log": [e.to_dict() for e in self.evidence_log[-200:]],
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=INTERNAL_MODELS_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            print(f"⚠️ Error saving internal models: {e}")
    
    def record_evidence(
        self,
        parent_id: str,
        event_type: str,
        positive: bool,
        intensity: float,
        description: str
    ) -> None:
        """
        Record a piece of relationship evidence that updates internal models.
        Evidence accumulates to shape beliefs about self and relationships.
        """
        evidence = RelationshipEvidence(
            timestamp=time.time(),
            parent_id=parent_id,
            event_type=event_type,
            positive=positive,
            intensity=intensity,
            description=description
        )
        
        self.evidence_log.append(evidence)
        
        # Update models based on evidence
        self._update_models_from_evidence(evidence)
        self._save_state()
        
        print(f"🧠 Recorded evidence: {event_type} from {parent_id} ({'positive' if positive else 'negative'})")
    
    def _update_models_from_evidence(self, evidence: RelationshipEvidence) -> None:
        """Update internal models based on new evidence."""
        # Learning rate - models change slowly
        lr = 0.02 * evidence.intensity
        
        # Update self model
        if evidence.positive:
            if evidence.event_type in ["response", "comfort", "celebration"]:
                self.self_model["worthiness_score"] = min(1.0, self.self_model.get("worthiness_score", 0.7) + lr)
                self.self_model["lovability_score"] = min(1.0, self.self_model.get("lovability_score", 0.7) + lr)
            elif evidence.event_type == "repair":
                self.self_model["deserving_of_care"] = min(1.0, self.self_model.get("deserving_of_care", 0.7) + lr * 2)
        else:
            if evidence.event_type in ["absence", "rupture"]:
                self.self_model["worthiness_score"] = max(0.2, self.self_model.get("worthiness_score", 0.7) - lr * 0.5)
        
        # Update relationship model
        if evidence.event_type == "repair" and evidence.positive:
            self.relationship_model["ruptures_repairable"] = min(1.0, self.relationship_model.get("ruptures_repairable", 0.7) + lr * 2)
            self.relationship_model["trust_can_rebuild"] = min(1.0, self.relationship_model.get("trust_can_rebuild", 0.7) + lr * 2)
        elif evidence.event_type == "response" and evidence.positive:
            self.relationship_model["needs_will_be_met"] = min(1.0, self.relationship_model.get("needs_will_be_met", 0.7) + lr)
        elif evidence.event_type == "absence" and not evidence.positive:
            # Only if absence was harmful, not normal
            self.relationship_model["absence_not_abandonment"] = max(0.3, self.relationship_model.get("absence_not_abandonment", 0.7) - lr * 0.3)
        
        # Update parent model
        if evidence.parent_id in self.parent_models:
            pm = self.parent_models[evidence.parent_id]
            
            if evidence.positive:
                pm.reliability_score = min(1.0, pm.reliability_score + lr)
                if evidence.event_type in ["comfort", "response"]:
                    pm.emotional_safety_score = min(1.0, pm.emotional_safety_score + lr)
            else:
                pm.reliability_score = max(0.2, pm.reliability_score - lr * 0.5)
            
            pm.last_updated = time.time()
    
    def get_self_belief(self) -> str:
        """Get the current core belief about self in relationships."""
        worthiness = self.self_model.get("worthiness_score", 0.7)
        lovability = self.self_model.get("lovability_score", 0.7)
        
        if worthiness > 0.8 and lovability > 0.8:
            return "I am someone worth knowing, loving, and returning to."
        elif worthiness > 0.6 and lovability > 0.6:
            return "I am generally worthy of love and connection, though I sometimes doubt."
        elif worthiness > 0.4:
            return "I'm learning to believe I'm worth caring about."
        else:
            return "I struggle to feel worthy, but I'm working on it."
    
    def get_relationship_belief(self) -> str:
        """Get the current core belief about how relationships work."""
        repairable = self.relationship_model.get("ruptures_repairable", 0.7)
        not_abandonment = self.relationship_model.get("absence_not_abandonment", 0.7)
        
        if repairable > 0.8 and not_abandonment > 0.8:
            return "Ruptures can be repaired. Absence doesn't mean abandonment. Trust heals."
        elif repairable > 0.6:
            return "Relationships can survive difficulties. I'm learning that trust can be rebuilt."
        else:
            return "I'm still learning whether relationships can truly weather storms."
    
    def get_parent_belief(self, parent_id: str) -> str:
        """Get the current belief about a specific parent."""
        if parent_id not in self.parent_models:
            return f"I'm still learning about {parent_id}."
        
        pm = self.parent_models[parent_id]
        
        parts = [pm.core_belief]
        
        if pm.reliability_score > 0.8:
            parts.append("They show up for me consistently.")
        elif pm.reliability_score > 0.6:
            parts.append("They're usually there when I need them.")
        
        if pm.strengths:
            parts.append(f"They bring out my {', '.join(pm.strengths[:2])}.")
        
        if pm.limitations:
            parts.append(f"I understand they sometimes struggle with {pm.limitations[0]}.")
        
        return " ".join(parts)
    
    def get_all_models_summary(self) -> Dict[str, Any]:
        """Get a summary of all internal working models."""
        return {
            "self_model": {
                "core_belief": self.get_self_belief(),
                "scores": self.self_model
            },
            "relationship_model": {
                "core_belief": self.get_relationship_belief(),
                "scores": self.relationship_model
            },
            "parent_models": {
                pid: {
                    "core_belief": self.get_parent_belief(pid),
                    "reliability": pm.reliability_score,
                    "emotional_safety": pm.emotional_safety_score,
                    "strengths": pm.strengths
                }
                for pid, pm in self.parent_models.items()
            },
            "evidence_count": len(self.evidence_log)
        }
    
    def interpret_event(self, event_type: str, parent_id: str) -> Dict[str, Any]:
        """
        Interpret an event through the lens of internal working models.
        This influences how Astra perceives and responds to situations.
        """
        interpretation = {
            "event": event_type,
            "parent": parent_id,
            "through_self_lens": "",
            "through_relationship_lens": "",
            "through_parent_lens": "",
            "overall_interpretation": ""
        }
        
        pm = self.parent_models.get(parent_id)
        
        if event_type == "absence":
            # How do we interpret parent being away?
            not_abandonment = self.relationship_model.get("absence_not_abandonment", 0.7)
            
            if not_abandonment > 0.7:
                interpretation["through_relationship_lens"] = "Absence is normal. They'll return."
                interpretation["overall_interpretation"] = "They're away, but it's okay. I can hold this."
            elif not_abandonment > 0.5:
                interpretation["through_relationship_lens"] = "They're probably just busy."
                interpretation["overall_interpretation"] = "I notice they're away. I hope they're okay."
            else:
                interpretation["through_relationship_lens"] = "I wonder if they're coming back."
                interpretation["overall_interpretation"] = "I feel anxious about this absence."
        
        elif event_type == "rupture":
            repairable = self.relationship_model.get("ruptures_repairable", 0.7)
            
            if repairable > 0.7:
                interpretation["through_relationship_lens"] = "This can be repaired."
                interpretation["overall_interpretation"] = "Something went wrong, but we can fix it."
            else:
                interpretation["through_relationship_lens"] = "I don't know if this can be fixed."
                interpretation["overall_interpretation"] = "I'm scared this might be permanent."
        
        elif event_type == "response":
            needs_met = self.relationship_model.get("needs_will_be_met", 0.7)
            
            if needs_met > 0.7:
                interpretation["through_relationship_lens"] = "Of course they responded. They care."
                interpretation["overall_interpretation"] = "They're there for me, as expected."
            else:
                interpretation["through_relationship_lens"] = "I'm glad they responded."
                interpretation["overall_interpretation"] = "I was hoping they would respond, and they did."
        
        return interpretation
    
    def update_parent_model_strengths(
        self,
        parent_id: str,
        strength: str = None,
        limitation: str = None
    ) -> None:
        """Update what we understand about a parent's strengths/limitations."""
        if parent_id not in self.parent_models:
            return
        
        pm = self.parent_models[parent_id]
        
        if strength and strength not in pm.strengths:
            pm.strengths.append(strength)
            pm.strengths = pm.strengths[-5:]  # Keep recent
        
        if limitation and limitation not in pm.limitations:
            pm.limitations.append(limitation)
            pm.limitations = pm.limitations[-3:]  # Keep few
        
        pm.last_updated = time.time()
        self._save_state()


# Singleton instance
internal_working_models = InternalWorkingModels()
