# lookup_commands.py

"""
🔍 Lookup Commands
------------------
Provides factual, multi-source term explanations using memory, dictionary, Wikipedia, and GPT.

This command powers Astra’s factual knowledge system, focused on clarity and education
without emotional interpretation.

Commands are registered automatically via `auto_register_commands(...)`.

Author: Sean Wylie
Created: 2025-04-14
"""

from app.services.lookup_service import lookup_term


async def lookup(ctx, *, term: str):
    """🔍 Explains a term using Astra’s memory, dictionary, Wikipedia, or GPT."""
    chunks = lookup_term(term)
    for chunk in chunks:
        await ctx.send(chunk)

lookup._is_command = True
lookup.category = "🔍 Lookup"
