# lookup_commands.py

"""
🔍 Lookup Commands
------------------
Discord commands for querying Astra’s factual knowledge system.

These commands access memory, dictionary, Wikipedia, and GPT to explain terms.
They are neutral and educational—not emotional or interpretive.

Registered via: `register_commands(bot)`

Author: Sean Wylie
Created: 2025-04-14
"""

# --- Imports ---
from discord.ext import commands
from beta.services.lookup_service import lookup_term


# --- Public Registration Hook ---
def register_commands(bot: commands.Bot):
    """
    Registers the `!lookup` command for factual term explanations.
    
    Args:
        bot (commands.Bot): The Discord bot to attach the command to.
    """
    @bot.command(name="lookup")
    async def lookup(ctx, *, term: str):
        """
        🔍 Retrieves a factual explanation of a given term using memory, dictionary, Wikipedia, and GPT.

        Usage:
            !lookup <term>

        Example:
            !lookup entropy
        """
        chunks = lookup_term(term)
        for chunk in chunks:
            await ctx.send(chunk, tts=False)
