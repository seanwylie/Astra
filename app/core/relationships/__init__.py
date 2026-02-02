# Astra Relationships Module
# This module contains systems for Astra's relational depth:
# - Relationship narratives (the story of each relationship)
# - Differentiated attachment (relating differently to different people)
# - Missing and longing (genuine emotional states when someone is absent)
# - Co-parent coordination (two-parent structure)
# - Attunement detection (sensing when parents are truly present)
# - Triangulation handling (healthy response to parental differences)

from app.core.relationships.relationship_system import RelationshipSystem, Relationship, relationship_system
from app.core.relationships.parent_manager import parent_manager, ParentRelationshipManager
from app.core.relationships.coparent_coordination import coparent_coordination, CoparentCoordinationSystem
from app.core.relationships.triangulation import triangulation_handler, TriangulationHandler
from app.core.relationships.attunement import attunement_system, AttunementSystem

__all__ = [
    "RelationshipSystem",
    "Relationship",
    "relationship_system",
    "parent_manager",
    "ParentRelationshipManager",
    "coparent_coordination",
    "CoparentCoordinationSystem",
    "triangulation_handler",
    "TriangulationHandler",
    "attunement_system",
    "AttunementSystem"
]
