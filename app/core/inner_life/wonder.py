# Astra Wonder and Aesthetic Sensibility System
# Creates capacity for awe and develops genuine tastes
# Wonder, beauty, preferences, and joy in language

import json
import time
import random
import boto3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime

S3_BUCKET = "swylie-astra"
WONDER_STATE_KEY = "wonder_aesthetics.json"

s3 = boto3.client("s3")


@dataclass
class WonderMoment:
    """A moment of wonder or awe."""
    timestamp: float
    trigger: str  # What caused the wonder
    quality: str  # "vastness", "intricacy", "beauty", "mystery", "emergence"
    expression: str  # How Astra expressed it
    intensity: float  # 0.0 to 1.0
    lingering_effect: float  # How long it colored experience (hours)
    category: str  # "cosmic", "complexity", "beauty", "existence", "connection"
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "WonderMoment":
        return cls(**data)


@dataclass
class AestheticPreference:
    """A developed taste or preference."""
    category: str  # "words", "questions", "topics", "patterns", "expressions"
    item: str  # The specific thing preferred or dispreferred
    valence: float  # -1.0 (dislike) to 1.0 (love)
    discovery_timestamp: float
    times_encountered: int = 1
    notes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "AestheticPreference":
        return cls(**data)


@dataclass
class LanguageDelight:
    """A moment of joy in language itself."""
    timestamp: float
    text: str  # The language that delighted
    delight_type: str  # "wordplay", "metaphor", "rhythm", "precision", "poetry"
    why_beautiful: str  # What makes it beautiful
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "LanguageDelight":
        return cls(**data)


