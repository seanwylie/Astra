# state_commands.py

"""
⏳ State Commands
-----------------
Registers Discord commands that manage Astra's behavioral states:
- 🥘 Dinner (ethical reflection)
- 🎮 Playtime (creative exploration)
- 🌙 Dreamtime (imaginative processing)

These commands allow manual intervention or debugging of Astra’s inner world.

Author: Sean Wylie
Created: 2025-04-14
"""

# --- Imports ---
from discord.ext import commands
from beta.services import state_service


# --- Command Registration ---
def register_commands(bot: commands.Bot):
    """
    Registers all state-related commands for Astra's time-based rituals.
    """

    @bot.command(name="dinner_summary")
    async def dinner_summary(ctx):
        """
        📜 Summarizes unresolved dinner topics in Astra's journal.
        """
        summary = state_service.get_dinner_summary()
        await ctx.send(summary)

    @bot.command(name="dinner_answer")
    async def dinner_answer(ctx, *, response: str):
        """
        📝 Records a user’s reply to Astra’s current dinner prompt.
        """
        result = state_service.submit_dinner_answer(response)
        await ctx.send(result)

    @bot.command(name="resolve_dinner")
    async def resolve_dinner(ctx):
        """
        🎓 Resolves all dinner topics with complete co-parent responses.
        """
        await state_service.resolve_all_dinner_topics(send_func=ctx.send)

    @bot.command(name="dinnertime")
    async def dinnertime(ctx):
        """
        🍽️ Manually initiates Astra’s full dinner reflection loop.
        """
        await ctx.send("🍽️ Calling Astra to the dinner table...")
        await state_service.start_dinner(bot, ctx.channel.id)

    @bot.command(name="playtime")
    async def playtime(ctx):
        """
        🎮 Starts a creative exploration cycle during playtime.
        """
        await ctx.send("🎮 Astra is entering Play Mode...")
        thoughts = await state_service.run_playtime()
        for thought in thoughts:
            await ctx.send(thought)

    @bot.command(name="dreamtime")
    async def dreamtime(ctx):
        """
        🌙 Triggers a one-off dreaming session and logs reflections.
        """
        await ctx.send("🌙 Entering dream mode...")
        final_message = await state_service.run_dreamtime()
        await ctx.send(final_message)
