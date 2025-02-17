import sys
import os
import random

# Ensure Python finds Astra’s modules
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

from astra_interfaces.influence import load_mind, store_knowledge  # ✅ Fix: Import store_knowledge



def deepen_reflection(reflection, mind_data):
    """Expand Astra's reflection by generating deeper inquiries."""
    
    # ✅ Ensure `reflection` is always a string
    if isinstance(reflection, list):
        print("🚨 Error: `reflection` is a list! Flattening...")
        reflection = " ".join(reflection)  # ✅ Convert list to string
    
    expansion_templates = [
        "How does this insight refine Astra’s evolving perspective?",
        "Are there counterpoints that challenge this perspective?",
        "What new questions arise from this understanding?",
        "How does this relate to Astra’s self-awareness?"
    ]
    deeper_question = random.choice(expansion_templates)

    # ✅ Store updated knowledge correctly
    store_knowledge(mind_data)

    print(f"🔍 Debug: Type of `reflection` before returning: {type(reflection)}")

    return f"{reflection}\n\n🔍 Deeper Thought: {deeper_question}"
