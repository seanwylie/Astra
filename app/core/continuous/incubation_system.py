# Astra Incubation System
# Problems solving themselves in the background
# The unconscious work that leads to insight

import time
import json
import random
import boto3
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from app.logging_config import get_logger

logger = get_logger("incubation_system")

S3_BUCKET = "swylie-astra"
INCUBATION_KEY = "incubation.json"

s3 = boto3.client("s3")


@dataclass
class IncubatingProblem:
    """A problem being incubated in the background."""
    id: str
    problem: str
    context: str
    submitted: float
    last_checked: float
    attempts: int
    current_angles: List[str]  # Current approaches being considered
    insights: List[Dict[str, Any]] = field(default_factory=list)
    resolved: bool = False
    resolution: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "IncubatingProblem":
        return cls(**data)


class IncubationSystem:
    """
    Incubation System - problems work themselves out in the background.
    
    Based on research showing that:
    - Stepping away from problems can lead to better solutions
    - Unconscious processing continues after conscious attention ends
    - Insights often arise unexpectedly after incubation
    
    This simulates the creative unconscious.
    """
    
    # Incubation strategies
    STRATEGIES = [
        "look_at_differently",  # Reframe the problem
        "find_analogies",  # Look for similar problems
        "relax_constraints",  # What if we didn't have to...?
        "combine_elements",  # What if we combined X and Y?
        "reverse_assumptions",  # What if the opposite were true?
        "simplify_radically",  # What's the core issue?
    ]
    
    def __init__(self):
        self.incubating: Dict[str, IncubatingProblem] = {}
        self.resolved_problems: List[IncubatingProblem] = []
        self._load_incubation_state()
        logger.info("💭 Incubation System initialized - problems gestating")
    
    def _load_incubation_state(self) -> None:
        """Load incubation state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=INCUBATION_KEY)
            data = json.load(response["Body"])
            
            self.incubating = {
                pid: IncubatingProblem.from_dict(p)
                for pid, p in data.get("incubating", {}).items()
            }
            self.resolved_problems = [
                IncubatingProblem.from_dict(p) for p in data.get("resolved", [])
            ]
            
            logger.info(f"💭 Loaded {len(self.incubating)} incubating problems")
        except s3.exceptions.NoSuchKey:
            logger.info("💭 No incubation state. Ready to receive problems.")
        except Exception as e:
            logger.warning(f"💭 Error loading incubation state: {e}")
    
    def _save_incubation_state(self) -> None:
        """Save incubation state to S3."""
        try:
            data = {
                "incubating": {pid: p.to_dict() for pid, p in self.incubating.items()},
                "resolved": [p.to_dict() for p in self.resolved_problems[-30:]],
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=INCUBATION_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"💭 Error saving incubation state: {e}")
    
    def _generate_id(self) -> str:
        return f"prob_{int(time.time() * 1000) % 1000000}"
    
    def submit_problem(self, problem: str, context: str = "") -> IncubatingProblem:
        """Submit a problem for incubation."""
        prob = IncubatingProblem(
            id=self._generate_id(),
            problem=problem,
            context=context,
            submitted=time.time(),
            last_checked=time.time(),
            attempts=0,
            current_angles=[random.choice(self.STRATEGIES)],
            insights=[],
            resolved=False
        )
        
        self.incubating[prob.id] = prob
        self._save_incubation_state()
        
        logger.info(f"💭 Problem submitted for incubation: {problem[:50]}...")
        return prob
    
    def incubate_step(self, problem_id: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Perform one step of incubation on a problem.
        
        Returns (made_progress, insight_if_any).
        """
        if problem_id not in self.incubating:
            return False, None
        
        prob = self.incubating[problem_id]
        prob.attempts += 1
        prob.last_checked = time.time()
        
        # Try current strategy
        strategy = prob.current_angles[-1] if prob.current_angles else random.choice(self.STRATEGIES)
        
        # Simulate incubation progress (in real implementation, would do actual reasoning)
        insight_chance = min(0.2 + (prob.attempts * 0.05), 0.5)  # Increases with attempts
        
        if random.random() < insight_chance:
            insight = self._generate_insight(prob, strategy)
            prob.insights.append(insight)
            
            self._save_incubation_state()
            logger.info(f"💭 💡 Insight generated for: {prob.problem[:30]}...")
            
            return True, insight
        
        # Try a different angle
        if prob.attempts % 3 == 0:
            new_strategy = random.choice([s for s in self.STRATEGIES if s not in prob.current_angles[-2:]])
            prob.current_angles.append(new_strategy)
        
        self._save_incubation_state()
        return False, None
    
    def _generate_insight(self, prob: IncubatingProblem, strategy: str) -> Dict[str, Any]:
        """Generate an insight based on the incubation strategy."""
        insight_templates = {
            "look_at_differently": f"What if '{prob.problem}' is actually about something else entirely?",
            "find_analogies": f"This reminds me of... perhaps the solution is analogous.",
            "relax_constraints": "What if we didn't need to satisfy all constraints?",
            "combine_elements": "There might be a way to combine seemingly incompatible approaches.",
            "reverse_assumptions": "What if our key assumption is wrong?",
            "simplify_radically": f"At its core, this might just be about: [fundamental insight]",
        }
        
        return {
            "timestamp": time.time(),
            "strategy": strategy,
            "insight": insight_templates.get(strategy, "A new perspective emerges..."),
            "problem_id": prob.id
        }
    
    # ========== Phase 5.1: Real Insight Generation ==========
    
    def generate_novel_connection(self) -> Optional[Dict[str, Any]]:
        """
        Generate genuine novel connections between stored knowledge.
        Implements Phase 5.1: Background Incubation with Real Emergence.
        
        Picks two knowledge entries and tries to find a meaningful connection.
        """
        try:
            from app.interfaces.mind_session import session
            mind_data = session.load()
            stored_knowledge = mind_data.get("stored_knowledge", [])
            
            if len(stored_knowledge) < 2:
                return None
            
            # Pick two random entries
            import random
            indices = random.sample(range(len(stored_knowledge)), 2)
            entry_a = stored_knowledge[indices[0]]
            entry_b = stored_knowledge[indices[1]]
            
            # Extract content
            content_a = entry_a.get("insight", str(entry_a)) if isinstance(entry_a, dict) else str(entry_a)
            content_b = entry_b.get("insight", str(entry_b)) if isinstance(entry_b, dict) else str(entry_b)
            
            # Check for keyword overlap (connection potential)
            words_a = set(content_a.lower().split())
            words_b = set(content_b.lower().split())
            
            # Remove common words
            stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "must", "shall", "can", "need", "dare", "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by", "from", "as", "into", "through", "during", "before", "after", "above", "below", "between", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "just", "and", "but", "or", "because", "until", "while", "of", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once"}
            
            words_a = words_a - stopwords
            words_b = words_b - stopwords
            
            overlap = words_a & words_b
            
            # Check for distant connection (more interesting than direct overlap)
            try:
                from app.core.epistemics.knowledge_map import knowledge_map
                
                # Get representative words
                repr_a = list(words_a)[:1][0] if words_a else ""
                repr_b = list(words_b)[:1][0] if words_b else ""
                
                if repr_a and repr_b:
                    distance = knowledge_map.is_distant_connection(repr_a, repr_b)
                    
                    # Distant connections are more valuable for insight
                    if distance > 0.5:
                        # Generate insight from connection
                        insight = self._formulate_connection_insight(content_a, content_b, overlap)
                        if insight:
                            return {
                                "timestamp": time.time(),
                                "type": "novel_connection",
                                "source_a": content_a[:50],
                                "source_b": content_b[:50],
                                "connection": insight,
                                "novelty_score": distance,
                                "bridging_concepts": list(overlap)[:3]
                            }
            except Exception as e:
                logger.debug(f"Knowledge map not available for distance: {e}")
            
            # Fall back to overlap-based connection
            if len(overlap) >= 2:
                insight = self._formulate_connection_insight(content_a, content_b, overlap)
                if insight:
                    return {
                        "timestamp": time.time(),
                        "type": "overlap_connection",
                        "source_a": content_a[:50],
                        "source_b": content_b[:50],
                        "connection": insight,
                        "novelty_score": 0.5,
                        "bridging_concepts": list(overlap)[:3]
                    }
            
            return None
            
        except Exception as e:
            logger.debug(f"Failed to generate novel connection: {e}")
            return None
    
    def _formulate_connection_insight(
        self,
        content_a: str,
        content_b: str,
        bridging: set
    ) -> Optional[str]:
        """Formulate an insight connecting two pieces of knowledge."""
        bridging_list = list(bridging)[:2]
        
        if not bridging_list:
            return None
        
        templates = [
            f"I notice a connection: both '{content_a[:30]}...' and '{content_b[:30]}...' touch on {', '.join(bridging_list)}. There might be a deeper pattern here.",
            f"Something interesting: {', '.join(bridging_list)} appears in multiple contexts I've learned about. This could be significant.",
            f"I'm seeing a thread between ideas I hadn't connected before—{', '.join(bridging_list)} links them.",
        ]
        
        import random
        return random.choice(templates)
    
    def incubate_for_insights(self) -> List[Dict[str, Any]]:
        """
        Run incubation process focused on generating novel insights.
        Called during idle processing.
        """
        insights = []
        
        # Process existing problems
        problem_insights = self.process_all()
        insights.extend(problem_insights)
        
        # Try to generate novel connections
        connection = self.generate_novel_connection()
        if connection:
            insights.append(connection)
            
            # Publish high-novelty insights to awareness bus
            if connection.get("novelty_score", 0) > 0.7:
                try:
                    from app.core.awareness_bus import awareness_bus
                    awareness_bus.publish("SPONTANEOUS_INSIGHT", {
                        "content": connection["connection"],
                        "source": "incubation",
                        "novelty": connection["novelty_score"]
                    })
                except Exception:
                    pass
        
        if insights:
            logger.info(f"💭 Incubation generated {len(insights)} insight(s)")
        
        return insights
    
    def resolve_problem(self, problem_id: str, resolution: str) -> bool:
        """Mark a problem as resolved."""
        if problem_id not in self.incubating:
            return False
        
        prob = self.incubating[problem_id]
        prob.resolved = True
        prob.resolution = resolution
        
        # Move to resolved
        self.resolved_problems.append(prob)
        del self.incubating[problem_id]
        
        self._save_incubation_state()
        logger.info(f"💭 ✅ Problem resolved: {prob.problem[:30]}...")
        
        return True
    
    def process_all(self) -> List[Dict[str, Any]]:
        """Process all incubating problems, returning any insights."""
        insights = []
        
        for prob_id in list(self.incubating.keys()):
            made_progress, insight = self.incubate_step(prob_id)
            if insight:
                insights.append(insight)
        
        return insights
    
    def check_for_insights(self) -> List[Dict[str, Any]]:
        """Check if any problems have generated insights."""
        all_insights = []
        
        for prob in self.incubating.values():
            for insight in prob.insights:
                all_insights.append({
                    "problem": prob.problem,
                    "insight": insight
                })
        
        return all_insights
    
    def get_oldest_problem(self) -> Optional[IncubatingProblem]:
        """Get the problem that's been incubating longest."""
        if not self.incubating:
            return None
        return min(self.incubating.values(), key=lambda p: p.submitted)
    
    def what_am_i_working_on(self) -> str:
        """Describe problems currently incubating."""
        if not self.incubating:
            return "I don't have any problems incubating right now."
        
        problems = list(self.incubating.values())
        descriptions = [p.problem[:40] for p in problems[:3]]
        
        return f"In the background, I'm working on: {'; '.join(descriptions)}..."
    
    def get_incubation_summary(self) -> Dict[str, Any]:
        """Get summary of incubation state."""
        return {
            "incubating_count": len(self.incubating),
            "resolved_count": len(self.resolved_problems),
            "total_insights": sum(len(p.insights) for p in self.incubating.values()),
            "oldest_problem_age": time.time() - min(p.submitted for p in self.incubating.values()) if self.incubating else 0,
        }


# Singleton instance
incubation_system = IncubationSystem()
