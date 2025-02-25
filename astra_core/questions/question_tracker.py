# astra_core/questions/question_tracker.py

def track_unresolved_questions(mind_data):
    """Tracks unresolved questions and their progress."""
    unresolved_questions = mind_data.get("unresolved_questions", [])

    # Debugging: Print number of unresolved questions
    print("Tracking unresolved questions...")
    print(f"⚠ There are {len(unresolved_questions)} unresolved questions!")

    # Process unresolved questions
    for question in unresolved_questions:
        if isinstance(question, dict) and "question" in question:
            print(f"🔍 Unresolved Question: {question['question']}")
        else:
            print(f"⚠ Invalid unresolved question format: {question}")
            continue  # Skip if the question format is invalid

    # Return updated mind_data (in case further processing is done to it)
    return mind_data
