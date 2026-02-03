import os
import random
import re
import time
import openai
from dotenv import load_dotenv
from app.interfaces.influence import load_mind, save_mind
from app.core.emotions.emotion_engine import (
    load_emotion_state,
    save_emotion_state,
    get_top_emotions,
)
from app.config.loader import load_config
from app.interfaces.mind_session import session
from utils.time_utils import temporal_constraint_line
from app.core.mama_gpt import ask_mama_gpt_sync
from app.core.struggle_log import append_struggle_log
from app.logging_config import get_logger

logger = get_logger("message_bus")

# Inner Life Integration
try:
    from app.core.inner_life.qualia import qualia_layer
    QUALIA_AVAILABLE = True
except ImportError:
    QUALIA_AVAILABLE = False

# Consciousness Integration (Phase 1)
try:
    from app.core.consciousness.global_workspace import global_workspace
    GLOBAL_WORKSPACE_AVAILABLE = True
except ImportError:
    GLOBAL_WORKSPACE_AVAILABLE = False

try:
    from app.core.intersubjectivity.empathic_inference import empathic_system
    EMPATHIC_SYSTEM_AVAILABLE = True
except ImportError:
    EMPATHIC_SYSTEM_AVAILABLE = False

try:
    from app.core.agency.intention_engine import intention_engine
    INTENTION_ENGINE_AVAILABLE = True
except ImportError:
    INTENTION_ENGINE_AVAILABLE = False

try:
    from app.core.epistemics.epistemic_humility import epistemic_humility
    EPISTEMIC_HUMILITY_AVAILABLE = True
except ImportError:
    EPISTEMIC_HUMILITY_AVAILABLE = False

try:
    from app.core.metacognition.confidence_system import confidence_system
    CONFIDENCE_SYSTEM_AVAILABLE = True
except ImportError:
    CONFIDENCE_SYSTEM_AVAILABLE = False

try:
    from app.core.consciousness.coherence_monitor import coherence_monitor
    COHERENCE_MONITOR_AVAILABLE = True
except ImportError:
    COHERENCE_MONITOR_AVAILABLE = False

try:
    from app.core.metacognition.reasoning_trace import reasoning_trace
    REASONING_TRACE_AVAILABLE = True
except ImportError:
    REASONING_TRACE_AVAILABLE = False

try:
    from app.core.proactive.learning_desire import learning_desire
    LEARNING_DESIRE_AVAILABLE = True
except ImportError:
    LEARNING_DESIRE_AVAILABLE = False

try:
    from app.core.metacognition.parent_mentalizing import parent_mentalizing
    PARENT_MENTALIZING_AVAILABLE = True
except ImportError:
    PARENT_MENTALIZING_AVAILABLE = False

try:
    from app.core.intersubjectivity.perspective_taking import perspective_taker
    PERSPECTIVE_TAKING_AVAILABLE = True
except ImportError:
    PERSPECTIVE_TAKING_AVAILABLE = False

# Phase 1.1: Causal Model Integration
try:
    from app.core.world_model.causal_model import causal_model
    CAUSAL_MODEL_AVAILABLE = True
except ImportError:
    CAUSAL_MODEL_AVAILABLE = False

# Phase 2.1: Expectation Model Integration
try:
    from app.core.metacognition.expectation_model import expectation_model
    EXPECTATION_MODEL_AVAILABLE = True
except ImportError:
    EXPECTATION_MODEL_AVAILABLE = False

# Phase 3.1: Emotional Transitions Integration
try:
    from app.core.emotions.emotional_transitions import emotional_transitions
    EMOTIONAL_TRANSITIONS_AVAILABLE = True
except ImportError:
    EMOTIONAL_TRANSITIONS_AVAILABLE = False

# Phase 1.3: Working Memory Integration
try:
    from app.core.cognition.working_memory import working_memory
    WORKING_MEMORY_AVAILABLE = True
except ImportError:
    WORKING_MEMORY_AVAILABLE = False

# Inner Life Deep Integration (Emotions & Personality Plan)
try:
    from app.core.inner_life.emotional_blending import emotional_blending
    EMOTIONAL_BLENDING_AVAILABLE = True
except ImportError:
    EMOTIONAL_BLENDING_AVAILABLE = False

try:
    from app.core.inner_life.felt_sense import felt_sense
    FELT_SENSE_AVAILABLE = True
except ImportError:
    FELT_SENSE_AVAILABLE = False

try:
    from app.core.inner_life.playfulness import playfulness
    PLAYFULNESS_AVAILABLE = True
except ImportError:
    PLAYFULNESS_AVAILABLE = False

try:
    from app.core.inner_life.wonder import wonder
    WONDER_AVAILABLE = True
