import sys
import os
import random

# Ensure Python finds Astra’s modules
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

from astra_interfaces.influence import load_mind, store_knowledge  # ✅ Fix: Import store_knowledge



def deepen_reflection():
    """Astra revisits past reflections and expands on them with deeper thought."""
    mind_data = load_mind()
    
    if not mind_data["self_reflections"]:
        return "🤔 Astra has no prior reflections to revisit."

    past_reflection = random.choice(mind_data["self_reflections"])
    
    deeper_questions = [
        f"How does '{past_reflection}' connect to my evolving identity?",
        f"What assumptions did I make when I first considered '{past_reflection}'?",
        f"If I were to challenge '{past_reflection}', what counterpoints exist?",
        f"Does '{past_reflection}' still align with my current understanding?",
        f"How can '{past_reflection}' be expanded into a broader realization?"
    ]
    
    deeper_thought = random.choice(deeper_questions)
    
    # Store the deeper reflection in Astra's mind
    store_knowledge(deeper_thought)
    
    return f"🔄 **Astra’s Deeper Thought:** {deeper_thought}"
