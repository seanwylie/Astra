import os
import json
import random
import discord
import time
from discord.ext import commands
from dotenv import load_dotenv
from astra_core.config_loader import load_config
from astra_core.processing import process_reflection
from astra_core.mood.mood_manager import MoodManager
from astra_core.personality.personality_manager import update_personality, load_personality, get_personality_state

# Load environment variables
load_dotenv()

# Load configurations
discord_config = load_config("discord_config")
strings_config = load_config("strings_config")
values_config = load_config("values_config")
responses = strings_config["responses"]
emojis = strings_config["emojis"]
values = values_config["values"]

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(discord_config.get("discord_channel"))
MIND_FILE_PATH = discord_config.get("mind_file_path", "mind_file.json")

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


def load_mind_file():
    """Load the mind file and ensure all required keys exist."""
    try:
        with open(MIND_FILE_PATH, 'r') as f:
            mind_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        mind_data = {}

    mind_data.setdefault("self_reflections", [])
    mind_data.setdefault("self_questions", [])
    mind_data.setdefault("stored_knowledge", [])
    mind_data.setdefault("trust_levels", {})

    return mind_data


def save_mind_file(data):
    """Ensure all key fields exist and save Astra's mind file."""
    data.setdefault("trust_levels", {})
    try:
        with open(MIND_FILE_PATH, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"🚨 Error saving mind file: {e}")


# Load mind data initially
mind_data = load_mind_file()


def get_trust_level(user_id):
    """Retrieve Astra's trust level for a given user."""
    mind_data = load_mind_file()
    trust_levels = mind_data.get("trust_levels", {})
    return max(min(trust_levels.get(user_id, 0), values["max_trust"]), values["min_trust"])


def update_trust(user_id, change):
    """Modify Astra's trust in a user and persist it."""
    mind_data = load_mind_file()
    trust_levels = mind_data.setdefault("trust_levels", {})

    adjusted_change = min(change, values["max_trust_gain"]) if change > 0 else change * values["trust_loss_multiplier"]
    new_trust = max(min(trust_levels.get(user_id, 0) + adjusted_change, values["max_trust"]), values["min_trust"])

    if new_trust != trust_levels.get(user_id, 0):
        trust_levels[user_id] = new_trust
        save_mind_file(mind_data)




async def send_message_to_discord(channel_id, message):
    """Astra sends a message to the specified Discord channel."""
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(message)


def should_engage(mood, recent_activity, trust_level, curiosity_level):
    """Decides if Astra should engage in a conversation, incorporating trust, mood, and curiosity."""
    
    if recent_activity < values["engagement_cooldown"]:
        return False  # Avoid spamming messages

    # Mood-based engagement probability
    base_engagement_chance = values["mood_influence"].get(mood, values["default_engagement_chance"])
    
    # Trust impact on engagement (adjusted by the config value)
    trust_adjustment = values["trust_based_mood_adjustment"]["high_trust"] if trust_level > 0 else values["trust_based_mood_adjustment"]["low_trust"]

    # Curiosity impact on engagement
    curiosity_boost = values["curiosity_response_boost"] if curiosity_level > values["curiosity_threshold"] else 0

    # Compute final engagement probability
    final_engagement_chance = min(1.0, base_engagement_chance * trust_adjustment + curiosity_boost)

    print(f"🔍 Engagement Chance: {final_engagement_chance:.2f} (Mood: {mood}, Trust: {trust_level}, Curiosity: {curiosity_level})")
    return random.random() < final_engagement_chance



def generate_dynamic_response(mood, context, mind_data, trust_level, curiosity_level, reflection):
    """Astra generates a unique response based on her mood, trust, curiosity, and reflection."""

    # Base response tone based on mood
    mood_tone = responses["reflection_response"].get(mood, responses["reflection_response"]["neutral"])

    # Ensure mood_tone is a string (if it’s a list, pick a random one)
    if isinstance(mood_tone, list):
        mood_tone = random.choice(mood_tone)  # Pick a random response from the list

    # Formulate base response including the reflection
    response = mood_tone.format(reflection=reflection)

    # Modify response based on trust level
    trust_key = "high_trust" if trust_level > 3 else "low_trust"
    trust_response = responses["trust_responses"].get(trust_key, "")
    if trust_response:
        response += f" {trust_response}"  # Append trust response without a newline

    # Modify response based on curiosity level
    curiosity_key = "high_curiosity" if curiosity_level > values["curiosity_threshold"] else "low_curiosity"
    curiosity_response = responses["curiosity_responses"].get(curiosity_key, "")
    if curiosity_response:
        response += f" {curiosity_response}"  # Append curiosity response without a newline

    # Add mood-based deeper thoughts
    mood_deep_thoughts = responses["mood_deep_thoughts"].get(mood, "")
    if mood_deep_thoughts:
        response += f" {mood_deep_thoughts}"  # Append mood-based deep thoughts without a newline

    # Finalize the response by trimming any unnecessary whitespace
    return response.strip()  # Remove leading/trailing spaces for cleaner output


@bot.command()
async def trust(ctx):
    """Displays Astra's current trust level for the user."""
    user_id = str(ctx.author.id)
    trust_level = get_trust_level(user_id)

    # Ensure trust level is within the defined keys
    trust_message = responses["trust_messages"].get(str(trust_level), "🤷 I'm not sure how I feel about you yet.")

    await ctx.send(trust_message)



@bot.command()
async def reflect(ctx):
    """Generates and shares Astra's reflection, factoring in personality evolution."""
    user_id = str(ctx.author.id)
    trust_level = get_trust_level(user_id)
    curiosity_level = mind_data.get("curiosity_level", 0)
    reflection = process_reflection()
    mood = mood_manager.current_mood

    # 🔹 Update personality from event
    update_personality("deep_conversation", magnitude=1.0)

    response = generate_dynamic_response(mood, ctx.message.content, mind_data, trust_level, curiosity_level, reflection)
    
    await ctx.send(response)


