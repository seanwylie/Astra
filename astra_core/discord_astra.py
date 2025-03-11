import os
import random
import discord
import asyncio
import openai
import requests
import re
import wikipedia
from openai import OpenAI
from discord.ext import commands
from dotenv import load_dotenv

from astra_core.knowledge import knowledge_manager  
from astra_core.config_loader import load_config, debug_log
from astra_core.processing import process_reflection
from astra_core.mood.mood_manager import MoodManager
from astra_core.personality.personality_manager import load_personality, get_personality_state
from astra_interfaces.influence import load_mind, save_mind
from astra_core.message_generator import MessageGenerator
from astra_core.emotions.emotion_manager import EmotionManager

# Load environment variables
load_dotenv()

# Load configurations
discord_config = load_config("discord_config")
strings_config = load_config("strings_config")
values_config = load_config("values_config")
soul_config = load_config("config_soul")
parent_mind = load_mind()
parent_values = parent_mind.get("core_values", {})
schedule_config = load_config("schedule_config")
parents_mind = load_mind()

responses, emojis, values = strings_config["responses"], strings_config["emojis"], values_config["values"]
TOKEN = os.getenv("TOKEN").strip()
CHANNEL_ID = int(discord_config.get("discord_channel"))

# Initialize bot with command prefix and intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=values["command_prefix"], intents=intents)

# Initialize managers
mood_manager = MoodManager()
message_generator = MessageGenerator()
emotion_manager = EmotionManager()

debug_log("Loading")  
mind_data = load_mind()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ Extract Unknown Terms
def extract_unknown_terms(user_message):
    """Extract potential complex terms from a message."""
    words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', user_message)
    stored_knowledge = knowledge_manager.mind_data.get("stored_knowledge", [])

    unknown_terms = [term for term in words if term.lower() not in stored_knowledge]
    return unknown_terms

# ✅ Look Up Definitions
def lookup_definition(term):
    """Fetch definitions using an external dictionary API."""
    clean_term = re.sub(r'[^\w\s]', '', term).strip()
    try:
        response = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{clean_term}")
        if response.status_code == 200:
            data = response.json()
            return data[0]['meanings'][0]['definitions'][0]['definition']
    except Exception as e:
        print(f"⚠ Dictionary lookup failed for '{clean_term}': {e}")
    return None

# ✅ Store Concept in Memory
def store_concept(term, definition):
    """Add a new concept and its definition to stored knowledge."""
    mind_data = load_mind()
    mind_data.setdefault("stored_knowledge", [])

    formatted_entry = f"📖 **{term}**: {definition}"

    if formatted_entry not in mind_data["stored_knowledge"]:
        mind_data["stored_knowledge"].append(formatted_entry)
        save_mind(mind_data)
        print(f"✅ Stored new concept: {formatted_entry}")
    else:
        print(f"⚠ Concept '{term}' already exists in memory.")

@bot.event
async def on_message(message):
    """Handles incoming Discord messages, applies Astra's emotional reasoning, and ensures smooth TTS delivery."""
    if message.author == bot.user:
        return  

    # ✅ Allow commands to be processed before continuing
    await bot.process_commands(message)

    user_message = message.content

    # ✅ Extract unknown terms and look up definitions
    unknown_terms = extract_unknown_terms(user_message)
    for term in unknown_terms:
        definition = lookup_definition(term)
        if definition:
            store_concept(term, definition)

    # ✅ Retrieve Astra's **mood** & **emotions**
    current_mood = mood_manager.current_mood  # ✅ Restoring mood
    emotions = emotion_manager.get_emotional_state()
    dominant_emotion = emotion_manager.get_dominant_emotion()

    # ✅ Retrieve past conversations for context
    past_conversations = knowledge_manager.mind_data.get("past_conversations", [])

    # ✅ Set internal state with both **mood** & **emotions**
    internal_state = {
        "mood": current_mood,  # ✅ Restored mood tracking
        "curiosity": 1.0,  # Placeholder until curiosity is dynamic
        "personality": ["thoughtful"],
        "emotions": emotions  # ✅ Now passing emotions alongside mood
    }
    print(internal_state)
    response = message_generator.generate_message(
        user_message=user_message,
        internal_state=internal_state,
        past_conversations=past_conversations
    )

    # ✅ Split response into logical chunks (200 chars max) for TTS
    chunk_size = 200
    response_chunks = []
    sentences = re.split(r'(?<=[.!?]) ', response)

    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 > chunk_size:
            response_chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk += " " + sentence

    response_chunks.append(current_chunk.strip())  # Add the last chunk

    # ✅ Send each chunk with a small delay for better TTS readability
    for chunk in response_chunks:
        await message.channel.send(chunk, tts=True)
        await asyncio.sleep(1.5)  # ✅ Prevents Discord rate-limiting issues