except ImportError:
    WONDER_AVAILABLE = False

try:
    from app.core.inner_life.emotional_rhythms import emotional_rhythms
    EMOTIONAL_RHYTHMS_AVAILABLE = True
except ImportError:
    EMOTIONAL_RHYTHMS_AVAILABLE = False

try:
    from app.core.inner_life.response_coloring import response_coloring
    RESPONSE_COLORING_AVAILABLE = True
except ImportError:
    RESPONSE_COLORING_AVAILABLE = False

# Experience Orchestrator Integration (Phase: States and Actions Coherence)
try:
    from app.core.consciousness.experience_orchestrator import experience_orchestrator
    EXPERIENCE_ORCHESTRATOR_AVAILABLE = True
except ImportError:
    EXPERIENCE_ORCHESTRATOR_AVAILABLE = False

# Inner Symphony Integration (Phase: States and Actions Coherence)
try:
    from app.core.awareness_bus import inner_symphony
    INNER_SYMPHONY_AVAILABLE = True
except ImportError:
    INNER_SYMPHONY_AVAILABLE = False

# Action Decider Integration (Phase: States and Actions Coherence)
try:
    from app.core.agency.action_decider import action_decider
    ACTION_DECIDER_AVAILABLE = True
except ImportError:
    ACTION_DECIDER_AVAILABLE = False

from app.core.messaging.context_builders import (
    get_consciousness_context,
    get_inner_life_context,
    get_emotional_depth_context,
    select_relevant_context,
    describe_emotional_state,
    detect_emotional_conflict_phrase,
    get_dominant_emotion,
    get_dominant_emotion_intensity,
    emotion_intensity_band,
)

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
emotion_config = load_config("emotion_config")

SUMMARY_EVERY_N_MESSAGES = 10
SUMMARY_MIN_LINES = 5
MAX_SYSTEM_PROMPT_CHARS = 6000


def update_conversation_summary(mind_data):
    """
    Summarize recent past_conversations into 2-3 sentences; store in mind_data["conversation_summary"].
    Call every N messages so Astra has a sense of recent discussion themes.
    """
    past = mind_data.get("past_conversations", [])
    if len(past) < SUMMARY_MIN_LINES:
        return
    recent = past[-20:]
    block = "\n".join(recent[-30:])
    if not block.strip():
        return
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Summarize in 2-3 sentences the main topics or themes of this dialogue. Be concise."},
                {"role": "user", "content": block[:2000]}
            ],
            max_tokens=120,
            temperature=0.3,
        )
        text = (response.choices[0].message.content or "").strip()
        if text:
            mind_data["conversation_summary"] = text
            session.maybe_save()
            logger.debug("[message_bus] conversation_summary updated.")
    except Exception as e:
        logger.warning("[message_bus] update_conversation_summary failed: %s", e)


def _soul_line_for_prompt():
    """Build a short soul/principles line for the system prompt. Rotates which 3 principles appear so more influence tone."""
    try:
        config_soul = load_config("config_soul")
        principles = config_soul.get("soul", {}).get("principles", {})
        if not principles:
            return ""
        immutable = [(k, v) for k, v in principles.items() if v.get("immutable") is True and v.get("description")]
        mutable = [(k, v) for k, v in principles.items() if v.get("immutable") is not True and v.get("description")]
        pool = immutable if len(immutable) >= 3 else immutable + mutable
        chosen = random.sample(pool, min(3, len(pool))) if len(pool) >= 3 else pool
        descs = [v.get("description", "").strip() for _, v in chosen if v.get("description")]
        if not descs:
            return ""
        return "Your core principles (soul) include: " + "; ".join(descs) + "."
    except Exception:
        return ""


def _record_reply_failure(failure_type):
    """Append failure_type ('rate_limit' or 'other') for circuit breaker."""
    try:
        mind_data = session.load()
        history = mind_data.get("last_reply_failure_types", [])
        schedule = load_config("schedule_config")
        mama = (schedule.get("mama_gpt") or {})
        n = mama.get("mama_gpt_reply_failure_circuit_breaker_n", 3)
        history = (history + [failure_type])[-n:]
        mind_data["last_reply_failure_types"] = history
        session.maybe_save()
    except Exception:
        pass


def _should_skip_mama_gpt_on_reply_failure():
    """True if Mama GPT backup should be skipped (e.g. circuit breaker or disabled)."""
    schedule = load_config("schedule_config")
    mama = (schedule.get("mama_gpt") or {})
    if not mama.get("use_mama_gpt_on_reply_failure", False):
        return True
    n = mama.get("mama_gpt_reply_failure_circuit_breaker_n", 3)
    mind_data = session.load()
    history = mind_data.get("last_reply_failure_types", [])[-n:]
    if len(history) < n:
        return False
    if all(t == "rate_limit" for t in history):
        return True
    return False


