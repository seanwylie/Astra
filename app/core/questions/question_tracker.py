from app.core.questions.question_flagger import can_answer_question
from app.logging_config import get_logger

logger = get_logger("questions.tracker")

def track_question_patterns(mind_data):
    """Tracks and deduplicates unresolved/self questions. Removes those that have been answered."""
    logger.debug("Tracking unresolved questions...")

    unresolved_questions = mind_data.get("unresolved_questions", [])
    self_questions = mind_data.get("self_questions", [])

    logger.debug("⚠ Total unresolved questions before cleanup: %s", len(unresolved_questions))
    logger.debug("⚠ Total self questions before cleanup: %s", len(self_questions))

    # ✅ Normalize and deduplicate self_questions (support dict or string)
    unique_self_qs = []
    seen_self = set()
    for q in self_questions:
        if isinstance(q, dict):
            norm = (q.get("question") or "").strip().lower()
        else:
            norm = (q or "").strip().lower()
        if norm and norm not in seen_self:
            unique_self_qs.append(q)
            seen_self.add(norm)

    mind_data["self_questions"] = unique_self_qs
    logger.debug("✅ Unique self questions retained: %s", len(unique_self_qs))

    # ✅ Convert all unresolved questions to dict format
    cleaned_unresolved = [
        {"question": q} if isinstance(q, str) else q
        for q in unresolved_questions
    ]

    # ✅ Filter out resolved ones
    # Optimize: Batch check answered questions once instead of calling can_answer_question for each
    self_questions = mind_data.get("self_questions", [])
    answered_set = set()
    answered_questions = [
        q for q in self_questions 
        if isinstance(q, dict) and not q.get("unresolved", True) and q.get("answer")
    ]
    MAX_ANSWERED_CHECKS = 50
    recent_answered = answered_questions[-MAX_ANSWERED_CHECKS:] if len(answered_questions) > MAX_ANSWERED_CHECKS else answered_questions
    
    for q in recent_answered:
        q_text = (q.get("question") or "").strip().lower()
        if q_text:
            answered_set.add(q_text[:200])  # Store first 200 chars for matching
    
    unresolved_clean = []
    seen_unresolved = set()
    for q in cleaned_unresolved:
        q_text = q["question"].strip()
        q_key = q_text.lower()
        if q_key in seen_unresolved:
            continue  # skip duplicates
        
        # Optimize: Quick check against answered set first
        q_clean_200 = q_key[:200]
        is_answered = any(
            fuzz.ratio(q_clean_200, answered[:200]) >= 70 
            for answered in answered_set
        )
        
        if not is_answered:
            unresolved_clean.append({"question": q_text})
            seen_unresolved.add(q_key)

    mind_data["unresolved_questions"] = unresolved_clean
    logger.debug("✅ Unresolved questions after cleanup: %s", len(unresolved_clean))

    return mind_data
