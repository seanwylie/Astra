import time
import sys
import os

# Add the project root to the Python path to resolve imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from astra_core.mood.mood_manager import mood_manager


# Manual Test Cases

def test_mood_influence():
    print("\n[TEST] Mood Influence")
    initial_mood = mood_manager.get_current_mood()
    print(f"Initial Mood: {initial_mood}")
    
    mood_manager.influence_mood("positive_feedback")
    updated_mood = mood_manager.get_current_mood()
    print(f"Updated Mood after positive feedback: {updated_mood}")
    
    mood_manager.influence_mood("negative_feedback")
    updated_mood = mood_manager.get_current_mood()
    print(f"Updated Mood after negative feedback: {updated_mood}")


def test_mood_influence_persistence():
    print("\n[TEST] Mood Influence Persistence")
    mood_manager.influence_mood("success")
    time.sleep(2)
    
    from astra_interfaces.influence import load_mind
    mind_data = load_mind()
    print("Mood Score after Success Influence:", mind_data.get("mood_score", "N/A"))


def test_modify_mood_influence():
    print("\n[TEST] Modify Mood Influence")
    mood_manager.modify_mood_influence("failure", -1.5)
    mood_manager.modify_mood_influence("success", 1.5)
    
    from astra_interfaces.influence import load_mind
    mind_data = load_mind()
    print("Updated Mood Influences:", mind_data.get("mood_influences", {}))


def test_modify_curiosity_factor():
    print("\n[TEST] Modify Curiosity Factor")
    mood_manager.modify_curiosity_factor("excited", 1.9)
    
    from astra_interfaces.influence import load_mind
    mind_data = load_mind()
    print("Updated Mood Curiosity Factors:", mind_data.get("moods", {}))


def test_mood_shift():
    print("\n[TEST] Mood Shift")
    initial_mood = mood_manager.get_current_mood()
    print(f"Initial Mood: {initial_mood}")
    
    mood_manager.influence_mood("deep_reflection")
    updated_mood = mood_manager.get_current_mood()
    print(f"Updated Mood after deep reflection: {updated_mood}")
    
    mood_manager.influence_mood("failure")
    updated_mood = mood_manager.get_current_mood()
    print(f"Updated Mood after failure: {updated_mood}")


def test_persistence_after_restart():
    print("\n[TEST] Persistence After Restart")
    mood_manager.modify_mood_influence("positive_feedback", 1.8)
    mood_manager.modify_curiosity_factor("curious", 1.7)
    
    print("Restarting Astra...")
    import os
    os.system("./wake_astra.sh")
    
    from astra_interfaces.influence import load_mind
    mind_data = load_mind()
    print("Mood Influences After Restart:", mind_data.get("mood_influences", {}))
    print("Curiosity Factors After Restart:", mind_data.get("moods", {}))


if __name__ == "__main__":
    test_mood_influence()
    test_mood_influence_persistence()
    test_modify_mood_influence()
    test_modify_curiosity_factor()
    test_mood_shift()
    test_persistence_after_restart()
