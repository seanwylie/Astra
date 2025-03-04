import os
import random
import discord
import time
import json
from discord.ext import commands
from astra_core.knowledge import knowledge_manager  # ✅ Re-enable knowledge lookup
from dotenv import load_dotenv
from astra_core.config_loader import load_config
from astra_core.processing import process_reflection
from astra_core.mood.mood_manager import MoodManager
from astra_core.personality.personality_manager import update_personality, load_personality, get_personality_state
from astra_interfaces.influence import load_mind, save_mind  # ✅ Centralized mind management
from astra_core.config_loader import debug_log

# Load environment variables
load_dotenv()

# Load configurations
discord_config = load_config("discord_config")
strings_config = load_config("strings_config")
values_config = load_config("values_config")
responses, emojis, values = strings_config["responses"], strings_config["emojis"], values_config["values"]

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(discord_config.get("discord_channel"))

# Track Astra's last message time
last_astra_message_time = 0 

# Initialize bot with command prefix and intents
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guild_reactions = True
intents.guild_messages = True
bot = commands.Bot(command_prefix=values["command_prefix"], intents=intents)

# Initialize MoodManager
mood_manager = MoodManager()

# ✅ Load mind data at startup
debug_log("Loading")  
mind_data = load_mind()

def get_trust_level(user_id):
    """Retrieve Astra's trust level for a given user."""
    debug_log("Loading")  
    return load_mind().get("trust_levels", {}).get(user_id, 0)

def update_trust(user_id, change):
    """Modify Astra's trust in a user and persist it."""
    debug_log("Loading")  
    mind_data = load_mind()
    trust_levels = mind_data.setdefault("trust_levels", {})
    trust_levels[user_id] = max(min(trust_levels.get(user_id, 0) + change, values["max_trust"]), values["min_trust"])
    debug_log("Saving")
    save_mind(mind_data)

async def send_message_to_discord(channel_id, message):
    """Astra sends a message to the specified Discord channel."""
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(message)

def should_engage(mood, recent_activity, trust_level, curiosity_level):
    """Decides if Astra should engage in a conversation dynamically."""
    if recent_activity < values["engagement_cooldown"]:
        return False  

    base_chance = values["mood_influence"].get(mood, values["default_engagement_chance"])
    trust_adjustment = values["trust_based_mood_adjustment"]["high_trust"] if trust_level > 0 else values["trust_based_mood_adjustment"]["low_trust"]
    curiosity_boost = values["curiosity_response_boost"] if curiosity_level > values["curiosity_threshold"] else 0

    return random.random() < min(1.0, base_chance * trust_adjustment + curiosity_boost)

@bot.command()
async def reflect(ctx):
    """Generates and shares Astra's reflection, factoring in personality evolution."""
    user_id = str(ctx.author.id)
    trust_level = get_trust_level(user_id)
    curiosity_level = mind_data.get("curiosity_level", 0)
    reflection = process_reflection()
    mood = mood_manager.current_mood

    update_personality("deep_conversation", magnitude=1.0)
    
    response = f"{responses['reflection_response'].get(mood, responses['reflection_response']['neutral'])} {reflection}"
    await ctx.send(response)

@bot.command()
async def ask(ctx):
    """Astra asks a self-reflective question based on her current mood."""
    if mind_data["self_questions"]:
        question_entry = random.choice(mind_data["self_questions"])
        question_text = question_entry["question"] if isinstance(question_entry, dict) else question_entry
    else:
        question_text = responses.get("ask_empty", "I don't have a question right now. Ask me to reflect!")

    await ctx.send(f"{responses['ask_intro'].get(mood_manager.current_mood, responses['ask_intro']['neutral'])}\n{question_text}")


@bot.command()
async def trust(ctx):
    """Displays Astra's current trust level for the user."""
    user_id = str(ctx.author.id)
    trust_level = get_trust_level(user_id)
    await ctx.send(responses["trust_messages"].get(str(trust_level), "🤷 I'm not sure how I feel about you yet."))

@bot.command()
async def knowledge(ctx):
    """Displays Astra's stored knowledge."""
    debug_log("Loading")  
    mind_data = load_mind()
    sample_insights = "\n".join(random.sample(mind_data["stored_knowledge"], min(3, len(mind_data["stored_knowledge"]))))
    await ctx.send(responses["knowledge_response"].format(knowledge=sample_insights))

@bot.command()
async def personality(ctx):
    """Displays Astra's current personality traits."""
    personality_state = load_personality()
    if not personality_state or "trait_weights" not in personality_state:
        await ctx.send("🔍 Astra doesn't seem to have any personality data yet.")
        return

    formatted_traits = "\n".join(f"**{trait}**: {value:.2f}" for trait, value in personality_state["trait_weights"].items())
    await ctx.send(f"🧠 **Astra's Personality State:**\n{formatted_traits}")

@bot.command()
async def mood(ctx):
    """Reports Astra's current mood with an organic explanation."""
    mood = mood_manager.current_mood
    personality_state = get_personality_state()
    trait_summaries = responses.get("trait_summaries", {})

    influencing_traits = [(trait, value) for trait, value in personality_state.get("trait_weights", {}).items() if value > 1.2]
    if influencing_traits:
        formatted_traits = [trait_summaries.get(trait, trait) for trait, _ in sorted(influencing_traits, key=lambda x: x[1], reverse=True)]
        trait_message = f"I'm influenced by {', '.join(formatted_traits[:-1])}, and {formatted_traits[-1]} today."
    else:
        trait_message = random.choice(responses.get("neutral_mood_messages", ["I'm just going with the flow today."]))

    await ctx.send(f"{responses.get('mood_intro', 'Right now, I feel')} {mood}. {trait_message}")

@bot.command(name="assist")  # Renames help command to "assist"
async def assist(ctx):
    await ctx.send("Here’s how you can interact with Astra...")

    """Displays a list of available commands."""
    commands_list = [
        "**!reflect** - Generate a self-reflection",
        "**!ask** - Ask Astra a self-reflective question",
        "**!trust** - Check your trust level with Astra",
        "**!knowledge** - See Astra's stored knowledge",
        "**!mood** - Check Astra's current mood",
        "**!personality** - View Astra's personality traits"
    ]
    await ctx.send(f"📜 **Astra's Commands:**\n" + "\n".join(commands_list))

@bot.command()
async def lookup(ctx, *, concept):
    """Forces Astra to look up a concept externally and store the knowledge."""
    found = knowledge_manager.retrieve_external_knowledge([concept])

    if found:
        await ctx.send(f"✅ I've learned something new about **{concept}**!")
    else:
        await ctx.send(f"❌ I couldn't find reliable information on **{concept}**.")



@bot.event
async def on_ready():
    """Indicates Astra is online and ready."""
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(responses["startup_message"].format(mood=mood_manager.current_mood))

bot.run(TOKEN)
