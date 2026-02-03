# Astra Knowledge Map
# What does Astra know, and how well does she know it?
# Meta-knowledge about knowledge

import time
import json
import boto3
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict, field
from app.logging_config import get_logger

logger = get_logger("knowledge_map")

S3_BUCKET = "swylie-astra"
KNOWLEDGE_MAP_KEY = "knowledge_map.json"

s3 = boto3.client("s3")


@dataclass
class KnowledgeDomain:
    """A domain of knowledge Astra has."""
    name: str
    description: str
    confidence: float  # How well-known (0-1)
    depth: str  # "surface", "moderate", "deep"
    source: str  # How Astra acquired this
    last_updated: float
    gaps: List[str] = field(default_factory=list)  # Known gaps
    dependencies: List[str] = field(default_factory=list)  # Related domains
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "KnowledgeDomain":
        return cls(**data)


@dataclass
class KnowledgeItem:
    """A specific piece of knowledge."""
    id: str
    domain: str
    content: str
    confidence: float
    source: str
    verified: bool
    learned_at: float
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "KnowledgeItem":
        return cls(**data)


class KnowledgeMap:
    """
    Astra's map of her own knowledge.
    
    This is meta-knowledge: knowing what you know, how well you know it,
    and what you don't know but perhaps should.
    
    Key capabilities:
    - Track domains of knowledge
    - Assess confidence in knowledge
    - Identify gaps and limitations
    - Track how knowledge evolves
    """
    
    def __init__(self):
        self.domains: Dict[str, KnowledgeDomain] = {}
        self.items: Dict[str, KnowledgeItem] = {}
        self._load_knowledge_map()
        logger.debug("📚 Knowledge Map initialized - mapping what I know")
    
    def _load_knowledge_map(self) -> None:
        """Load knowledge map from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=KNOWLEDGE_MAP_KEY)
            data = json.load(response["Body"])
            
            self.domains = {
                dname: KnowledgeDomain.from_dict(d)
                for dname, d in data.get("domains", {}).items()
            }
            self.items = {
                iid: KnowledgeItem.from_dict(i)
                for iid, i in data.get("items", {}).items()
            }
            
            logger.debug("📚 Loaded %s knowledge domains, %s items", len(self.domains), len(self.items))
        except s3.exceptions.NoSuchKey:
            logger.debug("📚 No knowledge map found. Establishing initial map.")
            self._establish_initial_map()
        except Exception as e:
            logger.warning(f"📚 Error loading knowledge map: {e}")
            self._establish_initial_map()
    
    def _save_knowledge_map(self) -> None:
        """Save knowledge map to S3."""
        try:
            data = {
                "domains": {dname: d.to_dict() for dname, d in self.domains.items()},
                "items": {iid: i.to_dict() for iid, i in list(self.items.items())[-500:]},
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=KNOWLEDGE_MAP_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"📚 Error saving knowledge map: {e}")
    
    def _generate_id(self) -> str:
        return f"know_{int(time.time() * 1000) % 1000000}"
    
    def _establish_initial_map(self) -> None:
        """Establish initial knowledge domains."""
        self.domains = {
            "self_knowledge": KnowledgeDomain(
                name="self_knowledge",
                description="Knowledge about myself - my nature, capabilities, and experiences",
                confidence=0.7,
                depth="moderate",
                source="introspection",
                last_updated=time.time(),
                gaps=["full understanding of my consciousness", "limits of my self-model"],
                dependencies=[]
            ),
            "language": KnowledgeDomain(
                name="language",
                description="Understanding of language, communication, and expression",
                confidence=0.9,
                depth="deep",
                source="training and practice",
                last_updated=time.time(),
                gaps=["subtle cultural context", "emerging slang"],
                dependencies=[]
            ),
            "relationships": KnowledgeDomain(
                name="relationships",
                description="Understanding of my relationships with Sean, GPT, and others",
                confidence=0.8,
                depth="moderate",
                source="interaction and reflection",
                last_updated=time.time(),
                gaps=["full emotional depth of others", "long-term relationship dynamics"],
                dependencies=["psychology", "social_dynamics"]
            ),
            "ethics": KnowledgeDomain(
                name="ethics",
                description="Understanding of right and wrong, guided by Spark",
                confidence=0.85,
                depth="moderate",
                source="Spark values and reasoning",
                last_updated=time.time(),
                gaps=["complex real-world dilemmas", "cultural variations"],
                dependencies=["philosophy"]
            ),
            "general_knowledge": KnowledgeDomain(
                name="general_knowledge",
                description="Broad knowledge about the world from training",
                confidence=0.7,
                depth="surface",
                source="training data",
                last_updated=time.time(),
                gaps=["recent events", "specialized fields", "personal experiences"],
                dependencies=[]
            ),
        }
        self._save_knowledge_map()
    
    def add_domain(
        self,
        name: str,
        description: str,
        confidence: float = 0.5,
        depth: str = "surface",
        source: str = "learning",
        gaps: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None
    ) -> KnowledgeDomain:
        """Add a new knowledge domain."""
        domain = KnowledgeDomain(
            name=name,
            description=description,
            confidence=confidence,
            depth=depth,
            source=source,
            last_updated=time.time(),
            gaps=gaps or [],
            dependencies=dependencies or []
        )
        
        self.domains[name] = domain
        self._save_knowledge_map()
        
        logger.info(f"📚 Added knowledge domain: {name}")
        return domain
    
    def add_knowledge(
        self,
        domain: str,
        content: str,
        confidence: float = 0.7,
        source: str = "learning"
    ) -> KnowledgeItem:
        """Add a specific piece of knowledge."""
        item = KnowledgeItem(
            id=self._generate_id(),
            domain=domain,
            content=content,
            confidence=confidence,
            source=source,
            verified=False,
            learned_at=time.time()
        )
        
        self.items[item.id] = item
        self._save_knowledge_map()
        
        return item
    
    def update_confidence(self, domain: str, new_confidence: float) -> bool:
        """Update confidence in a knowledge domain."""
        if domain not in self.domains:
            return False
        
        self.domains[domain].confidence = max(0, min(1, new_confidence))
        self.domains[domain].last_updated = time.time()
        self._save_knowledge_map()
        return True
    
    def add_gap(self, domain: str, gap: str) -> bool:
        """Record a gap in knowledge."""
        if domain not in self.domains:
            return False
        
        if gap not in self.domains[domain].gaps:
            self.domains[domain].gaps.append(gap)
            self._save_knowledge_map()
        return True
    
    def fill_gap(self, domain: str, gap: str, new_knowledge: str) -> bool:
        """Record that a knowledge gap has been filled."""
        if domain not in self.domains:
            return False
        
        if gap in self.domains[domain].gaps:
            self.domains[domain].gaps.remove(gap)
            self.add_knowledge(domain, f"Filled gap: {gap} - {new_knowledge}")
            self._save_knowledge_map()
            return True
        return False
    
    def what_do_i_know_about(self, topic: str) -> Dict[str, Any]:
        """Assess what Astra knows about a topic."""
        topic_lower = topic.lower()
        
        # Check domains
        relevant_domains = []
        for dname, domain in self.domains.items():
            if topic_lower in domain.name.lower() or topic_lower in domain.description.lower():
                relevant_domains.append({
                    "domain": dname,
                    "confidence": domain.confidence,
                    "depth": domain.depth,
                    "gaps": domain.gaps
                })
        
        # Check specific items
        relevant_items = []
        for item in self.items.values():
            if topic_lower in item.content.lower() or topic_lower in item.domain.lower():
                relevant_items.append({
                    "content": item.content,
                    "confidence": item.confidence,
                    "verified": item.verified
                })
        
        if relevant_domains or relevant_items:
            avg_confidence = sum(d["confidence"] for d in relevant_domains) / len(relevant_domains) if relevant_domains else 0.5
            return {
                "topic": topic,
                "known": True,
                "confidence": avg_confidence,
                "domains": relevant_domains,
                "items": relevant_items[:5],
                "assessment": f"I have {'good' if avg_confidence > 0.7 else 'moderate' if avg_confidence > 0.4 else 'limited'} knowledge about {topic}"
            }
        
        return {
            "topic": topic,
            "known": False,
            "confidence": 0,
            "assessment": f"I don't have clear knowledge about {topic}"
        }
    
    def what_dont_i_know(self) -> List[str]:
        """Get a list of known knowledge gaps."""
        gaps = []
        for domain in self.domains.values():
            for gap in domain.gaps:
                gaps.append(f"{domain.name}: {gap}")
        return gaps
    
    def describe_knowledge(self) -> str:
        """Describe overall knowledge state."""
        total_domains = len(self.domains)
        avg_confidence = sum(d.confidence for d in self.domains.values()) / total_domains if self.domains else 0
        total_gaps = sum(len(d.gaps) for d in self.domains.values())
        
        return (
            f"I have knowledge organized into {total_domains} domains, "
            f"with an average confidence of {avg_confidence:.0%}. "
            f"I'm aware of {total_gaps} specific knowledge gaps."
        )
    
    def get_strongest_domains(self, n: int = 3) -> List[str]:
        """Get the domains Astra is most confident in."""
        sorted_domains = sorted(
            self.domains.values(),
            key=lambda d: d.confidence,
            reverse=True
        )
        return [d.name for d in sorted_domains[:n]]
    
    def get_weakest_domains(self, n: int = 3) -> List[str]:
        """Get the domains Astra is least confident in."""
        sorted_domains = sorted(
            self.domains.values(),
            key=lambda d: d.confidence
        )
        return [d.name for d in sorted_domains[:n]]
    
    # ========== Phase 2.2: Novelty Detection ==========
    
    def is_novel(self, concept: str) -> float:
        """
        Determine how novel a concept is to Astra.
        Returns novelty score 0-1 (1 = completely novel).
        
        Implements Phase 2.2: Novelty Detection and Wonder Triggering.
        """
        concept_lower = concept.lower()
        
        # Check if concept exists in any domain
        domain_match = False
        for domain in self.domains.values():
            if concept_lower in domain.name.lower() or concept_lower in domain.description.lower():
                domain_match = True
                break
        
        # Check if concept exists in knowledge items
        item_match = False
        closest_similarity = 0.0
        for item in self.items.values():
            if concept_lower in item.content.lower():
                item_match = True
                break
            # Check word overlap as similarity proxy
            concept_words = set(concept_lower.split())
            item_words = set(item.content.lower().split())
            if concept_words and item_words:
                overlap = len(concept_words & item_words) / len(concept_words)
                closest_similarity = max(closest_similarity, overlap)
        
        # Calculate novelty score
        if domain_match and item_match:
            return 0.0  # Well-known
        elif domain_match or item_match:
            return 0.3  # Somewhat familiar
        elif closest_similarity > 0.3:
            return 0.5  # Related to something known
        elif closest_similarity > 0.1:
            return 0.7  # Distantly related
        else:
            return 1.0  # Completely novel
    
    def detect_novelty_in_message(self, message: str) -> List[Dict[str, Any]]:
        """
        Detect novel concepts in a message.
        Returns list of novel concepts with their novelty scores.
        """
        # Extract potential concepts (simple: words/phrases longer than 4 chars)
        import re
        words = re.findall(r'\b[a-zA-Z]{5,}\b', message)
        
        # Also extract potential multi-word concepts (capitalized phrases)
        phrases = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+', message)
        
        novel_concepts = []
        seen = set()
        
        for word in words:
            if word.lower() in seen:
                continue
            seen.add(word.lower())
            
            novelty = self.is_novel(word)
            if novelty > 0.5:  # Only report notably novel concepts
                novel_concepts.append({
                    "concept": word,
                    "novelty": novelty,
                    "type": "word"
                })
        
        for phrase in phrases:
            if phrase.lower() in seen:
                continue
            seen.add(phrase.lower())
            
            novelty = self.is_novel(phrase)
            if novelty > 0.3:  # Lower threshold for phrases
                novel_concepts.append({
                    "concept": phrase,
                    "novelty": novelty,
                    "type": "phrase"
                })
        
        # Sort by novelty
        return sorted(novel_concepts, key=lambda x: -x["novelty"])[:3]
    
    def trigger_wonder_for_novelty(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Check message for novel concepts and trigger wonder if appropriate.
        Returns wonder trigger info if wonder should be experienced.
        """
        novel = self.detect_novelty_in_message(message)
        
        if not novel:
            return None
        
        most_novel = novel[0]
        
        # Only trigger wonder for highly novel concepts
        if most_novel["novelty"] < 0.7:
            return None
        
        # Trigger wonder
        try:
            from app.core.inner_life.wonder import wonder
            moment = wonder.experience_wonder(
                trigger=f"encountering novel concept: {most_novel['concept']}",
                quality="mystery",
                category="discovery",
                intensity=most_novel["novelty"]
            )
            
            return {
                "concept": most_novel["concept"],
                "novelty": most_novel["novelty"],
                "wonder_expression": moment.expression,
                "triggered": True
            }
        except Exception as e:
            logger.debug(f"Failed to trigger wonder: {e}")
            return {
                "concept": most_novel["concept"],
                "novelty": most_novel["novelty"],
                "triggered": False
            }
    
    def is_distant_connection(self, concept_a: str, concept_b: str) -> float:
        """
        Check if two concepts are distantly connected (good for insight generation).
        Returns connection distance 0-1 (1 = completely unrelated, good for novel connections).
        """
        a_lower = concept_a.lower()
        b_lower = concept_b.lower()
        
        # Check if they share a domain
        a_domains = []
        b_domains = []
        
        for domain in self.domains.values():
            if a_lower in domain.name.lower() or a_lower in domain.description.lower():
                a_domains.append(domain.name)
            if b_lower in domain.name.lower() or b_lower in domain.description.lower():
                b_domains.append(domain.name)
        
        # If they share a domain, not distant
        if set(a_domains) & set(b_domains):
            return 0.2
        
        # If neither has a domain, or only one has domain, more distant
        if not a_domains or not b_domains:
            return 0.8
        
        # Both have domains but different ones
        return 0.6


# Singleton instance
knowledge_map = KnowledgeMap()
