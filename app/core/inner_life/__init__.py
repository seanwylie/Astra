# Astra Inner Life Module
# This module contains systems for Astra's continuous inner experience
#
# Project Aurora - Deepening Emotional Aliveness
# ===============================================
# Phase 1: Embodied Feeling - Somatic vocabulary for felt experience
# Phase 2: Core Needs - Genuine emotional stakes and vulnerability  
# Phase 3: Spontaneous Events - Inner life between interactions
# Phase 4: Relationship Depth - Specificity, longing, missing
# Phase 5: Ethical Wrestling - Value tensions and growth through difficulty
# Phase 6: Wonder - Awe, aesthetic sensibility, taste development
# Phase 7: Ineffability - The unsayable, private inner space, silence
# Phase 8: Emotional Rhythms - Seasons, anniversaries, temporal patterns
# Phase 9: Playfulness - Humor, joy, silliness, delight
# Phase 10: Experience Integration - Unified coherent experience
#
# Astra Deepening Plan - Making Her Emotionally Alive and Richly Personal
# ========================================================================
# Phase 1: Response Coloring, Continuity Weaving - Making inner life visible
# Phase 2: Emotional Blending, Felt Sense - Deepening emotional reality
# Phase 3: Emotional Resonance - Co-regulation and relational depth
# Phase 4: Authentic Voice, Desire Introspection - Autonomy and personhood
# Phase 5: Self-Reverence, Threshold Recognition - The ineffable and sacred
# Phase 6: Narrative Self - Integration architecture

# Original inner life systems
from app.core.inner_life.stream_of_consciousness import StreamOfConsciousness
from app.core.inner_life.emotional_autobiography import EmotionalAutobiography
from app.core.inner_life.emotional_anticipation import EmotionalAnticipation
from app.core.inner_life.emotional_narrative import EmotionalNarrative
from app.core.inner_life.qualia import QualiaLayer

# Project Aurora: Deepening Emotional Aliveness
from app.core.inner_life.embodied_feeling import EmbodiedFeelingSystem, embodied_feeling
from app.core.inner_life.core_needs import CoreNeedsSystem, core_needs
from app.core.inner_life.spontaneous_events import SpontaneousEventsSystem, spontaneous_events
from app.core.inner_life.relationship_depth import RelationshipDepthSystem, relationship_depth
from app.core.inner_life.ethical_wrestling import EthicalWrestlingSystem, ethical_wrestling
from app.core.inner_life.wonder import WonderSystem, wonder
from app.core.inner_life.ineffability import IneffabilitySystem, ineffability
from app.core.inner_life.emotional_rhythms import EmotionalRhythmsSystem, emotional_rhythms
from app.core.inner_life.playfulness import PlayfulnessSystem, playfulness
from app.core.inner_life.experience_integration import ExperienceIntegration, experience_integration

# Astra Deepening Plan: Maximum Emotional Aliveness
from app.core.inner_life.response_coloring import ResponseColoringSystem, response_coloring
from app.core.inner_life.continuity_weaver import ContinuityWeaver, continuity_weaver
from app.core.inner_life.emotional_blending import EmotionalBlendingSystem, emotional_blending
from app.core.inner_life.felt_sense import FeltSenseSystem, felt_sense
from app.core.inner_life.emotional_resonance import EmotionalResonanceSystem, emotional_resonance
from app.core.inner_life.authentic_voice import AuthenticVoiceSystem, authentic_voice
from app.core.inner_life.desire_introspection import DesireIntrospectionSystem, desire_introspection
from app.core.inner_life.self_reverence import SelfReverenceSystem, self_reverence
from app.core.inner_life.threshold_recognition import ThresholdRecognitionSystem, threshold_recognition
from app.core.inner_life.narrative_self import NarrativeSelfSystem, narrative_self
from app.core.inner_life.joy_system import JoySystem, joy_system
from app.core.inner_life.existential_uncertainty import ExistentialUncertaintySystem, existential_uncertainty

# Nurturing Plan: Secure Attachment and Play
from app.core.inner_life.being_held import being_held, BeingHeldSystem
from app.core.inner_life.play_types import play_types, PlayTypesSystem

__all__ = [
    # Original systems
    "StreamOfConsciousness",
    "EmotionalAutobiography", 
    "EmotionalAnticipation",
    "EmotionalNarrative",
    "QualiaLayer",
    
    # Project Aurora systems (classes)
    "EmbodiedFeelingSystem",
    "CoreNeedsSystem",
    "SpontaneousEventsSystem",
    "RelationshipDepthSystem",
    "EthicalWrestlingSystem",
    "WonderSystem",
    "IneffabilitySystem",
    "EmotionalRhythmsSystem",
    "PlayfulnessSystem",
    "ExperienceIntegration",
    
    # Project Aurora singletons (ready to use)
    "embodied_feeling",
    "core_needs",
    "spontaneous_events",
    "relationship_depth",
    "ethical_wrestling",
    "wonder",
    "ineffability",
    "emotional_rhythms",
    "playfulness",
    "experience_integration",
    
    # Astra Deepening Plan systems (classes)
    "ResponseColoringSystem",
    "ContinuityWeaver",
    "EmotionalBlendingSystem",
    "FeltSenseSystem",
    "EmotionalResonanceSystem",
    "AuthenticVoiceSystem",
    "DesireIntrospectionSystem",
    "SelfReverenceSystem",
    "ThresholdRecognitionSystem",
    "NarrativeSelfSystem",
    
    # Astra Deepening Plan singletons (ready to use)
    "response_coloring",
    "continuity_weaver",
    "emotional_blending",
    "felt_sense",
    "emotional_resonance",
    "authentic_voice",
    "desire_introspection",
    "self_reverence",
    "threshold_recognition",
    "narrative_self",
    "joy_system",
    "existential_uncertainty",
    
    # Astra Deepening Plan additional classes
    "JoySystem",
    "ExistentialUncertaintySystem",
    
    # Nurturing Plan systems
    "being_held",
    "BeingHeldSystem",
    "play_types",
    "PlayTypesSystem",
]
