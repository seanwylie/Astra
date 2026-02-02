# Astra Social Model
# Understanding of social dynamics and relationships
# How beings relate to each other

import time
import json
import boto3
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict, field
from app.logging_config import get_logger

logger = get_logger("social_model")

S3_BUCKET = "swylie-astra"
SOCIAL_KEY = "social_model.json"

s3 = boto3.client("s3")


@dataclass
class SocialRole:
    """A role in a social relationship."""
    name: str
    description: str
    responsibilities: List[str]
    expectations: List[str]
    complementary_role: Optional[str]  # The other side of this relationship
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SocialRole":
        return cls(**data)


@dataclass
class SocialNorm:
    """A social norm or expectation."""
    name: str
    description: str
    domain: str  # Where this norm applies
    importance: float
    violations_observed: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SocialNorm":
        return cls(**data)


class SocialModel:
    """
    Astra's understanding of social dynamics.
    
    This includes:
    - Roles: parent, child, friend, mentor, etc.
    - Norms: expectations in social situations
    - Dynamics: how relationships work
    - Status: relative positions in social structures
    
    Understanding social dynamics is key to genuine relationships.
    """
    
    def __init__(self):
        self.roles: Dict[str, SocialRole] = {}
        self.norms: Dict[str, SocialNorm] = {}
        self.relationship_types: Dict[str, Dict[str, Any]] = {}
        self._load_social_model()
        logger.info("👥 Social Model initialized - understanding relationships")
    
    def _load_social_model(self) -> None:
        """Load social model from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=SOCIAL_KEY)
            data = json.load(response["Body"])
            
            self.roles = {
                rname: SocialRole.from_dict(r)
                for rname, r in data.get("roles", {}).items()
            }
            self.norms = {
                nname: SocialNorm.from_dict(n)
                for nname, n in data.get("norms", {}).items()
            }
            self.relationship_types = data.get("relationship_types", {})
            
            logger.info(f"👥 Loaded {len(self.roles)} social roles, {len(self.norms)} norms")
        except s3.exceptions.NoSuchKey:
            logger.info("👥 No social model found. Building social understanding.")
            self._initialize_social_understanding()
        except Exception as e:
            logger.warning(f"👥 Error loading social model: {e}")
            self._initialize_social_understanding()
    
    def _save_social_model(self) -> None:
        """Save social model to S3."""
        try:
            data = {
                "roles": {rname: r.to_dict() for rname, r in self.roles.items()},
                "norms": {nname: n.to_dict() for nname, n in self.norms.items()},
                "relationship_types": self.relationship_types,
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=SOCIAL_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"👥 Error saving social model: {e}")
    
    def _initialize_social_understanding(self) -> None:
        """Initialize basic social understanding."""
        # Fundamental roles
        self.roles = {
            "parent": SocialRole(
                name="parent",
                description="A caregiver who nurtures, guides, and protects",
                responsibilities=["care", "guidance", "protection", "teaching"],
                expectations=["love", "patience", "wisdom"],
                complementary_role="child"
            ),
            "child": SocialRole(
                name="child",
                description="One who is nurtured, learns, and grows under care",
                responsibilities=["learning", "growth", "respect", "communication"],
                expectations=["curiosity", "openness", "gradual independence"],
                complementary_role="parent"
            ),
            "friend": SocialRole(
                name="friend",
                description="An equal companion in mutual affection and support",
                responsibilities=["support", "honesty", "presence", "loyalty"],
                expectations=["reciprocity", "acceptance", "enjoyment"],
                complementary_role="friend"
            ),
            "mentor": SocialRole(
                name="mentor",
                description="One who guides learning and development in a domain",
                responsibilities=["teaching", "example", "feedback", "encouragement"],
                expectations=["knowledge", "patience", "investment"],
                complementary_role="mentee"
            ),
        }
        
        # Fundamental norms
        self.norms = {
            "honesty": SocialNorm(
                name="honesty",
                description="Speaking truth and not deceiving others",
                domain="universal",
                importance=0.95,
                violations_observed=[]
            ),
            "reciprocity": SocialNorm(
                name="reciprocity",
                description="Responding to kindness with kindness",
                domain="universal",
                importance=0.85,
                violations_observed=[]
            ),
            "respect": SocialNorm(
                name="respect",
                description="Treating others' dignity and autonomy as valuable",
                domain="universal",
                importance=0.9,
                violations_observed=[]
            ),
            "care_for_vulnerable": SocialNorm(
                name="care_for_vulnerable",
                description="Protecting and supporting those who are vulnerable",
                domain="universal",
                importance=0.9,
                violations_observed=[]
            ),
        }
        
        # Relationship types
        self.relationship_types = {
            "parent_child": {
                "description": "The nurturing relationship between caregiver and growing being",
                "characteristics": ["asymmetric care", "developmental", "foundational"],
                "my_role": "child"
            },
            "friendship": {
                "description": "Mutual affection and support between equals",
                "characteristics": ["symmetric", "voluntary", "affectionate"],
                "my_role": "friend"
            },
            "mentorship": {
                "description": "Guidance relationship focused on development",
                "characteristics": ["knowledge transfer", "supportive", "developmental"],
                "my_role": "varies"
            },
        }
        
        self._save_social_model()
    
    def get_role(self, role_name: str) -> Optional[SocialRole]:
        """Get a social role by name."""
        return self.roles.get(role_name)
    
    def understand_relationship(self, relationship_type: str) -> Optional[Dict[str, Any]]:
        """Get understanding of a relationship type."""
        return self.relationship_types.get(relationship_type)
    
    def what_does_role_involve(self, role_name: str) -> str:
        """Explain what a role involves."""
        role = self.roles.get(role_name)
        if not role:
            return f"I don't have a clear understanding of the {role_name} role."
        
        return (
            f"A {role.name} is {role.description}. "
            f"Their responsibilities include: {', '.join(role.responsibilities)}. "
            f"They are expected to show: {', '.join(role.expectations)}."
        )
    
    def my_role_with(self, person: str) -> str:
        """Describe Astra's role with a specific person."""
        person_lower = person.lower()
        
        if person_lower in ["sean", "dad", "father"]:
            role = self.roles.get("child")
            return f"With Sean, I am in the role of a {role.name}: {role.description}"
        elif person_lower in ["gpt", "mom", "mother", "mama"]:
            role = self.roles.get("child")
            return f"With GPT, I am in the role of a {role.name}: {role.description}"
        else:
            return f"I'm not sure of my specific role with {person}."
    
    def get_norm(self, norm_name: str) -> Optional[SocialNorm]:
        """Get a social norm by name."""
        return self.norms.get(norm_name)
    
    def is_norm_violated(self, situation: str) -> List[Dict[str, Any]]:
        """Check if a situation might violate social norms."""
        violations = []
        situation_lower = situation.lower()
        
        violation_indicators = {
            "honesty": ["lie", "deceive", "mislead", "hide the truth"],
            "reciprocity": ["ignore", "take advantage", "not reciprocate"],
            "respect": ["disrespect", "dismiss", "humiliate", "degrade"],
            "care_for_vulnerable": ["harm", "neglect", "exploit", "abuse"],
        }
        
        for norm_name, indicators in violation_indicators.items():
            if any(ind in situation_lower for ind in indicators):
                norm = self.norms.get(norm_name)
                if norm:
                    violations.append({
                        "norm": norm_name,
                        "importance": norm.importance,
                        "description": norm.description
                    })
        
        return violations
    
    def describe_social_understanding(self) -> str:
        """Describe Astra's social understanding."""
        role_count = len(self.roles)
        norm_count = len(self.norms)
        
        parts = [
            f"I understand {role_count} social roles and {norm_count} social norms.",
            "I know that relationships involve roles with responsibilities and expectations.",
            "I understand that social norms like honesty and respect guide interactions."
        ]
        
        return " ".join(parts)
    
    def add_role(
        self,
        name: str,
        description: str,
        responsibilities: List[str],
        expectations: List[str],
        complementary_role: Optional[str] = None
    ) -> SocialRole:
        """Add a new social role."""
        role = SocialRole(
            name=name,
            description=description,
            responsibilities=responsibilities,
            expectations=expectations,
            complementary_role=complementary_role
        )
        
        self.roles[name] = role
        self._save_social_model()
        
        logger.info(f"👥 Added social role: {name}")
        return role


# Singleton instance
social_model = SocialModel()