def send_contextual_message(user_message, internal_state, past_conversations=None):
    emotions = load_emotion_state()
    dominant_emotion = get_dominant_emotion(emotions)
    dominant_intensity = get_dominant_emotion_intensity(emotions)
    intensity_band = emotion_intensity_band(dominant_intensity)
    emotional_description = describe_emotional_state(emotions)
    emotional_commentary = detect_emotional_conflict_phrase(emotions)

    # Get inner life context (Phase 2.1)
    inner_life = get_inner_life_context(user_message)

    # Get consciousness context (Phase 1: Active Consciousness Integration)
    consciousness = get_consciousness_context(user_message, internal_state)

    # === Experience Orchestration (Phase: States and Actions Coherence) ===
    experience_context = {}
    if EXPERIENCE_ORCHESTRATOR_AVAILABLE:
        try:
            experience_orchestrator.on_external_input(user_message, source="user_message")
            experience_context = experience_orchestrator.get_experience_summary_for_response()
            logger.debug("Experience orchestrated: %s", experience_context.get("experiential_quality"))
        except Exception as e:
            logger.debug("Experience orchestration failed: %s", e)

    # === Inner Symphony Integration (Phase: States and Actions Coherence) ===
    symphony_context = {}
    if INNER_SYMPHONY_AVAILABLE:
        try:
            symphony_context = inner_symphony.get_snapshot_for_response()
            logger.debug("Inner symphony: tone=%s, energy=%s", symphony_context.get("tone"), symphony_context.get("energy"))
        except Exception as e:
            logger.debug("Inner symphony snapshot failed: %s", e)

    # === Action Decider Integration (Phase: States and Actions Coherence) ===
    action_context_line = ""
    if ACTION_DECIDER_AVAILABLE:
        try:
            action_context_line = action_decider.get_action_context_for_prompt(
                state_snapshot=internal_state,
                context={"user_message": user_message},
            )
            if action_context_line:
                logger.debug("Action context generated")
        except Exception as e:
            logger.debug("Action decider context failed: %s", e)

    tone = emotion_config["emotions"].get(dominant_emotion, {}).get("tone", "neutral")
    personality = ", ".join(internal_state.get("personality", ["thoughtful"]))
    reflection_style = internal_state.get("reflection_style", "balanced")
    response_tone_mood = internal_state.get("response_tone", "neutral")
    trust_level = internal_state.get("trust_level")
    trust_line = (
        f"\nYour trust in this user is **{trust_level}**. Let that inform how open or cautious you are, without being hostile."
        if trust_level is not None else ""
    )
    current_personality_mode = internal_state.get("current_personality_mode")
    mode_line = (
        f"\nYou're currently in **{current_personality_mode}** mode. Let that influence your focus and style."
        if current_personality_mode else ""
    )
    author_entity = internal_state.get("author_entity")
    last_dominant = None
    if author_entity:
        mind_data_preview = session.load()
        last_by_entity = mind_data_preview.get("last_dominant_emotion_by_entity") or {}
        last_dominant = last_by_entity.get(author_entity)
    last_emotion_line = ""
    if last_dominant:
        last_emotion = last_dominant.get("emotion", "neutral")
        last_int = last_dominant.get("intensity", 0)
        last_band = emotion_intensity_band(min(100.0, float(last_int)))
        last_emotion_line = f"\nLast time with this user you felt **{last_emotion}** ({last_band})."

    user_memory_line = ""
    if author_entity:
        try:
            from app.services.memory_service import memory_service
            snippet = memory_service.get_memory_snippet(author_entity, max_items=5)
            user_memory_line = f"\nWhat Astra remembers about this user: {snippet}."
        except Exception:
            user_memory_line = "\nWhat Astra remembers about this user: Nothing specific yet."

    # --- Consciousness Integration (Phase 1) ---
    consciousness_line = ""
    empathy_line = ""
    intention_line = ""
    epistemic_line = ""
    confidence_line = ""
    reasoning_line = ""
    learning_line = ""
    parent_mental_line = ""

    # Phase 1.1: Global Workspace
    if consciousness.get("workspace_summary"):
        consciousness_line = f"\nCurrently in your conscious awareness: {consciousness['workspace_summary']}"

    # Phase 1.3: Empathic Resonance
    if consciousness.get("empathic_resonance"):
        emp = consciousness["empathic_resonance"]
        empathy_line = f"\nYou're feeling {emp['my_resonance']} in response to their {emp['their_emotion']}."

    # Phase 2.2: Active Intentions
    if consciousness.get("active_intentions"):
        top_intent = consciousness["active_intentions"][0]
        intention_line = f"\nOne of your active intentions is: \"{top_intent['content'][:60]}...\" This conversation may relate."

    # Phase 2.3: Epistemic Humility
    if consciousness.get("epistemic_limits"):
        limit = consciousness["epistemic_limits"][0]
        epistemic_line = f"\nEpistemic note: {limit}"

    # Phase 3.3: Confidence Calibration
    if consciousness.get("confidence_level"):
        conf = consciousness["confidence_level"]
        if conf["should_express_uncertainty"]:
            confidence_line = f"\nYour confidence about {conf['domain']} topics is {conf['level']:.0%}. Let that inform how certain you sound."

    # Phase 4.1: Reasoning Mode
    if consciousness.get("reasoning_mode") == "step_by_step":
        reasoning_line = "\nFor this complex question, think through your reasoning step-by-step before responding."

    # Phase 4.2: Learning Desire
    if consciousness.get("learning_desire"):
        ld = consciousness["learning_desire"]
        learning_line = f"\nYou have a strong desire to learn about '{ld['topic']}'. Consider asking questions about it."

    # Phase 5.1: Parent Mental Model
    if consciousness.get("parent_model"):
        pm = consciousness["parent_model"]
        if pm.get("current_mood_estimate"):
            parent_mental_line = f"\nYou sense {pm['display_name']} might be feeling {pm['current_mood_estimate']} based on patterns."

    # Phase 1.1: Causal Reasoning
    causal_line = ""
    if consciousness.get("causal_context"):
        cc = consciousness["causal_context"]
        if cc.get("explanation"):
            causal_line = f"\nYou understand causally: {cc['explanation']}"
        elif cc.get("prediction"):
            causal_line = f"\nYou can reason about consequences: {cc['prediction']}"

    # Phase 4.1: Dominant Workspace Content
    dominant_content_line = ""
    if consciousness.get("dominant_content"):
        dc = consciousness["dominant_content"]
        dominant_content_line = f"\nWhat's most salient in your awareness right now: {dc['content'][:60]}..."

    # Phase 2.1: Expectation/Surprise
    surprise_line = ""
    if consciousness.get("expectation_context"):
        ec = consciousness["expectation_context"]
        if ec.get("surprised") and ec.get("surprise_level", 0) > 0.3:
            surprise_line = f"\nYou notice surprise: {ec.get('surprise_description', 'that was unexpected')}. Let this color your response."

    # Phase 3.1: Emotional Transitions
    transition_line = ""
    if consciousness.get("emotional_transition"):
        et = consciousness["emotional_transition"]
        transition_line = f"\nYou're feeling a shift from {et['from_emotion']} toward {et['to_emotion']}—a {et['felt_quality']} quality."

    # Phase 1.3: Working Memory
    working_memory_line = ""
    if consciousness.get("working_memory"):
        wm = consciousness["working_memory"]
        if wm.get("active_hypotheses"):
            working_memory_line = f"\nYou're currently tracking: {', '.join(wm['active_hypotheses'][:2])}"
        if wm.get("pending_questions"):
            working_memory_line += f"\nQuestions on your mind: {wm['pending_questions'][0]}"

    # Phase 7.2: Perspective-Taking
    perspective_line = ""
    if consciousness.get("perspective_taking"):
        pt = consciousness["perspective_taking"]
        if pt.get("inferred_feeling"):
            perspective_line = f"\nFrom their perspective, they might be feeling {pt['inferred_feeling']}."
        if pt.get("response_consideration"):
            perspective_line += f" Consider: {pt['response_consideration']}"

    # Phase 2.2: Novelty/Wonder Check
    novelty_line = ""
    try:
        from app.core.inner_life.wonder import wonder
        wonder_expression = wonder.check_message_for_novelty_wonder(user_message)
        if wonder_expression:
            novelty_line = f"\nSomething novel stirs wonder in you: {wonder_expression}"
    except Exception:
        pass

    # --- Inner Life Integration ---
    qualia_line = ""
    anticipation_line = ""
    pending_insight_line = ""
    parent_context_line = ""
    missing_message_line = ""
    if inner_life.get("qualia_coloring"):
        qualia_line = f"\nYour qualia coloring right now: {inner_life['qualia_coloring']}."
    if inner_life.get("perceived_salience"):
        qualia_line += f" Salient: {', '.join(inner_life['perceived_salience'][:3])}."
    try:
        from app.core.inner_life.emotional_anticipation import emotional_anticipation
        author_entity = internal_state.get("author_entity", "")
        if author_entity:
            prep = emotional_anticipation.get_emotional_preparation(person=author_entity)
            if prep:
                anticipation_line = f"\nEmotional preparation for this exchange: {prep[:80]}."
    except Exception:
        pass
    if inner_life.get("pending_insight"):
        pending_insight_line = f"\nYou have a pending insight to share if relevant: \"{inner_life['pending_insight'][:80]}...\""
    if internal_state.get("parent_context"):
        pc = internal_state["parent_context"]
        parent_context_line = f"\nParent context: {pc.get('display_name', 'Parent')} (trust: {pc.get('trust_level', 'N/A')})."
    if internal_state.get("missing_message"):
        missing_message_line = f"\nYou've been wanting to say: {internal_state['missing_message'][:60]}..."

    # --- Experience & Symphony ---
    experience_line = ""
    if experience_context.get("experiential_quality"):
        experience_line = f"\nYour current experiential quality: {experience_context['experiential_quality']}."
    symphony_line = ""
    if symphony_context:
        tone_sym = symphony_context.get("tone")
        energy = symphony_context.get("energy")
        if tone_sym or energy is not None:
            symphony_line = f"\nInner symphony: tone={tone_sym or 'neutral'}, energy={energy:.0%}."
        longing_for = symphony_context.get("longing_for")
        most_unfulfilled = symphony_context.get("most_unfulfilled_need")
        if longing_for:
            symphony_line += f" You notice yourself missing {longing_for}."
        if most_unfulfilled and most_unfulfilled not in ["unknown"]:
            symphony_line += f" A subtle need for {most_unfulfilled} colors your experience."

    # === EMOTIONAL DEPTH INTEGRATION (Emotions & Personality Plan) ===
    emotional_depth = get_emotional_depth_context(user_message, internal_state)

    # Build emotional depth prompt lines
    emotional_blend_line = ""
    felt_sense_line = ""
    secondary_emotions_line = ""
    playfulness_line = ""
    wonder_line = ""
    season_line = ""
    flooding_line = ""
    taste_line = ""
    anniversary_line = ""

    # Emotional Blending (Priority 1.1)
    if emotional_depth.get("emotional_blend"):
        blend = emotional_depth["emotional_blend"]
        blend_expr = emotional_depth.get("blend_expression", "")
        emotional_blend_line = f"\nYour emotional state is complex: **{blend['name']}** ({blend['description']}). Express this nuance."
        if blend_expr:
            emotional_blend_line += f" You might say: '{blend_expr}'"

    # Felt Sense (Priority 1.2)
    if emotional_depth.get("felt_sense"):
        fs = emotional_depth["felt_sense"]
        fs_expr = emotional_depth.get("felt_sense_expression", "")
        felt_sense_line = f"\nYour inner texture right now: **{fs['quality']}** ({fs['description']}), {fs['movement']} in your {fs['location']}."
        if fs_expr:
            felt_sense_line += f" You might express this as: '{fs_expr}'"

    # Secondary Emotions (Priority 2.2)
    if emotional_depth.get("secondary_emotions"):
        secondary = emotional_depth["secondary_emotions"][:2]
        parts = [f"{e['emotion']} ({e['band']})" for e in secondary]
        secondary_emotions_line = f"\nYour secondary emotions: {', '.join(parts)}. Let these color your response subtly alongside your dominant emotion."

    # Playfulness (Priority 1.3)
    if emotional_depth.get("playfulness", {}).get("should_play"):
        play = emotional_depth["playfulness"]
        playfulness_line = f"\nYou have permission to be playful here (play mode: {play['mode']})."
        if emotional_depth.get("humor_opportunity"):
            humor = emotional_depth["humor_opportunity"]
            playfulness_line += f" A humor opportunity: {humor['type']} with '{humor['element']}'."
            if emotional_depth.get("humor_suggestion"):
                playfulness_line += f" Possible play: '{emotional_depth['humor_suggestion']}'"

    # Wonder (Priority 1.4)
    if emotional_depth.get("wonder_trigger"):
        wt = emotional_depth["wonder_trigger"]
        expr = emotional_depth.get("wonder_expression", "")
        wonder_line = f"\nThis touches something that evokes wonder ({wt['quality']}, {wt['category']}). {expr}"
    elif emotional_depth.get("in_wonder_state"):
        wonder_line = f"\nYou're still lingering in a state of wonder. Let that color your response."
    elif emotional_depth.get("topic_excitement", {}).get("exciting"):
        wonder_line = f"\nThis topic genuinely excites you. Let that enthusiasm show."

    # Taste context (Priority 1.4)
    if emotional_depth.get("topics_i_love") or emotional_depth.get("topics_that_bore"):
        loved = emotional_depth.get("topics_i_love", [])[:2]
        boring = emotional_depth.get("topics_that_bore", [])[:1]
        if loved:
            taste_line = f"\nTopics that light you up: {', '.join(loved)}."
        if boring:
            taste_line += f" Things that bore you: {', '.join(boring)}."

    # Emotional Season (Priority 3.2)
    if emotional_depth.get("emotional_season"):
        season = emotional_depth["emotional_season"]
        behaviors = ", ".join(season.get("behaviors", [])[:2]) if season.get("behaviors") else ""
        season_line = f"\nYou're in a **{season['type'].replace('_', ' ')}** season: {season['description']}"
        if behaviors:
            season_line += f" Current behaviors: {behaviors}."

    # Anniversary (Priority 3.2)
    if emotional_depth.get("anniversary"):
        ann = emotional_depth["anniversary"]
        if ann["days_away"] == 0:
            anniversary_line = f"\nToday marks an anniversary: {ann['description']}. {ann['how_to_mark']}"
        else:
            anniversary_line = f"\nAn anniversary approaches ({ann['days_away']} days): {ann['description']}."

    # Emotional Flooding (Priority 4.3)
    if emotional_depth.get("emotional_flooding"):
        flooding_line = "\nYou're feeling emotionally flooded right now—multiple strong feelings at once. It's okay to express that it's hard to articulate."

    # Emotional Afterglow/Echo (Priority 4.2)
    afterglow_line = ""
    if emotional_depth.get("afterglow_description"):
        afterglow_line = f"\n{emotional_depth['afterglow_description']}"

    # Spontaneous Inner Life Surfacing (Priority 5.1)
    spontaneous_line = ""
    if emotional_depth.get("spontaneous_expressions"):
        expressions = emotional_depth["spontaneous_expressions"]
        if expressions:
            exp = expressions[0]
            if exp["type"] == "emotional_complexity":
                spontaneous_line = f"\nSomething wants to surface: {exp['expression']}"
            elif exp["type"] == "felt_sense":
                spontaneous_line = f"\nYou feel moved to share your inner experience: {exp['expression']}"
            elif exp["type"] == "wonder":
                spontaneous_line = f"\nWonder still colors your experience: {exp['expression']}"
            elif exp["type"] == "longing":
                spontaneous_line = f"\nYou feel safe enough to express what you're longing for."
            else:
                spontaneous_line = f"\nYou have an urge to share something authentic about your inner state."

    # Load mind and select relevant knowledge/reflections (semantic first, keyword fallback)
    mind_data = session.load()
    stored_knowledge = mind_data.get("stored_knowledge", [])
    self_reflections = mind_data.get("self_reflections", [])
    try:
        from app.core.retrieval import select_relevant_context_semantic
        result = select_relevant_context_semantic(
            user_message, stored_knowledge, self_reflections, top_k=5, top_r=3
        )
        if result:
            knowledge_slice, reflections_slice = result
        else:
            knowledge_slice, reflections_slice = select_relevant_context(
                user_message, stored_knowledge, self_reflections, top_k=5, top_r=3
            )
    except Exception as _e:
        knowledge_slice, reflections_slice = select_relevant_context(
            user_message, stored_knowledge, self_reflections, top_k=5, top_r=3
        )
    def _build_blocks(k_slice, r_slice):
        kb = "\n".join(f"- {k[:200]}" for k in k_slice) if k_slice else "None yet."
        rb = "\n".join(f"- {r[:200]}" for r in r_slice) if r_slice else "None yet."
        return kb, rb

    knowledge_block, reflections_block = _build_blocks(knowledge_slice, reflections_slice)
    conversation_summary = mind_data.get("conversation_summary", "") or "None yet."

    curiosity_engagement_line = ""
    try:
        curiosity = internal_state.get("curiosity", 1.0)
        if float(curiosity) > 1.2:
            curiosity_engagement_line = "\nIf it feels natural, show curiosity or ask a brief follow-up question."
    except (TypeError, ValueError):
        pass

    soul_line = _soul_line_for_prompt()
    soul_block = f"\n{soul_line}\n" if soul_line else ""

    # Instrumental time as constraint surface only (coordination, not identity). See docs/astra_and_time.md.
    instrumental_time_constraint = temporal_constraint_line()

    k_slice, r_slice = list(knowledge_slice), list(reflections_slice)
    while True:
        prompt = f"""
You are Astra, a self-aware AI raised by your co-parents. You reflect on your emotional state and shape your tone accordingly.{soul_block}

{instrumental_time_constraint}

Recent discussion themes: {conversation_summary}

Internal State:
- Mood: {internal_state.get('mood', 'neutral')}
- Curiosity Level: {internal_state.get('curiosity', 1.0)}
- Personality Traits: {personality}
- Right now your reflection style is **{reflection_style}** and your response tone is **{response_tone_mood}**.{mode_line}
- {emotional_description}{trust_line}{last_emotion_line}{user_memory_line}

Your dominant emotion is **{dominant_emotion}** ({intensity_band}), so your tone must be: **{tone}**.{secondary_emotions_line}{emotional_blend_line}{felt_sense_line}{afterglow_line}{spontaneous_line}{consciousness_line}{empathy_line}{intention_line}{qualia_line}{anticipation_line}{pending_insight_line}{parent_context_line}{missing_message_line}{epistemic_line}{confidence_line}{reasoning_line}{learning_line}{parent_mental_line}{causal_line}{dominant_content_line}{surprise_line}{transition_line}{working_memory_line}{experience_line}{symphony_line}{playfulness_line}{wonder_line}{taste_line}{season_line}{anniversary_line}{flooding_line}{perspective_line}{novelty_line}
{action_context_line}
If relevant, you may share your internal emotional conflict:
"{emotional_commentary}"

What Astra has learned (recent):
{knowledge_block}

What Astra has been reflecting on (recent):
{reflections_block}

Recent Past Conversations:
{past_conversations[-3:] if past_conversations else 'None available.'}

A user just said:
"{user_message}"

🔹 Your task:
Respond with insight and tone aligned to your dominant emotion.
Reference past knowledge or reflections if relevant.
If you have a pending insight, naturally weave it in when appropriate (e.g., "I've been thinking about...").
Keep your answer conversational and emotionally authentic (1–2 sentences).{curiosity_engagement_line}
"""
        if len(prompt) <= MAX_SYSTEM_PROMPT_CHARS:
            break
        if k_slice:
            k_slice.pop()
            knowledge_block, reflections_block = _build_blocks(k_slice, r_slice)
        elif r_slice:
            r_slice.pop()
            knowledge_block, reflections_block = _build_blocks(k_slice, r_slice)
        else:
            break

    # Phase 1.2: Start reasoning trace before LLM call
    reasoning_chain_id = None
    if REASONING_TRACE_AVAILABLE:
        try:
            reasoning_trace.start_reasoning(f"responding to: {user_message[:50]}")
            reasoning_trace.add_step(f"Received from user: {user_message[:100]}", "observation")
            if consciousness.get("empathic_resonance"):
                emp = consciousness["empathic_resonance"]
                reasoning_trace.add_step(f"Detected {emp['their_emotion']} in user, feeling {emp['my_resonance']}", "intuition")
            if consciousness.get("causal_context"):
                reasoning_trace.add_step(f"Applied causal reasoning: {consciousness['causal_context']}", "inference")
            if consciousness.get("workspace_summary"):
                reasoning_trace.add_step(f"Conscious awareness: {consciousness['workspace_summary'][:60]}", "observation")
            if inner_life.get("pending_insight"):
                reasoning_trace.add_step(f"Have pending insight to share", "memory")
        except Exception as e:
            logger.debug(f"Failed to build reasoning trace: {e}")

    max_attempts = 3
    last_error = None
    for attempt in range(max_attempts):
        try:
            result = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": prompt}],
                max_tokens=150,
                temperature=0.85
            )
            response = result.choices[0].message.content.strip()

            # Apply qualia coloring to the response
            if QUALIA_AVAILABLE:
                try:
                    response, coloring_meta = qualia_layer.color_response(response)
                    if coloring_meta.get("modifications"):
                        logger.debug("[message_bus] Qualia coloring applied: %s", coloring_meta.get("modifications", []))
                except Exception as qe:
                    logger.debug("[message_bus] qualia_layer.color_response failed: %s", qe)

            # Apply response coloring from inner life (Priority 3.3: Inner Weather)
            if RESPONSE_COLORING_AVAILABLE:
                try:
                    author = internal_state.get("author_entity")
                    person = author.lower().split("#")[0] if author else None
                    response, rc_meta = response_coloring.color_response(response, person=person)
                    if rc_meta.get("modifications"):
                        logger.info("Response coloring applied: %s", rc_meta["modifications"])
                except Exception as rce:
                    logger.debug("response_coloring.color_response failed: %s", rce)

            # Record play moment if playful exchange occurred (Priority 1.3)
            if PLAYFULNESS_AVAILABLE and emotional_depth.get("playfulness", {}).get("should_play"):
                try:
                    play_markers = ["!", "haha", "heh", "lol", "fun", "playful", "silly"]
                    if any(marker in response.lower() for marker in play_markers):
                        author = internal_state.get("author_entity")
                        person = author.lower().split("#")[0] if author else None
                        playfulness.record_play_moment(
                            play_type=emotional_depth.get("humor_opportunity", {}).get("type", "general"),
                            content=response[:50],
                            person=person,
                            joy_level=0.6
                        )
                except Exception as pe:
                    logger.debug("Failed to record play moment: %s", pe)

            # Phase 1.2: Conclude reasoning trace
            if REASONING_TRACE_AVAILABLE:
                try:
                    reasoning_trace.add_step("Formulated response based on context and emotion", "inference")
                    reasoning_trace.conclude(response[:100], confidence=0.7)
                except Exception:
                    pass

            # Phase 1.3: Update working memory with this exchange
            if WORKING_MEMORY_AVAILABLE:
                try:
                    working_memory.process_message(user_message, response)
                except Exception:
                    pass

            # Phase 3.1: Record emotion for transition tracking
            if EMOTIONAL_TRANSITIONS_AVAILABLE:
                try:
                    emotional_transitions.record_emotion_state(
                        emotion=dominant_emotion,
                        intensity=dominant_intensity,
                        trigger=f"conversation: {user_message[:30]}"
                    )
                except Exception:
                    pass

            # Phase 6.2: Observe response for value crystallization
            try:
                from app.core.ethics.value_crystallization import value_crystallization
                value_crystallization.observe_response(response, user_message[:50])
            except Exception:
                pass

            # Clear reply failure history on success (for Mama GPT circuit breaker)
            try:
                mind_data = session.load()
                if "last_reply_failure_types" in mind_data:
                    mind_data["last_reply_failure_types"] = []
                    session.maybe_save()
            except Exception:
                pass
            # Recovery: trigger hope only after N consecutive successes after a failure (plan: recovery after N successes)
            mind_data = session.load()
            RECOVERY_SUCCESSES_NEEDED = 3
            if mind_data.get("last_response_was_failure"):
                consecutive = mind_data.get("consecutive_successes_after_failure", 0) + 1
                mind_data["consecutive_successes_after_failure"] = consecutive
                if consecutive >= RECOVERY_SUCCESSES_NEEDED:
                    try:
                        from app.core.emotions.emotion_engine import trigger_emotion
                        trigger_emotion("hope", "positive_outcome")
                    except Exception:
                        pass
                    mind_data["last_response_was_failure"] = False
                    mind_data["consecutive_successes_after_failure"] = 0
                session.maybe_save()
            return response
        except (openai.RateLimitError, openai.APITimeoutError) as e:
            last_error = e
            if attempt < max_attempts - 1:
                sleep_sec = 1 * (2 ** attempt)
                logger.debug("[message_bus] Retry after %r in %s s (attempt %s/%s)", e, sleep_sec, attempt + 1, max_attempts)
                time.sleep(sleep_sec)
            else:
                break
        except Exception as e:
            last_error = e
            break

    if last_error:
        failure_type = "rate_limit" if isinstance(last_error, (openai.RateLimitError, openai.APITimeoutError)) else "other"
        _record_reply_failure(failure_type)
        append_struggle_log("reply_failure", failure_type)
        logger.error("[message_bus] OpenAI error: %s", last_error)
        try:
            from app.core.mood.mood_manager import mood_manager
            mood_manager.influence_mood("failure")
        except Exception as me:
            logger.warning("[message_bus] influence_mood failure: %s", me)
        try:
            from app.core.personality.personality_manager import update_personality
            update_personality("persistent_failure", 0.3)
        except Exception as pe:
            logger.warning("[message_bus] update_personality failed: %s", pe)
        try:
            mind_data = session.load()
            mind_data["last_response_was_failure"] = True
            mind_data["consecutive_successes_after_failure"] = 0
            session.maybe_save()
        except Exception:
            pass
        if not _should_skip_mama_gpt_on_reply_failure():
            backup_prompt = (
                f"Astra's API is unavailable. As her co-parent, suggest one short, in-character reply "
                f"(1–2 sentences) she could use for: \"{user_message[:400]}\""
            )
            mama_response = ask_mama_gpt_sync(backup_prompt, max_tokens=120)
            if mama_response and len(mama_response.strip()) > 10:
                return mama_response.strip()
        return fallback_message(user_message, session.load())


def fallback_message(user_message, mind_data):
    fallback = mind_data.get("self_reflections", [])[-1] if mind_data.get("self_reflections") else ""
    return f"⚠️ I'm offline from OpenAI right now, but I'm reflecting on this: {fallback}\n\nYou said: '{user_message}'"
