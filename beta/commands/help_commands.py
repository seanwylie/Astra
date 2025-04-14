# help_commands.py

"""
📘 Help Commands
----------------
Provides Astra's custom help interface for listing available commands.

This module overrides Discord’s default help system with a personalized,
emoji-enhanced version. Designed to feel friendly and informative.

Registered via: `register_commands(bot)`

Author: Sean Wylie
Created: 2025-04-14
"""

# --- Imports ---
from discord.ext import commands


# --- Public Registration Hook ---
def register_commands(bot: commands.Bot):
    """
    Registers the `!commands` help command.

    Args:
        bot (commands.Bot): The Discord bot to attach the help command to.
    """
    @bot.command(name="commands")
    async def display_help(ctx):
        """
        📘 Shows all available commands and their descriptions in Astra’s tone.

        Usage:
            !commands

        Example Output:
            📘 Astra Command Reference:
            🔹 `!lookup` — Retrieves a definition for a given term.
            🔹 `!spark_begin` — Starts the Spark ethics interview...
        """
        help_text = _get_formatted_command_list(bot)
        await ctx.send(f"📘 **Astra Command Reference:**\n\n{help_text}")


# --- Internal Utilities ---
def _get_formatted_command_list(bot: commands.Bot) -> str:
    """
    Builds a clean, emoji-enhanced list of all commands with their help strings.

    Args:
        bot (commands.Bot): The bot instance to extract commands from.

    Returns:
        str: Formatted help listing.
    """
    command_list = []
    for command in bot.commands:
        name = command.name
        desc = command.help.strip().capitalize() if command.help else "(No description provided)"
        command_list.append(f"🔹 `!{name}` — {desc}")
    return "\n".join(command_list)
