# register_all_commands.py

"""
🧩 Command Registry
-------------------
Central hub for registering all Discord bot command modules.

This keeps `main.py` minimal and enables clean modular expansion.
"""

# --- Imports ---
from discord.ext import commands
from beta.commands import (
    emotion_commands,
    spark_commands,
    state_commands,
    help_commands,
    # 📦 Add future command modules here...
)

# --- Public Registration ---
def register_all_commands(bot: commands.Bot):
    """
    Registers all command modules to the provided Discord bot instance.
    
    Args:
        bot (commands.Bot): The Discord bot to attach commands to.
    """
    emotion_commands.register_commands(bot)
    spark_commands.register_commands(bot)
    state_commands.register_commands(bot)
    help_commands.register_commands(bot)
    # 📦 Register future modules here...
