import time
from astra_core.config_loader import load_config
from astra_interfaces.influence import load_mind, save_mind
from astra_core.knowledge import knowledge_manager
from astra_core.processing import process_reflection
from astra_core.config_loader import debug_log


# ✅ Load configurable dream settings
schedule_config = load_config("schedule_config")

# 🔧 Configurable Dreaming Constraints
MAX_DREAM_CYCLES = schedule_config.get("dream_duration", 1800) // 300  # ~10 cycles (adjusted dynamically)
EXTERNAL_LOOKUP_THRESHOLD = schedule_config.get("reflection_interval", 180) // 30  # Lookup if many unanswered

def start_dreaming():
    """Handles Astra's Dream Mode, prioritizing self-reflection before external lookups."""
    from astra_schedule.schedule import is_dream_time

    print("🌙 Astra has started Dream Mode.")

    while is_dream_time(time.localtime().tm_hour):
        time.sleep(300)  # Check every 5 minutes

        print("🌙 Astra is still dreaming...")
        debug_log("Loading")  
        mind_data = load_mind()

        # ✅ Step 1: Resolve Self-Questions Before External Lookup
        if mind_data["self_questions"]:
            print(f"🤔 Resolving {len(mind_data['self_questions'])} self-questions...")
            process_reflection()
        
        # ✅ Step 2: Extract & Limit External Lookups
        elif mind_data["unresolved_questions"]:
            print("🔍 No self-questions left, checking unknown terms...")
            unknown_terms = knowledge_manager.extract_unknown_terms(" ".join(q["question"] for q in mind_data["unresolved_questions"]))
            
            if unknown_terms:
                print(f"🌍 Attempting external knowledge retrieval for: {unknown_terms}")
                knowledge_manager.retrieve_external_knowledge(unknown_terms)

    print("🌅 Dream time is over. Transitioning to new mode.")


def trigger_external_lookup_if_needed(mind_data):
    """Triggers external knowledge lookup if unresolved questions exceed threshold."""
    unresolved_questions = mind_data.get("unresolved_questions", [])

    if len(unresolved_questions) > EXTERNAL_LOOKUP_THRESHOLD:
        print(f"🔍 Astra is missing answers for {len(unresolved_questions)} questions! Expanding knowledge...")

        # ✅ Extract unknown terms from unresolved questions
        unknown_terms = knowledge_manager.extract_unknown_terms(" ".join(q["question"] for q in unresolved_questions))

        if unknown_terms:
            knowledge_manager.retrieve_external_knowledge(unknown_terms)
            save_mind(mind_data)  # ✅ Save immediately

# ✅ Debugging: Track dream activity
def track_dream_state():
    debug_log("Loading")  
    mind_data = load_mind()
    print(f"🔍 Debug: Unresolved Questions Count: {len(mind_data.get('self_questions', []))}")
    print(f"🔍 Debug: Stored Knowledge Count: {len(mind_data.get('stored_knowledge', []))}")

if __name__ == "__main__":
    track_dream_state()
    start_dreaming()
