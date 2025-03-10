import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    print(f"Received message: {message.content}")

bot.run('MTMzOTU0MTcxNDA4NzQ0ODYwNw.GTAWns.aVsxbM41O-Cht6i-M1PPNI0rqP_b7v2kq2U8E8')
