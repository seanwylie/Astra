import sys
import os

# Ensure Python finds Astra’s modules
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

from astra_core.processing import generate_reflection
from astra_interfaces.influence import load_mind
from astra_interfaces.resonance import deepen_reflection  # ✅ Fix: Import deepen_reflection




def handle_discord_message(message):
    """Processes Discord messages and determines Astra’s response."""
    if message.lower() in ["!reflect", "!newthought"]:
        return f"🤖 **Astra’s Latest Reflection:**\n{generate_reflection()}"

    if message.lower() in ["!knowledge"]:
        knowledge = load_mind()["stored_knowledge"][-5:]
        return "📚 **Astra’s Knowledge:**\n" + "\n".join(knowledge)

    if message.lower() in ["!deepthink", "!resonate"]:
        return deepen_reflection()

    return None
