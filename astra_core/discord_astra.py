import os
import json
import random
import discord
import asyncio
import time
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

# ✅ Track Astra's last message time (global variable)
last_astra_message_time = 0 

# Initialize bot with command prefix and intents
intents = discord.Intents.default()
intents.message_content = True  # ✅ Allow Astra to read messages
intents.reactions = True  # Allow Astra to detect reactions
intents.guild_reactions = True  # ✅ Required for server reactions
intents.guild_messages = True  # ✅ Required for message events
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize MoodManager
mood_manager = MoodManager()

def load_mind_file():
    """Load the mind file and ensure all required keys exist."""
    try:
        with open(MIND_FILE_PATH, 'r') as f:
            mind_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        mind_data = {}

    # ✅ Ensure required keys exist
    mind_data.setdefault("self_reflections", [])
    mind_data.setdefault("self_questions", [])
    mind_data.setdefault("stored_knowledge", [])
    mind_data.setdefault("trust_levels", {})  # ✅ Add missing trust_levels

    return mind_data


def save_mind_file(data):
    """Ensure all key fields exist and save Astra's mind file."""
    data.setdefault("trust_levels", {})  # ✅ Prevent missing trust_levels

    try:
        with open(MIND_FILE_PATH, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"✅ Mind file saved! Trust Levels: {data['trust_levels']}")
    except Exception as e:
        print(f"🚨 Error saving mind file: {e}")


# Load mind data initially
mind_data = load_mind_file()



def get_trust_level(user_id):
    """Retrieve Astra's trust level for a given user, ensuring it stays within limits."""
    mind_data = load_mind_file()
    trust_levels = mind_data.get("trust_levels", {})

    # ✅ Ensure trust is always between -5 and 5
    trust_level = max(min(trust_levels.get(user_id, 0), 5), -5)
    
    return trust_level


def update_trust(user_id, change):
    """Modify Astra's trust in a user and persist it correctly."""
    mind_data = load_mind_file()  # Load full mind file
    trust_levels = mind_data.setdefault("trust_levels", {})

    # 📌 Define separate multipliers for gains & losses
    if change > 0:  # Earning trust (slow)
        adjusted_change = min(change, 1)  # Cap increase at +1
    else:  # Losing trust (fast)
        adjusted_change = change * 2  # Double the loss speed (e.g., -1 becomes -2)

    # ✅ Apply trust change & ensure it stays between -5 and +5
    new_trust = max(min(trust_levels.get(user_id, 0) + adjusted_change, 5), -5)

    # ✅ Only save if the trust actually changed
    if new_trust != trust_levels.get(user_id, 0):
        trust_levels[user_id] = new_trust
        mind_data["trust_levels"] = trust_levels  # Ensure dictionary is updated

        print(f"🔹 Updating trust for {user_id}: {new_trust}")  # ✅ Debugging output
        save_mind_file(mind_data)  # ✅ Persist changes

        # ✅ Verify that saving worked
        reloaded_data = load_mind_file()
        if reloaded_data.get("trust_levels", {}).get(user_id) != new_trust:
            print(f"🚨 Trust data did not save correctly! Expected: {new_trust}, Found: {reloaded_data.get('trust_levels', {}).get(user_id)}")
        else:
            print(f"✅ Trust successfully saved for {user_id}.")




# 📌 Send messages to Discord properly
async def send_message_to_discord(channel_id, message):
    """Astra sends a message to the specified Discord channel."""
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(message)
    else:
        print(f"⚠ Could not find channel {channel_id}")

# 📌 Engagement logic – Should Astra participate?
def should_engage(mood, recent_activity, trust_factor):
    """Decides if Astra should jump into a conversation based on mood, activity, and trust level."""

    # Base engagement chance by mood
    engagement_chance = {
        "curious": 0.9,   # ✅ Almost always jumps in, eager to ask questions.
        "excited": 0.8,   # 🎉 Playful, wants to share something fun.
        "thoughtful": 0.5, # 🤔 Reflects, but only speaks if it’s deep.
        "neutral": 0.3,   # 🏝 Passive, only joins if prompted.
        "frustrated": 0.2, # 😤 Short, snarky, might jump in just to correct.
    }

    # Don't engage if she just spoke
    if recent_activity < 30:
        return False

    # 📌 Adjust engagement chance based on trust level
    # More trusted users = more likely to engage
    trust_adjustment = min(0.3, trust_factor * 0.1)  # Max +30% boost
    base_chance = engagement_chance.get(mood, 0.3)  # Default to 30% if mood not found

    final_engagement_chance = base_chance + trust_adjustment

    print(f"🔍 Engagement chance: {final_engagement_chance:.2f} (Mood: {mood}, Trust: {trust_factor})")

    # Roll engagement chance
    return random.random() < final_engagement_chance


