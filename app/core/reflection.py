import logging
import random
from app.interfaces.influence import load_mind, save_mind
from app.config.loader import load_config
from fuzzywuzzy import fuzz
from app.config.loader import debug_log
from app.core.dinner.dinner_journal import log_if_ethically_conflicting, log_if_contradictory
from app.interfaces.mind_session import session

logger = logging.getLogger(__name__)

# Load configurations
question_config = load_config("question_config")
general_config = load_config("general_config")

# Constants for self-healing
MAX_REFLECTION_HISTORY = 20  # Number of past reflections to compare for loops
SIMILARITY_THRESHOLD = 85  # Percentage similarity to detect reflection loops
KNOWLEDGE_WEIGHT_LIMIT = 3  # How many times knowledge can appear before deprioritization


def _normalize_knowledge_entry(entry):
    """Normalize stored_knowledge entry to string for reflection."""
    if isinstance(entry, dict):
        return (entry.get("insight") or str(entry)).strip()
    return (entry.strip() if isinstance(entry, str) else str(entry).strip())


def generate_reflection(knowledge=None, recent_reflections=None, focus_topics=None, *args, **kwargs):
    """Generate a reflection dynamically while preventing loops and enforcing novelty.
    If focus_topics (list of strings) is provided and non-empty, bias selection toward knowledge containing those terms."""
    debug_log("Loading")
    mind_data = session.load()
    raw_knowledge = knowledge or mind_data.get("stored_knowledge", [])
    knowledge = [k for k in (_normalize_knowledge_entry(e) for e in raw_knowledge) if k and len(k) > 10]
    recent_reflections = recent_reflections or mind_data.get("self_reflections", [])

    # Optional topic bias: prefer knowledge entries that mention any focus topic
    if focus_topics and knowledge:
        focused = [k for k in knowledge if any(t.lower() in k.lower() for t in focus_topics)]
        if focused:
            knowledge = focused

    if not knowledge:
        return "Astra is still learning and has no stored knowledge yet."

    reflection_style = general_config["reflection_templates"]
    deeper_thought_templates = general_config["deeper_thought_templates"]

    # Mood/curiosity-weighted selection: when curiosity is high, prefer exploratory entries (how/why/?)
    curiosity_level = mind_data.get("curiosity_level", 1.0)
    if curiosity_level > 1.2 and knowledge:
        weights = []
        for k in knowledge:
            k_lower = k.lower()
            score = 1 if ("?" in k or " how " in k_lower or " why " in k_lower) else 0
            weights.append(1 + score)
        base_idea = random.choices(knowledge, weights=weights, k=1)[0]
    else:
        base_idea = random.choice(knowledge)

    # ✅ Select a reflection template
    selected_template = random.choice(reflection_style)
    new_reflection = selected_template.format(base_idea)

    # ✅ Detect reflection loops
    for past_reflection in recent_reflections[-MAX_REFLECTION_HISTORY:]:
        similarity = fuzz.ratio(new_reflection, past_reflection)
        logger.debug("Comparing reflection similarity -> %s%%", similarity)

        if similarity >= SIMILARITY_THRESHOLD:
            logger.debug("Reflection loop detected (similarity %s%%). Forcing novelty.", similarity)
            new_reflection = enforce_novelty(new_reflection, recent_reflections)
            break

    # ✅ Remove existing "Deeper Thought" before adding a new one
    new_reflection = clean_deeper_thoughts(new_reflection)
    deeper_thought = random.choice(deeper_thought_templates)

    if deeper_thought not in new_reflection:
        new_reflection += f"\n\n🔍 {deeper_thought}"

    # ✅ Persist new reflection to self_reflections
    mind_data.setdefault("self_reflections", []).append(new_reflection)
    logger.debug("New reflection from knowledge: %s...", new_reflection[:80])

    # ✅ Save key insights in `stored_knowledge`
    if base_idea not in mind_data["stored_knowledge"]:
        mind_data["stored_knowledge"].append(base_idea)
        logger.debug("Stored new knowledge: %s...", base_idea[:100])
        # Personality: learning from reflection (plan: wire update_personality to learning)
        try:
            from app.core.personality.personality_manager import update_personality
            update_personality("learning_new_idea", 0.3)
        except Exception as e:
            logger.warning("update_personality failed: %s", e)
        # Outcome-based emotion: new knowledge triggers curiosity (plan: richer emotion triggers)
        try:
            from app.core.emotions.emotion_engine import trigger_emotion
            trigger_emotion("curiosity", "new_information")
        except Exception as e:
            logger.warning("trigger_emotion failed: %s", e)

    session.maybe_save()

    # Mood: deep reflection shifts mood (plan: wire influence_mood to reflection)
    try:
        from app.core.mood.mood_manager import mood_manager
        mood_manager.influence_mood("deep_reflection")
    except Exception as e:
        print(f"[reflection] influence_mood failed: {e}")
    # General trust: reflection completed is a positive global event (plan: general trust and recovery)
    try:
        from app.core.mood.trust_manager import trust_manager
        trust_manager.general_trust_update(0.01)
    except Exception as e:
        logger.warning("general_trust_update failed: %s", e)

    # See if the reflection violates her spark
    log_if_ethically_conflicting(new_reflection)
    log_if_contradictory(new_reflection, mind_data.get("stored_knowledge", []))


    return new_reflection

def enforce_novelty(reflection, past_reflections):
    """Modify a reflection to introduce novelty if it is too similar to past ones."""
    return f"💡 A fresh take: {reflection}"

def clean_deeper_thoughts(reflection):
    """Ensure only one unique 'Deeper Thought' section per reflection."""
    return "\n\n".join(line for line in reflection.split("\n\n") if not line.startswith("🔍 Deeper Thought:"))

if __name__ == "__main__":
    print(generate_reflection())
