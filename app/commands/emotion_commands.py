# emotion_commands.py

"""
🧠 Emotional Commands
---------------------
Handles introspective commands related to Astra's emotional awareness and self-reflection.

This module defines Discord bot commands that allow users to:
- Query Astra’s current emotional state
- Manually trigger specific emotions for testing/debugging

Commands are registered automatically via `auto_register_commands(...)`.

Author: Sean Wylie
Created: 2025-04-14
"""

from app.services.emotion_service import (
    test_emotion_intensity,
    describe_current_emotions
)


async def how_are_you(ctx):
    """💬 Returns Astra's current dominant emotion and a descriptive summary."""
    result = describe_current_emotions()
    await ctx.send(result)

how_are_you._is_command = True
how_are_you.category = "🧠 Emotional"


async def test_emotion(ctx, emotion: str, amount: int = 10):
    """🧪 Triggers a scaled emotional response for testing Astra's emotion engine."""
    result = test_emotion_intensity(emotion, amount)
    await ctx.send(result)

test_emotion._is_command = True
test_emotion.category = "🧠 Emotional"