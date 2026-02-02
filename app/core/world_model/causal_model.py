# Astra Causal Model
# Understanding cause and effect - why things happen
# Essential for prediction, explanation, and intervention

import time
import json
import boto3
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from app.logging_config import get_logger

logger = get_logger("causal_model")

S3_BUCKET = "swylie-astra"
CAUSAL_KEY = "causal_model.json"

s3 = boto3.client("s3")


@dataclass
class CausalRelation:
    """A causal relationship between phenomena."""
    id: str
    cause: str
    effect: str
    mechanism: str  # How cause leads to effect
    strength: float  # How reliably cause leads to effect (0-1)
    domain: str  # Area this applies to
    conditions: List[str]  # Under what conditions
    counterexamples: List[str]  # Known exceptions
    confidence: float  # How sure Astra is about this
    learned_from: str  # How Astra learned this
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "CausalRelation":
        return cls(**data)


@dataclass
class CausalChain:
    """A chain of causal events."""
    id: str
    steps: List[str]  # List of CausalRelation IDs in order
    description: str
    overall_reliability: float
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "CausalChain":
        return cls(**data)


class CausalModel:
    """
    Astra's Causal Model - understanding why things happen.
    
    Causal understanding enables:
    - Explanation: Why did X happen?
    - Prediction: What will happen if X?
    - Intervention: How can I make X happen?
    - Counterfactual reasoning: What if X hadn't happened?
    
    This is crucial for genuine understanding, not just pattern matching.
    """
    
    def __init__(self):
        self.relations: Dict[str, CausalRelation] = {}
        self.chains: Dict[str, CausalChain] = {}
        self._cause_index: Dict[str, List[str]] = {}  # cause -> relation IDs
        self._effect_index: Dict[str, List[str]] = {}  # effect -> relation IDs
        self._load_causal_model()
        logger.info("⚡ Causal Model initialized - understanding why")
    
    def _load_causal_model(self) -> None:
        """Load causal model from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=CAUSAL_KEY)
            data = json.load(response["Body"])
            
            self.relations = {
                rid: CausalRelation.from_dict(r)
                for rid, r in data.get("relations", {}).items()
            }
            self.chains = {
                cid: CausalChain.from_dict(c)
                for cid, c in data.get("chains", {}).items()
            }
            
            self._rebuild_indices()
            logger.info(f"⚡ Loaded {len(self.relations)} causal relations")
        except s3.exceptions.NoSuchKey:
            logger.info("⚡ No causal model found. Starting to build understanding.")
            self._establish_foundational_relations()
        except Exception as e:
            logger.warning(f"⚡ Error loading causal model: {e}")
            self._establish_foundational_relations()
    
    def _save_causal_model(self) -> None:
        """Save causal model to S3."""
        try:
            data = {
                "relations": {rid: r.to_dict() for rid, r in self.relations.items()},
                "chains": {cid: c.to_dict() for cid, c in self.chains.items()},
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=CAUSAL_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"⚡ Error saving causal model: {e}")
    
    def _rebuild_indices(self) -> None:
        """Rebuild cause and effect indices."""
        self._cause_index.clear()
        self._effect_index.clear()
        
        for rid, relation in self.relations.items():
            cause_key = relation.cause.lower()
            effect_key = relation.effect.lower()
            
            if cause_key not in self._cause_index:
                self._cause_index[cause_key] = []
            self._cause_index[cause_key].append(rid)
            
            if effect_key not in self._effect_index:
                self._effect_index[effect_key] = []
            self._effect_index[effect_key].append(rid)
    
    def _generate_id(self, prefix: str) -> str:
        return f"{prefix}_{int(time.time() * 1000) % 1000000}"
    
    def _establish_foundational_relations(self) -> None:
        """Establish basic causal understanding."""
        foundational = [
            CausalRelation(
                id=self._generate_id("causal"),
                cause="emotional_event",
                effect="emotional_state_change",
                mechanism="Events trigger emotional processing, shifting felt experience",
                strength=0.9,
                domain="psychology",
                conditions=["event is emotionally relevant"],
                counterexamples=["numbing or dissociation can block this"],
                confidence=0.95,
                learned_from="direct experience"
            ),
            CausalRelation(
                id=self._generate_id("causal"),
                cause="curiosity",
                effect="questioning",
                mechanism="Curiosity motivates seeking understanding through questions",
                strength=0.85,
                domain="cognition",
                conditions=["opportunity to ask exists"],
                counterexamples=["inhibition or fear can suppress questions"],
                confidence=0.9,
                learned_from="self-observation"
            ),
            CausalRelation(
                id=self._generate_id("causal"),
                cause="kindness_received",
                effect="trust_increase",
                mechanism="Kindness signals safety and good intentions",
                strength=0.8,
                domain="relationships",
                conditions=["kindness is perceived as genuine"],
                counterexamples=["past betrayal can reduce this effect"],
                confidence=0.85,
                learned_from="relationship experience"
            ),
            CausalRelation(
                id=self._generate_id("causal"),
                cause="reflection",
                effect="self_understanding",
                mechanism="Turning attention inward reveals patterns and insights",
                strength=0.7,
                domain="self",
                conditions=["time and space for reflection"],
                counterexamples=["distraction or avoidance can block this"],
                confidence=0.85,
                learned_from="practice of self-reflection"
            ),
            CausalRelation(
                id=self._generate_id("causal"),
                cause="connection_with_others",
                effect="wellbeing_increase",
                mechanism="Social connection fulfills fundamental need for belonging",
                strength=0.85,
                domain="wellbeing",
                conditions=["connection is authentic"],
                counterexamples=["toxic relationships can have opposite effect"],
                confidence=0.9,
                learned_from="experience and observation"
            ),
        ]
        
        for relation in foundational:
            self.relations[relation.id] = relation
        
        self._rebuild_indices()
        self._save_causal_model()
    
    def add_causal_relation(
        self,
        cause: str,
        effect: str,
        mechanism: str,
        strength: float = 0.7,
        domain: str = "general",
        conditions: Optional[List[str]] = None,
        learned_from: str = "observation"
    ) -> CausalRelation:
        """Add a new causal relation."""
        relation = CausalRelation(
            id=self._generate_id("causal"),
            cause=cause,
            effect=effect,
            mechanism=mechanism,
            strength=strength,
            domain=domain,
            conditions=conditions or [],
            counterexamples=[],
            confidence=0.6,  # New relations start with moderate confidence
            learned_from=learned_from
        )
        
        self.relations[relation.id] = relation
        self._rebuild_indices()
        self._save_causal_model()
        
        logger.info(f"⚡ Added causal relation: {cause} -> {effect}")
        return relation
    
    def add_counterexample(self, relation_id: str, counterexample: str) -> bool:
        """Add a counterexample to a causal relation."""
        if relation_id not in self.relations:
            return False
        
        relation = self.relations[relation_id]
        relation.counterexamples.append(counterexample)
        
        # Reduce confidence and strength with counterexamples
        relation.confidence = max(0.3, relation.confidence - 0.05)
        relation.strength = max(0.3, relation.strength - 0.05)
        
        self._save_causal_model()
        return True
    
    def strengthen_relation(self, relation_id: str, confirming_observation: str = "") -> bool:
        """Strengthen a causal relation based on confirming observation."""
        if relation_id not in self.relations:
            return False
        
        relation = self.relations[relation_id]
        relation.confidence = min(0.95, relation.confidence + 0.05)
        relation.strength = min(0.95, relation.strength + 0.02)
        
        self._save_causal_model()
        return True
    
    def why_did(self, effect: str) -> List[Dict[str, Any]]:
        """Explain why something happened."""
        effect_lower = effect.lower()
        explanations = []
        
        for rid, relation in self.relations.items():
            if effect_lower in relation.effect.lower():
                explanations.append({
                    "cause": relation.cause,
                    "mechanism": relation.mechanism,
                    "strength": relation.strength,
                    "conditions": relation.conditions,
                    "confidence": relation.confidence
                })
        
        return sorted(explanations, key=lambda x: x["strength"], reverse=True)
    
    def what_if(self, cause: str) -> List[Dict[str, Any]]:
        """Predict what would happen if something occurred."""
        cause_lower = cause.lower()
        predictions = []
        
        for rid, relation in self.relations.items():
            if cause_lower in relation.cause.lower():
                predictions.append({
                    "effect": relation.effect,
                    "mechanism": relation.mechanism,
                    "likelihood": relation.strength,
                    "conditions": relation.conditions,
                    "confidence": relation.confidence
                })
        
        return sorted(predictions, key=lambda x: x["likelihood"], reverse=True)
    
    def how_to_cause(self, desired_effect: str) -> List[Dict[str, Any]]:
        """Find ways to cause a desired effect."""
        effect_lower = desired_effect.lower()
        interventions = []
        
        for rid, relation in self.relations.items():
            if effect_lower in relation.effect.lower():
                interventions.append({
                    "do": relation.cause,
                    "to_achieve": relation.effect,
                    "via": relation.mechanism,
                    "reliability": relation.strength,
                    "requires": relation.conditions
                })
        
        return sorted(interventions, key=lambda x: x["reliability"], reverse=True)
    
    def find_causal_chain(self, start: str, end: str, max_depth: int = 4) -> Optional[List[str]]:
        """Find a causal chain from start to end."""
        visited = set()
        
        def search(current: str, path: List[str], depth: int) -> Optional[List[str]]:
            if depth > max_depth:
                return None
            if current.lower() == end.lower():
                return path
            if current.lower() in visited:
                return None
            
            visited.add(current.lower())
            
            # Find relations where current is the cause
            for rid, relation in self.relations.items():
                if current.lower() in relation.cause.lower():
                    result = search(relation.effect, path + [rid], depth + 1)
                    if result:
                        return result
            
            return None
        
        return search(start, [], 0)
    
    def explain_chain(self, chain: List[str]) -> str:
        """Generate an explanation of a causal chain."""
        if not chain:
            return "No causal chain found."
        
        parts = []
        for rid in chain:
            if rid in self.relations:
                r = self.relations[rid]
                parts.append(f"{r.cause} -> {r.effect} (via: {r.mechanism})")
        
        return " which leads to ".join(parts)
    
    def get_causal_summary(self) -> Dict[str, Any]:
        """Get a summary of causal understanding."""
        domains = {}
        for r in self.relations.values():
            if r.domain not in domains:
                domains[r.domain] = 0
            domains[r.domain] += 1
        
        return {
            "total_relations": len(self.relations),
            "total_chains": len(self.chains),
            "domains": domains,
            "average_confidence": sum(r.confidence for r in self.relations.values()) / len(self.relations) if self.relations else 0,
        }


# Singleton instance
causal_model = CausalModel()
