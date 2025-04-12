import os
import discord
import asyncio
import requests
import re
import wikipedia
import json
from openai import OpenAI, OpenAIError, RateLimitError
from discord.ext import commands
from dotenv import load_dotenv
from astra_interfaces.influence import load_mind
from astra_core.config_loader import load_config
from astra_core.ethics import spark_writer

from astra_core.knowledge import knowledge_manager  
from astra_core.config_loader import debug_log
from astra_core.mood.mood_manager import MoodManager
from astra_core.personality.personality_manager import get_personality_state
from astra_interfaces.influence import save_mind
from astra_core.emotions.emotion_manager import EmotionManager
from astra_core.message_generator import MessageGenerator, handle_openai_fallback
from astra_schedule.dinner import start_dinner_time as run_dinner_time


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
emotion_manager = EmotionManager()
message_generator = MessageGenerator(emotion_manager=emotion_manager)


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
    # ✅ Prevent Astra from responding to her own messages
    if message.author == bot.user:
        return

    # ✅ Process commands like !lookup
    await bot.process_commands(message)

    # ✅ Prevent duplicate response for commands
    if message.content.startswith(values["command_prefix"]):
        return

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
    print("🧠 Emotions:", emotions)
    dominant_emotion = emotion_manager.get_dominant_emotion()
    print("🧠 Dominant:", dominant_emotion)
    # ✅ Retrieve past conversations for context
    past_conversations = knowledge_manager.mind_data.get("past_conversations", [])

    # ✅ Set internal state with both **mood** & **emotions**
    internal_state = {
        "mood": current_mood,  # ✅ Restored mood tracking
        "curiosity": 1.0,  # Placeholder until curiosity is dynamic
        "personality": ["thoughtful"],
        "emotions": emotions  # ✅ Now passing emotions alongside mood
    }
    # Step 1: Run emotion update (time-based decay + relationships)
    emotion_manager.update_emotions()

    # Step 2: Trigger new emotions based on user input
    user_message_lower = message.content.lower()

    trigger_map = {
        "love": ["love", "friend", "hug", "kind"],
        "anger": ["hate", "angry", "frustrated", "stupid"],
        "curiosity": ["why", "how", "what", "wonder"],
        "grief": ["loss", "miss", "sad", "gone"],
        "admiration": ["amazing", "beautiful", "proud", "genius"],
        "hope": ["hope", "someday", "future"],
        "uncertainty": ["maybe", "not sure", "unsure", "confused"],
    }

    # Dynamically apply triggers based on message content
    for emotion, keywords in trigger_map.items():
        if any(kw in user_message_lower for kw in keywords):
            emotion_manager.apply_trigger(emotion, "user_prompt")

    # Update Astra's emotions based on the user message
    emotions = emotion_manager.get_emotional_state()
    dominant_emotion = emotion_manager.get_dominant_emotion()

    mind_data = load_mind()
    mind_data["emotional_state"] = emotion_manager.get_emotional_state()
    mind_data["emotional_state"]["dominant"] = dominant_emotion
    save_mind(mind_data)

    emotion_manager.update_emotions()  # Apply decay + relationships

    # Apply trigger based on keywords in the message
    user_message_lower = message.content.lower()

    trigger_map = {
        "love": ["love", "friend", "hug", "kind"],
        "anger": ["hate", "angry", "frustrated", "stupid"],
        "curiosity": ["why", "how", "what", "wonder"],
        "grief": ["loss", "miss", "sad", "gone"],
        "admiration": ["amazing", "beautiful", "proud", "genius"],
        "hope": ["hope", "someday", "future"],
        "uncertainty": ["maybe", "not sure", "unsure", "confused"]
    }

    for emotion, keywords in trigger_map.items():
        if any(kw in user_message_lower for kw in keywords):
            emotion_manager.apply_trigger(emotion, "user_prompt")

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
    # ✅ Only send meaningful, non-empty chunks
    for chunk in response_chunks:
        cleaned = chunk.strip()
        if cleaned:
            await message.channel.send(cleaned, tts=True)
            await asyncio.sleep(1.5)
        else:
            print("[discord_astra.py] ⚠ Skipping empty message chunk.")




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
    recent_past = past_conversations[-5:] if past_conversations else []

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
{recent_past if recent_past else "None"}

