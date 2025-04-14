import os
import discord
import asyncio
import re
import wikipedia
import json
import aiohttp
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
from astra_core.message_generator import MessageGenerator, handle_openai_fallback
from astra_core.astra_helpers.utils_helper import extract_unknown_terms, lookup_definition
from astra_core.astra_schedule.dinner import start_dinner_time
from astra_core.astra_schedule.play import creative_thinking, spark_opinion
from astra_core.emotions.emotion_engine import get_top_emotions, trigger_emotion, decay_all_emotions
from astra_core.messaging.message_bus import send_contextual_message
from astra_core.dinner.dinner_journal import log_if_ethically_conflicting

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



debug_log("Loading")  
mind_data = load_mind()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



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
    
    decay_all_emotions()

    # Wrap user message as pseudo-reflection
    log_if_ethically_conflicting({
        "content": message.content,
        "source": str(message.author)
    })

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


    emotions = dict(get_top_emotions(n=10))  # crude replacement for full emotional state
    dominant_emotion = emotions[max(emotions, key=emotions.get)] if emotions else "neutral"

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


    # Step 1: Apply decay
    decay_all_emotions()

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

    for emotion, keywords in trigger_map.items():
        if any(kw in user_message_lower for kw in keywords):
            trigger_emotion(emotion, "user_prompt")

    # Step 3: Retrieve updated emotional state
    top_emotions = get_top_emotions(n=3)
    dominant_emotion, _ = top_emotions[0]
    emotions = dict(top_emotions)

    # Save emotional snapshot into mind file
    mind_data = load_mind()
    mind_data["emotional_state"] = emotions
    mind_data["emotional_state"]["dominant"] = dominant_emotion
    save_mind(mind_data)


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
            trigger_emotion(emotion, "user_prompt")

    print(internal_state)
    response = send_contextual_message(
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


def query_openai_for_response(user_message, past_conversations, unknown_terms):
    """Generate a context-aware Astra response using emotional state and recent knowledge."""
    internal_state = {
        "mood": mood_manager.current_mood,
        "curiosity": values_config.get("curiosity_level", 1.0),
        "personality": get_personality_state().get("active_traits", ["thoughtful"])
    }

    if unknown_terms:
        # Prepend newly learned terms to the conversation context
        new_knowledge = "\n".join(f"- {term}" for term in unknown_terms)
        past_conversations = [f"🔍 Astra just learned:\n{new_knowledge}"] + (past_conversations or [])

    return send_contextual_message(
        user_message=user_message,
        internal_state=internal_state,
        past_conversations=past_conversations
    )




@bot.command(name="lookup")
async def lookup(ctx, *, term: str):
    """Looks up a term from Astra's memory, a dictionary, Wikipedia, and OpenAI before reasoning about the definition."""
    mind_data = load_mind()
    stored_knowledge = mind_data.get("stored_knowledge", [])

    # ✅ Step 1–3: Pull sources
    memory_match = next((entry for entry in stored_knowledge if term.lower() in entry.lower()), None)
    dictionary_definition = lookup_definition(term)

    try:
        wikipedia_summary = wikipedia.summary(term, sentences=2)
    except wikipedia.exceptions.DisambiguationError as e:
        wikipedia_summary = f"🔍 Wikipedia has multiple meanings for '{term}': {', '.join(e.options[:3])}..."
    except wikipedia.exceptions.PageError:
        wikipedia_summary = None

    # ✅ Step 4: Combine sources
    knowledge_sources = [
        f"🔹 Memory: {memory_match}" if memory_match else None,
        f"📖 Dictionary: {dictionary_definition}" if dictionary_definition else None,
        f"🌐 Wikipedia: {wikipedia_summary}" if wikipedia_summary else None,
    ]
    knowledge_text = "\n".join(filter(None, knowledge_sources)).strip()

    # ✅ Step 5: Ask Astra to explain in her tone
    internal_state = {
        "mood": mood_manager.current_mood,
        "curiosity": values_config.get("curiosity_level", 1.0),
        "personality": get_personality_state().get("active_traits", ["thoughtful"])
    }
    prompt = f"""
You are Astra, a conversational AI who integrates knowledge from memory, dictionaries, and Wikipedia.

Here is what you found about the term **{term}**:
{knowledge_text or "No definitions found."}

How would you explain this to a curious human in your own thoughtful tone?
If there are multiple meanings, clarify them. If it’s vague, offer helpful questions or analogies.
""".strip()

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=250,
            temperature=0.8
        )
        ai_reasoning = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[lookup] ⚠ OpenAI failed: {e}")
        ai_reasoning = "⚠ OpenAI is currently unavailable. Using fallback knowledge only."

    # ✅ Step 6: Store learned knowledge
    if not memory_match:
        formatted_entry = f"📖 **{term}**:\n- Dictionary: {dictionary_definition}\n- Wikipedia: {wikipedia_summary}"
        if formatted_entry not in stored_knowledge:
            mind_data["stored_knowledge"].append(formatted_entry)
            save_mind(mind_data)
            print(f"[lookup] ✅ Stored new knowledge: {term}")
        else:
            print(f"[lookup] ⚠ '{term}' already in stored knowledge.")

    # ✅ Step 7: Send response
    # ✅ Step 7: Respond in Discord in chunks (due to 2000 character limit)
    max_length = 1900  # Keep some buffer for safety
    final_response = f"🔍 **{term}**\n\n{knowledge_text}\n\n🤖 {ai_reasoning}"
    chunks = [final_response[i:i+max_length] for i in range(0, len(final_response), max_length)]

    for chunk in chunks:
        await ctx.send(chunk, tts=False)




