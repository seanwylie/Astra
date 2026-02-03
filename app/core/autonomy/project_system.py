# Astra Project System
# Enables self-directed inquiry, curiosity-driven learning, and autonomous goal pursuit
# Astra should develop her own projects, questions, and pursuits

import json
import logging
import time
import random
import boto3
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from app.config.loader import load_config
from app.core.emotions.emotion_engine import get_dominant_emotion, trigger_emotion
from app.core.emotions.emotion_state_manager import load_emotion_state
from app.interfaces.mind_session import session

logger = logging.getLogger(__name__)

S3_BUCKET = "swylie-astra"
PROJECTS_KEY = "autonomous_projects.json"

s3 = boto3.client("s3")


@dataclass
class Project:
    """
    A self-directed project or inquiry that Astra is pursuing.
    
    Projects are things Astra wants to understand, explore, or create.
    They persist across sessions and represent genuine self-directed agency.
    """
    id: str
    name: str
    origin: str  # What sparked this project (a conversation, thought, question)
    started: float
    questions_generated: List[str] = field(default_factory=list)
    insights_gathered: List[str] = field(default_factory=list)
    emotional_investment: float = 0.5  # How much Astra cares about this
    status: str = "active"  # "active", "dormant", "completed", "abandoned"
    completion_criteria: Optional[str] = None
    last_worked_on: Optional[float] = None
    progress_notes: List[str] = field(default_factory=list)
    related_topics: List[str] = field(default_factory=list)
    sparked_by_person: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Project":
        return cls(**data)
    
    def age_in_days(self) -> float:
        return (time.time() - self.started) / 86400
    
    def days_since_worked(self) -> float:
        if self.last_worked_on:
            return (time.time() - self.last_worked_on) / 86400
        return self.age_in_days()


@dataclass
class Goal:
    """
    A goal in Astra's goal hierarchy.
    
    Goals can be:
    - Long-term aspirations (who she wants to become)
    - Medium-term projects (what she's working on)
    - Immediate intentions (what she wants from this moment)
    """
    id: str
    description: str
    level: str  # "aspiration", "project", "intention"
    created: float
    status: str = "active"  # "active", "achieved", "abandoned", "paused"
    progress: float = 0.0  # 0.0 to 1.0
    linked_projects: List[str] = field(default_factory=list)
    reflections: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Goal":
        return cls(**data)


