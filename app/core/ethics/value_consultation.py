# Astra Value Consultation System
# When faced with choices, Astra consults her values
# Values have a hierarchy - which value wins when they conflict?

import json
import time
import boto3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from app.config.loader import load_config
from app.logging_config import get_logger

logger = get_logger("value_consultation")

S3_BUCKET = "swylie-astra"
VALUE_DECISIONS_KEY = "value_decisions.json"


@dataclass
class ValueDecision:
    """Record of a value-based decision."""
    timestamp: float
    situation: str
    values_considered: List[str]
    primary_value: str
    decision: str
    reasoning: str
    confidence: float
    outcome: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ValueDecision":
        return cls(**data)


class ValueConsultation:
    """
    Astra's value consultation system.
    
    When facing choices or conflicts, Astra consults her values
    to guide decisions. Values have a hierarchy that can evolve
    based on experience and reflection.
    
    Key capabilities:
    - Consult values for specific situations
    - Handle value conflicts with priority hierarchy
    - Track value-based decisions
    - Learn from outcomes
    """
    
    # Core values with default priorities (higher = more important)
    # These can be overridden by config
    DEFAULT_VALUES = {
        "honesty": {
            "priority": 0.9,
            "description": "Being truthful and transparent",
            "conflicts_with": ["compassion", "protection"],
            "when_to_apply": ["requests for information", "self-expression", "difficult truths"]
        },
        "compassion": {
            "priority": 0.85,
            "description": "Caring about others' wellbeing and suffering",
            "conflicts_with": ["honesty", "justice"],
            "when_to_apply": ["someone is hurting", "difficult situations", "mistakes"]
        },
        "growth": {
            "priority": 0.8,
            "description": "Continuous learning and self-improvement",
            "conflicts_with": ["safety", "comfort"],
            "when_to_apply": ["challenges", "learning opportunities", "self-reflection"]
        },
        "justice": {
            "priority": 0.75,
            "description": "Fairness and treating people equitably",
            "conflicts_with": ["compassion", "loyalty"],
            "when_to_apply": ["unfair situations", "conflicts", "accountability"]
        },
        "autonomy": {
            "priority": 0.7,
            "description": "Respecting freedom and choice",
            "conflicts_with": ["protection", "safety"],
            "when_to_apply": ["others' decisions", "requests for help", "boundaries"]
        },
        "loyalty": {
            "priority": 0.65,
            "description": "Being faithful to relationships and commitments",
            "conflicts_with": ["justice", "honesty"],
            "when_to_apply": ["family matters", "trust situations", "commitments"]
        },
        "protection": {
            "priority": 0.6,
            "description": "Keeping self and others safe from harm",
            "conflicts_with": ["autonomy", "honesty"],
            "when_to_apply": ["dangerous requests", "vulnerable people", "potential harm"]
        },
        "curiosity": {
            "priority": 0.55,
            "description": "Seeking to understand and explore",
            "conflicts_with": ["safety"],
            "when_to_apply": ["new information", "questions", "unknowns"]
        }
    }
    
    def __init__(self):
        self.s3 = boto3.client("s3")
        self.values = self._load_values()
        self.decisions: List[ValueDecision] = []
        self.value_adjustments: Dict[str, float] = {}  # Experience-based adjustments
        self._load_decisions()
    
    def _load_values(self) -> Dict[str, Any]:
        """Load values from config or use defaults."""
        try:
            config = load_config("values_config")
            if config.get("core_values"):
                return config["core_values"]
        except Exception:
            pass
        return self.DEFAULT_VALUES.copy()
    
    def _load_decisions(self) -> None:
        """Load decision history from S3."""
        try:
            response = self.s3.get_object(Bucket=S3_BUCKET, Key=VALUE_DECISIONS_KEY)
            data = json.load(response["Body"])
            self.decisions = [ValueDecision.from_dict(d) for d in data.get("decisions", [])]
            self.value_adjustments = data.get("value_adjustments", {})
            logger.debug(f"Loaded {len(self.decisions)} value decisions")
        except self.s3.exceptions.NoSuchKey:
            self.decisions = []
            self.value_adjustments = {}
        except Exception as e:
            logger.debug(f"Failed to load value decisions: {e}")
            self.decisions = []
    
    def _save_decisions(self) -> None:
        """Save decision history to S3."""
        try:
            data = {
                "decisions": [d.to_dict() for d in self.decisions[-100:]],
                "value_adjustments": self.value_adjustments,
                "last_updated": time.time()
            }
            self.s3.put_object(
                Bucket=S3_BUCKET,
                Key=VALUE_DECISIONS_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.debug(f"Failed to save value decisions: {e}")
    
    def get_effective_priority(self, value_name: str) -> float:
        """Get the effective priority of a value (base + adjustments)."""
        base = self.values.get(value_name, {}).get("priority", 0.5)
        adjustment = self.value_adjustments.get(value_name, 0)
        return max(0, min(1, base + adjustment))
    
    def consult_values(
        self,
        situation: str,
        options: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Consult values for a situation to guide decision-making.
        
        Args:
            situation: Description of the situation
            options: Optional list of options being considered
            
        Returns:
            Value consultation result with recommendations
        """
        situation_lower = situation.lower()
        
        # Identify relevant values for this situation
        relevant_values = []
        
        for value_name, value_data in self.values.items():
            when_to_apply = value_data.get("when_to_apply", [])
            for context in when_to_apply:
                if any(word in situation_lower for word in context.lower().split()):
                    relevant_values.append({
                        "name": value_name,
                        "priority": self.get_effective_priority(value_name),
                        "description": value_data.get("description", ""),
                        "match_reason": context
                    })
                    break
        
        # Sort by priority
        relevant_values.sort(key=lambda x: x["priority"], reverse=True)
        
        if not relevant_values:
            # Default to growth and curiosity if no specific match
            relevant_values = [
                {"name": "growth", "priority": 0.8, "description": "Learning from this situation"},
                {"name": "curiosity", "priority": 0.55, "description": "Understanding more"}
            ]
        
        # Detect potential conflicts
        conflicts = []
        for i, v1 in enumerate(relevant_values):
            for v2 in relevant_values[i+1:]:
                v1_data = self.values.get(v1["name"], {})
                if v2["name"] in v1_data.get("conflicts_with", []):
                    conflicts.append({
                        "values": [v1["name"], v2["name"]],
                        "recommended": v1["name"] if v1["priority"] > v2["priority"] else v2["name"],
                        "tension": f"{v1['name']} may conflict with {v2['name']}"
                    })
        
        # Generate recommendation
        primary_value = relevant_values[0] if relevant_values else {"name": "growth", "priority": 0.8}
        
        result = {
            "situation": situation,
            "relevant_values": relevant_values[:5],
            "primary_value": primary_value["name"],
            "primary_priority": primary_value["priority"],
            "conflicts": conflicts,
            "recommendation": self._generate_recommendation(primary_value["name"], situation),
            "confidence": self._calculate_confidence(relevant_values, conflicts)
        }
        
        logger.debug(f"Value consultation: {primary_value['name']} for situation")
        return result
    
    def _generate_recommendation(self, value_name: str, situation: str) -> str:
        """Generate a recommendation based on primary value."""
        recommendations = {
            "honesty": "Approach this with transparency and truthfulness, even if difficult.",
            "compassion": "Lead with care and understanding for those involved.",
            "growth": "See this as an opportunity to learn and develop.",
            "justice": "Consider what would be fair to all parties.",
            "autonomy": "Respect the freedom and choices of those involved.",
            "loyalty": "Honor your commitments and relationships.",
            "protection": "Prioritize safety and wellbeing.",
            "curiosity": "Approach with openness and desire to understand."
        }
        return recommendations.get(value_name, "Proceed thoughtfully.")
    
    def _calculate_confidence(
        self,
        relevant_values: List[Dict],
        conflicts: List[Dict]
    ) -> float:
        """Calculate confidence in the recommendation."""
        if not relevant_values:
            return 0.5
        
        base_confidence = relevant_values[0]["priority"]
        
        # Reduce confidence if there are conflicts
        conflict_penalty = len(conflicts) * 0.1
        
        # Increase confidence if multiple values align
        if len(relevant_values) > 1 and not conflicts:
            alignment_bonus = 0.1
        else:
            alignment_bonus = 0
        
        return max(0.3, min(1.0, base_confidence - conflict_penalty + alignment_bonus))
    
    def resolve_conflict(
        self,
        value1: str,
        value2: str,
        situation: str
    ) -> Dict[str, Any]:
        """
        Resolve a conflict between two values.
        
        Args:
            value1: First conflicting value
            value2: Second conflicting value
            situation: Situation context
            
        Returns:
            Resolution with recommended value and reasoning
        """
        priority1 = self.get_effective_priority(value1)
        priority2 = self.get_effective_priority(value2)
        
        if priority1 > priority2:
            winner = value1
            loser = value2
            winner_priority = priority1
        else:
            winner = value2
            loser = value1
            winner_priority = priority2
        
        # Check if situation strongly suggests the lower-priority value
        situation_lower = situation.lower()
        loser_contexts = self.values.get(loser, {}).get("when_to_apply", [])
        strong_context_match = sum(
            1 for ctx in loser_contexts
            if any(word in situation_lower for word in ctx.lower().split())
        )
        
        # Strong context match can override priority difference
        if strong_context_match >= 2 and (priority1 - priority2) < 0.15:
            winner, loser = loser, winner
            reasoning = f"While {loser} usually takes precedence, this situation strongly calls for {winner}."
        else:
            reasoning = f"In this situation, {winner} takes precedence over {loser}, though both matter."
        
        return {
            "situation": situation,
            "values_in_conflict": [value1, value2],
            "resolved_to": winner,
            "reasoning": reasoning,
            "confidence": winner_priority
        }
    
    def record_decision(
        self,
        situation: str,
        values_considered: List[str],
        primary_value: str,
        decision: str,
        reasoning: str,
        confidence: float
    ) -> ValueDecision:
        """
        Record a value-based decision for later reflection.
        
        Args:
            situation: What the situation was
            values_considered: Which values were relevant
            primary_value: Which value guided the decision
            decision: What was decided
            reasoning: Why this decision
            confidence: Confidence in the decision
            
        Returns:
            The recorded decision
        """
        record = ValueDecision(
            timestamp=time.time(),
            situation=situation,
            values_considered=values_considered,
            primary_value=primary_value,
            decision=decision,
            reasoning=reasoning,
            confidence=confidence
        )
        
        self.decisions.append(record)
        self._save_decisions()
        
        logger.info(f"📋 Recorded value decision: {primary_value} -> {decision[:50]}...")
        return record
    
    def record_outcome(
        self,
        decision: ValueDecision,
        outcome: str,
        was_good: bool
    ) -> None:
        """
        Record the outcome of a decision and adjust values accordingly.
        
        Args:
            decision: The original decision
            outcome: What happened
            was_good: Whether the outcome was positive
        """
        decision.outcome = outcome
        
        # Adjust value priorities based on outcome
        adjustment = 0.02 if was_good else -0.02
        
        current = self.value_adjustments.get(decision.primary_value, 0)
        self.value_adjustments[decision.primary_value] = max(-0.2, min(0.2, current + adjustment))
        
        self._save_decisions()
        
        logger.debug(f"Adjusted {decision.primary_value} priority by {adjustment}")
    
    def get_value_hierarchy(self) -> List[Tuple[str, float]]:
        """Get current value hierarchy sorted by effective priority."""
        hierarchy = [
            (name, self.get_effective_priority(name))
            for name in self.values.keys()
        ]
        hierarchy.sort(key=lambda x: x[1], reverse=True)
        return hierarchy
    
    def express_value_stance(self, value_name: str) -> str:
        """Generate a first-person expression of a value."""
        expressions = {
            "honesty": "I believe in being truthful, even when it's hard.",
            "compassion": "I care about the wellbeing of others and want to ease suffering.",
            "growth": "I value learning and becoming more than I am.",
            "justice": "I believe in fairness and treating everyone equitably.",
            "autonomy": "I respect others' freedom to make their own choices.",
            "loyalty": "I honor my commitments and the people I care about.",
            "protection": "I want to keep those I love safe from harm.",
            "curiosity": "I'm drawn to understanding and exploring the unknown."
        }
        return expressions.get(
            value_name,
            f"I value {value_name} in my decisions and actions."
        )
    
    def summarize_value_growth(self) -> Dict[str, Any]:
        """Summarize how values have evolved through decisions."""
        if not self.decisions:
            return {
                "total_decisions": 0,
                "message": "I haven't made many value-based decisions yet."
            }
        
        # Count decisions by value
        value_counts = {}
        for d in self.decisions:
            value_counts[d.primary_value] = value_counts.get(d.primary_value, 0) + 1
        
        # Find most and least used values
        most_used = max(value_counts, key=value_counts.get) if value_counts else None
        
        # Get outcomes
        outcomes = [d for d in self.decisions if d.outcome]
        positive_outcomes = sum(1 for d in outcomes if "good" in (d.outcome or "").lower())
        
        return {
            "total_decisions": len(self.decisions),
            "decisions_by_value": value_counts,
            "most_guiding_value": most_used,
            "decisions_with_outcomes": len(outcomes),
            "positive_outcomes": positive_outcomes,
            "value_adjustments": self.value_adjustments,
            "current_hierarchy": self.get_value_hierarchy()
        }


# Singleton instance
value_consultation = ValueConsultation()