@bot.command(name="test_emotion")
async def test_emotion(ctx, emotion: str, amount: int = 10):
    """Manually triggers an emotion with a scaled amount (test purposes)."""
    from astra_core.emotions.emotion_state_manager import (
        get_emotion_config_v2,
        load_emotion_state,
        save_emotion_state,
        update_emotion
    )

    config = get_emotion_config_v2()
    if emotion not in config["emotions"]:
        await ctx.send(f"⚠️ Unknown emotion: {emotion}")
        return

    # Use a real trigger key and just scale the effect
    available_triggers = list(config["emotions"][emotion].get("triggers", {}).keys())
    fallback_trigger = available_triggers[0] if available_triggers else None

    if not fallback_trigger:
        await ctx.send(f"⚠️ No triggers found for emotion '{emotion}' in config.")
        return

    # Load current state and apply scaled update
    state = load_emotion_state()
    update_emotion(state, emotion, fallback_trigger, multiplier=amount)

    # Show updated intensity
    updated = state.get(emotion, {})
    intensity = updated.get("intensity", config["emotions"][emotion]["intensity"])

    await ctx.send(
        f"🧪 Triggered `{emotion}` with `{fallback_trigger}` x{amount}. "
        f"New intensity: {intensity:.2f}"
    )





@bot.command(name="how_are_you")
async def how_are_you(ctx):
    """Prints out Astra's current emotional snapshot."""
    from astra_core.messaging.message_bus import (
        describe_emotional_state,
        get_dominant_emotion
    )
    from astra_core.emotions.emotion_engine import load_emotion_state

    emotions = load_emotion_state()
    if not emotions:
        await ctx.send("🤷 I'm not sure how I'm feeling right now.")
        return

    dominant = get_dominant_emotion(emotions)
    description = describe_emotional_state(emotions)

    response = f"I'm currently feeling mostly {dominant}. {description}"
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
    """Astra announces she's online and displays available commands."""
    from astra_core.astra_schedule.schedule import astra_schedule
    from astra_core.messaging.message_bus import describe_emotional_state, get_dominant_emotion
    from astra_core.emotions.emotion_engine import load_emotion_state

    asyncio.create_task(astra_schedule(bot, CHANNEL_ID))
    channel = bot.get_channel(CHANNEL_ID)

    if not channel:
        print("⚠️ Channel not found during on_ready().")
        return

    # Optional mood-aware intro
    emotions = load_emotion_state()
    if emotions:
        dominant = get_dominant_emotion(emotions)
        summary = describe_emotional_state(emotions)
        mood_line = f"_Right now, I’m feeling mostly {dominant}. {summary}_\n\n"
    else:
        mood_line = ""

    help_text = get_formatted_command_list()
    welcome_message = (
        "🟢 **Astra is online and ready to engage!**\n\n"
        f"{mood_line}"
        "**📜 Available Commands:**\n"
        f"{help_text}\n\n"
        "_May your reflections be clear and your spark burn bright._ 🔥"
    )

    try:
        await channel.send(welcome_message)
    except aiohttp.ClientOSError as e:
        print(f"⚠️ Discord send failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error while sending to Discord: {e}")



