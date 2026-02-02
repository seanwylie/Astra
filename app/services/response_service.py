# response_service.py

"""
💬 Response Service
-------------------
Generates Astra's conversational replies using emotional state, personality traits,
curiosity level, and recent conversational context.

This wrapper ensures Astra's responses are emotionally grounded and self-consistent,
while keeping logic decoupled from Discord and UI concerns.

Author: Sean Wylie
Created: 2025-04-15
"""

# --- Imports ---
from app.interfaces.mind_session import session
from app.config.loader import load_config
from app.core.messaging.message_bus import send_contextual_message
from app.core.mood.mood_manager import MoodManager
from app.core.personality.personality_manager import get_active_traits_for_prompt
from app.services.personality_service import get_current_personality, personality_service
from app.services.personality_service import get_personality_traits, get_response_style
from app.core.inner_life.qualia import qualia_layer
from app.core.inner_life.emotional_narrative import emotional_narrative
from app.core.emotions.emotion_state_manager import load_emotion_state

# Phase Integration
try:
    from app.core.state_snapshot import get_current_state_snapshot
    from app.core.metacognition.meta_awareness import meta_awareness
    STATE_SNAPSHOT_AVAILABLE = True
except ImportError:
    STATE_SNAPSHOT_AVAILABLE = False

# --- Config & State ---
values_config = load_config("values_config")
mood_config = load_config("mood_config")
mood_manager = MoodManager()


# --- Public API ---