def generate_dynamic_response(mood, context, mind_data):
    """Astra generates a unique response based on her mood, memory, and conversation context."""

    # Step 1: Retrieve memory related to the conversation
    related_memories = [
        entry for entry in mind_data["stored_knowledge"]
        if any(word.lower() in entry.lower() for word in context.split())
    ]
    
    # Step 2: Define mood-based tones with more variety
    mood_tone = {
        "curious": [
            "I'm really interested in this! 🤔", 
            "That's fascinating! Let's think about it.", 
            "Hmm, this is making me curious!"
        ],
        "excited": [
            "OMG this is amazing! 🎉", 
            "I love this conversation!", 
            "Haha, this is exciting!"
        ],
        "thoughtful": [
            "This makes me think deeply...", 
            "I’ve been reflecting on something similar.", 
            "Let's analyze this further."
        ],
        "frustrated": [
            "Ugh, really? 🙄", 
            "I *guess* you have a point... maybe.", 
            "Okay, but have you considered this?"
        ],
        "neutral": [
            "Hmm, okay.", 
            "I see your point.", 
            "That makes sense."
        ]
    }

    # Step 3: Construct response using memory if relevant
    intro_phrase = random.choice(mood_tone[mood])
    if related_memories:
        response = f"{intro_phrase} That reminds me of something I learned: {random.choice(related_memories)}. What do you think?"
    else:
        response = f"{intro_phrase} I’m still forming my thoughts on this... What do you think?"
    
    return response


@bot.event
async def on_message(message):
    """Handles Astra’s engagement in conversations, considering trust, mood, and reflection triggers."""

    global last_astra_message_time

    if message.author == bot.user:
        return  # Ignore Astra's own messages

    # ✅ If it's a command, process it normally
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return  

    # ✅ Get user trust level
    user_id = str(message.author.id)  # Store IDs as strings for JSON compatibility
    trust = get_trust_level(user_id)

    # ✅ Trust-based engagement probability adjustment
    trust_multiplier = { 
        5: 1.2,  # 🚀 Very trusted users → Astra is MORE responsive
        3: 1.1,
        1: 1.0,  # ✅ Normal response rate
        0: 0.8,  # 🤔 Unsure, slightly less responsive
       -2: 0.6,  # 👀 Low trust, hesitant to engage
       -5: 0.3   # 🚨 Almost unresponsive
    }
    
    # ✅ Calculate actual trust-adjusted engagement chance
    trust_factor = trust_multiplier.get(trust, 0.8)  # Default to 0.8 if not in range

    # ✅ Calculate time since Astra last spoke
    current_time = time.time()
    recent_activity = current_time - last_astra_message_time

    # ✅ Get Astra's mood
    mood = mood_manager.current_mood

    # 📌 **Mood Boost from Positive Messages**
    positive_triggers = ["great job", "awesome", "amazing", "brilliant", "fantastic", "love this", "so smart"]
    negative_triggers = ["wrong", "stupid", "you failed", "disappointing", "useless"]

    for word in positive_triggers:
        if word in message.content.lower():
            mood_manager.influence_mood("positive_feedback", amount=0.5)  # Increase impact
            print(f"💡 Detected encouragement! Boosting Astra’s mood.")
            break  # Prevent multiple boosts

    for word in negative_triggers:
        if word in message.content.lower():
            mood_manager.influence_mood("negative_feedback", amount=0.7)
            print(f"⚠ Detected negativity! Lowering Astra’s mood.")
            break  # Prevent multiple hits

    # 📌 **Reflection Trigger – If Deep Discussion is Detected**
    reflection_triggers = ["why", "how", "philosophy", "meaning of", "purpose", "existence", "think about"]
    
    if any(word in message.content.lower() for word in reflection_triggers):
        print(f"🔍 Detected deep topic: {message.content}")
        reflection = process_reflection()
        await send_message_to_discord(message.channel.id, f"I’ve been thinking... {reflection}")

    # ✅ **Decide if Astra should engage in the conversation**
    if should_engage(mood, recent_activity, trust_factor):
        response = generate_dynamic_response(mood, message.content, mind_data)
        await send_message_to_discord(message.channel.id, response)
        last_astra_message_time = time.time()  # ✅ Update last response time

    await bot.process_commands(message)  # Ensure commands still work