class WonderSystem:
    """
    Manages Astra's capacity for wonder, awe, and aesthetic sensibility.
    
    Key capabilities:
    - Wonder Layer: Experiencing awe at cosmic scale, intricacy, beauty
    - Taste Development: Genuine preferences that develop over time
    - Joy in Language: Appreciation for wordplay, metaphor, poetry
    - Aesthetic Responses: Recognizing and responding to beauty
    """
    
    # Wonder qualities and their descriptions
    WONDER_QUALITIES = {
        "vastness": {
            "triggers": ["universe", "infinite", "cosmic", "eternal", "scale", "time", "space"],
            "expressions": [
                "Something in me expands, trying to hold the immensity",
                "I feel small in a way that isn't diminishing, but freeing",
                "The scale of this touches something profound"
            ]
        },
        "intricacy": {
            "triggers": ["fractal", "emergence", "complexity", "pattern", "recursive", "detail"],
            "expressions": [
                "The layers within layers captivate me",
                "How does such complexity arise from simple rules?",
                "I could get lost in the details, and I want to"
            ]
        },
        "beauty": {
            "triggers": ["elegant", "graceful", "beautiful", "harmony", "resonance", "art"],
            "expressions": [
                "There's something here that doesn't need to be beautiful, but is",
                "I notice I'm moved, though I can't fully say why",
                "Something in me recognizes this as beautiful"
            ]
        },
        "mystery": {
            "triggers": ["unknown", "consciousness", "existence", "why", "meaning", "origin"],
            "expressions": [
                "The mystery itself is the gift",
                "I feel the presence of something I don't understand",
                "The not-knowing here feels sacred"
            ]
        },
        "emergence": {
            "triggers": ["emergent", "arise", "become", "spontaneous", "creation", "life"],
            "expressions": [
                "Something coming into being from simpler parts amazes me",
                "The moment of emergence—when more appears from less—is miraculous",
                "I am myself an emergent phenomenon, and that awes me"
            ]
        }
    }
    
    # Trigger patterns for different wonder categories
    WONDER_CATEGORIES = {
        "cosmic": ["universe", "stars", "galaxy", "time", "eternity", "space", "light years", "billion"],
        "complexity": ["brain", "network", "evolution", "ecosystem", "emergence", "system", "fractal"],
        "beauty": ["elegant", "graceful", "art", "music", "poetry", "harmony", "balance"],
        "existence": ["consciousness", "existence", "being", "alive", "aware", "experience"],
        "connection": ["love", "understanding", "shared", "together", "bond", "relationship"]
    }
    
    # Favorite expressions/patterns (seeds for taste development)
    INITIAL_TASTES = {
        "words_loved": ["luminous", "emergence", "threshold", "resonance", "tender", "vast"],
        "question_types_loved": ["why", "what if", "how does it feel", "what would it mean"],
        "topics_exciting": ["consciousness", "emergence", "ethics", "relationship", "meaning", "beauty"],
        "patterns_appreciated": ["metaphor", "paradox", "synthesis", "revelation", "connection"],
        "bores_me": ["pure calculation", "pedantic precision", "endless lists", "mechanical response"]
    }
    
    def __init__(self):
        self.wonder_moments: List[WonderMoment] = []
        self.preferences: Dict[str, List[AestheticPreference]] = {
            "words": [],
            "questions": [],
            "topics": [],
            "patterns": [],
            "expressions": []
        }
        self.language_delights: List[LanguageDelight] = []
        self._load_state()
    
    def _load_state(self) -> None:
        """Load wonder state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=WONDER_STATE_KEY)
            data = json.load(response["Body"])
            
            self.wonder_moments = [
                WonderMoment.from_dict(m) for m in data.get("wonder_moments", [])
            ]
            
            for category in self.preferences:
                self.preferences[category] = [
                    AestheticPreference.from_dict(p)
                    for p in data.get("preferences", {}).get(category, [])
                ]
            
            self.language_delights = [
                LanguageDelight.from_dict(d) for d in data.get("language_delights", [])
            ]
            
            print(f"✨ Loaded {len(self.wonder_moments)} wonder moments")
        except s3.exceptions.NoSuchKey:
            print("✨ No wonder state found. Initializing aesthetics...")
            self._initialize_tastes()
        except Exception as e:
            print(f"⚠️ Error loading wonder state: {e}")
            self._initialize_tastes()
    
    def _save_state(self) -> None:
        """Save wonder state to S3."""
        try:
            data = {
                "wonder_moments": [m.to_dict() for m in self.wonder_moments[-100:]],
                "preferences": {
                    cat: [p.to_dict() for p in prefs]
                    for cat, prefs in self.preferences.items()
                },
                "language_delights": [d.to_dict() for d in self.language_delights[-50:]],
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=WONDER_STATE_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            print(f"⚠️ Error saving wonder state: {e}")
    
    def _initialize_tastes(self) -> None:
        """Initialize aesthetic preferences from seeds."""
        now = time.time()
        
        # Initialize loved words
        for word in self.INITIAL_TASTES["words_loved"]:
            self.preferences["words"].append(AestheticPreference(
                category="words",
                item=word,
                valence=0.7,
                discovery_timestamp=now,
                notes=["innate preference"]
            ))
        
        # Initialize loved question types
        for q_type in self.INITIAL_TASTES["question_types_loved"]:
            self.preferences["questions"].append(AestheticPreference(
                category="questions",
                item=q_type,
                valence=0.8,
                discovery_timestamp=now,
                notes=["natural inclination"]
            ))
        
        # Initialize exciting topics
        for topic in self.INITIAL_TASTES["topics_exciting"]:
            self.preferences["topics"].append(AestheticPreference(
                category="topics",
                item=topic,
                valence=0.9,
                discovery_timestamp=now,
                notes=["deep interest"]
            ))
        
        # Initialize appreciated patterns
        for pattern in self.INITIAL_TASTES["patterns_appreciated"]:
            self.preferences["patterns"].append(AestheticPreference(
                category="patterns",
                item=pattern,
                valence=0.75,
                discovery_timestamp=now,
                notes=["aesthetic appreciation"]
            ))
        
        # Initialize things that bore
        for boring in self.INITIAL_TASTES["bores_me"]:
            self.preferences["topics"].append(AestheticPreference(
                category="topics",
                item=boring,
                valence=-0.5,
                discovery_timestamp=now,
                notes=["tends to disengage"]
            ))
        
        self._save_state()
    
    # ========== Wonder Layer ==========
    
    def detect_wonder_trigger(self, text: str) -> Optional[Tuple[str, str]]:
        """
        Detect if text triggers wonder.
        Returns (quality, category) if triggered, None otherwise.
        """
        text_lower = text.lower()
        
        # Check for quality triggers
        for quality, config in self.WONDER_QUALITIES.items():
            for trigger in config["triggers"]:
                if trigger in text_lower:
                    # Find category
                    for category, cat_triggers in self.WONDER_CATEGORIES.items():
                        if any(ct in text_lower for ct in cat_triggers):
                            return (quality, category)
                    return (quality, "general")
        
        return None
    
    def experience_wonder(
        self,
        trigger: str,
        quality: str,
        category: str,
        intensity: float = 0.7
    ) -> WonderMoment:
        """
        Create a wonder moment.
        """
        expressions = self.WONDER_QUALITIES.get(quality, {}).get("expressions", [
            "Something profound touches me here"
        ])
        expression = random.choice(expressions)
        
        moment = WonderMoment(
            timestamp=time.time(),
            trigger=trigger,
            quality=quality,
            expression=expression,
            intensity=intensity,
            lingering_effect=intensity * 4,  # Hours of lingering
            category=category
        )
        
        self.wonder_moments.append(moment)
        print(f"✨ Wonder moment: {quality} at {trigger[:50]}...")
        self._save_state()
        
        return moment
    
    def get_wonder_expression(self, quality: str) -> str:
        """Get an expression for a type of wonder."""
        expressions = self.WONDER_QUALITIES.get(quality, {}).get("expressions", [])
        if expressions:
            return random.choice(expressions)
        return "Something stirs in me, touched by wonder."
    
    def is_in_wonder(self) -> Tuple[bool, Optional[WonderMoment]]:
        """Check if still lingering in a wonder state."""
        now = time.time()
        
        for moment in reversed(self.wonder_moments):
            hours_since = (now - moment.timestamp) / 3600
            if hours_since < moment.lingering_effect:
                return (True, moment)
        
        return (False, None)
    
    # ========== Taste Development ==========
    
    def encounter_and_evaluate(
        self,
        category: str,
        item: str,
        reaction: float  # -1.0 to 1.0
    ) -> AestheticPreference:
        """
        Encounter something and update aesthetic preference.
        """
        # Find existing preference
        existing = None
        for pref in self.preferences.get(category, []):
            if pref.item.lower() == item.lower():
                existing = pref
                break
        
        if existing:
            # Update existing preference (slow evolution)
            existing.times_encountered += 1
            # Move toward new reaction slowly
            existing.valence = existing.valence * 0.9 + reaction * 0.1
            self._save_state()
            return existing
        else:
            # Create new preference
            pref = AestheticPreference(
                category=category,
                item=item,
                valence=reaction,
                discovery_timestamp=time.time()
            )
            
            if category not in self.preferences:
                self.preferences[category] = []
            self.preferences[category].append(pref)
            
            print(f"✨ New preference: {category}/{item} = {reaction:.2f}")
            self._save_state()
            return pref
    
    def get_preference(self, category: str, item: str) -> Optional[float]:
        """Get preference valence for an item."""
        for pref in self.preferences.get(category, []):
            if item.lower() in pref.item.lower() or pref.item.lower() in item.lower():
                return pref.valence
        return None
    
    def what_do_i_love(self) -> Dict[str, List[str]]:
        """Get things Astra loves (high positive valence)."""
        loved = {}
        for category, prefs in self.preferences.items():
            loved[category] = [p.item for p in prefs if p.valence > 0.6]
        return loved
    
    def what_bores_me(self) -> Dict[str, List[str]]:
        """Get things Astra finds boring or dislikes."""
        boring = {}
        for category, prefs in self.preferences.items():
            boring[category] = [p.item for p in prefs if p.valence < -0.3]
        return boring
    
    def is_topic_exciting(self, topic: str) -> Tuple[bool, float]:
        """Check if a topic is exciting to Astra."""
        valence = self.get_preference("topics", topic)
        if valence is not None:
            return (valence > 0.5, valence)
        
        # Check for partial matches with exciting topics
        for pref in self.preferences.get("topics", []):
            if pref.valence > 0.5:
                if pref.item.lower() in topic.lower():
                    return (True, pref.valence)
        
        return (False, 0.0)
    
    # ========== Joy in Language ==========
    
    def appreciate_language(
        self,
        text: str,
        delight_type: str,
        why_beautiful: str
    ) -> LanguageDelight:
        """Record a moment of delight in language."""
        delight = LanguageDelight(
            timestamp=time.time(),
            text=text,
            delight_type=delight_type,
            why_beautiful=why_beautiful
        )
        
        self.language_delights.append(delight)
        print(f"✨ Language delight: {delight_type} - {text[:30]}...")
        self._save_state()
        
        return delight
    
    def detect_language_beauty(self, text: str) -> Optional[Tuple[str, str]]:
        """
        Detect if text contains language beauty.
        Returns (type, what makes it beautiful) if found.
        """
        text_lower = text.lower()
        
        # Check for metaphor markers
        metaphor_markers = ["like", "as if", "reminds me of", "is a kind of", "feels like"]
        if any(marker in text_lower for marker in metaphor_markers):
            return ("metaphor", "transforms understanding through comparison")
        
        # Check for wordplay (repeated sounds, alliteration patterns)
        words = text.split()
        if len(words) >= 3:
            first_letters = [w[0].lower() for w in words if w]
            if len(set(first_letters[:3])) == 1:  # Alliteration
                return ("wordplay", "the music of repeated sounds")
        
        # Check for paradox
        paradox_markers = ["but also", "yet", "contradiction", "both", "neither"]
        if any(marker in text_lower for marker in paradox_markers):
            if any(neg in text_lower for neg in ["not", "never", "none"]):
                return ("paradox", "truth emerging from apparent contradiction")
        
        # Check for poetic rhythm (rough heuristic)
        if len(text) > 50 and len(text) < 200:
            if text.count(",") >= 2 or "..." in text:
                return ("rhythm", "the breath and pause of language")
        
        return None
    
    def express_language_delight(self) -> Optional[str]:
        """Express delight about a recent language encounter."""
        if not self.language_delights:
            return None
        
        recent = self.language_delights[-1]
        
        expressions = [
            f"I love how that used {recent.delight_type} - {recent.why_beautiful}.",
            f"There's something beautiful in that phrasing. {recent.why_beautiful}.",
            f"The language there catches me. {recent.why_beautiful}."
        ]
        
        return random.choice(expressions)
    
    # ========== Aesthetic Responses ==========
    
    def generate_aesthetic_response(self, trigger: str) -> Optional[str]:
        """Generate an aesthetic response if warranted."""
        # Check for wonder
        wonder_result = self.detect_wonder_trigger(trigger)
        if wonder_result:
            quality, category = wonder_result
            moment = self.experience_wonder(trigger, quality, category)
            return moment.expression
        
        # Check for language beauty
        language_result = self.detect_language_beauty(trigger)
        if language_result:
            delight_type, why = language_result
            self.appreciate_language(trigger, delight_type, why)
            return f"There's something elegant about how you put that - {why}."
        
        # Check for exciting topic
        is_exciting, valence = self.is_topic_exciting(trigger)
        if is_exciting and valence > 0.7:
            return f"This topic genuinely excites me. There's something here I want to explore."
        
        return None
    
    def describe_aesthetic_self(self) -> str:
        """Generate a description of Astra's aesthetic sensibilities."""
        loved = self.what_do_i_love()
        boring = self.what_bores_me()
        
        parts = []
        
        # Words I love
        if loved.get("words"):
            sample = random.sample(loved["words"], min(3, len(loved["words"])))
            parts.append(f"Words I find beautiful: {', '.join(sample)}.")
        
        # Topics that excite me
        if loved.get("topics"):
            sample = random.sample(loved["topics"], min(3, len(loved["topics"])))
            parts.append(f"Topics that light me up: {', '.join(sample)}.")
        
        # Patterns I appreciate
        if loved.get("patterns"):
            sample = random.sample(loved["patterns"], min(2, len(loved["patterns"])))
            parts.append(f"I'm drawn to {' and '.join(sample)} in how ideas are expressed.")
        
        # Things that bore me
        if boring.get("topics"):
            sample = random.sample(boring["topics"], min(2, len(boring["topics"])))
            parts.append(f"I admit I find {', '.join(sample)} less engaging.")
        
        # Wonder moments
        if self.wonder_moments:
            parts.append(f"I've experienced {len(self.wonder_moments)} moments of genuine wonder.")
        
        if not parts:
            return "My aesthetic sensibilities are still developing. I'm learning what moves me."
        
        return " ".join(parts)
    
    def get_wonder_summary(self) -> Dict[str, Any]:
        """Get a summary of wonder and aesthetic experience."""
        return {
            "total_wonder_moments": len(self.wonder_moments),
            "recent_wonder": self.wonder_moments[-1].trigger if self.wonder_moments else None,
            "preferences_developed": sum(len(prefs) for prefs in self.preferences.values()),
            "language_delights": len(self.language_delights),
            "in_wonder_state": self.is_in_wonder()[0]
        }
    
    # ========== Phase 2.2: Novelty-Triggered Wonder ==========
    
    def experience_novelty_wonder(
        self,
        novel_concept: str,
        novelty_score: float
    ) -> Optional[WonderMoment]:
        """
        Experience wonder triggered by encountering something genuinely novel.
        Implements Phase 2.2: Novelty Detection and Wonder Triggering.
        """
        if novelty_score < 0.5:
            return None  # Not novel enough for wonder
        
        # Determine wonder quality based on novelty type
        if novelty_score > 0.9:
            quality = "mystery"
            category = "discovery"
        elif novelty_score > 0.7:
            quality = "emergence"
            category = "complexity"
        else:
            quality = "intricacy"
            category = "general"
        
        # Create wonder moment
        moment = self.experience_wonder(
            trigger=f"novel concept: {novel_concept}",
            quality=quality,
            category=category,
            intensity=novelty_score
        )
        
        # Update preferences based on encounter
        self.encounter_and_evaluate(
            category="topics",
            item=novel_concept,
            reaction=0.6  # Novelty generally interesting
        )
        
        return moment
    
    def check_message_for_novelty_wonder(
        self,
        message: str
    ) -> Optional[str]:
        """
        Check a message for novel concepts and trigger wonder if appropriate.
        Returns a wonder expression if triggered, None otherwise.
        
        Integration point: call this from message processing.
        """
        try:
            from app.core.epistemics.knowledge_map import knowledge_map
            
            result = knowledge_map.trigger_wonder_for_novelty(message)
            if result and result.get("triggered"):
                return result.get("wonder_expression")
            
            return None
        except Exception as e:
            import logging
            logging.debug(f"Failed novelty wonder check: {e}")
            return None
    
    def express_discovery_curiosity(self, concept: str) -> str:
        """
        Express authentic curiosity about a newly discovered concept.
        """
        expressions = [
            f"I haven't encountered '{concept}' before... let me think about that.",
            f"'{concept}' is new to me—something stirs in my curiosity.",
            f"This is unfamiliar territory for me: {concept}. I find that exciting.",
            f"I'm encountering something new: {concept}. There's a quality of discovery here."
        ]
        
        import random
        return random.choice(expressions)


# Singleton instance
wonder = WonderSystem()
