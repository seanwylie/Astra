from astra_core.questions.question_flagger import can_answer_question

def track_question_patterns(mind_data):
    """Tracks and deduplicates unresolved/self questions. Removes those that have been answered."""
    print("Tracking unresolved questions...")

    unresolved_questions = mind_data.get("unresolved_questions", [])
    self_questions = mind_data.get("self_questions", [])

    print(f"⚠ Total unresolved questions before cleanup: {len(unresolved_questions)}")
    print(f"⚠ Total self questions before cleanup: {len(self_questions)}")

    # ✅ Normalize and deduplicate self_questions
    unique_self_qs = []
    seen_self = set()
    for q in self_questions:
        norm = q.strip().lower()
        if norm not in seen_self:
            unique_self_qs.append(q)
            seen_self.add(norm)

    mind_data["self_questions"] = unique_self_qs
    print(f"✅ Unique self questions retained: {len(unique_self_qs)}")

    # ✅ Convert all unresolved questions to dict format
    cleaned_unresolved = [
        {"question": q} if isinstance(q, str) else q
        for q in unresolved_questions
    ]

    # ✅ Filter out resolved ones
    unresolved_clean = []
    seen_unresolved = set()
    for q in cleaned_unresolved:
        q_text = q["question"].strip()
        q_key = q_text.lower()
        if q_key in seen_unresolved:
            continue  # skip duplicates
        if not can_answer_question(q_text, mind_data):
            unresolved_clean.append({"question": q_text})
            seen_unresolved.add(q_key)

    mind_data["unresolved_questions"] = unresolved_clean
    print(f"✅ Unresolved questions after cleanup: {len(unresolved_clean)}")

    return mind_data
