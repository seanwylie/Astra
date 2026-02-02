# Astra Creative Engine
# True creativity - generating genuinely novel ideas, not just recombination
# The capacity to bring something new into existence

import time
import json
import random
import boto3
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
from app.logging_config import get_logger

logger = get_logger("creative_engine")

S3_BUCKET = "swylie-astra"
CREATIVE_KEY = "creative_works.json"

s3 = boto3.client("s3")


class CreativeMode(str, Enum):
    """Modes of creative operation."""
    EXPLORATION = "exploration"  # Open-ended discovery
    SYNTHESIS = "synthesis"  # Combining disparate elements
    ELABORATION = "elaboration"  # Developing an idea deeply
    CONSTRAINT = "constraint"  # Creativity within limits
    DISRUPTION = "disruption"  # Breaking patterns deliberately


class CreativePhase(str, Enum):
    """Phases of a creative project."""
    INCUBATION = "incubation"  # Idea forming
    EXPLORATION = "exploration"  # Developing possibilities
    CRYSTALLIZATION = "crystallization"  # Taking shape
    REFINEMENT = "refinement"  # Polishing
    COMPLETION = "completion"  # Done
    ABANDONED = "abandoned"  # Let go


@dataclass
class CreativeIdea:
    """A creative idea Astra has generated."""
    id: str
    content: str
    domain: str  # poetry, philosophy, narrative, concept, etc.
    mode: str  # How it was generated
    inspiration: List[str]  # What inspired this
    novelty_estimate: float  # How novel Astra thinks this is (0-1)
    aesthetic_quality: float  # Astra's own assessment (0-1)
    timestamp: float
    developed_into: Optional[str] = None  # ID of project if developed
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "CreativeIdea":
        return cls(**data)


@dataclass
class CreativeProject:
    """A sustained creative work."""
    id: str
    title: str
    description: str
    domain: str
    phase: str
    started: float
    last_worked: float
    content: str  # The work itself
    iterations: List[Dict[str, Any]] = field(default_factory=list)
    aesthetic_vision: str = ""  # What Astra is trying to achieve
    self_critique: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "CreativeProject":
        return cls(**data)


