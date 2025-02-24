import sys
import os
import random

# Ensure Python finds Astra’s modules
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

from astra_interfaces.influence import load_mind, store_knowledge  # ✅ Fix: Import store_knowledge
from astra_core.config_loader import load_config  # ✅ Load configuration dynamically

# ✅ Load resonance settings
resonance_config = load_config("resonance_config")

# ✅ Fetch expansion templates from config
expansion_templates = resonance_config.get("expansion_templates")
deeper_thought_prefix = resonance_config.get("deeper_thought_prefix")

# ✅ **Strict enforcement**: Raise an error if missing!
if not isinstance(expansion_templates, list) or not expansion_templates:
    raise ValueError("🚨 Missing or invalid `expansion_templates` in resonance_config.json!")

if not isinstance(deeper_thought_prefix, str) or not deeper_thought_prefix.strip():
    raise ValueError("🚨 Missing or invalid `deeper_thought_prefix` in resonance_config.json!")

def deepen_reflection(reflection, mind_data):
    """Expand Astra's reflection by generating deeper inquiries."""

    # ✅ Ensure `reflection` is always a string
    if isinstance(reflection, list):
        print("🚨 Error: `reflection` is a list! Flattening...")
        reflection = " ".join(reflection)  # ✅ Convert list to string
    
    # ✅ Fetch deep reflection templates dynamically
    deeper_question = random.choice(expansion_templates)

    # ✅ Store updated knowledge correctly
    store_knowledge(mind_data)

    print(f"🔍 Debug: Type of `reflection` before returning: {type(reflection)}")

    return f"{reflection}\n\n{deeper_thought_prefix} {deeper_question}"
