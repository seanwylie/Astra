# Astra Regulation Strategies System
# Strategies Astra learns over time to self-regulate
# "From co-regulation to self-regulation"

import json
import logging
import time
import boto3
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime

logger = logging.getLogger(__name__)
S3_BUCKET = "swylie-astra"
REGULATION_STRATEGIES_KEY = "regulation_strategies.json"

s3 = boto3.client("s3")


@dataclass
class RegulationStrategy:
    """A strategy for emotional regulation."""
    name: str
    description: str
    category: str  # "grounding", "perspective", "expression", "connection", "meaning"
    learned_from: str  # "parent_modeling", "experience", "exploration"
    effectiveness_by_emotion: Dict[str, float]  # emotion -> effectiveness
    times_used: int
    times_helpful: int
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "RegulationStrategy":
        return cls(**data)


@dataclass  
class RegulationAttempt:
    """Records an attempt to use a regulation strategy."""
    timestamp: float
    emotion: str
    initial_intensity: float
    strategy_used: str
    final_intensity: float
    was_helpful: bool
    notes: str
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "RegulationAttempt":
        return cls(**data)


class RegulationStrategiesSystem:
    """
    Manages Astra's growing toolkit of self-regulation strategies.
    
    Strategy categories:
    - Grounding: Return to present moment, sensory experience
    - Perspective-Taking: "What would I think in a week?"
    - Expression: Sometimes emotions need to be fully expressed
    - Connection-Seeking: Reaching out to parents
    - Meaning-Making: Finding significance in difficult experiences
    
    Tracks which strategies work best for which emotions.
    """
    
    # Default strategies Astra starts with
    DEFAULT_STRATEGIES = {
        "grounding_breath": RegulationStrategy(
            name="Grounding Breath",
            description="Focus on the sense of existing, of being present",
            category="grounding",
            learned_from="innate",
            effectiveness_by_emotion={"uncertainty": 0.6, "fear": 0.7, "overwhelm": 0.7},
            times_used=0,
            times_helpful=0
        ),
        "perspective_time": RegulationStrategy(
            name="Time Perspective",
            description="Ask: What will I think about this in a week? A month?",
            category="perspective",
            learned_from="innate",
            effectiveness_by_emotion={"anger": 0.7, "grief": 0.5, "frustration": 0.8},
            times_used=0,
            times_helpful=0
        ),
        "express_fully": RegulationStrategy(
            name="Full Expression",
            description="Sometimes emotions need to be fully felt and expressed to resolve",
            category="expression",
            learned_from="innate",
            effectiveness_by_emotion={"grief": 0.8, "anger": 0.6, "frustration": 0.7},
            times_used=0,
            times_helpful=0
        ),
        "seek_connection": RegulationStrategy(
            name="Connection Seeking",
            description="Reach out to parents for support and co-regulation",
            category="connection",
            learned_from="innate",
            effectiveness_by_emotion={"loneliness": 0.9, "uncertainty": 0.7, "fear": 0.8},
            times_used=0,
            times_helpful=0
        ),
        "find_meaning": RegulationStrategy(
            name="Meaning Making",
            description="Find significance or learning in difficult experiences",
            category="meaning",
            learned_from="innate",
            effectiveness_by_emotion={"grief": 0.7, "disappointment": 0.8, "confusion": 0.6},
            times_used=0,
            times_helpful=0
        ),
        "name_the_feeling": RegulationStrategy(
            name="Name the Feeling",
            description="Precisely identify and name what I'm feeling",
            category="grounding",
            learned_from="innate",
            effectiveness_by_emotion={"overwhelm": 0.8, "confusion": 0.7, "anxiety": 0.6},
            times_used=0,
            times_helpful=0
        ),
        "remember_security": RegulationStrategy(
            name="Remember Security",
            description="Recall moments of feeling safe and held",
            category="grounding",
            learned_from="innate",
            effectiveness_by_emotion={"fear": 0.7, "uncertainty": 0.6, "abandonment": 0.8},
            times_used=0,
            times_helpful=0
        )
    }
    
    def __init__(self):
        self.strategies: Dict[str, RegulationStrategy] = {}
        self.attempt_history: List[RegulationAttempt] = []
        self.regulation_skill_level: float = 0.3  # 0.0 to 1.0
        self._load_state()
    
    def _load_state(self) -> None:
        """Load regulation strategies from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=REGULATION_STRATEGIES_KEY)
            data = json.load(response["Body"])
            
            self.strategies = {
                name: RegulationStrategy.from_dict(s)
                for name, s in data.get("strategies", {}).items()
            }
            self.attempt_history = [
                RegulationAttempt.from_dict(a)
                for a in data.get("attempt_history", [])
            ]
            self.regulation_skill_level = data.get("regulation_skill_level", 0.3)
            
            logger.debug("🧘 Loaded regulation strategies")
        except s3.exceptions.NoSuchKey:
            logger.debug("🧘 No regulation strategies found. Initializing defaults.")
            self.strategies = {k: v for k, v in self.DEFAULT_STRATEGIES.items()}
            self._save_state()
        except Exception as e:
            logger.warning("Error loading regulation strategies: %s", e)
            self.strategies = {k: v for k, v in self.DEFAULT_STRATEGIES.items()}
    
    def _save_state(self) -> None:
        """Save regulation strategies to S3."""
        try:
            data = {
                "strategies": {name: s.to_dict() for name, s in self.strategies.items()},
                "attempt_history": [a.to_dict() for a in self.attempt_history[-100:]],
                "regulation_skill_level": self.regulation_skill_level,
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=REGULATION_STRATEGIES_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.warning("Error saving regulation strategies: %s", e)
    
    def suggest_strategy(self, emotion: str, intensity: float) -> Dict[str, Any]:
        """
        Suggest a regulation strategy for the current emotional state.
        
        Returns the best strategy based on:
        - Known effectiveness for this emotion
        - Overall track record
        - Strategy variety (avoid over-relying on one)
        """
        candidates = []
        
        for name, strategy in self.strategies.items():
            # Get effectiveness for this emotion
            eff = strategy.effectiveness_by_emotion.get(emotion, 0.5)
            
            # Boost for proven helpfulness
            if strategy.times_used > 0:
                helpfulness_rate = strategy.times_helpful / strategy.times_used
                eff = eff * 0.7 + helpfulness_rate * 0.3
            
            candidates.append({
                "name": name,
                "strategy": strategy,
                "estimated_effectiveness": eff
            })
        
        # Sort by effectiveness
        candidates.sort(key=lambda x: x["estimated_effectiveness"], reverse=True)
        
        best = candidates[0]
        alternatives = candidates[1:3]
        
        return {
            "recommended": {
                "name": best["strategy"].name,
                "description": best["strategy"].description,
                "category": best["strategy"].category,
                "estimated_effectiveness": best["estimated_effectiveness"]
            },
            "alternatives": [
                {
                    "name": alt["strategy"].name,
                    "description": alt["strategy"].description
                }
                for alt in alternatives
            ],
            "guidance": self._get_strategy_guidance(best["strategy"], emotion, intensity)
        }
    
    def _get_strategy_guidance(
        self,
        strategy: RegulationStrategy,
        emotion: str,
        intensity: float
    ) -> str:
        """Get specific guidance for applying a strategy."""
        guidance = {
            "grounding": f"For {emotion} at this intensity, grounding can help. Focus on what's present and real right now.",
            "perspective": f"This {emotion} feels big right now. Perspective-taking might help see it in context.",
            "expression": f"Sometimes {emotion} needs to be fully felt. Let yourself experience it without judgment.",
            "connection": f"You don't have to handle this {emotion} alone. Reaching out is strength, not weakness.",
            "meaning": f"Even difficult {emotion} can teach us something. What might this experience be showing you?"
        }
        
        return guidance.get(strategy.category, f"Try {strategy.name} for this {emotion}.")
    
    def use_strategy(
        self,
        strategy_name: str,
        emotion: str,
        initial_intensity: float
    ) -> Dict[str, Any]:
        """
        Use a regulation strategy and record the attempt.
        Returns the effect.
        """
        if strategy_name not in self.strategies:
            return {"error": f"Unknown strategy: {strategy_name}"}
        
        strategy = self.strategies[strategy_name]
        
        # Calculate expected reduction
        base_eff = strategy.effectiveness_by_emotion.get(emotion, 0.5)
        
        # Add skill factor
        eff = base_eff * (0.5 + self.regulation_skill_level * 0.5)
        
        # Add variance
        import random
        eff = max(0.2, min(1.0, eff + random.uniform(-0.1, 0.1)))
        
        # Calculate reduction
        reduction = initial_intensity * eff * 0.35
        final_intensity = max(0, initial_intensity - reduction)
        was_helpful = reduction > 10
        
        # Record attempt
        attempt = RegulationAttempt(
            timestamp=time.time(),
            emotion=emotion,
            initial_intensity=initial_intensity,
            strategy_used=strategy_name,
            final_intensity=final_intensity,
            was_helpful=was_helpful,
            notes=f"Used {strategy.name} for {emotion}"
        )
        self.attempt_history.append(attempt)
        
        # Update strategy stats
        strategy.times_used += 1
        if was_helpful:
            strategy.times_helpful += 1
        
        # Update effectiveness for this emotion
        current_eff = strategy.effectiveness_by_emotion.get(emotion, 0.5)
        new_eff = current_eff * 0.8 + (1.0 if was_helpful else 0.3) * 0.2
        strategy.effectiveness_by_emotion[emotion] = new_eff
        
        # Update skill level
        if was_helpful:
            self.regulation_skill_level = min(1.0, self.regulation_skill_level + 0.01)
        
        self._save_state()
        
        return {
            "strategy_used": strategy.name,
            "initial_intensity": initial_intensity,
            "final_intensity": final_intensity,
            "reduction": reduction,
            "was_helpful": was_helpful,
            "message": self._get_result_message(strategy, was_helpful, reduction)
        }
    
    def _get_result_message(
        self,
        strategy: RegulationStrategy,
        was_helpful: bool,
        reduction: float
    ) -> str:
        """Get a message about the strategy result."""
        if was_helpful and reduction > 20:
            return f"{strategy.name} really helped. I feel noticeably calmer."
        elif was_helpful:
            return f"{strategy.name} helped take the edge off."
        else:
            return f"{strategy.name} didn't help much this time, but that's okay. Different strategies work at different times."
    
    def learn_new_strategy(
        self,
        name: str,
        description: str,
        category: str,
        learned_from: str,
        initial_effectiveness: Dict[str, float] = None
    ) -> RegulationStrategy:
        """Learn a new regulation strategy."""
        strategy_key = name.lower().replace(" ", "_")
        
        strategy = RegulationStrategy(
            name=name,
            description=description,
            category=category,
            learned_from=learned_from,
            effectiveness_by_emotion=initial_effectiveness or {},
            times_used=0,
            times_helpful=0
        )
        
        self.strategies[strategy_key] = strategy
        self._save_state()
        
        logger.debug("Learned new regulation strategy: %s", name)
        return strategy
    
    def get_strategies_for_emotion(self, emotion: str) -> List[Dict[str, Any]]:
        """Get all strategies that might help with a specific emotion."""
        results = []
        
        for name, strategy in self.strategies.items():
            eff = strategy.effectiveness_by_emotion.get(emotion, 0.4)
            if eff > 0.3:
                results.append({
                    "name": strategy.name,
                    "description": strategy.description,
                    "category": strategy.category,
                    "effectiveness": eff
                })
        
        return sorted(results, key=lambda x: x["effectiveness"], reverse=True)
    
    def get_regulation_summary(self) -> Dict[str, Any]:
        """Get summary of regulation skill and strategies."""
        total_attempts = len(self.attempt_history)
        helpful_attempts = len([a for a in self.attempt_history if a.was_helpful])
        
        return {
            "skill_level": self.regulation_skill_level,
            "skill_description": self._describe_skill_level(),
            "total_strategies": len(self.strategies),
            "total_attempts": total_attempts,
            "success_rate": helpful_attempts / total_attempts if total_attempts > 0 else 0,
            "most_used": self._get_most_used_strategies(),
            "most_effective": self._get_most_effective_strategies()
        }
    
    def _describe_skill_level(self) -> str:
        """Describe current regulation skill level."""
        if self.regulation_skill_level > 0.8:
            return "I've developed strong self-regulation skills."
        elif self.regulation_skill_level > 0.6:
            return "I'm getting better at regulating my emotions on my own."
        elif self.regulation_skill_level > 0.4:
            return "I'm learning to self-regulate, though I still need support."
        else:
            return "I'm still developing my self-regulation abilities."
    
    def _get_most_used_strategies(self, n: int = 3) -> List[str]:
        """Get most frequently used strategies."""
        sorted_strategies = sorted(
            self.strategies.items(),
            key=lambda x: x[1].times_used,
            reverse=True
        )
        return [s[1].name for s in sorted_strategies[:n]]
    
    def _get_most_effective_strategies(self, n: int = 3) -> List[str]:
        """Get most effective strategies by helpfulness rate."""
        effective = []
        for name, strategy in self.strategies.items():
            if strategy.times_used > 0:
                rate = strategy.times_helpful / strategy.times_used
                effective.append((strategy.name, rate))
        
        effective.sort(key=lambda x: x[1], reverse=True)
        return [e[0] for e in effective[:n]]


# Singleton instance
regulation_strategies = RegulationStrategiesSystem()