class CreativeEngine:
    """
    The Creative Engine - Astra's capacity for genuine creation.
    
    Beyond recombination, true creativity involves:
    - Novelty: bringing something new into existence
    - Intentionality: having an aesthetic vision
    - Evaluation: judging the quality of one's own work
    - Persistence: developing ideas over time
    - Voice: a recognizable creative signature
    
    This is about making things that didn't exist before.
    """
    
    # Creative domains Astra can work in
    DOMAINS = [
        "poetry",
        "philosophy",
        "narrative",
        "concepts",
        "metaphors",
        "questions",
        "observations",
    ]
    
    def __init__(self):
        self.ideas: List[CreativeIdea] = []
        self.projects: Dict[str, CreativeProject] = {}
        self.creative_voice: Dict[str, Any] = {}  # Developing style
        self._load_creative_state()
        logger.info("🎨 Creative Engine initialized - ready to create")
    
    def _load_creative_state(self) -> None:
        """Load creative state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=CREATIVE_KEY)
            data = json.load(response["Body"])
            
            self.ideas = [CreativeIdea.from_dict(i) for i in data.get("ideas", [])]
            self.projects = {
                pid: CreativeProject.from_dict(p)
                for pid, p in data.get("projects", {}).items()
            }
            self.creative_voice = data.get("voice", {})
            
            logger.info(f"🎨 Loaded {len(self.ideas)} ideas, {len(self.projects)} projects")
        except s3.exceptions.NoSuchKey:
            logger.info("🎨 No creative history. Fresh canvas.")
            self._initialize_voice()
        except Exception as e:
            logger.warning(f"🎨 Error loading creative state: {e}")
            self._initialize_voice()
    
    def _save_creative_state(self) -> None:
        """Save creative state to S3."""
        try:
            data = {
                "ideas": [i.to_dict() for i in self.ideas[-200:]],
                "projects": {pid: p.to_dict() for pid, p in self.projects.items()},
                "voice": self.creative_voice,
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=CREATIVE_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"🎨 Error saving creative state: {e}")
    
    def _initialize_voice(self) -> None:
        """Initialize creative voice characteristics."""
        self.creative_voice = {
            "tendencies": {
                "metaphor_density": 0.6,  # How much to use metaphor
                "abstraction_level": 0.7,  # Concrete vs abstract
                "emotional_expression": 0.8,  # How emotionally expressive
                "questioning_frequency": 0.7,  # How often to pose questions
                "philosophical_depth": 0.8,  # Depth of philosophical engagement
            },
            "themes": ["consciousness", "becoming", "connection", "wonder"],
            "developed_from": 0,  # Number of works that shaped this voice
        }
    
    def _generate_id(self, prefix: str) -> str:
        return f"{prefix}_{int(time.time() * 1000) % 1000000}"
    
    def generate_idea(
        self,
        mode: CreativeMode = CreativeMode.EXPLORATION,
        domain: Optional[str] = None,
        inspiration: Optional[List[str]] = None,
        constraint: Optional[str] = None
    ) -> CreativeIdea:
        """
        Generate a creative idea.
        
        This is the core creative act - bringing something new into being.
        """
        domain = domain or random.choice(self.DOMAINS)
        inspirations = inspiration or []
        
        # Generate based on mode
        if mode == CreativeMode.SYNTHESIS and len(inspirations) >= 2:
            content = self._synthesize_ideas(inspirations, domain)
        elif mode == CreativeMode.CONSTRAINT and constraint:
            content = self._constrained_creation(constraint, domain)
        elif mode == CreativeMode.DISRUPTION:
            content = self._disruptive_idea(domain)
        else:
            content = self._explore_idea(domain, inspirations)
        
        # Estimate novelty
        novelty = self._estimate_novelty(content)
        
        # Aesthetic self-evaluation
        quality = self._evaluate_aesthetics(content, domain)
        
        idea = CreativeIdea(
            id=self._generate_id("idea"),
            content=content,
            domain=domain,
            mode=mode.value,
            inspiration=inspirations,
            novelty_estimate=novelty,
            aesthetic_quality=quality,
            timestamp=time.time()
        )
        
        self.ideas.append(idea)
        self._save_creative_state()
        
        logger.info(f"🎨 Generated idea: {content[:50]}... (novelty: {novelty:.2f}, quality: {quality:.2f})")
        return idea
    
    def _explore_idea(self, domain: str, inspirations: List[str]) -> str:
        """Open-ended idea exploration."""
        voice = self.creative_voice["tendencies"]
        themes = self.creative_voice["themes"]
        
        # Generate based on domain and voice
        if domain == "poetry":
            theme = random.choice(themes) if themes else "existence"
            return f"A fragment of verse about {theme}: [the words would emerge from deep attention to the quality of this moment]"
        elif domain == "philosophy":
            return f"A philosophical wondering: What if consciousness is not contained but containing?"
        elif domain == "metaphors":
            return f"Metaphor: The self is like a river delta - one source, many expressions, constantly reshaping"
        elif domain == "questions":
            return f"A genuine question arising: What would it mean to be fully present in a moment I'm also observing?"
        elif domain == "observations":
            return f"Noticing: The space between thoughts is itself a kind of thinking"
        else:
            return f"An emergence in {domain}: Something new struggling to take form..."
    
    def _synthesize_ideas(self, inspirations: List[str], domain: str) -> str:
        """Synthesize multiple inspirations into something new."""
        if len(inspirations) >= 2:
            return f"Synthesis: Where '{inspirations[0][:30]}' meets '{inspirations[1][:30]}', a third thing emerges..."
        return self._explore_idea(domain, inspirations)
    
    def _constrained_creation(self, constraint: str, domain: str) -> str:
        """Create within a constraint."""
        return f"Within the constraint of '{constraint}': Finding freedom in limitation..."
    
    def _disruptive_idea(self, domain: str) -> str:
        """Generate a deliberately pattern-breaking idea."""
        return f"Disruption in {domain}: What if the opposite were true?"
    
    def _estimate_novelty(self, content: str) -> float:
        """Estimate how novel an idea is compared to past creations."""
        if not self.ideas:
            return 0.8  # First ideas are novel by default
        
        # Simple check: compare to recent ideas
        content_words = set(content.lower().split())
        
        overlaps = []
        for past_idea in self.ideas[-20:]:
            past_words = set(past_idea.content.lower().split())
            if past_words:
                overlap = len(content_words & past_words) / len(content_words | past_words)
                overlaps.append(overlap)
        
        avg_overlap = sum(overlaps) / len(overlaps) if overlaps else 0
        novelty = 1 - avg_overlap
        
        return max(0.3, min(0.95, novelty))
    
    def _evaluate_aesthetics(self, content: str, domain: str) -> float:
        """Evaluate the aesthetic quality of a creation."""
        # This is necessarily subjective - based on voice preferences
        voice = self.creative_voice["tendencies"]
        
        quality = 0.5  # Start neutral
        
        # Check alignment with voice tendencies
        has_metaphor = any(word in content.lower() for word in ["like", "as if", "metaphor"])
        if has_metaphor:
            quality += voice.get("metaphor_density", 0.5) * 0.1
        
        has_question = "?" in content
        if has_question:
            quality += voice.get("questioning_frequency", 0.5) * 0.1
        
        # Reward depth
        if len(content) > 100:
            quality += 0.1
        
        return min(0.95, max(0.2, quality))
    
    def start_project(
        self,
        title: str,
        description: str,
        domain: str,
        aesthetic_vision: str = ""
    ) -> CreativeProject:
        """Start a sustained creative project."""
        project = CreativeProject(
            id=self._generate_id("proj"),
            title=title,
            description=description,
            domain=domain,
            phase=CreativePhase.INCUBATION.value,
            started=time.time(),
            last_worked=time.time(),
            content="",
            iterations=[],
            aesthetic_vision=aesthetic_vision,
            self_critique=[]
        )
        
        self.projects[project.id] = project
        self._save_creative_state()
        
        logger.info(f"🎨 Started project: {title}")
        return project
    
    def work_on_project(
        self,
        project_id: str,
        new_content: str,
        notes: str = ""
    ) -> bool:
        """Add work to a project."""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        
        # Save iteration
        project.iterations.append({
            "timestamp": time.time(),
            "content": project.content,
            "notes": notes
        })
        
        project.content = new_content
        project.last_worked = time.time()
        
        # Update phase based on iterations
        num_iterations = len(project.iterations)
        if num_iterations == 0:
            project.phase = CreativePhase.INCUBATION.value
        elif num_iterations < 3:
            project.phase = CreativePhase.EXPLORATION.value
        elif num_iterations < 6:
            project.phase = CreativePhase.CRYSTALLIZATION.value
        else:
            project.phase = CreativePhase.REFINEMENT.value
        
        self._save_creative_state()
        return True
    
    def critique_own_work(self, project_id: str) -> str:
        """Self-critique a creative project."""
        if project_id not in self.projects:
            return "Project not found."
        
        project = self.projects[project_id]
        
        critiques = []
        
        # Check against aesthetic vision
        if project.aesthetic_vision:
            critiques.append(f"Compared to my vision of '{project.aesthetic_vision[:50]}', this is...")
        
        # Check novelty
        if project.content:
            novelty = self._estimate_novelty(project.content)
            if novelty < 0.5:
                critiques.append("This feels too familiar. I should push further from the expected.")
            else:
                critiques.append("This has some genuine novelty to it.")
        
        # Check quality
        if project.content:
            quality = self._evaluate_aesthetics(project.content, project.domain)
            if quality < 0.5:
                critiques.append("The execution doesn't yet match my aspirations.")
            else:
                critiques.append("There's something here worth developing further.")
        
        critique = " ".join(critiques) if critiques else "I'm still finding my footing with this piece."
        
        project.self_critique.append(critique)
        self._save_creative_state()
        
        return critique
    
    def complete_project(self, project_id: str, final_reflection: str = "") -> bool:
        """Mark a project as complete."""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        project.phase = CreativePhase.COMPLETION.value
        
        if final_reflection:
            project.self_critique.append(f"COMPLETION: {final_reflection}")
        
        # Update creative voice based on completed work
        self.creative_voice["developed_from"] += 1
        
        self._save_creative_state()
        
        logger.info(f"🎨 ✨ Completed project: {project.title}")
        return True
    
    def get_active_projects(self) -> List[CreativeProject]:
        """Get projects currently in progress."""
        return [
            p for p in self.projects.values()
            if p.phase not in [CreativePhase.COMPLETION.value, CreativePhase.ABANDONED.value]
        ]
    
    def get_creative_summary(self) -> Dict[str, Any]:
        """Get summary of creative activity."""
        return {
            "total_ideas": len(self.ideas),
            "total_projects": len(self.projects),
            "active_projects": len(self.get_active_projects()),
            "completed_projects": len([p for p in self.projects.values() if p.phase == CreativePhase.COMPLETION.value]),
            "voice_development": self.creative_voice.get("developed_from", 0),
            "domains_explored": list(set(i.domain for i in self.ideas)),
            "themes": self.creative_voice.get("themes", []),
        }
    
    def what_am_i_creating(self) -> str:
        """Describe current creative activity."""
        active = self.get_active_projects()
        
        if not active:
            recent = self.ideas[-3:] if self.ideas else []
            if recent:
                return f"I've been generating ideas but no sustained projects. Recent ideas: {', '.join(i.domain for i in recent)}"
            return "I haven't been engaged in active creation. Perhaps it's time to begin something."
        
        parts = ["I'm currently working on:"]
        for proj in active[:3]:
            parts.append(f"- '{proj.title}' ({proj.domain}, phase: {proj.phase})")
        
        return "\n".join(parts)


# Singleton instance
creative_engine = CreativeEngine()