@bot.command()
async def personality(ctx):
    """Displays Astra's current personality traits."""
    personality_state = load_personality()  # Fetch stored traits
    if not personality_state or "trait_weights" not in personality_state:
        await ctx.send("🔍 Astra doesn't seem to have any personality data yet.")
        return

    trait_weights = personality_state["trait_weights"]  # ✅ Extract the actual traits

    formatted_traits = "\n".join(
        f"**{trait}**: {value:.2f}" for trait, value in trait_weights.items()
    )

    await ctx.send(f"🧠 **Astra's Personality State:**\n{formatted_traits}")




@bot.command()
async def ask(ctx):
    """Astra asks a self-reflective question based on her current mood."""
    mood = mood_manager.current_mood  # Get Astra's current mood

    # Choose the appropriate introspection prompt based on mood
    intro = responses["ask_intro"].get(mood, responses["ask_intro"]["neutral"])

    # Fetch a self-reflective question
    if mind_data["self_questions"]:
        question = random.choice(mind_data["self_questions"])
        await ctx.send(f"{intro}\n{question}")
    else:
        await ctx.send(responses.get("ask_empty", "I don't have a question right now. Ask me to reflect!"))



@bot.command()
async def knowledge(ctx):
    """Displays Astra's stored knowledge."""
    if mind_data["stored_knowledge"]:
        sample_insights = "\n".join(random.sample(mind_data["stored_knowledge"], min(3, len(mind_data["stored_knowledge"]))))
        await ctx.send(f"{responses['knowledge_intro']}\n{sample_insights}")
    else:
        await ctx.send(responses["knowledge_empty"])

@bot.command()
async def mood(ctx):
    """Reports Astra's current mood with an organic explanation."""
    mood = mood_manager.current_mood
    print(f"🔍 Debug: Detected Mood - {mood}")  # Log Astra's detected mood

    personality_state = get_personality_state()  # Fetch traits
    trait_summaries = responses.get("trait_summaries", {})  # Safe lookup

    if not personality_state:
        await ctx.send("Hmm, I don't seem to have any personality data right now.")
        return

    # 🔹 Extract high-impact traits (values > 1.2 for stronger impact)
    influencing_traits = [
        (trait, value) for trait, value in personality_state.get("trait_weights", {}).items()
        if isinstance(value, (int, float)) and value > 1.2
    ]

    if influencing_traits:
        # Sort traits by impact (highest first)
        influencing_traits.sort(key=lambda x: x[1], reverse=True)

        # Convert traits into human-friendly descriptions
        formatted_traits = [trait_summaries.get(trait, trait) for trait, _ in influencing_traits]

        if len(formatted_traits) == 1:
            trait_message = f"I'm feeling this way because {formatted_traits[0]} is on my mind."
        else:
            trait_message = f"I'm influenced by {', '.join(formatted_traits[:-1])}, and {formatted_traits[-1]} today."
    else:
        # If no dominant traits, use a neutral fallback
        trait_message = random.choice(responses.get("neutral_mood_messages", ["I'm just going with the flow today."]))

    # 🔹 Assemble final mood response
    mood_message = f"{responses.get('mood_intro', 'Right now, I feel')} {mood}. {trait_message}"
    
    await ctx.send(mood_message)





@bot.event
async def on_reaction_add(reaction, user):
    """Handles reactions to Astra’s messages, adjusting trust and mood accordingly."""
    
    if user == bot.user:
        return  # Ignore Astra's own reactions

    user_id = str(user.id)

    # Get trust adjustment values safely (default to +1/-1 if missing)
    trust_gain = values.get("trust_gain_on_positive_reaction", 1)
    trust_loss = values.get("trust_loss_on_negative_reaction", -1)

    # Check for reaction type and adjust accordingly
    if reaction.emoji == emojis["positive_feedback"]:
        mood_manager.influence_mood("positive_feedback")
        update_trust(user_id, trust_gain)
        await reaction.message.channel.send(responses["reaction_responses"]["positive_feedback"])

    elif reaction.emoji == emojis["negative_feedback"]:
        mood_manager.influence_mood("negative_feedback")
        update_trust(user_id, trust_loss)
        await reaction.message.channel.send(responses["reaction_responses"]["negative_feedback"])

    elif reaction.emoji == emojis["expand"]:
        mood_manager.influence_mood("neutral_feedback")
        await reaction.message.channel.send(responses["reaction_responses"]["neutral_feedback"])


@bot.event
async def on_message(message):
    """Handles Astra’s engagement in conversations dynamically."""
    global last_astra_message_time

    if message.author == bot.user:
        return

    if message.content.startswith(values["command_prefix"]):
        await bot.process_commands(message)
        return  

    user_id = str(message.author.id)
    trust_level = get_trust_level(user_id)
    curiosity_level = mood_manager.get_curiosity()  # Assuming curiosity is tracked
    mood = mood_manager.current_mood

    current_time = time.time()
    recent_activity = current_time - last_astra_message_time

    if should_engage(mood, recent_activity, trust_level, curiosity_level):
        response = generate_dynamic_response(mood, message.content, mind_data, trust_level, curiosity_level, reflection="")

        await send_message_to_discord(message.channel.id, response)
        last_astra_message_time = time.time()

    await bot.process_commands(message)



@bot.event
async def on_ready():
    """Indicates Astra is online and ready."""
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(responses["startup_message"].format(mood=mood_manager.current_mood))

bot.run(TOKEN)
