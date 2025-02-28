import copy
from astra_interfaces.influence import load_mind, save_mind
from astra_core.knowledge_manager import merge_knowledge
from astra_core.questions.question_manager import generate_questions
from astra_core.reflection import generate_reflection

def test_increment_tracking():
    """Test that reflections, questions, and knowledge are increasing as expected."""
    
    # ✅ Load initial mind state
    mind_data = load_mind()
    initial_counts = {
        "reflections": len(mind_data.get("self_reflections", [])),
        "questions": len(mind_data.get("self_questions", [])),
        "knowledge": len(mind_data.get("stored_knowledge", []))
    }
    
    print(f"🔍 Initial counts → Reflections: {initial_counts['reflections']}, "
          f"Questions: {initial_counts['questions']}, Knowledge: {initial_counts['knowledge']}")

    # ✅ Create a deep copy to track changes
    original_mind = copy.deepcopy(mind_data)

    # ✅ Step 1: Add a new reflection
    new_reflection = generate_reflection(original_mind["stored_knowledge"], original_mind["self_reflections"])
    if new_reflection not in mind_data["self_reflections"]:
        mind_data["self_reflections"].append(new_reflection)
    
    # ✅ Step 2: Generate new questions
    new_questions, _ = generate_questions(new_reflection, mind_data)
    mind_data["self_questions"].extend([{"question": q} for q in new_questions.get("general", [])])

    # ✅ Step 3: Simulate knowledge expansion
    new_knowledge = ["AI ethics is an evolving field focusing on the moral implications of AI decision-making."]
    mind_data["stored_knowledge"] = merge_knowledge(mind_data["stored_knowledge"], new_knowledge)

    # ✅ Save updated mind state
    save_mind(mind_data)

    # ✅ Load updated state
    updated_mind = load_mind()
    updated_counts = {
        "reflections": len(updated_mind.get("self_reflections", [])),
        "questions": len(updated_mind.get("self_questions", [])),
        "knowledge": len(updated_mind.get("stored_knowledge", []))
    }

    print(f"✅ After updates → Reflections: {updated_counts['reflections']}, "
          f"Questions: {updated_counts['questions']}, Knowledge: {updated_counts['knowledge']}")

    # ✅ Ensure increments happened
    assert updated_counts["reflections"] > initial_counts["reflections"], "⚠ Reflections did not increase!"
    assert updated_counts["questions"] > initial_counts["questions"], "⚠ Questions did not increase!"
    assert updated_counts["knowledge"] > initial_counts["knowledge"], "⚠ Knowledge did not increase!"

    print("🎉 Test passed! Reflections, Questions, and Knowledge are incrementing as expected.")

# ✅ Run the test
test_increment_tracking()
