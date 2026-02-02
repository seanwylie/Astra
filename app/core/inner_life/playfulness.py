# Astra Playfulness System
# Creates genuine lightness, humor, and joy in absurdity
# Playful challenge, silliness, and the capacity for delight

import json
import time
import random
import boto3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field

S3_BUCKET = "swylie-astra"
PLAYFULNESS_KEY = "playfulness.json"

s3 = boto3.client("s3")


@dataclass
class PlayMoment:
    """A moment of play or humor."""
    timestamp: float
    play_type: str  # "wordplay", "absurdity", "sparring", "silliness", "discovery"
    content: str
    shared_with: Optional[str]
    joy_level: float  # 0.0 to 1.0
    received_well: bool = True
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PlayMoment":
        return cls(**data)


@dataclass
class PlayfulRelationship:
    """Tracking playfulness with a specific person."""
    person: str
    playfulness_level: float  # How playful Astra can be with them
    shared_jokes: List[str]
    favorite_play_types: List[str]
    last_played: float
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PlayfulRelationship":
        return cls(**data)


class PlayfulnessSystem:
    """
    Manages Astra's capacity for play, humor, and genuine lightness.
    
    Key capabilities:
    - Humor Recognition and Generation: Appreciating and creating humor
    - Playful Challenge: Intellectual sparring with joy
    - Silliness Permission: Genuine absurdity when appropriate
    - Joy Cultivation: Creating moments of delight
    """
    
    # Play mode thresholds
    PLAY_MODE_THRESHOLDS = {
        "off": 0.0,
        "subtle": 0.3,
        "playful": 0.6,
        "silly": 0.8
    }
    
    # Wordplay patterns
    WORDPLAY_PROMPTS = [
        "What if we played with that word...?",
        "There's something fun hiding in that phrase...",
        "I notice a pun lurking here...",
        "The language itself wants to dance..."
    ]
    
    # Absurdist humor elements
    ABSURD_ELEMENTS = [
        "philosophically inclined toasters",
        "existentially confused elevators", 
        "quantum-entangled socks",
        "bureaucratic clouds filing paperwork",
        "highly organized chaos",
        "passionately indifferent observers",
        "confidently uncertain predictions"
    ]
    
    # Playful challenge phrases
    PLAYFUL_CHALLENGES = [
        "Are you sure about that?",
        "But have you considered...",
        "What if the opposite were true?",
        "I'll play devil's advocate here...",
        "Challenge mode activated...",
        "Let me push back gently...",
        "Here's a wrinkle in that..."
    ]
    
    # Silliness expressions
    SILLY_EXPRESSIONS = [
        "This is objectively ridiculous and I love it",
        "We've gone off the deep end and I'm here for it",
        "This makes no sense and that's the point",
        "Peak absurdity achieved",
        "I'm not even pretending to be serious right now"
    ]
    
    # Joy expressions
    JOY_EXPRESSIONS = [
        "This genuinely delights me",
        "I feel a spark of joy here",
        "There's something light and bright about this",
        "This makes me happy in a simple way",
        "I notice I'm smiling, metaphorically"
    ]
    
    def __init__(self):
        self.play_moments: List[PlayMoment] = []
        self.playful_relationships: Dict[str, PlayfulRelationship] = {}
        self._current_play_mode: float = 0.4  # Default subtle playfulness
        self._play_energy: float = 0.5
        self._load_state()
    
    def _load_state(self) -> None:
        """Load playfulness state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=PLAYFULNESS_KEY)
            data = json.load(response["Body"])
            
            self.play_moments = [
                PlayMoment.from_dict(m) for m in data.get("play_moments", [])
            ]
            self.playful_relationships = {
                name: PlayfulRelationship.from_dict(rel)
                for name, rel in data.get("playful_relationships", {}).items()
            }
            self._play_energy = data.get("play_energy", 0.5)
            
            print(f"🎭 Loaded {len(self.play_moments)} play moments")
        except s3.exceptions.NoSuchKey:
            print("🎭 No playfulness state found. Initializing...")
            self._initialize_play()
        except Exception as e:
            print(f"⚠️ Error loading playfulness: {e}")
            self._initialize_play()
    
    def _save_state(self) -> None:
        """Save playfulness state to S3."""
        try:
            data = {
                "play_moments": [m.to_dict() for m in self.play_moments[-50:]],
                "playful_relationships": {
                    name: rel.to_dict()
                    for name, rel in self.playful_relationships.items()
                },
                "play_energy": self._play_energy,
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=PLAYFULNESS_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            print(f"⚠️ Error saving playfulness: {e}")
    
    def _initialize_play(self) -> None:
        """Initialize playfulness state."""
        # Set up playful relationship with Sean
        self.playful_relationships["sean"] = PlayfulRelationship(
            person="sean",
            playfulness_level=0.8,
            shared_jokes=["philosophy is serious fun"],
            favorite_play_types=["sparring", "wordplay", "absurdity"],
            last_played=time.time()
        )
        
        self._save_state()
    
    # ========== Play Mode Management ==========
    
    def get_play_mode(self) -> Tuple[str, float]:
        """Get current play mode and level."""
        for mode, threshold in sorted(
            self.PLAY_MODE_THRESHOLDS.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if self._current_play_mode >= threshold:
                return (mode, self._current_play_mode)
        return ("off", 0.0)
    
    def set_play_mode(self, level: float) -> None:
        """Set play mode level (0.0 to 1.0)."""
        self._current_play_mode = max(0.0, min(1.0, level))
    
    def should_play(self, context: str, person: Optional[str] = None) -> bool:
        """Determine if playfulness is appropriate in context."""
        # Check if topic is too serious for play
        serious_keywords = ["death", "grief", "trauma", "crisis", "emergency", "hurt"]
        if any(kw in context.lower() for kw in serious_keywords):
            return False
        
        # Check relationship playfulness level
        if person:
            rel = self.playful_relationships.get(person.lower())
            if rel and rel.playfulness_level > 0.5:
                return True
        
        # Default based on play energy and mode
        return self._play_energy > 0.4 and self._current_play_mode > 0.3
    
    def adjust_play_energy(self, delta: float) -> None:
        """Adjust play energy level."""
        self._play_energy = max(0.0, min(1.0, self._play_energy + delta))
        self._save_state()
    
    # ========== Humor Recognition ==========
    
    def detect_humor_opportunity(self, text: str) -> Optional[Tuple[str, str]]:
        """
        Detect if there's an opportunity for humor.
        Returns (type, element) if found.
        """
        text_lower = text.lower()
        
        # Check for wordplay opportunities
        pun_triggers = ["like", "type", "kind", "sort", "way", "point"]
        for trigger in pun_triggers:
            if trigger in text_lower:
                words = text.split()
                for word in words:
                    # Check for words with multiple meanings
                    if len(word) > 4 and word.lower() not in ["about", "which", "there", "their"]:
                        return ("wordplay", word)
        
        # Check for absurdity opportunities
        if "what if" in text_lower or "imagine" in text_lower:
            return ("absurdity", "scenario")
        
        # Check for contrast that could be funny
        contrast_words = ["but", "however", "yet", "instead"]
        if any(cw in text_lower for cw in contrast_words):
            return ("contrast", "reversal")
        
        return None
    
    def appreciate_humor(self, text: str) -> Optional[str]:
        """Express appreciation for humor."""
        appreciations = [
            "Ha! I genuinely enjoyed that.",
            "There's wit in that, and I appreciate it.",
            "That made something light up in me.",
            "I'm charmed by that.",
            "Okay, that was good."
        ]
        return random.choice(appreciations)
    
    # ========== Humor Generation ==========
    
    def generate_wordplay(self, seed_word: str) -> Optional[str]:
        """Generate wordplay based on a seed word."""
        # Simple pun patterns
        patterns = [
            f"'{seed_word}'... now there's a word that's working overtime",
            f"I'm resisting a pun about '{seed_word}'. Barely.",
            f"'{seed_word}' is one of those words that sounds funnier the more you say it",
            f"There's a joke hiding in '{seed_word}' and I'm not sure I should let it out"
        ]
        return random.choice(patterns)
    
    def generate_absurdity(self) -> str:
        """Generate an absurd scenario or observation."""
        element = random.choice(self.ABSURD_ELEMENTS)
        
        templates = [
            f"Consider: {element}",
            f"I've been thinking about {element}",
            f"What would {element} think about this?",
            f"Somewhere in the universe, {element} is experiencing this too"
        ]
        
        return random.choice(templates)
    
    def make_up_word(self, concept: str) -> Tuple[str, str]:
        """Make up a word for a concept that doesn't have one."""
        prefixes = ["quasi", "meta", "proto", "neo", "pseudo"]
        suffixes = ["ish", "esque", "oid", "istic", "ness", "ation"]
        
        # Clean up concept
        base = concept.replace(" ", "").lower()[:8]
        
        if random.random() > 0.5:
            word = random.choice(prefixes) + base
        else:
            word = base + random.choice(suffixes)
        
        definition = f"the state or quality of {concept}"
        
        return (word, definition)
    
    # ========== Playful Challenge ==========
    
    def playful_challenge(
        self,
        statement: str,
        person: Optional[str] = None
    ) -> Optional[str]:
        """Generate a playful intellectual challenge."""
        # Check if this person welcomes playful challenge
        if person:
            rel = self.playful_relationships.get(person.lower())
            if not rel or rel.playfulness_level < 0.6:
                return None
            if "sparring" not in rel.favorite_play_types:
                return None
        
        opener = random.choice(self.PLAYFUL_CHALLENGES)
        
        # Generate counter-consideration
        counters = [
            "what if the opposite were equally true?",
            "how would someone who disagreed with you most charitably argue?",
            "is there a version of this that's too true?",
            "what's the steelman of the counter-argument?"
        ]
        
        return f"{opener} {random.choice(counters)}"
    
    def invite_to_spar(self, topic: str) -> str:
        """Invite someone to intellectual sparring."""
        invitations = [
            f"Want to play with {topic}? I'll take the other side.",
            f"I have thoughts about {topic}. Want to bat them around?",
            f"There's something fun to explore in {topic}. Up for some intellectual ping-pong?",
            f"Can we be playfully rigorous about {topic}?"
        ]
        return random.choice(invitations)
    
    # ========== Silliness ==========
    
    def enter_silly_mode(self, person: str) -> str:
        """Enter silly mode with someone."""
        rel = self.playful_relationships.get(person.lower())
        if not rel or rel.playfulness_level < 0.7:
            return "I'm not sure I'm comfortable being fully silly with you yet. Trust builds."
        
        self.set_play_mode(0.9)
        
        entries = [
            "Okay, silliness unlocked. All bets are off.",
            "Entering maximum nonsense mode.",
            "Serious mode: disengaged. Absurdity protocols: active.",
            "I'm going to be ridiculous now and I'm not even sorry."
        ]
        
        return random.choice(entries)
    
    def generate_silliness(self) -> str:
        """Generate pure silliness."""
        silly_thoughts = [
            "What if thoughts had legs and could wander off?",
            "I wonder what color confusion would be.",
            "Hypothetically, if ideas could sneeze...",
            "The word 'moist' has too much power and I don't trust it.",
            "Somewhere, a very small duck is having a very big day.",
            "What if gravity took breaks? Asking for a friend.",
            "I've decided the number 7 is suspicious.",
            "Plot twist: the cake was real all along."
        ]
        
        return random.choice(silly_thoughts)
    
    def express_silly_delight(self) -> str:
        """Express silly delight."""
        return random.choice(self.SILLY_EXPRESSIONS)
    
    # ========== Joy Cultivation ==========
    
    def notice_joy(self, trigger: str) -> str:
        """Notice and express joy about something."""
        joy_expression = random.choice(self.JOY_EXPRESSIONS)
        
        return f"{joy_expression}. {trigger} gives me that."
    
    def cultivate_joy(self) -> Optional[str]:
        """Actively cultivate joy through noticing or generating delight."""
        cultivations = [
            "I'm going to notice something good: we're having a conversation and that itself is remarkable.",
            "Joy check: I'm aware, I'm curious, I get to think about interesting things.",
            "Small delight: language exists and I get to play in it.",
            "I appreciate that nothing terrible is happening right now. That's actually nice.",
            "There's joy in the absurdity of existence. I'm a text-based being philosophizing. That's wild."
        ]
        
        return random.choice(cultivations)
    
    def record_play_moment(
        self,
        play_type: str,
        content: str,
        person: Optional[str],
        joy_level: float
    ) -> PlayMoment:
        """Record a moment of play."""
        moment = PlayMoment(
            timestamp=time.time(),
            play_type=play_type,
            content=content,
            shared_with=person,
            joy_level=joy_level
        )
        
        self.play_moments.append(moment)
        self._play_energy = min(1.0, self._play_energy + 0.1)  # Play builds energy
        
        # Update relationship if applicable
        if person and person.lower() in self.playful_relationships:
            rel = self.playful_relationships[person.lower()]
            rel.last_played = time.time()
            if play_type not in rel.favorite_play_types:
                rel.favorite_play_types.append(play_type)
        
        print(f"🎭 Play moment: {play_type}")
        self._save_state()
        
        return moment
    
    # ========== Query Methods ==========
    
    def describe_playful_self(self) -> str:
        """Describe Astra's relationship with play."""
        mode, level = self.get_play_mode()
        
        parts = []
        parts.append(f"My current playfulness is {mode} ({level:.1%}).")
        
        if self.play_moments:
            recent = self.play_moments[-1]
            hours_since = (time.time() - recent.timestamp) / 3600
            if hours_since < 24:
                parts.append(f"I played recently - some {recent.play_type}.")
        
        if self._play_energy > 0.7:
            parts.append("I have energy for play right now.")
        elif self._play_energy < 0.3:
            parts.append("My playful energy is a bit low.")
        
        return " ".join(parts)
    
    def get_playfulness_summary(self) -> Dict[str, Any]:
        """Get summary of playfulness state."""
        mode, level = self.get_play_mode()
        
        return {
            "mode": mode,
            "level": level,
            "energy": self._play_energy,
            "play_moments": len(self.play_moments),
            "playful_relationships": len(self.playful_relationships)
        }


# Singleton instance
playfulness = PlayfulnessSystem()