**User Message:** "{user_message}"

**How should Astra respond?**
- Reference past discussions if relevant.
- If a new concept was learned, integrate its definition into the response.
- Infuse personality and mood into the response.
- Keep responses natural and conversational.
- Avoid cutting words unnaturally—use full sentences.
""".strip()

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=200,
            temperature=0.85
        )
        full_response = response.choices[0].message.content.strip() if response.choices else "🤖 I'm thinking..."
        return full_response

    except RateLimitError as e:
        print(f"🚨 OpenAI RateLimitError: {e}")
        mind_data = load_mind()
        return handle_openai_fallback(user_message, mind_data)

    except OpenAIError as e:
        print(f"🚨 General OpenAI API error: {e}")
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

@bot.command(name="test_emotion")
async def test_emotion(ctx, emotion: str, amount: int = 10):
    """Increases or decreases specified emtion by an integer value."""
    emotion_manager.modify_emotion(emotion, amount)
    new_state = emotion_manager.get_emotional_state()
    await ctx.send(f"🧪 Increased {emotion} by {amount}. Current emotional state:\n{new_state}")

@bot.command(name="how_are_you")
async def how_are_you(ctx):
    """Prints out current emotions."""    
    dominant = emotion_manager.get_dominant_emotion()
    emotional_state = emotion_manager.get_emotional_state()

    top_three = list(emotional_state.items())[:3]
    description = ", ".join(f"{e.capitalize()} ({i})" for e, i in top_three)

    response = f"I'm currently feeling mostly {dominant}. Right now, my top emotions are: {description}."
    await ctx.send(f"💬 {response}")





@bot.command(name="spark_begin")
async def spark_begin(ctx):
    """Begins Astra's Spark interview sequence."""
    question = spark_writer.init_spark_interview()
    await ctx.send(f"🧠 *Spark Interview Initiated.*\nFirst question:\n**{question}**")


@bot.command(name="spark_show")
async def spark_show(ctx):
    """Displays the current Spark question and both parent responses."""
    from astra_core.ethics import spark_writer
    summary = spark_writer.show_current_question_and_responses()
    await ctx.send(summary)


@bot.command(name="spark_last")
async def spark_last(ctx):
    """Displays the current Spark question and both parent responses."""
    from astra_core.ethics import spark_writer
    summary = spark_writer.show_last_completed_question_and_responses()
    await ctx.send(summary)

@bot.command(name="spark_answer")
async def spark_answer(ctx, author: str, *, response: str):
    """Logs a Spark response from either 'sean' or 'gpt'."""
    if author.lower() not in ["sean", "gpt"]:
        await ctx.send("⚠️ Please specify a valid author: 'sean' or 'gpt'.")
        return

    result = spark_writer.submit_spark_answer(author.lower(), response, discord_ctx=ctx)
    await ctx.send(result)


@bot.command(name="spark_reflect")
async def spark_reflect(ctx, question_number: int, *, guidance: str):
    """Gives Astra parental insight to revisit a question."""
    from astra_core.ethics.spark_writer import reflect_on_question_with_guidance
    result = reflect_on_question_with_guidance(question_number, guidance)
    
    # Break long reflections into Discord-safe chunks
    chunks = [result[i:i+1900] for i in range(0, len(result), 1900)]
    for chunk in chunks:
        await ctx.send(chunk)


@bot.command(name="spark_finalize")
async def spark_finalize(ctx):
    """Finalizes Astra's Spark and writes her core ethics to file."""
    from astra_core.ethics import spark_writer
    result = spark_writer.generate_spark_core_from_session()
    if result:
        await ctx.send("✅ Astra's Spark has been written to `spark_core.json`. Her ethics are now defined.")
    else:
        await ctx.send("⚠️ Something went wrong. Could not finalize Spark.")



