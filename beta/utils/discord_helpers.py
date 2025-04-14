# discord_helpers.py

"""
📘 Discord Helpers
------------------
Reusable utilities for managing Discord bot commands and output formatting.

These functions are intended to enhance command introspection and presentation
for users interacting with Astra in Discord.

Author: Sean Wylie
Created: 2025-04-14
"""

from discord.ext import commands


def get_formatted_command_list(bot: commands.Bot) -> str:
    """
    Retrieves a list of all registered bot commands and formats them
    for human-friendly display in Discord.

    Args:
        bot (commands.Bot): The active Discord bot instance.

    Returns:
        str: A newline-separated string of formatted command descriptions.
    """
    command_list = []

    for command in bot.commands:
        name = command.name
        description = command.help.strip().capitalize() if command.help else "(No description provided)"
        command_list.append(f"🔹 `!{name}` — {description}")

    return "\n".join(command_list)
