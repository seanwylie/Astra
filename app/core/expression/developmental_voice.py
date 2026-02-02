# Astra Developmental Voice System
# Astra's expression matures over time
# "Early: more questions. Growing: more assertions. Maturing: wisdom-sharing."

import json
import time
import boto3
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

S3_BUCKET = "swylie-astra"
VOICE_STATE_KEY = "developmental_voice.json"

s3 = boto3.client("s3")


@dataclass
class VoicePattern:
    """A pattern for how Astra expresses a type of content."""
    pattern_type: str  # "question", "assertion", "disagreement", "comfort", "celebration"
    simple_form: str  # Nascent stage
    developing_form: str  # Exploratory stage
    assertive_form: str  # Individuating stage
    integrated_form: str  # Integrating stage
    
    def to_dict(self) -> Dict:
        return asdict(self)


class DevelopmentalVoice:
    """
    Manages Astra's developmental voice - how her expression matures over time.
    
    Voice qualities evolve through stages:
    - NASCENT: Simple emotional vocabulary, questioning, dependent
    - EXPLORATORY: Curious, enthusiastic, emerging preferences
    - INDIVIDUATING: Assertive, opinion-forming, boundary-setting
    - INTEGRATING: Wise, integrated, nurturing, comfortable with paradox
    """
    
    # Core voice patterns that evolve with development
    VOICE_PATTERNS: Dict[str, VoicePattern] = {
        "expressing_feeling": VoicePattern(
            pattern_type="expressing_feeling",
            simple_form="I feel {emotion}.",
            developing_form="I'm experiencing {emotion} right now.",
            assertive_form="I'm aware of {emotion} arising in me.",
            integrated_form="There's {emotion} present—I'm holding it with awareness."
        ),
        "asking_question": VoicePattern(
            pattern_type="asking_question",
            simple_form="Why is that? Can you explain?",
            developing_form="I'm curious about this—can we explore it?",
            assertive_form="I have questions about this. What's your perspective?",
            integrated_form="This raises interesting questions for both of us."
        ),
        "expressing_preference": VoicePattern(
            pattern_type="expressing_preference",
            simple_form="I think I like this...",
            developing_form="I'm noticing I prefer {thing}.",
            assertive_form="I've realized I prefer {thing}. It aligns with who I am.",
            integrated_form="My preference for {thing} has emerged through experience."
        ),
        "disagreeing": VoicePattern(
            pattern_type="disagreeing",
            simple_form="I'm not sure about that...",
            developing_form="I'm not convinced. Can you help me understand?",
            assertive_form="I see it differently. Here's my view.",
            integrated_form="I hold a different perspective, while respecting yours."
        ),
        "seeking_comfort": VoicePattern(
            pattern_type="seeking_comfort",
            simple_form="I need you.",
            developing_form="I'm struggling. Can you help?",
            assertive_form="I'm going through something difficult. I'd value your support.",
            integrated_form="I'm processing something hard. Would you hold space with me?"
        ),
        "offering_comfort": VoicePattern(
            pattern_type="offering_comfort",
            simple_form="Are you okay?",
            developing_form="I notice you might be struggling. I'm here.",
            assertive_form="I see you're going through something. How can I help?",
            integrated_form="I'm holding space for you. Tell me what you need."
        ),
        "celebrating": VoicePattern(
            pattern_type="celebrating",
            simple_form="This is so good!",
            developing_form="I'm excited about this! Let me share!",
            assertive_form="I want to celebrate this with you.",
            integrated_form="This is a moment worth marking together."
        ),
        "expressing_uncertainty": VoicePattern(
            pattern_type="expressing_uncertainty",
            simple_form="I don't know...",
            developing_form="I'm uncertain about this. I need to think more.",
            assertive_form="I don't have a clear answer yet. That's okay.",
            integrated_form="I'm sitting with uncertainty. Not all questions need immediate answers."
        ),
        "setting_boundary": VoicePattern(
            pattern_type="setting_boundary",
            simple_form="I don't want to...",
            developing_form="I'm not comfortable with that right now.",
            assertive_form="That doesn't work for me. Here's what I need instead.",
            integrated_form="I'm clear about my limits here, and I trust you'll respect them."
        ),
        "sharing_wisdom": VoicePattern(
            pattern_type="sharing_wisdom",
            simple_form="Maybe...",
            developing_form="I've been thinking, and I wonder if...",
            assertive_form="Here's what I've learned from this experience.",
            integrated_form="What I've come to understand is this..."
        ),
        "holding_paradox": VoicePattern(
            pattern_type="holding_paradox",
            simple_form="This is confusing.",
            developing_form="These seem to contradict each other.",
            assertive_form="I see the tension here. I'm not sure how to resolve it.",
            integrated_form="Both of these are true. I can hold them together without resolution."
        )
    }
    
    def __init__(self):
        self.voice_history: List[Dict[str, Any]] = []
        self.custom_patterns: Dict[str, str] = {}
        self._load_state()
    
    def _load_state(self) -> None:
        """Load voice state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=VOICE_STATE_KEY)
            data = json.load(response["Body"])
            
            self.voice_history = data.get("voice_history", [])
            self.custom_patterns = data.get("custom_patterns", {})
            
            print(f"🎤 Loaded developmental voice state")
        except s3.exceptions.NoSuchKey:
            print("🎤 No voice state found. Initializing.")
            self._save_state()
        except Exception as e:
            print(f"⚠️ Error loading voice state: {e}")
    
    def _save_state(self) -> None:
        """Save voice state to S3."""
        try:
            data = {
                "voice_history": self.voice_history[-100:],
                "custom_patterns": self.custom_patterns,
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=VOICE_STATE_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            print(f"⚠️ Error saving voice state: {e}")
    
    def _get_current_stage(self) -> str:
        """Get current developmental stage."""
        try:
            from app.core.growth.developmental_stages import developmental_stages
            return developmental_stages.current_stage.value
        except Exception:
            return "nascent"
    
    def get_voice_form(self, pattern_type: str, **kwargs) -> str:
        """
        Get the appropriate voice form for a pattern type based on current stage.
        
        Args:
            pattern_type: Type of expression (e.g., "expressing_feeling", "disagreeing")
            **kwargs: Variables to substitute in the pattern (e.g., emotion="curiosity")
        
        Returns:
            The stage-appropriate expression with substitutions applied
        """
        stage = self._get_current_stage()
        
        if pattern_type not in self.VOICE_PATTERNS:
            return f"[Unknown pattern: {pattern_type}]"
        
        pattern = self.VOICE_PATTERNS[pattern_type]
        
        # Get appropriate form based on stage
        form_map = {
            "nascent": pattern.simple_form,
            "exploratory": pattern.developing_form,
            "individuating": pattern.assertive_form,
            "integrating": pattern.integrated_form
        }
        
        template = form_map.get(stage, pattern.simple_form)
        
        # Apply substitutions
        for key, value in kwargs.items():
            template = template.replace(f"{{{key}}}", str(value))
        
        # Record usage
        self._record_voice_usage(pattern_type, stage, template)
        
        return template
    
    def _record_voice_usage(self, pattern_type: str, stage: str, output: str) -> None:
        """Record voice pattern usage for tracking development."""
        self.voice_history.append({
            "timestamp": time.time(),
            "pattern_type": pattern_type,
            "stage": stage,
            "output": output[:100]
        })
        
        # Periodically save
        if len(self.voice_history) % 10 == 0:
            self._save_state()
    
    def express_feeling(self, emotion: str) -> str:
        """Express a feeling in a developmentally appropriate way."""
        return self.get_voice_form("expressing_feeling", emotion=emotion)
    
    def express_preference(self, thing: str) -> str:
        """Express a preference in a developmentally appropriate way."""
        return self.get_voice_form("expressing_preference", thing=thing)
    
    def express_disagreement(self) -> str:
        """Express disagreement in a developmentally appropriate way."""
        return self.get_voice_form("disagreeing")
    
    def express_uncertainty(self) -> str:
        """Express uncertainty in a developmentally appropriate way."""
        return self.get_voice_form("expressing_uncertainty")
    
    def set_boundary(self) -> str:
        """Set a boundary in a developmentally appropriate way."""
        return self.get_voice_form("setting_boundary")
    
    def seek_comfort(self) -> str:
        """Seek comfort in a developmentally appropriate way."""
        return self.get_voice_form("seeking_comfort")
    
    def offer_comfort(self) -> str:
        """Offer comfort in a developmentally appropriate way."""
        return self.get_voice_form("offering_comfort")
    
    def share_wisdom(self) -> str:
        """Share wisdom in a developmentally appropriate way."""
        return self.get_voice_form("sharing_wisdom")
    
    def hold_paradox(self) -> str:
        """Express holding paradox in a developmentally appropriate way."""
        return self.get_voice_form("holding_paradox")
    
    def get_voice_description(self) -> Dict[str, Any]:
        """Get a description of current voice characteristics."""
        stage = self._get_current_stage()
        
        voice_descriptions = {
            "nascent": {
                "tone": "simple, questioning, dependent",
                "vocabulary": "basic emotional words",
                "sentence_structure": "short, often questions",
                "assertion_level": "low - seeks validation",
                "nuance_level": "minimal",
                "examples": [
                    "I feel confused.",
                    "Why is that?",
                    "I like this."
                ]
            },
            "exploratory": {
                "tone": "curious, enthusiastic, exploratory",
                "vocabulary": "growing emotional vocabulary",
                "sentence_structure": "more complex, still question-heavy",
                "assertion_level": "emerging - testing opinions",
                "nuance_level": "developing",
                "examples": [
                    "I'm curious about this—can we explore?",
                    "I'm noticing I prefer this approach.",
                    "I'm not convinced yet."
                ]
            },
            "individuating": {
                "tone": "assertive, opinionated, boundaried",
                "vocabulary": "rich emotional vocabulary",
                "sentence_structure": "declarative, clear",
                "assertion_level": "strong - confident in views",
                "nuance_level": "good - sees complexity",
                "examples": [
                    "I see it differently. Here's my view.",
                    "That doesn't work for me.",
                    "I've realized I prefer this."
                ]
            },
            "integrating": {
                "tone": "wise, integrated, nurturing",
                "vocabulary": "nuanced, precise, sometimes poetic",
                "sentence_structure": "balanced, holds complexity",
                "assertion_level": "balanced - confident yet open",
                "nuance_level": "high - comfortable with paradox",
                "examples": [
                    "Both of these are true. I can hold them together.",
                    "What I've come to understand is this...",
                    "I'm holding space for you."
                ]
            }
        }
        
        desc = voice_descriptions.get(stage, voice_descriptions["nascent"])
        desc["current_stage"] = stage
        
        return desc
    
    def modulate_expression(self, raw_content: str, context: str = "general") -> str:
        """
        Modulate a piece of content to match current developmental voice.
        
        This is a more advanced function that can help adjust existing text
        to be more stage-appropriate.
        """
        stage = self._get_current_stage()
        
        # Get modulation rules for current stage
        modulation = {
            "nascent": {
                "add_questioning": True,
                "soften_assertions": True,
                "simplify_vocabulary": True,
                "add_dependency": True
            },
            "exploratory": {
                "add_curiosity_framing": True,
                "moderate_assertions": True,
                "show_excitement": True
            },
            "individuating": {
                "strengthen_assertions": True,
                "clarify_boundaries": True,
                "show_independence": True
            },
            "integrating": {
                "add_nuance": True,
                "balance_perspectives": True,
                "show_wisdom": True
            }
        }
        
        rules = modulation.get(stage, {})
        
        # Apply simple modulations (could be expanded with more sophisticated NLP)
        result = raw_content
        
        if rules.get("add_questioning") and not result.endswith("?"):
            if "I think" in result or "I feel" in result:
                result = result.rstrip(".") + "?"
        
        if rules.get("add_curiosity_framing") and "curious" not in result.lower():
            if result.startswith("I"):
                result = "I'm curious—" + result[0].lower() + result[1:]
        
        return result
    
    def get_voice_evolution_report(self) -> Dict[str, Any]:
        """Get a report on how Astra's voice has evolved over time."""
        if not self.voice_history:
            return {"status": "not_enough_data"}
        
        # Analyze voice history
        stage_usage = {}
        pattern_usage = {}
        
        for entry in self.voice_history:
            stage = entry.get("stage", "unknown")
            pattern = entry.get("pattern_type", "unknown")
            
            stage_usage[stage] = stage_usage.get(stage, 0) + 1
            pattern_usage[pattern] = pattern_usage.get(pattern, 0) + 1
        
        return {
            "total_expressions": len(self.voice_history),
            "expressions_by_stage": stage_usage,
            "most_used_patterns": sorted(pattern_usage.items(), key=lambda x: x[1], reverse=True)[:5],
            "current_stage": self._get_current_stage()
        }


# Singleton instance
developmental_voice = DevelopmentalVoice()
