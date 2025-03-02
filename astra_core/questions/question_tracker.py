# astra_core/questions/question_tracker.py

from astra_core.questions.question_flagger import can_answer_question

def track_question_patterns(mind_data):
    """Tracks unresolved questions and removes those that have been answered."""
    unresolved_questions = mind_data.get("unresolved_questions", [])

    print("Tracking unresolved questions...")
    print(f"⚠ There are {len(unresolved_questions)} unresolved questions!")

    # ✅ Ensure all unresolved questions are in dict format
    unresolved_questions = [
        {"question": q} if isinstance(q, str) else q
        for q in unresolved_questions
    ]

    # ✅ Filter out questions that Astra can now answer
    unresolved_questions = [
        q for q in unresolved_questions if not can_answer_question(q["question"], mind_data)
    ]

    # ✅ Update the mind_data structure
    mind_data["unresolved_questions"] = unresolved_questions

    # Debugging: Print updated unresolved questions
    print(f"✅ After cleanup, {len(unresolved_questions)} unresolved questions remain.")
    # for question in unresolved_questions:
        # print(f"🔍 Unresolved Question: {question['question']}")

    return mind_data  # ✅ Return updated mind_data
