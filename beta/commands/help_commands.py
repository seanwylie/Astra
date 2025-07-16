# help_commands.py

"""
📘 Help Commands
----------------
Provides Astra's custom help interface for listing available commands.

This module overrides Discord’s default help system with a personalized,
emoji-enhanced version grouped by category.

Author: Sean Wylie
Created: 2025-04-14
"""

from discord.ext import commands
from collections import defaultdict
from beta.commands.utils.command_utils import load_category_order_from_docs


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
        """
        help_text = _get_formatted_command_list(bot)
        await ctx.send(help_text)


def _get_formatted_command_list(bot: commands.Bot) -> str:
    """
    Builds a clean, emoji-enhanced list of all commands grouped by category.

    Args:
        bot (commands.Bot): The bot instance to extract commands from.

    Returns:
        str: Formatted help listing.
    """
    grouped = defaultdict(list)

    for command in bot.commands:
        if command.name == "commands":
            continue  # Skip listing the help command itself
        name = command.name
        desc = command.help.strip().capitalize() if command.help else "(No description provided)"
        category = getattr(command, "category", "🧩 Miscellaneous")
        grouped[category].append((name, desc))

    # Sort commands alphabetically within each category
    for category in grouped:
        grouped[category].sort(key=lambda x: x[0])

    # Load docstring-based category order
    CATEGORY_ORDER = load_category_order_from_docs()

    # Build help output
    ordered_output = []
    emoji_index = []

    for cat in CATEGORY_ORDER:
        if cat in grouped:
            emoji = cat.split()[0]
            emoji_index.append(emoji)
            ordered_output.append(f"**{cat}:**")
            for name, desc in grouped[cat]:
                ordered_output.append(f"🔹 `!{name}` — {desc}")
            ordered_output.append("")

    # Handle any categories that weren't in the docstring-based order
    uncategorized = set(grouped.keys()) - set(CATEGORY_ORDER)
    for cat in sorted(uncategorized):
        emoji = cat.split()[0]
        emoji_index.append(emoji)
        ordered_output.append(f"**{cat}:**")
        for name, desc in grouped[cat]:
            ordered_output.append(f"🔹 `!{name}` — {desc}")
        ordered_output.append("")

    # Final combined output
    output = [
        f"📘 **Astra Command Reference**",
        f"\n🔹 **Categories:** {' | '.join(emoji_index)}",
        f"🔹 Type `!commands` at any time to redisplay this list.\n",
        *ordered_output,
        "May your reflections be clear and your spark burn bright. 🔥"
    ]
    return "\n".join(output)
