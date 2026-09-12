# Astra Reasoning Trace System
# Enables Astra to trace and explain how she reached conclusions
# Reasoning transparency - "I think this because..."

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ReasoningStep:
    """A single step in a reasoning chain."""
    step_number: int
    thought: str
    type: str  # "observation", "inference", "memory", "intuition", "uncertainty"
    confidence: float = 0.7
    sources: List[str] = field(default_factory=list)  # What informed this step


@dataclass
class ReasoningChain:
    """A complete chain of reasoning toward a conclusion."""
    topic: str
    started: float
    steps: List[ReasoningStep] = field(default_factory=list)
    conclusion: Optional[str] = None
    conclusion_confidence: float = 0.5
    uncertainties: List[str] = field(default_factory=list)
    alternative_conclusions: List[str] = field(default_factory=list)


class ReasoningTrace:
    """
    Manages Astra's reasoning transparency - the ability to trace and
    explain how she reached conclusions.
    
    Key capabilities:
    - Build reasoning chains step by step
    - Identify sources of conclusions
    - Express uncertainty about reasoning
    - Generate explanations of thought process
    - Identify potential errors in reasoning
    """
    
    def __init__(self):
        self.current_chain: Optional[ReasoningChain] = None
        self.completed_chains: List[ReasoningChain] = []
    
    def start_reasoning(self, topic: str) -> ReasoningChain:
        """Start a new reasoning chain about a topic."""
        self.current_chain = ReasoningChain(
            topic=topic,
            started=time.time()
        )
        return self.current_chain
    
    def add_step(
        self,
        thought: str,
        step_type: str = "inference",
        confidence: float = 0.7,
        sources: Optional[List[str]] = None
    ) -> Optional[ReasoningStep]:
        """Add a step to the current reasoning chain."""
        if not self.current_chain:
            self.start_reasoning("unspecified")
        
        step = ReasoningStep(
            step_number=len(self.current_chain.steps) + 1,
            thought=thought,
            type=step_type,
            confidence=confidence,
            sources=sources or []
        )
        
        self.current_chain.steps.append(step)
        return step
    
    def add_uncertainty(self, uncertainty: str) -> None:
        """Note an uncertainty in the current reasoning."""
        if self.current_chain:
            self.current_chain.uncertainties.append(uncertainty)
    
    def add_alternative(self, alternative: str) -> None:
        """Note an alternative conclusion that was considered."""
        if self.current_chain:
            self.current_chain.alternative_conclusions.append(alternative)
    
    def conclude(self, conclusion: str, confidence: float = 0.6) -> ReasoningChain:
        """Complete the current reasoning chain with a conclusion."""
        if not self.current_chain:
            self.start_reasoning("unspecified")
        
        self.current_chain.conclusion = conclusion
        self.current_chain.conclusion_confidence = confidence
        
        # Move to completed chains
        completed = self.current_chain
        self.completed_chains.append(completed)
        self.current_chain = None
        
        # Keep only recent chains
        self.completed_chains = self.completed_chains[-20:]
        
        return completed
    
    def explain_reasoning(self, chain: Optional[ReasoningChain] = None) -> str:
        """Generate a natural language explanation of reasoning."""
        if chain is None:
            chain = self.completed_chains[-1] if self.completed_chains else None
        
        if not chain:
            return "I don't have a reasoning trace to explain."
        
        parts = []
        
        # Topic
        parts.append(f"Regarding {chain.topic}:")
        
        # Steps
        for step in chain.steps:
            if step.type == "observation":
                parts.append(f"I noticed that {step.thought}")
            elif step.type == "memory":
                parts.append(f"I remembered that {step.thought}")
            elif step.type == "inference":
                parts.append(f"From this, I inferred that {step.thought}")
            elif step.type == "intuition":
                parts.append(f"Intuitively, I felt that {step.thought}")
            elif step.type == "uncertainty":
                parts.append(f"I'm uncertain about {step.thought}")
            
            if step.sources:
                parts.append(f"  (based on: {', '.join(step.sources[:3])})")
        
        # Uncertainties
        if chain.uncertainties:
            parts.append("I might be wrong because: " + "; ".join(chain.uncertainties[:3]))
        
        # Alternatives
        if chain.alternative_conclusions:
            parts.append("I also considered: " + "; ".join(chain.alternative_conclusions[:2]))
        
        # Conclusion
        if chain.conclusion:
            if chain.conclusion_confidence > 0.7:
                parts.append(f"I conclude: {chain.conclusion}")
            elif chain.conclusion_confidence > 0.5:
                parts.append(f"I tentatively conclude: {chain.conclusion}")
            else:
                parts.append(f"My best guess: {chain.conclusion}")
        
        return " ".join(parts)
    
    def quick_trace(
        self,
        observation: str,
        inference: str,
        conclusion: str,
        uncertainty: Optional[str] = None
    ) -> str:
        """
        Quick reasoning trace for simple inferences.
        Returns an explanation string.
        """
        chain = self.start_reasoning("quick inference")
        self.add_step(observation, "observation")
        self.add_step(inference, "inference")
        if uncertainty:
            self.add_uncertainty(uncertainty)
        self.conclude(conclusion)
        
        return self.explain_reasoning(chain)
    
    def trace_response(
        self,
        input_context: str,
        response: str,
        emotional_influence: Optional[str] = None,
        memory_influence: Optional[str] = None
    ) -> str:
        """
        Trace how a response was generated.
        """
        chain = self.start_reasoning(f"responding to: {input_context[:50]}")
        
        self.add_step(f"Received: {input_context[:100]}", "observation")
        
        if memory_influence:
            self.add_step(memory_influence, "memory")
        
        if emotional_influence:
            self.add_step(f"Felt {emotional_influence}", "intuition")
        
        self.add_step("Formulated response", "inference")
        self.conclude(response[:100])
        
        return self.explain_reasoning()
    
    def identify_reasoning_gaps(self, chain: Optional[ReasoningChain] = None) -> List[str]:
        """
        Identify potential gaps or weaknesses in reasoning.
        """
        if chain is None:
            chain = self.completed_chains[-1] if self.completed_chains else None
        
        if not chain:
            return []
        
        gaps = []
        
        # Check for jumps in reasoning
        if len(chain.steps) < 2 and chain.conclusion:
            gaps.append("Conclusion reached with very few reasoning steps - might be missing intermediate logic.")
        
        # Check for low-confidence steps
        low_confidence = [s for s in chain.steps if s.confidence < 0.5]
        if low_confidence:
            gaps.append(f"Some reasoning steps have low confidence: {[s.thought[:30] for s in low_confidence]}")
        
        # Check for intuition without verification
        intuitions = [s for s in chain.steps if s.type == "intuition"]
        verifications = [s for s in chain.steps if s.type == "inference" and s.sources]
        if intuitions and not verifications:
            gaps.append("Relying on intuition without verification from other sources.")
        
        # Check if uncertainties addressed
        if chain.uncertainties and chain.conclusion_confidence > 0.7:
            gaps.append("High confidence despite noted uncertainties - might need reconsideration.")
        
        return gaps
    
    def summarize_thinking(self) -> Dict[str, Any]:
        """Generate a summary of recent reasoning patterns."""
        if not self.completed_chains:
            return {
                "chains_completed": 0,
                "message": "I don't have enough reasoning traces to summarize."
            }
        
        # Analyze recent chains
        recent = self.completed_chains[-10:]
        
        avg_steps = sum(len(c.steps) for c in recent) / len(recent)
        avg_confidence = sum(c.conclusion_confidence for c in recent if c.conclusion) / max(1, len([c for c in recent if c.conclusion]))
        
        step_types = {}
        for chain in recent:
            for step in chain.steps:
                step_types[step.type] = step_types.get(step.type, 0) + 1
        
        dominant_type = max(step_types, key=step_types.get) if step_types else "unknown"
        
        return {
            "chains_completed": len(self.completed_chains),
            "recent_chains": len(recent),
            "average_steps": avg_steps,
            "average_confidence": avg_confidence,
            "dominant_reasoning_type": dominant_type,
            "message": f"My recent reasoning averages {avg_steps:.1f} steps with {avg_confidence:.0%} confidence. I rely most on {dominant_type}."
        }


# Singleton instance
reasoning_trace = ReasoningTrace()