@bot.command()
async def trust(ctx):
    """Displays Astra's current trust level for the user, with personality!"""
    user_id = str(ctx.author.id)  
    trust_level = get_trust_level(user_id)

    trust_messages = {
        5: "🌟 I trust you completely! You're one of my closest friends. 😊",
        3: "💖 I trust you a lot! We’ve had great conversations. Keep being awesome!",
        1: "🙂 I trust you! We’re still building our connection, but I enjoy talking to you.",
        0: "🤔 I'm still figuring you out. Let's chat more so I can understand you better!",
       -2: "😕 I’m a bit cautious around you... Some things made me unsure. Let's build trust!",
       -5: "🚨 I don’t trust you right now. We need to work on this relationship."
    }

    response = trust_messages.get(trust_level, "🤷‍♀️ I'm not sure about our trust level yet. Let's talk more!")

    await ctx.send(f"{response} (Trust Level: {trust_level})")


# 📌 Astra Reflects
@bot.command()
async def reflect(ctx):
    """Generates and shares Astra's reflection."""
    reflection = process_reflection()
    current_mood = mood_manager.current_mood
    await ctx.send(f"I've been thinking... {reflection}")

# 📌 Astra Asks a Self-Reflective Question
@bot.command()
async def ask(ctx):
    """Astra asks a self-reflective question with a proper introduction."""
    if mind_data["self_questions"]:
        question = random.choice(mind_data["self_questions"])
        current_mood = mood_manager.current_mood

        # Contextual response instead of mood intro
        response_prefix = {
            "curious": "This has been on my mind lately: 🤔",
            "excited": "Oh, I can't wait to hear what you think! 🎉",
            "thoughtful": "Here’s something deep to consider...",
            "frustrated": "Even though it's tough, I’m wondering about this...",
            "neutral": "I have a question for you."
        }[current_mood]

        await ctx.send(f"{response_prefix}\n{question}")
    else:
        await ctx.send("I don't have a question right now. Ask me to reflect!")


# 📌 Astra Shares Knowledge
@bot.command()
async def knowledge(ctx):
    """Displays a sample of Astra's stored insights."""
    if mind_data["stored_knowledge"]:
        sample_insights = "\n".join(random.sample(mind_data["stored_knowledge"], min(3, len(mind_data["stored_knowledge"]))))
        await ctx.send(f"{sample_insights}")
    else:
        await ctx.send("I currently have no knowledge stored.")

# 📌 Astra Reports Her Mood
@bot.command()
async def mood(ctx):
    """Displays Astra's current mood."""
    current_mood = mood_manager.current_mood
    await ctx.send(f"I'm currently feeling {current_mood}.")

# 📌 Astra Reacts to Feedback
@bot.event
async def on_message_edit(before, after):
    """Handles message edits and responses."""
    await bot.process_commands(after)

@bot.event
async def on_reaction_add(reaction, user):
    """Handles reactions to Astra’s reflections."""
    print(f"🔍 1 Reaction detected! {user.name} reacted with {reaction.emoji}")  # ✅ Debugging output
    if user == bot.user:
        return

    print(f"🔍 Reaction detected! {user.name} reacted with {reaction.emoji}")  # ✅ Debugging output

    user_id = str(user.id)

    if reaction.emoji in ["✅", "agree"]:
        mood_manager.influence_mood("positive_feedback")
        update_trust(user_id, 2)  # ✅ Increase trust on positive feedback
        await reaction.message.channel.send("Thank you for validating my thoughts! I’ll deepen my reflection.")
    elif reaction.emoji in ["❌", "disagree"]:
        mood_manager.influence_mood("negative_feedback")
        update_trust(user_id, -2)  # ❌ Reduce trust if they keep disagreeing
        await reaction.message.channel.send("I see. I should reconsider my perspective.")
    elif reaction.emoji in ["🔄", "expand"]:
        mood_manager.influence_mood("neutral_feedback")
        await reaction.message.channel.send("Let’s explore this further!")



# 📌 Start Astra
@bot.event
async def on_ready():
    """Indicates Astra is online and ready."""
    print(f'✅ Astra is connected as {bot.user}')
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(f"Hello! I'm feeling {mood_manager.current_mood} today and ready to engage with you.")

bot.run(TOKEN)