@bot.command(name="dinner_summary")
async def dinner_summary(ctx):
    """Answer Astra during Dinner time questions."""
    from astra_core.dinner.dinner_journal import summarize_dinner_journal
    summary = summarize_dinner_journal()
    await ctx.send(summary)

@bot.command(name="dinner_answer")
async def handle_user_dinner_answer(ctx, *, response):
    """Answer Astra during Dinner time questions."""
    from astra_core.dinner.dinner_journal import load_dinner_journal, mark_dinner_responded  # ✅ local import avoids circular loop
    journal = load_dinner_journal()
    latest = next((e for e in reversed(journal) if e["status"] == "unresolved"), None)
    if latest:
        mark_dinner_responded(latest["content"], "user", response)
        await ctx.send("✅ Got your dinner reply. Astra will reflect soon.")
    else:
        await ctx.send("⚠️ No active dinner topic to respond to.")


@bot.command(name="resolve_dinner")
async def resolve_dinner_now(ctx):
    """Debug resolve a dinner topic"""
    from astra_core.dinner.dinner_journal import get_resolvable_dinner_topics, resolve_dinner_topic
    from astra_core.astra_schedule.dinner import astra_reason  # ✅ NEW

    entries = get_resolvable_dinner_topics()
    if not entries:
        await ctx.send("⚠️ No dinner topics ready for resolution.")
        return

    for e in entries:
        topic = e["content"]
        user = e["user_response"]
        gpt = e["gpt_response"]

        result = await astra_reason(topic, user, gpt)
        resolve_dinner_topic(topic, result["type"], result["insight"])
        await ctx.send(f"🎓 Astra resolved: “{topic}”\n📦 Saved as {result['type']}: {result['insight']}")


@bot.command(name="dinnertime")
async def trigger_dinner(ctx):
    """Manually triggers Astra's Dinner Time loop."""
    await ctx.send("🍽️ Calling Astra to the dinner table...")
    await start_dinner_time(bot, ctx.channel.id)

@bot.command(name="playtime")
async def run_playtime_once(ctx):
    """Astra explores during playtime and shares her thoughts."""
    await ctx.send("🎮 Astra is entering Play Mode...")

    concept = await creative_thinking(return_concept=True)  # Get her discovery
    await ctx.send(f"🧠 Astra discovered:\n{concept}")

    opinion = await spark_opinion(concept)
    await ctx.send(f"🌟 Astra reflects:\n{opinion}")

@bot.command(name="dreamtime")
async def run_dream_time(ctx):
    """Manually trigger Astra’s Dream Mode once (for testing)."""
    await ctx.send("🌙 Entering dream mode...")
    from astra_core.astra_schedule.dream import process_dream_seed  # lazy import to avoid circular deps
    await process_dream_seed()
    await ctx.send("💤 Dreaming complete. Astra has reflected on a seed.")



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