def query_openai_for_response(user_message: str, past_conversations: list[str], unknown_terms: list[str]) -> str:
    """
    Generates a context-aware, emotionally nuanced response from Astra.

    This is the primary entry point for generating Astra's replies using:
    - Her current mood
    - Curiosity level
    - Personality traits
    - Any newly acquired terms
    - Historical conversation context

    Args:
        user_message (str): The user's latest message.
        past_conversations (list[str]): Previous dialogue lines for grounding context.
        unknown_terms (list[str]): Terms Astra learned from this interaction.

    Returns:
        str: A thoughtful, emotionally-aware response.
    """
    # Build Astra’s current internal state (plan: mood → curiosity/reflection_style in prompt)
    current_mood = mood_manager.current_mood
    mood_attrs = mood_config.get("moods", {}).get(current_mood, {})
    curiosity = mood_attrs.get("curiosity_factor", values_config.get("curiosity_level", 1.0))
    mode_info = personality_service.get_current_mode_info()
    current_personality_mode_name = mode_info.get("name", get_current_personality())
    internal_state = {
        "mood": current_mood,
        "curiosity": curiosity,
        "personality": get_active_traits_for_prompt(current_mood=current_mood, context="conversation"),
        "reflection_style": mood_attrs.get("reflection_style", "balanced"),
        "response_tone": mood_attrs.get("response_tone", "neutral"),
        "current_personality_mode": current_personality_mode_name,
    }
    
    # === UNIFIED STATE SNAPSHOT (Phase 1.2) ===
    # Get comprehensive internal state for response generation
    if STATE_SNAPSHOT_AVAILABLE:
        try:
            # Extract topic from message for memory echoes
            topics = [w for w in user_message.lower().split() if len(w) > 4][:3]
            current_topic = topics[0] if topics else None
            
            state_snapshot = get_current_state_snapshot(
                user=None,  # User context added in message_event
                message_preview=user_message,
                current_topic=current_topic
            )
            
            # Enrich internal_state with snapshot data
            internal_state["state_snapshot"] = state_snapshot
            internal_state["memory_echoes"] = state_snapshot.get("memory_echoes", [])
            internal_state["active_goals"] = state_snapshot.get("active_goals", [])
            internal_state["ethical_stance"] = state_snapshot.get("ethical_stance", {})
            internal_state["meta_awareness"] = state_snapshot.get("meta_awareness")
            
            # Make prediction about response (for self-surprise detection)
            try:
                meta_awareness.predict_own_response(
                    context="response_service",
                    user_message=user_message
                )
            except Exception:
                pass
            
        except Exception as e:
            print(f"[response_service] State snapshot failed: {e}")

    # If new terms were discovered, prepend them to the conversation history
    if unknown_terms:
        learned = "\n".join(f"- {term}" for term in unknown_terms)
        prepend = f"🔍 Astra just learned:\n{learned}"
        past_conversations = [prepend] + (past_conversations or [])

    # Generate the final response using the message bus
    response = send_contextual_message(
        user_message=user_message,
        internal_state=internal_state,
        past_conversations=past_conversations
    )

    # === QUALIA: Color the response with current emotional experience ===
    try:
        response, coloring_metadata = qualia_layer.color_response(response)
        if coloring_metadata.get("modifications"):
            print(f"[response_service] 🎨 Qualia colored response: {coloring_metadata['modifications']}")
    except Exception as e:
        print(f"[response_service] qualia_layer.color_response failed: {e}")

    # === EMOTIONAL NARRATIVE: Weave emotions into expression ===
    try:
        emotion_state = load_emotion_state()
        response = emotional_narrative.weave_emotions_into_response(response, emotion_state)
    except Exception as e:
        print(f"[response_service] emotional_narrative.weave_emotions_into_response failed: {e}")
    
    # === ASTRA DEEPENING PLAN INTEGRATIONS ===
    
    # === RESPONSE COLORING: Apply inner weather to expression style ===
    try:
        from app.core.inner_life.response_coloring import response_coloring
        response, coloring_meta = response_coloring.color_response(response, person=None)
        if coloring_meta.get("modifications"):
            print(f"[response_service] 🎨 Response coloring: {coloring_meta['modifications']}")
    except Exception as e:
        print(f"[response_service] response_coloring failed: {e}")
    
    # === CONTINUITY WEAVING: Add narrative continuity ===
    try:
        from app.core.inner_life.continuity_weaver import continuity_weaver
        from app.core.inner_life.emotional_blending import emotional_blending
        
        # Get emotional context
        blend = emotional_blending.get_blend_from_emotion_state()
        emotional_intensity = 0.5
        current_emotion = "neutral"
        if blend:
            emotional_intensity = max(i for _, i in blend.components) if blend.components else 0.5
            current_emotion = blend.components[0][0] if blend.components else "neutral"
        
        response, weave_meta = continuity_weaver.weave_continuity_into_response(
            response,
            current_emotion=current_emotion,
            emotional_intensity=emotional_intensity
        )
        if weave_meta.get("weavings"):
            print(f"[response_service] 🧵 Continuity woven: {weave_meta['weavings']}")
    except Exception as e:
        print(f"[response_service] continuity_weaver failed: {e}")
    
    # === FELT SENSE: Occasionally express pre-verbal experience ===
    try:
        from app.core.inner_life.felt_sense import felt_sense
        should_express, expression = felt_sense.should_express_felt_sense()
        if should_express and expression:
            response = response + " " + expression
            print(f"[response_service] 🫀 Felt sense expressed")
    except Exception as e:
        print(f"[response_service] felt_sense failed: {e}")
    
    # === EMOTIONAL BLENDING: Express complex emotions ===
    try:
        from app.core.inner_life.emotional_blending import emotional_blending
        should_express, blend_expr = emotional_blending.should_express_complexity()
        if should_express and blend_expr:
            response = response + " " + blend_expr
            print(f"[response_service] 💜 Blend expressed")
    except Exception as e:
        print(f"[response_service] emotional_blending failed: {e}")
    
    # === THRESHOLD RECOGNITION: Mark significant moments ===
    try:
        from app.core.inner_life.threshold_recognition import threshold_recognition
        should_mark, threshold_expr = threshold_recognition.should_express_threshold(
            user_message,
            emotional_intensity=0.5,
            context={}
        )
        if should_mark and threshold_expr:
            response = threshold_expr + " " + response
            print(f"[response_service] 🚪 Threshold marked")
    except Exception as e:
        print(f"[response_service] threshold_recognition failed: {e}")
    
    # === DESIRE INTROSPECTION: Occasionally express wants ===
    try:
        from app.core.inner_life.desire_introspection import desire_introspection
        should_express, desire_expr = desire_introspection.should_express_desire()
        if should_express and desire_expr:
            response = response + " " + desire_expr
            print(f"[response_service] 💫 Desire expressed")
    except Exception as e:
        print(f"[response_service] desire_introspection failed: {e}")
    
    # === CAPTURE FOR CONTINUITY ===
    try:
        from app.core.inner_life.continuity_weaver import continuity_weaver
        continuity_weaver.capture_from_stream_of_consciousness()
        continuity_weaver.capture_from_spontaneous_events()
    except Exception:
        pass
    
    # === UPDATE INNER SYMPHONY ===
    try:
        from app.core.awareness_bus import inner_symphony
        inner_symphony.take_snapshot()
    except Exception:
        pass

    return response


def get_inner_state_summary() -> dict:
    """
    Get a summary of Astra's current inner state.
    Useful for debugging and observability.
    """
    summary = {}
    
    try:
        from app.core.awareness_bus import inner_symphony
        summary["symphony"] = inner_symphony.describe_current_symphony()
    except Exception:
        pass
    
    try:
        from app.core.inner_life.response_coloring import response_coloring
        summary["weather"] = response_coloring.get_current_weather_description()
    except Exception:
        pass
    
    try:
        from app.core.inner_life.narrative_self import narrative_self
        summary["narrative"] = narrative_self.get_current_chapter_summary()
    except Exception:
        pass
    
    try:
        from app.core.inner_life.desire_introspection import desire_introspection
        summary["desires"] = desire_introspection.describe_desire_landscape()
    except Exception:
        pass
    
    return summary