# ✅ Query OpenAI for Response with Speech Enhancements
def query_openai_for_response(user_message, past_conversations, unknown_terms):
    """Ask OpenAI to refine Astra's response using past conversations and new concepts."""
    
    internal_state = {
        "mood": mood_manager.current_mood,
        "curiosity": values_config.get("curiosity_level", 1.0),
        "personality": get_personality_state().get("active_traits", ["thoughtful"])
    }
    
    personality_traits = ", ".join(internal_state["personality"])
    mood = internal_state["mood"]

    new_knowledge = "\n".join(f"- {term}" for term in unknown_terms) if unknown_terms else "None"

    prompt = f"""
    Astra is an AI who learns from conversations with her parents.
    She does NOT introduce external knowledge but references past discussions.

    **Astra's Internal State:**
    - Mood: {mood}
    - Curiosity Level: {internal_state["curiosity"]}
    - Personality Traits: {personality_traits}

    **Newly Learned Concepts:** 
    {new_knowledge}

    **Past Discussions:** 
    {past_conversations[-5:] if past_conversations else "None"}

    **User Message:** "{user_message}"

    **How should Astra respond?**
    - Reference past discussions if relevant.
    - If a new concept was learned, integrate its definition into the response.
    - Infuse personality and mood into the response.
    - Keep responses natural and conversational.
    - Avoid cutting words unnaturally—use full sentences.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=200,
            temperature=0.85
        )
        full_response = response.choices[0].message.content.strip() if response.choices else "🤖 I'm thinking..."
        
        # ✅ Ensure proper sentence breaks & avoid mid-word splitting
        formatted_response = full_response.replace(",", ", ").replace(".", ". ").replace("?", "? ")

        return formatted_response

    except Exception as e:
        print(f"🚨 Error occurred while querying OpenAI: {e}")
        return "⚠️ Something went wrong while processing my thoughts."


@bot.command(name="lookup")
async def lookup(ctx, *, term: str):
    """Looks up a term from Astra's memory, a dictionary, Wikipedia, and OpenAI before reasoning about the definition."""
    mind_data = load_mind()
    stored_knowledge = mind_data.get("stored_knowledge", [])

    # ✅ Step 1: Check Astra's stored knowledge
    memory_match = next((entry for entry in stored_knowledge if term.lower() in entry.lower()), None)

    # ✅ Step 2: Check dictionary API
    dictionary_definition = lookup_definition(term)

    # ✅ Step 3: Check Wikipedia
    try:
        wikipedia_summary = wikipedia.summary(term, sentences=2)
    except wikipedia.exceptions.DisambiguationError as e:
        wikipedia_summary = f"🔍 Wikipedia has multiple meanings for '{term}': {', '.join(e.options[:3])}..."
    except wikipedia.exceptions.PageError:
        wikipedia_summary = None

    # ✅ Step 4: Use OpenAI to reason about all found information
    knowledge_sources = [
        f"🔹 Memory: {memory_match}" if memory_match else None,
        f"📖 Dictionary: {dictionary_definition}" if dictionary_definition else None,
        f"🌐 Wikipedia: {wikipedia_summary}" if wikipedia_summary else None,
    ]
    knowledge_text = "\n".join(filter(None, knowledge_sources))

    # ✅ Step 5: Use OpenAI to generate a well-reasoned response
    openai_prompt = f"""
    Astra is an AI who learns from conversations. When asked about '{term}', she searches her memory, dictionaries, and Wikipedia.
    
    **Collected Definitions:** 
    {knowledge_text if knowledge_text else "No definitions found."}

    **How should Astra explain this concept in a conversational and insightful way?**
    - If multiple definitions exist, explain the differences.
    - Use Astra's personality and curiosity to engage the user.
    - Ask follow-up questions if needed.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": openai_prompt}],
            max_tokens=200,
            temperature=0.8
        )
        ai_reasoning = response.choices[0].message.content.strip()
    except Exception as e:
        ai_reasoning = "⚠ OpenAI is currently unavailable. Try again later."

    # ✅ Step 6: Combine everything into one final response
    final_response = f"🔍 **{term}**\n\n{knowledge_text}\n\n🤖 {ai_reasoning}"

    await ctx.send(final_response, tts=True)

# ✅ Bot Ready Event
@bot.event
async def on_ready():
    """Astra announces when she comes online.""" 
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("🟢 Astra is online and ready to engage!")

# ✅ Run the bot
bot.run(TOKEN)
