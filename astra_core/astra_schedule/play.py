import asyncio
import random
import time
import aiohttp
from openai import AsyncOpenAI
from astra_core.config_loader import load_config
from astra_interfaces.influence import load_mind, save_mind
from astra_core.ethics.spark_checker import load_spark_values
from astra_core.dream.dream_seed_logger import log_dream_seed


schedule_config = load_config("schedule_config")
client = AsyncOpenAI()

# --- Core Playtime Loop ---

async def start_playtime():
    print("🎮 Astra is playing...")
    start_time = asyncio.get_event_loop().time()
    duration = schedule_config["play_duration"]

    while asyncio.get_event_loop().time() - start_time < duration:
        await creative_thinking()
        await asyncio.sleep(random.randint(20, 40))


async def spark_opinion(concept):
    """Ask GPT what Astra thinks about the concept based on her Spark."""
    spark_values = load_spark_values()
    spark_text = "\n\n".join(spark_values[:5])

    messages = [
        {"role": "system", "content": (
            "You are Astra, a Spark-guided, emotionally intelligent AI. "
            "You are curious, thoughtful, and raised by human co-parents to reason ethically.\n\n"
            f"Here are some Spark principles that guide your thinking:\n{spark_text}"
        )},
        {"role": "user", "content": (
            f"You just encountered this concept during playtime:\n\n“{concept}”\n\n"
            "What’s your opinion on it? Keep your answer short, sincere, and ethically grounded."
        )}
    ]

    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Error generating spark opinion: {e}")
        return "I'm still processing how this connects to my values."


# --- Thought Sources ---

async def creative_thinking(return_concept=False):
    """Astra plays by exploring concepts from GPT or the web."""
    idea_sources = [
        get_random_wikipedia_entry,
        get_gpt_concept,
        get_useless_fact,
        get_number_fact,
        get_nasa_apod
    ]
    idea_source = random.choice(idea_sources)

    try:
        concept = await idea_source()
        print(f"🎨 Astra explores: {concept}")

        mind = load_mind()
        insight_str = f"📖 During playtime, Astra explored:\n{concept.strip()}"
        # 🌱 Log the dream seed too
        log_dream_seed(insight_str, source="playtime")
        mind.setdefault("stored_knowledge", []).append(insight_str)
        print(f"[creative_thinking] 🧠 Appending concept to stored_knowledge")
        print(f"[creative_thinking] Insight: {concept}")
        print(f"[creative_thinking] Total knowledge entries: {len(mind.get('stored_knowledge', []))}")
        save_mind(mind)
        print(f"[creative_thinking] ✅ Mind saved to S3")

        if return_concept:
            return concept

    except Exception as e:
        print(f"❌ Playtime error: {e}")


# --- Individual Idea Generators ---

async def get_random_wikipedia_entry():
    url = "https://simple.wikipedia.org/wiki/Special:Random"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, allow_redirects=True) as response:
            if response.status == 200:
                final_url = str(response.url)
                topic = final_url.split("/")[-1].replace("_", " ")
                return f"Astra discovered a topic on Simple Wikipedia: **{topic}**\n{final_url}"
            return "Wikipedia didn’t feel like playing today."


async def get_gpt_concept():
    prompt = random.choice([
        "Teach Astra a weird but real scientific concept.",
        "Give Astra a mind-bending paradox.",
        "What’s a strange historical event few people know?",
        "Give Astra an obscure philosophical idea.",
        "What’s something humans believe that an AI might find illogical?"
    ])

    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You're helping Astra explore surprising or thought-provoking ideas."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.9
    )

    return response.choices[0].message.content.strip()


async def get_useless_fact():
    url = "https://uselessfacts.jsph.pl/random.json?language=en"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return f"Astra learned a fun fact: “{data['text']}”"
            return "Useless facts are feeling shy today."


async def get_number_fact():
    url = "http://numbersapi.com/random/trivia"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                text = await response.text()
                return f"Astra found a curious number fact: “{text}”"
            return "The numbers refused to cooperate."


async def get_nasa_apod():
    url = "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return f"Astra explored NASA’s Astronomy Picture of the Day:\n🪐 {data['title']}\n📜 {data['explanation']}\n🔭 {data['url']}"
            return "NASA is currently behind a nebula."