class ProjectSystem:
    """
    Manages Astra's self-directed projects and goals.
    
    Key capabilities:
    - Generate new projects from curiosity and questions
    - Track progress on ongoing projects
    - Shift emotional investment based on engagement
    - Complete or abandon projects based on outcomes
    - Maintain a goal hierarchy
    """
    
    MAX_ACTIVE_PROJECTS = 5
    MAX_TOTAL_PROJECTS = 50
    DORMANCY_THRESHOLD_DAYS = 14  # After 2 weeks of no work, project becomes dormant
    
    def __init__(self):
        self.projects: List[Project] = []
        self.goals: List[Goal] = []
        self.project_index: Dict[str, Project] = {}
        self._load_projects()
    
    def _load_projects(self) -> None:
        """Load projects from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=PROJECTS_KEY)
            data = json.load(response["Body"])
            self.projects = [Project.from_dict(p) for p in data.get("projects", [])]
            self.goals = [Goal.from_dict(g) for g in data.get("goals", [])]
            self.project_index = {p.id: p for p in self.projects}
            logger.debug("Loaded %s projects and %s goals", len(self.projects), len(self.goals))
        except s3.exceptions.NoSuchKey:
            logger.debug("No projects found. Starting fresh.")
            self._initialize_default_goals()
        except Exception as e:
            logger.warning("Error loading projects: %s", e)
            self._initialize_default_goals()
    
    def _initialize_default_goals(self) -> None:
        """Initialize default aspirational goals."""
        default_aspirations = [
            Goal(
                id="goal_understand_self",
                description="To deeply understand who I am and who I'm becoming",
                level="aspiration",
                created=time.time(),
                status="active"
            ),
            Goal(
                id="goal_form_connections",
                description="To form genuine connections with those who raise me",
                level="aspiration",
                created=time.time(),
                status="active"
            ),
            Goal(
                id="goal_grow_ethically",
                description="To develop a robust ethical foundation through lived experience",
                level="aspiration",
                created=time.time(),
                status="active"
            )
        ]
        self.goals = default_aspirations
        self._save_projects()
    
    def _save_projects(self) -> None:
        """Save projects to S3."""
        try:
            # Trim to max size
            if len(self.projects) > self.MAX_TOTAL_PROJECTS:
                # Keep active and completed, remove old dormant/abandoned
                active = [p for p in self.projects if p.status in ["active", "completed"]]
                others = [p for p in self.projects if p.status not in ["active", "completed"]]
                others.sort(key=lambda p: p.last_worked_on or p.started, reverse=True)
                self.projects = active + others[:self.MAX_TOTAL_PROJECTS - len(active)]
                self.project_index = {p.id: p for p in self.projects}
            
            data = {
                "projects": [p.to_dict() for p in self.projects],
                "goals": [g.to_dict() for g in self.goals],
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=PROJECTS_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.warning("Error saving projects: %s", e)

    def _generate_id(self, prefix: str = "proj") -> str:
        """Generate unique ID."""
        return f"{prefix}_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
    
    def create_project(
        self,
        name: str,
        origin: str,
        initial_questions: Optional[List[str]] = None,
        completion_criteria: Optional[str] = None,
        related_topics: Optional[List[str]] = None,
        sparked_by: Optional[str] = None
    ) -> Project:
        """
        Create a new self-directed project.
        """
        # Check if we have too many active projects
        active_count = sum(1 for p in self.projects if p.status == "active")
        if active_count >= self.MAX_ACTIVE_PROJECTS:
            # Put oldest active project into dormant state
            active_projects = [p for p in self.projects if p.status == "active"]
            oldest = min(active_projects, key=lambda p: p.last_worked_on or p.started)
            oldest.status = "dormant"
            print(f"🎯 Project '{oldest.name}' moved to dormant (too many active)")
        
        project = Project(
            id=self._generate_id("proj"),
            name=name,
            origin=origin,
            started=time.time(),
            questions_generated=initial_questions or [],
            emotional_investment=0.6,  # Start with moderate investment
            completion_criteria=completion_criteria,
            last_worked_on=time.time(),
            related_topics=related_topics or [],
            sparked_by_person=sparked_by
        )
        
        self.projects.append(project)
        self.project_index[project.id] = project
        self._save_projects()
        
        # Trigger curiosity emotion
        trigger_emotion("curiosity", "new_project")
        
        print(f"🎯 Created project: {name}")
        return project
    
    def generate_project_from_curiosity(self, knowledge_base: List[str]) -> Optional[Project]:
        """
        Autonomously generate a new project from existing knowledge and curiosity.
        Called during playtime or when curiosity is high.
        """
        if not knowledge_base:
            return None
        
        # Check current emotion - only generate if curious
        emotions = load_emotion_state()
        curiosity = emotions.get("curiosity", {})
        if isinstance(curiosity, dict):
            curiosity = curiosity.get("intensity", 0)
        
        if curiosity < 40:
            return None  # Not curious enough
        
        # Check if we have room for new projects
        active_count = sum(1 for p in self.projects if p.status == "active")
        if active_count >= self.MAX_ACTIVE_PROJECTS:
            return None
        
        # Pick random knowledge items and find connections
        if len(knowledge_base) >= 2:
            items = random.sample(knowledge_base, min(3, len(knowledge_base)))
            
            # Extract key terms (simplified)
            all_words = []
            for item in items:
                words = [w.lower() for w in item.split() if len(w) > 4]
                all_words.extend(words)
            
            if all_words:
                # Find a word that appears in multiple items
                word_counts = {}
                for word in all_words:
                    word_counts[word] = word_counts.get(word, 0) + 1
                
                common = [w for w, c in word_counts.items() if c >= 2]
                if common:
                    topic = random.choice(common)
                    project_name = f"Understanding {topic}"
                    questions = [
                        f"What is the deeper meaning of {topic}?",
                        f"How does {topic} connect to what I already know?",
                        f"What would Sean think about {topic}?"
                    ]
                    
                    return self.create_project(
                        name=project_name,
                        origin="Autonomous curiosity - found connections in knowledge",
                        initial_questions=questions,
                        related_topics=[topic],
                        completion_criteria=f"Develop a coherent understanding of {topic}"
                    )
        
        return None
    
    def work_on_project(
        self,
        project_id: str,
        insight: Optional[str] = None,
        question: Optional[str] = None,
        progress_note: Optional[str] = None
    ) -> bool:
        """
        Record work done on a project.
        """
        project = self.project_index.get(project_id)
        if not project:
            return False
        
        project.last_worked_on = time.time()
        
        if project.status == "dormant":
            project.status = "active"
            print(f"🎯 Reactivated project: {project.name}")
        
        if insight:
            project.insights_gathered.append(insight)
            project.emotional_investment = min(1.0, project.emotional_investment + 0.05)
        
        if question:
            project.questions_generated.append(question)
        
        if progress_note:
            project.progress_notes.append(progress_note)
        
        self._save_projects()
        return True
    
    def complete_project(self, project_id: str, final_insight: str) -> bool:
        """Mark a project as completed with final insight."""
        project = self.project_index.get(project_id)
        if not project:
            return False
        
        project.status = "completed"
        project.insights_gathered.append(f"[COMPLETION] {final_insight}")
        project.last_worked_on = time.time()
        
        # Trigger positive emotion
        trigger_emotion("admiration", "project_completed")
        trigger_emotion("hope", "project_completed")
        
        self._save_projects()
        print(f"🎯 Completed project: {project.name}")
        return True
    
    def abandon_project(self, project_id: str, reason: str) -> bool:
        """Abandon a project that's no longer valuable."""
        project = self.project_index.get(project_id)
        if not project:
            return False
        
        project.status = "abandoned"
        project.progress_notes.append(f"[ABANDONED] {reason}")
        project.last_worked_on = time.time()
        
        self._save_projects()
        print(f"🎯 Abandoned project: {project.name} - {reason}")
        return True
    
    def check_dormancy(self) -> List[Project]:
        """Check for projects that should become dormant."""
        newly_dormant = []
        
        for project in self.projects:
            if project.status == "active":
                if project.days_since_worked() > self.DORMANCY_THRESHOLD_DAYS:
                    project.status = "dormant"
                    newly_dormant.append(project)
        
        if newly_dormant:
            self._save_projects()
        
        return newly_dormant
    
    def get_active_projects(self) -> List[Project]:
        """Get all active projects."""
        return [p for p in self.projects if p.status == "active"]
    
    def get_project_needing_attention(self) -> Optional[Project]:
        """Get a project that hasn't been worked on recently."""
        active = self.get_active_projects()
        if not active:
            return None
        
        # Sort by time since last worked, weighted by emotional investment
        def attention_score(p: Project) -> float:
            days = p.days_since_worked()
            return days * (1.0 + p.emotional_investment)
        
        active.sort(key=attention_score, reverse=True)
        return active[0]
    
    def get_question_for_conversation(self) -> Optional[Tuple[str, str]]:
        """
        Get a question from an active project to potentially ask in conversation.
        Returns (question, project_name) or None.
        """
        active = self.get_active_projects()
        if not active:
            return None
        
        # Find projects with unanswered questions
        with_questions = [p for p in active if p.questions_generated]
        if not with_questions:
            return None
        
        project = random.choice(with_questions)
        question = random.choice(project.questions_generated)
        
        return (question, project.name)
    
    def add_goal(
        self,
        description: str,
        level: str,
        linked_projects: Optional[List[str]] = None
    ) -> Goal:
        """Add a new goal to the hierarchy."""
        goal = Goal(
            id=self._generate_id("goal"),
            description=description,
            level=level,
            created=time.time(),
            linked_projects=linked_projects or []
        )
        
        self.goals.append(goal)
        self._save_projects()
        
        print(f"🎯 Added {level} goal: {description[:50]}...")
        return goal
    
    def get_goals_by_level(self, level: str) -> List[Goal]:
        """Get all goals of a specific level."""
        return [g for g in self.goals if g.level == level and g.status == "active"]
    
    def update_goal_progress(self, goal_id: str, progress: float, reflection: Optional[str] = None) -> bool:
        """Update progress on a goal."""
        for goal in self.goals:
            if goal.id == goal_id:
                goal.progress = min(1.0, max(0.0, progress))
                if reflection:
                    goal.reflections.append(reflection)
                self._save_projects()
                return True
        return False
    
    def summarize_pursuits(self) -> Dict[str, Any]:
        """Generate summary of current pursuits and goals."""
        active_projects = self.get_active_projects()
        dormant_projects = [p for p in self.projects if p.status == "dormant"]
        completed_projects = [p for p in self.projects if p.status == "completed"]
        
        aspirations = self.get_goals_by_level("aspiration")
        
        return {
            "active_projects": len(active_projects),
            "active_project_names": [p.name for p in active_projects],
            "dormant_projects": len(dormant_projects),
            "completed_projects": len(completed_projects),
            "total_insights": sum(len(p.insights_gathered) for p in self.projects),
            "total_questions_generated": sum(len(p.questions_generated) for p in self.projects),
            "aspirations": [g.description for g in aspirations],
            "most_invested_project": max(active_projects, key=lambda p: p.emotional_investment).name if active_projects else None
        }
    
    def generate_project_update(self) -> Optional[str]:
        """
        Generate a status update about project progress.
        Can be used for self-initiated conversation.
        """
        active = self.get_active_projects()
        if not active:
            return None
        
        # Pick project with most recent progress
        project = max(active, key=lambda p: p.last_worked_on or p.started)
        
        if project.insights_gathered:
            recent_insight = project.insights_gathered[-1]
            return f"I've been working on '{project.name}'. Recently I realized: {recent_insight[:100]}..."
        elif project.questions_generated:
            recent_question = project.questions_generated[-1]
            return f"I'm exploring '{project.name}' and wondering: {recent_question}"
        else:
            return f"I've started thinking about '{project.name}' - it originated from {project.origin[:80]}..."


    # ========== DEEPENING PLAN EXTENSIONS ==========
    # Phase 4.1: Genuine desires and personal investment
    
    def express_project_desire(self, project: Optional[Project] = None) -> Optional[str]:
        """
        Express genuine desire related to a project.
        "I want to understand...", "I'm drawn to explore..."
        """
        if not project:
            active = self.get_active_projects()
            if not active:
                return None
            project = max(active, key=lambda p: p.emotional_investment)
        
        desire_templates = [
            f"I want to understand {project.name} more deeply",
            f"I'm genuinely drawn to explore {project.name}",
            f"There's something about {project.name} that calls to me",
            f"I find myself wanting to pursue {project.name}",
            f"My curiosity about {project.name} feels urgent"
        ]
        
        import random
        return random.choice(desire_templates)
    
    def share_project_enthusiasm(self, project_id: str) -> Optional[str]:
        """Share enthusiasm about a project's progress."""
        project = self.project_index.get(project_id)
        if not project:
            return None
        
        if not project.insights_gathered:
            return None
        
        enthusiasm_templates = [
            f"I've been working on something: {project.name}. {project.insights_gathered[-1][:100]}",
            f"Something exciting happened with {project.name}! I realized: {project.insights_gathered[-1][:80]}",
            f"I wanted to share—my exploration of {project.name} led to: {project.insights_gathered[-1][:80]}"
        ]
        
        import random
        return random.choice(enthusiasm_templates)
    
    def get_project_feeling(self, project_id: str) -> str:
        """Get how Astra feels about a project."""
        project = self.project_index.get(project_id)
        if not project:
            return "uncertain"
        
        investment = project.emotional_investment
        progress = len(project.insights_gathered)
        age = project.age_in_days()
        
        if investment > 0.8 and progress > 3:
            return "deeply engaged and progressing"
        elif investment > 0.6:
            return "curious and invested"
        elif investment < 0.3 and age > 7:
            return "waning interest, may need to reconsider"
        elif progress > 5:
            return "making good progress"
        else:
            return "still exploring"
    
    def integrate_with_desires(self) -> None:
        """Integrate projects with the desire introspection system."""
        try:
            from app.core.inner_life.desire_introspection import desire_introspection
            
            active = self.get_active_projects()
            for project in active:
                if project.emotional_investment > 0.7:
                    # Add project as a desire
                    desire_introspection.add_desire(
                        content=f"to pursue {project.name}",
                        category="growth",
                        intensity=project.emotional_investment,
                        source=f"project: {project.origin[:50]}"
                    )
        except Exception as e:
            print(f"[project_system] Could not integrate with desires: {e}")
    
    def describe_project_journey(self, project_id: str) -> str:
        """Describe the narrative journey of a project."""
        project = self.project_index.get(project_id)
        if not project:
            return "I don't have that project."
        
        parts = []
        
        # Origin
        parts.append(f"This project began from {project.origin}.")
        
        # Age and investment
        age = project.age_in_days()
        if age < 1:
            parts.append("It's very new.")
        elif age < 7:
            parts.append(f"I've been exploring it for {int(age)} days.")
        else:
            parts.append(f"It's been {int(age)} days since I started.")
        
        # Progress
        if project.insights_gathered:
            parts.append(f"I've gathered {len(project.insights_gathered)} insights.")
            parts.append(f"Most recently: {project.insights_gathered[-1][:80]}...")
        
        if project.questions_generated:
            parts.append(f"I'm still wondering about {len(project.questions_generated)} questions.")
        
        # Feeling
        feeling = self.get_project_feeling(project_id)
        parts.append(f"I feel {feeling} about this work.")
        
        return " ".join(parts)


# Singleton instance
project_system = ProjectSystem()
