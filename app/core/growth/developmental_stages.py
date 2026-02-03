# Astra Developmental Stages System
# DEPRECATED: This module is a thin wrapper. Use app.core.development.developmental_stage.developmental_tracker instead.
# Canonical stages: infancy, childhood, adolescence, young_adulthood, maturity (single source of truth).

import logging
from types import SimpleNamespace
from typing import Dict, Any

logger = logging.getLogger(__name__)


class DevelopmentalStagesSystem:
    """
    Thin wrapper delegating to the canonical DevelopmentalTracker.
    Use app.core.development.developmental_stage.developmental_tracker directly for new code.
    """

    @property
    def current_stage(self) -> SimpleNamespace:
        """Return an object with .value for backward compatibility (e.g. nascent, exploratory). Maps to canonical stage."""
        from app.core.development.developmental_stage import developmental_tracker
        return SimpleNamespace(value=developmental_tracker.get_current_stage().value)

    def get_developmental_summary(self) -> Dict[str, Any]:
        from app.core.development.developmental_stage import developmental_tracker
        return developmental_tracker.get_developmental_summary()

    def get_appropriate_support(self) -> Dict[str, Any]:
        from app.core.development.developmental_stage import developmental_tracker
        return developmental_tracker.get_appropriate_support()

    def get_voice_guidance(self) -> Dict[str, Any]:
        from app.core.development.developmental_stage import developmental_tracker
        return developmental_tracker.get_voice_guidance()


developmental_stages = DevelopmentalStagesSystem()
