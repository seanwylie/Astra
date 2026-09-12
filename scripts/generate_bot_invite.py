#!/usr/bin/env python3
"""
Generate Discord bot invite URL with required permissions.
"""
import os
import sys
from pathlib import Path

# Add project root to path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
load_dotenv(os.path.expanduser("~/.env"))

import discord
from discord.ext import commands

token = os.getenv("TOKEN", "").strip()
if not token:
    print("❌ No TOKEN found in environment")
    sys.exit(1)

# Required permissions for Astra:
# - Read Messages/View Channels (0x400)
# - Send Messages (0x800)
# - Read Message History (0x10000)
# - Use External Emojis (0x4000000)
# - Add Reactions (0x40)
# Total: 67174464 (decimal) or 0x4000000 + 0x10000 + 0x800 + 0x400 + 0x40

REQUIRED_PERMISSIONS = 67174464

async def get_bot_id():
    """Get bot ID from token."""
    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
    
    try:
        await bot.login(token)
        user = bot.user
        if user:
            return user.id
        # If user is None, we need to fetch it
        await bot.connect()
        return bot.user.id if bot.user else None
    except Exception as e:
        print(f"Error connecting: {e}")
        return None
    finally:
        await bot.close()

def generate_invite_url(bot_id):
    """Generate OAuth2 invite URL."""
    if not bot_id:
        return None
    
    url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={bot_id}"
        f"&permissions={REQUIRED_PERMISSIONS}"
        f"&scope=bot"
    )
    return url

async def main():
    print("=" * 80)
    print("Discord Bot Invite URL Generator")
    print("=" * 80)
    print()
    print("Fetching bot ID from token...")
    
    bot_id = await get_bot_id()
    
    if not bot_id:
        print("❌ Could not get bot ID. Please check your TOKEN.")
        print()
        print("To generate invite URL manually:")
        print("1. Go to https://discord.com/developers/applications")
        print("2. Select your bot application")
        print("3. Copy the 'Application ID' (this is your bot's client ID)")
        print("4. Use this URL format:")
        print(f"   https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions={REQUIRED_PERMISSIONS}&scope=bot")
        sys.exit(1)
    
    invite_url = generate_invite_url(bot_id)
    
    print(f"✅ Bot ID: {bot_id}")
    print()
    print("=" * 80)
    print("INVITE URL (copy and open in browser):")
    print("=" * 80)
    print(invite_url)
    print("=" * 80)
    print()
    print("Required permissions:")
    print("  ✅ Read Messages/View Channels")
    print("  ✅ Send Messages")
    print("  ✅ Read Message History")
    print("  ✅ Use External Emojis")
    print("  ✅ Add Reactions")
    print()
    print("After inviting, make sure to enable 'MESSAGE CONTENT INTENT' in:")
    print("  Discord Developer Portal → Your Bot → Privileged Gateway Intents")
    print("=" * 80)

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCancelled.")