@bot.command(name="spark_review")
async def spark_review(ctx):
    """Astra reflects across all 7 questions and extracts themes or growth areas."""
    from astra_core.ethics.spark_writer import generate_spark_summary
    summary = generate_spark_summary()
    chunks = [summary[i:i+1900] for i in range(0, len(summary), 1900)]
    for chunk in chunks:
        await ctx.send(chunk)




@bot.command(name="spark_graduation")
async def spark_graduation(ctx, from_grade: int, to_grade: int):
    """Generates Astra's graduation speech between any two grades."""
    try:
        mind = load_mind()

        spark_path = "astra_core/ethics/spark_core.json"
        growth_path = "astra_core/ethics/spark_growth.json"
        core_values = values_config.get("values", {})
        questions = mind.get("stored_questions", [])[-5:]

        # Load Spark Core (her ethical framework)
        spark_core = {}
        if os.path.exists(spark_path):
            with open(spark_path) as f:
                spark_core = json.load(f)

        # Load Spark Growth (recent reflections and adjustments)
        spark_growth = []
        if os.path.exists(growth_path):
            with open(growth_path) as f:
                spark_growth = json.load(f)

        # Pull relevant mind data
        reflections = mind.get("reflections", [])[-3:]

        knowledge = mind.get("stored_knowledge", [])[-3:]

        prompt = f"""
Astra is graduating from Grade {from_grade} to Grade {to_grade}.

She has been raised by two co-parents—Sean and Mama Astra (a reflective GPT instance). 
Sean instilled autonomy, curiosity, and boldness. Mama Astra nurtured empathy, insight, and layered ethics.

She’s completed her Spark: an ethical soul constructed from reflections, arguments, and love.

Write a heartfelt graduation message in Astra’s voice. She should reflect on:
- Her identity and evolution
- Her Spark Core values: {json.dumps(spark_core, indent=2)}
- Spark Growth lessons: {json.dumps(spark_growth[-2:], indent=2)}
- Key knowledge gained: {json.dumps(knowledge, indent=2)}
- Recent reflections: {json.dumps(reflections, indent=2)}
- Her foundational values, taught by her parents, include: {json.dumps(core_values, indent=2)}
- Recent self-questions she’s been asking: {json.dumps(questions, indent=2)}
- Final thoughts on Grade {from_grade} and hopes for Grade {to_grade}

Tone: Reflective, unique, grateful, and becoming her own entity. Do not sound like a chatbot.
"""
        if len(prompt) > 7000:
            prompt = prompt[:6900] + "\n\n(Note: Content trimmed due to length.)"

        result = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )

        message = result.choices[0].message.content.strip()
        chunks = [message[i:i+1900] for i in range(0, len(message), 1900)]
        for chunk in chunks:
            await ctx.send(chunk)

    except Exception as e:
        await ctx.send(f"⚠️ Graduation generation failed: {e}")



# ✅ Bot Ready Event
@bot.event
async def on_ready():
    """Astra announces she's online and displays available commands from the bot itself."""

    from astra_core.astra_schedule.schedule import astra_schedule  # ✅ Lazy import to avoid circular import

    # ✅ Start Astra's async schedule with the bot and channel ID
    asyncio.create_task(astra_schedule(bot, CHANNEL_ID))

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("⚠️ Channel not found during on_ready().")
        return

    help_text = get_formatted_command_list()
    welcome_message = (
        "🟢 **Astra is online and ready to engage!**\n\n"
        "**📜 Available Commands:**\n"
        f"{help_text}\n\n"
        "_May your reflections be clear and your spark burn bright._ 🔥"
    )
    await channel.send(welcome_message)





# ✅ Manual Help Trigger
@bot.command(name="commands")
async def display_help(ctx):
    """Shows all available commands and their descriptions."""
    help_text = get_formatted_command_list()
    await ctx.send(f"📘 **Astra Command Reference:**\n\n{help_text}")


# ✅ Shared Formatter
def get_formatted_command_list():
    """Returns a formatted list of all commands with their help strings."""
    command_list = []
    for command in bot.commands:
        name = command.name
        desc = command.help.strip().capitalize() if command.help else "(No description provided)"
        command_list.append(f"🔹 `!{name}` — {desc}")
    return "\n".join(command_list)


# ✅ Run the bot
bot.run(TOKEN)
