import discord
import sys
import asyncio

# Discord bot token and channel ID
DISCORD_TOKEN = "MTMzOTU0MTcxNDA4NzQ0ODYwNw.GfizoM.-wF3ueIOcQd3KZa8Kvpp8nQ-P8GwCIHw6fDioU"
CHANNEL_ID = 1154855642893389926  # Replace with actual channel ID

# Initialize bot
intents = discord.Intents.default()
client = discord.Client(intents=intents)

async def send_message():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    thought = sys.argv[1]
    question = sys.argv[2]
    message = f"🤖 **Astra's New Insight:** {thought}\n❓ **Follow-up Thought:** {question}"
    await channel.send(message)
    await client.close()

@client.event
async def on_ready():
    asyncio.create_task(send_message())

client.run(DISCORD_TOKEN)
