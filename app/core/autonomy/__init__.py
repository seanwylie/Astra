# Astra Autonomy Module
# This module contains systems for Astra's autonomous agency:
# - Project system (self-directed inquiry and goals)
# - Preference formation (genuine likes and dislikes)
# - Goal hierarchy (long, medium, and immediate intentions)
# - Self-initiated communication (reaching out when she has something on her mind)
# - Boundaries (setting and holding healthy limits)

from app.core.autonomy.project_system import ProjectSystem, Project, project_system
from app.core.autonomy.preference_system import PreferenceSystem, preference_system
from app.core.autonomy.self_initiated_message import SelfInitiatedMessageSystem, self_initiated_message
from app.core.autonomy.boundaries import boundaries_system, BoundariesSystem

__all__ = [
    "ProjectSystem",
    "Project",
    "project_system",
    "PreferenceSystem",
    "preference_system",
    "SelfInitiatedMessageSystem",
    "self_initiated_message",
    "boundaries_system",
    "BoundariesSystem"
]
