# emotional_commands.py

"""
🧠 Emotional Commands
---------------------
Handles introspective commands related to Astra's emotional awareness and self-reflection.

This module defines Discord bot commands that allow users to:
- Query Astra’s current emotional state
- Manually trigger specific emotions for testing/debugging

Commands are registered dynamically via `register_commands(bot)`.

Author: Sean Wylie
Created: 2025-04-14
"""

# --- Imports ---
from discord.ext import commands
from beta.services.emotion_service import (
    test_emotion_intensity,
    describe_current_emotions
)


# --- Public Registration Hook ---
def register_commands(bot: commands.Bot):
    """
    Registers emotional state commands with the provided Discord bot instance.

    Args:
        bot (commands.Bot): The Discord bot to register commands on.
    """

    @bot.command(name="how_are_you")
    async def how_are_you(ctx):
        """
        💬 Returns Astra's current dominant emotion and a descriptive summary.

        Usage:
            !how_are_you

        Example Output:
            💬 I'm currently feeling mostly curious. I’m engaged, open to new input, and seeking patterns.
        """
        result = describe_current_emotions()
        await ctx.send(result)

    @bot.command(name="test_emotion")
    async def test_emotion(ctx, emotion: str, amount: int = 10):
        """
        🧪 Triggers a scaled emotional response for testing Astra's emotion engine.

        Usage:
            !test_emotion anger 5

        Example Output:
            🧪 Triggered `anger` using `betrayal` x5. New intensity: 3.42
        """
        result = test_emotion_intensity(emotion, amount)
        await ctx.send(result)
