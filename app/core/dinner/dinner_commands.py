# astra_core/dinner/dinner_commands.py

from discord.ext import commands
from app.core.dinner.dinner_journal import load_dinner_journal, mark_dinner_responded

def setup_dinner_commands(bot):
    @bot.command(name="dinner_answer")
    async def handle_user_dinner_answer(ctx, *, response):
        journal = load_dinner_journal()
        latest = next((e for e in reversed(journal) if e["status"] == "unresolved"), None)
        if latest:
            mark_dinner_responded(latest["content"], "user", response)
            await ctx.send("✅ Got your dinner reply. Astra will reflect soon.")
        else:
            await ctx.send("⚠️ No active dinner topic to respond to.")
