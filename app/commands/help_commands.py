# help_commands.py

"""
📘 Help Commands
----------------
Provides Astra's custom help interface for listing available commands.

This module overrides Discord's default help system with a personalized,
emoji-enhanced version: main !commands shows a short category index;
!commands_<slug> shows commands for that category only.

Author: Sean Wylie
Created: 2025-04-14
"""

from discord.ext import commands
from collections import defaultdict

# Category display string (as on command.category) -> slug and short description.
# Order here is the display order for the main !commands message.
CATEGORY_META = [
    ("💝 Nurturing", "nurture", "Co-parenting Astra with intention and care."),
    ("⏰ Schedule", "schedule", "Managing Astra's automated scheduling."),
    ("⏳ State", "state", "Dinner, play, dream, mind, goals."),
    ("🔍 Lookup", "lookup", "Look up terms and definitions."),
    ("🧬 Evolution", "evolution", "Astra-grown tools and code proposals."),
    ("🧠 Emotional", "emotional", "Emotional awareness and self-reflection."),
    ("🎭 Personality", "personality", "Personality modes and settings."),
    ("⚡ Spark", "spark", "Ethical Spark interview process."),
    ("🧩 Miscellaneous", "misc", "Analytics, creative, learning, memory, and other commands."),
]

# Lookup: category display name -> (slug, description)
_CATEGORY_TO_SLUG_DESC = {cat: (slug, desc) for cat, slug, desc in CATEGORY_META}
# Display order (category names)
_DISPLAY_ORDER = [cat for cat, _, _ in CATEGORY_META]

# Normalize docstring variants (e.g. "🔍 Lookup Commands") to canonical category for grouping
_CATEGORY_ALIASES = {
    "💝 Nurturing Commands": "💝 Nurturing",
    "⏰ Schedule Commands": "⏰ Schedule",
    "⏳ State Commands": "⏳ State",
    "🔍 Lookup Commands": "🔍 Lookup",
    "Evolution": "🧬 Evolution",
    "⚡ Spark Commands": "⚡ Spark",
    "🎭 Personality Commands": "🎭 Personality",
    "🧠 Emotional Commands": "🧠 Emotional",
}


def _group_commands_by_category(bot: commands.Bot):
    """Group all commands (except !commands and !commands_*) by category."""
    grouped = defaultdict(list)
    for command in bot.commands:
        name = command.name
        if name == "commands" or name.startswith("commands_"):
            continue
        category = getattr(command, "category", "🧩 Miscellaneous")
        # Ensure !lookup always appears under Lookup (in case category was lost at registration)
        if name == "lookup":
            category = "🔍 Lookup"
        category = _CATEGORY_ALIASES.get(category, category)
        desc = command.help.strip() if command.help else "(No description provided)"
        if desc:
            desc = desc.capitalize() if len(desc) > 1 else desc
        grouped[category].append((name, desc))
    for category in grouped:
        grouped[category].sort(key=lambda x: x[0])
    return grouped


def _get_formatted_command_list(bot: commands.Bot) -> str:
    """
    Builds the short category index only: header, categories line,
    "Type !commands...", one line per category with !commands_<slug>, footer.
    """
    grouped = _group_commands_by_category(bot)

    # Only categories in our mapping that have at least one command
    categories_with_commands = [cat for cat in _DISPLAY_ORDER if cat in grouped and grouped[cat]]

    # Categories line: join with | (use category name as-is for emojis)
    categories_line = " | ".join(categories_with_commands)

    # One line per category: !commands_<slug> | Category name - description
    lines = [
        "📘 **Astra Command Reference**",
        "",
        f"🔹 **Categories:** {categories_line}",
        "🔹 Type `!commands` at any time to redisplay this list.",
        "",
    ]
    for cat in _DISPLAY_ORDER:
        if cat not in grouped or not grouped[cat]:
            continue
        slug, desc = _CATEGORY_TO_SLUG_DESC[cat]
        # Emoji before the command, space after (e.g. "💝 `!commands_nurture` | Nurturing — ...")
        parts = cat.split(None, 1)
        if len(parts) == 2:
            emoji, name = parts[0], parts[1]
            prefix = f"{emoji} "
        else:
            prefix, name = "", cat
        lines.append(f"{prefix}`!commands_{slug}` | {name} — {desc}")

    lines.append("")
    lines.append("May your reflections be clear and your spark burn bright. 🔥")
    return "\n".join(lines)


def _format_category_commands(bot: commands.Bot, category: str) -> str:
    """Format a single category's commands: **Category:** then 🔹 !name — desc for each."""
    grouped = _group_commands_by_category(bot)
    if category not in grouped or not grouped[category]:
        return f"No commands in **{category}**."
    lines = [f"**{category}:**"]
    for name, desc in grouped[category]:
        lines.append(f"🔹 `!{name}` — {desc}")
    return "\n".join(lines)


def register_commands(bot: commands.Bot):
    """
    Registers `!commands` (short index) and `!commands_<slug>` for each category.
    """
    @bot.command(name="commands")
    async def display_help(ctx):
        """📘 Shows Astra's command reference (category index)."""
        help_text = _get_formatted_command_list(bot)
        await ctx.send(help_text)

    # Register !commands_<slug> for each known slug
    for _cat, slug, _desc in CATEGORY_META:
        _category = _cat
        _slug = slug

        async def category_handler(ctx, _cat=_category, _slug=_slug):
            text = _format_category_commands(bot, _cat)
            await ctx.send(text)

        category_handler.__name__ = f"commands_{_slug}"
        category_handler._is_command = True
        cmd = commands.Command(category_handler, name=f"commands_{_slug}")
        cmd.help = f"List commands in {_cat}"
        bot.add_command(cmd)
