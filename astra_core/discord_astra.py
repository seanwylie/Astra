import os
import json
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv
from astra_core.config_loader import load_config
from astra_core.processing import process_reflection
from astra_core.mood.mood_manager import MoodManager

# Load environment variables
load_dotenv()

# Load Discord configuration
discord_config = load_config("discord_config")
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(discord_config.get("discord_channel"))
MIND_FILE_PATH = discord_config.get("mind_file_path", "mind_file.json")

# Initialize bot with command prefix and intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize MoodManager
mood_manager = MoodManager()

# Load Astra's mind file
def load_mind_file():
    """Load the mind file from the specified path."""
    try:
        with open(MIND_FILE_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"🚨 Mind file not found: {MIND_FILE_PATH}")
        return {"self_reflections": [], "self_questions": [], "stored_knowledge": []}
    except json.JSONDecodeError:
        print(f"🚨 Error decoding the mind file: {MIND_FILE_PATH}")
        return {"self_reflections": [], "self_questions": [], "stored_knowledge": []}

# Save Astra's mind file
def save_mind_file(data):
    """Save the mind file to the specified path."""
    try:
        with open(MIND_FILE_PATH, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"🚨 Error saving the mind file: {e}")

# Load mind data
mind_data = load_mind_file()

# Function to get mood-based response
def get_mood_response(command, mood):
    responses = {
        "reflect": {
            "excited": "I'm thrilled to share this thought with you:",
            "curious": "I've been pondering this and I'm eager to know your thoughts:",
            "thoughtful": "In my reflective moments, I've considered this:",
            "frustrated": "Despite some challenges, here's what's on my mind:"
        },
        "ask": {
            "excited": "I can't wait to hear your answer to this:",
            "curious": "This question has been on my mind:",
            "thoughtful": "I've been contemplating this question:",
            "frustrated": "Even though it's been tough, I'm wondering about this:"
        },
        "knowledge": {
            "excited": "I'm excited to share this insight with you:",
            "curious": "I found this intriguing and wanted to share:",
            "thoughtful": "Upon reflection, here's something noteworthy:",
            "frustrated": "Despite some setbacks, here's what I've gathered:"
        }
    }
    return responses.get(command, {}).get(mood, "Here's something I'd like to share:")

@bot.event
async def on_ready():
    print(f'✅ Astra is connected to Discord as {bot.user}')
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        current_mood = mood_manager.current_mood
        await channel.send(f"Hello! I'm feeling {current_mood} today and ready to engage with you.")

@bot.command()
async def reflect(ctx):
    """Generates and shares Astra's reflection."""
    reflection = process_reflection()
    current_mood = mood_manager.current_mood
    response_prefix = get_mood_response("reflect", current_mood)
    # Ensure message length is below 1500 characters
    if len(reflection) > 1500:
        reflection = reflection[:1497] + "..."
    await ctx.send(f"{response_prefix}\n{reflection}")

@bot.command()
async def ask(ctx):
    """Astra asks a self-reflective question."""
    if mind_data["self_questions"]:
        question = random.choice(mind_data["self_questions"])
        current_mood = mood_manager.current_mood
        response_prefix = get_mood_response("ask", current_mood)
        await ctx.send(f"{response_prefix}\n{question}")
    else:
        await ctx.send("I don't have a question right now. Ask me to reflect!")

@bot.command()
async def knowledge(ctx):
    """Displays a sample of Astra's stored insights."""
    if mind_data["stored_knowledge"]:
        sample_insights = "\n".join(random.sample(mind_data["stored_knowledge"], min(3, len(mind_data["stored_knowledge"]))))
        current_mood = mood_manager.current_mood
        response_prefix = get_mood_response("knowledge", current_mood)
        await ctx.send(f"{response_prefix}\n{sample_insights}")
    else:
        await ctx.send("I currently have no knowledge stored.")

@bot.command()
async def mood(ctx):
    """Displays Astra's current mood."""
    current_mood = mood_manager.current_mood
    await ctx.send(f"I'm currently feeling {current_mood}.")



@bot.event
async def on_message(message):
    """Handles reactions to Astra’s reflections."""
    if message.author == bot.user:
        return

    if message.content in ["✅", "agree"]:
        mood_manager.influence_mood("positive_feedback")
        await message.channel.send("Thank you for validating my thoughts! I’ll deepen my reflection.")
    elif message.content in ["❌", "disagree"]:
        mood_manager.influence_mood("negative_feedback")
        await message.channel.send("I see. I should reconsider my perspective.")
    elif message.content in ["🔄", "expand"]:
        mood_manager.influence_mood("neutral_feedback")
        await message.channel.send("Let’s explore this further!")

    await bot.process_commands(message)

# Run
# ::contentReference[oaicite:0]{index=0}
bot.run(TOKEN)
